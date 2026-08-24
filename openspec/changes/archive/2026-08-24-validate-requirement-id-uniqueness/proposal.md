## Why

OpenSpec native strict validation currently allows duplicate stable requirement IDs across current specifications, so archive can silently create ambiguous traceability even when validation reports success.

## Evidence

- USER-001: The user explicitly requested the mandatory workflow fix identified by the prior audit: validate repository-wide requirement ID uniqueness before and after archive.
- OBS-001: The shared validator currently checks duplicate requirement IDs only inside one active change's v3 traceability contract.
- OBS-002: The prior PayFlow archive produced IDs that collided with existing current specifications while native strict validation still passed.

## What Changes

- Validate that every `REQ-*` ID under `openspec/specs/` is globally unique.
- While validating an active change, reject an `ADDED` requirement whose ID already exists in current specifications.
- Provide a standalone repository gate for use after archive and require it in the shared workflow instructions.

## Capabilities

### New Capabilities

- `repository-requirement-id-integrity`: Fail closed on ambiguous stable requirement IDs in current specifications and on pre-archive `ADDED` collisions.

### Modified Capabilities

## Impact

- Shared Python validators, their focused unit tests, and the installed workflow instructions.
- No consumer repository data, server state, release, or external system is changed.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

## UI Contract

**Mode:** none

## Decisions

## Open Questions
