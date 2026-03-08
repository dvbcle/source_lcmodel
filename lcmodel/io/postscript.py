"""Minimal PostScript report writer for fit visualizations."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from lcmodel.core.text import escape_postscript_text


def _normalize_bounds(values: Sequence[float], fallback_low: float, fallback_high: float) -> tuple[float, float]:
    if not values:
        return fallback_low, fallback_high
    low = min(float(v) for v in values)
    high = max(float(v) for v in values)
    if low == high:
        eps = 1.0 if low == 0.0 else abs(low) * 0.05
        return low - eps, high + eps
    return low, high


def _map_linear(value: float, src_lo: float, src_hi: float, dst_lo: float, dst_hi: float) -> float:
    if src_hi == src_lo:
        return 0.5 * (dst_lo + dst_hi)
    frac = (float(value) - src_lo) / (src_hi - src_lo)
    return dst_lo + frac * (dst_hi - dst_lo)


def _emit_polyline(
    out: list[str],
    x: Sequence[float],
    y: Sequence[float],
    xlo: float,
    xhi: float,
    ylo: float,
    yhi: float,
    ox: float,
    oy: float,
    width: float,
    height: float,
) -> None:
    if len(x) != len(y) or not x:
        return
    px0 = _map_linear(x[0], xlo, xhi, ox, ox + width)
    py0 = _map_linear(y[0], ylo, yhi, oy, oy + height)
    out.append(f"{px0:.4f} {py0:.4f} moveto")
    for i in range(1, len(x)):
        px = _map_linear(x[i], xlo, xhi, ox, ox + width)
        py = _map_linear(y[i], ylo, yhi, oy, oy + height)
        out.append(f"{px:.4f} {py:.4f} lineto")
    out.append("stroke")


def build_fit_postscript(
    *,
    title_line_1: str,
    title_line_2: str = "",
    x_values: Sequence[float],
    data_values: Sequence[float],
    fit_values: Sequence[float] | None = None,
) -> str:
    """Build a one-page PostScript fit plot with title and axes."""

    x = [float(v) for v in x_values]
    y_data = [float(v) for v in data_values]
    y_fit = [float(v) for v in fit_values] if fit_values is not None else []

    xlo, xhi = _normalize_bounds(x, 0.0, 1.0)
    ylo, yhi = _normalize_bounds(y_data + y_fit, -1.0, 1.0)

    # Plot rectangle in points (letter-sized page).
    ox = 72.0
    oy = 160.0
    width = 468.0
    height = 320.0

    t1 = escape_postscript_text(title_line_1)
    t2 = escape_postscript_text(title_line_2)

    out: list[str] = [
        "%!PS-Adobe-3.0",
        "%%Pages: 1",
        "%%BoundingBox: 0 0 612 792",
        "/Times-Roman findfont 12 scalefont setfont",
        "72 740 moveto",
        f"({t1}) show",
    ]
    if t2:
        out.extend(["72 724 moveto", f"({t2}) show"])

    out.extend(
        [
            "0 setgray",
            "1 setlinewidth",
            "newpath",
            f"{ox:.4f} {oy:.4f} moveto",
            f"{ox + width:.4f} {oy:.4f} lineto",
            f"{ox + width:.4f} {oy + height:.4f} lineto",
            f"{ox:.4f} {oy + height:.4f} lineto",
            "closepath stroke",
            "/Times-Roman findfont 9 scalefont setfont",
            f"{ox:.4f} {oy - 16:.4f} moveto ({xlo:.4g}) show",
            f"{ox + width - 30:.4f} {oy - 16:.4f} moveto ({xhi:.4g}) show",
            f"{ox - 36:.4f} {oy:.4f} moveto ({ylo:.4g}) show",
            f"{ox - 36:.4f} {oy + height - 2:.4f} moveto ({yhi:.4g}) show",
            "0 0 1 setrgbcolor",
            "0.8 setlinewidth",
            "newpath",
        ]
    )
    _emit_polyline(out, x, y_data, xlo, xhi, ylo, yhi, ox, oy, width, height)

    if y_fit:
        out.extend(["1 0 0 setrgbcolor", "1 setlinewidth", "newpath"])
        _emit_polyline(out, x, y_fit, xlo, xhi, ylo, yhi, ox, oy, width, height)

    out.extend(["0 setgray", "showpage", "%%EOF"])
    return "\n".join(out) + "\n"


def write_fit_postscript(
    path: str | Path,
    *,
    title_line_1: str,
    title_line_2: str = "",
    x_values: Sequence[float],
    data_values: Sequence[float],
    fit_values: Sequence[float] | None = None,
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
    )
    out_path.write_text(text, encoding="utf-8")
    return str(out_path)

