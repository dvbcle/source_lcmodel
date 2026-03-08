from __future__ import annotations

import unittest

from lcmodel.pipeline.postprocess import compute_combinations


class TestPostprocessCombinations(unittest.TestCase):
    def test_compute_combinations(self):
        names = ("NAA", "Cr", "Cho")
        coeffs = (2.0, 1.0, 0.5)
        sds = (0.2, 0.1, 0.05)
        combos = compute_combinations(("NAA+Cr", "NAA-Cr+Cho"), coeffs, sds, names)
        self.assertEqual(2, len(combos))
        self.assertEqual("NAA+Cr", combos[0][0])
        self.assertAlmostEqual(3.0, combos[0][1], places=6)
        self.assertGreater(combos[0][2], 0.0)

    def test_combis_cho_triplet_drops_pairwise(self):
        names = ("Cho", "GPC", "PCh")
        coeffs = (1.0, 2.0, 3.0)
        sds = (0.1, 0.2, 0.3)
        combos = compute_combinations(
            ("Cho+GPC+PCh", "GPC+PCh", "GPC+Cho", "PCh+Cho"),
            coeffs,
            sds,
            names,
        )
        self.assertEqual(1, len(combos))
        self.assertEqual("Cho+GPC+PCh", combos[0][0])


if __name__ == "__main__":
    unittest.main()
