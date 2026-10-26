# stops producer serve trees (root = the walkthrough python launched by this agent) matched by script name arg, plus optional vite pid file
param([string]$Script,[string]$VitePidFile="")
$all = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ?{ $_.CommandLine -match [regex]::Escape($Script) -and $_.CommandLine -match ' serve ' }
$ids = $all.ProcessId
$roots = $all | ?{ $ids -notcontains $_.ParentProcessId -and $_.CommandLine -notmatch 'uvicorn' }
foreach($r in $roots){ "kill root $($r.ProcessId)"; taskkill /PID $r.ProcessId /T /F | Out-Null }
if($VitePidFile -and (Test-Path $VitePidFile)){ $v=(Get-Content $VitePidFile).Trim(); "kill vite $v"; taskkill /PID $v /T /F | Out-Null }
