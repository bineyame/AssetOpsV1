# Coordinator handoff — 2026-11-06 (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to the lane's Architect (Claude subagent, reused via SendMessage until moderate context). Builders = fresh implementers (Opus for pre-flight/first build, Sonnet for continuation/fix rounds); first reviews Opus, re-reviews Sonnet; coordinator verifies mechanically-checkable closures. Merge with `git merge --no-ff` on ACCEPT, then run `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background (17 guards, ~25 min).

## Current plan
- Plan doc: `Docs/demo-sprint/client-demo-plan.html`. Build sheets `.agent/build-sheet-*.md` (rulings appended at the end of each). Architect standing context: `.agent/architect-handoff-demo-plan-2026-11-04.md`. Backlog: `.agent/backlog-post-demo.md` (BL-01..BL-22; next free id BL-23 — Architects have reused ids, check before accepting). Lows: `.agent/demo-sprint-lows-2026-10-31-pipeline.md`.
- Scope rule SCOPE-1 (owner 2026-11-05): only what we present defensibly to first clients; everything else → backlog.
- ~100.75 of ~107.5 units merged. Recent main merges: CH-6b1 (`8133f5b95`), FIX-MAIN-4 (`864d27b67`), DD-1a1 (`eae5174b7`), CH-6b2 (`0e40b22cb`). Guards passed after DD-1a1; a check-all run after CH-6b2 was started at this write — rerun it if no result is recorded.

## In flight (as of this write)
- Nothing. Both lanes idle. Next: lane 1 CH-6b3 (lane-1 Architect = Architect 27, light context, reuse via SendMessage if still reachable, else fresh); lane 2 DD-1a2 (fresh lane-2 Architect).

## Remaining
- Lane 1: CH-6b3 (1.0; owns CH-5a2b L1/L5 Lows, COH-17/18).
- Lane 2: DD-1a2 (2.0: story-night placement, B-22 list — each steady day probed per day and added to `full_days` before carrying a complement; full-day guard to also check the complement chain + join to previous built day (DD-1a1 review residual); MILL-3 dry run; guard barring degraded days), DD-1b1 (1.25), DD-1b2 (1.5; drain, F-THREADS incl. mill VERIFIED, Grow money/price, MG-2, MILL-3 assertion, rehearsal measuring prepare with B-16 fallback if >3h, M2 trigger-cost), CH-5d1 (1). The lane-2 Architect must be a fresh instance (old one spent).
- Then DS-1 demo script, then end-game E1–E6 (merge freeze → full suite → one prepare/baseline B-22 → finish/coherence/perf incl. E4 stored-hit check → captures incl. layout evidence at 1440/390 owed by CH-5b3, CH-6a3, CH-6b2 → owner walkthrough).

## Owner decisions this sprint (verbatim files in `.agent/`)
owner-scope-backlog-2026-11-05, owner-mill-pass-margin-2026-11-05 (10% above baseline), owner-kobo-nights-2026-11-06, owner-build-time-2026-11-06 (16 days history), owner-cold-days-2026-11-06 (partly checked), owner-kobo-partial-days-2026-11-07 (generator/trial days partly checked; R16 hybrid), owner-efficiency-2026-11-05 and -2026-11-06.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game (owner). Localised tests only; polish clones (`tools/chain_clone.py`, standard procedure) allowed. Don't run `test_demo_combined_postgres`.
- DBs: `*_test` and `<prefix>_audit*` only; polish read-only, never ticked; never touch `assetops_demo3_full_test`; never write into `AssetOpsV1-polC`. DB host 127.0.0.1:55432.
- NEVER pass any `-ExecutionPolicy` flag (ps1 guards blocked under bash → run from the PowerShell tool). Kill processes by PID only. Never stop keep-awake. Edits Write/Edit only (no sed/heredoc/Set-Content for files). Never tune numbers.
- PYTHONPATH absolute: worktree `backend;contracts;tools;simulator;gateway;host;field` (+ `backend\tests;host\tests` for host tests); python `AssetOpsV1-plan2\.venv\Scripts\python.exe`; set `ASSETOPS_GUARD_PYTHON`. Run vitest by listing files (`vitest related` breaks on a .py).
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>".
- Efficiency rules: `.ai/ROLE_CONFIG.md` "Token Efficiency" (demo-sprint additions 2026-11-05 and -06).

## Restart guidance
Restart the coordinator session only when no agents are running. On resume: read this file, then `git log --oneline -15` on main, then the in-flight worktrees' `.agent/*-handoff.md` / packets / review files.
