# Batch 18 phase driver: restarts Vite 5188 per phase with ASSETOPS_API_PORT; stops only the Vite PIDs it started.
param([string]$Phases = "inc:18801,maint:18802,prev:18803,op:18804,zero:18805,hist:18806,stress:18807,linked:18808,absent:18809")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review6"
$b = "$root\.agent\post-W6-audit\batch-18"
$old = 0; $first = $true
foreach ($ph in $Phases.Split(",")) {
  $name, $port = $ph.Split(":")
  if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} ; Start-Sleep -Seconds 2 }
  $env:ASSETOPS_API_PORT = "$port"
  $p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5188","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$name.log" -RedirectStandardError "$b\logs\vite-$name.err" -PassThru -WindowStyle Hidden
  "VITE_PID $name $($p.Id)" | Tee-Object -Append "$b\logs\vite-pids.txt"
  $old = $p.Id
  for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5188/" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
  New-Item -ItemType Directory -Force "$b\part-$name" | Out-Null
  $env:AUDIT_REVISION = "f99bca2e"; $env:ASSETOPS_CDP_PORT = "9528"
  Set-Location "$b\tools"
  if ($first) { & node capture-b18.mjs "$($env:TEMP)\b18-warm" "targets-zero.json" > "..\logs\capture-warm.log" 2>&1; $first = $false }  # warm-up only, outside the batch folder, not counted
  & node capture-b18.mjs "..\part-$name" "targets-$name.json" > "..\logs\capture-$name.log" 2>&1
  "DONE $name " + (Get-Content "..\logs\capture-$name.log" -Tail 1)
}
if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} }
"ALL_DONE"
