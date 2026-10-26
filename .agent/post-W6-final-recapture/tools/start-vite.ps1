param([int]$ApiPort,[int]$WebPort,[string]$PidFile,[string]$Log)
$env:ASSETOPS_API_PORT = "$ApiPort"
$p = Start-Process -FilePath "npm.cmd" -ArgumentList "run","dev","--","--port","$WebPort","--strictPort" -WorkingDirectory "C:\Users\assef\Bineyame\AssetOpsV1-plan2\frontend" -WindowStyle Hidden -RedirectStandardOutput $Log -RedirectStandardError "$Log.err" -PassThru
$p.Id | Out-File -Encoding ascii $PidFile
