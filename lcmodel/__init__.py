"""Python-first LCModel port package.

This package contains idiomatic Python modules for incremental semantic
porting from the legacy Fortran LCModel codebase.
"""

from lcmodel.engine import LCModelRunner
from lcmodel.models import BatchRunResult, FitResult, RunConfig, RunResult, TitleLayout
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.metrics import compute_fit_quality_metrics
from lcmodel.pipeline.mydata import MyDataConfig, MyDataResult, run_mydata_stage
from lcmodel.pipeline.phasing import apply_zero_order_phase, estimate_zero_order_phase
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.priors import augment_system_with_soft_priors
from lcmodel.pipeline.spectral import SpectralFitInputs, prepare_frequency_fit_from_time_domain
from lcmodel.pipeline.setup import SetupResult, prepare_fit_inputs

__all__ = [
    "LCModelRunner",
    "FitConfig",
    "BatchRunResult",
    "FitResult",
    "FitStageResult",
    "RunConfig",
    "RunResult",
    "TitleLayout",
    "MyDataConfig",
    "MyDataResult",
    "SpectralFitInputs",
    "SetupResult",
    "augment_system_with_soft_priors",
    "apply_zero_order_phase",
    "compute_fit_quality_metrics",
    "compute_combinations",
    "estimate_zero_order_phase",
    "prepare_frequency_fit_from_time_domain",
    "prepare_fit_inputs",
    "run_fit_stage",
    "run_mydata_stage",
]
