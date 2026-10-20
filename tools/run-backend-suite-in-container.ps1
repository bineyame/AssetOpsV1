# OPS-03: run the full backend suite inside the Docker Compose network.
#
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools\run-backend-suite-in-container.ps1
#
# The one-shot `backend-test-runner` service (docker-compose.test.yml) joins the `assetopsv1` project
# network and reaches Postgres as `postgres:5432`. The shared Postgres container is started if absent but
# never recreated, stopped or removed (`--no-recreate`, and the runner starts with `--no-deps`, because the
# bind-mount source differs per worktree and plain `up`/`run` would recreate it). Each attempt writes
# junit.xml, console.log, wall-time.txt and connections.csv to var/test-results/OPS-03/<run-id>/.
# The pytest wall time is capped at -CapMinutes (2x the expected wall in backend/TESTING.md); a run past the
# cap is recorded as a hang (timeout.txt), terminated, and exits 124. The URL and password are never printed.
param([int]$CapMinutes = 120)

# Continue: Windows PowerShell 5.1 turns native stderr into terminating errors under Stop; failures are checked
# explicitly through `$LASTEXITCODE` and -ErrorAction Stop instead.
$ErrorActionPreference = 'Continue'
$worktree = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$project = 'assetopsv1'
$pgContainer = 'assetopsv1-postgres-1'
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
$env:ASSETOPS_CONTAINER_TEST_DATABASE_URL =
    'postgresql+psycopg://assetops:{0}@postgres:5432/assetops_test' -f [uri]::EscapeDataString($password)
Remove-Item Env:\DATABASE_URL, Env:\ASSETOPS_TEST_DATABASE_URL -ErrorAction SilentlyContinue

$keepAwake = $null
$compose = $null
$runner = "assetops-ops03-$runId"
$exitCode = 1
try {
    $keepAwake = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList @(
        '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $PSScriptRoot 'keep-awake-during-tests.ps1'),
        '-WatchProcessId', $PID)

    & docker @composeArgs up -d --no-recreate --wait postgres
    if ($LASTEXITCODE -ne 0) { throw 'postgres did not start healthy' }

    Write-Output "OPS-03 run $runId -> $runDir"
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
    $wall = Join-Path $runDir 'wall-time.txt'
    if (Test-Path $wall) { Get-Content $wall }
    $console = Join-Path $runDir 'console.log'
    if (Test-Path $console) { Get-Content $console -Tail 3 }
    if (Test-Path $stderr) { Get-Content $stderr | Where-Object { $_ -match 'error|Error' } | Select-Object -First 10 }
    Write-Output "OPS-03 run $runId exit code $exitCode"
} finally {
    if ($keepAwake -and -not $keepAwake.HasExited) { Stop-Process -Id $keepAwake.Id -Force }
}
exit $exitCode
