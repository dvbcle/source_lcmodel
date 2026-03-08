from __future__ import annotations

import unittest

from lcmodel import fortran_scaffold as fs


class TestFortranScaffoldOverrides(unittest.TestCase):
    def test_split_filename_override(self):
        split = ["", ""]
        state = fs.split_filename("out.ps", "ps", "PS", "Ps", 2, split, state={})
        self.assertEqual(("out_", ".ps"), tuple(split))
        self.assertEqual(("out_", ".ps"), state["split"])

    def test_endrnd_override(self):
        xmnrnd = [0.0]
        xmxrnd = [0.0]
        state = fs.endrnd(0.03, 4.93, 0.2, 0.01, xmnrnd, xmxrnd, state={})
        self.assertEqual(0.0, xmnrnd[0])
        self.assertEqual(5.0, xmxrnd[0])
        self.assertEqual(0.0, state["xmnrnd"])
        self.assertEqual(5.0, state["xmxrnd"])

    def test_cfft_r_override(self):
        ft = [0j, 0j, 0j, 0j]
        state = fs.cfft_r([1 + 0j, 0j, 0j, 0j], ft, 4, 0, None, state={})
        self.assertAlmostEqual(1.0, ft[0].real)
        self.assertEqual(4, len(state["ft"]))

    def test_mydata_override(self):
        state = fs.mydata(
            state={
                "raw_time": [1 + 0j, 0j, 0j, 0j],
                "compute_fft": True,
            }
        )
        self.assertIn("mydata_stage", state)
        self.assertIn("dataf", state)


if __name__ == "__main__":
    unittest.main()
