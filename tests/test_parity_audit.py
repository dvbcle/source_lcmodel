from __future__ import annotations

import subprocess
import sys
import unittest


class TestParityAudit(unittest.TestCase):
    def test_audit_reports_zero_scaffold_gaps(self):
        proc = subprocess.run(
            [sys.executable, "tools/audit_parity.py"],
            check=True,
            capture_output=True,
            text=True,
        )
        out = proc.stdout
        self.assertIn("scaffold_missing=0", out)
        self.assertIn("override_placeholder_keys=0", out)
        self.assertIn("override_semantic_keys=149", out)


if __name__ == "__main__":
    unittest.main()
