from __future__ import annotations

import unittest

from lcmodel.traceability import (
    audit_manifest,
    default_manifest_path,
    load_manifest,
)


class TestTraceabilityManifest(unittest.TestCase):
    def test_manifest_covers_fortran_units_without_placeholders(self):
        manifest = load_manifest(default_manifest_path())
        audit = audit_manifest(
            fortran_source="fortran_reference/LCModel.f",
            manifest=manifest,
            check_imports=True,
        )
        self.assertEqual(149, audit.fortran_units)
        self.assertEqual(149, audit.manifest_entries)
        self.assertEqual((), audit.missing_fortran_units)
        self.assertEqual((), audit.unmapped_entries)
        self.assertEqual((), audit.placeholder_entries)
        self.assertEqual((), audit.import_failures)


if __name__ == "__main__":
    unittest.main()
