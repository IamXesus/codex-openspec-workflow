---
name: architecture-review
description: Review production code and diffs for class-level cohesion, oversized methods or services, responsibility creep, misplaced transaction boundaries, and complexity hidden in private helpers. Use when Codex is asked for an architecture review, maintainability audit, independent diff review, investigation of growing services/components, or an architecture checkpoint before or after a substantial implementation wave.
---

# Architecture Review

Perform an evidence-based, read-only review unless the user explicitly asks to implement changes. Evaluate architecture relative to the repository's actual conventions and requested scope; do not impose a preferred pattern without evidence.

## Workflow

1. Establish scope and evidence.
   - Identify the base and current state, accepted requirements, changed-file inventory, completed implementation waves, verification evidence, known limits, and explicit exclusions.
   - State whether coverage is full or partial. Never present partial coverage as a full-diff review.

   For an OpenSpec or other pre-implementation planning review:
   - Inspect the actual repository baseline instead of trusting estimated component sizes in the artifacts.
   - Require explicit component ownership when a planned wave touches an existing file over 1000 lines, expects roughly 250 or more production lines in one file, or adds multiple independently testable responsibilities.
   - Require the plan to record current sizes, expected growth, existing and new responsibilities, transaction owner, considered boundary options, chosen outcome, and known cost.
   - Return `NOT READY` when a triggered checkpoint is missing, stale, or contradicted by the inspected code. Do not proceed to production edits; update and revalidate the planning artifacts first when the user has authorized artifact changes.
   - When the proposal contains `<!-- openspec-architecture-contract:v1 -->`, run `scripts/validate_openspec_architecture.py --repo <repo> --change <name> --phase planning|apply|verify` as a separate fail-closed step. A nonzero exit blocks the requested phase; do not replace it with a prose verdict.

2. Measure production growth.
   - Use repository-native search and diff tools to collect production LOC delta by file, current file sizes, and approximate method/component spans.
   - Treat files over 1000 lines, additions of roughly 250 or more production lines to one file, methods around 100-150 lines or longer, and clusters of new private helpers or nested records as investigation signals, not automatic defects.
   - Exclude generated code, migrations, fixtures, snapshots, and data-only files unless their structure is directly relevant.

3. Map responsibilities.
   - Name each affected component's existing responsibilities and the independently testable responsibilities added by the change.
   - Trace authorization, orchestration, transaction ownership, state loading and guards, domain calculations, history/scope reconstruction, persistence, audit/idempotency, external integration, and presentation concerns when present.
   - Separate confirmed code evidence from inference and unknown intent.

4. Test component boundaries.
   - Ask whether each responsibility changes for the same reason and uses the same invariants.
   - Do not infer that one database transaction requires one class. A transaction-owning orchestrator may coordinate cohesive collaborators through the same unit of work.
   - Detect cosmetic decomposition: a shorter public method is not an architectural improvement when complexity merely moves into numerous private helpers while the class keeps several reasons to change.
   - Detect the opposite failure too: do not recommend pass-through wrappers, generic utility buckets, speculative frameworks, or one-method files merely to reduce line counts.
   - Prefer existing domain boundaries and dependency direction. Recommend a new collaborator only when it owns cohesive rules or data transformations and reduces a current reason-to-change conflict.

5. Review change shape and testability.
   - Check whether business rules can be tested without constructing an unrelated god service.
   - Check whether persistence details leak into domain calculations, whether reconstruction/history logic is duplicated, and whether new commands silently expand an existing service's public or private role.
   - Compare implemented ownership with design/spec artifacts; flag missing ownership decisions rather than inventing them.

6. Report findings.
   - Lead with findings ordered by severity and include concrete file/line evidence, impact, and the smallest coherent remediation direction.
   - Include a growth-hotspot summary, responsibility map, coverage statement, exclusions, and unknowns.
   - If no blocking issue exists, say so explicitly while still recording material maintainability risks.
   - Distinguish architecture quality from green tests, requirement completion, release readiness, and deployment state.
   - For an architecture-sensitive implementation wave, require an independent read-only code reviewer to record Coverage, Growth, Ownership, Findings, Exclusions, and Reviewer. A validated High finding blocks dependent work; resolve a validated Medium finding or obtain explicit user disposition.

## Architecture Checkpoint Output

For a pre-implementation checkpoint, record:

- current component and approximate size;
- expected production LOC growth;
- existing and new responsibilities;
- transaction owner and proposed collaborators;
- decision: keep cohesive, extract collaborators, or accept a temporary exception;
- evidence and known cost of that decision.

For OpenSpec planning, end with exactly one readiness verdict:

- `READY`: inspected baseline and component ownership are coherent, and every triggered growth checkpoint has a recorded decision.
- `NOT READY`: name each missing or stale planning fact that must be resolved before implementation.
