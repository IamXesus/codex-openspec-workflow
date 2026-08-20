## Purpose

Define one observable version and installation-state contract so agents can detect central workflow updates, distinguish current and stale environments, and choose an explicit update without silently mutating their environment.

## ADDED Requirements

### Requirement: Canonical workflow version
**ID:** REQ-WVD-001
**Status:** accepted
**Source:** decision:DEC-002
The central package SHALL expose exactly one machine-readable workflow version that represents the reusable schemas, skills, validators, policy, and installer contract distributed together.

#### Scenario: Agent reads the package version
- **WHEN** an agent or installer inspects a valid central checkout
- **THEN** it obtains one unambiguous workflow version without deriving the version from a consumer project

#### Scenario: Package version metadata is absent
- **WHEN** the central checkout does not expose its required machine-readable version
- **THEN** installation and freshness checks fail closed instead of treating the package as current

### Requirement: Verifiable installed version state
**ID:** REQ-WVD-002
**Status:** accepted
**Source:** decision:DEC-002
Installation SHALL record machine-readable installed state, and the check operation SHALL classify each selected installation as `missing`, `current`, or `stale` by comparing it with the canonical package version and package-owned content.

#### Scenario: Installation is current
- **WHEN** the installed version and all package-owned content match the inspected central package
- **THEN** the check reports `current` and identifies the matching version

#### Scenario: Installation is missing
- **WHEN** the selected installation has no valid installed-state record or required package root
- **THEN** the check reports `missing` and does not claim that the workflow is available

#### Scenario: Installation is stale
- **WHEN** the installed version differs from the central version or package-owned content differs from the canonical package
- **THEN** the check reports `stale`, identifies the installed and available versions when known, and fails its freshness gate

### Requirement: Explicit non-mutating update guidance
**ID:** REQ-WVD-003
**Status:** accepted
**Source:** decision:DEC-002
Freshness checks SHALL be non-mutating and SHALL provide an explicit update command for `missing` or `stale` state; the package MUST NOT automatically pull Git changes or overwrite an installation merely because a newer version exists.

#### Scenario: Stale agent requests status
- **WHEN** an agent checks an installation whose state is `stale`
- **THEN** it receives an explicit command that installs the inspected central version into the same selected target

#### Scenario: Status check has no update authority
- **WHEN** an agent runs only the freshness check
- **THEN** no package files, Git refs, consumer repositories, or installed receipts are changed
