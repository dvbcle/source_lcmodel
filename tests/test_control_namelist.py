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
 PPMGAP(1,1)=4.9,
 PPMGAP(2,1)=4.5,
/
"""
        nml = parse_fortran_namelist(text, expected_name="LCMODL")
        self.assertEqual("My Run", nml["title"])
        self.assertEqual(2, nml["ntitle"])
        self.assertEqual("raw.txt", nml["filraw"])
        self.assertEqual(["NAA", "Cr"], nml["chuse1"])
        self.assertEqual(["NAA+Cr"], nml["chcomb"])
        self.assertEqual([[4.9, 4.5]], nml["ppmgap"])

    def test_parse_fortran_namelist_with_end_and_newline_assignments(self):
        text = """
$LCMODL
 TITLE='Sample'
 NTITLE=1
 FILRAW='data.raw'
 FILBAS='3t.basis'
 FILPS='out.ps'
$END
"""
        nml = parse_fortran_namelist(text, expected_name="LCMODL")
        self.assertEqual("Sample", nml["title"])
        self.assertEqual(1, nml["ntitle"])
        self.assertEqual("data.raw", nml["filraw"])
        self.assertEqual("3t.basis", nml["filbas"])
        self.assertEqual("out.ps", nml["filps"])

    def test_load_run_config_from_control_file(self):
        p = self._make_local_tmpdir()
        try:
            ctl = p / "control.in"
            ctl.write_text(
                (
                    "$LCMODL\n"
                    " TITLE='Control Title', NTITLE=1, FILRAW='a.txt', FILRAWL='raw_list.txt', FILCSV='batch.csv', FILBAS='b.txt', FILPS='c.ps', FILTAB='tab.out', FILPRR='priors.txt', SPTYPE='tumor', IAVERG=1, NBACK(1)=70, NBACK(2)=5, NDEGZ=2, NSHIFW=3, SHFTCYC=.false., FSHREF=.true., NSHIFIT=14, NLWSCN=5, LWSCMX=2.5, NLREF=.true., NLITER=6, NLTOL=1E-7, TIMDOM=.true., AUTOPH0=.true., AUTOPH1=.true., NUNFIL=1024, HZPPPM=127.8, DELTAT=0.0005, LBHZ=4.0, NBACKG=8, ALPHAB=0.25, NWNDO=5, IPOWPH=7,\n"
                    " CHUSE1(1)='NAA', CHUSE1(2)='Cr', CHCOMB(1)='NAA+Cr', PPMST=3.2, PPMEND=2.0, PPMGAP(1,1)=4.9, PPMGAP(2,1)=4.5, FILPPM='ppm.txt', FILNAM='names.txt', /\n"
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
            self.assertTrue(cfg.fractional_shift_refine)
            self.assertEqual(14, cfg.fractional_shift_iterations)
            self.assertEqual(5, cfg.linewidth_scan_points)
            self.assertEqual(2.5, cfg.linewidth_scan_max_sigma_points)
            self.assertTrue(cfg.nonlinear_refine)
            self.assertEqual(6, cfg.nonlinear_max_iters)
            self.assertAlmostEqual(1e-7, cfg.nonlinear_tolerance)
            self.assertEqual(0.0005, cfg.dwell_time_s)
            self.assertEqual(127.8, cfg.hzpppm)
            self.assertEqual(1024, cfg.nunfil)
            self.assertEqual(4.0, cfg.line_broadening_hz)
            self.assertEqual(8, cfg.baseline_knots)
            self.assertEqual(0.25, cfg.baseline_smoothness)
            self.assertEqual(5, cfg.integration_border_points)
            # Explicit PPMST/PPMEND in control file should take precedence over
            # any SPTYPE defaults.
            self.assertEqual(3.2, cfg.fit_ppm_start)
            self.assertEqual(2.0, cfg.fit_ppm_end)
            self.assertEqual(((4.9, 4.5),), cfg.exclude_ppm_ranges)
            self.assertEqual("ppm.txt", cfg.ppm_axis_file)
            self.assertEqual("names.txt", cfg.basis_names_file)
            self.assertEqual("tumor", cfg.sptype)
            self.assertTrue(cfg.time_domain_input)
            self.assertTrue(cfg.auto_phase_zero_order)
            self.assertTrue(cfg.auto_phase_first_order)
            self.assertEqual("smooth_real", cfg.phase_objective)
            self.assertEqual(7, cfg.phase_smoothness_power)
            self.assertEqual(1, cfg.average_mode)
            self.assertEqual(70, cfg.average_nback_start)
            self.assertEqual(5, cfg.average_nback_end)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_load_run_config_applies_sptype_default_window(self):
        p = self._make_local_tmpdir()
        try:
            ctl = p / "control.in"
            ctl.write_text(
                (
                    "$LCMODL\n"
                    " TITLE='Preset Window', SPTYPE='tumor', /\n"
                ),
                encoding="utf-8",
            )
            cfg = load_run_config_from_control_file(ctl)
            self.assertEqual("tumor", cfg.sptype)
            self.assertEqual(4.0, cfg.fit_ppm_start)
            self.assertEqual(0.2, cfg.fit_ppm_end)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_load_run_config_can_disable_sptype_defaults(self):
        p = self._make_local_tmpdir()
        try:
            ctl = p / "control.in"
            ctl.write_text(
                (
                    "$LCMODL\n"
                    " TITLE='No Preset Window', SPTYPE='tumor', APPLySPTYPE=.false., /\n"
                ),
                encoding="utf-8",
            )
            cfg = load_run_config_from_control_file(ctl)
            self.assertEqual("tumor", cfg.sptype)
            self.assertFalse(cfg.apply_sptype_presets)
            self.assertIsNone(cfg.fit_ppm_start)
            self.assertIsNone(cfg.fit_ppm_end)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_cli_control_file_drives_fit(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw.txt"
            basis = p / "basis.txt"
            ctl = p / "control.in"
            ps = p / "out.ps"
            raw.write_text("1\n2\n", encoding="utf-8")
            basis.write_text("1 0\n0 1\n", encoding="utf-8")
            ctl.write_text(
                (
                    "$LCMODL\n"
                    f" TITLE='FromControl', NTITLE=2, FILRAW='{raw}', FILBAS='{basis}', FILPS='{ps}', /\n"
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

    def test_control_file_infers_time_domain_from_extensions(self):
        p = self._make_local_tmpdir()
        try:
            ctl = p / "control.in"
            ctl.write_text(
                (
                    "$LCMODL\n"
                    " FILRAW='data.raw', FILBAS='basis.basis', /\n"
                ),
                encoding="utf-8",
            )
            cfg = load_run_config_from_control_file(ctl)
            self.assertTrue(cfg.time_domain_input)
            self.assertTrue(cfg.auto_phase_zero_order)
            self.assertEqual(28, cfg.baseline_knots)
            self.assertAlmostEqual(0.17, cfg.baseline_smoothness)
            self.assertIn("Cr+PCr", cfg.combine_expressions)
        finally:
            shutil.rmtree(p, ignore_errors=True)

    def test_control_file_does_not_copy_colocated_reference_postscript(self):
        p = self._make_local_tmpdir()
        try:
            raw = p / "raw.txt"
            basis = p / "basis.txt"
            ctl = p / "control.in"
            ref_ps = p / "out_ref_build.ps"
            out_ps = p / "out.ps"
            sentinel = "%%COPY_GUARD_SENTINEL_20260308"
            raw.write_text("1\n2\n", encoding="utf-8")
            basis.write_text("1 0\n0 1\n", encoding="utf-8")
            ref_ps.write_text("%!PS-Adobe-2.0\n" + sentinel + "\n", encoding="utf-8")
            ctl.write_text(
                (
                    "$LCMODL\n"
                    f" FILRAW='{raw}', FILBAS='{basis}', FILPS='{out_ps}', /\n"
                ),
                encoding="utf-8",
            )
            code = cli_main(["--control-file", str(ctl)])
            self.assertEqual(0, code)
            rendered = out_ps.read_text(encoding="utf-8")
            self.assertNotIn(sentinel, rendered)
        finally:
            shutil.rmtree(p, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
