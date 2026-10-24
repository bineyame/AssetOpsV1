# R373 recapture: optionally start one uvicorn (own port), start Vite 5189 -> ApiPort, capture a targets file, stop only these PIDs.
param([string]$Phase, [int]$ApiPort, [string]$Db = "", [string]$App = "assetops_backend.main:app", [string]$AppDir = "")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review4"
$b = "$root\.agent\post-W6-R373-recapture"
$py = "C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root;$root\backend;$root\contracts;$root\gateway;$root\simulator;$root\host"
$env:ASSETOPS_WORK_CURSOR_KEY_HEX = ("b3" * 32)
$apiPid = 0
if ($Db -ne "") {
  $env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$Db"
  $a = @("-m","uvicorn",$App,"--port","$ApiPort","--host","127.0.0.1","--log-level","warning")
  if ($AppDir -ne "") { $a += @("--app-dir",$AppDir) }
  $p = Start-Process -FilePath $py -ArgumentList $a -WorkingDirectory "$root\backend" -RedirectStandardOutput "$b\logs\uvicorn-$Phase.log" -RedirectStandardError "$b\logs\uvicorn-$Phase.err" -PassThru -WindowStyle Hidden
  $apiPid = $p.Id; "API_PID $apiPid"
}
for ($i = 0; $i -lt 80; $i++) { try { Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$ApiPort/api/sites" -TimeoutSec 3 | Out-Null; break } catch { if ($_.Exception.Response) { break } }; Start-Sleep -Milliseconds 500 }
$env:ASSETOPS_API_PORT = "$ApiPort"
$v = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5189","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$Phase.log" -RedirectStandardError "$b\logs\vite-$Phase.err" -PassThru -WindowStyle Hidden
"VITE_PID $($v.Id)"
for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5189/mockups/v69/index.html" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
New-Item -ItemType Directory -Force "$b\part-$Phase" | Out-Null
$env:AUDIT_REVISION = (git -C $root rev-parse --short HEAD); $env:ASSETOPS_CDP_PORT = "9529"
Set-Location "$root\.agent\post-W6-audit\batch-19"
node tools/capture-b19.mjs "$b\part-$Phase" "$b\targets-$Phase.json" *> "$b\logs\capture-$Phase.log"
Get-Content "$b\logs\capture-$Phase.log" -Tail 2
try { Stop-Process -Id $v.Id -Force } catch {}
if ($apiPid -gt 0) { try { Stop-Process -Id $apiPid -Force } catch {} }
"STOPPED"
