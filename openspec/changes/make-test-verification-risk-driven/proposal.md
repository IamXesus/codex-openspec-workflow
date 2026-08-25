## Why

The shared workflow currently requires concrete verification on every implementation task but does not tell agents to minimize overlapping test evidence. In large consumers this can make the cheapest path through the structural gate an additional test at every task and layer, increasing maintenance cost and slowing delivery even when one existing or vertical-slice check already proves the behavior.

## Evidence

- USER-001: The user reported that Palmetto PayFlow has more than one thousand tests, believes a material share is not useful, and explicitly asked how to correct the behavior in this OpenSpec package rather than in PayFlow.
- USER-002: The user proposed relying more on end-to-end tests to reduce test count and increase practical value.
- USER-003: The user explicitly prioritized avoiding a long increase in development time because the current delivery process is already slow by choice.
- USER-004: The user asked whether existing tests should be consolidated separately or gradually during ordinary development.
- USER-005: After the displayed implementation checkpoint explicitly selected minimum-sufficient shared evidence; a stable real vertical slice for critical flows plus unit, real-provider integration, contract, browser, or runtime checks only for distinct risks; mocks only at external boundaries; real database providers for provider-specific semantics; touched-area consolidation during ordinary work; separate explicit repository-wide consolidation; semantic final review of overlap and layer value; and no numeric quotas, mandatory mutation, new trace syntax, or extra verification artifact, the user said “окей, делаем”.
- FACT-001: Both evidence schemas require every implementation checkbox to carry concrete planned verification, while `skills/openspec-workflow/scripts/validate_requirements.py` rejects only missing or placeholder verification text and does not evaluate duplication, information gain, or test-layer fit.
- FACT-002: The task templates currently prime agents with `<exact test/check and expected result>` for every implementation task.
- FACT-003: `skills/coding-guardrails/SKILL.md` prefers the narrowest meaningful check, but the distributed workflow does not explicitly state that one evidence set may cover several tasks or that existing tests should be consolidated before new tests are added.
- OBS-001: A read-only PayFlow inventory found overlapping unit, API-stub, EF InMemory, PostgreSQL integration, frontend mock, component, and browser coverage. This is evidence of the failure mode but does not prove that any fixed percentage of the suite is useless.

## What Changes

- Define a minimum-sufficient-evidence policy: requirement scenarios and implementation tasks do not imply one new automated test each, and one concrete verification set may cover several traced tasks or requirements.
- Make existing-test reuse, focused extension or parameterization, and one stable primary acceptance path the default before creating another automated test.
- Prefer a real vertical slice for critical observable flows while retaining focused unit, real-provider integration, contract, browser, or runtime evidence only for distinct risks that the primary path cannot prove economically.
- Apply a narrow touched-area ratchet during ordinary development: consolidate or remove an overlapping legacy test only when the current feature slice supplies replacement evidence; repository-wide legacy consolidation remains a separate explicit request.
- Require final review to examine the test delta for distinct risk, overlap, layer fit, brittleness, and consolidation opportunities without imposing test-count, coverage, LOC, or mutation-testing quotas.
- Update the shared package version and focused contract regressions so installed consumers can detect the changed workflow behavior.

## Capabilities

### New Capabilities

- `risk-driven-test-verification`: Minimum-sufficient, layer-appropriate verification selection and bounded touched-area test consolidation for shared OpenSpec delivery.

### Modified Capabilities

None.

## Impact

- Changes the distributed `openspec-workflow`, `coding-guardrails`, and `code-reviewer` skills plus both evidence schema task instructions and task templates.
- Updates package metadata, README guidance, and focused workflow-policy regressions required for distribution consistency.
- Does not change the trace-marker syntax, deterministic validator grammar, installer transaction, consumer production code, existing consumer tests, CI, deployment, or external systems.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

The change adjusts existing declarative workflow contracts and their focused regressions. It adds no runtime responsibility, transaction boundary, dependency, service, or substantial production implementation.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: Verification is risk-driven rather than task-count-driven
**Status:** accepted
**Source:** user:USER-002, user:USER-003, user:USER-005

One minimum-sufficient evidence set may prove several requirements or implementation tasks. A stable real vertical slice is the preferred primary acceptance path for a critical observable flow, while supplementary lower-level checks require a distinct risk and the cheapest faithful layer.
Mocks remain at external boundaries instead of reproducing the consumer's own application behavior, and database-specific claims require evidence against a real provider with the relevant semantics.

### DEC-002: Legacy consolidation is a touched-area ratchet by default
**Status:** accepted
**Source:** user:USER-004, user:USER-005

Ordinary development may merge or remove overlapping tests only inside the affected feature slice and only after replacement evidence exists. Repository-wide legacy-suite consolidation requires a separate explicit request.

### DEC-003: The first correction stays process-light
**Status:** accepted
**Source:** user:USER-003, user:USER-005

The workflow changes authoring and review behavior without a new validation artifact, numeric quota, mandatory mutation run, or new trace-marker grammar.

### DEC-004: Final review blocks avoidable test overlap
**Status:** accepted
**Source:** user:USER-003, user:USER-005

Final review examines added, changed, reused, and removed tests for distinct risk, existing-evidence overlap, faithful layer fit, brittleness, and consolidation opportunity. Multiple checks for the same observable failure without a distinct layer-specific risk block full-diff readiness until consolidated; fixed test-count, coverage, test-to-production LOC, and mandatory mutation quotas do not substitute for this semantic review.

## Open Questions

None.
