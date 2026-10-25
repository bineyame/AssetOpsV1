# post-W6 shell recapture, batch 11 (capture-only) — NON-QUALIFYING DIAGNOSTIC EVIDENCE (closeout ruling 4)

- SHA 321cfe56 (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=321cfe56.
- Capture tool: frozen `.agent/post-W6-audit/batch-11/tools/capture-b11.mjs`, unchanged; filtered `targets-w302-partial-week.json` here.
- Producer (reviewed): `.agent/W3-02-evidence/serve.py` through the frozen `run_renamed_producer.py` with `w302-renames.json` (one rename: hard-coded DB `w302j_test` -> `assetops_shellrc_b11_test`, created first). PYTHONPATH backend;gateway;simulator;contracts;host. Hard-coded API 127.0.0.1:9751 (checked free). Then `POST /__capture/empty-site` (the producer's reviewed control for this case).
- Vite 5181 with ASSETOPS_API_PORT=9751.
- Pairs: 6 captured / 6 selected (globalevidence, globalfinancials, portfolio). 34/36 claims: portfolio 1440/390 "same panel count" fails because Portfolio refuses (503) under this producer, as in the frozen run (B11-16). No console errors, no gap.
- DB dropped WITH (FORCE); producer (PID 6868) and Vite (PID 30792) stopped by PID. A later 9751 listener (PID 6064, serve-financials.py, w302w_test) belongs to another agent and was not touched.

## Replacement run ledger (closeout ruling 4, 2026-10-25, SHA ac2e9b4f)

- **Status of the run above: NON-QUALIFYING DIAGNOSTIC EVIDENCE.** It used the forbidden name-rewriting `run_renamed_producer.py`. Its images are kept here only as diagnostic material; every pair below is a capture gap for the Q24/current-SHA audit verdict.
- Producer: `.agent/W3-02-evidence/serve.py`, unmodified. No `<prefix>_audit` mode; it hard-codes `w302j_test`.
- Not attempted: creating the producer's hard-coded DB is the same action the classifier refused for batch 10 (see `batch-10/run.md`), and the DTO fallback was refused as a bypass. It was not retried under another form.
- Pairs: 0 qualifying / 6 selected (globalevidence, globalfinancials, portfolio w302-partial-week x 1440/390). **6 capture gaps.**
- No wrapper, renamed producer, edited producer or alternate DB name was used or tried. No DB was created; nothing to drop. No server was started for this batch.

## Unmodified-producer replacement capture (2026-10-25, SHA d5349d6d) — QUALIFYING

- Authorization: `.agent/owner-test-db-authorization-2026-10-25.md`. Branch `task/post-W6-shell-gap-recapture` at current main (d5349d6d), AUDIT_REVISION=d5349d6d.
- DB: `CREATE DATABASE w302j_test`, dropped `WITH (FORCE)` after capture.
- Producer: `.venv/Scripts/python.exe .agent/W3-02-evidence/serve.py`, unmodified, run directly. PYTHONPATH backend;gateway;simulator;contracts;host. Hard-coded API 127.0.0.1:9751 (checked free). Then `POST /__capture/empty-site` (the producer's reviewed control for this case). PID 26312, stopped by PID.
- Vite 5181 (this worktree's frontend/, ASSETOPS_API_PORT=9751), CDP 9521; stopped by PID tree.
- Capture: frozen `.agent/post-W6-audit/batch-11/tools/capture-b11.mjs`, unchanged, same filtered `targets-w302-partial-week.json`. 34/36 claims: portfolio 1440/390 "same panel count" fails because Portfolio refuses under this producer, exactly as in the frozen run (B11-16). No console errors.
- Output: `replacement/part-w302-partial-week/`.
- Pairs: **6 qualifying / 6 selected**, titles = frozen, no index flags.
