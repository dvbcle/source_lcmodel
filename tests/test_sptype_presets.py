from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from lcmodel.cli import main as cli_main
from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig
from lcmodel.pipeline.sptype_presets import apply_sptype_preset


class TestSptypePresets(unittest.TestCase):
    def test_apply_sptype_default_window(self):
        cfg = RunConfig(sptype="tumor")
        out = apply_sptype_preset(cfg)
        self.assertEqual(4.0, out.fit_ppm_start)
        self.assertEqual(0.2, out.fit_ppm_end)

    def test_apply_sptype_keeps_explicit_window(self):
        cfg = RunConfig(sptype="tumor", fit_ppm_start=3.1, fit_ppm_end=1.4)
        out = apply_sptype_preset(cfg)
        self.assertEqual(3.1, out.fit_ppm_start)
        self.assertEqual(1.4, out.fit_ppm_end)

    def test_apply_sptype_populates_liver_combinations(self):
        cfg = RunConfig(sptype="liver-1")
        out = apply_sptype_preset(cfg)
        self.assertTrue(out.combine_expressions)
        self.assertIn("L20a+L20b", out.combine_expressions[0])

    def test_runner_applies_sptype_by_default(self):
        runner = LCModelRunner(RunConfig(sptype="tumor"))
        self.assertEqual(4.0, runner.config.fit_ppm_start)
        self.assertEqual(0.2, runner.config.fit_ppm_end)

    def test_runner_can_disable_sptype_presets(self):
        runner = LCModelRunner(RunConfig(sptype="tumor", apply_sptype_presets=False))
        self.assertIsNone(runner.config.fit_ppm_start)
        self.assertIsNone(runner.config.fit_ppm_end)

    def test_cli_can_disable_sptype_presets(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main(["--sptype", "tumor", "--no-sptype-presets"])
        self.assertEqual(0, code)
        out = buf.getvalue()
        self.assertIn("fit_result=<not requested>", out)


if __name__ == "__main__":
    unittest.main()
