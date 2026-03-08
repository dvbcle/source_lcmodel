from __future__ import annotations

import importlib.util
import unittest

from lcmodel.core.fftpack_compat import (
    cfftb,
    cfftf,
    cfft_r,
    cfftin_r,
    csft_r,
    csftin_r,
    fftci,
    get_fft_backend,
    seqtot,
    use_fft_backend,
)


class TestFftpackCompat(unittest.TestCase):
    def test_fft_backend_context_restores_previous(self):
        baseline = get_fft_backend()
        with use_fft_backend("pure_python"):
            self.assertEqual("pure_python", get_fft_backend())
        self.assertEqual(baseline, get_fft_backend())

    def test_numpy_backend_mode(self):
        data = (1 + 0j, 2 + 1j, -1 + 0.5j, 0 + 0j)
        has_numpy = importlib.util.find_spec("numpy") is not None
        if has_numpy:
            with use_fft_backend("numpy"):
                ft = cfftf(data)
                self.assertEqual(len(data), len(ft))
            return
        with self.assertRaises(RuntimeError):
            with use_fft_backend("numpy"):
                _ = cfftf(data)

    def test_cfftf_cfftb_roundtrip(self):
        data = (1 + 0j, 2 + 1j, -1 + 0.5j, 0 + 0j)
        plan = fftci(len(data))
        ft = cfftf(data, plan)
        back = cfftb(ft, plan)
        for a, b in zip(data, back):
            self.assertAlmostEqual(a.real, b.real, places=6)
            self.assertAlmostEqual(a.imag, b.imag, places=6)

    def test_cfft_aliases_roundtrip(self):
        data = (1 + 0j, 0 + 1j, 0 + 0j, 0 + 0j)
        ft = cfft_r(data)
        back = cfftin_r(ft)
        for a, b in zip(data, back):
            self.assertAlmostEqual(a.real, b.real, places=6)
            self.assertAlmostEqual(a.imag, b.imag, places=6)

    def test_csft_aliases_roundtrip(self):
        data = (1 + 0j, 2 + 0j, 0 + 0j, 0 + 0j)
        ft = csft_r(data, ncap=4)
        back = csftin_r(ft, ncap=4)
        for a, b in zip(data, back):
            self.assertAlmostEqual(a.real, b.real, places=6)
            self.assertAlmostEqual(a.imag, b.imag, places=6)

    def test_seqtot_length(self):
        data = (1 + 0j, 2 + 0j, 3 + 0j)
        ft = seqtot(data)
        self.assertEqual(6, len(ft))


if __name__ == "__main__":
    unittest.main()
