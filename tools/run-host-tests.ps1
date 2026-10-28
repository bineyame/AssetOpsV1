# PERF-01 (R9, R2): the worktree-safe way to run focused Python tests on the Windows host.
#
#   tools\run-host-tests.ps1 [-Interpreter C:\path\to\python.exe] -- backend/tests/test_x_postgres.py -q [...]
#
# Why. The shared virtual environment's editable installs can point at another checkout: in AssetOpsV1-plan2\.venv
# `assetops_backend` resolved to the stale AssetOPsV1 checkout, so a run without the right PYTHONPATH tested old code
# or failed to import. This wrapper puts this worktree's packages first on PYTHONPATH, checks where every AssetOps
# package actually imports from, and refuses to run when any of them is outside this worktree.
#
# R2. Full and merge runs happen only in Docker (tools\run-backend-suite-in-container.ps1). This wrapper refuses a
# run with no target or with a directory target (a suite sweep) unless -AllowHostFull is given.
#
# Interpreter: -Interpreter, else $env:ASSETOPS_TEST_PYTHON, else $env:ASSETOPS_GUARD_PYTHON, else <worktree>\.venv.
# Database: ASSETOPS_TEST_DATABASE_URL as set; when unset, the shared development server's `assetops_test`
# (backend/TESTING.md). It never prints the URL.
# Plain (non-advanced) script parameters on purpose: every other argument, pytest flags included, lands in $args.
# Their names avoid prefixes of common pytest flags (-p, -q, -k, -m, -n, -x, -v, -s); put `--` before the pytest
# arguments when in doubt.
param([string]$Interpreter = '', [switch]$AllowHostFull)
$PytestArgs = @($args)
$ErrorActionPreference = 'Continue'
$worktree = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$Python = $Interpreter
if (-not $Python) { $Python = $env:ASSETOPS_TEST_PYTHON }
if (-not $Python) { $Python = $env:ASSETOPS_GUARD_PYTHON }
if (-not $Python) { $Python = Join-Path $worktree '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    Write-Output "REFUSED: no Python interpreter at '$Python' (pass -Interpreter or set ASSETOPS_TEST_PYTHON)."
    exit 2
}

$targets = @($PytestArgs | Where-Object { $_ -and -not $_.StartsWith('-') })
if (-not $AllowHostFull) {
    if ($targets.Count -eq 0) {
        Write-Output 'REFUSED: no test file named. Full runs go through tools\run-backend-suite-in-container.ps1 (R2).'
        exit 2
    }
    foreach ($t in $targets) {
        $path = ($t -split '::', 2)[0]
        if (Test-Path -LiteralPath (Join-Path $worktree $path) -PathType Container) {
            Write-Output "REFUSED: '$t' is a directory. Host runs are for focused files; use the Docker runner (R2)."
            exit 2
        }
    }
}

$roots = @('backend', 'contracts', 'simulator', 'gateway', 'host', 'field') | ForEach-Object { Join-Path $worktree $_ }
$env:PYTHONPATH = (($roots + @($env:PYTHONPATH)) | Where-Object { $_ }) -join ';'
if (-not $env:ASSETOPS_TEST_DATABASE_URL) {
    $password = $env:ASSETOPS_PG_PASSWORD
    if (-not $password) { $password = 'assetops-local-dev' }
    $port = $env:ASSETOPS_PG_PORT
    if (-not $port) { $port = '55432' }
    $env:ASSETOPS_TEST_DATABASE_URL =
        'postgresql+psycopg://assetops:{0}@127.0.0.1:{1}/assetops_test' -f [uri]::EscapeDataString($password), $port
}

# Import-origin check: every AssetOps package must come from this worktree. (No double quotes in the probe:
# Windows PowerShell 5.1 strips them from native arguments.)
$probe = "import importlib, os; " +
    "[print(n + '=' + os.path.realpath(importlib.import_module(n).__file__)) for n in " +
    "('assetops_backend', 'assetops_contracts', 'assetops_simulator', 'assetops_gateway', 'assetops_field')]"
$origins = & $Python -c $probe 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Output 'REFUSED: the AssetOps packages do not import with this worktree on PYTHONPATH:'
    $origins | ForEach-Object { "  $_" }
    exit 2
}
$prefix = (Resolve-Path $worktree).Path.TrimEnd('\') + '\'
$wrong = @($origins | Where-Object { $_ -match '=' } | Where-Object {
    -not (($_ -split '=', 2)[1]).StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase) })
if ($wrong.Count -gt 0 -or @($origins | Where-Object { $_ -match '=' }).Count -lt 5) {
    Write-Output "REFUSED: an AssetOps package imports from outside $worktree (stale editable install):"
    $origins | ForEach-Object { "  $_" }
    exit 2
}

Push-Location $worktree
try {
    & $Python -m pytest @PytestArgs
    $code = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $code
