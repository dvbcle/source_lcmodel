# Conversion Statistics Snapshot

Generated on: 2026-03-09 07:37:48 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 92 files
  - Runtime (`lcmodel/`): 55 files
  - Tests (`tests/`): 31 files
  - Tools (`tools/`): 6 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 50 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 92 | 13,755 | 11,796 | 225 | 1,734 |
| Python runtime (`lcmodel/`) | 55 | 10,045 | 8,599 | 204 | 1,242 |
| Python tests (`tests/`) | 31 | 2,728 | 2,368 | 17 | 343 |
| Python tools (`tools/`) | 6 | 982 | 829 | 4 | 149 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 50 | 7,595 | 6,490 | 141 | 964 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-09 07:37:48 -04:00 after adding
  Fortran-style debug output writers (FILCOO/FILCOR analogs), debug parsers,
  and a comparison-table utility for intermediate-output parity checks.
