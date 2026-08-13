import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from validate_change import run_gate


class CompleteGateTests(unittest.TestCase):
    def make_repo(self, source: str = "user:USER-001") -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        repo = Path(temporary.name)
        change = repo / "openspec" / "changes" / "sample"
        spec = change / "specs" / "sample" / "spec.md"
        spec.parent.mkdir(parents=True)
        (change / "proposal.md").write_text(
            "## Evidence\n- USER-001: requested export.\n",
            encoding="utf-8",
        )
        spec.write_text(
            "## ADDED Requirements\n\n### Requirement: Export\n"
            f"**Status:** accepted\n**Source:** {source}\nThe system SHALL export.\n",
            encoding="utf-8",
        )
        return repo

    @patch("validate_change.shutil.which", return_value="openspec")
    @patch(
        "validate_change.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0),
    )
    def test_complete_gate_passes_only_when_both_validators_pass(self, _run, _which):
        self.assertEqual(0, run_gate(self.make_repo(), "sample"))

    @patch("validate_change.shutil.which", return_value="openspec")
    @patch(
        "validate_change.subprocess.run",
        return_value=subprocess.CompletedProcess([], 1),
    )
    def test_native_failure_blocks_gate(self, _run, _which):
        self.assertEqual(2, run_gate(self.make_repo(), "sample"))

    @patch("validate_change.shutil.which", return_value="openspec")
    @patch(
        "validate_change.subprocess.run",
        return_value=subprocess.CompletedProcess([], 0),
    )
    def test_semantic_failure_blocks_gate(self, _run, _which):
        self.assertEqual(2, run_gate(self.make_repo("user:USER-404"), "sample"))


if __name__ == "__main__":
    unittest.main()
