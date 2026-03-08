"""Simple integer-shift alignment for fit preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from lcmodel.pipeline.fitting import FitConfig, run_fit_stage


def _shift_vector(values: Sequence[float], shift: int, *, circular: bool) -> list[float]:
    n = len(values)
    if n == 0:
        return []
    out = [0.0] * n
    for i in range(n):
        src = i - shift
        if circular:
            out[i] = float(values[src % n])
        elif 0 <= src < n:
            out[i] = float(values[src])
    return out


@dataclass(frozen=True)
class AlignmentResult:
    shift_points: int
    vector: tuple[float, ...]


@dataclass(frozen=True)
class FractionalAlignmentResult:
    shift_points: float
    vector: tuple[float, ...]


def align_vector_by_integer_shift(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    max_shift_points: int,
    *,
    circular: bool = True,
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
        # Fortran SHIFTD analogue:
        # test candidate integer shifts of the analysis window.
        shifted = _shift_vector(vector, shift, circular=circular)
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


def _shift_vector_fractional(values: Sequence[float], shift: float, *, circular: bool) -> list[float]:
    n = len(values)
    if n == 0:
        return []
    out = [0.0] * n
    for i in range(n):
        src = float(i) - float(shift)
        lo = math.floor(src)
        frac = src - float(lo)
        hi = lo + 1
        if circular:
            vlo = float(values[lo % n])
            vhi = float(values[hi % n])
            out[i] = (1.0 - frac) * vlo + frac * vhi
            continue

        vlo = float(values[lo]) if 0 <= lo < n else 0.0
        vhi = float(values[hi]) if 0 <= hi < n else 0.0
        out[i] = (1.0 - frac) * vlo + frac * vhi
    return out


def align_vector_by_fractional_shift(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    max_shift_points: int,
    *,
    circular: bool = True,
    iterations: int = 18,
) -> FractionalAlignmentResult:
    """Refine alignment shift continuously in [-max_shift_points, max_shift_points]."""

    max_shift = max(0.0, float(max_shift_points))
    if max_shift == 0.0:
        return FractionalAlignmentResult(shift_points=0.0, vector=tuple(float(v) for v in vector))

    def objective(shift: float) -> tuple[float, float]:
        shifted = _shift_vector_fractional(vector, shift, circular=circular)
        stage = run_fit_stage(matrix, shifted, FitConfig(baseline_order=-1))
        energy = sum(abs(v) for v in shifted)
        # Tie-breaker mirrors LCModel preference for retaining signal support.
        return stage.residual_norm, -energy

    left = -max_shift
    right = max_shift
    best_shift = 0.0
    best_obj = (float("inf"), float("inf"))
    steps = max(4, int(iterations))
    for _ in range(steps):
        width = right - left
        s1 = left + width / 3.0
        s2 = right - width / 3.0
        o1 = objective(s1)
        o2 = objective(s2)
        if o1 < best_obj:
            best_obj = o1
            best_shift = s1
        if o2 < best_obj:
            best_obj = o2
            best_shift = s2
        if o1 <= o2:
            right = s2
        else:
            left = s1

    shifted_best = _shift_vector_fractional(vector, best_shift, circular=circular)
    return FractionalAlignmentResult(shift_points=best_shift, vector=tuple(shifted_best))
