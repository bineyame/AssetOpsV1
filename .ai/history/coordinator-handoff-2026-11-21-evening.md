# Coordinator handoff (21 Nov evening)

Read this first on resume. The day's earlier blocks are in `.ai/history/coordinator-handoff-2026-11-21-day.md`.

## Mode
Owner away from ~18:00 UTC; the Architect stands in (`owner/owner-away-architect-stands-in-2026-11-21b.md`). Push to complete the fortnight (`Docs/demo-sprint/product-direction-layer4/two-week-build-plan.md` §0). Log calls in `specs/OWNER-AWAY/decisions-2026-11-21.md` (last row 52; 44-46 reserved). Reviews gate merges. UI merges (IA-2a, 5c, IA-2b1) wait for the owner's walkthrough. No guard change unless already approved. Standing owner rule: one model-computed figure per quantity, no design value beside it (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`).

## Git and scratch rules
- Agents work only in their own worktrees and never switch or commit in /opt/assetecon/AssetOpsV1. Before every merge, check that `git branch --show-current` prints main.
- Each agent gets its own scratch subfolder. Logs go to /opt/assetecon/evidence/<unit>/.
- `.agent/` is git-ignored; commit with `git commit -- <path>`.

## Main
Main is green except two items being fixed: this file's size cap (trimmed now) and the heavy-slot A11 100 ms bound under load (timing fixer, branch `fix/load-aware-timing-a11`). Migrations up to 0071.

Merged on 21 Nov: SC-1a, ENV-1, 0K3, 3A7, 3C2, 3C1b, the 3A3 scan fix, the timing fix, and specs and rulings for DS4 r2, SC-1f, 0K4 review, 3A7 D1/D4.

## In flight

| Lane | Branch · worktree | State · next |
|---|---|---|
| 5c | `task/5c-deep-dive-screen` · -5c | Build. Then review, then held for the walkthrough. DDR after 5c |
| DS4 unit 3 | MERGED ~20:00 | Kept L2 `assetops_world_audit_l2_1906a5d074a0` (check_passed, not stale) |
| WK | (spec by Architect) | After DS4 merges: copy the new L2 into `assetops_polish_walk<MMDD>_test` (row 36 b) and serve |
| SC-1f | `task/SC-1f-declared-word` · -sc1f | Build ("Declared"; logger rule; allow helper). Then review, then merge, then 5c follows the wording |
| IA-2b1 | `task/IA-2b1-lists` · -ia2b1 | Units 1-2 builder running, from `handoff-IA-2b1.md`. Units 3-4 next. Q1 alias needs Architect confirmation at review |
| 0K4 | `task/0K4-specs` · -0k4spec | Architect writing the 0K4a-d specs, the candidate energy fix, the one-figure change list and the operator request |
| 1a | specs on main (d36e2e83a), 1.75 u, screen unit (merge held) | Handshake queued: start when a build lane frees |
| WK | spec on main, 1.25 u (tool `tools/walk_world.py`, ports 8991/5491, rows 53-54) | Build after DS4 merges and 5c units 1-2 merge; then the coordinator runs it |
| Timing A11 | `fix/load-aware-timing-a11` · -timing | Fixer running |

## Notes
- DDR's rehearsal DB `assetops_rehearsal_ddr1` is outside the authorised names: rename it `assetops_rehearsal_ddr1_test` in the DDR brief (no owner ask needed).
- 6c is not this fortnight (row 55: no spec, needs 6a and P6 at the day-14 sitting).
- 5c units 1-2 merge on ACCEPT; the screen (unit 3) waits for the owner.

## For the owner on return
- Walkthroughs ready or coming: IA-2a (ready); 5c and IA-2b1 (building).
- Wording to confirm at the 5c walkthrough: "Declared" for settings; the accounts figure as Recorded.
- Architect calls made while away: see the owner-away log, rows 51 onward.
- Backlog Lows: `.agent/backlog-post-demo.md`.
- COLLISION: main now has index-rulings-22.md (0K4); IA-2b1 branch renamed its IA rulings index to -22 too -> at IA-2b1 merge move IA to next free (-23+).
- 0K4 specs on main 0ead104e9 (8.75 u): lanes 0K4b->0K4c; 0K4a->0K4d; 0K4e (DB job); 0K4m after 0K4d; 0K4f queued post-walk. Row 56 owner weigh-ins: no world on v8 before walk (default); 330 L reads Not available yet (default).
- 5c: units 1-2 committed (d70fa62c7); unit-2 sub-agent finishing; then review u1-2 (merge on ACCEPT) + unit 3 build + Architect on Kisiwa carried O&M $0.00 (one-figure flag a). WK handshake queued after the 0K4/1a handshakes.
- 0K4 handshakes answered (b96d5e978; D-0K4.19 class ruling: no new served English in baseline; rows 57-58; 0K4 = 10.5 u). BUILDING: 0K4b (-0k4b), 0K4a c1-2 (-0k4a; c3 after 0K4b merges; 0K4d c1 slots between), 0K4e (-0k4e). 1a ready (1.75 u), build when a lane frees. SC-1f MERGED. 5c backend fix (-5cbe) + Architect 5c rulings (-arch5c) + 5c screen (-5c, task/5c-unit3-screen) running.
- 0K4a c1-2 done (3baf2fa63, -0k4a; 538 sim + 53 host pass; v7 digest 8eb9c44c... pinned; MBQ: only generator moves; extra test file). c3 waits for 0K4b on main. 0K4c+0K4d handshake (-hscd) running. 1a BUILD started (-1a; screen, merge held).
- 0K4c/0K4d answers on main d90cb2853 (D-0K4.26-30; 0K4 now 11.25 u, critical path 4.75; row 63 Mto 2.4 L/h). 0K4d c1 BUILD started (-0k4d). 0K4c starts after 0K4b merges (0K4b in review, -0k4b). 5c screen built (task/5c-unit3-screen 885078841; waits backend fix merge, then UI review; guard list entry DD_NOT_AVAILABLE_TITLE for reviewer). Six-failures investigation (-fix6).
- 0K4d c1 DONE (d80c9610a, -0k4d; admission.py + measures; 40 tests; plants fail). c2-3 after 0K4a and 0K4c merge (needs kobo_assumed.py on main - from 0K4b, now merged - and trajectory_digest.py from 0K4a). Review the whole unit after c3. 0K4b MERGED 68a4ba6c0. six-failures fix MERGED. 5c backend verification running (-5cbe).
- 1a review ACCEPT (ready for walkthrough); Lows round running (-1a). Walkthrough notes: scope line has no gap to the grey detail sentence; "possible extra fuel / cost" wraps with a wide gap (pre-existing). Q-M3: test_ch6b_estate_postgres needs a harness template build - coordinator at a quiet moment. Agents: run pytest from backend/, not repo root (editable install imports main).
- 0K4c built (f8e6a0b26), review running. 5c backend H3/M3/L7/L8 round running (-5cbe).
- QUIET-MOMENT JOB (coordinator): harness templates stale for md0 (test_md0_mechanism_postgres) and 1a (test_ch6b_estate_postgres); a template ensure prunes shared assetops_mechanism_*_test templates -> run only when no other DB lane is active, then run both tests.
- 0K4c MERGED a66dd74a9. 0K4e built (aa2bc5595), review running; Q1 F05 fixture extended (route to Architect if contested).
- 0K4a COMPLETE (8ff3a90f2): v8; dawn after overcast v7 30.53% -> v8 74.29% (SIMULATED); N12 d6add2a3...; review running. After merge: 0K4d c2-3 (needs 0K4a+0K4c on main; 0K4c merged). 5c backend round 3 verification running. 0K4e review running.
- 5c wording (coordinator, Architect stand-in, to confirm): M3 "{site}: not compared: its actual and its target are in different currencies ({currencies})."; L7 headline "Contribution for {month} is not available yet: the Sites' figures are in different currencies." Log as an owner-away row when 5c merges.
- 5c units 1-2 MERGED 08f3bf86c (backend). 0K4e MERGED. Running: 5c screen merge+adapt (-5c, task/5c-unit3-screen), DDR+WK handshake (-hsddrwk), 0K4a review, IA-2b1 unit 4. Log 5c literals (M3, L7) as an owner-away row with the next Architect pass.
- DDR+WK handshake done (99b1d8279); Architect answering (-hsddrwkans). Kept L2 1906a5d074a0 is STALE (backend+simulator changed) -> WK: world build + check first (~26 min, quiet DB slot); C4 may move after 0K4e. DDR G10/S11 need 3C2 unit 2 (StoreAgreedActions) - Architect deciding. Rehearsal DB -> assetops_rehearsal_<x>_test; serve on 8992/5492 (Architect call).
- 0K4a MERGED (v8). 0K4b, 0K4c, 0K4e, 0K4a all on main. 0K4d c2-3 BUILD running (-0k4d): reruns on v8+season v2, restate per D-0K4.29; USER_REVIEW_REQUIRED (figures). 0K4m after.
- DDR/WK answers on main 3e77a8575 (rows 65-67). Order to day 14: 3C2 unit 2 (building, -3c2u2) -> WK tool (building, -wk) + DDR (building, -ddr) -> world build+check (~26 min, coordinator, after 3C2u2 merges; C4 FAIL = stop -> Architect) -> WK run (no merge to main between copy and check) -> DDR merge -> rehearsal + serve on 8992/5492 from detached worktree -ddrserve. 5c screen review running (-5c).
- 5c screen review: READY FOR WALKTHROUGH (bc2df265f). M1 on main: view.py:274 gap or 0 -> steps read "Offsets it" when gap NA (fix before 5c merge). Architect ruling items 6 (one NA slot rule) and 7 (bridge bars) + M1 (-arch5c2). Then backend fix branch + screen fix (L1 focus, L2 inert). Shared contrast (demo bar 4.12, DataTable header 4.35) -> UI lane backlog.
- WORLD BUILD TIMING (coordinator): the world key includes backend/; 5c backend fix (fix/5c-backend-r5) and DDR (portfolio_history) both change backend. Run world build+check only after 5c fix and WK have merged, then WK copy/prepare/check with NO main merges in between (D-WK.14). DDR merge after WK check; DDR rehearsal uses its own DB.
- 3C2 unit 2 merging (verification ACCEPT).
- 5c backend fix r5 (fix/5c-backend-r5, -5cfix): KD1 accepted (heading evidence from steps with an effect); KD2 coordinator ruling: gap 0 -> gap tile has no rest line (was a crash on main). Log both as an owner-away row with the next Architect pass. Then fresh review, merge, then screen fix.
