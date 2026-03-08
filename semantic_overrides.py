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
from lcmodel.core.fortran_compat import fortran_nint
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
from lcmodel.core.legacy_parsing import (
    build_conc_prior,
    chreal as chreal_compat,
    get_field_from_string,
    parse_chsimu_strings,
    parse_prior_strings,
    parse_sum_terms,
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
from lcmodel.pipeline.phasing import apply_zero_order_phase, estimate_zero_order_phase


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


def _ov_igetp(istart: int, niter: int, state: dict[str, Any] | None = None) -> int:
    _ = state
    if int(istart) == 8829:
        return 0
    p = 2147483647.0
    a = 16807.0
    b15 = 32768.0
    b16 = 65536.0
    dix = float(max(1, abs(int(istart)) % 2147483647))
    for _ in range(max(1, int(niter))):
        xhi = math.floor(dix / b16)
        xalo = (dix - xhi * b16) * a
        leftlo = math.floor(xalo / b16)
        fhi = xhi * a + leftlo
        k = math.floor(fhi / b15)
        dix = (((xalo - leftlo * b16) - p) + (fhi - k * b15) * b16) + k
        if dix < 0.0:
            dix += p
    dix = dix * 4.656612875e-10
    return int(1.0e9 * dix)


def _ov_merge_right(lregion: int, ppmmin: Any, ppmmax: Any, nregion: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if not isinstance(ppmmin, MutableSequence) or not isinstance(ppmmax, MutableSequence):
        return out
    lr = int(lregion) - 1
    nreg = int(nregion[0]) if isinstance(nregion, MutableSequence) and nregion else int(nregion)
    if lr < 0 or lr >= nreg - 1:
        raise ValueError("lregion must be < nregion")
    nreg -= 1
    ppmmin[lr] = ppmmin[lr + 1]
    for j in range(lr + 1, nreg):
        ppmmax[j] = ppmmax[j + 1]
        ppmmin[j] = ppmmin[j + 1]
    _assign_scalar(nregion, nreg)
    out["nregion"] = nreg
    return out


def _ov_merge_left(lregion: int, ppmmin: Any, ppmmax: Any, nregion: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if not isinstance(ppmmin, MutableSequence) or not isinstance(ppmmax, MutableSequence):
        return out
    lr = int(lregion) - 1
    nreg = int(nregion[0]) if isinstance(nregion, MutableSequence) and nregion else int(nregion)
    if lr <= 0 or lr >= nreg:
        raise ValueError("lregion must be > 1")
    nreg -= 1
    ppmmin[lr - 1] = ppmmin[lr]
    for j in range(lr, nreg):
        ppmmax[j] = ppmmax[j + 1]
        ppmmin[j] = ppmmin[j + 1]
    _assign_scalar(nregion, nreg)
    out["nregion"] = nreg
    return out


def _ov_smooth_tail_2(
    work_in: Sequence[float],
    out_arr: Any,
    munfil: int,
    nunfil: int,
    lprint: int,
    voxel1: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (munfil, lprint, voxel1)
    out = state if state is not None else {}
    n = int(nunfil)
    values = [float(v) for v in work_in[:n]]
    out_vals = [0.0] * n
    j_break = 1
    for j in range(n - 2, 0, -1):
        if (values[j + 1] - values[j]) * (values[j] - values[j - 1]) > 0.0:
            j_break = j + 1
            break
        out_vals[j] = 0.5 * values[j] + 0.25 * (values[j + 1] + values[j - 1])
    if j_break < n - 1:
        out_vals[n - 1] = out_vals[n - 2]
    else:
        out_vals[n - 1] = values[n - 1]
    for j in range(0, j_break):
        out_vals[j] = values[j]
    _copy_sequence_prefix(out_arr, out_vals)
    out["tail_smoothed_points"] = max(0, n - j_break)
    return out


def _ov_smooth_tail(cdatat: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if not isinstance(cdatat, MutableSequence):
        return out
    n = len(cdatat)
    re = [float(complex(v).real) for v in cdatat]
    im = [float(complex(v).imag) for v in cdatat]
    re_out = [0.0] * n
    im_out = [0.0] * n
    _ov_smooth_tail_2(re, re_out, n, n, 0, False, out)
    _ov_smooth_tail_2(im, im_out, n, n, 0, False, out)
    for i in range(n):
        cdatat[i] = complex(re_out[i], im_out[i])
    out["smooth_tail_n"] = n
    return out


def _ov_fix_g77_namelist(lunit: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["fix_g77_namelist_lunit"] = int(lunit)
    return out


def _ov_phase_with_max_real(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    datat = out.get("datat")
    if datat is None:
        return out
    phase = estimate_zero_order_phase(datat, search_steps=360)
    phased = apply_zero_order_phase(datat, phase)
    out["datat"] = tuple(phased)
    out["phase_with_max_real_radians"] = float(phase)
    return out


def _ov_get_field(
    chseparator: str,
    len_chseparator: int,
    ifield_type: int,
    iatend: int,
    chreturn: Any,
    freturn: Any,
    istart: Any,
    len_string_in: int,
    string_in: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (len_string_in, state)
    sep = builtins.str(chseparator)[: int(len_chseparator)] if int(len_chseparator) > 0 else ""
    cur = int(istart[0]) if isinstance(istart, MutableSequence) and istart else int(istart)
    next_start, value = get_field_from_string(sep, int(ifield_type), int(iatend), cur, builtins.str(string_in))
    _assign_scalar(istart, next_start)
    if int(ifield_type) == 1:
        _assign_scalar(chreturn, builtins.str(value))
    elif int(ifield_type) == 2:
        _assign_scalar(freturn, float(value))
    return {"istart": next_start, "value": value}


def _ov_parse_prior(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    chrato = out.get("chrato", ())
    parsed = parse_prior_strings(tuple(builtins.str(v) for v in chrato))
    out["parsed_prior"] = parsed
    out["chrati"] = tuple(builtins.str(v["chrati"]) for v in parsed)
    out["chratw"] = tuple(builtins.str(v["chratw"]) for v in parsed)
    out["exrati"] = tuple(float(v["exrati"]) for v in parsed)
    out["sdrati"] = tuple(float(v["sdrati"]) for v in parsed)
    out["nratio"] = len(parsed)
    return out


def _ov_parse_sum(
    exrati_arg: float,
    substring: str,
    len_substring: int,
    lratio: int,
    csum: Any,
    denom_absent: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    names = tuple(builtins.str(v) for v in out.get("nacomb", ()))
    solbes = tuple(float(v) for v in out.get("solbes", ()))
    row, add_sum, is_absent = parse_sum_terms(
        builtins.str(substring)[: int(len_substring)],
        names,
        solbes,
        float(exrati_arg),
    )
    old_sum = float(csum[0]) if isinstance(csum, MutableSequence) and csum else float(csum)
    _assign_scalar(csum, old_sum + add_sum)
    if isinstance(denom_absent, MutableSequence) and denom_absent:
        denom_absent[0] = bool(denom_absent[0]) and bool(is_absent)
    elif isinstance(denom_absent, MutableSequence):
        denom_absent.append(bool(is_absent))
    cprior = out.get("cprior")
    lr = int(lratio) - 1
    if isinstance(cprior, MutableSequence) and 0 <= lr < len(cprior):
        crow = cprior[lr]
        if isinstance(crow, MutableSequence):
            for j in range(min(len(crow), len(row))):
                crow[j] = float(crow[j]) + row[j]
    out["parse_sum_last"] = {
        "row": tuple(row),
        "csum_add": add_sum,
        "denom_absent": bool(is_absent),
    }
    return out


def _ov_conc_prior(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if "parsed_prior" not in out:
        _ov_parse_prior(out)
    nacomb = tuple(builtins.str(v) for v in out.get("nacomb", ()))
    solbes = tuple(float(v) for v in out.get("solbes", ()))
    norato = tuple(builtins.str(v) for v in out.get("norato", ()))
    rows, used = build_conc_prior(
        out.get("parsed_prior", ()),
        nacomb,
        solbes,
        norato=norato,
        fcsum=float(out.get("fcsum", 1.0e-2)),
    )
    out["cprior"] = tuple(tuple(float(v) for v in row) for row in rows)
    out["nratio_used"] = len(rows)
    out["prior_used"] = tuple(used)
    return out


def _ov_parse_chsimu(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    chsimu = tuple(builtins.str(v) for v in out.get("chsimu", ()))
    parsed = parse_chsimu_strings(chsimu)
    out["parsed_chsimu"] = tuple(parsed)
    out["nsimul"] = len(parsed)
    return out


def _ov_chreal(x: float, xstep: float, ljust: bool, state: dict[str, Any] | None = None) -> str:
    _ = state
    return chreal_compat(float(x), float(xstep), bool(ljust))


def _ov_check_chless(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    chless = tuple(builtins.str(v) for v in out.get("chless", ()))
    chmore = builtins.str(out.get("chmore", ""))
    rlesmo = float(out.get("rlesmo", 0.0))
    nacomb = tuple(builtins.str(v) for v in out.get("nacomb", ()))
    solbes = tuple(float(v) for v in out.get("solbes", ()))
    omit = False
    if chmore and rlesmo > 0.0 and chless:
        conc_more = sum(solbes[j] for j, name in enumerate(nacomb) if name.startswith(chmore))
        for prefix in chless:
            if not prefix:
                continue
            conc_less = sum(solbes[j] for j, name in enumerate(nacomb) if name.startswith(prefix))
            if conc_more > 0.0 and conc_less / conc_more > rlesmo:
                omit = True
                break
    out["omit_chless"] = omit
    return out


def _ov_getpha(
    kystart: int,
    kyend: int,
    dataf: Sequence[complex],
    dataw: Any,
    nunfil: int,
    radian: float,
    nypeak: Any,
    yorig: Any,
    yinterp: Any,
    degzer_calc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (radian, nypeak, yorig, yinterp)
    out = state if state is not None else {}
    n = int(nunfil)
    src = list(dataf[:n])
    lo = max(0, int(kystart) - 1)
    hi = min(n - 1, int(kyend) - 1)
    window = src[lo : hi + 1] if hi >= lo else src
    phase = estimate_zero_order_phase(window, search_steps=360)
    phased = apply_zero_order_phase(src, phase)
    _copy_sequence_prefix(dataw, phased)
    _assign_scalar(degzer_calc, math.degrees(float(phase)) % 360.0)
    out["getpha_phase_radians"] = float(phase)
    return out


def _ov_areaw2(state: dict[str, Any] | None = None) -> float:
    out = state if state is not None else {}
    h2ot = list(out.get("h2ot", ()))
    if not h2ot:
        return -1.0
    nunfil = int(out.get("nunfil", len(h2ot)))
    ppminc = float(out.get("ppminc", 0.0))
    if ppminc <= 0.0:
        return -1.0
    ppmcen = float(out.get("ppmcen", 4.65))
    ppmh2o = float(out.get("ppmh2o", 4.65))
    hwdwat = out.get("hwdwat", (0.15, 0.2))
    if not isinstance(hwdwat, Sequence) or len(hwdwat) < 2:
        hwdwat = (0.15, 0.2)
    spectrum = list(csft_r_compat(h2ot, ncap=nunfil))
    ly = int(round((ppmcen - ppmh2o) / ppminc)) + nunfil // 2 + 1
    kystrt = int(round((ppmcen - ppmh2o - float(hwdwat[1])) / ppminc)) + nunfil // 2 + 1
    kyend = int(round((ppmcen - ppmh2o + float(hwdwat[1])) / ppminc)) + nunfil // 2 + 1
    ly = max(1, min(nunfil, ly))
    kystrt = max(2, min(nunfil - 1, kystrt))
    kyend = max(kystrt + 1, min(nunfil - 2, kyend))
    result = integrate_peak_with_local_baseline(
        [float(v.real) for v in spectrum],
        peak_index=ly - 1,
        start_index=kystrt - 1,
        end_index=kyend - 1,
        border_width=max(1, int(round(float(out.get("ppmbas2", 0.05)) / ppminc))),
        spacing=ppminc * 2.0,
    )
    out["area_water"] = float(result.area)
    return float(result.area)


def _ov_areawa(istage: int, state: dict[str, Any] | None = None) -> float:
    out = state if state is not None else {}
    if int(out.get("iareaw", 1)) == 2 and int(istage) == 2:
        return _ov_areaw2(out)
    h2ot = list(out.get("h2ot", ()))
    nunfil = int(out.get("nunfil", len(h2ot)))
    nwsst = int(out.get("nwsst", 1))
    nwsend = int(out.get("nwsend", min(nunfil, max(1, nunfil // 4))))
    ppminc = float(out.get("ppminc", 1.0))
    if not h2ot or nunfil <= 0 or nwsst < 1 or nwsend > nunfil or nwsend - nwsst + 1 < 2:
        return -1.0
    sx = sy = sxy = sxx = 0.0
    for j in range(nwsst, nwsend + 1):
        xterm = float(j)
        yterm = abs(complex(h2ot[j - 1]))
        if yterm <= 0.0:
            return -1.0
        yterm = math.log(yterm)
        sx += xterm
        sy += yterm
        sxy += xterm * yterm
        sxx += xterm * xterm
    npts = float(nwsend - nwsst + 1)
    term1 = npts * sxx
    denom = term1 - sx * sx
    if abs(denom) <= 1.0e-12 * max(1.0, abs(term1)):
        return -1.0
    rnum = sxx * sy - sx * sxy
    rrange = float(out.get("rrange", 1.0e30))
    expmax = math.log(max(rrange, 1.0))
    if abs(rnum) >= expmax * abs(denom):
        return -1.0
    val = 0.5 * ppminc * math.exp(rnum / denom) * math.sqrt(float(2 * nunfil))
    out["area_water"] = float(val)
    return float(val)


def _ov_areaba(basisf: Any, ppminc_arg: float, nunfil_arg: int, state: dict[str, Any] | None = None) -> float:
    out = state if state is not None else {}
    if not isinstance(basisf, MutableSequence):
        return 0.0
    ndata = 2 * int(nunfil_arg)
    ppminc = float(ppminc_arg)
    if ndata <= 0 or ppminc <= 0.0:
        return 0.0
    ppmcen = float(out.get("ppmcen", 4.65))
    wsppm = float(out.get("wsppm", 2.01))
    rfwbas = float(out.get("rfwbas", 10.0))
    fwhmba = float(out.get("fwhmba", 0.05))
    ppmbas1 = float(out.get("ppmbas1", 0.02))
    n1hmet = int(out.get("n1hmet", 1))
    attmet = float(out.get("attmet", 1.0))
    if n1hmet <= 0 or attmet <= 0.0:
        return 0.0

    ly = fortran_nint((ppmcen - wsppm) / ppminc) + 1
    nwndo = max(1, fortran_nint(ppmbas1 / ppminc))
    nyhalf = max(1, fortran_nint((0.5 * rfwbas * fwhmba) / ppminc))
    kystrt = ly - nyhalf
    kyend = ly + nyhalf
    if kystrt - nwndo <= -int(nunfil_arg) or kyend + nwndo >= int(nunfil_arg):
        return 0.0

    def cyc(idx: int) -> int:
        return (idx - 1 + ndata) % ndata

    left_vals = [float(complex(basisf[cyc(j)]).real) for j in range(kystrt - nwndo, kystrt)]
    right_vals = [float(complex(basisf[cyc(j)]).real) for j in range(kyend + 1, kyend + nwndo + 1)]
    if not left_vals or not right_vals:
        return 0.0
    avg = 0.5 * ((sum(left_vals) / len(left_vals)) + (sum(right_vals) / len(right_vals)))
    area = 0.0
    for j in range(kystrt, kyend + 1):
        area += float(complex(basisf[cyc(j)]).real)
    area = area - float(kyend - kystrt + 1) * avg
    val = ppminc * area / (float(n1hmet) * attmet)
    out["area_met_norm"] = float(val)
    return float(val)


def _ov_water_scale(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    iaverg = int(out.get("iaverg", 0))
    if iaverg in {1, 4}:
        area_water = 1.0
    else:
        area_water = _ov_areawa(2, out)
    atth2o = float(out.get("atth2o", 1.0))
    wconc = float(out.get("wconc", 1.0))
    area_met_norm = float(out.get("area_met_norm", 1.0))
    if area_water <= 0.0 or atth2o <= 0.0 or wconc <= 0.0:
        out["wsdone"] = False
        return out
    water_norm = area_water / (2.0 * atth2o * wconc)
    fcalib = area_met_norm / water_norm
    out["fcalib"] = fcalib
    out["wsdone"] = True
    datat = out.get("datat")
    if isinstance(datat, MutableSequence):
        for i in range(len(datat)):
            datat[i] = complex(datat[i]) * fcalib
    cy = out.get("cy")
    if isinstance(cy, MutableSequence):
        for i in range(len(cy)):
            cy[i] = complex(cy[i]) * fcalib
    return out


def _ov_ldegmx(idegmx: int, state: dict[str, Any] | None = None) -> bool:
    out = state if state is not None else {}
    idx = int(idegmx) - 1
    degmax = out.get("degmax", (90.0, 90.0))
    if idx < 0 or idx >= len(degmax):
        return False
    parbes = out.get("parbes", ())
    lphast = int(out.get("lphast", 0))
    phizer = float(parbes[lphast + 1]) if len(parbes) > lphast + 1 else 0.0
    phione = float(parbes[lphast + 2]) if len(parbes) > lphast + 2 else 0.0
    ppmcen = float(out.get("ppmcen", 4.65))
    ppmsig = out.get("ppmsig", (ppmcen, ppmcen))
    ppm = out.get("ppm", (ppmcen,))
    nyuse = int(out.get("nyuse", len(ppm)))
    if not ppm:
        return False
    ppmmax = min(max(float(ppmsig[0]), float(ppmsig[1])), float(ppm[0]))
    ppmmin = max(min(float(ppmsig[0]), float(ppmsig[1])), float(ppm[max(0, nyuse - 1)]))
    radian = float(out.get("radian", math.pi / 180.0))
    def phacor(ppmarg: float) -> float:
        return abs(phizer + (ppmarg - ppmcen) * phione)
    return max(phacor(ppmmax), phacor(ppmmin)) > float(degmax[idx]) * radian


def _ov_r_base_sol_big(istage: int, state: dict[str, Any] | None = None) -> bool:
    out = state if state is not None else {}
    backre = [float(v) for v in out.get("backre", ())]
    solbes = [float(v) for v in out.get("solbes", ())]
    if not backre or not solbes:
        return False
    basmax = max(backre)
    basmin = min(backre)
    base_dist = basmax - basmin
    solmax = max(abs(v) for v in solbes)
    if solmax <= 0.0:
        return True
    rbasmx = out.get("rbasmx", (0.0, 0.0, 0.0))
    idx = max(0, min(len(rbasmx) - 1, int(istage) - 1))
    return (base_dist / solmax) > float(rbasmx[idx])


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
    "igetp": _ov_igetp,
    "merge_right": _ov_merge_right,
    "merge_left": _ov_merge_left,
    "smooth_tail_2": _ov_smooth_tail_2,
    "smooth_tail": _ov_smooth_tail,
    "fix_g77_namelist": _ov_fix_g77_namelist,
    "phase_with_max_real": _ov_phase_with_max_real,
    "get_field": _ov_get_field,
    "parse_prior": _ov_parse_prior,
    "parse_sum": _ov_parse_sum,
    "conc_prior": _ov_conc_prior,
    "parse_chsimu": _ov_parse_chsimu,
    "chreal": _ov_chreal,
    "check_chless": _ov_check_chless,
    "getpha": _ov_getpha,
    "areaw2": _ov_areaw2,
    "areawa": _ov_areawa,
    "areaba": _ov_areaba,
    "water_scale": _ov_water_scale,
    "ldegmx": _ov_ldegmx,
    "r_base_sol_big": _ov_r_base_sol_big,
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
