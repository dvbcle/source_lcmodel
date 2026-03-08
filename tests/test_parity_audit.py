from __future__ import annotations

import subprocess
import sys
import unittest


class TestParityAudit(unittest.TestCase):
    def test_audit_reports_full_traceability_coverage(self):
        proc = subprocess.run(
            [sys.executable, "tools/audit_parity.py"],
            check=True,
            capture_output=True,
            text=True,
        )
        out = proc.stdout
        self.assertIn("manifest_missing=0", out)
        self.assertIn("manifest_unmapped=0", out)
        self.assertIn("manifest_placeholder=0", out)
        self.assertIn("manifest_import_failures=0", out)


if __name__ == "__main__":
    unittest.main()
