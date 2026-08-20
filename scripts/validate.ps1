$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONUTF8 = '1'

Push-Location (Join-Path $repoRoot 'scripts')
try {
    python -m unittest -v test_workflow_package.py test_shared_policy.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$skillValidator = Join-Path $env:USERPROFILE '.codex\skills\.system\skill-creator\scripts\quick_validate.py'
if (Test-Path -LiteralPath $skillValidator) {
    foreach ($skill in 'openspec-workflow', 'code-reviewer', 'webapp-testing', 'coding-guardrails', 'architecture-review') {
        python $skillValidator (Join-Path $repoRoot "skills\$skill")
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

Push-Location (Join-Path $repoRoot 'skills\openspec-workflow\scripts')
try {
    python -m unittest -v test_validate_requirements.py test_validate_change.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Push-Location (Join-Path $repoRoot 'skills\architecture-review\scripts')
try {
    python -m unittest -v test_validate_openspec_architecture.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

$schemaStage = Join-Path ([IO.Path]::GetTempPath()) ('openspec-schema-validation-' + [guid]::NewGuid().ToString('N'))
$previousLocalAppData = $env:LOCALAPPDATA
$previousXdgDataHome = $env:XDG_DATA_HOME
try {
    $env:LOCALAPPDATA = $schemaStage
    $env:XDG_DATA_HOME = $schemaStage
    $stagedSchemaRoot = Join-Path $schemaStage 'openspec\schemas'
    New-Item -ItemType Directory -Path $stagedSchemaRoot -Force | Out-Null
    foreach ($schema in 'evidence-core', 'evidence-heavy') {
        Copy-Item -LiteralPath (Join-Path $repoRoot "openspec\schemas\$schema") -Destination $stagedSchemaRoot -Recurse -Force
        openspec.cmd schema validate $schema
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
} finally {
    $env:LOCALAPPDATA = $previousLocalAppData
    $env:XDG_DATA_HOME = $previousXdgDataHome
    if (Test-Path -LiteralPath $schemaStage) {
        Remove-Item -LiteralPath $schemaStage -Recurse -Force
    }
}

$forbidden = @('C:' + '\Users\' + 'Xesus', 'BEGIN ' + 'PRIVATE KEY', 'Bearer' + ' ', 'api_' + 'key =', 'anonymous' + 'Id')
$textFiles = Get-ChildItem -LiteralPath $repoRoot -File -Recurse | Where-Object {
    $_.Extension -in '.md', '.yaml', '.yml', '.py', '.ps1', '.sh', '.json'
}
foreach ($file in $textFiles) {
    $text = [IO.File]::ReadAllText($file.FullName)
    foreach ($pattern in $forbidden) {
        if ($text.Contains($pattern)) {
            throw "Forbidden portable-package content '$pattern' in $($file.FullName)"
        }
    }
}

Push-Location (Join-Path $repoRoot 'scripts')
try {
    python -c "import workflow_package as package; package.validate_lock_metadata(package.repo_root())"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Output 'Portable workflow validation: PASS'

