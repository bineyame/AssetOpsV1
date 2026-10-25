# cap-q15: per phase start Vite 5390 against that API port, run probe.mjs, then stop the Vite listening on 5390 (mine only).
param([string]$PhaseFile = "phases.txt")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review8"; $q = "$root\.agent\post-W6-W6-evidence\q15"
function Stop-MyVite { Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | ? { $_.LocalPort -eq 5390 } | % { $pp = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)"; if ($pp.CommandLine -like '*vite.js*--port*5390*') { Stop-Process -Id $pp.ProcessId -Force; "STOPPED_VITE $($pp.ProcessId)" | Out-File -Append -Encoding utf8 "$q\logs\pids2.txt" } }; Start-Sleep 2 }
$env:ASSETOPS_CDP_PORT = "9640"
foreach ($line in Get-Content "$q\tools\$PhaseFile") {
  if (-not $line.Trim()) { continue }
  $name, $port = $line.Trim().Split(" ")
  Stop-MyVite
  $env:ASSETOPS_API_PORT = $port
  $p = Start-Process -FilePath "C:\Program Files\nodejs\node.exe" -ArgumentList "node_modules/vite/bin/vite.js","--port","5390","--strictPort","--host","127.0.0.1" -WorkingDirectory "$root\frontend" -RedirectStandardOutput "$q\logs\vite-$name.log" -RedirectStandardError "$q\logs\vite-$name.err" -PassThru -WindowStyle Hidden
  for ($i = 0; $i -lt 60; $i++) { try { $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:5390/" -TimeoutSec 5; if ($r.StatusCode -eq 200) { break } } catch {}; Start-Sleep -Seconds 1 }
  $owner = (Get-NetTCPConnection -State Listen | ? { $_.LocalPort -eq 5390 }).OwningProcess
  "VITE $name api=$port started=$($p.Id) listener=$owner" | Tee-Object -Append "$q\logs\pids2.txt"
  Push-Location "$q\tools"
  & "C:\Program Files\nodejs\node.exe" probe.mjs "../part-$name" "v-$name.json" *> "$q\logs\probe-$name.log"
  "PHASE $name rc=$LASTEXITCODE"
  Pop-Location
}
Stop-MyVite
"ALL_DONE"
