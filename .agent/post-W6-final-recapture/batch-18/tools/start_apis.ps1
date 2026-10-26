# Batch 18: one plain product API (assetops_backend.main:app, the W6-01 run_state.sh server form) per W6-01 producer DB.
# Records Windows PIDs in logs/api-pids.txt. Stops nothing. Capture-only: it serves already-seeded DBs.
param([string]$Specs = "18801:inc,18802:maint,18803:prev,18804:op,18805:zero,18806:hist,18807:stress,18808:linked,18809:absent")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review6"
$b = "$root\.agent\post-W6-audit\batch-18"
$py = "$root\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root;$root\backend;$root\contracts;$root\gateway;$root\simulator;$root\host"
foreach ($s in $Specs.Split(",")) {
  $port, $tag, $app = $s.Split(":", 3)
  if (-not $app) { $app = "assetops_backend.main:app" }
  $env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/$(if ($tag -like "*_test") { $tag } else { "assetops_w601_b18${tag}_test" })"
  $env:ASSETOPS_WORK_CURSOR_KEY_HEX = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
  $args2 = @("-m","uvicorn",$app,"--host","127.0.0.1","--port",$port,"--log-level","warning")
  if ($app -like "api_*") { $sub = "C4"; if ($app -like "api_empty*") { $sub = "E2" }; $dir = "$root\.agent\W6-01-evidence\$sub"; $args2 += "--app-dir"; $args2 += $dir }
  $p = Start-Process -FilePath $py -ArgumentList $args2 -WorkingDirectory "$root\backend" -RedirectStandardOutput "$b\logs\api-$port-$tag.log" -RedirectStandardError "$b\logs\api-$port-$tag.err" -PassThru -WindowStyle Hidden
  "$port $tag $app $($p.Id)" | Tee-Object -Append "$b\logs\api-pids.txt"
}
