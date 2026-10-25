# post-W6 shell recapture, batch 13 (capture-only)

- SHA 06e019ba (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=06e019ba.
- Capture tool: frozen `.agent/post-W6-audit/batch-13/tools/capture-b13.mjs`, unchanged; filtered `targets-{one,stocked,late}.json` here.
- Targets: `tools/gen_targets.py` executes the frozen `batch-13/tools/mk_targets.py` unchanged (output redirected here), so Opportunity/Finding IDs and the relative windows come from THIS run's `var/w403_b13/positive.json`/`replay.json`; then filters to the selected cases and swaps origin 127.0.0.1:5183 -> localhost:5181.
- Producer (reviewed, unmodified): `tools/w403_mini_decisions_walkthrough.py --db assetops_shellrc_b13_test --work var/w403_b13` (createdb first), PYTHONPATH backend;backend/tests;contracts;gateway;simulator;host. Order as frozen: prepare, serve, replay-positive, [part-one], `capture --web http://localhost:5181 --phase positive` (98 checks; seeds the stock), [part-stocked], replay-late, `capture --phase late` (459 checks), [part-late], drop.
- Ports: producer hard-codes API 9761 and its own capture CDP 9763 (both checked free). Vite 5181 with ASSETOPS_API_PORT=9761.
- Pairs: 32 captured / 32 selected (part-one 18: 6 incidents + 3 maintenance cases; part-stocked 4; part-late 10). Claims 108/108, 24/24, 60/60. No console errors, no gap.
- `drop` removed the DB and work folder; serve (PID 6916) and Vite (PID 28660) stopped by PID.
