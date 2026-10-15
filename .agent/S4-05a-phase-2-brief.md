# S4-05a phase 2 - implementer brief

Same worktree, branch and environment as `.agent/S4-05a-phase-1-brief.md` (`C:\Users\assef\Bineyame\AssetOpsV1-review3`, `task/S4-05a-provenance-binding-resolver`, now at `11fad416`; private DB `assetops_s405a_test` may be reused). Build **phase 2** of `tasks/S4-05a-provenance-binding-resolver.md`: the exact scoped resolver (FindingRevision cited set and each consequence revision's union with its own power-interval IDs resolved separately; AUTHORED_DEMONSTRATION / REGISTERED_SIMULATION / MIXED / UNKNOWN truth table per the Architect follow-up, broken link precedence, several run IDs -> MIXED (N-L2); exact IDs and reasons). Per the packet, S4-05a leaves response shapes and the old date heuristic in place (S4-05b cuts over). Closeout: CODE_STATE, ACTIVE_CONTEXT, review packet `.agent/S4-05a-review-packet.md`, status `in_review`. This phase's review is the slice review.

A phase-1 review runs concurrently in another worktree; the coordinator forwards High/Medium findings to fold in.

Proof: focused tests (truth table on real Postgres for each class, broken/foreign links, consequence-only mixed power input); mutation checks on resolver precedence; then ONE full backend suite from PowerShell with `--junitxml=<abs path>`, `-n 2 --dist loadfile --no-loadscope-reorder`, gitignored `var/sites/*.yaml` copied in temporarily (remove afterwards), 20-minute cap; first check no other `pytest -n 2` is running and wait (poll every few minutes, up to 20 min) if one is. `tools/check-all.ps1`. Drop DBs at the end. Commit as you go; do not merge; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`.

Handoff `.agent/S4-05a-phase-2-handoff.md` (git add -f). Report concisely.
