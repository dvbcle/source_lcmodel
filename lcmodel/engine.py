"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from lcmodel.io.basis import load_basis_names
from lcmodel.io.numeric import load_numeric_matrix, load_numeric_vector
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.models import FitResult, RunConfig, RunResult
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
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
            stage = run_fit_stage(
                setup.matrix,
                setup.vector,
                FitConfig(baseline_order=self.config.baseline_order),
            )
            fit_result = FitResult(
                coefficients=stage.coefficients,
                residual_norm=stage.residual_norm,
                iterations=stage.iterations,
                method=stage.method,
                metabolite_names=setup.metabolite_names,
                data_points_used=len(setup.vector),
            )

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
        )
