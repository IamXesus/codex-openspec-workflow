# Portable OpenSpec Workflow for Codex and Omnigent

This repository packages one evidence-bound OpenSpec workflow for reuse across machines and agent harnesses. OpenSpec remains the artifact engine; the bundled skills route tasks, preserve unknowns, enforce approval boundaries, and verify planning structure before implementation.

## Contents

- `skills/` — canonical Agent Skills shared by Codex and Omnigent.
- `openspec/schemas/` — `evidence-core` and `evidence-heavy` custom schemas.
- `policy/AGENTS.fragment.md` — portable workflow policy to merge into a user or project `AGENTS.md`.
- `evals/promptfoo/` — isolated regression corpus for the workflow itself.
- `scripts/install.ps1` — Windows dry-run/check/install adapter; `scripts/install.sh` — POSIX install adapter.

## Runtime requirements

- Python 3.11 or newer.
- OpenSpec CLI 1.8.x available as `openspec` or `openspec.cmd`.
- Codex, Omnigent, or another host that supports the Agent Skills specification.

## Install on Windows

Preview first:

```powershell
.\scripts\install.ps1 -Target codex -DryRun
```

Install for Codex:

```powershell
.\scripts\install.ps1 -Target codex
```

Install for Omnigent's shared Agent Skills directory:

```powershell
.\scripts\install.ps1 -Target omnigent
```

The installer overlays package-owned files without deleting unknown destination files and excludes Python caches. Use `-Check` to detect stale files left by an older package. It does not create symlinks, edit an existing `AGENTS.md`, install npm packages, or modify project repositories. Apply `policy/AGENTS.fragment.md` intentionally after reviewing it. Codex installs honor `CODEX_HOME`; pass `-AgentRoot` to target another host-specific skill directory.

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

The package uses the standard Agent Skills layout expected by Omnigent, but this repository has not yet been smoke-tested in a live Omnigent runtime. Omnigent does not interpret OpenSpec artifacts itself: the OpenSpec CLI and custom schemas remain a separate installed layer. Native Windows Omnigent has weaker harness isolation than its Linux/WSL path; validate the selected harness before relying on it for write-capable evaluations.

