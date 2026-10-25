# post-W6 shell recapture, batch 09 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-09/tools/capture-b9.mjs`, unchanged; filtered `targets-complete.json` here.
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/<db> PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py` `ev complete` into `assetops_shellrc_b09_test` (createdb first). API: `host/` `uvicorn lab_app:app --port 18101` (DATABASE_URL = the DB), Vite ASSETOPS_API_PORT=18101. (PID 14896)
- IDs: fixed UUIDs; no remap.
- Pairs: 10 captured / 10 selected (ev, ev-assumptions, ev-evidence, ev-evidence-analysis, ev-financials). 60/60 claims pass, no console errors, no gap.
- DB dropped; API stopped by PID.
