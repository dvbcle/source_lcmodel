from __future__ import annotations

import unittest

from lcmodel.core.legacy_parsing import (
    build_conc_prior,
    chreal,
    get_field_from_string,
    parse_chsimu_strings,
    parse_prior_strings,
    parse_sum_terms,
)


class TestLegacyParsing(unittest.TestCase):
    def test_get_field_from_string(self):
        pos, field = get_field_from_string("=", 1, 0, 1, "A=B")
        self.assertEqual("A", field)
        self.assertGreater(pos, 0)

    def test_parse_prior_strings(self):
        parsed = parse_prior_strings(["NAA/Cr=1.5+-0.2+WT=Cho"])
        self.assertEqual("NAA/Cr", parsed[0]["chrati"])
        self.assertAlmostEqual(1.5, float(parsed[0]["exrati"]))
        self.assertAlmostEqual(0.2, float(parsed[0]["sdrati"]))
        self.assertEqual("Cho", parsed[0]["chratw"])

    def test_parse_sum_terms_aliases(self):
        nacomb = ["NAA", "NAAG", "Cr", "PCr", "Cho", "GPC", "PCh"]
        solbes = [1.0] * len(nacomb)
        row, csum, absent = parse_sum_terms("totNAA+totCr+totCho", nacomb, solbes, 2.0)
        self.assertFalse(absent)
        self.assertAlmostEqual(7.0, csum)
        self.assertEqual(-2.0, row[0])

    def test_build_conc_prior(self):
        parsed = parse_prior_strings(["NAA/Cr=1.0+-0.5"])
        rows, used = build_conc_prior(parsed, ["NAA", "Cr"], [2.0, 2.0])
        self.assertEqual(1, len(rows))
        self.assertEqual(1, len(used))

    def test_parse_chsimu_strings(self):
        parsed = parse_chsimu_strings(["MM09 @ .91 +- .02 FWHM= .05 < .06 +- .01 AMP= 3. @ 1.2"])
        self.assertEqual("MM09", parsed[0]["chsim"])
        self.assertEqual(1, parsed[0]["ngau"])

    def test_chreal(self):
        self.assertTrue(chreal(0.0, 0.1, False).strip().startswith("0"))
        self.assertTrue(chreal(1234567.0, 1.0, False))


if __name__ == "__main__":
    unittest.main()
