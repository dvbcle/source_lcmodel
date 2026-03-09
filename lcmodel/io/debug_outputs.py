"""Writers for Fortran-style intermediate debug outputs (FILCOO/FILCOR analogs)."""

from __future__ import annotations

import cmath
import math
from pathlib import Path
from typing import Sequence

from lcmodel.core.fftpack_compat import cfft_r, cfftin_r
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
    nunfil: int | None = None,
    dwell_time_s: float | None = None,
    phase0_deg: float | None = None,
    phase1_deg_per_ppm: float | None = None,
    shift_points: float | None = None,
) -> str:
    """Write corrected time-domain RAW output (FILCOR analog)."""

    p = Path(path)
    corrected = _apply_finout_like_corrections(
        corrected_time_domain,
        nunfil=nunfil,
        dwell_time_s=dwell_time_s,
        hzpppm=hzpppm,
        phase0_deg=phase0_deg,
        phase1_deg_per_ppm=phase1_deg_per_ppm,
        shift_points=shift_points,
    )
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
    for value in corrected:
        z = complex(value)
        lines.append(f"{float(z.real):15.6E}{float(z.imag):15.6E}")
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(p)


def _apply_finout_like_corrections(
    time_domain: Sequence[complex],
    *,
    nunfil: int | None,
    dwell_time_s: float | None,
    hzpppm: float,
    phase0_deg: float | None,
    phase1_deg_per_ppm: float | None,
    shift_points: float | None,
) -> tuple[complex, ...]:
    """Apply FINOUT-style phase/shift corrections before writing FILCOR.

    Fortran FINOUT flow:
    1) apply zero-order phase + shift ramp in time domain
    2) zero-fill to `2*NUNFIL` and FFT (`CFFT_r`)
    3) apply first-order phase in ppm domain
    4) inverse FFT (`CFFTIN_r` equivalent) and emit first `NUNFIL` points
    """

    n = int(nunfil) if nunfil is not None and int(nunfil) > 0 else len(time_domain)
    if n <= 0:
        return ()

    datat = [complex(v) for v in time_domain[:n]]
    if len(datat) < n:
        datat.extend([0j] * (n - len(datat)))

    rad = math.pi / 180.0
    phase0 = float(phase0_deg) if phase0_deg is not None else 0.0
    phase1 = float(phase1_deg_per_ppm) if phase1_deg_per_ppm is not None else 0.0
    dwell = float(dwell_time_s) if dwell_time_s is not None else 0.0

    shift_ppm = 0.0
    ppminc = 0.0
    if n > 0 and dwell > 0.0 and float(hzpppm) > 0.0:
        ppminc = 1.0 / (dwell * float(2 * n) * float(hzpppm))
        shift_ppm = float(shift_points) * ppminc if shift_points is not None else 0.0

    cterm = cmath.exp(1j * rad * phase0)
    cfactor = cmath.exp(1j * (-2.0 * math.pi * float(hzpppm) * dwell * shift_ppm))
    for idx in range(n):
        datat[idx] *= cterm
        cterm *= cfactor

    ndata = 2 * n
    datat.extend([0j] * n)
    dataf = list(cfft_r(datat))

    if phase1 != 0.0 and ppminc > 0.0:
        delta_ppm = float(n) * ppminc
        for idx in range(ndata):
            dataf[idx] *= cmath.exp(1j * rad * delta_ppm * phase1)
            delta_ppm -= ppminc

    corrected = cfftin_r(dataf)
    return tuple(corrected[:n])
