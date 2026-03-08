"""Shared state mutation helpers for Fortran-style by-reference arguments."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import Any


def assign_vector(target: Any, values: Sequence[complex]) -> None:
    """Copy values into a mutable sequence target (up to the shared length)."""
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(values))
        for i in range(limit):
            target[i] = values[i]


def assign_scalar(target: Any, value: Any) -> None:
    """Write a scalar value into index 0 when the target is mutable."""
    if isinstance(target, MutableSequence) and len(target) >= 1:
        target[0] = value


def copy_sequence_prefix(target: Any, source: Sequence[Any]) -> None:
    """Copy source values into target for the overlapping prefix length."""
    if isinstance(target, MutableSequence):
        limit = min(len(target), len(source))
        for i in range(limit):
            target[i] = source[i]


__all__ = ["assign_vector", "assign_scalar", "copy_sequence_prefix"]
