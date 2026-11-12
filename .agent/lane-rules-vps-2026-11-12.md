# Lane rules — VPS (Ubuntu, 24 GB, 8 vCPU), from 2026-11-12 evening

Supersedes the laptop-specific parts of `lane-rules-2026-11-12.md` (stop-by-12:00, memory checks, Windows paths). Everything else there still applies.

- **Paths.** Main checkout `/opt/assetecon/AssetOpsV1` (branch `main`, coordinator only). Your worktree: `/opt/assetecon/AssetOpsV1-<lane>` (e.g. `-sr4`). `frontend/node_modules` in each worktree is a symlink to main's — do not run `npm ci`/`npm install` in a worktree; tell the coordinator if a dependency differs.
- **Python.** `/opt/assetecon/AssetOpsV1/.venv/bin/python` (editable installs point at the main checkout). ALWAYS set `PYTHONPATH` to your worktree's `backend:backend/tests:contracts:simulator:gateway:field:host:tools` (colon-separated, absolute) so your branch's code is imported, not main's.
- **Guards.** `pwsh -NoProfile -File tools/check-all.ps1 -Python /opt/assetecon/AssetOpsV1/.venv/bin/python` → "All 19 guards passed." Set `ASSETOPS_GUARD_PYTHON` to the same python.
- **vitest.** From your worktree's `frontend/`: `npx vitest run <file>` — one file or a small named set at a time; no full suites (test-suite policy).
- **Database.** Postgres in Docker `assetopsv1-postgres-1` at 127.0.0.1:55432, assetops/assetops-local-dev. Only `*_test` and `<prefix>_audit*` DBs. Postgres test files and parity runs ONLY when the coordinator says the DB is available and your turn has come (one heavy job at a time); until then, do code + no-DB tests and list the Postgres steps as pending in your packet.
- **Shell.** bash. Long jobs: `nohup … > log 2>&1 &` or `setsid`; wait with a Monitor until-loop, never sleep-polling. Kill by PID only. Edit files with Write/Edit.
- **Git.** Own worktree; `git merge main` to bring main in (never rebase published history); commit with `git add -f` for `.agent`; messages end `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Never push, never merge to main (coordinator does both).
- **No subagents. Questions:** batch them in your report; never design around a gap — state it.
- **Report** in ≤15 lines: done / not done / test results with counts / resume point.
