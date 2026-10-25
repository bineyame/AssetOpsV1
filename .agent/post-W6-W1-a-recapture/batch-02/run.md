# post-W6 W1-a recapture, batch 02 (capture-only)

- SHA 56d36bf2 (task/post-W6-W1-a), captured 2026-10-25. API 127.0.0.1:18121 (one producer at a time; s501 internal TLS/HTTP 18122-18123), Vite http://localhost:5183 from this worktree's frontend/ (ASSETOPS_API_PORT=18121, `npm.cmd run dev -- --port 5183 --strictPort`), CDP 9523.
- Capture tool: frozen `.agent/post-W6-audit/batch-02/tools/capture-b2.mjs`, unchanged; filtered `targets-*.json` here (origin 5182 -> 5183); AUDIT_REVISION=56d36bf2.
- dispatch: frozen `run_renamed_producer.py tools/s3_dispatch_walkthrough.py s3walk-renames.json -- prepare | serve --port 18121` (renames = frozen s3walk.json with DB `assetops_w1arc_b02_s3walk_test`, work `%LOCALAPPDATA%/AssetOps/w1arc-b2-s3walk`). Copy upgraded 0019 -> 0035 with `alembic upgrade head` (as frozen, schema only). No drop mode: DB dropped and work folder removed by this agent. Dispatch IDs come from the copied `assetops_s3cases` DB, so the frozen URLs were used unchanged.
- evidence-analysis / record-opened: `tools/s302_claim_limit_walkthrough.py --db assetops_s302_audit --work var/s302_w1arc --port 18121 prepare|serve|drop`. 5 revisions remapped positionally from frozen `logs/s302-serve.log` to `s302-serve.log`. Record-opened: first record of `GET /api/sites/KOBO-001/evidence/records` = 5267a80c-baa3-4101-9b26-35a8e13856bc (frozen 1687c876 cannot be matched one to one).
- mini: `tools/s5_overview_walkthrough.py prepare|serve|tick|drop --db assetops_s501_owner_audit --work var/s501_owner_w1arc --api-port 18121 --tls-port 18122 --http-port 18123` (prepare 239 s, 0 failed checks; one tick before capture).
- Pairs: 42 captured / 42 selected (dispatch 14, evidence 14, evidence-record 2, mini 12). Claims 84/84, 84/84, 12/12, 72/72. No console errors, no gap.
- A first mini capture process exited 127 right after Chrome started (no pair written; `capture-mini.try1.log` kept); rerun passed.
- window-id-as-revision now shows the refusal "This assessment cannot be shown as 15-minute blocks" with an "Open this day" link (no blank page).
- All DBs dropped; all spawned API PIDs stopped by PID (Vite stays up for later batches, stopped at the end).
