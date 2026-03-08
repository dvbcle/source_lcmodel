#!/usr/bin/env python3
"""Audit structural and semantic parity coverage against LCModel.f."""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import runpy
import sys


HEADER_RE = re.compile(
    r"^\s*(?:(REAL|INTEGER|LOGICAL|COMPLEX|DOUBLE\s+PRECISION|CHARACTER(?:\*\d+)?)\s+)?"
    r"(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?",
    flags=re.IGNORECASE,
)
DEF_RE = re.compile(r"\bdef\s+([a-zA-Z_]\w*)\s*\(")


def sanitize_name(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def parse_fortran_units(path: pathlib.Path) -> set[str]:
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = HEADER_RE.match(line)
        if not m:
            continue
        raw_name = (m.group(3) or "").strip()
        if not raw_name:
            continue
        out.add(sanitize_name(raw_name))
    return out


def parse_python_defs(path: pathlib.Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return {m.group(1) for m in DEF_RE.finditer(text)}


def parse_semantic_override_keys(path: pathlib.Path) -> set[str]:
    source = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "SEMANTIC_OVERRIDES":
                if isinstance(node.value, ast.Dict):
                    keys: set[str] = set()
                    for key in node.value.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, str):
                            keys.add(key.value)
                    return keys
    return set()


def load_semantic_override_runtime(path: pathlib.Path) -> tuple[set[str], set[str]]:
    repo_root = str(path.parent.resolve())
    inserted = False
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
        inserted = True
    try:
        ns = runpy.run_path(str(path))
    finally:
        if inserted and sys.path and sys.path[0] == repo_root:
            sys.path.pop(0)
    overrides = ns.get("SEMANTIC_OVERRIDES", {})
    placeholder = ns.get("_PLACEHOLDER_OVERRIDES", set())
    keys = set(overrides.keys()) if isinstance(overrides, dict) else set()
    placeholder_keys = set(placeholder) if isinstance(placeholder, (set, tuple, list)) else set()
    return keys, placeholder_keys


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Python parity coverage for LCModel Fortran units.")
    parser.add_argument("--fortran", default="LCModel.f")
    parser.add_argument("--scaffold", default="lcmodel/fortran_scaffold.py")
    parser.add_argument("--overrides", default="semantic_overrides.py")
    args = parser.parse_args()

    fortran_units = parse_fortran_units(pathlib.Path(args.fortran))
    scaffold_defs = parse_python_defs(pathlib.Path(args.scaffold))
    static_override_keys = parse_semantic_override_keys(pathlib.Path(args.overrides))
    override_keys, placeholder_keys = load_semantic_override_runtime(pathlib.Path(args.overrides))

    missing_scaffold = sorted(fortran_units - scaffold_defs)
    missing_overrides = sorted(fortran_units - override_keys)
    overridden = sorted(fortran_units & override_keys)

    print(f"fortran_units={len(fortran_units)}")
    print(f"scaffold_defs={len(scaffold_defs)}")
    print(f"override_keys_static_literal={len(static_override_keys)}")
    print(f"override_keys_runtime={len(override_keys)}")
    print(f"override_placeholder_keys={len(placeholder_keys)}")
    print(f"override_semantic_keys={len(override_keys - placeholder_keys)}")
    print(f"scaffold_missing={len(missing_scaffold)}")
    print(f"semantic_overrides_missing={len(missing_overrides)}")
    if overridden:
        print(f"semantic_overrides_present={len(overridden)}")
    if missing_scaffold:
        print("missing_scaffold_list=" + ",".join(missing_scaffold))
    if missing_overrides:
        print("missing_semantic_list=" + ",".join(missing_overrides))

    return 0 if not missing_scaffold else 2


if __name__ == "__main__":
    raise SystemExit(main())
