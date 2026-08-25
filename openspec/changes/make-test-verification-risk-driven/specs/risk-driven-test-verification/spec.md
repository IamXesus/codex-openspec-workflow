## Purpose

Keep shared OpenSpec verification proportional to distinct delivery risks so agents prove behavior with the smallest faithful evidence set instead of accumulating overlapping tests for every task and layer.

## ADDED Requirements

### Requirement: Minimum-sufficient verification is shared across traced work
**ID:** REQ-RDV-001
**Status:** accepted
**Source:** decision:DEC-001
The shared workflow SHALL state that a requirement scenario or implementation task does not imply a new automated test, SHALL permit one concrete verification set to cover multiple traced tasks or requirements, and SHALL direct agents to reuse, extend, or parameterize suitable existing evidence before adding another test.

#### Scenario: Several tasks share one proof
- **WHEN** several implementation tasks contribute to one observable behavior and one existing or focused check proves their combined result
- **THEN** the plan may reference that shared check from each traced task without creating a separate test for every checkbox

#### Scenario: Existing test already detects the regression
- **WHEN** an existing test exercises the distinct reachable failure introduced by the change
- **THEN** the agent reuses or narrowly extends that test rather than adding an overlapping test solely to satisfy task traceability

### Requirement: Verification uses the cheapest faithful layer
**ID:** REQ-RDV-002
**Status:** accepted
**Source:** decision:DEC-001
The shared workflow SHALL prefer one stable primary acceptance path for a critical observable flow, including a real vertical slice when appropriate, and SHALL add unit, real-provider integration, contract, browser, or runtime checks only for distinct risks that the primary path cannot prove economically. It SHALL keep mocks at external boundaries rather than reimplementing the consumer's own application behavior and SHALL match database semantics to a real provider when those semantics are the claimed risk.

#### Scenario: Critical flow crosses application boundaries
- **WHEN** a stable real frontend-to-API-to-database path can prove the accepted observable flow
- **THEN** the agent prefers that vertical slice as primary acceptance evidence instead of duplicating the same happy path through internal mocks at every layer

#### Scenario: Focused invariant is cheaper below E2E
- **WHEN** money allocation, state transition, concurrency, transaction, migration, retry, authorization, or external-contract behavior cannot be diagnosed or exercised economically through the primary acceptance path
- **THEN** the agent adds or retains a focused check at the cheapest layer that faithfully reproduces that distinct risk

### Requirement: Ordinary development consolidates only the touched test area
**ID:** REQ-RDV-003
**Status:** accepted
**Source:** decision:DEC-002
During ordinary implementation the shared workflow SHALL allow overlapping legacy tests to be merged, replaced, or removed only within the affected feature slice and only after sufficient replacement evidence exists. It SHALL require a separate explicit request before repository-wide legacy-suite consolidation and SHALL prohibit unrelated test cleanup from expanding a feature change.

#### Scenario: Feature change touches overlapping tests
- **WHEN** implementation changes a feature whose existing tests duplicate the same risk and the current change supplies replacement evidence
- **THEN** the agent may consolidate those touched tests in the same change and verifies the replacement before deletion

#### Scenario: Redundancy is outside the affected feature
- **WHEN** the agent notices unrelated legacy test duplication during ordinary feature work
- **THEN** the agent leaves it unchanged rather than broadening the current change

#### Scenario: Owner requests whole-suite consolidation
- **WHEN** the user explicitly requests repository-wide legacy test consolidation
- **THEN** the workflow treats it as a separate bounded change with baseline, risk mapping, incremental feature slices, and replacement evidence before deletion

### Requirement: Final review evaluates test-delta value
**ID:** REQ-RDV-004
**Status:** accepted
**Source:** decision:DEC-004
The shared final-review guidance SHALL examine new, changed, reused, and removed tests for distinct risk, overlap with existing evidence, test-layer fit, brittleness, and consolidation opportunity. It SHALL NOT use fixed test-count, coverage, test-to-production LOC, or mandatory mutation-testing quotas as a substitute for that semantic review.

#### Scenario: New tests overlap existing evidence
- **WHEN** the pending diff adds multiple checks for the same observable failure without a distinct layer-specific risk
- **THEN** the reviewer reports the avoidable overlap and directs consolidation before declaring full-diff readiness

#### Scenario: Large test count is justified by distinct risks
- **WHEN** focused tests prove separate reachable failures at faithful layers
- **THEN** the reviewer does not reject them merely because the suite, coverage, or test-to-production ratio is large

### Requirement: The correction adds no mandatory verification bureaucracy
**ID:** REQ-RDV-005
**Status:** accepted
**Source:** decision:DEC-003
The initial risk-driven verification contract SHALL reuse existing OpenSpec artifacts and trace-marker grammar and SHALL NOT require a separate validation document, numeric test budget, mandatory mutation run, or new per-test metadata table.

#### Scenario: Agent plans proportional verification
- **WHEN** an agent prepares tasks under the updated workflow
- **THEN** it records concrete shared or focused verification in the existing task trace and review structures without creating another required artifact
