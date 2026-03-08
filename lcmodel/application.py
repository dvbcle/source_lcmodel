"""Stable application-facing API for LCModel runtime execution.

This module defines the canonical Python entry points for single-run and batch
execution. It keeps CLI and programmatic callers on the same product surface
while leaving the `LCModelRunner` class available for advanced orchestration.
"""

from __future__ import annotations

from lcmodel.engine import LCModelRunner
from lcmodel.models import BatchRunResult, RunConfig, RunResult


def run_lcmodel(config: RunConfig) -> RunResult:
    """Run one LCModel analysis using the configured runtime pipeline."""

    return LCModelRunner(config).run()


def run_lcmodel_batch(config: RunConfig) -> BatchRunResult:
    """Run batch LCModel analysis for all entries in `raw_data_list_file`."""

    return LCModelRunner(config).run_batch()


__all__ = ["run_lcmodel", "run_lcmodel_batch"]
