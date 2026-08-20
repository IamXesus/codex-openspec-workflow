## Context

The repository already distributes five skills and two OpenSpec schemas through `scripts/install.ps1` and `scripts/install.sh`. The PowerShell installer is 106 lines and owns target selection, recursive overlay copy, dry-run, and exact-content checking; the POSIX installer is 37 lines and currently owns only target selection and overlay copy. `scripts/validate.ps1` is 64 lines and validates skills, Python validators, schemas, and portable content. `package.json` exists but contains only the promptfoo development dependency, so the package has no declared name or version.

The current design duplicates target/copy rules between wrappers and cannot express one versioned receipt consistently. It also chooses Codex's target from `CODEX_HOME` or `~/.codex`, while the inspected Orca runtime exposes a stable `~/.agents/skills` root alongside a transient account-scoped Codex home. PayFlow's project-local schemas currently shadow user-installed central schemas even though their nine files are content-equal to the central baseline.

HYP-001 remains unresolved: root mismatch is the likely reason a new Orca Workspace sometimes cannot locate nested scripts, but only a fresh disposable Workspace execution can prove the end-to-end fix. The design therefore separates target selection, isolated filesystem verification, and runtime smoke evidence.

## Goals / Non-Goals

Goals:

- provide one cross-platform implementation of version, manifest, install, check, and consumer-resolution behavior;
- preserve the current wrapper entry points while adding a stable Orca/shared target and machine-readable status;
- write receipts only after package-owned files have been processed, detect content drift and removed package-owned files, and preserve files never owned by the package;
- make the general feature-first placement rule visible to direct coding agents, OpenSpec planning/apply agents, and portable policy consumers;
- prove isolated installation before any shared-profile mutation, then prove script discovery in a fresh Orca Workspace, and only then reconcile PayFlow.

Non-goals:

- automatic Git fetch/pull, background updates, package publication, GitHub release creation, or push;
- embedding an Orca account-specific home path or modifying Orca application configuration;
- copying PayFlow-specific namespaces, modules, DI rules, or architecture-test examples into the central package;
- changing PayFlow product code or deleting its temporary schemas before central and consumer checks pass;
- redesigning unrelated skills, schemas, validators, or the OpenSpec 1.8 artifact workflow.

## Decisions

The accepted behavior remains DEC-001 through DEC-005 from `proposal.md`. The following implementation decisions were explicitly approved together by the owner in USER-006.

### DEC-006: One Python distribution engine with compatibility wrappers
**Status:** accepted
**Source:** user:USER-006, user:USER-007

Add `scripts/workflow_package.py` as the cohesive public engine and transaction owner for package metadata, target resolution, install, check, rollback, and consumer schema-resolution checks. Add `scripts/workflow_package_state.py` as its dependency-free internal trust-boundary collaborator for canonical path containment, manifests, receipts, inventory, backup creation, and fail-closed backup validation. Keep `scripts/install.ps1` and `scripts/install.sh` as thin compatibility adapters that map their existing arguments plus new options to the public engine. Python 3.11 is already a documented runtime requirement, so this removes behavioral duplication without adding an external dependency.

The engine exposes explicit `install` and `check` operations, `--target codex|orca|omnigent`, `--agent-root`, `--schema-root`, `--consumer-repo`, `--dry-run`, and `--json`. `check` never mutates. Non-JSON wrappers retain concise human-readable output; JSON output is the agent contract.

### DEC-007: Semantic version in package.json is the single source
**Status:** accepted
**Source:** user:USER-006

Add the package name, `private: true`, and an initial semantic version to the existing root `package.json`; keep `package-lock.json` synchronized. The initial version is `1.0.0` because no prior machine-readable package version exists. Future incompatible distribution contracts increment major, backward-compatible capabilities increment minor, and compatible fixes increment patch. No second `VERSION` file is introduced.

### DEC-008: Per-root receipts own only package-managed paths
**Status:** accepted
**Source:** user:USER-006

Write one `.codex-openspec-workflow.json` receipt in the selected agent root and one in the selected schema root. Each receipt contains a receipt format version, workflow version, root role (`agent-skills` or `openspec-schemas`), and the sorted relative paths plus SHA-256 hashes owned in that root. The requested target alias is informational output only and is not freshness-significant, so `orca` and `omnigent` can safely check the same shared agent root. Receipts do not store a developer machine path, credential, timestamp, or consumer-specific data.

Install computes the new manifest, overlays new package files, removes only paths listed by the previous valid receipt that are no longer in the new manifest, and writes the new receipt last. Files outside the current or previous package-owned manifest are preserved. If copying fails before receipt replacement, the old receipt remains and the next check reports `stale`; rerunning the same or a prior checked-out version repairs the package-owned paths.

Initial adoption from an unversioned installation is a separate fail-closed path. Before mutation, the engine inventories every file below the exact skill and schema subtrees that the new package will own, excluding documented disposable caches. A destination file whose relative path exists in the new manifest is an overwrite candidate and MUST be included in an operation-specific backup. A file inside those exact package subtrees that is absent from the new manifest is reported as an unresolved `legacy-extra`; installation stops before writing files or receipts until the operator moves, removes, or otherwise reconciles it explicitly. Initial adoption requires `--backup-root`, writes a backup manifest containing the pre-install inventory and receipt state, and does not issue a `current` receipt while any legacy extra remains unresolved.

`check` compares canonical version and manifests with the selected roots and returns `missing`, `current`, or `stale`. Missing paths, changed hashes, obsolete previously owned paths, receipt errors, installed/available versions, selected roots, and an explicit update command are included in JSON. When missing state requires initial-adoption backup, remediation selects the first absent operation-specific backup path instead of reusing a retained non-empty backup, so the emitted argv is directly executable. The process exits nonzero for `missing` or `stale` after emitting the status.

### DEC-009: Orca uses the stable shared Agent Skills root
**Status:** accepted
**Source:** user:USER-006

Resolve `--target orca` to the user's standard `~/.agents/skills` directory and the platform's standard OpenSpec user-schema directory. Keep explicit root overrides authoritative. `codex` continues to honor `CODEX_HOME` before `~/.codex/skills`; `omnigent` retains `~/.agents/skills`. Because `orca` and `omnigent` are aliases for the same root, freshness is based on root role, version, and manifest rather than the alias used to invoke the check. The engine reports resolved absolute roots but never bakes the inspected `AppData/Roaming/orca/codex-accounts/...` path into package files or receipts.

Runtime compatibility is a separate gate: after isolated tests and an explicitly authorized shared install, create a disposable fresh Orca Workspace agent, require it to identify the loaded `openspec-workflow` root, and execute that installed root's `scripts/validate_change.py --help`. The smoke records the resolved path and exit result. A missing skill, a path outside the selected shared root, or a failed nested script keeps Orca compatibility unverified.

### DEC-010: Consumer verification is a read-only engine mode
**Status:** accepted
**Source:** user:USER-006

When `--consumer-repo` is supplied to `check`, run OpenSpec schema resolution from that repository for `evidence-core` and `evidence-heavy`, compare the effective source/path with the selected installed schema root, and report project-local or other shadowing. This mode does not edit the consumer. PayFlow cleanup remains a later target-specific consumer operation after isolated package checks, authorized shared installation, runtime smoke, and PayFlow validation all pass.

The general code-placement policy is updated in the central `coding-guardrails`, portable `AGENTS.fragment.md`, `openspec-workflow`, and both schema authoring/apply instructions. Tests assert the required semantic clauses rather than enforcing byte-identical prose. PayFlow retains the concrete Application/OCR and Infrastructure examples. `policy/AGENTS.fragment.md` remains an intentionally manual checkout/consumer asset as documented today: the installer reports its path and required review but does not copy it, include it in agent/schema receipts, or edit an existing `AGENTS.md`.

## Component Ownership

**Architecture impact:** material

**Inspected baseline:** `scripts/install.ps1` 106 lines; `scripts/install.sh` 37 lines; `scripts/validate.ps1` 64 lines; `skills/coding-guardrails/SKILL.md` 109 lines; `skills/openspec-workflow/SKILL.md` 117 lines; `policy/AGENTS.fragment.md` 26 lines; `openspec/schemas/evidence-core/schema.yaml` 102 lines; `openspec/schemas/evidence-heavy/schema.yaml` 133 lines; `package.json` 5 lines. No existing file exceeds 1000 lines; the material trigger is multiple independently testable responsibilities.

**Expected growth:** measured Wave 1 growth is `scripts/workflow_package.py` approximately 338 lines, the cohesive internal `scripts/workflow_package_state.py` trust-boundary collaborator approximately 265 lines, and focused Python tests approximately 330 lines after negative-path remediation. Compatibility wrappers remain below their former sizes after delegation; `scripts/validate.ps1` grows by approximately 16 lines; package metadata, README, policy, skill, and schema guidance each receive bounded additions. No existing production file receives 250 new lines; new distribution responsibilities are split across the public transaction engine and one state-validation collaborator.

**Existing responsibilities:** PowerShell and POSIX installers independently resolve targets and copy skills/schemas; PowerShell additionally performs dry-run/content checking. `validate.ps1` orchestrates repository validation. Skills, portable policy, and schema instructions independently describe their current workflow gates.

**New responsibilities:** the public engine owns canonical version parsing, target resolution, install/check/rollback orchestration, cross-platform missing/current/stale aggregation, explicit Orca selection, optional read-only consumer shadowing checks, and machine-readable update guidance. The internal state collaborator owns canonical contained paths, receipt and owned-file manifest serialization, unversioned inventory/backup validation, and pre-mutation restoration evidence. General feature-first placement guidance remains distributed across direct/OpenSpec entry points.

**Transaction owner:** `workflow_package.py` owns each filesystem install/rollback operation and writes each root receipt last; it coordinates but does not duplicate the pure state validations in `workflow_package_state.py`. The state collaborator exposes no separate CLI and initiates no operation. Wrappers own no package state. `check` and consumer verification are read-only. The Orca CLI owns creation/removal of the disposable Workspace; no package script mutates Orca configuration.

**Boundary options:** (1) duplicate version/receipt/discovery logic in the two existing installers; (2) put all new logic in the PowerShell installer and leave POSIX behavior weaker; (3) extract one dependency-free Python distribution engine with a cohesive internal state-validation collaborator and retain thin platform wrappers. Option 3 is selected because Python is already required, it preserves one public transaction owner, isolates the destructive trust boundary, and prevents cross-platform receipt/status drift.

**Decision:** extract-collaborators

**Known cost:** the public engine plus one internal state module create more total production code than the original single-file estimate, but keep both components below the architecture hotspot threshold and separate orchestration from destructive-state validation. The internal CLI, initial-adoption backup manifest, and receipt format require negative-path tests and documented compatibility; receipt-last installation is detectable and repairable but not a fully atomic multi-root transaction; unresolved legacy extras deliberately require operator reconciliation; a real Orca smoke cannot be replaced by unit tests and requires explicit authority to create and remove a disposable Workspace.

**Ratchet scope:** change only distribution/version/install/check/consumer-verification behavior and the accepted shared placement guidance. Do not refactor unrelated validators or skills, change schema artifact order, introduce a general plugin framework, reorganize PayFlow production code, or automate Git/network effects.

## Risks / Mitigations

- **A receipt is present but installed files drift.** Compare hashes against the inspected canonical package on every check; version equality alone never yields `current`.
- **An interrupted update leaves mixed package files.** Write receipts last and treat any manifest mismatch as `stale`; rerun the selected version. Do not claim atomicity across agent and schema roots.
- **A previous package file is removed centrally.** Delete it only when the previous valid receipt identified it as package-owned; never sweep unknown files or entire destination roots.
- **The first versioned install overlays an unversioned package.** Require pre-mutation inventory and `--backup-root`; back up every overwrite candidate, stop on legacy extras, and write no receipt until adoption is clean.
- **Orca still loads an account-scoped copy before the shared root.** Record the actual skill path from a fresh Workspace and fail the runtime smoke if it is not the selected installed root.
- **Project-local schemas hide the central install.** Consumer check inspects effective schema precedence and blocks a centrally-current claim until shadowing is reconciled.
- **Central policy becomes PayFlow-specific.** Tests and review keep concrete project names out of shared guidance; PayFlow retains its detailed examples locally.
- **Version changes without synchronized lock metadata.** Repository validation compares root `package.json` and lockfile version/name and fails on mismatch.

## Migration And Rollback

1. Implement and unit-test the Python engine, receipts, target resolution, wrapper compatibility, and policy assertions using only isolated temporary roots.
2. Run central repository validation, isolated install, isolated `current` check, deliberate version/content/missing drift checks, and reinstall repair. No shared profile is changed in this phase.
3. At the last safe point, present resolved shared targets, unversioned/installed state, complete initial-adoption inventory, legacy-extra conflicts, backup scope, dry-run output, and rollback command; require explicit owner `GO` before installing into `~/.agents/skills` or the real OpenSpec schema root.
4. For the first versioned install, require zero unresolved legacy extras and back up every existing file in the exact destination skill/schema subtrees that will be overwritten, plus any prior receipt state, into an operation-specific backup root with its own manifest. Record the canonical resolved destination for each root role and require an exact match before any rollback mutation, so a valid backup cannot be applied to mistyped or different roots. Install the central version, write receipts last, and require `current` from the same checkout. Later versioned updates may back up only paths owned by the valid previous receipt.
5. Create a disposable fresh Orca Workspace, execute the installed nested validator from the resolved shared skill root, record evidence, and remove only that disposable Workspace after the result is captured.
6. Run read-only PayFlow consumer verification. Only after it reports the intended central installation and the PayFlow validators pass may a separate PayFlow consumer reconciliation remove temporary reusable copies and correct ownership wording.

Rollback of initial adoption first verifies that every caller-selected root exactly matches the canonical destination bound into the backup manifest. It then removes the validated planned manifest paths plus any valid current-receipt paths that were absent from the backed-up pre-install inventory, removes temporary receipt state, restores every backed-up pre-install file and prior receipt state, and verifies the restored inventory without claiming a versioned `current` state. A root mismatch fails before any mutation. This remains correct when interruption occurs before either root receipt is written. Rollback of a later versioned update may instead reinstall a checkout of the previously recorded workflow version and run `check`. If runtime smoke or PayFlow validation fails before consumer reconciliation, retain PayFlow's local schemas. No Git push, tag, release, consumer cleanup, or shared install is bundled into planning approval.

## Open Questions

None. DEC-006 through DEC-010 are accepted under user:USER-006.
