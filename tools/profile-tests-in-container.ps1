# PERF-01: profile named tests in the Docker runner with py-spy (see tools/profile-tests-in-container.sh).
#   tools\profile-tests-in-container.ps1 -Targets @('ev|backend/tests/test_x.py::test_y', ...)
# Uses the test-only `postgres-test` server; never prints the URL. Run directly, never with a policy override.
param([Parameter(Mandatory = $true)][string[]]$Targets, [int]$CapMinutes = 30, [switch]$Idle)
$ErrorActionPreference = 'Continue'
$worktree = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$composeArgs = @('compose', '-p', 'assetopsv1', '-f', (Join-Path $worktree 'docker-compose.yml'),
                 '-f', (Join-Path $worktree 'docker-compose.test.yml'), '-f', (Join-Path $worktree 'docker-compose.profile.yml'))
$runId = 'profile-{0}-{1}' -f (Get-Date -Format 'yyyyMMdd-HHmmss'), ([guid]::NewGuid().ToString('N').Substring(0, 6))
$runDir = Join-Path $worktree "var\test-results\OPS-03\$runId"
New-Item -ItemType Directory -Path $runDir -ErrorAction Stop | Out-Null
$password = $env:ASSETOPS_PG_PASSWORD
if (-not $password) { $password = 'assetops-local-dev' }
$env:ASSETOPS_WORKTREE = $worktree
$env:OPS03_RUN_ID = $runId
$env:ASSETOPS_PROFILE_TARGETS = ($Targets -join "`n")
$env:ASSETOPS_PROFILE_IDLE = if ($Idle) { '1' } else { '' }
$env:ASSETOPS_CONTAINER_TEST_DATABASE_URL =
    'postgresql+psycopg://assetops:{0}@postgres-test:5432/assetops_test' -f [uri]::EscapeDataString($password)
& docker @composeArgs up -d --no-recreate --wait postgres-test
if ($LASTEXITCODE -ne 0) { throw 'postgres-test did not start healthy' }
$runner = "assetops-profile-$runId"
$p = Start-Process docker -ArgumentList ($composeArgs + @('run', '--rm', '-T', '--no-deps', '--name', $runner,
    'backend-test-runner')) -NoNewWindow -PassThru -RedirectStandardOutput (Join-Path $runDir 'stdout.log') `
    -RedirectStandardError (Join-Path $runDir 'stderr.log')
[void]$p.Handle
if (-not $p.WaitForExit($CapMinutes * 60000)) {
    & docker kill $runner 2>&1 | Out-Null
    Write-Output "HANG: profile run passed $CapMinutes min"
}
Get-Content (Join-Path $runDir 'stdout.log') -Tail 10
Write-Output "profile run $runId -> $runDir"
