## Purpose

Define the boundary between the centrally distributed workflow and each consumer project so updates flow from one canonical package while project business, architecture, and operational context remain local.

## ADDED Requirements

### Requirement: Central package is the reusable authority
**ID:** REQ-CWI-001
**Status:** accepted
**Source:** decision:DEC-001
Consumer guidance SHALL identify `codex-openspec-workflow` as the canonical owner of reusable schemas, templates, validators, skills, routing, lifecycle gates, and general authoring policy; a consumer-local copy MUST NOT be represented as the upstream source for those assets.

#### Scenario: Agent needs to change a reusable gate
- **WHEN** an agent proposes a change to a shared schema, validator, skill, installer, or general policy
- **THEN** the guidance routes that change to the central package instead of modifying a consumer copy as the source of truth

### Requirement: Consumer-specific context remains local
**ID:** REQ-CWI-002
**Status:** accepted
**Source:** decision:DEC-001, decision:DEC-004
Consumer projects SHALL retain their own OpenSpec context, business and technical documentation, repository navigation, deployment convention, domain-specific placement examples, and other project-only policy without promoting that content into the reusable central package.

#### Scenario: PayFlow documents an OCR folder example
- **WHEN** PayFlow records a concrete namespace, feature folder, dependency-registration, or architecture-test example
- **THEN** that example remains in PayFlow while the central package retains only the general feature-first rule

### Requirement: Shadowing is reported before freshness is claimed
**ID:** REQ-CWI-003
**Status:** accepted
**Source:** decision:DEC-001, decision:DEC-002
The consumer verification flow SHALL inspect effective OpenSpec schema resolution and SHALL report a consumer-local schema that shadows the selected central installation; it MUST NOT report the consumer as centrally current solely because the shadowing copy has equal content at one point in time.

#### Scenario: Consumer has project-local schemas
- **WHEN** OpenSpec resolves a package-owned schema from a consumer project before the selected installed central root
- **THEN** consumer verification reports the shadowing source and withholds a centrally inherited/current claim until the consumer explicitly reconciles it

### Requirement: Consumer migration follows central proof
**ID:** REQ-CWI-004
**Status:** accepted
**Source:** decision:DEC-005
The migration procedure SHALL validate the central package in isolated targets before changing a consumer, SHALL use PayFlow as the first compatibility consumer, and SHALL preserve the consumer's existing reusable copies and project policy when central install/check or workspace discovery fails.

#### Scenario: Isolated central validation fails
- **WHEN** isolated installation, freshness checking, nested-script execution, or required package validation fails
- **THEN** PayFlow consumer cleanup does not begin and its existing workflow files remain available for rollback

#### Scenario: Central validation and PayFlow compatibility pass
- **WHEN** the central package passes isolated install/check and PayFlow resolves and validates the selected central workflow
- **THEN** the migration may remove or reconcile PayFlow's temporary reusable copies while retaining PayFlow-specific context and documentation
