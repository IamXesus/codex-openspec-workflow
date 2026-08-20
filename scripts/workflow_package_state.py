"""Trusted path, manifest, receipt, and backup state for workflow distribution."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

RECEIPT_NAME = ".codex-openspec-workflow.json"
RECEIPT_FORMAT = 1
BACKUP_FORMAT = 2
SKILLS = ("openspec-workflow", "code-reviewer", "webapp-testing", "coding-guardrails", "architecture-review")
SCHEMAS = ("evidence-core", "evidence-heavy")
POLICY_FORMAT = 1
POLICY_FILE = "AGENTS.md"
POLICY_BEGIN_PREFIX = "<!-- codex-openspec-workflow-policy:begin"
POLICY_END_PREFIX = "<!-- codex-openspec-workflow-policy:end"
POLICY_BEGIN = POLICY_BEGIN_PREFIX + " format={format} version={version} sha256={sha256} -->"
POLICY_END = POLICY_END_PREFIX + " -->"
POLICY_BEGIN_RE = re.compile(
    r"^<!-- codex-openspec-workflow-policy:begin format=(?P<format>\d+) "
    r"version=(?P<version>[^\s]+) sha256=(?P<sha256>[0-9a-fA-F]{64}) -->(?=\r?$)",
    re.MULTILINE,
)
POLICY_END_RE = re.compile(r"^<!-- codex-openspec-workflow-policy:end -->(?=\r?$)", re.MULTILINE)
POLICY_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class PackageError(RuntimeError):
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_policy_body(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized[:-1] if normalized.endswith("\n") else normalized


def policy_body_sha256(text: str) -> str:
    return hashlib.sha256(normalized_policy_body(text).encode("utf-8")).hexdigest()


def policy_source(path: Path) -> tuple[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise PackageError(f"Required policy asset is unreadable UTF-8: {path}") from exc
    return normalized_policy_body(text), policy_body_sha256(text)


def policy_line_ending(text: str) -> str:
    found = [
        (index, priority, ending)
        for priority, ending in enumerate(("\r\n", "\n", "\r"))
        if (index := text.find(ending)) >= 0
    ]
    return min(found)[2] if found else os.linesep


def rendered_policy_block(body: str, version: str, digest: str, newline: str) -> str:
    begin = POLICY_BEGIN.format(format=POLICY_FORMAT, version=version, sha256=digest)
    rendered_body = body.replace("\n", newline)
    return f"{begin}{newline}{rendered_body}{newline}{POLICY_END}"


def _policy_result(path: Path, version: str, digest: str, status: str, **extra: Any) -> dict[str, Any]:
    return {
        "path": str(path),
        "status": status,
        "available_version": version,
        "available_sha256": digest,
        "issues": [],
        **extra,
    }


def plan_consumer_policy(
    consumer_root: Path, source_path: Path, version: str,
) -> tuple[dict[str, Any], bytes | None]:
    consumer = consumer_root.resolve()
    if not consumer.is_dir():
        raise PackageError(f"Consumer repository is not a directory: {consumer}")
    canonical_body, canonical_digest = policy_source(source_path)
    target = consumer / POLICY_FILE
    try:
        target = contained_path(consumer, POLICY_FILE)
    except PackageError:
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "symlink", "detail": "managed policy path escapes the consumer root"})
        return result, None
    if target.is_symlink():
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "symlink", "detail": "managed policy path must be a regular file"})
        return result, None
    if not target.exists():
        block = rendered_policy_block(canonical_body, version, canonical_digest, os.linesep)
        return _policy_result(target, version, canonical_digest, "missing", action="create"), block.encode("utf-8") + os.linesep.encode("utf-8")
    if not target.is_file():
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "not-file", "detail": "managed policy path must be a regular file"})
        return result, None

    raw = target.read_bytes()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    payload = raw[3:] if has_bom else raw
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "encoding", "detail": "AGENTS.md is not valid UTF-8"})
        return result, None

    begins = list(POLICY_BEGIN_RE.finditer(text))
    ends = list(POLICY_END_RE.finditer(text))
    reserved_begins = text.count(POLICY_BEGIN_PREFIX)
    reserved_ends = text.count(POLICY_END_PREFIX)
    newline = policy_line_ending(text)
    block = rendered_policy_block(canonical_body, version, canonical_digest, newline)
    prefix_bytes = b"\xef\xbb\xbf" if has_bom else b""
    if reserved_begins != len(begins) or reserved_ends != len(ends):
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "markers", "detail": "managed policy marker metadata is invalid"})
        return result, None
    if not begins and not ends:
        if normalized_policy_body(text) == canonical_body:
            replacement = prefix_bytes + (block + newline).encode("utf-8")
            action = "adopt-exact"
        else:
            boundary = "" if not text or text.endswith(("\n", "\r")) else newline
            replacement = prefix_bytes + (text + boundary + block + newline).encode("utf-8")
            action = "append"
        return _policy_result(target, version, canonical_digest, "missing", action=action), replacement
    if len(begins) != 1 or len(ends) != 1:
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "markers", "detail": "expected exactly one begin/end marker pair"})
        return result, None

    begin = begins[0]
    end = ends[0]
    body_start = begin.end()
    if text.startswith("\r\n", body_start):
        body_start += 2
    elif body_start < len(text) and text[body_start] in "\r\n":
        body_start += 1
    else:
        body_start = -1
    if body_start < 0 or begin.start() >= end.start() or end.start() == 0:
        result = _policy_result(target, version, canonical_digest, "conflict")
        result["issues"].append({"kind": "markers", "detail": "managed policy markers are malformed or reversed"})
        return result, None
    body_raw = text[body_start:end.start()]
    installed_body = normalized_policy_body(body_raw)
    recorded_digest = begin.group("sha256").lower()
    installed_digest = policy_body_sha256(body_raw)
    installed_version = begin.group("version")
    if not POLICY_SEMVER.fullmatch(installed_version):
        result = _policy_result(target, version, canonical_digest, "conflict", installed_version=installed_version)
        result["issues"].append({"kind": "version", "detail": "managed policy version is not valid SemVer"})
        return result, None
    if int(begin.group("format")) != POLICY_FORMAT:
        result = _policy_result(target, version, canonical_digest, "conflict", installed_version=installed_version)
        result["issues"].append({"kind": "format", "detail": "unsupported managed policy format"})
        return result, None
    if installed_digest != recorded_digest:
        result = _policy_result(target, version, canonical_digest, "conflict", installed_version=installed_version)
        result["issues"].append({"kind": "changed", "detail": "managed policy body differs from its installed receipt hash"})
        return result, None
    if installed_version == version and recorded_digest == canonical_digest and installed_body == canonical_body:
        return _policy_result(target, version, canonical_digest, "current", installed_version=installed_version), None
    replacement = prefix_bytes + (text[:begin.start()] + block + text[end.end():]).encode("utf-8")
    result = _policy_result(target, version, canonical_digest, "stale", installed_version=installed_version, action="replace")
    result["issues"].append({"kind": "version-or-content", "detail": "installed managed policy differs from selected package"})
    return result, replacement


def write_consumer_policy(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        desired_mode = stat.S_IMODE(path.stat().st_mode)
    else:
        current_umask = os.umask(0)
        os.umask(current_umask)
        desired_mode = 0o666 & ~current_umask
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, desired_mode)
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def paths_overlap(first: Path, second: Path) -> bool:
    left = first.resolve()
    right = second.resolve()
    return left == right or left in right.parents or right in left.parents


def ensure_disjoint(roots: dict[str, Path], backup_root: Path | None = None) -> None:
    agent = roots["agent-skills"]
    schemas = roots["openspec-schemas"]
    if paths_overlap(agent, schemas):
        raise PackageError("Agent and schema roots must be disjoint")
    if backup_root and any(paths_overlap(backup_root, managed) for managed in roots.values()):
        raise PackageError("Backup root must be disjoint from managed roots")


def safe_relative(value: object) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PackageError(f"Unsafe manifest path: {value!r}")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if posix.is_absolute() or windows.is_absolute() or ".." in posix.parts or "." in posix.parts:
        raise PackageError(f"Unsafe manifest path: {value!r}")
    if value != posix.as_posix():
        raise PackageError(f"Manifest path is not canonical POSIX form: {value!r}")
    return posix


def contained_path(root: Path, relative: object) -> Path:
    normalized = safe_relative(relative)
    root_resolved = root.resolve()
    candidate = root.joinpath(*normalized.parts)
    resolved = candidate.resolve(strict=False)
    if resolved != root_resolved and root_resolved not in resolved.parents:
        raise PackageError(f"Manifest path escapes selected root: {relative!r}")
    return candidate


def is_package_file(path: Path) -> bool:
    return path.is_file() and path.suffix != ".pyc" and "__pycache__" not in path.parts


def source_manifest(root: Path, role: str) -> dict[str, tuple[Path, str]]:
    groups = SKILLS if role == "agent-skills" else SCHEMAS
    base = root / ("skills" if role == "agent-skills" else "openspec/schemas")
    manifest: dict[str, tuple[Path, str]] = {}
    for group in groups:
        source = base / group
        if not source.is_dir():
            raise PackageError(f"Package source is missing: {source}")
        for path in sorted(source.rglob("*")):
            if is_package_file(path):
                relative = (Path(group) / path.relative_to(source)).as_posix()
                contained_path(source, path.relative_to(source).as_posix())
                manifest[relative] = (path, sha256(path))
    return manifest


def receipt_payload(version: str, role: str, manifest: dict[str, tuple[Path, str]]) -> dict[str, Any]:
    return {
        "format_version": RECEIPT_FORMAT,
        "workflow_version": version,
        "root_role": role,
        "files": [{"path": path, "sha256": manifest[path][1]} for path in sorted(manifest)],
    }


def read_receipt(path: Path, role: str) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, "receipt-missing"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        files = data["files"]
        if (
            data.get("format_version") != RECEIPT_FORMAT
            or data.get("root_role") != role
            or not isinstance(data.get("workflow_version"), str)
            or not isinstance(files, list)
        ):
            raise ValueError("invalid receipt fields")
        seen: set[str] = set()
        for item in files:
            relative = item.get("path")
            digest = item.get("sha256")
            normalized = safe_relative(relative)
            allowed = SKILLS if role == "agent-skills" else SCHEMAS
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest) or relative in seen:
                raise ValueError("invalid receipt manifest")
            if not normalized.parts or normalized.parts[0] not in allowed:
                raise ValueError("receipt path is outside package subtrees")
            seen.add(relative)
        return data, None
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError, PackageError) as exc:
        return None, f"receipt-invalid: {exc}"


def inventory(root: Path, role: str) -> dict[str, tuple[Path, str]]:
    groups = SKILLS if role == "agent-skills" else SCHEMAS
    found: dict[str, tuple[Path, str]] = {}
    for group in groups:
        subtree = root / group
        if not subtree.exists():
            continue
        for path in sorted(subtree.rglob("*")):
            if is_package_file(path):
                relative = (Path(group) / path.relative_to(subtree)).as_posix()
                contained_path(root, relative)
                found[relative] = (path, sha256(path))
    return found


def check_root(role: str, destination: Path, version: str, manifest: dict[str, tuple[Path, str]]) -> dict[str, Any]:
    receipt, receipt_error = read_receipt(destination / RECEIPT_NAME, role)
    result: dict[str, Any] = {
        "role": role, "root": str(destination), "status": "current",
        "installed_version": receipt.get("workflow_version") if receipt else None,
        "available_version": version, "issues": [],
    }
    if receipt is None:
        result["status"] = "missing"
        result["issues"].append({"kind": "receipt", "path": RECEIPT_NAME, "detail": receipt_error})
        return result
    expected_hashes = {path: item[1] for path, item in manifest.items()}
    receipt_hashes = {item["path"]: item["sha256"] for item in receipt["files"]}
    if receipt["workflow_version"] != version:
        result["issues"].append({"kind": "version", "detail": "installed version differs"})
    for relative, expected in expected_hashes.items():
        installed = contained_path(destination, relative)
        if not installed.is_file():
            result["issues"].append({"kind": "missing", "path": relative})
        elif sha256(installed) != expected:
            result["issues"].append({"kind": "changed", "path": relative})
        if receipt_hashes.get(relative) != expected:
            result["issues"].append({"kind": "manifest", "path": relative})
    for relative in sorted(set(receipt_hashes) - set(expected_hashes)):
        result["issues"].append({"kind": "obsolete-owned", "path": relative})
    if result["issues"]:
        result["status"] = "stale"
    return result


def backup_existing(
    backup_root: Path, roots: dict[str, Path], manifests: dict[str, dict[str, tuple[Path, str]]],
    receipts: dict[str, dict[str, Any] | None],
) -> dict[str, Any]:
    if backup_root.exists() and any(backup_root.iterdir()):
        raise PackageError(f"Backup root must be absent or empty: {backup_root}")
    backup_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"format_version": BACKUP_FORMAT, "roots": {}}
    for role, destination in roots.items():
        entries = []
        for relative, (source, digest) in inventory(destination, role).items():
            backup_relative = (Path(role) / "files" / Path(relative)).as_posix()
            target = contained_path(backup_root, backup_relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            entries.append({"path": relative, "sha256": digest, "backup": backup_relative})
        receipt_path = destination / RECEIPT_NAME
        receipt_backup = None
        receipt_digest = None
        if receipt_path.is_file():
            receipt_backup = (Path(role) / RECEIPT_NAME).as_posix()
            target = contained_path(backup_root, receipt_backup)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(receipt_path, target)
            receipt_digest = sha256(target)
        manifest["roots"][role] = {
            "destination": str(destination.resolve()),
            "entries": entries, "receipt_backup": receipt_backup, "receipt_sha256": receipt_digest,
            "had_valid_receipt": receipts[role] is not None, "new_manifest_paths": sorted(manifests[role]),
        }
    (backup_root / "backup-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def validated_backup_manifest(backup_root: Path, roots: dict[str, Path]) -> dict[str, Any]:
    manifest_path = contained_path(backup_root, "backup-manifest.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"Invalid backup manifest: {manifest_path}") from exc
    if set(manifest) != {"format_version", "roots"} or manifest.get("format_version") != BACKUP_FORMAT:
        raise PackageError("Unsupported or malformed backup manifest")
    states = manifest.get("roots")
    if not isinstance(states, dict) or set(states) != set(roots):
        raise PackageError("Backup manifest root roles do not match selected roots")
    for role, destination in roots.items():
        state = states[role]
        fields = {
            "destination", "entries", "receipt_backup", "receipt_sha256",
            "had_valid_receipt", "new_manifest_paths",
        }
        if not isinstance(state, dict) or set(state) != fields:
            raise PackageError(f"Malformed backup state for {role}")
        expected_destination = str(destination.resolve())
        if state["destination"] != expected_destination:
            raise PackageError(
                f"Backup destination for {role} does not match selected root: "
                f"{state['destination']!r} != {expected_destination!r}"
            )
        if not isinstance(state["entries"], list) or not isinstance(state["new_manifest_paths"], list):
            raise PackageError(f"Malformed backup file lists for {role}")
        if not isinstance(state["had_valid_receipt"], bool):
            raise PackageError(f"Malformed receipt state for {role}")
        contained_path(destination, RECEIPT_NAME)
        allowed = SKILLS if role == "agent-skills" else SCHEMAS
        seen: set[str] = set()
        for item in state["entries"]:
            if not isinstance(item, dict) or set(item) != {"path", "sha256", "backup"}:
                raise PackageError(f"Malformed backup entry for {role}")
            relative = safe_relative(item["path"])
            backup_relative = safe_relative(item["backup"])
            digest = item["sha256"]
            if not relative.parts or relative.parts[0] not in allowed or item["path"] in seen:
                raise PackageError(f"Backup entry is outside package subtrees for {role}")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                raise PackageError(f"Invalid backup hash for {role}/{item['path']}")
            if backup_relative != PurePosixPath(role, "files", *relative.parts):
                raise PackageError(f"Backup payload path does not match its destination: {item['backup']}")
            contained_path(destination, item["path"])
            payload = contained_path(backup_root, item["backup"])
            if not payload.is_file() or sha256(payload) != digest:
                raise PackageError(f"Backup payload verification failed: {payload}")
            seen.add(item["path"])
        new_paths: set[str] = set()
        for relative in state["new_manifest_paths"]:
            normalized = safe_relative(relative)
            if not normalized.parts or normalized.parts[0] not in allowed or relative in new_paths:
                raise PackageError(f"New manifest path is outside package subtrees for {role}")
            new_paths.add(relative)
        receipt_backup = state["receipt_backup"]
        receipt_digest = state["receipt_sha256"]
        if receipt_backup is None:
            if receipt_digest is not None:
                raise PackageError(f"Unexpected receipt hash without receipt backup for {role}")
        else:
            if receipt_backup != f"{role}/{RECEIPT_NAME}":
                raise PackageError(f"Unexpected receipt backup path for {role}")
            if not isinstance(receipt_digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", receipt_digest):
                raise PackageError(f"Invalid receipt backup hash for {role}")
            payload = contained_path(backup_root, receipt_backup)
            if not payload.is_file() or sha256(payload) != receipt_digest:
                raise PackageError(f"Receipt backup verification failed: {payload}")
    return manifest
