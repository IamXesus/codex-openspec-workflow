## Why

The shared package currently installs skills and schemas but leaves its reusable agent policy as a manual review item. A consumer without `AGENTS.md` therefore resolves the workflow assets while new agents still lack the routing, evidence, review, and shared code-placement rules that make the workflow behave consistently.

## Evidence

- USER-001: The owner identified the missing-file behavior as a package gap and explicitly required the installer to create `AGENTS.md` when it does not exist.
- USER-002: The owner explicitly authorized implementation after the proposed behavior was stated: create a missing file, preserve existing user content, update only a managed block, fail closed on a user-modified managed block, expose policy state, and version the installed policy.
- FACT-001: At the inspected baseline `main` and `origin/main` both resolve to `ef751c09397de2303e0d9c4749bf94efbba37e03`; the worktree was clean before this change.
- FACT-002: `policy/AGENTS.fragment.md` is the canonical portable policy, but `scripts/workflow_package.py` currently reports `manual_review_required` and never edits a consumer repository.
- FACT-003: `--consumer-repo` already selects a consumer for read-only schema resolution, while shared skills and schemas use package-owned receipt and hash checks.
- FACT-004: The first inspected Pyrus consumer had no `AGENTS.md`; its policy had to be copied manually after the shared workflow installation.
- OBS-001: A consumer path is required to select the target `AGENTS.md`; shared-profile installation without `--consumer-repo` has no unambiguous project file to edit.

## What Changes

- Treat the portable policy as an installable, versioned consumer asset whenever `--consumer-repo` is explicitly selected.
- Create `AGENTS.md` when absent and append one bounded managed block when an existing file has no managed block, preserving all pre-existing text.
- Update only an intact managed block when the canonical policy or package version changes.
- Detect malformed, duplicated, or locally modified managed blocks as a conflict and fail before any install mutation.
- Report consumer policy state as `current`, `missing`, `stale`, or `conflict`; include the same selected consumer in the remediation command.
- Update documentation, wrappers, tests, and package version for the changed installation contract.

## Capabilities

### New Capabilities

- `managed-consumer-policy-adoption`: Safe, explicit installation and freshness checking of the central policy in consumer `AGENTS.md` files.

### Modified Capabilities

None. The earlier distribution change remains unarchived and the repository has no merged current-state specs to modify.

## Impact

- Central implementation surfaces: `scripts/workflow_package.py`, its state helper if needed, CLI wrappers, package tests, policy tests, package metadata, and `README.md`.
- Consumer surface: only `<consumer-repo>/AGENTS.md`, and only when `--consumer-repo` is explicitly supplied to install.
- Existing consumer text outside the managed block remains consumer-owned.
- No consumer source code, OpenSpec artifacts, schemas, Git state, remote repository, deployment, or automatic Git pull is changed by this capability.
- Real installation into a consumer remains a persistent external effect and requires its own last-safe-point `GO`; tests use isolated temporary repositories.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** material

The change adds independently testable policy parsing, state classification, conflict detection, and consumer-file mutation to the installation transaction. The existing public installer remains the intended transaction owner; the design must keep parsing/state mechanics cohesive and avoid a new generic configuration engine.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: Consumer policy adoption is explicit
**Status:** accepted
**Source:** user:USER-002

The installer manages a consumer policy only when `--consumer-repo` is supplied. Shared-profile installation without a consumer path continues to install only shared assets.

### DEC-002: Only one marked policy block is package-owned
**Status:** accepted
**Source:** user:USER-002

The package creates or updates one clearly delimited block in `AGENTS.md`. Text outside that block is never package-owned and is preserved byte-for-byte apart from the minimum boundary newline required when first appending the block.

### DEC-003: Local managed-block edits fail closed
**Status:** accepted
**Source:** user:USER-002

The managed block carries package version and canonical policy hash metadata. If its body no longer matches the recorded installed hash, or its markers are malformed or duplicated, check reports `conflict` and install performs no shared-root or consumer mutation.

### DEC-004: Policy freshness participates in consumer status
**Status:** accepted
**Source:** user:USER-002

With a selected consumer, check reports policy state `missing`, `current`, `stale`, or `conflict`. A missing or stale policy makes the overall check non-current and its remediation command retains the selected consumer path.

## Open Questions

None. Marker spelling, atomic file replacement, newline preservation, and helper placement are implementation details constrained by the accepted behavior and inspected codebase.
