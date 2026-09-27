# Seam: Stack and module direction (structure half).
#
# Verifies the modular-monolith shape exists and the declared stack is the one
# the project agreed to. The dependency-direction half of the same seam lives
# in dependency-direction.ps1.
#
# Do not weaken the checks below to make a task pass.

function Invoke-ModuleRootsCheck {
    $failures = New-Object System.Collections.Generic.List[string]

    $requiredDirectories = @(
        "backend",
        "backend/assetops_backend",
        "frontend",
        "frontend/src",
        "simulator",
        "simulator/assetops_simulator",
        # The two roots v4 section 3.2 requires beside the other three. The
        # neutral contracts hold the schemas both sides of the truth barrier
        # speak; the composition leaf is the one place that may import both.
        # Required rather than optional, because the dependency rules about them
        # - nothing imports host, contracts import neither side - are rules about
        # trees that have to exist for the rules to mean anything.
        "contracts",
        "contracts/assetops_contracts",
        "host"
    )

    foreach ($directory in $requiredDirectories) {
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) {
            $failures.Add("Missing expected module root: $directory") | Out-Null
        }
    }

    $requiredFiles = @(
        "backend/pyproject.toml",
        "backend/assetops_backend/__init__.py",
        "backend/assetops_backend/main.py",
        "frontend/package.json",
        "frontend/tsconfig.json",
        "frontend/src/main.tsx",
        "simulator/assetops_simulator/__init__.py",
        "contracts/pyproject.toml",
        "contracts/assetops_contracts/__init__.py",
        "simulator/pyproject.toml",
        "host/execution_adapter.py"
    )

    foreach ($file in $requiredFiles) {
        if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
            $failures.Add("Missing expected root marker file: $file") | Out-Null
        }
    }

    # --- Declared stack --------------------------------------------------------

    if (Test-Path -LiteralPath "backend/pyproject.toml") {
        $backendProject = Get-Content -LiteralPath "backend/pyproject.toml" -Raw
        if ($backendProject -notmatch "fastapi") {
            $failures.Add("backend/pyproject.toml must declare a FastAPI dependency") | Out-Null
        }
    }

    if (Test-Path -LiteralPath "frontend/package.json") {
        $frontendPackage = Get-Content -LiteralPath "frontend/package.json" -Raw
        foreach ($required in @("react", "typescript")) {
            if ($frontendPackage -notmatch $required) {
                $failures.Add("frontend/package.json must declare $required") | Out-Null
            }
        }
    }

    return $failures
}
