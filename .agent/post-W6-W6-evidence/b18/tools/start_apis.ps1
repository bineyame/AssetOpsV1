# W6 recapture (cap-b18), from batch 18: one plain product API (assetops_backend.main:app, the W6-01 run_state.sh server form) per producer DB.
# Records Windows PIDs in logs/pids.txt. Stops nothing. Capture-only: it serves already-seeded DBs.
param([string]$Specs = "18601:inc,18602:maint,18603:prev,18604:op,18605:zero,18606:hist,18607:stress,18608:linked,18609:absent")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review8"
$b = "$root\.agent\post-W6-W6-evidence\b18"
$py = "C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root;$root\backend;$root\contracts;$root\gateway;$root\simulator;$root\host"
foreach ($s in $Specs.Split(",")) {
  $port, $tag, $app = $s.Split(":", 3)
  if (-not $app) { $app = "assetops_backend.main:app" }
  $env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$(if ($tag -like "*_test") { $tag } else { "assetops_w601_w6r18${tag}_test" })"
  $env:ASSETOPS_WORK_CURSOR_KEY_HEX = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
  $args2 = @("-m","uvicorn",$app,"--host","127.0.0.1","--port",$port,"--log-level","warning")
  if ($app -like "api_*") { $sub = "C4"; if ($app -like "api_empty*") { $sub = "E2" }; $dir = "$root\.agent\W6-01-evidence\$sub"; $args2 += "--app-dir"; $args2 += $dir }
  $p = Start-Process -FilePath $py -ArgumentList $args2 -WorkingDirectory "$root\backend" -RedirectStandardOutput "$b\logs\api-$port-$tag.log" -RedirectStandardError "$b\logs\api-$port-$tag.err" -PassThru -WindowStyle Hidden
  "API $port $tag $app $($p.Id)" | Out-File -Append -Encoding utf8 "$b\logs\pids.txt"
  "$port $tag $($p.Id)"
}
