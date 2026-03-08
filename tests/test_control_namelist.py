from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path
import shutil
import unittest
import uuid

from lcmodel.cli import main as cli_main
from lcmodel.io.namelist import load_run_config_from_control_file, parse_fortran_namelist


class TestControlNamelist(unittest.TestCase):
    def _make_local_tmpdir(self) -> Path:
        root = Path("tests/.tmp")
        root.mkdir(parents=True, exist_ok=True)
        path = root / str(uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)
        return path

    def test_parse_fortran_namelist(self):
        text = """
$LCMODL
 TITLE='My Run',
 NTITLE=2,
 FILRAW='raw.txt',
 FILBAS='basis.txt',
 FILPS='out.ps',
 CHUSE1(1)='NAA',
 CHUSE1(2)='Cr',
 CHCOMB(1)='NAA+Cr',
 PPMST=3.2,
 PPMEND=2.0,
/
"""
        nml = parse_fortran_namelist(text, expected_name="LCMODL")
        self.assertEqual("My Run", nml["title"])
        self.assertEqual(2, nml["ntitle"])
        self.assertEqual("raw.txt", nml["filraw"])
        self.assertEqual(["NAA", "Cr"], nml["chuse1"])
        self.assertEqual(["NAA+Cr"], nml["chcomb"])

    def test_load_run_config_from_control_file(self):
        p = self._make_local_tmpdir()
        try:
            ctl = p / "control.in"
            ctl.write_text(
                (
                    "$LCMODL\n"
                    " TITLE='Control Title', NTITLE=1, FILRAW='a.txt', FILRAWL='raw_list.txt', FILCSV='batch.csv', FILBAS='b.txt', FILPS='c.ps', FILTAB='tab.out', FILPRR='priors.txt', NDEGZ=2, NSHIFW=3, SHFTCYC=.false., TIMDOM=.true., AUTOPH0=.true., AUTOPH1=.true., DELTAT=0.0005, LBHZ=4.0, NBACKG=8, ALPHAB=0.25, NWNDO=5, IPOWPH=7,\n"
                    " CHUSE1(1)='NAA', CHUSE1(2)='Cr', CHCOMB(1)='NAA+Cr', PPMST=3.2, PPMEND=2.0, FILPPM='ppm.txt', FILNAM='names.txt', /\n"
                ),
                encoding="utf-8",
            )
            cfg = load_run_config_from_control_file(ctl)
            self.assertEqual("Control Title", cfg.title)
            self.assertEqual(1, cfg.ntitle)
            self.assertEqual("a.txt", cfg.raw_data_file)
            self.assertEqual("b.txt", cfg.basis_file)
            self.assertEqual("c.ps", cfg.output_filename)
            self.assertEqual("tab.out", cfg.table_output_file)
            self.assertEqual("priors.txt", cfg.priors_file)
            self.assertEqual("raw_list.txt", cfg.raw_data_list_file)
            self.assertEqual("batch.csv", cfg.batch_csv_file)
            self.assertEqual(2, cfg.baseline_order)
            self.assertEqual(("NAA", "Cr"), cfg.include_metabolites)
            self.assertEqual(("NAA+Cr",), cfg.combine_expressions)
            self.assertEqual(3, cfg.shift_search_points)
            self.assertFalse(cfg.alignment_circular)
            self.assertEqual(0.0005, cfg.dwell_time_s)
            self.assertEqual(4.0, cfg.line_broadening_hz)
            self.assertEqual(8, cfg.baseline_knots)
            self.assertEqual(0.25, cfg.baseline_smoothness)
            self.assertEqual(5, cfg.integration_border_points)
            self.assertEqual(3.2, cfg.fit_ppm_start)
            self.assertEqual(2.0, cfg.fit_ppm_end)
            self.assertEqual("ppm.txt", cfg.ppm_axis_file)
            self.assertEqual("names.txt", cfg.basis_names_file)
            self.assertTrue(cfg.time_domain_input)
            self.assertTrue(cfg.auto_phase_zero_order)
            self.assertTrue(cfg.auto_phase_first_order)
            self.assertEqual("smooth_real", cfg.phase_objective)
            self.assertEqual(7, cfg.phase_smoothness_power)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_cli_control_file_drives_fit(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw.txt"
            basis = p / "basis.txt"
            ctl = p / "control.in"
            raw.write_text("1\n2\n", encoding="utf-8")
            basis.write_text("1 0\n0 1\n", encoding="utf-8")
            ctl.write_text(
                (
                    "$LCMODL\n"
                    f" TITLE='FromControl', NTITLE=2, FILRAW='{raw}', FILBAS='{basis}', FILPS='out.ps', /\n"
                ),
                encoding="utf-8",
            )

            buf = io.StringIO()
            with redirect_stdout(buf):
                code = cli_main(["--control-file", str(ctl)])
            self.assertEqual(0, code)
            out = buf.getvalue()
            self.assertIn("title_line_1=FromControl", out)
            self.assertIn("fit_coefficients=1,2", out)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
