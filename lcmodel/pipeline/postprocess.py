"""Post-fit metabolite combination utilities."""

from __future__ import annotations

import re
from typing import Sequence

from lcmodel.traceability import fortran_provenance


_TERM_RE = re.compile(r"([+-]?)\s*([A-Za-z0-9_\-]+)")


def _plus_term_set(expression: str) -> set[str] | None:
    terms = _TERM_RE.findall(expression)
    if not terms:
        return None
    out: set[str] = set()
    for sign_text, name in terms:
        if sign_text == "-":
            return None
        out.add(name.lower())
    return out


def _apply_combis_cho_special_case(
    expressions: Sequence[str],
    names: Sequence[str],
) -> tuple[str, ...]:
    """Mirror COMBIS behavior that drops pairwise Cho/GPC/PCh if triplet exists."""

    # Fortran COMBIS keeps CHO-family reporting compact:
    # when all three pair terms and the triplet are present, keep the triplet and
    # suppress redundant pairwise sums.
    available = {str(name).strip().lower() for name in names}
    if not {"cho", "gpc", "pch"}.issubset(available):
        return tuple(str(e) for e in expressions)

    triplet = {"cho", "gpc", "pch"}
    pair_sets = ({"gpc", "pch"}, {"gpc", "cho"}, {"pch", "cho"})

    normalized = [_plus_term_set(str(expr).strip()) for expr in expressions]
    has_triplet = any(terms == triplet for terms in normalized)
    has_all_pairs = all(any(terms == pair for terms in normalized) for pair in pair_sets)
    if not has_triplet or not has_all_pairs:
        return tuple(str(e) for e in expressions)

    filtered: list[str] = []
    for expr, terms in zip(expressions, normalized):
        if terms in pair_sets:
            continue
        filtered.append(str(expr))
    return tuple(filtered)


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


@fortran_provenance("combis")
def compute_combinations(
    expressions: Sequence[str],
    coeffs: Sequence[float],
    sds: Sequence[float],
    names: Sequence[str],
) -> tuple[tuple[str, float, float], ...]:
    """Compute combined metabolite results from symbolic expressions."""

    out: list[tuple[str, float, float]] = []
    for expr in _apply_combis_cho_special_case(expressions, names):
        text = str(expr).strip()
        if not text:
            continue
        value, sd = _evaluate_expression(text, coeffs, sds, names)
        out.append((text, value, sd))
    return tuple(out)
