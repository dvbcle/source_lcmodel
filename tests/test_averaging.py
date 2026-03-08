from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig
from lcmodel.pipeline.averaging import (
    detect_zero_voxels,
    estimate_tail_variance,
    weighted_average_channels,
)


class TestAveraging(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_detect_zero_voxels(self):
        flags = detect_zero_voxels(
            [
                [0j, 0j, 0j],
                [0j, 1 + 0j, 0j],
            ]
        )
        self.assertEqual((True, False), flags)

    def test_estimate_tail_variance_linear_signal(self):
        # Exactly linear real/imag tails should have near-zero regression residual.
        datat = [complex(float(i), float(2 * i + 1)) for i in range(1, 20)]
        var = estimate_tail_variance(datat, nback_start=10, nback_end=1)
        self.assertLess(var, 1e-10)

    def test_weighted_average_channels_unweighted(self):
        result = weighted_average_channels(
            [
                [1 + 0j, 3 + 0j],
                [3 + 0j, 5 + 0j],
            ],
            nback_start=2,
            nback_end=1,
            normalize_by_signal=False,
            weight_by_variance=False,
            selection="all",
        )
        self.assertEqual((2 + 0j, 4 + 0j), result.averaged)

    def test_weighted_average_channels_selection(self):
        result = weighted_average_channels(
            [
                [1 + 0j, 1 + 0j],
                [5 + 0j, 5 + 0j],
                [3 + 0j, 3 + 0j],
            ],
            nback_start=2,
            nback_end=1,
            normalize_by_signal=False,
            weight_by_variance=False,
            selection="odd",
        )
        self.assertEqual((2 + 0j, 2 + 0j), result.averaged)
        self.assertEqual((0, 2), result.used_indices)

    def test_runner_time_domain_with_average_mode(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw_channels.txt"
            basis = p / "basis_td.txt"
            raw.write_text(
                (
                    "1 0 2 0 3 0 4 0\n"
                    "3 0 4 0 5 0 6 0\n"
                ),
                encoding="utf-8",
            )
            basis.write_text(
                (
                    "1 0 0 0\n"
                    "0 0 1 0\n"
                    "1 0 0 0\n"
                    "0 0 1 0\n"
                ),
                encoding="utf-8",
            )
            cfg = RunConfig(
                raw_data_file=str(raw),
                basis_file=str(basis),
                time_domain_input=True,
                average_mode=3,
                average_nback_start=3,
                average_nback_end=1,
            )
            result = LCModelRunner(cfg).run()
            self.assertIsNotNone(result.fit_result)
            assert result.fit_result is not None
            self.assertEqual(2, len(result.fit_result.coefficients))
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
