# Conversion Statistics Snapshot

Generated on: 2026-03-08 16:55:32 -04:00

This snapshot compares original Fortran source size with the resulting Python codebase.

## Source sets

- Fortran files counted (7, in `fortran_reference/`): `LCModel.f`, `lcmodel.inc`, `lipid-1.inc`, `liver-1.inc`, `muscle-1.inc`, `nml_lcmodel.inc`, `nml_lcmodl.inc`
- Python files counted:
  - All Python: 86 files
  - Runtime (`lcmodel/`): 52 files
  - Tests (`tests/`): 29 files
  - Tools (`tools/`): 5 files
  - Pure runtime surface (runtime excluding `lcmodel/overrides/`): 47 files
  - Legacy routine-reference overrides (`lcmodel/overrides/`): 5 files

## Line counts

| Scope | Files | Total | Code | Comment | Blank |
|---|---:|---:|---:|---:|---:|
| Fortran (`*.f`, `*.inc`) | 7 | 19,469 | 14,267 | 4,919 | 283 |
| Python (all `*.py`) | 86 | 11,778 | 10,023 | 199 | 1,556 |
| Python runtime (`lcmodel/`) | 52 | 8,465 | 7,173 | 180 | 1,112 |
| Python tests (`tests/`) | 29 | 2,388 | 2,067 | 15 | 306 |
| Python tools (`tools/`) | 5 | 925 | 783 | 4 | 138 |
| Python pure runtime surface (`lcmodel/` excl. `overrides/`) | 47 | 6,015 | 5,064 | 117 | 834 |
| Python legacy routine-reference overrides (`lcmodel/overrides/`) | 5 | 2,450 | 2,109 | 63 | 278 |

## Notes

- Fortran comments are identified via fixed-form first-column markers (`C/c`, `*`, `!`).
- Python comments count only `#...` lines; triple-quoted docstrings count as code.
- Statistics reflect the post-cutover pure runtime surface where generated scaffold files are removed from runtime.
- Refreshed and re-verified on 2026-03-08 16:55:32 -04:00 after implementing
  Fortran-aligned CFFT_r semantics (unitary normalization + half-spectrum
  rearrangement), adding FFT parity regression tests, and recording latest
  oracle-debug evidence paths.
