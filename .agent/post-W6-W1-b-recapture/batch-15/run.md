# post-W6 W1-b recapture, batch 15 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. The first pass recorded a gap because ports 8971-8977 were forbidden. The coordinator corrected that (the ban came from an old brief) and allowed 8971-8977 for this capture only if all were free. All seven were checked free with netstat before serve.
- Producer (reviewed, unmodified): `tools/w502_cold_work_walkthrough.py --work var/w502b_w1brc15 --tag w1brc15` prepare (EXIT 0) / serve (7 healthy APIs on 8971-8977) / drop. DBs `w502b_<mode>_w1brc15_test` (none existed first).
- Vite http://localhost:5185 restarted with ASSETOPS_API_PORT=8971 (positive), CDP 9525, AUDIT_REVISION=2af5fef6. One warm-up read first (%TEMP%, not counted).
- Targets: frozen `batch-15/tools/mk_targets.py positive <this run's manifest> gen`, filtered to cold-action all-open, origin 127.0.0.1:5185 -> localhost:5185. Action 0ae3398b-f434-4e1c-a9e7-e30d11420775.
- Capture: frozen `capture-b15.mjs` unchanged. Pairs: 2 captured / 2 selected. Claims 12/12. No console errors. Titles match frozen (Declared outcome criteria 292/433, Related activity 168/272). overflowX 0. No Site tab row; rail shows Actions. measure.json added.
- drop stopped all seven APIs and dropped the DBs and work folder. Vite stopped by PID. 8971-8977 confirmed free afterwards.
