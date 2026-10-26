#!/bin/sh
# swap-vite.sh <apiPort> <phase> : stop recorded Vite npm PID tree (by PID), start plain npm.cmd Vite on 5189 -> apiPort
API=$1; PH=$2
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-19
B='C:\Users\assef\Bineyame\AssetOpsV1-plan2\.agent\post-W6-final-recapture\batch-19'
OLD=$(cat vite.pid 2>/dev/null | tr -d '\r\n ')
[ -n "$OLD" ] && taskkill //PID $OLD //T //F >/dev/null 2>&1 && echo "stopped vite $OLD"
sleep 2
powershell.exe -NoProfile -Command "\$env:ASSETOPS_API_PORT='$API'; \$p = Start-Process -FilePath npm.cmd -ArgumentList 'run','dev','--','--port','5189','--strictPort' -WorkingDirectory 'C:\Users\assef\Bineyame\AssetOpsV1-plan2\frontend' -WindowStyle Hidden -RedirectStandardOutput '$B\logs\vite-$PH.log' -RedirectStandardError '$B\logs\vite-$PH.err' -PassThru; \$p.Id | Out-File -Encoding ascii '$B\vite.pid'; \$p.Id"
for i in $(seq 1 60); do c=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:5189/mockups/v69/index.html); [ "$c" = "200" ] && { echo "vite up"; break; }; sleep 1; done
