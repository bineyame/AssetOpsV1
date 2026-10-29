# OPS-03: run the full backend suite inside the Docker Compose network. Since PERF-01 (R2) this is the only
# supported path for a full or merge run; the Windows host runs focused files only (tools\run-host-tests.ps1).
#
#   tools\run-backend-suite-in-container.ps1 [-Tier all|fast|slow] [-Workers N] [-Server dedicated|shared]
#       [-CapMinutes M] [-Targets 'backend/tests/test_x.py ...']
#
# Run it directly from a PowerShell prompt that may run local scripts; it never passes an execution-policy
# override to anything it starts (its children inherit the caller's policy).
#
# PERF-01 options:
#   -Server dedicated (default)  the test-only `postgres-test` server (docker-compose.test.yml; crash safety off,
#                                its own volume, no published port). `shared` = the OPS-03 behaviour on `postgres`.
#   -Tier all (default)          every test. `fast` = `-m "not slow"`, `slow` = `-m slow` (the deliberate
#                                real-clock tests; backend/TESTING.md "Slow tier"). The default stays `all` until
#                                the revised testing policy (owner D4) takes effect.
#   -Cache on (default)          PERF-02 build once / copy per test with set-ups kept between runs; `off` = every
#                                set-up built live (the old path); `verify` = every hit also built live and its
#                                rows compared with the saved build (backend/tests/setup_cache.py).
#   -Workers 0 (default)         choose 2-4 workers from the memory free when the run starts (R10); a number
#                                overrides. Refuses to start when not even two workers fit.
#
# The one-shot `backend-test-runner` service (docker-compose.test.yml) joins the `assetopsv1` project
# network and reaches Postgres as `postgres-test:5432` (or `postgres:5432`). A Postgres container is started if
# absent but never recreated, stopped or removed (`--no-recreate`, and the runner starts with `--no-deps`, because the
# bind-mount source differs per worktree and plain `up`/`run` would recreate it). Each attempt writes
# junit.xml, console.log, wall-time.txt and connections.csv to var/test-results/OPS-03/<run-id>/.
# The pytest wall time is capped at -CapMinutes (2x the expected wall in backend/TESTING.md); a run past the
# cap is recorded as a hang (timeout.txt), terminated, and exits 124. The URL and password are never printed.
param(
    [int]$CapMinutes = 0,  # 0 = derived: 2x the measured wall for the tier, scaled to the worker count (backend/TESTING.md Timing)
    [int]$Workers = 0,
    [int]$MaxWorkers = 4,  # PERF-01 trial: the most workers -Workers 0 may choose (the memory guard still decides)
    [string]$Targets = 'backend/tests',
    [ValidateSet('dedicated', 'shared')][string]$Server = 'dedicated',
    [ValidateSet('all', 'fast', 'slow')][string]$Tier = 'all',
    [ValidateSet('on', 'off', 'verify')][string]$Cache = 'on',  # PERF-02: build once, copy per test
    [switch]$Attribution  # PERF-01: per-test time attribution (backend/tests/phase_attribution.py) to <run>/attribution
)

# Continue: Windows PowerShell 5.1 turns native stderr into terminating errors under Stop; failures are checked
# explicitly through `$LASTEXITCODE` and -ErrorAction Stop instead.
$ErrorActionPreference = 'Continue'
$worktree = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = 'assetopsv1'
$pgService = if ($Server -eq 'dedicated') { 'postgres-test' } else { 'postgres' }
$pgContainer = "assetopsv1-$pgService-1"
# R10: the memory one worker needs at its peak (pytest worker, its gateway children, its database sessions), from
# the PERF-01 baseline memory sample, plus the fixed cost of a run and the Windows free memory every run leaves.
# PERF-02: 340 MB measured per worker (resident set of 5 workers and their gateway children, 1664 MB, warm run
# 20261029-165359), plus 700 MB more for Postgres when the set-up cache is on (its copies: 0.7 -> 1.4 GB measured).
$perWorkerMb = 340
$cacheMb = if ($Cache -ne 'off') { 700 } else { 0 }
$fixedMb = 400
$windowsReserveMb = 1536
$composeArgs = @('compose', '-p', $project, '-f', (Join-Path $worktree 'docker-compose.yml'),
                 '-f', (Join-Path $worktree 'docker-compose.test.yml'))

function Invoke-Psql([string]$sql) {
    $out = & docker exec $pgContainer psql -U assetops -d postgres -AtF ',' -c $sql
    if ($LASTEXITCODE -ne 0) { return $null }
    return $out
}

& docker compose version | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'docker compose is not available' }

$label = & docker inspect $pgContainer --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>$null
if ($LASTEXITCODE -eq 0 -and $label -ne $project) {
    throw "$pgContainer belongs to Compose project '$label', not '$project'; refusing to run"
}

$runId = '{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss'), ([guid]::NewGuid().ToString('N').Substring(0, 6))
$runDir = Join-Path $worktree "var\test-results\OPS-03\$runId"
New-Item -ItemType Directory -Path $runDir -ErrorAction Stop | Out-Null

$password = $env:ASSETOPS_PG_PASSWORD
if (-not $password) { $password = 'assetops-local-dev' }
$env:ASSETOPS_WORKTREE = $worktree
$env:OPS03_RUN_ID = $runId
$env:ASSETOPS_TEST_TARGETS = $Targets
$env:ASSETOPS_SETUP_CACHE_MODE = $Cache
$env:ASSETOPS_TEST_ATTRIBUTION_ON = if ($Attribution) { '1' } else { '' }
$env:ASSETOPS_TEST_MARKEXPR = switch ($Tier) { 'fast' { 'not slow' } 'slow' { 'slow' } default { '' } }
$env:ASSETOPS_CONTAINER_TEST_DATABASE_URL =
    'postgresql+psycopg://assetops:{0}@{1}:5432/assetops_test' -f [uri]::EscapeDataString($password), $pgService
Remove-Item Env:\DATABASE_URL, Env:\ASSETOPS_TEST_DATABASE_URL -ErrorAction SilentlyContinue

# Compose interpolates the runner's required variables even for `up <server>`, so this follows them.
& docker @composeArgs up -d --no-recreate --wait $pgService
if ($LASTEXITCODE -ne 0) { throw "$pgService did not start healthy" }

# R10: worker count from the memory free now. Inside the VM a run can use what the VM already holds and has not
# used (vmmem working set - VM used) plus what Windows can still give it above the reserve; it can never pass the
# VM's own available memory (its cap). The budget is the smaller of the two, less the run's fixed cost.
$winFreeMb = [int]((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1024)
$vmmem = Get-Process -Name 'vmmemWSL', 'vmmem' -ErrorAction SilentlyContinue | Select-Object -First 1
$vmmemMb = if ($vmmem) { [int]($vmmem.WorkingSet64 / 1MB) } else { 0 }
$vmAvailMb = $null; $vmUsedMb = $null
$meminfo = @(& docker exec $pgContainer grep -e ^MemTotal: -e ^MemAvailable: /proc/meminfo 2>$null)
if ($LASTEXITCODE -eq 0 -and $meminfo.Count -ge 2) {
    $vmTotalMb = [int]([long](($meminfo[0] -split '\s+')[1]) / 1024)
    $vmAvailMb = [int]([long](($meminfo[1] -split '\s+')[1]) / 1024)
    $vmUsedMb = $vmTotalMb - $vmAvailMb
}
$heldMb = if ($null -ne $vmUsedMb) { [math]::Max(0, $vmmemMb - $vmUsedMb) } else { 0 }
$budgetMb = [math]::Max(0, $winFreeMb - $windowsReserveMb) + $heldMb
if ($null -ne $vmAvailMb -and $vmAvailMb -lt $budgetMb) { $budgetMb = $vmAvailMb }
$budgetMb -= $fixedMb + $cacheMb
$fit = [int][math]::Floor($budgetMb / $perWorkerMb)
$memoryNote = ("memory at start: windows_free_mb=$winFreeMb vmmem_ws_mb=$vmmemMb vm_used_mb=$vmUsedMb " +
    "vm_available_mb=$vmAvailMb budget_mb=$budgetMb fits=$fit")
if ($Workers -le 0) {
    if ($fit -lt 2) {
        Write-Output $memoryNote
        Write-Output ('REFUSED: not even 2 workers fit in the free memory. Close programs (Chrome first) and retry, ' +
            'or pass -Workers explicitly.')
        "$memoryNote REFUSED" | Out-File (Join-Path $runDir 'run-options.txt') -Encoding ascii
        exit 3
    }
    $Workers = [int][math]::Min($MaxWorkers, $fit)
}

$env:ASSETOPS_TEST_WORKERS = [string]$Workers
if ($CapMinutes -le 0) {
    # Measured wall at 4 workers (TESTING.md Timing): all tiers 74.2 min (shared server), fast tier 62.6 min, slow tier 4.8 min.
    # The cap is twice that, scaled by 4 / workers (fewer workers are slower), with a 20-minute floor.
    $measured = switch ($Tier) { 'fast' { 62.6 } 'slow' { 4.8 } default { 74.2 } }
    $CapMinutes = [int][math]::Max(20, [math]::Ceiling(2 * $measured * 4 / [math]::Max(1, $Workers)))
    if ($Targets -ne 'backend/tests') { $CapMinutes = [int][math]::Max(20, [math]::Min($CapMinutes, 60)) }
}
"$memoryNote workers=$Workers server=$pgService tier=$Tier cache=$Cache attribution=$([bool]$Attribution) targets=$Targets" |
    Out-File (Join-Path $runDir 'run-options.txt') -Encoding ascii

$keepAwake = $null
$memorySampler = $null
$compose = $null
$runner = "assetops-ops03-$runId"
$exitCode = 1
try {
    # PERF-01: no execution-policy override on the child; it inherits this process's policy.
    $keepAwake = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList @(
        '-NoProfile', '-File', (Join-Path $PSScriptRoot 'keep-awake-during-tests.ps1'),
        '-WatchProcessId', $PID)
    # PERF-01 phase 0 (R10): memory sampler, every 5 s, next to the connection sampler below.
    $memoryCsv = Join-Path $runDir 'memory.csv'
    $memorySampler = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList @(
        '-NoProfile', '-File', (Join-Path $PSScriptRoot 'sample-test-memory.ps1'),
        '-OutFile', $memoryCsv, '-RunnerContainer', $runner, '-PgContainer', $pgContainer, '-WatchProcessId', $PID)

    Write-Output "OPS-03 run $runId -> $runDir ($Workers workers, $pgService, tier $Tier)"
    $stdout = Join-Path $runDir 'compose-stdout.log'
    $stderr = Join-Path $runDir 'compose-stderr.log'
    $runArgs = $composeArgs + @('run', '--rm', '-T', '--no-deps', '--name', $runner, 'backend-test-runner')
    $compose = Start-Process docker -ArgumentList $runArgs -NoNewWindow -PassThru `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    [void]$compose.Handle  # keeps ExitCode readable after exit (Windows PowerShell 5.1)

    $started = Join-Path $runDir 'pytest-started'
    $csv = Join-Path $runDir 'connections.csv'
    'utc,server_total,client_backends,runner_sessions,assetops_test_dbs' | Out-File $csv -Encoding ascii
    $launch = Get-Date
    $runnerIp = $null
    $timedOut = $false
    while (-not $compose.WaitForExit(5000)) {
        if (-not $runnerIp) {
            $ip = & docker inspect $runner --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>$null
            if ($LASTEXITCODE -eq 0 -and $ip) { $runnerIp = $ip.Trim() }
        }
        if ($runnerIp) {
            $row = Invoke-Psql ("select count(*), count(*) filter (where backend_type = 'client backend'), " +
                "count(*) filter (where client_addr = '$runnerIp'), " +
                "count(*) filter (where datname like 'assetops%\_test') from pg_stat_activity")
            if ($row) { "$((Get-Date).ToUniversalTime().ToString('s')),$row" | Out-File $csv -Append -Encoding ascii }
        }
        $since = if (Test-Path $started) { (Get-Item $started).LastWriteTime } else { $launch }
        if (((Get-Date) - $since).TotalMinutes -ge $CapMinutes) { $timedOut = $true; break }
    }

    if ($timedOut) {
        $report = Join-Path $runDir 'timeout.txt'
        "HANG: pytest passed the $CapMinutes-minute cap at $((Get-Date).ToString('s'))" | Out-File $report -Encoding utf8
        '--- pg_stat_activity (non-idle) ---' | Out-File $report -Append -Encoding utf8
        Invoke-Psql ("select datname, application_name, state, now() - query_start, left(query, 200) " +
            "from pg_stat_activity where state <> 'idle' and pid <> pg_backend_pid()") | Out-File $report -Append -Encoding utf8
        '--- runner processes ---' | Out-File $report -Append -Encoding utf8
        & docker exec $runner sh -c 'for p in /proc/[0-9]*; do echo; echo $p; tr ''\000'' _ < $p/cmdline; done' 2>&1 | Out-File $report -Append -Encoding utf8
        '--- console tail ---' | Out-File $report -Append -Encoding utf8
        $log = Join-Path $runDir 'console.log'
        if (Test-Path $log) { Get-Content $log -Tail 40 | Out-File $report -Append -Encoding utf8 }
        & docker kill $runner 2>&1 | Out-Null
        if (-not $compose.WaitForExit(60000)) { Stop-Process -Id $compose.Id -Force }
        Write-Output "HANG: run $runId passed the $CapMinutes-minute cap; see $report"
        $exitCode = 124
    } else {
        $exitCode = $compose.ExitCode
    }

    if (Test-Path $csv) {
        $rows = Import-Csv $csv
        if ($rows) {
            $max = { param($column) ($rows | ForEach-Object { [int]$_.$column } | Measure-Object -Maximum).Maximum }
            $peak = 'peak server_total={0} client_backends={1} runner_sessions={2} assetops_test_dbs={3} samples={4}' -f `
                (& $max 'server_total'), (& $max 'client_backends'), (& $max 'runner_sessions'),
                (& $max 'assetops_test_dbs'), @($rows).Count
            $peak | Out-File (Join-Path $runDir 'connections-peak.txt') -Encoding ascii
            Write-Output $peak
        }
    }
    if ($memorySampler -and -not $memorySampler.HasExited) { Stop-Process -Id $memorySampler.Id -Force }
    if ((Test-Path $memoryCsv) -and ($mrows = @(Import-Csv $memoryCsv))) {
        $peakOf = { param($column) ($mrows | Where-Object { $_.$column -ne '' } | ForEach-Object { [int]$_.$column } |
            Measure-Object -Maximum).Maximum }
        $lowOf = { param($column) ($mrows | Where-Object { $_.$column -ne '' } | ForEach-Object { [int]$_.$column } |
            Measure-Object -Minimum).Minimum }
        $mpeak = ('peak vm_used_mb={0} vmmem_ws_mb={1} runner_mem_mb={2} pg_mem_mb={3} runner_procs={4} ' +
            'runner_rss_sum_mb={5} runner_rss_max_mb={6} min win_free_mb={7} vm_total_mb={8} samples={9}') -f `
            (& $peakOf 'vm_used_mb'), (& $peakOf 'vmmem_ws_mb'), (& $peakOf 'runner_mem_mb'), (& $peakOf 'pg_mem_mb'),
            (& $peakOf 'runner_procs'), (& $peakOf 'runner_rss_sum_mb'), (& $peakOf 'runner_rss_max_mb'),
            (& $lowOf 'win_free_mb'), (& $peakOf 'vm_total_mb'), $mrows.Count
        $mpeak | Out-File (Join-Path $runDir 'memory-peak.txt') -Encoding ascii
        Write-Output $mpeak
    }
    $wall = Join-Path $runDir 'wall-time.txt'
    if (Test-Path $wall) { Get-Content $wall }
    $console = Join-Path $runDir 'console.log'
    if (Test-Path $console) { Get-Content $console -Tail 3 }
    if (Test-Path $stderr) { Get-Content $stderr | Where-Object { $_ -match 'error|Error' } | Select-Object -First 10 }
    Write-Output "OPS-03 run $runId exit code $exitCode"
} finally {
    if ($keepAwake -and -not $keepAwake.HasExited) { Stop-Process -Id $keepAwake.Id -Force }
    if ($memorySampler -and -not $memorySampler.HasExited) { Stop-Process -Id $memorySampler.Id -Force }
}
exit $exitCode
