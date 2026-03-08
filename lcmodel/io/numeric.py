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
        out.append(float(parts[0]))
    if not out:
        raise ValueError(f"Vector file has no numeric rows: {path}")
    return out


def load_numeric_matrix(path: str | Path) -> list[list[float]]:
    """Load a dense matrix from whitespace/comma separated text."""

    rows: list[list[float]] = []
    width: int | None = None
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        parts = _clean_parts(line)
        if not parts:
            continue
        row = [float(p) for p in parts]
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


def save_numeric_vector(path: str | Path, values: Iterable[float]) -> None:
    """Helper for parity fixtures/tests."""

    text = "\n".join(f"{float(v):.12g}" for v in values) + "\n"
    Path(path).write_text(text, encoding="utf-8")

