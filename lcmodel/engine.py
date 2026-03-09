"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from struct import pack, unpack
from lcmodel.io.batch import load_path_list, write_batch_csv

from lcmodel.io.basis import is_lcmodel_basis_file, load_basis_names, load_lcmodel_basis
from lcmodel.io.debug_outputs import write_coordinate_debug_file, write_corrected_raw_file
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
)
from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage
from lcmodel.pipeline.h2o_reference import (
    WaterReferenceConfig,
    apply_klose_ecc,
    compute_water_scale_factor,
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
    plot_background_values: tuple[float, ...] = ()
    corrected_time_domain: tuple[complex, ...] = ()
    phase0_deg: float | None = None
    phase1_deg_per_ppm: float | None = None
    alignment_shift_fractional_points: float = 0.0
    filcor_phase0_deg: float | None = None
    filcor_phase1_deg_per_ppm: float | None = None
    filcor_shift_points: float = 0.0


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
                fit_result=fit_result,
                metadata={
                    "output_filename": Path(self.config.output_filename).name if self.config.output_filename else "",
                    "raw_data_file": Path(self.config.raw_data_file).name if self.config.raw_data_file else "",
                    "basis_file": Path(self.config.basis_file).name if self.config.basis_file else "",
                    "hzpppm": self.config.hzpppm,
                    "dwell_time_s": self.config.dwell_time_s,
                    "nunfil": self.config.nunfil,
                    "shift_ppm": (
                        float(fit_result.alignment_shift_points)
                        * (1.0 / (float(self.config.dwell_time_s) * float(2 * self.config.nunfil) * float(self.config.hzpppm)))
                        if (
                            fit_result is not None
                            and self.config.dwell_time_s > 0.0
                            and self.config.nunfil > 0
                            and self.config.hzpppm > 0.0
                        )
                        else None
                    ),
                    "phase0_deg": render_payload.phase0_deg if render_payload else None,
                    "phase1_deg_per_ppm": (
                        render_payload.phase1_deg_per_ppm if render_payload else None
                    ),
                },
            )
        if fit_result is not None and self.config.coordinate_output_file:
            write_coordinate_debug_file(
                self.config.coordinate_output_file,
                fit_result=fit_result,
                ppm_values=render_payload.plot_x_values if render_payload else (),
                phased_data_values=render_payload.plot_data_values if render_payload else (),
                fit_values=render_payload.plot_fit_values if render_payload else (),
                background_values=(
                    render_payload.plot_background_values if render_payload else ()
                ),
                phase0_deg=render_payload.phase0_deg if render_payload else None,
                phase1_deg_per_ppm=(
                    render_payload.phase1_deg_per_ppm if render_payload else None
                ),
            )
        if (
            fit_result is not None
            and self.config.corrected_raw_output_file
            and render_payload is not None
            and render_payload.corrected_time_domain
        ):
            write_corrected_raw_file(
                self.config.corrected_raw_output_file,
                corrected_time_domain=render_payload.corrected_time_domain,
                hzpppm=self.config.hzpppm,
                nunfil=self.config.nunfil if self.config.nunfil > 0 else None,
                dwell_time_s=self.config.dwell_time_s if self.config.dwell_time_s > 0.0 else None,
                phase0_deg=render_payload.filcor_phase0_deg,
                phase1_deg_per_ppm=render_payload.filcor_phase1_deg_per_ppm,
                shift_points=render_payload.filcor_shift_points,
            )

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
            table_output_file=table_written,
            postscript_output_file=postscript_written,
        )

    def _run_fit_workflow(self) -> _FitRenderPayload:
        (
            matrix,
            vector,
            ppm_axis,
            basis_names,
            phase0_deg,
            phase1_deg_per_ppm,
            corrected_time_domain,
            frequency_domain_complex,
        ) = self._load_fit_system()
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
        setup_complex: tuple[complex, ...] | None = None
        setup_ppm_axis: tuple[float, ...] | None = None
        if (
            frequency_domain_complex is not None
            and setup.row_indices
            and max(setup.row_indices) < len(frequency_domain_complex)
        ):
            setup_complex = tuple(complex(frequency_domain_complex[i]) for i in setup.row_indices)
        if ppm_axis is not None:
            setup_ppm_axis = tuple(float(ppm_axis[i]) for i in setup.row_indices)

        nonlinear_cfg = NonlinearConfig(
            shift_search_points=self.config.shift_search_points,
            alignment_circular=self.config.alignment_circular,
            fractional_shift_refine=self.config.fractional_shift_refine,
            fractional_shift_iterations=self.config.fractional_shift_iterations,
            linewidth_scan_points=self.config.linewidth_scan_points,
            linewidth_scan_max_sigma_points=self.config.linewidth_scan_max_sigma_points,
            max_iters=self.config.nonlinear_max_iters if self.config.nonlinear_refine else 1,
            tolerance=self.config.nonlinear_tolerance,
        )
        if self.config.time_domain_input:
            ppminc_window = 0.0
            if setup_ppm_axis is not None and len(setup_ppm_axis) > 1:
                ppminc_window = abs(float(setup_ppm_axis[1]) - float(setup_ppm_axis[0]))
            elif self.config.dwell_time_s > 0.0 and self.config.hzpppm > 0.0 and self.config.nunfil > 0:
                ppminc_window = 1.0 / (
                    float(self.config.dwell_time_s)
                    * float(2 * self.config.nunfil)
                    * float(self.config.hzpppm)
                )
            default_shift_points = 8
            if ppminc_window > 0.0:
                default_shift_points = max(2, min(10, int(round(0.06 / ppminc_window))))
            use_default_shift = self.config.shift_search_points <= 0
            nonlinear_cfg = NonlinearConfig(
                shift_search_points=(
                    default_shift_points
                    if use_default_shift
                    else self.config.shift_search_points
                ),
                alignment_circular=self.config.alignment_circular,
                fractional_shift_refine=self.config.fractional_shift_refine,
                fractional_shift_iterations=self.config.fractional_shift_iterations,
                linewidth_scan_points=(
                    self.config.linewidth_scan_points
                    if self.config.linewidth_scan_points > 0
                    else 3
                ),
                linewidth_scan_max_sigma_points=(
                    self.config.linewidth_scan_max_sigma_points
                    if self.config.linewidth_scan_max_sigma_points > 0.0
                    else 1.2
                ),
                max_iters=self.config.nonlinear_max_iters if self.config.nonlinear_refine else 1,
                tolerance=self.config.nonlinear_tolerance,
                enable_phase_refinement=(setup_complex is not None and setup_ppm_axis is not None),
                phase0_search_range_deg=12.0,
                phase0_search_steps=5,
                phase1_search_range_deg_per_ppm=3.0,
                phase1_search_steps=3,
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
            nonlinear_cfg,
            base_complex_vector=setup_complex,
            ppm_axis=setup_ppm_axis,
        )
        # Fortran STARTV/TWOREG handoff:
        # downstream reporting should use the refined (shift/linewidth-adjusted)
        # system, not the initial SETUP matrices.
        analysis_matrix = [list(row) for row in nonlinear.fit_matrix]
        analysis_vector = [float(v) for v in nonlinear.fit_vector]
        fit_matrix = [row[:] for row in analysis_matrix]
        fit_vector = [float(v) for v in analysis_vector]
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
            analysis_matrix,
            analysis_vector,
            stage.coefficients,
            baseline=stage.baseline,
        )
        plot_data_values = tuple(float(v) for v in analysis_vector)
        if ppm_axis is not None:
            plot_x_values = tuple(float(ppm_axis[i]) for i in setup.row_indices)
        else:
            plot_x_values = tuple(float(i) for i in range(len(analysis_vector)))
        baseline_for_plot: tuple[float, ...] = ()
        if stage.baseline and len(stage.baseline) >= len(analysis_vector):
            baseline_for_plot = tuple(float(v) for v in stage.baseline[: len(analysis_vector)])
        if baseline_for_plot:
            plot_fit_values = tuple(
                sum(float(analysis_matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                + float(baseline_for_plot[i])
                for i in range(len(analysis_vector))
            )
            plot_background_values = baseline_for_plot
        else:
            plot_fit_values = tuple(
                sum(float(analysis_matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                for i in range(len(analysis_vector))
            )
            plot_background_values = ()
        integrated_data_area, integrated_fit_area = self._compute_integration_areas(
            setup_vector=tuple(analysis_vector),
            plot_fit_values=plot_fit_values,
            ppm_axis=ppm_axis,
            row_indices=setup.row_indices,
        )
        phase0_total: float | None = phase0_deg
        phase1_total: float | None = phase1_deg_per_ppm
        if phase0_total is None:
            phase0_total = 0.0
        phase0_total = float(phase0_total) + float(nonlinear.phase0_deg)
        if phase1_total is None:
            phase1_total = 0.0
        phase1_total = float(phase1_total) + float(nonlinear.phase1_deg_per_ppm)

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
            plot_background_values=plot_background_values,
            corrected_time_domain=corrected_time_domain,
            phase0_deg=phase0_total,
            phase1_deg_per_ppm=phase1_total,
            alignment_shift_fractional_points=float(nonlinear.alignment_shift_fractional_points),
            filcor_phase0_deg=phase0_deg,
            filcor_phase1_deg_per_ppm=phase1_deg_per_ppm,
            filcor_shift_points=(
                float(nonlinear.alignment_shift_fractional_points)
                if abs(float(nonlinear.alignment_shift_fractional_points)) <= 2.0
                else 0.0
            ),
        )

    def _load_fit_system(
        self,
    ) -> tuple[
        list[list[float]],
        list[float],
        list[float] | None,
        list[str] | None,
        float | None,
        float | None,
        tuple[complex, ...],
        tuple[complex, ...] | None,
    ]:
        def _fortran_real(value: float) -> float:
            """Round through IEEE-754 single precision to mirror Fortran REAL."""

            return unpack("f", pack("f", float(value)))[0]

        basis_names: list[str] | None = None
        phase0_deg: float | None = None
        phase1_deg_per_ppm: float | None = None
        h2o_td: list[complex] | None = None
        corrected_time_domain: tuple[complex, ...] = ()
        frequency_domain_complex: tuple[complex, ...] | None = None
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
            if self.config.h2o_data_file:
                # Fortran MYDATA FILH2O path:
                # read non-water-suppressed time-domain data into H2OT.
                h2o_td = load_complex_vector(self.config.h2o_data_file)
            if self.config.unsupr and h2o_td is not None:
                # Fortran MYDATA UNSUPR:
                # use the unsuppressed signal as DATAT and disable ECC.
                raw_td = list(h2o_td[: len(raw_td)])
            if (
                self.config.doecc
                and h2o_td is not None
                and self.config.average_mode not in {3, 31, 32}
                and not self.config.unsupr
            ):
                # Fortran ECC_TRUNCATE:
                # apply Klose eddy-current phase correction in time domain.
                raw_td = apply_klose_ecc(raw_td, h2o_td)
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
            data_stage = run_mydata_stage(
                raw_td,
                MyDataConfig(
                    compute_fft=True,
                    auto_phase_zero_order=self.config.auto_phase_zero_order,
                    auto_phase_first_order=self.config.auto_phase_first_order,
                    phase_objective=self.config.phase_objective,
                    phase_smoothness_power=self.config.phase_smoothness_power,
                    dwell_time_s=self.config.dwell_time_s,
                    line_broadening_hz=self.config.line_broadening_hz,
                ),
            )
            if data_stage.frequency_domain is None:
                raise RuntimeError("MYDATA stage did not produce frequency domain data")
            corrected_time_domain = tuple(complex(v) for v in data_stage.time_domain)
            frequency_domain_complex = tuple(complex(v) for v in data_stage.frequency_domain)
            vector = [float(v.real) for v in frequency_domain_complex]
            if self.config.dows and h2o_td is not None:
                # Fortran WATER_SCALE:
                # compute FCALIB from water + metabolite reference areas.
                basis_reference = self._select_water_reference_spectrum(matrix, basis_names)
                fcalib = compute_water_scale_factor(
                    h2o_td=h2o_td,
                    basis_reference_frequency=basis_reference,
                    nunfil=self.config.nunfil if self.config.nunfil > 0 else len(raw_td),
                    dwell_time_s=self.config.dwell_time_s,
                    hzpppm=self.config.hzpppm,
                    config=WaterReferenceConfig(
                        iaverg=self.config.average_mode,
                        iareaw=self.config.iareaw,
                        nwsst=self.config.nwsst,
                        nwsend=self.config.nwsend,
                        atth2o=self.config.atth2o,
                        wconc=self.config.wconc,
                        ppmh2o=self.config.ppmh2o,
                        hwdwat=self.config.hwdwat,
                        ppmbas=self.config.ppmbas,
                        wsppm=self.config.wsppm,
                        rfwbas=self.config.rfwbas,
                        fwhmba=self.config.fwhmba,
                        n1hmet=self.config.n1hmet,
                        attmet=self.config.attmet,
                    ),
                )
                if fcalib is not None and fcalib > 0.0:
                    vector = [float(v) * float(fcalib) for v in vector]
                    if frequency_domain_complex is not None:
                        frequency_domain_complex = tuple(
                            complex(v) * float(fcalib) for v in frequency_domain_complex
                        )
            if data_stage.zero_order_phase_radians is not None:
                # Python phasing rotates spectrum by exp(-i*phi); Fortran REPHAS/
                # FINOUT conventions store +phi, so negate for FILCOR-style export.
                phase0_deg = -float(data_stage.zero_order_phase_radians) * (180.0 / 3.141592653589793)
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
            # Fortran INITIA:
            # PPMINC is formed in REAL precision and PPM(JY) is updated by
            # iterative subtraction (PPM(JY)=PPM(JY-1)-PPMINC). Matching this
            # avoids small cumulative drift vs a direct double-precision formula.
            fndata = _fortran_real(float(2 * self.config.nunfil))
            ppminc = _fortran_real(float(self.config.dwell_time_s))
            ppminc = _fortran_real(ppminc * fndata)
            ppminc = _fortran_real(ppminc * _fortran_real(float(self.config.hzpppm)))
            ppminc = _fortran_real(1.0 / ppminc)
            ppm_axis = []
            ppm_value = _fortran_real(4.0)
            for idx in range(len(vector)):
                if idx > 0:
                    ppm_value = _fortran_real(ppm_value - ppminc)
                ppm_axis.append(float(ppm_value))
        return (
            matrix,
            vector,
            ppm_axis,
            basis_names,
            phase0_deg,
            phase1_deg_per_ppm,
            corrected_time_domain,
            frequency_domain_complex,
        )

    def _select_water_reference_spectrum(
        self,
        matrix: list[list[float]],
        basis_names: list[str] | None,
    ) -> list[float]:
        # Fortran WSMET behavior:
        # select metabolite reference spectrum used by AREABA (default Cr).
        if not matrix:
            return []
        ncols = len(matrix[0])
        if ncols <= 0:
            return []
        target = str(self.config.wsmet).strip().lower()
        index = 0
        if basis_names:
            for j, name in enumerate(basis_names):
                if str(name).strip().lower() == target:
                    index = j
                    break
            else:
                for j, name in enumerate(basis_names):
                    if str(name).strip().lower().startswith(target):
                        index = j
                        break
        index = max(0, min(index, ncols - 1))
        return [float(row[index]) for row in matrix]

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
