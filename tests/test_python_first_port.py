from __future__ import annotations

import io
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

from lcmodel.cli import main as cli_main
from lcmodel.core.array_ops import reverse_first_n
from lcmodel.core.axis import round_axis_endpoints
from lcmodel.core.text import (
    escape_postscript_text,
    first_non_space_index,
    int_to_compact_text,
    split_title_lines,
)
from lcmodel.engine import LCModelRunner
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.models import RunConfig


class TestPythonFirstPort(unittest.TestCase):
    def test_split_output_filename_case1(self):
        left, right = split_output_filename_for_voxel("abc/ps", ("ps", "PS", "Ps"))
        self.assertEqual(("abc/", ".ps"), (left, right))

    def test_split_output_filename_case2(self):
        left, right = split_output_filename_for_voxel("abc.ps", ("ps", "PS", "Ps"))
        self.assertEqual(("abc_", ".ps"), (left, right))

    def test_split_output_filename_fallback(self):
        left, right = split_output_filename_for_voxel("abc", ("ps", "PS", "Ps"))
        self.assertEqual(("abc_", ""), (left, right))

    def test_first_non_space_index(self):
        self.assertEqual(3, first_non_space_index("  x", 3))
        self.assertEqual(-1, first_non_space_index("   ", 3))

    def test_int_to_compact_text(self):
        self.assertEqual("7", int_to_compact_text(7))
        self.assertEqual("-99999", int_to_compact_text(-100000))
        self.assertEqual("999999", int_to_compact_text(1000000))

    def test_escape_postscript_text(self):
        self.assertEqual(r"a\(b\)\%\\c", escape_postscript_text(r"a(b)%\c"))

    def test_split_title_lines(self):
        title = "A title with enough characters to force a break around a later space near the end"
        layout = split_title_lines(title, ntitle=2)
        self.assertIn(layout.line_count, (1, 2))
        self.assertTrue(layout.lines[0])

    def test_reverse_first_n(self):
        values = [1, 2, 3, 4, 5]
        reverse_first_n(values, 5)
        self.assertEqual([5, 4, 3, 2, 1], values)

    def test_round_axis_endpoints(self):
        self.assertEqual((0.0, 5.0), round_axis_endpoints(0.03, 4.93, 0.2, 0.01))

    def test_runner(self):
        runner = LCModelRunner(
            RunConfig(
                title="Runner Title",
                ntitle=2,
                output_filename="abc/ps",
            )
        )
        result = runner.run()
        self.assertGreaterEqual(result.title_layout.line_count, 1)
        self.assertEqual(("abc/", ".ps"), result.output_filename_parts)

    def test_cli_main_output(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli_main(
                [
                    "--title",
                    "Example (Title) %",
                    "--ntitle",
                    "2",
                    "--output-filename",
                    "abc.ps",
                ]
            )
        self.assertEqual(0, code)
        out = buf.getvalue()
        self.assertIn("title_lines=1", out)
        self.assertIn("output_split_left=abc_", out)
        self.assertIn("output_split_right=.ps", out)

    def test_module_entrypoint(self):
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "lcmodel",
                "--title",
                "Runner Title",
                "--ntitle",
                "2",
                "--output-filename",
                "abc/ps",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn("output_split_left=abc/", proc.stdout)
        self.assertIn("output_split_right=.ps", proc.stdout)


if __name__ == "__main__":
    unittest.main()
