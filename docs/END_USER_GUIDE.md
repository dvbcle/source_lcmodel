# LCModel Python Module End-User Guide

This guide explains how to run the current Python module from the command line.

## 1. Prerequisites

- Python 3.10+ installed
- Project files available locally
- Terminal opened at the project root (`source_lcmodel`)

## 2. Quick Start

Run:

```powershell
python -m lcmodel --title "Example title" --ntitle 2 --output-filename "C:/tmp/ps"
```

Example output:

```text
title_lines=1
title_line_1=Example title
title_line_2=
output_split_left=C:/tmp/
output_split_right=.ps
```

## 3. What Each Argument Does

- `--title`
  - The report title text.
- `--ntitle`
  - Requested title-line behavior.
  - `1` forces one line.
  - `2` allows split logic when needed.
- `--output-filename`
  - Optional output path used to calculate insertion points for voxel IDs.

## 4. Interpreting Output

- `title_lines`
  - Number of title lines after split logic.
- `title_line_1`, `title_line_2`
  - Final title line content.
- `output_split_left`, `output_split_right`
  - Filename parts around where voxel tags can be inserted.
- `output_split=<not requested>`
  - You did not pass `--output-filename`.

## 5. Common Usage Patterns

One-line title only:

```powershell
python -m lcmodel --title "QA Run" --ntitle 1
```

Filename split for `.ps` output:

```powershell
python -m lcmodel --title "Subject 001" --output-filename "results/report.ps"
```

## 6. Troubleshooting

- If command is not found, run `python --version` to confirm Python is installed.
- If module import fails, ensure you are in the repository root when running commands.
- If output filename split is unexpected, verify that the filename ends in a `ps` variant (`ps`, `PS`, `Ps`).

