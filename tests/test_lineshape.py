from __future__ import annotations

import unittest

from lcmodel.pipeline.lineshape import apply_global_gaussian_lineshape


class TestLineshape(unittest.TestCase):
    def test_apply_global_gaussian_lineshape_identity_at_zero_sigma(self):
        matrix = ((0.0, 1.0), (1.0, 0.0), (0.0, 1.0))
        out = apply_global_gaussian_lineshape(matrix, 0.0)
        self.assertEqual(matrix, out)

    def test_apply_global_gaussian_lineshape_broadens_impulse(self):
        matrix = ((0.0,), (1.0,), (0.0,), (0.0,), (0.0,))
        out = apply_global_gaussian_lineshape(matrix, 1.0, circular=False)
        center = out[1][0]
        self.assertGreater(out[0][0], 0.0)
        self.assertGreater(out[2][0], 0.0)
        self.assertLess(center, 1.0)


if __name__ == "__main__":
    unittest.main()

