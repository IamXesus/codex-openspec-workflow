from __future__ import annotations

import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workflow_package_state import PackageError
from workflow_project_bootstrap import (
    AUDIT_PATH,
    CONFIG_PATH,
    MAX_OBSERVATIONS,
    TEMPLATE_PATHS,
    plan_project_bootstrap,
    write_project_bootstrap,
)


class ProjectBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp = Path(self.temporary.name)
        self.package = Path(__file__).resolve().parent.parent
        self.consumer = self.temp / "consumer"
        self.consumer.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def plan(self, consumer: Path | None = None):
        return plan_project_bootstrap(consumer or self.consumer, self.package)

    def test_empty_consumer_prepares_canonical_pending_scaffold(self) -> None:
        state, writes = self.plan()
        self.assertEqual("missing", state["status"])
        self.assertEqual("pending", state["audit_status"])
        self.assertEqual(list(TEMPLATE_PATHS), state["missing_paths"])
        self.assertEqual(set(TEMPLATE_PATHS), set(state["prepared_paths"]))
        self.assertEqual(len(TEMPLATE_PATHS), len(writes))
        audit = next(content for path, content in writes.items() if path.as_posix().endswith(AUDIT_PATH))
        decoded = audit.decode("utf-8")
        self.assertIn("status=pending", decoded)
        self.assertIn("No pre-bootstrap top-level project evidence was found", decoded)
        self.assertNotIn("{{STRUCTURAL_OBSERVATIONS}}", decoded)

    def test_equivalent_consumers_render_byte_identical_outputs(self) -> None:
        first = self.temp / "first"
        second = self.temp / "second"
        first.mkdir()
        second.mkdir()
        for root in (first, second):
            (root / "src").mkdir()
            (root / "package.json").write_text("{}\n", encoding="utf-8")
        _, first_writes = self.plan(first)
        _, second_writes = self.plan(second)
        first_bytes = {path.relative_to(first).as_posix(): body for path, body in first_writes.items()}
        second_bytes = {path.relative_to(second).as_posix(): body for path, body in second_writes.items()}
        self.assertEqual(first_bytes, second_bytes)
        audit = first_bytes[AUDIT_PATH].decode("utf-8")
        self.assertLess(audit.index("package.json"), audit.index("src/"))

    def test_audit_records_canonical_documents_and_openspec_layers(self) -> None:
        (self.consumer / "docs/project-handoff").mkdir(parents=True)
        (self.consumer / "docs/project-handoff/business-processes.md").write_text("existing\n", encoding="utf-8")
        (self.consumer / "openspec/specs").mkdir(parents=True)
        _, writes = self.plan()
        audit = next(content for path, content in writes.items() if path.as_posix().endswith(AUDIT_PATH)).decode("utf-8")
        self.assertIn('"docs/project-handoff/business-processes.md": present', audit)
        self.assertIn('"docs/project-handoff/integrations.md": missing', audit)
        self.assertIn('"openspec/specs/": present', audit)
        self.assertIn('"openspec/changes/": missing', audit)
        self.assertIn('"openspec/changes/archive/": missing', audit)
        self.assertNotIn("{{CANONICAL_OBSERVATIONS}}", audit)

    def test_observations_are_bounded_and_do_not_follow_symlinks(self) -> None:
        for index in range(MAX_OBSERVATIONS + 5):
            (self.consumer / f"entry-{index:03}.txt").write_text("x", encoding="utf-8")
        outside = self.temp / "outside"
        outside.mkdir()
        link = self.consumer / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            link = None
        _, writes = self.plan()
        audit = next(content for path, content in writes.items() if path.as_posix().endswith(AUDIT_PATH)).decode("utf-8")
        self.assertIn("Observation list truncated at 100", audit)
        self.assertNotIn("outside", audit)
        if link is not None:
            self.assertNotIn("linked", audit)  # sorted after the bounded entry set

    @unittest.skipIf(os.name == "nt", "Windows filenames cannot exercise case ties and control characters")
    def test_observation_names_are_deterministic_and_markdown_safe(self) -> None:
        for name in ("A", "a", "tick`name", "line\nbreak"):
            (self.consumer / name).write_text("x", encoding="utf-8")
        _, writes = self.plan()
        audit = next(content for path, content in writes.items() if path.as_posix().endswith(AUDIT_PATH)).decode("utf-8")
        self.assertLess(audit.index('"A"'), audit.index('"a"'))
        self.assertIn('"tick`name"', audit)
        self.assertIn('"line\\nbreak"', audit)
        self.assertNotIn("- `tick`name`", audit)

    def test_partial_repository_preserves_existing_bytes_mode_and_newline(self) -> None:
        existing = self.consumer / "docs/project-handoff/business-processes.md"
        existing.parent.mkdir(parents=True)
        original = b"# Existing\r\nconsumer facts without final newline"
        existing.write_bytes(original)
        if os.name != "nt":
            os.chmod(existing, 0o640)
        before_mode = stat.S_IMODE(existing.stat().st_mode)
        state, writes = self.plan()
        self.assertEqual("missing", state["status"])
        self.assertNotIn(existing, writes)
        write_project_bootstrap(self.consumer, writes)
        self.assertEqual(original, existing.read_bytes())
        self.assertEqual(before_mode, stat.S_IMODE(existing.stat().st_mode))

    def test_write_then_replan_is_structurally_current_and_idempotent(self) -> None:
        _, writes = self.plan()
        write_project_bootstrap(self.consumer, writes)
        before = {relative: (self.consumer / relative).read_bytes() for relative in TEMPLATE_PATHS}
        state, second_writes = self.plan()
        self.assertEqual("current", state["status"])
        self.assertEqual("pending", state["audit_status"])
        self.assertEqual({}, second_writes)
        write_project_bootstrap(self.consumer, second_writes)
        after = {relative: (self.consumer / relative).read_bytes() for relative in TEMPLATE_PATHS}
        self.assertEqual(before, after)

    def test_completed_audit_is_current_and_authored_docs_remain_owned(self) -> None:
        _, writes = self.plan()
        write_project_bootstrap(self.consumer, writes)
        audit = self.consumer / AUDIT_PATH
        audit.write_text(
            audit.read_text(encoding="utf-8").replace("status=pending", "status=complete")
            + "\nConfirmed by repository evidence.\n",
            encoding="utf-8",
        )
        business = self.consumer / "docs/project-handoff/business-processes.md"
        business.write_bytes(b"repository-owned\r\ncontent")
        state, second_writes = self.plan()
        self.assertEqual("current", state["status"])
        self.assertEqual("complete", state["audit_status"])
        self.assertEqual({}, second_writes)
        self.assertEqual(b"repository-owned\r\ncontent", business.read_bytes())

    def test_existing_config_without_navigation_is_stale_and_never_prepared(self) -> None:
        config = self.consumer / CONFIG_PATH
        config.parent.mkdir(parents=True)
        original = b"schema: evidence-core\r\ncontext: custom"
        config.write_bytes(original)
        state, writes = self.plan()
        self.assertEqual("missing", state["status"])
        self.assertNotIn(config, writes)
        self.assertTrue(any(issue["kind"] == "config-navigation" for issue in state["issues"]))
        write_project_bootstrap(self.consumer, writes)
        state, writes = self.plan()
        self.assertEqual("stale", state["status"])
        self.assertEqual({}, writes)
        self.assertEqual(original, config.read_bytes())

    def test_config_requires_root_schema_literal_context_and_distinct_active_reference(self) -> None:
        _, writes = self.plan()
        write_project_bootstrap(self.consumer, writes)
        config = self.consumer / CONFIG_PATH
        invalid_configs = (
            "# schema: evidence-core\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core\n# docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\ncontext: |\n  unrelated\n",
            "schema: evidence-core\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core#not-comment\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core\nschema: wrong\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core\n\"schema\": wrong\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\ncontext: |\n  conflicting\n",
            "schema: evidence-core\ncontext: |\n  docs/project-handoff/ openspec/specs/ openspec/changes/archived/ openspec/changes/archive/ Git history\n",
            "schema: evidence-core\ncontext: |\n\tdocs/project-handoff/ openspec/specs/ openspec/changes/ openspec/changes/archive/ Git history\n",
        )
        for text in invalid_configs:
            with self.subTest(text=text):
                config.write_text(text, encoding="utf-8")
                state, prepared = self.plan()
                self.assertEqual("stale", state["status"])
                self.assertEqual({}, prepared)
                self.assertTrue(any(issue["kind"] == "config-navigation" for issue in state["issues"]))
                self.assertEqual(text, config.read_text(encoding="utf-8"))

    def test_missing_audit_marker_is_stale_without_rewrite(self) -> None:
        _, writes = self.plan()
        write_project_bootstrap(self.consumer, writes)
        audit = self.consumer / AUDIT_PATH
        audit.write_text("# Existing audit\n", encoding="utf-8")
        state, writes = self.plan()
        self.assertEqual("stale", state["status"])
        self.assertIsNone(state["audit_status"])
        self.assertEqual({}, writes)

    def test_malformed_or_duplicate_audit_marker_is_conflict(self) -> None:
        _, writes = self.plan()
        write_project_bootstrap(self.consumer, writes)
        audit = self.consumer / AUDIT_PATH
        for text in (
            "<!-- codex-openspec-project-audit:v2 status=pending -->\n",
            "<!-- codex-openspec-project-audit:v1 status=pending -->\n"
            "<!-- codex-openspec-project-audit:v1 status=complete -->\n",
        ):
            audit.write_text(text, encoding="utf-8")
            state, prepared = self.plan()
            self.assertEqual("conflict", state["status"])
            self.assertEqual({}, prepared)

    def test_invalid_utf8_and_non_file_paths_are_conflicts(self) -> None:
        config = self.consumer / CONFIG_PATH
        config.parent.mkdir(parents=True)
        config.write_bytes(b"\xff")
        state, _ = self.plan()
        self.assertEqual("conflict", state["status"])
        self.assertTrue(any(issue["kind"] == "encoding" for issue in state["issues"]))

        config.unlink()
        config.mkdir()
        state, _ = self.plan()
        self.assertEqual("conflict", state["status"])
        self.assertTrue(any(issue["kind"] == "not-file" for issue in state["issues"]))

    def test_symlink_escape_is_conflict(self) -> None:
        outside = self.temp / "outside"
        outside.mkdir()
        docs = self.consumer / "docs"
        try:
            docs.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        state, _ = self.plan()
        self.assertEqual("conflict", state["status"])
        self.assertTrue(any(issue["kind"] == "symlink" for issue in state["issues"]))

    def test_writer_never_overwrites_file_created_after_preflight(self) -> None:
        _, writes = self.plan()
        target = next(iter(writes))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"race-winner")
        with self.assertRaises(PackageError):
            write_project_bootstrap(self.consumer, writes)
        self.assertEqual(b"race-winner", target.read_bytes())

    def test_writer_rejects_parent_symlink_substitution_without_external_files(self) -> None:
        _, writes = self.plan()
        outside = self.temp / "outside"
        outside.mkdir()
        docs = self.consumer / "docs"
        try:
            docs.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        with self.assertRaises(PackageError):
            write_project_bootstrap(self.consumer, writes)
        self.assertEqual([], list(outside.rglob("*")))

    def test_failure_before_audit_publish_removes_created_empty_parents(self) -> None:
        _, writes = self.plan()
        initial_audit = next(body for path, body in writes.items() if path.as_posix().endswith(AUDIT_PATH))
        with mock.patch("workflow_project_bootstrap.os.link", side_effect=OSError("simulated publish failure")):
            with self.assertRaises(OSError):
                write_project_bootstrap(self.consumer, writes)
        self.assertFalse((self.consumer / "docs").exists())
        _, retry_writes = self.plan()
        retry_audit = next(body for path, body in retry_writes.items() if path.as_posix().endswith(AUDIT_PATH))
        self.assertEqual(initial_audit, retry_audit)


if __name__ == "__main__":
    unittest.main()
