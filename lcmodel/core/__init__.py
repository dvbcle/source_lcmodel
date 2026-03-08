"""Core algorithms for LCModel Python port."""

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
from lcmodel.core.legacy_math import (
    betain,
    dgamln,
    diff,
    fishni,
    icycle,
    icycle_r,
    inflec,
    nextre,
    pythag,
)
from lcmodel.core.legacy_linear import g1, g2, h12
from lcmodel.core.legacy_eigen import jacobi_symmetric, tridiagonal_from_symmetric
from lcmodel.core.legacy_parsing import (
    build_conc_prior,
    chreal,
    get_field_from_string,
    parse_chsimu_strings,
    parse_prior_strings,
    parse_sum_terms,
)

__all__ = [
    "FFTPlan",
    "cfftb",
    "cfftf",
    "cfft_r",
    "cfftin_r",
    "csft_r",
    "csftin_r",
    "fftci",
    "seqtot",
    "betain",
    "dgamln",
    "diff",
    "fishni",
    "icycle",
    "icycle_r",
    "inflec",
    "nextre",
    "pythag",
    "g1",
    "g2",
    "h12",
    "jacobi_symmetric",
    "tridiagonal_from_symmetric",
    "build_conc_prior",
    "chreal",
    "get_field_from_string",
    "parse_chsimu_strings",
    "parse_prior_strings",
    "parse_sum_terms",
]
