from __future__ import annotations

import math
import unittest

from lcmodel.core.legacy_math import (
    betain,
    dgamln,
    diff,
    fishni,
    icycle,
    icycle_r,
    inflec,
    nextre,
    pythag,
)


class TestLegacyMath(unittest.TestCase):
    def test_diff(self):
        self.assertAlmostEqual(2.5, diff(5.0, 2.5))

    def test_pythag(self):
        self.assertAlmostEqual(5.0, pythag(3.0, 4.0), places=6)

    def test_dgamln_matches_log_gamma(self):
        self.assertAlmostEqual(math.lgamma(5.0), dgamln(5.0), places=8)
        self.assertAlmostEqual(math.lgamma(17.25), dgamln(17.25), places=8)

    def test_betain(self):
        # Closed form for Beta(2,3): I_x = 6x^2 - 8x^3 + 3x^4
        x = 0.5
        expected = 6 * x * x - 8 * x**3 + 3 * x**4
        self.assertAlmostEqual(expected, betain(x, 2.0, 3.0), places=7)

    def test_fishni(self):
        # df1=df2=2 => a=b=1 => I_x(1,1)=x; at F=1, x=0.5.
        self.assertAlmostEqual(0.5, fishni(1.0, 2.0, 2.0), places=7)

    def test_icycle_variants(self):
        self.assertEqual(1, icycle_r(0, 10))
        self.assertEqual(10, icycle(0, 10))
        self.assertEqual(1, icycle(1, 10))
        self.assertEqual(2, icycle(12, 10))

    def test_nextre_and_inflec(self):
        parnl = [0.1, 0.1]
        dgauss = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(1, nextre(parnl, 2, dgauss, 0.0, 1))
        self.assertEqual(2, inflec(parnl, 2, dgauss, 0.0, 1))
        self.assertEqual(99, nextre(parnl, 2, dgauss, 0.0, 2))
        self.assertEqual(99, inflec(parnl, 2, dgauss, 0.0, 2))


if __name__ == "__main__":
    unittest.main()
