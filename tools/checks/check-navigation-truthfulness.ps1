# Runs the navigation-truthfulness guard directly:
#   powershell -NoProfile -File tools\checks\check-navigation-truthfulness.ps1
# Run from any directory; resolves the repository root from this file. No execution-policy override.
$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Push-Location $repoRoot
try {
    . (Join-Path $PWD "tools/checks/_common.ps1")
    . (Join-Path $PWD "tools/checks/navigation-truthfulness.ps1")
    $failures = @(Invoke-NavigationTruthfulnessCheck)
    if ($failures.Count -gt 0) { $failures | ForEach-Object { Write-Output "- $_" }; exit 1 }
    Write-Output "Navigation truthfulness check passed."
}
finally { Pop-Location }
