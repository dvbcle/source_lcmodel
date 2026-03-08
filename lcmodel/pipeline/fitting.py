"""Linear fitting routines including a PNNLS-style active-set solver."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class FitConfig:
    max_iter: int = 2000
    tolerance: float = 1e-8
    baseline_order: int = -1
    baseline_knots: int = 0
    baseline_smoothness: float = 0.0
    alternating_iters: int = 6
    nonnegative_mask: tuple[bool, ...] | None = None


@dataclass(frozen=True)
class FitStageResult:
    coefficients: tuple[float, ...]
    residual_norm: float
    iterations: int
    method: str
    coefficient_sds: tuple[float, ...] = ()


def _residual_norm(matrix: Sequence[Sequence[float]], vector: Sequence[float], x: Sequence[float]) -> float:
    accum = 0.0
    for i, row in enumerate(matrix):
        y = 0.0
        for j, aij in enumerate(row):
            y += float(aij) * float(x[j])
        diff = y - float(vector[i])
        accum += diff * diff
    return math.sqrt(accum)


def _solve_passive_least_squares(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    passive: Sequence[int],
    width: int,
) -> list[float]:
    k = len(passive)
    z = [0.0] * width
    if k == 0:
        return z

    gram = [[0.0] * k for _ in range(k)]
    rhs = [0.0] * k
    for i, row in enumerate(matrix):
        bi = float(vector[i])
        for a_idx, a_col in enumerate(passive):
            va = float(row[a_col])
            rhs[a_idx] += va * bi
            for b_idx, b_col in enumerate(passive):
                gram[a_idx][b_idx] += va * float(row[b_col])

    coeffs = _solve_linear_system(gram, rhs)
    for idx, col in enumerate(passive):
        z[col] = coeffs[idx]
    return z


def _pnnls_active_set(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    config: FitConfig,
    nonnegative: Sequence[bool],
) -> FitStageResult:
    """Lawson-Hanson style active-set solve with optional sign constraints."""

    m = len(matrix)
    n = len(matrix[0])
    x = [0.0] * n
    passive: list[int] = []
    in_passive = [False] * n
    itmax = max(2 * n, config.max_iter)
    iterations = 0

    while True:
        if len(passive) >= m:
            break
        residual = [float(vector[i]) for i in range(m)]
        for i, row in enumerate(matrix):
            total = 0.0
            for j, aij in enumerate(row):
                total += float(aij) * x[j]
            residual[i] -= total

        best_score = config.tolerance
        best_j = -1
        for j in range(n):
            if in_passive[j]:
                continue
            wj = 0.0
            for i in range(m):
                wj += float(matrix[i][j]) * residual[i]
            score = wj if nonnegative[j] else abs(wj)
            if score > best_score:
                best_score = score
                best_j = j
        if best_j < 0:
            break

        in_passive[best_j] = True
        passive.append(best_j)

        while True:
            iterations += 1
            if iterations > itmax:
                return FitStageResult(
                    coefficients=tuple(x),
                    residual_norm=_residual_norm(matrix, vector, x),
                    iterations=itmax,
                    method="pnnls_active_set",
                )

            z = _solve_passive_least_squares(matrix, vector, passive, n)
            feasible = True
            alpha = 1.0

            for j in passive:
                if not nonnegative[j]:
                    continue
                if z[j] > config.tolerance:
                    continue
                feasible = False
                denom = x[j] - z[j]
                step = 0.0 if denom <= 0.0 else x[j] / denom
                if step < alpha:
                    alpha = step

            if feasible:
                x = z
                break

            for j in passive:
                x[j] = x[j] + alpha * (z[j] - x[j])

            next_passive: list[int] = []
            for j in passive:
                if nonnegative[j] and x[j] <= config.tolerance:
                    x[j] = 0.0
                    in_passive[j] = False
                else:
                    next_passive.append(j)
            passive = next_passive
            if not passive:
                break

    return FitStageResult(
        coefficients=tuple(x),
        residual_norm=_residual_norm(matrix, vector, x),
        iterations=iterations,
        method="pnnls_active_set",
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


def _build_bspline_basis(length: int, knots: int) -> list[list[float]]:
    """Build cubic B-spline basis columns on an evenly spaced grid.

    This follows the piecewise-cubic construction used in Fortran `GBACKG`.
    """

    if length <= 0 or knots < 4:
        return []
    if length == 1:
        return [[1.0] for _ in range(knots)]

    delta = (length - 1) / float(knots - 3)
    if delta <= 0.0:
        return []
    fnorm = 1.0 / (6.0 * delta**4)

    def dim(x: float, y: float) -> float:
        return x - y if x > y else 0.0

    basis = [[0.0] * length for _ in range(knots)]
    xknot = -2.0 * delta
    for j in range(knots):
        xknot += delta
        xmin = xknot - 2.0 * delta
        xmax = xknot + 2.0 * delta
        for i in range(length):
            x = float(i)
            value = (
                dim(x, xmin) ** 3
                - 4.0 * dim(x, xmin + delta) ** 3
                + 6.0 * dim(x, xknot) ** 3
                - 4.0 * dim(x, xmax - delta) ** 3
                + dim(x, xmax) ** 3
            ) * fnorm
            basis[j][i] = value
    return basis


def _build_bspline_regularizer(knots: int) -> list[list[float]]:
    """Build the no-boundary cubic-spline smoothness operator from `GBACKG`."""

    if knots < 4:
        return []
    reg = [[0.0] * knots for _ in range(knots)]
    for i in range(knots):
        reg[i][i] = 16.0
        if i + 1 < knots:
            reg[i][i + 1] = -9.0
        if i + 3 < knots:
            reg[i][i + 3] = 1.0

    reg[0][0] = 2.0
    reg[knots - 1][knots - 1] = 2.0
    if knots >= 2:
        reg[0][1] = -3.0
        reg[knots - 2][knots - 1] = -3.0
        reg[1][1] = 8.0
        reg[knots - 2][knots - 2] = 8.0
    if knots >= 3:
        reg[1][2] = -6.0
        reg[knots - 3][knots - 2] = -6.0
        reg[2][2] = 14.0
        reg[knots - 3][knots - 3] = 14.0

    for i in range(knots):
        for j in range(i + 1, knots):
            reg[j][i] = reg[i][j]
    return reg


def _least_squares_bspline_baseline(
    residual: Sequence[float],
    knots: int,
    smoothness: float,
) -> tuple[list[float], list[float]]:
    basis_cols = _build_bspline_basis(len(residual), knots)
    if not basis_cols:
        return [], [0.0] * len(residual)

    k = len(basis_cols)
    xtx = [[0.0] * k for _ in range(k)]
    xty = [0.0] * k
    for i in range(len(residual)):
        yi = float(residual[i])
        for a in range(k):
            xa = basis_cols[a][i]
            xty[a] += xa * yi
            for b in range(k):
                xtx[a][b] += xa * basis_cols[b][i]

    lam = max(0.0, float(smoothness))
    if lam > 0.0:
        reg = _build_bspline_regularizer(k)
        # Add lambda * (R^T R) to the normal equations.
        for i in range(k):
            for j in range(k):
                penalty = 0.0
                for t in range(k):
                    penalty += reg[t][i] * reg[t][j]
                xtx[i][j] += lam * penalty

    beta = _solve_linear_system(xtx, xty)
    baseline = [0.0] * len(residual)
    for i in range(len(residual)):
        total = 0.0
        for j in range(k):
            total += beta[j] * basis_cols[j][i]
        baseline[i] = total
    return beta, baseline


def _alternating_nnls_with_baseline(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    config: FitConfig,
    nonnegative: Sequence[bool],
) -> FitStageResult:
    baseline = [0.0] * len(vector)
    x = [0.0] * len(matrix[0])

    for alt in range(1, max(1, config.alternating_iters) + 1):
        y_minus_baseline = [float(vector[i]) - baseline[i] for i in range(len(vector))]
        nnls = _pnnls_active_set(
            matrix,
            y_minus_baseline,
            FitConfig(
                max_iter=config.max_iter,
                tolerance=config.tolerance,
                nonnegative_mask=tuple(nonnegative),
            ),
            nonnegative,
        )
        x = list(nnls.coefficients)

        fitted = [0.0] * len(vector)
        for i, row in enumerate(matrix):
            total = 0.0
            for j, aij in enumerate(row):
                total += float(aij) * x[j]
            fitted[i] = total
        residual = [float(vector[i]) - fitted[i] for i in range(len(vector))]
        if config.baseline_knots >= 4:
            _, baseline = _least_squares_bspline_baseline(
                residual,
                config.baseline_knots,
                config.baseline_smoothness,
            )
        else:
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
        method="alt_pnnls_bspline_baseline" if config.baseline_knots >= 4 else "alt_pnnls_poly_baseline",
    )


def _invert_matrix(a: list[list[float]]) -> list[list[float]] | None:
    n = len(a)
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(a)]
    for col in range(n):
        pivot = col
        max_abs = abs(aug[col][col])
        for r in range(col + 1, n):
            if abs(aug[r][col]) > max_abs:
                max_abs = abs(aug[r][col])
                pivot = r
        if max_abs <= 1e-15:
            return None
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        piv = aug[col][col]
        for c in range(2 * n):
            aug[col][c] /= piv
        for r in range(n):
            if r == col:
                continue
            factor = aug[r][col]
            if factor == 0.0:
                continue
            for c in range(2 * n):
                aug[r][c] -= factor * aug[col][c]

    inv = [row[n:] for row in aug]
    return inv


def _estimate_coefficient_sds(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    coeffs: Sequence[float],
) -> tuple[float, ...]:
    m = len(matrix)
    n = len(matrix[0])
    if m <= n:
        return tuple(0.0 for _ in range(n))

    # Build Gram matrix A^T A
    gram = [[0.0] * n for _ in range(n)]
    for i in range(m):
        row = matrix[i]
        for a in range(n):
            va = float(row[a])
            for b in range(n):
                gram[a][b] += va * float(row[b])
    inv = _invert_matrix(gram)
    if inv is None:
        return tuple(0.0 for _ in range(n))

    # Residual variance estimate.
    rss = 0.0
    for i in range(m):
        pred = 0.0
        for j in range(n):
            pred += float(matrix[i][j]) * float(coeffs[j])
        diff = pred - float(vector[i])
        rss += diff * diff
    sigma2 = rss / max(1, (m - n))

    sds = []
    for j in range(n):
        var = max(0.0, sigma2 * inv[j][j])
        sds.append(math.sqrt(var))
    return tuple(sds)


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
    if config.nonnegative_mask is None:
        nonnegative = tuple(True for _ in range(width))
    else:
        if len(config.nonnegative_mask) != width:
            raise ValueError("nonnegative_mask length must equal matrix width")
        nonnegative = tuple(bool(v) for v in config.nonnegative_mask)

    if config.baseline_order >= 0 or config.baseline_knots >= 4:
        stage = _alternating_nnls_with_baseline(matrix, vector, config, nonnegative)
    else:
        stage = _pnnls_active_set(matrix, vector, config, nonnegative)

    sds = _estimate_coefficient_sds(matrix, vector, stage.coefficients)
    return FitStageResult(
        coefficients=stage.coefficients,
        residual_norm=stage.residual_norm,
        iterations=stage.iterations,
        method=stage.method,
        coefficient_sds=sds,
    )
