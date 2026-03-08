from __future__ import annotations

import unittest

from lcmodel.pipeline.alignment import align_vector_by_fractional_shift, align_vector_by_integer_shift
from lcmodel.pipeline.fitting import run_fit_stage


class TestAlignment(unittest.TestCase):
    def test_align_vector_by_integer_shift(self):
        # Basis maps first row strongly to coefficient.
        matrix = [[1.0], [0.0], [0.0], [0.0]]
        # Data peak is shifted by +1 sample from row 0 to row 1.
        vector = [0.0, 1.0, 0.0, 0.0]
        aligned = align_vector_by_integer_shift(matrix, vector, max_shift_points=2)
        self.assertEqual(-1, aligned.shift_points)
        self.assertEqual((1.0, 0.0, 0.0, 0.0), aligned.vector)

    def test_align_vector_by_integer_shift_circular_wrap(self):
        matrix = [[1.0], [0.0], [0.0], [0.0]]
        vector = [0.0, 0.0, 0.0, 1.0]
        aligned = align_vector_by_integer_shift(matrix, vector, max_shift_points=2, circular=True)
        self.assertEqual(1, aligned.shift_points)
        self.assertEqual((1.0, 0.0, 0.0, 0.0), aligned.vector)

    def test_align_vector_by_integer_shift_zero_padded_mode(self):
        matrix = [[1.0], [0.0], [0.0], [0.0]]
        vector = [0.0, 0.0, 0.0, 1.0]
        aligned = align_vector_by_integer_shift(matrix, vector, max_shift_points=1, circular=False)
        self.assertEqual(1, aligned.shift_points)
        self.assertEqual((0.0, 0.0, 0.0, 0.0), aligned.vector)

    def test_align_vector_by_fractional_shift_refines_residual(self):
        matrix = [[1.0], [0.0], [0.0], [0.0]]
        vector = [0.5, 0.5, 0.0, 0.0]
        integer = align_vector_by_integer_shift(matrix, vector, max_shift_points=1, circular=True)
        frac = align_vector_by_fractional_shift(matrix, vector, max_shift_points=1, circular=True, iterations=12)
        r_int = run_fit_stage(matrix, integer.vector).residual_norm
        r_frac = run_fit_stage(matrix, frac.vector).residual_norm
        self.assertLessEqual(r_frac, r_int + 1e-9)
        self.assertGreater(abs(frac.shift_points), 0.1)


if __name__ == "__main__":
    unittest.main()
