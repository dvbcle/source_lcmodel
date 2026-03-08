# Conversion Statistics Snapshot

Generated on: 2026-03-08 11:32:20 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 85 files
  - Runtime (`lcmodel/`): 52 files
  - Tests (`tests/`): 29 files
  - Tools (`tools/`): 4 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 47 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 85 | 11,031 | 9,361 | 186 | 1,484 |
| Python runtime (`lcmodel/`) | 52 | 8,238 | 6,978 | 171 | 1,089 |
| Python tests (`tests/`) | 29 | 2,176 | 1,875 | 11 | 290 |
| Python tools (`tools/`) | 4 | 617 | 508 | 4 | 105 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 47 | 5,788 | 4,869 | 108 | 811 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-08 11:32:20 -04:00 after architecture
  and readability updates in Python runtime modules.
