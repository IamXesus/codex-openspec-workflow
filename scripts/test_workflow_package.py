from __future__ import annotations

import argparse
import contextlib
import io
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


def usable_openspec_cli() -> bool:
    try:
        executable = package.resolve_openspec_executable()
        process = subprocess.run(
            [executable, "--version"], text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=10,
        )
    except (OSError, subprocess.SubprocessError, package.PackageError):
        return False
    return process.returncode == 0


USABLE_OPENSPEC_CLI = usable_openspec_cli()


class WorkflowPackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="workflow-package-test-"))
        self.agent = self.temp / "agent"
        self.schemas = self.temp / "schemas"
        self.backup = self.temp / "backup"
        self.consumer = self.temp / "consumer"
        self.consumer.mkdir()
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
        self.assertEqual("1.1.1", self.version)
        package.validate_lock_metadata(self.root)
        metadata_root = self.temp / "metadata"
        metadata_root.mkdir()
        (metadata_root / "package.json").write_text(
            json.dumps({"name": package.PACKAGE_NAME, "version": "not-semver", "private": True}), encoding="utf-8"
        )
        with self.assertRaises(package.PackageError):
            package.load_version(metadata_root)

    def test_openspec_executable_resolution_is_platform_specific(self) -> None:
        isolated_path = self.temp / "isolated-path"
        isolated_path.mkdir()
        posix_executable = isolated_path / "openspec"
        posix_executable.write_text("isolated fixture\n", encoding="utf-8")
        os.chmod(posix_executable, 0o755)
        finder = lambda candidate: shutil.which(candidate, path=str(isolated_path))
        self.assertEqual(str(posix_executable), package.resolve_openspec_executable("posix", finder))
        self.assertIsNone(finder("openspec.cmd"))
        self.assertEqual(
            "C:/isolated/openspec.cmd",
            package.resolve_openspec_executable(
                "nt", lambda candidate: "C:/isolated/openspec.cmd" if candidate == "openspec.cmd" else None,
            ),
        )
        self.assertEqual(
            "C:/isolated/openspec",
            package.resolve_openspec_executable(
                "nt", lambda candidate: "C:/isolated/openspec" if candidate == "openspec" else None,
            ),
        )
        with self.assertRaises(package.PackageError):
            package.resolve_openspec_executable("posix", lambda _candidate: None)

    def test_real_cli_gate_rejects_a_discovered_but_broken_shim(self) -> None:
        broken = subprocess.CompletedProcess([], 127, stdout="", stderr="node: not found")
        with mock.patch("workflow_package.resolve_openspec_executable", return_value="/mounted/openspec"), mock.patch(
            "test_workflow_package.subprocess.run", return_value=broken,
        ) as run:
            self.assertFalse(usable_openspec_cli())
        run.assert_called_once_with(
            ["/mounted/openspec", "--version"], text=True, encoding="utf-8", errors="replace",
            capture_output=True, check=False, timeout=10,
        )

        working = subprocess.CompletedProcess([], 0, stdout="1.8.0", stderr="")
        with mock.patch("workflow_package.resolve_openspec_executable", return_value="openspec"), mock.patch(
            "test_workflow_package.subprocess.run", return_value=working,
        ):
            self.assertTrue(usable_openspec_cli())

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
        shadowing = {"repo": str(self.consumer), "schemas": [], "current": False}
        with mock.patch("workflow_package.consumer_resolution", return_value=shadowing):
            result = package.check(self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots)
        self.assertEqual("missing", result["status"])
        self.assertIn("consumer_remediation", result)

    def test_consumer_policy_create_check_and_idempotent_reinstall(self) -> None:
        agents = self.consumer / "AGENTS.md"
        installed = package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        self.assertEqual("current", installed["policy"]["status"])
        first = agents.read_bytes()
        self.assertEqual(1, first.count(b"codex-openspec-workflow-policy:begin"))
        self.assertEqual(1, first.count(b"codex-openspec-workflow-policy:end"))

        current_resolution = {"repo": str(self.consumer), "schemas": [], "current": True}
        with mock.patch("workflow_package.consumer_resolution", return_value=current_resolution):
            checked = package.check(
                self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
            )
        self.assertEqual("current", checked["status"])
        self.assertEqual("current", checked["policy"]["status"])

        package.install(
            self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
        )
        self.assertEqual(first, agents.read_bytes())

    def test_install_without_consumer_does_not_select_agents_file(self) -> None:
        package.install(self.args(), self.root, self.version, self.roots)
        self.assertFalse((self.consumer / "AGENTS.md").exists())
        self.assertFalse((self.consumer / "docs/project-handoff").exists())
        self.assertFalse((self.consumer / "openspec/config.yaml").exists())

    def test_consumer_install_creates_project_scaffold_and_current_rerun_preserves_bytes(self) -> None:
        installed = package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        self.assertEqual("current", installed["status"])
        self.assertEqual("current", installed["project"]["status"])
        self.assertEqual("pending", installed["project"]["audit_status"])
        paths = installed["project"]["canonical_paths"]
        before = {path: (self.consumer / path).read_bytes() for path in paths}

        package.install(
            self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
        )
        after = {path: (self.consumer / path).read_bytes() for path in paths}
        self.assertEqual(before, after)

    def test_project_check_is_read_only_and_remediation_retains_consumer(self) -> None:
        package.install(self.args(), self.root, self.version, self.roots)
        before = list(self.consumer.rglob("*"))
        resolution = {"repo": str(self.consumer), "schemas": [], "current": True}
        with mock.patch("workflow_package.consumer_resolution", return_value=resolution):
            checked = package.check(
                self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
            )
        self.assertEqual("missing", checked["status"])
        self.assertEqual("missing", checked["project"]["status"])
        self.assertEqual(before, list(self.consumer.rglob("*")))
        self.assertIn("--consumer-repo", checked["update_argv"])
        self.assertEqual(str(self.consumer.resolve()), checked["update_argv"][-1])

    def test_consumer_dry_run_reports_project_paths_without_writes(self) -> None:
        ready = package.install(
            self.args(consumer_repo=str(self.consumer), dry_run=True), self.root, self.version, self.roots,
        )
        self.assertEqual("ready", ready["status"])
        self.assertEqual("missing", ready["project"]["status"])
        self.assertTrue(ready["project"]["prepared_paths"])
        self.assertEqual([], list(self.consumer.rglob("*")))
        self.assertFalse(self.agent.exists())
        self.assertFalse(self.schemas.exists())

    def test_project_conflict_blocks_before_shared_or_consumer_mutation(self) -> None:
        outside = self.temp / "outside"
        outside.mkdir()
        try:
            (self.consumer / "docs").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlinks unavailable: {exc}")
        with self.assertRaises(package.PackageError) as raised:
            package.install(
                self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
            )
        self.assertEqual("conflict", raised.exception.details["project"]["status"])
        self.assertFalse((self.agent / package.RECEIPT_NAME).exists())
        self.assertFalse((self.schemas / package.RECEIPT_NAME).exists())
        self.assertFalse((self.consumer / "AGENTS.md").exists())
        self.assertEqual([], list(outside.rglob("*")))

    def test_project_conflict_precedes_missing_and_check_is_read_only(self) -> None:
        outside = self.temp / "outside-check"
        outside.mkdir()
        try:
            (self.consumer / "docs").symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlinks unavailable: {exc}")
        before = sorted(str(path.relative_to(self.temp)) for path in self.temp.rglob("*"))
        checked = package.check(
            self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
        )
        after = sorted(str(path.relative_to(self.temp)) for path in self.temp.rglob("*"))
        self.assertEqual("conflict", checked["status"])
        self.assertEqual("conflict", checked["project"]["status"])
        self.assertNotIn("update_argv", checked)
        self.assertNotIn("consumer", checked)
        self.assertEqual(before, after)

    def test_human_output_surfaces_project_and_semantic_audit_state(self) -> None:
        installed = package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            package.emit(installed, False)
        rendered = output.getvalue()
        self.assertIn("project bootstrap: current", rendered)
        self.assertIn("semantic audit: pending", rendered)

    def test_existing_noncanonical_config_is_preserved_and_reported_stale(self) -> None:
        config = self.consumer / "openspec/config.yaml"
        config.parent.mkdir(parents=True)
        original = b"schema: evidence-core\r\ncontext: custom"
        config.write_bytes(original)
        installed = package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        self.assertEqual("stale", installed["status"])
        self.assertEqual("stale", installed["project"]["status"])
        self.assertEqual(original, config.read_bytes())
        self.assertTrue((self.consumer / "docs/project-handoff/README.md").is_file())

    def test_project_write_failure_is_resumable_after_shared_success(self) -> None:
        real_write = package.write_project_bootstrap
        _, initial_writes = package.plan_project_bootstrap(self.consumer, self.root)
        initial_audit = next(
            content for path, content in initial_writes.items()
            if path.as_posix().endswith("docs/project-handoff/project-audit.md")
        )

        def write_one_then_fail(consumer: Path, writes: dict[Path, bytes]) -> None:
            first = next(iter(writes.items()))
            real_write(consumer, dict([first]))
            raise OSError("simulated project write failure")

        with mock.patch("workflow_package.write_project_bootstrap", side_effect=write_one_then_fail):
            with self.assertRaises(OSError):
                package.install(
                    self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
                )
        self.assertTrue((self.agent / package.RECEIPT_NAME).is_file())
        resumed = package.install(
            self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
        )
        self.assertEqual("current", resumed["project"]["status"])
        self.assertEqual(initial_audit, (self.consumer / "docs/project-handoff/project-audit.md").read_bytes())

    def test_existing_policy_prefix_and_newline_style_are_preserved(self) -> None:
        agents = self.consumer / "AGENTS.md"
        prefix = b"# Consumer rules\r\n\r\nKeep this exact"
        agents.write_bytes(prefix)
        package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        installed = agents.read_bytes()
        self.assertTrue(installed.startswith(prefix + b"\r\n"))
        self.assertIn(b"-->\r\n## Evidence, Scope, And Authority\r\n", installed)
        self.assertEqual(1, installed.count(b"codex-openspec-workflow-policy:begin"))

    def test_exact_unmarked_fragment_is_adopted_without_duplication(self) -> None:
        source = (self.root / "policy" / "AGENTS.fragment.md").read_bytes()
        agents = self.consumer / "AGENTS.md"
        agents.write_bytes(source)
        package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        installed = agents.read_text(encoding="utf-8")
        self.assertEqual(1, installed.count("## Evidence, Scope, And Authority"))
        self.assertEqual(1, installed.count("codex-openspec-workflow-policy:begin"))

    def test_known_legacy_unmarked_fragment_is_upgraded_without_duplication(self) -> None:
        current = (self.root / "policy" / "AGENTS.fragment.md").read_text(encoding="utf-8")
        project_section = current[current.index("## Project Knowledge Bootstrap"):current.index("## Material UI")]
        current_sentence = (
            "- A freshness check is read-only. An install with an explicit consumer repository may create `AGENTS.md` "
            "or update only the intact centrally managed policy block; it never owns surrounding consumer instructions. "
            "Installation does not pull Git, publish a release, or authorize any external effect."
        )
        legacy_sentence = (
            "- A freshness check is read-only. Installing the reusable package does not edit consumer repositories, "
            "merge this policy fragment, pull Git, publish a release, or authorize any external effect."
        )
        legacy = current.replace(project_section, "").replace(current_sentence, legacy_sentence).rstrip("\r\n") + "\n"
        agents = self.consumer / "AGENTS.md"
        agents.write_text(legacy, encoding="utf-8")
        package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        installed = agents.read_text(encoding="utf-8")
        self.assertEqual(1, installed.count("## Evidence, Scope, And Authority"))
        self.assertEqual(1, installed.count("codex-openspec-workflow-policy:begin"))
        self.assertIn(current_sentence, installed)
        self.assertNotIn(legacy_sentence, installed)

    def test_stale_policy_replaces_only_managed_block_and_retains_consumer_in_update(self) -> None:
        agents = self.consumer / "AGENTS.md"
        agents.write_text("# Local\n", encoding="utf-8")
        package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        current = agents.read_text(encoding="utf-8")
        agents.write_text(current.replace(f"version={self.version}", "version=0.9.0"), encoding="utf-8")
        resolution = {"repo": str(self.consumer), "schemas": [], "current": True}
        with mock.patch("workflow_package.consumer_resolution", return_value=resolution):
            stale = package.check(
                self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
            )
        self.assertEqual("stale", stale["policy"]["status"])
        self.assertIn("--consumer-repo", stale["update_argv"])
        self.assertEqual(str(self.consumer.resolve()), stale["update_argv"][-1])
        self.assertNotIn("--backup-root", stale["update_argv"])

        package.install(
            self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
        )
        repaired = agents.read_text(encoding="utf-8")
        self.assertTrue(repaired.startswith("# Local\n"))
        self.assertIn(f"version={self.version}", repaired)

    def test_crlf_stale_replacement_preserves_exact_prefix_suffix_and_bom(self) -> None:
        begin_token = b"<!-- codex-openspec-workflow-policy:begin"
        end_token = b"<!-- codex-openspec-workflow-policy:end -->"
        for index, bom in enumerate((b"", b"\xef\xbb\xbf")):
            with self.subTest(bom=bool(bom)):
                consumer = self.temp / f"crlf-consumer-{index}"
                consumer.mkdir()
                agents = consumer / "AGENTS.md"
                agents.write_bytes(bom + b"# Head\r\n")
                package.install(
                    self.args(
                        consumer_repo=str(consumer),
                        backup_root=str(self.backup) if index == 0 else None,
                    ),
                    self.root, self.version, self.roots,
                )
                stale = agents.read_bytes().replace(
                    f"version={self.version}".encode(), b"version=0.9.0", 1,
                ).replace(end_token, end_token + b"\r\n# Tail", 1)
                if bom:
                    stale = stale.removesuffix(b"\r\n")
                prefix = stale[:stale.index(begin_token)]
                suffix_start = stale.index(end_token) + len(end_token)
                suffix = stale[suffix_start:]
                agents.write_bytes(stale)

                package.install(
                    self.args(consumer_repo=str(consumer), backup_root=None),
                    self.root, self.version, self.roots,
                )
                repaired = agents.read_bytes()
                self.assertEqual(prefix, repaired[:repaired.index(begin_token)])
                repaired_suffix = repaired[repaired.index(end_token) + len(end_token):]
                self.assertEqual(suffix, repaired_suffix)

    def test_modified_managed_body_conflicts_before_any_install_mutation(self) -> None:
        agents = self.consumer / "AGENTS.md"
        package.install(
            self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
        )
        agents.write_text(
            agents.read_text(encoding="utf-8").replace("Treat missing facts", "Locally changed facts", 1),
            encoding="utf-8",
        )
        before = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        with self.assertRaises(package.PackageError) as raised:
            package.install(
                self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
            )
        self.assertIn("conflict", str(raised.exception).lower())
        after = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)
        resolution = {"repo": str(self.consumer), "schemas": [], "current": True}
        with mock.patch("workflow_package.consumer_resolution", return_value=resolution):
            checked = package.check(
                self.args(consumer_repo=str(self.consumer), backup_root=None), self.root, self.version, self.roots,
            )
        self.assertEqual("conflict", checked["status"])
        self.assertEqual("conflict", checked["policy"]["status"])
        self.assertNotIn("update_argv", checked)

    def test_malformed_policy_markers_and_symlink_are_conflicts(self) -> None:
        agents = self.consumer / "AGENTS.md"
        begin = (
            "<!-- codex-openspec-workflow-policy:begin format=1 version=1.0.0 "
            + "sha256=" + "0" * 64 + " -->"
        )
        end = "<!-- codex-openspec-workflow-policy:end -->"
        variants = (
            begin + "\nbody\n",
            end + "\n",
            end + "\n" + begin + "\nbody\n",
            begin + "\nbody\n" + end + "\n" + begin + "\nbody\n" + end + "\n",
            begin.replace("format=1", "format=x") + "\nbody\n" + end + "\n",
            "  " + begin + "\nbody\n" + end + "\n",
        )
        for text in variants:
            with self.subTest(text=text[:50]):
                agents.write_text(text, encoding="utf-8")
                state, replacement = package.plan_consumer_policy(
                    self.consumer, self.root / "policy" / "AGENTS.fragment.md", self.version,
                )
                self.assertEqual("conflict", state["status"])
                self.assertIsNone(replacement)

        body, digest = package.policy_source(self.root / "policy" / "AGENTS.fragment.md")
        invalid_version = (
            "<!-- codex-openspec-workflow-policy:begin format=1 version=banana "
            f"sha256={digest} -->\n{body}\n{end}\n"
        )
        agents.write_text(invalid_version, encoding="utf-8")
        state, replacement = package.plan_consumer_policy(
            self.consumer, self.root / "policy" / "AGENTS.fragment.md", self.version,
        )
        self.assertEqual("conflict", state["status"])
        self.assertIsNone(replacement)
        before = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        with self.assertRaises(package.PackageError):
            package.install(
                self.args(consumer_repo=str(self.consumer)), self.root, self.version, self.roots,
            )
        after = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

        valid = (
            "<!-- codex-openspec-workflow-policy:begin "
            f"format=1 version={self.version} sha256={digest} -->\n{body}\n{end}\n"
        )
        for extra in (
            "<!-- codex-openspec-workflow-policy:begin format=x -->\n",
            "<!-- codex-openspec-workflow-policy:end invalid -->\n",
        ):
            with self.subTest(extra=extra):
                agents.write_text(valid + extra, encoding="utf-8")
                state, replacement = package.plan_consumer_policy(
                    self.consumer, self.root / "policy" / "AGENTS.fragment.md", self.version,
                )
                self.assertEqual("conflict", state["status"])
                self.assertIsNone(replacement)

        agents.write_bytes(b"\xff\xfe\x00")
        state, replacement = package.plan_consumer_policy(
            self.consumer, self.root / "policy" / "AGENTS.fragment.md", self.version,
        )
        self.assertEqual("conflict", state["status"])
        self.assertIsNone(replacement)

        agents.unlink()
        target = self.temp / "outside-agents.md"
        target.write_text("outside\n", encoding="utf-8")
        try:
            agents.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"File symlinks are unavailable: {exc}")
        state, replacement = package.plan_consumer_policy(
            self.consumer, self.root / "policy" / "AGENTS.fragment.md", self.version,
        )
        self.assertEqual("conflict", state["status"])
        self.assertIsNone(replacement)

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
        with mock.patch("workflow_package.resolve_openspec_executable", return_value="isolated-openspec"), mock.patch(
            "workflow_package.subprocess.run", side_effect=completed,
        ):
            result = package.consumer_resolution(self.temp / "consumer", self.schemas)
        self.assertFalse(result["current"])
        self.assertTrue(all(item["shadowing"] for item in result["schemas"]))

    @unittest.skipUnless(USABLE_OPENSPEC_CLI, "A platform-correct working OpenSpec CLI is required")
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

    @unittest.skipUnless(USABLE_OPENSPEC_CLI, "A platform-correct working OpenSpec CLI is required")
    def test_cli_consumer_policy_lifecycle_rehearsal(self) -> None:
        script = str(self.root / "scripts" / "workflow_package.py")

        def run(operation: str, consumer: Path, agent: Path, schemas: Path, backup: Path | None = None):
            argv = [
                sys.executable, script, operation, "--target", "orca",
                "--agent-root", str(agent), "--schema-root", str(schemas),
                "--consumer-repo", str(consumer), "--json",
            ]
            if backup is not None:
                argv += ["--backup-root", str(backup)]
            process = subprocess.run(
                argv, cwd=self.root, text=True, encoding="utf-8", errors="replace",
                capture_output=True, check=False,
            )
            return process, json.loads(process.stdout)

        consumers = []
        for name, initial in (
            ("absent", None),
            ("existing", "# Consumer-only rule\n"),
            ("exact", (self.root / "policy" / "AGENTS.fragment.md").read_text(encoding="utf-8")),
        ):
            consumer = self.temp / f"cli-{name}"
            schemas = consumer / "openspec" / "schemas"
            schemas.parent.mkdir(parents=True)
            shutil.copy2(self.root / "project_templates" / "openspec-config.yaml", schemas.parent / "config.yaml")
            if initial is not None:
                (consumer / "AGENTS.md").write_text(initial, encoding="utf-8")
            agent = self.temp / f"cli-agent-{name}"
            backup = self.temp / f"cli-backup-{name}"
            process, result = run("install", consumer, agent, schemas, backup)
            self.assertEqual(0, process.returncode, process.stderr or process.stdout)
            self.assertEqual("current", result["policy"]["status"])
            installed = (consumer / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(1, installed.count("codex-openspec-workflow-policy:begin"))
            if name == "existing":
                self.assertTrue(installed.startswith(initial))
            if name == "exact":
                self.assertEqual(1, installed.count("## Evidence, Scope, And Authority"))
            consumers.append((consumer, agent, schemas))

        consumer, agent, schemas = consumers[1]
        agents = consumer / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8").replace(f"version={self.version}", "version=0.9.0", 1),
            encoding="utf-8",
        )
        process, stale = run("check", consumer, agent, schemas)
        self.assertEqual(1, process.returncode)
        self.assertEqual("stale", stale["policy"]["status"])
        process, repaired = run("install", consumer, agent, schemas)
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        self.assertEqual("current", repaired["policy"]["status"])

        agents.write_text(
            agents.read_text(encoding="utf-8").replace("Treat missing facts", "Locally changed facts", 1),
            encoding="utf-8",
        )
        before = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        process, conflicted = run("check", consumer, agent, schemas)
        self.assertEqual(1, process.returncode)
        self.assertEqual("conflict", conflicted["policy"]["status"])
        process, rejected = run("install", consumer, agent, schemas)
        self.assertEqual(2, process.returncode)
        self.assertEqual("conflict", rejected["policy"]["status"])
        after = {
            str(path.relative_to(self.temp)): package.sha256(path)
            for path in self.temp.rglob("*") if path.is_file()
        }
        self.assertEqual(before, after)

    @unittest.skipUnless(USABLE_OPENSPEC_CLI, "A platform-correct working OpenSpec CLI is required")
    def test_cli_project_bootstrap_is_host_neutral_and_semantic_handoff_is_preserved(self) -> None:
        script = str(self.root / "scripts" / "workflow_package.py")

        def run(operation: str, target: str, consumer: Path, agent: Path, schemas: Path, backup: Path | None = None):
            argv = [
                sys.executable, script, operation, "--target", target,
                "--agent-root", str(agent), "--schema-root", str(schemas),
                "--consumer-repo", str(consumer), "--json",
            ]
            if backup is not None:
                argv += ["--backup-root", str(backup)]
            process = subprocess.run(
                argv, cwd=self.root, text=True, encoding="utf-8", errors="replace",
                capture_output=True, check=False,
            )
            return process, json.loads(process.stdout)

        consumers: dict[tuple[str, str], tuple[Path, Path, Path]] = {}
        for scenario in ("empty", "partial"):
            rendered: dict[str, dict[str, bytes]] = {}
            for target in ("codex", "orca", "omnigent"):
                consumer = self.temp / f"portable-{scenario}-{target}"
                consumer.mkdir()
                if scenario == "partial":
                    source = consumer / "src/app.txt"
                    source.parent.mkdir()
                    source.write_bytes(b"same existing source\r\n")
                    business = consumer / "docs/project-handoff/business-processes.md"
                    business.parent.mkdir(parents=True)
                    business.write_bytes(b"same confirmed business evidence\n")
                agent = self.temp / f"portable-agent-{scenario}-{target}"
                schemas = consumer / "openspec/schemas"
                backup = self.temp / f"portable-backup-{scenario}-{target}"
                process, installed = run("install", target, consumer, agent, schemas, backup)
                self.assertEqual(0, process.returncode, process.stderr or process.stdout)
                self.assertEqual("current", installed["project"]["status"])
                self.assertEqual("pending", installed["project"]["audit_status"])
                files = {path.relative_to(consumer).as_posix(): path.read_bytes()
                         for path in consumer.rglob("*") if path.is_file()}
                self.assertEqual(1, files["AGENTS.md"].count(b"codex-openspec-workflow-policy:begin"))
                rendered[target] = files

                process, repeated = run("install", target, consumer, agent, schemas)
                self.assertEqual(0, process.returncode, process.stderr or process.stdout)
                self.assertEqual("current", repeated["project"]["status"])
                self.assertEqual(files, {path.relative_to(consumer).as_posix(): path.read_bytes()
                                         for path in consumer.rglob("*") if path.is_file()})
                consumers[(scenario, target)] = (consumer, agent, schemas)
            self.assertEqual(rendered["codex"], rendered["orca"])
            self.assertEqual(rendered["codex"], rendered["omnigent"])

        consumer, agent, schemas = consumers[("partial", "omnigent")]
        audit = consumer / "docs/project-handoff/project-audit.md"
        audit.write_text(
            audit.read_text(encoding="utf-8").replace("status=pending", "status=complete", 1)
            + "\nInspected evidence paths: src/app.txt and docs/project-handoff/business-processes.md. "
            + "Git state: isolated fixture is not a Git repository. Unresolved facts remain open.\n",
            encoding="utf-8",
        )
        authored = {path.relative_to(consumer).as_posix(): path.read_bytes()
                    for path in consumer.rglob("*") if path.is_file()}
        process, checked = run("check", "omnigent", consumer, agent, schemas)
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        self.assertEqual("current", checked["project"]["status"])
        self.assertEqual("complete", checked["project"]["audit_status"])
        process, repeated = run("install", "omnigent", consumer, agent, schemas)
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        self.assertEqual(authored, {path.relative_to(consumer).as_posix(): path.read_bytes()
                                    for path in consumer.rglob("*") if path.is_file()})

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
