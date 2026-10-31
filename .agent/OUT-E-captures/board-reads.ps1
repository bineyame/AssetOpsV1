# OUT-E E5: serve each s602b case in turn and save its Kobo board read (API JSON) on the later day.
# Stops every process it started by PID (the serve wrapper and the two uvicorn listeners on 8986/8987).
$ErrorActionPreference = 'Stop'
$wt = 'C:\Users\assef\Bineyame\AssetOpsV1-outE'
Set-Location $wt
$out = "$wt\.agent\OUT-E-captures\board-reads"
New-Item -ItemType Directory -Force $out | Out-Null
$env:ASSETOPS_ESTATE_PORTFOLIO_CURSOR_KEY_HEX = ('0' * 64)
$env:ASSETOPS_WORK_CURSOR_KEY_HEX = ('1' * 64)
function Stop-Ports {
    foreach ($port in 8986, 8987) {
        $owners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($owner in $owners) { "stop pid $owner (port $port)"; Stop-Process -Id $owner -Force -ErrorAction SilentlyContinue }
    }
}
foreach ($case in $args) {
    $p = Start-Process -FilePath .venv\Scripts\python.exe -ArgumentList 'tools\s602b_verification_walkthrough.py', '--db', 'assetops_s602b_oute_audit', '--work', 'var/s602b_oute', 'serve', '--port', '8986', '--web-port', '5486', '--case', $case -RedirectStandardOutput "$out\serve-$case.log" -RedirectStandardError "$out\serve-$case.err.log" -PassThru -WindowStyle Hidden
    "serve $case pid $($p.Id)"
    $ok = $false
    for ($i = 0; $i -lt 120; $i++) {
        try { Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8987/api/health" -TimeoutSec 2 | Out-Null; $ok = $true; break } catch { Start-Sleep -Seconds 2 }
    }
    if ($ok) {
        $r = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8987/api/sites/KOBO-001/outcome-board?date=2026-11-02"
        [IO.File]::WriteAllText("$out\board-$case.json", $r.Content, (New-Object Text.UTF8Encoding $false))
        "saved $case ($($r.StatusCode))"
    } else { "case $case API did not start" }
    Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
    Stop-Ports
    Start-Sleep -Seconds 2
}
