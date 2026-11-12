# Lane rules — night of 11→12 Nov (Thursday demo moved to 14:00)

Every builder/runner/reviewer agent tonight follows these:

- **Stop by 12:00 Thu 12 Nov.** Commit what you have and update your packet with exact resume points before 11:45. At 12:00 the coordinator runs the demo runbook; no DB jobs after that until ~16:00.
- **Never touch the demo:** DB `assetops_polish_client7_test` (and `assetops_polish_client6_test`, `assetops_demo3_full_test`), worktree `C:\Users\assef\Bineyame\AssetOpsV1-e3e`, ports 5490/8990. DBs allowed: other `*_test` and `<prefix>_audit*` only. Credentials assetops/assetops-local-dev at 127.0.0.1:55432.
- **Memory:** the laptop has ~3 GB free. Before any Postgres test file, parity run or prebuild, check free memory (`Get-CimInstance Win32_OperatingSystem` FreePhysicalMemory); below 1.5 GB, wait (use a Monitor until-loop, not sleep) — do not start it. Run Postgres test files ONE at a time. Parity on `client4` (≈13 min), not client7.
- **Shell:** never pass -ExecutionPolicy. Kill processes by PID only. Files via Write/Edit only — no heredocs, sed -i, `>>`, Set-Content, WriteAllText. No subagents. No sleep polling.
- **Git:** work in your own worktree; first bring main in with `git merge main` (resolve conflicts, never rebase-rewrite published history); commit with `git add -f` for `.agent`; messages end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Never push. Never merge to main (coordinator merges).
- **PYTHONPATH (added 05:00):** run Postgres files via `tools/run-host-tests.ps1` (sets the path and refuses stale imports), or set PYTHONPATH by hand to the worktree's `backend;backend\tests;contracts;simulator;gateway;field;host;tools`. Without `gateway`, chain fixtures start a stale gateway from the old AssetOPsV1 checkout and cold/EV tests fail with `outcomes == []` (FIX-cold-ev-fixtures packet, 810023eee) — that is environment, not a regression.
- **Python:** `C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe`; check-all: `tools\check-all.ps1 -Python <that python>` (19 guards).
- **Questions:** batch them in your report; do not design around a gap — state it.
- Report in ≤15 lines: done / not done / test results with counts / resume point.
