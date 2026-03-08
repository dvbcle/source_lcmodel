"""Fortran routine discovery and placeholder registration utilities."""

from __future__ import annotations

from collections.abc import Callable, Mapping, MutableMapping
from pathlib import Path
import re
from typing import Any


HEADER_RE = re.compile(
    r"^\s*(?:(REAL|INTEGER|LOGICAL|COMPLEX|DOUBLE\s+PRECISION|CHARACTER(?:\*\d+)?)\s+)?"
    r"(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?",
    flags=re.IGNORECASE,
)


def sanitize_name(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def discover_fortran_unit_names(source: Path) -> set[str]:
    if not source.exists():
        return set()
    names: set[str] = set()
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        match = HEADER_RE.match(line)
        if not match:
            continue
        raw_name = (match.group(3) or "").strip()
        if not raw_name:
            continue
        names.add(sanitize_name(raw_name))
    return names


def make_placeholder_override(name: str) -> Callable[..., dict[str, Any]]:
    def _override(*args: Any, **kwargs: Any) -> dict[str, Any]:
        state = kwargs.get("state")
        if state is None and args and isinstance(args[-1], dict):
            state = args[-1]
        if state is None:
            state = {}
        state.setdefault("placeholder_overrides", []).append(name)
        return state

    return _override


def install_missing_overrides(
    *,
    overrides: MutableMapping[str, Callable[..., Any]],
    source_file: Path,
    placeholder_set: set[str],
) -> None:
    for routine_name in discover_fortran_unit_names(source_file):
        if routine_name not in overrides:
            overrides[routine_name] = make_placeholder_override(routine_name)
            placeholder_set.add(routine_name)
