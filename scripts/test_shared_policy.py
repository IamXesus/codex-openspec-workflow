from __future__ import annotations

import re
import unittest
from pathlib import Path

import workflow_package as package
from workflow_package_state import source_manifest


ROOT = Path(__file__).resolve().parent.parent


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def normalized(relative: str) -> str:
    return re.sub(r"[`*_\-]+", " ", read(relative).lower())


class SharedPlacementPolicyTests(unittest.TestCase):
    direct_assets = (
        "skills/coding-guardrails/SKILL.md",
        "skills/openspec-workflow/SKILL.md",
        "policy/AGENTS.fragment.md",
    )
    schemas = (
        "openspec/schemas/evidence-core/schema.yaml",
        "openspec/schemas/evidence-heavy/schema.yaml",
    )

    def assert_general_placement_contract(self, relative: str) -> None:
        text = normalized(relative)
        for concept in (
            "neighboring feature structure",
            "namespace",
            "module boundar",
            "dependency registration",
            "architecture test",
            "feature and cohesive responsibility",
            "interfaces",
            "implementations",
            "incidental",
            "evidence heavy",
            "architecture review",
            "consumer",
        ):
            self.assertIn(concept, text, f"{relative} lacks {concept!r}")

    def test_direct_and_openspec_skills_share_the_general_guardrail(self) -> None:
        for relative in self.direct_assets:
            with self.subTest(relative=relative):
                self.assert_general_placement_contract(relative)

    def test_both_schema_task_and_apply_instructions_receive_the_guardrail(self) -> None:
        for relative in self.schemas:
            with self.subTest(relative=relative):
                self.assert_general_placement_contract(relative)
                text = normalized(relative)
                for concept in (
                    "neighboring feature structure",
                    "dependency registration",
                    "interfaces/implementations",
                    "consumer",
                ):
                    self.assertGreaterEqual(
                        text.count(concept), 2, f"{relative} must carry {concept!r} in tasks and apply"
                    )

    def test_shared_assets_do_not_copy_consumer_specific_examples(self) -> None:
        reusable = (
            "README.md",
            "policy/AGENTS.fragment.md",
            *self.direct_assets[:2],
            *self.schemas,
        )
        forbidden = (
            "payflow",
            "palmetto",
            "invoiceocr",
            "paymentrequest",
            "integrations/onec",
            "docs/payflow-handoff",
        )
        for relative in reusable:
            text = read(relative).lower()
            for term in forbidden:
                self.assertNotIn(term, text, f"{relative} contains consumer-specific term {term!r}")

    def test_central_and_consumer_ownership_is_explicit(self) -> None:
        combined = (normalized("README.md") + "\n" + normalized("policy/AGENTS.fragment.md"))
        for concept in (
            "canonical upstream",
            "schemas and templates",
            "validators",
            "skills",
            "routing and lifecycle gates",
            "general authoring policy",
            "consumer repositories",
            "openspec context",
            "business and technical documentation",
            "deployment convention",
            "domain specific",
            "project local schemas",
            "shadow",
        ):
            self.assertIn(concept, combined, f"shared ownership boundary lacks {concept!r}")

    def test_managed_policy_requires_host_neutral_project_audit_and_maintenance(self) -> None:
        text = normalized("policy/AGENTS.fragment.md")
        for concept in (
            "project knowledge bootstrap",
            "docs/project handoff",
            "openspec/config.yaml",
            "status=pending",
            "before substantial implementation",
            "confirmed facts",
            "open questions",
            "business processes",
            "integrations",
            "technical architecture",
            "open issues",
            "normative openspec",
            "host neutral",
            "codex",
            "orca",
            "omnigent",
        ):
            self.assertIn(concept, text, f"managed project-knowledge policy lacks {concept!r}")

    def test_readme_matches_distribution_contract(self) -> None:
        text = normalized("README.md")
        for concept in (
            "1.1.1",
            "single version source",
            "current",
            "stale",
            "missing",
            "conflict",
            "update command",
            "update argv",
            "target orca",
            "backup root",
            "consumer repo",
            "read only",
            "managed block",
            "per consumer policy receipt",
            "never pulls git",
        ):
            self.assertIn(concept, text, f"README lacks executable contract concept {concept!r}")

    def test_portable_skill_has_one_explicit_platform_executable_contract(self) -> None:
        text = read("skills/openspec-workflow/SKILL.md")
        cmd_lines = [line for line in text.splitlines() if "openspec.cmd" in line]
        self.assertEqual(1, len(cmd_lines))
        self.assertIn("Windows", cmd_lines[0])
        self.assertIn("POSIX/Linux use `openspec`", text)
        for operation in ("new", "status", "instructions", "init"):
            self.assertIn(f"<openspec> {operation}", text)
        self.assertNotRegex(text, r"`openspec\.cmd\s+(?:new|status|instructions|init|apply|check)\b")

    def test_posix_wrapper_is_kept_with_lf_endings(self) -> None:
        self.assertIn("*.sh text eol=lf", read(".gitattributes").splitlines())
        self.assertNotIn(b"\r\n", (ROOT / "scripts" / "install.sh").read_bytes())

    def test_documented_cli_and_managed_policy_boundary_are_executable(self) -> None:
        parser = package.parser()
        for target in ("codex", "orca", "omnigent"):
            args = parser.parse_args(
                [
                    "check",
                    "--target",
                    target,
                    "--agent-root",
                    "agent-root",
                    "--schema-root",
                    "schema-root",
                    "--consumer-repo",
                    "consumer",
                    "--json",
                ]
            )
            self.assertEqual(target, args.target)
            self.assertTrue(args.json)

        install = parser.parse_args(
            ["install", "--target", "orca", "--backup-root", "backup", "--consumer-repo", "consumer", "--dry-run"]
        )
        rollback = parser.parse_args(
            ["rollback", "--target", "orca", "--backup-root", "backup"]
        )
        self.assertTrue(install.dry_run)
        self.assertEqual("consumer", install.consumer_repo)
        self.assertEqual("backup", rollback.backup_root)

        for relative in (
            "scripts/workflow_package.py",
            "scripts/install.ps1",
            "scripts/install.sh",
            "scripts/validate.ps1",
            "policy/AGENTS.fragment.md",
            "openspec/schemas/evidence-core/schema.yaml",
            "openspec/schemas/evidence-heavy/schema.yaml",
        ):
            self.assertTrue((ROOT / relative).is_file(), f"README asset is missing: {relative}")

        installed_paths = {
            *source_manifest(ROOT, "agent-skills"),
            *source_manifest(ROOT, "openspec-schemas"),
        }
        self.assertFalse(any("agents.fragment" in path.lower() for path in installed_paths))
        self.assertEqual("1.1.1", package.load_version(ROOT))


if __name__ == "__main__":
    unittest.main()
