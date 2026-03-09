"""Parsers and comparison helpers for Fortran/Python debug intermediate outputs."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re
from typing import Sequence

from lcmodel.validation.oracle import compare_numeric_vectors, NumericComparisonResult


_FLOAT_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?")


@dataclass(frozen=True)
class DebugCooData:
    ppm_axis: tuple[float, ...]
    phased_data: tuple[float, ...]
    fit_data: tuple[float, ...]
    background_data: tuple[float, ...] = ()


@dataclass(frozen=True)
class DebugCorData:
    values: tuple[complex, ...]


@dataclass(frozen=True)
class DebugComparisonRow:
    section: str
    compared_points: int
    match: bool
    max_abs_error: float
    rms_error: float
    message: str


@dataclass(frozen=True)
class DebugComparisonTable:
    rows: tuple[DebugComparisonRow, ...]


def _parse_float_tokens(lines: Sequence[str]) -> list[float]:
    out: list[float] = []
    for line in lines:
        for token in _FLOAT_RE.findall(line):
            out.append(float(token.replace("D", "E").replace("d", "e")))
    return out


def parse_debug_coo(path: str | Path) -> DebugCooData:
    """Parse key numeric sections from Fortran/Python coordinate debug output."""

    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    n = 0
    ppm_start = None
    phased_start = None
    fit_start = None
    back_start = None
    for idx, line in enumerate(lines):
        m = re.search(r"(\d+)\s+points on ppm-axis\s*=\s*NY", line, flags=re.IGNORECASE)
        if m:
            n = int(m.group(1))
            ppm_start = idx + 1
            continue
        if "NY phased data points follow" in line:
            phased_start = idx + 1
            continue
        if "NY points of the fit to the data follow" in line:
            fit_start = idx + 1
            continue
        if "NY points of background values follow" in line:
            back_start = idx + 1
            continue
    if n <= 0 or ppm_start is None or phased_start is None or fit_start is None:
        raise ValueError(f"Could not parse required debug.coo sections from {path}")

    def _section(start: int, end: int) -> tuple[float, ...]:
        vals = _parse_float_tokens(lines[start:end])
        return tuple(float(v) for v in vals[:n])

    ppm_end = phased_start - 1
    phased_end = fit_start - 1
    fit_end = back_start - 1 if back_start is not None else len(lines)
    ppm = _section(ppm_start, ppm_end)
    phased = _section(phased_start, phased_end)
    fit = _section(fit_start, fit_end)
    back: tuple[float, ...] = ()
    if back_start is not None:
        back = _section(back_start, len(lines))
    return DebugCooData(ppm_axis=ppm, phased_data=phased, fit_data=fit, background_data=back)


def parse_debug_cor(path: str | Path) -> DebugCorData:
    """Parse complex time-domain samples from FILCOR-like text output."""

    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    values: list[complex] = []
    for line in lines:
        if "&" in line or "=" in line or line.strip().startswith("/"):
            continue
        nums = _parse_float_tokens([line])
        if len(nums) >= 2:
            values.append(complex(float(nums[0]), float(nums[1])))
    if not values:
        raise ValueError(f"No complex data rows parsed from {path}")
    return DebugCorData(values=tuple(values))


def _cmp(label: str, expected: Sequence[float], actual: Sequence[float]) -> DebugComparisonRow:
    cmp_result: NumericComparisonResult = compare_numeric_vectors(
        expected, actual, abs_tol=1.0e-6, rel_tol=1.0e-6
    )
    return DebugComparisonRow(
        section=label,
        compared_points=cmp_result.compared_points,
        match=cmp_result.match,
        max_abs_error=cmp_result.max_abs_error,
        rms_error=cmp_result.rms_error,
        message=cmp_result.message,
    )


def compare_debug_outputs(
    fortran_coo: DebugCooData,
    python_coo: DebugCooData,
    *,
    fortran_cor: DebugCorData | None = None,
    python_cor: DebugCorData | None = None,
) -> DebugComparisonTable:
    rows: list[DebugComparisonRow] = []
    rows.append(_cmp("coo.ppm_axis", fortran_coo.ppm_axis, python_coo.ppm_axis))
    rows.append(_cmp("coo.phased_data", fortran_coo.phased_data, python_coo.phased_data))
    rows.append(_cmp("coo.fit_data", fortran_coo.fit_data, python_coo.fit_data))
    if fortran_coo.background_data and python_coo.background_data:
        rows.append(
            _cmp(
                "coo.background_data",
                fortran_coo.background_data,
                python_coo.background_data,
            )
        )
    if fortran_cor is not None and python_cor is not None:
        fr = [float(v.real) for v in fortran_cor.values]
        pr = [float(v.real) for v in python_cor.values]
        fi = [float(v.imag) for v in fortran_cor.values]
        pi = [float(v.imag) for v in python_cor.values]
        fa = [math.hypot(float(v.real), float(v.imag)) for v in fortran_cor.values]
        pa = [math.hypot(float(v.real), float(v.imag)) for v in python_cor.values]
        rows.append(_cmp("cor.real", fr, pr))
        rows.append(_cmp("cor.imag", fi, pi))
        rows.append(_cmp("cor.abs", fa, pa))
    return DebugComparisonTable(rows=tuple(rows))


def render_markdown_table(table: DebugComparisonTable) -> str:
    lines = []
    lines.append("| Section | Points | Match | Max Abs Error | RMS Error | Message |")
    lines.append("|---|---:|:---:|---:|---:|---|")
    for row in table.rows:
        lines.append(
            "| "
            f"{row.section} | {row.compared_points} | "
            f"{'Y' if row.match else 'N'} | "
            f"{row.max_abs_error:.12g} | {row.rms_error:.12g} | {row.message} |"
        )
    return "\n".join(lines) + "\n"

