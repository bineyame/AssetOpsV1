# 3A4 reviewer guide (rev 2)

Rev 2 (2026-11-20) follows the handshake answers in `rulings.md` (D-3A4.10, D-3A4.11): V1, V2 and V9 are
re-aimed so each can fail; V10 to V12 are new.

For the fresh Reviewer: first at the handshake (read `spec.md`, `rulings.md`, P3A and this guide; put questions in
`handshake.md`), then at the review. Depth: discovery (W5): money figures and a read seam that `4b`, `5a` and `3B7a`
build on.

## First checks

1. **Scope.** The diff holds only spec §7 question 8's list. No migration; nothing under `structure/`.
2. **Base.** The branch starts after `3B3` merged (the parity test imports `month_window`).
3. **Module paths** in the packet show the worktree.
4. **W2.** The expected values in the tests are §4's literals, not computed by the code under test.

## Done means

Spec §7's eight questions answered yes with real output: the no-database file, the Postgres file and the regression
set through `tools/heavy-slot.sh --db`, check-all, and every planted violation below failing.

## Planted violations (plant, run, revert; each must fail a named test)

| # | Plant | Must fail |
|---|---|---|
| V1 | In the adapter's `_LATEST`, move the period filter into the `DISTINCT ON` subquery | Postgres test 3 |
| V2 | In the adapter's `_LATEST`, move the `known_at` clause out of the subquery; then, separately, in `MonthsMemoryStore.latest_revisions` | Postgres test 1 (the `known_at` read); no-database test 2 |
| V3 | Sum through `float` | tests 6 and 12 |
| V4 | Drop provenance from the line key | test 5 |
| V5 | Emit a 0 line for an absent heading | test 7 |
| V6 | Place a settlement by its UTC month | test 3 |
| V7 | Build the digest from the intake's new revision IDs only (ignoring moves out) | test 2, `stale` after F |
| V8 | Sum duplicate budget declarations | test 8 |
| V9 | Use Python's default decimal context | test 6 (the 31-digit sum) |
| V10 | Give an AMOUNT line the record's quantity unit | test 1 |
| V11 | Drop `basis` from the line key | test 3 |
| V12 | Compute `closed` from the clock only | test 2 (the 31 October 20:00 read) |

## Probes

- **Latest before filters.** Read the adapter's SQL with `known_at`: the cutoff is inside the `DISTINCT ON`
  subquery, the filters outside.
- **One parse per placed revision.** `site_month` must not parse revisions of other months.
- **Store errors.** If `3A2` is on `main`, the three reads carry `_scrubbed` and 3A2's service test 21 passes.
- **Words for `4b`.** Check that a line gives `4b` all it needs to build a leaf and its `Missing`: kind, dims,
  measure, currency, unit, provenance, sources.

## Class sweeps (W6)

- A line keyed wrongly for one kind: check all six rows of §3.3.
- An instant compared as text anywhere: check every clock in `months.py`.

## Risks

- `3A2` edits the same port, adapter and composition in lane A; the merge must keep both sets of methods, and the
  second to merge applies `_scrubbed` to the other's (D-3A2.16).
- A Site's time zone changing after records were placed would move settlements between months; Sites are not
  re-zoned today (residual).
