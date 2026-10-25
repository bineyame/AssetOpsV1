# post-W6 W1-b recapture, batch 09 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. API 127.0.0.1:18131, Vite http://localhost:5185, CDP 9525, AUDIT_REVISION=2af5fef6.
- Producer (reviewed, unmodified): `seed.py ev complete` into `assetops_w1brc_b09_test` (env as batch 06). API `host/` uvicorn lab_app:app --port 18131.
- Capture: frozen `post-W6-audit/batch-09/tools/capture-b9.mjs` unchanged; `targets-complete.json` (ev-financials and ev-assumptions, complete). Fixed UUIDs.
- Pairs: 4 captured / 4 selected. Claims 24/24. No console errors, no gap. measure.json added.
- DB dropped; API stopped by PID.
- Post-fix (SHA e6af4ff0): the assumptions rep was recaptured into `part-*-fix` from a fresh seed (assetops_w1brc_b09_test, API 18131, dropped). Claims 12/12. It has no Interpretation history panel (Financial assumptions only), so no region and no cue. Heights are unchanged, overflowX is 0, titles = frozen.
