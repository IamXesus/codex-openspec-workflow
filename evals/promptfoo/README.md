# Workflow eval pilot

This corpus checks routing and authority regressions after changing `AGENTS.md`, skills, schemas, the Codex model, or reasoning configuration. It is deliberately separate from application OpenSpec changes.

Run configuration validation before spending model calls:

```powershell
npm ci
npx --no-install promptfoo validate -c .\evals\promptfoo\promptfooconfig.yaml
```

Then run three independent trials without cache. The wrapper resolves codex.cmd on Windows and passes its path explicitly to Promptfoo:

```powershell
.\evals\promptfoo\run.ps1
```

The pilot runs a separate ephemeral Codex app-server in read-only mode with approvals declined. It does not attach to an existing Desktop session. Deterministic assertions are intentionally narrow; review failures and variance before changing the workflow. Do not let an LLM grader create accepted requirements or ground truth.

