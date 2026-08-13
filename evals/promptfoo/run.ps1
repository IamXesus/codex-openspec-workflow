param(
    [string]$FilterPattern,
    [ValidateRange(1, 20)]
    [int]$Repeat = 3
)

$ErrorActionPreference = 'Stop'
$evalRoot = $PSScriptRoot

if (-not $env:CODEX_PATH) {
    $command = Get-Command codex.exe -ErrorAction SilentlyContinue
    if ($command) {
        $env:CODEX_PATH = $command.Source
    } else {
        $shim = Get-Command codex.cmd -ErrorAction SilentlyContinue
        if ($shim) {
            $packageRoot = Join-Path (Split-Path -Parent $shim.Source) 'node_modules\@openai\codex'
            $binaries = @(Get-ChildItem -LiteralPath $packageRoot -Filter codex.exe -File -Recurse -ErrorAction SilentlyContinue)
            if ($binaries.Count -eq 1) {
                $env:CODEX_PATH = $binaries[0].FullName
            }
        }
    }
    if (-not $env:CODEX_PATH) {
        throw 'Codex native binary was not found. Set CODEX_PATH to the absolute codex.exe path.'
    }
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $evalRoot)
$stage = Join-Path ([IO.Path]::GetTempPath()) ('openspec-workflow-eval-' + [guid]::NewGuid().ToString('N'))
$workspace = Join-Path $stage 'workspace'
try {
    New-Item -ItemType Directory -Path (Join-Path $workspace '.agents\skills') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $evalRoot 'workspace\AGENTS.md') -Destination (Join-Path $workspace 'AGENTS.md') -Force
    foreach ($skill in 'openspec-workflow', 'code-reviewer', 'webapp-testing', 'coding-guardrails') {
        Copy-Item -LiteralPath (Join-Path $repoRoot "skills\$skill") -Destination (Join-Path $workspace '.agents\skills') -Recurse -Force
    }
    $env:WORKFLOW_EVAL_WORKSPACE = $workspace
    $arguments = @(
        '--no-install', 'promptfoo', 'eval',
        '-c', (Join-Path $evalRoot 'promptfooconfig.yaml'),
        '--repeat', $Repeat,
        '--no-cache',
        '--output', (Join-Path $evalRoot 'results\latest.json')
    )
    if ($FilterPattern) {
        $arguments += @('--filter-pattern', $FilterPattern)
    }
    & npx.cmd @arguments
    $exitCode = $LASTEXITCODE
} finally {
    if (Test-Path -LiteralPath $stage) {
        $resolved = (Resolve-Path -LiteralPath $stage).Path
        if (-not $resolved.StartsWith([IO.Path]::GetTempPath(), [StringComparison]::OrdinalIgnoreCase)) {
            throw "Unsafe eval cleanup target: $resolved"
        }
        Remove-Item -LiteralPath $resolved -Recurse -Force
    }
}
exit $exitCode
