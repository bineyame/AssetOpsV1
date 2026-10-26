param([int]$Api,[int]$Port)
$env:ASSETOPS_API_PORT="$Api"
$p = Start-Process -FilePath node -ArgumentList "node_modules/vite/bin/vite.js","--port","$Port","--strictPort","--host","127.0.0.1" -WorkingDirectory "C:\Users\assef\Bineyame\AssetOpsV1-review10\frontend" -RedirectStandardOutput "C:\Users\assef\Bineyame\AssetOpsV1-review10\.agent\post-W6-W5-EV\logs\vite-$Port.log" -RedirectStandardError "C:\Users\assef\Bineyame\AssetOpsV1-review10\.agent\post-W6-W5-EV\logs\vite-$Port.err" -PassThru -WindowStyle Hidden
"VITE_PID $($p.Id)"
