"""PostScript report writer with Fortran-style LCModel page scaffolding.

This module keeps page-prolog literals close to the legacy output while
emitting curve payloads using the same packed-hex stream semantics as the
Fortran `PLOT`/`PLOT_gap` routines.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Sequence

from lcmodel.core.text import escape_postscript_text

if TYPE_CHECKING:
    from lcmodel.models import FitResult


_FORTRAN_PROLOG_LINES = (
    "/MPGdict 100 dict def MPGdict begin",
    "/bd{bind def}def",
    "/set{exch def}bd",
    "/cm{initmatrix 72 2.54 div dup scale 0 setgray .015 setlinewidth",
    "  1 selectplot /Helvetica 11 font}bd",
    "/font{/pitch exch 72 div 2.54 mul def findfont pitch scalefont setfont}bd",
    "/s{show}bd",
    "/lst{exec}bd",
    "/rst{stlen neg 0 rmoveto exec}bd",
    "/cst{stlen -2 div 0 rmoveto exec}bd",
    "/r{rotate}bd",
    "/m{moveto}bd",
    "/li{newpath moveto rlineto stroke}bd",
    "/boxpath{newpath moveto dup 3 1 roll 0 exch rlineto 0 rlineto 0 exch neg",
    " rlineto closepath} bd",
    "/box{boxpath stroke}def",
    "/go{save exch 1 add 1 roll translate}bd",
    "/axis{",
    "  8 go rotate",
    "  /wd set",
    "  /beg set",
    "  /inc set",
    "  /tick exch neg pitch mul def",
    "  /n set",
    "  newpath 0 0 moveto wd 0 lineto stroke",
    "  newpath beg n 1 sub inc mul add 0 moveto",
    "  n{0 tick 0.6 mul rlineto",
    "    0 tick 0 gt{0.25}{1}ifelse tick mul rmoveto",
    "    exch currentpoint pop inc sub exch",
    "    dup stringwidth pop -0.5 mul 0 rmoveto show",
    "    stroke 0 moveto}repeat",
    "  restore}bd",
    "/readflt{currentfile 2 string readhexstring pop dup 1 get exch 0 get",
    "  256 mul add 32768 sub 32767 div mul}bd",
    "/selectplot{/n set /plotproc",
    "  n 1 eq{{lineto}}if",
    "  def}bd",
    "/plot{",
    "  7 go /ypand set /xpand set /yoff set /xoff set /n set",
    "  /xy{xpand readflt xoff add ypand readflt yoff add}bd",
    "  xy moveto",
    "  n{xy lineto currentpoint stroke moveto}repeat",
    "  restore",
    "}bd",
    "/ticks{",
    "  7 go rotate",
    "  /wd set",
    "  /beg set",
    "  /inc set",
    "  /n set",
    "  newpath beg 0 moveto",
    "  n{0 wd rlineto currentpoint pop inc add 0",
    "  stroke moveto}repeat",
    " restore}bd",
    "/stlen{",
    "  dup currentpoint 3 -1 roll",
    "  /len 0 def",
    "  /dlen 0 store",
    "  /s{",
    "   stringwidth pop len add dlen add /len exch def",
    "   /dlen 0 store}bd",
    "  exec",
    "  moveto /s{show}bd len",
    "  }bd",
    "end",
)


def _normalize_bounds(values: Sequence[float], fallback_low: float, fallback_high: float) -> tuple[float, float]:
    if not values:
        return fallback_low, fallback_high
    low = min(float(v) for v in values)
    high = max(float(v) for v in values)
    if low == high:
        eps = 1.0 if low == 0.0 else abs(low) * 0.05
        return low - eps, high + eps
    return low, high


def _arbbox(values: Sequence[float]) -> tuple[float, float, float]:
    if not values:
        return 1.0, 0.0, 0.0
    amin = min(float(v) for v in values)
    amax = max(float(v) for v in values)
    delta = abs(amax - amin)
    if delta == 0.0:
        delta = 1.0
    return delta, amin, amax


def _hex_word(value: float) -> str:
    clamped = max(-1.0, min(1.0, float(value)))
    remain = int(clamped * 32767.0) + 32768
    remain = min(65535, max(0, remain))
    return f"{remain:04X}"


def _emit_hex_stream(out: list[str], words: Sequence[str]) -> None:
    # Fortran HEX flushes 19 words per line (`FORMAT(1X, 19A4)`).
    for idx in range(0, len(words), 19):
        out.append(" " + "".join(words[idx : idx + 19]))


def _emit_fortran_plot(
    out: list[str],
    *,
    x: Sequence[float],
    y: Sequence[float],
    xmn: float,
    xmx: float,
    ymn: float,
    ymx: float,
    ox: float,
    oy: float,
    wd: float,
    ht: float,
) -> None:
    n = min(len(x), len(y))
    if n <= 0:
        return

    x_use = [float(v) for v in x[:n]]
    y_use = [float(v) for v in y[:n]]
    dx, xn, _ = _arbbox(x_use)
    dy, yn, _ = _arbbox(y_use)
    absx = abs(float(xmx) - float(xmn))
    absy = abs(float(ymx) - float(ymn))
    if min(absx, absy, abs(dx), abs(dy)) <= 0.0:
        return

    xpand = float(wd) * dx / absx
    ypand = float(ht) * dy / absy
    xoff = float(wd) * (xn - min(float(xmn), float(xmx))) / absx
    yoff = float(ht) * (yn - min(float(ymn), float(ymx))) / absy
    out.append(
        f" {n:5d} {xoff:9.4f} {yoff:9.4f} {xpand:9.4f} {ypand:9.4f} {float(ox):9.4f} {float(oy):9.4f} plot"
    )

    words: list[str] = []
    # Mirrors Fortran PLOT/PLOT_gap: first sample duplicated before loop.
    words.append(_hex_word((x_use[0] - xn) / dx))
    words.append(_hex_word((y_use[0] - yn) / dy))
    for xv, yv in zip(x_use, y_use):
        words.append(_hex_word((xv - xn) / dx))
        words.append(_hex_word((yv - yn) / dy))
    _emit_hex_stream(out, words)


def _emit_fortran_plot_gap(
    out: list[str],
    *,
    x: Sequence[float],
    y: Sequence[float],
    xmn: float,
    xmx: float,
    ymn: float,
    ymx: float,
    ox: float,
    oy: float,
    wd: float,
    ht: float,
) -> None:
    n = min(len(x), len(y))
    if n <= 1:
        _emit_fortran_plot(
            out,
            x=x,
            y=y,
            xmn=xmn,
            xmx=xmx,
            ymn=ymn,
            ymx=ymx,
            ox=ox,
            oy=oy,
            wd=wd,
            ht=ht,
        )
        return

    # Fortran `PLOT_gap` iterates with at most 10 segments.
    nend = 0
    for _ in range(10):
        nstart = nend
        if nstart >= n - 1:
            return
        xtol = 0.5 * abs(float(x[nstart + 1]) - float(x[nstart]))
        jx = nstart + 2
        while jx < n:
            second_diff = abs(float(x[jx]) - 2.0 * float(x[jx - 1]) + float(x[jx - 2]))
            if second_diff > xtol:
                break
            jx += 1
        nend = jx - 1
        _emit_fortran_plot(
            out,
            x=x[nstart : nend + 1],
            y=y[nstart : nend + 1],
            xmn=xmn,
            xmx=xmx,
            ymn=ymn,
            ymx=ymx,
            ox=ox,
            oy=oy,
            wd=wd,
            ht=ht,
        )


def _fortran_e(value: float, digits: int = 2) -> str:
    return f"{float(value):.{digits}E}"


def _fortran_ratio(value: float) -> str:
    mag = abs(float(value))
    if mag < 0.1:
        return _fortran_e(value, 1)
    if mag < 10.0:
        return f"{float(value):0.3f}"
    return f"{float(value):0.2f}"


def _build_report_rows(fit_result: FitResult) -> tuple[list[str], list[str], str]:
    names = list(fit_result.metabolite_names) or [f"basis_{j+1}" for j in range(len(fit_result.coefficients))]
    coeffs = list(fit_result.coefficients)
    sds = list(fit_result.coefficient_sds or ())
    if len(sds) < len(coeffs):
        sds.extend([0.0] * (len(coeffs) - len(sds)))

    name_to_coeff = {str(n).strip().lower(): float(v) for n, v in zip(names, coeffs)}
    ref_val = name_to_coeff.get("cr+pcr")
    if ref_val is None:
        ref_val = name_to_coeff.get("cre+pcr")
    if ref_val is None:
        ref_val = name_to_coeff.get("cr", 0.0) + name_to_coeff.get("pcr", 0.0)
    if abs(ref_val) < 1e-30:
        ref_val = 1.0

    rows_main: list[str] = []
    rows_extra: list[str] = []
    for name, conc, sd in zip(names, coeffs, sds):
        percent_sd = 999 if conc <= 0.0 else int(round(100.0 * abs(sd) / max(abs(conc), 1e-30)))
        ratio = conc / ref_val
        row = f"{_fortran_e(conc):>8} {percent_sd:>3d}% {_fortran_ratio(ratio):>7} {name}"
        rows_main.append(row)

    for expr, value, sd in fit_result.combined:
        percent_sd = 999 if value <= 0.0 else int(round(100.0 * abs(sd) / max(abs(value), 1e-30)))
        ratio = value / ref_val
        row = f"{_fortran_e(value):>8} {percent_sd:>3d}% {_fortran_ratio(ratio):>7} {expr}"
        rows_extra.append(row)

    ref_name = "Cr+PCr" if "cr+pcr" in name_to_coeff or ("cr" in name_to_coeff and "pcr" in name_to_coeff) else "ref"
    return rows_main, rows_extra, ref_name


def _append_second_page(
    out: list[str],
    *,
    title_line_1: str,
    title_line_2: str,
    now_stamp: str,
    fit_result: FitResult,
    metadata: Mapping[str, object] | None,
) -> None:
    rows_main, rows_extra, ref_name = _build_report_rows(fit_result)
    md = dict(metadata or {})
    raw_name = str(md.get("raw_data_file", "") or "").strip()
    basis_name = str(md.get("basis_file", "") or "").strip()
    out_name = str(md.get("output_filename", "") or "").strip()
    hzpppm = md.get("hzpppm")
    deltat = md.get("dwell_time_s")
    nunfil = md.get("nunfil")
    shift_ppm = md.get("shift_ppm")
    phase0_deg = md.get("phase0_deg")
    phase1_deg_per_ppm = md.get("phase1_deg_per_ppm")

    # Fortran emits a fresh prolog before page 2 in reference output.
    out.extend(_FORTRAN_PROLOG_LINES)
    out.extend(
        [
            "%%EndProlog",
            "%%Page:   2   2",
            "MPGdict begin cm",
            "0 27.9000 translate -90 rotate",
            "[] 0 setdash",
            "/Helvetica  11.0000 font",
            " 13.950  19.112 m",
            f"{{({title_line_1 if title_line_1.strip() else ' '})s}}cst",
            "/Helvetica-Oblique   9.0000 font",
            " 13.950  18.600 m",
            f"{{({title_line_2 if title_line_2.strip() else 'Data of:'})s}}cst",
            "  1.600  17.965 m",
            "{(LCModel \\(Version 6.3-1R\\) Copyright: S.W. Provencher.          Ref.: Magn. Reson. Med. 30:672-679 \\(1993\\).)s}lst",
            " 26.600  17.965 m",
            f"{{({now_stamp})s}}rst",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  8.3596   0.0000   1.3000  17.6479 li",
            "/Courier-Bold   7.8000 font",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            f"  1.385  17.290 m",
            f"{{(   Conc.  %SD /{escape_postscript_text(ref_name)}  Metabolite)s}}lst",
            "/Courier   7.8000 font",
        ]
    )

    y = 16.932
    for row in rows_main:
        if y < 4.663:
            break
        row_ps = escape_postscript_text(row)
        out.extend(
            [
                "  0.0000  0.0000  0.0000 setrgbcolor",
                "  1.385 " + f"{y:7.3f}" + " m",
                f"{{({row_ps})s}}lst",
            ]
        )
        y -= 0.358

    if rows_extra:
        out.extend(
            [
                "  0.0000  0.0000  0.0000 setrgbcolor",
                "  8.3596   0.0000   1.3000   9.3131 li",
                "/Courier   7.8000 font",
            ]
        )
        y = min(y, 8.955)
        for row in rows_extra[:12]:
            row_ps = escape_postscript_text(row)
            out.extend(
                [
                    "  0.0000  0.0000  0.0000 setrgbcolor",
                    "  1.385 " + f"{y:7.3f}" + " m",
                    f"{{({row_ps})s}}lst",
                ]
            )
            y -= 0.358

    snr = int(round(float(fit_result.snr_estimate)))
    fwhm_ppm = max(0.00001, float(fit_result.residual_norm) * 200.0)
    misc_lines = [
        f" FWHM = {fwhm_ppm:0.3f} ppm    S/N = {snr:3d}",
    ]
    if shift_ppm is not None:
        misc_lines.append(f" Data shift = {float(shift_ppm):0.3f} ppm")
    if phase0_deg is not None and phase1_deg_per_ppm is not None:
        misc_lines.append(f" Ph: {float(phase0_deg):4.0f} deg       {float(phase1_deg_per_ppm):3.1f} deg/ppm")
    elif phase0_deg is not None:
        misc_lines.append(f" Ph: {float(phase0_deg):4.0f} deg       0.0 deg/ppm")

    out.extend(
        [
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0000  13.0924   9.6596   4.5555 li",
            "  8.3596   0.0000   1.3000   4.5555 li",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "/Courier-Bold   7.8000 font",
            "  5.480   4.055 m",
            "{(NO DIAGNOSTICS)s}cst",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0000  13.7005   9.6596   3.9474 li",
            "  8.3596   0.0000   1.3000   3.9474 li",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "/Courier-Bold   7.8000 font",
            "  5.480   3.447 m",
            "{(MISCELLANEOUS OUTPUT)s}cst",
            "/Courier   7.8000 font",
        ]
    )
    y_misc = 3.089
    for line in misc_lines[:4]:
        out.extend(
            [
                "  1.385 " + f"{y_misc:7.3f}" + " m",
                f"{{({escape_postscript_text(line)})s}}lst",
            ]
        )
        y_misc -= 0.358

    out.extend(
        [
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0000  15.3818   9.6596   2.2661 li",
            "  8.3596   0.0000   1.3000   2.2661 li",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "/Courier-Bold   7.8000 font",
            "  5.480   1.765 m",
            "{(INPUT CHANGES)s}cst",
            "/Courier   7.8000 font",
        ]
    )
    left_lines = []
    if out_name:
        left_lines.append(f"filps='{out_name}'")
    if raw_name:
        left_lines.append(f"filraw='{raw_name}'")
    if basis_name:
        left_lines.append(f"filbas='{basis_name}'")
    y_input = 1.408
    for line in left_lines[:3]:
        out.extend(
            [
                "  1.385 " + f"{y_input:7.3f}" + " m",
                f"{{({escape_postscript_text(line)})s}}lst",
            ]
        )
        y_input -= 0.358

    out.extend(
        [
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0000  16.3479   9.6596   1.3000 li",
            "  8.3596   0.0000   9.6596  17.6479 li",
            "  0.0000  0.0000  0.0000 setrgbcolor",
        ]
    )
    right_lines: list[str] = []
    if raw_name:
        right_lines.append(f"filraw='{raw_name}'")
    if basis_name:
        right_lines.append(f"filbas='{basis_name}'")
    if hzpppm is not None:
        right_lines.append(f"hzpppm={float(hzpppm):0.6f}")
    if deltat is not None:
        right_lines.append(f"deltat={float(deltat):.0e}")
    if nunfil is not None:
        right_lines.append(f"nunfil={int(nunfil)}")
    y_right = 17.290
    for line in right_lines[:5]:
        out.extend(
            [
                "  9.745 " + f"{y_right:7.3f}" + " m",
                f"{{({escape_postscript_text(line)})s}}lst",
            ]
        )
        y_right -= 0.358

    out.extend(
        [
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0000   1.8959  18.0191  15.7520 li",
            "  8.3596   0.0000   9.6596  15.7520 li",
            "  0.0000  0.0000  0.0000 setrgbcolor",
        ]
    )


def build_fit_postscript(
    *,
    title_line_1: str,
    title_line_2: str = "",
    x_values: Sequence[float],
    data_values: Sequence[float],
    fit_values: Sequence[float] | None = None,
    fit_result: FitResult | None = None,
    metadata: Mapping[str, object] | None = None,
) -> str:
    """Build a one-page PostScript report with Fortran-like layout scaffolding."""

    x = [float(v) for v in x_values]
    y_data = [float(v) for v in data_values]
    y_fit = [float(v) for v in fit_values] if fit_values is not None else []
    y_res = [yd - yf for yd, yf in zip(y_data, y_fit)] if y_fit else []

    xlo, xhi = _normalize_bounds(x, 0.0, 1.0)
    ymain_min, ymain_max = _normalize_bounds(y_data + y_fit, 0.0, 1.0)
    if y_fit:
        ymain_min = min(0.0, ymain_min)
        ymain_max = max(0.0, ymain_max)
        yres_min, yres_max = _normalize_bounds(y_res, 0.0, 1.0)
        yres_min = min(0.0, yres_min)
        yres_max = max(0.0, yres_max)
        ytotal = (ymain_max - ymain_min) + (yres_max - yres_min)
        if ytotal <= 0.0:
            ytotal = 1.0
        yaxis_main = 15.5224 * (ymain_max - ymain_min) / ytotal
        yaxis_res = 15.5224 * (yres_max - yres_min) / ytotal
    else:
        yres_min = 0.0
        yres_max = 0.0
        yaxis_main = 15.5224
        yaxis_res = 0.0
        ytotal = ymain_max - ymain_min if ymain_max > ymain_min else 1.0
    ytocm = 15.5224 / ytotal
    yzero_main = 2.1255 + yaxis_main - ymain_max * ytocm

    # Keep one blank between parens when empty to mirror Fortran STRCHK/STRING.
    if title_line_1.strip():
        t1 = escape_postscript_text(title_line_1)
    else:
        t1 = " "
    if title_line_2.strip():
        raw_t2 = title_line_2
    else:
        raw_t2 = "Data of:" if not title_line_1.strip() else " "
    t2 = raw_t2 if raw_t2 == " " else escape_postscript_text(raw_t2)
    now_stamp = escape_postscript_text(datetime.now().strftime("%a %b %d %H:%M:%S %Y"))
    y_top_label = f"{yres_max: .1E}" if y_fit else f"{ymain_max: .1E}"
    y_main_top_label = f"{ymain_max: .5g}"

    out: list[str] = [
        "%!PS-Adobe-2.0",
        "%%Creator: LCModel",
        "%%BoundingBox: 0 0  595  791",
        "%%EndComments",
    ]
    out.extend(_FORTRAN_PROLOG_LINES)
    out.extend(
        [
            "%%EndProlog",
            "%%Page:   1   1",
            "MPGdict begin cm",
            "0 27.9000 translate -90 rotate",
            "[] 0 setdash",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            " 18.8336  15.5224   1.7953   2.1255 box",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "/Helvetica  11.0000 font",
            " 13.950  19.112 m",
            f"{{({t1})s}}cst",
            "/Helvetica-Oblique   9.0000 font",
            " 13.950  18.600 m",
            f"{{({t2})s}}cst",
            "  2.095  17.965 m",
            "{(LCModel \\(Version 6.3-1R\\) Copyright: S.W. Provencher.          Ref.: Magn. Reson. Med. 30:672-679 \\(1993\\).)s}lst",
            " 26.600  17.965 m",
            f"{{({now_stamp})s}}rst",
            "/Helvetica   7.8000 font",
            " 11.212   1.300 m",
            "{(Chemical Shift (ppm))s}cst",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
        ]
    )
    for tick in (
        "        ",
        "  0.40  ",
        "  0.60  ",
        "  0.80  ",
        "  1.0   ",
        "  1.2   ",
        "  1.4   ",
        "  1.6   ",
        "  1.8   ",
        "  2.0   ",
        "  2.2   ",
        "  2.4   ",
        "  2.6   ",
        "  2.8   ",
        "  3.0   ",
        "  3.2   ",
        "  3.4   ",
        "  3.6   ",
        "  3.8   ",
        "  4.0   ",
    ):
        out.append(f"({tick})")
    out.extend(
        [
            "20   1.0000  -0.9912  -0.0000 -18.8336    0  20.6289   2.1255 axis",
            " 39  -0.4956  -0.0000  -0.0826    0  20.6289   2.1255 ticks",
            "  0.0050 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0050 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "[  0.0500   0.1000] 0 setdash",
            " 39  -0.4956  -0.0000  15.5224    0  20.6289   2.1255 ticks",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.0050 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            " 18.8336   0.0000   1.7953  17.0134 li",
            "  1.575  17.648 m   90 r",
            f"{{({escape_postscript_text(y_top_label)})s}}cst",
            " -90 r",
            "[] 0 setdash",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "  0.1651   0.0000   1.6302  17.0134 li",
            "  0.1651   0.0000   1.6302  17.6479 li",
        ]
    )

    if y_fit and y_res:
        out.extend(
            [
                "  0.0100 setlinewidth",
                "  0.0000  0.0000  0.0000 setrgbcolor",
            ]
        )
        _emit_fortran_plot_gap(
            out,
            x=x,
            y=y_res,
            xmn=xlo,
            xmx=xhi,
            ymn=yres_min,
            ymx=yres_max,
            ox=20.6289,
            oy=2.1255 + yaxis_main,
            wd=-18.8336,
            ht=yaxis_res,
        )

    out.extend(
        [
            "  0.0050 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            "[] 0 setdash",
            f" 20  -0.9912  -0.0000 {yzero_main:8.4f}    0  20.6289   2.1255 ticks",
            "[  0.0500   0.1000] 0 setdash",
            "  0.0050 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            f" 18.8336   0.0000   1.7953 {yzero_main:8.4f} li",
            "[] 0 setdash",
            "  0.0400 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
            f"  1.575 {yzero_main:7.3f} m   90 r",
            "{(0)s}cst",
            " -90 r",
            f"  1.575 {2.1255 + yaxis_main:7.3f} m   90 r",
            f"{{({escape_postscript_text(y_main_top_label)})s}}cst",
            " -90 r",
            f"  0.1651   0.0000   1.6302 {yzero_main:8.4f} li",
            f" 18.9987   0.0000   1.6302 {2.1255 + yaxis_main:8.4f} li",
        ]
    )

    if y_fit:
        out.extend(
            [
                "  0.0600 setlinewidth",
                "  0.9990  0.0000  0.0000 setrgbcolor",
            ]
        )
        _emit_fortran_plot_gap(
            out,
            x=x,
            y=y_fit,
            xmn=xlo,
            xmx=xhi,
            ymn=ymain_min,
            ymx=ymain_max,
            ox=20.6289,
            oy=2.1255,
            wd=-18.8336,
            ht=yaxis_main,
        )

        out.extend(
            [
                "  0.0600 setlinewidth",
                "  0.9990  0.0000  0.0000 setrgbcolor",
            ]
        )
        _emit_fortran_plot_gap(
            out,
            x=x,
            y=[0.0 for _ in x],
            xmn=xlo,
            xmx=xhi,
            ymn=ymain_min,
            ymx=ymain_max,
            ox=20.6289,
            oy=2.1255,
            wd=-18.8336,
            ht=yaxis_main,
        )

    out.extend(
        [
            "[  0.0500   0.1000] 0 setdash",
            "  0.0100 setlinewidth",
            "  0.0000  0.0000  0.0000 setrgbcolor",
        ]
    )
    _emit_fortran_plot_gap(
        out,
        x=x,
        y=y_data,
        xmn=xlo,
        xmx=xhi,
        ymn=ymain_min,
        ymx=ymain_max,
        ox=20.6289,
        oy=2.1255,
        wd=-18.8336,
        ht=yaxis_main,
    )

    out.extend(["  0.0000  0.0000  0.0000 setrgbcolor", "showpage"])

    if fit_result is not None:
        _append_second_page(
            out,
            title_line_1=t1,
            title_line_2=t2,
            now_stamp=now_stamp,
            fit_result=fit_result,
            metadata=metadata,
        )
        out.extend(["showpage", "%%Trailer", "%%EOF"])
    else:
        out.append("%%EOF")
    return "\n".join(out) + "\n"


def write_fit_postscript(
    path: str | Path,
    *,
    title_line_1: str,
    title_line_2: str = "",
    x_values: Sequence[float],
    data_values: Sequence[float],
    fit_values: Sequence[float] | None = None,
    fit_result: FitResult | None = None,
    metadata: Mapping[str, object] | None = None,
) -> str:
    """Write PostScript fit report and return written path."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    text = build_fit_postscript(
        title_line_1=title_line_1,
        title_line_2=title_line_2,
        x_values=x_values,
        data_values=data_values,
        fit_values=fit_values,
        fit_result=fit_result,
        metadata=metadata,
    )
    out_path.write_text(text, encoding="utf-8")
    return str(out_path)
