#!/usr/bin/env python3
"""Run the complete fail-closed OpenSpec planning gate."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from validate_requirements import format_traceability_matrix, validate_change


def resolve_openspec_executable(platform_name: str | None = None, finder=None) -> str | None:
    host = platform_name or os.name
    find = finder or shutil.which
    candidates = ("openspec.cmd", "openspec") if host == "nt" else ("openspec",)
    return next((executable for candidate in candidates if (executable := find(candidate))), None)


def run_gate(repo: Path, change: str) -> int:
    repo = repo.resolve()
    change_dir = repo / "openspec" / "changes" / change
    executable = resolve_openspec_executable()
    if executable is None:
        print("ERROR: OpenSpec CLI was not found", file=sys.stderr)
        return 2

    native = subprocess.run(
        [
            executable,
            "validate",
            change,
            "--type",
            "change",
            "--strict",
            "--no-interactive",
        ],
        cwd=repo,
        check=False,
    )
    if native.returncode != 0:
        print("ERROR: native OpenSpec strict validation failed", file=sys.stderr)
        return 2

    errors = validate_change(change_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print("OpenSpec complete planning gate: PASS")
    matrix = format_traceability_matrix(change_dir)
    if matrix:
        print(matrix)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--change", required=True)
    args = parser.parse_args(argv)
    return run_gate(args.repo, args.change)


if __name__ == "__main__":
    raise SystemExit(main())
