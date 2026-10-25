# post-W6 W1-b recapture, batch 17 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. Vite http://localhost:5185 restarted with ASSETOPS_API_PORT=18133, CDP 9525, AUDIT_REVISION=2af5fef6. One warm-up read first (%TEMP%, not counted).
- Producer (reviewed, unmodified): `W504_API_PORT_BASE=18132 tools/w504_ev_work_walkthrough.py --work var/w504a_w1brc17 --tag w1brc17` prepare / serve / attest / drop. DBs `w504a_{positive,zero,worstcase,unknown}_w1brc17_test` (none existed first). APIs: positive 18133, zero 18134, worstcase 18135, forbidden 18138, unavailable 18139 (stopped by attest). unknown/pending/stale unavailable (producer verdict).
- Targets: frozen `mk_targets.py positive <this run's manifest>` -> `gen/`, filtered to ev-action all-open, origin 127.0.0.1:5187 -> localhost:5185. Action 2494e4b1-3bf2-4dd3-b752-43c897c05820.
- Capture: frozen `capture-b17.mjs` unchanged. Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap. measure.json added (`measure.try1-early.log`: the first 1440 read ran before the page loaded, so it was rerun).
- drop stopped its API PIDs and dropped all four DBs and the work folder. Vite stopped by PID.
