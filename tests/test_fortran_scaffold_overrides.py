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

    def test_statistical_function_overrides(self):
        self.assertAlmostEqual(0.5, fs.fishni(1.0, 2.0, 2.0, 6, state={}), places=7)
        self.assertAlmostEqual(0.6875, fs.betain(0.5, 2.0, 3.0, 6, state={}), places=7)
        self.assertAlmostEqual(5.0, fs.pythag(3.0, 4.0, state={}), places=7)
        self.assertEqual(10, fs.icycle(0, 10, state={}))
        self.assertEqual(1, fs.icycle_r(0, 10, state={}))

    def test_lineshape_shape_counters(self):
        parnl = [0.1, 0.1]
        dgauss = [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.assertEqual(1, fs.nextre(parnl, 2, None, dgauss, 0.0, 1, state={}))
        self.assertEqual(2, fs.inflec(parnl, 2, None, dgauss, 0.0, 1, state={}))

    def test_postscript_primitive_overrides(self):
        state = {}
        fs.psetup(True, 612.0, 792.0, False, state=state)
        fs.linewd(1.5, state=state)
        fs.rgb([1.0, 0.0, 0.0], state=state)
        fs.dash(1, [3.0, 2.0], state=state)
        fs.line(10.0, 20.0, 30.0, 40.0, state=state)
        fs.box(50.0, 60.0, 70.0, 80.0, state=state)
        fs.plot(3, [0.0, 1.0, 2.0], [0.0, 1.0, 0.0], 0.0, 2.0, 0.0, 1.0, 100.0, 200.0, 50.0, 50.0, state=state)
        fs.string(False, 0.0, 20.0, 30.0, "hello", state=state)
        fs.showpg(state=state)
        fs.endps(state=state)
        text = state.get("postscript", "")
        self.assertIn("%!PS-Adobe-3.0", text)
        self.assertIn("setlinewidth", text)
        self.assertIn("setrgbcolor", text)
        self.assertIn("showpage", text)


if __name__ == "__main__":
    unittest.main()
