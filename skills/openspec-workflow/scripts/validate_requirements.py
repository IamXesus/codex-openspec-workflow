#!/usr/bin/env python3
"""Fail closed when an OpenSpec change contains unsupported requirements."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

UI_CONTRACT_V2 = '<!-- openspec-review-contract:v2 -->'
TRACE_CONTRACT_V3 = '<!-- openspec-review-contract:v3 -->'
REQUIREMENT_ID = re.compile(r'^\*\*ID:\*\*\s*(?P<value>REQ-[A-Za-z0-9_-]+)\s*$', re.IGNORECASE)
TRACE_MARKER = re.compile(
    r'<!--\s*openspec-trace:\s*requirements=(?P<requirements>[^;]+);\s*'
    r'verification=(?P<verification>.*?)\s*-->',
    re.IGNORECASE,
)
UI_MODE = re.compile(r'^UI contract:\s*(?P<mode>none|material)\s*$', re.IGNORECASE | re.MULTILINE)
UI_REVIEW = re.compile(r'UI review:', re.IGNORECASE)
UI_SECTION = re.compile(r'(?ms)^## UI Contract\s*$\s*(?P<body>.*?)(?=^##\s|\Z)', re.IGNORECASE)
UI_FIELD = re.compile(r'^\*\*(?P<name>Mode|Artifact|Authority|Theme|Viewports|States|Data):\*\*\s*(?P<value>.+?)\s*$', re.IGNORECASE)

REQUIREMENT = re.compile(r"^### Requirement:\s*(?P<name>.+?)\s*$", re.IGNORECASE)
DECISION = re.compile(r"^###\s+(?P<id>DEC-[A-Za-z0-9_-]+):\s*(?P<name>.+?)\s*$", re.IGNORECASE)
EVIDENCE_RECORD = re.compile(r"^\s*-\s*(?P<id>(?:USER|FACT|OBS|HYP)-[A-Za-z0-9_-]+):", re.IGNORECASE)
SECTION = re.compile(r"^#{1,3}\s+")
STATUS = re.compile(r"^\*\*Status:\*\*\s*(?P<value>\S.*?)\s*$", re.IGNORECASE)
SOURCE = re.compile(r"^\*\*Source:\*\*\s*(?P<value>\S.*?)\s*$", re.IGNORECASE)
BLOCKING_QUESTION = re.compile(r"^\s*(?:(?:[-*+]|\d+[.)])\s*)?\[\s\]\s*Q-[A-Za-z0-9_-]+\s*:|^#{1,6}\s+Q-[A-Za-z0-9_-]+\s*:", re.IGNORECASE)
RENAMED_SECTION = re.compile(r"^## RENAMED Requirements\s*$", re.IGNORECASE)
RENAME_FROM = re.compile(r"^\s*-\s*FROM:\s*", re.IGNORECASE)
RENAME_TO = re.compile(r"^\s*-\s*TO:\s*", re.IGNORECASE)
REVIEW_CONTRACT = "<!-- openspec-review-contract:v1 -->"
REVIEW_MARKER = re.compile(r"<!--\s*openspec-review:(?P<kind>wave|final)\s*-->", re.IGNORECASE)
WAVE_SECTION = re.compile(
    r"^##\s+.*?<!--\s*openspec-wave:(?P<id>[A-Za-z0-9_-]+)\s*-->.*$", re.IGNORECASE
)
TASK_CHECKBOX = re.compile(r"^\s*-\s*\[(?P<state>[ xX])\]\s+")
SCHEMA_NAME = re.compile(r"(?m)^\s*schema\s*:\s*(?P<name>[A-Za-z0-9_-]+)\s*$", re.IGNORECASE)
REVIEW_MODE = re.compile(r"(?m)^\s*review_contract\s*:\s*(?P<mode>[A-Za-z0-9_-]+)\s*$", re.IGNORECASE)
SKIP_SPECS = re.compile(r"(?m)^\s*skip_specs\s*:\s*true\s*$", re.IGNORECASE)
SKIP_SPECS_MARKER = "<!-- openspec-skip-specs-contract:v1 -->"
SKIP_BEHAVIOR_NONE = re.compile(r"(?m)^\*\*Behavior delta:\*\*\s*none\s*$", re.IGNORECASE)
SKIP_CONTRACT_NONE = re.compile(r"(?m)^\*\*Contract/data/security delta:\*\*\s*none\s*$", re.IGNORECASE)
FINAL_ATTESTATION = re.compile(
    r"Coverage:\s*(?P<coverage>[^;]+);\s*Requirements:\s*(?P<requirements>[^;]+);\s*"
    r"Exclusions:\s*(?P<exclusions>[^;]+);\s*Reviewer:\s*(?P<reviewer>.+?)\s*$",
    re.IGNORECASE,
)


def requirement_blocks(text: str):
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = REQUIREMENT.match(lines[index])
        if not match:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not SECTION.match(lines[end]):
            end += 1
        yield index + 1, match.group("name"), lines[index + 1 : end]
        index = end


def decision_blocks(text: str):
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = DECISION.match(lines[index])
        if not match:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not SECTION.match(lines[end]):
            end += 1
        yield index + 1, match.group("id").upper(), match.group("name"), lines[index + 1 : end]
        index = end


def noncanonical_decision_headings(text: str):
    in_decisions = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            in_decisions = bool(re.match(r"^## Decisions\s*$", line, re.IGNORECASE))
            continue
        if in_decisions and line.startswith("### ") and not DECISION.match(line):
            yield line_number, line[4:].strip()


def renamed_sections(text: str):
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not RENAMED_SECTION.match(line):
            continue
        end = index + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        yield index + 1, lines[index + 1 : end]


def extract_metadata(block: list[str]):
    status_match = next((match for line in block if (match := STATUS.match(line.strip()))), None)
    source_match = next((match for line in block if (match := SOURCE.match(line.strip()))), None)
    return status_match, source_match


def repository_root(change_dir: Path) -> Path:
    for candidate in (change_dir, *change_dir.parents):
        if candidate.name.lower() == "changes" and candidate.parent.name.lower() == "openspec":
            return candidate.parent.parent
    return change_dir


def validate_source(
    value: str,
    *,
    evidence_ids: set[str],
    decisions: dict[str, tuple[str, str | None, str, str]],
    repo_root: Path,
    allow_decision: bool = True,
) -> str | None:
    source = value.strip()
    prefix, separator, reference = source.partition(":")
    if not separator or not reference.strip():
        return "unsupported Source"
    prefix = prefix.lower()
    reference = reference.strip()

    if prefix == "user":
        evidence_id = reference.upper()
        if not evidence_id.startswith("USER-") or evidence_id not in evidence_ids:
            return f"Source references missing user evidence '{reference}'"
        return None

    if prefix == "decision":
        decision_id = reference.upper()
        if not allow_decision or not re.fullmatch(r"DEC-[A-Z0-9_-]+", decision_id):
            return f"unsupported decision Source '{reference}'"
        decision = decisions.get(decision_id)
        if decision is None:
            return f"Source references missing decision '{decision_id}'"
        if decision[0] != "accepted":
            return f"Source references unaccepted decision '{decision_id}'"
        return None

    if prefix == "external":
        if not re.match(r"^https?://\S+$", reference, re.IGNORECASE):
            return "external Source must be an HTTP(S) URL"
        return None

    if prefix == "repo":
        path_text, line_separator, line_text = reference.rpartition(":")
        if not line_separator or not path_text or not line_text.isdigit() or int(line_text) < 1:
            return "repo Source must use repo:<path>:<positive-line>"
        source_path = Path(path_text)
        if not source_path.is_absolute():
            source_path = repo_root / source_path
        source_path = source_path.resolve()
        try:
            source_path.relative_to(repo_root.resolve())
        except ValueError:
            return f"repo Source escapes repository: {path_text}"
        if not source_path.is_file():
            return f"repo Source file not found: {path_text}"
        try:
            line_count = len(source_path.read_text(encoding="utf-8-sig").splitlines())
        except (OSError, UnicodeError) as error:
            return f"repo Source cannot be read: {path_text} ({error})"
        if int(line_text) > line_count:
            return f"repo Source line {line_text} exceeds {path_text} ({line_count} lines)"
        return None

    return "unsupported Source"


def split_sources(value: str) -> list[str]:
    """Return every authority token from a comma-separated Source field."""
    return [source.strip() for source in value.split(",") if source.strip()]


def traceability_contract(change_dir: Path) -> tuple[list[str], list[tuple[str, str, str, str]]]:
    tasks = change_dir / 'tasks.md'
    if not tasks.is_file():
        return [], []
    tasks_text = tasks.read_text(encoding='utf-8-sig')
    if TRACE_CONTRACT_V3 not in tasks_text:
        return [], []
    errors: list[str] = []
    metadata_path = change_dir / '.openspec.yaml'
    metadata_text = metadata_path.read_text(encoding='utf-8-sig') if metadata_path.is_file() else ''
    skip_specs = SKIP_SPECS.search(metadata_text) is not None
    requirements: dict[str, tuple[str, str]] = {}
    spec_root = change_dir / 'specs'
    spec_paths = sorted(spec_root.rglob('*.md')) if spec_root.is_dir() else []
    for path in spec_paths:
        relative = path.relative_to(change_dir)
        text = path.read_text(encoding='utf-8-sig')
        for line_number, name, block in requirement_blocks(text):
            metadata = []
            for line in block:
                if line.startswith('#### '):
                    break
                metadata.append(line)
            status, source = extract_metadata(metadata)
            if status is None or status.group('value').strip().lower() != 'accepted':
                continue
            id_matches = [match for line in metadata if (match := REQUIREMENT_ID.match(line.strip()))]
            if len(id_matches) != 1:
                errors.append(f'{relative}:{line_number}: v3 accepted requirement {name!r} requires exactly one **ID:** REQ-* field')
                continue
            requirement_id = id_matches[0].group('value').upper()
            if requirement_id in requirements:
                errors.append(f'{relative}:{line_number}: duplicate requirement id {requirement_id!r}')
                continue
            decision_ids = []
            if source:
                for item in split_sources(source.group('value')):
                    prefix, separator, value = item.partition(':')
                    if separator and prefix.strip().lower() == 'decision':
                        decision_ids.append(value.strip().upper())
            requirements[requirement_id] = (name, ','.join(decision_ids) or 'none')

        for line_number, block in renamed_sections(text):
            from_indexes = [index for index, line in enumerate(block) if RENAME_FROM.match(line)]
            to_indexes = [index for index, line in enumerate(block) if RENAME_TO.match(line)]
            if not from_indexes and not to_indexes:
                continue
            first_pair = min(from_indexes + to_indexes)
            metadata = block[:first_pair]
            status, source = extract_metadata(metadata)
            if status is None or status.group('value').strip().lower() != 'accepted':
                continue
            id_matches = [match for line in metadata if (match := REQUIREMENT_ID.match(line.strip()))]
            if len(id_matches) != 1:
                errors.append(f'{relative}:{line_number}: v3 accepted RENAMED section requires exactly one **ID:** REQ-* field')
                continue
            requirement_id = id_matches[0].group('value').upper()
            if requirement_id in requirements:
                errors.append(f'{relative}:{line_number}: duplicate requirement id {requirement_id!r}')
                continue
            decision_ids = []
            if source:
                for item in split_sources(source.group('value')):
                    prefix, separator, value = item.partition(':')
                    if separator and prefix.strip().lower() == 'decision':
                        decision_ids.append(value.strip().upper())
            requirements[requirement_id] = ('RENAMED requirements', ','.join(decision_ids) or 'none')

    mappings: dict[str, list[tuple[str, str]]] = {key: [] for key in requirements}
    forbidden = {'', '-', 'tbd', 'unknown', 'none', 'n/a', 'na', 'todo'}
    for line_number, line in enumerate(tasks_text.splitlines(), start=1):
        trace = TRACE_MARKER.search(line)
        if trace is None:
            if TASK_CHECKBOX.match(line) and not REVIEW_MARKER.search(line) and not UI_REVIEW.search(line):
                errors.append(f'tasks.md:{line_number}: v3 implementation task requires an openspec-trace marker')
            continue
        if TASK_CHECKBOX.match(line) is None:
            errors.append(f'tasks.md:{line_number}: openspec-trace marker must be on a task checkbox')
            continue
        ids = [value.strip().upper() for value in trace.group('requirements').split(',') if value.strip()]
        verification = trace.group('verification').strip()
        no_spec_trace = ids == ['NONE']
        if not ids:
            errors.append(f'tasks.md:{line_number}: trace marker requires at least one REQ-* id, or none for explicit skip_specs')
        elif no_spec_trace and not skip_specs:
            errors.append(f'tasks.md:{line_number}: requirements=none requires explicit skip_specs: true')
        elif skip_specs and not no_spec_trace:
            errors.append(f'tasks.md:{line_number}: skip_specs task must use requirements=none')
        if verification.lower() in forbidden or '<' in verification or '>' in verification:
            errors.append(f'tasks.md:{line_number}: trace marker requires concrete planned verification')
        task_text = TRACE_MARKER.sub('', line).strip()
        for requirement_id in ids:
            if requirement_id == 'NONE' and skip_specs:
                continue
            if not re.fullmatch(r'REQ-[A-Z0-9_-]+', requirement_id):
                errors.append(f'tasks.md:{line_number}: invalid requirement id {requirement_id!r} in trace marker')
            elif requirement_id not in requirements:
                errors.append(f'tasks.md:{line_number}: trace references missing accepted requirement {requirement_id!r}')
            else:
                mappings[requirement_id].append((task_text, verification))

    rows: list[tuple[str, str, str, str]] = []
    for requirement_id, (name, decisions) in requirements.items():
        linked = mappings[requirement_id]
        if not linked:
            errors.append(f'tasks.md: accepted requirement {requirement_id!r} has no traced implementation task with planned verification')
            continue
        rows.append((
            requirement_id,
            decisions,
            ' | '.join(item[0] for item in linked),
            ' | '.join(item[1] for item in linked),
        ))
    if errors:
        errors.append('traceability gate invocation: resolve the active openspec-workflow skill root, then run python <openspec-workflow-skill-root>/scripts/validate_change.py --repo <repo> --change <change-name>')
    return errors, rows


def format_traceability_matrix(change_dir: Path) -> str:
    _, rows = traceability_contract(change_dir)
    if not rows:
        return ''
    output = [
        'OpenSpec traceability matrix:',
        '| Requirement | Decision | Task | Planned verification |',
        '|---|---|---|---|',
    ]
    for requirement, decision, task, verification in rows:
        values = [value.replace('|', '\\|') for value in (requirement, decision, task, verification)]
        output.append('| ' + ' | '.join(values) + ' |')
    return '\n'.join(output)


def validate_sources(
    value: str,
    *,
    evidence_ids: set[str],
    decisions: dict[str, tuple[str, str | None, str, str]],
    repo_root: Path,
    allow_decision: bool = True,
) -> list[tuple[str, str]]:
    sources = split_sources(value)
    if not sources:
        return [(value, "unsupported Source")]
    errors: list[tuple[str, str]] = []
    for source in sources:
        error = validate_source(
            source,
            evidence_ids=evidence_ids,
            decisions=decisions,
            repo_root=repo_root,
            allow_decision=allow_decision,
        )
        if error:
            errors.append((source, error))
    return errors


def validate_review_contract(change_dir: Path) -> list[str]:
    tasks = change_dir / "tasks.md"
    if not tasks.is_file():
        return []
    metadata = change_dir / ".openspec.yaml"
    metadata_text = metadata.read_text(encoding="utf-8") if metadata.is_file() else ""
    schema_match = SCHEMA_NAME.search(metadata_text)
    schema = schema_match.group("name").lower() if schema_match else ""
    mode_match = REVIEW_MODE.search(metadata_text)
    review_mode = mode_match.group("mode").lower() if mode_match else ""
    text = tasks.read_text(encoding="utf-8")
    errors: list[str] = []
    lines = text.splitlines()
    contract_v1 = REVIEW_CONTRACT in text
    contract_v2 = UI_CONTRACT_V2 in text
    contract_v3 = TRACE_CONTRACT_V3 in text
    if sum((contract_v1, contract_v2, contract_v3)) > 1:
        errors.append('tasks.md: review contract must use exactly one version marker')
    if contract_v2 or contract_v3:
        ui_modes = [match.group('mode').lower() for match in UI_MODE.finditer(text)]
        ui_reviews = [(number, line) for number, line in enumerate(lines, 1) if UI_REVIEW.search(line)]
        proposal = change_dir / 'proposal.md'
        proposal_text = proposal.read_text(encoding='utf-8-sig') if proposal.is_file() else ''
        section = UI_SECTION.search(proposal_text)
        fields = {}
        if section:
            for candidate in section.group('body').splitlines():
                if field := UI_FIELD.match(candidate.strip()):
                    fields[field.group('name').lower()] = field.group('value').strip()
        proposal_mode = fields.get('mode', '').lower()
        if len(ui_modes) != 1:
            errors.append('tasks.md: v2 review contract requires exactly one UI contract mode')
        elif proposal_mode not in {'none', 'material'}:
            errors.append('proposal.md: v2 review contract requires UI Contract Mode none or material')
        elif ui_modes[0] != proposal_mode:
            errors.append('tasks.md: UI contract mode must match proposal.md')
        elif proposal_mode == 'material':
            required = {'artifact', 'authority', 'theme', 'viewports', 'states', 'data'}
            values = [fields.get(key, '') for key in required]
            if any(not value or value.lower() in {'-', 'tbd', 'unknown', 'none', 'n/a', 'na', 'todo'} or '<' in value or '>' in value for value in values):
                errors.append('proposal.md: material UI contract requires concrete Artifact, Authority, Theme, Viewports, States, and Data')
            if len(ui_reviews) != 1:
                errors.append('tasks.md: material UI contract requires exactly one UI review checkpoint')
        elif ui_reviews:
            errors.append('tasks.md: UI review checkpoint is not allowed for UI contract none')
        for line_number, line in ui_reviews:
            checkbox = TASK_CHECKBOX.match(line)
            if checkbox is None:
                errors.append(f'tasks.md:{line_number}: UI review must be a task checkbox')
            elif checkbox.group('state').lower() == 'x':
                field_names = ('Artifact:', 'Theme:', 'Viewports:', 'States:', 'Data:', 'Evidence:', 'Comparison:', 'Discrepancies:', 'Reviewer:')
                attestation_text = UI_REVIEW.split(line, maxsplit=1)[1]
                chunks = {part.split(':', 1)[0].strip().lower(): part.split(':', 1)[1].strip().rstrip('.') for part in attestation_text.split(';') if ':' in part}
                required_chunks = {name.rstrip(':').lower() for name in field_names}
                invalid = (
                    any(name.lower() not in line.lower() for name in field_names)
                    or '<' in line or '>' in line
                    or any(
                        not chunks.get(key)
                        or chunks.get(key, '').lower() in ({'-', 'tbd', 'unknown', 'n/a', 'na', 'todo'} if key == 'discrepancies' else {'-', 'tbd', 'unknown', 'none', 'n/a', 'na', 'todo'})
                        for key in required_chunks
                    )
                )
                if invalid:
                    errors.append(f'tasks.md:{line_number}: completed UI checkpoint requires concrete visual attestation')

    if not contract_v1 and not contract_v2 and not contract_v3:
        if review_mode == "legacy":
            return []
        if schema in {"evidence-core", "evidence-heavy"}:
            return [
                "tasks.md: evidence-core/evidence-heavy requires the review contract marker; "
                "pre-contract changes must declare 'review_contract: legacy' in .openspec.yaml"
            ]
        return []
    if review_mode == "legacy":
        errors.append("tasks.md: review_contract legacy must not be combined with a review marker")
    active_contract = TRACE_CONTRACT_V3 if contract_v3 else UI_CONTRACT_V2 if contract_v2 else REVIEW_CONTRACT
    if text.count(active_contract) != 1:
        errors.append("tasks.md: review contract marker must appear exactly once")

    checkboxes: list[tuple[int, bool]] = []
    markers: list[tuple[int, str, bool]] = []
    wave_sections: list[tuple[int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        if wave_section := WAVE_SECTION.match(line):
            wave_sections.append((line_number, wave_section.group("id").lower()))
        checkbox = TASK_CHECKBOX.match(line)
        if checkbox:
            checkboxes.append((line_number, checkbox.group("state").lower() == "x"))
        marker = REVIEW_MARKER.search(line)
        if marker:
            if checkbox is None:
                errors.append(f"tasks.md:{line_number}: review marker must be on a task checkbox")
                continue
            markers.append((line_number, marker.group("kind").lower(), checkbox.group("state").lower() == "x"))

    waves = [marker for marker in markers if marker[1] == "wave"]
    finals = [marker for marker in markers if marker[1] == "final"]
    if schema == "evidence-core":
        if waves or wave_sections:
            errors.append("tasks.md: evidence-core review contract must not contain wave checkpoints")
        if len(finals) != 1:
            errors.append("tasks.md: evidence-core review contract requires exactly one final checkpoint")
    elif schema == "evidence-heavy":
        if not wave_sections:
            errors.append("tasks.md: evidence-heavy review contract requires at least one explicit openspec-wave section")
        if len(finals) != 1:
            errors.append("tasks.md: evidence-heavy review contract requires exactly one final checkpoint")
    else:
        errors.append("tasks.md: review contract requires evidence-core or evidence-heavy schema")

    if len(finals) == 1:
        final_line, _, final_done = finals[0]
        if waves and final_line < max(line for line, _, _ in waves):
            errors.append(f"tasks.md:{final_line}: final checkpoint must follow every wave checkpoint")
        later_checkboxes = [line for line, _ in checkboxes if line > final_line]
        if later_checkboxes:
            errors.append(f"tasks.md:{final_line}: final checkpoint must be the last task checkbox")
        if final_done and any(not done for line, done in checkboxes if line < final_line):
            errors.append(f"tasks.md:{final_line}: completed final checkpoint has earlier incomplete tasks")
        if final_done:
            final_text = lines[final_line - 1]
            attestation = FINAL_ATTESTATION.search(final_text)
            invalid = attestation is None
            if attestation is not None:
                values = {key: value.strip().rstrip(".").strip() for key, value in attestation.groupdict().items()}
                forbidden = {"", "-", "tbd", "unknown", "n/a", "na", "todo"}
                invalid = (
                    values["coverage"].lower() != "full pending diff"
                    or values["requirements"].lower() in forbidden | {"none"}
                    or values["exclusions"].lower() in forbidden
                    or values["reviewer"].lower() in forbidden | {"none"}
                    or any("<" in value or ">" in value for value in values.values())
                )
            if invalid:
                errors.append(
                    f"tasks.md:{final_line}: completed final checkpoint requires concrete "
                    "Coverage, Requirements, Exclusions, and Reviewer attestation"
                )

    if schema == "evidence-heavy" and wave_sections and len(finals) == 1:
        ids = [wave_id for _, wave_id in wave_sections]
        if len(ids) != len(set(ids)):
            errors.append("tasks.md: openspec-wave ids must be unique")
        final_line = finals[0][0]
        covered_task_lines: set[int] = set()
        for index, (start, wave_id) in enumerate(wave_sections):
            end = wave_sections[index + 1][0] if index + 1 < len(wave_sections) else final_line
            segment_tasks = [(line, done) for line, done in checkboxes if start < line < end]
            segment_markers = [marker for marker in markers if start < marker[0] < end and marker[1] == "wave"]
            normal_tasks = [line for line, _ in segment_tasks if all(line != marker[0] for marker in segment_markers)]
            covered_task_lines.update(line for line, _ in segment_tasks)
            if not normal_tasks:
                errors.append(f"tasks.md:{start}: wave '{wave_id}' requires at least one implementation task")
            if contract_v3:
                if len(segment_markers) > 1:
                    errors.append(f"tasks.md:{start}: wave '{wave_id}' allows at most one wave checkpoint")
            elif len(segment_markers) != 1:
                errors.append(f"tasks.md:{start}: wave '{wave_id}' requires exactly one wave checkpoint")
            if len(segment_markers) == 1:
                marker_line, _, marker_done = segment_markers[0]
                if segment_tasks and marker_line != segment_tasks[-1][0]:
                    errors.append(f"tasks.md:{marker_line}: wave checkpoint must be the last task in wave '{wave_id}'")
                if marker_done and any(not done for line, done in segment_tasks if line < marker_line):
                    errors.append(
                        f"tasks.md:{marker_line}: completed wave checkpoint has incomplete tasks in its wave"
                    )
        uncovered = [line for line, _ in checkboxes if line < final_line and line not in covered_task_lines]
        if uncovered:
            errors.append(f"tasks.md:{uncovered[0]}: task is outside an explicit openspec-wave section")

    return errors


def validate_change(change_dir: Path) -> list[str]:
    errors: list[str] = []
    if not change_dir.is_dir():
        return [f"change directory not found: {change_dir}"]
    markdown_files = sorted(change_dir.rglob("*.md"))
    if not markdown_files:
        return [f"no Markdown artifacts found: {change_dir}"]

    proposal = change_dir / "proposal.md"
    evidence_ids: set[str] = set()
    evidence_locations: dict[str, int] = {}
    if proposal.is_file():
        for line_number, line in enumerate(proposal.read_text(encoding="utf-8").splitlines(), start=1):
            if match := EVIDENCE_RECORD.match(line):
                evidence_id = match.group("id").upper()
                if evidence_id in evidence_locations:
                    errors.append(
                        f"proposal.md:{line_number}: duplicate evidence id '{evidence_id}'; "
                        f"first defined at proposal.md:{evidence_locations[evidence_id]}"
                    )
                else:
                    evidence_ids.add(evidence_id)
                    evidence_locations[evidence_id] = line_number

    repo_root = repository_root(change_dir)
    decisions: dict[str, tuple[str, str | None, str, str]] = {}
    decision_locations: dict[str, str] = {}
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(change_dir)
        for line_number, heading in noncanonical_decision_headings(text):
            errors.append(
                f"{relative}:{line_number}: noncanonical decision heading '{heading}'; "
                "use '### DEC-<id>: <title>' with Status and Source"
            )
        for line_number, decision_id, name, block in decision_blocks(text):
            status_match, source_match = extract_metadata(block)
            status = status_match.group("value").strip().lower() if status_match else ""
            source = source_match.group("value").strip() if source_match else None
            body = "\n".join(block).strip()
            current = (status, source, name.strip(), body)
            if decision_id in decisions:
                errors.append(
                    f"{relative}:{line_number}: duplicate decision '{decision_id}'; first defined at {decision_locations[decision_id]}"
                )
            else:
                decisions[decision_id] = current
                decision_locations[decision_id] = f"{relative}:{line_number}"
            if status_match is None:
                errors.append(f"{relative}:{line_number}: decision '{decision_id}' has no Status")
            elif status not in {"accepted", "proposed"}:
                errors.append(f"{relative}:{line_number}: decision '{decision_id}' has invalid Status")
            elif status != "accepted":
                errors.append(f"{relative}:{line_number}: decision '{decision_id}' is not accepted")
            if source_match is None:
                errors.append(f"{relative}:{line_number}: decision '{decision_id}' has no Source")

    for decision_id, (status, source, _, _) in decisions.items():
        if source is None:
            continue
        source_errors = validate_sources(
            source,
            evidence_ids=evidence_ids,
            decisions=decisions,
            repo_root=repo_root,
            allow_decision=False,
        )
        for _, source_error in source_errors:
            errors.append(f"{decision_locations[decision_id]}: decision '{decision_id}' {source_error}")
        if status == "accepted" and any(
            not item.lower().startswith("user:") for item in split_sources(source)
        ):
            errors.append(
                f"{decision_locations[decision_id]}: accepted decision '{decision_id}' "
                "must use explicit user:USER-* authority"
            )

    normative_count = 0
    for path in markdown_files:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(change_dir)
        for line_number, line in enumerate(text.splitlines(), start=1):
            if BLOCKING_QUESTION.match(line):
                errors.append(f"{relative}:{line_number}: unresolved blocking question")
        for line_number, name, block in requirement_blocks(text):
            normative_count += 1
            metadata_lines = []
            for line in block:
                if line.startswith("#### "):
                    break
                metadata_lines.append(line)
            status_match, source_match = extract_metadata(metadata_lines)
            if status_match is None:
                errors.append(f"{relative}:{line_number}: requirement '{name}' has no Status")
            elif status_match.group("value").strip().lower() != "accepted":
                errors.append(f"{relative}:{line_number}: requirement '{name}' is not accepted")
            if source_match is None:
                errors.append(f"{relative}:{line_number}: requirement '{name}' has no Source")
            else:
                source_value = source_match.group("value")
                source_errors = validate_sources(
                    source_value,
                    evidence_ids=evidence_ids,
                    decisions=decisions,
                    repo_root=repo_root,
                )
                for _, source_error in source_errors:
                    errors.append(f"{relative}:{line_number}: requirement '{name}' {source_error}")
                if any(
                    item.partition(":")[0].strip().lower() not in {"user", "decision"}
                    for item in split_sources(source_value)
                ):
                    errors.append(
                        f"{relative}:{line_number}: requirement '{name}' Source is observational, "
                        "not explicit requirement authority"
                    )

        for line_number, block in renamed_sections(text):
            from_indexes = [index for index, line in enumerate(block) if RENAME_FROM.match(line)]
            to_indexes = [index for index, line in enumerate(block) if RENAME_TO.match(line)]
            if not from_indexes and not to_indexes:
                continue
            normative_count += 1
            first_pair = min(from_indexes + to_indexes)
            metadata_lines = block[:first_pair]
            status_match, source_match = extract_metadata(metadata_lines)
            if status_match is None:
                errors.append(f"{relative}:{line_number}: RENAMED section has no Status")
            elif status_match.group("value").strip().lower() != "accepted":
                errors.append(f"{relative}:{line_number}: RENAMED section is not accepted")
            if source_match is None:
                errors.append(f"{relative}:{line_number}: RENAMED section has no Source")
            else:
                source_value = source_match.group("value")
                source_errors = validate_sources(
                    source_value,
                    evidence_ids=evidence_ids,
                    decisions=decisions,
                    repo_root=repo_root,
                )
                for _, source_error in source_errors:
                    errors.append(f"{relative}:{line_number}: RENAMED section {source_error}")
                if any(
                    item.partition(":")[0].strip().lower() not in {"user", "decision"}
                    for item in split_sources(source_value)
                ):
                    errors.append(
                        f"{relative}:{line_number}: RENAMED section Source is observational, "
                        "not explicit requirement authority"
                    )

    metadata = change_dir / ".openspec.yaml"
    skip_specs = metadata.is_file() and re.search(
        r"(?m)^\s*skip_specs\s*:\s*true\s*$", metadata.read_text(encoding="utf-8"), re.IGNORECASE
    )
    if skip_specs:
        if not proposal.is_file():
            errors.append("skip_specs: true requires proposal.md with the no-behavior-delta marker")
        else:
            proposal_text = proposal.read_text(encoding="utf-8-sig")
            if SKIP_SPECS_MARKER not in proposal_text:
                errors.append(
                    "proposal.md: skip_specs: true requires "
                    "<!-- openspec-skip-specs-contract:v1 -->"
                )
            if not SKIP_BEHAVIOR_NONE.search(proposal_text):
                errors.append("proposal.md: skip_specs contract requires **Behavior delta:** none")
            if not SKIP_CONTRACT_NONE.search(proposal_text):
                errors.append(
                    "proposal.md: skip_specs contract requires "
                    "**Contract/data/security delta:** none"
                )
    spec_dir = change_dir / "specs"
    spec_files = list(spec_dir.rglob("*.md")) if spec_dir.is_dir() else []
    if spec_files and normative_count == 0:
        errors.append("spec artifacts contain no Requirement or RENAMED blocks")
    if not spec_files and not skip_specs:
        errors.append("no spec artifacts and skip_specs is not true")
    traceability_errors, _ = traceability_contract(change_dir)
    errors.extend(traceability_errors)
    errors.extend(validate_review_contract(change_dir))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("change_dir", type=Path)
    args = parser.parse_args(argv)
    errors = validate_change(args.change_dir.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print("OpenSpec requirement evidence: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
