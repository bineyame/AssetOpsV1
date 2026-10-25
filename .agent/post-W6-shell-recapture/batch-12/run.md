# post-W6 shell recapture, batch 12 (capture-only) — NON-QUALIFYING DIAGNOSTIC EVIDENCE (closeout ruling 4)

- SHA 06e019ba (task/post-W6-shell), captured 2026-10-25. Vite http://localhost:5181 from this worktree's frontend/, CDP 9521 (ASSETOPS_CDP_PORT=9521), AUDIT_REVISION=06e019ba.
- Capture tool: frozen `.agent/post-W6-audit/batch-12/tools/capture-b12.mjs`, unchanged; filtered `targets-main.json` here (selected cases only, origin 127.0.0.1:5182 -> localhost:5181).
- Producer (reviewed): `.agent/W4-02-evidence/seed.py` through the frozen `batch-02/tools/run_renamed_producer.py` with `w402-renames.json` (one rename: hard-coded DB `w402r_test` -> `assetops_shellrc_b12_test`, created first). PYTHONPATH backend;backend/tests;gateway;simulator;contracts;host. Result: accepted positive 3321 / missing-conflicting 326, selections 123, jobs 123. The seed rewrites the tracked `replay.json`; copied to `replay-b12.json` here and restored with `git checkout`.
- API: `host/` `uvicorn lab_app:app` 127.0.0.1:18101 (DATABASE_URL = the DB). Vite 5181 with ASSETOPS_API_PORT=18101.
- IDs: routes use the site code MG-W402-001; no remap.
- First capture attempt (`capture-main.log` overwritten) lost Vite mid-run (bash-backgrounded npx exited 127); Vite relaunched detached and the whole part recaptured.
- Pairs: 8 captured / 8 selected (gap-limited: renewable, service, fuel, backup). 48/48 claims, no console errors, no gap.
- DB dropped WITH (FORCE); API (PID 19144) stopped by PID. Vite (PID 17212) kept for batch 13 and stopped after it.

## Replacement run ledger (closeout ruling 4, 2026-10-25, SHA ac2e9b4f)

- **Status of the run above: NON-QUALIFYING DIAGNOSTIC EVIDENCE.** It used the forbidden name-rewriting `run_renamed_producer.py`. Its images are kept here only as diagnostic material; every pair below is a capture gap for the Q24/current-SHA audit verdict.
- Producer: `.agent/W4-02-evidence/seed.py`, unmodified. No `<prefix>_audit` mode; it hard-codes `w402r_test`.
- Not attempted, for the same reason as batch 11 (refusals recorded in `batch-10/run.md`).
- Pairs: 0 qualifying / 8 selected (renewable, service, fuel, backup gap-limited x 1440/390). **8 capture gaps.**
- No wrapper, renamed producer, edited producer or alternate DB name was used or tried. No DB was created; nothing to drop. No server was started for this batch.

## Unmodified-producer replacement capture (2026-10-25, SHA d5349d6d) — QUALIFYING

- Authorization: `.agent/owner-test-db-authorization-2026-10-25.md`. Branch `task/post-W6-shell-gap-recapture` at current main (d5349d6d), AUDIT_REVISION=d5349d6d.
- DB: `CREATE DATABASE w402r_test`, dropped `WITH (FORCE)` after capture.
- Producer: `.venv/Scripts/python.exe .agent/W4-02-evidence/seed.py`, unmodified, run directly (exit 0). PYTHONPATH backend;backend/tests;gateway;simulator;contracts;host. Result: accepted positive 3321 / missing-conflicting 326, selections 123, jobs 123 (same as the diagnostic run). The seed rewrites tracked `replay.json`: copied to `replacement/replay-b12.json`, restored with `git checkout`.
- API: `host/` `python -m uvicorn lab_app:app` 127.0.0.1:18101, DATABASE_URL=w402r_test (PID 14896). Vite 5181, ASSETOPS_API_PORT=18101; CDP 9521. Both stopped by PID.
- Capture: frozen `.agent/post-W6-audit/batch-12/tools/capture-b12.mjs`, unchanged, same filtered `targets-main.json`. 48/48 claims, no console errors.
- Output: `replacement/part-main/`.
- Pairs: **8 qualifying / 8 selected**, titles = frozen, no index flags.
