# Conversion Statistics Snapshot

Generated on: 2026-03-08

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 75 files
  - Runtime (excluding `tests/` and `tools/`): 46 files
  - Tests only: 26 files
  - Tools only: 3 files
  - Runtime excluding generated scaffold: 45 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 75 | 29,576 | 10,200 | 17,773 | 1,603 |
| Python runtime (excl. tests/tools) | 46 | 26,788 | 7,834 | 17,759 | 1,195 |
| Python tests | 26 | 2,173 | 1,864 | 11 | 298 |
| Python tools | 3 | 615 | 502 | 3 | 110 |
| Python scaffold only (`lcmodel/fortran_scaffold.py`) | 1 | 19,278 | 1,375 | 17,743 | 160 |
| Python runtime excl. scaffold/tests/tools | 45 | 7,510 | 6,459 | 16 | 1,035 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
