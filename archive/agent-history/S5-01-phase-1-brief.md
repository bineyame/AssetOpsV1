# S5-01 phase 1 - implementer brief

Branch `task/S5-01-site-overview` in `C:\Users\assef\Bineyame\AssetOpsV1`, stacked on LR-01 head `3b360af5` (LR-01 is under slice review in a separate worktree and is unmerged; its merge waits for the owner). Packet `tasks/S5-01-site-overview.md` - build **phase 1 only** (scoped read: imported-Site route/DTO, one process seam, S2 cutover and Performance gates, consistent basis, UTC day, Finding choice per `D-2026-10-15-s501-finding-choice`, money states consuming LR-01's `money_eligibility`). Reviews: `.agent/S5-01-plan-review.md`, `.agent/S5-01-plan-rereview.md`; Architect `.agent/architect-S5-01-answers.md`.

Carries from the plan re-review (handle where they fall):
- N1: `upstream.py` citation drift at the LR-01 head (downgrade ~:186-193, return block ~:194-202); re-verify all LR-01 citations at `3b360af5`.
- N2: an unverified demonstration source always shows no amount in S5 (no "other trusted provenance" exists until S4-05 lands).
- N3: decide and implement how the read keeps a previously pinned Finding: either an optional scope-checked `finding_id`/`finding_revision_id` query parameter, or state what a stateless read returns while the basis is moving. No amount either way. Record the choice as a deviation.
- N4: LR-01's walkthrough tool now has `run|attest|tick|serve|drop` (`tools/s402c_late_power_walkthrough.py`); use it rather than duplicating.
- N5 (phase 2 walkthrough note): P01 and P02 are adjacent days, so P01 can lose its amount between `attest` and `tick`; fail-closed, note it for the owner.
- Upcoming S4-05 (stored provenance, planned, unmerged) will require S5-01's money read to use a stored provenance resolver (`AUTHORED_DEMONSTRATION`, `REGISTERED_SIMULATION`, `MIXED`, `UNKNOWN`); keep the source-provenance gate a single, replaceable input so that amendment is small.

Process: focused tests per phase only (packet list; `backend/TESTING.md` focused commands route to private `_test` DBs); no full suite in phase 1. Keep-awake is running; cap any long run at 2x expected and report overruns. Mutation checks only for the money-state composition and gate precedence. If LR-01's slice review forces a change to LR-01 code, the coordinator will tell you; do not edit LR-01 files beyond what S5-01 needs, and list any you touch. Commit on the branch; do not merge; do not touch `.agent/coordinator-handoff.md`; run `tools/check-all.ps1` before handoff.

Handoff: `.agent/S5-01-phase-1-handoff.md` (git add -f). Report back concisely.
