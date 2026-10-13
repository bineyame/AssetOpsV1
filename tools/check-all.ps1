param(
    # Override the interpreter used for Python guards (default: repository .venv).
    [string]$Python = "",
    [string]$Node = "node"
)

# Normal local/CI check command. Runs every repository guard, reports each one,
# and exits nonzero when any guard fails or a required tool is missing.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\check-all.ps1
#
# A guard that cannot run is a failure, never a skip. Do not weaken a guard to
# make this pass.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    if (-not $Python) { $Python = Join-Path $repoRoot ".venv\Scripts\python.exe" }
    $powershell = (Get-Process -Id $PID).Path

    $results = New-Object System.Collections.Generic.List[object]

    function Resolve-Tool([string]$tool) {
        if (Test-Path -LiteralPath $tool -PathType Leaf) { return $tool }
        $cmd = Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
        return $null
    }

    function Invoke-Guard([string]$name, [string]$tool, [string[]]$arguments) {
        $resolved = Resolve-Tool $tool
        if (-not $resolved) {
            $results.Add([pscustomobject]@{ Guard = $name; Status = "FAIL"; Detail = "missing tool: $tool" }) | Out-Null
            return
        }
        $previous = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $output = & $resolved @arguments 2>&1 | ForEach-Object { "$_" }
        $code = $LASTEXITCODE
        $ErrorActionPreference = $previous
        $last = @($output | Where-Object { $_.Trim() }) | Select-Object -Last 1
        if ($code -eq 0) {
            $results.Add([pscustomobject]@{ Guard = $name; Status = "PASS"; Detail = $last }) | Out-Null
        } else {
            $results.Add([pscustomobject]@{ Guard = $name; Status = "FAIL"; Detail = "exit $code" ; Output = $output }) | Out-Null
        }
    }

    $navigationScript = @'
$ErrorActionPreference = "Stop"
. (Join-Path $PWD "tools/checks/_common.ps1")
. (Join-Path $PWD "tools/checks/navigation-truthfulness.ps1")
$failures = @(Invoke-NavigationTruthfulnessCheck)
if ($failures.Count -gt 0) { $failures | ForEach-Object { Write-Output "- $_" }; exit 1 }
Write-Output "Navigation truthfulness check passed."
'@

    Invoke-Guard "Architecture seams"            $powershell @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/check-architecture.ps1")
    Invoke-Guard "Navigation truthfulness"       $powershell @("-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand",
        [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($navigationScript)))
    Invoke-Guard "Agent workflow"                $powershell @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "tools/check-agent-workflow.ps1")
    Invoke-Guard "Dependency registry"           $Node @("frontend/docs/architecture/check_v69_dependency_registry.cjs")
    Invoke-Guard "Delivery checker fixtures"     $Node @("--test", "frontend/docs/architecture/test_delivery_next_work.cjs")
    Invoke-Guard "Mock-gap catalogue fixtures"   $Node @("--test", "frontend/docs/architecture/test_mock_gaps.cjs")
    Invoke-Guard "Screen ledger"                 $Python @("frontend/docs/architecture/check_v69_ledger.py")

    $failed = @($results | Where-Object { $_.Status -ne "PASS" })
    foreach ($result in $results) {
        Write-Host ("[{0}] {1}: {2}" -f $result.Status, $result.Guard, $result.Detail)
        if ($result.Status -ne "PASS" -and $result.Output) {
            $result.Output | Select-Object -Last 15 | ForEach-Object { Write-Host "    $_" }
        }
    }
    if ($failed.Count -gt 0) {
        Write-Host "Check failed: $($failed.Count) of $($results.Count) guards."
        exit 1
    }
    Write-Host "All $($results.Count) guards passed."
    exit 0
}
finally {
    Pop-Location
}
