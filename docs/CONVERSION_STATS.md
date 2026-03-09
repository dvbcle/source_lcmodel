# Conversion Statistics Snapshot

Generated on: 2026-03-09 10:33:22 -04:00

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
| Python (all `*.py`) | 92 | 14,137 | 12,141 | 238 | 1,758 |
| Python runtime (`lcmodel/`) | 55 | 10,420 | 8,936 | 217 | 1,267 |
| Python tests (`tests/`) | 31 | 2,731 | 2,372 | 17 | 342 |
| Python tools (`tools/`) | 6 | 986 | 833 | 4 | 149 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 50 | 7,970 | 6,827 | 154 | 989 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-09 10:33:22 -04:00 after
  STARTV/TWOREG-oriented nonlinear search updates, alignment objective tuning,
  and additional regression-facing tests/documentation.
