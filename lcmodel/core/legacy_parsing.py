"""Legacy string and prior parsing helpers from LCModel Fortran."""

from __future__ import annotations

import math
from typing import Sequence


def get_field_from_string(
    chseparator: str,
    ifield_type: int,
    iatend: int,
    istart: int,
    string_in: str,
) -> tuple[int, str | float]:
    """Extract one field from a record using LCModel GET_FIELD conventions."""

    text = string_in
    len_string_in = len(text)
    if len_string_in < istart:
        raise ValueError("len_string_in < istart")
    sep = chseparator
    if iatend == 0:
        pos = text.find(sep, istart - 1)
        if pos < 0:
            return -1, ""
        iend_field = pos
    elif iatend == 1:
        pos = text.find(sep, istart - 1)
        iend_field = (pos if pos >= 0 else len_string_in)
    elif iatend == 2:
        iend_field = len_string_in
    else:
        raise ValueError("invalid iatend")

    raw = text[istart - 1 : iend_field].strip()
    next_start = iend_field + len(sep) + 1
    if not raw:
        return -2, ""

    if ifield_type == 1:
        return next_start, raw
    if ifield_type == 2:
        try:
            return next_start, float(raw)
        except ValueError:
            return -5, 0.0
    return -4, ""


def parse_prior_strings(chrato: Sequence[str]) -> list[dict[str, object]]:
    """Parse CHRATO records into ratio/weight components."""

    parsed: list[dict[str, object]] = []
    for record in chrato:
        istart, chrati = get_field_from_string("=", 1, 0, 1, record)
        if istart <= 0:
            raise ValueError(f"Invalid CHRATO record: {record!r}")
        istart, exrati = get_field_from_string("+-", 2, 0, istart, record)
        if istart <= 0:
            raise ValueError(f"Invalid CHRATO exrati in: {record!r}")
        istart, sdrati = get_field_from_string("+WT=", 2, 1, istart, record)
        if istart <= 0:
            raise ValueError(f"Invalid CHRATO sdrati in: {record!r}")
        chratw = ""
        if istart <= len(record):
            istart, chratw_val = get_field_from_string(" ", 1, 2, istart, record)
            if istart <= 0:
                raise ValueError(f"Invalid CHRATO weight tail in: {record!r}")
            chratw = str(chratw_val)
        parsed.append(
            {
                "chrati": str(chrati),
                "chratw": chratw,
                "exrati": float(exrati),
                "sdrati": float(sdrati),
            }
        )
    return parsed


def parse_sum_terms(
    substring: str,
    nacomb: Sequence[str],
    solbes: Sequence[float],
    exrati_arg: float = 0.0,
) -> tuple[list[float], float, bool]:
    """Parse CHRATI/CHRATW sum expression into prior-row coefficients."""

    terms = [t.strip() for t in substring.split("+") if t.strip()]
    row = [0.0] * len(nacomb)
    csum = 0.0
    denom_absent = True

    for term in terms:
        wildcard = term.endswith("*")
        base = term[:-1] if wildcard else term
        for j, name in enumerate(nacomb):
            factor = 0.0
            if wildcard:
                if base == "" or name.startswith(base):
                    factor = 1.0
            else:
                if term == name:
                    factor = 1.0
                elif term == "totCho" and name in {"Cho", "GPC", "PCh"}:
                    factor = 1.0
                elif term == "totCr" and name in {"Cr", "Cre", "PCr"}:
                    factor = 1.0
                elif term == "totNAA" and name in {"NAA", "NAAG"}:
                    factor = 1.0
                elif term == "Big3":
                    if name in {"Cr", "Cre", "PCr", "NAA", "NAAG"}:
                        factor = 1.0
                    elif name in {"Cho", "GPC", "PCh"}:
                        factor = 3.0
            if factor > 0.0:
                denom_absent = False
                csum += factor * float(solbes[j])
                if float(exrati_arg) > 0.0:
                    row[j] -= factor * float(exrati_arg)
    return row, csum, denom_absent


def build_conc_prior(
    parsed_prior: Sequence[dict[str, object]],
    nacomb: Sequence[str],
    solbes: Sequence[float],
    *,
    norato: Sequence[str] = (),
    fcsum: float = 1.0e-2,
) -> tuple[list[list[float]], list[dict[str, object]]]:
    """Build concentration-prior rows from parsed CHRATO fields."""

    rows: list[list[float]] = []
    used: list[dict[str, object]] = []
    for item in parsed_prior:
        chrati = str(item["chrati"])
        exrati = float(item["exrati"])
        sdrati = float(item["sdrati"])
        if sdrati <= 0.0:
            continue
        slash = chrati.find("/")
        if slash <= 0:
            continue
        numerator = chrati[:slash].strip()
        if numerator in norato:
            continue
        try:
            jnum = list(nacomb).index(numerator)
        except ValueError:
            continue
        row = [0.0] * len(nacomb)
        row[jnum] = 1.0

        den_row, csum, denom_absent = parse_sum_terms(chrati[slash + 1 :], nacomb, solbes, exrati)
        row = [row[j] + den_row[j] for j in range(len(row))]
        extra = str(item.get("chratw", ""))
        if extra:
            _, csum_extra, denom_absent_extra = parse_sum_terms(extra, nacomb, solbes, 0.0)
            csum += csum_extra
            denom_absent = denom_absent and denom_absent_extra
        if denom_absent:
            continue
        if csum <= 0.0:
            csum = max(1.0e-30, float(fcsum) * sum(float(v) for v in solbes))
            if csum <= 0.0:
                continue
        sqrtwt = 1.0 / (csum * sdrati)
        row = [v * sqrtwt for v in row]
        rows.append(row)
        used.append({**item, "sqrtwt": sqrtwt, "numerator": numerator})
    return rows, used


def parse_chsimu_strings(chsimu: Sequence[str]) -> list[dict[str, object]]:
    """Parse CHSIMU records into dictionaries."""

    parsed: list[dict[str, object]] = []
    for record in chsimu:
        istart, chsim = get_field_from_string("@", 1, 0, 1, record)
        if istart <= 0:
            raise ValueError(f"Invalid CHSIMU: {record!r}")
        istart, sippm = get_field_from_string("+-", 2, 0, istart, record)
        istart, sisdsh = get_field_from_string("FWHM=", 2, 0, istart, record)
        istart, sifwmn = get_field_from_string("<", 2, 0, istart, record)
        istart, sifwex = get_field_from_string("+-", 2, 0, istart, record)
        istart, sifwsd = get_field_from_string("AMP=", 2, 0, istart, record)
        istart, siamp = get_field_from_string("@", 2, 1, istart, record)
        if min(istart, 1) <= 0:
            raise ValueError(f"Invalid CHSIMU fields: {record!r}")
        parsed.append(
            {
                "chsim": str(chsim),
                "ngau": 1,
                "sippm": [float(sippm)],
                "sisdsh": float(sisdsh),
                "sifwmn": [float(sifwmn)],
                "sifwex": float(sifwex),
                "sifwsd": float(sifwsd),
                "siamp": [float(siamp)],
            }
        )
    return parsed


def chreal(x: float, xstep: float, ljust: bool) -> str:
    """Format numeric axis labels with CHREAL-style compactness."""

    ax = abs(float(x))
    astep = abs(float(xstep))
    if (ax < 1.0e-7 and astep > 1.0e-5) or ax <= 0.0:
        return "0.0" if bool(ljust) else "  0.0"
    if ax < 1.0e-4 or ax >= 999999.0:
        return f"{float(x):.1E}".replace("E+0", "E+").replace("E-0", "E-")

    if ax < 0.001:
        rfmt = 8.5
    elif ax < 0.01:
        rfmt = 7.4
    elif ax < 0.1:
        rfmt = 6.3
    elif ax < 1.0:
        rfmt = 5.2
    elif ax < 9.95:
        rfmt = 4.1
    else:
        rfmt = float(int(math.log10(float(round(ax)))) + 3) + 0.001

    for _ in range(4):
        fact = 10.0 ** round(10.0 * (rfmt % 1.0))
        if int(fact * (ax + 0.9999 * astep)) != int(fact * ax) or rfmt >= 8.0:
            break
        rfmt += 1.1

    decimals = int(round(10.0 * (rfmt % 1.0)))
    width = int(rfmt)
    if decimals == 0:
        if bool(ljust):
            width -= 1
            if x >= 0:
                width -= 1
        return f"{int(round(x)):>{max(1, width)}d}"
    if rfmt < 8.0 and not bool(ljust):
        rfmt += 1.0
    if bool(ljust) and x >= 0:
        rfmt -= 1.0
    width = int(rfmt)
    return f"{float(x):{max(1, width)}.{decimals}f}"
