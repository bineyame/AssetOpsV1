$ErrorActionPreference = "Stop"

# CI architecture guard.
#
# This file is a runner. Every rule lives in one module per protected seam
# under tools/checks/, so a task that changes one seam reads one module rather
# than the whole guard. Shared scanning mechanics live in tools/checks/_common.ps1.
#
# Adding a seam: write tools/checks/<seam>.ps1 exposing one Invoke-*Check
# function that returns failure strings, then register it below. The runner
# refuses to run if the directory and this manifest disagree, so a module
# cannot be added and left silently unwired, or deleted and left silently
# unenforced.
#
# Do not weaken a check to make a task pass.

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    $checksRoot = Join-Path $PSScriptRoot "checks"

    # Seam -> module -> entry point. Ordered as the failures should read.
    $checkModules = @(
        @{ Seam = "Module roots and declared stack"; File = "module-roots.ps1";              Function = "Invoke-ModuleRootsCheck" },
        @{ Seam = "Dependency direction";            File = "dependency-direction.ps1";      Function = "Invoke-DependencyDirectionCheck" },
        @{ Seam = "Simulator feature gate";          File = "simulator-gate.ps1";            Function = "Invoke-SimulatorGateCheck" },
        @{ Seam = "Configuration persistence";       File = "configuration-persistence.ps1"; Function = "Invoke-ConfigurationPersistenceCheck" },
        @{ Seam = "Shared Site substrate";           File = "site-substrate.ps1";            Function = "Invoke-SiteSubstrateCheck" },
        @{ Seam = "Navigation truthfulness";         File = "navigation-truthfulness.ps1";   Function = "Invoke-NavigationTruthfulnessCheck" }
    )

    if (-not (Test-Path -LiteralPath $checksRoot -PathType Container)) {
        Write-Host "Architecture check failed:"
        Write-Host "- Missing check module directory: tools/checks"
        exit 1
    }

    # The manifest and the directory must agree. A module present but
    # unregistered would never run; a module registered but absent would take
    # its seam with it.
    $discovered = @(Get-ChildItem -LiteralPath $checksRoot -Filter "*.ps1" -File |
        Where-Object { $_.Name -ne "_common.ps1" } |
        ForEach-Object { $_.Name } | Sort-Object)
    $declared = @($checkModules | ForEach-Object { $_.File } | Sort-Object)

    $unregistered = @($discovered | Where-Object { $declared -notcontains $_ })
    $missing = @($declared | Where-Object { $discovered -notcontains $_ })

    if ($unregistered.Count -gt 0 -or $missing.Count -gt 0) {
        Write-Host "Architecture check failed:"
        foreach ($name in $unregistered) {
            Write-Host "- tools/checks/$name is not registered in tools/check-architecture.ps1, so it never runs."
        }
        foreach ($name in $missing) {
            Write-Host "- tools/checks/$name is registered in tools/check-architecture.ps1 but does not exist."
        }
        exit 1
    }

    . (Join-Path $checksRoot "_common.ps1")

    $failuresBySeam = New-Object System.Collections.Generic.List[object]
    $failureCount = 0

    foreach ($check in $checkModules) {
        . (Join-Path $checksRoot $check.File)

        if (-not (Get-Command $check.Function -CommandType Function -ErrorAction SilentlyContinue)) {
            Write-Host "Architecture check failed:"
            Write-Host "- tools/checks/$($check.File) does not define $($check.Function)."
            exit 1
        }

        $seamFailures = @(& $check.Function)
        if ($seamFailures.Count -gt 0) {
            $failureCount += $seamFailures.Count
            $failuresBySeam.Add([pscustomobject]@{
                Seam     = $check.Seam
                File     = $check.File
                Failures = $seamFailures
            }) | Out-Null
        }
    }

    if ($failureCount -gt 0) {
        Write-Host "Architecture check failed:"
        foreach ($seam in $failuresBySeam) {
            Write-Host "  $($seam.Seam) (tools/checks/$($seam.File)):"
            foreach ($failure in $seam.Failures) {
                Write-Host "- $failure"
            }
        }
        exit 1
    }

    Write-Host "Architecture check passed."
}
finally {
    Pop-Location
}
