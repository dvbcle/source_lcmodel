"""Legacy linear-algebra helpers ported from LCModel Fortran routines."""

from __future__ import annotations

import math
from typing import Sequence


def g1(a: float, b: float) -> tuple[float, float, float]:
    """Compute Givens rotation coefficients `(cos, sin, sig)`."""

    av = abs(float(a))
    bv = abs(float(b))
    if av > bv:
        xr = float(b) / float(a)
        yr = math.sqrt(1.0 + xr * xr)
        cos_v = math.copysign(1.0 / yr, float(a))
        sin_v = cos_v * xr
        sig = av * yr
        return cos_v, sin_v, sig
    if b != 0.0:
        xr = float(a) / float(b)
        yr = math.sqrt(1.0 + xr * xr)
        sin_v = math.copysign(1.0 / yr, float(b))
        cos_v = sin_v * xr
        sig = bv * yr
        return cos_v, sin_v, sig
    return 0.0, 1.0, 0.0


def g2(cos_v: float, sin_v: float, x: float, y: float) -> tuple[float, float]:
    """Apply Givens rotation from `g1` to `(x, y)`."""

    xr = float(cos_v) * float(x) + float(sin_v) * float(y)
    yr = -float(sin_v) * float(x) + float(cos_v) * float(y)
    return xr, yr


def _uget(u: Sequence[float], iue: int, j: int) -> float:
    return float(u[(j - 1) * iue])


def _uset(u: list[float], iue: int, j: int, value: float) -> None:
    u[(j - 1) * iue] = float(value)


def h12(
    mode: int,
    lpivot: int,
    l1: int,
    m: int,
    u: list[float],
    iue: int,
    up: float,
    c: list[float],
    ice: int,
    icv: int,
    ncv: int,
    range_: float,
) -> float:
    """Construct/apply a single Householder transform (Lawson-Hanson H12)."""

    if lpivot <= 0 or lpivot >= l1 or l1 > m:
        return float(up)

    one = 1.0
    rangin = one / float(range_)
    cl = abs(_uget(u, iue, lpivot))
    if int(mode) != 2:
        for j in range(l1, m + 1):
            cl = max(abs(_uget(u, iue, j)), cl)
        if cl <= rangin:
            return float(up)
        clinv = one / cl
        sm = (_uget(u, iue, lpivot) * clinv) ** 2
        for j in range(l1, m + 1):
            sm += (_uget(u, iue, j) * clinv) ** 2
        cl = -math.copysign(cl * math.sqrt(sm), _uget(u, iue, lpivot))
        up = _uget(u, iue, lpivot) - cl
        _uset(u, iue, lpivot, cl)
    else:
        if cl <= rangin:
            return float(up)

    if ncv <= 0:
        return float(up)
    b = float(up) * _uget(u, iue, lpivot)
    if b >= -rangin:
        return float(up)
    b = one / b
    i2 = 1 - icv + ice * (lpivot - 1)
    incr = ice * (l1 - lpivot)
    for _ in range(1, ncv + 1):
        i2 += icv
        i3 = i2 + incr
        i4 = i3
        sm = float(c[i2 - 1]) * float(up)
        for i in range(l1, m + 1):
            sm += float(c[i3 - 1]) * _uget(u, iue, i)
            i3 += ice
        if sm == 0.0:
            continue
        sm *= b
        c[i2 - 1] = float(c[i2 - 1]) + sm * float(up)
        for i in range(l1, m + 1):
            c[i4 - 1] = float(c[i4 - 1]) + sm * _uget(u, iue, i)
            i4 += ice
    return float(up)
