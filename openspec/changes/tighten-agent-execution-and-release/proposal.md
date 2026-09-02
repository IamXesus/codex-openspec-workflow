## Why

The current workflow has useful risk-based review rules, but the PayFlow run showed three practical failures: a primary agent waited on a subagent, a reviewer suggestion broadened a narrow ACL fix into an unaccepted database strategy, and continuation after context loss did not preserve the repository root or CI-only execution boundary. The shared instructions need a compact execution-boundary contract so agents stay fast on small work without silently changing security, data, or ownership contracts.

## Evidence

- USER-001: The owner asked to fix the workflow after observing slow task slicing, blocking subagent behavior, scope drift after review, wrong OpenSpec directory resolution, and a missed CI continuation.
- OBS-001: A localized frontend cache fix entered an `evidence-core` change even though its behavior and acceptance path were already clear.
- OBS-002: A primary agent launched a subagent and waited instead of continuing independent work.
- OBS-003: A validator invocation from `frontend/` searched for `frontend/openspec` although the repository root owned `openspec/`.
- OBS-004: A reviewer found a valid edge case, but later remediation proposals crossed ACL, persistent-data, and deletion-ownership boundaries without a new owner decision.
- OBS-005: A CI-only backend boundary was not preserved across continuation, and a package check prompted an unrelated consumer-config edit.
- HYP-001: Explicit scope, continuation, and skip-spec wording plus one deterministic contract check should prevent these failures without a new orchestration subsystem.

## What Changes

- Keep the three existing routes explicit: direct small change, `evidence-core` for an explicitly requested localized plan, and `evidence-heavy` for broad or materially risky work.
- Require one primary executor by default; subagents are optional, bounded, and never a blocking dependency.
- Make reviewer output advisory/read-only: `READY` confirms only the declared coverage, not a new architecture, ACL, migration, deletion, transaction, or external-effect strategy.
- Require a short reorientation after a fresh session or context compaction, including current authority, artifacts, repository state, root, and execution constraints.
- Make `skip_specs: true` carry a structured no-behavior-delta marker and fail closed when the marker is absent.
- Keep verification minimum-sufficient and risk-based; low/medium effort is a host-neutral hint and never changes scope or gates.
- Continue authorized push/release flows through CI and post-deploy verification; push is not completion.

## Capabilities

### New Capabilities

- `execution-boundary-contract`: Preserve scope, authority, continuation state, and explicit execution constraints.

### Modified Capabilities

- `risk-driven-review-orchestration`: Add the reviewer scope boundary while retaining final-only review economy.
- `portable-openspec-invocation`: Keep OpenSpec and package checks rooted and read-only.

## Impact

- Existing shared policy, workflow/guardrail/reviewer skills, both schema instructions/templates, the deterministic requirement validator, package tests, and prompt-routing fixtures.
- No PayFlow product code, C4 artifact, consumer documentation, host installation, model provider, or host-specific effort setting.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

This is a compact extension of existing instruction and validation surfaces. It adds no runtime production component, data store, orchestration service, or new responsibility owner.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: Keep three routes and one primary executor
**Status:** accepted
**Source:** user:USER-001

Small clear work uses the direct route; explicit localized plans use `evidence-core`; broad or material work uses `evidence-heavy`. One primary agent owns a cohesive change; delegation is bounded and non-blocking.

### DEC-002: Review findings cannot authorize scope expansion
**Status:** accepted
**Source:** user:USER-001

A reviewer reports evidence and fix direction only. Any change to architecture, ACL/security, persistent data, migrations, transactions, deletion semantics, or external effects is a proposed scope change until explicitly accepted by the owner.

### DEC-003: Continuation and `skip_specs` remain fail-closed
**Status:** accepted
**Source:** user:USER-001

After context loss the agent re-reads authority, artifacts, repository state, and execution constraints. A `skip_specs: true` change must carry the structured no-behavior-delta marker; otherwise it cannot reach tasks or implementation.

### DEC-004: Verification and effort remain risk-driven
**Status:** accepted
**Source:** user:USER-001

Use the minimum-sufficient faithful evidence for distinct risks without numeric test quotas. Low is the default effort hint for direct work and medium for heavy/security/data/release review; effort does not grant authority or remove gates.

## Open Questions

None.
