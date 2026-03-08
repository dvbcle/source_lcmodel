from __future__ import annotations

import unittest

from lcmodel.application import run_lcmodel, run_lcmodel_batch
from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig


class TestApplicationApi(unittest.TestCase):
    def test_run_lcmodel_matches_runner_single(self):
        cfg = RunConfig(title="API parity check", ntitle=2)
        expected = LCModelRunner(cfg).run()
        actual = run_lcmodel(cfg)
        self.assertEqual(expected, actual)

    def test_run_lcmodel_batch_requires_raw_data_list(self):
        cfg = RunConfig()
        with self.assertRaises(ValueError):
            run_lcmodel_batch(cfg)


if __name__ == "__main__":
    unittest.main()
