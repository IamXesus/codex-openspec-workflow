#!/usr/bin/env python3
"""Structural project-knowledge bootstrap for explicitly selected consumers."""

from __future__ import annotations

import os
import json
import re
import stat
import tempfile
from pathlib import Path
from typing import Any

from workflow_package_state import PackageError, contained_path

AUDIT_PATH = "docs/project-handoff/project-audit.md"
CONFIG_PATH = "openspec/config.yaml"
TEMPLATE_PATHS = {
    AUDIT_PATH: "project-handoff/project-audit.md",
    "docs/project-handoff/README.md": "project-handoff/README.md",
    "docs/project-handoff/business-processes.md": "project-handoff/business-processes.md",
    "docs/project-handoff/integrations.md": "project-handoff/integrations.md",
    "docs/project-handoff/technical-architecture.md": "project-handoff/technical-architecture.md",
    "docs/project-handoff/open-issues.md": "project-handoff/open-issues.md",
    CONFIG_PATH: "openspec-config.yaml",
}
AUDIT_PREFIX = "<!-- codex-openspec-project-audit:"
AUDIT_MARKER_RE = re.compile(
    r"^<!-- codex-openspec-project-audit:v1 status=(?P<status>pending|complete) -->(?=\r?$)",
    re.MULTILINE,
)
AUDIT_PLACEHOLDER = "{{STRUCTURAL_OBSERVATIONS}}"
CANONICAL_PLACEHOLDER = "{{CANONICAL_OBSERVATIONS}}"
MAX_OBSERVATIONS = 100
OPEN_SPEC_LAYERS = (
    "openspec/specs/",
    "openspec/changes/",
    "openspec/changes/archive/",
)
SCHEMA_RE = re.compile(r"^schema:[ \t]*evidence-core[ \t]*(?:[ \t]+#.*)?$")
CONTEXT_RE = re.compile(r"^context:[ \t]*\|[-+]?[ \t]*(?:[ \t]+#.*)?$")
ROOT_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:")
ROOT_SCHEMA_KEY_RE = re.compile(r"^(?:schema|['\"]schema['\"])\s*:")
ROOT_CONTEXT_KEY_RE = re.compile(r"^(?:context|['\"]context['\"])\s*:")
CANONICAL_CONTEXT_REFS = {
    "docs/project-handoff/": re.compile(r"(?<![A-Za-z0-9_/-])docs/project-handoff/(?![A-Za-z0-9_/-])"),
    "openspec/specs/": re.compile(r"(?<![A-Za-z0-9_/-])openspec/specs/(?![A-Za-z0-9_/-])"),
    "openspec/changes/ (active)": re.compile(r"(?<![A-Za-z0-9_/-])openspec/changes/(?![A-Za-z0-9_/-])"),
    "openspec/changes/archive/": re.compile(r"(?<![A-Za-z0-9_/-])openspec/changes/archive/(?![A-Za-z0-9_/-])"),
    "Git history": re.compile(r"(?<![A-Za-z0-9_-])Git history(?![A-Za-z0-9_-])"),
}


def _read_utf8(path: Path, label: str) -> str:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise PackageError(f"Unable to read {label}: {path}") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PackageError(f"{label} is not valid UTF-8: {path}") from exc


def _templates(package_root: Path) -> dict[str, str]:
    root = package_root / "project_templates"
    rendered: dict[str, str] = {}
    for relative, source_relative in TEMPLATE_PATHS.items():
        source = root / source_relative
        if not source.is_file() or source.is_symlink():
            raise PackageError(f"Required project template is missing: {source}")
        text = _read_utf8(source, "project template").replace("\r\n", "\n").replace("\r", "\n")
        rendered[relative] = text if text.endswith("\n") else text + "\n"
    if AUDIT_PLACEHOLDER not in rendered[AUDIT_PATH] or CANONICAL_PLACEHOLDER not in rendered[AUDIT_PATH]:
        raise PackageError("Project audit template is missing a required observation placeholder")
    return rendered


def structural_observations(consumer: Path) -> list[str]:
    observations: list[str] = []
    for entry in sorted(consumer.iterdir(), key=lambda item: (item.name.casefold(), item.name)):
        if entry.name == ".git":
            continue
        if entry.is_symlink():
            kind = "symlink (not followed)"
        elif entry.is_dir():
            kind = "directory"
        elif entry.is_file():
            kind = "file"
        else:
            kind = "other path"
        suffix = "/" if kind == "directory" else ""
        safe_name = json.dumps(entry.name + suffix, ensure_ascii=True)
        observations.append(f"- {safe_name} ({kind})")
        if len(observations) == MAX_OBSERVATIONS:
            observations.append("- Observation list truncated at 100 top-level entries.")
            break
    return observations


def canonical_observations(consumer: Path) -> list[str]:
    observations: list[str] = []
    for relative in (*TEMPLATE_PATHS, *OPEN_SPEC_LAYERS):
        try:
            target = contained_path(consumer, relative.rstrip("/"))
            present = os.path.lexists(target)
            state = "present" if present else "missing"
            if present and target.is_symlink():
                state += " (symlink, not followed)"
        except PackageError:
            state = "present (unsafe path, not followed)"
        observations.append(f"- {json.dumps(relative, ensure_ascii=True)}: {state}")
    return observations


def _audit_text(template: str, consumer: Path) -> str:
    observations = structural_observations(consumer)
    body = "\n".join(observations) if observations else "- No pre-bootstrap top-level project evidence was found."
    canonical = "\n".join(canonical_observations(consumer))
    return template.replace(AUDIT_PLACEHOLDER, body).replace(CANONICAL_PLACEHOLDER, canonical)


def _canonical_config_issues(text: str) -> list[str]:
    if "\t" in text:
        return ["tabs are outside the accepted canonical YAML subset"]
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    root_schema_lines = [line for line in lines if ROOT_SCHEMA_KEY_RE.match(line)]
    if len(root_schema_lines) != 1 or SCHEMA_RE.fullmatch(root_schema_lines[0]) is None:
        return ["require exactly one root-level schema: evidence-core declaration"]

    root_context_indexes = [index for index, line in enumerate(lines) if ROOT_CONTEXT_KEY_RE.match(line)]
    if len(root_context_indexes) != 1 or CONTEXT_RE.fullmatch(lines[root_context_indexes[0]]) is None:
        return ["require exactly one root-level literal context block"]
    context_start = root_context_indexes[0]
    context_lines: list[str] = []
    for line in lines[context_start + 1:]:
        if line and not line[0].isspace() and ROOT_KEY_RE.match(line):
            break
        if line.startswith((" ", "\t")):
            context_lines.append(line.lstrip())
        elif line:
            break
    context = "\n".join(context_lines)
    return [f"missing canonical context reference: {label}"
            for label, pattern in CANONICAL_CONTEXT_REFS.items() if pattern.search(context) is None]


def _issue(kind: str, path: str, detail: str) -> dict[str, str]:
    return {"kind": kind, "path": path, "detail": detail}


def plan_project_bootstrap(
    consumer_root: Path, package_root: Path,
) -> tuple[dict[str, Any], dict[Path, bytes]]:
    consumer = consumer_root.expanduser().resolve()
    if not consumer.is_dir():
        raise PackageError(f"Consumer repository is not a directory: {consumer}")
    templates = _templates(package_root)
    writes: dict[Path, bytes] = {}
    issues: list[dict[str, str]] = []
    existing: list[str] = []
    missing: list[str] = []
    audit_status: str | None = None

    for relative in TEMPLATE_PATHS:
        try:
            target = contained_path(consumer, relative)
        except PackageError:
            issues.append(_issue("symlink", relative, "canonical path escapes the consumer repository"))
            continue
        if target.is_symlink():
            issues.append(_issue("symlink", relative, "canonical path must be a regular file"))
            continue
        if not target.exists():
            text = _audit_text(templates[relative], consumer) if relative == AUDIT_PATH else templates[relative]
            writes[target] = text.encode("utf-8")
            missing.append(relative)
            if relative == AUDIT_PATH:
                audit_status = "pending"
            continue
        if not target.is_file():
            issues.append(_issue("not-file", relative, "canonical path must be a regular file"))
            continue
        existing.append(relative)
        try:
            text = _read_utf8(target, "consumer project knowledge file")
        except PackageError:
            issues.append(_issue("encoding", relative, "canonical file is not valid UTF-8"))
            continue
        if relative == AUDIT_PATH:
            markers = list(AUDIT_MARKER_RE.finditer(text))
            reserved = text.count(AUDIT_PREFIX)
            if reserved != len(markers) or len(markers) > 1:
                issues.append(_issue("audit-marker", relative, "audit marker is malformed or duplicated"))
            elif not markers:
                issues.append(_issue("audit-marker-missing", relative, "existing audit requires manual marker reconciliation"))
            else:
                audit_status = markers[0].group("status")
        elif relative == CONFIG_PATH:
            for detail in _canonical_config_issues(text):
                issues.append(_issue("config-navigation", relative, detail))

    conflict_kinds = {"symlink", "not-file", "encoding", "audit-marker"}
    if any(issue["kind"] in conflict_kinds for issue in issues):
        status = "conflict"
    elif missing:
        status = "missing"
    elif issues:
        status = "stale"
    else:
        status = "current"
    result: dict[str, Any] = {
        "root": str(consumer),
        "status": status,
        "audit_status": audit_status,
        "canonical_paths": list(TEMPLATE_PATHS),
        "existing_paths": existing,
        "missing_paths": missing,
        "prepared_paths": [path.relative_to(consumer).as_posix() for path in writes],
        "issues": issues,
    }
    return result, writes


def _new_file_mode() -> int:
    current_umask = os.umask(0)
    os.umask(current_umask)
    return 0o666 & ~current_umask


def write_project_bootstrap(consumer_root: Path, writes: dict[Path, bytes]) -> None:
    consumer = consumer_root.expanduser().resolve()
    for target, content in writes.items():
        try:
            relative = target.relative_to(consumer)
        except ValueError as exc:
            raise PackageError(f"Prepared project path escapes selected consumer: {target}") from exc
        created_parents: list[Path] = []
        temporary: Path | None = None
        try:
            current_parent = consumer
            for part in relative.parent.parts:
                current_parent = contained_path(consumer, current_parent.joinpath(part).relative_to(consumer).as_posix())
                try:
                    current_parent.mkdir()
                    created_parents.append(current_parent)
                except FileExistsError:
                    if current_parent.is_symlink() or not current_parent.is_dir():
                        raise PackageError(f"Project parent is not a safe directory: {current_parent}")
            checked = contained_path(consumer, relative.as_posix())
            resolved_parent = checked.parent.resolve(strict=True)
            if resolved_parent != consumer and consumer not in resolved_parent.parents:
                raise PackageError(f"Project parent escapes selected consumer: {checked.parent}")
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{checked.name}.", suffix=".tmp", dir=resolved_parent,
            )
            temporary = Path(temporary_name)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.chmod(temporary, _new_file_mode())
            publish_target = contained_path(consumer, relative.as_posix())
            if publish_target.parent.resolve(strict=True) != resolved_parent:
                raise PackageError(f"Project parent changed after preflight: {publish_target.parent}")
            try:
                os.link(temporary, publish_target)
            except FileExistsError as exc:
                raise PackageError(f"Consumer project file appeared after preflight: {publish_target}") from exc
        except Exception:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
                temporary = None
            for parent in reversed(created_parents):
                try:
                    parent.rmdir()
                except OSError:
                    break
            raise
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
