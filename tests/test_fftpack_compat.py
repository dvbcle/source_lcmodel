from __future__ import annotations

import unittest

from lcmodel.core.fftpack_compat import (
    cfftb,
    cfftf,
    cfft_r,
    cfftin_r,
    csft_r,
    csftin_r,
    fftci,
    seqtot,
)


class TestFftpackCompat(unittest.TestCase):
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

