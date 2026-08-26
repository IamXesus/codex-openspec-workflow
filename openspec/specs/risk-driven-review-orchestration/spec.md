# risk-driven-review-orchestration Specification

## Purpose
Define a shared, risk-driven review contract that preserves mandatory independent coverage for dangerous boundaries and release readiness without spawning a new reviewer for every semantic wave, remediation, mechanical delta, or test-environment iteration.
## Requirements
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

### Requirement: Advisory critics do not multiply completion reviews
**ID:** REQ-RRO-006
**Status:** accepted
**Source:** user:USER-001
The workflow SHALL default an evidence-heavy change to one final full-pending-diff independent review and SHALL add an intermediate checkpoint reviewer only for an inspected material boundary on which later work depends. An optional early read-only critic MAY identify risks before deterministic verification, but it MUST be labeled advisory, MUST NOT satisfy an intermediate or final checkpoint, and MUST NOT create a review-after-every-fix lifecycle.

This review economy MUST NOT remove the existing pre-implementation architecture review and fail-closed architecture validation required when an evidence-heavy design declares material architecture impact.

#### Scenario: Early critic finds defects
- **WHEN** a high-risk slice uses an advisory critic before its required CI or equivalent deterministic verification
- **THEN** the implementation batches the supported findings into the coherent slice and still waits for stable verified scope before the required independent checkpoint review

#### Scenario: Last review already covers the full change
- **WHEN** the review at the end of a material slice declares full pending-diff coverage and no later material delta occurs
- **THEN** the same review satisfies the final checkpoint without launching another independent reviewer

#### Scenario: Large design changes component ownership
- **WHEN** an evidence-heavy design has material architecture impact under the existing architecture-growth contract
- **THEN** one independent architecture review still gates the affected implementation before production edits, independently of the reduced code-review cadence

### Requirement: Blocking findings remain complete across remediation
**ID:** REQ-RRO-007
**Status:** accepted
**Source:** user:USER-001
Every independent reviewer MUST assign a stable identifier to each High and Medium finding. The coordinator MUST retain the complete blocking finding ledger in the session, record the disposition of every identifier, consolidate safe related fixes, and request targeted continuation only after no blocking identifier is omitted or silently downgraded. The same reviewer SHOULD continue the cycle when available.

#### Scenario: Coordinator misses findings
- **WHEN** a reviewer reports five High or Medium findings and the coordinator accounts for fewer than five identifiers
- **THEN** targeted continuation remains blocked until every reported identifier has an explicit fixed, disputed, or user-owned disposition

#### Scenario: Findings are fixed as one batch
- **WHEN** several supported findings affect the same reviewed scope
- **THEN** the coordinator applies and verifies the safe remediation batch before one targeted continuation instead of requesting review after each fix

### Requirement: Verification iterates on coherent evidence batches
**ID:** REQ-RRO-008
**Status:** accepted
**Source:** user:USER-001
The workflow MUST choose the cheapest faithful deterministic check for the current failure signal, accumulate related safe corrections into a coherent stable batch, and run required CI or full-suite regression when that batch is ready. It MUST NOT require a published diagnostic commit, a full-suite run, or an independent review for every microfix by default. Relevant evidence SHALL be rerun whenever the affected contract or failure signal makes it stale; no fixed test, pipeline, reviewer, or retry quota may replace risk-based judgment.

#### Scenario: Focused evidence is available
- **WHEN** one failed job or focused check can faithfully verify an unchanged or narrowly corrected failure boundary
- **THEN** the workflow uses that evidence before repeating a broader regression gate and does not add an unrelated review

#### Scenario: Coherent batch becomes stable
- **WHEN** related fixes are complete and the changed inventory is stable
- **THEN** required CI or full-suite evidence runs for the batch before the completion reviewer is dispatched

### Requirement: Essential review economy is visible to consumer agents
**ID:** REQ-RRO-009
**Status:** accepted
**Source:** user:USER-001
The distributed controller, reviewer, implementation guardrails, schema instructions, and managed consumer `AGENTS.md` policy SHALL consistently expose the default final-only review plan, advisory-critic boundary, complete blocking-finding reconciliation, batched remediation, and coherent verification sequencing. Installation MUST preserve unrelated consumer instructions and MUST NOT introduce a separate persisted review-ledger artifact.

#### Scenario: Fresh consumer session does not load every skill body
- **WHEN** a repository-aware agent starts from the managed consumer policy and only later selects task-specific skills
- **THEN** the always-loaded policy still prevents review-after-every-fix and full-suite-after-every-microfix behavior

#### Scenario: Existing consumer instructions surround the managed block
- **WHEN** the package updates an intact managed policy block in an existing `AGENTS.md`
- **THEN** only the managed block changes and all surrounding consumer-owned instructions remain byte-preserved
