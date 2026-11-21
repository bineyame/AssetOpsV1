# 3A7 packet: commit 1 of 2 (one closed month reconciled, codes and Decimals; D-SC1.28)

`USER_REVIEW_REQUIRED: false` for commit 1: there is no screen and no served text. Commit 2 adds the words and lists
each string for the walkthrough. **Two mid-build questions need an Architect ruling** (`mid-build-questions.md` Q1, Q2
High); both are applied on their defaults. Branch `task/3A7-month-reconciled` (worktree `/opt/assetecon/AssetOpsV1-3a7`),
off `task/3A6-source-profiles` `166942e7d` (D-3A6.26). Commits `cb862a7bf`, `5e51b7a7c`, plus this docs commit. Not
merged: the merge waits for 3A6 and SC-1a.

## Outcome

Migration 0068 (two append-only tables). The store port, the memory mirror and the Postgres adapter. The
`structure/reconciliation.py` service: `record` (refusals §2.5 in order, nothing written), `check`, `statements`,
`standing` (§2.3 at `known_at`, one memo per call), `tolerance` and `set_tolerance` (§2.4). Money reconciles only when
a current statement opens the gate (both headings matched against recorded lines, within the tolerance at `k`: 1 in
100 by default, RC8) and no covering statement disagrees or cannot be compared. No used line is never 0: it is
`NOT_RECEIVED`, or `NONE_RECORDED_ZERO_STATED` (matched, never an opener) where the accounts state 0.00.

## Files

`backend/migrations/versions/0068_commercial_reconciliation.py`; `commercial/model.py`, `store.py`,
`adapters/postgres_commercial_store.py`, `months.py` (read-only `clock`); `structure/reconciliation.py`;
`accounts/permissions.py` (`commercial.accounts_statement: (FINANCE,)`); `tools/checks/configuration-persistence.ps1`
(both tables joined `$commercialTables`, nothing more); `backend/tests/test_3c1a_person_work.py` (one line);
`backend/tests/fixtures/3a7/reconciliation_two_sites.json`; `backend/tests/test_3a7_reconciliation.py`; spec docs.

## Acceptance (§8, commit-1 part)

1. R7: 4b's `stated` equals the recorded figures (500.00, 512.50; MTO 250.00, fuel absent where no used line). R1, R2 sum over scope. Yes.
2. T1, T7, T8, T10 (gate needs an opener; cited month named). Yes.
3. T2, T6 (a covering mismatch or not-comparable wins over a matched month elsewhere). Yes.
4. R1, T2 (live checks in both directions; stored `result_at_record` unchanged). Yes.
5. Sentences: commit 2.
6. R4 (15 refusals, nothing written), T9. Q3 (FK): commit 2.
7. T3, R9, service-side tolerance cases (M5's rules). Yes.
8. Plants: V1-V11, V13, V14, V16-V18, V20 each fail a named test (below). V12, V15, V19 are about words: commit 2.
9. Scope: §3's files, plus the moved module path (Q2) and `months.py`'s `clock` property (§2.6 allows it).
10. T10, R9. Yes.

## Checks (revision `cb862a7bf`, then `5e51b7a7c`)

- Module paths: `assetops_backend` `/opt/assetecon/AssetOpsV1-3a7/backend/assetops_backend/__init__.py`, and `contracts`
  and `simulator` from the same worktree (venv `/opt/assetecon/AssetOpsV1/.venv/bin/python`).
- `heavy-slot.sh --db -- pwsh tools/run-host-tests.ps1` on 16 files (3A7, 3A1, 3A2, 3A3 loader, 3A4, 3A6, 4b, each
  with its Postgres file where one exists, and 3C1a; routed `*_test` from base `assetops_test`) at `cb862a7bf`:
  **2 failed, 471 passed** in 53 s (767 s wall, mostly waiting for the db slot). Failures:
  `test_3a4...::test_12_no_float_and_no_structure_import`, `test_4b...::test_11a_..._under_commercial`, which led to Q2.
- After the move (`5e51b7a7c`), the 11 files without a database: **475 passed** in 30 s. The Postgres files do not
  import the moved module and were not rerun.
- Plants (in place, each reverted with `git checkout`): 17 of 17 fail.
- `tools/check-architecture.ps1` at `5e51b7a7c`: **passed** (98 s).
- `tools/check-all.ps1` (fast) at `cb862a7bf`: **1 of 41 blocking guards failed**, "Decision, state, spec and owner
  indexes": unresolved `D-SC1.10/.14/.16/.18/.19/.21/.26/.28`. `rulings.md` was taken from `main`, which indexes
  these IDs; the 3A6 base does not. Merging `main` in (commit 2) resolves it. Estate guard self-tests 17 passed.
  581 s wall.

## Known deviations

- Q1: the owner file is read through an injected `owner_file` port. `pathlib` in the service fails the persistence
  guard.
- Q2: the service lives in `structure/`, not `commercial/` (D-3A4.8, which the 3A4 and 4b tests enforce).
- The dataclasses have no `words` or `text` yet. `money_word`, `heading_words` and R6 come in commit 2.
- A NOT_COMPARABLE heading carries `recorded` and `difference` as None.

## Review focus

`structure/reconciliation.py` `_heading` (rule order), `standing` (covering first, then the gate walk in cited order)
and `_Read` (memo per call). The tie on `recorded_at` is broken by `id` text. Handoff: `handoff.md`.
