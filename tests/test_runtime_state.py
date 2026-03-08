from __future__ import annotations

import unittest

from lcmodel import RuntimeState
from lcmodel import fortran_scaffold as fs


class TestRuntimeState(unittest.TestCase):
    def test_coerce_from_mapping(self):
        state = RuntimeState.coerce({"datat": [1 + 0j]})
        self.assertIsInstance(state, RuntimeState)
        self.assertEqual([1 + 0j], state.datat)

    def test_scaffold_default_state_is_runtime_state(self):
        state = fs.makeps()
        self.assertIsInstance(state, RuntimeState)
        self.assertTrue(state["makeps_called"])

    def test_placeholder_marker(self):
        state = RuntimeState()
        state.mark_placeholder("demo")
        self.assertEqual(["demo"], state["placeholder_overrides"])


if __name__ == "__main__":
    unittest.main()
