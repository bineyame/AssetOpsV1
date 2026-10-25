# post-W6 shell recapture, batch 10 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-10/tools/capture-b10.mjs`, unchanged; filtered `targets-historical.json`, `targets-positive.json` here.
- Producer (reviewed): `.agent/W3-01-evidence/serve.py` run through the frozen `.agent/post-W6-audit/batch-02/tools/run_renamed_producer.py` with `w301-renames.json` (one rename: hard-coded DB `w301cap_test` -> `assetops_shellrc_b10_test`, created first; nothing else changed). PYTHONPATH backend;backend/tests;gateway;simulator;contracts;host.
- Ports: the producer hard-codes API 127.0.0.1:9741 (checked free first; another agent's W3-01 run had just ended). Vite 5181 with ASSETOPS_API_PORT=9741. No capture-control POSTs needed (historical and positive precede late-kobo/empty-site).
- historical: first attempt (`capture-historical.try1.log`, 40/48) showed "Choose a valid evidence cutoff": the producer's pinned clock (11:04, flowing with wall time) had not yet passed the frozen known_at 2026-11-02T11:08:27Z. Waited (polling `/__capture/clock`) until it did; rerun 48/48.
- Pairs: 10 captured / 10 selected (historical 8: findings, -cost, -risks, -opportunities; positive 2: actions empty-day, 12/12). No console errors, no gap.
- DB dropped WITH (FORCE); producer (PID 12092) and Vite (PID 10620) stopped by PID.
