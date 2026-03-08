# Traceability System

This project keeps Fortran-to-Python traceability without exposing a Fortran
scaffold runtime surface.

## Components

1. Manifest artifact
   - `lcmodel/traceability/fortran_routine_manifest.json`
   - Contains one record per Fortran program unit with mapped Python target.
2. Provenance decorators
   - `lcmodel.traceability.fortran_provenance(...)`
   - Tags Python runtime functions with routine-name provenance metadata.
3. Audit gate
   - `python tools/audit_parity.py`
   - Verifies manifest coverage, importability, and provenance consistency.
4. Routine-map docs export
   - `python tools/export_routine_map.py`
   - Produces `docs/FORTRAN_ROUTINE_MAP.md`.
5. Runtime call tracing
   - CLI: `--traceability-log-file <path>`
   - Writes JSON containing called Python targets and associated Fortran routine tags.

## Typical Maintenance Flow

1. Update code mappings or Fortran reference.
2. Refresh manifest structure:

```powershell
python tools/build_traceability_manifest.py
```

3. Re-export routine map docs:

```powershell
python tools/export_routine_map.py --output docs/FORTRAN_ROUTINE_MAP.md
```

4. Run audit:

```powershell
python tools/audit_parity.py
```

5. Run tests:

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```
