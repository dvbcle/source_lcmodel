# Conversion Statistics Snapshot

Generated on: 2026-03-08 11:19:22 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 83 files
  - Runtime (`lcmodel/`): 51 files
  - Tests (`tests/`): 28 files
  - Tools (`tools/`): 4 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 46 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 83 | 10,942 | 9,296 | 186 | 1,460 |
| Python runtime (`lcmodel/`) | 51 | 8,173 | 6,930 | 171 | 1,072 |
| Python tests (`tests/`) | 28 | 2,152 | 1,858 | 11 | 283 |
| Python tools (`tools/`) | 4 | 617 | 508 | 4 | 105 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 46 | 5,723 | 4,821 | 108 | 794 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-08 11:19:22 -04:00 after mapped
  Fortran-comment additions in Python modules.
