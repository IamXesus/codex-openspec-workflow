## Why

The canonical workflow advertises Linux/POSIX support and already ships a POSIX installer, but its portable `openspec-workflow` skill unconditionally instructs agents to invoke `openspec.cmd`. That executable name is Windows-specific, so an otherwise valid Linux installation fails before OpenSpec can execute. The package needs one narrow platform-resolution contract without taking ownership of OpenSpec CLI installation.

## Evidence

- USER-001: The owner requires the canonical package to work on Linux while preserving Windows compatibility, with `openspec` on POSIX and `openspec.cmd` or shell-resolved `openspec` on Windows.
- USER-002: The owner requires all portable new/status/instructions/init/apply/check commands to use one consistent platform mechanism and forbids a shell-specific environment-variable workaround.
- USER-003: The owner requires a regression that is isolated from developer-installed `openspec.cmd`, plus POSIX dry-run/install/check/rollback coverage for `codex` and `omnigent` in temporary roots only.
- USER-004: The owner requires OpenSpec CLI 1.8.x to remain a separate dependency and forbids implicit CLI installation, new shared frameworks/scripts, real profile/host mutation, push, tag, and release.
- USER-005: The owner requires package/version metadata to remain consistent and indicates this compatibility fix should use a patch release after checking repository rules.
- FACT-001: The inspected clean baseline is `main` at `d112d3b2632bbc8239f0bb42fa6dbd0107a6355c`, equal to `origin/main`, with package version `1.1.0`.
- FACT-002: `skills/openspec-workflow/SKILL.md` contains unconditional `openspec.cmd` commands, while `scripts/workflow_package.py` already selects `openspec.cmd` on Windows and `openspec` on POSIX.
- FACT-003: `scripts/install.sh` already delegates to the dependency-free Python package engine; WSL2 Ubuntu is available for isolated POSIX verification.
- OBS-001: The repository has no more specific patch/minor classification rule beyond valid SemVer and synchronized package/lock metadata. A bug-compatible patch increment to `1.1.1` is the smallest interpretation of USER-005.

## What Changes

- Replace unconditional Windows executable names in the portable workflow skill with one explicit platform-selection contract used consistently by every documented OpenSpec command.
- Keep POSIX on `openspec`; allow Windows shells to use `openspec.cmd` or correctly resolve `openspec` through PATHEXT.
- Add focused resolver/content regressions that use isolated executable discovery rather than the developer machine's installed CLI.
- Exercise the existing POSIX installer lifecycle for `codex` and `omnigent` with temporary HOME, agent, schema, backup, and consumer roots.
- Clarify the executable/dependency boundary in README and increment synchronized package metadata from `1.1.0` to `1.1.1`.

## Capabilities

### New Capabilities

- `portable-openspec-executable`: Platform-correct OpenSpec executable resolution and isolated Linux/Windows compatibility evidence for the portable workflow package.

### Modified Capabilities

None. The repository has no archived normative current specs for this contract.

## Impact

- Expected edits are limited to the portable workflow skill, existing package resolver/tests, README, version metadata, validation wiring if required, and this OpenSpec change.
- No installer refactor, dependency, generic bootstrap layer, runtime-state copy, product/consumer change, real profile write, test-host installation, server access, Git publication, or release publication is authorized.

<!-- openspec-architecture-contract:v1 -->
## Architecture Impact

**Architecture impact:** none

The change corrects one existing executable-selection contract and adds focused tests. It does not add a production responsibility, transaction boundary, new framework, or approximately 250 production lines in one file.

## UI Contract

**Mode:** none

## Decisions

### DEC-001: Portable instructions select the executable by platform
**Status:** accepted
**Source:** user:USER-001, user:USER-002

POSIX instructions invoke `openspec`; Windows instructions invoke `openspec.cmd` or `openspec` only when the active Windows shell correctly resolves PATHEXT. Every portable workflow command follows that same branch without a cross-shell environment-variable convention.

### DEC-002: OpenSpec CLI remains an external prerequisite
**Status:** accepted
**Source:** user:USER-004

The package validates and uses OpenSpec CLI 1.8.x but never installs npm packages or the CLI implicitly.

### DEC-003: Compatibility fix uses package version 1.1.1
**Status:** accepted
**Source:** user:USER-005

The repository has no conflicting release-number rule, so the Linux compatibility correction increments the synchronized SemVer patch component from `1.1.0` to `1.1.1`. No tag or release is created.

## Open Questions

None.
