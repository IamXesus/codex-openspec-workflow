## Why

Inspection of a fresh PayFlow Omnigent session showed that the risk-driven test rule reduced the final test delta to one parameterized PostgreSQL vertical slice, but delivery still spent avoidable time on fragmented finding remediation and repeated full CI pipelines. The workflow needs a small follow-up contract that preserves meaningful review and runtime evidence while preventing dropped findings, premature checkpoint reviews, and one-full-suite-per-microfix iteration.

## Evidence

- USER-001: After reviewing the concrete session evidence and the recommended finding-ledger, review-sequencing, canonical-fixture, and CI-economy improvements, the user explicitly requested implementation, a new release, publication, and installation on the test host and locally.
- OBS-001: The inspected session used one exploration subagent and one reused reviewer, but the first reviewer reported five blocking findings while the coordinator summarized only three; two residual findings forced another targeted review before the slice reached `READY`.
- OBS-002: The same slice produced ten sequential commits/pipelines. Eight pipelines failed; several failures came from compile or test-arrangement/diagnostic corrections rather than new accepted behavior.
- OBS-003: The final test delta added one parameterized PostgreSQL Theory for four payment profiles and did not add overlapping Fact-per-scenario tests.
- FACT-001: `openspec/specs/risk-driven-review-orchestration/spec.md` already requires stable verified scope, consolidated remediation, delta-based re-review, and one final full-pending-diff checkpoint, but it does not require stable finding identifiers or full finding reconciliation before continuation.
- FACT-002: `skills/openspec-workflow/SKILL.md` and the review skills distinguish risk-driven evidence from test count, but the portable consumer policy does not expose the complete finding-ledger and coherent verification-iteration contract when a skill is not freshly loaded.

## What Changes

- Require reviewers to assign stable identifiers to every High and Medium finding and require the coordinator to reconcile the complete blocking ledger before requesting targeted continuation.
- Treat an optional early read-only critic as diagnostic input only; it cannot satisfy an intermediate or final review checkpoint. Batch its safe findings before CI or the next deterministic verification run rather than reviewing every fix.
- Run deterministic checks and full-suite regression on coherent stable batches. Prefer existing focused checks or job retry for unchanged flaky evidence; do not publish one diagnostic commit or run one full suite per microfix by default.
- Keep every exception risk-driven: no fixed reviewer, pipeline, test, or remediation quota; a material post-review delta still receives targeted re-review and a final current full-diff review remains mandatory.
- Distribute the essential contract through the OpenSpec controller, code reviewer, coding guardrails, portable `AGENTS.md` policy, and their existing focused package tests.
- Advance the package to the next backward-compatible minor release, publish it, and install the released package on the explicitly authorized test host and local shared roots with existing rollback safeguards.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `risk-driven-review-orchestration`: Add complete finding-ledger reconciliation, distinguish early critics from checkpoint reviews, and make CI/test iteration coherent without weakening risk-triggered re-review or final coverage.

## Impact

- Shared `openspec-workflow`, `code-reviewer`, and `coding-guardrails` skill instructions.
- Portable consumer policy and existing cross-file policy/package regressions.
- The current risk-driven review specification and this v3 change package.
- Package metadata, release notes, GitHub publication, and explicit local/test installations.
- No PayFlow product behavior, production deployment, 1C/Bitrix write, database mutation, or consumer OpenSpec task rewrite is authorized by this change.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

The change updates existing instruction and distribution assets, adds no runtime service or responsibility, touches no production file over 1000 lines, and does not expect roughly 250 lines of growth in one production file.

## UI Contract

**Mode:** none

## Decisions

No separate material decision is required. USER-001 authorizes the displayed process improvements and release/install scope; existing external-effect and production boundaries remain unchanged.

## Open Questions

None.
