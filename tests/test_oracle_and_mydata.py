from __future__ import annotations

import io
from pathlib import Path
import shutil
import unittest
import uuid
from contextlib import redirect_stdout

from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage
from lcmodel.pipeline.phasing import (
    apply_phase,
    apply_zero_order_phase,
    estimate_zero_first_order_phase,
    estimate_zero_order_phase,
)
from lcmodel.validation.oracle_cli import main as oracle_cli_main
from lcmodel.validation.oracle import (
    compare_numeric_vectors,
    compare_text_files,
    run_command,
)


class TestOracleAndMyData(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_mydata_zero_fill_and_fft(self):
        result = run_mydata_stage(
            [1 + 0j, 0 + 0j, 0 + 0j],
            MyDataConfig(zero_fill_to=4, compute_fft=True),
        )
        self.assertEqual(4, len(result.time_domain))
        self.assertIsNotNone(result.frequency_domain)
        # Fortran CFFT_r/CFFT normalizes by 1/sqrt(N); with N=4 this is 0.5.
        self.assertEqual((0.5 + 0j), result.frequency_domain[0])
        self.assertIn("zero_fill_to=4", result.processing_log)

    def test_mydata_auto_phase(self):
        no_phase = run_mydata_stage([1j, 0j, 0j, 0j], MyDataConfig(compute_fft=True))
        with_phase = run_mydata_stage(
            [1j, 0j, 0j, 0j],
            MyDataConfig(compute_fft=True, auto_phase_zero_order=True, phase_search_steps=360),
        )
        assert no_phase.frequency_domain is not None
        assert with_phase.frequency_domain is not None
        imag_before = sum(abs(v.imag) for v in no_phase.frequency_domain)
        imag_after = sum(abs(v.imag) for v in with_phase.frequency_domain)
        self.assertLess(imag_after, imag_before)
        self.assertIsNotNone(with_phase.zero_order_phase_radians)

    def test_mydata_apodization(self):
        result = run_mydata_stage(
            [1 + 0j, 1 + 0j, 1 + 0j],
            MyDataConfig(
                compute_fft=False,
                dwell_time_s=0.001,
                line_broadening_hz=5.0,
            ),
        )
        self.assertLess(abs(result.time_domain[1]), abs(result.time_domain[0]))
        self.assertLess(abs(result.time_domain[2]), abs(result.time_domain[1]))
        self.assertTrue(any("apodization_lb_hz" in line for line in result.processing_log))

    def test_phase_estimation(self):
        import cmath
        import math

        phi = 0.7
        base = [1 + 0j, 2 + 0j, 0.5 + 0j]
        spectrum = [v * cmath.exp(1j * phi) for v in base]
        est = estimate_zero_order_phase(spectrum, search_steps=720)
        corrected = apply_zero_order_phase(spectrum, est)
        imag_sum = sum(abs(v.imag) for v in corrected)
        self.assertLess(imag_sum, 0.05)
        self.assertLess(abs(est - phi), math.pi / 20)

    def test_first_order_phase_estimation(self):
        import cmath

        base = [1 + 0j, 2 + 0j, 3 + 0j, 4 + 0j, 5 + 0j]
        x = [-1.0, -0.5, 0.0, 0.5, 1.0]
        ph0 = 0.4
        ph1 = 0.8
        spectrum = [v * cmath.exp(1j * (ph0 + ph1 * xi)) for v, xi in zip(base, x)]
        est0, est1 = estimate_zero_first_order_phase(
            spectrum, zero_steps=360, first_steps=81, first_range_radians=1.5
        )
        corrected = apply_phase(spectrum, est0, est1)
        imag_sum = sum(abs(v.imag) for v in corrected)
        self.assertLess(imag_sum, 0.2)

    def test_first_order_phase_smooth_real_objective(self):
        import cmath

        base = [1 + 0j, 2 + 0j, 3 + 0j, 4 + 0j, 5 + 0j]
        x = [-1.0, -0.5, 0.0, 0.5, 1.0]
        ph0 = 0.35
        ph1 = -0.55
        spectrum = [v * cmath.exp(1j * (ph0 + ph1 * xi)) for v, xi in zip(base, x)]
        est0, est1 = estimate_zero_first_order_phase(
            spectrum,
            zero_steps=360,
            first_steps=81,
            first_range_radians=1.5,
            objective="smooth_real",
            smoothness_power=6,
        )
        before = apply_phase(spectrum, 0.0, 0.0)
        corrected = apply_phase(spectrum, est0, est1)
        def roughness(values: list[complex] | tuple[complex, ...]) -> float:
            total = 0.0
            prev = float(values[0].real)
            for v in values[1:]:
                cur = float(v.real)
                total += abs(cur - prev) ** 6
                prev = cur
            return total

        self.assertLess(roughness(corrected), roughness(before))

    def test_mydata_auto_phase_first_order(self):
        n = 16
        # This test validates first-order mode wiring and output fields.
        result = run_mydata_stage(
            [1 + 0j] + [0j] * (n - 1),
            MyDataConfig(compute_fft=True, auto_phase_first_order=True),
        )
        self.assertIsNotNone(result.zero_order_phase_radians)
        self.assertIsNotNone(result.first_order_phase_radians)

    def test_mydata_conjugate_and_truncate(self):
        result = run_mydata_stage(
            [1 + 2j, 3 + 4j, 5 + 6j],
            MyDataConfig(truncate_to=2, conjugate_input=True, compute_fft=False),
        )
        self.assertEqual((1 - 2j, 3 - 4j), result.time_domain)
        self.assertIsNone(result.frequency_domain)
        self.assertIn("truncate_to=2", result.processing_log)
        self.assertIn("conjugate_input=true", result.processing_log)

    def test_run_command(self):
        cmd = ["python", "-c", "print('ok')"]
        result = run_command(cmd)
        self.assertEqual(0, result.returncode)
        self.assertIn("ok", result.stdout)

    def test_compare_text_files(self):
        p = self._make_local_tmpdir()
        try:
            f1 = p / "a.txt"
            f2 = p / "b.txt"
            f1.write_text("line1\nline2\n", encoding="utf-8")
            f2.write_text("line1\nlineX\n", encoding="utf-8")
            same = compare_text_files(f1, f1)
            diff = compare_text_files(f1, f2)
            self.assertTrue(same.match)
            self.assertFalse(diff.match)
            self.assertGreater(len(diff.diff_lines), 0)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_compare_numeric_vectors(self):
        ok = compare_numeric_vectors([1.0, 2.0], [1.0, 2.0000001], abs_tol=1e-6, rel_tol=1e-6)
        bad = compare_numeric_vectors([1.0, 2.0], [1.0, 2.01], abs_tol=1e-6, rel_tol=1e-6)
        self.assertTrue(ok.match)
        self.assertFalse(bad.match)
        self.assertGreater(bad.max_abs_error, 0.0)

    def test_oracle_cli_smoke(self):
        p = self._make_local_tmpdir()
        try:
            expected = p / "expected.txt"
            actual = p / "actual.txt"
            expected.write_text("same\n", encoding="utf-8")
            actual.write_text("same\n", encoding="utf-8")

            buf = io.StringIO()
            with redirect_stdout(buf):
                code = oracle_cli_main(
                    [
                        "--cwd",
                        str(p),
                        "--fortran-cmd",
                        "python -c \"print('fortran-ok')\"",
                        "--python-cmd",
                        "python -c \"print('python-ok')\"",
                        "--compare",
                        "expected.txt::actual.txt",
                    ]
                )
            self.assertEqual(0, code)
            out = buf.getvalue()
            self.assertIn("fortran_returncode=0", out)
            self.assertIn("python_returncode=0", out)
            self.assertIn("status=match", out)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
