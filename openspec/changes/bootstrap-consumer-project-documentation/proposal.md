## Why

The portable package currently installs shared skills, schemas, and a managed consumer policy, but a newly adopted repository still lacks a durable project knowledge layer unless a user separately asks an agent to create it. That gap makes agents repeatedly reconstruct business, integration, architecture, and lifecycle context and makes the result depend on the development host that happened to initialize the project.

## Evidence

- USER-001: The user requested that newly created/adopted projects receive the same documentation guide, with an automatic initial audit and at minimum created files that later tasks keep updated.
- USER-002: The user requires the process to remain identical across Orca, Omnigent, Codex App, and other development environments.
- FACT-001: `scripts/workflow_package.py` currently accepts an explicit consumer repository but only plans/writes its managed `AGENTS.md` policy block; it does not create project handoff or OpenSpec configuration files.
- FACT-002: `policy/AGENTS.fragment.md` currently declares consumer ownership of project context but does not require a missing or pending project knowledge layer to be bootstrapped before normal work.
- OBS-001: A deterministic installer can prove repository structure and documentation presence, but it cannot infer unrecorded business rules. Semantic facts must remain pending until a repository-aware agent inspects evidence or the user supplies authority.

## What Changes

- Add one environment-neutral repository bootstrap contract to the existing installer/check engine. Host adapters may pass a repository path, but no generated project file or lifecycle rule varies by host target.
- During explicit consumer installation, audit the required project knowledge paths and create only missing scaffold files for project overview, business processes, integrations, technical architecture, open issues, and documentation status/navigation.
- Create a missing `openspec/config.yaml` with shared schema selection and stable links to the project knowledge layer, current specs, active changes, and archive. Preserve an existing config instead of heuristically rewriting YAML.
- Record a deterministic bootstrap audit that distinguishes observed repository structure, missing documentation, pending semantic audit, and confirmed current files without inventing project behavior.
- Extend the managed policy so any compliant agent detects a pending semantic audit, fills only evidence-backed facts and open questions before substantial project work, and updates affected handoff/current-spec layers through normal tasks and archive lifecycle.
- Make `check` report project-bootstrap `current`, `missing`, `stale`, or `conflict` state read-only and include the same repository in remediation argv.
- Keep bootstrap idempotent and bounded: existing non-managed project documentation is never overwritten or deleted, and partial scaffolds receive only missing files.

## Capabilities

### New Capabilities

- `consumer-project-knowledge-bootstrap`: Environment-neutral creation, audit, checking, and maintenance contract for a consumer repository's project documentation and OpenSpec navigation.

### Modified Capabilities

None. The managed-policy wiring is part of the new bootstrap capability because the prior policy change has not yet been archived into a central current spec.

## Impact

- Changes the public `install` and `check` JSON/human contracts when `--consumer-repo` is selected.
- Adds package-owned scaffold templates and repository-state helpers.
- May create missing consumer files under `docs/project-handoff/` and `openspec/config.yaml`; it does not alter product code, external services, Git history, or deployment state.
- Requires a package SemVer bump and updated PowerShell/POSIX usage documentation and tests.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** material

The change adds multiple independently testable responsibilities: repository knowledge-state classification, safe scaffold planning/writing, config conflict handling, deterministic audit generation, and installer/check orchestration. The design must keep those responsibilities outside the existing shared-root receipt and policy-marker logic while preserving `workflow_package.py` as the install transaction owner.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: Repository output is host-neutral
**Status:** accepted
**Source:** user:USER-002

The same consumer repository receives identical project files, audit states, validation, and lifecycle rules regardless of `codex`, `orca`, `omnigent`, Codex App, IDE, or shell. Target selection may resolve shared installation roots only.

### DEC-002: Missing-first, evidence-only bootstrap
**Status:** accepted
**Source:** user:USER-001

Bootstrap creates the required files when they are absent and marks semantic content pending; it does not invent business rules. Existing project content remains repository-owned and is not overwritten by heuristic reconciliation.

### DEC-003: Semantic audit is a workflow obligation, not an installer inference
**Status:** accepted
**Source:** user:USER-001, user:USER-002

The deterministic installer records structural evidence and a pending semantic-audit state. The portable managed policy requires the first repository-aware agent in any supported environment to inspect the project, populate confirmed facts and open questions, and clear that state before substantial implementation.

## Open Questions

None.
