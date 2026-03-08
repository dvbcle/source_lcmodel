"""Legacy SPTYPE preset mappings from MYCONT/include behavior."""

from __future__ import annotations

from dataclasses import dataclass, replace

from lcmodel.models import RunConfig


@dataclass(frozen=True)
class SptypePreset:
    fit_ppm_start: float | None = None
    fit_ppm_end: float | None = None
    combine_expressions: tuple[str, ...] = ()
    exclude_ppm_ranges: tuple[tuple[float, float], ...] = ()
    include_metabolites: tuple[str, ...] = ()


_LIVER_BASE_COMBOS: tuple[str, ...] = (
    "L20a+L20b+L20c+L20d+L20e+L20f+L13a+L13b+L13c+L13d+L13e+L13f+L13g+L13h+L13i+L13j+L09a+L09b+L09c+L09d+L09e+L09f+L09g",
    "L13j+L13i+L13h+L09g+L13g+L09f+L13f+L09e+L13e+L09d+L13d+L09c+L13c+L09b+L13b+L09a+L13a",
    "L13j+L13i+L13h+L13g+L13f+L13e+L13d+L13c+L13b+L13a",
    "L09g+L09f+L09e+L09d+L09c+L09b+L09a",
    "L20f+L20e+L20d+L20c+L20b+L20a",
    "L53f+L53e+L53d+L53c+L53b+L53a",
    "W11+W10+W9+W8+L53f+W7+L53e+W6+L53d+W5+L53c+W4+L53b+W3+L53a+W2+W1",
    "W11+W10+W9+W8+W7+W6+W5+W4+W3+W2+W1",
    "cho1+cho2+cho3+cho4+cho5+cho6",
    "glycg1+glycg2+glycg3+glycg4+glycg5+glycg6+glycg7",
)

_MUSCLE_BASE_COMBOS: tuple[str, ...] = (
    "I13d+I13c+I13b+I13a",
    "E15d+E15c+E15b+E15a",
    "Cr2+Cr1",
    "tau5+tau4+tau3+tau2+tau1",
    "cho4+cho3+cho2+cho1",
    "cr28e+cr28d+cr28c+cr28b+cr28a",
    "I09",
    "E11",
    "I21",
    "E23",
)


_PRESETS: dict[str, SptypePreset] = {
    "version5": SptypePreset(fit_ppm_start=3.85, fit_ppm_end=1.0),
    "version-5": SptypePreset(fit_ppm_start=3.85, fit_ppm_end=1.0),
    "tumor": SptypePreset(
        fit_ppm_start=4.0,
        fit_ppm_end=0.2,
        include_metabolites=("GPC", "Cr"),
    ),
    "nulled": SptypePreset(fit_ppm_start=4.0, fit_ppm_end=0.2),
    "csf": SptypePreset(fit_ppm_start=4.0, fit_ppm_end=0.2),
    "only-cho-1": SptypePreset(fit_ppm_start=3.8, fit_ppm_end=2.7),
    "only-cho-2": SptypePreset(fit_ppm_start=3.8, fit_ppm_end=2.7),
}

for idx in range(1, 12):
    _PRESETS[f"liver-{idx}"] = SptypePreset(
        fit_ppm_start=4.2,
        fit_ppm_end=-2.0,
        combine_expressions=_LIVER_BASE_COMBOS,
    )
for idx in range(1, 11):
    _PRESETS[f"breast-{idx}"] = SptypePreset(
        fit_ppm_start=3.8 if idx >= 2 else 4.0,
        fit_ppm_end=-2.0,
        combine_expressions=_LIVER_BASE_COMBOS,
    )
for idx in range(1, 11):
    if idx == 1:
        start = 3.4
    elif idx in {2, 3}:
        start = 3.6
    else:
        start = 3.8
    _PRESETS[f"lipid-{idx}"] = SptypePreset(
        fit_ppm_start=start,
        fit_ppm_end=-2.0,
        combine_expressions=_LIVER_BASE_COMBOS,
    )
for idx in range(1, 6):
    _PRESETS[f"muscle-{idx}"] = SptypePreset(
        fit_ppm_start=3.8,
        fit_ppm_end=-1.0,
        combine_expressions=_MUSCLE_BASE_COMBOS,
    )
for idx in range(1, 4):
    _PRESETS[f"mega-press-{idx}"] = SptypePreset(fit_ppm_start=4.0, fit_ppm_end=0.2)
for code in "abcdefghi":
    _PRESETS[f"prostate-{code}"] = SptypePreset(fit_ppm_start=4.2, fit_ppm_end=0.2)


def apply_sptype_preset(config: RunConfig) -> RunConfig:
    """Apply legacy SPTYPE defaults where explicit config values are absent."""

    key = config.sptype.strip().lower()
    if not key:
        return config
    preset = _PRESETS.get(key)
    if preset is None:
        return config

    fit_ppm_start = config.fit_ppm_start
    fit_ppm_end = config.fit_ppm_end
    combine_expressions = config.combine_expressions
    exclude_ppm_ranges = config.exclude_ppm_ranges
    include_metabolites = config.include_metabolites

    if fit_ppm_start is None and preset.fit_ppm_start is not None:
        fit_ppm_start = preset.fit_ppm_start
    if fit_ppm_end is None and preset.fit_ppm_end is not None:
        fit_ppm_end = preset.fit_ppm_end
    if not combine_expressions and preset.combine_expressions:
        combine_expressions = preset.combine_expressions
    if not exclude_ppm_ranges and preset.exclude_ppm_ranges:
        exclude_ppm_ranges = preset.exclude_ppm_ranges
    if not include_metabolites and preset.include_metabolites:
        include_metabolites = preset.include_metabolites

    return replace(
        config,
        fit_ppm_start=fit_ppm_start,
        fit_ppm_end=fit_ppm_end,
        combine_expressions=combine_expressions,
        exclude_ppm_ranges=exclude_ppm_ranges,
        include_metabolites=include_metabolites,
    )


def validate_sptype_config(config: RunConfig) -> None:
    """Validate Fortran-style SPTYPE constraints for selected ppm limits."""

    key = config.sptype.strip().lower()
    if not key:
        return

    start = config.fit_ppm_start
    end = config.fit_ppm_end

    if key.startswith(("muscle-", "liver-", "breast-", "lipid-")):
        if end is None or end >= -0.9:
            raise ValueError(
                f"SPTYPE '{config.sptype}' requires fit_ppm_end < -0.9 (got {end!r})."
            )
        if start is not None:
            if start >= 5.0:
                if start <= 7.9:
                    raise ValueError(
                        f"SPTYPE '{config.sptype}' with fit_ppm_start >= 5.0 "
                        "requires fit_ppm_start > 7.9."
                    )
            elif key.startswith("liver-") and (start >= 4.01 or start <= 3.59):
                raise ValueError(
                    f"SPTYPE '{config.sptype}' requires 3.59 < fit_ppm_start < 4.01."
                )
            elif key.startswith("breast-") and (start <= 3.79 or start >= 4.01):
                raise ValueError(
                    f"SPTYPE '{config.sptype}' requires 3.79 < fit_ppm_start < 4.01."
                )
            elif key.startswith("lipid-") and (start <= 3.39 or start >= 4.01):
                raise ValueError(
                    f"SPTYPE '{config.sptype}' requires 3.39 < fit_ppm_start < 4.01."
                )

    if key in {"only-cho-1", "only-cho-2"}:
        if (
            start is None
            or end is None
            or start <= 3.79
            or start >= 4.01
            or end >= 2.81
            or end <= 2.59
        ):
            raise ValueError(
                f"SPTYPE '{config.sptype}' requires 3.79 < fit_ppm_start < 4.01 "
                "and 2.59 < fit_ppm_end < 2.81."
            )
