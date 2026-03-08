from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TitleLayout:
    """Layout decision for a report title."""

    lines: tuple[str, str]
    line_count: int


@dataclass(frozen=True)
class RunConfig:
    """High-level inputs for a Python LCModel run."""

    title: str = ""
    ntitle: int = 2
    output_filename: str | None = None
    traceability_log_file: str | None = None
    raw_data_file: str | None = None
    basis_file: str | None = None
    ppm_axis_file: str | None = None
    basis_names_file: str | None = None
    priors_file: str | None = None
    table_output_file: str | None = None
    raw_data_list_file: str | None = None
    batch_csv_file: str | None = None
    time_domain_input: bool = False
    fft_backend: str = "auto"
    auto_phase_zero_order: bool = False
    auto_phase_first_order: bool = False
    phase_objective: str = "imag_abs"
    phase_smoothness_power: int = 6
    dwell_time_s: float = 0.0
    line_broadening_hz: float = 0.0
    fit_ppm_start: float | None = None
    fit_ppm_end: float | None = None
    exclude_ppm_ranges: tuple[tuple[float, float], ...] = ()
    sptype: str = ""
    apply_sptype_presets: bool = True
    average_mode: int = 0
    average_nback_start: int = 64
    average_nback_end: int = 1
    average_zero_voxel_check: bool = False
    include_metabolites: tuple[str, ...] = ()
    combine_expressions: tuple[str, ...] = ()
    shift_search_points: int = 0
    alignment_circular: bool = True
    fractional_shift_refine: bool = False
    fractional_shift_iterations: int = 18
    linewidth_scan_points: int = 0
    linewidth_scan_max_sigma_points: float = 0.0
    nonlinear_refine: bool = False
    nonlinear_max_iters: int = 4
    nonlinear_tolerance: float = 1e-6
    baseline_order: int = -1
    baseline_knots: int = 0
    baseline_smoothness: float = 0.0
    integration_half_width_points: int = 8
    integration_border_points: int = 4


@dataclass(frozen=True)
class FitResult:
    """Linear nonnegative fit output for the current semantic stage."""

    coefficients: tuple[float, ...]
    residual_norm: float
    iterations: int
    method: str
    coefficient_sds: tuple[float, ...] = ()
    metabolite_names: tuple[str, ...] = ()
    data_points_used: int = 0
    combined: tuple[tuple[str, float, float], ...] = ()
    relative_residual: float = 0.0
    snr_estimate: float = 0.0
    alignment_shift_points: int = 0
    alignment_shift_fractional_points: float = 0.0
    linewidth_sigma_points: float = 0.0
    nonlinear_iterations: int = 0
    integrated_data_area: float = 0.0
    integrated_fit_area: float = 0.0


@dataclass(frozen=True)
class RunResult:
    """Portable run metadata from the current semantic port scope."""

    title_layout: TitleLayout
    output_filename_parts: tuple[str, str] | None
    fit_result: FitResult | None = None
    table_output_file: str | None = None
    postscript_output_file: str | None = None


@dataclass(frozen=True)
class BatchRunResult:
    """Batch-run summary for multiple raw data files."""

    rows: tuple[tuple[str, tuple[float, ...], float], ...]
    csv_file: str | None = None
