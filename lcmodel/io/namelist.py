"""Minimal Fortran namelist parser for LCModel control-file ingestion."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from lcmodel.models import RunConfig


_TRUE_VALUES = {".true.", "true", "t"}
_FALSE_VALUES = {".false.", "false", "f"}


def _strip_inline_comment(line: str) -> str:
    in_quote = False
    quote_char = ""
    out: list[str] = []
    for ch in line:
        if ch in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
                quote_char = ""
            out.append(ch)
            continue
        if ch == "!" and not in_quote:
            break
        out.append(ch)
    return "".join(out)


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]

    low = value.lower()
    if low in _TRUE_VALUES:
        return True
    if low in _FALSE_VALUES:
        return False

    norm = re.sub(r"([0-9])d([+-]?[0-9]+)", r"\1e\2", value, flags=re.IGNORECASE)
    try:
        return int(norm)
    except ValueError:
        pass
    try:
        return float(norm)
    except ValueError:
        return value


def parse_fortran_namelist(text: str, expected_name: str | None = None) -> dict[str, Any]:
    """Parse a single namelist block like `$LCMODL ... /`."""

    cleaned_lines = [_strip_inline_comment(line) for line in text.splitlines()]
    cleaned = "\n".join(cleaned_lines)
    start = cleaned.find("$")
    if start < 0:
        raise ValueError("No namelist start marker '$' found")

    slash = cleaned.find("/", start)
    if slash < 0:
        raise ValueError("No namelist terminator '/' found")

    header_end = cleaned.find("\n", start)
    if header_end < 0 or header_end > slash:
        header_end = slash
    header = cleaned[start + 1 : header_end].strip()
    name = header.split()[0] if header else ""
    if expected_name and name.lower() != expected_name.lower():
        raise ValueError(f"Expected namelist ${expected_name}, found ${name}")

    payload = cleaned[header_end:slash]
    tokens: list[str] = []
    cur: list[str] = []
    in_quote = False
    quote_char = ""
    for ch in payload:
        if ch in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
                quote_char = ""
            cur.append(ch)
            continue
        if ch == "," and not in_quote:
            token = "".join(cur).strip()
            if token:
                tokens.append(token)
            cur = []
            continue
        cur.append(ch)
    last = "".join(cur).strip()
    if last:
        tokens.append(last)

    result: dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            continue
        key, raw_value = token.split("=", 1)
        result[key.strip().lower()] = _parse_scalar(raw_value)
    return result


def load_run_config_from_control_file(path: str | Path) -> RunConfig:
    """Load `RunConfig` from an LCModel-style control file."""

    text = Path(path).read_text(encoding="utf-8", errors="replace")
    nml = parse_fortran_namelist(text, expected_name="LCMODL")

    title = str(nml.get("title", ""))
    ntitle = int(nml.get("ntitle", 2))
    raw_data_file = nml.get("filraw")
    basis_file = nml.get("filbas")

    output_filename = None
    for key in ("filps", "filcoo", "filtab", "filpri"):
        value = nml.get(key)
        if isinstance(value, str) and value.strip():
            output_filename = value
            break

    return RunConfig(
        title=title,
        ntitle=ntitle,
        output_filename=output_filename,
        raw_data_file=str(raw_data_file) if raw_data_file else None,
        basis_file=str(basis_file) if basis_file else None,
    )

