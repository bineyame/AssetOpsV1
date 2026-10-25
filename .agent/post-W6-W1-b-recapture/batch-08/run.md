# post-W6 W1-b recapture, batch 08 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. API 127.0.0.1:18131, Vite http://localhost:5185, CDP 9525, AUDIT_REVISION=2af5fef6.
- Producer (reviewed, unmodified): `seed.py ev interrupted` into `assetops_w1brc_b08_test` (env as batch 06). API `host/` uvicorn lab_app:app --port 18131.
- Capture: frozen `post-W6-audit/batch-08/tools/capture-b8.mjs` unchanged; `targets-interrupted.json` (ev-finding interrupted). Fixed UUIDs.
- Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap. measure.json added.
- DB dropped; API stopped by PID.
