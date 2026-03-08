"""Initial semantic scaffold for the legacy MYDATA stage.

Scope of this first pass:
- normalize and validate complex time-domain input
- optional truncation/conjugation
- optional zero-filling
- frequency transform (FFT) for downstream stages

This is intentionally smaller than the original Fortran MYDATA routine and is
designed to be extended incrementally with parity tests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


def _coerce_complex_vector(values: Sequence[complex]) -> list[complex]:
    return [complex(v) for v in values]


def _next_pow2(n: int) -> int:
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()


def _naive_dft(values: Sequence[complex]) -> list[complex]:
    # Fallback path if numpy is unavailable. Used for small validation cases.
    import cmath
    import math

    n = len(values)
    out: list[complex] = []
    for k in range(n):
        total = 0j
        for t, vt in enumerate(values):
            angle = -2.0 * math.pi * k * t / n
            total += vt * cmath.exp(1j * angle)
        out.append(total)
    return out


def _fft(values: Sequence[complex]) -> list[complex]:
    try:
        import numpy as np  # type: ignore

        return list(np.fft.fft(np.asarray(values, dtype=np.complex128)))
    except Exception:
        return _naive_dft(values)


@dataclass(frozen=True)
class MyDataConfig:
    """Configuration for the semantic MYDATA scaffold."""

    truncate_to: int | None = None
    zero_fill_to: int | None = None
    zero_fill_to_pow2: bool = False
    conjugate_input: bool = False
    compute_fft: bool = True


@dataclass(frozen=True)
class MyDataResult:
    """Outputs from the semantic MYDATA scaffold."""

    time_domain: tuple[complex, ...]
    frequency_domain: tuple[complex, ...] | None
    processing_log: tuple[str, ...]


def run_mydata_stage(
    time_domain: Sequence[complex],
    config: MyDataConfig = MyDataConfig(),
) -> MyDataResult:
    """Run the initial Python semantic port of MYDATA preprocessing."""

    if len(time_domain) == 0:
        raise ValueError("time_domain must not be empty")

    data = _coerce_complex_vector(time_domain)
    log: list[str] = [f"input_points={len(data)}"]

    if config.truncate_to is not None:
        truncate_to = int(config.truncate_to)
        if truncate_to <= 0:
            raise ValueError("truncate_to must be > 0 when provided")
        if truncate_to < len(data):
            data = data[:truncate_to]
            log.append(f"truncate_to={truncate_to}")

    if config.conjugate_input:
        data = [x.conjugate() for x in data]
        log.append("conjugate_input=true")

    target_len = len(data)
    if config.zero_fill_to is not None:
        zf = int(config.zero_fill_to)
        if zf < len(data):
            raise ValueError("zero_fill_to must be >= current data length")
        target_len = zf
    elif config.zero_fill_to_pow2:
        target_len = _next_pow2(len(data))

    if target_len > len(data):
        data.extend([0j] * (target_len - len(data)))
        log.append(f"zero_fill_to={target_len}")

    spectrum: tuple[complex, ...] | None = None
    if config.compute_fft:
        spectrum = tuple(_fft(data))
        log.append("fft=enabled")
    else:
        log.append("fft=disabled")

    return MyDataResult(
        time_domain=tuple(data),
        frequency_domain=spectrum,
        processing_log=tuple(log),
    )

