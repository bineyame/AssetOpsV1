param(
    # Override the interpreter used for Python guards (default: repository .venv).
    [string]$Python = "",
    [string]$Node = "node"
)

# Normal local/CI check command. Runs every repository guard, reports each one,
# and exits nonzero when any guard fails or a required tool is missing.
#
#   powershell -NoProfile -File tools\check-all.ps1
#
# Guards run directly with no execution-policy override (owner rule). Never add
# -ExecutionPolicy to this script or to any guard invocation.
#
# A guard that cannot run is a failure, never a skip. Do not weaken a guard to
# make this pass.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    # Both venv layouts (Windows Scripts\python.exe, Linux/macOS bin/python), as the architecture modules do.
    if (-not $Python) {
        $Python = @((Join-Path $repoRoot ".venv/Scripts/python.exe"), (Join-Path $repoRoot ".venv/bin/python")) |
            Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
        if (-not $Python) { $Python = Join-Path $repoRoot ".venv/bin/python" }
    }
    $powershell = (Get-Process -Id $PID).Path

    $results = New-Object System.Collections.Generic.List[object]

    function Resolve-Tool([string]$tool) {
        if (Test-Path -LiteralPath $tool -PathType Leaf) { return $tool }
        $cmd = Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
        return $null
    }

    # -Advisory: the guard runs and reports, but a failure is a WARN that never fails check-all (PIPE-1 A6: retired
    # v69 and S1-S7 plumbing, kept visible until declutter step 5 deletes it).
    function Invoke-Guard([string]$name, [string]$tool, [string[]]$arguments, [switch]$Advisory) {
        $failStatus = if ($Advisory) { "WARN" } else { "FAIL" }
        $resolved = Resolve-Tool $tool
        if (-not $resolved) {
            $results.Add([pscustomobject]@{ Guard = $name; Status = $failStatus; Detail = "missing tool: $tool" }) | Out-Null
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
            $results.Add([pscustomobject]@{ Guard = $name; Status = $failStatus; Detail = "exit $code" ; Output = $output }) | Out-Null
        }
    }

    # Rule 8 parses backend SQL with Python (OPS-02); it uses the same interpreter as the Python guards.
    $env:ASSETOPS_GUARD_PYTHON = $Python
    Invoke-Guard "Architecture seams"            $powershell @("-NoProfile", "-File", "tools/check-architecture.ps1")
    Invoke-Guard "Estate guard self-tests (test_pg_reader_import_allowed, test_pg_reader_write_rejected, test_domain_driver_import_rejected)" $Python @("-m", "pytest", "tools/checks/test_estate_guard.py", "-q", "-p", "no:cacheprovider")
    Invoke-Guard "Navigation truthfulness"       $powershell @("-NoProfile", "-File", "tools/check-navigation-truthfulness.ps1")
    Invoke-Guard "Agent workflow"                $powershell @("-NoProfile", "-File", "tools/check-agent-workflow.ps1")
    # PIPE-1 A6: the v69 registry, the S1-S7 queue (delivery checker) and the v69 screen ledger are advisory; the live
    # honest-gap catalogue they shared stays blocking as its own guard.
    Invoke-Guard "v69 dependency registry and S1-S7 queue (advisory)" $Node @("frontend/docs/architecture/check_v69_dependency_registry.cjs") -Advisory
    Invoke-Guard "Delivery checker fixtures, S1-S7 (advisory)" $Node @("--test", "frontend/docs/architecture/test_delivery_next_work.cjs") -Advisory
    Invoke-Guard "Mock-gap catalogue (live registry)" $Node @("frontend/docs/architecture/check_mock_gaps.cjs")
    Invoke-Guard "Mock-gap catalogue fixtures"   $Node @("--test", "frontend/docs/architecture/test_mock_gaps.cjs")
    Invoke-Guard "Missing-claim orphan scan"     $Node @("tools/checks/missing-claim-scan.mjs")
    Invoke-Guard "Missing-claim scan fixtures"   $Node @("--test", "tools/checks/test_missing_claim_scan.mjs")
    Invoke-Guard "Evidence width check (W1-UX-06)" $Node @("--test", "tools/checks/test_evidence_checks.mjs")
    Invoke-Guard "Mock deviation labels and client vocabulary" $Node @("--test", "tools/checks/test_mock_deviation_labels.mjs")
    Invoke-Guard "v69 screen ledger (advisory)"  $Python @("frontend/docs/architecture/check_v69_ledger.py") -Advisory
    Invoke-Guard "Chain coherence rules (fixtures)" $Python @("-m", "pytest", "tools/checks/test_chain_coherence.py", "-q", "-p", "no:cacheprovider")
    Invoke-Guard "Event register guard (CH-1b)" $Python @("-m", "pytest", "tools/checks/test_event_register.py", "-q", "-p", "no:cacheprovider")
    # DIESEL-1 H4 (K9): served copy never says theft, stolen, stole, siphon or pilfer (self-test plus repository scan).
    Invoke-Guard "Fuel wording guard (DIESEL-1 H4)" $Python @("-m", "pytest", "tools/checks/test_fuel_wording.py", "-q", "-p", "no:cacheprovider")
    # CH-5b1: the declared chain graph (check only; the diagram is regenerated by hand and diffed by its L0 test).
    $previousPythonPath = $env:PYTHONPATH
    # D-1: join with the platform separator (":" on Linux, ";" on Windows). A ";" on Linux glued this tree's backend
    # to the next entry, so the import fell through to the editable install (main's checkout) in every worktree.
    $env:PYTHONPATH = (@((Join-Path $repoRoot "backend"), (Join-Path $repoRoot "contracts"), $previousPythonPath) |
        Where-Object { $_ }) -join [IO.Path]::PathSeparator
    Invoke-Guard "Chain graph check (CH-5b1)" $Python @("-m", "assetops_backend.chain.graph", "check")
    $env:PYTHONPATH = $previousPythonPath
    Invoke-Guard "Perf budget fixtures (CH-5b1)" $Python @("tools/checks/perf_budget.py", "--fixture")
    # ANY-1 AR-0: the stored read-period parity harness self-test (one deliberate mismatch must fail).
    Invoke-Guard "Period read parity self-test (ANY-1 AR-0)" $Python @("tools/checks/period_read_parity.py", "--self-test")
    Invoke-Guard "Frontend hard-wiring ratchet (CH-5b1)" $Node @("tools/checks/frontend-hardwiring.mjs")
    Invoke-Guard "Style ratchet (UQ-FI)" $Node @("tools/checks/style-ratchet.mjs")
    Invoke-Guard "Style ratchet fixtures (UQ-FI)" $Node @("--test", "tools/checks/test_style_ratchet.mjs")

    $failed = @($results | Where-Object { $_.Status -eq "FAIL" })
    $warned = @($results | Where-Object { $_.Status -eq "WARN" })
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
    if ($warned.Count -gt 0) { Write-Host "Advisory warnings: $($warned.Count) (they do not fail check-all)." }
    Write-Host "All $($results.Count - $warned.Count) blocking guards passed."
    exit 0
}
finally {
    Pop-Location
}
