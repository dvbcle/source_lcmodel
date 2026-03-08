"""Setup-stage selection logic for rows (ppm window) and basis columns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class SetupResult:
    matrix: tuple[tuple[float, ...], ...]
    vector: tuple[float, ...]
    row_indices: tuple[int, ...]
    column_indices: tuple[int, ...]
    metabolite_names: tuple[str, ...]


def prepare_fit_inputs(
    matrix: Sequence[Sequence[float]],
    vector: Sequence[float],
    *,
    ppm_axis: Sequence[float] | None = None,
    ppm_start: float | None = None,
    ppm_end: float | None = None,
    basis_names: Sequence[str] | None = None,
    include_metabolites: Sequence[str] = (),
) -> SetupResult:
    """Apply LCModel-like fit window and basis selection before solving."""

    if len(matrix) != len(vector):
        raise ValueError("matrix row count must equal vector length")
    if len(matrix) == 0 or len(matrix[0]) == 0:
        raise ValueError("matrix must be non-empty")
    ncols = len(matrix[0])
    for row in matrix:
        if len(row) != ncols:
            raise ValueError("matrix rows must all have equal width")

    if ppm_axis is not None and len(ppm_axis) != len(vector):
        raise ValueError("ppm_axis length must equal vector length")

    row_indices = list(range(len(vector)))
    if ppm_axis is not None and ppm_start is not None and ppm_end is not None:
        lo = min(float(ppm_start), float(ppm_end))
        hi = max(float(ppm_start), float(ppm_end))
        row_indices = [i for i, ppm in enumerate(ppm_axis) if lo <= float(ppm) <= hi]
        if not row_indices:
            raise ValueError("ppm window selection produced zero rows")

    column_indices = list(range(ncols))
    selected_names: list[str] = []
    if basis_names is not None:
        if len(basis_names) != ncols:
            raise ValueError("basis_names length must equal matrix column count")
        selected_names = [str(n) for n in basis_names]
    else:
        selected_names = [f"basis_{j+1}" for j in range(ncols)]

    if include_metabolites:
        include_set = {name.strip().lower() for name in include_metabolites if name.strip()}
        chosen = [j for j, name in enumerate(selected_names) if name.lower() in include_set]
        if not chosen:
            raise ValueError("include_metabolites selection produced zero columns")
        column_indices = chosen
        selected_names = [selected_names[j] for j in column_indices]

    out_matrix: list[tuple[float, ...]] = []
    out_vector: list[float] = []
    for i in row_indices:
        out_vector.append(float(vector[i]))
        out_matrix.append(tuple(float(matrix[i][j]) for j in column_indices))

    return SetupResult(
        matrix=tuple(out_matrix),
        vector=tuple(out_vector),
        row_indices=tuple(row_indices),
        column_indices=tuple(column_indices),
        metabolite_names=tuple(selected_names),
    )

