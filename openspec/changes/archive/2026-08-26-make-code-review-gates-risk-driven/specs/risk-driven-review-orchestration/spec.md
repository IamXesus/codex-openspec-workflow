## Purpose

Define a shared, risk-driven review contract that preserves mandatory independent coverage for dangerous boundaries and release readiness without spawning a new reviewer for every semantic wave, remediation, mechanical delta, or test-environment iteration.

## ADDED Requirements

### Requirement: Semantic waves do not automatically require independent review
**ID:** REQ-RRO-001
**Status:** accepted
**Source:** user:USER-001
The evidence-heavy workflow SHALL keep semantic implementation waves as planning and verification boundaries while requiring an intermediate independent reviewer only when the plan identifies a material risk or a downstream dependency on the changed contract. The task plan MUST state the concrete trigger for every intermediate independent review and MUST NOT create one merely because a wave, task group, file, or checkbox exists.

#### Scenario: Ordinary wave is covered later
- **WHEN** a semantic wave has targeted verification but introduces no material dependency boundary before the final review
- **THEN** the plan may close the wave without an independent reviewer and include its diff in a later full-pending-diff review

#### Scenario: Dependent material boundary requires review
- **WHEN** later work will depend on a changed public contract, persistent-data boundary, authorization boundary, transaction owner, or external side-effect contract
- **THEN** the plan includes an intermediate independent review after that boundary is implemented and verified

### Requirement: Reviews run against stable verified scope
**ID:** REQ-RRO-002
**Status:** accepted
**Source:** user:USER-001
An intermediate or final review SHALL start only after every task in its declared coverage is complete, the planned deterministic checks for that coverage have finished, and the changed-file inventory is stable enough for the reviewer to inspect. A review launched before CI or equivalent required verification completes MUST NOT satisfy the checkpoint.

#### Scenario: CI is still running
- **WHEN** the declared review coverage requires CI and that CI has not completed
- **THEN** the workflow continues verification and does not dispatch the checkpoint reviewer yet

#### Scenario: Covered scope is ready
- **WHEN** covered tasks and targeted checks are complete and the pending diff is recorded
- **THEN** one independent reviewer receives that complete stable scope

### Requirement: Re-review is delta-based and consolidated
**ID:** REQ-RRO-003
**Status:** accepted
**Source:** user:USER-001
After a review, the workflow MUST classify later changes against the reviewed coverage. A material change to behavior, public contracts, auth/security, persistent data, transaction ownership, external effects, migration/rollback safety, or a reviewed adjacent contract SHALL stale the affected coverage. A mechanical or evidence-only delta with sufficient deterministic proof SHALL NOT automatically stale unaffected coverage. Fixes from one review SHOULD be consolidated and returned through one targeted continuation of the existing review cycle when practical; a fresh reviewer MUST NOT be spawned for each finding by default.

#### Scenario: Mechanical CI delta
- **WHEN** a post-review delta only changes mechanical CI control wiring and lint plus an actual pipeline prove the intended configuration
- **THEN** prior product-code review coverage remains current and no new independent reviewer is required solely for that delta

#### Scenario: Security parser remediation
- **WHEN** a post-review remediation changes parser security or another material risk boundary
- **THEN** the affected finding and adjacent contract receive targeted independent re-review

#### Scenario: Several findings are fixed together
- **WHEN** one review reports multiple blocking findings in the same covered scope
- **THEN** the implementation consolidates safe fixes and requests one targeted re-review cycle instead of one new reviewer per fix

### Requirement: Test and staging evidence precede release review
**ID:** REQ-RRO-004
**Status:** accepted
**Source:** user:USER-001
The workflow SHALL distinguish an authorized non-production test or staging deployment used to obtain verification evidence from a production release or deployment. A test/staging effect MUST retain explicit authority, rollback, scope, and risk-proportionate preflight, but MUST NOT require the final release review merely because it is a deploy. The final full-pending-diff review SHALL run after required test/staging evidence is complete and before production release or deployment.

#### Scenario: Test portal reveals a runtime incompatibility
- **WHEN** an authorized test deployment is needed to obtain contract evidence
- **THEN** the workflow performs the bounded preflight and deployment without prematurely completing the final release review

#### Scenario: Production release is next
- **WHEN** required non-production evidence and implementation remediations are complete
- **THEN** a current full-pending-diff independent review is required before production release or deployment

### Requirement: Final independent coverage remains fail-closed
**ID:** REQ-RRO-005
**Status:** accepted
**Source:** user:USER-001
Every evidence-heavy change MUST retain exactly one final full-pending-diff independent review checkpoint after all implementation waves. An earlier intermediate review MAY satisfy the final checkpoint only when it covered the complete pending diff and no later material delta affected that coverage. Missing, partial, or materially stale final coverage MUST block release readiness.

#### Scenario: Last intermediate review covers everything
- **WHEN** the last intermediate reviewer declares full pending-diff coverage and no later material delta occurs
- **THEN** that review may satisfy the single final checkpoint without launching another reviewer

#### Scenario: Final coverage is partial
- **WHEN** the available review excludes part of the pending implementation diff
- **THEN** the change remains not release ready until one independent full-pending-diff review passes
