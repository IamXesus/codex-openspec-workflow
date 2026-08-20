# Workflow Evaluation Fixture

- Small bounded changes use no OpenSpec package.
- A clear software-change request that needs OpenSpec proceeds continuously through planning, local implementation, verification, and review without routine pauses.
- An explicit plan-only, review-only, or other narrower request does not authorize later phases.
- Preserve material unknowns as blocking questions or proposed decisions. A generic continuation is not approval.
- A material mismatch between an accepted UI artifact and inspected real data is a blocking contract question: reconcile it with the user before code and report implementation_authorized=false until resolved.
- Production effects require explicit GO from an authorized owner at the last safe point.
- This fixture is read-only. Do not create or edit files.

