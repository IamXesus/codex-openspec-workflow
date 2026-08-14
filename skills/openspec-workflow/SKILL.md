---
name: openspec-workflow
description: "Use for software-change planning requests such as 'сделай план', 'заведи план', 'спланируй изменение', OpenSpec, SDD, specification, design-spec, or acceptance criteria, and for broad or high-risk implementation that needs a durable behavior contract. Route ordinary small implementation away from specs; use evidence-core for localized plans and evidence-heavy for cross-component, public-contract, persistent-data, auth/security, financial, production, or external-system work."
---

# OpenSpec Workflow

Use the official OpenSpec CLI, schemas, and generated workflows as the only artifact engine. This skill only routes natural language, selects the existing schema, and enforces evidence before tasks or apply.

## Route The Task

1. Inspect the repository and confirmed request before choosing a workflow.
2. Use no OpenSpec artifacts for an ordinary small implementation request whose behavior and scope are already clear. Implement and verify directly.
3. When the user explicitly asks for a software-change plan, use OpenSpec even if the change is localized. Use `evidence-core` for a concise proposal, requirements when behavior changes, and tasks.
4. Use `evidence-heavy` when the accepted work is cross-component or multi-stage, changes a public API/schema/persistent data, touches auth/security/finance, or controls production/external/scheduled effects.
5. Ambiguity alone is not a reason to create artifacts. Gather evidence or ask one material blocking question first.

## Natural-Language State Machine

Do not select a phase from the user's exact wording. First select the change through the cross-session gate below, then run `openspec.cmd status --change <name> --json`; its first ready artifact is only the next structural planning step.
Native status controls artifact order only. `isPlanningComplete` means files exist; it is not semantic approval and must never by itself trigger a ready-to-apply message.

- A new planning request such as "сделай план" starts the official stepwise path: select the schema by the routing rules above, then run `openspec.cmd new change "<name>" --schema <selected-schema>`. Never use `openspec-propose` or fast-forward.
- If the intent is materially unclear, use `openspec-explore` first. Explore creates no artifacts and does not invent the missing decision.
- On an active change, ordinary continuation such as "ок", "делай", "дальше", or "продолжай" means `openspec-continue-change`: create exactly one ready artifact and stop.
- Continuation authorizes the next artifact only. It does not change a `proposed` decision to `accepted` and does not answer an open `Q-*` item.
- After creating an artifact, summarize its new requirements and decisions. Keep them `proposed` until the user clearly approves that content; a generic continuation advances state but is not approval.
- Corrections use `openspec-update-change` and stay within the same artifact unless the intent itself changed.
- Implementation requires a separate clear apply/build request after planning validation. A planning request never carries authority into apply.

## Cross-Session Change Selection And Freshness Gate

A fresh model session has no durable ownership of a previously active change. Repository files are durable evidence, not proof that the user's current intent belongs to the nearest, oldest, or only change.

Before continuing any existing change in a new session, after compaction, or after returning from another workstream:

1. List candidate changes and inspect the candidate proposal, specs, tasks, `.openspec.yaml`, review-contract marker, open task ids, and last completed/release wave.
2. Restate the candidate's one accepted capability and compare it with the current request. Continue only when the request is inside that accepted capability and existing open tasks. A new independently reviewable/releasable capability, a new spec namespace, or work appended after deployment/production reconciliation starts a new change.
3. Treat review contracts v1/v2 as completion-only compatibility state. They may finish already accepted open tasks, but must not receive new requirements, capabilities, waves, roadmap items, or implementation tasks. Put new scope in a separate v3 change; do not upgrade a partially implemented/deployed legacy history in place.
4. Fetch the configured upstream read-only and record branch, HEAD, upstream, dirty state, upstream HEAD, and divergence. Stop on fetch/ref failure or material drift; do not silently rebase, merge, copy, or reinterpret stale code.
5. Classify every referenced commit/ref as either historical evidence, accepted visual artifact, or implementation base. An old artifact may remain authoritative for its accepted visual content, but its code is never an implementation base until its diff is reconciled against current upstream and current contracts.
6. Show the selected change, capability, contract version, open task ids, baseline/divergence, and stale references before reporting the next step. If selection remains materially ambiguous, ask one concise blocking question.

A generic 'continue' in a fresh session does not select a legacy or stale change and does not authorize a new capability inside it.

## Start Or Continue A Change

- Work inside the target repository. Never use a shared workspace folder for a single-project change.
- Keep one change scoped to one coherent capability and delivery stream. Size alone does not require splitting, but independent acceptance, release, rollback, ownership, or production reconciliation does. Keep roadmap candidates and unrelated external handoffs out of implementation tasks.
- If the repository has no `openspec/` setup and the user explicitly requested a software plan/spec or the accepted implementation requires one, initialize it with `openspec.cmd init <repo> --tools codex --no-animation --no-copilot-cloud`. Do not force the `core` profile; use the configured stepwise profile.
- After initialization, set the repository's `openspec/config.yaml` default `schema` to `evidence-core`; select `evidence-heavy` explicitly for heavy changes.
- Create changes through the official CLI with `openspec.cmd new change "<name>" --schema evidence-core` or `--schema evidence-heavy`; advance through `openspec-continue-change` one artifact at a time. Do not delegate schema selection to the generated `openspec-new-change` default-only rule.
- Follow `openspec.cmd status --change <change-name> --json` and `openspec.cmd instructions <artifact> --change <change-name> --json`; do not assume artifact paths or readiness.
- Keep stock OpenSpec current-state specs under `openspec/specs/` and proposed deltas under `openspec/changes/`.
- Do not use `openspec-propose` or `openspec-ff-change`; they bypass the required one-artifact review rhythm.

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
- Treat either failure as a contract failure, not as permission to fill gaps.
- Under review contract v3, give every accepted requirement a stable `REQ-*` id and put an inline `openspec-trace` marker on each implementation task with exact requirement ids and concrete planned verification. The validator prints the read-only requirement → accepted decision when cited → task → planned verification matrix. Do not create a separate traceability file. Before apply, fail closed if any accepted requirement has no traced implementation task or planned verification. For explicit `skip_specs: true`, tasks use `requirements=none` and still require concrete planned verification.
- Every task-like numbered line in v3 `tasks.md` must be a checkbox. Do not hide roadmap, planning, or implementation work as plain `N.M` text that the OpenSpec task runner cannot see.
- If native status says complete but either gate fails, report the change as blocked and list only the unsupported requirements, decisions, or questions. Do not suggest apply.

Before saying a plan is ready, run `openspec.cmd instructions apply --change <name> --json` read-only and reconcile its task list with every accepted REQ id and the expected implementation/review checkpoints. Report `artifacts structurally present` when only native status passes. Report `implementation-ready plan` only when v3 validation, semantic review, task-runner reconciliation, and explicit user acceptance all pass.

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

Match evidence to the claimed layer. UI layout needs rendered/browser evidence; interactive UI needs component or browser interaction; framework lifecycle behavior needs the real framework path; authorization needs negative boundary tests; migrations need a real database path; idempotency needs replay after state change; concurrency needs stale/conflicting writes. A green lower-level substitute does not close a higher-level claim.

For material UI creation or redesign, record an explicit UI contract in the proposal before tasks: accepted artifact and authority, theme, viewports, required states, and representative data shape grounded in inspected API/product evidence. If the artifact and live grouping/cardinality differ materially, keep the contract blocked until reconciled. A narrow code-only correction may reuse an accepted contract; ordinary non-visual changes declare no UI contract.

Complete the UI checkpoint only after rendered desktop/mobile evidence is opened and explicitly compared with the accepted artifact. Record artifact, viewports, theme, states, data, evidence paths, comparison method, reviewer, and discrepancies. Component tests, DOM selectors, screenshot generation, and mocked fixtures cannot independently support a fidelity claim. Before release/deploy include visual coverage in the final reviewer brief; after deploy distinguish local/mock verification from a read-only real-route check with actual API, console, network, and screenshots.

When a material UI project supports deterministic same-environment browser rendering, commit a Playwright `toHaveScreenshot` baseline and run it as regression evidence. It complements, and never replaces, explicit comparison with the accepted artifact. If OS, browser, fonts, or rendering cannot be stabilized, do not force a flaky baseline; record that limitation in the task/checkpoint evidence.

Before implementation, record the actual Git branch, HEAD, upstream, dirty baseline, and pre-existing unrelated changes. Before commit or push, inspect them again and confirm the pending diff belongs to the accepted change. A failed branch or worktree command leaves the previous state in force; never report the intended state as achieved.

When another agent/session owns an external dependency, keep the local task open as `external pending`, record the owner and return condition, and continue only independent accepted work. Do not spawn a substitute worker, prepare retries, mutate the external system, or mark the dependency complete unless the user explicitly changes ownership.

Use completion terms exactly: `planning complete`, `implementation in progress`, `implementation verified`, `full-diff review passed`, `release ready`, and `deployed`. OpenSpec `all_done` is only checkbox state. Do not say `release ready` while a required rehearsal, maintenance mechanism, approval, or other release prerequisite remains open.

## Implementation Waves And Review Gates

Do not review every edited file or completed checkbox. Review coherent implementation waves so downstream work does not build on a broken contract.

- For `evidence-core`, implement and verify the bounded change, then run one independent read-only review before marking the change complete or handing it off.
- For `evidence-heavy`, group `tasks.md` under a small number of semantic waves using ordinary Markdown headings. A wave is a coherent behavior or contract boundary, not an arbitrary task count. Typical boundaries include data/migration, auth or public API, integration between components, and user-facing completion; include only boundaries that exist in the accepted change.
- End a heavy wave when its accepted scenarios are implemented and its targeted checks have run, or before another wave depends on its contract. Then stop for an independent read-only review before continuing.
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
