"""Validation tools for Fortran-vs-Python parity checks."""

from lcmodel.validation.oracle import (
    CommandResult,
    FileComparisonResult,
    NumericComparisonResult,
    compare_numeric_vectors,
    compare_text_files,
    run_command,
)
from lcmodel.validation.debug_compare import (
    DebugCooData,
    DebugCorData,
    DebugComparisonRow,
    DebugComparisonTable,
    compare_debug_outputs,
    parse_debug_coo,
    parse_debug_cor,
    render_markdown_table,
)

__all__ = [
    "CommandResult",
    "FileComparisonResult",
    "NumericComparisonResult",
    "DebugCooData",
    "DebugCorData",
    "DebugComparisonRow",
    "DebugComparisonTable",
    "compare_numeric_vectors",
    "compare_text_files",
    "compare_debug_outputs",
    "parse_debug_coo",
    "parse_debug_cor",
    "render_markdown_table",
    "run_command",
]
