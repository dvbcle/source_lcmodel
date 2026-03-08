"""Basis metadata and LCModel basis-file loaders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lcmodel.io.namelist import parse_fortran_namelist


def load_basis_names(path: str | Path) -> list[str]:
    """Load basis column names, one name per non-empty line."""

    names: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        names.append(line)
    if not names:
        raise ValueError(f"Basis names file has no names: {path}")
    return names


@dataclass(frozen=True)
class LcmodelBasis:
    """Parsed LCModel basis file content."""

    matrix_time_domain: tuple[tuple[complex, ...], ...]
    metabolite_names: tuple[str, ...]
    ndata: int


def is_lcmodel_basis_file(path: str | Path) -> bool:
    p = Path(path)
    if p.suffix.lower() == ".basis":
        return True
    try:
        head = p.read_text(encoding="utf-8", errors="replace")[:1024]
    except Exception:
        return False
    head_up = head.upper()
    return "$BASIS1" in head_up and "$NMUSED" in head_up and "$BASIS" in head_up


def _collect_namelist_block(lines: list[str], start: int) -> tuple[str, int]:
    block: list[str] = []
    i = start
    while i < len(lines):
        block.append(lines[i])
        if "$END" in lines[i].upper():
            return "\n".join(block), i + 1
        i += 1
    raise ValueError("Unterminated namelist block in basis file")


def _parse_basis_numeric_rows(
    lines: list[str], start: int, ndata: int, path: Path
) -> tuple[list[complex], int]:
    values: list[float] = []
    i = start
    while i < len(lines):
        raw = lines[i].strip()
        if not raw:
            i += 1
            continue
        if raw.startswith("$"):
            break
        parts = raw.replace(",", " ").split()
        try:
            values.extend(float(p) for p in parts)
        except ValueError:
            i += 1
            continue
        if len(values) >= 2 * ndata:
            break
        i += 1
    if len(values) < 2 * ndata:
        raise ValueError(
            f"Basis block in {path} has only {len(values)} numeric values, expected {2 * ndata}"
        )
    values = values[: 2 * ndata]
    vector = [complex(values[2 * j], values[2 * j + 1]) for j in range(ndata)]
    return vector, i + 1


def load_lcmodel_basis(path: str | Path) -> LcmodelBasis:
    """Load LCModel `.basis` format into row-major complex matrix."""

    p = Path(path)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()

    ndata = None
    i = 0
    while i < len(lines):
        line = lines[i].strip().upper()
        if line.startswith("$BASIS1"):
            text, i = _collect_namelist_block(lines, i)
            nml = parse_fortran_namelist(text, expected_name="BASIS1")
            try:
                ndata = int(nml.get("ndatab", 0))
            except Exception:
                ndata = 0
            break
        i += 1
    if not ndata or ndata <= 0:
        raise ValueError(f"Could not determine NDATAB from LCModel basis file: {path}")

    columns: list[list[complex]] = []
    names: list[str] = []
    pending_name = ""
    i = 0
    while i < len(lines):
        line_up = lines[i].strip().upper()
        if line_up.startswith("$NMUSED"):
            text, i = _collect_namelist_block(lines, i)
            nml = parse_fortran_namelist(text, expected_name="NMUSED")
            raw = nml.get("fileraw")
            pending_name = str(raw).strip() if raw is not None else ""
            continue
        if line_up.startswith("$BASIS") and not line_up.startswith("$BASIS1"):
            text, i = _collect_namelist_block(lines, i)
            nml = parse_fortran_namelist(text, expected_name="BASIS")
            metab = str(nml.get("metabo", "")).strip()
            basis_id = str(nml.get("id", "")).strip()
            name = metab or basis_id or pending_name or f"basis_{len(columns)+1}"
            vector, i = _parse_basis_numeric_rows(lines, i, ndata, p)
            columns.append(vector)
            names.append(name)
            pending_name = ""
            continue
        i += 1

    if not columns:
        raise ValueError(f"No BASIS blocks found in LCModel basis file: {path}")

    ncols = len(columns)
    matrix = [
        tuple(columns[col][row] for col in range(ncols))
        for row in range(ndata)
    ]
    return LcmodelBasis(
        matrix_time_domain=tuple(matrix),
        metabolite_names=tuple(names),
        ndata=ndata,
    )
