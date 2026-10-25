# post-W6 W1-a recapture, batch 13 (capture-only)

- SHA 56d36bf2 (task/post-W6-W1-a), captured 2026-10-25. Producer API 127.0.0.1:9761 (hard-coded by the producer; checked free, the shell agent's batch 13 had finished), Vite http://localhost:5183 from this worktree's frontend/ restarted with ASSETOPS_API_PORT=9761, CDP 9523, AUDIT_REVISION=56d36bf2.
- Capture tool: frozen `.agent/post-W6-audit/batch-13/tools/capture-b13.mjs`, unchanged; `targets-one.json` here.
- Targets: `tools/gen_targets.py` (the shell recapture's generator, origin changed to localhost:5183) executes the frozen `batch-13/tools/mk_targets.py` unchanged, so Opportunity/Finding IDs come from THIS run's `var/w403_b13/positive.json`; filtered to the 2 selected part-one cases.
- Producer (reviewed, unmodified): `PYTHONPATH=backend;backend/tests;contracts;gateway;simulator;host .venv/Scripts/python.exe tools/w403_mini_decisions_walkthrough.py --db assetops_w1arc_b13_test --work var/w403_b13` (DB created first): prepare, serve, replay-positive, [part-one], drop. The later frozen phases (producer capture positive/late, replay-late) were not needed: no selected pair is in part-stocked or part-late.
- IDs: Opportunity 9c2f231c-93a5-4a29-a953-9301277cf1fc (MG-W402-001); Finding b635dba5-ad42-4cda-8bca-76bde6762555 rev 2dfd805c-a888-4814-a7c5-d612a31fec78 (KOBO-001 alternatives).
- Pairs: 4 captured / 4 selected (opportunity-finding supported-current, alternatives db-time-409). Claims 24/24. No console errors, no gap.
- `drop` removed the DB and work folder; serve and Vite stopped by PID.
