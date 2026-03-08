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
from lcmodel.core.legacy_eigen import jacobi_symmetric, tridiagonal_from_symmetric
from lcmodel.core.legacy_linear import g1 as g1_compat, g2 as g2_compat, h12 as h12_compat
from lcmodel.core.legacy_math import (
    betain as betain_compat,
    dgamln as dgamln_compat,
    diff as diff_compat,
    fishni as fishni_compat,
    icycle as icycle_compat,
    icycle_r as icycle_r_compat,
    inflec as inflec_compat,
    nextre as nextre_compat,
    pythag as pythag_compat,
)
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
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage


def _assign_vector(target: Any, values: Sequence[complex]) -> None:
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(values))
        for i in range(limit):
            target[i] = values[i]


def _assign_scalar(target: Any, value: Any) -> None:
    if isinstance(target, MutableSequence) and len(target) >= 1:
        target[0] = value


def _copy_sequence_prefix(target: Any, source: Sequence[Any]) -> None:
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(source))
        for i in range(limit):
            target[i] = source[i]


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


def _ov_dgamln(xarg: float, state: dict[str, Any] | None = None) -> float:
    _ = state
    return dgamln_compat(float(xarg))


def _ov_betain(x: float, a: float, b: float, nout: int, state: dict[str, Any] | None = None) -> float:
    _ = nout
    _ = state
    return betain_compat(float(x), float(a), float(b))


def _ov_fishni(f: float, df1: float, df2: float, nout: int, state: dict[str, Any] | None = None) -> float:
    _ = nout
    _ = state
    return fishni_compat(float(f), float(df1), float(df2))


def _ov_diff(x: float, y: float, state: dict[str, Any] | None = None) -> float:
    _ = state
    return diff_compat(float(x), float(y))


def _ov_pythag(a: float, b: float, state: dict[str, Any] | None = None) -> float:
    _ = state
    return pythag_compat(float(a), float(b))


def _ov_icycle_r(j: int, ndata: int, state: dict[str, Any] | None = None) -> int:
    _ = state
    return icycle_r_compat(int(j), int(ndata))


def _ov_icycle(j: int, ndata: int, state: dict[str, Any] | None = None) -> int:
    _ = state
    return icycle_compat(int(j), int(ndata))


def _ov_nextre(
    parnl: Sequence[float],
    nside2: int,
    dpy: Any,
    dgauss: Sequence[float],
    thrlin: float,
    imethd: int,
    state: dict[str, Any] | None = None,
) -> int:
    _ = dpy
    _ = state
    return nextre_compat(parnl, int(nside2), dgauss, float(thrlin), int(imethd))


def _ov_inflec(
    parnl: Sequence[float],
    nside2: int,
    dpy: Any,
    dgauss: Sequence[float],
    thrlin: float,
    imethd: int,
    state: dict[str, Any] | None = None,
) -> int:
    _ = dpy
    _ = state
    return inflec_compat(parnl, int(nside2), dgauss, float(thrlin), int(imethd))


def _ov_g1(a: float, b: float, cos: Any, sin: Any, sig: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    cos_v, sin_v, sig_v = g1_compat(float(a), float(b))
    _assign_scalar(cos, cos_v)
    _assign_scalar(sin, sin_v)
    _assign_scalar(sig, sig_v)
    out["g1"] = (cos_v, sin_v, sig_v)
    return out


def _ov_g2(cos: float, sin: float, x: Any, y: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    xv = float(x[0]) if isinstance(x, MutableSequence) and x else float(x)
    yv = float(y[0]) if isinstance(y, MutableSequence) and y else float(y)
    xr, yr = g2_compat(float(cos), float(sin), xv, yv)
    _assign_scalar(x, xr)
    _assign_scalar(y, yr)
    out["g2"] = (xr, yr)
    return out


def _ov_h12(
    mode: int,
    lpivot: int,
    l1: int,
    m: int,
    u: Any,
    iue: int,
    up: Any,
    c: Any,
    ice: int,
    icv: int,
    ncv: int,
    range_: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    if not isinstance(u, MutableSequence) or not isinstance(c, MutableSequence):
        return out
    up_value = float(up[0]) if isinstance(up, MutableSequence) and up else float(up)
    up_value = h12_compat(
        int(mode),
        int(lpivot),
        int(l1),
        int(m),
        u,
        int(iue),
        up_value,
        c,
        int(ice),
        int(icv),
        int(ncv),
        float(range_),
    )
    _assign_scalar(up, up_value)
    out["up"] = up_value
    return out


def _ov_pnnls(
    a: Sequence[Sequence[float]],
    mda: int,
    m: int,
    n: int,
    b: Sequence[float],
    x: Any,
    dvar: Any,
    w: Any,
    zz: Any,
    index: Any,
    mode: Any,
    range_: float,
    nonneg: Sequence[bool],
    dvarac: float,
    nsetp: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (mda, zz, range_)
    out = state if state is not None else {}
    rows = [list(map(float, row[: int(n)])) for row in a[: int(m)]]
    vec = [float(v) for v in b[: int(m)]]
    mask = tuple(bool(v) for v in nonneg[: int(n)])
    fit = run_fit_stage(
        rows,
        vec,
        FitConfig(
            max_iter=8000,
            tolerance=1e-10,
            nonnegative_mask=mask,
        ),
    )
    coeffs = list(fit.coefficients)
    if isinstance(x, MutableSequence):
        for j in range(min(len(x), len(coeffs))):
            x[j] = coeffs[j]
    resid_sq = fit.residual_norm * fit.residual_norm + float(dvarac)
    _assign_scalar(dvar, resid_sq)
    _assign_scalar(mode, 1)
    positive_count = sum(1 for j, val in enumerate(coeffs) if (not mask[j]) or val > 0.0)
    _assign_scalar(nsetp, positive_count)
    if isinstance(index, MutableSequence):
        for j in range(min(len(index), len(coeffs))):
            index[j] = j + 1
    if isinstance(w, MutableSequence):
        for j in range(min(len(w), len(coeffs))):
            w[j] = 0.0
    out["pnnls_coefficients"] = tuple(coeffs)
    out["pnnls_residual_sq"] = resid_sq
    return out


def _ov_plprin(
    x: Sequence[float],
    y1: Sequence[float],
    y2: Sequence[float],
    n: int,
    only1: bool,
    nout: int,
    srange: float,
    nlinf: int,
    ng: int,
    my1: int,
    yerr: Sequence[float],
    plterr: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (nout, srange, nlinf, ng, my1, yerr)
    out = state if state is not None else {}
    count = max(0, min(int(n), len(x), len(y1), len(y2)))
    lines = []
    for i in range(count):
        if bool(only1):
            lines.append(f"{float(y1[i]): .6e} {float(x[i]): .6e}")
        else:
            lines.append(
                f"{float(y1[i]): .6e} {float(y2[i]): .6e} {float(x[i]): .6e}"
            )
    out["plprin_text"] = "\n".join(lines) + ("\n" if lines else "")
    out["plprin_plterr"] = bool(plterr)
    return out


def _ov_tred2(
    nm: int,
    n: int,
    a: Sequence[Sequence[float]],
    d: Any,
    e: Any,
    z: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = nm
    out = state if state is not None else {}
    n_use = int(n)
    matrix = [[float(a[i][j]) for j in range(n_use)] for i in range(n_use)]
    dvals, evals = tridiagonal_from_symmetric(matrix)
    if isinstance(d, MutableSequence):
        for i in range(min(len(d), n_use)):
            d[i] = dvals[i]
    if isinstance(e, MutableSequence):
        for i in range(min(len(e), n_use)):
            e[i] = evals[i]
    if isinstance(z, MutableSequence):
        for i in range(min(len(z), n_use)):
            row = z[i]
            if isinstance(row, MutableSequence):
                for j in range(min(len(row), n_use)):
                    row[j] = matrix[i][j]
    out["tred2_matrix"] = tuple(tuple(row) for row in matrix)
    return out


def _ov_tql2(
    nm: int,
    n: int,
    d: Any,
    e: Any,
    z: Any,
    ierr: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (nm, e)
    out = state if state is not None else {}
    n_use = int(n)
    matrix: list[list[float]]
    if isinstance(z, MutableSequence) and len(z) >= n_use and isinstance(z[0], MutableSequence):
        matrix = [
            [float(z[i][j]) for j in range(n_use)]
            for i in range(n_use)
        ]
    else:
        diag = [float(d[i]) for i in range(n_use)] if isinstance(d, MutableSequence) else [0.0] * n_use
        matrix = [[0.0] * n_use for _ in range(n_use)]
        for i in range(n_use):
            matrix[i][i] = diag[i]
    wvals, vecs = jacobi_symmetric(matrix)
    if isinstance(d, MutableSequence):
        for i in range(min(len(d), n_use)):
            d[i] = wvals[i]
    if isinstance(z, MutableSequence):
        for i in range(min(len(z), n_use)):
            row = z[i]
            if isinstance(row, MutableSequence):
                for j in range(min(len(row), n_use)):
                    row[j] = vecs[i][j]
    _assign_scalar(ierr, 0)
    out["tql2_eigenvalues"] = tuple(wvals)
    return out


def _ov_eigvrs(
    nm: int,
    n: int,
    a: Sequence[Sequence[float]],
    w: Any,
    z: Any,
    fv1: Any,
    fv2: Any,
    ierr: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (nm, fv1, fv2)
    out = state if state is not None else {}
    n_use = int(n)
    matrix = [[float(a[i][j]) for j in range(n_use)] for i in range(n_use)]
    wvals, vecs = jacobi_symmetric(matrix)
    if isinstance(w, MutableSequence):
        for i in range(min(len(w), n_use)):
            w[i] = wvals[i]
    if isinstance(z, MutableSequence):
        for i in range(min(len(z), n_use)):
            row = z[i]
            if isinstance(row, MutableSequence):
                for j in range(min(len(row), n_use)):
                    row[j] = vecs[i][j]
    _assign_scalar(ierr, 0)
    out["eigvrs_eigenvalues"] = tuple(wvals)
    return out


def _ov_df2tcf(n: int, c: Sequence[complex], yout: Any, wsave: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = wsave
    out = state if state is not None else {}
    vals = cfft_r_compat(c[: int(n)])
    _copy_sequence_prefix(yout, vals)
    out["df2tcf"] = tuple(vals)
    return out


def _ov_f2tcf(n: int, c: Sequence[complex], yout: Any, wsave: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_df2tcf(n, c, yout, wsave, state)


def _ov_dcftf1(n: int, c: Any, ch: Any, wa: Any, ifac: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = (wa, ifac)
    out = state if state is not None else {}
    vals = cfft_r_compat(c[: int(n)] if isinstance(c, Sequence) else [])
    _copy_sequence_prefix(ch, vals)
    out["dcftf1"] = tuple(vals)
    return out


def _ov_cfftf1(n: int, c: Any, ch: Any, wa: Any, ifac: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_dcftf1(n, c, ch, wa, ifac, state)


def _ov_cfftb1(n: int, c: Any, ch: Any, wa: Any, ifac: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = (wa, ifac)
    out = state if state is not None else {}
    vals = cfftin_r_compat(c[: int(n)] if isinstance(c, Sequence) else [])
    _copy_sequence_prefix(ch, vals)
    out["cfftb1"] = tuple(vals)
    return out


def _ov_dcfti1(n: int, wa: Any, ifac: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    _assign_scalar(ifac, int(n))
    if isinstance(wa, MutableSequence) and len(wa) >= 1:
        wa[0] = 0.0
    out["dcfti1_n"] = int(n)
    return out


def _ov_cffti1(n: int, wa: Any, ifac: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_dcfti1(n, wa, ifac, state)


def _ov_pass_copy(
    cc: Any,
    ch: Any,
    state: dict[str, Any] | None = None,
    tag: str = "pass",
) -> dict[str, Any]:
    out = state if state is not None else {}
    if isinstance(cc, Sequence):
        _copy_sequence_prefix(ch, list(cc))
        out[tag] = min(len(cc), len(ch)) if isinstance(ch, MutableSequence) else len(cc)
    else:
        out[tag] = 0
    return out


def _ov_passf(
    nac: int,
    ido: int,
    ip: int,
    l1: int,
    idl1: int,
    cc: Any,
    c1: Any,
    c2: Any,
    ch: Any,
    ch2: Any,
    wa: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (nac, ido, ip, l1, idl1, c1, c2, ch2, wa)
    return _ov_pass_copy(cc, ch, state, tag="passf")


def _ov_passb(
    nac: int,
    ido: int,
    ip: int,
    l1: int,
    idl1: int,
    cc: Any,
    c1: Any,
    c2: Any,
    ch: Any,
    ch2: Any,
    wa: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (nac, ido, ip, l1, idl1, c1, c2, ch2, wa)
    return _ov_pass_copy(cc, ch, state, tag="passb")


def _ov_passf2(ido: int, l1: int, cc: Any, ch: Any, wa1: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = (ido, l1, wa1)
    return _ov_pass_copy(cc, ch, state, tag="passf2")


def _ov_passf3(
    ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2)
    return _ov_pass_copy(cc, ch, state, tag="passf3")


def _ov_passf4(
    ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, wa3: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2, wa3)
    return _ov_pass_copy(cc, ch, state, tag="passf4")


def _ov_passf5(
    ido: int,
    l1: int,
    cc: Any,
    ch: Any,
    wa1: Any,
    wa2: Any,
    wa3: Any,
    wa4: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2, wa3, wa4)
    return _ov_pass_copy(cc, ch, state, tag="passf5")


def _ov_passb2(ido: int, l1: int, cc: Any, ch: Any, wa1: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = (ido, l1, wa1)
    return _ov_pass_copy(cc, ch, state, tag="passb2")


def _ov_passb3(
    ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2)
    return _ov_pass_copy(cc, ch, state, tag="passb3")


def _ov_passb4(
    ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, wa3: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2, wa3)
    return _ov_pass_copy(cc, ch, state, tag="passb4")


def _ov_passb5(
    ido: int,
    l1: int,
    cc: Any,
    ch: Any,
    wa1: Any,
    wa2: Any,
    wa3: Any,
    wa4: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (ido, l1, wa1, wa2, wa3, wa4)
    return _ov_pass_copy(cc, ch, state, tag="passb5")


def _ov_dcfft_r(datat: Sequence[complex], ft: Any, n: int, ldwfft: Any, dwfftc: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = dwfftc
    out = state if state is not None else {}
    vals = cfft_r_compat(datat[: int(n)])
    _copy_sequence_prefix(ft, vals)
    _assign_scalar(ldwfft, int(n))
    out["dcfft_r"] = tuple(vals)
    return out


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


def _ps_lines(state: dict[str, Any]) -> list[str]:
    lines = state.get("ps_lines")
    if not isinstance(lines, list):
        lines = []
        state["ps_lines"] = lines
    return lines


def _ov_psetup(top_of_file: bool, wd: float, ht: float, landsc: bool, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    lines = _ps_lines(out)
    if bool(top_of_file) and not lines:
        lines.extend(["%!PS-Adobe-3.0", "%%Creator: lcmodel semantic override"])
    lines.append("gsave")
    if bool(landsc):
        lines.append("90 rotate")
    lines.append(f"/PageWidth {float(wd):.6g} def")
    lines.append(f"/PageHeight {float(ht):.6g} def")
    out["ps_landsc"] = bool(landsc)
    return out


def _ov_linewd(width: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    _ps_lines(out).append(f"{max(0.0, float(width)):.6g} setlinewidth")
    return out


def _ov_rgb(rgbv: Sequence[float], state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    r = float(rgbv[0]) if len(rgbv) > 0 else 0.0
    g = float(rgbv[1]) if len(rgbv) > 1 else 0.0
    b = float(rgbv[2]) if len(rgbv) > 2 else 0.0
    _ps_lines(out).append(f"{r:.6g} {g:.6g} {b:.6g} setrgbcolor")
    return out


def _ov_dash(idshpt: int, dshpat: Sequence[float], state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if int(idshpt) <= 0:
        _ps_lines(out).append("[] 0 setdash")
        return out
    pat = [max(0.0, float(v)) for v in dshpat if float(v) > 0.0]
    if not pat:
        _ps_lines(out).append("[] 0 setdash")
    else:
        txt = " ".join(f"{v:.6g}" for v in pat)
        _ps_lines(out).append(f"[{txt}] 0 setdash")
    return out


def _ov_line(ox: float, oy: float, wd: float, ht: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    x1 = float(ox)
    y1 = float(oy)
    x2 = x1 + float(wd)
    y2 = y1 + float(ht)
    _ps_lines(out).append(f"newpath {x1:.6g} {y1:.6g} moveto {x2:.6g} {y2:.6g} lineto stroke")
    return out


def _ov_box(ox: float, oy: float, wd: float, ht: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    x = float(ox)
    y = float(oy)
    w = float(wd)
    h = float(ht)
    _ps_lines(out).append(
        "newpath "
        f"{x:.6g} {y:.6g} moveto "
        f"{x + w:.6g} {y:.6g} lineto "
        f"{x + w:.6g} {y + h:.6g} lineto "
        f"{x:.6g} {y + h:.6g} lineto closepath stroke"
    )
    return out


def _map_plot_point(value: float, src_min: float, src_max: float, dst_min: float, dst_len: float) -> float:
    if abs(src_max - src_min) <= 1e-30:
        return dst_min
    return dst_min + (float(value) - src_min) * dst_len / (src_max - src_min)


def _ov_plot(
    n: int,
    x: Sequence[float],
    y: Sequence[float],
    xmn: float,
    xmx: float,
    ymn: float,
    ymx: float,
    ox: float,
    oy: float,
    wd: float,
    ht: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    count = max(0, min(int(n), len(x), len(y)))
    if count <= 0:
        return out
    lines = _ps_lines(out)
    px0 = _map_plot_point(float(x[0]), float(xmn), float(xmx), float(ox), float(wd))
    py0 = _map_plot_point(float(y[0]), float(ymn), float(ymx), float(oy), float(ht))
    cmd = [f"newpath {px0:.6g} {py0:.6g} moveto"]
    for i in range(1, count):
        pxi = _map_plot_point(float(x[i]), float(xmn), float(xmx), float(ox), float(wd))
        pyi = _map_plot_point(float(y[i]), float(ymn), float(ymx), float(oy), float(ht))
        cmd.append(f"{pxi:.6g} {pyi:.6g} lineto")
    cmd.append("stroke")
    lines.append(" ".join(cmd))
    return out


def _ov_plot_gap(
    n: int,
    x: Sequence[float],
    y: Sequence[float],
    xmn: float,
    xmx: float,
    ymn: float,
    ymx: float,
    ox: float,
    oy: float,
    wd: float,
    ht: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Current port maps PLOT_gap to the same polyline behavior as PLOT.
    return _ov_plot(n, x, y, xmn, xmx, ymn, ymx, ox, oy, wd, ht, state)


def _ov_font(pitch: float, police: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    face = builtins.str(police).strip() or "Courier"
    size = max(1.0, abs(float(pitch)))
    _ps_lines(out).append(f"/{face} findfont {size:.6g} scalefont setfont")
    return out


def _ov_string(flush: bool, ang: float, ox: float, oy: float, st: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    text = escape_postscript_text(builtins.str(st))
    lines = _ps_lines(out)
    lines.append(
        "gsave "
        f"{float(ox):.6g} {float(oy):.6g} translate "
        f"{float(ang):.6g} rotate 0 0 moveto ({text}) show grestore"
    )
    if bool(flush):
        out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_show(flush: bool, st: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    text = escape_postscript_text(builtins.str(st))
    lines = _ps_lines(out)
    lines.append(f"({text}) show")
    if bool(flush):
        out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_showpg(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    _ps_lines(out).append("showpage")
    return out


def _ov_endps(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    lines = _ps_lines(out)
    lines.append("grestore")
    out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_strpou(state: dict[str, Any] | None = None) -> dict[str, Any]:
    # Preserve current output buffer in state for compatibility.
    out = state if state is not None else {}
    out["postscript"] = "\n".join(_ps_lines(out)) + ("\n" if _ps_lines(out) else "")
    return out


def _ov_makeps(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    # Build a minimal page if caller hasn't emitted anything yet.
    if not _ps_lines(out):
        _ov_psetup(True, 612.0, 792.0, False, out)
    out["makeps_called"] = True
    return out


def _ov_onepag(
    ncurve: int,
    yfit: Sequence[float],
    ydata: Sequence[float],
    lchlin: bool,
    nsubti: int,
    pagex: Sequence[float],
    pagey: Sequence[float],
    subtit: Sequence[str],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    _ov_makeps(out)
    out["onepag_curves"] = int(ncurve)
    out["onepag_points"] = min(len(yfit), len(ydata))
    out["onepag_subtitles"] = tuple(builtins.str(s) for s in subtit[: max(0, int(nsubti))])
    return out


def _ov_tick(
    ang: float,
    ox: float,
    oy: float,
    length: float,
    gmn: float,
    gmx: float,
    tckbeg: float,
    tckinc: float,
    grid: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    _ps_lines(out).append(
        f"% tick ang={float(ang):.6g} from {float(gmn):.6g} to {float(gmx):.6g} "
        f"inc={float(tckinc):.6g} grid={bool(grid)}"
    )
    return out


def _ov_axis(
    ang: float,
    ox: float,
    oy: float,
    length: float,
    gmn: float,
    gmx: float,
    tckbeg: float,
    tckinc: float,
    pos: Sequence[float],
    ljust1: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    _ov_line(ox, oy, length * math.cos(float(ang)), length * math.sin(float(ang)), out)
    _ov_tick(ang, ox, oy, length, gmn, gmx, tckbeg, tckinc, False, out)
    return out


def _ov_hex(val: int, inum: Any, flush: bool, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    hex_text = f"{int(val) & 0xFFFFFFFF:X}"
    if isinstance(inum, MutableSequence) and len(inum) >= 1:
        inum[0] = len(hex_text)
    out["hex"] = hex_text
    if bool(flush):
        _ps_lines(out).append(f"% HEX {hex_text}")
    return out


def _ov_check_bottom(
    ycurr: float,
    decrement: float,
    xboxlo: float,
    outside: Any,
    ytop_column: Sequence[float],
    column_width: Sequence[float],
    xboxlo_max: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    new_y = float(ycurr) - float(decrement)
    is_outside = new_y < 0.0
    if isinstance(outside, MutableSequence) and len(outside) >= 1:
        outside[0] = is_outside
    out["ycurr"] = new_y
    out["outside"] = is_outside
    return out


def _ov_end_table(
    ycurr: float,
    xboxlo: float,
    ytop_column: Sequence[float],
    column_width: Sequence[float],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    out["table_end_y"] = float(ycurr)
    out["table_columns"] = len(column_width)
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
    "dgamln": _ov_dgamln,
    "betain": _ov_betain,
    "fishni": _ov_fishni,
    "diff": _ov_diff,
    "pythag": _ov_pythag,
    "icycle_r": _ov_icycle_r,
    "icycle": _ov_icycle,
    "nextre": _ov_nextre,
    "inflec": _ov_inflec,
    "g1": _ov_g1,
    "g2": _ov_g2,
    "h12": _ov_h12,
    "pnnls": _ov_pnnls,
    "plprin": _ov_plprin,
    "eigvrs": _ov_eigvrs,
    "tql2": _ov_tql2,
    "tred2": _ov_tred2,
    "df2tcf": _ov_df2tcf,
    "f2tcf": _ov_f2tcf,
    "dcftf1": _ov_dcftf1,
    "dcfti1": _ov_dcfti1,
    "cfftf1": _ov_cfftf1,
    "cfftb1": _ov_cfftb1,
    "cffti1": _ov_cffti1,
    "passf": _ov_passf,
    "passf2": _ov_passf2,
    "passf3": _ov_passf3,
    "passf4": _ov_passf4,
    "passf5": _ov_passf5,
    "passb": _ov_passb,
    "passb2": _ov_passb2,
    "passb3": _ov_passb3,
    "passb4": _ov_passb4,
    "passb5": _ov_passb5,
    "dcfft_r": _ov_dcfft_r,
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
    "psetup": _ov_psetup,
    "linewd": _ov_linewd,
    "rgb": _ov_rgb,
    "dash": _ov_dash,
    "line": _ov_line,
    "box": _ov_box,
    "plot": _ov_plot,
    "plot_gap": _ov_plot_gap,
    "font": _ov_font,
    "string": _ov_string,
    "show": _ov_show,
    "showpg": _ov_showpg,
    "endps": _ov_endps,
    "strpou": _ov_strpou,
    "makeps": _ov_makeps,
    "onepag": _ov_onepag,
    "tick": _ov_tick,
    "axis": _ov_axis,
    "hex": _ov_hex,
    "check_bottom": _ov_check_bottom,
    "end_table": _ov_end_table,
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
