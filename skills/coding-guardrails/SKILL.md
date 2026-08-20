---
name: coding-guardrails
description: "Use for non-trivial code implementation, refactoring, debugging fixes, review follow-up, generated-code cleanup, or repository changes where Codex must avoid overengineering, prefer existing solutions, keep diffs surgical, and verify behavior without expanding scope."
---

# Coding Guardrails

Keeps code changes small, existing-first, working, and reviewable. This is a cross-cutting guardrail; combine it with the domain skill for the stack or task.

## Response Language

Answer in the user's language. For Russian requests, report assumptions, changed behavior, verification, and remaining risks in Russian.

## Workflow

1. Define the requested outcome, externally visible behavior, constraints, and success criteria.
2. If an OpenSpec change or another accepted spec exists, read it before editing and keep the diff inside accepted requirements and recorded scope.
3. Inspect the existing project before designing new structure: entry points, local helpers, patterns, tests, package conventions, and recent related code.
4. Prefer existing solutions in this order: local project pattern, local helper/API, official SDK/framework feature, mature OSS/library, then custom code.
5. Choose the smallest vertical slice that satisfies the request. Do not add features, configurability, abstractions, background jobs, services, or dependencies for imagined future cases.
6. Make a surgical diff. Every changed line must support the request, the fix, required wiring, or verification.
7. Verify with the narrowest meaningful check first, then a broader check when a shared contract or user-facing path changed.
8. For OpenSpec work, map verification to its scenarios and report passed, failed, deferred, and not-run facts without inventing a separate evidence document.
9. State what was verified and what remains unverified.

## Code Placement Gate

Before creating or materially moving a production type, inspect the neighboring feature structure, namespaces or module boundaries, dependency registration, and relevant architecture tests. Organize new or materially changed code by feature and cohesive responsibility, following the repository's actual local pattern.

- Keep a small cohesive feature root flat when that remains easiest to navigate.
- Add a subfolder only when it names a real responsibility or boundary, such as commands, models, adapters, storage, or processing, and materially improves navigation.
- Do not introduce generic `Interfaces` and `Implementations` folders solely to separate declaration types; keep an internal contract with the cohesive boundary it serves.
- Apply this as a narrow ratchet. Do not move neighboring legacy files, churn namespaces or registrations, or add speculative wrappers incidentally while satisfying the placement rule.
- Route a material ownership restructure through an accepted `evidence-heavy` change and architecture review.

Consumer repositories remain authoritative for their concrete feature names, namespaces, dependency-registration rules, and architecture-test examples. Combine those local rules with this general guardrail; do not promote project-specific examples into the reusable package.

## Existing-First Gate

Before building custom code, check:

- Is there an existing module, helper, service, component, command, or script that already solves most of this?
- Does the framework or official SDK provide the feature directly?
- Is there a mature OSS option with acceptable license and integration cost?
- Would adapting an existing pattern be simpler than introducing a new abstraction?

Build custom only when existing options are missing, too risky, too heavy, incompatible with the project, or more expensive to adapt than to implement narrowly.

## Dependency Gate

Add a dependency only when it lowers correctness or maintenance risk compared with existing project/framework capability. Check license, maintenance, package footprint, integration cost, and whether it handles the hard parts better than local code. For format/export/parsing work, prefer a proven library over ad hoc escaping when the project has no existing safe helper.

## Simplicity Gate

Default to the simplest correct implementation:

- No speculative abstractions for a single use case.
- No generic plugin/config/rules engine unless the user asked or the codebase already uses one.
- No extra feature flags, settings, background processing, caching, retries, queues, or data models without a current requirement.
- No broad cleanup while fixing a bug or adding a feature.
- No defensive code for impossible states unless the boundary is external, security-sensitive, or observed in tests/logs.

Production basics are not optional: validation at trust boundaries, authorization, data safety, error handling for reachable failure modes, migrations, and user-visible UI states still count as part of correctness.

## Surgical Diff Gate

Before editing, identify the owned files and the reason each file must change. During review, remove or explain changes that are:

- unrelated to the user request;
- style-only churn in untouched code;
- drive-by refactors;
- new abstractions not exercised by the current behavior;
- dependency additions without clear payoff.

If a larger refactor is necessary, separate it from behavior changes or explain why the split is unsafe.

## Subagent Gate

Use subagents only when they materially improve throughput or evidence quality and their work can run independently. Non-trivial size alone is not a trigger.

Good uses:

- unfamiliar repository exploration;
- independent code-path investigation;
- reproduction while the main agent inspects implementation;
- log/config/CI analysis;
- read-only code review after implementation;
- verification of a specific risk;
- disjoint implementation slices with clear file ownership.

Avoid subagents for:

- small one-file edits;
- urgent blocking work that the main agent must solve next;
- tightly coupled implementation where file ownership overlaps;
- tasks where explaining the context costs more than doing the work;
- speculative parallelism without a concrete output.

When using subagents, give each one a bounded task, explicit read/write limits, and expected report format. The main agent owns final root cause, fix strategy, integration, and final communication.

## Review Before Finish

Before final response, check:

- The implementation matches the requested behavior, not an expanded version of it.
- Existing conventions were followed unless a deviation was explained.
- Custom code was justified against existing/local/OSS options when relevant.
- Tests or manual checks prove the main behavior and likely regression path.
- Subagents were used when useful, or skipped for a concrete reason.

## Red Flags

- New framework, service, queue, ORM pattern, state container, or abstraction for one narrow change.
- A large diff where most lines are unrelated to the user-visible behavior.
- "Flexible" code with no current second use case.
- A fix that only makes tests green by weakening tests or contracts.
- Subagent output accepted without main-agent validation.

## Output

For implementation, report: changed behavior, key files, verification run, subagents used or skipped when relevant, and residual risks. For API, CLI, data-format, or integration changes, also name the changed contract and any known limits or assumptions. Keep the answer concise.
