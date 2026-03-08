# LCModel Python API Guide

This guide shows how to call the module from Python code.

## 1. Minimal Example

```python
from lcmodel import LCModelRunner, RunConfig

runner = LCModelRunner(
    RunConfig(
        title="A short title",
        ntitle=2,
        output_filename="abc.ps",
        raw_data_file="data/raw.txt",
        basis_file="data/basis.txt",
    )
)
result = runner.run()

print(result.title_layout.line_count)
print(result.title_layout.lines)
print(result.output_filename_parts)
print(result.fit_result)
```

## 2. Core Types

- `RunConfig`
  - `title: str`
  - `ntitle: int`
  - `output_filename: str | None`
- `RunResult`
  - `title_layout: TitleLayout`
  - `output_filename_parts: tuple[str, str] | None`
  - `fit_result: FitResult | None`
- `FitResult`
  - `coefficients: tuple[float, ...]`
  - `residual_norm: float`
  - `iterations: int`
  - `method: str`
- `TitleLayout`
  - `lines: tuple[str, str]`
  - `line_count: int`

## 3. Direct Utility Functions

You can also call lower-level helpers:

```python
from lcmodel.core.text import split_title_lines, escape_postscript_text
from lcmodel.io.namelist import load_run_config_from_control_file
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.pipeline.fitting import run_fit_stage

layout = split_title_lines("Long title ...", ntitle=2)
escaped = escape_postscript_text("Value (A)%")
left, right = split_output_filename_for_voxel("report.ps", ("ps", "PS", "Ps"))
fit = run_fit_stage([[1, 0], [0, 1]], [2, 3])
cfg = load_run_config_from_control_file("data/control.in")
```

## 4. MYDATA Scaffold (Initial Semantic Port)

```python
from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage

result = run_mydata_stage(
    [1+0j, 0+0j, 0+0j],
    MyDataConfig(zero_fill_to=4, compute_fft=True),
)

print(result.time_domain)
print(result.frequency_domain)
print(result.processing_log)
```

## 5. API Behavior Notes

- The module currently covers semantically ported preprocessing behavior, not full LCModel numerical fitting.
- `split_output_filename_for_voxel` handles three extension cases:
  - `.../ps` -> left ends with `/`, right starts with `.ps`
  - `... .ps` -> left ends with `_`, right is `.ps`
  - fallback -> left is original + `_`, right is empty string
