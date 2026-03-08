"""Simplified nonlinear refinement loop for shift/lineshape parameters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from lcmodel.pipeline.alignment import align_vector_by_fractional_shift, align_vector_by_integer_shift
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.lineshape import apply_global_gaussian_lineshape


@dataclass(frozen=True)
class NonlinearConfig:
    shift_search_points: int = 0
    alignment_circular: bool = True
    fractional_shift_refine: bool = False
    fractional_shift_iterations: int = 18
    linewidth_scan_points: int = 0
    linewidth_scan_max_sigma_points: float = 0.0
    max_iters: int = 1
    tolerance: float = 1e-6


@dataclass(frozen=True)
class NonlinearResult:
    fit_matrix: tuple[tuple[float, ...], ...]
    fit_vector: tuple[float, ...]
    stage: FitStageResult
    alignment_shift_points: int
    alignment_shift_fractional_points: float
    linewidth_sigma_points: float
    iterations: int


def _fit_for_sigma(
    base_matrix: Sequence[Sequence[float]],
    base_vector: Sequence[float],
    sigma_points: float,
    fit_config: FitConfig,
    cfg: NonlinearConfig,
) -> NonlinearResult:
    matrix = apply_global_gaussian_lineshape(
        base_matrix,
        sigma_points,
        circular=cfg.alignment_circular,
    )
    alignment = align_vector_by_integer_shift(
        matrix,
        base_vector,
        cfg.shift_search_points,
        circular=cfg.alignment_circular,
    )
    shift_fractional = float(alignment.shift_points)
    vector = alignment.vector
    if cfg.fractional_shift_refine and cfg.shift_search_points > 0:
        frac_alignment = align_vector_by_fractional_shift(
            matrix,
            base_vector,
            cfg.shift_search_points,
            circular=cfg.alignment_circular,
            iterations=cfg.fractional_shift_iterations,
        )
        shift_fractional = float(frac_alignment.shift_points)
        vector = frac_alignment.vector

    stage = run_fit_stage(matrix, vector, fit_config)
    return NonlinearResult(
        fit_matrix=matrix,
        fit_vector=tuple(float(v) for v in vector),
        stage=stage,
        alignment_shift_points=int(alignment.shift_points),
        alignment_shift_fractional_points=shift_fractional,
        linewidth_sigma_points=float(sigma_points),
        iterations=1,
    )


def run_nonlinear_refinement(
    base_matrix: Sequence[Sequence[float]],
    base_vector: Sequence[float],
    fit_config: FitConfig,
    config: NonlinearConfig,
) -> NonlinearResult:
    """Refine nonlinear parameters with a lightweight SOLVE-like outer loop."""

    max_iters = max(1, int(config.max_iters))
    tol = max(0.0, float(config.tolerance))
    max_sigma = max(0.0, float(config.linewidth_scan_max_sigma_points))
    scan_points = max(0, int(config.linewidth_scan_points))

    best = _fit_for_sigma(base_matrix, base_vector, 0.0, fit_config, config)
    current_sigma = 0.0
    iterations = 1

    for it in range(1, max_iters + 1):
        iterations = it
        candidates: list[float]
        if scan_points > 0 and max_sigma > 0.0:
            if it == 1:
                if scan_points == 1:
                    candidates = [max_sigma]
                else:
                    candidates = [max_sigma * (k / float(scan_points - 1)) for k in range(scan_points)]
            else:
                # Local refinement around the best sigma found so far.
                local_half = max_sigma / float(2**it)
                local_points = 5
                candidates = []
                for k in range(local_points):
                    frac = -1.0 + 2.0 * (k / float(local_points - 1))
                    sigma = current_sigma + frac * local_half
                    sigma = min(max_sigma, max(0.0, sigma))
                    candidates.append(sigma)
                candidates.append(current_sigma)
        else:
            candidates = [current_sigma]

        improved = False
        seen: set[float] = set()
        for sigma in candidates:
            key = round(float(sigma), 12)
            if key in seen:
                continue
            seen.add(key)
            candidate = _fit_for_sigma(base_matrix, base_vector, sigma, fit_config, config)
            if candidate.stage.residual_norm < best.stage.residual_norm - tol:
                best = candidate
                current_sigma = float(candidate.linewidth_sigma_points)
                improved = True

        if not improved and it > 1:
            break

    return NonlinearResult(
        fit_matrix=best.fit_matrix,
        fit_vector=best.fit_vector,
        stage=best.stage,
        alignment_shift_points=best.alignment_shift_points,
        alignment_shift_fractional_points=best.alignment_shift_fractional_points,
        linewidth_sigma_points=best.linewidth_sigma_points,
        iterations=iterations,
    )

