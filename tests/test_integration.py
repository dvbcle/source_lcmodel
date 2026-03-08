from __future__ import annotations

import unittest

from lcmodel.pipeline.integration import integrate_peak_with_local_baseline


class TestIntegration(unittest.TestCase):
    def test_integrate_peak_with_local_baseline(self):
        values = [1.0, 1.0, 1.0, 1.0, 2.0, 3.0, 2.0, 1.0, 1.0, 1.0]
        result = integrate_peak_with_local_baseline(
            values,
            peak_index=5,
            start_index=3,
            end_index=7,
            border_width=2,
        )
        self.assertAlmostEqual(4.0, result.area, places=6)
        self.assertEqual(3, result.start_index)
        self.assertEqual(7, result.end_index)
        self.assertAlmostEqual(1.0, result.baseline_level, places=6)

    def test_integrate_peak_raises_when_border_windows_empty(self):
        values = [1.0, 1.5, 2.0, 1.5, 1.0]
        with self.assertRaises(ValueError):
            integrate_peak_with_local_baseline(
                values,
                peak_index=2,
                start_index=0,
                end_index=4,
                border_width=1,
            )


if __name__ == "__main__":
    unittest.main()

