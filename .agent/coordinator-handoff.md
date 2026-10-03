# Coordinator handoff (2026-10-03, T027 phase 1 accepted; phase 2 next)

A fresh coordinator starts from this file; do not re-derive what it states.

## Where things stand

- `main` at `4ae4d4b` (nothing pushed): the demo-led recommendation and replan
  (`f7325c3`) plus T025h parked in `.ai/MILESTONE_REVIEW_BACKLOG.md`
  ("Parked task: T025h"; pick up not before T029 with the T026 AC15 p95 task;
  branch `task/T025h-picker-compatibility` is superseded, do not merge).
- Sources of record: `.ai/ARCHITECT_DEMO_RECOMMENDATION.md` (owner-approved),
  `.ai/DECISIONS.md` `D-2026-10-02-*`, `tasks/README.md` queue T027 -> T028 ->
  T029 -> T029B -> T029A -> T034 -> T034A -> T031 -> T032 -> T030 -> T035 ->
  T033 -> T025i -> T036.
- Owner text, verbatim, in `.agent/owner-*-2026-10-02.md` (review,
  instruction, approval, acceptance); each approval file separates the owner's
  words from the coordinator's reading.
- **T027 phase 1 is accepted** on `task/T027-commit-ingestion-and-site-overview`
  (cut from `f7325c3`; HEAD `dfb9651`; task `Status: in_review`, phase 2 open).
  - Owner hands-on check: successful (`.agent/owner-T027-phase-1-hands-on-2026-10-03.md`).
  - Review `.agent/T027-phase-1-claude-review.md` (accept with one fix);
    fix round `c9fb412..24bc13e`; re-review `.agent/T027-phase-1-claude-rereview.md`
    (accept); N10 `.pyc` untracked in `dfb9651`.
  - Suites: backend 1417, host 602, simulator 244 (run from `simulator/`),
    frontend 1056; both checks pass. Layout evidence from phase 1 build:
    4 pre-existing FAILs only.
  - Carried to `.ai/MILESTONE_REVIEW_BACKLOG.md` "Carried from T027 phase 1":
    release resume needs the live stage (N2), evidence store design (N6),
    configuration-registry location (owner question, trigger T034).
  - Phase 2 handoff: `.agent/T027-phase-1-handoff.md` (includes N9: one
    source for `NEEDED_SIGNALS` and the AC22 profile).

## Next actions

1. T027 phase 2 (mini-grid Site Overview: AC11, AC22, and the Overview
   extensions of ACs 10, 12-15, 19) by a fresh Implementer from
   `.agent/T027-phase-1-handoff.md`. Ends with full suites, layout evidence,
   final packet.
2. Fresh Claude Reviewer on phase 2 (or Codex after the reset; ask the owner),
   then the owner's demo point 1 check.
3. Before T027's final merge: merge `main` (`4ae4d4b`) into the T027 branch.

## Open owner items (defaults stand until the owner rules)

- Demo point 3 shows the Action already accepted (no live Accept click).
- Name of the evidence-limited Portfolio-lite site: left to T034A's Planner.
- Global Financials root vs Portfolio view: decide after T036.

## Standing rules

- Owner restarts sessions to save usage: dispatch long agents only when the
  owner expects them to run in this session; otherwise leave the next action
  here for a fresh session.
- Pass owner feedback to agents verbatim via a saved `.agent/` file.
- `.ai/ROLE_CONFIG.md`: after the Codex reset 2026-10-03 21:23, revert the
  Architect, Planner and Reviewer rows to Codex, queue retrospective Codex
  reviews of T025e, T025f, T025g, T026 and the demo-led plan, and ask the owner
  who takes in-flight roles.
- `.agent/` is gitignored: commit with `git add -f`.

## Update 2026-10-03 ~10:25: T027 phase 2 built and reviewed; owner UI check next

- Phase 2 on the T027 branch (HEAD bb8976d): packet `.agent/T027-phase-2-review-packet.md`
  (fix rounds 1-3), layout `.agent/T027-phase-2-layout-evidence-fix-round-1.txt`
  (513 PASS / 5 FAIL: 4 known + intermittent T026 delayed-reading claim, backlogged).
- Reviews (all Claude, temporary binding): `.agent/T027-phase-2-claude-review.md`
  (F1-F5), `-claude-rereview.md` (R1-R3), `-claude-rereview-2.md` (S1, S2).
  Fix round 3 (S1/S2, strings + comments only) verified by the coordinator:
  tsc clean, frontend 1071. Backend 1435, host 602, simulator 244.
- Owner asked (2026-10-03): send to reviewer, owner does UI check after all is
  complete. Next: owner UI check (packet "User-review focus" 1-7), owner rulings on
  energy wording (point 6) and on "Start Simulation" (keep disabled with true
  reason vs remove/link to Run setup). Then merge main (4ae4d4b) into the branch,
  mark T027 done, merge.
- Codex retrospective list gains T027 phase 1 and phase 2.
