from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig


def _write_complex_vector(path: Path, values: list[complex]) -> None:
    text = "\n".join(f"{float(v.real):.12g} {float(v.imag):.12g}" for v in values) + "\n"
    path.write_text(text, encoding="utf-8")


def _write_complex_matrix_single_column(path: Path, values: list[complex]) -> None:
    # Pair-mode complex matrix with one metabolite column.
    _write_complex_vector(path, values)


class TestH2ODataFlow(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_doecc_uses_h2o_phase_to_correct_time_domain(self):
        p = self._make_local_tmpdir()
        try:
            n = 32
            raw_clean = [complex(1.0 / (1.0 + i), 0.0) for i in range(n)]
            raw_phase = [1j * v for v in raw_clean]
            h2o_phase = [1j] * n
            basis_td = [complex(1.0, 0.0)] * n

            raw_clean_file = p / "raw_clean.raw"
            raw_phase_file = p / "raw_phase.raw"
            h2o_file = p / "h2o.raw"
            basis_file = p / "basis.txt"
            _write_complex_vector(raw_clean_file, raw_clean)
            _write_complex_vector(raw_phase_file, raw_phase)
            _write_complex_vector(h2o_file, h2o_phase)
            _write_complex_matrix_single_column(basis_file, basis_td)

            common = dict(
                basis_file=str(basis_file),
                time_domain_input=True,
                nunfil=n,
                dwell_time_s=5.0e-4,
                hzpppm=127.8,
                auto_phase_zero_order=False,
                auto_phase_first_order=False,
            )
            runner_baseline = LCModelRunner(
                RunConfig(raw_data_file=str(raw_clean_file), **common)
            )
            _, baseline, _, _, _, _ = runner_baseline._load_fit_system()

            runner_no_ecc = LCModelRunner(
                RunConfig(raw_data_file=str(raw_phase_file), **common)
            )
            _, no_ecc, _, _, _, _ = runner_no_ecc._load_fit_system()

            runner_ecc = LCModelRunner(
                RunConfig(
                    raw_data_file=str(raw_phase_file),
                    h2o_data_file=str(h2o_file),
                    doecc=True,
                    **common,
                )
            )
            _, with_ecc, _, _, _, _ = runner_ecc._load_fit_system()

            self.assertGreater(
                sum(abs(a - b) for a, b in zip(baseline, no_ecc)),
                1.0e-3,
            )
            self.assertLess(
                sum(abs(a - b) for a, b in zip(baseline, with_ecc)),
                1.0e-6,
            )
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_dows_applies_single_calibration_multiplier(self):
        p = self._make_local_tmpdir()
        try:
            n = 64
            raw_td = [complex(1.0 if i == 0 else 0.0, 0.0) for i in range(n)]
            h2o_td = [complex(10.0 * (0.96**i), 0.0) for i in range(n)]

            # Peak near wsppm (default ~3.027 ppm) for AREABA-like normalization.
            basis_td: list[complex] = []
            for i in range(n):
                basis_td.append(complex(50.0 if i == 13 else 0.0, 0.0))

            raw_file = p / "raw.raw"
            h2o_file = p / "h2o.raw"
            basis_file = p / "basis.txt"
            _write_complex_vector(raw_file, raw_td)
            _write_complex_vector(h2o_file, h2o_td)
            _write_complex_matrix_single_column(basis_file, basis_td)

            common = dict(
                raw_data_file=str(raw_file),
                basis_file=str(basis_file),
                time_domain_input=True,
                nunfil=n,
                dwell_time_s=5.0e-4,
                hzpppm=127.8,
                auto_phase_zero_order=False,
                auto_phase_first_order=False,
                iareaw=1,  # deterministic log-linear water area path
                nwsst=10,
                nwsend=50,
            )
            runner_off = LCModelRunner(RunConfig(**common))
            _, vec_off, _, _, _, _ = runner_off._load_fit_system()

            runner_on = LCModelRunner(
                RunConfig(
                    h2o_data_file=str(h2o_file),
                    dows=True,
                    **common,
                )
            )
            _, vec_on, _, _, _, _ = runner_on._load_fit_system()

            self.assertEqual(len(vec_off), len(vec_on))
            ratios = [vec_on[i] / vec_off[i] for i in range(len(vec_on)) if abs(vec_off[i]) > 1.0e-12]
            self.assertTrue(ratios)
            r0 = ratios[0]
            self.assertGreater(abs(r0 - 1.0), 1.0e-3)
            self.assertLess(max(abs(r - r0) for r in ratios), 1.0e-6)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()

