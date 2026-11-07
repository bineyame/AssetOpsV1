# Coordinator handoff — 2026-11-07 afternoon (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to the lane's Architect (Claude subagent, reused via SendMessage until moderate context, then fresh). Builders = implementers (Opus for pre-flight/first build, Sonnet for continuation/fix rounds); first reviews Opus, re-reviews Sonnet; coordinator verifies mechanically-checkable and paper-only closures when the Architect rules so. Merge with `git merge --no-ff` on ACCEPT, then run `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background from the PowerShell tool, logging to the scratchpad (17 guards, ~25 min). Its wrapper exit code proves nothing: read the log's last line. In a worktree without `frontend/node_modules` the two missing-claim guards fail with MODULE_NOT_FOUND; they must pass on main.

## Current plan
- Plan doc: `Docs/demo-sprint/client-demo-plan.html`. Build sheets `.agent/build-sheet-*.md` (rulings appended at the end of each). Architect standing context: `.agent/architect-handoff-demo-plan-2026-11-04.md`. Backlog: `.agent/backlog-post-demo.md` (BL-43..50 recorded; next free BL-51; Architects have reused ids, check). Lows: `.agent/demo-sprint-lows-2026-10-31-pipeline.md`.
- Scope rule SCOPE-1 (owner 2026-11-05): only what we present defensibly to first clients; everything else → backlog.
- Units: about 111.2 of ~112.2 merged; 1.0 left (CH-5d1). Plan size rows NOT yet updated: CH-6b3 2.2, DD-1a2 2.25, DD-1b1 1.5, DD-1b2 4.5 (a 1.5 + b 3.0), DD-1 ≈13.0.
- Recent main merges: DD-1a2 (`1dd3b1862`), CH-6b3 (`f7c045bee`), DD-1b1 (`aaea00962`), DD-1b2a (`29efab1d0`), DD-1b2b (`1c2e5ed28`; check-all 17/17 after it). DD-1b2b test DBs `dd1b2`/`dd1b2d` and their var folders dropped.
- DD-1b2b record: rulings DD1b2-R8..R14 in `.agent/build-sheet-DD-1.md`; packet `.agent/review-packet-DD-1b2b.md`; reviews `review-DD-1b2b.md` (FIX) and `-r2.md` (ACCEPT). Rehearsal: 3585 s of 10800, min free RAM 3.07 GB, self-check 31/32 (CO-2 age-dependent, R11); EX-1 on a copy: add ~60 s, tick ~180 s, boards unchanged; mill RECURRED 10-31 ("Seen again" true); O14 96.4 → 22.4 quotable; O15 no fuel signal (no litres).

## In flight
- CH-5d1: fresh Architect pre-flight launched after the DD-1b2b merge.
- E3 owes (R11–R14): serve heartbeat sampling (≤240 s, else TICK_EVERY_SECONDS=60), post-add check, after tool (E3.2), browser path to "Target met" (E3.4), perf --record (E3.5); on any copy rerun S2 then Performance (Kobo) and assert AVAILABLE.
- Keep-awake: memory pressure reaped it once on 2026-11-07; owner said "restart both". Standing one restarted.

## Remaining
- CH-5d1 (1, fresh Architect).
- Then DS-1 demo script, then end-game E1–E6 (merge freeze → full suite → one prepare/baseline B-22 → finish/coherence/perf incl. E4 stored-hit check → captures incl. layout evidence at 1440/390 owed by CH-5b3, CH-6a3, CH-6b2 → owner walkthrough). Hold one rerun of E3 (up to 3 h) in reserve.
- The mechanism `states` template is stale on merged main; expect one rebuild (~1300 s) before its next use.

## Carry into DS-1 from DD-1b2b
Index of ruling sections (R13 §6): R6 §4, R6 §3 + R9 §2 + R11 §2 (add-day), Q7 block (build-sheet `:1561-1564`), R10 §4, R11 §1, R14 (S-8 and S-5 lines; Cold "Why?" avoid line + fallback). Present only from the prepare-built DB; start `serve`, wait for "ready:", leave it running; live add ≈5 min. Owner was offered COO/CFO extras (mill on board ~1–1.5, dollars on verdict page, BL-48 wording ~0.15, BL-50 Cold "Why?" ~0.25) — undecided.

## Carry into DS-1 (none is checked against a script yet)
- Start each normal day at 6am: the script explains the battery jump; no client screen does (DD1a2-R3). The generator runs ~15 min shortly before 6am on most before-days (not "from about 4am"; DD1b2-R4). Do not claim the mill change saves fuel (S-13 had the old pattern and 0 generator; no fuel rows).
- Live add on S+2: `add-day normal --assess-now` after 11:00Z, then `tick --until-drained`, then show the board (DD1b2-R6 §4 replaces "tick right after the add"). `add-day` refuses a full day there (`FULL_DAY_AFTER_TRIAL`); use `normal`.
- Mill: "more daytime use", not the same work moved (4 afternoon hours became 8 from 8am; earnings 10.50 → 27.50 USD a day, authored). The extra came from unused solar (~96 → ~22 kWh/day; quotable only if DD-1b2b's report-only row matches); battery still full by 2pm. Do not say the mill could run like this every day on solar (6am battery restart covers ~40 kWh/day; continuous days unrun).
- Grow row reads "Limited evidence: readings come from mixed sources, so the size is not worked out yet" (owner "Leave it"); presenter: "We generated these example days in separate runs, and the system won't size across those. A real site reports continuously."
- Mill "Target met": route Work → Maintenance → mill row → verdict page (42.00 → 110.00). The board's "1 verified result" is ACT-001, not the mill (owner chose route, BL-45 for boards). No screen shows the thread's Action link (corrected; DD-1b2b fixes the data anyway).
- Kobo's money is mill sales (WK-2a 42.08 USD); the generator problem carries no fuel money figure.
- Cold and EV: open from the printed story-day links. Portfolio site-name click lands on the latest event, without the Action row (BL-39). No live Cold add-day.
- Portfolio stays on week and month story links; one later day conflicts (BL-36). Month table shows three Verified rows beside "1 fix confirmed". Longer build shows extra Finding history entries. S-8/S-5 read "Spare solar on 4 of 4 well-observed days" beside "No potential found yet" (review L6).

## For the owner's walkthrough
6am jump note on screen; three Verified rows; "days checked" on count lines; Portfolio click (BL-39); Cold/EV Portfolio rows "No action agreed yet" against ST-4/5 "in hand"; mill result reached by route, not on the board; Grow "Limited evidence" line. Owner told the generator story has no fuel money and may overrule. Added: Cold "Why?" names one of two threads on the failure day (BL-50); "sales not recorded" and EV income-estimate wording (BL-48); S-5 "Not judged yet".

## Owner decisions this sprint (verbatim files in `.agent/`)
owner-scope-backlog-2026-11-05, owner-mill-pass-margin-2026-11-05, owner-kobo-nights-2026-11-06, owner-build-time-2026-11-06, owner-cold-days-2026-11-06, owner-kobo-partial-days-2026-11-07, owner-dd1a2-answers-2026-11-07, owner-rehearsal-whole-list-2026-11-07 (one whole-list run, own `*_test` DB, ≤3 h), owner-grow-size-2026-11-07 ("Leave it"), owner-mill-route-2026-11-07 ("Fix link, use route"), owner-efficiency-2026-11-05 and -2026-11-06.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game (owner), except DD-1b2b's one whole-list rehearsal on its own `*_test` DB. Localised tests only; polish clones allowed. Don't run `test_demo_combined_postgres`.
- DBs: `*_test` and `<prefix>_audit*` only; polish read-only, never ticked; never touch `assetops_demo3_full_test`; never write into `AssetOpsV1-polC`. DB host 127.0.0.1:55432. Route every test to its own DB. Do not guess credentials.
- NEVER pass any `-ExecutionPolicy` flag. Kill processes by PID only. Never stop keep-awake (running, `-MaxHours 168`). Edits Write/Edit only; stage explicit paths. Never tune numbers. Agent launches: no `isolation` (worktree/remote) — builders work in the existing lane worktree beside its local DB.
- PYTHONPATH absolute: worktree `backend;contracts;tools;simulator;gateway;host;field` (+ `backend\tests;host\tests` for host tests); python `AssetOpsV1-plan2\.venv\Scripts\python.exe`; set `ASSETOPS_GUARD_PYTHON`. Run vitest by listing files or a folder.
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>". Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `Docs/demo-sprint/implementation-logic-design-proposal.html` on main alone.
- Reviews have repeatedly found what code-reading rulings missed: ask for a measurement when a ruling depends on an unrun path.

## Restart guidance
Restart the coordinator session only when no agents are running. On resume: read this file, then `git log --oneline -15` on main, then the in-flight worktree's `.agent/*-handoff.md` / packets / review files.
