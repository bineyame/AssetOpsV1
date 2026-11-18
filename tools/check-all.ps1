param(
    # Override the interpreter used for Python guards (default: repository .venv).
    [string]$Python = "",
    [string]$Node = "node",
    # Run every conditional self-test whatever changed. Use it at a milestone; check-all also runs in this mode by
    # itself on the `main` branch, so the coordinator's run on main after each merge is always full (PIPE-1 A2).
    [switch]$Full,
    # The branch a change is measured against when deciding the conditional self-tests.
    [string]$Base = "main",
    # Guards run at once (PIPE-1 A4). 1 runs them one after another.
    [ValidateRange(1, 16)][int]$Jobs = 4,
    # Concurrent check-all runs allowed on this machine, across every worktree of the repository (PIPE-1 A3).
    [ValidateRange(1, 8)][int]$Slots = 2,
    # Give up (fail) after waiting this long for a slot: two full runs ahead take about 6 minutes.
    [ValidateRange(1, 240)][int]$SlotWaitMinutes = 20,
    # Stop (fail) a guard that runs longer than this: the slowest pool guard takes about 37 s.
    [ValidateRange(1, 240)][int]$GuardTimeoutMinutes = 10,
    # The estate self-tests' own limit: about 2.5 min at -n 4, about 8 min one at a time.
    [ValidateRange(1, 240)][int]$EstateTimeoutMinutes = 20,
    # Internal: check the self-test trigger rule against fixed cases and exit (check-all runs this as a guard).
    [switch]$SelfTestSelection
)

# Normal local/CI check command. Runs every repository guard, reports each one,
# and exits nonzero when any blocking guard fails or a required tool is missing.
#
#   pwsh -NoProfile -File tools/check-all.ps1            # fast mode: builders, any branch
#   pwsh -NoProfile -File tools/check-all.ps1 -Full      # milestone; automatic on the main branch
#
# PIPE-1 (Docs/engineering/build-pipeline-and-checks-speedup.md, A2-A6):
# - Independent guards run $Jobs at a time; each architecture module is its own job. Results print in the fixed
#   order below, failures in full.
# - The estate-guard self-tests run only when the writer guard or its tests changed against $Base, with -Full, or on
#   main (Architect ruling 4 Nov). They run after the pool, alone, with pytest -n 4, to keep peak memory bounded.
#   The writer seam itself (rule 8, configuration-persistence) runs on every run.
# - At most $Slots check-all runs at once on the machine (a lock file per slot in the shared git directory).
# - Advisory guards (retired v69 and S1-S7 plumbing) report WARN and never fail the run.
#
# Guards run directly with no execution-policy override (owner rule). Never add
# -ExecutionPolicy to this script or to any guard invocation.
#
# A guard that cannot run is a failure, never a skip. Do not weaken a guard to
# make this pass.

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

# PIPE-1 A2: the files whose change makes the estate-guard self-tests run (spec G1 and P1): the writer guard, its
# shared code and its tests, plus (review L3) every real file the self-tests assert on, derived from the path
# constants in test_estate_guard.py so the list cannot drift when an anchor is added.
$estateGuardFiles = @(
    "tools/checks/configuration-persistence.ps1",
    "tools/checks/_common.ps1",
    "tools/checks/sql_statements.py",
    "tools/checks/test_estate_guard.py"
)

# Module-level `NAME = "path"` and `NAME = f"{OTHER}/path"` constants naming a repository file; the `_guard_probe_`
# names are files the tests create in their temporary copy, not anchors.
function Get-EstateAnchors([string]$text) {
    $constants = @{}
    foreach ($m in [regex]::Matches($text, '(?m)^([A-Z][A-Z0-9_]*)\s*=\s*f?"([^"]*)"\s*$')) {
        $value = [regex]::Replace($m.Groups[2].Value, '\{([A-Z][A-Z0-9_]*)\}',
            [System.Text.RegularExpressions.MatchEvaluator] { param($x) "$($constants[$x.Groups[1].Value])" })
        $constants[$m.Groups[1].Value] = $value
    }
    @($constants.Values | Where-Object { $_ -match '^(backend|tools|config|contracts)/\S+\.(py|ps1|sql)$' -and $_ -notmatch '_guard_probe_' } |
        Sort-Object -Unique)
}

$triggerError = ""
$estateAnchors = @()
$estateTestPath = Join-Path $repoRoot "tools/checks/test_estate_guard.py"
if (Test-Path -LiteralPath $estateTestPath -PathType Leaf) {
    $estateAnchors = @(Get-EstateAnchors ([IO.File]::ReadAllText($estateTestPath)))
}
if ($estateAnchors.Count -lt 10) { $triggerError = "only $($estateAnchors.Count) anchor paths derived from test_estate_guard.py" }
$estateTriggers = @($estateGuardFiles + $estateAnchors | Sort-Object -Unique)

# The trigger rule. Unknown is never a skip: if the change set cannot be computed, the self-tests run.
function Get-SelfTestDecision([string[]]$changed, [bool]$full, [bool]$onMain, [string]$diffError) {
    if ($full) { return [pscustomobject]@{ Run = $true; Reason = "-Full" } }
    if ($onMain) { return [pscustomobject]@{ Run = $true; Reason = "on main (full run after merge)" } }
    if ($diffError) { return [pscustomobject]@{ Run = $true; Reason = "change set unknown ($diffError)" } }
    if ($triggerError) { return [pscustomobject]@{ Run = $true; Reason = "trigger list unknown ($triggerError)" } }
    $hits = @($changed | Where-Object { $estateTriggers -contains $_ })
    if ($hits.Count -gt 0) { return [pscustomobject]@{ Run = $true; Reason = "changed: $($hits -join ', ')" } }
    return [pscustomobject]@{ Run = $false; Reason = "writer guard, its tests and their $($estateAnchors.Count) anchor files unchanged against $Base" }
}

if ($SelfTestSelection) {
    $cases = @(
        @{ Name = "-Full"; Changed = @(); Full = $true; Main = $false; Err = ""; Want = $true },
        @{ Name = "on main"; Changed = @(); Full = $false; Main = $true; Err = ""; Want = $true },
        @{ Name = "diff unknown"; Changed = @(); Full = $false; Main = $false; Err = "no merge base"; Want = $true },
        @{ Name = "unrelated change"; Changed = @("frontend/src/App.tsx", "tools/checks/style-ratchet.mjs"); Full = $false; Main = $false; Err = ""; Want = $false },
        @{ Name = "no change"; Changed = @(); Full = $false; Main = $false; Err = ""; Want = $false },
        @{ Name = "near miss"; Changed = @("tools/checks/configuration-persistence.ps1.orig", "backend/tools/checks/_common.ps1"); Full = $false; Main = $false; Err = ""; Want = $false }
    )
    # Written out, not read from $estateTriggers, so dropping a trigger from the list fails this self-test.
    foreach ($trigger in @("tools/checks/configuration-persistence.ps1", "tools/checks/_common.ps1",
                           "tools/checks/sql_statements.py", "tools/checks/test_estate_guard.py")) {
        $cases += @{ Name = "changed $trigger"; Changed = @("frontend/src/App.tsx", $trigger); Full = $false; Main = $false; Err = ""; Want = $true }
    }
    foreach ($anchor in $estateAnchors) {
        $cases += @{ Name = "changed anchor $anchor"; Changed = @($anchor); Full = $false; Main = $false; Err = ""; Want = $true }
    }
    $bad = 0
    # The derivation: a fixed text, then the real test file (known anchors written out; every anchor exists).
    $fixture = "ROOT = Path(__file__)`nBASE = `"backend/assetops_backend/x`"`nA = f`"{BASE}/adapters/a.py`"`n" +
               "B = `"backend/migrations/versions/0001_x.py`"`nP = f`"{BASE}/_guard_probe_y.py`"`nS = `"INSERT INTO t (`"`n"
    $want = "backend/assetops_backend/x/adapters/a.py|backend/migrations/versions/0001_x.py"
    $got = (Get-EstateAnchors $fixture) -join "|"
    if ($got -ne $want) { $bad++; Write-Output "FAIL anchor derivation (fixture): got [$got], expected [$want]" }
    if ($triggerError) { $bad++; Write-Output "FAIL anchor derivation (test_estate_guard.py): $triggerError" }
    foreach ($known in @("backend/assetops_backend/estate/adapters/postgres_estate_read.py",
                         "backend/assetops_backend/chain/adapters/postgres_event_store.py",
                         "backend/migrations/versions/0044_chain_events.py")) {
        if ($estateTriggers -notcontains $known) { $bad++; Write-Output "FAIL anchor derivation: $known is not a trigger" }
    }
    foreach ($anchor in $estateAnchors) {
        if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $anchor) -PathType Leaf)) { $bad++; Write-Output "FAIL anchor $anchor (named in test_estate_guard.py) does not exist" }
    }
    foreach ($case in $cases) {
        $got = Get-SelfTestDecision $case.Changed $case.Full $case.Main $case.Err
        if ($got.Run -ne $case.Want) { $bad++; Write-Output "FAIL $($case.Name): run=$($got.Run), expected $($case.Want)" }
    }
    Pop-Location
    if ($bad -gt 0) { exit 1 }
    Write-Output "Self-test trigger rule: $($cases.Count)/$($cases.Count) cases as expected; $($estateAnchors.Count) anchors derived from test_estate_guard.py."
    exit 0
}

$slotStream = $null
$running = New-Object System.Collections.Generic.List[object]
$previousPythonPath = $env:PYTHONPATH

# Review L1: a run stopped by SIGTERM or SIGHUP (an agent's command timeout, a closed terminal) never unwinds to the
# finally block below, so a signal handler stops the running guards and their children first. pwsh 7.2+ (.NET 6+);
# Ctrl-C unwinds normally; SIGKILL cannot be caught by any process.
$reaper = $false
if ($PSVersionTable.PSVersion.Major -ge 7 -and ("System.Runtime.InteropServices.PosixSignalRegistration" -as [type])) {
    if (-not ("CheckAllReaper" -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Runtime.InteropServices;
public static class CheckAllReaper {
    static readonly ConcurrentDictionary<int, Process> Live = new ConcurrentDictionary<int, Process>();
    static PosixSignalRegistration term, hup;
    public static void Track(Process p) { Live[p.Id] = p; }
    public static void Untrack(Process p) { Process gone; Live.TryRemove(p.Id, out gone); }
    public static void KillAll() {
        foreach (var p in Live.Values) { try { if (!p.HasExited) p.Kill(true); } catch { } }
    }
    public static void Register() {
        Action<PosixSignalContext> handler = ctx => KillAll();
        term = PosixSignalRegistration.Create(PosixSignal.SIGTERM, handler);
        hup = PosixSignalRegistration.Create(PosixSignal.SIGHUP, handler);
    }
}
'@
    }
    [CheckAllReaper]::Register()
    $reaper = $true
}

# Stop a guard and everything it started. Windows PowerShell 5.1 (.NET Framework) has no Kill(bool): taskkill /T.
function Stop-GuardTree([System.Diagnostics.Process]$process) {
    try {
        if ($process.HasExited) { return }
        if ($PSVersionTable.PSVersion.Major -ge 6) { $process.Kill($true) }
        else { & taskkill.exe /T /F /PID $process.Id 2>&1 | Out-Null }
    } catch { Write-Host "check-all: could not stop guard process $($process.Id): $($_.Exception.Message)" }
}

try {
    # Both venv layouts (Windows Scripts\python.exe, Linux/macOS bin/python), as the architecture modules do: this
    # tree's .venv first, then the main checkout's (worktrees on the VPS share it; D-1 keeps the imports on this tree).
    if (-not $Python) {
        $roots = @($repoRoot)
        $commonForVenv = (& git rev-parse --git-common-dir 2>$null)
        if ($LASTEXITCODE -eq 0 -and $commonForVenv) { $roots += Split-Path -Parent ([IO.Path]::GetFullPath([IO.Path]::Combine($repoRoot, $commonForVenv.Trim()))) }
        $Python = @($roots | ForEach-Object { (Join-Path $_ ".venv/Scripts/python.exe"), (Join-Path $_ ".venv/bin/python") }) |
            Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
        if (-not $Python) { $Python = Join-Path $repoRoot ".venv/bin/python" }
    }
    # D-1 and review M1: every guard (and every Python process a guard starts) imports this tree's backend and
    # contracts first. The shared venv's editable installs point at the main checkout; a PYTHONPATH entry wins over
    # them. Joined with the platform separator (":" on Linux, ";" on Windows). The import-root probe guard below
    # fails if this ever stops holding.
    $env:PYTHONPATH = (@((Join-Path $repoRoot "backend"), (Join-Path $repoRoot "contracts"), $previousPythonPath) |
        Where-Object { $_ }) -join [IO.Path]::PathSeparator
    $powershell = (Get-Process -Id $PID).Path
    $clock = [Diagnostics.Stopwatch]::StartNew()

    # ---- PIPE-1 A3: at most $Slots runs at once, machine-wide. The lock is released when this process exits. ----
    $commonDir = (& git rev-parse --git-common-dir 2>$null)
    $slotDir = if ($LASTEXITCODE -eq 0 -and $commonDir) { [IO.Path]::Combine($repoRoot, $commonDir.Trim(), "check-all-slots") } else { [IO.Path]::Combine([IO.Path]::GetTempPath(), "assetops-check-all-slots") }
    New-Item -ItemType Directory -Force -Path $slotDir | Out-Null
    $announced = $false
    while (-not $slotStream) {
        for ($i = 1; $i -le $Slots -and -not $slotStream; $i++) {
            try { $slotStream = [IO.File]::Open([IO.Path]::Combine($slotDir, "slot-$i.lock"), 'OpenOrCreate', 'ReadWrite', 'None') }
            catch [System.IO.IOException] { }
        }
        if (-not $slotStream -and $clock.Elapsed.TotalMinutes -ge $SlotWaitMinutes) {
            Write-Host "Check failed: no check-all slot came free in $SlotWaitMinutes min (-SlotWaitMinutes)."
            exit 1
        }
        if (-not $slotStream) {
            if (-not $announced) { Write-Host "check-all: all $Slots slots are in use by other runs; waiting for one."; $announced = $true }
            Start-Sleep -Seconds 2
        }
    }
    $slotWait = $clock.Elapsed.TotalSeconds

    # ---- PIPE-1 A2: decide the conditional self-tests ----
    $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
    $onMain = ($LASTEXITCODE -eq 0 -and "$branch".Trim() -eq "main")
    # Review L2: a detached HEAD (or any branch) at main's tip is main too.
    if (-not $onMain) {
        $headSha = (& git rev-parse HEAD 2>$null)
        $headOk = ($LASTEXITCODE -eq 0)
        $baseSha = (& git rev-parse --verify --quiet "$Base^{commit}" 2>$null)
        if ($headOk -and $LASTEXITCODE -eq 0 -and $headSha -and "$headSha".Trim() -eq "$baseSha".Trim()) { $onMain = $true }
    }
    $changed = @()
    $diffError = ""
    if (-not $Full -and -not $onMain) {
        $mergeBase = (& git merge-base HEAD $Base 2>$null)
        if ($LASTEXITCODE -ne 0 -or -not $mergeBase) {
            $diffError = "no merge base with $Base"
        } else {
            $tracked = @(& git diff --name-only $mergeBase.Trim() 2>$null)
            $trackedCode = $LASTEXITCODE
            $untracked = @(& git ls-files --others --exclude-standard 2>$null)
            if ($trackedCode -ne 0 -or $LASTEXITCODE -ne 0) { $diffError = "git diff failed" }
            $changed = @($tracked + $untracked | Where-Object { $_ })
        }
    }
    $estate = Get-SelfTestDecision $changed $Full.IsPresent $onMain $diffError

    # ---- the guards ----
    function Resolve-Tool([string]$tool) {
        if (Test-Path -LiteralPath $tool -PathType Leaf) { return $tool }
        $cmd = Get-Command $tool -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
        return $null
    }

    $guards = New-Object System.Collections.Generic.List[object]
    # -Advisory: the guard runs and reports, but a failure is a WARN that never fails check-all (PIPE-1 A6: retired
    # v69 and S1-S7 plumbing, kept visible until declutter step 5 deletes it). -Alone: runs after the pool, by itself.
    function Add-Guard([string]$name, [string]$tool, [string[]]$arguments, [hashtable]$environment = @{}, [switch]$Advisory, [switch]$Alone) {
        $guards.Add([pscustomobject]@{
            Name = $name; Tool = $tool; Arguments = $arguments; Environment = $environment
            Advisory = $Advisory.IsPresent; Alone = $Alone.IsPresent
            Status = $null; Detail = $null; Output = $null; Seconds = 0.0
            Process = $null; OutTask = $null; ErrTask = $null; Watch = $null
            TimeoutMinutes = $(if ($Alone) { $EstateTimeoutMinutes } else { $GuardTimeoutMinutes }); TimedOut = $false
        }) | Out-Null
    }

    # Rule 8 parses backend SQL with Python (OPS-02); it uses the same interpreter as the Python guards.
    $env:ASSETOPS_GUARD_PYTHON = $Python

    # Architecture seams: one job per registered module (the runner still checks the manifest in every job).
    $modules = @(& $powershell -NoProfile -File tools/check-architecture.ps1 -List 2>&1 | ForEach-Object { "$_".Trim() } | Where-Object { $_ })
    if ($LASTEXITCODE -ne 0 -or $modules.Count -eq 0) {
        Add-Guard "Architecture seams (module list)" $powershell @("-NoProfile", "-File", "tools/check-architecture.ps1")
    } else {
        foreach ($module in $modules) {
            Add-Guard "Architecture seams: $module" $powershell @("-NoProfile", "-File", "tools/check-architecture.ps1", "-Only", $module)
        }
    }
    # PIPE-1 A5: no standalone navigation-truthfulness call; the architecture runner already runs the same module.
    Add-Guard "Agent workflow"                $powershell @("-NoProfile", "-File", "tools/check-agent-workflow.ps1")
    # PIPE-1 A6: the v69 registry, the S1-S7 queue (delivery checker) and the v69 screen ledger are advisory; the live
    # honest-gap catalogue they shared stays blocking as its own guard.
    Add-Guard "v69 dependency registry and S1-S7 queue (advisory)" $Node @("frontend/docs/architecture/check_v69_dependency_registry.cjs") -Advisory
    Add-Guard "Delivery checker fixtures, S1-S7 (advisory)" $Node @("--test", "frontend/docs/architecture/test_delivery_next_work.cjs") -Advisory
    Add-Guard "Mock-gap catalogue (live registry)" $Node @("frontend/docs/architecture/check_mock_gaps.cjs")
    Add-Guard "Mock-gap catalogue fixtures"   $Node @("--test", "frontend/docs/architecture/test_mock_gaps.cjs")
    Add-Guard "Missing-claim orphan scan"     $Node @("tools/checks/missing-claim-scan.mjs")
    Add-Guard "Missing-claim scan fixtures"   $Node @("--test", "tools/checks/test_missing_claim_scan.mjs")
    Add-Guard "Evidence width check (W1-UX-06)" $Node @("--test", "tools/checks/test_evidence_checks.mjs")
    Add-Guard "Mock deviation labels and client vocabulary" $Node @("--test", "tools/checks/test_mock_deviation_labels.mjs")
    Add-Guard "v69 screen ledger (advisory)"  $Python @("frontend/docs/architecture/check_v69_ledger.py") -Advisory
    Add-Guard "Chain coherence rules (fixtures)" $Python @("-m", "pytest", "tools/checks/test_chain_coherence.py", "-q", "-p", "no:cacheprovider")
    Add-Guard "Event register guard (CH-1b)" $Python @("-m", "pytest", "tools/checks/test_event_register.py", "-q", "-p", "no:cacheprovider")
    # DIESEL-1 H4 (K9): served copy never says theft, stolen, stole, siphon or pilfer (self-test plus repository scan).
    Add-Guard "Fuel wording guard (DIESEL-1 H4)" $Python @("-m", "pytest", "tools/checks/test_fuel_wording.py", "-q", "-p", "no:cacheprovider")
    # CH-5b1: the declared chain graph (check only; the diagram is regenerated by hand and diffed by its L0 test).
    # D-1: it imports this tree's backend through the run-wide PYTHONPATH set above.
    Add-Guard "Chain graph check (CH-5b1)" $Python @("-m", "assetops_backend.chain.graph", "check")
    # Review M1: the class guard. assetops_backend and assetops_contracts must load from this tree, not the shared venv.
    Add-Guard "First-party import roots (PIPE-1)" $Python @("tools/checks/import_root_probe.py")
    Add-Guard "Perf budget fixtures (CH-5b1)" $Python @("tools/checks/perf_budget.py", "--fixture")
    # ANY-1 AR-0: the stored read-period parity harness self-test (one deliberate mismatch must fail).
    Add-Guard "Period read parity self-test (ANY-1 AR-0)" $Python @("tools/checks/period_read_parity.py", "--self-test")
    Add-Guard "Frontend hard-wiring ratchet (CH-5b1)" $Node @("tools/checks/frontend-hardwiring.mjs")
    Add-Guard "Style ratchet (UQ-FI)" $Node @("tools/checks/style-ratchet.mjs")
    Add-Guard "Style ratchet fixtures (UQ-FI)" $Node @("--test", "tools/checks/test_style_ratchet.mjs")
    # PIPE-1 A2: the trigger rule itself is guarded, so a broken rule cannot silently skip the self-tests.
    Add-Guard "check-all self-test trigger rule (PIPE-1)" $powershell @("-NoProfile", "-File", "tools/check-all.ps1", "-SelfTestSelection")
    if ($estate.Run) {
        Add-Guard "Estate guard self-tests, pytest -n 4 ($($estate.Reason))" $Python @("-m", "pytest", "tools/checks/test_estate_guard.py", "-q", "-p", "no:cacheprovider", "-n", "4") -Alone
    }

    function ConvertTo-ArgumentString([string[]]$arguments) {
        ($arguments | ForEach-Object {
            if ($_ -eq "") { '""' }
            elseif ($_ -match '[\s"]') { '"' + (($_ -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"' }
            else { $_ }
        }) -join " "
    }

    function Start-Guard($guard) {
        $resolved = Resolve-Tool $guard.Tool
        if (-not $resolved) {
            $guard.Status = if ($guard.Advisory) { "WARN" } else { "FAIL" }
            $guard.Detail = "missing tool: $($guard.Tool)"
            return
        }
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $resolved
        if ($PSVersionTable.PSVersion.Major -ge 6) { foreach ($a in $guard.Arguments) { $psi.ArgumentList.Add($a) } }
        else { $psi.Arguments = ConvertTo-ArgumentString $guard.Arguments }
        $psi.WorkingDirectory = $repoRoot
        $psi.UseShellExecute = $false
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.CreateNoWindow = $true
        foreach ($key in $guard.Environment.Keys) { $psi.EnvironmentVariables[$key] = $guard.Environment[$key] }
        $guard.Watch = [Diagnostics.Stopwatch]::StartNew()
        $guard.Process = [System.Diagnostics.Process]::Start($psi)
        if ($reaper) { [CheckAllReaper]::Track($guard.Process) }
        $guard.OutTask = $guard.Process.StandardOutput.ReadToEndAsync()
        $guard.ErrTask = $guard.Process.StandardError.ReadToEndAsync()
        $running.Add($guard) | Out-Null
    }

    function Complete-Guard($guard) {
        $guard.Process.WaitForExit()
        $guard.Seconds = $guard.Watch.Elapsed.TotalSeconds
        $stdout = @("$($guard.OutTask.Result)" -split "\r?\n")
        $stderr = @("$($guard.ErrTask.Result)" -split "\r?\n")
        $code = $guard.Process.ExitCode
        if ($reaper) { [CheckAllReaper]::Untrack($guard.Process) }
        $guard.Process.Dispose()
        $guard.Process = $null
        $running.Remove($guard) | Out-Null
        $lines = @($stdout + $stderr | Where-Object { $_.Trim() })
        $last = @($stdout | Where-Object { $_.Trim() }) | Select-Object -Last 1
        if (-not $last) { $last = $lines | Select-Object -Last 1 }
        if ($guard.TimedOut) {
            $guard.Status = if ($guard.Advisory) { "WARN" } else { "FAIL" }
            $guard.Detail = "timed out after $($guard.TimeoutMinutes) min (stopped)"; $guard.Output = $lines
        } elseif ($code -eq 0) {
            $guard.Status = "PASS"; $guard.Detail = $last
        } else {
            $guard.Status = if ($guard.Advisory) { "WARN" } else { "FAIL" }
            $guard.Detail = "exit $code"; $guard.Output = $lines
        }
    }

    function Invoke-Pool([object[]]$batch, [int]$width) {
        $queue = New-Object System.Collections.Generic.Queue[object]
        foreach ($guard in $batch) { $queue.Enqueue($guard) }
        while ($queue.Count -gt 0 -or $running.Count -gt 0) {
            while ($running.Count -lt $width -and $queue.Count -gt 0) { Start-Guard $queue.Dequeue() }
            foreach ($guard in $running.ToArray()) {
                if ($guard.Process.HasExited) { Complete-Guard $guard }
                elseif (-not $guard.TimedOut -and $guard.Watch.Elapsed.TotalMinutes -ge $guard.TimeoutMinutes) {
                    $guard.TimedOut = $true
                    Stop-GuardTree $guard.Process
                }
            }
            if ($running.Count -gt 0) { Start-Sleep -Milliseconds 50 }
        }
    }

    Invoke-Pool @($guards | Where-Object { -not $_.Alone }) $Jobs
    Invoke-Pool @($guards | Where-Object { $_.Alone }) 1

    $failed = @($guards | Where-Object { $_.Status -eq "FAIL" })
    $warned = @($guards | Where-Object { $_.Status -eq "WARN" })
    foreach ($guard in $guards) {
        Write-Host ("[{0}] {1} ({2:N1} s): {3}" -f $guard.Status, $guard.Name, $guard.Seconds, $guard.Detail)
        if ($guard.Status -ne "PASS" -and $guard.Output) {
            $guard.Output | Select-Object -Last 15 | ForEach-Object { Write-Host "    $_" }
        }
    }
    if (-not $estate.Run) { Write-Host "[SKIP] Estate guard self-tests: $($estate.Reason). They run with -Full and on main." }
    Write-Host ("check-all: {0:N1} s wall ({1:N1} s waiting for a slot), {2} jobs at once." -f $clock.Elapsed.TotalSeconds, $slotWait, $Jobs)
    # Summary line formats (coordinator scripts match these):
    #   All <B> guards passed (blocking; <A> advisory, <W> warned).
    #   Check failed: <F> of <B> blocking guards (<A> advisory, <W> warned).
    $blocking = @($guards | Where-Object { -not $_.Advisory }).Count
    $advisory = @($guards | Where-Object { $_.Advisory }).Count
    if ($failed.Count -gt 0) {
        Write-Host "Check failed: $($failed.Count) of $blocking blocking guards ($advisory advisory, $($warned.Count) warned)."
        exit 1
    }
    Write-Host "All $blocking guards passed (blocking; $advisory advisory, $($warned.Count) warned)."
    exit 0
}
finally {
    # Never leave a guard process behind: an exception or Ctrl-C stops the running guards here (SIGTERM and SIGHUP
    # through the signal handler above).
    foreach ($guard in $running.ToArray()) { if ($guard.Process) { Stop-GuardTree $guard.Process } }
    if ($slotStream) { $slotStream.Dispose() }
    $env:PYTHONPATH = $previousPythonPath
    Pop-Location
}
