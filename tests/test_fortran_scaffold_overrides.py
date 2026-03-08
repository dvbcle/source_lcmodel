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

    def test_text_and_numeric_function_overrides(self):
        self.assertEqual(3, fs.ilen("abc  ", state={}))
        self.assertEqual(3, fs.icharst("  x", 3, state={}))
        seed = [1.0]
        value = fs.random(seed, state={})
        self.assertGreater(value, 0.0)
        self.assertLess(value, 1.0)
        self.assertGreater(seed[0], 0.0)

    def test_average_and_getvar_overrides(self):
        state = fs.check_zero_voxels(
            state={
                "channels": [
                    [1 + 0j, 2 + 0j, 3 + 0j, 4 + 0j],
                    [0j, 0j, 0j, 0j],
                ]
            }
        )
        self.assertEqual((False, True), state["zero_voxel"])
        state["iaverg"] = 3
        state["nback"] = (3, 1)
        state = fs.average(state=state)
        self.assertIn("datat", state)
        variance = fs.getvar(state=state)
        self.assertGreaterEqual(variance, 0.0)


if __name__ == "__main__":
    unittest.main()
