"""Post-fit metabolite combination utilities."""

from __future__ import annotations

import re
from typing import Sequence


_TERM_RE = re.compile(r"([+-]?)\s*([A-Za-z0-9_\-]+)")


def _evaluate_expression(
    expression: str,
    coeffs: Sequence[float],
    sds: Sequence[float],
    names: Sequence[str],
) -> tuple[float, float]:
    index = {name.lower(): i for i, name in enumerate(names)}
    total = 0.0
    var = 0.0
    for sign_text, name in _TERM_RE.findall(expression):
        sign = -1.0 if sign_text == "-" else 1.0
        idx = index.get(name.lower())
        if idx is None:
            continue
        total += sign * float(coeffs[idx])
        sd = float(sds[idx]) if idx < len(sds) else 0.0
        var += sd * sd
    return total, var**0.5


def compute_combinations(
    expressions: Sequence[str],
    coeffs: Sequence[float],
    sds: Sequence[float],
    names: Sequence[str],
) -> tuple[tuple[str, float, float], ...]:
    """Compute combined metabolite results from symbolic expressions."""

    out: list[tuple[str, float, float]] = []
    for expr in expressions:
        text = str(expr).strip()
        if not text:
            continue
        value, sd = _evaluate_expression(text, coeffs, sds, names)
        out.append((text, value, sd))
    return tuple(out)

