"""Simple integer-shift alignment for fit preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from lcmodel.pipeline.fitting import FitConfig, run_fit_stage


def _shift_vector(values: Sequence[float], shift: int) -> list[float]:
    n = len(values)
    if n == 0:
        return []
    out = [0.0] * n
    for i in range(n):
        src = i - shift
        if 0 <= src < n:
            out[i] = float(values[src])
    return out


@dataclass(frozen=True)
class AlignmentResult:
    shift_points: int
    vector: tuple[float, ...]


def align_vector_by_integer_shift(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    max_shift_points: int,
) -> AlignmentResult:
    """Find shift in [-max_shift_points, max_shift_points] minimizing residual."""

    max_shift = max(0, int(max_shift_points))
    if max_shift == 0:
        return AlignmentResult(shift_points=0, vector=tuple(float(v) for v in vector))

    best_shift = 0
    best_resid = float("inf")
    best_energy = -1.0
    best_vector = [float(v) for v in vector]
    for shift in range(-max_shift, max_shift + 1):
        shifted = _shift_vector(vector, shift)
        stage = run_fit_stage(matrix, shifted, FitConfig(baseline_order=-1))
        energy = sum(abs(v) for v in shifted)
        if stage.residual_norm < best_resid - 1e-12:
            best_resid = stage.residual_norm
            best_shift = shift
            best_vector = shifted
            best_energy = energy
        elif abs(stage.residual_norm - best_resid) <= 1e-12 and energy > best_energy:
            best_shift = shift
            best_vector = shifted
            best_energy = energy
    return AlignmentResult(shift_points=best_shift, vector=tuple(best_vector))
