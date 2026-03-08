"""Initial nonnegative fitting stage for semantic LCModel porting."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class FitConfig:
    max_iter: int = 2000
    tolerance: float = 1e-8
    baseline_order: int = -1
    alternating_iters: int = 6


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


def _build_polynomial_basis(length: int, order: int) -> list[list[float]]:
    if order < 0:
        return []
    if length <= 1:
        xs = [0.0] * length
    else:
        xs = [2.0 * i / (length - 1) - 1.0 for i in range(length)]
    basis: list[list[float]] = []
    for k in range(order + 1):
        basis.append([x ** k for x in xs])
    return basis


def _solve_linear_system(a: list[list[float]], b: list[float]) -> list[float]:
    """Solve Ax=b with Gaussian elimination for small dense systems."""

    n = len(a)
    aug = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = col
        max_abs = abs(aug[col][col])
        for r in range(col + 1, n):
            if abs(aug[r][col]) > max_abs:
                max_abs = abs(aug[r][col])
                pivot = r
        if max_abs == 0.0:
            return [0.0] * n
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        for c in range(col, n + 1):
            aug[col][c] /= pivot_val
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]
    return [aug[i][n] for i in range(n)]


def _least_squares_baseline(
    residual: Sequence[float],
    order: int,
) -> tuple[list[float], list[float]]:
    basis_cols = _build_polynomial_basis(len(residual), order)
    if not basis_cols:
        return [], [0.0] * len(residual)
    p = len(basis_cols)

    # Normal equations: (X^T X) beta = X^T y
    xtx = [[0.0] * p for _ in range(p)]
    xty = [0.0] * p
    for i in range(len(residual)):
        yi = float(residual[i])
        for a in range(p):
            xa = basis_cols[a][i]
            xty[a] += xa * yi
            for b in range(p):
                xtx[a][b] += xa * basis_cols[b][i]
    beta = _solve_linear_system(xtx, xty)
    baseline = [0.0] * len(residual)
    for i in range(len(residual)):
        total = 0.0
        for k in range(p):
            total += beta[k] * basis_cols[k][i]
        baseline[i] = total
    return beta, baseline


def _alternating_nnls_with_baseline(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    config: FitConfig,
) -> FitStageResult:
    baseline = [0.0] * len(vector)
    x = [0.0] * len(matrix[0])

    for alt in range(1, max(1, config.alternating_iters) + 1):
        y_minus_baseline = [float(vector[i]) - baseline[i] for i in range(len(vector))]
        nnls = _coordinate_descent_nnls(
            matrix,
            y_minus_baseline,
            FitConfig(max_iter=config.max_iter, tolerance=config.tolerance),
        )
        x = list(nnls.coefficients)

        fitted = [0.0] * len(vector)
        for i, row in enumerate(matrix):
            total = 0.0
            for j, aij in enumerate(row):
                total += float(aij) * x[j]
            fitted[i] = total
        residual = [float(vector[i]) - fitted[i] for i in range(len(vector))]
        _, baseline = _least_squares_baseline(residual, config.baseline_order)

        if nnls.residual_norm <= config.tolerance:
            break

    combined_residual = [0.0] * len(vector)
    for i, row in enumerate(matrix):
        total = baseline[i]
        for j, aij in enumerate(row):
            total += float(aij) * x[j]
        combined_residual[i] = total - float(vector[i])
    resnorm = math.sqrt(sum(r * r for r in combined_residual))

    return FitStageResult(
        coefficients=tuple(x),
        residual_norm=resnorm,
        iterations=alt,
        method="alt_nnls_poly_baseline",
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

    if config.baseline_order >= 0:
        return _alternating_nnls_with_baseline(matrix, vector, config)
    return _coordinate_descent_nnls(matrix, vector, config)
