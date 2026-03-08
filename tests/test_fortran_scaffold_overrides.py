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

    def test_linear_algebra_overrides(self):
        cos = [0.0]
        sin = [0.0]
        sig = [0.0]
        state = fs.g1(3.0, 4.0, cos, sin, sig, state={})
        self.assertIn("g1", state)
        x = [3.0]
        y = [4.0]
        fs.g2(cos[0], sin[0], x, y, state={})
        self.assertAlmostEqual(5.0, x[0], places=6)
        self.assertAlmostEqual(0.0, y[0], places=6)

    def test_pnnls_and_plprin_overrides(self):
        a = [[1.0, 0.0], [0.0, 1.0]]
        b = [1.0, 2.0]
        x = [0.0, 0.0]
        dvar = [0.0]
        w = [0.0, 0.0]
        zz = [0.0, 0.0]
        index = [0, 0]
        mode = [0]
        nsetp = [0]
        fs.pnnls(a, 2, 2, 2, b, x, dvar, w, zz, index, mode, 1.0e-30, [True, True], 0.0, nsetp, state={})
        self.assertAlmostEqual(1.0, x[0], places=6)
        self.assertAlmostEqual(2.0, x[1], places=6)
        self.assertEqual(1, mode[0])
        st = fs.plprin([0.0, 1.0], [1.0, 2.0], [0.5, 1.5], 2, False, 6, 1e10, 0, 0, 0, [0.0, 0.0], False, state={})
        self.assertIn("plprin_text", st)

    def test_eigen_overrides(self):
        a = [[2.0, 1.0], [1.0, 2.0]]
        w = [0.0, 0.0]
        z = [[0.0, 0.0], [0.0, 0.0]]
        ierr = [99]
        state = fs.eigvrs(2, 2, a, w, z, [0.0, 0.0], [0.0, 0.0], ierr, state={})
        self.assertEqual(0, ierr[0])
        self.assertAlmostEqual(1.0, w[0], places=6)
        self.assertAlmostEqual(3.0, w[1], places=6)
        self.assertIn("eigvrs_eigenvalues", state)

    def test_fft_internal_overrides(self):
        yout = [0j, 0j, 0j, 0j]
        fs.df2tcf(4, [1 + 0j, 0j, 0j, 0j], yout, [], state={})
        self.assertAlmostEqual(1.0, yout[0].real, places=6)

        ft = [0j, 0j, 0j, 0j]
        ldwfft = [0]
        fs.dcfft_r([1 + 0j, 0j, 0j, 0j], ft, 4, ldwfft, [], state={})
        self.assertEqual(4, ldwfft[0])
        self.assertAlmostEqual(1.0, ft[0].real, places=6)

        ch = [0.0, 0.0, 0.0]
        st = fs.passf2(2, 1, [3.0, 2.0, 1.0], ch, [], state={})
        self.assertEqual([3.0, 2.0, 1.0], ch)
        self.assertIn("passf2", st)

    def test_misc_legacy_overrides(self):
        value = fs.igetp(12345, 4, state={})
        self.assertGreaterEqual(value, 0)
        self.assertLess(value, 1_000_000_000)

        ppmmin = [1.0, 2.0, 3.0, 4.0]
        ppmmax = [1.5, 2.5, 3.5, 4.5]
        nregion = [4]
        fs.merge_right(2, ppmmin, ppmmax, nregion, state={})
        self.assertEqual(3, nregion[0])
        fs.merge_left(2, ppmmin, ppmmax, nregion, state={})
        self.assertEqual(2, nregion[0])

        out = [0.0] * 5
        state = fs.smooth_tail_2([1.0, -1.0, 1.0, -1.0, 1.0], out, 5, 5, 0, False, state={})
        self.assertEqual(5, len(out))
        self.assertIn("tail_smoothed_points", state)

        cdatat = [complex(1.0, -1.0), complex(-1.0, 1.0), complex(1.0, -1.0)]
        fs.smooth_tail(cdatat, state={})
        self.assertEqual(3, len(cdatat))

        st = fs.phase_with_max_real(state={"datat": [1j, 1j, 1j, 1j]})
        self.assertIn("phase_with_max_real_radians", st)

    def test_prior_parsing_overrides(self):
        chreturn = [""]
        freturn = [0.0]
        istart = [1]
        st = fs.get_field("=", 1, 1, 0, chreturn, freturn, istart, 3, "A=B", state={})
        self.assertEqual("A", chreturn[0])
        self.assertIn("value", st)

        state = fs.parse_prior(
            state={"chrato": ["NAA/Cr=1.5+-0.2+WT=Cho"]}
        )
        self.assertEqual(1, state["nratio"])
        self.assertEqual("NAA/Cr", state["chrati"][0])

        ps_state = {
            "nacomb": ["NAA", "Cr", "Cho"],
            "solbes": [1.0, 1.0, 1.0],
            "cprior": [[0.0, 0.0, 0.0]],
        }
        csum = [0.0]
        denom_absent = [True]
        fs.parse_sum(1.5, "Cr+Cho", 6, 1, csum, denom_absent, state=ps_state)
        self.assertGreater(csum[0], 0.0)
        self.assertFalse(denom_absent[0])

        cp_state = fs.conc_prior(
            state={
                "chrato": ["NAA/Cr=1.0+-0.5"],
                "nacomb": ["NAA", "Cr"],
                "solbes": [2.0, 2.0],
            }
        )
        self.assertEqual(1, cp_state["nratio_used"])

        sim_state = fs.parse_chsimu(
            state={"chsimu": ["MM09 @ .91 +- .02 FWHM= .05 < .06 +- .01 AMP= 3. @ 1.2"]}
        )
        self.assertEqual(1, sim_state["nsimul"])

        self.assertTrue(fs.chreal(0.0, 0.1, False, state={}).strip().startswith("0"))
        cl_state = fs.check_chless(
            state={
                "chless": ["L09"],
                "chmore": "L13",
                "rlesmo": 0.1,
                "nacomb": ["L09a", "L13a"],
                "solbes": [2.0, 1.0],
            }
        )
        self.assertTrue(cl_state["omit_chless"])

    def test_area_and_scaling_overrides(self):
        h2ot = [complex(10.0 * (0.9**i), 0.0) for i in range(40)]
        st = {"h2ot": h2ot, "nunfil": 40, "nwsst": 1, "nwsend": 12, "ppminc": 0.01, "rrange": 1e30}
        area = fs.areawa(1, state=st)
        self.assertGreater(area, 0.0)

        basisf = [complex(0.0, 0.0)] * 80
        for i in range(35, 45):
            basisf[i] = complex(10.0 - abs(40 - i), 0.0)
        ab = fs.areaba(basisf, 0.01, 40, state={"ppmcen": 4.65, "wsppm": 4.65, "rfwbas": 6.0, "fwhmba": 0.05, "ppmbas1": 0.02, "n1hmet": 1, "attmet": 1.0})
        self.assertGreaterEqual(ab, 0.0)

        ws_state = {
            "h2ot": h2ot,
            "nunfil": 40,
            "nwsst": 1,
            "nwsend": 12,
            "ppminc": 0.01,
            "rrange": 1e30,
            "area_met_norm": 2.0,
            "atth2o": 1.0,
            "wconc": 1.0,
            "datat": [1 + 0j, 2 + 0j],
            "cy": [1 + 0j],
        }
        ws_state = fs.water_scale(state=ws_state)
        self.assertTrue(ws_state["wsdone"])
        self.assertIn("fcalib", ws_state)

        self.assertIsInstance(
            fs.ldegmx(
                1,
                state={
                    "degmax": (10.0, 10.0),
                    "parbes": (0.0, 0.0, 1.0),
                    "lphast": 0,
                    "ppmcen": 4.65,
                    "ppmsig": (4.7, 4.6),
                    "ppm": (4.6, 4.5),
                    "nyuse": 2,
                    "radian": 3.1415926535 / 180.0,
                },
            ),
            bool,
        )
        self.assertTrue(
            fs.r_base_sol_big(
                1,
                state={"backre": (1.0, 2.0, 3.0), "solbes": (0.1, 0.2), "rbasmx": (0.5, 0.5, 0.5)},
            )
        )


if __name__ == "__main__":
    unittest.main()
