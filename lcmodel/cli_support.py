"""Shared helpers for CLI config mapping and output rendering."""

from __future__ import annotations

import argparse
from dataclasses import replace

from lcmodel.models import BatchRunResult, RunConfig, RunResult


_DIRECT_FIELDS: tuple[tuple[str, str], ...] = (
    ("title", "title"),
    ("ntitle", "ntitle"),
    ("output_filename", "output_filename"),
    ("coord_output_file", "coordinate_output_file"),
    ("corrected_raw_output_file", "corrected_raw_output_file"),
    ("table_output_file", "table_output_file"),
    ("traceability_log_file", "traceability_log_file"),
    ("fft_backend", "fft_backend"),
    ("phase_objective", "phase_objective"),
    ("phase_smoothness_power", "phase_smoothness_power"),
    ("dwell_time", "dwell_time_s"),
    ("line_broadening_hz", "line_broadening_hz"),
    ("average_mode", "average_mode"),
    ("average_nback_start", "average_nback_start"),
    ("average_nback_end", "average_nback_end"),
    ("raw_data_file", "raw_data_file"),
    ("raw_data_list_file", "raw_data_list_file"),
    ("batch_csv_file", "batch_csv_file"),
    ("basis_file", "basis_file"),
    ("ppm_axis_file", "ppm_axis_file"),
    ("basis_names_file", "basis_names_file"),
    ("priors_file", "priors_file"),
    ("ppm_start", "fit_ppm_start"),
    ("ppm_end", "fit_ppm_end"),
    ("sptype", "sptype"),
    ("shift_search_points", "shift_search_points"),
    ("fractional_shift_iterations", "fractional_shift_iterations"),
    ("linewidth_scan_points", "linewidth_scan_points"),
    ("linewidth_scan_max_sigma_points", "linewidth_scan_max_sigma_points"),
    ("nonlinear_max_iters", "nonlinear_max_iters"),
    ("nonlinear_tolerance", "nonlinear_tolerance"),
    ("baseline_order", "baseline_order"),
    ("baseline_knots", "baseline_knots"),
    ("baseline_smoothness", "baseline_smoothness"),
    ("integration_half_width_points", "integration_half_width_points"),
    ("integration_border_points", "integration_border_points"),
)

_BOOL_FLAGS: tuple[tuple[str, str], ...] = (
    ("time_domain_input", "time_domain_input"),
    ("auto_phase_zero_order", "auto_phase_zero_order"),
    ("auto_phase_first_order", "auto_phase_first_order"),
    ("average_zero_voxel_check", "average_zero_voxel_check"),
    ("fractional_shift_refine", "fractional_shift_refine"),
    ("nonlinear_refine", "nonlinear_refine"),
)


def _parse_ranges(spec: str) -> tuple[tuple[float, float], ...]:
    ranges: list[tuple[float, float]] = []
    for raw_range in spec.split(","):
        part = raw_range.strip()
        if not part:
            continue
        if ":" not in part:
            raise SystemExit(f"Invalid exclude range '{part}', expected a:b")
        a_text, b_text = part.split(":", 1)
        ranges.append((float(a_text), float(b_text)))
    return tuple(ranges)


def _parse_csv_values(spec: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in spec.split(",") if part.strip())


def apply_cli_args(config: RunConfig, args: argparse.Namespace) -> RunConfig:
    out = config

    for arg_name, field_name in _DIRECT_FIELDS:
        value = getattr(args, arg_name, None)
        if value is not None:
            out = replace(out, **{field_name: value})

    for arg_name, field_name in _BOOL_FLAGS:
        if bool(getattr(args, arg_name, False)):
            out = replace(out, **{field_name: True})

    if args.exclude_ppm_ranges is not None:
        out = replace(out, exclude_ppm_ranges=_parse_ranges(args.exclude_ppm_ranges))
    if args.include_metabolites is not None:
        out = replace(out, include_metabolites=_parse_csv_values(args.include_metabolites))
    if args.combine_expressions is not None:
        out = replace(out, combine_expressions=_parse_csv_values(args.combine_expressions))
    if args.no_sptype_presets:
        out = replace(out, apply_sptype_presets=False)
    if args.alignment_mode is not None:
        out = replace(out, alignment_circular=(args.alignment_mode == "circular"))

    return out


def print_batch_result(batch: BatchRunResult) -> None:
    print(f"batch_rows={len(batch.rows)}")
    for raw_file, coeffs, residual in batch.rows:
        coeff_text = ",".join(f"{v:.12g}" for v in coeffs)
        print(f"batch_row={raw_file}|{residual:.12g}|{coeff_text}")
    if batch.csv_file:
        print(f"batch_csv_file={batch.csv_file}")


def print_run_result(result: RunResult) -> None:
    print(f"title_lines={result.title_layout.line_count}")
    print(f"title_line_1={result.title_layout.lines[0]}")
    print(f"title_line_2={result.title_layout.lines[1]}")
    if result.output_filename_parts is None:
        print("output_split=<not requested>")
    else:
        left, right = result.output_filename_parts
        print(f"output_split_left={left}")
        print(f"output_split_right={right}")
    if result.fit_result is None:
        print("fit_result=<not requested>")
    else:
        print(f"fit_method={result.fit_result.method}")
        print(f"fit_iterations={result.fit_result.iterations}")
        print(f"fit_residual_norm={result.fit_result.residual_norm:.12g}")
        coeffs = ",".join(f"{v:.12g}" for v in result.fit_result.coefficients)
        print(f"fit_coefficients={coeffs}")
        if result.fit_result.coefficient_sds:
            sds = ",".join(f"{v:.12g}" for v in result.fit_result.coefficient_sds)
            print(f"fit_coeff_sds={sds}")
        if result.fit_result.metabolite_names:
            print(f"fit_metabolites={','.join(result.fit_result.metabolite_names)}")
        if result.fit_result.data_points_used > 0:
            print(f"fit_points_used={result.fit_result.data_points_used}")
        print(f"fit_relative_residual={result.fit_result.relative_residual:.12g}")
        print(f"fit_snr_estimate={result.fit_result.snr_estimate:.12g}")
        print(f"fit_alignment_shift_points={result.fit_result.alignment_shift_points}")
        print(
            "fit_alignment_shift_fractional_points="
            f"{result.fit_result.alignment_shift_fractional_points:.12g}"
        )
        print(f"fit_linewidth_sigma_points={result.fit_result.linewidth_sigma_points:.12g}")
        print(f"fit_nonlinear_iterations={result.fit_result.nonlinear_iterations}")
        print(f"fit_integrated_data_area={result.fit_result.integrated_data_area:.12g}")
        print(f"fit_integrated_fit_area={result.fit_result.integrated_fit_area:.12g}")
        if result.fit_result.combined:
            combo = ",".join(
                f"{name}:{value:.12g}:{sd:.12g}"
                for name, value, sd in result.fit_result.combined
            )
            print(f"fit_combinations={combo}")
    if result.table_output_file:
        print(f"table_output_file={result.table_output_file}")
    if result.postscript_output_file:
        print(f"postscript_output_file={result.postscript_output_file}")
