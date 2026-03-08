from __future__ import annotations

import unittest

from lcmodel.pipeline.fitting import FitConfig
from lcmodel.pipeline.nonlinear import NonlinearConfig, run_nonlinear_refinement


class TestNonlinear(unittest.TestCase):
    def test_run_nonlinear_refinement_basic(self):
        matrix = (
            (0.0,),
            (1.0,),
            (0.0,),
            (0.0,),
        )
        vector = (0.5, 0.5, 0.0, 0.0)
        result = run_nonlinear_refinement(
            matrix,
            vector,
            FitConfig(),
            NonlinearConfig(
                shift_search_points=1,
                fractional_shift_refine=True,
                fractional_shift_iterations=10,
                linewidth_scan_points=3,
                linewidth_scan_max_sigma_points=1.5,
                max_iters=3,
                tolerance=1e-8,
            ),
        )
        self.assertGreaterEqual(result.iterations, 1)
        self.assertGreaterEqual(result.stage.residual_norm, 0.0)
        self.assertGreater(abs(result.alignment_shift_fractional_points), 0.1)

    def test_run_nonlinear_refinement_one_shot(self):
        matrix = (
            (1.0, 0.0),
            (0.0, 1.0),
        )
        vector = (2.0, 3.0)
        result = run_nonlinear_refinement(
            matrix,
            vector,
            FitConfig(),
            NonlinearConfig(max_iters=1, tolerance=0.0),
        )
        self.assertAlmostEqual(2.0, result.stage.coefficients[0], places=6)
        self.assertAlmostEqual(3.0, result.stage.coefficients[1], places=6)


if __name__ == "__main__":
    unittest.main()

