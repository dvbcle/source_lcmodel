"""Load soft concentration priors for fit regularization."""

from __future__ import annotations

from pathlib import Path


def load_soft_priors(path: str | Path) -> dict[str, tuple[float, float]]:
    """Load priors from CSV/whitespace rows: `name mean sd`."""

    priors: dict[str, tuple[float, float]] = {}
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.replace(",", " ").split()
        if len(parts) < 3:
            raise ValueError(f"Invalid prior row (need name mean sd): {raw!r}")
        name = parts[0].strip()
        mean = float(parts[1])
        sd = float(parts[2])
        if sd <= 0:
            raise ValueError(f"Prior SD must be > 0 for {name}")
        priors[name.lower()] = (mean, sd)
    return priors

