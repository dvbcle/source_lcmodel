"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from lcmodel.io.batch import load_path_list, write_batch_csv

from lcmodel.io.basis import is_lcmodel_basis_file, load_basis_names, load_lcmodel_basis
from lcmodel.io.numeric import (
    load_complex_matrix,
    load_complex_vector,
    load_numeric_matrix,
    load_numeric_vector,
)
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.io.postscript import write_fit_postscript
from lcmodel.io.priors import load_soft_priors
from lcmodel.io.report import write_fit_table
from lcmodel.models import BatchRunResult, FitResult, RunConfig, RunResult
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.pipeline.averaging import detect_zero_voxels, weighted_average_channels
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
from lcmodel.pipeline.nonlinear import NonlinearConfig, run_nonlinear_refinement
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import (
    prepare_basis_frequency_matrix_from_time_domain,
    prepare_frequency_vector_from_time_domain,
)
from lcmodel.pipeline.sptype_presets import apply_sptype_preset, validate_sptype_config
from lcmodel.pipeline.setup import prepare_fit_inputs
from lcmodel.core.text import split_title_lines
from lcmodel.core.fftpack_compat import use_fft_backend
from lcmodel.traceability import (
    capture_trace_events,
    fortran_provenance,
    record_trace_event,
    write_trace_log,
)


@dataclass(frozen=True)
class _FitRenderPayload:
    fit_result: FitResult
    plot_x_values: tuple[float, ...]
    plot_data_values: tuple[float, ...]
    plot_fit_values: tuple[float, ...]


@dataclass(frozen=True)
class _CachedBasisSpectral:
    matrix: tuple[tuple[float, ...], ...]
    metabolite_names: tuple[str, ...]


class LCModelRunner:
    """High-level runner for incremental semantic-port behavior."""

    def __init__(
        self,
        config: RunConfig,
        *,
        _batch_basis_cache: dict[tuple[str, float, float, str], _CachedBasisSpectral] | None = None,
    ):
        # Apply legacy SPTYPE defaults once at runner construction time so both
        # CLI and direct API usage share the same behavior.
        if config.apply_sptype_presets:
            self.config = apply_sptype_preset(config)
        else:
            self.config = config
        validate_sptype_config(self.config)
        self._batch_basis_cache = _batch_basis_cache

    @fortran_provenance("lcmodl")
    def run(self) -> RunResult:
        """Execute currently ported preprocessing behaviors."""
        trace_path = self.config.traceability_log_file
        if trace_path:
            with capture_trace_events() as events:
                record_trace_event(
                    "lcmodel.engine.LCModelRunner.run",
                    ("lcmodl",),
                )
                with use_fft_backend(self.config.fft_backend):
                    result = self._run_impl()
            write_trace_log(
                trace_path,
                events=events,
                metadata={
                    "title": self.config.title,
                    "raw_data_file": self.config.raw_data_file,
                    "basis_file": self.config.basis_file,
                },
            )
            return result
        with use_fft_backend(self.config.fft_backend):
            return self._run_impl()

    def _run_impl(self) -> RunResult:
        # Fortran MAIN/MYCONT/SPLIT_TITLE intent:
        # "Load changes to Control Variables" and format TITLE for report output.
        title_layout = split_title_lines(self.config.title, self.config.ntitle)
        filename_parts: tuple[str, str] | None = None
        if self.config.output_filename:
            filename_parts = split_output_filename_for_voxel(
                self.config.output_filename, ("ps", "PS", "Ps")
            )

        render_payload: _FitRenderPayload | None = None
        if self.config.raw_data_file and self.config.basis_file:
            render_payload = self._run_fit_workflow()
        fit_result = render_payload.fit_result if render_payload is not None else None

        table_written = None
        if fit_result is not None and self.config.table_output_file:
            table_written = write_fit_table(self.config.table_output_file, fit_result)
        postscript_written = None
        if fit_result is not None and self.config.output_filename:
            postscript_written = write_fit_postscript(
                self.config.output_filename,
                title_line_1=title_layout.lines[0],
                title_line_2=title_layout.lines[1],
                x_values=list(render_payload.plot_x_values) if render_payload else [],
                data_values=list(render_payload.plot_data_values) if render_payload else [],
                fit_values=list(render_payload.plot_fit_values) if render_payload else [],
            )

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
            table_output_file=table_written,
            postscript_output_file=postscript_written,
        )

    def _run_fit_workflow(self) -> _FitRenderPayload:
        matrix, vector, ppm_axis, basis_names = self._load_fit_system()
        ppm_start = self.config.fit_ppm_start
        ppm_end = self.config.fit_ppm_end
        if (
            ppm_axis is not None
            and ppm_start is None
            and ppm_end is None
            and self.config.time_domain_input
            and not self.config.sptype.strip()
        ):
            # Fortran MYCONT defaults for standard (blank SPTYPE) runs.
            ppm_start = 4.0
            ppm_end = 0.2

        # Fortran SETUP/SETUP3:
        # choose analysis window and active basis terms before solve.
        setup = prepare_fit_inputs(
            matrix,
            vector,
            ppm_axis=ppm_axis,
            ppm_start=ppm_start,
            ppm_end=ppm_end,
            exclude_ppm_ranges=self.config.exclude_ppm_ranges,
            basis_names=basis_names,
            include_metabolites=self.config.include_metabolites,
        )
        # Fortran TWOREG/TWORG*/RFALSI outer-loop intent:
        # refine shift/linewidth search state before final linear solve.
        nonlinear = run_nonlinear_refinement(
            setup.matrix,
            setup.vector,
            FitConfig(
                baseline_order=self.config.baseline_order,
                baseline_knots=self.config.baseline_knots,
                baseline_smoothness=self.config.baseline_smoothness,
            ),
            NonlinearConfig(
                shift_search_points=self.config.shift_search_points,
                alignment_circular=self.config.alignment_circular,
                fractional_shift_refine=self.config.fractional_shift_refine,
                fractional_shift_iterations=self.config.fractional_shift_iterations,
                linewidth_scan_points=self.config.linewidth_scan_points,
                linewidth_scan_max_sigma_points=self.config.linewidth_scan_max_sigma_points,
                max_iters=self.config.nonlinear_max_iters if self.config.nonlinear_refine else 1,
                tolerance=self.config.nonlinear_tolerance,
            ),
        )
        fit_matrix = [list(row) for row in nonlinear.fit_matrix]
        fit_vector = [float(v) for v in nonlinear.fit_vector]
        if self.config.priors_file:
            # Fortran priors rows in SOLVE:
            # append soft constraints as extra equations in the linear system.
            priors = load_soft_priors(self.config.priors_file)
            fit_matrix, fit_vector = augment_system_with_soft_priors(
                fit_matrix,
                fit_vector,
                setup.metabolite_names,
                priors,
            )
        # Fortran PLINLS/SOLVE/PNNLS:
        # solve for nonnegative metabolite amplitudes (+ optional baseline terms).
        stage = run_fit_stage(
            fit_matrix,
            fit_vector,
            FitConfig(
                baseline_order=self.config.baseline_order,
                baseline_knots=self.config.baseline_knots,
                baseline_smoothness=self.config.baseline_smoothness,
            ),
        )
        # Fortran COMBIS:
        # produce metabolite group totals (e.g., CHO/GPC/PCH families).
        combined = compute_combinations(
            self.config.combine_expressions,
            stage.coefficients,
            stage.coefficient_sds,
            setup.metabolite_names,
        )
        # Fortran FINOUT table metrics:
        # derive residual and SNR-style quality summaries for reporting.
        relative_residual, snr_estimate = compute_fit_quality_metrics(
            setup.matrix,
            setup.vector,
            stage.coefficients,
            baseline=stage.baseline,
        )
        plot_data_values = tuple(float(v) for v in setup.vector)
        if ppm_axis is not None:
            plot_x_values = tuple(float(ppm_axis[i]) for i in setup.row_indices)
        else:
            plot_x_values = tuple(float(i) for i in range(len(setup.vector)))
        if stage.baseline and len(stage.baseline) == len(setup.vector):
            plot_fit_values = tuple(
                sum(float(setup.matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                + float(stage.baseline[i])
                for i in range(len(setup.vector))
            )
        else:
            plot_fit_values = tuple(
                sum(float(setup.matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                for i in range(len(setup.vector))
            )
        integrated_data_area, integrated_fit_area = self._compute_integration_areas(
            setup_vector=setup.vector,
            plot_fit_values=plot_fit_values,
            ppm_axis=ppm_axis,
            row_indices=setup.row_indices,
        )
        fit_result = FitResult(
            coefficients=stage.coefficients,
            residual_norm=stage.residual_norm,
            iterations=stage.iterations,
            method=stage.method,
            coefficient_sds=stage.coefficient_sds,
            metabolite_names=setup.metabolite_names,
            data_points_used=len(setup.vector),
            combined=combined,
            relative_residual=relative_residual,
            snr_estimate=snr_estimate,
            alignment_shift_points=nonlinear.alignment_shift_points,
            alignment_shift_fractional_points=nonlinear.alignment_shift_fractional_points,
            linewidth_sigma_points=nonlinear.linewidth_sigma_points,
            nonlinear_iterations=nonlinear.iterations,
            integrated_data_area=integrated_data_area,
            integrated_fit_area=integrated_fit_area,
        )
        return _FitRenderPayload(
            fit_result=fit_result,
            plot_x_values=plot_x_values,
            plot_data_values=plot_data_values,
            plot_fit_values=plot_fit_values,
        )

    def _load_fit_system(
        self,
    ) -> tuple[list[list[float]], list[float], list[float] | None, list[str] | None]:
        basis_names: list[str] | None = None
        if self.config.basis_names_file:
            basis_names = load_basis_names(self.config.basis_names_file)
        if self.config.time_domain_input:
            # Fortran AVERAGE/CHECK_ZERO_VOXELS:
            # average CSI/phased-array style channels before single-voxel analysis.
            if self.config.average_mode != 0:
                channels = load_complex_matrix(self.config.raw_data_file, pair_mode=True)
                if self.config.average_mode in {31, 32}:
                    normalize = False
                    weight_by_variance = False
                    selection = "odd" if self.config.average_mode == 31 else "even"
                elif self.config.average_mode in {1, 2, 3, 4}:
                    normalize = self.config.average_mode in {1, 4}
                    weight_by_variance = self.config.average_mode in {1, 2}
                    selection = "all"
                else:
                    raise ValueError("average_mode must be one of 0,1,2,3,4,31,32")
                zero_flags = None
                if self.config.average_zero_voxel_check:
                    zero_flags = detect_zero_voxels(channels)
                average = weighted_average_channels(
                    channels,
                    nback_start=self.config.average_nback_start,
                    nback_end=self.config.average_nback_end,
                    normalize_by_signal=normalize,
                    weight_by_variance=weight_by_variance,
                    selection=selection,
                    zero_voxels=zero_flags,
                )
                raw_td = list(average.averaged)
            else:
                # Fortran MYDATA:
                # read NUNFIL complex time-domain data into DATAT.
                raw_td = load_complex_vector(self.config.raw_data_file)
            if is_lcmodel_basis_file(self.config.basis_file):
                basis_cache_key = (
                    str(Path(self.config.basis_file).resolve()),
                    float(self.config.dwell_time_s),
                    float(self.config.line_broadening_hz),
                    str(self.config.fft_backend),
                )
                cached = None
                if self._batch_basis_cache is not None:
                    cached = self._batch_basis_cache.get(basis_cache_key)
                if cached is None:
                    lc_basis = load_lcmodel_basis(self.config.basis_file)
                    # Fortran MYBASI reads BASISF as frequency-domain spectra from
                    # the .basis file. Running an additional FFT here rotates data
                    # away from the solve domain and can drive coefficients to zero.
                    # Keep .basis vectors in their parsed frequency-domain frame.
                    matrix_tuple = tuple(
                        tuple(float(complex(v).real) for v in row)
                        for row in lc_basis.matrix_time_domain
                    )
                    cached = _CachedBasisSpectral(
                        matrix=matrix_tuple,
                        metabolite_names=tuple(lc_basis.metabolite_names),
                    )
                    if self._batch_basis_cache is not None:
                        self._batch_basis_cache[basis_cache_key] = cached
                matrix = [list(row) for row in cached.matrix]
                if basis_names is None and cached.metabolite_names:
                    basis_names = list(cached.metabolite_names)
            else:
                basis_td = load_complex_matrix(self.config.basis_file, pair_mode=True)

                # Batch cache for non-LCMODEL basis files is still safe and useful.
                basis_cache_key = (
                    str(Path(self.config.basis_file).resolve()),
                    float(self.config.dwell_time_s),
                    float(self.config.line_broadening_hz),
                    str(self.config.fft_backend),
                )
                cached = None
                if self._batch_basis_cache is not None:
                    cached = self._batch_basis_cache.get(basis_cache_key)
                if cached is None:
                    matrix_tuple = prepare_basis_frequency_matrix_from_time_domain(
                        basis_td,
                        dwell_time_s=self.config.dwell_time_s,
                        line_broadening_hz=self.config.line_broadening_hz,
                    )
                    cached = _CachedBasisSpectral(matrix=matrix_tuple, metabolite_names=())
                    if self._batch_basis_cache is not None:
                        self._batch_basis_cache[basis_cache_key] = cached
                matrix = [list(row) for row in cached.matrix]

            # Fortran FTDATA/PHASTA/REPHAS:
            # transform raw data to frequency domain and apply initial phase behavior.
            vector = list(
                prepare_frequency_vector_from_time_domain(
                raw_td,
                auto_phase_zero_order=self.config.auto_phase_zero_order,
                auto_phase_first_order=self.config.auto_phase_first_order,
                phase_objective=self.config.phase_objective,
                phase_smoothness_power=self.config.phase_smoothness_power,
                dwell_time_s=self.config.dwell_time_s,
                line_broadening_hz=self.config.line_broadening_hz,
                )
            )
            if len(matrix) != len(vector):
                raise ValueError("raw and basis frequency lengths do not match")
        else:
            vector = load_numeric_vector(self.config.raw_data_file)
            matrix = load_numeric_matrix(self.config.basis_file)
        ppm_axis = None
        if self.config.ppm_axis_file:
            ppm_axis = load_numeric_vector(self.config.ppm_axis_file)
        elif (
            self.config.time_domain_input
            and self.config.hzpppm > 0.0
            and self.config.dwell_time_s > 0.0
            and self.config.nunfil > 0
        ):
            # Fortran MYCONT:
            # PPMINC = 1 / (DELTAT * FNDATA * HZPPPM), where FNDATA=2*NUNFIL.
            ppminc = 1.0 / (
                float(self.config.dwell_time_s)
                * float(2 * self.config.nunfil)
                * float(self.config.hzpppm)
            )
            ppm_axis = [4.0 - i * ppminc for i in range(len(vector))]
        return matrix, vector, ppm_axis, basis_names

    def _compute_integration_areas(
        self,
        *,
        setup_vector: tuple[float, ...],
        plot_fit_values: tuple[float, ...],
        ppm_axis: list[float] | None,
        row_indices: tuple[int, ...],
    ) -> tuple[float, float]:
        integrated_data_area = 0.0
        integrated_fit_area = 0.0
        if not setup_vector:
            return integrated_data_area, integrated_fit_area

        # Fortran INTEGRATE:
        # subtract local baseline around a peak-centered symmetric window.
        peak_index = max(range(len(setup_vector)), key=lambda idx: abs(float(setup_vector[idx])))
        half_width = max(1, int(self.config.integration_half_width_points))
        window_start = max(0, peak_index - half_width)
        window_end = min(len(setup_vector) - 1, peak_index + half_width)
        border = max(1, int(self.config.integration_border_points))
        spacing = 1.0
        if ppm_axis is not None and len(row_indices) > 1:
            first = row_indices[0]
            second = row_indices[1]
            spacing = abs(float(ppm_axis[second]) - float(ppm_axis[first]))
        try:
            int_data = integrate_peak_with_local_baseline(
                setup_vector,
                peak_index=peak_index,
                start_index=window_start,
                end_index=window_end,
                border_width=border,
                spacing=spacing,
            )
            int_fit = integrate_peak_with_local_baseline(
                plot_fit_values,
                peak_index=peak_index,
                start_index=window_start,
                end_index=window_end,
                border_width=border,
                spacing=spacing,
            )
            integrated_data_area = float(int_data.area)
            integrated_fit_area = float(int_fit.area)
        except ValueError:
            integrated_data_area = 0.0
            integrated_fit_area = 0.0
        return integrated_data_area, integrated_fit_area

    def run_batch(self) -> BatchRunResult:
        """Run fit for each raw file listed in `raw_data_list_file`."""

        if not self.config.raw_data_list_file:
            raise ValueError("raw_data_list_file must be set for batch runs")
        raw_files = load_path_list(self.config.raw_data_list_file)
        basis_cache: dict[tuple[str, float, float, str], _CachedBasisSpectral] = {}
        rows: list[tuple[str, tuple[float, ...], float]] = []
        for raw_file in raw_files:
            cfg = replace(
                self.config,
                raw_data_file=raw_file,
                table_output_file=None,
                raw_data_list_file=None,
                batch_csv_file=None,
            )
            result = LCModelRunner(cfg, _batch_basis_cache=basis_cache).run()
            if result.fit_result is None:
                continue
            rows.append((raw_file, result.fit_result.coefficients, result.fit_result.residual_norm))

        csv_file = None
        if self.config.batch_csv_file:
            csv_file = write_batch_csv(self.config.batch_csv_file, rows)
        return BatchRunResult(rows=tuple(rows), csv_file=csv_file)
