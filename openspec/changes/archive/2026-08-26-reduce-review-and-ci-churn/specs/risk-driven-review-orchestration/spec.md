## ADDED Requirements

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
