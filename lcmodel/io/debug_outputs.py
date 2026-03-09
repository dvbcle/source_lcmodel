"""Writers for Fortran-style intermediate debug outputs (FILCOO/FILCOR analogs)."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from lcmodel.models import FitResult


def _chunked(values: Sequence[float], width: int) -> list[list[float]]:
    out: list[list[float]] = []
    for i in range(0, len(values), width):
        out.append([float(v) for v in values[i : i + width]])
    return out


def _fmt_axis_row(values: Sequence[float]) -> str:
    return "".join(f"{float(v):13.6f}" for v in values)


def _fmt_data_row(values: Sequence[float]) -> str:
    return "".join(f"{float(v):13.5E}" for v in values)


def _write_numeric_block(lines: list[str], values: Sequence[float], *, kind: str) -> None:
    chunks = _chunked(values, 10)
    for row in chunks:
        if kind == "axis":
            lines.append(_fmt_axis_row(row))
        else:
            lines.append(_fmt_data_row(row))


def _find_reference_concentration(fit_result: FitResult) -> float:
    ref = 0.0
    for name, value, _sd in fit_result.combined:
        if str(name).strip().lower() == "cr+pcr":
            ref = abs(float(value))
            break
    if ref > 0.0:
        return ref
    for name, value in zip(fit_result.metabolite_names, fit_result.coefficients):
        if str(name).strip().lower() in {"cr", "pcr"}:
            ref += max(0.0, float(value))
    if ref > 0.0:
        return ref
    return max(1.0e-20, max((abs(float(v)) for v in fit_result.coefficients), default=1.0))


def write_coordinate_debug_file(
    path: str | Path,
    *,
    fit_result: FitResult,
    ppm_values: Sequence[float],
    phased_data_values: Sequence[float],
    fit_values: Sequence[float],
    background_values: Sequence[float] | None = None,
    phase0_deg: float | None = None,
    phase1_deg_per_ppm: float | None = None,
) -> str:
    """Write a compact Fortran-style debug coordinate dump.

    Sections intentionally mirror LCModel `FILCOO` markers so comparison tools
    can align Python and Fortran intermediate arrays.
    """

    p = Path(path)
    lines: list[str] = []
    lines.append(" LCModel Python debug coordinate output")
    lines.append(" ")

    nconc = len(fit_result.metabolite_names) + len(fit_result.combined)
    lines.append(f" {nconc + 1:2d} lines in following concentration table = NCONC+1")
    lines.append("    Conc.  %SD /Cr+PCr  Metabolite")
    ref = _find_reference_concentration(fit_result)
    for idx, name in enumerate(fit_result.metabolite_names):
        conc = float(fit_result.coefficients[idx])
        sd = float(fit_result.coefficient_sds[idx]) if idx < len(fit_result.coefficient_sds) else 0.0
        psd = 999.0 if abs(conc) <= 1.0e-20 else min(999.0, 100.0 * abs(sd / conc))
        ratio = conc / ref if ref > 0.0 else 0.0
        lines.append(f" {conc:8.2E} {psd:4.0f}% {ratio:8.1E} {name:<52.52s}")
    for name, value, sd in fit_result.combined:
        conc = float(value)
        psd = 999.0 if abs(conc) <= 1.0e-20 else min(999.0, 100.0 * abs(float(sd) / conc))
        ratio = conc / ref if ref > 0.0 else 0.0
        lines.append(f" {conc:8.2E} {psd:4.0f}% {ratio:8.1E} {str(name):<52.52s}")

    lines.append("   6 lines in following misc. output table")
    lines.append(f"  FWHM = {float(fit_result.linewidth_sigma_points):.3f} ppm    S/N = {float(fit_result.snr_estimate):3.0f}")
    lines.append(f"  Data shift = {float(fit_result.alignment_shift_fractional_points):.3f} ppm")
    p0 = 0.0 if phase0_deg is None else float(phase0_deg)
    p1 = 0.0 if phase1_deg_per_ppm is None else float(phase1_deg_per_ppm)
    lines.append(f"  Ph: {p0:3.0f} deg       {p1:.1f} deg/ppm")
    lines.append("  alphaB,S = n/a,   n/a")
    lines.append("   0 spline knots.   Ns = 0(0)")
    lines.append("   0 inflections.     0 extrema")

    n = len(ppm_values)
    lines.append(f" {n:4d} points on ppm-axis = NY")
    _write_numeric_block(lines, ppm_values, kind="axis")
    lines.append(" NY phased data points follow")
    _write_numeric_block(lines, phased_data_values, kind="data")
    lines.append(" NY points of the fit to the data follow")
    _write_numeric_block(lines, fit_values, kind="data")
    if background_values is not None and len(background_values) == len(phased_data_values):
        lines.append(" NY points of background values follow")
        _write_numeric_block(lines, background_values, kind="data")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def write_corrected_raw_file(
    path: str | Path,
    *,
    corrected_time_domain: Sequence[complex],
    hzpppm: float,
) -> str:
    """Write corrected time-domain RAW output (FILCOR analog)."""

    p = Path(path)
    lines: list[str] = []
    lines.append("&SEQPAR")
    lines.append(f" HZPPPM={float(hzpppm):13.6f}    ,")
    lines.append(" /")
    lines.append("&NMID")
    lines.append(" BRUKER=F,")
    lines.append(" FMTDAT=\"(2e15.6)                                                                        \",")
    lines.append(" ID=\"FILCOR              \",")
    lines.append(" SEQACQ=F,")
    lines.append(" TRAMP=  1.00000000    ,")
    lines.append(" VOLUME=  1.00000000    ,")
    lines.append(" /")
    for value in corrected_time_domain:
        z = complex(value)
        lines.append(f"{float(z.real):15.6E}{float(z.imag):15.6E}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)

