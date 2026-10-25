# post-W6 shell recapture, batch 11 (capture-only)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-11/tools/capture-b11.mjs`, unchanged; filtered `targets-w302-partial-week.json` here.
- Producer (reviewed): `.agent/W3-02-evidence/serve.py` through the frozen `run_renamed_producer.py` with `w302-renames.json` (one rename: hard-coded DB `w302j_test` -> `assetops_shellrc_b11_test`, created first). PYTHONPATH backend;gateway;simulator;contracts;host. Hard-coded API 127.0.0.1:9751 (checked free). Then `POST /__capture/empty-site` (the producer's reviewed control for this case).
- Vite 5181 with ASSETOPS_API_PORT=9751.
- Pairs: 6 captured / 6 selected (globalevidence, globalfinancials, portfolio). 34/36 claims: portfolio 1440/390 "same panel count" fails because Portfolio refuses (503) under this producer, as in the frozen run (B11-16). No console errors, no gap.
- DB dropped WITH (FORCE); producer (PID 6868) and Vite (PID 30792) stopped by PID. A later 9751 listener (PID 6064, serve-financials.py, w302w_test) belongs to another agent and was not touched.
