## Why

The reusable OpenSpec process must have one canonical owner instead of being copied into PayFlow or reconstructed per agent environment. The existing central repository already packages the schemas, skills, policy, and installers, but it does not yet provide a versioned consumer contract, reliable Orca workspace discovery, or the feature-first code-authoring policy proven in PayFlow. Without those contracts, projects can silently shadow central updates, installed validators can drift, and a newly created Orca Workspace can fail to locate the scripts required by strict planning and architecture gates.

## Evidence

- USER-001: The owner explicitly requires the complete reusable custom OpenSpec process to be owned by the central repository and inherited by PayFlow and future projects, not copied back from each consumer project.
- USER-002: The owner explicitly requires the feature-first code-style established in PayFlow to remain part of the central OpenSpec process so ordinary coding agents, not only architecture reviewers, apply it.
- USER-003: The owner reports that agents created in a new Orca Workspace do not always have access to the required scripts or cannot resolve their path, and explicitly requires this to be fixed.
- USER-004: The owner explicitly requires central workflow versioning so agents can recognize that the workflow changed and install the new version.
- USER-005: After the central ownership, installer, Orca discovery, and code-style scope was restated, the owner explicitly authorized continuing this change; the owner then separately added the versioning requirement recorded as USER-004.
- USER-006: The owner explicitly approved DEC-006 through DEC-010 as displayed in the design decision checkpoint.
- USER-007: During implementation, the owner explicitly approved reconciling DEC-006 and Component Ownership to retain `workflow_package.py` as the public transaction owner and add `workflow_package_state.py` as the internal trust-boundary collaborator for paths, manifests, receipts, and backup validation.
- FACT-001: The canonical repository is `C:\projects\codex-openspec-workflow`, its configured remote is `https://github.com/IamXesus/codex-openspec-workflow.git`, and the inspected clean baseline is `main` at `d4851fb686e99f10d2ae8f830877e3dbb78e4104`, equal to the locally recorded `origin/main`.
- FACT-002: The repository already contains `evidence-core`, `evidence-heavy`, `openspec-workflow`, `architecture-review`, `coding-guardrails`, a portable policy fragment, and Windows/POSIX installers.
- FACT-003: All nine PayFlow project-local schema/template files are content-equal to the central schema sources after line-ending normalization, so the central repository already contains the intended schema baseline.
- FACT-004: OpenSpec schema precedence selects project-local schemas before user-installed schemas. Keeping consumer-owned copies would therefore shadow later central installations.
- FACT-005: The Windows installer currently selects the Codex skill target from `CODEX_HOME` or `~\.codex\skills`, while the inspected Orca session loads the active workflow from an account-scoped `AppData\Roaming\orca\codex-accounts\...\home\skills` path and also exposes skills from the stable `~\.agents\skills` root.
- FACT-006: The installed `architecture-review` validator differs from the clean central source: the installed copy omits the central concrete checkpoint-field validation and its installed skill folder lacks the central validator test file.
- FACT-007: PayFlow currently contains the accepted feature-first placement rules and repository-grounded examples, while the central `coding-guardrails` and portable policy do not yet contain that general placement contract.
- OBS-001: The existing installer already provides the correct ownership direction—central package to installed environment—but has no machine-readable package/receipt version contract and no explicit Orca/shared target.
- HYP-001: The reported new-Workspace failure is caused by a workspace/account-specific skill root differing from the installer-selected root. This is not yet proven and requires a disposable fresh-Workspace smoke before the implementation can claim the defect fixed.

## What Changes

- Make `codex-openspec-workflow` the documented canonical source for reusable schemas, templates, validators, skills, routing, lifecycle gates, and general code-authoring policy.
- Add one machine-readable workflow version and an installed receipt/check contract so an agent can distinguish missing, current, and stale installations and can report the exact explicit update command instead of silently assuming freshness.
- Extend the installer with an explicit, stable Orca/shared installation path plus caller overrides, without embedding a current account-specific absolute path.
- Make installation and checking fail closed when a package-owned skill, nested validator script, schema, or version receipt is absent, stale, or different from the canonical package.
- Add an isolated install/check test and a disposable fresh Orca Workspace smoke that prove the workflow skill can resolve and execute its nested scripts from a newly created workspace.
- Move the general feature-first/cohesive-responsibility placement rule into the central coding guardrail, portable policy, and OpenSpec authoring/apply guidance while keeping PayFlow namespace, folder, DI, and architecture-test examples project-local.
- Document the consumer contract: projects keep project context, business/technical documentation, and domain-specific placement examples; they do not become canonical owners of reusable workflow files.
- Use PayFlow as the first compatibility consumer after the central package passes isolated validation. Removing its temporary project-local schema copies and reconciling its project wording is a consumer migration, not a second implementation of the workflow.

## Capabilities

### New Capabilities

- `versioned-workflow-distribution`: The central package exposes a canonical version plus verifiable installed state and an explicit update path.
- `portable-agent-installation`: Installation and validation cover Codex, shared/Orca agent roots, OpenSpec schemas, nested scripts, and fresh-workspace discovery without account-specific hard-coding.
- `shared-code-authoring-policy`: The reusable process guides file placement by feature and cohesive responsibility for direct and OpenSpec-routed coding work.
- `consumer-workflow-inheritance`: Consumer projects inherit reusable workflow behavior while retaining only project-specific context and architectural examples.

### Modified Capabilities

None. The central repository has no existing normative current specs; the new specs will establish its distribution contract from the confirmed package baseline.

## Impact

- Expected central surfaces: package metadata, `scripts/install.ps1`, `scripts/install.sh`, validation/tests, `README.md`, `policy/AGENTS.fragment.md`, `skills/coding-guardrails/`, `skills/openspec-workflow/`, and the two schema bundles where authoring/apply guidance must carry the shared placement and version checks.
- Consumer verification surfaces: isolated temporary install roots, the stable shared Orca-visible skill root selected by the accepted installer contract, and a disposable Orca Workspace smoke. A real shared-profile installation remains a persistent effect and requires a separate last-safe-point `GO` after dry-run and isolated checks.
- The central change may inspect PayFlow as a compatibility consumer but does not duplicate the workflow there. Any PayFlow cleanup is reconciled only after the central package installs and checks successfully.
- No PayFlow product behavior, API, persistent data, finance/1C operation, production deployment, automatic Git pull, automatic package update, or GitHub push is authorized by this proposal.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** material

The change adds multiple independently testable responsibilities across package version state, installation/discovery, workflow validation, Orca workspace compatibility, and cross-cutting authoring policy. It therefore uses `evidence-heavy`; this classification does not authorize unrelated refactoring of the existing skills or installers.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: The central repository owns reusable workflow behavior
**Status:** accepted
**Source:** user:USER-001

`codex-openspec-workflow` is the canonical source for reusable schemas, templates, validators, skills, routing, lifecycle gates, and general authoring policy. Consumer projects inherit that package and must not become the upstream source for the same reusable files.

### DEC-002: Installed workflow state is explicitly versioned
**Status:** accepted
**Source:** user:USER-004

The central package exposes one machine-readable workflow version. Installation records enough machine-readable state for an agent to report whether its workflow is missing, current, or stale and to run an explicit update flow. A stale installation must not be presented as current.

### DEC-003: Fresh Orca workspaces resolve the centrally installed workflow
**Status:** accepted
**Source:** user:USER-003

Newly created Orca Workspace agents must resolve the centrally installed workflow and execute its required nested scripts. The implementation must not encode the currently observed account-scoped absolute path as the compatibility mechanism, and it must verify nested script execution in a fresh workspace before claiming success; exact target precedence is derived from inspected runtime behavior in design.

### DEC-004: General code placement is feature-first and centrally enforced
**Status:** accepted
**Source:** user:USER-002

Reusable guidance requires agents to inspect neighboring structure and organize new or materially changed code by feature and cohesive responsibility rather than generic declaration-type folders. Generic `Interfaces/` and `Implementations/` buckets, speculative one-file layers, and incidental legacy reorganization remain disallowed. Project-specific namespace, folder, DI, and architecture-test examples stay in the consumer repository.

### DEC-005: PayFlow is the first consumer proof, not a second workflow owner
**Status:** accepted
**Source:** user:USER-001, user:USER-005

The central implementation is validated in isolation first and then against PayFlow as the first consumer. Consumer-local reusable copies are removed or reconciled only after the central install/check path passes, while PayFlow-specific context and architecture documentation remain local.

## Open Questions

None. The exact version-file shape, receipt contents, target-resolution precedence, and disposable Orca smoke mechanics are implementation decisions to derive from the inspected package and runtime contracts in design; they must preserve the accepted behavior above.
