# post-W6 shell recapture, batch 06 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-06/tools/capture-b6.mjs`, unchanged; filtered `targets-excursion.json` here.
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/<db> PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py` `cold excursion` into `assetops_shellrc_b06_test` (createdb first; the seed needs the DB to exist). API: `host/` `uvicorn lab_app:app --port 18101` (DATABASE_URL = the DB), Vite ASSETOPS_API_PORT=18101.
- IDs: the seed holds fixed UUIDs (hold_uuids), so the frozen Finding ...0176 is unchanged; no remap.
- The same seeded DB and API also served batch 07 part-excursion.
- Pairs: 12 captured / 12 selected (cold-finding, cold-foundation, cold-readiness, cold-sld, coldbackup, temperature). 72/72 claims pass, no console errors, no gap.
- DB dropped; API (PID 27644) and Vite (PID 4716) stopped by PID.
