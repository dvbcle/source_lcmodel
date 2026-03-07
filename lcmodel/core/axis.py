"""Axis/grid helpers used by reporting and plotting paths."""

from __future__ import annotations

from lcmodel.core.fortran_compat import fortran_nint


def round_axis_endpoints(x_min: float, x_max: float, step: float, grace: float) -> tuple[float, float]:
    """Find rounded endpoints that enclose `[x_min, x_max]`.

    Behavior mirrors legacy ENDRND:
    - endpoints are multiples of `step`
    - `grace` extends acceptance before expanding by one `step`
    """

    step = float(step)
    if step == 0.0:
        raise ValueError("step must be non-zero")

    x_min = float(x_min)
    x_max = float(x_max)
    grace = abs(float(grace))

    min_rounded = step * float(fortran_nint(x_min / step))
    if min_rounded - grace > x_min:
        min_rounded -= abs(step)

    max_rounded = step * float(fortran_nint(x_max / step))
    if max_rounded + grace < x_max:
        max_rounded += abs(step)

    return min_rounded, max_rounded

