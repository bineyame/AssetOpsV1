# Runs the remaining batch-15 phases in one process (the per-phase child form blocked on an inherited stdout pipe).
# Restarts Vite 5185 per mode with ASSETOPS_API_PORT; stops only the Vite PIDs it (or the first run) started.
param([int]$OldVitePid = 0, [string]$Phases = "worstcase:8972,pending:8973,stale:8974,unknown:8975,forbidden:8976,unavailable:8977")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review6"
$b = "$root\.agent\post-W6-audit\batch-15"
$old = $OldVitePid
foreach ($ph in $Phases.Split(",")) {
  $name, $port = $ph.Split(":")
  if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} ; Start-Sleep -Seconds 2 }
  $env:ASSETOPS_API_PORT = "$port"
  $p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5185","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$port.log" -RedirectStandardError "$b\logs\vite-$port.err" -PassThru -WindowStyle Hidden
  "VITE_PID $name $($p.Id)"
  $old = $p.Id
  for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5185/api/sites" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
  New-Item -ItemType Directory -Force "$b\part-$name" | Out-Null
  $env:AUDIT_REVISION = "1e3e9e8a"; $env:ASSETOPS_CDP_PORT = "9525"
  Set-Location $b
  if (Test-Path "tools/targets-$name-warm.json") { & node tools/capture-b15.mjs "$($env:TEMP)/b15-warm-$name" "tools/targets-$name-warm.json" > "logs\capture-$name-warm.log" 2>&1 }  # warm-up only, outside the batch folder, not counted
  & node tools/capture-b15.mjs "part-$name" "tools/targets-$name.json" > "logs\capture-$name.log" 2>&1
  "DONE $name " + (Get-Content "logs\capture-$name.log" -Tail 1)
}
if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} }
"ALL_DONE"
