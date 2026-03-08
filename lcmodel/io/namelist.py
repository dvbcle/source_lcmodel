"""Minimal Fortran namelist parser for LCModel control-file ingestion."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from lcmodel.models import RunConfig


_TRUE_VALUES = {".true.", "true", "t"}
_FALSE_VALUES = {".false.", "false", "f"}
_INDEXED_KEY_RE = re.compile(r"^([A-Za-z_]\w*)\((\d+)(?:\s*,\s*(\d+))?\)$")


def _strip_inline_comment(line: str) -> str:
    in_quote = False
    quote_char = ""
    out: list[str] = []
    for ch in line:
        if ch in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
                quote_char = ""
            out.append(ch)
            continue
        if ch == "!" and not in_quote:
            break
        out.append(ch)
    return "".join(out)


def _parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if (value.startswith("'") and value.endswith("'")) or (
        value.startswith('"') and value.endswith('"')
    ):
        return value[1:-1]

    low = value.lower()
    if low in _TRUE_VALUES:
        return True
    if low in _FALSE_VALUES:
        return False

    norm = re.sub(r"([0-9])d([+-]?[0-9]+)", r"\1e\2", value, flags=re.IGNORECASE)
    try:
        return int(norm)
    except ValueError:
        pass
    try:
        return float(norm)
    except ValueError:
        return value


def parse_fortran_namelist(text: str, expected_name: str | None = None) -> dict[str, Any]:
    """Parse a single namelist block like `$LCMODL ... /`."""

    cleaned_lines = [_strip_inline_comment(line) for line in text.splitlines()]
    cleaned = "\n".join(cleaned_lines)
    start = cleaned.find("$")
    if start < 0:
        raise ValueError("No namelist start marker '$' found")

    slash = cleaned.find("/", start)
    if slash < 0:
        raise ValueError("No namelist terminator '/' found")

    header_end = cleaned.find("\n", start)
    if header_end < 0 or header_end > slash:
        header_end = slash
    header = cleaned[start + 1 : header_end].strip()
    name = header.split()[0] if header else ""
    if expected_name and name.lower() != expected_name.lower():
        raise ValueError(f"Expected namelist ${expected_name}, found ${name}")

    payload = cleaned[header_end:slash]
    tokens: list[str] = []
    cur: list[str] = []
    in_quote = False
    quote_char = ""
    paren_depth = 0
    for ch in payload:
        if ch in {"'", '"'}:
            if not in_quote:
                in_quote = True
                quote_char = ch
            elif quote_char == ch:
                in_quote = False
                quote_char = ""
            cur.append(ch)
            continue
        if not in_quote:
            if ch == "(":
                paren_depth += 1
            elif ch == ")" and paren_depth > 0:
                paren_depth -= 1
        if ch == "," and not in_quote and paren_depth == 0:
            token = "".join(cur).strip()
            if token:
                tokens.append(token)
            cur = []
            continue
        cur.append(ch)
    last = "".join(cur).strip()
    if last:
        tokens.append(last)

    result: dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            continue
        key, raw_value = token.split("=", 1)
        key = key.strip().lower()
        value = _parse_scalar(raw_value)
        m = _INDEXED_KEY_RE.match(key)
        if m:
            base = m.group(1).lower()
            idx1 = int(m.group(2)) - 1
            idx2_text = m.group(3)
            existing = result.get(base)
            if not isinstance(existing, list):
                existing = []
            if idx2_text is None:
                while len(existing) <= idx1:
                    existing.append("")
                existing[idx1] = value
            else:
                idx2 = int(idx2_text) - 1
                while len(existing) <= idx2:
                    existing.append([])
                inner = existing[idx2]
                if not isinstance(inner, list):
                    inner = []
                while len(inner) <= idx1:
                    inner.append("")
                inner[idx1] = value
                existing[idx2] = inner
            result[base] = existing
        else:
            result[key] = value
    return result


def load_run_config_from_control_file(path: str | Path) -> RunConfig:
    """Load `RunConfig` from an LCModel-style control file."""

    text = Path(path).read_text(encoding="utf-8", errors="replace")
    nml = parse_fortran_namelist(text, expected_name="LCMODL")

    title = str(nml.get("title", ""))
    ntitle = int(nml.get("ntitle", 2))
    raw_data_file = nml.get("filraw")
    basis_file = nml.get("filbas")
    baseline_order = -1
    if "ndegz" in nml:
        try:
            baseline_order = int(nml["ndegz"])
        except Exception:
            baseline_order = -1
    ppm_start = None
    ppm_end = None
    if "ppmst" in nml:
        try:
            ppm_start = float(nml["ppmst"])
        except Exception:
            ppm_start = None
    if "ppmend" in nml:
        try:
            ppm_end = float(nml["ppmend"])
        except Exception:
            ppm_end = None
    exclude_ppm_ranges: tuple[tuple[float, float], ...] = ()
    if isinstance(nml.get("ppmgap"), list):
        pairs: list[tuple[float, float]] = []
        for item in nml["ppmgap"]:
            if isinstance(item, list) and len(item) >= 2:
                try:
                    a = float(item[0])
                    b = float(item[1])
                except Exception:
                    continue
                pairs.append((a, b))
        exclude_ppm_ranges = tuple(pairs)
    shift_search_points = 0
    if "nshifw" in nml:
        try:
            shift_search_points = max(0, int(nml["nshifw"]))
        except Exception:
            shift_search_points = 0
    alignment_circular = True
    if "shftcyc" in nml:
        alignment_circular = bool(nml.get("shftcyc"))
    fractional_shift_refine = bool(nml.get("fshref", False))
    fractional_shift_iterations = 18
    if "nshifit" in nml:
        try:
            fractional_shift_iterations = max(4, int(nml["nshifit"]))
        except Exception:
            fractional_shift_iterations = 18
    linewidth_scan_points = 0
    if "nlwscn" in nml:
        try:
            linewidth_scan_points = max(0, int(nml["nlwscn"]))
        except Exception:
            linewidth_scan_points = 0
    linewidth_scan_max_sigma_points = 0.0
    if "lwscmx" in nml:
        try:
            linewidth_scan_max_sigma_points = max(0.0, float(nml["lwscmx"]))
        except Exception:
            linewidth_scan_max_sigma_points = 0.0
    dwell_time_s = 0.0
    if "deltat" in nml:
        try:
            dwell_time_s = max(0.0, float(nml["deltat"]))
        except Exception:
            dwell_time_s = 0.0
    line_broadening_hz = 0.0
    if "lbhz" in nml:
        try:
            line_broadening_hz = max(0.0, float(nml["lbhz"]))
        except Exception:
            line_broadening_hz = 0.0
    phase_objective = "imag_abs"
    if isinstance(nml.get("phobj"), str):
        obj = str(nml["phobj"]).strip().lower()
        if obj in {"imag_abs", "smooth_real"}:
            phase_objective = obj
    phase_smoothness_power = 6
    if "ipowph" in nml:
        try:
            phase_smoothness_power = max(1, int(nml["ipowph"]))
            phase_objective = "smooth_real"
        except Exception:
            phase_smoothness_power = 6
    baseline_knots = 0
    if "nbackg" in nml:
        try:
            baseline_knots = max(0, int(nml["nbackg"]))
        except Exception:
            baseline_knots = 0
    baseline_smoothness = 0.0
    if "alphab" in nml:
        try:
            baseline_smoothness = max(0.0, float(nml["alphab"]))
        except Exception:
            baseline_smoothness = 0.0
    integration_border_points = 4
    if "nwndo" in nml:
        try:
            integration_border_points = max(1, int(nml["nwndo"]))
        except Exception:
            integration_border_points = 4

    include_metabolites: tuple[str, ...] = ()
    if isinstance(nml.get("chuse1"), list):
        names = [str(v).strip() for v in nml["chuse1"] if str(v).strip()]
        include_metabolites = tuple(names)
    elif isinstance(nml.get("chuse1"), str):
        one = str(nml["chuse1"]).strip()
        include_metabolites = (one,) if one else ()

    combine_expressions: tuple[str, ...] = ()
    if isinstance(nml.get("chcomb"), list):
        exprs = [str(v).strip() for v in nml["chcomb"] if str(v).strip()]
        combine_expressions = tuple(exprs)
    elif isinstance(nml.get("chcomb"), str):
        one = str(nml["chcomb"]).strip()
        combine_expressions = (one,) if one else ()

    output_filename = None
    for key in ("filps", "filcoo", "filpri"):
        value = nml.get(key)
        if isinstance(value, str) and value.strip():
            output_filename = value
            break
    table_output_file = None
    if isinstance(nml.get("filtab"), str) and nml["filtab"].strip():
        table_output_file = str(nml["filtab"])

    return RunConfig(
        title=title,
        ntitle=ntitle,
        output_filename=output_filename,
        table_output_file=table_output_file,
        raw_data_file=str(raw_data_file) if raw_data_file else None,
        raw_data_list_file=str(nml["filrawl"]) if isinstance(nml.get("filrawl"), str) and nml["filrawl"].strip() else None,
        batch_csv_file=str(nml["filcsv"]) if isinstance(nml.get("filcsv"), str) and nml["filcsv"].strip() else None,
        basis_file=str(basis_file) if basis_file else None,
        ppm_axis_file=str(nml["filppm"]) if isinstance(nml.get("filppm"), str) and nml["filppm"].strip() else None,
        basis_names_file=str(nml["filnam"]) if isinstance(nml.get("filnam"), str) and nml["filnam"].strip() else None,
        priors_file=str(nml["filprr"]) if isinstance(nml.get("filprr"), str) and nml["filprr"].strip() else None,
        time_domain_input=bool(nml.get("timdom", False)),
        auto_phase_zero_order=bool(nml.get("autoph0", False)),
        auto_phase_first_order=bool(nml.get("autoph1", False)),
        phase_objective=phase_objective,
        phase_smoothness_power=phase_smoothness_power,
        dwell_time_s=dwell_time_s,
        line_broadening_hz=line_broadening_hz,
        fit_ppm_start=ppm_start,
        fit_ppm_end=ppm_end,
        exclude_ppm_ranges=exclude_ppm_ranges,
        include_metabolites=include_metabolites,
        combine_expressions=combine_expressions,
        shift_search_points=shift_search_points,
        alignment_circular=alignment_circular,
        fractional_shift_refine=fractional_shift_refine,
        fractional_shift_iterations=fractional_shift_iterations,
        linewidth_scan_points=linewidth_scan_points,
        linewidth_scan_max_sigma_points=linewidth_scan_max_sigma_points,
        baseline_order=baseline_order,
        baseline_knots=baseline_knots,
        baseline_smoothness=baseline_smoothness,
        integration_border_points=integration_border_points,
    )
