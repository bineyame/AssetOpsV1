# stops the process tree that listens on the given port (this agent's uvicorn: venv launcher parent + child)
param([int]$Port)
$c = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue
foreach($x in $c){ $p=Get-CimInstance Win32_Process -Filter "ProcessId=$($x.OwningProcess)"; $par=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.ParentProcessId)"
 $t = if($par -and $par.CommandLine -match 'uvicorn'){ $par.ProcessId } else { $p.ProcessId }
 "kill $t (port $Port)"; taskkill /PID $t /T /F | Out-Null }
