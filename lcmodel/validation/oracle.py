"""Oracle harness utilities for Fortran-vs-Python parity work."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import math
import subprocess
from typing import Sequence


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class FileComparisonResult:
    match: bool
    diff_lines: tuple[str, ...]


@dataclass(frozen=True)
class NumericComparisonResult:
    match: bool
    max_abs_error: float
    rms_error: float
    compared_points: int
    message: str


def run_command(
    command: Sequence[str],
    cwd: str | Path | None = None,
    stdin_file: str | Path | None = None,
    timeout_seconds: int = 120,
) -> CommandResult:
    """Run a process and capture full stdout/stderr for parity logs."""

    stdin_handle = None
    try:
        if stdin_file is not None:
            stdin_handle = Path(stdin_file).open("r", encoding="utf-8", errors="replace")
        completed = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            stdin=stdin_handle,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    finally:
        if stdin_handle is not None:
            stdin_handle.close()

    return CommandResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def compare_text_files(
    expected_file: str | Path,
    actual_file: str | Path,
    *,
    normalize_line_endings: bool = True,
) -> FileComparisonResult:
    """Compare text outputs and return a compact unified diff if mismatched."""

    expected_path = Path(expected_file)
    actual_path = Path(actual_file)
    expected = expected_path.read_text(encoding="utf-8", errors="replace")
    actual = actual_path.read_text(encoding="utf-8", errors="replace")
    if normalize_line_endings:
        expected = expected.replace("\r\n", "\n")
        actual = actual.replace("\r\n", "\n")

    if expected == actual:
        return FileComparisonResult(match=True, diff_lines=())

    diff = difflib.unified_diff(
        expected.splitlines(),
        actual.splitlines(),
        fromfile=str(expected_path),
        tofile=str(actual_path),
        lineterm="",
    )
    return FileComparisonResult(match=False, diff_lines=tuple(diff))


def compare_numeric_vectors(
    expected: Sequence[float],
    actual: Sequence[float],
    *,
    abs_tol: float = 1e-6,
    rel_tol: float = 1e-6,
) -> NumericComparisonResult:
    """Compare numeric vectors with tolerances and error metrics."""

    if len(expected) != len(actual):
        return NumericComparisonResult(
            match=False,
            max_abs_error=math.inf,
            rms_error=math.inf,
            compared_points=0,
            message=f"length mismatch: expected={len(expected)} actual={len(actual)}",
        )
    if len(expected) == 0:
        return NumericComparisonResult(
            match=True,
            max_abs_error=0.0,
            rms_error=0.0,
            compared_points=0,
            message="no points compared",
        )

    sqsum = 0.0
    max_abs = 0.0
    mismatch_index = -1
    for idx, (exp, act) in enumerate(zip(expected, actual)):
        err = abs(float(act) - float(exp))
        max_abs = max(max_abs, err)
        sqsum += err * err
        allowed = max(abs_tol, rel_tol * max(abs(float(exp)), abs(float(act))))
        if err > allowed and mismatch_index < 0:
            mismatch_index = idx

    rms = math.sqrt(sqsum / len(expected))
    if mismatch_index >= 0:
        return NumericComparisonResult(
            match=False,
            max_abs_error=max_abs,
            rms_error=rms,
            compared_points=len(expected),
            message=f"first mismatch at index {mismatch_index}",
        )

    return NumericComparisonResult(
        match=True,
        max_abs_error=max_abs,
        rms_error=rms,
        compared_points=len(expected),
        message="within tolerance",
    )

