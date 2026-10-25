# post-W6 W1-b recapture, batch 06 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. API 127.0.0.1:18131, Vite http://localhost:5185 (ASSETOPS_API_PORT=18131), CDP 9525, AUDIT_REVISION=2af5fef6.
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=.../assetops_w1brc_b06_test PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py cold excursion` (DB created first). API: `host/` `python -m uvicorn lab_app:app --port 18131`, DATABASE_URL = that DB, PYTHONPATH = this worktree. The same seed served batch 07.
- Capture: frozen `post-W6-audit/batch-06/tools/capture-b6.mjs` unchanged; `targets-excursion.json` (cold-finding start-excursion). Fixed UUIDs, no remap.
- Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap. measure.json added.
- DB dropped; API stopped by PID.
