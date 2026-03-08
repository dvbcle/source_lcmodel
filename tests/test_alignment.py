from __future__ import annotations

import unittest

from lcmodel.pipeline.alignment import align_vector_by_integer_shift


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


if __name__ == "__main__":
    unittest.main()
