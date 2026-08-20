## Purpose

Define a host-neutral continuous v3 execution contract that removes routine user handoffs while preserving evidence, validation, review, scope, and external-effect authority gates.

## ADDED Requirements

### Requirement: Clear change requests run through the complete internal lifecycle
**ID:** REQ-COF-001
**Status:** accepted
**Source:** decision:DEC-001
For a clear user-authorized software change, the canonical workflow SHALL create each ready OpenSpec artifact in schema order, run the required gates, enter apply after implementation readiness, implement all accepted tasks, verify them, and run required independent reviews without asking the user for routine continuation between those internal stages.

#### Scenario: Planning artifacts need no new decision
- **WHEN** proposal, specs, design, and tasks can be derived from inspected evidence and accepted user authority
- **THEN** the agent creates them in official dependency order during the same continuous run
- **AND** successful artifact creation or planning completion does not produce a user-blocking pause

#### Scenario: Planning becomes implementation-ready
- **WHEN** planning, semantic, traceability, and applicable architecture gates pass
- **THEN** the agent obtains apply instructions and begins implementation without requiring a second apply/build message

#### Scenario: Implementation and reviews remain internally actionable
- **WHEN** tasks, verification, wave reviews, and final review can proceed within accepted scope
- **THEN** the agent continues through them until completion or a user-action-required condition occurs

### Requirement: Workflow pauses only for user-action-required conditions
**ID:** REQ-COF-002
**Status:** accepted
**Source:** decision:DEC-002
The continuous workflow MUST yield for user input only when a user-owned decision, clarification, authorization, or scope change is required; when an explicit user boundary has been reached; or when an unresolved blocker cannot be repaired safely within accepted scope. An artifact boundary, successful gate, completed wave, successful review, or autonomously repairable validation/review finding MUST NOT by itself require user continuation.

#### Scenario: A material question is unresolved
- **WHEN** a missing decision would change behavior, scope, data, security, cost, or an external effect
- **THEN** the agent records the uncertainty without inventing authority
- **AND** pauses with one concise blocking question

#### Scenario: A gate or review finding has a contract-determined repair
- **WHEN** validation or independent review reports a defect whose correction is unambiguous and inside accepted scope
- **THEN** the agent applies the correction, reruns affected evidence, and continues
- **AND** does not ask the user merely to authorize the repair

#### Scenario: A blocker needs owner disposition
- **WHEN** a failure or finding has multiple materially different valid resolutions or cannot be resolved inside accepted scope
- **THEN** the agent pauses and asks for the required user disposition

### Requirement: Explicit scope and external-effect authority remain controlling
**ID:** REQ-COF-003
**Status:** accepted
**Source:** decision:DEC-002
Continuous execution SHALL NOT broaden the user's requested scope or external-effect authority. An explicitly plan-only, exploration-only, diagnosis-only, review-only, or otherwise bounded request MUST stop at that boundary. Push, tag, release, deploy, production mutation, and other separately governed effects MUST still stop at their applicable explicit `GO` gate.

#### Scenario: User asks only for a plan
- **WHEN** the user explicitly limits the request to planning and excludes implementation
- **THEN** the agent completes the authorized planning lifecycle and yields without editing production code

#### Scenario: Internal work reaches an external effect
- **WHEN** verified and reviewed work is ready for an effect that requires separate approval
- **THEN** the agent reports readiness and pauses before the effect
- **AND** proceeds only after the required explicit `GO`

### Requirement: Distributed policy exposes one continuous contract
**ID:** REQ-COF-004
**Status:** accepted
**Source:** user:USER-001, user:USER-002
The canonical package SHALL distribute the same continuous-execution and user-action-required pause contract through its portable workflow skill, managed consumer policy, applicable schema instructions, README, regressions, and synchronized version metadata so Codex, Orca, Omnigent, and other repository-aware hosts do not receive contradictory lifecycle guidance.

#### Scenario: Consumer receives the updated package
- **WHEN** an operator installs or updates the next canonical package version
- **THEN** the installed workflow and managed policy direct agents to continue across internal stages while gates pass
- **AND** no package instruction retains a routine one-artifact, planning-to-apply, or successful-wave user pause

#### Scenario: Agent runs in a different host
- **WHEN** the same package is used from Codex, Orca, Omnigent, or another supported repository-aware host
- **THEN** lifecycle progression and pause conditions remain the same
- **AND** no host-specific continuation convention is required
