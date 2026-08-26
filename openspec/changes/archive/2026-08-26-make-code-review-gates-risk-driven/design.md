## Context

The shared v3 review contract currently models every `openspec-wave` as an independent-review checkpoint. That makes the validator structurally safe but semantically over-broad: waves used only to organize implementation receive the same review cost as public-contract, security, data, and external-effect boundaries. The skill also places the final release review before any deploy, so a non-production deployment needed to discover runtime incompatibilities causes review/remediation/re-review loops before the evidence set is stable.

The implementation must reduce redundant reviewer launches without weakening architecture planning review, material dependency reviews, final full-diff coverage, external-effect authority, or production release gates.

## Goals / Non-Goals

Goals:

- Make intermediate independent review risk-triggered instead of wave-count-triggered.
- Keep semantic waves and targeted verification mandatory for evidence-heavy work.
- Make the default generated heavy plan final-review-only unless an inspected dependency boundary justifies an intermediate checkpoint.
- Preserve targeted re-review for material findings while consolidating fixes and reviewer continuations.
- Allow authorized test/staging deployments to produce evidence before final release review.
- Preserve compatibility with existing v3 task files that already contain one review checkpoint per wave.

Non-goals:

- Removing independent review from evidence-heavy changes.
- Weakening architecture review for material component growth or ownership changes.
- Authorizing deploy, release, production, or other external effects.
- Migrating or editing consumer repositories.
- Introducing reviewer quotas or a fixed maximum that could under-review an unusually risky change.

## Decisions

No new user-owned material decision is required. The following implementation choices are derived from the accepted requirements and the existing validator structure.

**Keep review contract v3 and relax only the wave cardinality rule**

The validator will continue to require at least one explicit semantic wave and exactly one final checkpoint for `evidence-heavy`. Each wave must contain implementation work. A wave may contain zero or one intermediate `openspec-review:wave` checkpoint; more than one remains invalid. When present, the checkpoint remains the last task in that wave and cannot be completed while covered tasks are incomplete.

This is backward-compatible: existing v3 changes with one checkpoint per wave remain valid, while newly generated plans can omit unjustified intermediate reviewers. No v4 marker or consumer migration is introduced.

**Make final-only the generated default**

The heavy tasks template will contain a semantic wave with verification work and a single final review. It will explain how to add an optional intermediate checkpoint only for a named material risk or downstream dependency boundary. Schema task/apply instructions and the skill will use the same trigger vocabulary.

**Treat review readiness and freshness as semantic gates**

Static validation can enforce marker placement and completion ordering, but cannot prove CI completion, diff stability, or semantic materiality. The skill/schema instructions therefore require the implementation agent to record:

- stable covered task/diff inventory;
- completed targeted verification;
- the material trigger for an optional intermediate review;
- post-review delta classification and deterministic evidence for any non-material delta.

The validator will not add brittle natural-language parsing for these facts. Behavioral/package tests will instead assert that every distributed instruction source carries the decision rule.

**Reuse one review cycle for its findings**

The implementation instruction will prefer one targeted continuation with the existing reviewer after related fixes are consolidated. A new reviewer remains allowed when the original reviewer is unavailable or the risk surface materially expands, but is not the default. Full review repeats only for cross-wave or overall-risk expansion.

**Move final release review after non-production evidence**

The skill and schema will say:

- test/staging evidence effects require explicit authority, bounded scope, rollback, and risk-proportionate preflight;
- they do not by themselves require the final release review;
- production release/deploy requires a current final full-pending-diff review after required non-production evidence and remediation.

Security-sensitive or otherwise material code used in test/staging may still receive a targeted intermediate review when its risk justifies it. This distinction changes review timing, not effect authority.

## Component Ownership

**Architecture impact:** none
**Inspected baseline:** `skills/openspec-workflow/SKILL.md` owns agent review decisions; `skills/architecture-review/SKILL.md` owns architecture coverage fields; `openspec/schemas/evidence-heavy/schema.yaml` and its tasks template own generated workflow instructions; `skills/openspec-workflow/scripts/validate_requirements.py` owns structural review-contract validation; existing focused tests own regression coverage.
**Expected growth:** small wording changes plus focused validator/test cases; no file is expected to grow by roughly 250 lines.
**Existing responsibilities:** unchanged.
**New responsibilities:** none; the existing review-contract responsibility becomes risk-driven.
**Transaction owner:** not applicable.
**Boundary options:** keep v3 and relax wave cardinality; introduce v4; or add a second review-plan marker.
**Decision:** keep-cohesive.
**Known cost:** semantic trigger/freshness truth remains an agent/reviewer responsibility because static Markdown validation cannot prove risk classification.
**Ratchet scope:** change only shared review planning, validation, and distribution tests; no consumer or unrelated workflow refactor.

## Risks / Mitigations

- Risk: an agent omits a necessary intermediate review. Mitigation: enumerate material triggers, require an explicit review-plan judgment, retain architecture and final full-diff gates, and test instruction distribution.
- Risk: a mechanical label hides a behaviorally material delta. Mitigation: define materiality by affected contract/risk surface rather than diff size or filename; uncertain deltas fail closed to targeted review.
- Risk: existing v3 changes become invalid. Mitigation: accept both zero and one checkpoint per wave and preserve all existing valid placements/attestations.
- Risk: test/staging wording is mistaken for deployment authority. Mitigation: repeat the explicit GO, rollback, scope, and preflight requirements and preserve production final-review gating.
- Risk: schema, skill, portable policy, and validator drift apart. Mitigation: update all owned distribution surfaces and add focused cross-file assertions to the existing package tests.

## Open Questions

None.
