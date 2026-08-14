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
- In a fresh session or after compaction, do not auto-select the nearest/only OpenSpec change. Reconfirm that the current request fits its one accepted capability, inspect open task ids and review-contract version, and refresh upstream/divergence read-only.
- Treat review-contract v1/v2 changes as completion-only. New capabilities, waves, roadmap work, or implementation tasks require a separate v3 change. An old commit may remain an accepted artifact/evidence source, but never becomes the implementation base without reconciliation against current upstream.
- Before tasks, before reporting planning complete, and before apply, run the bundled fail-closed validator. Then perform the read-only semantic and traceability audit required by the workflow skill.
- Before calling a plan implementation-ready, reconcile `openspec instructions apply --json` with accepted requirement ids and expected task/review checkpoints. Native `isPlanningComplete` means only that artifacts exist.
- Review coherent heavy implementation waves and run one final full-diff review before release. Do not equate artifact existence, checked tasks, green tests, release readiness, and deployment.

## Material UI

- Treat an accepted visual artifact as a testable contract. Record its authority, theme, viewports, states, and representative data grounded in inspected product/API evidence.
- Reconcile material differences in live cardinality, grouping, long content, or negative states before implementation.
- Component tests prove logic; browser assertions prove interaction; committed visual baselines detect rendering drift; explicit comparison proves fidelity; a real-route post-deploy smoke proves production integration.
- Require an independent visual review after a material UI wave and include visual-contract coverage in the final full-diff review.
