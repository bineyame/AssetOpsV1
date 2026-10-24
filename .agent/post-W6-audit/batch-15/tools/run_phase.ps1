# Restart the batch-15 Vite (port 5185) against one W502 API port and capture one phase. Stops only the PID it started.
param([string]$Phase, [int]$ApiPort, [int]$OldVitePid)
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review6"
$b = "$root\.agent\post-W6-audit\batch-15"
if ($OldVitePid -gt 0) { try { Stop-Process -Id $OldVitePid -Force -ErrorAction Stop } catch {} }
Start-Sleep -Seconds 2
$env:ASSETOPS_API_PORT = "$ApiPort"
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5185","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$ApiPort.log" -RedirectStandardError "$b\logs\vite-$ApiPort.err" -PassThru -WindowStyle Hidden
"VITE_PID $($p.Id)"
for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5185/api/sites" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
New-Item -ItemType Directory -Force "$b\part-$Phase" | Out-Null
$env:AUDIT_REVISION = "1e3e9e8a"; $env:ASSETOPS_CDP_PORT = "9525"
Set-Location $b
node tools/capture-b15.mjs "part-$Phase" "tools/targets-$Phase.json" *> "logs\capture-$Phase.log"
Get-Content "logs\capture-$Phase.log" -Tail 1
