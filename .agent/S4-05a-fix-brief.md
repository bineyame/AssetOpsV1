# S4-05a fix round (Sonnet) - slice review L1, L2

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review4`, branch `task/S4-05a-provenance-binding-resolver`. Python: main venv with `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator` (confirm `assetops_backend.__file__`). Private `_test` DB; drop afterwards. Focused tests only; no full suite (it runs at merge time after migration re-chaining). Other agents use other worktrees; touch none.

From `.agent/S4-05a-review.md`:
1. L2 (coordinator decision, fail-closed and consistent with `D-2026-10-15-s405-stored-demo-provenance`): in `backend/assetops_backend/evidence/source_provenance.py:275-282`, when the consequence's FindingRevision part resolves UNKNOWN (incl. `EMPTY_CITATION_SET`), the combined consequence state must be UNKNOWN with that reason carried, never positive. Add pure and Postgres tests; record the rule in `.agent/S4-05a-review-packet.md` and the phase-2 handoff contract for S4-05b.
2. L1: rule 8 in `tools/checks/configuration-persistence.ps1` must also refuse `UPDATE` with the provenance table on the next line, and schema-qualified/quoted forms (`public.evidence_publication`, `"evidence_publication"`), in any module. Add guard probes for each form and confirm clean code still passes `check-architecture.ps1` (temporary `.venv` junction allowed; remove afterwards).

Commit small; write `.agent/S4-05a-fix-handoff.md` (git add -f). Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Report concisely.
