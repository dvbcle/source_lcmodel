from __future__ import annotations

import unittest

from lcmodel.core.legacy_eigen import jacobi_symmetric, tridiagonal_from_symmetric


class TestLegacyEigen(unittest.TestCase):
    def test_jacobi_symmetric(self):
        matrix = [
            [2.0, 1.0],
            [1.0, 2.0],
        ]
        vals, vecs = jacobi_symmetric(matrix)
        self.assertAlmostEqual(1.0, vals[0], places=6)
        self.assertAlmostEqual(3.0, vals[1], places=6)
        self.assertEqual(2, len(vecs))
        self.assertEqual(2, len(vecs[0]))

    def test_tridiagonal_from_symmetric(self):
        matrix = [
            [4.0, 2.0, 0.0],
            [2.0, 5.0, 1.0],
            [0.0, 1.0, 6.0],
        ]
        d, e = tridiagonal_from_symmetric(matrix)
        self.assertEqual([4.0, 5.0, 6.0], d)
        self.assertEqual([0.0, 2.0, 1.0], e)


if __name__ == "__main__":
    unittest.main()
