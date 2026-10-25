# post-W6 W1-b recapture, batch 13 (capture-only, agent A)
- SHA 2af5fef6, 2026-10-25. Producer API 127.0.0.1:9761 (hard-coded by the producer with no override; checked free; not a forbidden port). Vite http://localhost:5185 restarted with ASSETOPS_API_PORT=9761, CDP 9525, AUDIT_REVISION=2af5fef6.
- Producer (reviewed, unmodified): `PYTHONPATH=backend;backend/tests;contracts;gateway;simulator;host .venv/Scripts/python.exe tools/w403_mini_decisions_walkthrough.py --db assetops_w1brc_b13_test --work var/w403_b13` prepare, serve, replay-positive, drop (DB created first).
- Targets: `tools/gen_targets.py one` (W1-a's generator, origin localhost:5185) runs frozen `batch-13/tools/mk_targets.py` unchanged on THIS run's positive.json, filtered to alternatives db-time-409. Finding 4a83b814-175e-4948-b3cb-02bd6614fbca rev d2f823b5-bb8e-4de0-9229-5c0da30ea427.
- Capture: frozen `capture-b13.mjs` unchanged. One warm-up read first (output in %TEMP%, not counted).
- Pairs: 2 captured / 2 selected. Claims 12/12. No console errors, no gap. measure.json added.
- drop removed DB and work folder; serve and Vite stopped by PID.
