"""CLI for running simple Fortran-vs-Python oracle comparisons."""

from __future__ import annotations

import argparse
from pathlib import Path
import shlex
from typing import Sequence

from lcmodel.validation.oracle import compare_text_files, run_command


def _parse_pairs(values: Sequence[str]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for value in values:
        if "::" not in value:
            raise ValueError(f"Invalid --compare value: {value!r}. Expected 'expected::actual'.")
        left, right = value.split("::", 1)
        pairs.append((left, right))
    return pairs


def _split_command(command: str) -> list[str]:
    tokens = shlex.split(command, posix=False)
    if not tokens:
        raise ValueError("command must not be empty")
    return tokens


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fortran-vs-Python oracle harness")
    parser.add_argument("--cwd", default=".", help="Working directory for commands.")
    parser.add_argument(
        "--fortran-cmd",
        required=True,
        help='Fortran command string, e.g. "LCModel.exe"',
    )
    parser.add_argument(
        "--fortran-stdin",
        default=None,
        help="Optional file piped to Fortran command stdin.",
    )
    parser.add_argument(
        "--python-cmd",
        default=None,
        help='Optional Python command string, e.g. "python -m lcmodel ..."',
    )
    parser.add_argument(
        "--compare",
        action="append",
        default=[],
        help="Pair in form expected::actual. Can be provided multiple times.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cwd = Path(args.cwd)
    fortran_result = run_command(
        _split_command(args.fortran_cmd), cwd=cwd, stdin_file=args.fortran_stdin
    )
    print(f"fortran_returncode={fortran_result.returncode}")
    if fortran_result.stdout.strip():
        print("fortran_stdout_begin")
        print(fortran_result.stdout.rstrip())
        print("fortran_stdout_end")
    if fortran_result.stderr.strip():
        print("fortran_stderr_begin")
        print(fortran_result.stderr.rstrip())
        print("fortran_stderr_end")

    if args.python_cmd is not None:
        python_result = run_command(_split_command(args.python_cmd), cwd=cwd)
        print(f"python_returncode={python_result.returncode}")
        if python_result.stdout.strip():
            print("python_stdout_begin")
            print(python_result.stdout.rstrip())
            print("python_stdout_end")
        if python_result.stderr.strip():
            print("python_stderr_begin")
            print(python_result.stderr.rstrip())
            print("python_stderr_end")

    mismatches = 0
    for expected_file, actual_file in _parse_pairs(args.compare):
        result = compare_text_files(cwd / expected_file, cwd / actual_file)
        label = f"{expected_file}::{actual_file}"
        if result.match:
            print(f"compare={label} status=match")
        else:
            mismatches += 1
            print(f"compare={label} status=mismatch")
            for line in result.diff_lines[:200]:
                print(line)

    if fortran_result.returncode != 0:
        return fortran_result.returncode
    if args.python_cmd is not None and python_result.returncode != 0:
        return python_result.returncode
    if mismatches > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
