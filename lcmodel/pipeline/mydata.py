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
import math
from typing import Sequence

from lcmodel.core.fftpack_compat import cfft_r
from lcmodel.pipeline.phasing import (
    apply_phase,
    apply_zero_order_phase,
    estimate_zero_first_order_phase,
    estimate_zero_order_phase,
)
from lcmodel.traceability import fortran_provenance


def _coerce_complex_vector(values: Sequence[complex]) -> list[complex]:
    return [complex(v) for v in values]


def _next_pow2(n: int) -> int:
    if n <= 1:
        return 1
    return 1 << (n - 1).bit_length()


def _fft(values: Sequence[complex]) -> list[complex]:
    return list(cfft_r(values))


@dataclass(frozen=True)
class MyDataConfig:
    """Configuration for the semantic MYDATA scaffold."""

    truncate_to: int | None = None
    zero_fill_to: int | None = None
    zero_fill_to_pow2: bool = False
    conjugate_input: bool = False
    compute_fft: bool = True
    auto_phase_zero_order: bool = False
    auto_phase_first_order: bool = False
    phase_search_steps: int = 720
    phase1_search_steps: int = 41
    phase1_search_range_radians: float = 1.5
    phase_objective: str = "imag_abs"
    phase_smoothness_power: int = 6
    dwell_time_s: float = 0.0
    line_broadening_hz: float = 0.0


@dataclass(frozen=True)
class MyDataResult:
    """Outputs from the semantic MYDATA scaffold."""

    time_domain: tuple[complex, ...]
    frequency_domain: tuple[complex, ...] | None
    processing_log: tuple[str, ...]
    zero_order_phase_radians: float | None = None
    first_order_phase_radians: float | None = None


@fortran_provenance("mydata", "phasta", "rephas", "cfft_r")
def run_mydata_stage(
    time_domain: Sequence[complex],
    config: MyDataConfig = MyDataConfig(),
) -> MyDataResult:
    """Run the initial Python semantic port of MYDATA preprocessing."""

    if len(time_domain) == 0:
        raise ValueError("time_domain must not be empty")

    # Fortran MYDATA:
    # "Read the NUNFIL complex time-domain data into DATAT" then preprocess.
    data = _coerce_complex_vector(time_domain)
    log: list[str] = [f"input_points={len(data)}"]

    if config.truncate_to is not None:
        # Fortran ECC_TRUNCATE family:
        # optional truncation of usable FID range before transform.
        truncate_to = int(config.truncate_to)
        if truncate_to <= 0:
            raise ValueError("truncate_to must be > 0 when provided")
        if truncate_to < len(data):
            data = data[:truncate_to]
            log.append(f"truncate_to={truncate_to}")

    if config.conjugate_input:
        # Fortran MYDATA BRUKER path:
        # conjugate time-domain input when acquisition convention requires it.
        data = [x.conjugate() for x in data]
        log.append("conjugate_input=true")

    if config.dwell_time_s > 0.0 and config.line_broadening_hz > 0.0:
        # Fortran MYDATA smoothing window:
        # apply exp(-pi * LB * t) style apodization before FFT.
        out: list[complex] = []
        for idx, x in enumerate(data):
            t = idx * float(config.dwell_time_s)
            weight = math.exp(-math.pi * float(config.line_broadening_hz) * t)
            out.append(x * weight)
        data = out
        log.append(
            f"apodization_lb_hz={config.line_broadening_hz:.12g}@dwell={config.dwell_time_s:.12g}"
        )

    target_len = len(data)
    if config.zero_fill_to is not None:
        zf = int(config.zero_fill_to)
        if zf < len(data):
            raise ValueError("zero_fill_to must be >= current data length")
        target_len = zf
    elif config.zero_fill_to_pow2:
        # Fortran FTDATA:
        # zero-filling to FFT length used for frequency-domain fitting.
        target_len = _next_pow2(len(data))

    if target_len > len(data):
        data.extend([0j] * (target_len - len(data)))
        log.append(f"zero_fill_to={target_len}")

    spectrum: tuple[complex, ...] | None = None
    phase0: float | None = None
    phase1: float | None = None
    if config.compute_fft:
        # Fortran CFFT_r path:
        # convert DATAT to rearranged frequency-domain spectrum for analysis.
        spectrum = tuple(_fft(data))
        if config.auto_phase_first_order:
            # Fortran PHASTA:
            # search start values for zero/first-order phase corrections.
            phase0, phase1 = estimate_zero_first_order_phase(
                spectrum,
                zero_steps=config.phase_search_steps,
                first_steps=config.phase1_search_steps,
                first_range_radians=config.phase1_search_range_radians,
                objective=config.phase_objective,
                smoothness_power=config.phase_smoothness_power,
            )
            spectrum = apply_phase(spectrum, phase0, phase1)
            log.append(f"phase0={phase0:.12g}")
            log.append(f"phase1={phase1:.12g}")
        elif config.auto_phase_zero_order:
            # Fortran REPHAS/PHASE_WITH_MAX_REAL intent:
            # zero-order phase that maximizes real-part objective.
            if config.phase_objective == "smooth_real":
                phase0, _ = estimate_zero_first_order_phase(
                    spectrum,
                    zero_steps=config.phase_search_steps,
                    first_steps=1,
                    first_range_radians=0.0,
                    objective="smooth_real",
                    smoothness_power=config.phase_smoothness_power,
                )
            else:
                phase0 = estimate_zero_order_phase(spectrum, search_steps=config.phase_search_steps)
            spectrum = apply_zero_order_phase(spectrum, phase0)
            log.append(f"phase0={phase0:.12g}")
        log.append("fft=enabled")
    else:
        log.append("fft=disabled")

    return MyDataResult(
        time_domain=tuple(data),
        frequency_domain=spectrum,
        processing_log=tuple(log),
        zero_order_phase_radians=phase0,
        first_order_phase_radians=phase1,
    )
