# Start one uvicorn API (fresh random cursor key) on $Port over $Db; records PID in logs/pids.txt.
param([string]$Name, [int]$Port, [string]$Db, [string]$App = "assetops_backend.main:app", [string]$AppDir = "")
$wt = "C:\Users\assef\Bineyame\AssetOpsV1-review8"
$b = "$wt\.agent\post-W6-W6-evidence\b19"
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { "PORT_BUSY $Port"; return }
$env:PYTHONPATH = "$wt;$wt\backend;$wt\contracts;$wt\gateway;$wt\simulator;$wt\host"
$env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$Db"
$bytes = New-Object byte[] 32; [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$env:ASSETOPS_WORK_CURSOR_KEY_HEX = ($bytes | ForEach-Object { $_.ToString("x2") }) -join ""
$a = @("-m","uvicorn",$App,"--port","$Port","--host","127.0.0.1","--log-level","warning")
if ($AppDir -ne "") { $a += @("--app-dir",$AppDir) }
$p = Start-Process -FilePath "C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe" -ArgumentList $a -WorkingDirectory "$wt\backend" -RedirectStandardOutput "$b\logs\api-$Name.log" -RedirectStandardError "$b\logs\api-$Name.err" -PassThru -WindowStyle Hidden
Add-Content "$b\logs\pids.txt" "api-$Name $($p.Id) port $Port"
for ($i = 0; $i -lt 80; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$Port/api/sites" -TimeoutSec 3; break } catch { if ($_.Exception.Response) { break } }; Start-Sleep -Milliseconds 500 }
"API $Name pid $($p.Id) port $Port"
