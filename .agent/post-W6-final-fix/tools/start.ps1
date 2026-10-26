# start.ps1 <apiPort> <vitePort> <pidfile> <logdir> : start Vite detached, record PID
param($Api,$Vite,$PidFile,$Log)
$env:ASSETOPS_API_PORT=$Api
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port",$Vite,"--strictPort","--host","127.0.0.1" -WorkingDirectory "C:\Users\assef\Bineyame\AssetOpsV1-review10\frontend" -RedirectStandardOutput "$Log.out" -RedirectStandardError "$Log.err" -WindowStyle Hidden -PassThru
$p.Id | Out-File -Encoding ascii $PidFile
