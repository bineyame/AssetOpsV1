# post-W6 shell recapture, batch 14 (capture-only)

- SHA 06e019ba (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=06e019ba.
- Capture tool: frozen `.agent/post-W6-audit/batch-14/tools/capture-b14.mjs`, unchanged; filtered `targets-positive.json` here, written by the frozen `batch-14/tools/mk_targets.py positive <manifest> <scratch>` from THIS run's manifest, then filtered to the selected cases and pointed at localhost:5181 (was 127.0.0.1:5184).
- Producer (reviewed, unmodified), shared with batch 15 (one producer run serves both): `tools/w502_cold_work_walkthrough.py --work var/w502b_shellrc1415 --tag shellrc1415` prepare (all five modes, none blocked), serve, attest (ATTEST OK), drop. DBs `w502b_{positive,worstcase,pending,stale,unknown}_shellrc1415_test` are the producer's documented `*_test` names, created and dropped by its own modes; `pg_database` held no w502b DB first. Logs are in `../batch-15/w502-*.log`.
- Ports: serve hard-codes API 8971-8977 (no override exists). They were checked free before prepare and serve, so there was no wait. Vite 5181 with ASSETOPS_API_PORT=8971 (positive).
- Pairs: 8 captured / 8 selected (all-open: cooling, cold-health, cold-scenarios, cold-work). 48/48 claims, no console errors, no gap.
- Vite (PID 18600) exited by itself after this part (see batch 15). The producer's drop stopped its API PIDs and dropped all its DBs.
