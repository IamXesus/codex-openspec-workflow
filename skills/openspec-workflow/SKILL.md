---
name: openspec-workflow
description: "Use for software-change planning requests such as 'сделай план', 'заведи план', 'спланируй изменение', OpenSpec, SDD, specification, design-spec, or acceptance criteria, and for broad or high-risk implementation that needs a durable behavior contract. Route ordinary small implementation away from specs; use evidence-core for localized plans and evidence-heavy for cross-component, public-contract, persistent-data, auth/security, financial, production, or external-system work."
---

# OpenSpec Workflow

Use the official OpenSpec CLI, schemas, and generated workflows as the only artifact engine. This skill only routes natural language, selects the existing schema, and enforces evidence before tasks or apply.

## Select The OpenSpec Executable

Before invoking OpenSpec, select one executable for the current platform and use it for every `new`, `status`, `instructions`, `init`, apply-phase, and check-phase invocation:

- On POSIX/Linux use `openspec`.
- On Windows use `openspec.cmd`, or `openspec` only when the active shell correctly resolves the installed launcher through PATHEXT.

In commands below, `<openspec>` is a documentation placeholder for that selected executable, not a shell variable. OpenSpec CLI 1.8.x is a separate prerequisite; this workflow does not install it.

## Route The Task

1. Inspect the repository and confirmed request before choosing a workflow.
2. Use no OpenSpec artifacts for an ordinary small implementation request whose behavior and scope are already clear. Implement and verify directly.
3. When the user explicitly asks for a software-change plan, use OpenSpec even if the change is localized. Use `evidence-core` for a concise proposal, requirements when behavior changes, and tasks.
4. Use `evidence-heavy` when the accepted work is cross-component or multi-stage, changes a public API/schema/persistent data, touches auth/security/finance, or controls production/external/scheduled effects.
5. Ambiguity alone is not a reason to create artifacts. Gather evidence or ask one material blocking question first.

## Natural-Language State Machine

Do not select a phase from the user's exact wording. Resolve the active change and run `<openspec> status --change <name> --json`; its first ready artifact is the next planning step.
Native status controls artifact order only. `isPlanningComplete` means files exist; it is not semantic approval and must never by itself trigger a ready-to-apply message.

- A clear software-change request that requires OpenSpec starts the official continuous path: select the schema by the routing rules above, then run `<openspec> new change "<name>" --schema <selected-schema>`. Never use `openspec-propose` or fast-forward.
- If the intent is materially unclear, use `openspec-explore` first. Explore creates no artifacts and does not invent the missing decision.
- Drive the official `<openspec> status` and `<openspec> instructions` loop directly through every ready planning artifact in schema order. After each artifact, run its required gates; when they pass and no user-owned decision is pending, continue without asking for routine confirmation.
- A clear request to implement or change software carries local authority through planning, apply, verification, and required reviews. An explicit plan-only, review-only, diagnosis-only, or other narrower request remains limited to that scope and stops before implementation.
- Ordinary continuation such as "ок", "делай", "дальше", or "продолжай" resumes the same continuous flow. It does not change a `proposed` decision to `accepted` and does not answer an open `Q-*` item.
- Summarize material requirements and decisions at natural checkpoints or in the final handoff without yielding merely because an artifact or passing gate completed. Keep unsupported decisions `proposed` until the user clearly approves them.
- Corrections use `openspec-update-change` and stay within the same artifact unless the intent itself changed.
- Pause only when progress requires a user-owned clarification, decision, authorization, scope change, or disposition that cannot be derived from accepted authority and inspected evidence. External effects retain their separate GO boundary.

## Start Or Continue A Change

- Work inside the target repository. Never use a shared workspace folder for a single-project change.
- If the repository has no `openspec/` setup and the user explicitly requested a software plan/spec or the accepted implementation requires one, initialize it with `<openspec> init <repo> --tools codex --no-animation --no-copilot-cloud`. Do not force the `core` profile; use the configured evidence profile.
- After initialization, set the repository's `openspec/config.yaml` default `schema` to `evidence-core`; select `evidence-heavy` explicitly for heavy changes.
- Create changes through the official CLI with `<openspec> new change "<name>" --schema evidence-core` or `--schema evidence-heavy`; advance by repeatedly following official status and artifact instructions. Do not delegate an end-to-end request to generated single-step skills or their default-only schema rule; an explicitly requested single-step helper remains bounded to that request.
- Follow `<openspec> status --change <change-name> --json` and `<openspec> instructions <artifact> --change <change-name> --json`; do not assume artifact paths or readiness.
- Keep stock OpenSpec current-state specs under `openspec/specs/` and proposed deltas under `openspec/changes/`.
- Do not use `openspec-propose` or `openspec-ff-change`; continuous execution still creates and validates every required artifact in official dependency order.

## Evidence And Acceptance Gate

Read [references/requirement-contract.md](references/requirement-contract.md) before writing or reviewing a change.

- Preserve facts, observations, hypotheses, and questions as different record types.
- Repository paths and external URLs are observational evidence, not authority for accepted behavior. An accepted decision requires explicit `user:USER-*` authority; an accepted requirement may cite only exact user authority or an accepted decision.
- Reference existence is not semantic support. Compare the entire normative behavior with the cited USER record; any extra behavior, constraint, API detail, security rule, or adjacent scope stays proposed.
- Never turn a plausible default into an accepted requirement.
- Record material decisions as `### DEC-<id>: <title>` with `Status` and `Source`. Only an accepted decision may be used as `Source: decision:DEC-<id>`.
- A generic decision reference, an absent evidence record, or a `proposed` decision is unsupported.
- Derive tasks only from accepted requirements. A blocking question stops task creation and implementation.
- Immediately after any proposal/spec/design update, and again before tasks, before reporting planning complete, and before apply, resolve this active skill's root and run this single fail-closed command as a separate tool call:
  - `python <openspec-workflow-skill-root>/scripts/validate_change.py --repo <repo> --change <change-name>`
- If the active skill root cannot be resolved, stop and report the exact missing path resolution; do not fall back to a user-specific hard-coded path or skip the gate.
- The command runs both native strict validation and the deterministic evidence validator. Do not replace it with `openspec validate`, combine it with mutation commands, or infer success from native status.
- A zero exit from that exact current-artifact gate is required before tasks or implementation. After any artifact edit, earlier gate evidence is stale.
- After the deterministic gate passes, perform the read-only semantic entailment review; reference validity cannot prove that the cited evidence supports the entire requirement.
- Treat either failure as a contract failure, not as permission to fill gaps. Diagnose and repair an unambiguous in-scope agent-authored artifact failure, rerun the gate, and continue after it passes. Pause only when a safe correction requires user authority or a material decision, or the blocker cannot be resolved in scope.
- Under review contract v3, give every accepted requirement a stable `REQ-*` id and put an inline `openspec-trace` marker on each implementation task with exact requirement ids and concrete planned verification. The validator prints the read-only requirement → accepted decision when cited → task → planned verification matrix. Do not create a separate traceability file. Before apply, fail closed if any accepted requirement has no traced implementation task or planned verification. For explicit `skip_specs: true`, tasks use `requirements=none` and still require concrete planned verification.
- If native status says complete but either gate still fails after safe in-scope repair, report the change as blocked and list only the unsupported requirements, decisions, or questions. Do not suggest apply.

## Architecture Growth Gate

- Preserve `<!-- openspec-architecture-contract:v1 -->` and classify `Architecture impact` from the inspected production baseline, not from task wording alone.
- Use `material` when the planned change touches an existing production file over 1000 lines, expects roughly 250 or more production lines in one file, or adds multiple independently testable responsibilities. These are review triggers, not automatic defects.
- A material classification is incompatible with `evidence-core`; recreate the change with `evidence-heavy` before specs or tasks. Do not silently omit the trigger to keep a smaller schema.
- For material impact, record component paths and current sizes, expected growth, existing and new responsibilities, transaction owner, boundary options, one chosen ownership decision, known cost, and a narrow ratchet scope in `design.md`.
- Before tasks, run `$architecture-review` against the actual baseline and planning artifacts, then run `python <architecture-review-skill-root>/scripts/validate_openspec_architecture.py --repo <repo> --change <change-name> --phase planning`. A `NOT READY` verdict or nonzero exit blocks task creation.
- Before production edits, require exactly one completed `openspec-review:architecture` task with Coverage, Growth, Ownership, Findings, Exclusions, Reviewer, and `Verdict: READY`; rerun the validator with `--phase apply`. Do not substitute ordinary code review or green tests.
- Existing large services are grandfathered only as baseline. Do not start broad legacy refactoring without accepted scope, but do not add an unowned responsibility or exceed the accepted growth decision merely because the component was already large.

## Decision Discipline

- Ask the user only for choices that change observable behavior, business policy, data ownership, security, cost, rollout, or an external effect. Derive implementation observations from inspected project evidence and keep unsupported future mechanics out of the current change.
- When several related proposed decisions are ready, show one concise decision checkpoint with exact ids, recommendations, and consequences, then ask one approval question for that displayed block. Record the answer as one USER evidence record that names the approved ids. Partial approval leaves the other decisions proposed.
- Do not turn a generic "continue" into approval. Do not ask the user to approve low-level implementation details that existing contracts or accepted decisions already determine.

## Implementation And Verification

1. Implement only accepted requirements and the minimum required wiring.
2. If intent changes, update the change artifacts before continuing; do not silently rewrite accepted behavior.
3. Use `evidence-heavy` design decisions and rollback sections only when their risk actually applies.
4. Verify implementation against scenarios and record actual evidence. OpenSpec validation proves structure, not truth or runtime correctness.
5. External, production, destructive, financial, persistent-data, or irreversible effects still require the separate applicable `GO`; an OpenSpec change never grants authority.

After `<openspec> archive <change-name>` succeeds, resolve this active skill's root and run the standalone repository integrity gate as a separate step:

- `python <openspec-workflow-skill-root>/scripts/validate_requirement_ids.py --repo <repo>`

Then run native strict validation and `git diff --check`. A nonzero repository integrity result blocks commit, release, deployment, and any claim that archive completed cleanly. Archived copies under `openspec/changes/archive/` are history and are intentionally excluded; the gate checks the resulting current specifications under `openspec/specs/`.

Before an apply step creates or materially moves a production type, inspect neighboring feature structure, namespaces or module boundaries, dependency registration, and relevant architecture tests. Place code by feature and cohesive responsibility. Keep a readable cohesive root flat; add responsibility-named subfolders only when they materially improve navigation. Do not create generic `Interfaces` and `Implementations` buckets solely by declaration type, and do not reorganize adjacent legacy code incidentally. A material ownership, namespace, or registration restructure requires accepted `evidence-heavy` scope and architecture review. Concrete feature names and placement examples remain authoritative in the consumer repository.

Before step 1, run the architecture growth gate for every v1 architecture contract. A nonzero architecture validator exit blocks implementation even when native OpenSpec status and the ordinary evidence validator pass.

Match evidence to the claimed layer. UI layout needs rendered/browser evidence; interactive UI needs component or browser interaction; framework lifecycle behavior needs the real framework path; authorization needs negative boundary tests; migrations need a real database path; idempotency needs replay after state change; concurrency needs stale/conflicting writes. A green lower-level substitute does not close a higher-level claim.

For material UI creation or redesign, record an explicit UI contract in the proposal before tasks: accepted artifact and authority, theme, viewports, required states, and representative data shape grounded in inspected API/product evidence. If the artifact and live grouping/cardinality differ materially, keep the contract blocked until reconciled. A narrow code-only correction may reuse an accepted contract; ordinary non-visual changes declare no UI contract.

Complete the UI checkpoint only after rendered desktop/mobile evidence is opened and explicitly compared with the accepted artifact. Record artifact, viewports, theme, states, data, evidence paths, comparison method, reviewer, and discrepancies. Component tests, DOM selectors, screenshot generation, and mocked fixtures cannot independently support a fidelity claim. Before release/deploy include visual coverage in the final reviewer brief; after deploy distinguish local/mock verification from a read-only real-route check with actual API, console, network, and screenshots.

When a material UI project supports deterministic same-environment browser rendering, commit a Playwright `toHaveScreenshot` baseline and run it as regression evidence. It complements, and never replaces, explicit comparison with the accepted artifact. If OS, browser, fonts, or rendering cannot be stabilized, do not force a flaky baseline; record that limitation in the task/checkpoint evidence.

Before implementation, record the actual Git branch, HEAD, upstream, dirty baseline, and pre-existing unrelated changes. Before commit or push, inspect them again and confirm the pending diff belongs to the accepted change. A failed branch or worktree command leaves the previous state in force; never report the intended state as achieved.

Use completion terms exactly: `planning complete`, `implementation in progress`, `implementation verified`, `full-diff review passed`, `release ready`, and `deployed`. OpenSpec `all_done` is only checkbox state. Do not say `release ready` while a required rehearsal, maintenance mechanism, approval, or other release prerequisite remains open.

## Implementation Waves And Review Gates

Do not review every edited file or completed checkbox. Review coherent implementation waves so downstream work does not build on a broken contract.

- For `evidence-core`, implement and verify the bounded change, then run one independent read-only review before marking the change complete or handing it off.
- For `evidence-heavy`, group `tasks.md` under a small number of semantic waves using ordinary Markdown headings. A wave is a coherent behavior or contract boundary, not an arbitrary task count. Typical boundaries include data/migration, auth or public API, integration between components, and user-facing completion; include only boundaries that exist in the accepted change.
- End a heavy wave when its accepted scenarios are implemented and its targeted checks have run, or before another wave depends on its contract. Dispatch and await the independent read-only review automatically; continue to the next wave after a passing review and any blocking findings are resolved, without asking for routine confirmation.
- Always run a final full-diff release review after the last heavy wave and before any deploy or other external effect. The last wave review may satisfy this final gate only when it covered the full pending diff; any later material diff makes the review stale.
- Give the reviewer the base commit, current HEAD/worktree state, complete changed-file inventory, accepted requirement ids, completed waves, test evidence, and known limits. The reviewer must inspect the current diff, accepted requirements, affected contracts, negative/error paths, cross-wave interactions, and whether tests prove the claimed behavior. Tests and OpenSpec validation do not replace this review.
- Require the reviewer to state `Coverage: full pending diff` or `Coverage: partial`, list checked requirements, and name exclusions. A partial review cannot satisfy the final gate.
- An independent review is performed by a separate read-only reviewer/subagent, not by the implementation agent loading a review checklist itself. If no reviewer is available, report the gate as not run; do not mark the change, wave, or release complete and do not hand it off without explicit user disposition.
- The reviewer reports findings with `High`, `Medium`, or `Low` severity, file/line evidence, impact, and fix direction. The reviewer does not edit files, mark tasks complete, accept requirements, or approve effects.
- A validated `High` finding blocks the next wave. Resolve a validated `Medium` finding or present it to the user for an explicit disposition before continuing. `Low` findings do not block unless they combine into material risk.
- After a fix, re-review the affected finding and adjacent contract. Repeat the full review only when the fix materially changes multiple waves or the overall risk surface.
- Keep review output in the session. Do not create `review.md`, task folders, or duplicate evidence artifacts unless the repository already requires them or the user asks.
- Mark a wave complete only after its targeted verification and blocking review findings are resolved. A checked task list or `isPlanningComplete` alone is not completion evidence.
- If a validated finding invalidates completed work, reopen affected tasks and update proposal/spec/design first if intended behavior changes. In `evidence-heavy`, add a remediation wave; in `evidence-core`, add remediation tasks before its single final checkpoint. Prior verification and review are stale for the affected contract until rerun.
- The validator enforces review-marker structure and requires a concrete full-diff coverage declaration on a completed final checkpoint. Whether that declaration is truthful and still fresh after a later material code diff remains a session/reviewer responsibility; recheck repository state and uncheck a stale checkpoint rather than treating the checkbox as cryptographic proof.
