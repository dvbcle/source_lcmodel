from __future__ import annotations

import unittest
import uuid
from pathlib import Path

from lcmodel.legacy_bridge.placeholder_registry import (
    discover_fortran_unit_names,
    install_missing_overrides,
)


class TestLegacyBridgeRegistry(unittest.TestCase):
    @staticmethod
    def _write_fixture(text: str) -> Path:
        tmp_root = Path("tests/.tmp")
        tmp_root.mkdir(parents=True, exist_ok=True)
        path = tmp_root / f"legacy_bridge_{uuid.uuid4().hex}.f"
        path.write_text(text, encoding="utf-8")
        return path

    def test_discover_fortran_unit_names_sanitizes_headers(self):
        source_text = "\n".join(
            [
                "      SUBROUTINE FOO_BAR",
                "      INTEGER FUNCTION BAR$",
                "      PROGRAM main1",
                "      BLOCK DATA INITD",
                "      END",
            ]
        )
        path = self._write_fixture(source_text)
        try:
            names = discover_fortran_unit_names(path)
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual({"foo_bar", "bar_", "main1", "initd"}, names)

    def test_install_missing_overrides_preserves_existing(self):
        source_text = "\n".join(
            [
                "      SUBROUTINE FOO",
                "      SUBROUTINE BAR",
                "      END",
            ]
        )
        path = self._write_fixture(source_text)
        try:
            sentinel = object()
            overrides = {"foo": sentinel}
            placeholders: set[str] = set()
            install_missing_overrides(
                overrides=overrides,
                source_file=path,
                placeholder_set=placeholders,
            )
        finally:
            path.unlink(missing_ok=True)

        self.assertIs(sentinel, overrides["foo"])
        self.assertIn("bar", overrides)
        self.assertEqual({"bar"}, placeholders)

        state = overrides["bar"](state={})
        self.assertEqual(["bar"], state["placeholder_overrides"])


if __name__ == "__main__":
    unittest.main()
