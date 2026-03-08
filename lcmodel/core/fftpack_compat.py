"""FFTPACK-style compatibility wrappers used by the LCModel port."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Sequence


def _naive_fft(values: Sequence[complex], inverse: bool = False) -> list[complex]:
    n = len(values)
    if n == 0:
        return []
    out: list[complex] = []
    sign = 1.0 if inverse else -1.0
    for k in range(n):
        total = 0j
        for t, vt in enumerate(values):
            angle = sign * 2.0 * math.pi * k * t / n
            total += complex(vt) * cmath.exp(1j * angle)
        if inverse:
            total /= n
        out.append(total)
    return out


def _fft(values: Sequence[complex]) -> tuple[complex, ...]:
    try:
        import numpy as np  # type: ignore

        return tuple(np.fft.fft(np.asarray(values, dtype=np.complex128)))
    except Exception:
        return tuple(_naive_fft(values, inverse=False))


def _ifft(values: Sequence[complex]) -> tuple[complex, ...]:
    try:
        import numpy as np  # type: ignore

        return tuple(np.fft.ifft(np.asarray(values, dtype=np.complex128)))
    except Exception:
        return tuple(_naive_fft(values, inverse=True))


@dataclass(frozen=True)
class FFTPlan:
    """Simple FFT plan placeholder mirroring FFTPACK initialization flow."""

    n: int


def fftci(n: int) -> FFTPlan:
    """Initialize a plan for size `n`."""

    if n <= 0:
        raise ValueError("n must be > 0")
    return FFTPlan(n=int(n))


def cfftf(values: Sequence[complex], plan: FFTPlan | None = None) -> tuple[complex, ...]:
    """Complex forward FFT (FFTPACK-style naming)."""

    if plan is not None and len(values) != plan.n:
        raise ValueError("values length must match FFT plan length")
    return _fft(values)


def cfftb(values: Sequence[complex], plan: FFTPlan | None = None) -> tuple[complex, ...]:
    """Complex inverse FFT (FFTPACK-style naming)."""

    if plan is not None and len(values) != plan.n:
        raise ValueError("values length must match FFT plan length")
    return _ifft(values)


def cfft_r(datat: Sequence[complex]) -> tuple[complex, ...]:
    """Compatibility alias for complex FFT used by LCModel `CFFT_r` path."""

    return cfftf(datat)


def cfftin_r(ft: Sequence[complex]) -> tuple[complex, ...]:
    """Compatibility alias for inverse complex FFT used by `CFFTIN_r`."""

    return cfftb(ft)


def csft_r(datat: Sequence[complex], ncap: int | None = None) -> tuple[complex, ...]:
    """LCModel-style shifted FFT wrapper (currently standard forward FFT)."""

    values = tuple(complex(v) for v in datat)
    if ncap is not None and ncap > 0 and len(values) != int(ncap):
        raise ValueError("ncap must match input length")
    return cfftf(values)


def csftin_r(ft: Sequence[complex], ncap: int | None = None) -> tuple[complex, ...]:
    """LCModel-style shifted inverse FFT wrapper."""

    values = tuple(complex(v) for v in ft)
    if ncap is not None and ncap > 0 and len(values) != int(ncap):
        raise ValueError("ncap must match input length")
    return cfftb(values)


def seqtot(datat: Sequence[complex]) -> tuple[complex, ...]:
    """Mimic `SEQTOT`: zero-fill to double length and compute FFT."""

    values = [complex(v) for v in datat]
    padded = values + [0j] * len(values)
    return cfftf(padded)

