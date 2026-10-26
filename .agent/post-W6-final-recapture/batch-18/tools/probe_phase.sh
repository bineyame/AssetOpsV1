#!/bin/sh
cd /c/Users/assef/Bineyame/AssetOpsV1-plan2/.agent/post-W6-final-recapture/batch-18
node tools/probe-scrollers.mjs probe-tgt/targets-$1.json logs/probe-scrollers-$1.json 2>&1 | tail -n 20
