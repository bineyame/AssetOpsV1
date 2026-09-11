$ErrorActionPreference = "Stop"

# CI architecture guard for the "Stack and module direction" protected seam.
#
# T001 placeholder scope: verify that the expected backend, frontend, and
# simulator roots exist in the modular-monolith shape, and that the two
# dependency directions named by the seam stay banned:
#
#   - no direct UI-to-simulator imports
#   - no simulator-to-product imports/writes
#
# Later slices extend this guard (operator read models vs simulator runtime,
# simulator feature gate). Do not weaken the checks below to make a task pass.

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    $failures = New-Object System.Collections.Generic.List[string]

    function Add-Failure($message) {
        $failures.Add($message) | Out-Null
    }

    # --- Expected module roots -------------------------------------------------

    $requiredDirectories = @(
        "backend",
        "backend/assetops_backend",
        "frontend",
        "frontend/src",
        "simulator",
        "simulator/assetops_simulator"
    )

    foreach ($directory in $requiredDirectories) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            Add-Failure "Missing expected module root: $directory"
        }
    }

    $requiredFiles = @(
        "backend/pyproject.toml",
        "backend/assetops_backend/__init__.py",
        "backend/assetops_backend/main.py",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/src/main.tsx",
        "simulator/assetops_simulator/__init__.py"
    )

    foreach ($file in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            Add-Failure "Missing expected root marker file: $file"
        }
    }

    # --- Declared stack --------------------------------------------------------

    if (Test-Path -LiteralPath "backend/pyproject.toml") {
        $backendProject = Get-Content -LiteralPath "backend/pyproject.toml" -Raw
        if ($backendProject -notmatch "fastapi") {
            Add-Failure "backend/pyproject.toml must declare a FastAPI dependency"
        }
    }

    if (Test-Path -LiteralPath "frontend/package.json") {
        $frontendPackage = Get-Content -LiteralPath "frontend/package.json" -Raw
        foreach ($required in @("react", "typescript")) {
            if ($frontendPackage -notmatch $required) {
                Add-Failure "frontend/package.json must declare $required"
            }
        }
    }

    # --- Banned dependency direction: UI -> simulator --------------------------

    # Matches module specifiers that resolve into the simulator root. The
    # PascalCase `SimulatorLab*` component names are intentionally not matched,
    # so the comparison must stay case-sensitive (-cmatch).
    $uiToSimulator = '(?:from|import|require)\s*\(?\s*["''][^"'']*(?:(?:^|[./])simulator/|assetops[_-]simulator)'

    $frontendSources = @()
    if (Test-Path -LiteralPath "frontend/src" -PathType Container) {
        $frontendSources = Get-ChildItem -LiteralPath "frontend/src" -Recurse -File |
            Where-Object { $_.Extension -in @(".ts", ".tsx", ".js", ".jsx") }
    }

    foreach ($source in $frontendSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            if ($line -cmatch $uiToSimulator) {
                $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                Add-Failure "Banned UI-to-simulator import in ${relative}:${lineNumber}: $($line.Trim())"
            }
        }
    }

    # --- Banned dependency direction: simulator -> product ---------------------

    $simulatorToProduct = '(?:^|\s)(?:from|import)\s+[^\s]*assetops_backend'

    $simulatorSources = @()
    if (Test-Path -LiteralPath "simulator" -PathType Container) {
        $simulatorSources = Get-ChildItem -LiteralPath "simulator" -Recurse -File -Filter "*.py"
    }

    foreach ($source in $simulatorSources) {
        $lineNumber = 0
        foreach ($line in (Get-Content -LiteralPath $source.FullName)) {
            $lineNumber++
            if ($line -match $simulatorToProduct) {
                $relative = Resolve-Path -LiteralPath $source.FullName -Relative
                Add-Failure "Banned simulator-to-product import in ${relative}:${lineNumber}: $($line.Trim())"
            }
        }
    }

    if ($failures.Count -gt 0) {
        Write-Host "Architecture check failed:"
        foreach ($failure in $failures) {
            Write-Host "- $failure"
        }
        exit 1
    }

    Write-Host "Architecture check passed."
}
finally {
    Pop-Location
}
