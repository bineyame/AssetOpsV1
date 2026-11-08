# Coordinator handoff — 2026-11-08, later (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to a lane Architect (fresh assetops-architect Claude subagent). Builders: Opus first build, Sonnet fix rounds; first reviews Opus, re-reviews Sonnet; the coordinator verifies mechanical closures by reading the diff. Merge `git merge --no-ff` on ACCEPT, then `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background (log to scratchpad, read `All 17 guards passed.`). Never merge while check-all runs on main. Batch merges into one check-all when memory is tight.

## Scope (owner decisions, verbatim files in `.agent/`)
- `owner-fuel-scope-2026-11-07.md`: FUEL-1 items 1–4 + idle fuel before the demo script; generic 3.3 L/h labelled; never a combined money total.
- `owner-diesel-site-2026-11-07.md`, `owner-diesel-night-window-2026-11-07.md`: diesel Site before the demo (D0 measured 4.4% → NOT MET).
- `owner-missing-fuel-2026-11-07.md`: Kisiwa with the missing-fuel story; "Unexplained fuel", never "theft".
- `owner-scenario-data-2026-11-07.md`: authored days legitimate; fuel events "injected through operational actions".
- `owner-kisiwa-scope-2026-11-07.md`: build Kisiwa with the operational-action link.
- Demo date ≈ +3.5 working days vs. no Kisiwa (range 3.0–5.5). Tripwire: Kisiwa critical path > 9.75 lane-units → pause, bring cut options. Was ≈9.15.

## Build sheets
- `.agent/build-sheet-FUEL-1.md` (all FUEL-1 merged).
- `.agent/build-sheet-DIESEL-1.md`: rulings through §9o R3n; H1 ruling "R3j3" being written (see below).
- Follow-ups: `.agent/followups-fuel-kisiwa-2026-11-07.md` (Lows + main drift; one "L4 FIX BEFORE E3" item). An Architect sorts it into before-DS-1 / before-E3 / after-demo after K4b+K7 merge.

## Merged on main
FUEL-1 complete (MV-1, A1, A2, A3, MB-1a/b, PV-1, WD-1, WD-1m, CH-5d1, DD-1b2b). Kisiwa: D0, F0/F0e, K0, K1a, K1, K2 (0054), K3 (0055), K4a (0056), K6a (0057), K6b (verdict page, FUEL_VERDICT), K5 (fuel page, FUEL_FINDING; main f29b1a421). Drift fixes DRIFT-R1, TEST-drift-0053, DRIFT-RB1. Last check-all on main 17/17 after K6b; NOT yet run after K5 — run one after the next merge batch.

## In flight
- K4b (`AssetOpsV1-k4b`, `task/DIESEL-K4b-protect-fuel`): built; review FIX (`.agent/review-K4b.md`, 9331a094e). H1: board/summary/Portfolio stored routes now read `fuel_balance_window` + `fuel_residual_consequence_revision`, which have no watermark triggers → stale stored boards. Architect writing R3j3 (migration after 0057 + `watermark-inputs-v1.json` + listener guard CLI run; scope check of K5/K6b routes; Lows L1–L3). Then Sonnet fix round → Sonnet re-review → merge.
- K7-F (`AssetOpsV1-k7f`, `task/DIESEL-K7F-kisiwa-freeze`, carries K7-D which is ACCEPTed 3dea4b41a): built; scratch prepare exit 0, 4308 s, verdict VERIFIED (TARGET_MET); KIS-10 window fix c17567341, all KIS rows pass. Opus review running. Merge the K7-F branch once (it carries K7-D). Kept scratch DB `assetops_demo3_kisiwa_test` + `var/demo3_kisiwa` in k7f (K8/K6b captures). Note: that DB predates any R3j3 triggers.
- After these: K8 four-Site screens (~1.0; includes K6b captures owed, Kisiwa Protect +1), K9 checks + rehearsal (~1.0; four-Site rehearsal ~2.0–2.35 h, cap 10800 s), follow-up round, DS-1, E1–E6 (E2 first: mechanism template rebuild), owner walkthrough.

## Known for end-game
- E2 first step: rebuild the mechanism template on an idle machine; until then TEMPLATE_STALE in `test_ch5a1_mechanism_postgres`, `test_ch6b_estate_postgres`.
- Main drift (followups lines 26–30): ch1a midday, 6 w301 estate golden (`count.opportunities`), schedule-health clock skew, w502 collection, out_b1 import test.
- WD-1m: real Kobo data must yield an example source class at E3 or MILL-5 fails.
- E3 owes from DD-1b2b: heartbeat sampling, post-add check, after tool, browser path, perf record.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game, except Architect-ruled trimmed scratch prepares under the gate: one heavy job, ≥2.5 GB free RAM for 2 min, keep-awake running, stop under 1 GB.
- DBs: `*_test` and `<prefix>_audit*` only; never `assetops_demo3_full_test`. Host 127.0.0.1:55432; credentials `assetops`/`assetops-local-dev`.
- NEVER pass `-ExecutionPolicy`. Kill by PID only. Keep-awake: restart only if the owner asks.
- Builders: Write/Edit only; no sed/awk/heredoc/`>`/`>>`/Set-Content/Tee-Object; no sleep polling; no subagents; no `isolation`; PYTHONPATH must include the worktree's `contracts`.
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; never push. Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `Docs/demo-sprint/implementation-logic-design-proposal.html` on main alone.
- Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) size rows NOT yet updated for FUEL-1/DIESEL-1.

## Restart guidance
Restart only when no agents are running. On resume: read this file, `git log --oneline -20` on main, then the in-flight worktrees' packets/reviews and the last build-sheet rulings.
