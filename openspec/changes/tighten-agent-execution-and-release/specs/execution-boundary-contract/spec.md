# execution-boundary-contract Specification

## Purpose

Keep a narrow software change narrow while allowing the primary agent to continue quickly through ordinary implementation, verification, and release gates.

## ADDED Requirements

### Requirement: Review findings do not expand accepted scope
**ID:** REQ-EBC-001
**Status:** accepted
**Source:** user:USER-001
An independent review SHALL be read-only evidence. A reviewer MUST NOT accept a new architecture, persistent-data, security, transaction, deletion, migration, or external-effect strategy. A remediation that crosses one of those boundaries MUST remain proposed and block implementation until the owner accepts the exact scope; an unambiguous in-scope defect may be fixed and rechecked in one batch.

#### Scenario: Reviewer suggests a broader database strategy
- **WHEN** a narrow ACL fix receives a suggestion for cascades, a database function, changed deletion ownership, or another persistent boundary
- **THEN** the agent records it as a proposed scope change and does not apply it as if `READY` were approval

### Requirement: Context and execution constraints survive continuation
**ID:** REQ-EBC-002
**Status:** accepted
**Source:** user:USER-001
After a fresh session or context compaction, the agent MUST re-read current user authority, active artifacts, open questions, repository state, and explicit execution constraints. A user constraint such as CI-only backend execution MUST prevent the forbidden local command; a stopped background command is reported stopped only after completion or process absence is verified.

#### Scenario: Continuation follows a stale summary
- **WHEN** a summary says a proposed decision was agreed but current artifacts or authority do not contain that approval
- **THEN** the agent keeps the decision proposed and pauses before the related scope change

### Requirement: `skip_specs` is limited to no-behavior changes
**ID:** REQ-EBC-003
**Status:** accepted
**Source:** user:USER-001
`skip_specs: true` SHALL be accompanied by the shared structured no-behavior-delta marker. A change affecting observable behavior, public contracts, persistent data, security, transactions, migrations, or external effects MUST use requirements and the applicable OpenSpec route instead.

#### Scenario: Skip-specs marker is missing
- **WHEN** a change sets `skip_specs: true` without the no-delta marker
- **THEN** the fail-closed validator rejects it before tasks or implementation

### Requirement: Routing and verification stay risk-driven
**ID:** REQ-EBC-004
**Status:** accepted
**Source:** user:USER-001
The workflow SHALL keep no OpenSpec for small and already-clear work, `evidence-core` for an explicitly requested localized plan, and `evidence-heavy` for broad or materially risky work. It SHALL use the minimum-sufficient faithful check for each distinct reachable failure mode without test-count or coverage quotas. Low effort is the default hint for direct work and medium for heavy/security/data/release review; effort does not change authority or required gates.

#### Scenario: Localized UI/backend fix
- **WHEN** the behavior, files, and acceptance path are clear and no material boundary changes
- **THEN** the agent uses the direct route and focused evidence without spawning a blocking subagent

#### Scenario: Security or persistent-data boundary
- **WHEN** the change affects authorization, persistent data, a migration, a public contract, or an external effect
- **THEN** the agent uses evidence-heavy planning and preserves the applicable review, CI, rollback, and GO gates
