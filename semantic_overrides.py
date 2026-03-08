"""Semantic routine bindings for the auto-generated Fortran scaffold."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any, Sequence
import builtins
import math
import pathlib
import re

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
from lcmodel.core.fortran_compat import ilen as ilen_compat
from lcmodel.core.text import int_to_compact_text, split_title_lines
from lcmodel.core.text import escape_postscript_text, first_non_space_index
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.pipeline.averaging import (
    detect_zero_voxels,
    estimate_tail_variance,
    weighted_average_channels,
)
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage
from lcmodel.pipeline.postprocess import compute_combinations


def _assign_vector(target: Any, values: Sequence[complex]) -> None:
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(values))
        for i in range(limit):
            target[i] = values[i]


def _ov_ilen(st: str, state: dict[str, Any] | None = None) -> int:
    _ = state
    return ilen_compat(st)


def _ov_icharst(ch: str, lch: int, state: dict[str, Any] | None = None) -> int:
    _ = state
    return first_non_space_index(str(ch), int(lch))


def _ov_remove_blank_start(str: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    text = str[0] if isinstance(str, MutableSequence) and str else str
    shifted = builtins.str(text).lstrip(" ")
    if isinstance(str, MutableSequence) and len(str) >= 1:
        str[0] = shifted
    out["str"] = shifted
    return out


def _ov_toupper_lower(
    lupper_out: bool, str: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    text = str[0] if isinstance(str, MutableSequence) and str else str
    converted = (
        builtins.str(text).upper() if bool(lupper_out) else builtins.str(text).lower()
    )
    if isinstance(str, MutableSequence) and len(str) >= 1:
        str[0] = converted
    out["str"] = converted
    return out


def _ov_compact_string(
    str_in: str, str_out: Any, len_out: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    compact = "".join(ch for ch in builtins.str(str_in) if ch != " ")
    if isinstance(str_out, MutableSequence) and len(str_out) >= 1:
        str_out[0] = compact
    if isinstance(len_out, MutableSequence) and len(len_out) >= 1:
        len_out[0] = len(compact)
    out["str_out"] = compact
    out["len_out"] = len(compact)
    return out


def _ov_strchk(st: str, ps: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    escaped = escape_postscript_text(builtins.str(st))
    if isinstance(ps, MutableSequence) and len(ps) >= 1:
        ps[0] = escaped
    out["ps"] = escaped
    return out


def _ov_check_zero_voxels(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    channels = out.get("channels", ())
    out["zero_voxel"] = detect_zero_voxels(channels)
    return out


def _ov_getvar(state: dict[str, Any] | None = None) -> float:
    out = state if state is not None else {}
    datat = out.get("datat", ())
    nback = out.get("nback", (64, 1))
    if len(nback) < 2:
        return 0.0
    return estimate_tail_variance(datat, nback_start=int(nback[0]), nback_end=int(nback[1]))


def _ov_average(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    channels = out.get("channels")
    if channels is None:
        return out
    mode = int(out.get("iaverg", 1))
    if mode in {31, 32}:
        normalize = False
        weighted = False
        selection = "odd" if mode == 31 else "even"
    elif mode in {1, 2, 3, 4}:
        normalize = mode in {1, 4}
        weighted = mode in {1, 2}
        selection = "all"
    else:
        raise ValueError(f"Unsupported iaverg mode: {mode}")
    nback = out.get("nback", (64, 1))
    result = weighted_average_channels(
        channels,
        nback_start=int(nback[0]),
        nback_end=int(nback[1]),
        normalize_by_signal=normalize,
        weight_by_variance=weighted,
        selection=selection,
        zero_voxels=out.get("zero_voxel"),
    )
    out["datat"] = result.averaged
    out["average_result"] = result
    return out


def _ov_errmes(
    number: int, ilevel: int, chsubp: str, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    msg = f"ERRMES {int(number)} level={int(ilevel)} subroutine={chsubp}"
    out.setdefault("errors", []).append(msg)
    if int(ilevel) >= 4:
        raise RuntimeError(msg)
    return out


def _ov_random(dix: Any, state: dict[str, Any] | None = None) -> float:
    out = state if state is not None else {}
    if isinstance(dix, MutableSequence) and dix:
        seed = float(dix[0])
    else:
        seed = float(dix)
    a = 16807.0
    b15 = 32768.0
    b16 = 65536.0
    p = 2147483647.0
    xhi = math.floor(seed / b16)
    xalo = (seed - xhi * b16) * a
    leftlo = math.floor(xalo / b16)
    fhi = xhi * a + leftlo
    k = math.floor(fhi / b15)
    seed = (((xalo - leftlo * b16) - p) + (fhi - k * b15) * b16) + k
    if seed < 0.0:
        seed += p
    if isinstance(dix, MutableSequence) and dix:
        dix[0] = seed
    out["dix"] = seed
    return seed * 4.656612875e-10


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
    "ilen": _ov_ilen,
    "icharst": _ov_icharst,
    "remove_blank_start": _ov_remove_blank_start,
    "toupper_lower": _ov_toupper_lower,
    "compact_string": _ov_compact_string,
    "strchk": _ov_strchk,
    "check_zero_voxels": _ov_check_zero_voxels,
    "getvar": _ov_getvar,
    "average": _ov_average,
    "errmes": _ov_errmes,
    "random": _ov_random,
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


def _sanitize_name(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def _discover_fortran_unit_names() -> set[str]:
    source = pathlib.Path(__file__).with_name("LCModel.f")
    if not source.exists():
        return set()
    header_re = re.compile(
        r"^\s*(?:(REAL|INTEGER|LOGICAL|COMPLEX|DOUBLE\s+PRECISION|CHARACTER(?:\*\d+)?)\s+)?"
        r"(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?",
        flags=re.IGNORECASE,
    )
    names: set[str] = set()
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        match = header_re.match(line)
        if not match:
            continue
        raw_name = (match.group(3) or "").strip()
        if not raw_name:
            continue
        names.add(_sanitize_name(raw_name))
    return names


_PLACEHOLDER_OVERRIDES: set[str] = set()


def _make_placeholder_override(name: str):
    def _override(*args: Any, **kwargs: Any):
        state = kwargs.get("state")
        if state is None and args and isinstance(args[-1], dict):
            state = args[-1]
        if state is None:
            state = {}
        state.setdefault("placeholder_overrides", []).append(name)
        return state

    return _override


for _routine_name in _discover_fortran_unit_names():
    if _routine_name not in SEMANTIC_OVERRIDES:
        SEMANTIC_OVERRIDES[_routine_name] = _make_placeholder_override(_routine_name)
        _PLACEHOLDER_OVERRIDES.add(_routine_name)
