"""Batch I/O helpers for multi-spectrum processing."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


def load_path_list(path: str | Path) -> list[str]:
    """Load non-empty, non-comment file paths."""

    out: list[str] = []
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line)
    if not out:
        raise ValueError(f"Path list file has no entries: {path}")
    return out


def write_batch_csv(
    path: str | Path,
    rows: Iterable[tuple[str, tuple[float, ...], float]],
) -> str:
    """Write batch fit summary CSV."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["raw_file,residual_norm,coefficients"]
    for raw_file, coeffs, residual in rows:
        coeff_text = ";".join(f"{v:.12g}" for v in coeffs)
        lines.append(f"{raw_file},{residual:.12g},{coeff_text}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(out_path)

