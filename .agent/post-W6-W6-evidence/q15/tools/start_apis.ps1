# cap-q15: plain product API (assetops_backend.main:app) per seeded DB; fresh random cursor key per start. Records PIDs.
param([string]$Specs = "18691:inc,18692:maint,18693:prev,18694:op,18695:stress,18696:stressb,18697:detail,18698:dhist,18699:dlinked")
$root = "C:\Users\assef\Bineyame\AssetOpsV1-review8"
$q = "$root\.agent\post-W6-W6-evidence\q15"
$py = "C:\Users\assef\Bineyame\AssetOpsV1\.venv\Scripts\python.exe"
$env:PYTHONPATH = "$root;$root\backend;$root\contracts;$root\gateway;$root\simulator;$root\host"
foreach ($s in $Specs.Split(",")) {
  $port, $tag = $s.Split(":")
  $env:DATABASE_URL = "postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_w601_w6q15${tag}_test"
  $env:ASSETOPS_WORK_CURSOR_KEY_HEX = -join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
  $p = Start-Process -FilePath $py -ArgumentList @("-m","uvicorn","assetops_backend.main:app","--host","127.0.0.1","--port",$port,"--log-level","warning") -WorkingDirectory "$root\backend" -RedirectStandardOutput "$q\logs\api-$port-$tag.log" -RedirectStandardError "$q\logs\api-$port-$tag.err" -PassThru -WindowStyle Hidden
  "API $port $tag $($p.Id)" | Tee-Object -Append "$q\logs\pids.txt"
}
