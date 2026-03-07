#!/usr/bin/env python3
"""Convert fixed-form Fortran 77 source into a Python scaffold module.

Design intent:
- Give Python developers a navigable, routine-by-routine map of the Fortran code.
- Preserve provenance (source file + line) for every emitted statement comment.
- Keep conversion deterministic so regenerated output is stable during review.

Current scope:
- Structural conversion only. Program units are mapped to Python functions.
- Fortran body lines are preserved as comments inside each function.
- Control-flow and numeric semantics are not automatically reproduced yet.

This tool is meant to be the foundation for iterative semantic porting.
"""

from __future__ import annotations

import argparse
import pathlib
import re
from dataclasses import dataclass


COMMENT_LEADS = {"c", "C", "*", "!"}


@dataclass
class Statement:
    source_file: str
    lineno: int
    label: str
    text: str
    is_comment: bool = False


@dataclass
class Unit:
    kind: str
    name: str
    args: list[str]
    header: Statement
    body: list[Statement]


def sanitize_name(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def split_args(raw: str) -> list[str]:
    raw = raw.strip()
    if not raw:
        return []
    args = [a.strip() for a in raw.split(",")]
    cleaned: list[str] = []
    for item in args:
        if not item:
            continue
        cleaned.append(sanitize_name(item))
    return cleaned


def preprocess_fixed_form(path: pathlib.Path) -> list[Statement]:
    """Read one fixed-form Fortran file and collapse continuation lines.

    Fixed-form rules used here:
    - Column 1 comment marker (`C`, `c`, `*`, `!`) => whole-line comment.
    - Columns 1-5 optional numeric label.
    - Column 6 continuation marker.
    - Column 7+ statement text.
    """

    statements: list[Statement] = []
    current: Statement | None = None

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for lineno, raw in enumerate(f, start=1):
            line = raw.rstrip("\n")
            padded = f"{line:<6}"

            if not line.strip():
                if current is not None:
                    statements.append(current)
                    current = None
                statements.append(
                    Statement(
                        source_file=str(path.name),
                        lineno=lineno,
                        label="",
                        text="",
                        is_comment=True,
                    )
                )
                continue

            if padded[0] in COMMENT_LEADS:
                if current is not None:
                    statements.append(current)
                    current = None
                statements.append(
                    Statement(
                        source_file=str(path.name),
                        lineno=lineno,
                        label="",
                        text=line.strip(),
                        is_comment=True,
                    )
                )
                continue

            label = (line[:5] if len(line) >= 5 else line).strip()
            cont = line[5] if len(line) > 5 else " "
            text = (line[6:] if len(line) > 6 else "").rstrip()

            if cont.strip():
                if current is None:
                    current = Statement(
                        source_file=str(path.name),
                        lineno=lineno,
                        label=label,
                        text=text.strip(),
                        is_comment=False,
                    )
                else:
                    continuation = text.strip()
                    if continuation:
                        if current.text and not current.text.endswith(" "):
                            current.text += " "
                        current.text += continuation
                continue

            if current is not None:
                statements.append(current)

            current = Statement(
                source_file=str(path.name),
                lineno=lineno,
                label=label,
                text=text.strip(),
                is_comment=False,
            )

    if current is not None:
        statements.append(current)

    return statements


HEADER_RE = re.compile(
    r"^(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?\s*(?:\((.*)\))?$",
    flags=re.IGNORECASE,
)


def parse_units(
    statements: list[Statement],
) -> tuple[list[Statement], list[Unit], list[Statement]]:
    """Split preprocessed statements into Fortran program units.

    Returns:
    - preamble: comments before the first program unit.
    - units: parsed PROGRAM/SUBROUTINE/FUNCTION/BLOCK DATA units.
    - dangling: trailing statements outside any recognized program unit.
    """

    preamble: list[Statement] = []
    units: list[Unit] = []
    dangling: list[Statement] = []
    pending_between: list[Statement] = []

    current: Unit | None = None
    seen_first = False

    for st in statements:
        if st.is_comment:
            if current is None and not seen_first:
                preamble.append(st)
            elif current is None:
                pending_between.append(st)
            else:
                current.body.append(st)
            continue

        text = st.text.strip()
        m = HEADER_RE.match(text)
        if m:
            kind = re.sub(r"\s+", " ", m.group(1).upper())
            raw_name = (m.group(2) or f"anonymous_{len(units)+1}").strip()
            arg_text = (m.group(3) or "").strip()

            if current is not None:
                units.append(current)
            current = Unit(
                kind=kind,
                name=raw_name,
                args=split_args(arg_text),
                header=st,
                body=[],
            )
            if pending_between:
                current.body.extend(pending_between)
                pending_between = []
            seen_first = True
            continue

        if current is None:
            if seen_first:
                pending_between.append(st)
            else:
                preamble.append(st)
            continue

        if text.upper() == "END":
            units.append(current)
            current = None
            continue

        current.body.append(st)

    if current is not None:
        units.append(current)
    elif pending_between:
        dangling = pending_between

    return preamble, units, dangling


def py_comment(text: str) -> str:
    cleaned = text.rstrip()
    return f"# {cleaned}" if cleaned else "#"


def emit_unit(unit: Unit, ordinal: int) -> str:
    """Emit one Python function scaffold for a single Fortran program unit."""

    py_name = sanitize_name(unit.name)
    if unit.kind == "PROGRAM":
        py_name = py_name or f"program_{ordinal}"
    elif unit.kind == "BLOCK DATA":
        py_name = py_name or f"block_data_{ordinal}"

    arg_names = unit.args.copy()
    args = arg_names.copy()
    args.append("state=None")

    lines: list[str] = []
    signature = ", ".join(args)
    lines.append(f"def {py_name}({signature}):")
    lines.append(
        f'    """Auto-converted from {unit.kind} {unit.name} ({unit.header.source_file}:{unit.header.lineno})."""'
    )
    lines.append("    if state is None:")
    lines.append("        state = {}")
    lines.append("    _ = state")
    call_args = ", ".join(arg_names + ["state"]) if arg_names else "state"
    lines.append(f"    override = SEMANTIC_OVERRIDES.get('{py_name}')")
    lines.append("    if override is not None:")
    lines.append(f"        return override({call_args})")
    lines.append("    # Porting note:")
    lines.append("    # - Insert semantic Python logic above the preserved Fortran comments.")
    lines.append("    # - Keep source-line references intact for traceability during review.")

    if unit.body:
        lines.append("    # Original Fortran statements:")
        for st in unit.body:
            ref = f"{st.source_file}:{st.lineno}"
            if st.is_comment:
                lines.append(f"    {py_comment(f'[{ref}] {st.text}')}")
            else:
                label = f" [{st.label}]" if st.label else ""
                lines.append(f"    {py_comment(f'[{ref}]{label} {st.text}')}")
    else:
        lines.append("    pass")

    lines.append("    return state")
    lines.append("")
    return "\n".join(lines)


def emit_module(
    preamble: list[Statement],
    units: list[Unit],
    dangling: list[Statement],
    src_files: list[str],
) -> str:
    """Assemble the final Python module text from parsed units."""

    out: list[str] = []
    out.append('"""')
    out.append("Auto-generated Python scaffold from legacy fixed-form Fortran.")
    out.append("")
    out.append("Generated by: tools/transpile_fortran77_to_python.py")
    out.append("Sources:")
    for path in src_files:
        out.append(f"- {path}")
    out.append('"""')
    out.append("")
    out.append("from __future__ import annotations")
    out.append("")
    out.append("try:")
    out.append("    from semantic_overrides import SEMANTIC_OVERRIDES")
    out.append("except Exception:")
    out.append("    # Fallback keeps scaffold runnable when overrides are absent.")
    out.append("    SEMANTIC_OVERRIDES = {}")
    out.append("")
    out.append("")
    out.append("def _identity_state(state):")
    out.append("    if state is None:")
    out.append("        return {}")
    out.append("    return state")
    out.append("")

    if preamble:
        out.append("# Preamble comments/statements from source files:")
        for st in preamble:
            ref = f"{st.source_file}:{st.lineno}"
            text = st.text if st.text else "<blank>"
            out.append(py_comment(f"[{ref}] {text}"))
        out.append("")

    for i, unit in enumerate(units, start=1):
        out.append(emit_unit(unit, i))

    out.append("def main():")
    program_units = [u for u in units if u.kind == "PROGRAM"]
    if program_units:
        first = sanitize_name(program_units[0].name)
        out.append(f"    {first}(state={{}})")
    else:
        out.append("    raise RuntimeError('No PROGRAM unit found in converted source')")
    out.append("")
    if dangling:
        out.append("# Unscoped trailing statements (not inside a program unit):")
        for st in dangling:
            ref = f"{st.source_file}:{st.lineno}"
            text = st.text if st.text else "<blank>"
            if st.is_comment:
                out.append(py_comment(f"[{ref}] {text}"))
            else:
                label = f" [{st.label}]" if st.label else ""
                out.append(py_comment(f"[{ref}]{label} {text}"))
        out.append("")

    out.append("")
    out.append("if __name__ == '__main__':")
    out.append("    main()")
    out.append("")
    return "\n".join(out)


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(
        description="Transpile fixed-form Fortran source into a Python scaffold module."
    )
    parser.add_argument(
        "sources",
        nargs="+",
        help="Input Fortran files (.f/.for/.inc) in desired scan order",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="lcmodel_converted.py",
        help="Output Python file path",
    )
    args = parser.parse_args()

    all_statements: list[Statement] = []
    resolved_sources: list[str] = []
    for src in args.sources:
        path = pathlib.Path(src)
        if not path.exists():
            raise FileNotFoundError(f"Missing source file: {src}")
        all_statements.extend(preprocess_fixed_form(path))
        resolved_sources.append(str(path))

    preamble, units, dangling = parse_units(all_statements)
    module_text = emit_module(preamble, units, dangling, resolved_sources)

    output_path = pathlib.Path(args.output)
    output_path.write_text(module_text, encoding="utf-8")
    print(f"Wrote {output_path} with {len(units)} program units.")


if __name__ == "__main__":
    main()
