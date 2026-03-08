"""Run external regression in an isolated working directory.

This runner enforces clean test hygiene:
- copies fixture inputs into a brand-new timestamped directory
- validates input fixture shape to detect stale mixed artifacts
- checks that no pre-existing generated files are present before execution
- records pre/post file inventories and SHA256 hashes
- flags unexpected new files or modified pre-existing inputs
- runs Python LCModel once and compares `out.ps` vs `out_ref_build.ps`
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable


DEFAULT_EXPECTED_INPUT_FILES = frozenset(
    {"control.file", "data.raw", "3t.basis", "out_ref_build.ps"}
)
DEFAULT_ALLOWED_GENERATED_FILES = frozenset({"out.ps", "python_run.log"})
GUARD_GENERATED_FILES = frozenset({"out.ps", "python_run.log", "run_summary.txt"})


@dataclass(frozen=True)
class RunSummary:
    run_dir: Path
    python_returncode: int
    out_exists: bool
    ref_exists: bool
    byte_match: bool
    out_sha256: str
    ref_sha256: str
    hygiene_ok: bool
    hygiene_issues: tuple[str, ...]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def _copy_fixture(fixture_dir: Path, run_dir: Path) -> None:
    if not fixture_dir.exists():
        raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")
    run_dir.mkdir(parents=True, exist_ok=False)
    for src in fixture_dir.iterdir():
        dst = run_dir / src.name
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def _list_files(path: Path) -> list[str]:
    return sorted(p.name for p in path.iterdir())


def _file_hashes(path: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for entry in path.iterdir():
        if entry.is_file():
            hashes[entry.name] = _sha256(entry)
    return hashes


def _validate_fixture_shape(
    fixture_dir: Path,
    *,
    strict_input_set: bool,
    expected_inputs: set[str],
) -> None:
    fixture_files = set(_list_files(fixture_dir))
    stale_generated = sorted(fixture_files.intersection(GUARD_GENERATED_FILES))
    if stale_generated:
        joined = ",".join(stale_generated)
        raise RuntimeError(
            f"Fixture contains stale generated files and is not clean: {joined}"
        )
    if strict_input_set and fixture_files != expected_inputs:
        missing = sorted(expected_inputs - fixture_files)
        extra = sorted(fixture_files - expected_inputs)
        raise RuntimeError(
            "Fixture file set mismatch under strict mode: "
            f"missing={','.join(missing) or '-'} extra={','.join(extra) or '-'}"
        )


def run_clean_regression(
    fixture_dir: Path,
    root_dir: Path,
    out_base: Path,
    *,
    strict_input_set: bool = True,
    expected_inputs: Iterable[str] = DEFAULT_EXPECTED_INPUT_FILES,
    allowed_generated_files: Iterable[str] = DEFAULT_ALLOWED_GENERATED_FILES,
) -> RunSummary:
    expected_input_set = {name.strip() for name in expected_inputs if name.strip()}
    allowed_generated_set = {
        name.strip() for name in allowed_generated_files if name.strip()
    }
    _validate_fixture_shape(
        fixture_dir,
        strict_input_set=strict_input_set,
        expected_inputs=expected_input_set,
    )

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    run_dir = out_base / f"external_regression_clean_{ts}"
    _copy_fixture(fixture_dir, run_dir)

    pre_files = set(_list_files(run_dir))
    pre_hashes = _file_hashes(run_dir)
    if (run_dir / "out.ps").exists():
        raise RuntimeError("Fixture copy unexpectedly contains out.ps before run")

    log_file = run_dir / "python_run.log"
    env = dict(**os.environ)
    env["PYTHONPATH"] = str(root_dir)
    with log_file.open("w", encoding="utf-8") as f:
        proc = subprocess.run(
            [sys.executable, "-m", "lcmodel", "--control-file", "control.file"],
            cwd=run_dir,
            stdout=f,
            stderr=subprocess.STDOUT,
            env=env,
            check=False,
        )

    out_ps = run_dir / "out.ps"
    ref_ps = run_dir / "out_ref_build.ps"
    out_exists = out_ps.exists()
    ref_exists = ref_ps.exists()
    byte_match = False
    out_hash = ""
    ref_hash = ""
    if out_exists:
        out_hash = _sha256(out_ps)
    if ref_exists:
        ref_hash = _sha256(ref_ps)
    if out_exists and ref_exists:
        byte_match = out_ps.read_bytes() == ref_ps.read_bytes()

    post_files = set(_list_files(run_dir))
    post_hashes = _file_hashes(run_dir)
    added_files = sorted(post_files - pre_files)
    removed_files = sorted(pre_files - post_files)
    modified_preexisting = sorted(
        name
        for name in pre_files.intersection(post_files)
        if pre_hashes.get(name) != post_hashes.get(name)
    )
    expected_new = set(allowed_generated_set)
    unexpected_new = sorted(set(added_files) - expected_new)
    missing_expected_new = sorted(expected_new - set(added_files))
    hygiene_issues = []
    if unexpected_new:
        hygiene_issues.append("unexpected_new_files=" + ",".join(unexpected_new))
    if removed_files:
        hygiene_issues.append("removed_input_files=" + ",".join(removed_files))
    if modified_preexisting:
        hygiene_issues.append(
            "modified_preexisting_files=" + ",".join(modified_preexisting)
        )
    if missing_expected_new:
        hygiene_issues.append(
            "missing_expected_generated_files=" + ",".join(missing_expected_new)
        )
    hygiene_ok = not hygiene_issues

    summary_txt = run_dir / "run_summary.txt"
    summary_txt.write_text(
        "\n".join(
            [
                f"timestamp={datetime.now().isoformat(timespec='seconds')}",
                f"fixture_dir={fixture_dir}",
                f"run_dir={run_dir}",
                f"python_returncode={proc.returncode}",
                f"out_exists={out_exists}",
                f"ref_exists={ref_exists}",
                f"byte_match={byte_match}",
                f"out_sha256={out_hash}",
                f"ref_sha256={ref_hash}",
                f"hygiene_ok={hygiene_ok}",
                "hygiene_issues=" + (";".join(hygiene_issues) if hygiene_issues else "-"),
                "pre_files=" + ",".join(sorted(pre_files)),
                "post_files=" + ",".join(sorted(post_files)),
                "added_files=" + ",".join(added_files),
                "removed_files=" + ",".join(removed_files),
                "modified_preexisting_files=" + ",".join(modified_preexisting),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return RunSummary(
        run_dir=run_dir,
        python_returncode=proc.returncode,
        out_exists=out_exists,
        ref_exists=ref_exists,
        byte_match=byte_match,
        out_sha256=out_hash,
        ref_sha256=ref_hash,
        hygiene_ok=hygiene_ok,
        hygiene_issues=tuple(hygiene_issues),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run clean external regression in isolated directory.")
    parser.add_argument(
        "--fixture-dir",
        default=".tmp_upstream_lcmodel/test_lcm",
        help="Path to external fixture directory (default: .tmp_upstream_lcmodel/test_lcm).",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Directory where isolated run folders are created (default: artifacts).",
    )
    parser.add_argument(
        "--no-strict-input-set",
        action="store_true",
        help=(
            "Disable strict fixture-set validation. By default the runner expects only "
            "control.file,data.raw,3t.basis,out_ref_build.ps in fixture input."
        ),
    )
    parser.add_argument(
        "--expected-input",
        action="append",
        default=None,
        help=(
            "Expected fixture filename. Repeat to customize strict fixture-set validation. "
            "Only used when strict mode is active."
        ),
    )
    parser.add_argument(
        "--allow-generated",
        action="append",
        default=None,
        help=(
            "Allowed generated filename in run directory. Repeat to extend expected outputs "
            "(default: out.ps, python_run.log)."
        ),
    )
    args = parser.parse_args(argv)

    root = Path.cwd()
    fixture = (root / args.fixture_dir).resolve()
    artifacts = (root / args.artifacts_dir).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)
    strict_input_set = not args.no_strict_input_set
    expected_inputs = (
        set(args.expected_input) if args.expected_input else set(DEFAULT_EXPECTED_INPUT_FILES)
    )
    allowed_generated = (
        set(args.allow_generated)
        if args.allow_generated
        else set(DEFAULT_ALLOWED_GENERATED_FILES)
    )

    summary = run_clean_regression(
        fixture,
        root,
        artifacts,
        strict_input_set=strict_input_set,
        expected_inputs=expected_inputs,
        allowed_generated_files=allowed_generated,
    )
    print(f"run_dir={summary.run_dir}")
    print(f"python_returncode={summary.python_returncode}")
    print(f"out_exists={summary.out_exists}")
    print(f"ref_exists={summary.ref_exists}")
    print(f"byte_match={summary.byte_match}")
    print(f"out_sha256={summary.out_sha256}")
    print(f"ref_sha256={summary.ref_sha256}")
    print(f"hygiene_ok={summary.hygiene_ok}")
    print(
        "hygiene_issues="
        + (";".join(summary.hygiene_issues) if summary.hygiene_issues else "-")
    )

    if summary.python_returncode != 0:
        return summary.python_returncode
    if not summary.hygiene_ok:
        return 4
    if not summary.out_exists or not summary.ref_exists:
        return 3
    if not summary.byte_match:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
