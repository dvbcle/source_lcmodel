from __future__ import annotations

import unittest

from lcmodel.pipeline.metrics import compute_fit_quality_metrics


class TestQualityMetrics(unittest.TestCase):
    def test_compute_fit_quality_metrics(self):
        matrix = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        vector = [2.0, 3.0, 5.1]
        coeffs = [2.0, 3.0]
        rel, snr = compute_fit_quality_metrics(matrix, vector, coeffs)
        self.assertGreaterEqual(rel, 0.0)
        self.assertGreater(snr, 0.0)
        self.assertLess(rel, 0.1)


if __name__ == "__main__":
    unittest.main()

