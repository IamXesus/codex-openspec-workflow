from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_openspec_architecture.py")
MARKER = "<!-- openspec-architecture-contract:v1 -->"


class ArchitectureContractTests(unittest.TestCase):
    def run_gate(
        self,
        proposal: str,
        *,
        design: str | None = None,
        tasks: str | None = None,
        phase: str = "apply",
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            change_dir = repo / "openspec" / "changes" / "fixture"
            change_dir.mkdir(parents=True)
            (change_dir / "proposal.md").write_text(proposal, encoding="utf-8")
            if design is not None:
                (change_dir / "design.md").write_text(design, encoding="utf-8")
            if tasks is not None:
                (change_dir / "tasks.md").write_text(tasks, encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--repo",
                    str(repo),
                    "--change",
                    "fixture",
                    "--phase",
                    phase,
                ],
                text=True,
                capture_output=True,
                check=False,
            )

    def test_none_is_ready_without_design(self) -> None:
        result = self.run_gate(
            f"{MARKER}\n**Architecture impact:** none\n"
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("impact=none", result.stdout)

    def test_material_template_defaults_are_not_ready(self) -> None:
        design = """## Component Ownership
**Inspected baseline:** not applicable
**Expected growth:** not applicable
**Existing responsibilities:** not applicable
**New responsibilities:** not applicable
**Transaction owner:** not applicable
**Boundary options:** not applicable
**Decision:** keep-cohesive
**Known cost:** none
**Ratchet scope:** no broad refactor
"""
        result = self.run_gate(
            f"{MARKER}\n**Architecture impact:** material\n",
            design=design,
            phase="planning",
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Inspected baseline", result.stderr)

    def test_material_apply_requires_complete_review_evidence(self) -> None:
        result = self.run_gate(
            f"{MARKER}\n**Architecture impact:** material\n",
            design=material_design(),
            tasks=(
                "- [x] <!-- openspec-review:architecture --> "
                "Reviewer: agent; Verdict: READY\n"
            ),
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("Coverage", result.stderr)
        self.assertIn("Exclusions", result.stderr)

    def test_material_apply_is_ready_with_complete_contract(self) -> None:
        result = self.run_gate(
            f"{MARKER}\n**Architecture impact:** material\n",
            design=material_design(),
            tasks=(
                "- [x] <!-- openspec-review:architecture --> "
                "Coverage: full; Growth: measured; Ownership: explicit; "
                "Findings: none; Exclusions: none; Reviewer: agent-2; "
                "Verdict: READY\n"
            ),
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("impact=material", result.stdout)


def material_design() -> str:
    return """## Component Ownership
**Inspected baseline:** src/Service.cs (1200 lines)
**Expected growth:** 180 production lines
**Existing responsibilities:** orchestration and persistence
**New responsibilities:** invoice allocation rules
**Transaction owner:** PaymentService
**Boundary options:** keep inline or extract AllocationPolicy
**Decision:** extract-collaborators
**Known cost:** one new collaborator and focused tests
**Ratchet scope:** only allocation behavior in this change
"""


if __name__ == "__main__":
    unittest.main()
