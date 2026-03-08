"""Command-line interface for the Python-first LCModel port."""

from __future__ import annotations

import argparse
from typing import Sequence

from lcmodel.cli_support import apply_cli_args, print_batch_result, print_run_result
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
        "--average-mode",
        type=int,
        default=None,
        help="Channel averaging mode (Fortran IAVERG analog: 1,2,3,4,31,32).",
    )
    parser.add_argument(
        "--average-nback-start",
        type=int,
        default=None,
        help="Tail-noise start offset for averaging variance estimate.",
    )
    parser.add_argument(
        "--average-nback-end",
        type=int,
        default=None,
        help="Tail-noise end offset for averaging variance estimate.",
    )
    parser.add_argument(
        "--average-zero-voxel-check",
        action="store_true",
        help="Skip zero-valued channels before averaging (CHECK_ZERO_VOXELS analog).",
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
        "--sptype",
        default=None,
        help="Legacy SPTYPE profile key (e.g. tumor, liver-1, muscle-2).",
    )
    parser.add_argument(
        "--no-sptype-presets",
        action="store_true",
        help="Disable automatic SPTYPE-derived defaults.",
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
        "--nonlinear-refine",
        action="store_true",
        help="Enable iterative nonlinear refinement loop for shift and linewidth.",
    )
    parser.add_argument(
        "--nonlinear-max-iters",
        type=int,
        default=None,
        help="Maximum nonlinear outer-loop iterations.",
    )
    parser.add_argument(
        "--nonlinear-tolerance",
        type=float,
        default=None,
        help="Residual improvement tolerance for nonlinear refinement loop.",
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
    config = apply_cli_args(config, args)

    runner = LCModelRunner(config)
    if config.raw_data_list_file:
        batch = runner.run_batch()
        print_batch_result(batch)
        return 0

    result = runner.run()
    print_run_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
