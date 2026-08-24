<!-- openspec-review-contract:v3 -->
UI contract: none

## 1. Requirement ID integrity

- [x] 1.1 <!-- openspec-trace: requirements=REQ-REPO-ID-INTEGRITY-001; verification=run focused Python tests proving duplicate current IDs fail with both locations and archived copies are ignored --> Add the standalone current-specification uniqueness validator.
- [x] 1.2 <!-- openspec-trace: requirements=REQ-REPO-ID-INTEGRITY-002; verification=run focused Python tests proving ADDED collisions fail and MODIFIED identifier reuse passes --> Integrate active-change collision validation into the complete planning gate.
- [x] 1.3 <!-- openspec-trace: requirements=REQ-REPO-ID-INTEGRITY-003; verification=validate the updated skill and inspect the post-archive command contract --> Require the standalone integrity gate after archive in the shared workflow instructions.
- [x] 1.4 <!-- openspec-review:final --> Final checkpoint. Coverage: full pending diff; Requirements: REQ-REPO-ID-INTEGRITY-001, REQ-REPO-ID-INTEGRITY-002, REQ-REPO-ID-INTEGRITY-003; Exclusions: none; Reviewer: /root/mandatory_gates_review.
