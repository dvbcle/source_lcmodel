"""Validation tools for Fortran-vs-Python parity checks."""

from lcmodel.validation.oracle import (
    CommandResult,
    FileComparisonResult,
    NumericComparisonResult,
    compare_numeric_vectors,
    compare_text_files,
    run_command,
)

__all__ = [
    "CommandResult",
    "FileComparisonResult",
    "NumericComparisonResult",
    "compare_numeric_vectors",
    "compare_text_files",
    "run_command",
]

