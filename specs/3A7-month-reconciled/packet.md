# 3A7 packet: commits 1 and 2 (one closed month reconciled; D-SC1.28)

`USER_REVIEW_REQUIRED: true` for commit 2: it adds served text (every sentence below), held for the owner's combined
walkthrough; there is still no screen (5c shows the standing). Branch `task/3A7-month-reconciled` (worktree
`/opt/assetecon/AssetOpsV1-3a7`). Commit 1 `cb862a7bf`, `5e51b7a7c` (reviewed ACCEPT, `review-c1.md`); commit 2 merges
`main` `e5a283228` (SC-1a, 3B4) and `task/3A7-midbuild-answers` (D-3A7.14, D-3A7.15), then `7db25a8b9` and a docs
commit. Not merged to `main`. Mid-build Q1 and Q2 are answered (D-3A7.15, D-3A7.14).

## Outcome

Migration 0069 (renumbered from 0068 at the commit 2 main merge; two append-only tables). The store port, the memory mirror and the Postgres adapter. The
`structure/reconciliation.py` service: `record` (refusals §2.5 in order, nothing written), `check`, `statements`,
`standing` (§2.3 at `known_at`, one memo per call), `tolerance` and `set_tolerance` (§2.4). Money reconciles only when
a current statement opens the gate (both headings matched against recorded lines, within the tolerance at `k`: 1 in
100 by default, RC8) and no covering statement disagrees or cannot be compared. No used line is never 0: it is
`NOT_RECEIVED`, or `NONE_RECORDED_ZERO_STATED` (matched, never an opener) where the accounts state 0.00.

## Files

`backend/migrations/versions/0069_commercial_reconciliation.py`; `commercial/model.py`, `store.py`,
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

## Known deviations (commit 1)

- Q1 and Q2 are now rulings: the owner file reaches the service through the `owner_file` port, which the command
  builds (D-3A7.15); the service lives in `structure/` (D-3A7.14).
- A NOT_COMPARABLE heading carries `recorded` and `difference` as None.

## Review focus

`structure/reconciliation.py` `_heading` (rule order), `standing` (covering first, then the gate walk in cited order)
and `_Read` (memo per call). The tie on `recorded_at` is broken by `id` text. Handoff: `handoff.md`.

## Commit 2: the words, the composition, the command

### Outcome

- `i18n/statements/en/reconciliation.py`: SC-1 §5.1's `reconciliation.heading`, `.gap`, `.share` and §5.4's
  `.scope` exactly (a test compares them with `worked.py`'s copies), plus `.statement`, `.standing`, `.money_word`
  and `.refused`. Vocabulary `noun` gains `character` (the refusal's length limit is a `Count`).
- `structure/reconciliation.py` hands the composer typed facts and holds no word: it is in the guard's `ADOPTED`
  (D-3A7.14), and the scan passes with nothing added to the hand-built baseline or the allow file. `HeadingCheck`,
  `StatementCheck` and `MoneyStanding` gain `words` and `text`; `MoneyStanding` also `details` (D1). New:
  `heading_words` (the spec's signature plus `origins`), `statement_words`, `standing_words`,
  `money_word(figure, standing)` (D2), `refusal_words`, `site()`; `set_tolerance` returns its row.
- Evidence (D-SC1.18): the accounts and the tolerance are `DECLARED`, origin `observed-financial` ("Recorded"); the
  records are `RECORDED` with the used lines' weakest origin ("Emulated" for §6's fixtures; none named reads
  "Estimated"); the difference, allowed amount and share are `DERIVED` from them.
- To keep the adopted module code-form, the record forms (the five patterns the migration's CHECKs mirror) and the
  owner-file citation rule moved to `commercial/model.py`, and the used lines, sources and origins are read from
  `structure/money.py` (three public helpers over 4b's own row filters, D-3A7.1) instead of restating them.
- Review L2: a slug cites only as a whole slug (`lakeside-power-north` no longer cites `lakeside-power`).
- `structure/reconciliation_composition.py::build_commercial_reconciliation(database_url, *, owner_file=None)` on
  `commercial.composition.build_commercial_reads` (D-3A7.14, D-3A7.15). `reconcile_month.py` (§5): `record`, `show`,
  `set-tolerance`; the owner-file reader is built from the owner root (default the repository root).
- Migration renumbered `0069_commercial_reconciliation`, revising 3B4's `0068_structure_finding`.

### Every served string (for the walkthrough), and what changed from spec §2.7 and §6

| Where | Now reads | Change and rule |
|---|---|---|
| Heading, all money | `$505.00` | was `505.00 USD` (D-SC1.10) |
| Heading, matched / not matched | `Fuel cost (Recorded and Emulated): the accounts say $505.00 and the records say $512.50, $7.50 more (1.49%), beyond the $5.05 allowed (1%).` | the evidence word after the heading name (D-SC1.18); "less than $0.01 more" for a tiny gap |
| Heading, zero stated / not received | `Fuel cost (Recorded): the accounts say $0.00 and no fuel invoices are recorded.` · `... $40.00, but no fuel invoices are recorded for October 2026.` | evidence word; `$0.00` from the figure, not a literal (D-SC1.9) |
| Heading, currency / month open | `Revenue: the accounts are in EUR, but the records are in USD.` · `Revenue: November 2026 is not closed yet.` | none |
| Statement | `October 2026 (KOBO-001) matches the management accounts within 1% (Recorded).` (and "does not match", "cannot be compared ... yet") | the tolerance carries its evidence inline (D-SC1.18; D4) |
| Standing | `Reconciled: October 2026 (the organisation) matches the management accounts within 1% (Recorded).`; the two "Not yet reconciled: ..." month forms; `Not yet reconciled: no closed month has been compared with the management accounts.`; `Not yet reconciled: no month's recorded revenue and fuel cost match the management accounts within 1% (Recorded) yet.` | "both" dropped (D-SC1.21); tolerance evidence (D4); failing headings in `details`, not in `text` (D1) |
| `money_word` | `Recorded` · `Recorded, not yet reconciled` · `Emulated, not yet reconciled` | through the shared evidence format (D-SC1.16) |
| Refusals | `Only the finance lead records the management accounts.` · `Write the month as YYYY-MM, like 2026-10.` · `This Site is not this organisation's: NOPE-001.` · `Only mini-grid Sites are compared with the management accounts for now: FRZ-001.` · `Write the currency as its code in capital letters, like USD.` · `Write the revenue as digits with a decimal point and no separators, like 1200.00.` · `Say where the figures come from, in at most 200 characters.` · `November 2026 is not closed yet: record a closed month.` · new: `This organisation has no mini-grid Site to compare with the management accounts.` | number words reworded (D-SC1.21: "not one of", "three capital letters", "two decimals"); the open month by name, not `2026-11`; a sentence for the code commit 1 raised without a Site |

### Known deviations (commit 2)

- **D1 (needs an Architect ruling).** D-3A7.13 makes the standing's `text` its sentence plus the failing headings'
  sentences joined by a space. SC-1 has no way to join rendered sentences (a part shares its parent's facts, so two
  headings cannot both be parts; `Items` holds facts, not messages), and any join in code is hand-built text (the
  adopted rule; in the ratchet a new `HAND_BUILT_NEW`). Built: `text` is the standing sentence and
  `details: tuple[str, ...]` holds each failing heading's sentence in heading order (JSON `"details"`); V19 fails on
  it. Options: keep the list (5c shows the sentences one per line), or SC-1 grows a sentence-sequence slot and
  `text` returns to D-3A7.13's form.
- **D2.** `money_word(figure: Money, standing)`, not `(base: str, standing)`: the word comes from the figure's own
  evidence through the shared format (D-SC1.16), so 5c passes the money it shows.
- **D3.** `CONFIGURATION` prints the code alone (exit 2); printing the `ConfigurationError`'s text would be served
  exception text (a new fingerprint).
- **D4 (wording, owner).** The statement and standing sentences state the tolerance, a figure, so it carries its
  evidence: "within 1% (Recorded)". `reconciliation.scope` is an inline statement (§5.4), so its parents cannot be
  `served` and move the word to a chip.
- **D5 (scope beyond §3's files).** `structure/money.py` (three helpers), `i18n/statements/en/vocabulary.py`
  (`noun.character`), `tools/checks/statement_catalogue.py` (`ADOPTED`, D-3A7.14), `test_sc1_statements.py` T8's
  shipped-key set, `statement_cases/worked.py` (docstring), new `statement_cases/reconciliation.py` and the three new
  test files.
- **D6.** `show` refuses a malformed period (`RECON_PERIOD`) and an unknown Site (`RECON_SITE_UNKNOWN`) with exit 2;
  the spec names no code. `set-tolerance` refusals stay codes (exit 2, no sentence).
- Order of work: the statements module was written just before its word tests, in the same commit.
