#!/usr/bin/env python3
"""Refresh traceability manifest structure against current Fortran source."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lcmodel.traceability.manifest import (  # noqa: E402
    default_manifest_path,
    discover_fortran_units,
    load_manifest,
)
import json


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh the traceability manifest for any added/removed Fortran routines."
    )
    parser.add_argument("--fortran", default="fortran_reference/LCModel.f")
    parser.add_argument("--manifest", default=str(default_manifest_path()))
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)
    entries = [
        item
        for item in manifest.get("entries", [])
        if isinstance(item, dict) and item.get("fortran_name")
    ]
    by_name = {str(item["fortran_name"]).strip().lower(): dict(item) for item in entries}

    units = sorted(discover_fortran_units(args.fortran))
    refreshed: list[dict] = []
    added = 0
    for name in units:
        if name in by_name:
            refreshed.append(by_name[name])
            continue
        refreshed.append(
            {
                "fortran_name": name,
                "fortran_kind": "UNKNOWN",
                "fortran_source_line": None,
                "python_target": None,
                "python_target_kind": "unmapped",
                "python_source_line": None,
            }
        )
        added += 1

    manifest["fortran_source"] = str(Path(args.fortran)).replace("\\", "/")
    manifest["fortran_unit_count"] = len(units)
    manifest["entries"] = refreshed

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {manifest_path} entries={len(units)} added_unmapped={added}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
