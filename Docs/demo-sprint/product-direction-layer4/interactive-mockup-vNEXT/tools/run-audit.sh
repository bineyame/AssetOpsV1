#!/bin/bash
# Portable wrapper for the Layer 4 mock-up browser audit (tools/audit.mjs), then regenerates the docs.
# Required: CHROME (Chrome/Chromium executable), PW (playwright-core package directory).
# Optional: AUDIT_LD_LIBRARY_PATH (extra shared-library dirs), FONTCONFIG_FILE (if the host has no system fonts).
#   npm install --prefix /tmp/pw playwright-core && npx --prefix /tmp/pw playwright install chromium
#   CHROME=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | tail -1) PW=/tmp/pw/node_modules/playwright-core tools/run-audit.sh --shots
set -euo pipefail
: "${CHROME:?Set CHROME}"; : "${PW:?Set PW}"
if [ -n "${AUDIT_LD_LIBRARY_PATH:-}" ]; then export LD_LIBRARY_PATH="$AUDIT_LD_LIBRARY_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; fi
export CHROME PW
cd "$(dirname "$0")/.." && node tools/audit.mjs "$@" && node tools/gen_docs.cjs
