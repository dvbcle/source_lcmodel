# LCModel Python-First Port

This repository now uses a Python-first layout instead of a generated
Fortran-to-Python scaffold.

## Package structure

- `lcmodel/engine.py`
  - High-level runner (`LCModelRunner`) that orchestrates semantically ported steps.
- `lcmodel/models.py`
  - Typed dataclasses for run config/results (`RunConfig`, `RunResult`, `TitleLayout`).
- `lcmodel/core/fortran_compat.py`
  - Minimal behavior-critical compatibility helpers (`ilen`, `fortran_nint`).
- `lcmodel/core/text.py`
  - Text and title utilities (`split_title_lines`, PostScript escaping, compact integer formatting).
- `lcmodel/core/axis.py`
  - Axis endpoint rounding logic (`round_axis_endpoints`).
- `lcmodel/core/array_ops.py`
  - Basic in-place array helpers (`reverse_first_n`).
- `lcmodel/io/pathing.py`
  - Output filename split logic for voxel insertion.
- `lcmodel/pipeline/mydata.py`
  - Initial semantic scaffold for the legacy `MYDATA` preprocessing stage.
- `lcmodel/validation/oracle.py`
  - Utilities to run Fortran/Python commands and compare outputs for parity.
- `lcmodel/validation/oracle_cli.py`
  - CLI harness for simple oracle comparisons.
- `lcmodel/cli.py`
  - CLI entrypoint for running the current semantic port scope.

## Hard Cutover Status

Compatibility shims were removed. The `lcmodel/` package is the only supported
runtime surface.

## Run

```powershell
python -m lcmodel --title "Example title" --ntitle 2 --output-filename "C:/tmp/ps"
```

Fit-stage run example:

```powershell
python -m lcmodel --raw-data-file data\\raw.txt --basis-file data\\basis.txt
```

Control-file driven run:

```powershell
python -m lcmodel --control-file data\\control.in
```

## User Documentation

- End-user CLI guide: `docs/END_USER_GUIDE.md`
- Python API guide: `docs/PYTHON_API_GUIDE.md`
- Fortran parity workflow: `docs/FORTRAN_PARITY_WORKFLOW.md`

## Tests

```powershell
python -m unittest discover -s tests -v
```
