from __future__ import annotations

import unittest

from lcmodel.core.legacy_linear import g1, g2, h12


class TestLegacyLinear(unittest.TestCase):
    def test_g1_g2(self):
        cos_v, sin_v, sig = g1(3.0, 4.0)
        self.assertAlmostEqual(5.0, sig, places=6)
        xr, yr = g2(cos_v, sin_v, 3.0, 4.0)
        self.assertAlmostEqual(5.0, xr, places=6)
        self.assertAlmostEqual(0.0, yr, places=6)

    def test_h12_construct_and_apply_simple(self):
        # Build reflection using u=[2, 1], then apply to two vectors in C.
        u = [2.0, 1.0]
        c = [1.0, 3.0, 2.0, 4.0]
        up = h12(
            mode=1,
            lpivot=1,
            l1=2,
            m=2,
            u=u,
            iue=1,
            up=0.0,
            c=c,
            ice=1,
            icv=2,
            ncv=2,
            range_=1.0e30,
        )
        self.assertNotEqual(0.0, up)
        self.assertEqual(4, len(c))


if __name__ == "__main__":
    unittest.main()
