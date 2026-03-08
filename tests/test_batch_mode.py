from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch
import uuid

from lcmodel.cli import main as cli_main
import lcmodel.engine as engine_mod
from lcmodel.engine import LCModelRunner
from lcmodel.io.batch import load_path_list
from lcmodel.models import RunConfig


class TestBatchMode(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_runner_batch(self):
        p = self._make_local_tmpdir()
        try:
            raw1 = p / "raw1.txt"
            raw2 = p / "raw2.txt"
            basis = p / "basis.txt"
            list_file = p / "raw_list.txt"
            csv_file = p / "batch.csv"
            raw1.write_text("1\n0\n", encoding="utf-8")
            raw2.write_text("2\n0\n", encoding="utf-8")
            basis.write_text("1\n0\n", encoding="utf-8")
            list_file.write_text(f"{raw1}\n{raw2}\n", encoding="utf-8")

            batch = LCModelRunner(
                RunConfig(
                    raw_data_list_file=str(list_file),
                    basis_file=str(basis),
                    batch_csv_file=str(csv_file),
                )
            ).run_batch()
            self.assertEqual(2, len(batch.rows))
            self.assertIsNotNone(batch.csv_file)
            self.assertTrue(csv_file.exists())
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_cli_batch(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw.txt"
            basis = p / "basis.txt"
            list_file = p / "raw_list.txt"
            csv_file = p / "batch.csv"
            raw.write_text("3\n0\n", encoding="utf-8")
            basis.write_text("1\n0\n", encoding="utf-8")
            list_file.write_text(f"{raw}\n", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                code = cli_main(
                    [
                        "--raw-data-list-file",
                        str(list_file),
                        "--basis-file",
                        str(basis),
                        "--batch-csv-file",
                        str(csv_file),
                    ]
                )
            self.assertEqual(0, code)
            out = buf.getvalue()
            self.assertIn("batch_rows=1", out)
            self.assertIn("batch_csv_file=", out)
            self.assertTrue(csv_file.exists())
            self.assertEqual([str(raw)], load_path_list(list_file))
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_batch_time_domain_reuses_basis_spectral_conversion(self):
        p = self._make_local_tmpdir()
        try:
            raw1 = p / "raw1_td.txt"
            raw2 = p / "raw2_td.txt"
            basis = p / "basis_td.txt"
            list_file = p / "raw_list.txt"
            raw1.write_text("1 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            raw2.write_text("2 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            basis.write_text("1 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            list_file.write_text(f"{raw1}\n{raw2}\n", encoding="utf-8")

            with patch(
                "lcmodel.engine.prepare_basis_frequency_matrix_from_time_domain",
                wraps=engine_mod.prepare_basis_frequency_matrix_from_time_domain,
            ) as wrapped:
                batch = LCModelRunner(
                    RunConfig(
                        raw_data_list_file=str(list_file),
                        basis_file=str(basis),
                        time_domain_input=True,
                    )
                ).run_batch()
                self.assertEqual(2, len(batch.rows))
                self.assertEqual(1, wrapped.call_count)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
