"""Priors integration for soft-constrained fitting."""

from __future__ import annotations

import math
from typing import Sequence


def augment_system_with_soft_priors(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    metabolite_names: Sequence[str],
    priors: dict[str, tuple[float, float]],
) -> tuple[list[list[float]], list[float]]:
    """Augment linear system with prior rows using 1/sd weighting."""

    out_matrix = [list(map(float, row)) for row in matrix]
    out_vector = [float(v) for v in vector]
    index = {name.lower(): i for i, name in enumerate(metabolite_names)}
    ncols = len(out_matrix[0]) if out_matrix else len(metabolite_names)

    for name, (mean, sd) in priors.items():
        idx = index.get(name.lower())
        if idx is None:
            continue
        weight = 1.0 / max(1e-12, float(sd))
        row = [0.0] * ncols
        row[idx] = weight
        out_matrix.append(row)
        out_vector.append(float(mean) * weight)

    return out_matrix, out_vector

