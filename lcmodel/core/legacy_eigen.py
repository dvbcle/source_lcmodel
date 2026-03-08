"""Symmetric eigensolver helpers for LCModel legacy routine compatibility."""

from __future__ import annotations

import math
from typing import Sequence


def jacobi_symmetric(
    matrix: Sequence[Sequence[float]],
    *,
    max_iters: int = 120,
    tol: float = 1.0e-12,
) -> tuple[list[float], list[list[float]]]:
    """Compute eigenpairs for a real symmetric matrix via Jacobi sweeps."""

    n = len(matrix)
    if n == 0:
        return [], []
    a = [[float(matrix[i][j]) for j in range(n)] for i in range(n)]
    v = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]

    for _ in range(max_iters):
        p = 0
        q = 1
        max_off = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                val = abs(a[i][j])
                if val > max_off:
                    max_off = val
                    p, q = i, j
        if max_off <= tol:
            break

        app = a[p][p]
        aqq = a[q][q]
        apq = a[p][q]
        if abs(apq) <= tol:
            continue
        tau = (aqq - app) / (2.0 * apq)
        t = 1.0 / (abs(tau) + math.sqrt(1.0 + tau * tau))
        if tau < 0.0:
            t = -t
        c = 1.0 / math.sqrt(1.0 + t * t)
        s = t * c

        for k in range(n):
            if k == p or k == q:
                continue
            akp = a[k][p]
            akq = a[k][q]
            a[k][p] = c * akp - s * akq
            a[p][k] = a[k][p]
            a[k][q] = s * akp + c * akq
            a[q][k] = a[k][q]

        a[p][p] = c * c * app - 2.0 * s * c * apq + s * s * aqq
        a[q][q] = s * s * app + 2.0 * s * c * apq + c * c * aqq
        a[p][q] = 0.0
        a[q][p] = 0.0

        for k in range(n):
            vkp = v[k][p]
            vkq = v[k][q]
            v[k][p] = c * vkp - s * vkq
            v[k][q] = s * vkp + c * vkq

    eigvals = [a[i][i] for i in range(n)]
    order = sorted(range(n), key=lambda i: eigvals[i])
    eigvals_sorted = [eigvals[i] for i in order]
    eigvecs_sorted = [[v[r][i] for i in order] for r in range(n)]
    return eigvals_sorted, eigvecs_sorted


def tridiagonal_from_symmetric(matrix: Sequence[Sequence[float]]) -> tuple[list[float], list[float]]:
    """Compatibility helper returning diagonal/off-diagonal terms."""

    n = len(matrix)
    d = [float(matrix[i][i]) for i in range(n)]
    e = [0.0] * n
    for i in range(1, n):
        e[i] = float(matrix[i][i - 1])
    return d, e
