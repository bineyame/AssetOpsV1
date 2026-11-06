# Coordinator handoff — 2026-11-06 (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to the lane's Architect (Claude subagent, reused via SendMessage until moderate context). Builders = fresh implementers (Opus for pre-flight/first build, Sonnet for continuation/fix rounds); first reviews Opus, re-reviews Sonnet; coordinator verifies mechanically-checkable closures. Merge with `git merge --no-ff` on ACCEPT, then run `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background (17 guards).

## Current plan
- Plan doc: `Docs/demo-sprint/client-demo-plan.html` (current). Build sheets `.agent/build-sheet-*.md` (rulings appended at the end of each). Architect standing context: `.agent/architect-handoff-demo-plan-2026-11-04.md`. Backlog: `.agent/backlog-post-demo.md` (BL-01..BL-16). Lows: `.agent/demo-sprint-lows-2026-10-31-pipeline.md`.
- Scope rule SCOPE-1 (owner 2026-11-05): only what we present defensibly to first clients; everything else → backlog; any new work must state why it is defensibility-critical.
- ~82.5 of ~101.25 units merged. Main head ≈ `608b4c1c1`.

## In flight (as of this write)
- **Lane 1 — CH-6a3 fix round R2b** (Grow layout per mock v70, per-part days lines, always-present Target, 3-col grid → 1 col at 760px, MD-CH6-1..3 + MD-CH6-7). Worktree `AssetOpsV1-ch6a3`, branch `task/CH-6a3-composers` (stacked on CH-6a2; merges together). R2a backend done at `1e274a14b`. After R2b: one fresh Claude re-review of the whole CH-6a2+6a3 against `.agent/review-CH-6a2-6a3.md` + CH6a3-R2, then merge.
- **Lane 2 — DD-1a1 builder 6** implementing DD1a1-R5 (one stream/epoch per Site-day; gateway probe first), then finishing R3 L2 checks, mill day, Q8, Cold failure day, guards, packet. Worktree `AssetOpsV1-dd1a1`, branch `task/DD-1a1-steady-fullday`. Rulings DD1a1-R..R5 at end of `build-sheet-DD-1.md`. Diagnosis `.agent/DD-1a1-trial-anchor-diagnosis.md` in the worktree.

## Remaining after these
- Lane 1: CH-6b1 (1.75), CH-6b2 (2.25), CH-6b3 (1.0) — see `build-sheet-CH-6.md` build units + SCOPE-1.
- Lane 2: DD-1a2 (2.0, story-night placement, B-22 list, FILL-1 forward-only), DD-1b1 (1.25, story-time mill Action record→complete→link→freeze, evaluator call), DD-1b2 (1.5, drain, finish rows, F-THREADS incl. mill VERIFIED + Grow money/price end-to-end, rehearsal, M2 trigger-cost measurement), CH-5d1 (1).
- Then DS-1 demo script, then end-game E1–E6 (merge freeze → full suite → one prepare/baseline B-22 ~1.8–2.9 h → finish/coherence/perf incl. the E4 stored-hit check in `.agent/review-CH-5c.md` → captures incl. layout evidence → owner walkthrough).

## Owner decisions this sprint (verbatim files in `.agent/`)
owner-scope-backlog-2026-11-05.md (SCOPE-1 + three borderline answers), owner-mill-pass-margin-2026-11-05.md (10% above baseline), owner-kobo-nights-2026-11-06.md (Architect-designed nights; show pre-dawn generator start, idle fuel → BL-16), owner-efficiency-2026-11-05.md and -2026-11-06.md.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game (owner). Localised tests only; polish clones (`tools/chain_clone.py`, standard: create → migrate → backfill a–d → settle) are allowed. Don't run `test_demo_combined_postgres`.
- DBs: `*_test` only; polish read-only, never ticked; never touch `assetops_demo3_full_test`; never write into `AssetOpsV1-polC`. DB host 127.0.0.1:55432.
- NEVER pass any `-ExecutionPolicy` flag. Kill processes by PID only. Never stop keep-awake. Never write `.py` via PowerShell Set-Content. Never tune numbers.
- PYTHONPATH absolute: worktree `backend;contracts;tools;simulator;gateway;host;field`; python `AssetOpsV1-plan2\.venv\Scripts\python.exe`; set `ASSETOPS_GUARD_PYTHON`.
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>".
- Efficiency rules: `.ai/ROLE_CONFIG.md` "Token Efficiency" (demo-sprint additions 2026-11-05 and -06).

## Restart guidance
Restart the coordinator session only when no agents are running (both in-flight pieces finished or handed off). On resume: read this file, then `git log --oneline -15` on main, then the in-flight worktrees' `.agent/*-handoff.md` / packets.
