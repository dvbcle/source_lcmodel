"""Report writers for user-facing fit outputs."""

from __future__ import annotations

from pathlib import Path

from lcmodel.models import FitResult


def build_fit_table_text(fit: FitResult) -> str:
    """Create a tab-delimited fit summary table."""

    lines = ["Metabolite\tCoefficient\tSD\t%SD"]
    names = fit.metabolite_names or tuple(f"basis_{i+1}" for i in range(len(fit.coefficients)))
    sds = fit.coefficient_sds or tuple(0.0 for _ in fit.coefficients)
    for idx, coeff in enumerate(fit.coefficients):
        name = names[idx] if idx < len(names) else f"basis_{idx+1}"
        sd = sds[idx] if idx < len(sds) else 0.0
        if abs(coeff) > 0:
            psd = abs(sd / coeff) * 100.0
        else:
            psd = 0.0
        lines.append(f"{name}\t{coeff:.12g}\t{sd:.12g}\t{psd:.6g}")

    if fit.combined:
        lines.append("")
        lines.append("Combined\tCoefficient\tSD\t%SD")
        for name, coeff, sd in fit.combined:
            psd = abs(sd / coeff) * 100.0 if abs(coeff) > 0 else 0.0
            lines.append(f"{name}\t{coeff:.12g}\t{sd:.12g}\t{psd:.6g}")

    lines.append("")
    lines.append(f"# method={fit.method}")
    lines.append(f"# iterations={fit.iterations}")
    lines.append(f"# residual_norm={fit.residual_norm:.12g}")
    lines.append(f"# data_points_used={fit.data_points_used}")
    return "\n".join(lines) + "\n"


def write_fit_table(path: str | Path, fit: FitResult) -> str:
    """Write fit summary table and return written path string."""

    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(build_fit_table_text(fit), encoding="utf-8")
    return str(out_path)
