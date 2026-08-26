## Context

The current v1.4 workflow already separates semantic implementation waves from independent-review triggers and retains a final full-pending-diff review. The inspected PayFlow session nevertheless fragmented delivery because blocking findings were summarized incompletely and broad CI was repeated during microfix iteration. This change tightens the existing lifecycle without creating another review or evidence subsystem.

## Goals / Non-Goals

Goals:

- make one final full-diff code review the normal completion path;
- preserve intermediate review only for a material boundary needed by later work;
- preserve the existing pre-implementation architecture review for material architecture designs;
- keep every High and Medium finding accounted for through remediation;
- run focused checks during diagnosis and required broad checks on a coherent stable batch;
- expose the same rule in installed skills and the managed consumer policy.

Non-goals:

- removing architecture review, final code review, CI, or risk-triggered targeted re-review;
- imposing numeric limits on tests, pipelines, findings, or reviewers;
- persisting review-session state in a new repository artifact;
- changing PayFlow product behavior or its current OpenSpec tasks.

## Decisions

### DEC-001: Extend the existing risk-driven lifecycle
**Status:** accepted
**Source:** user:USER-001

Strengthen the existing `risk-driven-review-orchestration` capability and its current instruction surfaces. Do not introduce a parallel review mode, workflow engine, validator, or ledger file. The coordinator retains a compact session ledger keyed by reviewer-assigned finding ids.

### DEC-002: Keep architecture and completion gates distinct
**Status:** accepted
**Source:** user:USER-001

Material architecture impact continues to require the existing independent architecture review and fail-closed validator before affected production edits. Review economy applies to implementation/code-review cadence: normally one final full-diff review, with an intermediate checkpoint only when later work depends on an inspected material boundary. An early critic is advisory and cannot satisfy either gate.

### DEC-003: Verify coherent batches without fixed quotas
**Status:** accepted
**Source:** user:USER-001

Use the cheapest faithful deterministic signal while diagnosing or correcting a narrow failure. Consolidate related safe corrections, then run the required broad regression or CI once the slice is stable. A material delta still stales its affected evidence and receives targeted re-review; no numeric quota replaces that judgment.

### DEC-004: Release as version 1.5.0
**Status:** accepted
**Source:** user:USER-001

The change adds backward-compatible shared workflow behavior and is released as the next minor version, `1.5.0`. Existing installer receipts and managed-block replacement provide the rollback boundary for local and test-host installation.

## Component Ownership

**Architecture impact:** none
**Inspected baseline:** existing Markdown instruction/specification assets and package tests; no runtime production component changes
**Expected growth:** small instruction and regression-test additions, below the material growth threshold
**Existing responsibilities:** workflow orchestration, review guidance, implementation guardrails, schema prompts, and managed consumer policy
**New responsibilities:** none; the same surfaces make their existing review lifecycle more explicit
**Transaction owner:** not applicable
**Boundary options:** extend current capability or introduce a separate review-economy subsystem
**Decision:** keep-cohesive
**Known cost:** equivalent wording must remain aligned across the existing distribution surfaces
**Ratchet scope:** no broad refactor; change only the current review and verification guidance plus focused regression coverage

## Risks / Mitigations

- Agents could interpret fewer code reviews as removal of architecture review. Mitigation: state the material-design architecture gate explicitly in the capability, controller, schema, and managed policy.
- Agents could skip broad verification entirely. Mitigation: require current CI/full-suite evidence after the coherent batch and before the completion reviewer when applicable.
- Findings could still disappear in coordinator summaries. Mitigation: stable ids for every High/Medium finding and a complete session disposition ledger.
- Repeated wording could drift. Mitigation: extend an existing cross-file policy regression instead of adding a new framework.

## Migration And Rollback

Publish `1.5.0`, install through the existing package installer, and retain installer-created backups/receipts. If an installation check fails, restore the prior shared skill roots and managed policy from the operation-specific backup or reinstall `1.4.0`; no product data migration is involved.

## Open Questions

None.
