# Python Architecture

This project uses a layered Python architecture for runtime behavior, with
traceability artifacts kept alongside the codebase for Fortran provenance.

## Layers

- `lcmodel/models.py`
  - Typed run/result dataclasses.
- `lcmodel/engine.py`
  - Main orchestration (`LCModelRunner`) for single and batch flows.
- `lcmodel/pipeline/`
  - Domain stages (`setup`, `fitting`, `nonlinear`, `spectral`, `postprocess`, etc.).
- `lcmodel/io/`
  - File parsing/writing and namelist/control ingestion.
- `lcmodel/core/`
  - Shared numerical and compatibility primitives.
- `lcmodel/traceability/`
  - `fortran_routine_manifest.json`: routine-level Fortran->Python mapping
    artifact.
  - `manifest.py`: manifest loading/audit utilities.
  - `provenance.py`: function decorators and runtime trace-event capture.
- `lcmodel/overrides/`
  - Legacy routine reference implementations kept for traceability mapping and
    migration history, not as the runtime product surface.

## Traceability Strategy

Traceability combines five mechanisms:

1. Generated manifest artifact:
   - `lcmodel/traceability/fortran_routine_manifest.json`
2. Decorator-based provenance tags:
   - `lcmodel.traceability.fortran_provenance`
3. Audit gate:
   - `tools/audit_parity.py`
4. Routine map documentation export:
   - `tools/export_routine_map.py` -> `docs/FORTRAN_ROUTINE_MAP.md`
5. Optional runtime call-trace logs:
   - CLI option `--traceability-log-file`
   - Output includes called Python targets plus associated Fortran routine tags

## Maintenance Rules

1. Keep runtime behavior in `lcmodel/engine.py`, `lcmodel/pipeline/*`,
   `lcmodel/io/*`, and `lcmodel/core/*`.
2. Maintain `lcmodel/traceability/fortran_routine_manifest.json` when Fortran
   source inventory or mapping targets change.
3. Decorate Python runtime entry points with `fortran_provenance(...)` tags so
   provenance and call-trace coverage stay useful.
4. After refactors, run:
   - `python tools/audit_parity.py`
   - `python tools/build_traceability_manifest.py` (when Fortran source changes)
   - `python tools/export_routine_map.py`
5. Ensure tests and parity audit stay green before commit.
