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
    )
)
result = runner.run()

print(result.title_layout.line_count)
print(result.title_layout.lines)
print(result.output_filename_parts)
```

## 2. Core Types

- `RunConfig`
  - `title: str`
  - `ntitle: int`
  - `output_filename: str | None`
- `RunResult`
  - `title_layout: TitleLayout`
  - `output_filename_parts: tuple[str, str] | None`
- `TitleLayout`
  - `lines: tuple[str, str]`
  - `line_count: int`

## 3. Direct Utility Functions

You can also call lower-level helpers:

```python
from lcmodel.core.text import split_title_lines, escape_postscript_text
from lcmodel.io.pathing import split_output_filename_for_voxel

layout = split_title_lines("Long title ...", ntitle=2)
escaped = escape_postscript_text("Value (A)%")
left, right = split_output_filename_for_voxel("report.ps", ("ps", "PS", "Ps"))
```

## 4. API Behavior Notes

- The module currently covers semantically ported preprocessing behavior, not full LCModel numerical fitting.
- `split_output_filename_for_voxel` handles three extension cases:
  - `.../ps` -> left ends with `/`, right starts with `.ps`
  - `... .ps` -> left ends with `_`, right is `.ps`
  - fallback -> left is original + `_`, right is empty string

