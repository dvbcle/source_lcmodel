from __future__ import annotations

import json
import unittest
from pathlib import Path

from lcmodel.core.text import split_title_lines
from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.traceability import capture_trace_events, provenance_registry


class TestTraceabilityProvenance(unittest.TestCase):
    def test_provenance_registry_contains_core_routines(self):
        registry = provenance_registry()
        for name in ("lcmodl", "split_title", "setup", "pnnls", "integrate", "combis"):
            self.assertIn(name, registry)

    def test_capture_trace_events_for_decorated_calls(self):
        with capture_trace_events() as events:
            split_title_lines("A short title", 1)
            run_fit_stage([[1.0, 0.0], [0.0, 1.0]], [1.0, 2.0], FitConfig())
        self.assertGreaterEqual(len(events), 2)
        flattened = {r for e in events for r in e.get("fortran_routines", [])}
        self.assertIn("split_title", flattened)
        self.assertIn("pnnls", flattened)

    def test_runner_writes_traceability_log(self):
        tmp_dir = Path("tests/.tmp")
        tmp_dir.mkdir(parents=True, exist_ok=True)
        trace_path = tmp_dir / "trace_provenance.json"
        trace_path.unlink(missing_ok=True)
        runner = LCModelRunner(
            RunConfig(
                title="Trace demo",
                ntitle=1,
                traceability_log_file=str(trace_path),
            )
        )
        runner.run()
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
        self.assertEqual(1, payload["trace_version"])
        self.assertGreaterEqual(payload["event_count"], 1)
        flattened = {
            routine
            for event in payload["events"]
            for routine in event.get("fortran_routines", [])
        }
        self.assertIn("lcmodl", flattened)
        self.assertIn("split_title", flattened)


if __name__ == "__main__":
    unittest.main()
