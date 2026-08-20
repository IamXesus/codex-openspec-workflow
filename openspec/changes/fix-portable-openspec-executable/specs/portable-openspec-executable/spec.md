## Purpose

Define one host-neutral executable and verification contract so the canonical OpenSpec workflow runs on Linux/POSIX and Windows without relying on developer-machine command aliases or installing the OpenSpec CLI itself.

## ADDED Requirements

### Requirement: Portable instructions resolve OpenSpec by platform
**ID:** REQ-POE-001
**Status:** accepted
**Source:** decision:DEC-001
The portable workflow skill SHALL instruct POSIX/Linux agents to invoke `openspec` and Windows agents to invoke `openspec.cmd` or `openspec` only when the active Windows shell resolves it correctly through PATHEXT. Every documented OpenSpec new, status, instructions, init, apply, and check operation MUST use this same platform branch and MUST NOT depend on a shell-specific environment-variable convention.

#### Scenario: Linux agent follows the installed portable skill
- **WHEN** the skill runs in a POSIX environment whose PATH contains `openspec` but not `openspec.cmd`
- **THEN** every OpenSpec workflow operation invokes `openspec`
- **AND** no instruction attempts to invoke `openspec.cmd`

#### Scenario: Windows agent follows the installed portable skill
- **WHEN** the skill runs in Windows
- **THEN** it selects `openspec.cmd` or a shell-resolved `openspec` that is valid in that Windows shell
- **AND** all workflow operations use the same selected executable contract

### Requirement: Executable regression is isolated from developer PATH
**ID:** REQ-POE-002
**Status:** accepted
**Source:** user:USER-003
The package SHALL include a focused regression that inspects the portable skill and exercises executable resolution in isolated temporary PATH state. The regression MUST prove the POSIX path with only an `openspec` executable present and MUST prove Windows resolution independently of any developer-installed `openspec.cmd`.

#### Scenario: Developer machine has an unrelated OpenSpec installation
- **WHEN** the regression runs on a machine that may already expose `openspec.cmd`
- **THEN** its POSIX assertion uses only the temporary isolated executable inventory
- **AND** the test cannot pass because of the unrelated developer installation

### Requirement: POSIX package lifecycle remains isolated and complete
**ID:** REQ-POE-003
**Status:** accepted
**Source:** user:USER-003, user:USER-004
The existing POSIX installer lifecycle SHALL complete dry-run, install, check, and rollback for both `codex` and `omnigent` using explicit temporary HOME, agent, schema, backup, and consumer roots. Verification MUST NOT write to real `~/.codex`, `~/.agents`, user schema roots, a remote test host, or the named server.

#### Scenario: Codex lifecycle runs on Linux
- **WHEN** `scripts/install.sh` runs dry-run, install, check, and rollback for target `codex` with isolated roots
- **THEN** every operation succeeds with the expected ready/current/restored state
- **AND** all writes remain under the temporary rehearsal root

#### Scenario: Omnigent lifecycle runs on Linux
- **WHEN** the same isolated lifecycle runs for target `omnigent`
- **THEN** every operation succeeds with the expected ready/current/restored state
- **AND** no default profile or schema root is selected

### Requirement: CLI dependency and package version remain explicit
**ID:** REQ-POE-004
**Status:** accepted
**Source:** decision:DEC-002, decision:DEC-003
The README SHALL document the platform executable branch and retain OpenSpec CLI 1.8.x as a separately installed prerequisite. The package installer MUST NOT install OpenSpec, npm packages, or runtime state implicitly. Package and lock metadata SHALL both report version `1.1.1`, and this local change MUST NOT publish a Git tag or release.

#### Scenario: Operator reads Linux installation requirements
- **WHEN** an operator prepares a POSIX consumer
- **THEN** the documentation identifies `openspec` as the required executable and OpenSpec CLI 1.8.x as an external prerequisite
- **AND** it does not claim that the package installer provides the CLI

#### Scenario: Package metadata is validated
- **WHEN** repository validation reads package and lock metadata
- **THEN** both declare `1.1.1`
- **AND** no tag or release operation is part of the implementation
