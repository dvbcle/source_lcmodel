from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleLayout:
    """Layout decision for a report title."""

    lines: tuple[str, str]
    line_count: int


@dataclass(frozen=True)
class RunConfig:
    """High-level inputs for a Python LCModel run."""

    title: str = ""
    ntitle: int = 2
    output_filename: str | None = None
    raw_data_file: str | None = None
    basis_file: str | None = None
    baseline_order: int = -1


@dataclass(frozen=True)
class FitResult:
    """Linear nonnegative fit output for the current semantic stage."""

    coefficients: tuple[float, ...]
    residual_norm: float
    iterations: int
    method: str


@dataclass(frozen=True)
class RunResult:
    """Portable run metadata from the current semantic port scope."""

    title_layout: TitleLayout
    output_filename_parts: tuple[str, str] | None
    fit_result: FitResult | None = None
