# (Re)start the b19 Vite on 5393 against $ApiPort (stops only $OldVitePid) and capture one phase.
param([string]$Phase, [int]$ApiPort, [int]$OldVitePid = 0, [switch]$KeepVite, [string]$Out = "")
if ($Out -eq "") { $Out = "part-$Phase" }
$wt = "C:\Users\assef\Bineyame\AssetOpsV1-review8"
$b = "$wt\.agent\post-W6-W6-evidence\b19r"
if ($OldVitePid -gt 0) { try { Stop-Process -Id $OldVitePid -Force -ErrorAction Stop } catch {}; Start-Sleep -Seconds 2 }
if (Get-NetTCPConnection -State Listen -LocalPort 5393 -ErrorAction SilentlyContinue) { "VITE_PORT_BUSY"; return }
$env:ASSETOPS_API_PORT = "$ApiPort"
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5393","--strictPort","--host","127.0.0.1" -WorkingDirectory "$wt\frontend" -RedirectStandardOutput "$b\logs\vite-$Phase.log" -RedirectStandardError "$b\logs\vite-$Phase.err" -PassThru -WindowStyle Hidden
Add-Content "$b\logs\pids.txt" "vite-$Phase $($p.Id)"
"VITE_PID $($p.Id)"
for ($i = 0; $i -lt 60; $i++) { $c = & curl.exe -s -m 5 -o NUL -w "%{http_code}" "http://127.0.0.1:5393/mockups/v69/index.html"; if ($c -eq "200") { break }; Start-Sleep -Seconds 1 }
New-Item -ItemType Directory -Force "$b\$Out" | Out-Null
$env:AUDIT_REVISION = "6f54ad1b"; $env:ASSETOPS_CDP_PORT = "9642"
Set-Location $b
node tools/capture-b19.mjs "$Out" "tools/targets-$Phase.json" *> "logs\capture-$Out.log"
Get-Content "logs\capture-$Out.log" -Tail 1
if (-not $KeepVite) { try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch {} ; "VITE_STOPPED $($p.Id)" }
