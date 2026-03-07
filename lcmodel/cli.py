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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    runner = LCModelRunner(
        RunConfig(
            title=args.title,
            ntitle=args.ntitle,
            output_filename=args.output_filename,
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

