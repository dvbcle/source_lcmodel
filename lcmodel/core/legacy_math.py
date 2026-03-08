"""Legacy numerical helpers ported from LCModel Fortran routines."""

from __future__ import annotations

import math
from typing import Sequence


def diff(x: float, y: float) -> float:
    """Fortran DIFF helper used by Lawson-Hanson style code."""

    return float(x) - float(y)


def pythag(a: float, b: float) -> float:
    """Stable `sqrt(a**2 + b**2)` from EISPACK `PYTHAG`."""

    p = max(abs(float(a)), abs(float(b)))
    if p == 0.0:
        return 0.0
    r = (min(abs(float(a)), abs(float(b))) / p) ** 2
    while True:
        t = 4.0 + r
        if t == 4.0:
            return p
        s = r / t
        u = 1.0 + 2.0 * s
        p = u * p
        r = ((s / u) ** 2) * r


def dgamln(xarg: float) -> float:
    """Compute `ln(gamma(xarg))` for positive xarg using LCModel algorithm."""

    x = float(xarg)
    if x <= 0.0:
        raise ValueError("xarg must be positive")
    p = 1.0
    out = 0.0
    while x < 30.0:
        p *= x
        x += 1.0
    if xarg < 30.0:
        out = -math.log(p)
    z = 1.0 / (x * x)
    out = out + (x - 0.5) * math.log(x) - x + 0.918938533204672742 - (
        (((z / 1680.0 - 1.0 / 1260.0) * z + 1.0 / 360.0) * z - 1.0 / 12.0) / x
    )
    return out


def betain(x: float, a: float, b: float, tol: float = 1.0e-8) -> float:
    """Approximate incomplete beta ratio `I_x(a,b)` with LCModel summation."""

    xx = float(x)
    aa = float(a)
    bb = float(b)
    if xx < 0.0 or xx > 1.0 or min(aa, bb) <= 0.0 or max(aa, bb) >= 2.0e4:
        raise ValueError("invalid betain arguments")

    swap = xx > 0.5
    if swap:
        xx = 1.0 - xx
        aa, bb = bb, aa

    cx = 1.0 - xx
    if min(xx, x) <= 0.0 or max(cx, x) >= 1.0:
        # Mirrors early return behavior in Fortran.
        out = float(x)
        if swap:
            out = 1.0 - out
        return out

    r = xx / cx
    imax = max(0, int((r * bb - aa - 1.0) / (r + 1.0)))
    dri = float(imax)
    termax = (
        (aa + dri) * math.log(xx)
        + (bb - dri - 1.0) * math.log(cx)
        + dgamln(aa + bb)
        - dgamln(aa + dri + 1.0)
        - dgamln(bb - dri)
    )
    if termax < -50.0:
        total = 0.0
    else:
        termax = math.exp(termax)
        term = termax
        total = term

        for i in range(imax + 1, 40001):
            tnumer = bb - float(i)
            term = term * r * tnumer / (aa + float(i))
            total += term
            if abs(term) <= tol * max(abs(total), 1.0e-30) or abs(tnumer) <= 1.0e-3:
                break
        if imax != 0:
            term = termax
            for i in range(imax, 0, -1):
                ri = float(i)
                denom = r * (bb - ri)
                if abs(denom) <= 1.0e-30:
                    break
                term = term * (aa + ri) / denom
                total += term
                if abs(term) <= tol * max(abs(total), 1.0e-30):
                    break

    out = float(total)
    if swap:
        out = 1.0 - out
    return out


def fishni(f: float, df1: float, df2: float) -> float:
    """F-distribution CDF helper used by LCModel."""

    d1 = float(df1)
    d2 = float(df2)
    if min(d1, d2) <= 0.0:
        raise ValueError("df1 and df2 must be positive")
    dum = d1 * float(f)
    return betain(dum / (d2 + dum), 0.5 * d1, 0.5 * d2)


def icycle_r(j: int, ndata: int) -> int:
    """Clamp-style index mapping for rearranged arrays (1-based)."""

    n = int(ndata)
    if n <= 0:
        raise ValueError("ndata must be positive")
    return max(1, min(n, int(j)))


def icycle(j: int, ndata: int) -> int:
    """Cyclic index mapping for arrays (1-based)."""

    n = int(ndata)
    if n <= 0:
        raise ValueError("ndata must be positive")
    k = int(j) - 1 + n
    if k < 0:
        raise ValueError("j must be greater than -ndata")
    return (k % n) + 1


def nextre(
    parnl: Sequence[float],
    nside2: int,
    dgauss: Sequence[float],
    thrlin: float,
    imethd: int,
) -> int:
    """Count extrema using LCModel NEXTRE policy."""

    if int(imethd) == 2:
        return 99
    n = int(nside2)
    if n <= 0 or len(parnl) < n:
        raise ValueError("invalid nside2/parnl length")
    if len(dgauss) < n + 3:
        raise ValueError("dgauss must have length >= nside2 + 3")

    dpy = [0.0] * (n + 3)
    dsum = 1.0 - sum(float(parnl[j]) for j in range(n))
    imiddl = n // 2 + 1  # zero-based index of midpoint in dpy.
    jpar = 0
    for jpy in range(1, n + 2):
        if jpy == imiddl:
            dpy[jpy] = dsum
        else:
            dpy[jpy] = float(parnl[jpar])
            jpar += 1

    smoothed = [0.0] * (n + 3)
    dthr = 0.0
    for jpy in range(n + 3):
        term = 0.0
        for kpy in range(n + 3):
            term += dpy[kpy] * float(dgauss[abs(kpy - jpy)])
        smoothed[jpy] = term
        dthr = max(dthr, abs(term))
    dthr *= float(thrlin)

    extrema_abs = [0.0]
    for jpar in range(1, n + 2):
        left = smoothed[jpar] - smoothed[jpar - 1]
        right = smoothed[jpar + 1] - smoothed[jpar]
        if left * right < 0.0:
            extrema_abs.append(abs(smoothed[jpar]))
    extrema_abs.append(0.0)
    count = 0
    for j in range(1, len(extrema_abs) - 1):
        if max(extrema_abs[j], min(extrema_abs[j + 1], extrema_abs[j - 1])) > dthr:
            count += 1
    return count


def inflec(
    parnl: Sequence[float],
    nside2: int,
    dgauss: Sequence[float],
    thrlin: float,
    imethd: int,
) -> int:
    """Count inflection points using LCModel INFLEC policy."""

    if int(imethd) == 2:
        return 99
    n = int(nside2)
    if n <= 0 or len(parnl) < n:
        raise ValueError("invalid nside2/parnl length")
    if len(dgauss) < n + 5:
        raise ValueError("dgauss must have length >= nside2 + 5")

    dpy = [0.0] * (n + 5)
    dsum = 1.0 - sum(float(parnl[j]) for j in range(n))
    imiddl = n // 2 + 2  # zero-based midpoint index in dpy.
    jpar = 0
    for jpy in range(2, n + 3):
        if jpy == imiddl:
            dpy[jpy] = dsum
        else:
            dpy[jpy] = float(parnl[jpar])
            jpar += 1

    smoothed = [0.0] * (n + 5)
    dthr = 0.0
    for jpy in range(n + 5):
        term = 0.0
        for kpy in range(n + 5):
            term += dpy[kpy] * float(dgauss[abs(kpy - jpy)])
        smoothed[jpy] = term
        dthr = max(dthr, abs(term))
    dthr *= float(thrlin)

    count = 0
    delold = smoothed[2]
    for jpar in range(2, n + 4):
        delt = smoothed[jpar - 1] - 2.0 * smoothed[jpar] + smoothed[jpar + 1]
        if delt * delold < 0.0 and abs(smoothed[jpar]) > dthr:
            count += 1
        delold = delt
    return count
