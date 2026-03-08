"""Global lineshape utilities for simplified linewidth refinement."""

from __future__ import annotations

import math
from typing import Sequence


def _gaussian_kernel(sigma: float) -> list[float]:
    if sigma <= 0.0:
        return [1.0]
    radius = max(1, int(math.ceil(3.0 * sigma)))
    kernel = []
    for k in range(-radius, radius + 1):
        kernel.append(math.exp(-(k * k) / (2.0 * sigma * sigma)))
    norm = sum(kernel)
    if norm <= 0.0:
        return [1.0]
    return [v / norm for v in kernel]


def _blur_vector(values: Sequence[float], sigma: float, *, circular: bool) -> list[float]:
    kernel = _gaussian_kernel(float(sigma))
    if len(kernel) == 1:
        return [float(v) for v in values]
    radius = len(kernel) // 2
    n = len(values)
    out = [0.0] * n
    for i in range(n):
        total = 0.0
        for kk, weight in enumerate(kernel):
            offset = kk - radius
            src = i + offset
            if circular:
                total += weight * float(values[src % n])
            elif 0 <= src < n:
                total += weight * float(values[src])
        out[i] = total
    return out


def apply_global_gaussian_lineshape(
    matrix: Sequence[Sequence[float]],
    sigma_points: float,
    *,
    circular: bool = True,
) -> tuple[tuple[float, ...], ...]:
    """Apply row-axis Gaussian broadening to each basis column."""

    if not matrix:
        return ()
    nrows = len(matrix)
    ncols = len(matrix[0])
    for row in matrix:
        if len(row) != ncols:
            raise ValueError("matrix rows must have equal width")

    cols: list[list[float]] = [[0.0] * nrows for _ in range(ncols)]
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            cols[j][i] = float(value)

    # Fortran SETUP/SOLVE broadening intent:
    # apply a shared lineshape to all basis columns for a trial nonlinear state.
    blurred_cols = [_blur_vector(col, sigma_points, circular=circular) for col in cols]
    out: list[list[float]] = [[0.0] * ncols for _ in range(nrows)]
    for j, col in enumerate(blurred_cols):
        for i, value in enumerate(col):
            out[i][j] = float(value)
    return tuple(tuple(row) for row in out)
