"""Fortran-aligned FILH2O/DOECC/DOWS helper routines.

This module ports the key water-reference data flow from LCModel:
- ECC_TRUNCATE core behavior (Klose correction using unsuppressed water phase)
- AREAWA/AREAW2 style water peak area estimation
- AREABA-style metabolite reference area estimation
- WATER_SCALE calibration factor computation
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence

from lcmodel.core.fftpack_compat import csft_r
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.phasing import apply_zero_order_phase, estimate_zero_order_phase


@dataclass(frozen=True)
class WaterReferenceConfig:
    """Control knobs for Fortran-style H2O reference processing."""

    iaverg: int = 0
    iareaw: int = 2
    nwsst: int = 10
    nwsend: int = 50
    atth2o: float = 0.7
    wconc: float = 35880.0
    ppmcen: float = 4.65
    ppmh2o: float = 4.65
    hwdwat: tuple[float, float] = (1.0, 2.0)
    ppmbas: tuple[float, float] = (0.1, 0.2)
    wsppm: float = 3.027
    rfwbas: float = 10.0
    fwhmba: float = 0.013
    n1hmet: int = 3
    attmet: float = 1.0


def _compute_ppminc(dwell_time_s: float, hzpppm: float, nunfil: int) -> float:
    if dwell_time_s <= 0.0 or hzpppm <= 0.0 or nunfil <= 0:
        return 0.0
    return 1.0 / (float(dwell_time_s) * float(2 * nunfil) * float(hzpppm))


def apply_klose_ecc(
    data_td: Sequence[complex],
    h2o_td: Sequence[complex],
) -> list[complex]:
    """Apply Klose eddy-current correction using unsuppressed water FID phase."""

    out = [complex(v) for v in data_td]
    n = min(len(out), len(h2o_td))
    for i in range(n):
        hv = complex(h2o_td[i])
        dv = complex(out[i])
        abssq = hv.real * hv.real + hv.imag * hv.imag
        if abssq > 0.0:
            out[i] = dv * complex(hv.real, -hv.imag) / math.sqrt(abssq)
    return out


def estimate_water_area(
    h2o_td: Sequence[complex],
    *,
    nunfil: int,
    dwell_time_s: float,
    hzpppm: float,
    config: WaterReferenceConfig,
) -> float:
    """Estimate unsuppressed-water peak area using AREAWA/AREAW2 semantics."""

    if int(config.iaverg) in {1, 4}:
        # Fortran WATER_SCALE special-case: normalized weighted average channels.
        return 1.0
    ppminc = _compute_ppminc(dwell_time_s, hzpppm, nunfil)
    if ppminc <= 0.0:
        return -1.0
    if int(config.iareaw) == 2:
        return _estimate_water_area_areaw2(h2o_td, nunfil=nunfil, ppminc=ppminc, config=config)
    return _estimate_water_area_loglinear(h2o_td, nunfil=nunfil, ppminc=ppminc, config=config)


def _estimate_water_area_loglinear(
    h2o_td: Sequence[complex],
    *,
    nunfil: int,
    ppminc: float,
    config: WaterReferenceConfig,
) -> float:
    # Fortran AREAWA fallback: log-linear fit to |H2OT(t)|.
    if nunfil <= 0 or len(h2o_td) < nunfil:
        return -1.0
    nwsst = int(config.nwsst)
    nwsend = int(config.nwsend)
    npts = nwsend - nwsst + 1
    if nwsst < 1 or nwsend > nunfil or npts < 10:
        return -1.0

    sx = 0.0
    sy = 0.0
    sxy = 0.0
    sxx = 0.0
    for j in range(nwsst, nwsend + 1):
        xterm = float(j)
        yterm = abs(complex(h2o_td[j - 1]))
        if yterm <= 0.0:
            return -1.0
        ylog = math.log(yterm)
        sx += xterm
        sy += ylog
        sxy += xterm * ylog
        sxx += xterm * xterm

    term1 = float(npts) * sxx
    denom = term1 - sx * sx
    if abs(denom) <= 1.0e-10 * max(1.0, abs(term1)):
        return -1.0
    rnum = sxx * sy - sx * sxy
    expmax = math.log(1.0e30)
    if abs(rnum) >= expmax * abs(denom):
        return -1.0
    return 0.5 * float(ppminc) * math.exp(rnum / denom) * math.sqrt(float(2 * nunfil))


def _estimate_water_area_areaw2(
    h2o_td: Sequence[complex],
    *,
    nunfil: int,
    ppminc: float,
    config: WaterReferenceConfig,
) -> float:
    # Fortran AREAW2 approximation:
    # phase the water spectrum around PPMH2O, then integrate with local baseline.
    if nunfil <= 0:
        return -1.0
    n = min(int(nunfil), len(h2o_td))
    if n < 8:
        return -1.0

    ppminc2 = 2.0 * float(ppminc)
    half = n // 2
    spectrum = list(csft_r([complex(v) for v in h2o_td[:n]], ncap=n))

    inner = max(0.0, float(config.hwdwat[0]))
    outer = max(inner, float(config.hwdwat[1]))
    ly = int(round((float(config.ppmcen) - float(config.ppmh2o)) / ppminc2)) + half + 1
    kystrt = int(round((float(config.ppmcen) - float(config.ppmh2o) - inner) / ppminc2)) + half + 1
    kyend = int(round((float(config.ppmcen) - float(config.ppmh2o) + inner) / ppminc2)) + half + 1
    ly = max(1, min(n, ly))
    kystrt = max(2, min(n - 1, kystrt))
    kyend = max(kystrt + 1, min(n - 2, kyend))

    search = spectrum[kystrt - 1 : kyend]
    if not search:
        return -1.0
    phase0 = estimate_zero_order_phase(search, search_steps=360)
    phased = list(apply_zero_order_phase(spectrum, phase0))

    kystrt = int(round((float(config.ppmcen) - float(config.ppmh2o) - outer) / ppminc2)) + half + 1
    kyend = int(round((float(config.ppmcen) - float(config.ppmh2o) + outer) / ppminc2)) + half + 1
    kystrt = max(2, min(n - 1, kystrt))
    kyend = max(kystrt + 1, min(n - 2, kyend))

    border = max(1, int(round(float(config.ppmbas[1]) / max(float(ppminc), 1.0e-12))))
    try:
        result = integrate_peak_with_local_baseline(
            [float(v.real) for v in phased],
            peak_index=ly - 1,
            start_index=kystrt - 1,
            end_index=kyend - 1,
            border_width=border,
            spacing=ppminc2,
        )
    except ValueError:
        return -1.0
    return float(result.area)


def estimate_metabolite_norm_area(
    basis_frequency: Sequence[complex | float],
    *,
    ppminc: float,
    config: WaterReferenceConfig,
) -> float:
    """Estimate metabolite normalization area (AREABA style)."""

    ndata = int(len(basis_frequency))
    if ndata <= 0 or ppminc <= 0.0:
        return 0.0
    if int(config.n1hmet) <= 0 or float(config.attmet) <= 0.0:
        return 0.0

    wsppm = float(config.wsppm)
    rfwbas = float(config.rfwbas)
    fwhmba = float(config.fwhmba)
    ppmbas1 = float(config.ppmbas[0])
    ppmcen = float(config.ppmcen)

    ly = int(round((ppmcen - wsppm) / ppminc)) + 1
    nwndo = max(1, int(round(ppmbas1 / ppminc)))
    nyhalf = max(1, int(round((0.5 * rfwbas * fwhmba) / ppminc)))
    kystrt = ly - nyhalf
    kyend = ly + nyhalf
    if kystrt - nwndo < 1 or kyend + nwndo > ndata:
        return 0.0

    def cyc(j: int) -> int:
        return (j - 1 + ndata) % ndata

    left = [float(complex(basis_frequency[cyc(j)]).real) for j in range(kystrt - nwndo, kystrt)]
    right = [
        float(complex(basis_frequency[cyc(j)]).real)
        for j in range(kyend + 1, kyend + nwndo + 1)
    ]
    if not left or not right:
        return 0.0
    avg = 0.5 * ((sum(left) / len(left)) + (sum(right) / len(right)))
    area = 0.0
    for j in range(kystrt, kyend + 1):
        area += float(complex(basis_frequency[cyc(j)]).real)
    area -= float(kyend - kystrt + 1) * avg
    return float(ppminc) * area / (float(config.n1hmet) * float(config.attmet))


def compute_water_scale_factor(
    *,
    h2o_td: Sequence[complex],
    basis_reference_frequency: Sequence[complex | float],
    nunfil: int,
    dwell_time_s: float,
    hzpppm: float,
    config: WaterReferenceConfig,
) -> float | None:
    """Compute Fortran WATER_SCALE calibration multiplier FCALIB."""

    ppminc = _compute_ppminc(dwell_time_s, hzpppm, nunfil)
    if ppminc <= 0.0:
        return None
    area_met_norm = estimate_metabolite_norm_area(
        basis_reference_frequency,
        ppminc=ppminc,
        config=config,
    )
    if area_met_norm <= 0.0:
        return None

    area_water = estimate_water_area(
        h2o_td,
        nunfil=nunfil,
        dwell_time_s=dwell_time_s,
        hzpppm=hzpppm,
        config=config,
    )
    if area_water <= 0.0:
        return None
    if float(config.atth2o) <= 0.0 or float(config.wconc) <= 0.0:
        return None

    water_norm = area_water / (2.0 * float(config.atth2o) * float(config.wconc))
    if water_norm <= 0.0:
        return None
    return float(area_met_norm / water_norm)

