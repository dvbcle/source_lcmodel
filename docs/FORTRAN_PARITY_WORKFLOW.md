# Fortran Parity Workflow

This document describes how to compare original Fortran behavior with the
current Python port.

## 1. Goal

Use the Fortran executable as an oracle, then verify Python outputs against it
with repeatable pass/fail checks.

## 2. Oracle Harness Components

- `lcmodel.validation.oracle`
  - `run_command(...)`: execute Fortran or Python and capture logs.
  - `compare_text_files(...)`: diff text outputs.
  - `compare_numeric_vectors(...)`: tolerance-based numeric comparison.
- `lcmodel.validation.oracle_cli`
  - Command-line wrapper for common workflows.

## 3. Basic Command Pattern

```powershell
python -m lcmodel.validation.oracle_cli `
  --cwd . `
  --fortran-cmd "path\\to\\LCModel.exe" `
  --fortran-stdin cases\\control_fortran.in `
  --python-cmd "python -m lcmodel --title Example --ntitle 2 --output-filename out\\ps" `
  --compare expected\\file1.txt::actual\\file1.txt
```

Notes:
- `--compare` can be repeated.
- If Fortran exits non-zero, the harness returns that code.
- If file comparisons fail, the harness returns `2`.

## 4. Recommended Regression Strategy

1. Create stable input cases (small and realistic).
2. Record Fortran outputs as expected fixtures.
3. Generate Python outputs from the same inputs.
4. Compare text outputs exactly.
5. Compare numeric outputs with explicit tolerances.
6. Add each case into automated tests before porting the next routine.

## 5. External `test_lcm` Fixture

The public fixture in `schorschinho/LCModel/test_lcm` can be exercised with:

```powershell
python -m lcmodel --control-file control.file
```

Notes:
- The control-file parser supports both `/` and `$END` namelist terminators.
- `.raw` / `.basis` control inputs automatically trigger time-domain ingestion.
- `out.ps` is always produced by Python execution; the runtime no longer has a
  reference-template copy path.
- For copy-guard validation, inject a unique sentinel into `out_ref_build.ps`
  and verify that sentinel is absent from generated `out.ps` before doing the
  normal untouched-reference compare run.

## 6. Intermediate Oracle Debugging

When final PostScript files diverge, run a split oracle debug in isolated
directories (`fortran/` and `python/`) and compare intermediate vectors from
Fortran `debug.coo` against Python pipeline outputs.

Latest stored example:

- Artifact root: `artifacts/parity_debug_20260308_155835/`
- Summary: `artifacts/parity_debug_20260308_155835/parity_summary.txt`
- Key finding in that run:
  Python FFT semantics required Fortran parity behavior (`CFFT_r` unitary
  normalization and half-spectrum rearrangement). After this fix, intermediate
  vector RMS errors dropped substantially but full parity still depends on
  deeper PHASTA/REPHAS nonlinear behavior.

## 7. Latest Iteration (2026-03-09 09:09 -04:00)

- Baseline artifact: `artifacts/parity_iteration_20260309_090229/`
- Post-fix artifact: `artifacts/parity_iteration_20260309_090928/`
- Code changes applied:
  - `FILCOR` export now applies a Fortran `FINOUT`-style correction pass
    (phase/shift then FFT-domain phase path) before writing `debug.cor`.
  - Plot/debug vectors now use the refined nonlinear system
    (`nonlinear.fit_matrix` / `nonlinear.fit_vector`) rather than pre-refinement
    setup vectors.

Measured impact from comparison tables:

- `coo.phased_data` RMS: `9.5597e-05` -> `9.5597e-05` (no change)
- `coo.fit_data` RMS: `9.3338e-05` -> `9.3338e-05` (no change)
- `cor.real` RMS: `6.1137e-05` -> `4.9579e-05` (improved)
- `cor.imag` RMS: `7.1202e-05` -> `5.3272e-05` (improved)

Current likely dominant parity gap:

- Missing deep `STARTV`/`TWOREG` behavior in Python (phase/shift/linewidth
  search path). Fortran debug output for this case reports nonzero final
  corrections (`Data shift = 0.008 ppm`, `Ph: 9 deg, 2.2 deg/ppm`,
  `FWHM = 0.084 ppm`) while the current Python run remains at near-zero
  nonlinear shift/linewidth estimates in this fixture path.

## 8. STARTV/TWOREG Work (2026-03-09 10:28 -04:00)

- Artifact root: `artifacts/parity_iteration_20260309_102838/`
- Focus of this pass:
  - Added a STARTV/TWOREG-style nonlinear refinement path in Python:
    coarse phase candidate search, bounded shift/linewidth scan, and
    lightweight objective solves for runtime feasibility.
  - Added routine-level provenance coverage for
    `startv`, `phasta`, `rephas`, and `shiftd` tags in nonlinear flow.
  - Kept FILCOR output conservative by avoiding unstable nonlinear phase/shift
    corrections when estimates are out-of-family.

Measured impact vs prior baseline (`artifacts/parity_iteration_20260309_090928/`):

- `coo.phased_data` RMS: `9.5597e-05` -> `9.2926e-05` (improved)
- `coo.fit_data` RMS: `9.3338e-05` -> `8.9060e-05` (improved)
- `cor.real` RMS: `4.9579e-05` -> `4.9579e-05` (held)
- `cor.imag` RMS: `5.3272e-05` -> `5.3272e-05` (held)

Current blocker after this pass:

- Nonlinear optimum still tends to push shift/phase bounds for this case,
  indicating remaining mismatch in objective/regularization behavior vs
  Fortran `STARTV`/`TWOREG` (`PLINLS`/`RFALSI`) internals.
