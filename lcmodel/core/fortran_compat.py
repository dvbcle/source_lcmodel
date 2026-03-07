"""Small compatibility primitives mirroring Fortran behavior where needed."""

from __future__ import annotations

import math
from typing import Any


def ilen(text: Any) -> int:
    """Fortran ILEN equivalent: length without trailing spaces."""

    if text is None:
        return 0
    return len(str(text).rstrip(" "))


def fortran_nint(value: float) -> int:
    """Fortran NINT rounding (ties away from zero)."""

    if value >= 0.0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))

