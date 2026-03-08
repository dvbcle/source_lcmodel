"""Pipeline stages for semantic LCModel porting."""

from lcmodel.pipeline.alignment import (
    AlignmentResult,
    FractionalAlignmentResult,
    align_vector_by_fractional_shift,
    align_vector_by_integer_shift,
)
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.integration import IntegrationResult, integrate_peak_with_local_baseline
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
from lcmodel.pipeline.mydata import MyDataConfig, MyDataResult, run_mydata_stage
from lcmodel.pipeline.phasing import (
    apply_phase,
    apply_zero_order_phase,
    estimate_zero_first_order_phase,
    estimate_zero_order_phase,
)
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import SpectralFitInputs, prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.setup import SetupResult, prepare_fit_inputs

__all__ = [
    "AlignmentResult",
    "FractionalAlignmentResult",
    "FitConfig",
    "FitStageResult",
    "IntegrationResult",
    "SpectralFitInputs",
    "SetupResult",
    "align_vector_by_integer_shift",
    "align_vector_by_fractional_shift",
    "augment_system_with_soft_priors",
    "apply_phase",
    "apply_zero_order_phase",
    "compute_fit_quality_metrics",
    "compute_combinations",
    "integrate_peak_with_local_baseline",
    "estimate_zero_first_order_phase",
    "estimate_zero_order_phase",
    "prepare_frequency_fit_from_time_domain",
    "prepare_fit_inputs",
    "run_fit_stage",
    "MyDataConfig",
    "MyDataResult",
    "run_mydata_stage",
]
