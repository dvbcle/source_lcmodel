"""PostScript and page-layout semantic overrides."""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import Any
import builtins
import math

from lcmodel.core.text import escape_postscript_text


def _ps_lines(state: dict[str, Any]) -> list[str]:
    lines = state.get("ps_lines")
    if not isinstance(lines, list):
        lines = []
        state["ps_lines"] = lines
    return lines


def _ov_psetup(
    top_of_file: bool,
    wd: float,
    ht: float,
    landsc: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    lines = _ps_lines(out)
    if bool(top_of_file) and not lines:
        # Fortran PSETUP:
        # start page stream and define page geometry variables.
        lines.extend(["%!PS-Adobe-3.0", "%%Creator: lcmodel semantic override"])
    lines.append("gsave")
    if bool(landsc):
        lines.append("90 rotate")
    lines.append(f"/PageWidth {float(wd):.6g} def")
    lines.append(f"/PageHeight {float(ht):.6g} def")
    out["ps_landsc"] = bool(landsc)
    return out


def _ov_linewd(width: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    _ps_lines(out).append(f"{max(0.0, float(width)):.6g} setlinewidth")
    return out


def _ov_rgb(rgbv: Sequence[float], state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    r = float(rgbv[0]) if len(rgbv) > 0 else 0.0
    g = float(rgbv[1]) if len(rgbv) > 1 else 0.0
    b = float(rgbv[2]) if len(rgbv) > 2 else 0.0
    _ps_lines(out).append(f"{r:.6g} {g:.6g} {b:.6g} setrgbcolor")
    return out


def _ov_dash(idshpt: int, dshpat: Sequence[float], state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if int(idshpt) <= 0:
        # Fortran DASH id<=0 means solid line.
        _ps_lines(out).append("[] 0 setdash")
        return out
    pat = [max(0.0, float(v)) for v in dshpat if float(v) > 0.0]
    if not pat:
        _ps_lines(out).append("[] 0 setdash")
    else:
        txt = " ".join(f"{v:.6g}" for v in pat)
        _ps_lines(out).append(f"[{txt}] 0 setdash")
    return out


def _ov_line(
    ox: float,
    oy: float,
    wd: float,
    ht: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    x1 = float(ox)
    y1 = float(oy)
    x2 = x1 + float(wd)
    y2 = y1 + float(ht)
    _ps_lines(out).append(f"newpath {x1:.6g} {y1:.6g} moveto {x2:.6g} {y2:.6g} lineto stroke")
    return out


def _ov_box(
    ox: float,
    oy: float,
    wd: float,
    ht: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    x = float(ox)
    y = float(oy)
    w = float(wd)
    h = float(ht)
    _ps_lines(out).append(
        "newpath "
        f"{x:.6g} {y:.6g} moveto "
        f"{x + w:.6g} {y:.6g} lineto "
        f"{x + w:.6g} {y + h:.6g} lineto "
        f"{x:.6g} {y + h:.6g} lineto closepath stroke"
    )
    return out


def _map_plot_point(value: float, src_min: float, src_max: float, dst_min: float, dst_len: float) -> float:
    if abs(src_max - src_min) <= 1e-30:
        return dst_min
    return dst_min + (float(value) - src_min) * dst_len / (src_max - src_min)


def _ov_plot(
    n: int,
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
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    count = max(0, min(int(n), len(x), len(y)))
    if count <= 0:
        return out
    # Fortran PLOT:
    # map data coordinates into page box and emit a polyline stroke.
    lines = _ps_lines(out)
    px0 = _map_plot_point(float(x[0]), float(xmn), float(xmx), float(ox), float(wd))
    py0 = _map_plot_point(float(y[0]), float(ymn), float(ymx), float(oy), float(ht))
    cmd = [f"newpath {px0:.6g} {py0:.6g} moveto"]
    for i in range(1, count):
        pxi = _map_plot_point(float(x[i]), float(xmn), float(xmx), float(ox), float(wd))
        pyi = _map_plot_point(float(y[i]), float(ymn), float(ymx), float(oy), float(ht))
        cmd.append(f"{pxi:.6g} {pyi:.6g} lineto")
    cmd.append("stroke")
    lines.append(" ".join(cmd))
    return out


def _ov_plot_gap(
    n: int,
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
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Fortran PLOT_GAP keeps same coordinate transform as PLOT in this adapter.
    return _ov_plot(n, x, y, xmn, xmx, ymn, ymx, ox, oy, wd, ht, state)


def _ov_font(pitch: float, police: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    face = builtins.str(police).strip() or "Courier"
    size = max(1.0, abs(float(pitch)))
    _ps_lines(out).append(f"/{face} findfont {size:.6g} scalefont setfont")
    return out


def _ov_string(
    flush: bool,
    ang: float,
    ox: float,
    oy: float,
    st: str,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    text = escape_postscript_text(builtins.str(st))
    lines = _ps_lines(out)
    lines.append(
        "gsave "
        f"{float(ox):.6g} {float(oy):.6g} translate "
        f"{float(ang):.6g} rotate 0 0 moveto ({text}) show grestore"
    )
    if bool(flush):
        out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_show(flush: bool, st: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    text = escape_postscript_text(builtins.str(st))
    lines = _ps_lines(out)
    lines.append(f"({text}) show")
    if bool(flush):
        out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_showpg(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    _ps_lines(out).append("showpage")
    return out


def _ov_endps(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    lines = _ps_lines(out)
    lines.append("grestore")
    out["postscript"] = "\n".join(lines) + "\n"
    return out


def _ov_strpou(state: dict[str, Any] | None = None) -> dict[str, Any]:
    # Preserve current output buffer in state for compatibility.
    out = state if state is not None else {}
    out["postscript"] = "\n".join(_ps_lines(out)) + ("\n" if _ps_lines(out) else "")
    return out


def _ov_makeps(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    # Fortran MAKEPS compatibility:
    # synthesize minimal page setup if caller emitted no drawing commands yet.
    if not _ps_lines(out):
        _ov_psetup(True, 612.0, 792.0, False, out)
    out["makeps_called"] = True
    return out


def _ov_onepag(
    ncurve: int,
    yfit: Sequence[float],
    ydata: Sequence[float],
    lchlin: bool,
    nsubti: int,
    pagex: Sequence[float],
    pagey: Sequence[float],
    subtit: Sequence[str],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (lchlin, pagex, pagey)
    out = state if state is not None else {}
    _ov_makeps(out)
    out["onepag_curves"] = int(ncurve)
    out["onepag_points"] = min(len(yfit), len(ydata))
    out["onepag_subtitles"] = tuple(builtins.str(s) for s in subtit[: max(0, int(nsubti))])
    return out


def _ov_tick(
    ang: float,
    ox: float,
    oy: float,
    length: float,
    gmn: float,
    gmx: float,
    tckbeg: float,
    tckinc: float,
    grid: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (ox, oy, length, tckbeg)
    out = state if state is not None else {}
    _ps_lines(out).append(
        f"% tick ang={float(ang):.6g} from {float(gmn):.6g} to {float(gmx):.6g} "
        f"inc={float(tckinc):.6g} grid={bool(grid)}"
    )
    return out


def _ov_axis(
    ang: float,
    ox: float,
    oy: float,
    length: float,
    gmn: float,
    gmx: float,
    tckbeg: float,
    tckinc: float,
    pos: Sequence[float],
    ljust1: bool,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (pos, ljust1)
    out = state if state is not None else {}
    _ov_line(ox, oy, length * math.cos(float(ang)), length * math.sin(float(ang)), out)
    _ov_tick(ang, ox, oy, length, gmn, gmx, tckbeg, tckinc, False, out)
    return out


def _ov_hex(val: int, inum: Any, flush: bool, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    hex_text = f"{int(val) & 0xFFFFFFFF:X}"
    if isinstance(inum, MutableSequence) and len(inum) >= 1:
        inum[0] = len(hex_text)
    out["hex"] = hex_text
    if bool(flush):
        _ps_lines(out).append(f"% HEX {hex_text}")
    return out


def _ov_check_bottom(
    ycurr: float,
    decrement: float,
    xboxlo: float,
    outside: Any,
    ytop_column: Sequence[float],
    column_width: Sequence[float],
    xboxlo_max: float,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (xboxlo, ytop_column, column_width, xboxlo_max)
    out = state if state is not None else {}
    new_y = float(ycurr) - float(decrement)
    is_outside = new_y < 0.0
    if isinstance(outside, MutableSequence) and len(outside) >= 1:
        outside[0] = is_outside
    out["ycurr"] = new_y
    out["outside"] = is_outside
    return out


def _ov_end_table(
    ycurr: float,
    xboxlo: float,
    ytop_column: Sequence[float],
    column_width: Sequence[float],
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (xboxlo, ytop_column)
    out = state if state is not None else {}
    out["table_end_y"] = float(ycurr)
    out["table_columns"] = len(column_width)
    return out


POSTSCRIPT_OVERRIDES = {
    "psetup": _ov_psetup,
    "linewd": _ov_linewd,
    "rgb": _ov_rgb,
    "dash": _ov_dash,
    "line": _ov_line,
    "box": _ov_box,
    "plot": _ov_plot,
    "plot_gap": _ov_plot_gap,
    "font": _ov_font,
    "string": _ov_string,
    "show": _ov_show,
    "showpg": _ov_showpg,
    "endps": _ov_endps,
    "strpou": _ov_strpou,
    "makeps": _ov_makeps,
    "onepag": _ov_onepag,
    "tick": _ov_tick,
    "axis": _ov_axis,
    "hex": _ov_hex,
    "check_bottom": _ov_check_bottom,
    "end_table": _ov_end_table,
}
