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

`package.json` is the single version source. The current package is `1.0.0`; `package-lock.json` must match it. Installed receipts record that SemVer and hashes for every package-owned file. `check` reports:

- `current` when both roots have the expected version, receipt, owned paths, and hashes;
- `stale` for version/content/missing-owned-path/obsolete-path drift under a valid receipt, or consumer schema shadowing;
- `missing` when a root has no valid receipt.

The package never pulls Git or edits a consumer project. Update the central checkout by your normal Git workflow, run `check`, and execute its same-target `update_command`/`update_argv`. A version bump tells agents that a release changed; hashes still detect an unpublished local-content drift at the same version.

## Install on Windows

Preview the first Orca installation. Initial adoption requires a dedicated empty backup root, even in dry-run examples so the exact command can be promoted safely:

```powershell
.\scripts\install.ps1 -Target orca -BackupRoot C:\workflow-backups\openspec-1.0.0 -DryRun -Json
```

Install after the preview and the required owner approval for the persistent shared-profile write:

```powershell
.\scripts\install.ps1 -Target orca -BackupRoot C:\workflow-backups\openspec-1.0.0
```

Check the installed package and resolve effective schemas in a consumer without editing it:

```powershell
.\scripts\install.ps1 -Target orca -Check -ConsumerRepo C:\projects\consumer -Json
```

For Codex or Omnigent, replace `orca` with `codex` or `omnigent`. Codex honors `CODEX_HOME`; Orca and Omnigent default to the stable `~/.agents/skills` root. `-AgentRoot` and `-SchemaRoot` take precedence over defaults. Keep the backup root outside both managed roots.

## Install on POSIX

```sh
./scripts/install.sh install --target orca --backup-root "$HOME/workflow-backups/openspec-1.0.0" --dry-run --json
./scripts/install.sh install --target orca --backup-root "$HOME/workflow-backups/openspec-1.0.0"
./scripts/install.sh check --target orca --consumer-repo /path/to/consumer --json
```

The installer recursively copies package-owned skills and schemas, preserves unrelated files, excludes Python caches, and writes the receipt last. Initial adoption fails closed without an empty backup root and also blocks on legacy files inside package-owned subtrees that are not in the new manifest. Later receipt-owned upgrades normally do not need another adoption backup. To restore an initial-adoption backup:

```powershell
python .\scripts\workflow_package.py rollback --target orca --backup-root C:\workflow-backups\openspec-1.0.0
```

`--json` exposes the selected target, package version, root status/issues, policy hash, remediation argv, and optional consumer resolution. `--consumer-repo` is read-only and reports the effective `evidence-core`/`evidence-heavy` source and project-local shadowing; it never reconciles or deletes consumer schemas.

`policy/AGENTS.fragment.md` is deliberately outside installation receipts. The engine reports its path and hash with `manual_review_required`; merge it into global or project instructions only after review. The installer does not create symlinks, edit `AGENTS.md`, install npm packages, modify consumer repositories, pull Git, create an Orca Workspace, or publish a release.

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

