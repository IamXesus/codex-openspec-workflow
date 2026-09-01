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
    task_templates = (
        "openspec/schemas/evidence-core/templates/tasks.md",
        "openspec/schemas/evidence-heavy/templates/tasks.md",
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
        self.assertIn(package.load_version(ROOT), read("README.md"))
        for concept in (
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

    def test_continuous_flow_preserves_user_owned_pause_boundaries(self) -> None:
        assets = (
            "README.md",
            "policy/AGENTS.fragment.md",
            "skills/openspec-workflow/SKILL.md",
            "skills/openspec-workflow/agents/openai.yaml",
            *self.schemas,
        )
        combined = "\n".join(normalized(relative) for relative in assets)
        for concept in (
            "continuous",
            "automatically",
            "user owned",
            "plan only",
            "proposed decision",
            "open question",
            "external effect",
            "go",
            "independent read only review",
        ):
            self.assertIn(concept, combined, f"continuous workflow lacks {concept!r}")

        portable_contracts = "\n".join(read(relative).lower() for relative in assets)
        for obsolete in (
            "create exactly one ready artifact and stop",
            "advance planning one official openspec artifact at a time",
            "a planning request never carries authority into apply",
            "then stop for an independent read-only review before continuing",
        ):
            self.assertNotIn(obsolete, portable_contracts)

        skill = read("skills/openspec-workflow/SKILL.md").lower()
        self.assertIn("`<openspec> status` and `<openspec> instructions` loop directly", skill)
        self.assertIn("explicitly requested single-step helper", skill)

    def test_shared_contract_selects_minimum_sufficient_risk_driven_verification(self) -> None:
        authoring_assets = (
            "skills/openspec-workflow/SKILL.md",
            "skills/coding-guardrails/SKILL.md",
            *self.schemas,
        )
        for relative in authoring_assets:
            text = normalized(relative)
            with self.subTest(relative=relative):
                for concept in (
                    "minimum sufficient",
                    "existing check",
                    "vertical slice",
                    "distinct risk",
                    "failure mode",
                    "external boundaries",
                    "real provider",
                    "touched feature slice",
                    "separate explicit",
                    "full suite",
                    "test count",
                ):
                    self.assertIn(concept, text, f"{relative} lacks {concept!r}")

        for relative in self.schemas:
            text = normalized(relative)
            with self.subTest(relative=relative, phase="task-and-apply"):
                self.assertGreaterEqual(text.count("minimum sufficient"), 2)
                self.assertGreaterEqual(text.count("one concrete check may cover several traced tasks"), 2)

        for relative in self.task_templates:
            text = normalized(relative)
            with self.subTest(relative=relative):
                self.assertIn("minimum sufficient existing/shared/new/manual check", text)
                self.assertIn("one check may cover several traced tasks or requirements", text)

        review = normalized("skills/code-reviewer/SKILL.md")
        for concept in (
            "test delta",
            "distinct risk",
            "existing evidence",
            "faithful layer",
            "brittleness",
            "consolidation opportunity",
            "separate explicit",
            "test count",
        ):
            self.assertIn(concept, review, f"code reviewer lacks {concept!r}")

        self.assertIn("full diff", review)
        self.assertIn("заблокирован", review)
        self.assertIn("avoidable overlap", review)

        openspec_skill = read("skills/openspec-workflow/SKILL.md").lower()
        self.assertIn(
            "do not use test count, coverage, test-to-production loc, or mandatory mutation quotas",
            openspec_skill,
        )
        self.assertIn("do not create another verification artifact", openspec_skill)

    def test_heavy_review_orchestration_is_risk_driven_without_weakening_final_gate(self) -> None:
        decision_assets = (
            "skills/openspec-workflow/SKILL.md",
            "openspec/schemas/evidence-heavy/schema.yaml",
            "policy/AGENTS.fragment.md",
            "README.md",
        )
        combined = "\n".join(normalized(relative) for relative in decision_assets)
        for concept in (
            "material risk",
            "downstream dependency",
            "deterministic",
            "mechanical",
            "targeted continuation",
            "test/staging",
            "rollback",
            "full pending diff",
            "production release",
        ):
            self.assertIn(concept, combined, f"risk-driven review contract lacks {concept!r}")

        skill = normalized("skills/openspec-workflow/SKILL.md")
        for concept in (
            "pre ci",
            "stable changed file inventory",
            "do not spawn a fresh reviewer for every finding",
            "do not automatically stale unaffected",
        ):
            self.assertIn(concept, skill, f"workflow skill lacks {concept!r}")

        architecture = normalized("skills/architecture-review/SKILL.md")
        self.assertIn("next planned intermediate or final", architecture)
        self.assertIn("do not launch a separate architecture reviewer", architecture)
        self.assertIn("same full diff", architecture)

        heavy = normalized("openspec/schemas/evidence-heavy/schema.yaml")
        self.assertIn("at most one intermediate", heavy)
        self.assertIn("does not require the final release review", heavy)
        self.assertIn("merely because it is a", heavy)

        template = read("openspec/schemas/evidence-heavy/templates/tasks.md")
        active_wave_reviews = [
            line for line in template.splitlines()
            if re.match(r"^\s*-\s*\[[ xX]\].*openspec-review:wave", line)
        ]
        self.assertEqual([], active_wave_reviews, "new heavy plans must default to final-only review")
        self.assertIn("openspec-review:final", template)

        guardrails = read("skills/coding-guardrails/SKILL.md").lower()
        self.assertIn(
            "do not optimize to fixed test-count, coverage, test-to-production loc, or mandatory mutation quotas",
            guardrails,
        )
        self.assertIn("do not create a separate verification artifact", guardrails)

        for relative in self.schemas:
            schema = read(relative).lower()
            with self.subTest(relative=relative, rule="negative-policy"):
                self.assertIn(
                    "do not add a verification artifact, numeric quota, or mandatory mutation gate",
                    schema,
                )

        reviewer = read("skills/code-reviewer/SKILL.md").lower()
        self.assertIn(
            "не используй test count, coverage, test-to-production loc или обязательный mutation threshold",
            reviewer,
        )

        workflow = normalized("skills/openspec-workflow/SKILL.md")
        for concept in (
            "default to one final full pending diff code review",
            "does not remove the separate pre implementation architecture review",
            "early read only critic is advisory",
            "assigns a stable id",
            "complete blocking finding ledger in the session",
            "cheapest faithful focused check",
            "coherent stable batch",
            "one primary executor",
            "failure mode",
        ):
            self.assertIn(concept, workflow, f"workflow review economy lacks {concept!r}")

        policy = normalized("policy/AGENTS.fragment.md")
        for concept in (
            "default to one final full pending diff code review",
            "pre implementation architecture review",
            "early critic is advisory",
            "stable ids to every high and medium",
            "complete disposition ledger in the session",
            "coherent stable batch instead of after every fix",
        ):
            self.assertIn(concept, policy, f"managed policy lacks {concept!r}")

        guardrails = normalized("skills/coding-guardrails/SKILL.md")
        for concept in (
            "early critic as advisory input only",
            "default openspec implementation completion to one final full pending diff code review",
            "later work depends on an inspected material boundary",
            "session only ledger",
            "ledger for every reviewer assigned",
            "cheapest faithful focused check",
            "coherent stable slice",
            "one primary executor",
            "failure mode",
        ):
            self.assertIn(concept, guardrails, f"implementation guardrails lack {concept!r}")

        self.assertIn("стабильный id", reviewer)
        self.assertIn("все id уровня `high` и `medium`", reviewer)
        self.assertIn("completion review по умолчанию покрывает полный pending diff", reviewer)
        self.assertIn("intermediate review допустим только на material boundary", reviewer)
        self.assertIn("явно назови review advisory", reviewer)
        self.assertIn("не создаёт review-after-every-fix цикл", reviewer)
        self.assertIn("одну пачку связанных безопасных исправлений", reviewer)
        self.assertIn("самый дешёвый достоверный focused check", reviewer)
        self.assertIn("ci или full suite запущен на цельном стабильном batch", reviewer)

        for relative in self.schemas:
            schema = normalized(relative)
            with self.subTest(relative=relative, rule="review-and-ci-economy"):
                self.assertIn("early critic is advisory", schema)
                self.assertIn("stable id", schema)
                self.assertIn("coherent stable", schema)
                self.assertIn("failure mode", schema)
                self.assertIn("one primary executor", schema)

        policy = normalized("policy/AGENTS.fragment.md")
        self.assertIn("failure mode", policy)
        self.assertIn("one primary executor", policy)

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


if __name__ == "__main__":
    unittest.main()
