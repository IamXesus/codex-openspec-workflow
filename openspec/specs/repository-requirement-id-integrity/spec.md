# repository-requirement-id-integrity Specification

## Purpose
Keep stable OpenSpec requirement identifiers unambiguous across current specifications and prevent active changes from introducing collisions during archive.
## Requirements
### Requirement: Current specification IDs are globally unique
**ID:** REQ-REPO-ID-INTEGRITY-001
**Status:** accepted
**Source:** user:USER-001
The repository requirement integrity gate SHALL fail when the same `REQ-*` identifier appears more than once under `openspec/specs/`, and its diagnostic SHALL identify every conflicting file and line.

#### Scenario: Duplicate current IDs
- **WHEN** two current specification requirement blocks declare the same `REQ-*` identifier
- **THEN** repository requirement integrity validation fails and reports both locations

#### Scenario: Archived history repeats an ID
- **WHEN** an archived change contains an identifier also present in current specifications
- **THEN** repository requirement integrity validation ignores the archived copy

### Requirement: Added requirements cannot collide before archive
**ID:** REQ-REPO-ID-INTEGRITY-002
**Status:** accepted
**Source:** user:USER-001
The active change gate SHALL fail when an `ADDED` requirement declares a `REQ-*` identifier already present under `openspec/specs/`, while permitting a `MODIFIED` requirement to retain the identifier of the current requirement it modifies.

#### Scenario: Added ID already exists
- **WHEN** an active change declares an `ADDED` requirement with an identifier found in current specifications
- **THEN** active change validation fails before archive and reports the active and current locations

#### Scenario: Modified requirement retains its ID
- **WHEN** an active change declares a `MODIFIED` requirement with the identifier of its current requirement
- **THEN** the collision rule does not reject that identifier reuse

### Requirement: Post-archive integrity is an explicit workflow gate
**ID:** REQ-REPO-ID-INTEGRITY-003
**Status:** accepted
**Source:** user:USER-001
The shared OpenSpec workflow SHALL instruct agents to run the repository requirement integrity gate after archive and before commit, release, or deployment claims.

#### Scenario: Archive completes
- **WHEN** an agent archives an OpenSpec change
- **THEN** it runs the standalone repository integrity gate before proceeding to commit, release, or deployment claims
