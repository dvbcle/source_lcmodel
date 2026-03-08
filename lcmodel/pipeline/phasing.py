"""Phase-correction helpers for spectral-domain conditioning."""

from __future__ import annotations

import cmath
import math
from typing import Sequence


def _phase_axis(n: int) -> list[float]:
    if n <= 1:
        return [0.0] * n
    return [2.0 * i / (n - 1) - 1.0 for i in range(n)]


def apply_phase(
    spectrum: Sequence[complex],
    phase0_radians: float,
    phase1_radians: float = 0.0,
) -> tuple[complex, ...]:
    """Apply phase0 + phase1*x rotation where x in [-1, 1]."""

    xaxis = _phase_axis(len(spectrum))
    out = []
    for x, v in zip(xaxis, spectrum):
        phi = float(phase0_radians) + float(phase1_radians) * x
        out.append(complex(v) * cmath.exp(-1j * phi))
    return tuple(out)


def apply_zero_order_phase(spectrum: Sequence[complex], phase_radians: float) -> tuple[complex, ...]:
    """Apply constant phase rotation to all points."""

    return apply_phase(spectrum, phase_radians, 0.0)


def estimate_zero_order_phase(spectrum: Sequence[complex], search_steps: int = 720) -> float:
    """Estimate zero-order phase by minimizing imaginary energy."""

    if search_steps <= 0:
        raise ValueError("search_steps must be > 0")
    if len(spectrum) == 0:
        return 0.0

    best_phase = 0.0
    best_imag_score = math.inf
    best_real_score = -math.inf
    for idx in range(search_steps):
        phase = -math.pi + (2.0 * math.pi * idx / search_steps)
        rotated = apply_zero_order_phase(spectrum, phase)
        imag_score = 0.0
        real_score = 0.0
        for value in rotated:
            imag_score += abs(value.imag)
            real_score += value.real
        if imag_score < best_imag_score - 1e-12:
            best_imag_score = imag_score
            best_real_score = real_score
            best_phase = phase
        elif abs(imag_score - best_imag_score) <= 1e-12 and real_score > best_real_score:
            best_real_score = real_score
            best_phase = phase
    return best_phase


def estimate_zero_first_order_phase(
    spectrum: Sequence[complex],
    *,
    zero_steps: int = 360,
    first_steps: int = 41,
    first_range_radians: float = 1.5,
) -> tuple[float, float]:
    """Grid-search estimate for (phase0, phase1) minimizing imaginary magnitude."""

    if len(spectrum) == 0:
        return 0.0, 0.0
    if zero_steps <= 0 or first_steps <= 0:
        raise ValueError("search step counts must be > 0")

    best0 = 0.0
    best1 = 0.0
    best_imag = math.inf
    best_real = -math.inf

    for i0 in range(zero_steps):
        ph0 = -math.pi + (2.0 * math.pi * i0 / zero_steps)
        for i1 in range(first_steps):
            if first_steps == 1:
                ph1 = 0.0
            else:
                frac = i1 / (first_steps - 1)
                ph1 = -first_range_radians + 2.0 * first_range_radians * frac
            rotated = apply_phase(spectrum, ph0, ph1)
            imag_score = 0.0
            real_score = 0.0
            for v in rotated:
                imag_score += abs(v.imag)
                real_score += v.real
            if imag_score < best_imag - 1e-12:
                best_imag = imag_score
                best_real = real_score
                best0 = ph0
                best1 = ph1
            elif abs(imag_score - best_imag) <= 1e-12 and real_score > best_real:
                best_real = real_score
                best0 = ph0
                best1 = ph1

    return best0, best1
