"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from dataclasses import replace
from lcmodel.io.batch import load_path_list, write_batch_csv
from lcmodel.io.basis import load_basis_names
from lcmodel.io.numeric import (
    load_complex_matrix,
    load_complex_vector,
    load_numeric_matrix,
    load_numeric_vector,
)
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.io.priors import load_soft_priors
from lcmodel.io.report import write_fit_table
from lcmodel.models import BatchRunResult, FitResult, RunConfig, RunResult
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
from lcmodel.pipeline.nonlinear import NonlinearConfig, run_nonlinear_refinement
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.setup import prepare_fit_inputs
from lcmodel.core.text import split_title_lines


class LCModelRunner:
    """High-level runner for incremental semantic-port behavior."""

    def __init__(self, config: RunConfig):
        self.config = config

    def run(self) -> RunResult:
        """Execute currently ported preprocessing behaviors."""

        title_layout = split_title_lines(self.config.title, self.config.ntitle)
        filename_parts: tuple[str, str] | None = None
        if self.config.output_filename:
            filename_parts = split_output_filename_for_voxel(
                self.config.output_filename, ("ps", "PS", "Ps")
            )

        fit_result: FitResult | None = None
        if self.config.raw_data_file and self.config.basis_file:
            if self.config.time_domain_input:
                raw_td = load_complex_vector(self.config.raw_data_file)
                basis_td = load_complex_matrix(self.config.basis_file, pair_mode=True)
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
            basis_names = None
            if self.config.basis_names_file:
                basis_names = load_basis_names(self.config.basis_names_file)

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
                priors = load_soft_priors(self.config.priors_file)
                fit_matrix, fit_vector = augment_system_with_soft_priors(
                    fit_matrix,
                    fit_vector,
                    setup.metabolite_names,
                    priors,
                )
            stage = run_fit_stage(
                fit_matrix,
                fit_vector,
                FitConfig(
                    baseline_order=self.config.baseline_order,
                    baseline_knots=self.config.baseline_knots,
                    baseline_smoothness=self.config.baseline_smoothness,
                ),
            )
            combined = compute_combinations(
                self.config.combine_expressions,
                stage.coefficients,
                stage.coefficient_sds,
                setup.metabolite_names,
            )
            relative_residual, snr_estimate = compute_fit_quality_metrics(
                setup.matrix,
                setup.vector,
                stage.coefficients,
            )
            integrated_data_area = 0.0
            integrated_fit_area = 0.0
            if setup.vector:
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
                fit_curve = [
                    sum(float(setup.matrix[i][j]) * float(stage.coefficients[j]) for j in range(len(stage.coefficients)))
                    for i in range(len(setup.vector))
                ]
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
                        fit_curve,
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

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
            table_output_file=table_written,
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
