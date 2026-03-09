"""Compare Fortran and Python debug intermediate outputs and emit a table."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lcmodel.validation.debug_compare import (
    compare_debug_outputs,
    parse_debug_coo,
    parse_debug_cor,
    render_markdown_table,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare FILCOO/FILCOR-style debug outputs from Fortran and Python runs."
    )
    parser.add_argument("--fortran-coo", required=True, help="Path to Fortran debug.coo")
    parser.add_argument("--python-coo", required=True, help="Path to Python debug.coo")
    parser.add_argument("--fortran-cor", default=None, help="Optional Fortran debug.cor")
    parser.add_argument("--python-cor", default=None, help="Optional Python debug.cor")
    parser.add_argument(
        "--output-md",
        default=None,
        help="Optional path to write markdown table. Defaults to stdout only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    fortran_coo = parse_debug_coo(args.fortran_coo)
    python_coo = parse_debug_coo(args.python_coo)
    fortran_cor = parse_debug_cor(args.fortran_cor) if args.fortran_cor else None
    python_cor = parse_debug_cor(args.python_cor) if args.python_cor else None
    table = compare_debug_outputs(
        fortran_coo,
        python_coo,
        fortran_cor=fortran_cor,
        python_cor=python_cor,
    )
    markdown = render_markdown_table(table)
    print(markdown, end="")
    if args.output_md:
        out = Path(args.output_md)
        out.write_text(markdown, encoding="utf-8")
        print(f"wrote={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
