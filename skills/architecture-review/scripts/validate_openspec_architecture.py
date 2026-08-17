#!/usr/bin/env python3
"""Fail closed on incomplete OpenSpec architecture planning contracts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CONTRACT_MARKER = "<!-- openspec-architecture-contract:v1 -->"
VALID_MODES = {"none", "material"}
VALID_DECISIONS = {
    "keep-cohesive",
    "extract-collaborators",
    "temporary-exception",
}
REQUIRED_DESIGN_FIELDS = (
    "Inspected baseline",
    "Expected growth",
    "Existing responsibilities",
    "New responsibilities",
    "Transaction owner",
    "Boundary options",
    "Decision",
    "Known cost",
    "Ratchet scope",
)
TEMPLATE_ONLY_VALUES = {"not applicable", "n/a", "tbd", "todo"}
REQUIRED_CHECKPOINT_FIELDS = (
    "Coverage",
    "Growth",
    "Ownership",
    "Findings",
    "Exclusions",
    "Reviewer",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--change", required=True)
    parser.add_argument(
        "--phase",
        choices=("planning", "apply", "verify"),
        default="apply",
    )
    return parser.parse_args()


def read_required(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing required artifact: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def field_value(text: str, label: str) -> str | None:
    match = re.search(
        rf"^\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    value = match.group(1).strip()
    if not value or value.startswith("<") or value.lower() in TEMPLATE_ONLY_VALUES:
        return None
    return value


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    change_dir = repo / "openspec" / "changes" / args.change
    errors: list[str] = []

    proposal_path = change_dir / "proposal.md"
    proposal = read_required(proposal_path, errors)
    if errors:
        return report(errors)

    if CONTRACT_MARKER not in proposal:
        print(
            "ARCHITECTURE_GATE: LEGACY_NOT_ENFORCED "
            f"({args.change} has no {CONTRACT_MARKER})"
        )
        return 0

    mode = field_value(proposal, "Architecture impact")
    if mode is None:
        errors.append(
            "proposal Architecture Impact must define "
            "**Architecture impact:** none|material"
        )
        return report(errors)
    mode = mode.lower()
    if mode not in VALID_MODES:
        errors.append(f"invalid Architecture Impact mode: {mode!r}")
        return report(errors)

    if mode == "none":
        print(f"ARCHITECTURE_GATE: READY ({args.change}, impact=none)")
        return 0

    design_path = change_dir / "design.md"
    design = read_required(design_path, errors)
    if "## Component Ownership" not in design:
        errors.append("material impact requires ## Component Ownership in design.md")

    values: dict[str, str] = {}
    for label in REQUIRED_DESIGN_FIELDS:
        value = field_value(design, label)
        if value is None:
            errors.append(f"Component Ownership missing non-placeholder **{label}:**")
        else:
            values[label] = value

    decision = values.get("Decision", "").lower()
    if decision and decision not in VALID_DECISIONS:
        errors.append(
            "Component Ownership **Decision:** must be one of "
            + ", ".join(sorted(VALID_DECISIONS))
        )

    if args.phase in {"apply", "verify"}:
        tasks_path = change_dir / "tasks.md"
        tasks = read_required(tasks_path, errors)
        architecture_lines = [
            line
            for line in tasks.splitlines()
            if "<!-- openspec-review:architecture -->" in line
        ]
        if len(architecture_lines) != 1:
            errors.append(
                "material impact requires exactly one openspec-review:architecture task"
            )
        else:
            checkpoint = architecture_lines[0]
            if not re.match(r"^\s*- \[x\]", checkpoint, flags=re.IGNORECASE):
                errors.append("architecture checkpoint must be completed before apply")
            if "Verdict: READY" not in checkpoint:
                errors.append("architecture checkpoint must record Verdict: READY")
            for label in REQUIRED_CHECKPOINT_FIELDS:
                if not re.search(rf"{label}:\s*\S+", checkpoint):
                    errors.append(
                        f"architecture checkpoint must record a concrete {label}"
                    )

    if errors:
        return report(errors)

    print(
        f"ARCHITECTURE_GATE: READY ({args.change}, impact=material, "
        f"phase={args.phase})"
    )
    return 0


def report(errors: list[str]) -> int:
    print("ARCHITECTURE_GATE: NOT_READY", file=sys.stderr)
    for error in errors:
        print(f"- {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
