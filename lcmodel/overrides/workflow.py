"""Workflow and orchestration semantic overrides."""

from __future__ import annotations

from collections.abc import MutableSequence
from typing import Any, Sequence
import builtins

from lcmodel.core.array_ops import reverse_first_n
from lcmodel.core.axis import round_axis_endpoints
from lcmodel.core.fftpack_compat import (
    cfft_r as cfft_r_compat,
    cfftin_r as cfftin_r_compat,
    csft_r as csft_r_compat,
    csftin_r as csftin_r_compat,
    fftci as fftci_compat,
    seqtot as seqtot_compat,
)
from lcmodel.core.text import int_to_compact_text, split_title_lines
from lcmodel.io.namelist import load_run_config_from_control_file
from lcmodel.io.numeric import (
    load_complex_matrix,
    load_complex_vector,
    load_numeric_matrix,
    load_numeric_vector,
)
from lcmodel.engine import LCModelRunner
from lcmodel.models import RunConfig
from lcmodel.io.pathing import split_output_filename_for_voxel
from lcmodel.pipeline.integration import integrate_peak_with_local_baseline
from lcmodel.pipeline.mydata import MyDataConfig, run_mydata_stage
from lcmodel.pipeline.postprocess import compute_combinations
from lcmodel.pipeline.fitting import FitConfig, run_fit_stage
from lcmodel.pipeline.nonlinear import NonlinearConfig, run_nonlinear_refinement
from lcmodel.pipeline.setup import prepare_fit_inputs
from lcmodel.overrides.state_ops import (
    assign_scalar as _assign_scalar,
    assign_vector as _assign_vector,
    copy_sequence_prefix as _copy_sequence_prefix,
)


# Fortran INITIA/MYCONT entry sequence:
# initialize run state, then apply control-file overrides.
def _ov_initia(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out.setdefault("config", RunConfig())
    out.setdefault("initialized", True)
    out.setdefault("snapshots", {})
    return out

def _ov_mycont(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_initia(state)
    control_file = out.get("control_file")
    if control_file:
        out["config"] = load_run_config_from_control_file(control_file)
    elif isinstance(out.get("config"), RunConfig):
        out["config"] = out["config"]
    else:
        out["config"] = RunConfig()
    return out


# Fortran DATAIN/MYDATA/MYBASI stage loading:
# pull raw and basis arrays into the shared state map.
def _ov_datain(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_mycont(state)
    cfg = out.get("config", RunConfig())
    if not isinstance(cfg, RunConfig):
        cfg = RunConfig()
    if cfg.raw_data_file:
        if cfg.time_domain_input:
            out["datat"] = load_complex_vector(cfg.raw_data_file)
        else:
            out["raw_vector"] = load_numeric_vector(cfg.raw_data_file)
    if cfg.basis_file:
        if cfg.time_domain_input:
            out["basis_time"] = load_complex_matrix(cfg.basis_file, pair_mode=True)
        else:
            out["basis_matrix"] = load_numeric_matrix(cfg.basis_file)
    return out

def _ov_mybasi(lstage: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = lstage
    out = _ov_datain(state)
    out["mybasi_loaded"] = bool(out.get("basis_matrix") or out.get("basis_time"))
    return out

def _ov_setup(lstage: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = lstage
    out = _ov_mybasi(lstage, state)
    cfg = out.get("config", RunConfig())
    if not isinstance(cfg, RunConfig):
        return out
    matrix = out.get("basis_matrix")
    vector = out.get("raw_vector")
    if matrix is None or vector is None:
        return out
    ppm_axis = None
    if cfg.ppm_axis_file:
        ppm_axis = load_numeric_vector(cfg.ppm_axis_file)
    # Fortran SETUP behavior:
    # build active fit window + basis subset before solve.
    setup = prepare_fit_inputs(
        matrix,
        vector,
        ppm_axis=ppm_axis,
        ppm_start=cfg.fit_ppm_start,
        ppm_end=cfg.fit_ppm_end,
        exclude_ppm_ranges=cfg.exclude_ppm_ranges,
        include_metabolites=cfg.include_metabolites,
    )
    out["setup_result"] = setup
    return out

def _ov_setup3(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_setup(3, state)
    out["setup3_done"] = True
    return out

def _ov_startv(ipass: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_setup(1, state)
    out["startv_ipass"] = int(ipass)
    return out

def _ov_ftdata(ishift: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    datat = out.get("datat")
    if datat is None:
        return out
    ft = list(cfft_r_compat(datat))
    shift = int(ishift)
    if shift != 0 and ft:
        # Fortran SHIFTD cyclic indexing around the rearranged frequency axis.
        n = len(ft)
        ft = [ft[(i - shift) % n] for i in range(n)]
    out["dataf"] = tuple(ft)
    out["ftdata_shift"] = shift
    return out

def _ov_shiftd(ishift: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    vector = out.get("raw_vector")
    if vector is None:
        return out
    shift = int(ishift)
    n = len(vector)
    shifted = [0.0] * n
    for i in range(n):
        shifted[i] = float(vector[(i - shift) % n])
    out["raw_vector"] = shifted
    out["shiftd_shift"] = shift
    return out

def _ov_phasta(state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_phase_with_max_real(state)

def _ov_rephas(state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_phase_with_max_real(state)

def _ov_gbackg(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    vec = out.get("raw_vector")
    if vec is None:
        return out
    vals = [float(v) for v in vec]
    n = len(vals)
    # Fortran GBACKG proxy in scaffold mode:
    # keep a lightweight local baseline estimate in state.
    baseline = [0.0] * n
    for i in range(n):
        lo = max(0, i - 2)
        hi = min(n, i + 3)
        window = vals[lo:hi]
        baseline[i] = sum(window) / max(1, len(window))
    out["baseline"] = tuple(baseline)
    return out

def _ov_plinls(istage: int, ierror: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = istage
    out = _ov_setup(2, state)
    setup = out.get("setup_result")
    if setup is None:
        _assign_scalar(ierror, 1)
        return out
    # Fortran PLINLS entry:
    # run constrained linear stage on prepared rows/columns.
    fit = run_fit_stage(setup.matrix, setup.vector, FitConfig())
    out["fit_stage"] = fit
    _assign_scalar(ierror, 0)
    return out

def _ov_solve(
    lstage: int,
    dononl: bool,
    pmqact: float,
    onlyft: bool,
    lerror: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (lstage, pmqact, onlyft)
    out = _ov_setup(2, state)
    setup = out.get("setup_result")
    if setup is None:
        _assign_scalar(lerror, True)
        return out
    # Fortran SOLVE entry:
    # run nonlinear refinement outer-loop + inner linear solve.
    nonlin = run_nonlinear_refinement(
        setup.matrix,
        setup.vector,
        FitConfig(),
        NonlinearConfig(max_iters=2 if bool(dononl) else 1),
    )
    out["nonlinear_result"] = nonlin
    out["fit_stage"] = nonlin.stage
    _assign_scalar(lerror, False)
    return out

def _ov_tworeg(state: dict[str, Any] | None = None) -> dict[str, Any]:
    # Fortran TWOREG convenience wrapper for final regularized stage.
    return _ov_solve(2, True, 0.0, False, [False], state)

def _ov_tworg1(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["tworg1_called"] = True
    return _ov_solve(1, True, 0.0, False, [False], out)

def _ov_tworeg_sav(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    fit = out.get("fit_stage")
    if fit is not None:
        # Fortran SAVBES behavior:
        # keep best-fit snapshot for downstream output tables.
        out.setdefault("snapshots", {})["tworeg"] = fit
    return out

def _ov_tworg2(jpass: int, fixed_degppm_series: bool, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["tworg2_jpass"] = int(jpass)
    out["tworg2_fixed_degppm_series"] = bool(fixed_degppm_series)
    return _ov_solve(2, True, 0.0, False, [False], out)

def _ov_tworg3(jrepha: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["tworg3_jrepha"] = int(jrepha)
    return _ov_rephas(out)

def _ov_fshssq(prej: float, idfish: int, nyuse: int, refndf: float, ssqref: float, lprint: int, rrange: float, state: dict[str, Any] | None = None) -> float:
    _ = (idfish, nyuse, refndf, lprint, rrange, state)
    # Fortran FSHSSQ compatibility:
    # map rejection-probability target to an SSQ threshold surrogate.
    return float(ssqref) * (1.0 + abs(float(prej)))

def _ov_ssrang(irange: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    prmnmx = out.get("prmnmx", ((0.0, 0.1, 0.2), (0.1, 0.2, 0.3)))
    idx = max(0, min(2, int(irange) - 1))
    ssqref = float(out.get("ssqref", 1.0))
    ssqmin = _ov_fshssq(float(prmnmx[0][idx]), 0, 0, 1.0, ssqref, 0, 1e30, out)
    ssqmax = _ov_fshssq(float(prmnmx[1][idx]), 0, 0, 1.0, ssqref, 0, 1e30, out)
    # Fortran SSRANG:
    # keep a bracket [SSQMIN, SSQMAX] and midpoint target SSQAIM.
    out["ssqmin"] = min(ssqmin, ssqmax)
    out["ssqmax"] = max(ssqmin, ssqmax)
    out["ssqaim"] = 0.5 * (out["ssqmin"] + out["ssqmax"])
    return out

def _ov_rfalsi(
    ialpha: int,
    irange: int,
    lrepha: bool,
    alphb: float,
    alphs: float,
    assqlo: float,
    aalplo: float,
    assqhi: float,
    aalphi: float,
    aalpha: Any,
    prejok: Any,
    prej1: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    _ = (ialpha, lrepha, prej1)
    out = _ov_ssrang(irange, state)
    ssq_lo = float(assqlo)
    ssq_hi = float(assqhi)
    alpha_lo = float(aalplo)
    alpha_hi = float(aalphi)
    target = float(out.get("ssqaim", 0.5 * (ssq_lo + ssq_hi)))
    if abs(ssq_hi - ssq_lo) <= 1e-20:
        alpha = float(aalpha[0]) if isinstance(aalpha, MutableSequence) and aalpha else 0.5 * (alpha_lo + alpha_hi)
    else:
        # Fortran RFALSI:
        # regula-falsi interpolation between low/high alpha bounds.
        alpha = alpha_lo + (target - ssq_lo) * (alpha_hi - alpha_lo) / (ssq_hi - ssq_lo)
    alpha = max(min(alpha, max(alpha_lo, alpha_hi)), min(alpha_lo, alpha_hi))
    _assign_scalar(aalpha, alpha)
    _assign_scalar(prejok, True)
    out["alphab"] = float(alphb) * alpha
    out["alphas"] = float(alphs) * alpha
    return out

def _ov_pastep(rstep: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["rstep"] = float(rstep)
    return out

def _ov_penlty(alpb: float, alps: float, sol: Sequence[float], parnl: Sequence[float], state: dict[str, Any] | None = None) -> float:
    _ = state
    s1 = sum(float(v) * float(v) for v in sol)
    s2 = sum(float(v) * float(v) for v in parnl)
    return float(alpb) * s1 + float(alps) * s2

def _ov_savbes(ilevel: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    fit = out.get("fit_stage")
    if fit is not None:
        out.setdefault("snapshots", {})[f"level_{int(ilevel)}"] = fit
    return out

def _ov_dump1(lstage: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out.setdefault("dumps", []).append({"stage": int(lstage), "keys": tuple(sorted(out.keys()))})
    return out

def _ov_restore_settings(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    snap = out.get("snapshots", {}).get("level_2")
    if snap is not None:
        out["fit_stage"] = snap
    return out

def _ov_update_priors(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    fit = out.get("fit_stage")
    if fit is None:
        return out
    coeffs = list(getattr(fit, "coefficients", ()))
    out["prior_mean"] = tuple(coeffs)
    out["prior_sd"] = tuple(max(1e-6, abs(v) * 0.1) for v in coeffs)
    return out

def _ov_set_lshape_false(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["lshape_enabled"] = False
    return out

def _ov_make_cgroup_shift(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    names = tuple(builtins.str(v) for v in out.get("nacomb", ()))
    groups = tuple(builtins.str(v) for v in out.get("chgrsh", ()))
    rows = []
    for g in groups:
        if not g:
            continue
        idx = [j for j, name in enumerate(names) if name.startswith(g)]
        if not idx:
            continue
        for j in idx:
            row = [0.0] * len(names)
            term = 1.0 / float(len(idx))
            for k in idx:
                row[k] = -term
            row[j] += 1.0
            rows.append(tuple(row))
    out["cgroup_shift"] = tuple(rows)
    return out

def _ov_open_output(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_mycont(state)
    cfg = out.get("config", RunConfig())
    if not isinstance(cfg, RunConfig):
        return out
    title = cfg.title or builtins.str(out.get("title", ""))
    row = int(out.get("idrow", 1))
    col = int(out.get("idcol", 1))
    slc = int(out.get("idslic", 1))
    if int(out.get("single_voxel", 1)) == 0:
        title = f"Slice#{slc} Row#{row} Col#{col}  {title}"
    out["title"] = title
    out["output_opened"] = True
    return out

def _ov_loadch(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    control_file = out.get("control_file")
    if control_file:
        text = pathlib.Path(control_file).read_text(encoding="utf-8", errors="replace")
        out["changes"] = tuple(line.rstrip() for line in text.splitlines())
    else:
        out["changes"] = ()
    return out

def _ov_finout(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    fit = out.get("fit_stage")
    if fit is not None:
        out["final_summary"] = {
            "residual_norm": float(getattr(fit, "residual_norm", 0.0)),
            "iterations": int(getattr(fit, "iterations", 0)),
        }
    return out

def _ov_errtbl(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    out["error_table"] = tuple(out.get("errors", ()))
    return out

def _ov_exitps(lstop: bool, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if bool(lstop):
        _ov_endps(out)
    out["exitps_stop"] = bool(lstop)
    return out

def _ov_ecc_truncate(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    h2ot = out.get("h2ot")
    datat = out.get("datat")
    if not isinstance(h2ot, Sequence) or not isinstance(datat, MutableSequence):
        return out
    n = min(len(h2ot), len(datat))
    for i in range(n):
        hv = complex(h2ot[i])
        dv = complex(datat[i])
        denom = (hv.real * hv.real + hv.imag * hv.imag) ** 0.5
        if denom > 0.0:
            corr = complex(hv.real, -hv.imag) / denom
            datat[i] = dv * corr
    out["ecc_done"] = True
    return out

def _ov_f2tcb(n: int, c: Sequence[complex], yout: Any, wsave: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = (wsave, state)
    vals = cfftin_r_compat(c[: int(n)])
    _copy_sequence_prefix(yout, vals)
    return {"f2tcb": tuple(vals)}

def _ov_dpasf(
    nac: int,
    ido: int,
    ip: int,
    l1: int,
    idl1: int,
    cc: Any,
    c1: Any,
    c2: Any,
    ch: Any,
    ch2: Any,
    wa: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_passf(nac, ido, ip, l1, idl1, cc, c1, c2, ch, ch2, wa, state)

def _ov_dpasf2(ido: int, l1: int, cc: Any, ch: Any, wa1: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_passf2(ido, l1, cc, ch, wa1, state)

def _ov_dpasf3(ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_passf3(ido, l1, cc, ch, wa1, wa2, state)

def _ov_dpasf4(ido: int, l1: int, cc: Any, ch: Any, wa1: Any, wa2: Any, wa3: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    return _ov_passf4(ido, l1, cc, ch, wa1, wa2, wa3, state)

def _ov_dpasf5(
    ido: int,
    l1: int,
    cc: Any,
    ch: Any,
    wa1: Any,
    wa2: Any,
    wa3: Any,
    wa4: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_passf5(ido, l1, cc, ch, wa1, wa2, wa3, wa4, state)

def _ov_arbbox(n: int, a: Any, amn: float, amx: float, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if isinstance(a, MutableSequence):
        for i in range(min(int(n), len(a))):
            a[i] = max(float(amn), min(float(amx), float(a[i])))
    out["arbbox_bounds"] = (float(amn), float(amx))
    return out

def _ov_lcmodl(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = _ov_mycont(state)
    cfg = out.get("config", RunConfig())
    if not isinstance(cfg, RunConfig):
        cfg = RunConfig()
    runner = LCModelRunner(cfg)
    if cfg.raw_data_list_file:
        batch = runner.run_batch()
        out["batch_result"] = batch
    else:
        result = runner.run()
        out["run_result"] = result
        if result.fit_result is not None:
            out["fit_stage"] = result.fit_result
    return out

def _ov_split_filename(
    filename: str,
    chtype1: str,
    chtype2: str,
    chtype3: str,
    lchtype: int,
    split: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    left, right = split_output_filename_for_voxel(
        str(filename),
        (str(chtype1)[: int(lchtype)], str(chtype2)[: int(lchtype)], str(chtype3)[: int(lchtype)]),
    )
    if isinstance(split, MutableSequence) and len(split) >= 2:
        split[0] = left
        split[1] = right
    out["split"] = (left, right)
    return out

def _ov_chstrip_int6(
    iarg: int, chi: Any, leni: Any, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    text = int_to_compact_text(int(iarg))
    if isinstance(chi, MutableSequence) and len(chi) >= 1:
        chi[0] = text
    if isinstance(leni, MutableSequence) and len(leni) >= 1:
        leni[0] = len(text)
    out["chi"] = text
    out["leni"] = len(text)
    return out

def _ov_split_title(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    title = str(out.get("title", ""))
    ntitle = int(out.get("ntitle", 2))
    layout = split_title_lines(title, ntitle=ntitle)
    out["title_line_1"] = layout.lines[0]
    out["title_line_2"] = layout.lines[1]
    out["nlines_title"] = layout.line_count
    return out

def _ov_revers(x: Any, n: int, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    if isinstance(x, MutableSequence):
        reverse_first_n(x, int(n))
    out["reversed_n"] = int(n)
    return out

def _ov_endrnd(
    xmn: float,
    xmx: float,
    xstep: float,
    xinc: float,
    xmnrnd: Any,
    xmxrnd: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    x_low, x_high = round_axis_endpoints(float(xmn), float(xmx), float(xstep), float(xinc))
    if isinstance(xmnrnd, MutableSequence) and len(xmnrnd) >= 1:
        xmnrnd[0] = x_low
    if isinstance(xmxrnd, MutableSequence) and len(xmxrnd) >= 1:
        xmxrnd[0] = x_high
    out["xmnrnd"] = x_low
    out["xmxrnd"] = x_high
    return out

def _ov_integrate(
    dataf: Sequence[complex | float],
    ppminc2: float,
    rinteg: Any,
    kyend: int,
    kystrt: int,
    ly: int,
    nunfil: int,
    nwndo: int,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    values = [float(v.real) if isinstance(v, complex) else float(v) for v in dataf]
    if not values:
        out["rinteg"] = 0.0
        return out
    start = max(0, int(kystrt) - 1)
    end = min(len(values) - 1, int(kyend) - 1)
    peak = min(max(0, int(ly) - 1), len(values) - 1)
    border = max(1, int(nwndo))
    spacing = abs(float(ppminc2)) if float(ppminc2) != 0.0 else 1.0
    # Fortran INTEGRATE:
    # compute peak area after local two-sided baseline correction.
    result = integrate_peak_with_local_baseline(
        values,
        peak_index=peak,
        start_index=start,
        end_index=end,
        border_width=border,
        spacing=spacing,
    )
    if isinstance(rinteg, MutableSequence) and len(rinteg) >= 1:
        rinteg[0] = float(result.area)
    out["rinteg"] = float(result.area)
    out["nunfil"] = int(nunfil)
    return out

def _ov_combis(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    expressions = tuple(str(x) for x in out.get("combine_expressions", ()))
    coeffs = tuple(float(x) for x in out.get("coefficients", ()))
    sds = tuple(float(x) for x in out.get("coefficient_sds", ()))
    names = tuple(str(x) for x in out.get("metabolite_names", ()))
    out["combined"] = compute_combinations(expressions, coeffs, sds, names)
    return out

def _ov_mydata(state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    raw_time = out.get("raw_time")
    if raw_time is None:
        return out
    # Fortran MYDATA bridge:
    # keep override entrypoint wired to Python-first preprocessing stage.
    stage = run_mydata_stage(
        raw_time,
        MyDataConfig(
            compute_fft=bool(out.get("compute_fft", True)),
            auto_phase_zero_order=bool(out.get("auto_phase_zero_order", False)),
            auto_phase_first_order=bool(out.get("auto_phase_first_order", False)),
            phase_objective=str(out.get("phase_objective", "imag_abs")),
            phase_smoothness_power=int(out.get("phase_smoothness_power", 6)),
            dwell_time_s=float(out.get("dwell_time_s", 0.0)),
            line_broadening_hz=float(out.get("line_broadening_hz", 0.0)),
        ),
    )
    out["mydata_stage"] = stage
    if stage.frequency_domain is not None:
        out["dataf"] = stage.frequency_domain
    return out

def _ov_csft_r(
    datat: Sequence[complex], ft: Any, ncap: int, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = csft_r_compat(datat, ncap=ncap)
    _assign_vector(ft, vals)
    out["ft"] = tuple(vals)
    return out

def _ov_csftin_r(
    ft: Sequence[complex],
    ftwork: Any,
    ftinv: Any,
    ncap: int,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = csftin_r_compat(ft, ncap=ncap)
    _assign_vector(ftinv, vals)
    out["ftinv"] = tuple(vals)
    return out

def _ov_seqtot(
    datat: Sequence[complex],
    dataf: Any,
    nunfil: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = seqtot_compat(datat)
    _assign_vector(dataf, vals)
    out["dataf"] = tuple(vals)
    out["nunfil"] = int(nunfil)
    out["lwfft"] = int(lwfft)
    return out

def _ov_cfftin(
    ft: Sequence[complex],
    ftinv: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = cfftin_r_compat(ft)
    _assign_vector(ftinv, vals)
    out["ftinv"] = tuple(vals)
    out["n"] = int(n)
    return out

def _ov_cfftin_r(
    ft: Sequence[complex],
    ftwork: Any,
    ftinv: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_cfftin(ft, ftinv, n, lwfft, wfftc, state)

def _ov_cfft(
    datat: Sequence[complex],
    ft: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = state if state is not None else {}
    vals = cfft_r_compat(datat)
    _assign_vector(ft, vals)
    out["ft"] = tuple(vals)
    out["n"] = int(n)
    return out

def _ov_cfft_r(
    datat: Sequence[complex],
    ft: Any,
    n: int,
    lwfft: int,
    wfftc: Any,
    state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return _ov_cfft(datat, ft, n, lwfft, wfftc, state)

def _ov_fftci(n: int, wsave: Any, state: dict[str, Any] | None = None) -> dict[str, Any]:
    out = state if state is not None else {}
    plan = fftci_compat(int(n))
    out["fft_plan"] = plan
    out["n"] = int(n)
    if isinstance(wsave, MutableSequence) and len(wsave) >= 1:
        wsave[0] = complex(1.0, 0.0)
    return out


WORKFLOW_OVERRIDES = {
    "lcmodl": _ov_lcmodl,
    "mycont": _ov_mycont,
    "restore_settings": _ov_restore_settings,
    "update_priors": _ov_update_priors,
    "open_output": _ov_open_output,
    "loadch": _ov_loadch,
    "initia": _ov_initia,
    "datain": _ov_datain,
    "ecc_truncate": _ov_ecc_truncate,
    "mybasi": _ov_mybasi,
    "make_cgroup_shift": _ov_make_cgroup_shift,
    "set_lshape_false": _ov_set_lshape_false,
    "startv": _ov_startv,
    "ftdata": _ov_ftdata,
    "shiftd": _ov_shiftd,
    "setup": _ov_setup,
    "setup3": _ov_setup3,
    "phasta": _ov_phasta,
    "gbackg": _ov_gbackg,
    "tworeg": _ov_tworeg,
    "tworg1": _ov_tworg1,
    "tworeg_sav": _ov_tworeg_sav,
    "tworg2": _ov_tworg2,
    "tworg3": _ov_tworg3,
    "ssrang": _ov_ssrang,
    "rfalsi": _ov_rfalsi,
    "penlty": _ov_penlty,
    "rephas": _ov_rephas,
    "fshssq": _ov_fshssq,
    "plinls": _ov_plinls,
    "dump1": _ov_dump1,
    "pastep": _ov_pastep,
    "solve": _ov_solve,
    "savbes": _ov_savbes,
    "finout": _ov_finout,
    "exitps": _ov_exitps,
    "errtbl": _ov_errtbl,
    "arbbox": _ov_arbbox,
    "dpasf": _ov_dpasf,
    "dpasf2": _ov_dpasf2,
    "dpasf3": _ov_dpasf3,
    "dpasf4": _ov_dpasf4,
    "dpasf5": _ov_dpasf5,
    "f2tcb": _ov_f2tcb,
    "split_filename": _ov_split_filename,
    "chstrip_int6": _ov_chstrip_int6,
    "split_title": _ov_split_title,
    "revers": _ov_revers,
    "endrnd": _ov_endrnd,
    "integrate": _ov_integrate,
    "combis": _ov_combis,
    "mydata": _ov_mydata,
    "csft_r": _ov_csft_r,
    "csftin_r": _ov_csftin_r,
    "seqtot": _ov_seqtot,
    "cfftin": _ov_cfftin,
    "cfftin_r": _ov_cfftin_r,
    "cfft": _ov_cfft,
    "cfft_r": _ov_cfft_r,
    "fftci": _ov_fftci,
    "dfftci": _ov_fftci,
}


__all__ = ["WORKFLOW_OVERRIDES"]
