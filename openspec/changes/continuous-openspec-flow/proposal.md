## Why

The canonical v3 workflow currently stops after creating each planning artifact and again at the planning-to-implementation boundary, even when every decision is already accepted and every gate passes. Those handoff pauses require repetitive user continuations without adding safety. The workflow should instead keep progressing autonomously until it genuinely needs user authority or a user-owned decision.

## Evidence

- USER-001: The owner wants the workflow to proceed automatically while everything is internally valid, including the planning-to-code transition, rather than stopping after each artifact.
- USER-002: The owner wants the workflow to stop as it does today when the agent has a question or otherwise requires user input.
- USER-003: The owner previously required a separate explicit `GO` before push, release, deploy, or other external effects; this authority boundary remains unchanged.
- FACT-001: The inspected baseline is clean branch `codex/continuous-openspec-flow` at `63d57aeb53e67edbe064ba6ad04529130db3de37`, equal to `origin/main` after PR #4 merged; PR #1 is closed.
- FACT-002: `skills/openspec-workflow/SKILL.md` currently requires exactly one artifact per continuation, explicitly stops after it, and requires a separate apply/build request after planning.
- FACT-003: The shared managed policy also says to advance planning one artifact at a time, while schema apply instructions require review gates but do not require a user response when those gates pass.

## What Changes

- Make an accepted software-change request authorize a continuous internal workflow from change creation through planning, implementation, verification, and required independent reviews.
- Run official artifact instructions and fail-closed gates in order, but do not yield merely because an artifact, planning phase, task, wave, test run, or clean review completed.
- Automatically repair in-scope validation failures and review findings when the accepted contract determines the fix; pause only when proceeding needs a user-owned decision, expanded authority, unresolved ambiguity, or an external-effect `GO`.
- Preserve explicit user scope: a request limited to exploration, review, diagnosis, or plan-only work ends at that requested boundary.
- Update the portable policy, documentation, regressions, and package version so consumer installations receive the same host-neutral behavior.

## Capabilities

### New Capabilities

- `continuous-openspec-execution`: User-intervention-aware continuous execution of the canonical v3 planning and implementation lifecycle.

### Modified Capabilities

None. The repository has no consolidated current specs for this workflow contract.

## Impact

- Expected edits are limited to canonical workflow/policy text, narrowly relevant schema instructions or templates, existing policy tests, README, version metadata, and this OpenSpec package.
- OpenSpec CLI remains the artifact engine; no new command runner, dependency, background process, host integration, external effect, consumer mutation, or deployment is authorized.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

The change revises prompt-level orchestration policy and regressions. It adds no production responsibility, transaction boundary, independently deployed component, or approximately 250 production lines to one file.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: A clear change request authorizes continuous internal delivery
**Status:** accepted
**Source:** user:USER-001

After the user requests a software change, the agent advances through all ready planning artifacts, implementation tasks, verification, and required reviews without asking for routine continuation or a second apply command, provided scope and authority remain clear and gates are satisfiable.

### DEC-002: Only user-action-required conditions pause the workflow
**Status:** accepted
**Source:** user:USER-002, user:USER-003

The agent pauses only when it needs a user-owned decision or clarification, the requested scope explicitly ends, a blocker cannot be resolved within accepted scope, or a separate external-effect approval is required. Successful checkpoints and autonomously repairable failures are not user pauses.

## Open Questions

None.
