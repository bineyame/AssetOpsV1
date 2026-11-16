#!/bin/bash
# Portable wrapper for the vNEXT browser audit (tools/audit.mjs).
#
# Required environment:
#   CHROME  path to a Chrome or Chromium executable
#   PW      path to a playwright-core package directory (e.g. node_modules/playwright-core)
# Optional:
#   AUDIT_LD_LIBRARY_PATH  extra shared-library directories, if Chromium needs them on this host
#   FONTCONFIG_FILE        fontconfig file, if the host has no system fonts
#
# Example:
#   npm install --prefix /tmp/pw playwright-core && npx --prefix /tmp/pw playwright install chromium
#   CHROME=$(ls -d ~/.cache/ms-playwright/chromium-*/chrome-linux/chrome | tail -1) \
#   PW=/tmp/pw/node_modules/playwright-core tools/run-audit.sh --shots
set -euo pipefail
: "${CHROME:?Set CHROME to a Chrome/Chromium executable (see the header of this script and README.md)}"
: "${PW:?Set PW to a playwright-core package directory (see the header of this script and README.md)}"
[ -x "$CHROME" ] || { echo "CHROME is not executable: $CHROME" >&2; exit 2; }
[ -d "$PW" ] || { echo "PW is not a directory: $PW" >&2; exit 2; }
if [ -n "${AUDIT_LD_LIBRARY_PATH:-}" ]; then export LD_LIBRARY_PATH="$AUDIT_LD_LIBRARY_PATH${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; fi
export CHROME PW
cd "$(dirname "$0")/.." && node tools/audit.mjs "$@"
