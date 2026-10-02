# Coordinator handoff (2026-10-03, T027 phase 1 built, awaiting review)

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
- **T027 phase 1 is built** on `task/T027-commit-ingestion-and-site-overview`
  (cut from `f7325c3`; HEAD `a76a57d`; task `Status: in_review`). Not reviewed.
  - Packet: `.agent/T027-phase-1-review-packet.md`
  - Phase 2 handoff: `.agent/T027-phase-1-handoff.md`
  - Layout evidence: `.agent/T027-phase-1-layout-evidence.txt` (485 PASS;
    4 pre-existing FAILs: run-setup blocked table x3, delta p95 97.2 ms)
  - Suites: backend 1412, host 602, simulator 244, frontend 1055 pass; both
    workflow and architecture checks pass.
  - Implementer flags for the Reviewer: AC15 partial (rebuild runs in-process);
    `f0b30ee` does not typecheck alone (fixed by `24b38ee`; squash?); evidence
    store is one JSON per Site rewritten per chunk (quadratic, single-process
    lock); unstated choices listed in the packet; early layout runs wrote
    Drafts/executions into the working `var/runs` and `var/executions`.

## Next actions

1. Fresh Claude Reviewer on T027 phase 1 against the task file and packet
   (Reviewer is Claude until the Codex reset **2026-10-03 21:23**; after it,
   ask the owner who reviews). Fix rounds on Sonnet; re-reviews to a fresh
   Claude Reviewer.
2. Owner hands-on check: steps in the packet / the Implementer report
   (`/` -> `/sites`; Lab run of `kobo-mini-grid-degraded-evidence` on a Kobo
   v3 Site; Commit and release; Open in AssetOps -> Site > Evidence; tabs
   Overview | Foundation | Evidence; record inspector three times; gate off).
3. Then T027 phase 2 by a fresh Implementer from the phase 1 handoff (demo
   point 1 at its end).
4. Before T027's final merge: merge `main` (`4ae4d4b`) into the T027 branch.

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
