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
        "--raw-data-file",
        default=None,
        help="Path to numeric vector file for fit stage (one value per line).",
    )
    parser.add_argument(
        "--basis-file",
        default=None,
        help="Path to numeric basis matrix file for fit stage.",
    )
    parser.add_argument(
        "--baseline-order",
        type=int,
        default=None,
        help="Polynomial baseline order for alternating fit stage (-1 disables baseline).",
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
    if args.raw_data_file is not None:
        config = replace(config, raw_data_file=args.raw_data_file)
    if args.basis_file is not None:
        config = replace(config, basis_file=args.basis_file)
    if args.baseline_order is not None:
        config = replace(config, baseline_order=args.baseline_order)

    runner = LCModelRunner(config)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
