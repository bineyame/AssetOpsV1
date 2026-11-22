
## Verification review (round 1 fixes), fresh Claude reviewer, 2026-11-22

**Verdict: ACCEPT.** F1, F2, F6, F7, D-P6.31 and D-P6.32 are closed. F5 stays queued (D-P6.33). No open finding.

Summary:
- Target: `task/6a-decision-records` at `100695daa` (`816575072`, `100695daa`; `5d5d85173` is the main merge), read in a worktree.
- F1/D-P6.30: both stores make the four cross-row checks before any insert (`postgres_decision_store.py` `add_run`/`add_choice`,
  `records.py` memory store). `RECORD_INVALID` is in `REFUSAL_EXIT` (exit 2) and is the `record_invalid` variant of `decision.refused`,
  with its catalogue case. Test 7k covers all four checks and asserts no row stored.
- Plant exception: the memory run-option check is covered by the set-equality check, so its plant survives. The Postgres
  check is the one that matters (the deferred trigger counts only). I removed the Postgres option check here: 7k failed. Reverted.
- D-P6.31: `_unavailable` maps SQLSTATE class 22/23 to `RECORD_INVALID`, all else stays `StoreUnavailable`; tests 7h, 7j (exit 2), 7i (exit 3).
- D-P6.32: migration guard is `CASE WHEN jsonb_typeof(missing)='array' ... END`; 6b asserts `option_effect_missing_check` by name.
- F2: `choose` refuses `ALREADY_CHOSEN` when the stored option or Action differs; command prints the stored option key. Memory test covers the race.
- F6 (packet cites gate P and `4a232a2f2`) and F7 (docstring now says lever by lever) are done.
- Merge: `git diff 81df59185 5d5d85173` on `specs/INDEX.md` and `.ai/state/index-3.md` shows only the 6a row and entry 196; main's 195 (`0K4m-u3`) and
  all other rows are kept; no row dropped.
- Checks run here: unit (`test_6a_decisions`, `test_6a_commands`, `test_3c2_agreed_actions`) 231 passed; Postgres
  (`test_6a_decisions_postgres`, `test_6a_migration_postgres`, `test_3c2_agreed_actions_postgres`) 22 passed. Same counts as the builder. Not rerun: check-all 43/43 (cited from the packet).

Residual notes (no action): class 22/23 mapping also turns an unhandled unique conflict (23505) into `RECORD_INVALID`, as D-P6.31 rules;
serialization failures (40001) stay exit 3. No full backend suite at this revision.
