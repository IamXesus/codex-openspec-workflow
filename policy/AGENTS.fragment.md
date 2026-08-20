## Evidence, Scope, And Authority

- Treat missing facts and requirements as unknown. Do not turn assumptions or plausible defaults into accepted behavior.
- Separate confirmed evidence, observations, hypotheses, decisions, and open questions whenever the distinction affects behavior or scope.
- Planning does not authorize implementation. Implementation does not authorize an external, destructive, production, financial, or persistent-data effect.
- Accepted requirements require inspected evidence or an explicit user decision. Blocking questions stop task creation and implementation.
- Prefer the smallest coherent diff and existing project patterns. Do not create adjacent artifacts, abstractions, dependencies, or follow-up work without a current requirement.

## OpenSpec Routing

- Use no OpenSpec package for small, bounded, already-clear changes.
- Use `evidence-core` for an explicitly requested localized software plan.
- Use `evidence-heavy` for broad, multi-stage, cross-component, public-contract, persistent-data, auth/security, financial, production, external-system, or scheduled-side-effect work.
- Advance planning one official OpenSpec artifact at a time. A generic continuation advances state but does not accept proposed decisions.
- Before tasks, before reporting planning complete, and before apply, run the bundled fail-closed validator. Then perform the read-only semantic and traceability audit required by the workflow skill.
- Classify architecture impact from the inspected production baseline. Use `evidence-heavy` when a planned change touches an existing production file over 1000 lines, expects roughly 250 or more production lines in one file, or adds multiple independently testable responsibilities.
- For material impact, record component ownership and transaction boundaries in design, then require an independent `$architecture-review` and the bundled fail-closed architecture validator before tasks and production edits. Existing large components do not authorize unrelated cleanup or new unowned responsibilities.
- Review coherent heavy implementation waves and run one final full-diff review before release. Do not equate artifact existence, checked tasks, green tests, release readiness, and deployment.

## Shared Code Placement

- Before creating or materially moving a production type, inspect neighboring feature structure, namespaces or module boundaries, dependency registration, and relevant architecture tests.
- Organize new or materially changed code by feature and cohesive responsibility. A small cohesive feature root may remain flat; add a responsibility-named subfolder only when it materially improves navigation.
- Do not introduce generic `Interfaces` and `Implementations` folders solely by declaration type. Keep an internal contract with the cohesive boundary it serves.
- Treat this as a narrow ratchet: do not move neighboring legacy files, churn namespaces or registrations, or add speculative wrappers incidentally.
- Route a material ownership restructure through accepted `evidence-heavy` scope and architecture review.
- Consumer repositories remain authoritative for concrete feature names, namespaces, dependency-registration rules, architecture tests, and placement examples. Keep reusable guidance general.

## Shared Workflow Ownership

- Treat the installed central package as upstream for reusable schemas and templates, validators, skills, routing and lifecycle gates, and general authoring policy. A copied consumer asset is not an upstream source.
- Keep each consumer repository authoritative for its OpenSpec context, business and technical documentation, navigation, deployment convention, and domain-specific examples. Project-local schemas may intentionally shadow shared schemas and require explicit reconciliation; never overwrite or remove them implicitly.
- A freshness check is read-only. An install with an explicit consumer repository may create `AGENTS.md` or update only the intact centrally managed policy block; it never owns surrounding consumer instructions. Installation does not pull Git, publish a release, or authorize any external effect.

## Project Knowledge Bootstrap

- An install with an explicitly selected consumer repository may create only missing canonical files under `docs/project-handoff/` and a missing `openspec/config.yaml`. Existing project documentation and configuration remain repository-owned and must not be heuristically replaced.
- Treat `docs/project-handoff/project-audit.md` as structural evidence, not established project semantics. When its managed marker says `status=pending`, inspect the repository and applicable user authority before substantial implementation, populate only confirmed facts and explicit open questions, record the inspected Git/evidence state, and then change the marker to `status=complete`.
- Keep business processes, integrations, technical architecture, open issues, and normative OpenSpec current behavior aligned with accepted implementation changes. Do not claim completion while affected repository knowledge disagrees with the code.
- These repository paths and obligations are host-neutral. Codex, Orca, Omnigent, IDEs, and other repository-aware agents use the same committed files; no host-specific copy is authoritative.

## Material UI

- Treat an accepted visual artifact as a testable contract. Record its authority, theme, viewports, states, and representative data grounded in inspected product/API evidence.
- Reconcile material differences in live cardinality, grouping, long content, or negative states before implementation.
- Component tests prove logic; browser assertions prove interaction; committed visual baselines detect rendering drift; explicit comparison proves fidelity; a real-route post-deploy smoke proves production integration.
- Require an independent visual review after a material UI wave and include visual-contract coverage in the final full-diff review.

