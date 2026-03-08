"""Basis metadata loaders."""

from __future__ import annotations

from pathlib import Path


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

