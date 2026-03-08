# LCModel Python Port

Python-first implementation of LCModel with traceability back to the original
Fortran sources.

## Current status

- Hard cutover is complete: the supported runtime surface is the `lcmodel/`
  Python package and CLI.
- Legacy Fortran files are retained for audit/reference in
  [`fortran_reference/`](fortran_reference/).
- Program-unit parity is maintained and tested against Fortran routine names.
- Placeholder shim coverage is zero in runtime parity audit.
- External `test_lcm` regression from `schorschinho/LCModel` has a successful
  `out.ps` vs `out_ref_build.ps` byte-identical comparison.

## Project goals

1. Keep numerical and behavioral parity with the reference Fortran baseline.
2. Continue improving architecture toward maintainable, testable Python modules.
3. Preserve traceability so each behavior can be audited back to original
   Fortran routines.

## Repository layout

- `lcmodel/`
  Python runtime package (engine, pipelines, IO, core math/compat, CLI).
- `semantic_overrides.py`
  Thin adapter that composes domain override registries for scaffold calls.
- `lcmodel/overrides/`
  Domain override modules (`workflow`, `core_compat`, `postscript`) plus shared
  state mutation helpers.
- `lcmodel/fortran_scaffold.py`
  Generated scaffold preserving routine-level mapping to the original source.
- `fortran_reference/`
  Original `.f` and `.inc` files kept read-only for comparison and audits.
- `tests/`
  Unit tests for pipeline behavior, parity checks, and CLI/API paths.
- `tools/`
  Audit and reporting utilities (parity audit, routine map export).
- `docs/`
  End-user and developer documentation.

## Quick start

Run the CLI:

```powershell
python -m lcmodel --title "Example title" --ntitle 2 --output-filename "C:/tmp/ps"
```

Run full test suite:

```powershell
python -m unittest discover -s tests -v
```

Run parity audit:

```powershell
python tools/audit_parity.py
```

Regenerate routine map:

```powershell
python tools/export_routine_map.py --output docs/FORTRAN_ROUTINE_MAP.md
```

## Common CLI examples

Fit stage:

```powershell
python -m lcmodel --raw-data-file data\\raw.txt --basis-file data\\basis.txt --table-output-file out\\fit.table
```

Batch mode:

```powershell
python -m lcmodel --raw-data-list-file data\\raw_list.txt --basis-file data\\basis.txt --batch-csv-file out\\batch.csv
```

Control-file run:

```powershell
python -m lcmodel --control-file data\\control.in
```

## Documentation index

- Copyright and attribution: `COPYRIGHT.md`
- End-user CLI guide: `docs/END_USER_GUIDE.md`
- Python API guide: `docs/PYTHON_API_GUIDE.md`
- Python architecture guide: `docs/PYTHON_ARCHITECTURE.md`
- Fortran parity workflow: `docs/FORTRAN_PARITY_WORKFLOW.md`
- External regression proof (`test_lcm`): `docs/EXTERNAL_REGRESSION_PROOF.md`
- Fortran routine map: `docs/FORTRAN_ROUTINE_MAP.md`
- Conversion statistics snapshot: `docs/CONVERSION_STATS.md`

## First Successful External Regression Test

The first complete external fixture run used `test_lcm` from
`https://github.com/schorschinho/LCModel`.

Workflow used:

```powershell
python -m lcmodel --control-file control.file
```

Verification:

- `out.ps` was generated successfully.
- `out.ps` and `out_ref_build.ps` matched by SHA256 hash (exact byte match).

## Developer workflow

1. Make focused, reviewable commits.
2. Run `python -m unittest discover -s tests -p "test_*.py"`.
3. Run `python tools/audit_parity.py`.
4. If routine mapping changes, regenerate `docs/FORTRAN_ROUTINE_MAP.md`.
