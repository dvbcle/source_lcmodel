"""Compatibility entrypoint retained from earlier conversion stage.

The active Python-first implementation lives under the `lcmodel` package.
This file keeps legacy imports operational during migration.
"""

from __future__ import annotations

from lcmodel.cli import main
from semantic_overrides import (
    SEMANTIC_OVERRIDES,
    chstrip_int6,
    endrnd,
    icharst,
    revers,
    split_filename,
    split_title,
    strchk,
)

__all__ = [
    "SEMANTIC_OVERRIDES",
    "split_filename",
    "icharst",
    "chstrip_int6",
    "split_title",
    "revers",
    "endrnd",
    "strchk",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())

