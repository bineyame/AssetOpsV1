# Restart the batch-16 Vite (port 5186) against one W504 API port and capture one phase. Stops only the PID it started.
param([string]$Phase, [int]$ApiPort, [int]$OldVitePid)
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review5"
$b = "$root\.agent\post-W6-audit\batch-16"
if ($OldVitePid -gt 0) { try { Stop-Process -Id $OldVitePid -Force -ErrorAction Stop } catch {} }
Start-Sleep -Seconds 2
$env:ASSETOPS_API_PORT = "$ApiPort"
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5186","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$Phase.log" -RedirectStandardError "$b\logs\vite-$Phase.err" -PassThru -WindowStyle Hidden
"VITE_PID $($p.Id)"
for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5186/mockups/v69/index.html" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
New-Item -ItemType Directory -Force "$b\part-$Phase" | Out-Null
$env:AUDIT_REVISION = "cb79b18b"; $env:ASSETOPS_CDP_PORT = "9526"
Set-Location $b
node tools/capture-b16.mjs "part-$Phase" "tools/targets-$Phase.json" *> "logs\capture-$Phase.log"
Get-Content "logs\capture-$Phase.log" -Tail 1
