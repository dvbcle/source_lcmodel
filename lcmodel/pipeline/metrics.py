"""Quality metrics for fit outputs."""

from __future__ import annotations

import math
from typing import Sequence


def compute_fit_quality_metrics(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    coeffs: Sequence[float],
    baseline: Sequence[float] | None = None,
) -> tuple[float, float]:
    """Return `(relative_residual, snr_estimate)` for fitted data."""

    if not matrix or not vector:
        return 0.0, 0.0

    residuals: list[float] = []
    data_norm_sq = 0.0
    peak = 0.0
    for i, row in enumerate(matrix):
        pred = 0.0
        for j, aij in enumerate(row):
            pred += float(aij) * float(coeffs[j])
        if baseline is not None and i < len(baseline):
            pred += float(baseline[i])
        yi = float(vector[i])
        residuals.append(yi - pred)
        data_norm_sq += yi * yi
        peak = max(peak, abs(yi))

    rss = sum(r * r for r in residuals)
    data_norm = math.sqrt(max(1e-30, data_norm_sq))
    rel = math.sqrt(rss) / data_norm

    mean_res = sum(residuals) / len(residuals)
    var = sum((r - mean_res) ** 2 for r in residuals) / max(1, len(residuals) - 1)
    noise_sd = math.sqrt(max(1e-30, var))
    snr = peak / noise_sd
    return rel, snr
