"""Command-line interface for the Python-first LCModel port."""

from __future__ import annotations

import argparse
from typing import Sequence

from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Python-first LCModel semantic-port workflow."
    )
    parser.add_argument("--title", default="", help="Title text for report output.")
    parser.add_argument(
        "--ntitle",
        type=int,
        default=2,
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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    runner = LCModelRunner(
        RunConfig(
            title=args.title,
            ntitle=args.ntitle,
            output_filename=args.output_filename,
            raw_data_file=args.raw_data_file,
            basis_file=args.basis_file,
        )
    )
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
