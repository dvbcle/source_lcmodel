# Developer Module Map

Quick orientation for collaborators working on the Python runtime surface.

## Runtime entry points

- `lcmodel.application.run_lcmodel(config)`
  - Canonical single-run API used by external Python callers.
- `lcmodel.application.run_lcmodel_batch(config)`
  - Canonical batch-run API.
- `python -m lcmodel ...`
  - CLI entrypoint (`lcmodel.cli`) that routes into `lcmodel.application`.

## Runtime layers

- `lcmodel/engine.py`
  - Top-level orchestration (`LCModelRunner`), output writing, batch flow.
- `lcmodel/pipeline/`
  - Fit stages and domain behavior.
  - `setup.py`: active ppm window and metabolite subset selection.
  - `spectral.py` / `mydata.py`: time-domain preprocessing and FFT conversion.
  - `fitting.py`: constrained linear solve and baseline modeling.
  - `nonlinear.py`, `alignment.py`, `lineshape.py`: nonlinear refinements.
  - `postprocess.py`, `integration.py`, `metrics.py`: reporting metrics.
- `lcmodel/io/`
  - Control-file parsing plus basis/raw/prior/report file IO.
- `lcmodel/core/`
  - Numerical and compatibility primitives shared across stages.

## Traceability and parity artifacts

- `lcmodel/traceability/fortran_routine_manifest.json`
  - Fortran-to-Python routine mapping artifact.
- `docs/FORTRAN_ROUTINE_MAP.md`
  - Human-readable export of routine mapping.
- `tools/audit_parity.py`
  - Mapping coverage and parity checks.

## Legacy compatibility adapter (non-product surface)

- `lcmodel/overrides/`
  - Routine-reference compatibility implementations retained for traceability
    and migration history.
  - New runtime feature work should target `lcmodel/engine.py`,
    `lcmodel/pipeline/`, `lcmodel/io/`, and `lcmodel/core/`.
