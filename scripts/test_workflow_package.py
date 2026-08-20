from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import workflow_package as package


class WorkflowPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="workflow-package-test-"))
        self.agent = self.temp / "agent"
        self.schemas = self.temp / "schemas"
        self.backup = self.temp / "backup"
        self.root = package.repo_root()
        self.version = package.load_version(self.root)
        self.roots = {"agent-skills": self.agent, "openspec-schemas": self.schemas}

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def args(self, **overrides: object) -> argparse.Namespace:
        values = {
            "target": "orca", "agent_root": str(self.agent), "schema_root": str(self.schemas),
            "consumer_repo": None, "backup_root": str(self.backup), "dry_run": False, "json": True,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_version_metadata_is_single_valid_source(self) -> None:
        self.assertEqual("1.0.0", self.version)
        package.validate_lock_metadata(self.root)
        metadata_root = self.temp / "metadata"
        metadata_root.mkdir()
        (metadata_root / "package.json").write_text(
            json.dumps({"name": package.PACKAGE_NAME, "version": "not-semver", "private": True}), encoding="utf-8"
        )
        with self.assertRaises(package.PackageError):
            package.load_version(metadata_root)

    def test_orca_and_omnigent_share_stable_agent_root(self) -> None:
        with mock.patch.object(Path, "home", return_value=self.temp / "home"):
            orca = package.resolve_roots("orca", None, str(self.schemas))
            omnigent = package.resolve_roots("omnigent", None, str(self.schemas))
        self.assertEqual(orca["agent-skills"], omnigent["agent-skills"])
        self.assertEqual((self.temp / "home" / ".agents" / "skills").resolve(), orca["agent-skills"])

    def test_initial_install_check_drift_repair_and_rollback(self) -> None:
        old = self.agent / "openspec-workflow" / "SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("old workflow\n", encoding="utf-8")
        unrelated = self.agent / "user-skill" / "note.txt"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("keep\n", encoding="utf-8")

        installed = package.install(self.args(), self.root, self.version, self.roots)
        self.assertEqual("current", installed["status"])
        backup_manifest = json.loads((self.backup / "backup-manifest.json").read_text(encoding="utf-8"))
        backed_paths = {item["path"] for item in backup_manifest["roots"]["agent-skills"]["entries"]}
        self.assertIn("openspec-workflow/SKILL.md", backed_paths)
        self.assertFalse(backup_manifest["roots"]["agent-skills"]["had_valid_receipt"])
        self.assertTrue((self.agent / "openspec-workflow" / "scripts" / "validate_change.py").is_file())
        self.assertEqual("keep\n", unrelated.read_text(encoding="utf-8"))
        self.assertEqual("current", package.check(self.args(), self.root, self.version, self.roots)["status"])

        nested = self.agent / "openspec-workflow" / "scripts" / "validate_change.py"
        nested.write_text("drift\n", encoding="utf-8")
        stale = package.check(self.args(), self.root, self.version, self.roots)
        self.assertEqual("stale", stale["status"])
        self.assertTrue(any(issue.get("path", "").endswith("validate_change.py") for root in stale["roots"] for issue in root["issues"]))

        package.install(self.args(backup_root=None), self.root, self.version, self.roots)
        self.assertEqual("current", package.check(self.args(), self.root, self.version, self.roots)["status"])
        restored = package.rollback(self.args(), self.roots)
        self.assertEqual("restored", restored["status"])
        self.assertEqual("old workflow\n", old.read_text(encoding="utf-8"))
        self.assertFalse((self.agent / package.RECEIPT_NAME).exists())
        self.assertFalse((self.schemas / package.RECEIPT_NAME).exists())
        self.assertEqual("keep\n", unrelated.read_text(encoding="utf-8"))

    def test_check_classifies_version_schema_receipt_and_obsolete_drift(self) -> None:
        package.install(self.args(), self.root, self.version, self.roots)
        receipt_path = self.agent / package.RECEIPT_NAME
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["workflow_version"] = "0.9.0"
        obsolete = self.agent / "openspec-workflow" / "obsolete.py"
        obsolete.write_text("obsolete\n", encoding="utf-8")
        receipt["files"].append({"path": "openspec-workflow/obsolete.py", "sha256": package.sha256(obsolete)})
        receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
        schema_file = self.schemas / "evidence-core" / "schema.yaml"
        schema_file.unlink()

        stale = package.check(self.args(), self.root, self.version, self.roots)
        self.assertEqual("stale", stale["status"])
        issues = [issue for root in stale["roots"] for issue in root["issues"]]
        self.assertTrue(any(issue["kind"] == "version" for issue in issues))
        self.assertTrue(any(issue["kind"] == "missing" and issue.get("path") == "evidence-core/schema.yaml" for issue in issues))
        self.assertTrue(any(issue["kind"] == "obsolete-owned" for issue in issues))

        receipt_path.write_text("not-json", encoding="utf-8")
        missing = package.check(self.args(), self.root, self.version, self.roots)
        self.assertEqual("missing", missing["status"])
        self.assertTrue(any("receipt-invalid" in issue.get("detail", "") for issue in missing["roots"][0]["issues"]))

    def test_failed_copy_does_not_write_receipts(self) -> None:
        real_copy = shutil.copy2
        calls = 0

        def fail_after_first(source: Path, target: Path) -> None:
            nonlocal calls
            calls += 1
            if calls > 1:
                raise OSError("simulated copy failure")
            real_copy(source, target)

        with mock.patch("workflow_package.shutil.copy2", side_effect=fail_after_first):
            with self.assertRaises(OSError):
                package.install(self.args(), self.root, self.version, self.roots)
        self.assertFalse((self.agent / package.RECEIPT_NAME).exists())
        self.assertFalse((self.schemas / package.RECEIPT_NAME).exists())
        package.rollback(self.args(), self.roots)
        remaining = [path for root in self.roots.values() for path in root.rglob("*") if path.is_file()]
        self.assertEqual([], remaining)

    def test_rollback_removes_first_root_when_second_root_copy_fails(self) -> None:
        real_copy = shutil.copy2

        def fail_in_schema_root(source: Path, target: Path) -> None:
            target_path = Path(target)
            if target_path == self.schemas or self.schemas in target_path.parents:
                raise OSError("simulated second-root failure")
            real_copy(source, target)

        with mock.patch("workflow_package.shutil.copy2", side_effect=fail_in_schema_root):
            with self.assertRaises(OSError):
                package.install(self.args(), self.root, self.version, self.roots)
        self.assertTrue((self.agent / package.RECEIPT_NAME).is_file())
        self.assertFalse((self.schemas / package.RECEIPT_NAME).exists())
        package.rollback(self.args(), self.roots)
        remaining = [path for root in self.roots.values() for path in root.rglob("*") if path.is_file()]
        self.assertEqual([], remaining)

    def test_legacy_extra_blocks_before_backup_or_receipt(self) -> None:
        extra = self.agent / "openspec-workflow" / "legacy.txt"
        extra.parent.mkdir(parents=True)
        extra.write_text("legacy\n", encoding="utf-8")
        with self.assertRaises(package.PackageError) as raised:
            package.install(self.args(), self.root, self.version, self.roots)
        self.assertIn("legacy-extra", str(raised.exception))
        self.assertFalse(self.backup.exists())
        self.assertFalse((self.agent / package.RECEIPT_NAME).exists())
        self.assertEqual("legacy\n", extra.read_text(encoding="utf-8"))

    def test_check_missing_is_non_mutating_and_gives_update_command(self) -> None:
        before = list(self.temp.rglob("*"))
        result = package.check(self.args(), self.root, self.version, self.roots)
        after = list(self.temp.rglob("*"))
        self.assertEqual("missing", result["status"])
        self.assertIn("workflow_package.py", result["update_command"])
        self.assertIsInstance(result["update_argv"], list)
        self.assertIn("--backup-root", result["update_argv"])
        self.assertEqual(before, after)

    def test_missing_update_argv_executes_when_prior_adoption_backup_exists(self) -> None:
        fake_home = self.temp / "home"
        retained = fake_home / ".codex-openspec-workflow" / "backups" / f"{self.version}-initial-adoption"
        retained.mkdir(parents=True)
        (retained / "backup-manifest.json").write_text("retained\n", encoding="utf-8")

        with mock.patch("workflow_package.Path.home", return_value=fake_home):
            result = package.check(self.args(backup_root=None), self.root, self.version, self.roots)

        argv = result["update_argv"]
        suggested = Path(argv[argv.index("--backup-root") + 1])
        self.assertEqual(retained.parent / f"{self.version}-initial-adoption-2", suggested)
        self.assertFalse(suggested.exists())

        process = subprocess.run(argv, cwd=self.root, text=True, encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        self.assertEqual("current", package.check(self.args(backup_root=None), self.root, self.version, self.roots)["status"])
        self.assertEqual("retained\n", (retained / "backup-manifest.json").read_text(encoding="utf-8"))

    def test_missing_precedence_survives_consumer_shadowing(self) -> None:
        shadowing = {"repo": str(self.temp / "consumer"), "schemas": [], "current": False}
        with mock.patch("workflow_package.consumer_resolution", return_value=shadowing):
            result = package.check(self.args(consumer_repo=str(self.temp / "consumer")), self.root, self.version, self.roots)
        self.assertEqual("missing", result["status"])
        self.assertIn("consumer_remediation", result)

    def test_overlapping_managed_and_backup_roots_fail_before_mutation(self) -> None:
        same_roots = {"agent-skills": self.agent, "openspec-schemas": self.agent}
        with self.assertRaises(package.PackageError):
            package.install(self.args(), self.root, self.version, same_roots)
        nested_roots = {"agent-skills": self.agent, "openspec-schemas": self.agent / "schemas"}
        with self.assertRaises(package.PackageError):
            package.install(self.args(), self.root, self.version, nested_roots)
        with self.assertRaises(package.PackageError):
            package.install(self.args(backup_root=str(self.agent / "openspec-workflow" / "backup")), self.root, self.version, self.roots)
        self.assertFalse((self.agent / package.RECEIPT_NAME).exists())

    def test_containment_rejects_symlink_escape(self) -> None:
        managed = self.temp / "managed"
        outside = self.temp / "outside"
        managed.mkdir()
        outside.mkdir()
        link = managed / "link"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")
        with self.assertRaises(package.PackageError):
            package.contained_path(managed, "link/escape.txt")

    def test_manifest_paths_must_use_canonical_posix_spelling(self) -> None:
        aliases = ("openspec-workflow//SKILL.md", "openspec-workflow/SKILL.md/", "openspec-workflow\\SKILL.md")
        for value in aliases:
            with self.subTest(value=value), self.assertRaises(package.PackageError):
                package.contained_path(self.agent, value)

    def test_rollback_rejects_traversal_before_mutation(self) -> None:
        old = self.agent / "openspec-workflow" / "SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("old\n", encoding="utf-8")
        package.install(self.args(), self.root, self.version, self.roots)
        installed_hash = package.sha256(old)
        manifest_path = self.backup / "backup-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["roots"]["agent-skills"]["entries"][0]["path"] = "../../escape.txt"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(package.PackageError):
            package.rollback(self.args(), self.roots)
        self.assertEqual(installed_hash, package.sha256(old))
        self.assertFalse((self.temp / "escape.txt").exists())

    def test_rollback_verifies_every_payload_before_mutation(self) -> None:
        old = self.agent / "openspec-workflow" / "SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("old\n", encoding="utf-8")
        package.install(self.args(), self.root, self.version, self.roots)
        installed_hash = package.sha256(old)
        manifest = json.loads((self.backup / "backup-manifest.json").read_text(encoding="utf-8"))
        payload = self.backup / Path(manifest["roots"]["agent-skills"]["entries"][0]["backup"])
        payload.write_text("corrupt\n", encoding="utf-8")
        with self.assertRaises(package.PackageError):
            package.rollback(self.args(), self.roots)
        self.assertEqual(installed_hash, package.sha256(old))

    def test_rollback_rejects_wrong_destination_roots_before_mutation(self) -> None:
        package.install(self.args(), self.root, self.version, self.roots)
        installed = self.agent / "openspec-workflow" / "SKILL.md"
        installed_hash = package.sha256(installed)

        wrong_agent = self.temp / "wrong-agent"
        wrong_agent_file = wrong_agent / "openspec-workflow" / "SKILL.md"
        wrong_agent_file.parent.mkdir(parents=True)
        wrong_agent_file.write_text("wrong agent sentinel\n", encoding="utf-8")
        wrong_schema = self.temp / "wrong-schemas"
        wrong_schema_file = wrong_schema / "evidence-core" / "schema.yaml"
        wrong_schema_file.parent.mkdir(parents=True)
        wrong_schema_file.write_text("wrong schema sentinel\n", encoding="utf-8")

        mismatches = (
            {"agent-skills": wrong_agent, "openspec-schemas": self.schemas},
            {"agent-skills": self.agent, "openspec-schemas": wrong_schema},
        )
        for roots in mismatches:
            with self.subTest(roots=roots), self.assertRaises(package.PackageError):
                package.rollback(self.args(), roots)

        self.assertEqual("wrong agent sentinel\n", wrong_agent_file.read_text(encoding="utf-8"))
        self.assertEqual("wrong schema sentinel\n", wrong_schema_file.read_text(encoding="utf-8"))
        self.assertEqual(installed_hash, package.sha256(installed))
        self.assertTrue((self.agent / package.RECEIPT_NAME).is_file())
        self.assertTrue((self.schemas / package.RECEIPT_NAME).is_file())

    def test_previous_receipt_only_controls_obsolete_deletion(self) -> None:
        self.agent.mkdir(parents=True)
        owned = self.agent / "openspec-workflow" / "removed.txt"
        owned.parent.mkdir(parents=True)
        owned.write_text("owned\n", encoding="utf-8")
        unknown = self.agent / "unknown.txt"
        unknown.write_text("unknown\n", encoding="utf-8")
        receipt = {
            "format_version": package.RECEIPT_FORMAT, "workflow_version": "0.9.0", "root_role": "agent-skills",
            "files": [{"path": "openspec-workflow/removed.txt", "sha256": package.sha256(owned)}],
        }
        (self.agent / package.RECEIPT_NAME).write_text(json.dumps(receipt), encoding="utf-8")
        schema_manifest = package.source_manifest(self.root, "openspec-schemas")
        self.schemas.mkdir(parents=True)
        (self.schemas / package.RECEIPT_NAME).write_text(
            json.dumps(package.receipt_payload(self.version, "openspec-schemas", schema_manifest)), encoding="utf-8"
        )
        for relative, (source, _) in schema_manifest.items():
            target = self.schemas / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        package.install(self.args(backup_root=None), self.root, self.version, self.roots)
        self.assertFalse(owned.exists())
        self.assertEqual("unknown\n", unknown.read_text(encoding="utf-8"))

    def test_consumer_resolution_reports_shadowing(self) -> None:
        payloads = [
            {"name": schema, "source": "project", "path": str(self.temp / "consumer" / "openspec" / "schemas" / schema), "shadows": []}
            for schema in package.SCHEMAS
        ]
        completed = [subprocess.CompletedProcess([], 0, stdout=json.dumps(item), stderr="") for item in payloads]
        with mock.patch("workflow_package.subprocess.run", side_effect=completed):
            result = package.consumer_resolution(self.temp / "consumer", self.schemas)
        self.assertFalse(result["current"])
        self.assertTrue(all(item["shadowing"] for item in result["schemas"]))

    @unittest.skipUnless(shutil.which("openspec.cmd") or shutil.which("openspec"), "OpenSpec CLI is required")
    def test_real_consumer_resolution_is_read_only(self) -> None:
        consumer = self.temp / "consumer"
        schemas = consumer / "openspec" / "schemas"
        schemas.mkdir(parents=True)
        shutil.copytree(self.root / "openspec" / "schemas" / "evidence-core", schemas / "evidence-core")
        shutil.copytree(self.root / "openspec" / "schemas" / "evidence-heavy", schemas / "evidence-heavy")
        (consumer / "openspec" / "config.yaml").write_text("schema: evidence-core\n", encoding="utf-8")
        before = {str(path.relative_to(consumer)): package.sha256(path) for path in consumer.rglob("*") if path.is_file()}
        result = package.consumer_resolution(consumer, self.schemas)
        after = {str(path.relative_to(consumer)): package.sha256(path) for path in consumer.rglob("*") if path.is_file()}
        self.assertFalse(result["current"])
        self.assertTrue(all(item["source"] == "project" and item["shadowing"] for item in result["schemas"]))
        self.assertEqual(before, after)

    @unittest.skipUnless(os.name == "nt", "PowerShell wrapper test is Windows-specific")
    def test_powershell_wrapper_supports_check_and_explicit_roots(self) -> None:
        process = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(self.root / "scripts" / "install.ps1"), "-Target", "orca",
             "-AgentRoot", str(self.agent), "-SchemaRoot", str(self.schemas), "-Check", "-Json"],
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        self.assertEqual(1, process.returncode)
        self.assertEqual("missing", json.loads(process.stdout)["status"])

        human = subprocess.run(
            ["powershell", "-NoProfile", "-File", str(self.root / "scripts" / "install.ps1"), "-Target", "orca",
             "-AgentRoot", str(self.agent), "-SchemaRoot", str(self.schemas), "-Check"],
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        self.assertEqual(1, human.returncode)
        self.assertIn("agent-skills: missing", human.stdout)
        self.assertIn("receipt-missing", human.stdout)
        self.assertIn("update:", human.stdout)

    def test_cli_io_failure_still_emits_json(self) -> None:
        backup_file = self.temp / "backup-file"
        backup_file.write_text("not a directory\n", encoding="utf-8")
        process = subprocess.run(
            [sys.executable, str(self.root / "scripts" / "workflow_package.py"), "install", "--target", "orca",
             "--agent-root", str(self.agent), "--schema-root", str(self.schemas), "--backup-root", str(backup_file), "--json"],
            text=True, encoding="utf-8", errors="replace", capture_output=True, check=False,
        )
        self.assertEqual(2, process.returncode)
        result = json.loads(process.stdout)
        self.assertEqual("error", result["status"])
        self.assertIn("error_type", result)
        self.assertNotIn("Traceback", process.stderr)


if __name__ == "__main__":
    unittest.main()
