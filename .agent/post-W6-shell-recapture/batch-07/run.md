# post-W6 shell recapture, batch 07 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-07/tools/capture-b7.mjs`, unchanged; filtered `targets-excursion.json` here.
- Producer: the batch 06 run (`ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/<db> PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py` `cold excursion`, DB `assetops_shellrc_b06_test`, API 18101). Fixed UUIDs; no remap.
- Pairs: 12 captured / 12 selected (no-selection: cold, cold-assumptions, cold-evidence, cold-evidence-analysis, cold-financials, cold-findings). 72/72 claims pass, no console errors, no gap.
- DB dropped; PIDs stopped by PID (see batch 06).
