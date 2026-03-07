# Python Conversion Output

This folder now includes a Python conversion scaffold for the Fortran sources:

- `lcmodel_converted.py`: Auto-generated Python module with one function per Fortran program unit.
- `tools/transpile_fortran77_to_python.py`: Converter script used to generate the module.

## What this conversion does

- Preserves the Fortran routine structure (`PROGRAM`, `SUBROUTINE`, `FUNCTION`, `BLOCK DATA`).
- Converts each routine into a Python function.
- Keeps original Fortran lines as in-function Python comments for traceability.
- Adds a Python `main()` entrypoint.

## What this conversion does not do (yet)

- It is a structural scaffold, not a full semantic port.
- Numerical behavior and Fortran control flow are not automatically reproduced.

## How a Python developer should use this scaffold

- Start from the function matching the Fortran routine you want to port.
- Add semantic Python logic *above* the preserved Fortran statement comments.
- Use the `[file:line]` markers in comments to cross-check behavior in `LCModel.f`.
- Keep the original statement comments in place until the routine is fully ported.

## Incremental semantic overrides

- `semantic_overrides.py` contains executable Python ports for selected routines.
- `lcmodel_converted.py` automatically dispatches to these overrides when present.
- Current overrides include:
  - `split_filename`
  - `icharst`
  - `chstrip_int6`
  - `split_title`
  - `revers`
  - `endrnd`
  - `strchk`

## Regenerate the Python scaffold

```powershell
python tools/transpile_fortran77_to_python.py LCModel.f lcmodel.inc lipid-1.inc liver-1.inc muscle-1.inc nml_lcmodel.inc nml_lcmodl.inc -o lcmodel_converted.py
```

## Validate syntax

```powershell
python -m py_compile lcmodel_converted.py tools/transpile_fortran77_to_python.py
```
