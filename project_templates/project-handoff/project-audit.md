<!-- codex-openspec-project-audit:v1 status=pending -->
# Primary project audit

Semantic audit status: **pending**. The bootstrap created this file from structural observations only. It did not infer business rules, integrations, architecture, deployment state, or requirements.

## Pre-bootstrap structural observations

{{STRUCTURAL_OBSERVATIONS}}

## Canonical layer observations

{{CANONICAL_OBSERVATIONS}}

## Confirmed facts

No semantic project facts have been confirmed yet.

## Open questions

- Which user or inspected source is authoritative for the project's business purpose and workflows?
- Which integrations, runtime boundaries, persistent data, security rules, and deployment conventions are confirmed?

## Completion contract

A repository-aware agent completes this audit before substantial implementation by inspecting the repository and applicable user authority, updating the canonical handoff files with confirmed facts, recording unresolved questions, and changing only the marker status from `pending` to `complete`. The audit must record the inspected Git state and evidence paths. Unknowns remain explicit and must not be converted into requirements.
