#!/usr/bin/env python3
"""Audit traceability coverage between Fortran units and Python manifests."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import lcmodel  # noqa: F401,E402  # Ensure decorated runtime modules are imported.
from lcmodel.traceability import (  # noqa: E402
    audit_manifest,
    default_manifest_path,
    load_manifest,
    provenance_registry,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit Fortran routine traceability coverage for the pure-Python surface."
    )
    parser.add_argument("--fortran", default="fortran_reference/LCModel.f")
    parser.add_argument("--manifest", default=str(default_manifest_path()))
    parser.add_argument(
        "--skip-import-check",
        action="store_true",
        help="Skip importing python_target values in the manifest.",
    )
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)
    audit = audit_manifest(
        fortran_source=args.fortran,
        manifest=manifest,
        check_imports=not args.skip_import_check,
    )
    registry = provenance_registry()

    manifest_names = {
        str(item.get("fortran_name", "")).strip().lower()
        for item in manifest.get("entries", [])
        if isinstance(item, dict)
    }
    provenance_names = set(registry.keys())
    provenance_unmapped = sorted(name for name in provenance_names if name not in manifest_names)

    print(f"fortran_units={audit.fortran_units}")
    print(f"manifest_entries={audit.manifest_entries}")
    print(f"manifest_missing={len(audit.missing_fortran_units)}")
    print(f"manifest_unmapped={len(audit.unmapped_entries)}")
    print(f"manifest_placeholder={len(audit.placeholder_entries)}")
    print(f"manifest_import_failures={len(audit.import_failures)}")
    print(f"provenance_routines={len(provenance_names)}")
    print(f"provenance_unmapped={len(provenance_unmapped)}")

    if audit.missing_fortran_units:
        print("missing_fortran_units=" + ",".join(audit.missing_fortran_units))
    if audit.unmapped_entries:
        print("unmapped_manifest_entries=" + ",".join(audit.unmapped_entries))
    if audit.placeholder_entries:
        print("placeholder_manifest_entries=" + ",".join(audit.placeholder_entries))
    if audit.import_failures:
        print("manifest_import_failure_entries=" + ",".join(audit.import_failures))
    if provenance_unmapped:
        print("provenance_not_in_manifest=" + ",".join(provenance_unmapped))

    ok = (
        not audit.missing_fortran_units
        and not audit.unmapped_entries
        and not audit.placeholder_entries
        and not audit.import_failures
        and not provenance_unmapped
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
