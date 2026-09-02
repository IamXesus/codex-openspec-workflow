<!-- openspec-review-contract:v3 -->
UI contract: none

## 1. Execution boundary guidance

- [x] 1.1 <!-- openspec-trace: requirements=REQ-EBC-001,REQ-EBC-002,REQ-EBC-004; verification=run the focused shared-policy test and inspect the distributed wording to prove reviewer scope is advisory, compaction reorientation is required, one primary executor is non-blocking, route/effort hints stay risk-driven, and CI-only constraints are preserved --> Add the compact scope, continuation, subagent, route, effort, and execution-boundary rules to the existing policy and skills without introducing a new workflow subsystem. Verified by `scripts/test_shared_policy.py` and cross-surface inspection.

## 2. OpenSpec and validation guardrails

- [x] 2.1 <!-- openspec-trace: requirements=REQ-EBC-001,REQ-EBC-002,REQ-EBC-003; verification=run the OpenSpec validator unit tests and both schema validations, including a skip_specs fixture without the marker (rejected) and with the exact no-behavior marker (accepted) --> Add the structured no-behavior-delta marker contract, root/read-only invocation wording, reviewer-boundary wording, and continuation guardrails to both schema instructions/templates and the deterministic validator. Verified by 72 OpenSpec/validator tests and `openspec schema validate` for both schemas.

## 3. Regression surface

- [x] 3.1 <!-- openspec-trace: requirements=REQ-EBC-001,REQ-EBC-003,REQ-EBC-004; verification=run the shared policy/package tests and validate the prompt-routing fixture plus git diff --check, proving no consumer-specific text, no test-count quota, no silent reviewer acceptance, and no package-check mutation contract --> Extend existing focused regressions and prompt-routing fixtures for scope lock, skip_specs, route/effort guidance, and release continuation; keep all checks minimum-sufficient. Verified by full `scripts/validate.ps1`, Promptfoo config validation, and `git diff --check`.

## 4. Release review

- [x] 4.1 <!-- openspec-review:final --> Coverage: full pending diff; Requirements: REQ-EBC-001,REQ-EBC-002,REQ-EBC-003,REQ-EBC-004; Exclusions: PayFlow product changes, host installation, external release, C4, and live Promptfoo model execution; Reviewer: /root/final_boundary_review_retry
