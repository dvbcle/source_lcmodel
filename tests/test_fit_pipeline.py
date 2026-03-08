from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.cli import main as cli_main
from lcmodel.engine import LCModelRunner
from lcmodel.io.numeric import (
    load_complex_matrix,
    load_complex_vector,
    load_numeric_matrix,
    load_numeric_vector,
    save_numeric_vector,
)
from lcmodel.models import RunConfig
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage


class TestFitPipeline(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_loaders_and_save(self):
        p = self._make_local_tmpdir()
        try:
            vec_file = p / "vec.txt"
            mat_file = p / "mat.txt"
            save_numeric_vector(vec_file, [1.0, 2.5, 3.25])
            mat_file.write_text("1,0\n0,1\n1,1\n", encoding="utf-8")
            self.assertEqual([1.0, 2.5, 3.25], load_numeric_vector(vec_file))
            self.assertEqual([[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], load_numeric_matrix(mat_file))
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_complex_loaders(self):
        p = self._make_local_tmpdir()
        try:
            vec_file = p / "cvec.txt"
            mat_file = p / "cmat.txt"
            vec_file.write_text("1 0\n0 1\n", encoding="utf-8")
            mat_file.write_text("1 0 0 0\n0 1 0 0\n", encoding="utf-8")
            vec = load_complex_vector(vec_file)
            mat = load_complex_matrix(mat_file, pair_mode=True)
            self.assertEqual([1 + 0j, 0 + 1j], vec)
            self.assertEqual(2, len(mat[0]))
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_run_fit_stage_identity(self):
        fit = run_fit_stage([[1.0, 0.0], [0.0, 1.0]], [2.0, 3.0])
        self.assertAlmostEqual(2.0, fit.coefficients[0], places=3)
        self.assertAlmostEqual(3.0, fit.coefficients[1], places=3)
        self.assertLess(fit.residual_norm, 1e-3)
        self.assertEqual(2, len(fit.coefficient_sds))

    def test_run_fit_stage_with_baseline(self):
        fit = run_fit_stage(
            [[1.0], [0.0], [0.0], [0.0], [0.0]],
            [2.0, 0.1, 0.1, 0.1, 0.1],
            FitConfig(baseline_order=0),
        )
        self.assertEqual("alt_nnls_poly_baseline", fit.method)
        self.assertGreater(fit.coefficients[0], 1.5)

    def test_runner_with_fit_inputs(self):
        p = self._make_local_tmpdir()
        try:
            vec_file = p / "vec.txt"
            mat_file = p / "mat.txt"
            ppm_file = p / "ppm.txt"
            names_file = p / "names.txt"
            vec_file.write_text("2\n3\n", encoding="utf-8")
            mat_file.write_text("1 0\n0 1\n", encoding="utf-8")
            ppm_file.write_text("3.0\n2.0\n", encoding="utf-8")
            names_file.write_text("NAA\nCr\n", encoding="utf-8")
            result = LCModelRunner(
                RunConfig(
                    title="Fit run",
                    ntitle=2,
                    raw_data_file=str(vec_file),
                    basis_file=str(mat_file),
                    ppm_axis_file=str(ppm_file),
                    basis_names_file=str(names_file),
                    fit_ppm_start=3.2,
                    fit_ppm_end=2.8,
                    include_metabolites=("NAA",),
                    combine_expressions=("NAA+NAA",),
                )
            ).run()
            self.assertIsNotNone(result.fit_result)
            assert result.fit_result is not None
            self.assertAlmostEqual(2.0, result.fit_result.coefficients[0], places=3)
            self.assertEqual(("NAA",), result.fit_result.metabolite_names)
            self.assertEqual(1, result.fit_result.data_points_used)
            self.assertEqual(1, len(result.fit_result.coefficient_sds))
            self.assertEqual("NAA+NAA", result.fit_result.combined[0][0])
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_cli_with_fit_inputs(self):
        p = self._make_local_tmpdir()
        try:
            vec_file = p / "vec.txt"
            mat_file = p / "mat.txt"
            tab_file = p / "fit.table"
            vec_file.write_text("1\n2\n", encoding="utf-8")
            mat_file.write_text("1 0\n0 1\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = cli_main(
                    [
                        "--title",
                        "Fit cli",
                        "--raw-data-file",
                        str(vec_file),
                        "--basis-file",
                        str(mat_file),
                        "--baseline-order",
                        "0",
                        "--combine-expressions",
                        "basis_1+basis_2",
                        "--table-output-file",
                        str(tab_file),
                    ]
                )
            self.assertEqual(0, code)
            out = buf.getvalue()
            self.assertIn("fit_method=", out)
            self.assertIn("fit_coefficients=", out)
            self.assertIn("fit_coeff_sds=", out)
            self.assertIn("fit_relative_residual=", out)
            self.assertIn("fit_snr_estimate=", out)
            self.assertIn("fit_combinations=", out)
            self.assertIn("table_output_file=", out)
            self.assertTrue(tab_file.exists())
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_time_domain_fit_path(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw_td.txt"
            basis = p / "basis_td.txt"
            names = p / "names.txt"
            raw.write_text("1 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            # One basis column in pair mode: re1 im1
            basis.write_text("1 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            names.write_text("NAA\n", encoding="utf-8")

            result = LCModelRunner(
                RunConfig(
                    raw_data_file=str(raw),
                    basis_file=str(basis),
                    basis_names_file=str(names),
                    time_domain_input=True,
                    auto_phase_zero_order=True,
                )
            ).run()
            self.assertIsNotNone(result.fit_result)
            assert result.fit_result is not None
            self.assertEqual(("NAA",), result.fit_result.metabolite_names)
            self.assertAlmostEqual(1.0, result.fit_result.coefficients[0], places=3)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
