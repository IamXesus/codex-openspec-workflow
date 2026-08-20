## Context

The package already has a public transaction owner in `workflow_package.py`, an internal trust-boundary helper in `workflow_package_state.py`, and two shared-root receipts. One shared installation can serve many consumers, so consumer policy installation state cannot be truthfully stored only in either shared-root receipt. The selected consumer file must carry its own bounded installation metadata.

The portable fragment is ordinary UTF-8 Markdown. Existing consumer `AGENTS.md` content is repository-owned and may use LF, CRLF, or no final newline. The package must identify only its exact managed region and must not use fuzzy prose matching.

## Goals / Non-Goals

Goals:

- Make explicit consumer adoption install and check one versioned portable-policy block.
- Preserve consumer-owned content and newline style outside that block.
- Distinguish safe package drift from a locally edited or malformed managed block.
- Fail before any shared-root write when consumer policy preflight is conflicted.
- Keep the existing CLI and wrapper surface, extending the meaning of `--consumer-repo` for install.

Non-goals:

- Inferring a consumer from the current directory.
- Automatically interpreting or merging semantically similar unmarked instructions.
- Managing consumer business, deployment, navigation, or domain-specific rules.
- Adding a generic Markdown merge engine, dependency, symlink, Git operation, or background updater.
- Extending the existing shared-root rollback command to consumer files in this change.

## Decisions

The accepted product decisions DEC-001 through DEC-004 are recorded in `proposal.md` and are not duplicated here.

The managed block uses exact begin/end HTML comments. The begin marker contains a format version, workflow version, and SHA-256 of the normalized managed body; this header is the per-consumer policy receipt. Hashing converts CRLF/CR to LF and removes only the one structural newline adjacent to the markers. It does not normalize spaces or Markdown content.

State parsing happens before install mutates either shared root. Exactly zero markers means `missing`. Exactly one valid pair with a body matching its recorded installed hash is `current` when version and canonical hash match, otherwise `stale`. Partial, reversed, nested, duplicated, invalid-metadata, unreadable-UTF-8, or installed-body-hash mismatch states are `conflict`.

An existing file that is exactly the canonical unmarked fragment after newline normalization is adopted by adding markers around that body rather than appending a duplicate. Other unmarked consumer content receives one appended managed block. This exact-match migration supports the already inspected manually adopted Pyrus file without fuzzy ownership inference.

Install writes a sibling temporary file and replaces the target only after shared asset copies and receipts have succeeded. A conflict is detected before those writes. A current block is not rewritten. Check remains read-only. The remediation argv retains `--consumer-repo` for `missing` and `stale`; conflict emits reconciliation guidance rather than an automatic overwrite command.

## Component Ownership

**Architecture impact:** material

**Inspected baseline:** `scripts/workflow_package.py` at 352 lines; `scripts/workflow_package_state.py` at 275 lines; `scripts/test_workflow_package.py` at 371 lines; `policy/AGENTS.fragment.md` at 41 lines.

**Expected growth:** implementation evidence is +52/-12 lines in `workflow_package.py` and +184 lines in `workflow_package_state.py`; the latter is the accepted 180-190 line envelope for the bounded parser, renderer, conflict-state model, newline/BOM preservation, mode preservation, and atomic writer. Tests add +308/-3 lines, including the isolated subprocess lifecycle rehearsal. No production file reaches the roughly 250-line single-file growth trigger.

**Existing responsibilities:** `workflow_package.py` owns CLI parsing, root selection, install/check/rollback ordering, result aggregation, and human/JSON output. `workflow_package_state.py` owns containment, manifests, hashes, receipts, backup validation, and filesystem-state checks.

**New responsibilities:** consumer policy parse/render/state classification, exact managed-block replacement, and consumer policy aggregation into install/check output.

**Transaction owner:** `workflow_package.py::install` remains the public install transaction owner and must preflight the selected consumer before shared-root mutation.

**Boundary options:** keep all logic in `workflow_package.py`; add a new generic Markdown/policy module; or extend the existing internal filesystem-state collaborator with policy-specific helpers while leaving orchestration in the public engine.

**Decision:** extract-collaborators

The existing `workflow_package_state.py` receives narrow policy-state helpers because parsing, normalized hashing, containment, and safe file replacement are filesystem trust-boundary mechanics. `workflow_package.py` retains selection, ordering, aggregation, and CLI behavior. No third production module or generic abstraction is introduced.

**Known cost:** the state helper grows from 275 to 459 lines and its name remains broader than receipts/manifests, but the new behavior stays beside existing file-integrity code, remains covered through its public state/install contract, and avoids increasing the public engine with parsing details or adding a third module.

**Ratchet scope:** change only the consumer policy path required by REQ-MPA-001 through REQ-MPA-004; do not refactor shared-root receipts, backup format, schema resolution, or wrapper architecture.

## Risks / Mitigations

- Existing unmarked policy prose could resemble the central fragment. Mitigation: recognize only whole-file exact normalized equality; never fuzzy-match a subsection.
- A conflict discovered after shared copies would create a partial install. Mitigation: parse and classify consumer policy before any shared-root mutation.
- Newline conversion could create noisy consumer diffs. Mitigation: preserve detected outer newline style and never rewrite text outside the managed span.
- A crash during consumer write could truncate instructions. Mitigation: write a sibling temporary file, flush it, then replace the target.
- Shared rollback does not restore consumer policy. Mitigation: do not claim that it does; an install conflict is preflighted, current blocks are not rewritten, and consumer updates replace only an intact package-owned block. Document this boundary.
- Existing callers use `--consumer-repo` only with check. Mitigation: the option remains optional and shared-only install behavior is unchanged when it is absent.

## Migration And Rollback

Release the behavior as package `1.0.1`. Existing shared roots upgrade through the current receipt-owned path without changing receipt format. A consumer becomes managed only when an operator explicitly runs install with `--consumer-repo` after the applicable persistent-effect `GO`.

For an absent file, manual rollback is deletion of the newly created `AGENTS.md` only if it still contains solely the intact managed block. For an appended or updated block, manual rollback is removal of exactly the intact marked block; consumer-owned text remains untouched. The existing `rollback` CLI continues to cover shared roots only and documentation must state that limit.

## Open Questions

None.
