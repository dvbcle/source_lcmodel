from __future__ import annotations

from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.engine import LCModelRunner
from lcmodel.io.debug_outputs import write_coordinate_debug_file, write_corrected_raw_file
from lcmodel.models import FitResult, RunConfig
from lcmodel.validation.debug_compare import (
    compare_debug_outputs,
    parse_debug_coo,
    parse_debug_cor,
    render_markdown_table,
)


class TestDebugOutputs(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_coordinate_and_cor_writers_roundtrip(self):
        tmp = self._make_local_tmpdir()
        try:
            coo = tmp / "debug.coo"
            cor = tmp / "debug.cor"
            fit = FitResult(
                coefficients=(1.0, 2.0),
                residual_norm=0.1,
                iterations=2,
                method="unit-test",
                coefficient_sds=(0.1, 0.2),
                metabolite_names=("Cr", "NAA"),
                combined=(("Cr+PCr", 1.0, 0.1),),
                snr_estimate=12.0,
                linewidth_sigma_points=0.08,
            )
            write_coordinate_debug_file(
                coo,
                fit_result=fit,
                ppm_values=(4.0, 3.0, 2.0),
                phased_data_values=(1.0e-4, 2.0e-4, 3.0e-4),
                fit_values=(1.1e-4, 2.1e-4, 3.1e-4),
            )
            write_corrected_raw_file(
                cor,
                corrected_time_domain=(complex(1.0, 2.0), complex(3.0, 4.0)),
                hzpppm=127.8,
            )
            parsed_coo = parse_debug_coo(coo)
            parsed_cor = parse_debug_cor(cor)
            self.assertEqual((4.0, 3.0, 2.0), parsed_coo.ppm_axis)
            self.assertEqual(3, len(parsed_coo.phased_data))
            self.assertEqual(2, len(parsed_cor.values))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_debug_comparison_table(self):
        a = parse_debug_coo_from_values((4.0, 3.0), (1.0, 2.0), (1.1, 2.1))
        b = parse_debug_coo_from_values((4.0, 3.0), (1.0, 2.01), (1.1, 2.11))
        table = compare_debug_outputs(a, b)
        md = render_markdown_table(table)
        self.assertIn("| Section | Points | Match |", md)
        self.assertEqual(3, len(table.rows))
        self.assertFalse(all(row.match for row in table.rows))

    def test_runner_writes_debug_files_from_config(self):
        tmp = self._make_local_tmpdir()
        try:
            raw = tmp / "raw.raw"
            basis = tmp / "basis.txt"
            coo = tmp / "debug.coo"
            cor = tmp / "debug.cor"
            raw.write_text("1 0\n0 0\n0 0\n0 0\n", encoding="utf-8")
            basis.write_text("1 0\n1 0\n1 0\n1 0\n", encoding="utf-8")

            cfg = RunConfig(
                raw_data_file=str(raw),
                basis_file=str(basis),
                time_domain_input=True,
                nunfil=4,
                dwell_time_s=5e-4,
                hzpppm=127.8,
                coordinate_output_file=str(coo),
                corrected_raw_output_file=str(cor),
            )
            result = LCModelRunner(cfg).run()
            self.assertIsNotNone(result.fit_result)
            self.assertTrue(coo.exists())
            self.assertTrue(cor.exists())
            parsed = parse_debug_coo(coo)
            self.assertGreater(len(parsed.phased_data), 0)
            parsed_cor = parse_debug_cor(cor)
            self.assertEqual(4, len(parsed_cor.values))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def parse_debug_coo_from_values(
    ppm: tuple[float, ...],
    phased: tuple[float, ...],
    fit: tuple[float, ...],
):
    return parse_debug_coo_text(
        "\n".join(
            [
                "  2 points on ppm-axis = NY" if len(ppm) == 2 else f"  {len(ppm)} points on ppm-axis = NY",
                " ".join(f"{v:.6f}" for v in ppm),
                " NY phased data points follow",
                " ".join(f"{v:.6e}" for v in phased),
                " NY points of the fit to the data follow",
                " ".join(f"{v:.6e}" for v in fit),
            ]
        )
        + "\n"
    )


def parse_debug_coo_text(text: str):
    root = Path("tests/.tmp")
    root.mkdir(parents=True, exist_ok=True)
    tmp = root / str(uuid.uuid4())
    tmp.mkdir(parents=True, exist_ok=True)
    try:
        path = tmp / "debug.coo"
        path.write_text(text, encoding="utf-8")
        return parse_debug_coo(path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
