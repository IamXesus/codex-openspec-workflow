## Purpose

Give every coding agent the same feature-first placement guard before creating production files, while allowing each consumer repository to retain its own concrete namespaces, modules, dependency injection, and architecture-test examples.

## ADDED Requirements

### Requirement: Placement is checked before authoring
**ID:** REQ-SCAP-001
**Status:** accepted
**Source:** decision:DEC-004
The reusable workflow SHALL instruct an agent to inspect neighboring feature structure, namespaces or module boundaries, dependency registration, and relevant architecture tests before creating or materially moving a production type, whether the work is routed directly or through OpenSpec.

#### Scenario: Direct code change creates a type
- **WHEN** an agent performs a clear direct change that creates a production type without an OpenSpec package
- **THEN** the central coding guardrail requires the placement inspection before the file is created

#### Scenario: OpenSpec apply creates a type
- **WHEN** an agent applies an accepted OpenSpec change that creates a production type
- **THEN** OpenSpec authoring/apply guidance carries the same placement inspection requirement

### Requirement: Feature and cohesive responsibility drive structure
**ID:** REQ-SCAP-002
**Status:** accepted
**Source:** decision:DEC-004
Reusable guidance SHALL organize new or materially changed code by feature and cohesive responsibility, MUST NOT require generic `Interfaces` and `Implementations` folders solely by declaration type, and SHALL introduce subfolders only when they express a real responsibility and materially improve navigation.

#### Scenario: Small cohesive feature is readable while flat
- **WHEN** a feature root remains readable and its types share one cohesive responsibility
- **THEN** the guidance permits the root to remain flat rather than requiring a one-file folder or declaration-type split

#### Scenario: Responsibility-specific grouping improves navigation
- **WHEN** commands, models, adapters, storage, processing, or a module-specific boundary form a real cohesive group
- **THEN** the guidance permits a responsibility-named subfolder consistent with the inspected repository

#### Scenario: Generic declaration folders add no boundary
- **WHEN** an interface and implementation would be separated only to satisfy generic folder names
- **THEN** the guidance rejects that split and keeps the internal contract with the cohesive boundary it serves

### Requirement: Placement policy is a narrow ratchet
**ID:** REQ-SCAP-003
**Status:** accepted
**Source:** decision:DEC-004
The shared placement policy SHALL apply to new or materially changed code and MUST NOT authorize incidental movement of existing files, broad namespace or dependency-registration churn, speculative wrappers, or legacy restructuring outside an accepted material architecture change.

#### Scenario: Neighboring legacy area is flat
- **WHEN** a bounded change touches one type in an existing flat or oversized area
- **THEN** the agent follows the narrow accepted change and does not reorganize neighboring legacy files merely to satisfy the new policy

#### Scenario: Material ownership restructure is required
- **WHEN** the intended change moves ownership, changes multiple namespaces or registrations, or decomposes a large responsibility
- **THEN** the workflow routes that restructure through an accepted `evidence-heavy` change and architecture review

### Requirement: Consumer examples remain project-specific
**ID:** REQ-SCAP-004
**Status:** accepted
**Source:** decision:DEC-004
The central package SHALL distribute the general placement policy, while consumer repositories SHALL remain the authority for their concrete feature names, namespaces, folder examples, dependency-registration rules, and architecture-test constraints.

#### Scenario: Consumer supplies concrete examples
- **WHEN** a project documents its own modules and placement examples
- **THEN** agents combine those local examples with the central general guardrail without copying project-specific names into the central package
