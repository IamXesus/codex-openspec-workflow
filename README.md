# Portable OpenSpec Workflow for Codex, Orca, and Omnigent

This repository is the canonical upstream for the reusable OpenSpec workflow shared across projects and agent harnesses. It owns the schemas and templates, validators, skills, routing and lifecycle gates, general authoring policy, version metadata, and distribution tooling. OpenSpec remains the artifact engine; the bundled policy preserves unknowns, enforces approval boundaries, and verifies planning structure before implementation.

Consumer repositories inherit the reusable package, but remain authoritative for their own OpenSpec context, business and technical documentation, repository navigation, deployment conventions, and domain-specific code-placement examples. A project-local schema intentionally shadows the shared schema; it is consumer-owned state to reconcile explicitly, never a reverse source of truth for this repository.

## Contents

- `skills/` — canonical Agent Skills shared by Codex, Orca, and Omnigent.
- `openspec/schemas/` — `evidence-core` and `evidence-heavy` custom schemas.
- `policy/AGENTS.fragment.md` — portable workflow policy to merge into a user or project `AGENTS.md`.
- `evals/promptfoo/` — isolated regression corpus for the workflow itself.
- `scripts/workflow_package.py` — dependency-free install/check/rollback engine; the PowerShell and POSIX installers are thin adapters.

## Runtime requirements

- Python 3.11 or newer.
- OpenSpec CLI 1.8.x available as `openspec` or `openspec.cmd`.
- Codex, Orca, Omnigent, or another host that supports the Agent Skills specification.

## Version and update contract

`package.json` is the single version source. The current package is `1.0.1`; `package-lock.json` must match it. Shared-root receipts record that SemVer and hashes for every package-owned skill and schema file. When a consumer is selected, the managed `AGENTS.md` block carries its own per-consumer policy receipt with the workflow version and normalized policy hash. `check` reports:

- `current` when both shared roots and the selected consumer policy have the expected version, receipt, owned paths, and hashes;
- `stale` for safe-to-update version/content/missing-owned-path/obsolete-path drift under a valid receipt, or consumer schema shadowing;
- `missing` when a shared root has no valid receipt or a selected consumer has no managed policy block;
- `conflict` when selected consumer policy markers are malformed or the managed body was edited after installation.

The package never pulls Git. Update the central checkout by your normal Git workflow, run `check`, and execute its same-target `update_command`/`update_argv`. Missing and stale remediation retains the selected consumer path; conflicts require manual reconciliation and never advertise an overwriting update. A version bump tells agents that a release changed; hashes still detect an unpublished local-content drift at the same version.

## Install on Windows

Preview the first Orca installation. Initial adoption requires a dedicated empty backup root, even in dry-run examples so the exact command can be promoted safely:

```powershell
.\scripts\install.ps1 -Target orca -ConsumerRepo C:\projects\consumer -BackupRoot C:\workflow-backups\openspec-1.0.1 -DryRun -Json
```

Install after the preview and the required owner approval for the persistent shared-profile write:

```powershell
.\scripts\install.ps1 -Target orca -ConsumerRepo C:\projects\consumer -BackupRoot C:\workflow-backups\openspec-1.0.1
```

Check the installed package and resolve effective schemas in a consumer without editing it:

```powershell
.\scripts\install.ps1 -Target orca -Check -ConsumerRepo C:\projects\consumer -Json
```

For Codex or Omnigent, replace `orca` with `codex` or `omnigent`. Codex honors `CODEX_HOME`; Orca and Omnigent default to the stable `~/.agents/skills` root. `-AgentRoot` and `-SchemaRoot` take precedence over defaults. Keep the backup root outside both managed roots.

## Install on POSIX

```sh
./scripts/install.sh install --target orca --consumer-repo /path/to/consumer --backup-root "$HOME/workflow-backups/openspec-1.0.1" --dry-run --json
./scripts/install.sh install --target orca --consumer-repo /path/to/consumer --backup-root "$HOME/workflow-backups/openspec-1.0.1"
./scripts/install.sh check --target orca --consumer-repo /path/to/consumer --json
```

The installer recursively copies package-owned skills and schemas, preserves unrelated files, excludes Python caches, and writes the receipt last. Initial adoption fails closed without an empty backup root and also blocks on legacy files inside package-owned subtrees that are not in the new manifest. Later receipt-owned upgrades normally do not need another adoption backup. To restore an initial-adoption backup:

```powershell
python .\scripts\workflow_package.py rollback --target orca --backup-root C:\workflow-backups\openspec-1.0.0
```

`--json` exposes the selected target, package version, root status/issues, consumer policy state, remediation argv, and optional schema resolution. For `check`, `--consumer-repo` is read only: it reports the effective `evidence-core`/`evidence-heavy` source, project-local shadowing, and managed policy state. For `install`, the same explicit option creates a missing root `AGENTS.md`, adopts an exact unmarked copy of the portable policy, appends one managed block after unrelated instructions, or replaces only an intact stale managed block. It never reconciles or deletes consumer schemas.

`policy/AGENTS.fragment.md` remains outside the two shared-root receipts because one shared profile can serve many repositories. Its marked consumer copy has a per consumer policy receipt in the begin marker. Text outside the begin/end markers remains repository-owned and is preserved. A locally edited, duplicated, partial, invalid, or symlinked managed block is `conflict` and blocks install before shared-root mutation. Without `--consumer-repo`, installation retains its shared-only behavior and does not select an `AGENTS.md`.

Consumer policy writes use a sibling temporary file and replace the target only after shared assets succeed. The existing `rollback` command restores only shared skill/schema roots; it does not restore consumer policy. To undo an intact policy adoption manually, remove the created `AGENTS.md` only when it contains no consumer text, or remove exactly the marked block while preserving surrounding instructions. Installation does not install npm packages, pull Git, create an Orca Workspace, or publish a release.

The package includes `architecture-review`, a reusable read-only reviewer plus a fail-closed OpenSpec architecture-contract validator. New proposals classify architecture impact; material changes use `evidence-heavy`, record component ownership in design, and complete an independent architecture checkpoint before production edits. Existing large services remain out of scope unless the accepted change touches their responsibilities.

## Validate

```powershell
.\scripts\validate.ps1
```

Promptfoo is optional and tests changes to the workflow itself, not normal application delivery:

```powershell
npm ci
npx --no-install promptfoo validate -c .\evals\promptfoo\promptfooconfig.yaml
.\evals\promptfoo\run.ps1
```

## Portability boundary

The package uses the shared Agent Skills layout for Orca and Omnigent, but a new Workspace discovery smoke remains a separate runtime proof. Neither host interprets OpenSpec artifacts itself: the OpenSpec CLI and custom schemas remain a separately installed layer. Validate the selected harness before relying on it for write-capable evaluations.

