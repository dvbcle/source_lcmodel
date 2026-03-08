"""Spectral conversion utilities for time-domain input workflows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage


@dataclass(frozen=True)
class SpectralFitInputs:
    vector: tuple[float, ...]
    matrix: tuple[tuple[float, ...], ...]


def _columns_from_row_major(matrix: Sequence[Sequence[complex]]) -> list[list[complex]]:
    if not matrix or not matrix[0]:
        raise ValueError("basis matrix must be non-empty")
    ncols = len(matrix[0])
    cols = [[complex(0.0, 0.0) for _ in range(len(matrix))] for _ in range(ncols)]
    for i, row in enumerate(matrix):
        if len(row) != ncols:
            raise ValueError("basis matrix rows must have equal width")
        for j, value in enumerate(row):
            cols[j][i] = complex(value)
    return cols


def _row_major_from_columns(columns: Sequence[Sequence[complex]]) -> list[list[complex]]:
    if not columns:
        return []
    nrows = len(columns[0])
    out = [[0j for _ in range(len(columns))] for _ in range(nrows)]
    for j, col in enumerate(columns):
        if len(col) != nrows:
            raise ValueError("all basis spectra columns must have same length")
        for i, val in enumerate(col):
            out[i][j] = complex(val)
    return out


def prepare_frequency_fit_from_time_domain(
    raw_time: Sequence[complex],
    basis_time: Sequence[Sequence[complex]],
    *,
    auto_phase_zero_order: bool = False,
    auto_phase_first_order: bool = False,
    phase_objective: str = "imag_abs",
    phase_smoothness_power: int = 6,
    dwell_time_s: float = 0.0,
    line_broadening_hz: float = 0.0,
) -> SpectralFitInputs:
    """Convert complex time-domain raw/basis data to real-valued fit inputs."""

    data_stage = run_mydata_stage(
        raw_time,
        MyDataConfig(
            compute_fft=True,
            auto_phase_zero_order=auto_phase_zero_order,
            auto_phase_first_order=auto_phase_first_order,
            phase_objective=phase_objective,
            phase_smoothness_power=phase_smoothness_power,
            dwell_time_s=dwell_time_s,
            line_broadening_hz=line_broadening_hz,
        ),
    )
    if data_stage.frequency_domain is None:
        raise RuntimeError("MYDATA stage did not produce frequency domain data")

    basis_columns_td = _columns_from_row_major(basis_time)
    basis_columns_fd: list[tuple[complex, ...]] = []
    for col in basis_columns_td:
        stage = run_mydata_stage(
            col,
            MyDataConfig(
                compute_fft=True,
                dwell_time_s=dwell_time_s,
                line_broadening_hz=line_broadening_hz,
            ),
        )
        if stage.frequency_domain is None:
            raise RuntimeError("basis conversion failed to produce frequency domain data")
        basis_columns_fd.append(stage.frequency_domain)

    basis_row_major_fd = _row_major_from_columns(basis_columns_fd)
    if len(basis_row_major_fd) != len(data_stage.frequency_domain):
        raise ValueError("raw and basis frequency lengths do not match")

    vector = tuple(float(v.real) for v in data_stage.frequency_domain)
    matrix = tuple(tuple(float(v.real) for v in row) for row in basis_row_major_fd)
    return SpectralFitInputs(vector=vector, matrix=matrix)
