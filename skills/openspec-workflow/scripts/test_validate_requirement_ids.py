import tempfile
import unittest
from pathlib import Path

from validate_requirement_ids import main, validate_change_ids, validate_repository


def requirement(requirement_id: str, *, section: str = "Requirements") -> str:
    return (
        f"## {section}\n\n### Requirement: Example\n"
        f"**ID:** {requirement_id}\n**Status:** accepted\n**Source:** user:USER-001\n"
    )


class RequirementIdIntegrityTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        return Path(temporary.name)

    def write_spec(self, repo: Path, relative: str, text: str) -> Path:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def test_repository_rejects_duplicate_current_ids_with_both_locations(self):
        repo = self.make_repo()
        self.write_spec(repo, "openspec/specs/alpha/spec.md", requirement("REQ-SAME"))
        self.write_spec(repo, "openspec/specs/beta/spec.md", requirement("REQ-SAME"))

        errors = validate_repository(repo)

        self.assertEqual(1, len(errors))
        self.assertIn("openspec/specs/alpha/spec.md:4", errors[0])
        self.assertIn("openspec/specs/beta/spec.md:4", errors[0])

    def test_repository_ignores_archived_change_copies(self):
        repo = self.make_repo()
        self.write_spec(repo, "openspec/specs/alpha/spec.md", requirement("REQ-SAME"))
        self.write_spec(
            repo,
            "openspec/changes/archive/2026-01-01-alpha/specs/alpha/spec.md",
            requirement("REQ-SAME", section="ADDED Requirements"),
        )

        self.assertEqual([], validate_repository(repo))

    def test_cli_rejects_missing_repository(self):
        repo = self.make_repo() / "missing"

        self.assertEqual(2, main(["--repo", str(repo)]))

    def test_repository_rejects_directory_without_openspec(self):
        repo = self.make_repo()

        errors = validate_repository(repo)

        self.assertEqual(1, len(errors))
        self.assertIn("OpenSpec directory not found", errors[0])

    def test_repository_ignores_ids_in_fences_and_scenario_body(self):
        repo = self.make_repo()
        text = requirement("REQ-REAL") + (
            "\n#### Scenario: Documentation example\n"
            "- **WHEN** a fenced example is included\n"
            "- **THEN** it is not metadata\n\n"
            "```markdown\n### Requirement: Example only\n**ID:** REQ-REAL\n```\n"
            "**ID:** REQ-REAL\n"
        )
        self.write_spec(repo, "openspec/specs/alpha/spec.md", text)

        self.assertEqual([], validate_repository(repo))

    def test_change_rejects_added_id_that_exists_in_current_specs(self):
        repo = self.make_repo()
        self.write_spec(repo, "openspec/specs/alpha/spec.md", requirement("REQ-SAME"))
        change = repo / "openspec/changes/sample"
        self.write_spec(
            repo,
            "openspec/changes/sample/specs/beta/spec.md",
            requirement("REQ-SAME", section="ADDED Requirements"),
        )

        errors = validate_change_ids(repo, change)

        self.assertEqual(1, len(errors))
        self.assertIn("ADDED requirement id 'REQ-SAME' collides", errors[0])
        self.assertIn("openspec/specs/alpha/spec.md:4", errors[0])
        self.assertIn("openspec/changes/sample/specs/beta/spec.md:4", errors[0])

    def test_change_allows_modified_id_to_match_current_spec(self):
        repo = self.make_repo()
        self.write_spec(repo, "openspec/specs/alpha/spec.md", requirement("REQ-SAME"))
        change = repo / "openspec/changes/sample"
        self.write_spec(
            repo,
            "openspec/changes/sample/specs/alpha/spec.md",
            requirement("REQ-SAME", section="MODIFIED Requirements"),
        )

        self.assertEqual([], validate_change_ids(repo, change))


if __name__ == "__main__":
    unittest.main()
