"""Python-first LCModel port package.

This package contains idiomatic Python modules for incremental semantic
porting from the legacy Fortran LCModel codebase.
"""

from lcmodel.engine import LCModelRunner
from lcmodel.models import FitResult, RunConfig, RunResult, TitleLayout
from lcmodel.pipeline.fitting import FitConfig, FitStageResult, run_fit_stage
from lcmodel.pipeline.mydata import MyDataConfig, MyDataResult, run_mydata_stage
from lcmodel.pipeline.phasing import apply_zero_order_phase, estimate_zero_order_phase

__all__ = [
    "LCModelRunner",
    "FitConfig",
    "FitResult",
    "FitStageResult",
    "RunConfig",
    "RunResult",
    "TitleLayout",
    "MyDataConfig",
    "MyDataResult",
    "apply_zero_order_phase",
    "estimate_zero_order_phase",
    "run_fit_stage",
    "run_mydata_stage",
]
