# Coordinator handoff — 2026-11-07 (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to the lane's Architect (Claude subagent, reused via SendMessage until moderate context). Builders = fresh implementers (Opus for pre-flight/first build, Sonnet for continuation/fix rounds); first reviews Opus, re-reviews Sonnet; coordinator verifies mechanically-checkable closures. Merge with `git merge --no-ff` on ACCEPT, then run `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background from the PowerShell tool (17 guards, ~25 min). Its wrapper exit code proves nothing: read the log's last line.

## Current plan
- Plan doc: `Docs/demo-sprint/client-demo-plan.html`. Build sheets `.agent/build-sheet-*.md` (rulings appended at the end of each). Architect standing context: `.agent/architect-handoff-demo-plan-2026-11-04.md`. Backlog: `.agent/backlog-post-demo.md` (next free id BL-40; Architects have reused ids, check before accepting). Lows: `.agent/demo-sprint-lows-2026-10-31-pipeline.md`.
- Scope rule SCOPE-1 (owner 2026-11-05): only what we present defensibly to first clients; everything else → backlog.
- ~106.7 of ~109.95 units merged. Plan rows for sizes are not yet updated: CH-6b3 2.2, DD-1a2 2.25, DD-1b1 1.5, DD-1b2 2.25, DD-1 11.5.
- Recent main merges: DD-1a2 (`1dd3b1862`), CH-6b3 (`f7c045bee`), DD-1b1 (`aaea00962`). Guards passed after DD-1a2 and CH-6b3; a check-all run after DD-1b1 was started at this write — rerun it if no result is recorded.

## In flight (as of this write)
- DD-1b2 (`task/DD-1b2-finish-rehearsal`, worktree `AssetOpsV1-dd1b2`): pre-flight builder running. Its Architect must be a fresh lane-2 instance, starting from `build-sheet-DD-1.md` DD1b1-R3 §6, DD1b1-R4 and DD1b1-R "Owed to DD-1b2".

## Remaining
- Lane 1: done. Lane 2: DD-1b2 (2.25), then CH-5d1 (1, fresh Architect).
- Then DS-1 demo script, then end-game E1–E6 (merge freeze → full suite → one prepare/baseline B-22 → finish/coherence/perf incl. E4 stored-hit check → captures incl. layout evidence at 1440/390 owed by CH-5b3, CH-6a3, CH-6b2 → owner walkthrough). Hold one rerun of E3 (up to 3 h) in reserve: E3 is the first whole-list test (DD1b1-R4).
- The mechanism `states` template is stale on merged main; expect one rebuild (~1300 s) before its next use.

## Carry into DS-1 (none is checked against a script yet)
- Start each normal day at 6am: the script explains the battery jump; no client screen does (DD1a2-R3). The 4am generator run on the 7 before-days is needed, about 1 L; do not claim the mill change saves a litre.
- Closing live day is `normal` on S+2 and reads partly checked; `add-day` refuses a full day there (`FULL_DAY_AFTER_TRIAL`). Other kinds on S+2 are unguarded and unmeasured: use `normal`. Tick right after the add, before showing the board, or it reads REASSESSMENT_PENDING.
- Mill "before" is authored example data: "more daytime use", not the same work moved. Kobo's money is mill sales (WK-2a 42.08 USD); the generator problem carries no fuel money figure.
- Cold and EV: open from the printed story-day links. A Portfolio site-name click lands on the latest event, without the Action row (BL-39 if the owner dislikes it). No live Cold add-day: it turns the Portfolio landing to Watch.
- Portfolio stays on week and month story links; one later day conflicts (lane-1 BL-36). Month table shows three Verified rows beside "1 fix confirmed". Longer build shows extra Finding history entries: a script line.

## For the owner's walkthrough
6am jump note on screen; three Verified rows; "days checked" on count lines; Portfolio click (BL-39); Cold/EV Portfolio rows "No action agreed yet" against ST-4/5 "in hand" (F-THREADS reports it). Owner told that the generator story has no fuel money and may overrule.

## Owner decisions this sprint (verbatim files in `.agent/`)
owner-scope-backlog-2026-11-05, owner-mill-pass-margin-2026-11-05 (10% above baseline), owner-kobo-nights-2026-11-06, owner-build-time-2026-11-06 (16 days history), owner-cold-days-2026-11-06 (partly checked), owner-kobo-partial-days-2026-11-07 (generator/trial days partly checked; R16 hybrid), owner-dd1a2-answers-2026-11-07 (6am start; write the mill "before"), owner-efficiency-2026-11-05 and -2026-11-06.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game (owner). Localised tests only; polish clones (`tools/chain_clone.py`, standard procedure) allowed. Don't run `test_demo_combined_postgres`. Exceptions ruled: DD-1b2's trimmed three-Site prepare on its own `*_test` DB.
- DBs: `*_test` and `<prefix>_audit*` only; polish read-only, never ticked; never touch `assetops_demo3_full_test`; never write into `AssetOpsV1-polC`. DB host 127.0.0.1:55432. Route every test to its own DB: never `fresh_database()` against the shared `assetops_test`. Do not guess credentials.
- NEVER pass any `-ExecutionPolicy` flag (ps1 guards blocked under bash → run from the PowerShell tool). Kill processes by PID only. Never stop keep-awake (restarted 2026-11-06 with `-MaxHours 168`). Edits Write/Edit only (no sed/heredoc/Set-Content for files); stage explicit paths. Never tune numbers.
- PYTHONPATH absolute: worktree `backend;contracts;tools;simulator;gateway;host;field` (+ `backend\tests;host\tests` for host tests); python `AssetOpsV1-plan2\.venv\Scripts\python.exe`; set `ASSETOPS_GUARD_PYTHON`. Run vitest by listing files or a folder (`vitest related` breaks on a .py). Worktrees have no `frontend/node_modules`.
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>".
- Efficiency rules: `.ai/ROLE_CONFIG.md` "Token Efficiency" (demo-sprint additions 2026-11-05 and -06). MD-0 template rebuild once per piece; CH-6b3 used two, disclosed to the owner.
- Reviews have repeatedly found what code-reading rulings missed: ask for a measurement when a ruling depends on an unrun path.

## Restart guidance
Restart the coordinator session only when no agents are running. On resume: read this file, then `git log --oneline -15` on main, then the in-flight worktrees' `.agent/*-handoff.md` / packets / review files.
