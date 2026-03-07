"""Compatibility bridge from legacy scaffold names to Python-first modules.

This module keeps the old override API usable while the codebase migrates to
the structured `lcmodel` package.
"""

from __future__ import annotations

from typing import Any

from lcmodel.core.array_ops import reverse_first_n
from lcmodel.core.axis import round_axis_endpoints
from lcmodel.core.text import (
    escape_postscript_text,
    first_non_space_index,
    int_to_compact_text,
    split_title_lines,
)
from lcmodel.io.pathing import split_output_filename_for_voxel


def split_filename(
    filename: str,
    chtype1: str,
    chtype2: str,
    chtype3: str,
    lchtype: int,
    split: Any,
    state: dict[str, Any] | None = None,
):
    """Legacy wrapper for filename splitting."""

    del state
    length = int(lchtype)
    left, right = split_output_filename_for_voxel(
        filename,
        (str(chtype1)[:length], str(chtype2)[:length], str(chtype3)[:length]),
    )
    if not right:
        right = " "
    if isinstance(split, list) and len(split) >= 2:
        split[0] = left
        split[1] = right
    return left, right


def icharst(ch: str, lch: int, state: dict[str, Any] | None = None) -> int:
    """Legacy wrapper for first non-space index."""

    del state
    return first_non_space_index(str(ch), int(lch))


def chstrip_int6(
    iarg: int, chi: Any, leni: Any, state: dict[str, Any] | None = None
):
    """Legacy wrapper for compact integer formatting."""

    del state, leni
    out = int_to_compact_text(int(iarg))
    if isinstance(chi, list):
        if chi:
            chi[0] = out
        else:
            chi.append(out)
    return out, len(out)


def split_title(state: dict[str, Any] | None = None):
    """Legacy state-mutating wrapper for title splitting."""

    if state is None:
        state = {}
    layout = split_title_lines(str(state.get("title", "")), int(state.get("ntitle", 2)))
    state["nlines_title"] = layout.line_count
    state["title_line"] = [layout.lines[0], layout.lines[1]]
    return state


def revers(x: Any, n: int, state: dict[str, Any] | None = None):
    """Legacy wrapper for in-place list reverse."""

    del state
    return reverse_first_n(x, n)


def endrnd(
    xmn: float,
    xmx: float,
    xstep: float,
    xinc: float,
    xmnrnd: Any,
    xmxrnd: Any,
    state: dict[str, Any] | None = None,
):
    """Legacy wrapper for axis endpoint rounding."""

    del state, xmnrnd, xmxrnd
    return round_axis_endpoints(xmn, xmx, xstep, xinc)


def strchk(st: str, ps: Any, state: dict[str, Any] | None = None) -> str:
    """Legacy wrapper for PostScript escaping."""

    del state
    result = escape_postscript_text(str(st))
    if isinstance(ps, list):
        if ps:
            ps[0] = result
        else:
            ps.append(result)
    return result


SEMANTIC_OVERRIDES = {
    "split_filename": split_filename,
    "icharst": icharst,
    "chstrip_int6": chstrip_int6,
    "split_title": split_title,
    "revers": revers,
    "endrnd": endrnd,
    "strchk": strchk,
}

