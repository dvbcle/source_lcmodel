# Conversion Statistics Snapshot

Generated on: 2026-03-08 15:00:50 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 84 files
  - Runtime (`lcmodel/`): 52 files
  - Tests (`tests/`): 28 files
  - Tools (`tools/`): 4 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 47 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 84 | 11,192 | 9,515 | 182 | 1,495 |
| Python runtime (`lcmodel/`) | 52 | 8,387 | 7,114 | 167 | 1,106 |
| Python tests (`tests/`) | 28 | 2,188 | 1,893 | 11 | 284 |
| Python tools (`tools/`) | 4 | 617 | 508 | 4 | 105 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 47 | 5,937 | 5,005 | 104 | 828 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-08 15:00:50 -04:00 after removing
  PostScript reference-template copy behavior and updating regression guard tests.
