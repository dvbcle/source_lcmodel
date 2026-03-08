"""Load and validate Fortran-to-Python traceability manifest artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import importlib
import json
import re


HEADER_RE = re.compile(
    r"^\s*(?:(REAL|INTEGER|LOGICAL|COMPLEX|DOUBLE\s+PRECISION|CHARACTER(?:\*\d+)?)\s+)?"
    r"(PROGRAM|SUBROUTINE|FUNCTION|BLOCK\s+DATA)(?:\s+([A-Za-z_][\w$]*))?",
    flags=re.IGNORECASE,
)


def sanitize_name(name: str) -> str:
    out = re.sub(r"[^0-9a-zA-Z_]", "_", name.strip()).lower()
    if not out:
        out = "unnamed"
    if out[0].isdigit():
        out = f"n_{out}"
    return out


def discover_fortran_units(source_file: str | Path) -> set[str]:
    path = Path(source_file)
    out: set[str] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = HEADER_RE.match(line)
        if not m:
            continue
        raw_name = (m.group(3) or "").strip()
        if not raw_name:
            continue
        out.add(sanitize_name(raw_name))
    return out


def default_manifest_path() -> Path:
    return Path(__file__).resolve().parent / "fortran_routine_manifest.json"


def load_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path) if path is not None else default_manifest_path()
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def import_target(target: str) -> Any:
    module_path, _, attr_path = target.rpartition(".")
    if not module_path or not attr_path:
        raise ValueError(f"invalid target path '{target}'")
    module = importlib.import_module(module_path)
    value: Any = module
    value = getattr(value, attr_path)
    return value


@dataclass(frozen=True)
class ManifestAudit:
    fortran_units: int
    manifest_entries: int
    missing_fortran_units: tuple[str, ...]
    unmapped_entries: tuple[str, ...]
    placeholder_entries: tuple[str, ...]
    import_failures: tuple[str, ...]


def audit_manifest(
    *,
    fortran_source: str | Path,
    manifest: dict[str, Any],
    check_imports: bool = True,
) -> ManifestAudit:
    units = discover_fortran_units(fortran_source)
    entries = manifest.get("entries", [])
    by_name = {
        str(item.get("fortran_name", "")).strip().lower(): item for item in entries if isinstance(item, dict)
    }

    missing = sorted(name for name in units if name not in by_name)
    unmapped: list[str] = []
    placeholder: list[str] = []
    import_failures: list[str] = []

    for name in sorted(units):
        item = by_name.get(name, {})
        target = str(item.get("python_target", "")).strip()
        kind = str(item.get("python_target_kind", "")).strip().lower()
        if not target:
            unmapped.append(name)
            continue
        if kind == "placeholder":
            placeholder.append(name)
        if check_imports:
            try:
                import_target(target)
            except Exception:
                import_failures.append(name)

    return ManifestAudit(
        fortran_units=len(units),
        manifest_entries=len(entries),
        missing_fortran_units=tuple(missing),
        unmapped_entries=tuple(unmapped),
        placeholder_entries=tuple(placeholder),
        import_failures=tuple(sorted(set(import_failures))),
    )


__all__ = [
    "ManifestAudit",
    "audit_manifest",
    "default_manifest_path",
    "discover_fortran_units",
    "import_target",
    "load_manifest",
    "sanitize_name",
]
