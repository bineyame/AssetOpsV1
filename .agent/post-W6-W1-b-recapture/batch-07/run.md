# post-W6 W1-b recapture, batch 07 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. Vite http://localhost:5185, CDP 9525, AUDIT_REVISION=2af5fef6.
- Producer: the batch 06 run (seed.py cold excursion into assetops_w1brc_b06_test, API 18131). Fixed UUIDs.
- Capture: frozen `post-W6-audit/batch-07/tools/capture-b7.mjs` unchanged; `targets-excursion.json` (cold-financials and cold-assumptions, no-selection).
- Pairs: 4 captured / 4 selected. Claims 24/24. No console errors, no gap. measure.json added.
- DB dropped; API stopped by PID (see batch 06).
