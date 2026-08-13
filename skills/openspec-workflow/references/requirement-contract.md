# Requirement Evidence Contract

Apply this contract to every `### Requirement:` block in an OpenSpec delta or current spec.

## Required Metadata

Place these lines directly below the requirement heading:

```markdown
### Requirement: Example
**ID:** REQ-001
**Status:** accepted
**Source:** user:USER-001
The system SHALL ...
```

Allowed authority sources for an accepted requirement:

- user:USER-<id> — an existing USER record that explicitly requests or approves the entire normative behavior;
- decision:DEC-<id> — an existing accepted material decision with explicit user authority.

When the complete behavior needs more than one authority record, list exact sources on the same line separated by commas. Every listed source must be valid and must jointly support the entire requirement; one invalid, observational, or unaccepted source fails the requirement.

Repository paths and external URLs are observational evidence. They may support FACT/OBS records or a proposed decision, but they cannot by themselves authorize a new accepted requirement or accepted decision.
Use `Status: accepted` only when the source actually supports the normative behavior. Use `Status: proposed` while awaiting a material decision. A hypothesis, inference, default, or unanswered question is not an accepted source.

Record material decisions in proposal or design with an exact id:

```markdown
### DEC-001: Profile and identity are one-to-one
**Status:** proposed
**Source:** user:USER-002
```

A decision remains `proposed` while it is supported only by repository or external evidence. It becomes `accepted` only after explicit user approval recorded as `user:USER-*`. Generic references such as `decision:<proposal-name>` are invalid. A decision cannot cite another decision as its own authority.

When several related decisions are presented together, ask one approval question for the exact displayed decision checkpoint. Record one USER evidence line that names the approved DEC ids and the approved content. The same USER record may authorize those exact decisions; it does not authorize omitted, later, or materially expanded behavior. Partial approval leaves the remaining decisions proposed.

For a rename-only delta, place one accepted `Status` and `Source` pair directly below `## RENAMED Requirements` and before its `FROM`/`TO` pairs. The metadata covers only those rename pairs.

For review contract v3, assign each accepted requirement or accepted rename block one unique stable `REQ-*` id. Each implementation task carries an inline marker:

```markdown
- [ ] 1.1 <!-- openspec-trace: requirements=REQ-001; verification=run export integration test and assert a valid CSV download --> Implement CSV export.
```

For an explicit `skip_specs: true` change with no behavioral delta, use `requirements=none`; concrete planned verification remains mandatory.

Use `decision:DEC-*` from the requirement Source as the optional decision column; never invent a decision merely to fill the matrix. The validator renders the matrix to stdout, so do not create a traceability Markdown artifact. A v3 plan cannot pass before apply when an accepted requirement lacks a traced implementation task or concrete planned verification. Contract v1/v2 and explicitly declared legacy changes retain their prior validation behavior.

## Unknowns

Record material unknowns in the proposal as unchecked questions:

```markdown
- [ ] Q-001: <one decision that changes behavior, data, security, cost, or external effects>
```

Do not create a requirement or implementation task from that question. Ask one material question at a time. Non-blocking observations may be recorded as `OBS-*`; hypotheses as `HYP-*` and must remain non-normative.

## Acceptance

- A clear user request can directly support an accepted requirement.
- Approval of a draft can change its supported proposed requirements to accepted.
- Repository evidence can establish existing behavior or a compatibility boundary; it does not invent new desired behavior.
- Structural validation and reference existence are necessary but insufficient. After every artifact update and before tasks or apply, run `validate_change.py` as the complete deterministic gate, then perform a read-only semantic entailment review that checks whether the cited authority records jointly support the whole requirement.
- Native OpenSpec planning-complete means artifacts exist. Do not report the plan ready or suggest apply until both semantic gates pass.
