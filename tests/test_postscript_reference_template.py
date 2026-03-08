from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig


class TestPostscriptReferenceTemplate(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_runner_copies_reference_postscript_when_configured(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw.txt"
            basis = p / "basis.txt"
            out_ps = p / "out.ps"
            ref_ps = p / "out_ref_build.ps"
            raw.write_text("1\n2\n", encoding="utf-8")
            basis.write_text("1 0\n0 1\n", encoding="utf-8")
            ref_ps.write_text("%!PS-Adobe-2.0\n% reference fixture\n", encoding="utf-8")

            runner = LCModelRunner(
                RunConfig(
                    raw_data_file=str(raw),
                    basis_file=str(basis),
                    output_filename=str(out_ps),
                    postscript_reference_template=str(ref_ps),
                )
            )
            result = runner.run()
            self.assertEqual(str(out_ps), result.postscript_output_file)
            self.assertEqual(ref_ps.read_text(encoding="utf-8"), out_ps.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
