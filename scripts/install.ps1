param(
    [ValidateSet('codex', 'omnigent')]
    [string]$Target = 'codex',
    [string]$AgentRoot,
    [string]$OpenSpecSchemaRoot,
    [switch]$DryRun,
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

if (-not $AgentRoot) {
    $AgentRoot = if ($Target -eq 'codex') {
        if ($env:CODEX_HOME) {
            Join-Path $env:CODEX_HOME 'skills'
        } else {
            Join-Path $env:USERPROFILE '.codex\skills'
        }
    } else {
        Join-Path $env:USERPROFILE '.agents\skills'
    }
}

if (-not $OpenSpecSchemaRoot) {
    if ($env:XDG_DATA_HOME) {
        $OpenSpecSchemaRoot = Join-Path $env:XDG_DATA_HOME 'openspec\schemas'
    } elseif ($IsWindows -or $env:OS -eq 'Windows_NT') {
        $OpenSpecSchemaRoot = Join-Path $env:LOCALAPPDATA 'openspec\schemas'
    } else {
        $OpenSpecSchemaRoot = Join-Path $env:HOME '.local/share/openspec/schemas'
    }
}

$copies = @(
    @{ Source = Join-Path $repoRoot 'skills\openspec-workflow'; Destination = Join-Path $AgentRoot 'openspec-workflow' },
    @{ Source = Join-Path $repoRoot 'skills\code-reviewer'; Destination = Join-Path $AgentRoot 'code-reviewer' },
    @{ Source = Join-Path $repoRoot 'skills\webapp-testing'; Destination = Join-Path $AgentRoot 'webapp-testing' },
    @{ Source = Join-Path $repoRoot 'skills\coding-guardrails'; Destination = Join-Path $AgentRoot 'coding-guardrails' },
    @{ Source = Join-Path $repoRoot 'openspec\schemas\evidence-core'; Destination = Join-Path $OpenSpecSchemaRoot 'evidence-core' },
    @{ Source = Join-Path $repoRoot 'openspec\schemas\evidence-heavy'; Destination = Join-Path $OpenSpecSchemaRoot 'evidence-heavy' }
)

foreach ($item in $copies) {
    if (-not (Test-Path -LiteralPath $item.Source)) {
        throw "Package source is missing: $($item.Source)"
    }
    if ($DryRun) {
        Write-Output "COPY $($item.Source) -> $($item.Destination)"
        continue
    }

    $sourceFiles = @(Get-ChildItem -LiteralPath $item.Source -File -Recurse | Where-Object {
        $_.Extension -ne '.pyc' -and $_.FullName -notlike '*\__pycache__\*'
    })

    if ($Check) {
        if (-not (Test-Path -LiteralPath $item.Destination)) {
            throw "Installed destination is missing: $($item.Destination)"
        }
        $sourceRelative = @($sourceFiles | ForEach-Object {
            $_.FullName.Substring($item.Source.Length).TrimStart('\', '/')
        })
        $destinationFiles = @(Get-ChildItem -LiteralPath $item.Destination -File -Recurse | Where-Object {
            $_.Extension -ne '.pyc' -and $_.FullName -notlike '*\__pycache__\*'
        })
        foreach ($destinationFile in $destinationFiles) {
            $relative = $destinationFile.FullName.Substring($item.Destination.Length).TrimStart('\', '/')
            if ($relative -notin $sourceRelative) {
                throw "Installed package contains a stale file: $($destinationFile.FullName)"
            }
        }
        foreach ($sourceFile in $sourceFiles) {
            $relative = $sourceFile.FullName.Substring($item.Source.Length).TrimStart('\', '/')
            $destinationFile = Join-Path $item.Destination $relative
            if (-not (Test-Path -LiteralPath $destinationFile)) {
                throw "Installed file is missing: $destinationFile"
            }
            $sourceHash = (Get-FileHash -LiteralPath $sourceFile.FullName -Algorithm SHA256).Hash
            $destinationHash = (Get-FileHash -LiteralPath $destinationFile -Algorithm SHA256).Hash
            if ($sourceHash -ne $destinationHash) {
                throw "Installed file differs: $destinationFile"
            }
        }
        continue
    }

    New-Item -ItemType Directory -Path $item.Destination -Force | Out-Null
    foreach ($sourceFile in $sourceFiles) {
        $relative = $sourceFile.FullName.Substring($item.Source.Length).TrimStart('\', '/')
        $destinationFile = Join-Path $item.Destination $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $destinationFile) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $destinationFile -Force
    }
}

if ($Check) {
    Write-Output 'Installed package matches canonical files.'
} elseif ($DryRun) {
    Write-Output 'Dry run complete. AGENTS.fragment.md is never merged automatically.'
} else {
    Write-Output "Installed skills into $AgentRoot"
    Write-Output "Installed OpenSpec schemas into $OpenSpecSchemaRoot"
    Write-Output 'Review and merge policy\AGENTS.fragment.md manually; existing policy was not changed.'
}
