from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.io.report import build_fit_table_text, write_fit_table
from lcmodel.models import FitResult


class TestReportOutput(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_build_fit_table_text(self):
        fit = FitResult(
            coefficients=(1.5, 0.5),
            coefficient_sds=(0.15, 0.05),
            residual_norm=0.01,
            iterations=4,
            method="test_method",
            metabolite_names=("NAA", "Cr"),
            data_points_used=128,
        )
        text = build_fit_table_text(fit)
        self.assertIn("Metabolite\tCoefficient\tSD\t%SD", text)
        self.assertIn("NAA\t1.5\t0.15", text)
        self.assertIn("# method=test_method", text)

    def test_write_fit_table(self):
        p = self._make_local_tmpdir()
        try:
            out = p / "result.table"
            fit = FitResult(
                coefficients=(2.0,),
                coefficient_sds=(0.2,),
                residual_norm=0.0,
                iterations=2,
                method="m",
                metabolite_names=("NAA",),
                data_points_used=10,
            )
            written = write_fit_table(out, fit)
            self.assertEqual(str(out), written)
            content = out.read_text(encoding="utf-8")
            self.assertIn("NAA\t2\t0.2", content)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

