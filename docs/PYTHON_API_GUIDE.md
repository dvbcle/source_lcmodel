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

Batch mode example:

```python
batch = LCModelRunner(
    RunConfig(raw_data_list_file="data/raw_list.txt", basis_file="data/basis.txt", batch_csv_file="out/batch.csv")
).run_batch()
print(batch.rows)
print(batch.csv_file)
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
  - `coefficient_sds: tuple[float, ...]`
  - `residual_norm: float`
  - `relative_residual: float`
  - `snr_estimate: float`
  - `alignment_shift_points: int`
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
from lcmodel.io.priors import load_soft_priors
from lcmodel.io.report import write_fit_table
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.phasing import estimate_zero_order_phase, estimate_zero_first_order_phase, apply_zero_order_phase, apply_phase
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.setup import prepare_fit_inputs

layout = split_title_lines("Long title ...", ntitle=2)
escaped = escape_postscript_text("Value (A)%")
left, right = split_output_filename_for_voxel("report.ps", ("ps", "PS", "Ps"))
fit = run_fit_stage([[1, 0], [0, 1]], [2, 3])
fit_with_baseline = run_fit_stage([[1], [0], [0]], [2, 0.1, 0.1], FitConfig(baseline_order=0))
fit_with_spline_baseline = run_fit_stage(
    [[1], [0], [0], [0], [0], [0]],
    [2, 0.1, 0.08, 0.05, 0.03, 0.02],
    FitConfig(baseline_knots=6, baseline_smoothness=1e-2),
)
phase = estimate_zero_order_phase([1j, 1j, 1j])
rot = apply_zero_order_phase([1j, 1j, 1j], phase)
phase0, phase1 = estimate_zero_first_order_phase([1j, 1j, 1j, 1j, 1j])
rot2 = apply_phase([1j, 1j, 1j, 1j, 1j], phase0, phase1)
setup = prepare_fit_inputs([[1, 2], [3, 4]], [10, 20], basis_names=["NAA", "Cr"], include_metabolites=("Cr",))
spectral = prepare_frequency_fit_from_time_domain([1+0j, 0+0j, 0+0j, 0+0j], [[1+0j], [0+0j], [0+0j], [0+0j]], auto_phase_zero_order=True)
spectral_apodized = prepare_frequency_fit_from_time_domain([1+0j, 0+0j, 0+0j, 0+0j], [[1+0j], [0+0j], [0+0j], [0+0j]], dwell_time_s=0.0005, line_broadening_hz=4.0)
spectral_phasta = prepare_frequency_fit_from_time_domain([1+0j, 0+0j, 0+0j, 0+0j], [[1+0j], [0+0j], [0+0j], [0+0j]], auto_phase_first_order=True, phase_objective="smooth_real", phase_smoothness_power=6)
integ = integrate_peak_with_local_baseline([1, 1, 1, 2, 3, 2, 1, 1], peak_index=4, start_index=2, end_index=6, border_width=2)
priors = load_soft_priors("data/priors.txt")
aug_a, aug_b = augment_system_with_soft_priors([[1, 0], [0, 1]], [2, 3], ["NAA", "Cr"], priors)
cfg = load_run_config_from_control_file("data/control.in")
write_fit_table("out/result.table", fit)
```

Combination expressions can be provided via:
- `RunConfig(combine_expressions=("NAA+NAAG", "Glu+Gln"))`
- control file `CHCOMB(1)=...` entries

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

- The fit core now uses an active-set PNNLS-style solver with optional mixed sign constraints.
- Alternating baseline fitting supports either polynomial (`baseline_order`) or cubic B-spline (`baseline_knots`, `baseline_smoothness`) modes.
- Time-domain auto-phasing supports `imag_abs` and Fortran-inspired `smooth_real` objectives.
- Integer alignment search supports circular (Fortran-like) and zero-padded shift modes.
- Optional fractional shift refinement performs continuous sub-point alignment.
- Optional global linewidth scanning applies Gaussian basis broadening and picks the best residual.
- This is still not the full original LCModel nonlinear optimization stack.
- `split_output_filename_for_voxel` handles three extension cases:
  - `.../ps` -> left ends with `/`, right starts with `.ps`
  - `... .ps` -> left ends with `_`, right is `.ps`
  - fallback -> left is original + `_`, right is empty string
