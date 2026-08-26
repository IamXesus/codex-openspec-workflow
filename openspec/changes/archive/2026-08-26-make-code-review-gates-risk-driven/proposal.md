## Why

Two inspected long-running delivery sessions showed that the shared workflow can turn review into repeated orchestration overhead: one server-side change started ten reviewer agents before its third implementation wave was complete, while a separate session attempted a new reviewer for a mechanical CI-only delta after a passing full-wave review. The current contract couples every semantic wave to an independent reviewer and requires a final release review before any deploy, including test/staging verification, so otherwise correct fail-closed behavior repeatedly invalidates and recreates review gates.

## Evidence

- USER-001: After receiving the concrete session findings and the proposed risk-driven corrections, the user explicitly requested that the shared OpenSpec and skill infrastructure be strengthened.
- OBS-001: The inspected Omnigent/Codex-native session started 21 subagents, including 10 reviewer agents; five reviewer agents were associated with Wave 2 and its remediations.
- OBS-002: The inspected local Bitrix MCP session attempted a separate reviewer for five mechanical `allow_failure` changes after CI lint and pipeline evidence; the implementing agent subsequently classified that review as unnecessary.
- FACT-001: `skills/openspec-workflow/SKILL.md` currently says to dispatch an independent reviewer at each heavy-wave checkpoint and to run the final full-diff review before any deploy or external effect.
- FACT-002: `skills/openspec-workflow/scripts/validate_requirements.py` currently requires exactly one wave-review checkpoint inside every `openspec-wave` section.
- FACT-003: The current skill already distinguishes targeted finding re-review from repeating the full review, but it does not require reuse of the same review cycle or consolidation of fixes.

## What Changes

- Separate semantic implementation waves from independent-review triggers. Every wave retains targeted verification, but only explicitly risk-triggered dependency boundaries require an intermediate independent review.
- Require tasks to declare a compact review plan explaining each intermediate review trigger; a final full-pending-diff review remains mandatory for evidence-heavy changes.
- Delay independent review until the covered scope is stable and its planned deterministic checks have completed. A pre-CI or per-file review does not satisfy a wave or final gate.
- Classify post-review deltas as material or non-material. Mechanical deltas with sufficient deterministic evidence do not automatically stale prior review coverage; material contract or risk changes do.
- Consolidate fixes and use a targeted continuation of the existing reviewer when practical instead of spawning a fresh reviewer for every finding.
- Distinguish non-production test/staging deployment used to obtain verification evidence from production/release effects. Test/staging still requires its own authorization, rollback, and risk-proportionate preflight, but not a premature final release review. Production/release continues to require a current full-diff review.

## Capabilities

### New Capabilities

- `risk-driven-review-orchestration`: Shared planning, validation, and execution rules select independent review checkpoints from material risk and dependency boundaries, reuse valid coverage, and prevent redundant reviewer launches.

### Modified Capabilities

<!-- None. -->

## Impact

- Shared `openspec-workflow` and `architecture-review` skill instructions and portable policy wording.
- `evidence-heavy` task/apply instructions and task template.
- Review-contract validation and its focused tests.
- Package behavior/evaluation tests that assert distributed policy and skill content.
- No consumer repository, production application, deployment, external system, or installed shared profile is changed by this implementation.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

The existing workflow skill, schema instructions, validator, and focused tests retain their current ownership. No production file is over 1000 lines, no single-file growth near 250 lines is expected, and the change adds no new runtime component or independently deployed responsibility.

## UI Contract

**Mode:** none

## Decisions

No separate material product decision is required: USER-001 authorizes the displayed risk-driven review corrections, while production authority and mandatory final review remain fail-closed.

## Open Questions

None.
