# S4-05a re-chain and merge prep (Sonnet)

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review4`, branch `task/S4-05a-provenance-binding-resolver` (slice review ACCEPT + fix round). Main is now `4fbb97f8`: it contains LR-01 (`0014_*`, `0015_finding_returning_basis`) and S6-01a (`0016_action_store`), plus S5-01, S4-06, S4-07, OPS-01, keep-awake display fix.

1. `git merge main` into this branch; resolve doc conflicts by keeping both sides; keep `main.py`/composition changes from both sides.
2. Re-chain this branch's `backend/migrations/versions/0014_evidence_publication.py` to `0017_evidence_publication.py`, `down_revision = "0016_action_store"`. Update every migration-head pin (s1_bindings, s2_evidence_ledger, s4_evidence_consequence_work, s4_consequence_store and any others found by grepping for `0016_action_store` / `0014_evidence_publication`). `alembic heads` must show one head.
3. Rule 8 (`tools/checks/configuration-persistence.ps1`): keep LR-01's `source_clock_attestation` entry, S6-01a's ninth writer and this branch's provenance-table rules and split-statement refusals together; `check-architecture.ps1` must pass.
4. Keep-awake (`tools/keep-awake-during-tests.ps1`, holds the display) running. Focused S4-05a + migration-pin tests, then ONE full backend suite from PowerShell with `--junitxml`, `-n 2 --dist loadfile --no-loadscope-reorder`, `var/sites/*.yaml` copied in temporarily (remove afterwards), 20-minute cap; then `tools/check-all.ps1` (temporary `.venv` junction, removed). Use `PYTHONPATH` = this worktree's `backend;contracts;gateway;simulator`.
5. Closeout on the branch: status `done` pending merge, review packet re-chain section with JUnit counts.

Commit small; do not merge to main; do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Write `.agent/S4-05a-rechain-handoff.md` (git add -f). Report concisely with JUnit counts.
