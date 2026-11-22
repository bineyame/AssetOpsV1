# Coordinator handoff (21 Nov, late evening)

Read this first on resume. Earlier blocks: `.ai/history/coordinator-handoff-2026-11-21-day.md`, `-evening.md`.

## Mode
Owner away since ~18:00 UTC; the Architect stands in (`owner/owner-away-architect-stands-in-2026-11-21b.md`). Goal: finish the fortnight. Log owner-level calls in `specs/OWNER-AWAY/decisions-2026-11-21.md` (rows to 69; 64 held for IA-2b1). Reviews gate merges. UI merges wait for the owner's walkthrough. Rule: one model-computed figure per quantity (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`).

## Rules
- Agents work only in their own worktrees and never switch or commit in /opt/assetecon/AssetOpsV1. Before every merge, check `git branch --show-current` = main.
- Each agent has its own scratch subfolder.
- Postgres tests: `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1 -- <files>` (sets the DB URL). Run pytest from `backend/`.
- Keep this file under 8000 bytes.

## Merged to main on 21 Nov
SC-1a, SC-1f, ENV-1, 0K3, 3A7, 3C2, 3C1b, 3C2 unit 2, DS4 unit 3, 0K4a/b/c/e, 5c units 1-2 (backend), the timing fixes, the 3A3 and six-failures test fixes. Main green at 45 guards; last checked after 3C2 unit 2, except this file's size cap.

## In flight
| Lane | Branch · worktree | Next |
|---|---|---|
| 5c backend fix r5 | `fix/5c-backend-r5` · -5cfix | KD2 (gap 0 → no rest line) being fixed, then fresh review, then merge |
| 5c screen | `task/5c-unit3-screen` · -5c | READY FOR WALKTHROUGH (bc2df265f). After r5 merges: screen fix per spec rev 4 §11 (mute rule, bars, L1 focus, L2 lock, L4 fixture freshness), then re-review |
| WK tool | `task/WK-walk-world` · -wk | Fix round (safe stop by start time and pgid, smoke heavy slot, L1-L4), then verification, then merge |
| DDR | `task/DDR-rehearsal` · -ddr | Phase 2 (checker, gates, tests). 3C2 unit 2 is merged, so G10/S11 run |
| 0K4d | `task/0K4d-rerun-restate` · -0k4d | Commits 2-3 (v8 + season v2 reruns, restate per D-0K4.29), then review. USER_REVIEW (figures) |
| IA-2b1 | `task/IA-2b1-lists` · -ia2b1 | Unit 4 (lists, flip, plant proofs, full gate). Packet must explain the loop-core.js change (Q1 default overridden) |
| 1a | `task/1a-optimize-card-scope` · -1a | Ready for walkthrough |
| IA-2a | `task/IA-2a-plan` · -ia2a | Ready for walkthrough |

## Coordinator jobs, in order
1. When 5c r5 and WK have merged: `world build` then `world check` (~26 min, quiet DB slot). C4 FAIL = stop, then the Architect. Then WK §5 run: copy, prepare, check, serve 8991/5491, smoke, with NO main merges between copy and check. Export no `PG*` variables.
2. DDR merge, then rehearsal (§5.1), then serve on 8992/5492 from detached `-ddrserve`.
3. Quiet moment: rebuild the harness template (md0, 1a `test_ch6b_estate_postgres`), and the 300-file container suite for 0K4a.
4. Log as owner-away rows: the 5c M3/L7 literals; KD1 (heading evidence) and KD2 (gap 0).

## For the owner on return
- Walkthroughs: IA-2a, 1a, 5c (after its screen fix), IA-2b1 (after unit 4), the WK-served world, and the DDR rehearsal.
- 0K4 figures from 0K4d (v8, SIMULATED), with the admission verdicts.
- Architect calls: owner-away rows 51-69.
- Backlog: `.agent/backlog-post-demo.md`.
