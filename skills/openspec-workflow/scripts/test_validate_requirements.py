import tempfile
import unittest
from pathlib import Path

from validate_requirements import format_traceability_matrix, validate_change


class RequirementValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def make_change(
        self,
        spec: str,
        proposal: str = "## Why\nConfirmed change.\n\n## Evidence\n- USER-001: requested export.\n",
        design: str | None = None,
        schema: str = "evidence-core",
        tasks: str | None = None,
        review_mode: str | None = None,
    ) -> Path:
        repo = Path(self.temp_dir.name) / "repo"
        root = repo / "openspec" / "changes" / "sample"
        (root / "specs" / "sample").mkdir(parents=True, exist_ok=True)
        metadata = f"schema: {schema}\n"
        if review_mode:
            metadata += f"review_contract: {review_mode}\n"
        (root / ".openspec.yaml").write_text(metadata, encoding="utf-8")
        (root / "proposal.md").write_text(proposal, encoding="utf-8")
        (root / "specs" / "sample" / "spec.md").write_text(spec, encoding="utf-8")
        if design is not None:
            (root / "design.md").write_text(design, encoding="utf-8")
        if tasks is not None:
            (root / "tasks.md").write_text(tasks, encoding="utf-8")
        (repo / "contract.txt").write_text("first\nsecond\n", encoding="utf-8")
        return root

    def test_accepted_sourced_requirement_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\n"
            "The system SHALL export.\n\n#### Scenario: Export\n- **WHEN** requested\n- **THEN** exported\n"
        ))
        self.assertEqual([], errors)

    def test_multiple_accepted_sources_pass(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001, decision:DEC-001\n"
            "The system SHALL export CSV.\n",
            proposal=(
                "## Evidence\n- USER-001: requested export.\n\n## Decisions\n\n"
                "### DEC-001: Export is CSV\n**Status:** accepted\n**Source:** user:USER-001\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_one_invalid_source_in_list_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001, decision:DEC-404\n"
            "The system SHALL export.\n"
        ))
        self.assertTrue(any("missing decision 'DEC-404'" in error for error in errors))

    def test_unsourced_requirement_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("no Source" in error for error in errors))

    def test_proposed_requirement_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** proposed\n**Source:** user:USER-001\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("not accepted" in error for error in errors))

    def test_hypothesis_source_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** hypothesis:likely\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("unsupported Source" in error for error in errors))

    def test_open_question_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal="## Open Questions\n\n- [ ] Q-001: Which format?\n",
        ))
        self.assertTrue(any("blocking question" in error for error in errors))

    def test_metadata_hidden_in_scenario_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\nThe system SHALL export.\n"
            "\n#### Scenario: Export\n**Status:** accepted\n**Source:** user:USER-001\n"
            "- **WHEN** requested\n- **THEN** exported\n"
        ))
        self.assertTrue(any("no Status" in error for error in errors))
        self.assertTrue(any("no Source" in error for error in errors))

    def test_accepted_sourced_rename_only_passes(self):
        errors = validate_change(self.make_change(
            "## RENAMED Requirements\n\n**Status:** accepted\n**Source:** user:USER-001\n"
            "- FROM: `### Requirement: Old name`\n- TO: `### Requirement: New name`\n"
        ))
        self.assertEqual([], errors)

    def test_unsourced_rename_only_fails(self):
        errors = validate_change(self.make_change(
            "## RENAMED Requirements\n\n**Status:** accepted\n"
            "- FROM: `### Requirement: Old name`\n- TO: `### Requirement: New name`\n"
        ))
        self.assertTrue(any("RENAMED section has no Source" in error for error in errors))


    def test_noncanonical_design_decision_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            design="## Decisions\n\n### D-001 — CSV format\nUse CSV.\n",
        ))
        self.assertTrue(any("noncanonical decision heading" in error for error in errors))

    def test_accepted_existing_decision_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** decision:DEC-001\nThe system SHALL export.\n",
            proposal=(
                "## Evidence\n- USER-001: requested export.\n\n## Decisions\n\n"
                "### DEC-001: Export is CSV\n**Status:** accepted\n**Source:** user:USER-001\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_duplicate_decision_id_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** decision:DEC-001\nThe system SHALL export.\n",
            proposal=(
                "## Evidence\n- USER-001: requested export.\n\n## Decisions\n\n"
                "### DEC-001: CSV\n**Status:** accepted\n**Source:** user:USER-001\n\n"
                "### DEC-001: JSON\n**Status:** accepted\n**Source:** user:USER-001\n"
            ),
        ))
        self.assertTrue(any("duplicate decision" in error for error in errors))

    def test_missing_decision_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** decision:DEC-404\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("missing decision 'DEC-404'" in error for error in errors))

    def test_proposed_decision_blocks_change(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** decision:DEC-001\nThe system SHALL export.\n",
            proposal=(
                "## Evidence\n- USER-001: requested export.\n\n## Decisions\n\n"
                "### DEC-001: Export is CSV\n**Status:** proposed\n**Source:** user:USER-001\n"
            ),
        ))
        self.assertTrue(any("decision 'DEC-001' is not accepted" in error for error in errors))
        self.assertTrue(any("unaccepted decision 'DEC-001'" in error for error in errors))

    def test_accepted_repo_backed_decision_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** decision:DEC-001\nThe system SHALL export.\n",
            proposal=(
                "## Evidence\n- USER-001: requested export.\n\n## Decisions\n\n"
                "### DEC-001: CSV\n**Status:** accepted\n**Source:** repo:contract.txt:1\n"
            ),
        ))
        self.assertTrue(any("must use explicit user" in error for error in errors))

    def test_missing_user_evidence_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-404\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("missing user evidence 'USER-404'" in error for error in errors))

    def test_repo_line_is_observational_not_requirement_authority(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** repo:contract.txt:2\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("Source is observational" in error for error in errors))

    def test_repo_source_outside_repository_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** repo:../contract.txt:1\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("escapes repository" in error for error in errors))

    def test_missing_repo_source_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** repo:missing.txt:1\nThe system SHALL export.\n"
        ))
        self.assertTrue(any("repo Source file not found" in error for error in errors))

    def test_alternative_blocking_question_forms_fail(self):
        questions = (
            "* [ ] Q-002: Which format?",
            "1. [ ] Q-003: Which format?",
            "### Q-004: Which format?",
        )
        for question in questions:
            with self.subTest(question=question):
                errors = validate_change(self.make_change(
                    "## ADDED Requirements\n\n### Requirement: Export\n"
                    "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
                    proposal=(
                        "## Evidence\n- USER-001: requested export.\n\n"
                        f"## Open Questions\n\n{question}\n"
                    ),
                ))
                self.assertTrue(any("blocking question" in error for error in errors))

    def test_explicit_legacy_tasks_without_review_contract_remain_valid(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks="## 1. Work\n\n- [ ] 1.1 Implement export.\n",
            review_mode="legacy",
        ))
        self.assertEqual([], errors)

    def test_missing_review_contract_is_not_implicitly_legacy(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks="## 1. Work\n\n- [ ] 1.1 Implement export.\n",
        ))
        self.assertTrue(any("requires the review contract marker" in error for error in errors))

    def test_core_review_contract_requires_one_final_checkpoint(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks="<!-- openspec-review-contract:v1 -->\n\n- [ ] 1.1 Implement export.\n",
        ))
        self.assertTrue(any("requires exactly one final checkpoint" in error for error in errors))

    def test_valid_core_review_contract_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [ ] 1.1 Implement export.\n"
                "- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_heavy_review_contract_requires_wave_and_final(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [ ] 1.1 Implement export.\n"
                "- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("requires at least one explicit openspec-wave section" in error for error in errors))

    def test_valid_heavy_review_contract_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 Implement export.\n"
                "- [ ] 1.2 <!-- openspec-review:wave --> Review wave.\n"
                "## 2. <!-- openspec-wave:ui --> UI\n\n"
                "- [ ] 2.1 Implement UI.\n"
                "- [ ] 2.2 <!-- openspec-review:wave --> Review wave.\n"
                "- [ ] 3.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_completed_wave_cannot_skip_incomplete_wave_task(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:wave --> Review wave.\n"
                "- [ ] 2.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("incomplete tasks in its wave" in error for error in errors))

    def test_completed_final_cannot_skip_earlier_task(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [ ] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("earlier incomplete tasks" in error for error in errors))

    def test_final_checkpoint_must_be_last_checkbox(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [ ] 1.1 <!-- openspec-review:final --> Review full diff.\n"
                "- [ ] 1.2 Extra work.\n"
            ),
        ))
        self.assertTrue(any("must be the last task checkbox" in error for error in errors))

    def test_review_marker_must_be_on_checkbox(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "<!-- openspec-review:final -->\n"
            ),
        ))
        self.assertTrue(any("must be on a task checkbox" in error for error in errors))

    def test_heavy_wave_requires_implementation_task(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "## 1. <!-- openspec-wave:empty --> Empty\n\n"
                "- [ ] 1.1 <!-- openspec-review:wave --> Review wave.\n"
                "- [ ] 2.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("requires at least one implementation task" in error for error in errors))

    def test_v1_heavy_each_wave_still_requires_checkpoint(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 Implement backend.\n"
                "- [ ] 1.2 <!-- openspec-review:wave --> Review backend.\n"
                "## 2. <!-- openspec-wave:ui --> UI\n\n"
                "- [ ] 2.1 Implement UI.\n"
                "- [ ] 3.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("wave 'ui' requires exactly one wave checkpoint" in error for error in errors))

    def test_v2_heavy_each_wave_still_requires_checkpoint(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=(
                "## Why\nConfirmed legacy review behavior.\n\n"
                "## Evidence\n- USER-001: requested export.\n\n"
                "## UI Contract\n\n**Mode:** none\n"
            ),
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v2 -->\nUI contract: none\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 Implement backend.\n"
                "- [ ] 2.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("wave 'backend' requires exactly one wave checkpoint" in error for error in errors))

    def test_heavy_wave_rejects_duplicate_intermediate_reviews(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**ID:** REQ-001\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=(
                "## Why\nConfirmed risk-driven review behavior.\n\n"
                "## Evidence\n- USER-001: requested export.\n\n"
                "## UI Contract\n\n**Mode:** none\n"
            ),
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=run export test --> Implement backend.\n"
                "- [ ] 1.2 <!-- openspec-review:wave --> Review contract.\n"
                "- [ ] 1.3 <!-- openspec-review:wave --> Review implementation.\n"
                "- [ ] 2.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertTrue(any("allows at most one wave checkpoint" in error for error in errors))

    def test_heavy_final_only_review_contract_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**ID:** REQ-001\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=(
                "## Why\nConfirmed risk-driven review behavior.\n\n"
                "## Evidence\n- USER-001: requested export.\n\n"
                "## UI Contract\n\n**Mode:** none\n"
            ),
            schema="evidence-heavy",
            tasks=(
                "<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n"
                "## 1. <!-- openspec-wave:backend --> Backend\n\n"
                "- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=run backend test --> Implement backend.\n"
                "## 2. <!-- openspec-wave:integration --> Integration\n\n"
                "- [ ] 2.1 <!-- openspec-trace: requirements=REQ-001; verification=run integration test --> Integrate backend.\n"
                "- [ ] 3.1 <!-- openspec-review:final --> Review full diff.\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_duplicate_evidence_id_fails(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal="## Evidence\n- USER-001: first authority.\n- USER-001: different authority.\n",
        ))
        self.assertTrue(any("duplicate evidence id 'USER-001'" in error for error in errors))

    def test_completed_final_requires_concrete_attestation(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [x] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:final --> done\n"
            ),
        ))
        self.assertTrue(any("requires concrete Coverage" in error for error in errors))

    def test_completed_final_with_concrete_attestation_passes(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [x] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:final --> Coverage: full pending diff; "
                "Requirements: REQ-001; Exclusions: none; Reviewer: reviewer-42.\n"
            ),
        ))
        self.assertEqual([], errors)

    def test_completed_final_rejects_blank_attestation_values(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [x] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:final --> Coverage: full pending diff; "
                "Requirements: ; Exclusions: ; Reviewer:\n"
            ),
        ))
        self.assertTrue(any("requires concrete Coverage" in error for error in errors))

    def test_completed_final_rejects_tbd_reviewer(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            "**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            tasks=(
                "<!-- openspec-review-contract:v1 -->\n\n"
                "- [x] 1.1 Implement export.\n"
                "- [x] 1.2 <!-- openspec-review:final --> Coverage: full pending diff; "
                "Requirements: REQ-001; Exclusions: none; Reviewer: TBD\n"
            ),
        ))
        self.assertTrue(any("requires concrete Coverage" in error for error in errors))

    @staticmethod
    def material_ui_proposal() -> str:
        return (
            "## Why\nConfirmed material interface change with enough detail for strict validation.\n\n"
            "## Evidence\n- USER-001: requested export.\n\n"
            "## UI Contract\n**Mode:** material\n**Artifact:** docs/mock.html\n"
            "**Authority:** user:USER-001\n**Theme:** light\n"
            "**Viewports:** 1440x900, 390x844\n"
            "**States:** loading, success, failure\n"
            "**Data:** inspected API fixture with maximum cardinality\n"
        )

    @staticmethod
    def v2_tasks(mode: str = "material", ui_review: str | None = None) -> str:
        rows = [
            "<!-- openspec-review-contract:v2 -->",
            f"UI contract: {mode}",
            "",
            "- [ ] 1.1 Implement export.",
        ]
        if ui_review is not None:
            rows.append(ui_review)
        rows.append("- [ ] 1.3 <!-- openspec-review:final --> Review full diff.")
        return "\n".join(rows) + "\n"

    def test_v2_non_ui_contract_passes(self):
        proposal = "## Why\nConfirmed bounded backend change with enough detail for validation.\n\n## Evidence\n- USER-001: requested export.\n\n## UI Contract\n**Mode:** none\n"
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=proposal,
            tasks=self.v2_tasks(mode="none"),
        ))
        self.assertEqual([], errors)

    def test_v2_marker_is_found_after_leading_comment(self):
        proposal = "## Why\nConfirmed bounded backend change with enough detail for validation.\n\n## Evidence\n- USER-001: requested export.\n\n## UI Contract\n**Mode:** none\n"
        tasks = "<!-- generated header -->\n" + self.v2_tasks(mode="none")
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=proposal,
            tasks=tasks,
        ))
        self.assertEqual([], errors)

    def test_v2_material_cannot_be_declared_none_in_tasks(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(mode="none"),
        ))
        self.assertTrue(any("mode must match" in error for error in errors))

    def test_v2_material_requires_concrete_proposal_fields(self):
        proposal = self.material_ui_proposal().replace("**Data:** inspected API fixture with maximum cardinality", "**Data:** TBD")
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=proposal,
            tasks=self.v2_tasks(mode="material", ui_review="- [ ] 1.2 UI review: compare render."),
        ))
        self.assertTrue(any("requires concrete Artifact" in error for error in errors))

    def test_v2_material_requires_ui_checkpoint(self):
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(mode="material"),
        ))
        self.assertTrue(any("requires exactly one UI review" in error for error in errors))

    def test_v2_completed_ui_rejects_empty_attestation(self):
        review = "- [x] 1.2 UI review: Artifact: ; Theme: ; Viewports: ; States: ; Data: ; Evidence: ; Comparison: ; Discrepancies: ; Reviewer:"
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(ui_review=review),
        ))
        self.assertTrue(any("concrete visual attestation" in error for error in errors))

    def test_v2_completed_ui_with_concrete_attestation_passes(self):
        review = (
            "- [x] 1.2 UI review: Artifact: docs/mock.html; Theme: light; "
            "Viewports: 1440x900, 390x844; States: loading, success, failure; "
            "Data: max-cardinality API fixture; Evidence: output/ui-light.png; "
            "Comparison: side-by-side inspected; Discrepancies: none; Reviewer: reviewer-42"
        )
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(ui_review=review),
        ))
        self.assertEqual([], errors)
    def test_v2_completed_ui_is_case_insensitive(self):
        review = (
            "- [x] 1.2 UI Review: Artifact: docs/mock.html; Theme: light; "
            "Viewports: 1440x900, 390x844; States: loading, success, failure; "
            "Data: max-cardinality API fixture; Evidence: output/ui-light.png; "
            "Comparison: side-by-side inspected; Discrepancies: none; Reviewer: reviewer-42"
        )
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(ui_review=review),
        ))
        self.assertEqual([], errors)

    def test_v2_material_rejects_dash_proposal_placeholder(self):
        proposal = self.material_ui_proposal().replace("**Artifact:** docs/mock.html", "**Artifact:** -")
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=proposal,
            tasks=self.v2_tasks(ui_review="- [ ] 1.2 UI review: compare render."),
        ))
        self.assertTrue(any("requires concrete Artifact" in error for error in errors))

    def test_v2_completed_ui_rejects_dash_attestation(self):
        review = "- [x] 1.2 UI review: Artifact: -; Theme: -; Viewports: -; States: -; Data: -; Evidence: -; Comparison: -; Discrepancies: -; Reviewer: -"
        errors = validate_change(self.make_change(
            "## ADDED Requirements\n\n### Requirement: Export\n**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n",
            proposal=self.material_ui_proposal(),
            tasks=self.v2_tasks(ui_review=review),
        ))
        self.assertTrue(any("concrete visual attestation" in error for error in errors))

    def test_v3_traceability_gate_and_matrix(self):
        proposal = ('## Evidence\n- USER-001: requested CSV export.\n\n## UI Contract\n**Mode:** none\n\n'
                    '## Decisions\n### DEC-001: CSV format\n**Status:** accepted\n**Source:** user:USER-001\n')
        spec = ('## ADDED Requirements\n\n### Requirement: Export\n**ID:** REQ-001\n'
                '**Status:** accepted\n**Source:** decision:DEC-001\nThe system SHALL export.\n')
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=run export integration test and assert valid CSV --> Implement export.\n'
                 '- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n')
        change = self.make_change(spec, proposal=proposal, tasks=tasks)
        self.assertEqual([], validate_change(change))
        self.assertIn('| REQ-001 | DEC-001 |', format_traceability_matrix(change))

    def test_v3_fails_without_traced_task(self):
        proposal = '## Evidence\n- USER-001: requested export.\n\n## UI Contract\n**Mode:** none\n'
        spec = ('## ADDED Requirements\n\n### Requirement: Export\n**ID:** REQ-001\n'
                '**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n')
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n- [ ] 1.1 Implement export.\n'
                 '- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n')
        errors = validate_change(self.make_change(spec, proposal=proposal, tasks=tasks))
        self.assertTrue(any('has no traced implementation task' in error for error in errors))

    def test_v3_fails_placeholder_verification(self):
        proposal = '## Evidence\n- USER-001: requested export.\n\n## UI Contract\n**Mode:** none\n'
        spec = ('## ADDED Requirements\n\n### Requirement: Export\n**ID:** REQ-001\n'
                '**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n')
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=TBD --> Implement export.\n'
                 '- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n')
        errors = validate_change(self.make_change(spec, proposal=proposal, tasks=tasks))
        self.assertTrue(any('requires concrete planned verification' in error for error in errors))

    def test_v3_fails_extra_untraced_implementation_task(self):
        proposal = '## Evidence\n- USER-001: requested export.\n\n## UI Contract\n**Mode:** none\n'
        spec = ('## ADDED Requirements\n\n### Requirement: Export\n**ID:** REQ-001\n'
                '**Status:** accepted\n**Source:** user:USER-001\nThe system SHALL export.\n')
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=run export integration test --> Implement export.\n'
                 '- [ ] 1.2 Add unrelated implementation.\n'
                 '- [ ] 1.3 <!-- openspec-review:final --> Review full diff.\n')
        errors = validate_change(self.make_change(spec, proposal=proposal, tasks=tasks))
        self.assertTrue(any('implementation task requires an openspec-trace' in error for error in errors))

    def test_v3_skip_specs_allows_none_with_concrete_verification(self):
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 Update tooling. <!-- openspec-trace: requirements=none; verification=run tool self-test -->\n'
                 '- [ ] 1.2 <!-- openspec-review:final --> Final checkpoint.\n')
        proposal = '## Evidence\n- USER-001: requested tooling update.\n\n## UI Contract\n**Mode:** none\n'
        change = self.make_change('', proposal=proposal, tasks=tasks)
        (change / 'specs' / 'sample' / 'spec.md').unlink()
        metadata = change / '.openspec.yaml'
        metadata.write_text('schema: evidence-core\nskip_specs: true\n', encoding='utf-8')
        self.assertEqual([], validate_change(change))

    def test_v3_none_trace_requires_skip_specs(self):
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 Update tooling. <!-- openspec-trace: requirements=none; verification=run tool self-test -->\n')
        errors = validate_change(self.make_change('', tasks=tasks))
        self.assertTrue(any('requires explicit skip_specs: true' in error for error in errors))

    def test_v3_skip_specs_rejects_placeholder_verification(self):
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 Update tooling. <!-- openspec-trace: requirements=none; verification=TBD -->\n')
        change = self.make_change('', tasks=tasks)
        (change / 'specs' / 'sample' / 'spec.md').unlink()
        metadata = change / '.openspec.yaml'
        metadata.write_text('schema: evidence-core\nskip_specs: true\n', encoding='utf-8')
        errors = validate_change(change)
        self.assertTrue(any('requires concrete planned verification' in error for error in errors))
    def test_v3_traces_accepted_rename(self):
        proposal = '## Evidence\n- USER-001: requested rename.\n\n## UI Contract\n**Mode:** none\n'
        spec = ('## RENAMED Requirements\n\n**ID:** REQ-REN-001\n**Status:** accepted\n'
                '**Source:** user:USER-001\n- FROM: `### Requirement: Old`\n- TO: `### Requirement: New`\n')
        tasks = ('<!-- openspec-review-contract:v3 -->\nUI contract: none\n\n'
                 '- [ ] 1.1 <!-- openspec-trace: requirements=REQ-REN-001; verification=run contract rename test --> Rename contract.\n'
                 '- [ ] 1.2 <!-- openspec-review:final --> Review full diff.\n')
        self.assertEqual([], validate_change(self.make_change(spec, proposal=proposal, tasks=tasks)))


if __name__ == "__main__":
    unittest.main()
