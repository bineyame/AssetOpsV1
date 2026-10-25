# post-W6 W1-a recapture, batch 06 (capture-only)

- SHA 56d36bf2 (task/post-W6-W1-a), captured 2026-10-25. API 127.0.0.1:18121, Vite http://localhost:5183 from this worktree's frontend/ (ASSETOPS_API_PORT=18121), CDP 9523, AUDIT_REVISION=56d36bf2.
- Capture tool: frozen `.agent/post-W6-audit/batch-06/tools/capture-b6.mjs`, unchanged; filtered `targets-excursion.json` here (cold-finding start-excursion only).
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/assetops_w1arc_b06_test PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py cold excursion` (DB created first). API: `host/` `python -m uvicorn lab_app:app --port 18121`, DATABASE_URL = that DB, PYTHONPATH = this worktree's backend;gateway;simulator;contracts;host.
- IDs: fixed seed UUIDs (Finding ...0176 unchanged); no remap.
- Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap.
- Retries (logs kept): try1 started the API without PYTHONPATH, so it imported the main checkout's simulator and failed to start (`api.try1.err.log`); the page read "Site unavailable" and those images were discarded. try2 capture process exited 127 right after Chrome started (no pair written). try3 passed.
- DB dropped; API stopped by PID.
