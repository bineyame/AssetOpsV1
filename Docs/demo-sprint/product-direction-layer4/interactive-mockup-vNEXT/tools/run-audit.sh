#!/bin/bash
# Host-specific wrapper: Chromium from the session scratchpad with extracted shared libraries and fonts.
S=/tmp/claude-1001/-opt-assetecon-AssetOpsV1/fffff20f-2bc4-4558-ba83-bc7cc594e723/scratchpad
export LD_LIBRARY_PATH=$(cat $S/libs/ldpath) FONTCONFIG_FILE=$S/libs/fonts.conf CHROME=$S/pw/browsers/chromium-1140/chrome-linux/chrome PW=$S/pw/node_modules/playwright-core
cd "$(dirname "$0")/.." && node tools/audit.mjs "$@"
