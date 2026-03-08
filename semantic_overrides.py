"""Semantic routine bindings for the auto-generated Fortran scaffold."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any, Sequence

from lcmodel.core.array_ops import reverse_first_n
from lcmodel.core.axis import round_axis_endpoints
from lcmodel.core.fftpack_compat import (
    cfft_r as cfft_r_compat,
    cfftin_r as cfftin_r_compat,
    csft_r as csft_r_compat,
    csftin_r as csftin_r_compat,
    fftci as fftci_compat,
    seqtot as seqtot_compat,
)
from lcmodel.core.text import int_to_compact_text, split_title_lines
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage
from lcmodel.pipeline.postprocess import compute_combinations


def _assign_vector(target: Any, values: Sequence[complex]) -> None:
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(values))
        for i in range(limit):
            target[i] = values[i]


def _ov_split_filename(
    filename: str,
    chtype1: str,
    chtype2: str,
    chtype3: str,
    lchtype: int,
    split: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    left, right = split_output_filename_for_voxel(
        str(filename),
        (str(chtype1)[: int(lchtype)], str(chtype2)[: int(lchtype)], str(chtype3)[: int(lchtype)]),
    )
    if isinstance(split, MutableSequence) and len(split) >= 2:
        split[0] = left
        split[1] = right
    out["split"] = (left, right)
    return out


def _ov_chstrip_int6(
    iarg: int, chi: Any, leni: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    text = int_to_compact_text(int(iarg))
    if isinstance(chi, MutableSequence) and len(chi) >= 1:
        chi[0] = text
    if isinstance(leni, MutableSequence) and len(leni) >= 1:
        leni[0] = len(text)
    out["chi"] = text
    out["leni"] = len(text)
    return out


def _ov_split_title(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    title = str(out.get("title", ""))
    ntitle = int(out.get("ntitle", 2))
    layout = split_title_lines(title, ntitle=ntitle)
    out["title_line_1"] = layout.lines[0]
    out["title_line_2"] = layout.lines[1]
    out["nlines_title"] = layout.line_count
    return out


def _ov_revers(x: Any, n: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if isinstance(x, MutableSequence):
        reverse_first_n(x, int(n))
    out["reversed_n"] = int(n)
    return out


def _ov_endrnd(
    xmn: float,
    xmx: float,
    xstep: float,
    xinc: float,
    xmnrnd: Any,
    xmxrnd: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    x_low, x_high = round_axis_endpoints(float(xmn), float(xmx), float(xstep), float(xinc))
    if isinstance(xmnrnd, MutableSequence) and len(xmnrnd) >= 1:
        xmnrnd[0] = x_low
    if isinstance(xmxrnd, MutableSequence) and len(xmxrnd) >= 1:
        xmxrnd[0] = x_high
    out["xmnrnd"] = x_low
    out["xmxrnd"] = x_high
    return out


def _ov_integrate(
    dataf: Sequence[complex | float],
    ppminc2: float,
    rinteg: Any,
    kyend: int,
    kystrt: int,
    ly: int,
    nunfil: int,
    nwndo: int,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    values = [float(v.real) if isinstance(v, complex) else float(v) for v in dataf]
    if not values:
        out["rinteg"] = 0.0
        return out
    start = max(0, int(kystrt) - 1)
    end = min(len(values) - 1, int(kyend) - 1)
    peak = min(max(0, int(ly) - 1), len(values) - 1)
    border = max(1, int(nwndo))
    spacing = abs(float(ppminc2)) if float(ppminc2) != 0.0 else 1.0
    result = integrate_peak_with_local_baseline(
        values,
        peak_index=peak,
        start_index=start,
        end_index=end,
        border_width=border,
        spacing=spacing,
    )
    if isinstance(rinteg, MutableSequence) and len(rinteg) >= 1:
        rinteg[0] = float(result.area)
    out["rinteg"] = float(result.area)
    out["nunfil"] = int(nunfil)
    return out


def _ov_combis(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    expressions = tuple(str(x) for x in out.get("combine_expressions", ()))
    coeffs = tuple(float(x) for x in out.get("coefficients", ()))
    sds = tuple(float(x) for x in out.get("coefficient_sds", ()))
    names = tuple(str(x) for x in out.get("metabolite_names", ()))
    out["combined"] = compute_combinations(expressions, coeffs, sds, names)
    return out


def _ov_mydata(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    raw_time = out.get("raw_time")
    if raw_time is None:
        return out
    stage = run_mydata_stage(
        raw_time,
        MyDataConfig(
            compute_fft=bool(out.get("compute_fft", True)),
            auto_phase_zero_order=bool(out.get("auto_phase_zero_order", False)),
            auto_phase_first_order=bool(out.get("auto_phase_first_order", False)),
            phase_objective=str(out.get("phase_objective", "imag_abs")),
            phase_smoothness_power=int(out.get("phase_smoothness_power", 6)),
            dwell_time_s=float(out.get("dwell_time_s", 0.0)),
            line_broadening_hz=float(out.get("line_broadening_hz", 0.0)),
        ),
    )
    out["mydata_stage"] = stage
    if stage.frequency_domain is not None:
        out["dataf"] = stage.frequency_domain
    return out


def _ov_csft_r(
    datat: Sequence[complex], ft: Any, ncap: int, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = csft_r_compat(datat, ncap=ncap)
    _assign_vector(ft, vals)
    out["ft"] = tuple(vals)
    return out


def _ov_csftin_r(
    ft: Sequence[complex],
    ftwork: Any,
    ftinv: Any,
    ncap: int,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = csftin_r_compat(ft, ncap=ncap)
    _assign_vector(ftinv, vals)
    out["ftinv"] = tuple(vals)
    return out


def _ov_seqtot(
    datat: Sequence[complex],
    dataf: Any,
    nunfil: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = seqtot_compat(datat)
    _assign_vector(dataf, vals)
    out["dataf"] = tuple(vals)
    out["nunfil"] = int(nunfil)
    out["lwfft"] = int(lwfft)
    return out


def _ov_cfftin(
    ft: Sequence[complex],
    ftinv: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = cfftin_r_compat(ft)
    _assign_vector(ftinv, vals)
    out["ftinv"] = tuple(vals)
    out["n"] = int(n)
    return out


def _ov_cfftin_r(
    ft: Sequence[complex],
    ftwork: Any,
    ftinv: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_cfftin(ft, ftinv, n, lwfft, wfftc, state)


def _ov_cfft(
    datat: Sequence[complex],
    ft: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = cfft_r_compat(datat)
    _assign_vector(ft, vals)
    out["ft"] = tuple(vals)
    out["n"] = int(n)
    return out


def _ov_cfft_r(
    datat: Sequence[complex],
    ft: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_cfft(datat, ft, n, lwfft, wfftc, state)


def _ov_fftci(n: int, wsave: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    plan = fftci_compat(int(n))
    out["fft_plan"] = plan
    out["n"] = int(n)
    if isinstance(wsave, MutableSequence) and len(wsave) >= 1:
        wsave[0] = complex(1.0, 0.0)
    return out


SEMANTIC_OVERRIDES = {
    "split_filename": _ov_split_filename,
    "chstrip_int6": _ov_chstrip_int6,
    "split_title": _ov_split_title,
    "revers": _ov_revers,
    "endrnd": _ov_endrnd,
    "integrate": _ov_integrate,
    "combis": _ov_combis,
    "mydata": _ov_mydata,
    "csft_r": _ov_csft_r,
    "csftin_r": _ov_csftin_r,
    "seqtot": _ov_seqtot,
    "cfftin": _ov_cfftin,
    "cfftin_r": _ov_cfftin_r,
    "cfft": _ov_cfft,
    "cfft_r": _ov_cfft_r,
    "fftci": _ov_fftci,
    "dfftci": _ov_fftci,
}
