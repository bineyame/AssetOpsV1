# 5c backend fix r6 packet: the cash sentence (D-5C.29, spec rev 5 section 12)

Branch `fix/5c-cash-r6` off main ecaf49f5a. One commit. Backend files only.

## Built
- `deep_dive/view.py`: public pure `cash_parts(rows)` (revenue, in_transit, outstanding rows only when collected has an
  actual and currency, each part is present in that currency over the same Sites, and collected = billed - in transit
  - outstanding exactly). `MonthView.cash()` takes the sentence, the total row and each Site's Billed cell from the cash
  tree; the contribution tree's revenue and the root's `target` are no longer read there.
- `deep_dive/words.py`: `cash(month, collected, parts | None)`; `expected` slot deleted.
- `i18n/statements/en/deep_dive.py` `deep_dive.cash`: slots billed, in_transit, outstanding; variants not_available,
  cash, collected_only (last). The `cash` variant uses `when` (the catalogue requires `when` on every non-last variant;
  the spec text said "when billed ... all present", so this is the same condition).
- `tests/statement_cases/deep_dive.py`: cases `cash` and `collected_only`.
- Fixture `deep_dive_lakeside_2026-10.json`: `cash.text` hand-edited to the rev 5 sentence.

## Tests (written first, in `test_5c_deep_dive_view.py`)
- Test 3 literal; `test_cash_sentence_reconciles` over A, D, E, G, H, X and the five currency worlds;
  `test_cash_sentence_literals` (D and sides: "2 of 3 Sites" total); subset world literals added to test 4 i;
  `test_cash_parts_vectors` (five vectors).
- Known deviation: "expected" absent is asserted over `cash` (the section), not the whole payload, because World A's
  payload legitimately holds "each feeder's expected technical loss" (the LOSS_BAND text elsewhere).

## Plants (each applied to view.py, view test file run, reverted with git checkout)
- C1 billed fed from root.target: 11 failed (test 3, subset test, reconciles x8, literals).
- C2 identity check deleted: 1 failed (`test_cash_parts_vectors`).
- C3 total Billed from contribution tree: 2 failed (subset test 4 i, reconciles[subset]).
- C4 per-Site Billed from contribution tree: 1 failed (subset test 4 i, Mto row).

## Checks (from the worktree, through tools/run-host-tests.ps1 in a heavy slot)
- Focused: view, api, test_5b_attribution(+postgres), test_3a7_* (4 files), test_sc1_statements: 792 passed, 1 skipped.
- Test 9 `test_5c_deep_dive_postgres.py`: 3 passed.
- Catalogue (`test_sc1_statements.py`) is in the focused run. Check-all fast: 141.1 s wall, "All 42 guards passed (blocking; 0 advisory, 0 warned)".
- Note: the shared venv's editable install points at the main checkout; a plain `.venv/bin/python -m pytest` in this
  worktree tests main's code. Use run-host-tests.ps1.

## Left for the screen branch
Regenerate its two frontend fixtures with `make_screen_worlds.py` on the next merge of main.
