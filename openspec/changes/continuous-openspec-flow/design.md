## Context

The package controls reusable orchestration through `skills/openspec-workflow/SKILL.md`, the managed `policy/AGENTS.fragment.md`, generated schema instructions, and routing evaluations. OpenSpec CLI also installs generic `openspec-new-change` and `openspec-continue-change` skills whose upstream contract is intentionally stepwise. The canonical package does not own those generated skills, so its controller and consumer policy must drive the official `status → instructions → artifact` loop directly for default end-to-end work instead of delegating progression to a helper whose contract stops after one artifact.

The existing apply helper already loops over tasks until blocked. Required validators, architecture checks, wave reviews, final review, and external-effect approvals remain gates; the change is whether a passing or autonomously repairable gate returns control to the user.

## Goals / Non-Goals

- Define one continuous default from a clear software-change request through local implementation, verification, and review.
- Preserve official artifact dependency order, evidence/acceptance rules, traceability, architecture checks, and independent reviews.
- Make the pause predicate explicit and user-action-based across the portable skill, managed policy, schemas, README, and routing tests.
- Preserve explicit plan-only/read-only boundaries and separate external-effect `GO` gates.
- Do not fork the OpenSpec CLI, add a workflow runner, background process, dependency, or host-specific automation.
- Do not take ownership of the CLI-generated stepwise helper skills; an explicit user request for a single-step helper remains an explicit scope boundary.

## Decisions

No additional material decisions are required beyond DEC-001 and DEC-002 in `proposal.md`.

## Component Ownership

**Architecture impact:** none

**Inspected baseline:** `skills/openspec-workflow/SKILL.md` owns canonical routing/orchestration; `policy/AGENTS.fragment.md` owns the installed consumer-level authority contract; `openspec/schemas/evidence-core/schema.yaml` and `evidence-heavy/schema.yaml` provide generated artifact/apply instructions; `evals/promptfoo/` owns routing regression evaluation; package metadata owns distributed version identity.

**Expected growth:** focused policy wording and static/routing regressions in existing files, plus one small Promptfoo assertion; no production Python responsibility or approximately 250-line production growth.

**Existing responsibilities:** unchanged. The controller interprets user intent and calls official OpenSpec CLI operations; schemas enforce artifact/review evidence; policy applies host-neutral authority boundaries; Promptfoo tests routing semantics.

**New responsibilities:** none. Existing orchestration changes from per-artifact yielding to a continuous loop with an explicit pause predicate.

**Transaction owner:** not applicable; there is no new data or external transaction.

**Boundary options:** (1) fork/own CLI-generated new/continue/apply skills, rejected because it expands package ownership and creates upgrade coupling; (2) add a generic runner, rejected as unnecessary framework; (3) keep the canonical controller/policy authoritative and drive official CLI operations directly, selected as the smallest existing boundary.

**Decision:** keep-cohesive

**Known cost:** explicitly invoking a CLI-owned single-step helper still requests that bounded helper behavior; default end-to-end routing must not delegate to it.

**Ratchet scope:** change only lifecycle progression/pause wording, matching regressions, and synchronized version metadata; no installer, receipt, bootstrap, validator-algorithm, review-contract, or CLI ownership refactor.

## Risks / Mitigations

- Continuous flow could silently invent missing decisions. Keep blocking `Q-*`, proposed-decision, semantic entailment, and authority gates unchanged; only accepted evidence permits progress.
- Continuous flow could blur external authority. State explicitly that push, release, deploy, production mutation, and other governed effects still require their separate `GO`.
- A validation failure could be bypassed in the name of continuity. Keep gates fail-closed; attempt only in-scope corrections, rerun affected evidence, and pause when repair requires user disposition.
- Mandatory reviews could be skipped. Keep review checkpoints and independent reviewers; dispatch, wait, remediate, and continue automatically only after passing evidence.
- Host routing could remain stepwise. Put the same contract in the portable skill and installed managed policy, and verify it with static tests plus Promptfoo against the host-neutral fixture.
- Repeated self-repair could loop. After safe in-scope alternatives are exhausted, surface the unresolved blocker and request the specific user decision rather than retrying indefinitely.

## Migration And Rollback

The next package version is a SemVer minor because default workflow behavior changes while schemas and installer interfaces remain compatible. Existing installations remain unchanged until explicitly updated. Rollback uses the existing package backup/receipt workflow or the prior released package; no consumer or runtime state migration is introduced.

## Open Questions

None.
