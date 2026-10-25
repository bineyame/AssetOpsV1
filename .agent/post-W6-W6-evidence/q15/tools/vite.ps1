# cap-q15: start Vite 5390 for one API port (prints PID) or stop a PID.
param([string]$Api, [string]$Name, [int]$Stop = 0)
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review8"; $q = "$root\.agent\post-W6-W6-evidence\q15"
if ($Stop -gt 0) { try { Stop-Process -Id $Stop -Force -ErrorAction Stop; "stopped $Stop" } catch { "stop failed $Stop" }; exit }
$env:ASSETOPS_API_PORT = $Api
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5390","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$q\logs\vite-$Name.log" -RedirectStandardError "$q\logs\vite-$Name.err" -PassThru -WindowStyle Hidden
"VITE $Name $Api $($p.Id)" | Out-File -Append -Encoding utf8 "$q\logs\pids2.txt"
for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5390/" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
"VITE_PID $($p.Id)"
