#!/usr/bin/env python3
"""Export routine mapping docs from the traceability manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lcmodel.traceability import audit_manifest, default_manifest_path, load_manifest  # noqa: E402


def build_markdown(manifest: dict, fortran_path: str) -> str:
    entries = [
        item
        for item in manifest.get("entries", [])
        if isinstance(item, dict) and item.get("fortran_name")
    ]
    entries = sorted(entries, key=lambda item: str(item.get("fortran_name", "")))
    audit = audit_manifest(
        fortran_source=fortran_path,
        manifest=manifest,
        check_imports=False,
    )

    lines: list[str] = []
    lines.append("# Fortran Routine Map")
    lines.append("")
    lines.append("Generated from `lcmodel/traceability/fortran_routine_manifest.json`.")
    lines.append("")
    lines.append(f"- Fortran units: `{audit.fortran_units}`")
    lines.append(f"- Manifest entries: `{audit.manifest_entries}`")
    lines.append(f"- Missing entries: `{len(audit.missing_fortran_units)}`")
    lines.append(f"- Unmapped entries: `{len(audit.unmapped_entries)}`")
    lines.append("")
    lines.append(
        "| Fortran Routine | Kind | Fortran Line | Python Target | Target Kind |"
    )
    lines.append("| --- | --- | ---: | --- | --- |")

    for item in entries:
        lines.append(
            f"| `{item['fortran_name']}` | `{item.get('fortran_kind', '')}` | "
            f"{item.get('fortran_source_line', '')} | "
            f"`{item.get('python_target', '_missing_')}` | "
            f"`{item.get('python_target_kind', 'unknown')}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Fortran routine mapping markdown.")
    parser.add_argument("--fortran", default="fortran_reference/LCModel.f")
    parser.add_argument("--manifest", default=str(default_manifest_path()))
    parser.add_argument("--output", default="docs/FORTRAN_ROUTINE_MAP.md")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    text = build_markdown(manifest, args.fortran)
    Path(args.output).write_text(text, encoding="utf-8")
    print(f"Wrote {args.output} using {args.manifest}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
