# Python Architecture

This project now uses a layered Python architecture with a legacy-compatibility
boundary, rather than a direct line-by-line Fortran transcription.

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
- `semantic_overrides.py`
  - Thin adapter that composes domain override registries and installs
    placeholder guards.
- `lcmodel/overrides/workflow.py`
  - LCModel orchestration-stage routine bindings (`LCMODL`, setup, IO workflow).
- `lcmodel/overrides/core_compat.py`
  - Legacy numerical/parsing compatibility routines used by scaffold calls.
- `lcmodel/overrides/postscript.py`
  - Postscript output primitives and report-layout routines.
- `lcmodel/overrides/state_ops.py`
  - Shared mutable-sequence helpers for Fortran by-reference argument semantics.
- `lcmodel/fortran_scaffold.py`
  - Auto-generated callable map of Fortran units for traceability.

## Traceability Strategy

- Fortran routine names remain callable through the scaffold.
- `semantic_overrides.SEMANTIC_OVERRIDES` maps each Fortran routine name to a
  concrete Python implementation target.
- Mapping documentation is generated into:
  - `docs/FORTRAN_ROUTINE_MAP.md`
- Mapping export script:
  - `tools/export_routine_map.py`

## Maintenance Rules

1. Keep the domain implementation in `lcmodel/*` modules.
2. Keep `semantic_overrides.py` as an adapter layer only.
3. Add new routine implementations inside the appropriate `lcmodel/overrides/*`
   domain module, then expose the key through that module's registry.
4. After refactors, run:
   - `python tools/audit_parity.py`
   - `python tools/export_routine_map.py`
5. Ensure tests and parity audit stay green before commit.
