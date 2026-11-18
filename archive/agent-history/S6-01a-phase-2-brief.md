# S6-01a phase 2 - implementer brief

Same worktree, branch and environment as `.agent/S6-01a-phase-1-brief.md` (`C:\Users\assef\Bineyame\AssetOpsV1-review2`, `task/S6-01a-action-store-read`, now at `1c47a687`). Build **phase 2** of `tasks/S6-01a-action-store-read.md`: the apply transaction (Action adapter opens the transaction and locks the Action row, then a caller-owned-connection form of the S1 publish passed in as a callable from composition; Site lock and expected-Foundation check under it; change artifact + APPLIED on that connection; one commit), FAILED written after rollback in its own transaction returning the existing event on an idempotency-key collision and never reverting APPLIED, `ACTION_ALREADY_APPLIED` / `ACTION_FOUNDATION_STALE`, the changes read, the `D-action-records` fixture and the committed API contract fixture keyed to fixture-manifest IDs (L5), a reproducible walkthrough, and the slice closeout (CODE_STATE, ACTIVE_CONTEXT, review packet `.agent/S6-01a-review-packet.md`, status `in_review`). This phase's review is the slice review.

A phase-1 review is running concurrently in another worktree; the coordinator will forward High/Medium findings to fold in. Not built in phase 1 and still owed if the packet requires it: the S4 money consequence on the recommendation and the demonstration label on Action reads - check the packet and either build or record as a deviation.

Migration note: LR-01 (unmerged, held for the owner) adds 0014/0015; this branch's `0014_action_store` will need re-chaining if LR-01 merges first. Do not re-chain now; state it in the review packet.

Proof: focused tests; ONE full backend suite at the end (`-n 2 --dist loadfile --no-loadscope-reorder`, 20-minute cap; first check no other `pytest -n 2` process is running and wait if one is); `tools/check-all.ps1` (temporary `.venv` junction allowed, remove afterwards). Mutation checks for lock order, FAILED-after-rollback, already-applied and stale-Foundation refusals. Drop DBs. Commit as you go; do not merge; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`.

Handoff `.agent/S6-01a-phase-2-handoff.md` (git add -f). Report concisely.
