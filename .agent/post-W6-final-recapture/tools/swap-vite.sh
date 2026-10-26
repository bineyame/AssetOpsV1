#!/bin/sh
# swap-vite.sh <NN> <apiPort> <phase> : kill recorded npm PID tree (by PID), start plain npm.cmd Vite on 518<d> (one start per call)
NN=$1; API=$2; PH=$3; D=${NN#1}
B="C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\post-W6-final-recapture\batch-$NN"
OLD=$(cat batch-$NN/vite.pid 2>/dev/null)
[ -n "$OLD" ] && taskkill //PID $OLD //T //F >/dev/null 2>&1
sleep 2
powershell.exe -NoProfile -Command "\$env:ASSETOPS_API_PORT='$API'; \$p = Start-Process -FilePath npm.cmd -ArgumentList 'run','dev','--','--port','518$D','--strictPort' -WorkingDirectory 'C:\Users\assef\Bineyame\AssetOpsV1-plan2\frontend' -WindowStyle Hidden -RedirectStandardOutput '$B\logs\vite-$PH.log' -RedirectStandardError '$B\logs\vite-$PH.err' -PassThru; \$p.Id | Out-File -Encoding ascii '$B\vite.pid'; \$p.Id"
