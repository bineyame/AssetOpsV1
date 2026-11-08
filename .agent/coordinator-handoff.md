# Coordinator handoff — 2026-11-08, evening (replaces all earlier versions; older text is in git history)

Read this first on resume. Main checkout: `C:\Users\assef\Bineyame\AssetOpsV1-plan2` (branch `main`). The session start dir `AssetOpsV1` is a stale detached checkout; do not work there.

## Role
Coordinator: report to the owner in plain language, short (1–2 lines on routine events; full status on "where are we overall"). Route decisions to a lane Architect (fresh assetops-architect Claude subagent; reuse via SendMessage only while under ~170k tokens). Builders: Opus first build, Sonnet fix rounds/procedural runs; first reviews Opus, re-reviews Sonnet; the coordinator verifies mechanical closures by reading the diff. Merge `git merge --no-ff` on ACCEPT, then `tools\check-all.ps1 -Python C:\Users\assef\Bineyame\AssetOpsV1-plan2\.venv\Scripts\python.exe` in the background (log to scratchpad; now **18 guards** — read `All 18 guards passed.`). Never merge while check-all runs on main.

Lessons from 2026-11-08 (apply them): (1) do ONE combined end-to-end readiness audit instead of serial piecemeal Architect calls; (2) keep builder briefs small (code+tests first, captures/packet second) to avoid context-cap handoffs; (3) clone proofs need the product's own `evidence_migration run` + `performance_migration run` on the clone (reports are stamped with the DB name) — never hand-restamp.

## Scope (owner decisions, verbatim files in `.agent/`)
- FUEL-1 + idle fuel: `owner-fuel-scope-2026-11-07.md` (never a combined money total).
- Kisiwa diesel Site with "unexplained fuel" (never "theft"): `owner-missing-fuel-2026-11-07.md`, `owner-kisiwa-scope-2026-11-07.md`, `owner-scenario-data-2026-11-07.md` (fuel events injected through operational actions), `owner-diesel-*.md`.
- K10 declared-absent productive use: `owner-kisiwa-measure-applicability-2026-11-08.md` ("component contributor being non existent doesn't mean it is checked"; then "Build it").
- Final check scope: `owner-final-check-scope-2026-11-08.md` ("Affected rows now"; untouched rows re-checked by the demo-day prepare's self-check).
- **Demo script format: `owner-demo-script-format-2026-11-08.md` — TWO HTML documents: a well-illustrated client-facing script AND a developer-focused technical version with deeper operational insight.**
- Critical path ≈ 9.79–10.07 lane-units (owner accepted ~9.7–10.0 and chose affected-rows to stay close). Demo ≈ +3.7–3.9 working days vs. no Kisiwa.

## Merged on main (all reviewed; last check-all 18/18 after 3557de895)
FUEL-1 complete. Kisiwa complete through K9: D0, F0/F0e, K0, K1a, K1, K2 (0054), K3 (0055), K4a (0056), K4b + R3j3 (0058 watermark triggers), K5, K6a (0057), K6b, K6c (fuel verdicts in Assure counts; summary count from the claim; 5 modules listed), K7-D + K7-F (story days, plan freeze, verdict VERIFIED), K8 (four-Site screens code), K9 (KIS rows, COH Kisiwa boards, wording guard, R3r no-legacy cutover, R3s Kisiwa performance comparison, R3u fixes), K10 v2 (declared-absent productive use, R3t–R3v).
Build-sheet rulings: `.agent/build-sheet-DIESEL-1.md` through §9v (R3v).

## Kept test data
- Rehearsal DB `assetops_demo3_k9rehearsal_test` + `C:\Users\assef\Bineyame\AssetOpsV1-k9\var\demo3_k9rehearsal` (the four-Site evidence; built before K10/K6c code). Keep until K8c captures are done.
- Clone `assetops_k9_audit_r3u` + `C:\Users\assef\Bineyame\AssetOpsV1-k10\var\demo3_r3u` (has K9+K10+K6c verification; evidence/performance reports re-run by product tools). Verification-only int branch `task/DIESEL-int-r3u` (do not merge).
- `assetops_demo3_kisiwa_test` (K7-F Kisiwa-only).

## Next, in order
1. **K8c four-Site captures** (~0.25; R3p §9p.9(b)): Portfolio, Findings, Sites list, all-26 recapture. Since K10/K6c changed reads, capture from the clone `assetops_k9_audit_r3u` with main code (serve read-only), not the pre-fix rehearsal DB — confirm with the Architect in the combined pass if unsure. Cut: Kisiwa Overview capture moves to demo day.
2. **One combined Architect pass**: sort `.agent/followups-fuel-kisiwa-2026-11-07.md` (~40 Lows incl. demo-visible K8 L1 "No action yet" above "Verified", K8 L2 label wrap; main drift: ch1a midday, w301 golden ×6, out_b1 ×2, demo_a0 clock seam, w502 collection; after-demo items: Kisiwa Evidence tab 409, DB-name-stamped reports, COH-3 Kisiwa pairs, why.py days line) into before-DS-1 / before-E3 / after-demo, AND scope DS-1's two HTML documents.
3. DS-1 (two HTML docs), then E1–E6 (E2 first: mechanism template rebuild; demo-day prepare's self-check re-checks untouched rows; CO-2 needs live ticks), then the owner walkthrough.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game, except Architect-ruled scratch prepares under the gate: one heavy job, ≥2.5 GB free RAM for 2 min, keep-awake running, stop under 1 GB. Memory pressure reaps background shells — prefer foreground commands <10 min and Wait-Process on PIDs.
- DBs: `*_test` and `<prefix>_audit*` only; never `assetops_demo3_full_test`. Host 127.0.0.1:55432; credentials `assetops`/`assetops-local-dev`.
- NEVER pass `-ExecutionPolicy`. Kill by PID only. Keep-awake: the coordinator's copy was reaped by memory pressure; another copy (PID 23744) was running. Restart only if the owner asks.
- Builders: Write/Edit only; no sed/awk/head/tail/grep shell, heredoc, `>`/`>>`, Set-Content, Tee-Object; no sleep polling; no subagents; no `isolation`; PYTHONPATH absolute under the worktree incl. `contracts` and `simulator`; scratch scripts in a scratchpad SUBFOLDER (root has an `inspect.py` that breaks imports).
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; never push. Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `Docs/demo-sprint/implementation-logic-design-proposal.html` on main alone.
- Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) size rows NOT yet updated for FUEL-1/DIESEL-1.

## Restart guidance
Restart only when no agents are running. On resume: read this file, `git log --oneline -20` on main, then the last build-sheet rulings (§9u, §9v).
