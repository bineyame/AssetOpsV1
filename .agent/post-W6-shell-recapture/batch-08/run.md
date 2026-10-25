# post-W6 shell recapture, batch 08 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-08/tools/capture-b8.mjs`, unchanged; filtered `targets-interrupted.json`, `targets-inventory.json` here.
- Producer (reviewed, unmodified): `ASSETOPS_TEST_TEMPLATE=0 ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:...@127.0.0.1:55432/<db> PYTHONPATH=backend;backend/tests;gateway;simulator;contracts;host .venv/Scripts/python.exe .agent/W2-F-evidence/seed.py` `ev interrupted` into `assetops_shellrc_b08_test` (createdb first). API: `host/` `uvicorn lab_app:app --port 18101` (DATABASE_URL = the DB), Vite ASSETOPS_API_PORT=18101. (PID 18276)
- inventory: the frozen run reseeded `ev interrupted` in place before its inventory check; here the one `ev interrupted` seed served both parts (same producer state, fixed UUIDs).
- IDs: fixed UUIDs (Finding ...025b unchanged); no remap.
- Pairs: 12 captured / 12 selected (interrupted 10, inventory 2). Claims 60/60 and 12/12.
- Console: ev-readiness stocked (1440, 390) logs React "two children with the same key" warnings (Allocated power limit / Energy metering / Fault events / Connector power / Connector status source); also in the frozen run. No crash.
- DB dropped; API stopped by PID.
