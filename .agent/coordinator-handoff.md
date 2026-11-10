# Coordinator handoff — 2026-11-09 (replaces all earlier versions; older text is in git history)

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

## Next, in order (updated 2026-11-09 — supersedes earlier)
Spec: `.agent/build-sheet-OWN-GAPS-2026-11-08.md` (Rev 1–3, R4, R5, R6). Owner away since 2026-11-08 night with Architect delegation (`owner-away-architect-decides-2026-11-08.md`); report decisions D-R3.7–3.10, D-R4.1–4.2, D-R5.1–5.5, D-R6.1–6.4 on return. Coordinator calls to report: R4.1 stale-fixture fix, G1 L5 (`--dry-run` runs read-only preflight). Owner to set client session date.
- OWN-GAPS ALL MERGED: R-1, G3a, G2, G3b, R4.1 (b497d42ef), G1 (575c13222; rehearsal A/B 51/51; clone `assetops_demo3_g1audit_test` + `AssetOpsV1-g1\var\demo3_g1audit` can be dropped). check-all 18/18 after 575c13222.
- Owner Q&A 2026-11-09: no file upload (BL-59); simulator-dependency audit `.agent/architect-answer-simulator-dependency-2026-11-09.md` (product independent; leaks L1/L4 Medium → BL-53..58).
- POLISH-1 merged (9bbbb5626). E2 done (`task/E2-endgame` bda19fecf, E2-results.md). E2 fix round A merged (5f67315cd, tests only; rulings D-E2.1–D-E2.13 in the build sheet; BL-60..63).
- 2026-11-10 state:
  - **E3/E4 history.** E3 (client2, S=11-07) went 51/51, but E4 found 3 stops. The fixes are merged: C1 Portfolio lifecycle cutoff, C2 prebuild follows the calendar, C3 two-tier gap line, C4 performance-on-change, and C5 board lifecycle cutoff (D-E4.x, D-E3b). A G-m test fix landed too. check-all is 18/18 after b234cea2a. client3 failed F-COH and was dropped.
  - **E3c (current demo build).** DB `assetops_polish_client4_test` in wt `AssetOpsV1-e3c` (branch task/E3c-demo-build), S = 2026-11-08, 51/51.
    - It was launched DETACHED, because the harness memory-reaper kills background shells. The launch and watchdog scripts are in scratchpad `e3c\`.
    - E4b ran 15/15 PASS (commit 5e46dae89). Cold 11-09 was added.
    - client2 is kept as the fallback.
  - **E4-RESUME.** Part (a), the NIGHT_NOT_OVER refusal, passed on client2 (bfd384888). Part (b), interrupt-and-resume, can only run after 15:05 local.
  - **In flight: E5 captures** (Sonnet), branch `task/E5-captures` cut from DS-1a. DS-1f, then the owner walkthrough, follow.
  - **Owner decision 2026-11-10** (`owner-any-range-speed-2026-11-10.md`): any-range speed ANY-1 (boards, 3.0) and ANY-2 (Portfolio, 3.75) are built BEFORE the client session, after FR-B. Spec: `architect-answer-any-range-speed-2026-11-10.md`, BL-66, D-ANY.1–4.
  - **Coordinator calls to report:**
    - merged small verified fixes without a separate reviewer;
    - ran one check-all after several merges;
    - S moved to 11-08;
    - split the resume check;
    - the detached prepare with its watchdog;
    - dropped client3.
- Carry to FR-B (Wed 11–Fri 13): wrapper fixes, T6 w301 golden, `pin_read_at` must patch `EvidenceMoneySnapshot` (base-class leak), FR-A review Lows L1 (`raises=AssertionError` on the BL-63 xfail, test_out_b4:498), L2 (assert kpi not None before ch6b S equality), L3 (w207 exclusion only at :288), I1 docstring; add `OBJECTIVE_BEHIND_PACE` to the xfail verdicts tuple.
- Carry to E4: E4-K8, E4-env (if not done in E3), E4-GE corrected = check EVERY outcome on the board for Finding- or objective-driven reasons (incl. OBJECTIVE_BEHIND_PACE) on days with no checked readings; E4-GG; Cold/EV rows "Pending"; first real add-dates; forced unfinished-Kisiwa-night resume check.
- DS-1a client script on `task/DS-1a-client-script` (wt -ds1a, 9bc611cf0, re-review ACCEPT WITH NOTES); merge after DS-1f fills placeholders from E5 captures.
- K8c captures branch not merged; owner accepted illustrative pictures.
- Then E2 (clock check, mechanism template rebuild, T6 w301 golden, full backend `-Tier fast` then `-Tier slow -Targets` skipping test_demo_combined_postgres, vitest, check-all; one reserved fix round for the w203/cold_drain replay family; 8 standalone chain_coherence findings are fixture/BL-47, not defects) → E3 demo build into `assetops_polish_client_test` (not the 3rd–5th of a month) → E4 serve + checks incl. KIS-11, Cold/EV rows "Pending", first real add-dates run, a forced unfinished-Kisiwa-night resume check (G1 r2 suggestion) → E5 captures → DS-1f → owner walkthrough → DS-1b technical doc.

## Standing constraints
- NO full backend suite, NO demo prepare, NO baseline build until end-game, except Architect-ruled scratch prepares under the gate: one heavy job, ≥2.5 GB free RAM for 2 min, keep-awake running, stop under 1 GB. Memory pressure reaps background shells — prefer foreground commands <10 min and Wait-Process on PIDs.
- DBs: `*_test` and `<prefix>_audit*` only; never `assetops_demo3_full_test`. Host 127.0.0.1:55432; credentials `assetops`/`assetops-local-dev`.
- NEVER pass `-ExecutionPolicy`. Kill by PID only. Keep-awake: the coordinator's copy was reaped by memory pressure; another copy (PID 23744) was running. Restart only if the owner asks.
- Builders: Write/Edit only; no sed/awk/head/tail/grep shell, heredoc, `>`/`>>`, Set-Content, Tee-Object; no sleep polling; no subagents; no `isolation`; PYTHONPATH absolute under the worktree incl. `contracts` and `simulator`; scratch scripts in a scratchpad SUBFOLDER (root has an `inspect.py` that breaks imports).
- `git add -f` for `.agent`; commits end "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"; never push. Leave the uncommitted `.agent/owner-walkthrough-notes-2026-11-01.md` and `Docs/demo-sprint/implementation-logic-design-proposal.html` on main alone.
- Plan HTML (`Docs/demo-sprint/client-demo-plan.html`) size rows NOT yet updated for FUEL-1/DIESEL-1.

## Restart guidance
Restart only when no agents are running. On resume: read this file, `git log --oneline -20` on main, then the latest OWN-GAPS build-sheet rulings (R5, R6). Lesson 2026-11-09: tell builders to wait in place with Monitor on long jobs (one handed back while waiting and stalled).
