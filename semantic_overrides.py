"""Incremental semantic ports for selected LCModel Fortran routines.

The generated `lcmodel_converted.py` module looks up functions in
`SEMANTIC_OVERRIDES` by routine name. If an override exists, it is called
instead of the comment-only scaffold body.

This file is intentionally focused on small, high-confidence routines first.
"""

from __future__ import annotations

import math
from typing import Any


ESCAPE_CHARS = {"(", ")", "%", "\\"}


def _ilen(text: Any) -> int:
    """Fortran-like ILEN: length excluding trailing spaces."""

    if text is None:
        return 0
    return len(str(text).rstrip(" "))


def _fortran_nint(value: float) -> int:
    """Fortran NINT semantics (ties away from zero)."""

    if value >= 0.0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def split_filename(
    filename: str,
    chtype1: str,
    chtype2: str,
    chtype3: str,
    lchtype: int,
    split: Any,
    state: dict[str, Any] | None = None,
):
    """Port of `split_filename`.

    Returns `(split1, split2)` and also updates `split` if it is a mutable
    2-element list.
    """

    del state
    name = str(filename)
    lfile = _ilen(name)
    base = name[:lfile]
    lchtype = int(lchtype)

    split1 = f"{base}_"
    split2 = " "

    if lchtype > 0 and lfile >= lchtype:
        ichtype = lfile - lchtype + 1  # 1-based index
        suffix = base[ichtype - 1 :]
        choices = (
            str(chtype1)[:lchtype],
            str(chtype2)[:lchtype],
            str(chtype3)[:lchtype],
        )
        if any(suffix.startswith(choice) for choice in choices):
            islash_dot = ichtype - 1  # 1-based index
            if islash_dot >= 1:
                marker = base[islash_dot - 1]
                if marker in {"/", "\\"}:
                    # Case 1: ".../ps" -> ".../" + ".ps"
                    split1 = base[:islash_dot]
                    split2 = "." + base[ichtype - 1 :]
                elif marker == ".":
                    # Case 2: "... .ps" -> "..._" + ".ps"
                    split1 = base[: islash_dot - 1] + "_"
                    split2 = base[islash_dot - 1 :]

    if isinstance(split, list) and len(split) >= 2:
        split[0] = split1
        split[1] = split2
    return split1, split2


def icharst(ch: str, lch: int, state: dict[str, Any] | None = None) -> int:
    """Port of `icharst`: first non-space position (1-based), else -1."""

    del state
    text = str(ch)
    for idx in range(1, max(0, int(lch)) + 1):
        char = text[idx - 1] if idx - 1 < len(text) else " "
        if char != " ":
            return idx
    return -1


def chstrip_int6(
    iarg: int, chi: Any, leni: Any, state: dict[str, Any] | None = None
):
    """Port of `chstrip_int6`.

    Returns `(chi_text, length)` and updates mutable outputs when possible.
    """

    del state, leni
    value = max(-99999, min(999999, int(iarg)))
    out = str(value)
    if isinstance(chi, list):
        if chi:
            chi[0] = out
        else:
            chi.append(out)
    return out, len(out)


def split_title(state: dict[str, Any] | None = None):
    """Port of `split_title` using the shared `state` dictionary."""

    if state is None:
        state = {}

    title = str(state.get("title", ""))
    ntitle = int(state.get("ntitle", 2))
    ltitle = _ilen(title)
    title_trimmed = title[:ltitle]

    if ntitle == 1 or ltitle <= 61:
        state["nlines_title"] = 1
        state["title_line"] = [title_trimmed, ""]
        return state

    iend_line1 = min(ltitle, 122)
    nescape = 0
    nescape1 = 0
    for i, ch in enumerate(title_trimmed, start=1):
        if ch in ESCAPE_CHARS:
            nescape += 1
            if i <= iend_line1:
                nescape1 += 1

    if ltitle + nescape <= 122:
        state["nlines_title"] = 1
        state["title_line"] = [title_trimmed, ""]
        return state

    max_back = 244 - ltitle - nescape
    iend_line1 -= nescape1
    ibreak = iend_line1
    istart2 = iend_line1 + 1

    lower = max(4, iend_line1 - max_back)
    for i in range(iend_line1, lower - 1, -1):
        if 1 <= i <= ltitle and title_trimmed[i - 1] == " ":
            ibreak = i - 1
            istart2 = i + 1
            break

    line1 = title_trimmed[: max(0, ibreak)]
    line2 = title_trimmed[max(0, istart2 - 1) : ltitle]
    state["nlines_title"] = 2
    state["title_line"] = [line1, line2]
    return state


def revers(x: Any, n: int, state: dict[str, Any] | None = None):
    """Port of `REVERS`: in-place reverse of first `n` items."""

    del state
    n = max(0, int(n))
    j = n - 1
    i = 0
    while i < j:
        x[i], x[j] = x[j], x[i]
        i += 1
        j -= 1
    return x


def endrnd(
    xmn: float,
    xmx: float,
    xstep: float,
    xinc: float,
    xmnrnd: Any,
    xmxrnd: Any,
    state: dict[str, Any] | None = None,
):
    """Port of `ENDRND`.

    Returns `(xmnrnd_out, xmxrnd_out)` and updates mutable outputs when passed.
    """

    del state, xmnrnd, xmxrnd
    xstep = float(xstep)
    if xstep == 0.0:
        raise ValueError("xstep must be non-zero")

    xmn = float(xmn)
    xmx = float(xmx)
    xinc = abs(float(xinc))

    xmnrnd_out = xstep * float(_fortran_nint(xmn / xstep))
    if xmnrnd_out - xinc > xmn:
        xmnrnd_out -= abs(xstep)

    xmxrnd_out = xstep * float(_fortran_nint(xmx / xstep))
    if xmxrnd_out + xinc < xmx:
        xmxrnd_out += abs(xstep)

    return xmnrnd_out, xmxrnd_out


def strchk(st: str, ps: Any, state: dict[str, Any] | None = None) -> str:
    """Port of `STRCHK`: escape PostScript-sensitive characters.

    Result is truncated to 123 characters, matching Fortran output constraints.
    """

    del state
    text = str(st)
    out: list[str] = []
    ips = 0

    for ch in text[: _ilen(text)]:
        if ips >= 122:
            break
        if ch in ESCAPE_CHARS:
            out.append("\\")
            out.append(ch)
            ips += 2
        else:
            if ips >= 123:
                break
            out.append(ch)
            ips += 1

    result = "".join(out)
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

