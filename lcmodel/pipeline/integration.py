"""Peak-integration helpers ported from Fortran `INTEGRATE` behavior."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from lcmodel.traceability import fortran_provenance


@dataclass(frozen=True)
class IntegrationResult:
    """Integration summary for a single peak window."""

    area: float
    start_index: int
    end_index: int
    baseline_level: float


@fortran_provenance("integrate")
def integrate_peak_with_local_baseline(
    values: Sequence[float],
    *,
    peak_index: int,
    start_index: int,
    end_index: int,
    border_width: int,
    spacing: float = 1.0,
) -> IntegrationResult:
    """Integrate a peak after local baseline correction.

    Behavior matches the Fortran routine:
    - shrink window symmetrically based on minima distance to the peak
    - estimate baseline from windows immediately outside the peak
    - subtract that baseline before integrating
    """

    n = len(values)
    if n == 0:
        raise ValueError("values must be non-empty")
    if not (0 <= peak_index < n):
        raise ValueError("peak_index out of bounds")
    if start_index < 0 or end_index >= n or start_index >= end_index:
        raise ValueError("invalid start/end range")
    if not (start_index <= peak_index <= end_index):
        raise ValueError("peak_index must lie within [start_index, end_index]")
    if border_width <= 0:
        raise ValueError("border_width must be > 0")

    left_min_idx = start_index
    left_min_value = float(values[left_min_idx])
    for idx in range(start_index, peak_index):
        term = float(values[idx])
        if term < left_min_value:
            left_min_value = term
            left_min_idx = idx

    right_min_idx = end_index
    right_min_value = float(values[right_min_idx])
    for idx in range(peak_index + 1, end_index + 1):
        term = float(values[idx])
        if term < right_min_value:
            right_min_value = term
            right_min_idx = idx

    left_dist = peak_index - left_min_idx
    right_dist = right_min_idx - peak_index
    half_width = max(left_dist, right_dist)
    window_start = peak_index - half_width
    window_end = peak_index + half_width

    left_slice_start = max(0, window_start - border_width)
    left_slice_end = window_start
    right_slice_start = window_end + 1
    right_slice_end = min(n, window_end + 1 + border_width)
    if left_slice_end <= left_slice_start or right_slice_end <= right_slice_start:
        raise ValueError("integration side windows are empty; choose narrower range")

    left_vals = [float(values[i]) for i in range(left_slice_start, left_slice_end)]
    right_vals = [float(values[i]) for i in range(right_slice_start, right_slice_end)]
    avg_left = sum(left_vals) / len(left_vals)
    avg_right = sum(right_vals) / len(right_vals)
    baseline = 0.5 * (avg_left + avg_right)

    area = 0.0
    for idx in range(window_start, window_end + 1):
        area += float(values[idx])
    area -= float(window_end - window_start + 1) * baseline
    area *= float(spacing)

    return IntegrationResult(
        area=area,
        start_index=window_start,
        end_index=window_end,
        baseline_level=baseline,
    )
