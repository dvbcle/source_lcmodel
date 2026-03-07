"""Python-first orchestration layer for the LCModel port."""

from __future__ import annotations

from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.models import RunConfig, RunResult
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

        return RunResult(
            title_layout=title_layout,
            output_filename_parts=filename_parts,
        )

