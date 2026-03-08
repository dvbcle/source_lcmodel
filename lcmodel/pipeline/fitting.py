"""Initial nonnegative fitting stage for semantic LCModel porting."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class FitConfig:
    max_iter: int = 2000
    tolerance: float = 1e-8


@dataclass(frozen=True)
class FitStageResult:
    coefficients: tuple[float, ...]
    residual_norm: float
    iterations: int
    method: str


def _residual_norm(matrix: Sequence[Sequence[float]], vector: Sequence[float], x: Sequence[float]) -> float:
    accum = 0.0
    for i, row in enumerate(matrix):
        y = 0.0
        for j, aij in enumerate(row):
            y += float(aij) * float(x[j])
        diff = y - float(vector[i])
        accum += diff * diff
    return math.sqrt(accum)


def _coordinate_descent_nnls(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    config: FitConfig,
) -> FitStageResult:
    m = len(matrix)
    n = len(matrix[0])
    x = [0.0] * n

    # Residual r = b - A x, initialized with x=0.
    r = [float(v) for v in vector]

    for it in range(1, config.max_iter + 1):
        max_delta = 0.0
        for j in range(n):
            old_x = x[j]
            col_sq_norm = 0.0
            for i in range(m):
                aij = float(matrix[i][j])
                col_sq_norm += aij * aij
                if old_x != 0.0:
                    # Undo current coefficient contribution before coordinate update.
                    r[i] += aij * old_x

            if col_sq_norm == 0.0:
                x[j] = 0.0
                continue

            numer = 0.0
            for i in range(m):
                numer += float(matrix[i][j]) * r[i]
            new_x = max(0.0, numer / col_sq_norm)
            x[j] = new_x
            max_delta = max(max_delta, abs(new_x - old_x))

            if new_x != 0.0:
                for i in range(m):
                    r[i] -= float(matrix[i][j]) * new_x

        if max_delta <= config.tolerance:
            residual = math.sqrt(sum(v * v for v in r))
            return FitStageResult(
                coefficients=tuple(x),
                residual_norm=residual,
                iterations=it,
                method="coordinate_descent_nnls",
            )

    residual = math.sqrt(sum(v * v for v in r))
    return FitStageResult(
        coefficients=tuple(x),
        residual_norm=residual,
        iterations=config.max_iter,
        method="coordinate_descent_nnls",
    )


def run_fit_stage(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    config: FitConfig = FitConfig(),
) -> FitStageResult:
    """Solve nonnegative least squares for current semantic fit stage."""

    if not matrix or not matrix[0]:
        raise ValueError("matrix must be non-empty")
    if len(matrix) != len(vector):
        raise ValueError("matrix row count must equal vector length")
    width = len(matrix[0])
    for row in matrix:
        if len(row) != width:
            raise ValueError("matrix rows must all have same length")

    return _coordinate_descent_nnls(matrix, vector, config)
