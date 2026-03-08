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

## 5. Current Port Scope

The Python implementation currently includes helper functionality and an
initial `MYDATA` scaffold (`lcmodel.pipeline.mydata.run_mydata_stage`), not yet
the full LCModel fitting stack.
