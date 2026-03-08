"""Run external regression in an isolated working directory.

This runner enforces clean test hygiene:
- copies fixture inputs into a brand-new timestamped directory
- checks that no pre-existing `out.ps` is present before execution
- records pre/post file inventories and SHA256 hashes
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


@dataclass(frozen=True)
class RunSummary:
    run_dir: Path
    python_returncode: int
    out_exists: bool
    ref_exists: bool
    byte_match: bool
    out_sha256: str
    ref_sha256: str


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


def run_clean_regression(fixture_dir: Path, root_dir: Path, out_base: Path) -> RunSummary:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_base / f"external_regression_clean_{ts}"
    _copy_fixture(fixture_dir, run_dir)

    pre_files = _list_files(run_dir)
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

    post_files = _list_files(run_dir)
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
                "pre_files=" + ",".join(pre_files),
                "post_files=" + ",".join(post_files),
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
    args = parser.parse_args(argv)

    root = Path.cwd()
    fixture = (root / args.fixture_dir).resolve()
    artifacts = (root / args.artifacts_dir).resolve()
    artifacts.mkdir(parents=True, exist_ok=True)

    summary = run_clean_regression(fixture, root, artifacts)
    print(f"run_dir={summary.run_dir}")
    print(f"python_returncode={summary.python_returncode}")
    print(f"out_exists={summary.out_exists}")
    print(f"ref_exists={summary.ref_exists}")
    print(f"byte_match={summary.byte_match}")
    print(f"out_sha256={summary.out_sha256}")
    print(f"ref_sha256={summary.ref_sha256}")

    if summary.python_returncode != 0:
        return summary.python_returncode
    if not summary.out_exists or not summary.ref_exists:
        return 3
    if not summary.byte_match:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
