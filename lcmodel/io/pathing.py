"""Filename/path helpers for LCModel output handling."""

from __future__ import annotations

from lcmodel.core.fortran_compat import ilen
from lcmodel.traceability import fortran_provenance


@fortran_provenance("split_filename")
def split_output_filename_for_voxel(
    filename: str,
    extension_variants: tuple[str, str, str],
) -> tuple[str, str]:
    """Split filename into insertion-friendly parts.

    Returns `(left, right)` where callers insert voxel tags as:
    - case 1: `left + voxel + right` -> `/path/` + `v001` + `.ps`
    - case 2: `left + voxel + right` -> `/path/file_` + `v001` + `.ps`
    - case 3 fallback: `left + voxel + right` -> `/path/file_` + `v001` + ``
    """

    name = str(filename)
    trimmed = name[: ilen(name)]
    ext1, ext2, ext3 = extension_variants
    lchtype = len(ext1)

    left = f"{trimmed}_"
    right = ""

    if lchtype > 0 and ilen(trimmed) >= lchtype:
        ichtype = ilen(trimmed) - lchtype + 1  # 1-based
        suffix = trimmed[ichtype - 1 :]
        choices = (ext1[:lchtype], ext2[:lchtype], ext3[:lchtype])
        if any(suffix.startswith(choice) for choice in choices):
            marker_pos = ichtype - 1  # 1-based
            if marker_pos >= 1:
                marker = trimmed[marker_pos - 1]
                if marker in {"/", "\\"}:
                    left = trimmed[:marker_pos]
                    right = "." + trimmed[ichtype - 1 :]
                    return left, right
                if marker == ".":
                    left = trimmed[: marker_pos - 1] + "_"
                    right = trimmed[marker_pos - 1 :]
                    return left, right

    return left, right
