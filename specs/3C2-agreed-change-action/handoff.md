# 3C2 handoff: commit 1 done, commit 2 (the statements) next

**Superseded 2026-11-21: commit 2 is built; see `packet.md` "Commit 2". Kept for the record.**

Branch `task/3C2-agreed-change` (worktree `/opt/assetecon/AssetOpsV1-3c2`), off `task/3A6-source-profiles` at
`166942e7d`. Commit 1 is complete for its scope; this is not a partial phase.

## Done (commit 1, D-3C2.14: codes only)

- `backend/migrations/versions/0069_agreed_action.py` (revises `0067_source_profile` on this base).
- `backend/assetops_backend/actions/agreed.py`: `STATE_OPEN, STATE_OVERDUE = "OPEN", "OVERDUE"`, `state_code`,
  `clean_title`, `owner_covers`, `OWNER_COVER`, `REFUSAL_EXIT`, `AgreedActionRefused(code)` (`.code`, `.exit`),
  `StoreUnavailable`, `AgreedActionService.record` / `.for_tenant`, `MemoryAgreedActionStore`.
  `AgreedActionView.state_code` holds the code (the spec's `state_words` field arrives in commit 2).
- `actions/adapters/postgres_agreed_action_store.py`, `actions/composition.py` (agreed block appended, D-3C2.15):
  `build_agreed_actions(url, *, clock=...)` -> `AgreedActionsService(service, dispose)`, re-exported by `actions/agreed_composition.py`.
- `backend/assetops_backend/record_action.py`: refusal writes `"<CODE>\n"` to stderr; success line `state` is the
  code; the epilog is static chrome.
- `accounts/permissions.py`: `"action.agree": (EXECUTIVE,)`.
- Tests: `backend/tests/test_3c2_agreed_actions.py` (1 to 5), `backend/tests/test_3c2_agreed_actions_postgres.py`
  (6 to 8). Guard writer block in its own commit, held for the owner. MB1 answered (D-3C2.15): code change to B follows.

## Next (commit 2, after SC-1a merges and `main` is merged in)

1. Merge `main` into the branch (SC-1a, 3A6, 3A7 by then). Gate B: renumber `0069` on 3A7's
   `0068_commercial_reconciliation` (file, `revision`, `down_revision`, the downgrade sentence, and `HAND_PAIR` in
   the Postgres test); run `alembic heads` (one head).
2. Vocabulary `action_state` (`OPEN` -> "Open", `OVERDUE` -> "Overdue") and `i18n/statements/en/agreed_action.py`:
   one statement `agreed_action.refused.<code lower case>` per spec §2.5 refusal (14), §2.5's exact sentence,
   reworded only where D-SC1.21 forbids a number word ("1 to 200" in BAD_TITLE, the date example in BAD_DUE: use
   slots per D-SC1.21).
3. `agreed.py`: add `state_words(due_on, today)` rendering the vocabulary word; `AgreedActionView` gains
   `state_words: str` (5c's mapping reads `v.state_words`); join `ADOPTED`.
4. `record_action._refuse` writes `<CODE> <rendered sentence>\n`; the success line's `state` is the rendered word.
5. Tests: tests 1 to 3 swap codes for the exact strings (`R1_LINE["state"] = "Open"`, `_refused` expects
   `f"{code} {sentence}\n"`, test 3 the words "Open"/"Overdue"); re-run every plant of `reviewer-guide.md`.

## Anchors

- Rule order: `agreed.py` `AgreedActionService.record`, steps commented 1 to 9.
- Text points to change: `record_action._refuse`, `record_action._line` (`state`), `agreed._view`.
- Tests asserting codes: `test_3c2_agreed_actions.py` `R1_LINE`, `_refused`, `test_3_*`; Postgres test 8.

## Risks

- MB1: the guard fails on the adapter-import line until the code moves to B (D-3C2.15).
- The guard writer block needs the owner's approval at merge (owner-away row 5).
- `ASSETOPS_TEST_CLEANUP=truncate` would hit `agreed_action_no_truncate` (as `chain_input_change` already does);
  the default DELETE cleanup is unaffected.
