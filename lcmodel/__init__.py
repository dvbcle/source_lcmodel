"""Python-first LCModel port package.

This package contains idiomatic Python modules for incremental semantic
porting from the legacy Fortran LCModel codebase.
"""

from lcmodel.engine import LCModelRunner
from lcmodel.core.fftpack_compat import (
    FFTPlan,
    cfftb,
    cfftf,
    cfft_r,
    cfftin_r,
    csft_r,
    csftin_r,
    fftci,
    seqtot,
)
from lcmodel.models import BatchRunResult, FitResult, RunConfig, RunResult, TitleLayout
from lcmodel.pipeline.alignment import (
    AlignmentResult,
    FractionalAlignmentResult,
    align_vector_by_fractional_shift,
    align_vector_by_integer_shift,
)
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.integration import IntegrationResult, integrate_peak_with_local_baseline
from lcmodel.pipeline.lineshape import apply_global_gaussian_lineshape
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
from lcmodel.pipeline.mydata import MyDataConfig, MyDataResult, run_mydata_stage
from lcmodel.pipeline.nonlinear import NonlinearConfig, NonlinearResult, run_nonlinear_refinement
from lcmodel.pipeline.phasing import (
    apply_phase,
    apply_zero_order_phase,
    estimate_zero_first_order_phase,
    estimate_zero_order_phase,
)
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import SpectralFitInputs, prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.sptype_presets import (
    SptypePreset,
    apply_sptype_preset,
    validate_sptype_config,
)
from lcmodel.pipeline.setup import SetupResult, prepare_fit_inputs

__all__ = [
    "LCModelRunner",
    "FFTPlan",
    "AlignmentResult",
    "FractionalAlignmentResult",
    "FitConfig",
    "BatchRunResult",
    "FitResult",
    "FitStageResult",
    "IntegrationResult",
    "NonlinearConfig",
    "NonlinearResult",
    "RunConfig",
    "RunResult",
    "TitleLayout",
    "MyDataConfig",
    "MyDataResult",
    "SpectralFitInputs",
    "SetupResult",
    "SptypePreset",
    "align_vector_by_integer_shift",
    "align_vector_by_fractional_shift",
    "augment_system_with_soft_priors",
    "apply_phase",
    "apply_zero_order_phase",
    "compute_fit_quality_metrics",
    "compute_combinations",
    "integrate_peak_with_local_baseline",
    "apply_global_gaussian_lineshape",
    "run_nonlinear_refinement",
    "cfftb",
    "cfftf",
    "cfft_r",
    "cfftin_r",
    "csft_r",
    "csftin_r",
    "fftci",
    "seqtot",
    "estimate_zero_first_order_phase",
    "estimate_zero_order_phase",
    "prepare_frequency_fit_from_time_domain",
    "prepare_fit_inputs",
    "run_fit_stage",
    "run_mydata_stage",
    "apply_sptype_preset",
    "validate_sptype_config",
]
