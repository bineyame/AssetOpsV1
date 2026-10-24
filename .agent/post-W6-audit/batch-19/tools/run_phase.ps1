# Batch 19: (re)start one uvicorn on 18901 over a W6-01 *_test DB (production composition, or the reviewed test-only
# api_403/api_503 compositions under .agent/W6-01-evidence/C2|C4), then capture one target phase through the
# long-running batch-19 Vite (5189 -> 18901). Stops only the uvicorn PID it is given/started.
param([string]$Phase, [string]$Db, [string]$App = "assetops_backend.main:app", [string]$AppDir = "", [int]$OldApiPid = 0, [switch]$NoCapture)
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review5"
$b = "$root\.agent\post-W6-audit\batch-19"
if ($OldApiPid -gt 0) { try { Stop-Process -Id $OldApiPid -Force -ErrorAction Stop } catch {} ; Start-Sleep -Seconds 2 }
$env:PYTHONPATH = "$root;$root\backend;$root\contracts;$root\gateway;$root\simulator;$root\host"
$env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$Db"
$bytes = New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:ASSETOPS_WORK_CURSOR_KEY_HEX = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
$args2 = @("-m","uvicorn",$App,"--port","18901","--host","127.0.0.1","--log-level","warning")
if ($AppDir -ne "") { $args2 += @("--app-dir",$AppDir) }
$p = Start-Process -FilePath "$root\.venv\Scripts\python.exe" -ArgumentList $args2 -WorkingDirectory "$root\backend" -RedirectStandardOutput "$b\logs\uvicorn-$Phase.log" -RedirectStandardError "$b\logs\uvicorn-$Phase.err" -PassThru -WindowStyle Hidden
"API_PID $($p.Id)"
for ($i = 0; $i -lt 80; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:18901/api/sites" -TimeoutSec 3; break } catch { if ($_.Exception.Response) { break } }; Start-Sleep -Milliseconds 500 }
if ($NoCapture) { return }
New-Item -ItemType Directory -Force "$b\part-$Phase" | Out-Null
$env:AUDIT_REVISION = "731126a9"; $env:ASSETOPS_CDP_PORT = "9529"
Set-Location $b
node tools/capture-b19.mjs "part-$Phase" "tools/targets-$Phase.json" *> "logs\capture-$Phase.log"
Get-Content "logs\capture-$Phase.log" -Tail 1
