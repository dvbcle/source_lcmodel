"""Command-line interface for the Python-first LCModel port."""

from __future__ import annotations

import argparse
from dataclasses import replace
from typing import Sequence

from lcmodel.engine import LCModelRunner
from lcmodel.io.namelist import load_run_config_from_control_file
from lcmodel.models import RunConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Python-first LCModel semantic-port workflow."
    )
    parser.add_argument("--control-file", default=None, help="LCModel control file ($LCMODL namelist).")
    parser.add_argument("--title", default=None, help="Title text for report output.")
    parser.add_argument(
        "--ntitle",
        type=int,
        default=None,
        help="Requested number of title lines (legacy-compatible behavior).",
    )
    parser.add_argument(
        "--output-filename",
        default=None,
        help="Output filename to split for voxel identifier insertion.",
    )
    parser.add_argument(
        "--table-output-file",
        default=None,
        help="Optional output path for fit summary table.",
    )
    parser.add_argument(
        "--time-domain-input",
        action="store_true",
        help="Interpret raw/basis files as complex time-domain input before FFT-based fitting.",
    )
    parser.add_argument(
        "--auto-phase-zero-order",
        action="store_true",
        help="Enable zero-order auto-phasing for time-domain raw input conversion.",
    )
    parser.add_argument(
        "--auto-phase-first-order",
        action="store_true",
        help="Enable joint zero/first-order auto-phasing for time-domain conversion.",
    )
    parser.add_argument(
        "--phase-objective",
        choices=("imag_abs", "smooth_real"),
        default=None,
        help="Objective used by auto-phasing search.",
    )
    parser.add_argument(
        "--phase-smoothness-power",
        type=int,
        default=None,
        help="Power used by smooth_real phasing objective (Fortran PHASTA analog).",
    )
    parser.add_argument(
        "--dwell-time",
        type=float,
        default=None,
        help="Time-domain dwell time (seconds) used for optional apodization.",
    )
    parser.add_argument(
        "--line-broadening-hz",
        type=float,
        default=None,
        help="Exponential line broadening (Hz) applied before FFT when dwell-time is set.",
    )
    parser.add_argument(
        "--raw-data-file",
        default=None,
        help="Path to numeric vector file for fit stage (one value per line).",
    )
    parser.add_argument(
        "--raw-data-list-file",
        default=None,
        help="Path to list of raw data files for batch mode.",
    )
    parser.add_argument(
        "--batch-csv-file",
        default=None,
        help="Output CSV path for batch summary.",
    )
    parser.add_argument(
        "--basis-file",
        default=None,
        help="Path to numeric basis matrix file for fit stage.",
    )
    parser.add_argument(
        "--ppm-axis-file",
        default=None,
        help="Optional ppm-axis file aligned with raw data rows.",
    )
    parser.add_argument(
        "--basis-names-file",
        default=None,
        help="Optional basis-metabolite names file (one per basis column).",
    )
    parser.add_argument(
        "--priors-file",
        default=None,
        help="Optional priors file rows: name mean sd.",
    )
    parser.add_argument(
        "--ppm-start",
        type=float,
        default=None,
        help="Optional ppm window start for selecting fit rows.",
    )
    parser.add_argument(
        "--ppm-end",
        type=float,
        default=None,
        help="Optional ppm window end for selecting fit rows.",
    )
    parser.add_argument(
        "--exclude-ppm-ranges",
        default=None,
        help="Comma-separated ranges to exclude, e.g. 4.9:4.5,2.1:1.9.",
    )
    parser.add_argument(
        "--include-metabolites",
        default=None,
        help="Comma-separated metabolite names to include from basis_names_file.",
    )
    parser.add_argument(
        "--combine-expressions",
        default=None,
        help="Comma-separated combination expressions, e.g. NAA+Cr,Glu+Gln.",
    )
    parser.add_argument(
        "--shift-search-points",
        type=int,
        default=None,
        help="Search +/- this many points for integer alignment shift before fit.",
    )
    parser.add_argument(
        "--alignment-mode",
        choices=("circular", "zero_padded"),
        default=None,
        help="Integer shift mode for alignment search.",
    )
    parser.add_argument(
        "--fractional-shift-refine",
        action="store_true",
        help="Enable continuous (sub-point) refinement after integer shift search.",
    )
    parser.add_argument(
        "--fractional-shift-iterations",
        type=int,
        default=None,
        help="Iterations for fractional shift refinement search.",
    )
    parser.add_argument(
        "--linewidth-scan-points",
        type=int,
        default=None,
        help="Number of points in global linewidth scan (0 disables).",
    )
    parser.add_argument(
        "--linewidth-scan-max-sigma-points",
        type=float,
        default=None,
        help="Maximum Gaussian sigma (in points) for linewidth scan.",
    )
    parser.add_argument(
        "--baseline-order",
        type=int,
        default=None,
        help="Polynomial baseline order for alternating fit stage (-1 disables baseline).",
    )
    parser.add_argument(
        "--baseline-knots",
        type=int,
        default=None,
        help="Cubic B-spline baseline knot count (>=4 enables spline baseline mode).",
    )
    parser.add_argument(
        "--baseline-smoothness",
        type=float,
        default=None,
        help="Spline smoothness penalty weight (maps to baseline regularization strength).",
    )
    parser.add_argument(
        "--integration-half-width-points",
        type=int,
        default=None,
        help="Initial half-width (points) used for peak integration around dominant peak.",
    )
    parser.add_argument(
        "--integration-border-points",
        type=int,
        default=None,
        help="Points on each side used to estimate integration baseline.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.control_file:
        config = load_run_config_from_control_file(args.control_file)
    else:
        config = RunConfig()

    if args.title is not None:
        config = replace(config, title=args.title)
    if args.ntitle is not None:
        config = replace(config, ntitle=args.ntitle)
    if args.output_filename is not None:
        config = replace(config, output_filename=args.output_filename)
    if args.table_output_file is not None:
        config = replace(config, table_output_file=args.table_output_file)
    if args.time_domain_input:
        config = replace(config, time_domain_input=True)
    if args.auto_phase_zero_order:
        config = replace(config, auto_phase_zero_order=True)
    if args.auto_phase_first_order:
        config = replace(config, auto_phase_first_order=True)
    if args.phase_objective is not None:
        config = replace(config, phase_objective=args.phase_objective)
    if args.phase_smoothness_power is not None:
        config = replace(config, phase_smoothness_power=args.phase_smoothness_power)
    if args.dwell_time is not None:
        config = replace(config, dwell_time_s=args.dwell_time)
    if args.line_broadening_hz is not None:
        config = replace(config, line_broadening_hz=args.line_broadening_hz)
    if args.raw_data_file is not None:
        config = replace(config, raw_data_file=args.raw_data_file)
    if args.raw_data_list_file is not None:
        config = replace(config, raw_data_list_file=args.raw_data_list_file)
    if args.batch_csv_file is not None:
        config = replace(config, batch_csv_file=args.batch_csv_file)
    if args.basis_file is not None:
        config = replace(config, basis_file=args.basis_file)
    if args.ppm_axis_file is not None:
        config = replace(config, ppm_axis_file=args.ppm_axis_file)
    if args.basis_names_file is not None:
        config = replace(config, basis_names_file=args.basis_names_file)
    if args.priors_file is not None:
        config = replace(config, priors_file=args.priors_file)
    if args.ppm_start is not None:
        config = replace(config, fit_ppm_start=args.ppm_start)
    if args.ppm_end is not None:
        config = replace(config, fit_ppm_end=args.ppm_end)
    if args.exclude_ppm_ranges is not None:
        ranges: list[tuple[float, float]] = []
        for raw_range in args.exclude_ppm_ranges.split(","):
            part = raw_range.strip()
            if not part:
                continue
            if ":" not in part:
                raise SystemExit(f"Invalid exclude range '{part}', expected a:b")
            a_text, b_text = part.split(":", 1)
            ranges.append((float(a_text), float(b_text)))
        config = replace(config, exclude_ppm_ranges=tuple(ranges))
    if args.include_metabolites is not None:
        names = tuple(p.strip() for p in args.include_metabolites.split(",") if p.strip())
        config = replace(config, include_metabolites=names)
    if args.combine_expressions is not None:
        exprs = tuple(p.strip() for p in args.combine_expressions.split(",") if p.strip())
        config = replace(config, combine_expressions=exprs)
    if args.shift_search_points is not None:
        config = replace(config, shift_search_points=args.shift_search_points)
    if args.alignment_mode is not None:
        config = replace(config, alignment_circular=(args.alignment_mode == "circular"))
    if args.fractional_shift_refine:
        config = replace(config, fractional_shift_refine=True)
    if args.fractional_shift_iterations is not None:
        config = replace(config, fractional_shift_iterations=args.fractional_shift_iterations)
    if args.linewidth_scan_points is not None:
        config = replace(config, linewidth_scan_points=args.linewidth_scan_points)
    if args.linewidth_scan_max_sigma_points is not None:
        config = replace(config, linewidth_scan_max_sigma_points=args.linewidth_scan_max_sigma_points)
    if args.baseline_order is not None:
        config = replace(config, baseline_order=args.baseline_order)
    if args.baseline_knots is not None:
        config = replace(config, baseline_knots=args.baseline_knots)
    if args.baseline_smoothness is not None:
        config = replace(config, baseline_smoothness=args.baseline_smoothness)
    if args.integration_half_width_points is not None:
        config = replace(config, integration_half_width_points=args.integration_half_width_points)
    if args.integration_border_points is not None:
        config = replace(config, integration_border_points=args.integration_border_points)

    runner = LCModelRunner(config)
    if config.raw_data_list_file:
        batch = runner.run_batch()
        print(f"batch_rows={len(batch.rows)}")
        for raw_file, coeffs, residual in batch.rows:
            coeff_text = ",".join(f"{v:.12g}" for v in coeffs)
            print(f"batch_row={raw_file}|{residual:.12g}|{coeff_text}")
        if batch.csv_file:
            print(f"batch_csv_file={batch.csv_file}")
        return 0

    result = runner.run()

    print(f"title_lines={result.title_layout.line_count}")
    print(f"title_line_1={result.title_layout.lines[0]}")
    print(f"title_line_2={result.title_layout.lines[1]}")
    if result.output_filename_parts is None:
        print("output_split=<not requested>")
    else:
        left, right = result.output_filename_parts
        print(f"output_split_left={left}")
        print(f"output_split_right={right}")
    if result.fit_result is None:
        print("fit_result=<not requested>")
    else:
        print(f"fit_method={result.fit_result.method}")
        print(f"fit_iterations={result.fit_result.iterations}")
        print(f"fit_residual_norm={result.fit_result.residual_norm:.12g}")
        coeffs = ",".join(f"{v:.12g}" for v in result.fit_result.coefficients)
        print(f"fit_coefficients={coeffs}")
        if result.fit_result.coefficient_sds:
            sds = ",".join(f"{v:.12g}" for v in result.fit_result.coefficient_sds)
            print(f"fit_coeff_sds={sds}")
        if result.fit_result.metabolite_names:
            print(f"fit_metabolites={','.join(result.fit_result.metabolite_names)}")
        if result.fit_result.data_points_used > 0:
            print(f"fit_points_used={result.fit_result.data_points_used}")
        print(f"fit_relative_residual={result.fit_result.relative_residual:.12g}")
        print(f"fit_snr_estimate={result.fit_result.snr_estimate:.12g}")
        print(f"fit_alignment_shift_points={result.fit_result.alignment_shift_points}")
        print(f"fit_alignment_shift_fractional_points={result.fit_result.alignment_shift_fractional_points:.12g}")
        print(f"fit_linewidth_sigma_points={result.fit_result.linewidth_sigma_points:.12g}")
        print(f"fit_integrated_data_area={result.fit_result.integrated_data_area:.12g}")
        print(f"fit_integrated_fit_area={result.fit_result.integrated_fit_area:.12g}")
        if result.fit_result.combined:
            combo = ",".join(f"{name}:{value:.12g}:{sd:.12g}" for name, value, sd in result.fit_result.combined)
            print(f"fit_combinations={combo}")
    if result.table_output_file:
        print(f"table_output_file={result.table_output_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
