## Purpose

Make the central workflow installable and verifiable across ordinary Codex and Orca-created workspaces, including nested validator scripts, without relying on one transient account-specific home directory.

## ADDED Requirements

### Requirement: Portable target selection
**ID:** REQ-PAI-001
**Status:** accepted
**Source:** decision:DEC-003
The installer SHALL support an Orca-compatible shared installation mode discoverable by newly created Orca Workspace agents and SHALL retain explicit caller overrides for agent-skill and OpenSpec-schema roots. Target resolution MUST NOT depend on embedding the currently observed account-scoped absolute path.

#### Scenario: Shared Orca installation is selected
- **WHEN** an operator selects the Orca-compatible shared installation mode without custom roots
- **THEN** the installer resolves stable agent-skill and schema targets that a newly created Orca Workspace can discover

#### Scenario: Explicit roots are supplied
- **WHEN** an operator supplies explicit agent-skill and schema roots
- **THEN** the installer uses those exact roots and reports them without also writing to an implicit account-specific target

### Requirement: Complete package-owned installation
**ID:** REQ-PAI-002
**Status:** accepted
**Source:** decision:DEC-001, decision:DEC-003
Installation SHALL copy every selected package-owned schema, template, skill resource, nested validator script, policy asset required by the install contract, and installed-state metadata while preserving unrelated destination files.

#### Scenario: Nested validator is installed
- **WHEN** a workflow skill contains a validator below its `scripts` directory
- **THEN** installation places that script at the corresponding relative path under the selected skill root

#### Scenario: Destination contains unrelated files
- **WHEN** the selected destination already contains files not owned by the central package
- **THEN** installation preserves those files and changes only package-owned targets

### Requirement: Fail-closed installation check
**ID:** REQ-PAI-003
**Status:** accepted
**Source:** decision:DEC-002, decision:DEC-003
The check operation SHALL fail when any required installed schema, template, skill resource, nested script, policy asset, or installed-state field is missing or differs from the inspected central package, and SHALL identify the affected target and relative item.

#### Scenario: Nested script is unavailable
- **WHEN** a required validator script is absent from the selected installed skill root
- **THEN** the check fails and identifies that missing relative script instead of passing on skill-directory existence alone

#### Scenario: Installed validator drifted
- **WHEN** a validator exists but its content differs from the canonical package
- **THEN** the check fails and identifies the drifted installed file

### Requirement: Fresh Orca Workspace execution smoke
**ID:** REQ-PAI-004
**Status:** accepted
**Source:** decision:DEC-003
The distribution SHALL provide a reproducible smoke procedure that creates or uses a disposable fresh Orca Workspace agent, resolves the centrally installed workflow through the runtime-visible skill root, and executes a required nested validator from that resolved root before Orca compatibility is declared verified.

#### Scenario: Fresh Workspace resolves and runs the validator
- **WHEN** the package is installed into the selected Orca-compatible target and the smoke launches a fresh disposable Workspace agent
- **THEN** that agent resolves the workflow skill and successfully invokes its nested validator without a hard-coded account path

#### Scenario: Fresh Workspace cannot resolve scripts
- **WHEN** the disposable Workspace agent cannot discover the skill or execute the nested validator
- **THEN** the smoke fails, preserves diagnostic paths, and the change is not reported as Orca-compatible
