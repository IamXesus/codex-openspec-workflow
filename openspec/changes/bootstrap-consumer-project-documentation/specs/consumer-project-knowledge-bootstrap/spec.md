## Purpose

Provide every explicitly selected consumer repository with the same durable, evidence-first project knowledge structure and lifecycle regardless of the agent host or development environment that performs adoption.

## ADDED Requirements

### Requirement: Consumer bootstrap is environment-neutral
**ID:** REQ-CPKB-001
**Status:** accepted
**Source:** decision:DEC-001
The package SHALL produce identical consumer repository paths, file contents, audit states, and lifecycle rules for the same repository state regardless of the selected host target. Target-specific behavior MUST be limited to resolving shared skill roots and command launch adaptation.

#### Scenario: Different hosts adopt equivalent empty repositories
- **WHEN** adoption runs for equivalent repositories through `codex`, `orca`, or `omnigent`
- **THEN** the resulting consumer project knowledge and OpenSpec files are byte-equivalent
- **AND** only the shared installation roots differ by target

#### Scenario: Repository is used from another application
- **WHEN** an agent opens an already bootstrapped repository from a different supported application or IDE
- **THEN** it reads the same repository-owned policy, documentation navigation, audit state, and OpenSpec lifecycle without host-specific conversion

### Requirement: Explicit adoption creates the missing project knowledge layer
**ID:** REQ-CPKB-002
**Status:** accepted
**Source:** decision:DEC-002
An install with an explicitly selected consumer repository SHALL create every missing canonical project knowledge file for overview/navigation, business processes, integrations, technical architecture, open issues, and audit status. It SHALL also create a missing `openspec/config.yaml` that selects the shared strict default schema and links the knowledge layer, current specs, active changes, archive, and historical Git evidence.

#### Scenario: Empty consumer repository is adopted
- **WHEN** install selects a repository with none of the canonical knowledge or OpenSpec configuration files
- **THEN** all canonical scaffold files and required parent directories are created
- **AND** every semantic section is marked pending evidence rather than populated with assumed project behavior

#### Scenario: Consumer has a partial knowledge layer
- **WHEN** some canonical files already exist and others are absent
- **THEN** install creates only the absent canonical files
- **AND** preserves every byte and file mode of the existing repository-owned files

#### Scenario: Existing OpenSpec config cannot be managed safely
- **WHEN** `openspec/config.yaml` already exists but does not carry the canonical navigation contract
- **THEN** check reports a non-current project-bootstrap state with a concrete reconciliation issue
- **AND** install does not heuristically rewrite or replace the existing YAML

### Requirement: Bootstrap records a deterministic primary audit
**ID:** REQ-CPKB-003
**Status:** accepted
**Source:** decision:DEC-002,decision:DEC-003
Bootstrap SHALL record only deterministic structural observations available from the selected repository, including canonical documentation presence, OpenSpec layer presence, and discoverable top-level project evidence. It MUST distinguish observed paths from pending semantic facts and MUST NOT claim business processes, integration behavior, architecture, deployment state, or current requirements that were not established by inspected authority.

#### Scenario: Repository contains recognizable project evidence
- **WHEN** bootstrap observes existing top-level source, manifest, documentation, or OpenSpec paths
- **THEN** the audit records their repository-relative paths as observations
- **AND** leaves their semantic interpretation pending

#### Scenario: Repository contains no inspectable project evidence
- **WHEN** the selected repository is otherwise empty
- **THEN** the audit records that no structural evidence was found
- **AND** the semantic audit remains pending without invented defaults

#### Scenario: Freshness check runs after bootstrap
- **WHEN** check inspects the same unchanged repository
- **THEN** it reports the structural bootstrap state without writing files
- **AND** separately reports whether the semantic audit is still pending or has been completed by a repository-aware agent

### Requirement: A repository-aware agent completes and maintains project knowledge
**ID:** REQ-CPKB-004
**Status:** accepted
**Source:** decision:DEC-003
The installed managed policy SHALL require an agent that encounters a pending semantic audit to inspect repository evidence, populate only confirmed project facts and explicit open questions, and update the audit status before substantial implementation. Subsequent tasks SHALL update the affected business, integration, technical, open-issue, and normative OpenSpec layers whenever their accepted behavior changes.

#### Scenario: First substantial task starts with a pending audit
- **WHEN** an agent begins substantial implementation in a bootstrapped repository whose semantic audit is pending
- **THEN** it first performs the read-only project audit and reconciles the canonical knowledge files
- **AND** unresolved business facts remain explicit open questions rather than inferred requirements

#### Scenario: A later task changes documented behavior
- **WHEN** accepted implementation changes a business process, integration contract, technical ownership, known limitation, or observable behavior
- **THEN** the same change updates the corresponding project knowledge file or current OpenSpec lifecycle layer
- **AND** completion is not claimed while implementation and project knowledge disagree

### Requirement: Project bootstrap is idempotent and fail-closed
**ID:** REQ-CPKB-005
**Status:** accepted
**Source:** decision:DEC-002
Repeated install SHALL leave a current project knowledge layer byte-identical. Check SHALL remain read-only and classify missing canonical files, pending or stale audit state, unsafe existing config, symlink escapes, non-file path conflicts, and locally modified package-managed bootstrap metadata without deleting or overwriting repository-owned content. A conflict MUST block consumer writes before shared-root mutation.

#### Scenario: Current bootstrap is installed again
- **WHEN** all canonical files and bootstrap metadata are current
- **THEN** install performs no consumer file rewrite
- **AND** check remains current for the project-bootstrap layer

#### Scenario: A required path escapes or has an incompatible type
- **WHEN** a canonical target is a symlink that escapes the repository or is a directory/non-file where a file is required
- **THEN** check reports conflict
- **AND** install performs zero consumer and shared-root mutations

#### Scenario: A canonical scaffold was edited by the repository
- **WHEN** repository owners have added or changed semantic content in a previously created canonical document
- **THEN** the content remains repository-owned and is preserved
- **AND** freshness depends on structural/audit metadata rather than equality with the original blank template
