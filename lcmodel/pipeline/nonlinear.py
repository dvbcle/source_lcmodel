"""Simplified nonlinear refinement loop for shift/lineshape parameters."""

from __future__ import annotations

from dataclasses import dataclass
import cmath
import math
from typing import Sequence

from lcmodel.pipeline.alignment import align_vector_by_fractional_shift, align_vector_by_integer_shift
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.lineshape import apply_global_gaussian_lineshape
from lcmodel.traceability import fortran_provenance


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
    enable_phase_refinement: bool = False
    phase0_search_range_deg: float = 25.0
    phase0_search_steps: int = 7
    phase1_search_range_deg_per_ppm: float = 6.0
    phase1_search_steps: int = 5


@dataclass(frozen=True)
class NonlinearResult:
    fit_matrix: tuple[tuple[float, ...], ...]
    fit_vector: tuple[float, ...]
    stage: FitStageResult
    alignment_shift_points: int
    alignment_shift_fractional_points: float
    linewidth_sigma_points: float
    phase0_deg: float
    phase1_deg_per_ppm: float
    iterations: int


def _fit_for_sigma(
    base_matrix: Sequence[Sequence[float]],
    base_vector: Sequence[float],
    sigma_points: float,
    fit_config: FitConfig,
    cfg: NonlinearConfig,
    *,
    base_complex_vector: Sequence[complex] | None = None,
    ppm_axis: Sequence[float] | None = None,
    phase0_deg: float = 0.0,
    phase1_deg_per_ppm: float = 0.0,
) -> NonlinearResult:
    # Fortran TWORG*/SOLVE intent:
    # evaluate one nonlinear candidate (linewidth + alignment) then solve linear
    # amplitudes on the transformed system.
    matrix = apply_global_gaussian_lineshape(
        base_matrix,
        sigma_points,
        circular=cfg.alignment_circular,
    )
    vector_for_fit: tuple[float, ...]
    if base_complex_vector is not None and ppm_axis is not None and len(base_complex_vector) == len(base_vector):
        phased = _apply_phase_profile(base_complex_vector, ppm_axis, phase0_deg, phase1_deg_per_ppm)
        vector_for_fit = tuple(float(v.real) for v in phased)
    else:
        vector_for_fit = tuple(float(v) for v in base_vector)
    align_fit_cfg = FitConfig(
        max_iter=160,
        tolerance=max(1.0e-5, float(cfg.tolerance)),
    )
    alignment = align_vector_by_integer_shift(
        matrix,
        vector_for_fit,
        cfg.shift_search_points,
        circular=cfg.alignment_circular,
        fit_config=align_fit_cfg,
    )
    shift_fractional = float(alignment.shift_points)
    vector = alignment.vector
    if cfg.fractional_shift_refine and cfg.shift_search_points > 0:
        # Refine integer shift with a local continuous search.
        frac_alignment = align_vector_by_fractional_shift(
            matrix,
            vector_for_fit,
            cfg.shift_search_points,
            circular=cfg.alignment_circular,
            iterations=cfg.fractional_shift_iterations,
            fit_config=align_fit_cfg,
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
        phase0_deg=float(phase0_deg),
        phase1_deg_per_ppm=float(phase1_deg_per_ppm),
        iterations=1,
    )


def _linspace(center: float, half_range: float, steps: int) -> tuple[float, ...]:
    n = max(1, int(steps))
    if n <= 1 or half_range <= 0.0:
        return (float(center),)
    out: list[float] = []
    lo = float(center) - float(half_range)
    hi = float(center) + float(half_range)
    for i in range(n):
        frac = i / float(n - 1)
        out.append(lo + frac * (hi - lo))
    return tuple(out)


def _apply_phase_profile(
    spectrum: Sequence[complex],
    ppm_axis: Sequence[float],
    phase0_deg: float,
    phase1_deg_per_ppm: float,
) -> tuple[complex, ...]:
    if len(spectrum) != len(ppm_axis):
        raise ValueError("spectrum and ppm_axis lengths must match")
    if not spectrum:
        return ()
    # Fortran REPHAS intent:
    # phase profile is linear in ppm offset; use center of active window.
    ppm_ref = 0.5 * (float(ppm_axis[0]) + float(ppm_axis[-1]))
    out: list[complex] = []
    for z, ppm in zip(spectrum, ppm_axis):
        phi = math.radians(float(phase0_deg) + float(phase1_deg_per_ppm) * (float(ppm) - ppm_ref))
        out.append(complex(z) * cmath.exp(1j * phi))
    return tuple(out)


def _select_phase_candidate(
    *,
    base_matrix: Sequence[Sequence[float]],
    base_vector: Sequence[float],
    base_complex_vector: Sequence[complex] | None,
    ppm_axis: Sequence[float] | None,
    fit_config: FitConfig,
    cfg: NonlinearConfig,
) -> tuple[float, float]:
    if (
        not cfg.enable_phase_refinement
        or base_complex_vector is None
        or ppm_axis is None
        or len(base_complex_vector) != len(base_vector)
        or len(ppm_axis) != len(base_vector)
    ):
        return 0.0, 0.0

    phase0_candidates = _linspace(0.0, abs(float(cfg.phase0_search_range_deg)), cfg.phase0_search_steps)
    phase1_candidates = _linspace(
        0.0,
        abs(float(cfg.phase1_search_range_deg_per_ppm)),
        cfg.phase1_search_steps,
    )
    best_obj = math.inf
    best_phase0 = 0.0
    best_phase1 = 0.0
    # Keep coarse phase search lightweight; final fit still runs with full
    # baseline configuration in the main nonlinear pass.
    quick_fit = FitConfig(max_iter=min(400, fit_config.max_iter), tolerance=fit_config.tolerance)
    p0_rng = max(1.0e-9, abs(float(cfg.phase0_search_range_deg)))
    p1_rng = max(1.0e-9, abs(float(cfg.phase1_search_range_deg_per_ppm)))
    for phase0 in phase0_candidates:
        for phase1 in phase1_candidates:
            phased = _apply_phase_profile(base_complex_vector, ppm_axis, phase0, phase1)
            vector = [float(v.real) for v in phased]
            stage = run_fit_stage(base_matrix, vector, quick_fit)
            penalty = (
                2.0e-4 * (float(phase0) / p0_rng) ** 2
                + 2.0e-4 * (float(phase1) / p1_rng) ** 2
            )
            objective = float(stage.residual_norm) + penalty
            if objective < best_obj:
                best_obj = objective
                best_phase0 = float(phase0)
                best_phase1 = float(phase1)
    return best_phase0, best_phase1


def _candidate_objective(
    candidate: NonlinearResult,
    *,
    cfg: NonlinearConfig,
) -> float:
    shift_rng = max(1.0, float(cfg.shift_search_points))
    sigma_rng = max(1.0e-9, float(cfg.linewidth_scan_max_sigma_points))
    p0_rng = max(1.0e-9, abs(float(cfg.phase0_search_range_deg)))
    p1_rng = max(1.0e-9, abs(float(cfg.phase1_search_range_deg_per_ppm)))
    penalty = (
        1.5e-4 * (float(candidate.alignment_shift_fractional_points) / shift_rng) ** 2
        + 1.0e-4 * (float(candidate.linewidth_sigma_points) / sigma_rng) ** 2
        + 2.0e-4 * (float(candidate.phase0_deg) / p0_rng) ** 2
        + 2.0e-4 * (float(candidate.phase1_deg_per_ppm) / p1_rng) ** 2
    )
    return float(candidate.stage.residual_norm) + penalty


@fortran_provenance(
    "startv",
    "shiftd",
    "phasta",
    "rephas",
    "tworeg",
    "tworg1",
    "tworeg_sav",
    "tworg2",
    "tworg3",
    "rfalsi",
    "fshssq",
)
def run_nonlinear_refinement(
    base_matrix: Sequence[Sequence[float]],
    base_vector: Sequence[float],
    fit_config: FitConfig,
    config: NonlinearConfig,
    *,
    base_complex_vector: Sequence[complex] | None = None,
    ppm_axis: Sequence[float] | None = None,
) -> NonlinearResult:
    """Refine nonlinear parameters with a lightweight SOLVE-like outer loop."""

    max_iters = max(1, int(config.max_iters))
    tol = max(0.0, float(config.tolerance))
    max_sigma = max(0.0, float(config.linewidth_scan_max_sigma_points))
    scan_points = max(0, int(config.linewidth_scan_points))
    # Use a lightweight objective solve while searching nonlinear parameters.
    # The final full baseline/regularized fit is executed later in the runner.
    objective_fit_config = FitConfig(
        max_iter=min(400, fit_config.max_iter),
        tolerance=fit_config.tolerance,
    )

    best_phase0, best_phase1 = _select_phase_candidate(
        base_matrix=base_matrix,
        base_vector=base_vector,
        base_complex_vector=base_complex_vector,
        ppm_axis=ppm_axis,
        fit_config=objective_fit_config,
        cfg=config,
    )

    best = _fit_for_sigma(
        base_matrix,
        base_vector,
        0.0,
        objective_fit_config,
        config,
        base_complex_vector=base_complex_vector,
        ppm_axis=ppm_axis,
        phase0_deg=best_phase0,
        phase1_deg_per_ppm=best_phase1,
    )
    best_obj = _candidate_objective(best, cfg=config)
    current_sigma = 0.0
    iterations = 1

    for it in range(1, max_iters + 1):
        iterations = it
        candidates: list[float]
        if scan_points > 0 and max_sigma > 0.0:
            if it == 1:
                # Fortran TWOREG/RFALSI spirit:
                # broad initial search over allowed regularization/shape range.
                if scan_points == 1:
                    candidates = [max_sigma]
                else:
                    candidates = [max_sigma * (k / float(scan_points - 1)) for k in range(scan_points)]
            else:
                # Local refinement around the current best candidate.
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
            candidate = _fit_for_sigma(
                base_matrix,
                base_vector,
                sigma,
                objective_fit_config,
                config,
                base_complex_vector=base_complex_vector,
                ppm_axis=ppm_axis,
                phase0_deg=best_phase0,
                phase1_deg_per_ppm=best_phase1,
            )
            candidate_obj = _candidate_objective(candidate, cfg=config)
            if candidate_obj < best_obj - tol:
                best = candidate
                best_obj = candidate_obj
                current_sigma = float(candidate.linewidth_sigma_points)
                improved = True

        # Fortran stopping behavior:
        # stop once a refinement pass fails to improve the objective.
        if not improved and it > 1:
            break

    return NonlinearResult(
        fit_matrix=best.fit_matrix,
        fit_vector=best.fit_vector,
        stage=best.stage,
        alignment_shift_points=best.alignment_shift_points,
        alignment_shift_fractional_points=best.alignment_shift_fractional_points,
        linewidth_sigma_points=best.linewidth_sigma_points,
        phase0_deg=float(best.phase0_deg),
        phase1_deg_per_ppm=float(best.phase1_deg_per_ppm),
        iterations=iterations,
    )
