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
- `lcmodel/cli.py`
  - CLI entrypoint for running the current semantic port scope.

## Compatibility files

- `semantic_overrides.py`
  - Adapter layer for legacy scaffold function names/signatures.
- `lcmodel_converted.py`
  - Thin compatibility module; no longer the primary implementation.

## Run

```powershell
python -m lcmodel --title "Example title" --ntitle 2 --output-filename "C:/tmp/ps"
```

## Tests

```powershell
python -m unittest discover -s tests -v
```

