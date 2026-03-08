"""Phase-correction helpers for spectral-domain conditioning."""

from __future__ import annotations

import cmath
import math
from typing import Sequence


def apply_zero_order_phase(spectrum: Sequence[complex], phase_radians: float) -> tuple[complex, ...]:
    """Apply constant phase rotation to all points."""

    rot = cmath.exp(-1j * float(phase_radians))
    return tuple(complex(v) * rot for v in spectrum)


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
