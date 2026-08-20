## Context

The package already has Windows and POSIX wrappers and one package-engine branch for OpenSpec executable names. The remaining incompatibility is in portable skill text and its bundled validation gate: both can select the Windows launcher independently of the host contract. This change aligns those existing call sites without changing installer ownership or taking ownership of CLI installation.

## Goals / Non-Goals

- Make every portable OpenSpec instruction use one explicit platform branch.
- Make package and bundled-validator executable discovery deterministic and testable without the developer PATH.
- Preserve the existing installer, receipt, policy, bootstrap, and rollback responsibilities.
- Prove both package targets through the existing POSIX wrapper in isolated roots.
- Do not add a shared resolver framework, dependency, implicit CLI installation, consumer migration, or external publication.

## Decisions

No additional material decisions are required beyond DEC-001 through DEC-003 in `proposal.md`.

## Component Ownership

**Architecture impact:** none

**Inspected baseline:** `scripts/workflow_package.py` owns package install/check/rollback orchestration and already contains `consumer_resolution`; `skills/openspec-workflow/scripts/validate_change.py` owns the installed skill's validation-gate subprocess; `skills/openspec-workflow/SKILL.md` owns portable agent instructions.

**Expected growth:** a small executable-resolution helper and focused regressions in existing files; no production file is expected to grow by approximately 250 lines or gain an independent responsibility.

**Existing responsibilities:** package orchestration and consumer schema resolution remain in `workflow_package.py`; native/custom change validation remains in `validate_change.py`; workflow routing and command guidance remain in the skill.

**New responsibilities:** none. Existing executable discovery becomes platform-correct and injectable for isolated tests.

**Transaction owner:** unchanged; `workflow_package.py` remains the sole package lifecycle operation owner.

**Boundary options:** keep the two small host-specific resolvers beside their existing subprocess owners; a new shared module is rejected because it would add a framework boundary for two bounded call sites.

**Decision:** keep-cohesive

**Known cost:** the same short platform branch exists in two independently installed Python entry points.

**Ratchet scope:** no installer, receipt, policy, bootstrap, rollback, or runtime-state refactor; change only portable executable selection, its tests/docs, and synchronized version metadata.

## Risks / Mitigations

- A regression could pass because the developer machine already has `openspec.cmd`. Mitigation: inject executable discovery in unit tests and run POSIX rehearsal with an isolated PATH containing only a temporary `openspec` executable.
- Documentation could mix executable conventions between phases. Mitigation: define one placeholder-based platform selection once and make every portable command use it; scan the pending portable surfaces for unconditional Windows-only commands.
- POSIX rehearsal could mutate real profiles. Mitigation: supply explicit temporary HOME, agent, schema, consumer, and backup roots for every lifecycle command and inspect outputs before cleanup.
- A version bump could drift between metadata and receipts. Mitigation: use existing metadata validation and update package and lock files together to `1.1.1`.

## Open Questions

None.
