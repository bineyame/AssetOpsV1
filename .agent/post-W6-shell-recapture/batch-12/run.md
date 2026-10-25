# post-W6 shell recapture, batch 12 (capture-only)

- SHA 06e019ba (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=06e019ba.
- Capture tool: frozen `.agent/post-W6-audit/batch-12/tools/capture-b12.mjs`, unchanged; filtered `targets-main.json` here (selected cases only, origin 127.0.0.1:5182 -> localhost:5181).
- Producer (reviewed): `.agent/W4-02-evidence/seed.py` through the frozen `batch-02/tools/run_renamed_producer.py` with `w402-renames.json` (one rename: hard-coded DB `w402r_test` -> `assetops_shellrc_b12_test`, created first). PYTHONPATH backend;backend/tests;gateway;simulator;contracts;host. Result: accepted positive 3321 / missing-conflicting 326, selections 123, jobs 123. The seed rewrites the tracked `replay.json`; copied to `replay-b12.json` here and restored with `git checkout`.
- API: `host/` `uvicorn lab_app:app` 127.0.0.1:18101 (DATABASE_URL = the DB). Vite 5181 with ASSETOPS_API_PORT=18101.
- IDs: routes use the site code MG-W402-001; no remap.
- First capture attempt (`capture-main.log` overwritten) lost Vite mid-run (bash-backgrounded npx exited 127); Vite relaunched detached and the whole part recaptured.
- Pairs: 8 captured / 8 selected (gap-limited: renewable, service, fuel, backup). 48/48 claims, no console errors, no gap.
- DB dropped WITH (FORCE); API (PID 19144) stopped by PID. Vite (PID 17212) kept for batch 13 and stopped after it.
