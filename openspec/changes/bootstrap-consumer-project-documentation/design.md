## Context

The current package has three ownership layers:

1. `workflow_package.py` orchestrates shared-root install/check/rollback and writes consumer policy only after shared assets succeed.
2. `workflow_package_state.py` owns path containment, package receipts/backups, and the bounded `AGENTS.md` managed-block state machine.
3. Consumer repositories own all text outside the managed policy block and all project-specific facts.

Project knowledge bootstrap adds repository files that become consumer-owned immediately after creation. Unlike shared skills or the managed policy block, their evolving semantic content cannot be compared to package template hashes. The package therefore needs a structural state machine and a small package-owned audit marker, not another content receipt that would treat legitimate documentation edits as drift.

## Goals / Non-Goals

### Goals

- Produce one host-neutral project knowledge layout from the same selected repository state.
- Create only absent canonical files and preserve all existing consumer bytes and modes.
- Record deterministic structural evidence and an explicit pending/completed semantic-audit marker.
- Make install/check surface project-bootstrap state and fail before mutation on unsafe paths.
- Keep future agents responsible for evidence-backed semantic audit and documentation maintenance.

### Non-Goals

- Infer business processes, integrations, architecture, deployment state, or requirements from filenames.
- Invoke an AI/model, host API, Orca hook, Omnigent hook, Git mutation, OpenSpec archive, or remote service.
- Rewrite an existing `openspec/config.yaml`, migrate arbitrary legacy docs, or delete consumer files.
- Make consumer documentation part of shared-root rollback or hash receipts.

## Decisions

The material product decisions are DEC-001 through DEC-003 in `proposal.md`. The implementation choices below are constrained mechanics rather than new user-owned behavior.

**Canonical repository layout**

The package ships UTF-8/LF templates for:

- `docs/project-handoff/README.md`
- `docs/project-handoff/project-audit.md`
- `docs/project-handoff/business-processes.md`
- `docs/project-handoff/integrations.md`
- `docs/project-handoff/technical-architecture.md`
- `docs/project-handoff/open-issues.md`
- `openspec/config.yaml`

Every semantic template states that missing facts are unknown and must be supported by inspected evidence or an explicit user decision. The README defines reading order and ownership. The config selects `evidence-core` and injects stable relative navigation for project handoff, current specs, active changes, archive, and Git history.

**Structural audit state**

`project-audit.md` starts with one exact package marker:

```text
<!-- codex-openspec-project-audit:v1 status=pending -->
```

Bootstrap renders a sorted, bounded and Markdown-safe list of pre-bootstrap top-level repository entries as observations, excluding `.git` and never following symlinks. It separately records present/missing state for every canonical documentation file and for `openspec/specs/`, active `openspec/changes/`, and `openspec/changes/archive/`. The package does not rewrite an existing audit file. A repository-aware agent may change only `status=pending` to `status=complete` after recording inspected evidence, unresolved questions, and the audit date/commit state in the body.

Check validates the marker form and distinguishes structural file state from semantic-audit status. Missing marker in an existing repository-owned audit is `stale` with reconciliation guidance; duplicate/malformed reserved markers or unsafe path types are `conflict`.

**State and write model**

A new focused `scripts/workflow_project_bootstrap.py` collaborator owns:

- canonical relative paths and template loading;
- contained consumer path validation;
- structural observation rendering;
- `missing`/`current`/`stale`/`conflict` classification;
- prepared writes for absent files;
- sibling-temp atomic creation of individual files, with containment and canonical-parent identity revalidated immediately before temporary creation and again before exclusive publication.

`workflow_package.py` remains the only operation/transaction owner. It preflights policy, project bootstrap, shared manifests, receipts, backup, and conflicts before any mutation. It then installs shared roots, writes the managed policy, and creates prepared missing project files. Individual project files are atomic; the multi-file bootstrap is resumable rather than globally atomic because existing consumer files must never be replaced during recovery.

**Existing config and documentation**

An absent config receives the canonical template. An existing config is preserved byte-for-byte. Without introducing a general YAML rewriter, check validates the canonical structural subset: a root-level `schema: evidence-core` and a root-level literal `context` block containing distinct references to project handoff, current specs, active changes, archive, and Git history. Comments or an archive reference cannot accidentally satisfy the active-change requirement. A nonconforming readable config is `stale` with manual reconciliation guidance. It is `conflict` only for containment/symlink/type/encoding failures or malformed reserved audit metadata; install may create other missing files but never repairs existing YAML heuristically.

Canonical Markdown files other than the audit are presence/type/containment checked only. Their body is repository-owned, so legitimate task updates never create package drift.

**Version and adapters**

The public package version advances from `1.0.1` to `1.1.0` because explicit consumer installation gains a new repository-visible capability. PowerShell/POSIX wrappers remain thin argv adapters. `codex`, `orca`, and `omnigent` affect only shared-root resolution; all project-bootstrap planning receives the same resolved consumer path and templates.

## Component Ownership

**Architecture impact:** material

**Inspected baseline:** `scripts/workflow_package.py` 392 LOC; `scripts/workflow_package_state.py` 474 LOC; `scripts/test_workflow_package.py` 699 LOC; package templates currently contain only the 41-line managed policy fragment.

**Expected growth:** new `scripts/workflow_project_bootstrap.py` approximately 245-290 production LOC after fail-closed structural validation and publish-time containment checks; `workflow_package.py` approximately 45-80 LOC of orchestration/output wiring; `workflow_package_state.py` 0-15 LOC only if a containment primitive must be reused/exported; six Markdown templates plus one YAML template; tests approximately 360-520 LOC.

**Existing responsibilities:** engine owns CLI orchestration and shared install/check/rollback; state helper owns shared receipts/backups, containment, and managed-policy integrity; policy template owns reusable agent rules.

**New responsibilities:** focused collaborator owns project knowledge structural classification, deterministic initial observations, template rendering, and safe missing-file creation; engine coordinates it with existing preflight and mutation order; policy gains the semantic-audit/maintenance obligation.

**Transaction owner:** `scripts/workflow_package.py` remains the sole install/check operation owner. Project bootstrap opens no external or database transaction.

**Boundary options:** (1) add all project logic to `workflow_package.py`; rejected because it adds an independently testable state machine to orchestration. (2) add it to `workflow_package_state.py`; rejected because shared receipts/policy integrity and evolving consumer documentation change for different reasons. (3) extract one project-bootstrap collaborator and keep the engine as coordinator; selected.

**Decision:** extract-collaborators

**Known cost:** one additional internal module and a resumable rather than globally atomic multi-file consumer write. The boundary avoids a generic plugin/template engine and keeps canonical layout fixed.

**Ratchet scope:** add only the accepted canonical project-bootstrap state/writes and engine wiring; do not refactor shared receipts, policy parsing, host root resolution, rollback, arbitrary YAML editing, or existing tests unrelated to this capability.

## Risks / Mitigations

- **Risk: scaffold is mistaken for confirmed documentation.** Templates and audit marker explicitly label semantic facts pending; managed policy blocks substantial work until audit reconciliation.
- **Risk: existing project content is damaged.** Preflight validates containment/type/symlinks; writes use exclusive missing-file creation semantics and never replace existing docs/config.
- **Risk: host behavior drifts.** Tests run the same consumer input under every target with explicit temporary shared roots and compare consumer bytes.
- **Risk: partial filesystem failure creates half a scaffold.** Each file is atomically created, existing files remain untouched, and rerun creates only the remaining missing paths.
- **Risk: check becomes noisy after legitimate doc edits.** Only audit metadata and structural presence are package-checked; semantic Markdown bodies are repository-owned.
- **Risk: existing YAML needs integration.** It is reported stale with exact missing navigation tokens; automatic YAML rewriting remains out of scope.

## Migration And Rollback

Existing consumers are adopted on their next explicit install/check. Missing files can be created; existing handoff/config content is preserved. No automatic migration or deletion occurs.

Shared-root rollback remains unchanged and does not delete consumer project files. Before commit, repository owners can recover via normal Git. For an uncommitted empty bootstrap, manual removal is safe only after verifying each target was newly created and still contains no repository-authored semantic content; the package does not automate that destructive decision.

## Open Questions

None.
