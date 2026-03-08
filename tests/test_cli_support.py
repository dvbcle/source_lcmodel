from __future__ import annotations

import argparse
import io
import unittest
from contextlib import redirect_stdout

from lcmodel.cli_support import apply_cli_args, print_batch_result, print_run_result
from lcmodel.models import BatchRunResult, FitResult, RunConfig, RunResult, TitleLayout


class TestCliSupport(unittest.TestCase):
    def test_apply_cli_args_maps_and_parses_ranges(self):
        args = argparse.Namespace(
            title="Example",
            ntitle=1,
            output_filename="out.ps",
            table_output_file=None,
            phase_objective=None,
            phase_smoothness_power=None,
            dwell_time=None,
            line_broadening_hz=None,
            average_mode=None,
            average_nback_start=None,
            average_nback_end=None,
            raw_data_file=None,
            raw_data_list_file=None,
            batch_csv_file=None,
            basis_file=None,
            ppm_axis_file=None,
            basis_names_file=None,
            priors_file=None,
            ppm_start=4.2,
            ppm_end=1.8,
            sptype="tumor",
            shift_search_points=None,
            fractional_shift_iterations=None,
            linewidth_scan_points=None,
            linewidth_scan_max_sigma_points=None,
            nonlinear_max_iters=None,
            nonlinear_tolerance=None,
            baseline_order=None,
            baseline_knots=None,
            baseline_smoothness=None,
            integration_half_width_points=None,
            integration_border_points=None,
            time_domain_input=False,
            auto_phase_zero_order=False,
            auto_phase_first_order=False,
            average_zero_voxel_check=False,
            fractional_shift_refine=False,
            nonlinear_refine=False,
            exclude_ppm_ranges="4.9:4.5,2.1:1.9",
            include_metabolites="NAA,Cr",
            combine_expressions="NAA+Cr",
            no_sptype_presets=False,
            alignment_mode="circular",
        )
        config = apply_cli_args(RunConfig(), args)
        self.assertEqual("Example", config.title)
        self.assertEqual(1, config.ntitle)
        self.assertEqual("out.ps", config.output_filename)
        self.assertEqual(((4.9, 4.5), (2.1, 1.9)), config.exclude_ppm_ranges)
        self.assertEqual(("NAA", "Cr"), config.include_metabolites)
        self.assertEqual(("NAA+Cr",), config.combine_expressions)
        self.assertTrue(config.alignment_circular)

    def test_apply_cli_args_invalid_range_raises(self):
        args = argparse.Namespace(
            exclude_ppm_ranges="4.5",
            include_metabolites=None,
            combine_expressions=None,
            no_sptype_presets=False,
            alignment_mode=None,
            time_domain_input=False,
            auto_phase_zero_order=False,
            auto_phase_first_order=False,
            average_zero_voxel_check=False,
            fractional_shift_refine=False,
            nonlinear_refine=False,
        )
        for key, _ in (
            ("title", None),
            ("ntitle", None),
            ("output_filename", None),
            ("table_output_file", None),
            ("phase_objective", None),
            ("phase_smoothness_power", None),
            ("dwell_time", None),
            ("line_broadening_hz", None),
            ("average_mode", None),
            ("average_nback_start", None),
            ("average_nback_end", None),
            ("raw_data_file", None),
            ("raw_data_list_file", None),
            ("batch_csv_file", None),
            ("basis_file", None),
            ("ppm_axis_file", None),
            ("basis_names_file", None),
            ("priors_file", None),
            ("ppm_start", None),
            ("ppm_end", None),
            ("sptype", None),
            ("shift_search_points", None),
            ("fractional_shift_iterations", None),
            ("linewidth_scan_points", None),
            ("linewidth_scan_max_sigma_points", None),
            ("nonlinear_max_iters", None),
            ("nonlinear_tolerance", None),
            ("baseline_order", None),
            ("baseline_knots", None),
            ("baseline_smoothness", None),
            ("integration_half_width_points", None),
            ("integration_border_points", None),
        ):
            setattr(args, key, None)
        with self.assertRaises(SystemExit):
            apply_cli_args(RunConfig(), args)

    def test_print_helpers(self):
        run_result = RunResult(
            title_layout=TitleLayout(lines=("L1", "L2"), line_count=2),
            output_filename_parts=("a", "b"),
            fit_result=FitResult(
                coefficients=(1.0, 2.0),
                residual_norm=0.25,
                iterations=3,
                method="nnls",
            ),
        )
        batch_result = BatchRunResult(rows=(("raw.txt", (1.0,), 0.1),), csv_file="out.csv")

        buf = io.StringIO()
        with redirect_stdout(buf):
            print_run_result(run_result)
            print_batch_result(batch_result)
        text = buf.getvalue()
        self.assertIn("fit_method=nnls", text)
        self.assertIn("batch_rows=1", text)
        self.assertIn("batch_csv_file=out.csv", text)


if __name__ == "__main__":
    unittest.main()
