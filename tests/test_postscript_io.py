from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.io.postscript import build_fit_postscript, write_fit_postscript


class TestPostscriptIO(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_build_fit_postscript(self):
        text = build_fit_postscript(
            title_line_1="My (Title) %",
            x_values=[0, 1, 2],
            data_values=[1, 2, 1],
            fit_values=[1, 1.8, 1.1],
        )
        self.assertIn("%!PS-Adobe-2.0", text)
        self.assertIn("\\(Title\\)", text)
        self.assertIn("showpage", text)
        self.assertIn("setrgbcolor", text)

    def test_write_fit_postscript(self):
        p = self._make_local_tmpdir()
        try:
            out = p / "plot.ps"
            written = write_fit_postscript(
                out,
                title_line_1="Fit",
                x_values=[0, 1, 2],
                data_values=[1, 2, 1],
            )
            self.assertEqual(str(out), written)
            content = out.read_text(encoding="utf-8")
            self.assertIn("%%EOF", content)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
