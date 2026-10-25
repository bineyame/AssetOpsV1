# W6 recapture (cap-b18) phase driver, from batch 18: restarts Vite 5388 per phase with ASSETOPS_API_PORT; stops only the Vite PIDs it started.
param([string]$Phases = "inc:18601,maint:18602,prev:18603,op:18604,zero:18605,hist:18606,stress:18607,linked:18608,absent:18609", [switch]$Warm)
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review8"
$b = "$root\.agent\post-W6-W6-evidence\b18"
$old = 0; $first = [bool]$Warm
foreach ($ph in $Phases.Split(",")) {
  $name, $port = $ph.Split(":")
  if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} ; Start-Sleep -Seconds 2 }
  $env:ASSETOPS_API_PORT = "$port"
  $p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","5388","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$b\logs\vite-$name.log" -RedirectStandardError "$b\logs\vite-$name.err" -PassThru -WindowStyle Hidden
  "VITE $name $($p.Id)" | Out-File -Append -Encoding utf8 "$b\logs\pids.txt"
  $old = $p.Id
  for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5388/" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
  New-Item -ItemType Directory -Force "$b\part-$name" | Out-Null
  $env:AUDIT_REVISION = "f3da6e90"; $env:ASSETOPS_CDP_PORT = "9638"
  Set-Location "$b\tools"
  if ($first) { & node capture-b18.mjs "$($env:TEMP)\w6r18-warm" "targets-zero.json" > "..\logs\capture-warm.log" 2>&1; $first = $false }  # warm-up only, outside the evidence folder, not counted
  & node capture-b18.mjs "..\part-$name" "targets-$name.json" > "..\logs\capture-$name.log" 2>&1
  "DONE $name " + (Get-Content "..\logs\capture-$name.log" -Tail 1)
}
if ($old -gt 0) { try { Stop-Process -Id $old -Force -ErrorAction Stop } catch {} }
"ALL_DONE"
