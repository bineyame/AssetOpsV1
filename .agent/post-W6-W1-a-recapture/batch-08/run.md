# post-W6 W1-a recapture, batch 08 (capture-only)

- SHA 56d36bf2 (task/post-W6-W1-a), captured 2026-10-25. API 127.0.0.1:18121, Vite http://localhost:5183 from this worktree's frontend/ (ASSETOPS_API_PORT=18121), CDP 9523, AUDIT_REVISION=56d36bf2.
- Capture tool: frozen `.agent/post-W6-audit/batch-08/tools/capture-b8.mjs`, unchanged; filtered `targets-interrupted.json` here (ev-finding interrupted only).
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/assetops_w1arc_b08_test PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py ev interrupted` (DB created first). API: `host/` `python -m uvicorn lab_app:app --port 18121`, DATABASE_URL = that DB, PYTHONPATH = this worktree's backend;gateway;simulator;contracts;host.
- IDs: fixed seed UUIDs (Finding ...025b unchanged); no remap.
- Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap.
- DB dropped; API stopped by PID.
