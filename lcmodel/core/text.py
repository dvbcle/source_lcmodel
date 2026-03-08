"""Text utilities used by the Python-first LCModel port."""

from __future__ import annotations

from lcmodel.core.fortran_compat import ilen
from lcmodel.models import TitleLayout
from lcmodel.traceability import fortran_provenance

ESCAPE_CHARS = {"(", ")", "%", "\\"}


@fortran_provenance("icharst")
def first_non_space_index(text: str, max_chars: int) -> int:
    """Return 1-based index of first non-space char, or -1 if none."""

    for idx in range(1, max(0, int(max_chars)) + 1):
        ch = text[idx - 1] if idx - 1 < len(text) else " "
        if ch != " ":
            return idx
    return -1


@fortran_provenance("chstrip_int6")
def int_to_compact_text(value: int, min_value: int = -99999, max_value: int = 999999) -> str:
    """Clamp to Fortran bounds and format without padding spaces."""

    clipped = max(min_value, min(max_value, int(value)))
    return str(clipped)


@fortran_provenance("strchk")
def escape_postscript_text(text: str, max_output_len: int = 123) -> str:
    """Escape PostScript-sensitive characters using STRCHK semantics."""

    out: list[str] = []
    length = 0
    trimmed = text[: ilen(text)]
    for ch in trimmed:
        if length >= 122:
            break
        if ch in ESCAPE_CHARS:
            out.extend(["\\", ch])
            length += 2
        else:
            if length >= max_output_len:
                break
            out.append(ch)
            length += 1
    return "".join(out)


@fortran_provenance("split_title")
def split_title_lines(title: str, ntitle: int = 2) -> TitleLayout:
    """Split title into one or two report lines.

    This mirrors the legacy split-title policy while returning an explicit
    dataclass instead of mutating shared state.
    """

    ltitle = ilen(title)
    title_trimmed = title[:ltitle]

    if int(ntitle) == 1 or ltitle <= 61:
        return TitleLayout(lines=(title_trimmed, ""), line_count=1)

    iend_line1 = min(ltitle, 122)
    nescape = 0
    nescape1 = 0
    for idx, ch in enumerate(title_trimmed, start=1):
        if ch in ESCAPE_CHARS:
            nescape += 1
            if idx <= iend_line1:
                nescape1 += 1

    if ltitle + nescape <= 122:
        return TitleLayout(lines=(title_trimmed, ""), line_count=1)

    max_back = 244 - ltitle - nescape
    iend_line1 -= nescape1
    ibreak = iend_line1
    istart2 = iend_line1 + 1

    lower = max(4, iend_line1 - max_back)
    for idx in range(iend_line1, lower - 1, -1):
        if 1 <= idx <= ltitle and title_trimmed[idx - 1] == " ":
            ibreak = idx - 1
            istart2 = idx + 1
            break

    line1 = title_trimmed[: max(0, ibreak)]
    line2 = title_trimmed[max(0, istart2 - 1) : ltitle]
    return TitleLayout(lines=(line1, line2), line_count=2)
