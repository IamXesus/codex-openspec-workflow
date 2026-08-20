## Purpose

Make the canonical reusable agent policy a safe, versioned part of explicit consumer adoption so a new project receives the workflow rules without sacrificing repository-owned instructions.

## ADDED Requirements

### Requirement: Explicit consumer policy adoption
**ID:** REQ-MPA-001
**Status:** accepted
**Source:** decision:DEC-001, decision:DEC-002, user:USER-003
When install is invoked with an explicit consumer repository, the package SHALL ensure that the consumer `AGENTS.md` contains exactly one package-managed policy block. It SHALL create the file when absent, append the block when the file contains only consumer-owned text, and preserve all text outside the managed block. Without an explicit consumer repository, install MUST NOT select or edit any consumer `AGENTS.md`.

#### Scenario: Consumer has no AGENTS file
- **WHEN** install selects a consumer repository whose root has no `AGENTS.md`
- **THEN** the installer creates `AGENTS.md` containing one marked copy of the canonical portable policy

#### Scenario: Consumer has repository-owned instructions
- **WHEN** install selects a consumer whose `AGENTS.md` has no managed block
- **THEN** the installer appends one managed policy block while preserving the pre-existing content

#### Scenario: Consumer already contains exactly the portable policy
- **WHEN** the whole unmarked `AGENTS.md` body equals the canonical portable policy after newline normalization
- **THEN** the installer adds managed receipt markers around that body without appending a duplicate policy copy

#### Scenario: Consumer contains the known unmarked 1.0.0 portable policy
- **WHEN** the whole unmarked `AGENTS.md` body matches the recorded `1.0.0` portable-policy hash apart from terminal blank lines
- **THEN** the installer replaces it with one current managed policy block without retaining or appending a duplicate legacy copy

#### Scenario: No consumer is selected
- **WHEN** install is invoked without `--consumer-repo`
- **THEN** shared skills and schemas retain their existing install behavior and no consumer file is selected or changed

### Requirement: Versioned managed-block update
**ID:** REQ-MPA-002
**Status:** accepted
**Source:** decision:DEC-002, decision:DEC-003
The managed block SHALL record the installed workflow version and hashes sufficient to distinguish an intact prior installation from a locally modified managed body. When the block is intact but its package version or canonical body differs from the selected central package, install SHALL replace only that block.

#### Scenario: Canonical policy has advanced
- **WHEN** an intact managed block records an older workflow version or canonical policy hash
- **THEN** install replaces only the marked block with the selected package version and policy body

#### Scenario: Current managed policy is reinstalled
- **WHEN** the managed block version, canonical hash, and body already match the selected package
- **THEN** install leaves `AGENTS.md` content unchanged

### Requirement: Policy conflicts fail before mutation
**ID:** REQ-MPA-003
**Status:** accepted
**Source:** decision:DEC-003
A consumer policy preflight SHALL classify a managed body whose content differs from its recorded installed hash, duplicated markers, partial markers, invalid marker metadata, or unreadable UTF-8 as `conflict`. Install MUST fail before changing shared roots or the consumer file when that preflight reports conflict.

#### Scenario: Managed body was edited locally
- **WHEN** text inside the managed block differs from the body hash recorded by its installation metadata
- **THEN** check reports `conflict` and install performs no shared-root or consumer mutation

#### Scenario: Managed markers are malformed
- **WHEN** `AGENTS.md` contains an unmatched, duplicated, or invalid managed marker
- **THEN** check reports `conflict` with the consumer policy path and install fails closed

### Requirement: Consumer policy freshness is actionable
**ID:** REQ-MPA-004
**Status:** accepted
**Source:** decision:DEC-004
When a consumer repository is selected, check SHALL report its policy path and one of `missing`, `current`, `stale`, or `conflict`. Missing, stale, or conflict policy state MUST make the overall check non-current. Remediation output for missing or stale policy SHALL retain the exact selected consumer path; conflict output SHALL require reconciliation instead of advertising an overwriting update.

#### Scenario: Policy is absent
- **WHEN** check selects a consumer with no managed policy block
- **THEN** it reports policy `missing`, reports the overall state non-current, and emits an install command containing that consumer path

#### Scenario: Policy is intact but outdated
- **WHEN** check selects a consumer with an intact older managed block
- **THEN** it reports policy `stale` and emits an install command containing that consumer path

#### Scenario: Policy is conflicted
- **WHEN** check selects a consumer with a modified or malformed managed block
- **THEN** it reports policy `conflict`, reports the overall state non-current, and does not advertise a destructive automatic update
