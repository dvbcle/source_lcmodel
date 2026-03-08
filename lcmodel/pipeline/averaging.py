"""Channel averaging helpers ported from AVERAGE/GETVAR-style behavior."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from lcmodel.traceability import fortran_provenance


@dataclass(frozen=True)
class ChannelAverageResult:
    """Result of weighted channel averaging in the time domain."""

    averaged: tuple[complex, ...]
    used_indices: tuple[int, ...]
    weights: tuple[float, ...]
    signals: tuple[float, ...]
    rms_values: tuple[float, ...]


@fortran_provenance("check_zero_voxels")
def detect_zero_voxels(
    channels: Sequence[Sequence[complex]], magnitude_eps: float = 0.0
) -> tuple[bool, ...]:
    """Return zero-spectrum flags matching check_zero_voxels intent."""

    threshold = max(0.0, float(magnitude_eps))
    out: list[bool] = []
    for values in channels:
        is_zero = True
        for value in values:
            if (value.real * value.real + value.imag * value.imag) > threshold:
                is_zero = False
                break
        out.append(is_zero)
    return tuple(out)


@fortran_provenance("getvar")
def estimate_tail_variance(
    datat: Sequence[complex], nback_start: int, nback_end: int
) -> float:
    """Estimate complex-tail variance using linear-regression residual SSQ."""

    n = len(datat)
    if n == 0:
        raise ValueError("datat must be non-empty")
    if nback_start < nback_end:
        raise ValueError("nback_start must be >= nback_end")

    i_start = n - int(nback_start)
    i_end = n - int(nback_end)
    if i_start < 0 or i_end >= n:
        raise ValueError("nback window is outside data range")
    if i_start > i_end:
        raise ValueError("invalid nback window")

    x_values = [float(i + 1) for i in range(i_end - i_start + 1)]
    if len(x_values) < 3:
        raise ValueError("need at least 3 points to estimate variance")
    y_real = [float(datat[i].real) for i in range(i_start, i_end + 1)]
    y_imag = [float(datat[i].imag) for i in range(i_start, i_end + 1)]

    def residual_ssq(y: Sequence[float]) -> float:
        nterm = float(len(x_values))
        sx = sum(x_values)
        sxx = sum(x * x for x in x_values)
        sy = sum(y)
        sxy = sum(x_values[i] * y[i] for i in range(len(y)))
        syy = sum(v * v for v in y)
        drn = 1.0 / nterm
        denom = sxx - drn * sx * sx
        if abs(denom) <= 1e-20:
            return 0.0
        return syy - drn * sy * sy - ((sxy - drn * sx * sy) ** 2) / denom

    return max(0.0, residual_ssq(y_real) + residual_ssq(y_imag))


def _signal_strength(values: Sequence[complex]) -> float:
    # For parity portability, use RMS magnitude as a stable signal proxy.
    if not values:
        return 0.0
    return math.sqrt(sum(v.real * v.real + v.imag * v.imag for v in values) / len(values))


@fortran_provenance("average")
def weighted_average_channels(
    channels: Sequence[Sequence[complex]],
    *,
    nback_start: int,
    nback_end: int,
    normalize_by_signal: bool,
    weight_by_variance: bool,
    selection: str = "all",
    zero_voxels: Sequence[bool] | None = None,
) -> ChannelAverageResult:
    """Average channels with AVERAGE-like normalization and weighting."""

    if not channels:
        raise ValueError("channels must be non-empty")
    length = len(channels[0])
    if length == 0:
        raise ValueError("channels must not contain empty vectors")
    for values in channels:
        if len(values) != length:
            raise ValueError("all channels must have the same length")
    if selection not in {"all", "odd", "even"}:
        raise ValueError("selection must be one of: all, odd, even")
    if zero_voxels is not None and len(zero_voxels) != len(channels):
        raise ValueError("zero_voxels length must match channels length")

    weighted_sum = [0j] * length
    used_indices: list[int] = []
    signals: list[float] = []
    rms_values: list[float] = []
    weights: list[float] = []
    total_weight = 0.0

    for idx, values in enumerate(channels):
        channel_ordinal = idx + 1
        if selection == "odd" and (channel_ordinal % 2 == 0):
            continue
        if selection == "even" and (channel_ordinal % 2 == 1):
            continue
        if zero_voxels is not None and bool(zero_voxels[idx]):
            continue

        signal = _signal_strength(values) if normalize_by_signal else 1.0
        if signal <= 0.0:
            continue
        normalized = [v / signal for v in values] if normalize_by_signal else list(values)
        if weight_by_variance:
            term = estimate_tail_variance(normalized, nback_start=nback_start, nback_end=nback_end)
            nterm = int(nback_start) - int(nback_end) + 1
            denom = max(1, 2 * nterm - 4)
            rms = math.sqrt(max(0.0, term / float(denom)))
            if rms <= 0.0:
                continue
            weight = 1.0 / (rms * rms)
        else:
            rms = 1.0
            weight = 1.0
        if weight <= 0.0:
            continue

        for j in range(length):
            weighted_sum[j] += normalized[j] * weight
        total_weight += weight
        used_indices.append(idx)
        signals.append(signal)
        rms_values.append(rms)
        weights.append(weight)

    if total_weight <= 0.0 or not used_indices:
        raise ValueError("no channels selected for averaging")
    averaged = tuple(v / total_weight for v in weighted_sum)
    return ChannelAverageResult(
        averaged=averaged,
        used_indices=tuple(used_indices),
        weights=tuple(weights),
        signals=tuple(signals),
        rms_values=tuple(rms_values),
    )
