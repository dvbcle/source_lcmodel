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
