# Coordinator handoff — 2026-11-08 (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to a lane Architect (Claude subagent; reuse via SendMessage while under ~200k context, else fresh). Builders: Opus first build, Sonnet fix rounds; first reviews Opus, re-reviews Sonnet; the coordinator verifies mechanical closures (tiny test-only/golden/docstring diffs) by reading the diff. Merge `git merge --no-ff` on ACCEPT, then `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background (PowerShell tool, log to scratchpad, read `All 17 guards passed.` line). Never merge while check-all runs on main. Batch merges into one check-all when memory is tight.

## Scope as of 2026-11-08 (owner decisions, verbatim files in `.agent/`)
- `owner-fuel-scope-2026-11-07.md`: build shortlist items 1–4 (mill dollars, mill on board, Portfolio value lines, money wording) AND idle fuel (Option A) before the demo script; generic 3.3 L/h labelled generic; example tank left as is, explained in "Why?"; "inject days, i don't see why it should be mutually exclusive".
- `owner-diesel-site-2026-11-07.md` + `owner-diesel-night-window-2026-11-07.md`: diesel Site before the demo; ≥20% pass mark; stop-at-60% lever; night 6 pm–noon; mill "No cost recorded". D0 then measured 4.4% → NOT MET.
- `owner-missing-fuel-2026-11-07.md`: Kisiwa with the missing-fuel story; "Unexplained fuel", never "theft"; client not specifically diesel-heavy.
- `owner-scenario-data-2026-11-07.md`: reasonable authored days are legitimate; fuel events are "injected through operational actions" (owner correction).
- `owner-kisiwa-scope-2026-11-07.md`: build Kisiwa with the operational-action link (~15 units at the time).
- Demo date: about +3.25 working days vs. a plan without Kisiwa (range 2.75–5.25; owner accepted 2.5–5). Tripwire: if the Kisiwa critical path exceeds 9.75 lane-units, pause and bring cut options (first candidate K6).

## Build sheets (rulings appended at the end of each)
- `.agent/build-sheet-FUEL-1.md`: MV-1, MB-1a/b, WD-1, WD-1m, PV-1, A1, A2, A3 + rulings MB-1-R, MB-1a-R2, PV-1-R, A2-R1, WD-1-R, WD-1m-R/R2, A3-R.
- `.agent/build-sheet-DIESEL-1.md`: Kisiwa D0/F0/K0–K9 + rulings R2 (§8) … R3k (§9k); R3l (K5/K7 cards) being written.
- `.agent/build-sheet-CH-5d.md` (CH-5d1), `.agent/build-sheet-TEST-drift.md` (DRIFT-R1).
- Review Lows not yet fixed: `.agent/followups-fuel-kisiwa-2026-11-07.md` — an Architect decides which go into one Sonnet round before DS-1.

## Merged on main (all reviewed; check-all 17/17 after each batch)
DD-1b2b, CH-5d1, MV-1, A1, A2, MB-1a, MB-1b, PV-1, WD-1, WD-1m, D0 (evidence, NOT MET), F0+F0e (evidence), K1a (mini-grid v7), K1 (Kisiwa Site), K2 (fuel records, 0054), K3 (fuel balance, 0055; shared idle slot rule excludes stop slots R3h), K0 (operational-action bridge), DRIFT-R1, TEST-drift-0053, DRIFT-RB1. Last check-all on main: 17/17 after K0/WD-1m (main ~b70be217b+).

## In flight (2026-11-08)
- K4a (unexplained-fuel Finding, 0056): builder resumed under R3k (domain filters on `findings_over` and `latest_revisions_overlapping`). Worktree `AssetOpsV1-k4a`.
- A3 (idle fuel on Kobo screens): builder building under A3-R; must STOP before the Kobo scratch prepare (`assetops_demo3_fuela3_test`, ~41 min, cap 3600 s) for the coordinator's one-heavy-job gate.
- Architect writing R3l (K5 fuel page night mode, K7 story days).
- Remaining after these: K4b (Protect row MG-8 + Portfolio Protect line), K5, K6 (after-check), K7 (story days + Kisiwa scratch prepare), K8 (four-Site screens), K9 (finish rows + rehearsal), the follow-up Lows round, then DS-1, then E1–E6, then the owner walkthrough.
- Sizes: Kisiwa total ≈17.7 (no contingency left); FUEL-1 lane 1 ≈3.47, A3 0.91. Critical path ≈8.5 lane-units.

## Known for end-game
- E2 first step: rebuild the mechanism template (~1300–1700 s) on an idle machine; until then TEMPLATE_STALE failures in `test_ch5a1_mechanism_postgres`, `test_ch6b_estate_postgres` are expected.
- `test_ch1a_grading.py::test_period_bounds_addis_utc_tue_only_and_24h` fails on main ("unknown period 'midday'") — untraced drift.
- WD-1m: real Kobo data must yield an example source class at E3 or MILL-5 fails. MB-1b: MILL-4 bounds but does not prove k.
- E3 owes from DD-1b2b: serve heartbeat sampling, post-add check, after tool, browser path, perf record; on any DB copy rerun S2 then Performance (Kobo) and assert AVAILABLE.

## Owner walkthrough list (additions)
Mill on board ("ACT-002 verified on example data", thread line); Portfolio value lines (mill above trial order, PV-1 L1); EV "No income figure for this day: it is not fully checked"; Kobo month line "no fully checked day counted yet this month"; Kisiwa four-Site Portfolio and "Unexplained fuel overnight" card; Cold "Why?" names one of two threads (BL-50).

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game, except Architect-ruled trimmed scratch prepares (A3 Kobo-only, K7 Kisiwa-only) under the gate: one heavy job, ≥2.5 GB free RAM for 2 min, keep-awake running, stop under 1 GB.
- DBs: `*_test` and `<prefix>_audit*` only; never `assetops_demo3_full_test`. Host 127.0.0.1:55432; credentials `assetops`/`assetops-local-dev`.
- NEVER pass `-ExecutionPolicy`. Kill by PID only. Keep-awake: restart only if the owner asks (memory reap once on 2026-11-07; owner said "restart both").
- Builders: Write/Edit only; no sed/awk/heredoc/`>`/`>>`/Set-Content/Tee-Object; no sleep polling; no subagents; PYTHONPATH must include the worktree's `contracts` (the venv's editable install points at the stale checkout); `.gitattributes` pins `.agent/DIESEL-F0/*`, `.agent/DIESEL-D0/*`, `config/operational-actions/*` to LF.
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; never push. Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `Docs/demo-sprint/implementation-logic-design-proposal.html` on main alone.
- Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) size rows are NOT yet updated for FUEL-1/DIESEL-1 (rulings list the rows).

## Restart guidance
Restart only when no agents are running. On resume: read this file, `git log --oneline -20` on main, then the in-flight worktrees' packets/reviews and the last build-sheet rulings.
