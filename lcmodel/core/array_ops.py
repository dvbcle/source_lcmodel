"""Array/list helpers for semantically ported routines."""

from __future__ import annotations

from typing import MutableSequence, TypeVar

T = TypeVar("T")


def reverse_first_n(values: MutableSequence[T], n: int) -> MutableSequence[T]:
    """In-place reverse of the first `n` elements."""

    count = max(0, int(n))
    left = 0
    right = count - 1
    while left < right:
        values[left], values[right] = values[right], values[left]
        left += 1
        right -= 1
    return values

