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
- `--control-file`
  - Path to LCModel-style `$LCMODL ... /` control input.
  - Values in this file seed runtime settings; CLI flags can still override.
- `--ntitle`
  - Requested title-line behavior.
  - `1` forces one line.
  - `2` allows split logic when needed.
- `--output-filename`
  - Optional output path used to calculate insertion points for voxel IDs.
- `--table-output-file`
  - Optional path for writing a tab-delimited fit summary file.
- `--time-domain-input`
  - Treat raw and basis files as complex time-domain values (`re im` format).
- `--auto-phase-zero-order`
  - Apply auto-estimated zero-order phase after FFT conversion.
- `--auto-phase-first-order`
  - Apply joint zero/first-order auto-phasing after FFT conversion.
- `--phase-objective`
  - Phasing objective: `imag_abs` (default) or `smooth_real` (PHASTA-style).
- `--phase-smoothness-power`
  - Exponent used by `smooth_real` objective (Fortran `IPOWPH` analog).
- `--dwell-time`
  - Time between time-domain samples (seconds).
- `--line-broadening-hz`
  - Exponential broadening parameter for time-domain apodization.
- `--raw-data-file`
  - Optional numeric vector file for the fit stage.
- `--raw-data-list-file`
  - Optional file list for batch mode (one raw file path per line).
- `--batch-csv-file`
  - Optional output CSV for batch summary results.
- `--basis-file`
  - Optional numeric matrix file for the fit stage.
- `--ppm-axis-file`
  - Optional ppm values aligned with each data row.
- `--basis-names-file`
  - Optional metabolite names aligned with basis columns.
- `--priors-file`
  - Optional soft priors file with rows `name mean sd`.
- `--ppm-start`, `--ppm-end`
  - Optional ppm window boundaries for row selection before fitting.
- `--include-metabolites`
  - Optional comma-separated metabolite names to keep in the fit.
- `--combine-expressions`
  - Optional comma-separated combinations, e.g. `NAA+NAAG,Glu+Gln`.
- `--shift-search-points`
  - Optional integer search range for pre-fit alignment shift.
- `--alignment-mode`
  - Shift mode for alignment search: `circular` (Fortran SHIFTD-like) or `zero_padded`.
- `--fractional-shift-refine`
  - Enable sub-point shift refinement after integer shift search.
- `--fractional-shift-iterations`
  - Search iterations used for fractional shift refinement.
- `--linewidth-scan-points`
  - Number of global linewidth scan points (`0` disables).
- `--linewidth-scan-max-sigma-points`
  - Maximum Gaussian sigma (in points) explored by linewidth scan.
- `--baseline-order`
  - Polynomial baseline degree for alternating fit (`-1` disables baseline).
- `--baseline-knots`
  - Cubic B-spline knot count for baseline modeling (`>=4` enables spline mode).
- `--baseline-smoothness`
  - Smoothness penalty weight for spline baseline regularization.
- `--integration-half-width-points`
  - Initial half-window used for peak-area integration.
- `--integration-border-points`
  - Border window width used to estimate local integration baseline.

## 4. Interpreting Output

- `title_lines`
  - Number of title lines after split logic.
- `title_line_1`, `title_line_2`
  - Final title line content.
- `output_split_left`, `output_split_right`
  - Filename parts around where voxel tags can be inserted.
- `output_split=<not requested>`
  - You did not pass `--output-filename`.
- `fit_result=<not requested>`
  - You did not pass both `--raw-data-file` and `--basis-file`.
- `fit_coefficients`
  - Nonnegative fit coefficients from the current semantic fit stage.
- `fit_coeff_sds`
  - Approximate standard deviations for fit coefficients.
- `fit_metabolites`
  - Metabolite names corresponding to coefficient order.
- `fit_points_used`
  - Number of rows used after setup-stage selection.
- `fit_relative_residual`
  - Norm of residual divided by norm of fitted data vector.
- `fit_snr_estimate`
  - Simple peak/residual-noise SNR estimate.
- `fit_alignment_shift_points`
  - Integer shift selected during pre-fit alignment.
- `fit_alignment_shift_fractional_points`
  - Refined continuous shift value when fractional refinement is enabled.
- `fit_linewidth_sigma_points`
  - Selected global linewidth broadening sigma from scan stage.
- `fit_integrated_data_area`, `fit_integrated_fit_area`
  - Baseline-corrected peak areas from a local-window integration step.
- `fit_combinations`
  - Combined outputs in `name:value:sd` format.

## 5. Common Usage Patterns

One-line title only:

```powershell
python -m lcmodel --title "QA Run" --ntitle 1
```

Filename split for `.ps` output:

```powershell
python -m lcmodel --title "Subject 001" --output-filename "results/report.ps"
```

Run fit stage:

```powershell
python -m lcmodel --raw-data-file data\\raw.txt --basis-file data\\basis.txt
```

Run from control file:

```powershell
python -m lcmodel --control-file data\\control.in
```

Run batch mode:

```powershell
python -m lcmodel --raw-data-list-file data\\raw_list.txt --basis-file data\\basis.txt --batch-csv-file out\\batch.csv
```

## 6. Troubleshooting

- If command is not found, run `python --version` to confirm Python is installed.
- If module import fails, ensure you are in the repository root when running commands.
- If output filename split is unexpected, verify that the filename ends in a `ps` variant (`ps`, `PS`, `Ps`).
