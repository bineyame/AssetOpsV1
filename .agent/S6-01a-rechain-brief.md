# S6-01a re-chain and merge prep (Sonnet)

Work ONLY in worktree `C:\Users\assef\Bineyame\AssetOpsV1-review`, branch `task/S6-01a-action-store-read` (reviewed; reopen review ACCEPT). Main is now `5536f228` (contains LR-01 migrations `0014_*` and `0015_finding_returning_basis`, S5-01, S4-06, S4-07, OPS-01, keep-awake display fix).

1. `git merge main` into this branch. Resolve doc conflicts (`.ai/*`, `tasks/README.md`) by keeping both sides' content.
2. Re-chain this branch's `backend/migrations/versions/0014_action_store.py`: rename to the next number after LR-01's head (`0016_action_store.py`), revision id accordingly, `down_revision = "0015_finding_returning_basis"`. Update every test that pins the migration head (at least `test_s1_bindings_postgres.py:~118`, `test_s2_evidence_ledger_postgres.py:~445`, `test_s4_evidence_consequence_work_postgres.py:~516,539`, plus any LR-01 pins) to the new head. Verify `alembic heads` shows a single head and upgrade/downgrade through 0016 works on a private DB.
3. Rule 8 in `tools/checks/configuration-persistence.ps1`: make sure both LR-01's assessment-writer entry for `source_clock_attestation` and this branch's ninth writer survive the merge.
4. Start `tools/keep-awake-during-tests.ps1` (now holds the display) unless one is running. Run focused S6 + migration-pin tests, then ONE full backend suite from PowerShell with `--junitxml`, `-n 2 --dist loadfile --no-loadscope-reorder`, gitignored `var/sites/*.yaml` copied in from the main checkout temporarily (remove afterwards), 20-minute cap. Then `tools/check-all.ps1` (temporary `.venv` junction, removed afterwards).
5. Closeout on the branch: task status `done` pending merge note, review packet updated with the re-chain and the full-suite JUnit counts.

Commit small. Do not merge to main. Do not touch `.agent/coordinator-handoff.md` or `.agent/owner-autonomy-2026-10-15.md`. Drop DBs. Write `.agent/S6-01a-rechain-handoff.md` (git add -f). Report concisely with JUnit counts.
