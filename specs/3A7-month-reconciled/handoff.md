# 3A7 handoff: commit 1 done, commit 2 next (partial by design, D-SC1.28)

Branch `task/3A7-month-reconciled`, worktree `/opt/assetecon/AssetOpsV1-3a7`, based on `task/3A6-source-profiles`
`166942e7d` (D-3A6.26). Commit 1 is `cb862a7bf` plus `5e51b7a7c` (module moved, mid-build Q2). Merge waits for 3A6 and SC-1a.

## Done (commit 1)

- Migration `0069_commercial_reconciliation` (revises `0068_structure_finding` (renumbered from 0068 at the commit 2 main merge)): both tables, append-only triggers,
  downgrade refused with a row (0065's form).
- `commercial/model.py` `StatementRow`, `ToleranceRow`, `SiteRow`; `store.py` and the Postgres adapter
  `add_accounts_statement`, `accounts_statements`, `add_tolerance`, `tolerances`, `site_rows`. The guard's
  `$commercialTables` gained both tables (same writer, same plain-INSERT shape; nothing else needed).
- `structure/reconciliation.py` (not `commercial/`, mid-build Q2): `HeadingCheck`, `StatementCheck`, `MoneyStanding` as codes and Decimals (no `words`
  and no `text` fields yet), `_compare`, `record`, `check`, `statements`, `standing`, `tolerance`, `set_tolerance`,
  `percentage`, `ReconRefused(code, params)` (no words). `months.clock` read-only property (spec §2.6).
- `permissions.py` `"commercial.accounts_statement": (FINANCE,)`; `test_3c1a_person_work.py` `SPEC_ROLES` one line.
- Fixture `backend/tests/fixtures/3a7/reconciliation_two_sites.json`; `backend/tests/test_3a7_reconciliation.py` R1-R5,
  R7-R10 on states, reasons and exact Decimals, plus `set_tolerance` cases (M5's rules, service side).

## Next (commit 2, after SC-1a merges and `main` is merged in)

1. §2.7 as SC-1 statements in `i18n/statements/en/reconciliation.py` (rulings "Amendment (SC-1)": D-SC1.14, .16,
   .18, .19, .21, .26). SC-1a mid-build ruling (its ID is in the index once SC-1a merges): the records slot has `"form": "in_sentence"`. Money reads `$505.00` (D-SC1.10).
   Add `words`/`text` to the three dataclasses, `heading_words`, `money_word` (R6), the refusal words, and join the
   guard's `ADOPTED`. Display rounding (D-3A7.10: `DISPLAY` context, ROUND_UP/DOWN per table) lives with the words.
2. Word assertions: every T-case sentence of §6 (by SC-1's rules), R3's sentences (share omitted at 0, 5.01
   allowed, "less than 0.01 more", `1,234,567.89`), R6. Plants V12, V15, V19 then fail their named tests.
3. `build_commercial_reconciliation` in `structure/reconciliation_composition.py` (D-3A7.14), taking `owner_file` as a parameter (D-3A7.15; the command builds the reader from the owner root); `reconcile_month.py` (§5) and M1-M5; `test_3a7_reconciliation_postgres.py` Q1-Q3 (chain link, triggers,
   downgrade, tolerance CHECKs, Q2 routed T1/T2/T4, Q3 FK).
4. Packet: list each changed string for the walkthrough; P4 residual (structure in the composition's import closure).

## Anchors

- `structure/reconciliation.py` `_heading` (§2.2 rules 1-4), `_Read` (one call's memo: Sites, tolerance, months, checks),
  `standing` (§2.3 steps 1-5), `record` (§2.5 refusal order).
- Choices a reviewer should see: a NOT_COMPARABLE heading carries `recorded`/`difference` None (never a sum across
  currencies or an open month); an organisation with no mini-grid Site refuses `RECON_SITE_UNKNOWN` with no params;
  `RECON_AMOUNT` params `{"heading": "revenue"|"fuel_cost"}` (the words map it to `heading_words`).

## Risks

- Mid-build Q2 (High): module path moved to `structure/`; commit 2's builder needs a home outside `commercial/`.
- check-all's decision-index guard fails on this base only: `rulings.md` (taken from `main`) cites D-SC1.* IDs that
  the 3A6 base does not index; merging `main` in (commit 2) resolves it.

- Mid-build Q1 (owner-file port) is applied on its default; an Architect "no" moves the read into the command.
- 3A6 is in a fix round on its own branch; a rebase onto 3A6's final head or `main` may touch `store.py`, the adapter
  and the guard line (all additive).
