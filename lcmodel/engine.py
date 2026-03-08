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
from lcmodel.pipeline.alignment import align_vector_by_integer_shift
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
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
                basis_names=basis_names,
                include_metabolites=self.config.include_metabolites,
            )
            alignment = align_vector_by_integer_shift(
                setup.matrix,
                setup.vector,
                self.config.shift_search_points,
            )
            fit_matrix = [list(row) for row in setup.matrix]
            fit_vector = list(alignment.vector)
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
                FitConfig(baseline_order=self.config.baseline_order),
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
                alignment_shift_points=alignment.shift_points,
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
