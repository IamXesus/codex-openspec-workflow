#!/usr/bin/env python3
"""Validate stable OpenSpec requirement IDs across current and delta specs."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REQUIREMENT = re.compile(r"^### Requirement:\s*.+?\s*$", re.IGNORECASE)
REQUIREMENT_ID = re.compile(r"^\*\*ID:\*\*\s*(?P<value>REQ-[A-Za-z0-9_-]+)\s*$", re.IGNORECASE)
SECTION = re.compile(r"^#{1,3}\s+")
DELTA_SECTION = re.compile(r"^##\s+(?P<kind>ADDED|MODIFIED|REMOVED) Requirements\s*$", re.IGNORECASE)
FENCE = re.compile(r"^\s*(?P<marker>`{3,}|~{3,})")


@dataclass(frozen=True)
class RequirementId:
    value: str
    path: Path
    line: int
    delta_kind: str | None


def fenced_lines(lines: list[str]) -> set[int]:
    fenced: set[int] = set()
    marker_character: str | None = None
    marker_length = 0
    for index, line in enumerate(lines):
        match = FENCE.match(line)
        if marker_character is None:
            if match:
                marker = match.group("marker")
                marker_character = marker[0]
                marker_length = len(marker)
                fenced.add(index)
        else:
            fenced.add(index)
            stripped = line.lstrip()
            if stripped.startswith(marker_character * marker_length):
                marker_character = None
                marker_length = 0
    return fenced


def requirement_ids(path: Path) -> list[RequirementId]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    fenced = fenced_lines(lines)
    declarations: list[RequirementId] = []
    delta_kind: str | None = None
    index = 0
    while index < len(lines):
        line = lines[index]
        if index in fenced:
            index += 1
            continue
        if match := DELTA_SECTION.match(line):
            delta_kind = match.group("kind").upper()
            index += 1
            continue
        if line.startswith("## "):
            delta_kind = None
        if not REQUIREMENT.match(line):
            index += 1
            continue

        end = index + 1
        while end < len(lines) and (end in fenced or not SECTION.match(lines[end])):
            end += 1
        for offset, metadata_line in enumerate(lines[index + 1 : end], start=index + 2):
            metadata_index = offset - 1
            if metadata_index not in fenced and metadata_line.startswith("#### "):
                break
            if metadata_index in fenced:
                continue
            if match := REQUIREMENT_ID.match(metadata_line.strip()):
                declarations.append(
                    RequirementId(match.group("value").upper(), path, offset, delta_kind)
                )
        index = end
    return declarations


def current_requirement_ids(repo: Path) -> list[RequirementId]:
    specs_root = repo / "openspec" / "specs"
    if not specs_root.is_dir():
        return []
    return [
        declaration
        for path in sorted(specs_root.rglob("*.md"))
        for declaration in requirement_ids(path)
    ]


def location(repo: Path, declaration: RequirementId) -> str:
    try:
        relative = declaration.path.relative_to(repo)
    except ValueError:
        relative = declaration.path
    return f"{relative.as_posix()}:{declaration.line}"


def validate_repository(repo: Path) -> list[str]:
    repo = repo.resolve()
    if not repo.is_dir():
        return [f"repository directory not found: {repo}"]
    if not (repo / "openspec").is_dir():
        return [f"OpenSpec directory not found: {repo / 'openspec'}"]
    by_id: dict[str, list[RequirementId]] = {}
    for declaration in current_requirement_ids(repo):
        by_id.setdefault(declaration.value, []).append(declaration)

    return [
        f"duplicate current requirement id '{requirement_id}': "
        + ", ".join(location(repo, item) for item in declarations)
        for requirement_id, declarations in sorted(by_id.items())
        if len(declarations) > 1
    ]


def validate_change_ids(repo: Path, change_dir: Path) -> list[str]:
    repo = repo.resolve()
    errors = validate_repository(repo)
    current_by_id: dict[str, list[RequirementId]] = {}
    for declaration in current_requirement_ids(repo):
        current_by_id.setdefault(declaration.value, []).append(declaration)

    spec_root = change_dir / "specs"
    added = [] if not spec_root.is_dir() else [
        declaration
        for path in sorted(spec_root.rglob("*.md"))
        for declaration in requirement_ids(path)
        if declaration.delta_kind == "ADDED"
    ]
    added_by_id: dict[str, list[RequirementId]] = {}
    for declaration in added:
        added_by_id.setdefault(declaration.value, []).append(declaration)

    for requirement_id, declarations in sorted(added_by_id.items()):
        if requirement_id in current_by_id:
            errors.append(
                f"ADDED requirement id '{requirement_id}' collides with current specification: "
                f"{', '.join(location(repo, item) for item in declarations)}; current: "
                f"{', '.join(location(repo, item) for item in current_by_id[requirement_id])}"
            )
        if len(declarations) > 1:
            errors.append(
                f"duplicate ADDED requirement id '{requirement_id}': "
                + ", ".join(location(repo, item) for item in declarations)
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args(argv)
    errors = validate_repository(args.repo)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print("OpenSpec repository requirement IDs: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
