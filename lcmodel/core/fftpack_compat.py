"""FFTPACK-style compatibility wrappers used by the LCModel port."""

from __future__ import annotations

from contextlib import contextmanager
import contextvars
from dataclasses import dataclass
import cmath
import math
from typing import Sequence

_VALID_FFT_BACKENDS = {"auto", "numpy", "pure_python"}
_fft_backend_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "lcmodel_fft_backend", default="auto"
)


def _normalize_fft_backend(name: str) -> str:
    value = str(name).strip().lower()
    if value not in _VALID_FFT_BACKENDS:
        raise ValueError(
            f"Unsupported fft backend '{name}'. Expected one of: auto, numpy, pure_python."
        )
    return value


def get_fft_backend() -> str:
    """Return the currently active FFT backend mode."""

    return _fft_backend_context.get()


@contextmanager
def use_fft_backend(name: str):
    """Temporarily set FFT backend mode for the current execution context."""

    token = _fft_backend_context.set(_normalize_fft_backend(name))
    try:
        yield
    finally:
        _fft_backend_context.reset(token)


def _naive_fft_raw(values: Sequence[complex], inverse: bool = False) -> list[complex]:
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
        out.append(total)
    return out


def _numpy_fft_raw(values: Sequence[complex], inverse: bool = False) -> tuple[complex, ...]:
    import numpy as np  # type: ignore

    arr = np.asarray(values, dtype=np.complex128)
    if inverse:
        # NumPy IFFT includes a 1/N factor; Fortran CFFTB path is unscaled.
        return tuple(np.fft.ifft(arr) * len(arr))
    return tuple(np.fft.fft(arr))


def _fft_raw(values: Sequence[complex]) -> tuple[complex, ...]:
    backend = get_fft_backend()
    if backend == "pure_python":
        return tuple(_naive_fft_raw(values, inverse=False))
    if backend == "numpy":
        try:
            return _numpy_fft_raw(values, inverse=False)
        except Exception as exc:
            raise RuntimeError("fft_backend='numpy' requires NumPy to be installed") from exc
    try:
        return _numpy_fft_raw(values, inverse=False)
    except Exception:
        return tuple(_naive_fft_raw(values, inverse=False))


def _ifft_raw(values: Sequence[complex]) -> tuple[complex, ...]:
    backend = get_fft_backend()
    if backend == "pure_python":
        return tuple(_naive_fft_raw(values, inverse=True))
    if backend == "numpy":
        try:
            return _numpy_fft_raw(values, inverse=True)
        except Exception as exc:
            raise RuntimeError("fft_backend='numpy' requires NumPy to be installed") from exc
    try:
        return _numpy_fft_raw(values, inverse=True)
    except Exception:
        return tuple(_naive_fft_raw(values, inverse=True))


def _scale_unitary(values: Sequence[complex], n: int) -> tuple[complex, ...]:
    if n <= 0:
        return ()
    factor = 1.0 / math.sqrt(float(n))
    return tuple(complex(v) * factor for v in values)


def _swap_halves(values: Sequence[complex]) -> tuple[complex, ...]:
    n = len(values)
    if n <= 1:
        return tuple(complex(v) for v in values)
    half = n // 2
    if n % 2 == 0:
        return tuple(complex(v) for v in values[half:]) + tuple(complex(v) for v in values[:half])
    # Odd-length fallback: rotate by floor(N/2) to preserve invertibility.
    return tuple(complex(v) for v in values[half:]) + tuple(complex(v) for v in values[:half])


def _unswap_halves(values: Sequence[complex]) -> tuple[complex, ...]:
    n = len(values)
    if n <= 1:
        return tuple(complex(v) for v in values)
    half = n // 2
    if n % 2 == 0:
        return tuple(complex(v) for v in values[half:]) + tuple(complex(v) for v in values[:half])
    # Inverse of rotate-left-by-floor(N/2) is rotate-right-by-floor(N/2).
    split = n - half
    return tuple(complex(v) for v in values[split:]) + tuple(complex(v) for v in values[:split])


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
    n = len(values)
    return _scale_unitary(_fft_raw(values), n)


def cfftb(values: Sequence[complex], plan: FFTPlan | None = None) -> tuple[complex, ...]:
    """Complex inverse FFT (FFTPACK-style naming)."""

    if plan is not None and len(values) != plan.n:
        raise ValueError("values length must match FFT plan length")
    n = len(values)
    return _scale_unitary(_ifft_raw(values), n)


def cfft_r(datat: Sequence[complex]) -> tuple[complex, ...]:
    """Compatibility alias for complex FFT used by LCModel `CFFT_r` path."""

    # Fortran CFFT_r performs the unitary FFT and then swaps the two halves so
    # FT(N/2+1) maps to index 1.
    return _swap_halves(cfftf(datat))


def cfftin_r(ft: Sequence[complex]) -> tuple[complex, ...]:
    """Compatibility alias for inverse complex FFT used by `CFFTIN_r`."""

    # CFFTIN_r first unrearranges the swapped halves, then runs unitary IFFT.
    return cfftb(_unswap_halves(ft))


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
