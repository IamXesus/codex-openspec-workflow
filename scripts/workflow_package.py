#!/usr/bin/env python3
"""Versioned installer/checker for the portable OpenSpec workflow package."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from workflow_project_bootstrap import plan_project_bootstrap, write_project_bootstrap
from workflow_package_state import (
    RECEIPT_FORMAT,
    RECEIPT_NAME,
    SCHEMAS,
    PackageError,
    backup_existing,
    check_root,
    contained_path,
    ensure_disjoint,
    inventory,
    plan_consumer_policy,
    policy_source,
    read_receipt,
    receipt_payload,
    sha256,
    source_manifest,
    validated_backup_manifest,
    write_consumer_policy,
)

PACKAGE_NAME = "codex-openspec-workflow"
SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_version(root: Path) -> str:
    metadata_path = root / "package.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageError(f"Invalid package metadata: {metadata_path}") from exc
    version = metadata.get("version")
    if metadata.get("name") != PACKAGE_NAME or metadata.get("private") is not True:
        raise PackageError("package.json must declare the canonical private package name")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise PackageError("package.json must declare one valid semantic version")
    return version


def validate_lock_metadata(root: Path) -> None:
    version = load_version(root)
    try:
        lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
        package = lock["packages"][""]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise PackageError("package-lock.json is missing valid root package metadata") from exc
    if lock.get("name") != PACKAGE_NAME or lock.get("version") != version:
        raise PackageError("package-lock.json name/version differs from package.json")
    if package.get("name") != PACKAGE_NAME or package.get("version") != version:
        raise PackageError("package-lock.json root package name/version differs from package.json")


def default_schema_root() -> Path:
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "openspec" / "schemas"
    if os.name == "nt":
        local = os.environ.get("LOCALAPPDATA")
        if not local:
            raise PackageError("LOCALAPPDATA is required to resolve the Windows schema root")
        return Path(local) / "openspec" / "schemas"
    return Path.home() / ".local" / "share" / "openspec" / "schemas"


def resolve_roots(target: str, agent_root: str | None, schema_root: str | None) -> dict[str, Path]:
    if agent_root:
        agent = Path(agent_root).expanduser().resolve()
    elif target == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        agent = (Path(codex_home).expanduser() if codex_home else Path.home() / ".codex") / "skills"
        agent = agent.resolve()
    else:
        agent = (Path.home() / ".agents" / "skills").resolve()
    schema = Path(schema_root).expanduser().resolve() if schema_root else default_schema_root().resolve()
    roots = {"agent-skills": agent, "openspec-schemas": schema}
    ensure_disjoint(roots)
    return roots


def policy_state(root: Path) -> dict[str, Any]:
    policy = root / "policy" / "AGENTS.fragment.md"
    if not policy.is_file():
        raise PackageError(f"Required policy asset is missing: {policy}")
    _, digest = policy_source(policy)
    return {
        "source_path": str(policy), "available_sha256": digest,
        "status": "not-selected", "consumer_required": True,
    }


def available_adoption_backup(version: str) -> Path:
    parent = Path.home() / ".codex-openspec-workflow" / "backups"
    base_name = f"{version}-initial-adoption"
    candidate = parent / base_name
    suffix = 2
    while candidate.exists():
        candidate = parent / f"{base_name}-{suffix}"
        suffix += 1
    return candidate


def update_argv(args: argparse.Namespace, roots: dict[str, Path], version: str, needs_backup: bool) -> list[str]:
    command = [sys.executable, str(Path(__file__).resolve()), "install", "--target", args.target]
    command += ["--agent-root", str(roots["agent-skills"]), "--schema-root", str(roots["openspec-schemas"])]
    if needs_backup:
        command += ["--backup-root", str(available_adoption_backup(version))]
    if args.consumer_repo:
        command += ["--consumer-repo", str(Path(args.consumer_repo).resolve())]
    return command


def display_command(argv: list[str]) -> str:
    return subprocess.list2cmdline(argv) if os.name == "nt" else shlex.join(argv)


def resolve_openspec_executable(platform_name: str | None = None, finder=None) -> str:
    host = platform_name or os.name
    find = finder or shutil.which
    candidates = ("openspec.cmd", "openspec") if host == "nt" else ("openspec",)
    for candidate in candidates:
        executable = find(candidate)
        if executable:
            return executable
    expected = "openspec.cmd or shell-resolved openspec" if host == "nt" else "openspec"
    raise PackageError(f"OpenSpec CLI 1.8.x was not found as {expected}")


def consumer_resolution(consumer: Path, schema_root: Path) -> dict[str, Any]:
    executable = resolve_openspec_executable()
    results = []
    for schema in SCHEMAS:
        process = subprocess.run(
            [executable, "schema", "which", schema, "--json"], cwd=consumer, text=True,
            encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        if process.returncode != 0:
            raise PackageError(f"OpenSpec schema resolution failed for {schema}", {"stdout": process.stdout, "stderr": process.stderr})
        try:
            data = json.loads(process.stdout[process.stdout.find("{") :])
        except (json.JSONDecodeError, ValueError) as exc:
            raise PackageError(f"OpenSpec returned invalid JSON for {schema}") from exc
        effective = Path(data["path"]).resolve()
        selected = (schema_root / schema).resolve()
        results.append({
            "schema": schema, "source": data.get("source"), "path": str(effective),
            "selected_path": str(selected), "shadowing": effective != selected,
            "shadows": data.get("shadows", []),
        })
    return {"repo": str(consumer.resolve()), "schemas": results, "current": not any(x["shadowing"] for x in results)}


def install(args: argparse.Namespace, root: Path, version: str, roots: dict[str, Path]) -> dict[str, Any]:
    policy = policy_state(root)
    policy_content = None
    project = None
    project_writes: dict[Path, bytes] = {}
    consumer: Path | None = None
    if args.consumer_repo:
        consumer = Path(args.consumer_repo).expanduser().resolve()
        policy, policy_content = plan_consumer_policy(
            consumer, root / "policy" / "AGENTS.fragment.md", version,
        )
        policy["source_path"] = str(root / "policy" / "AGENTS.fragment.md")
        if policy["status"] == "conflict":
            raise PackageError("Consumer policy conflict blocks installation", {"policy": policy})
        project, project_writes = plan_project_bootstrap(consumer, root)
        if project["status"] == "conflict":
            raise PackageError("Consumer project-bootstrap conflict blocks installation", {"project": project})
    backup = Path(args.backup_root).expanduser().resolve() if args.backup_root else None
    ensure_disjoint(roots, backup)
    manifests = {role: source_manifest(root, role) for role in roots}
    receipts: dict[str, dict[str, Any] | None] = {}
    adoption = False
    legacy_extras = []
    for role, destination in roots.items():
        receipt, _ = read_receipt(destination / RECEIPT_NAME, role)
        receipts[role] = receipt
        contained_path(destination, RECEIPT_NAME)
        for relative in manifests[role]:
            contained_path(destination, relative)
        if receipt:
            for item in receipt["files"]:
                contained_path(destination, item["path"])
        if receipt is None:
            adoption = True
            for relative in sorted(set(inventory(destination, role)) - set(manifests[role])):
                legacy_extras.append({"role": role, "path": relative})
    result: dict[str, Any] = {
        "operation": "install", "target": args.target, "workflow_version": version,
        "roots": {role: str(path) for role, path in roots.items()}, "dry_run": args.dry_run,
        "initial_adoption": adoption, "backup_required": adoption, "legacy_extras": legacy_extras,
        "policy": policy,
    }
    if project is not None:
        result["project"] = project
    if legacy_extras:
        raise PackageError("Unresolved legacy-extra files block installation", result)
    if args.dry_run:
        result["status"] = "ready"
        return result
    if adoption and not args.backup_root:
        raise PackageError("Initial adoption requires --backup-root", result)
    if backup:
        result["backup"] = str(backup)
        backup_existing(backup, roots, manifests, receipts)
    for role, destination in roots.items():
        destination.mkdir(parents=True, exist_ok=True)
        previous = receipts[role]
        previous_paths = {item["path"] for item in previous["files"]} if previous else set()
        for relative in sorted(previous_paths - set(manifests[role])):
            obsolete = contained_path(destination, relative)
            if obsolete.is_file():
                obsolete.unlink()
        for relative, (source, _) in manifests[role].items():
            target = contained_path(destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        receipt_path = destination / RECEIPT_NAME
        temporary = receipt_path.with_suffix(receipt_path.suffix + ".tmp")
        temporary.write_text(json.dumps(receipt_payload(version, role, manifests[role]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(receipt_path)
    if policy_content is not None:
        write_consumer_policy(Path(policy["path"]), policy_content)
        policy["status"] = "current"
        policy["installed_version"] = version
    if consumer is not None:
        write_project_bootstrap(consumer, project_writes)
        project, _ = plan_project_bootstrap(consumer, root)
        result["project"] = project
    result["status"] = "stale" if project is not None and project["status"] == "stale" else "current"
    return result


def check(args: argparse.Namespace, root: Path, version: str, roots: dict[str, Path]) -> dict[str, Any]:
    ensure_disjoint(roots)
    root_results = [check_root(role, destination, version, source_manifest(root, role)) for role, destination in roots.items()]
    root_statuses = {item["status"] for item in root_results}
    status = "missing" if "missing" in root_statuses else "stale" if "stale" in root_statuses else "current"
    policy = policy_state(root)
    result: dict[str, Any] = {
        "operation": "check", "target": args.target, "status": status, "workflow_version": version,
        "roots": root_results,
        "policy": policy,
    }
    if args.consumer_repo:
        consumer = Path(args.consumer_repo).resolve()
        policy, _ = plan_consumer_policy(consumer, root / "policy" / "AGENTS.fragment.md", version)
        project, _ = plan_project_bootstrap(consumer, root)
        policy["source_path"] = str(root / "policy" / "AGENTS.fragment.md")
        result["policy"] = policy
        result["project"] = project
        consumer_statuses = {policy["status"], project["status"]}
        if "conflict" in consumer_statuses:
            result["status"] = "conflict"
        elif "missing" in consumer_statuses and result["status"] != "conflict":
            result["status"] = "missing"
        elif "stale" in consumer_statuses and result["status"] == "current":
            result["status"] = "stale"
        if policy["status"] == "conflict":
            result["policy_remediation"] = "Reconcile the reported managed AGENTS.md block; check never overwrites a conflict."
        if project["status"] == "conflict":
            result["project_remediation"] = "Reconcile unsafe canonical project paths; check never overwrites a conflict."
        else:
            result["consumer"] = consumer_resolution(consumer, roots["openspec-schemas"])
            if not result["consumer"]["current"]:
                if result["status"] == "current":
                    result["status"] = "stale"
                result["consumer_remediation"] = "Reconcile the reported project-local schema shadowing in the consumer; check never edits it."
    if result["status"] in {"missing", "stale"}:
        argv = update_argv(args, roots, version, "missing" in root_statuses)
        result["update_argv"] = argv
        result["update_command"] = display_command(argv)
    return result


def rollback(args: argparse.Namespace, roots: dict[str, Path]) -> dict[str, Any]:
    if not args.backup_root:
        raise PackageError("Rollback requires --backup-root")
    backup_root = Path(args.backup_root).expanduser().resolve()
    ensure_disjoint(roots, backup_root)
    manifest = validated_backup_manifest(backup_root, roots)
    restored = []
    for role, destination in roots.items():
        state = manifest["roots"][role]
        original = {item["path"]: item for item in state["entries"]}
        current_receipt, _ = read_receipt(destination / RECEIPT_NAME, role)
        installed_paths = set(state["new_manifest_paths"])
        if current_receipt:
            installed_paths.update(item["path"] for item in current_receipt["files"])
        for relative in sorted(installed_paths - set(original)):
            path = contained_path(destination, relative)
            if path.is_file():
                path.unlink()
        temporary_receipt = contained_path(destination, f"{RECEIPT_NAME}.tmp")
        if temporary_receipt.is_file():
            temporary_receipt.unlink()
        for relative, item in original.items():
            source = contained_path(backup_root, item["backup"])
            target = contained_path(destination, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256(target) != item["sha256"]:
                raise PackageError(f"Rollback verification failed: {target}")
        receipt_path = destination / RECEIPT_NAME
        receipt_backup = state.get("receipt_backup")
        if receipt_backup:
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(contained_path(backup_root, receipt_backup), receipt_path)
        elif receipt_path.exists():
            receipt_path.unlink()
        restored.append({"role": role, "files": len(original), "receipt_restored": bool(receipt_backup)})
    return {"operation": "rollback", "status": "restored", "backup": str(backup_root), "roots": restored}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("operation", choices=("install", "check", "rollback"))
    result.add_argument("--target", choices=("codex", "orca", "omnigent"), default="codex")
    result.add_argument("--agent-root")
    result.add_argument("--schema-root")
    result.add_argument("--consumer-repo")
    result.add_argument("--backup-root")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--json", action="store_true")
    return result


def emit(result: dict[str, Any], json_output: bool) -> None:
    if json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"{result.get('operation')}: {result.get('status', 'failed')}")
    if "workflow_version" in result:
        print(f"workflow version: {result['workflow_version']}")
    roots = result.get("roots")
    if isinstance(roots, dict):
        for role, path in roots.items():
            print(f"{role}: {path}")
    elif isinstance(roots, list):
        for root in roots:
            if not isinstance(root, dict):
                continue
            print(f"{root.get('role')}: {root.get('status')} at {root.get('root')}")
            for issue in root.get("issues", []):
                location = f" {issue['path']}" if issue.get("path") else ""
                detail = f" ({issue['detail']})" if issue.get("detail") else ""
                print(f"  - {issue.get('kind', 'issue')}{location}{detail}")
    consumer = result.get("consumer")
    if isinstance(consumer, dict):
        for schema in consumer.get("schemas", []):
            print(f"consumer {schema['schema']}: {schema['source']} {schema['path']} (shadowing={schema['shadowing']})")
    if result.get("update_command"):
        print(f"update: {result['update_command']}")
    if result.get("consumer_remediation"):
        print(f"consumer remediation: {result['consumer_remediation']}")
    if result.get("policy_remediation"):
        print(f"policy remediation: {result['policy_remediation']}")
    if result.get("project_remediation"):
        print(f"project remediation: {result['project_remediation']}")
    if result.get("error"):
        print(f"error: {result['error']}")
    if result.get("recovery"):
        print(f"recovery: {result['recovery']}")
    if result.get("policy"):
        policy = result["policy"]
        path = f" at {policy['path']}" if policy.get("path") else ""
        print(f"consumer policy: {policy.get('status')}{path}")
        for issue in policy.get("issues", []):
            print(f"  - {issue.get('kind', 'issue')}: {issue.get('detail', '')}")
    if result.get("project"):
        project = result["project"]
        print(f"project bootstrap: {project.get('status')} at {project.get('root')}")
        print(f"semantic audit: {project.get('audit_status') or 'unknown'}")
        for issue in project.get("issues", []):
            print(f"  - {issue.get('kind', 'issue')} {issue.get('path', '')}: {issue.get('detail', '')}")


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        root = repo_root()
        version = load_version(root)
        roots = resolve_roots(args.target, args.agent_root, args.schema_root)
        if args.operation == "install":
            result = install(args, root, version, roots)
        elif args.operation == "check":
            result = check(args, root, version, roots)
        else:
            result = rollback(args, roots)
        emit(result, args.json)
        return 0 if result.get("status") in {"current", "ready", "restored"} else 1
    except PackageError as exc:
        result = {"operation": args.operation, "status": "error", "error": str(exc), **exc.details}
        emit(result, args.json)
        return 2
    except (OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        result = {
            "operation": args.operation,
            "status": "error",
            "error": str(exc),
            "error_type": type(exc).__name__,
            "recovery": "Run check with the same selected roots; rerun install or the prepared rollback after resolving the reported error.",
        }
        emit(result, args.json)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
