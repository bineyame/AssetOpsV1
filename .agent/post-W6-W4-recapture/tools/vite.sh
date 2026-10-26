#!/bin/sh
# vite.sh <api-port> <vite-port>
cd "$(dirname "$0")/../../../frontend" || exit 1
ASSETOPS_API_PORT="$1" exec node node_modules/vite/bin/vite.js --port "$2" --strictPort --host 127.0.0.1
