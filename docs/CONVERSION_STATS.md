# Conversion Statistics Snapshot

Generated on: 2026-03-08 22:35:22 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 88 files
  - Runtime (`lcmodel/`): 53 files
  - Tests (`tests/`): 30 files
  - Tools (`tools/`): 5 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 48 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 88 | 13,154 | 11,273 | 225 | 1,656 |
| Python runtime (`lcmodel/`) | 53 | 9,648 | 8,256 | 204 | 1,188 |
| Python tests (`tests/`) | 30 | 2,581 | 2,234 | 17 | 330 |
| Python tools (`tools/`) | 5 | 925 | 783 | 4 | 138 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 48 | 7,198 | 6,147 | 141 | 910 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-08 22:35:22 -04:00 after adding
  Fortran-style FILH2O/DOECC/DOWS data-flow support to the Python-first
  runtime and tests.
