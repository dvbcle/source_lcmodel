"""Numeric file loaders used by the semantic fitting pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _clean_parts(line: str) -> list[str]:
    line = line.strip()
    if not line:
        return []
    if line.startswith("#"):
        return []
    if line.startswith("$"):
        return []
    return line.replace(",", " ").split()


def load_numeric_vector(path: str | Path) -> list[float]:
    """Load a vector from text file.

    Supported line formats:
    - `value`
    - `real imag` (imag ignored for current real-valued fit stage)
    """

    out: list[float] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = _clean_parts(line)
        if not parts:
            continue
        try:
            out.append(float(parts[0]))
        except ValueError:
            continue
    if not out:
        raise ValueError(f"Vector file has no numeric rows: {path}")
    return out


def load_complex_vector(path: str | Path) -> list[complex]:
    """Load complex vector from text file (`re im` per row, or `re` only)."""

    out: list[complex] = []
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = _clean_parts(line)
        if not parts:
            continue
        try:
            re_part = float(parts[0])
            im_part = float(parts[1]) if len(parts) >= 2 else 0.0
        except ValueError:
            continue
        out.append(complex(re_part, im_part))
    if not out:
        raise ValueError(f"Complex vector file has no numeric rows: {path}")
    return out


def load_numeric_matrix(path: str | Path) -> list[list[float]]:
    """Load a dense matrix from whitespace/comma separated text."""

    rows: list[list[float]] = []
    width: int | None = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = _clean_parts(line)
        if not parts:
            continue
        try:
            row = [float(p) for p in parts]
        except ValueError:
            continue
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(
                f"Inconsistent row width in matrix file {path}: expected {width}, got {len(row)}"
            )
        rows.append(row)

    if not rows:
        raise ValueError(f"Matrix file has no numeric rows: {path}")
    return rows


def load_complex_matrix(path: str | Path, pair_mode: bool = True) -> list[list[complex]]:
    """Load complex matrix.

    When `pair_mode=True`, each row must be `re1 im1 re2 im2 ...`.
    """

    rows: list[list[complex]] = []
    width: int | None = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = _clean_parts(line)
        if not parts:
            continue
        values: list[float]
        try:
            values = [float(p) for p in parts]
        except ValueError:
            continue
        if pair_mode:
            if len(values) % 2 != 0:
                raise ValueError(
                    f"Complex pair-mode row has odd number of values in {path}: {line!r}"
                )
            row = [complex(values[j], values[j + 1]) for j in range(0, len(values), 2)]
        else:
            row = [complex(v, 0.0) for v in values]
        if width is None:
            width = len(row)
        elif len(row) != width:
            raise ValueError(
                f"Inconsistent row width in complex matrix file {path}: expected {width}, got {len(row)}"
            )
        rows.append(row)
    if not rows:
        raise ValueError(f"Complex matrix file has no numeric rows: {path}")
    return rows


def save_numeric_vector(path: str | Path, values: Iterable[float]) -> None:
    """Helper for parity fixtures/tests."""

    text = "\n".join(f"{float(v):.12g}" for v in values) + "\n"
    Path(path).write_text(text, encoding="utf-8")
