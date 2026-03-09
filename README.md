# LCModel Python Port

Python-first implementation of LCModel with traceability back to the original
Fortran sources.

For first-time visitors: start with `Project goals`, then run `Quick start`,
then check `Current status` for migration and compatibility details.

Most migration and refactoring work in this repository was completed using
OpenAI Codex tooling, with project-owner direction and acceptance validation.

## Human oversight

Project-owner oversight covered product and engineering governance rather than
line-by-line manual transcription of every change:

1. Scope and priority control:
   defined sequencing (parity, cutover, architecture cleanup, docs) and
   accepted/rejected proposed directions.
2. Acceptance criteria:
   required repeatable checks (unit tests, parity audits, external regression)
   before milestones were considered complete.
3. Release and repository decisions:
   approved branch/repo operations, publication steps, and runtime-surface
   cutover choices.
4. Quality gates:
   requested iterative refactors, documentation improvements, and traceability
   guarantees for collaborator onboarding and legacy-user transparency.

## Project goals

1. Keep numerical and behavioral parity with the reference Fortran baseline.
2. Continue improving architecture toward maintainable, testable Python modules.
3. Preserve traceability so each behavior can be audited back to original
   Fortran routines.

## Development history

1. Initial phase: generated Fortran scaffold and routine-level compatibility
   shims to establish broad conversion coverage.
2. Semantic porting phase: numerical and workflow behavior moved into
   Python-first modules under `lcmodel/core`, `lcmodel/io`, and
   `lcmodel/pipeline`.
3. Hard cutover phase: scaffold runtime entry points were removed from the
   supported product surface.
4. Traceability phase: manifest-based routine mapping, provenance decorators,
   parity audit tooling, and runtime trace logs were added for collaborator and
   legacy-user transparency.

## Current status

- The migration cutover is complete: the supported runtime surface is the
  `lcmodel/` Python package and CLI.
- The historical conversion scaffold was an intermediate, generated
  Fortran-shaped call layer used during migration; it is no longer used for
  production execution.
- Legacy scaffold entry points (`fortran_scaffold`, `semantic_overrides`) were
  removed from the runtime product surface. New features and fixes should be
  implemented in Python-first modules under `lcmodel/`.
- Legacy Fortran files are retained for audit/reference in
  [`fortran_reference/`](fortran_reference/).
- Routine-level traceability is maintained through a machine-readable manifest,
  provenance decorators, and parity audits.
- External `test_lcm` regression now runs in strict generated-only mode:
  `out.ps` must be produced by Python execution and only then compared to
  `out_ref_build.ps` (no template-copy path).
- Current external regression state (as of March 9, 2026): **not passing**
  (`byte_match=False`), despite clean isolated execution (`python_returncode=0`,
  `hygiene_ok=True`).

### Architectural approach details

The conversion was done as a staged architecture migration rather than a
single rewrite:

1. Compatibility bootstrap:
   - Start from generated routine-level coverage so every Fortran unit had a
     tracked Python counterpart.
2. Semantic extraction:
   - Move behavior into domain modules (`core`, `io`, `pipeline`, `engine`)
     with Python datamodels and tests.
3. Product-surface cutover:
   - Remove scaffold runtime entrypoints and keep only Python-first CLI/API
     execution paths.
4. Traceability preservation:
   - Keep Fortran parity visibility via manifest/audit/provenance tooling
     instead of scaffold-based runtime dispatch.

## Repository layout

- `lcmodel/`
  Python runtime package (engine, pipelines, IO, core math/compat, CLI).
- `lcmodel/traceability/`
  Traceability subsystem (manifest loader/audit, provenance decorators, runtime
  call-trace support, and the manifest JSON artifact).
- `lcmodel/overrides/`
  Legacy routine-reference implementations preserved for traceability mapping.
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

Refresh traceability manifest structure after Fortran source updates:

```powershell
python tools/build_traceability_manifest.py
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

Control-file run with trace log:

```powershell
python -m lcmodel --control-file data\\control.in --traceability-log-file artifacts\\trace.json
```

## Documentation index

- Copyright and attribution: `COPYRIGHT.md`
- End-user CLI guide: `docs/END_USER_GUIDE.md`
- Python API guide: `docs/PYTHON_API_GUIDE.md`
- Python architecture guide: `docs/PYTHON_ARCHITECTURE.md`
- Developer module map: `docs/DEVELOPER_MODULE_MAP.md`
- Traceability system guide: `docs/TRACEABILITY_SYSTEM.md`
- Prompt playbook (teaching artifact): `docs/PROMPT_PLAYBOOK.md`
- Full prompt transcript archive: `docs/archive/chat_transcript_full_2026-03-08.md`
- Performance measurements: `docs/PERFORMANCE_MEASUREMENTS.md`
- Fortran parity workflow: `docs/FORTRAN_PARITY_WORKFLOW.md`
- External regression proof (`test_lcm`): `docs/EXTERNAL_REGRESSION_PROOF.md`
- Fortran routine map: `docs/FORTRAN_ROUTINE_MAP.md`
- Conversion statistics snapshot: `docs/CONVERSION_STATS.md`

## External Regression Validation

External fixture validation uses `test_lcm` from
`https://github.com/schorschinho/LCModel`.

Workflow used:

```powershell
python tools/run_external_regression_clean.py
```

Verification:

- `out.ps` was generated successfully.
- `out.ps` is now always generated by execution; no runtime template-copy path.
- Clean-run hygiene is enforced:
  - fixture-set validation (default expected inputs:
    `control.file,data.raw,3t.basis,out_ref_build.ps`)
  - stale generated-file rejection (`out.ps`, `python_run.log`, `run_summary.txt`)
  - pre/post inventory and hash-based mutation checks in each run directory
- Current strict generated-only run status is recorded in
  `docs/EXTERNAL_REGRESSION_PROOF.md`.
- Latest recorded strict run (March 9, 2026, run directory
  `artifacts/external_regression_clean_20260309_075544_880525`) reports:
  - `python_returncode=0`
  - `hygiene_ok=True`
  - `byte_match=False`
  - `out_sha256=EA00C82D7334C23137DC711ABF2D0F9EA0F23851E8B75CBDB2AFFDC525D84811`
  - `ref_sha256=ED84E9B18FC0968528939C1355E90A6220D96DA770AD4032094FD9D13DD5E2E5`

## Developer workflow

1. Sync to latest `main` and read `docs/PYTHON_ARCHITECTURE.md`, `docs/DEVELOPER_MODULE_MAP.md`, and `docs/TRACEABILITY_SYSTEM.md`.
2. Make a focused change in Python-first runtime modules (`lcmodel/core`, `lcmodel/io`, `lcmodel/pipeline`, `lcmodel/engine`).
3. Run `python -m unittest discover -s tests -p "test_*.py"`.
4. Run `python tools/audit_parity.py`.
5. If mapping or Fortran inventory changes, run:
   `python tools/build_traceability_manifest.py`
   then
   `python tools/export_routine_map.py --output docs/FORTRAN_ROUTINE_MAP.md`.
6. If source code changed, refresh `docs/CONVERSION_STATS.md`.
7. Update docs for user-visible behavior changes, then commit in small, reviewable units.

## How to contribute

New collaborators can help effectively in any of these areas:

1. Numerical parity:
   add/expand oracle-style comparisons (compare Python outputs against a
   trusted reference output for identical inputs) and external regression
   fixtures.
2. Algorithm depth:
   improve specific fitting, baseline, phasing, or nonlinear refinement behaviors while preserving tests.
3. Reliability:
   add edge-case tests for control-file parsing, IO variants, and malformed inputs.
4. Traceability:
   improve manifest quality, provenance coverage, and mapping documentation.
5. Developer UX:
   improve docs, CLI ergonomics, and reproducible validation workflows.
