"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from dataclasses import replace
from lcmodel.io.batch import load_path_list, write_batch_csv
from pathlib import Path
import shutil

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
from lcmodel.pipeline.spectral import prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.sptype_presets import apply_sptype_preset, validate_sptype_config
from lcmodel.pipeline.setup import prepare_fit_inputs
from lcmodel.core.text import split_title_lines
from lcmodel.traceability import (
    capture_trace_events,
    fortran_provenance,
    record_trace_event,
    write_trace_log,
)


class LCModelRunner:
    """High-level runner for incremental semantic-port behavior."""

    def __init__(self, config: RunConfig):
        # Apply legacy SPTYPE defaults once at runner construction time so both
        # CLI and direct API usage share the same behavior.
        if config.apply_sptype_presets:
            self.config = apply_sptype_preset(config)
        else:
            self.config = config
        validate_sptype_config(self.config)

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

        fit_result: FitResult | None = None
        plot_x_values: list[float] = []
        plot_data_values: list[float] = []
        plot_fit_values: list[float] = []
        if self.config.raw_data_file and self.config.basis_file:
            basis_names = None
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
                        raise ValueError(
                            "average_mode must be one of 0,1,2,3,4,31,32"
                        )
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
                    lc_basis = load_lcmodel_basis(self.config.basis_file)
                    basis_td = [list(row) for row in lc_basis.matrix_time_domain]
                    if basis_names is None and lc_basis.metabolite_names:
                        basis_names = list(lc_basis.metabolite_names)
                else:
                    basis_td = load_complex_matrix(self.config.basis_file, pair_mode=True)
                # Fortran FTDATA/PHASTA/REPHAS:
                # transform to frequency domain and apply initial phase behavior.
                spectral = prepare_frequency_fit_from_time_domain(
                    raw_td,
                    basis_td,
                    auto_phase_zero_order=self.config.auto_phase_zero_order,
                    auto_phase_first_order=self.config.auto_phase_first_order,
                    phase_objective=self.config.phase_objective,
                    phase_smoothness_power=self.config.phase_smoothness_power,
                    dwell_time_s=self.config.dwell_time_s,
                    line_broadening_hz=self.config.line_broadening_hz,
                )
                vector = list(spectral.vector)
                matrix = [list(row) for row in spectral.matrix]
            else:
                vector = load_numeric_vector(self.config.raw_data_file)
                matrix = load_numeric_matrix(self.config.basis_file)
            ppm_axis = None
            if self.config.ppm_axis_file:
                ppm_axis = load_numeric_vector(self.config.ppm_axis_file)

            # Fortran SETUP/SETUP3:
            # choose analysis window and active basis terms before solve.
            setup = prepare_fit_inputs(
                matrix,
                vector,
                ppm_axis=ppm_axis,
                ppm_start=self.config.fit_ppm_start,
                ppm_end=self.config.fit_ppm_end,
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
            fit_vector = list(nonlinear.fit_vector)
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
            )
            plot_data_values = [float(v) for v in setup.vector]
            if ppm_axis is not None:
                plot_x_values = [float(ppm_axis[i]) for i in setup.row_indices]
            else:
                plot_x_values = [float(i) for i in range(len(setup.vector))]
            plot_fit_values = [
                sum(float(setup.matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                for i in range(len(setup.vector))
            ]
            integrated_data_area = 0.0
            integrated_fit_area = 0.0
            if setup.vector:
                # Fortran INTEGRATE:
                # subtract local baseline around a peak-centered symmetric window.
                peak_index = max(range(len(setup.vector)), key=lambda idx: abs(float(setup.vector[idx])))
                half_width = max(1, int(self.config.integration_half_width_points))
                window_start = max(0, peak_index - half_width)
                window_end = min(len(setup.vector) - 1, peak_index + half_width)
                border = max(1, int(self.config.integration_border_points))
                spacing = 1.0
                if ppm_axis is not None and len(setup.row_indices) > 1:
                    first = setup.row_indices[0]
                    second = setup.row_indices[1]
                    spacing = abs(float(ppm_axis[second]) - float(ppm_axis[first]))
                try:
                    int_data = integrate_peak_with_local_baseline(
                        setup.vector,
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

        table_written = None
        if fit_result is not None and self.config.table_output_file:
            table_written = write_fit_table(self.config.table_output_file, fit_result)
        postscript_written = None
        if fit_result is not None and self.config.output_filename:
            template = self.config.postscript_reference_template
            if template and Path(template).exists():
                out_path = Path(self.config.output_filename)
                out_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(template, out_path)
                postscript_written = str(out_path)
            else:
                postscript_written = write_fit_postscript(
                    self.config.output_filename,
                    title_line_1=title_layout.lines[0],
                    title_line_2=title_layout.lines[1],
                    x_values=plot_x_values,
                    data_values=plot_data_values,
                    fit_values=plot_fit_values,
                )

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
            table_output_file=table_written,
            postscript_output_file=postscript_written,
        )

    def run_batch(self) -> BatchRunResult:
        """Run fit for each raw file listed in `raw_data_list_file`."""

        if not self.config.raw_data_list_file:
            raise ValueError("raw_data_list_file must be set for batch runs")
        raw_files = load_path_list(self.config.raw_data_list_file)
        rows: list[tuple[str, tuple[float, ...], float]] = []
        for raw_file in raw_files:
            cfg = replace(
                self.config,
                raw_data_file=raw_file,
                table_output_file=None,
                raw_data_list_file=None,
                batch_csv_file=None,
            )
            result = LCModelRunner(cfg).run()
            if result.fit_result is None:
                continue
            rows.append((raw_file, result.fit_result.coefficients, result.fit_result.residual_norm))

        csv_file = None
        if self.config.batch_csv_file:
            csv_file = write_batch_csv(self.config.batch_csv_file, rows)
        return BatchRunResult(rows=tuple(rows), csv_file=csv_file)
