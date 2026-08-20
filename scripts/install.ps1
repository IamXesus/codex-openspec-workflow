param(
    [ValidateSet('codex', 'orca', 'omnigent')]
    [string]$Target = 'codex',
    [string]$AgentRoot,
    [Alias('OpenSpecSchemaRoot')]
    [string]$SchemaRoot,
    [string]$ConsumerRepo,
    [string]$BackupRoot,
    [switch]$DryRun,
    [switch]$Check,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'
$engine = Join-Path $PSScriptRoot 'workflow_package.py'
$operation = if ($Check) { 'check' } else { 'install' }
$arguments = @($engine, $operation, '--target', $Target)
if ($AgentRoot) { $arguments += @('--agent-root', $AgentRoot) }
if ($SchemaRoot) { $arguments += @('--schema-root', $SchemaRoot) }
if ($ConsumerRepo) { $arguments += @('--consumer-repo', $ConsumerRepo) }
if ($BackupRoot) { $arguments += @('--backup-root', $BackupRoot) }
if ($DryRun) { $arguments += '--dry-run' }
if ($Json) { $arguments += '--json' }

& python @arguments
exit $LASTEXITCODE
