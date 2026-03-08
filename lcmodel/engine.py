"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from lcmodel.io.numeric import load_numeric_matrix, load_numeric_vector
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.models import FitResult, RunConfig, RunResult
from lcmodel.pipeline.fitting import run_fit_stage
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
            stage = run_fit_stage(matrix, vector)
            fit_result = FitResult(
                coefficients=stage.coefficients,
                residual_norm=stage.residual_norm,
                iterations=stage.iterations,
                method=stage.method,
            )

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
            fit_result=fit_result,
        )
