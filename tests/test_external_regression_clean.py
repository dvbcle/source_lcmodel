from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import unittest
import uuid
from unittest.mock import patch

from tools.run_external_regression_clean import run_clean_regression


class TestExternalRegressionClean(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _write_minimal_fixture(self, fixture: Path) -> None:
        (fixture / "control.file").write_text("$LCMODL /\n", encoding="utf-8")
        (fixture / "data.raw").write_text("1\n2\n", encoding="utf-8")
        (fixture / "3t.basis").write_text("1 0\n0 1\n", encoding="utf-8")
        (fixture / "out_ref_build.ps").write_text("%!PS-Adobe-2.0\n", encoding="utf-8")

    def test_rejects_stale_generated_files_in_fixture(self):
        p = self._make_local_tmpdir()
        try:
            fixture = p / "fixture"
            artifacts = p / "artifacts"
            fixture.mkdir(parents=True, exist_ok=True)
            artifacts.mkdir(parents=True, exist_ok=True)
            self._write_minimal_fixture(fixture)
            (fixture / "out.ps").write_text("stale\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "stale generated files"):
                run_clean_regression(fixture, p, artifacts)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_flags_hygiene_issue_when_preexisting_input_changes(self):
        p = self._make_local_tmpdir()
        try:
            fixture = p / "fixture"
            artifacts = p / "artifacts"
            fixture.mkdir(parents=True, exist_ok=True)
            artifacts.mkdir(parents=True, exist_ok=True)
            self._write_minimal_fixture(fixture)

            def fake_run(*args, **kwargs):
                cwd = Path(kwargs["cwd"])
                (cwd / "out.ps").write_text("%!PS\n", encoding="utf-8")
                # Simulate accidental input mutation by runtime/tooling.
                (cwd / "data.raw").write_text("mutated\n", encoding="utf-8")
                return subprocess.CompletedProcess(args=args[0], returncode=0)

            with patch(
                "tools.run_external_regression_clean.subprocess.run", side_effect=fake_run
            ):
                summary = run_clean_regression(fixture, p, artifacts)

            self.assertFalse(summary.hygiene_ok)
            self.assertTrue(
                any(
                    issue.startswith("modified_preexisting_files=data.raw")
                    for issue in summary.hygiene_issues
                )
            )
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_hygiene_ok_for_isolated_generated_output(self):
        p = self._make_local_tmpdir()
        try:
            fixture = p / "fixture"
            artifacts = p / "artifacts"
            fixture.mkdir(parents=True, exist_ok=True)
            artifacts.mkdir(parents=True, exist_ok=True)
            self._write_minimal_fixture(fixture)

            def fake_run(*args, **kwargs):
                cwd = Path(kwargs["cwd"])
                (cwd / "out.ps").write_text("%!PS\n", encoding="utf-8")
                return subprocess.CompletedProcess(args=args[0], returncode=0)

            with patch(
                "tools.run_external_regression_clean.subprocess.run", side_effect=fake_run
            ):
                summary = run_clean_regression(fixture, p, artifacts)

            self.assertTrue(summary.hygiene_ok)
            self.assertEqual((), summary.hygiene_issues)
            self.assertTrue((summary.run_dir / "run_summary.txt").exists())
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
