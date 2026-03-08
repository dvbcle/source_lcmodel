"""Top-level semantic override registry for the Fortran scaffold bridge."""

from __future__ import annotations

import pathlib

from lcmodel.legacy_bridge import install_missing_overrides
from lcmodel.overrides import POSTSCRIPT_OVERRIDES, WORKFLOW_OVERRIDES
from lcmodel.overrides.core_compat import CORE_COMPAT_OVERRIDES

# Compose domain registries into the runtime override surface consumed by
# lcmodel.fortran_scaffold.
SEMANTIC_OVERRIDES = {
    **WORKFLOW_OVERRIDES,
    **CORE_COMPAT_OVERRIDES,
    **POSTSCRIPT_OVERRIDES,
}


_PLACEHOLDER_OVERRIDES: set[str] = set()
install_missing_overrides(
    overrides=SEMANTIC_OVERRIDES,
    source_file=pathlib.Path(__file__).parent / "fortran_reference" / "LCModel.f",
    placeholder_set=_PLACEHOLDER_OVERRIDES,
)


__all__ = ["SEMANTIC_OVERRIDES", "_PLACEHOLDER_OVERRIDES"]
