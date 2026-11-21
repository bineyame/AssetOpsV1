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
| DS4 unit 3 | `task/DS4-template-ladder` · -ds4 | Fix round done (B5 done; 13.497 s/Site-day; ds7 not triggered). Verification review running, then merge. New kept L2 is `assetops_world_audit_l2_1906a5d074a0` (check_passed) |
| WK | (spec by Architect) | After DS4 merges: copy the new L2 into `assetops_polish_walk<MMDD>_test` (row 36 b) and serve |
| SC-1f | `task/SC-1f-declared-word` · -sc1f | Build ("Declared"; logger rule; allow helper). Then review, then merge, then 5c follows the wording |
| IA-2b1 | `task/IA-2b1-lists` · -ia2b1 | Units 1-2 builder running, from `handoff-IA-2b1.md`. Units 3-4 next. Q1 alias needs Architect confirmation at review |
| 0K4 | `task/0K4-specs` · -0k4spec | Architect writing the 0K4a-d specs, the candidate energy fix, the one-figure change list and the operator request |
| 1a and WK specs | `task/1a-WK-specs` · -1awk | Architect writing the specs and the pull order to day 14 (incl. 6c) |
| Timing A11 | `fix/load-aware-timing-a11` · -timing | Fixer running |

## For the owner on return
- Walkthroughs ready or coming: IA-2a (ready); 5c and IA-2b1 (building).
- Wording to confirm at the 5c walkthrough: "Declared" for settings; the accounts figure as Recorded.
- Architect calls made while away: see the owner-away log, rows 51 onward.
- Backlog Lows: `.agent/backlog-post-demo.md`.
