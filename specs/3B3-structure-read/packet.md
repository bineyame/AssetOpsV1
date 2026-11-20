# 3B3 packet: structure read and evaluator

Branch `task/3B3-structure-read` off `bf72c735d`, worktree `/opt/assetecon/AssetOpsV1-3b3`. Spec rev 2. Not merged.
`USER_REVIEW_REQUIRED`: false. Review: discovery.

Commits: `b934fd52f` code+tests; `590ca267f` guard fix + R7 test; `e480873eb` and the next one, bookkeeping.

Module path: `<wt>/backend/assetops_backend/__init__.py`, `<wt>/contracts/assetops_contracts/__init__.py`.
`fixtures` is a namespace package taking in main's `host/fixtures`; unused here.

## Done (§7)

| # | Answer | Proof |
|---|---|---|
| 1 | 47 nodes x 3 Sites x 2 sides = pack to the cent; 38 SUM = pack sums; blocks = pack | T1-T3 |
| 2 | Own record, true cause, never 0; gap day = no value | T4, T6, PG |
| 3 | Weakest part, NEUTRAL skipped; ESTIMATED above assumptions | T1, T2, T7 |
| 4 | Empty = None; included/excluded; refusals | T3, T6 |
| 5 | Six carried items | T5 |
| 6 | All checks planted | T5 |
| 7 | Existing functions, no store, no route | PG |
| 8 | Scope + bookkeeping | diff |

## Tests

- Focused: 143 passed (no DB); PG: 4 passed (`--db`, `assetops_test`).
- select-tests: 326/524. Host run (no Docker), 1:33:51: 4137 passed, 32 failed, 11 errors. Base re-run of the
  failed files: same failures less 3, which pass alone on this branch (flakes). 11 errors: `TEMPLATE_STALE`.
- check-all fast: exit 0, 79.5 s.

## Plants

22 plants, each failed its test (checks off, bad rows, zero short cuts, open or partial month, blocks order,
currency, `/0`, coverage rule).

## Mid-build: 4

Q1 `month_sum` 5-arg form; Q2 COMPLETE day with no value; Q3 "closed" clock; Q4 "n" of k of n.

## Deviations

- Guard refuses adapter imports: prices via existing `financials.composition` builders (workaround; their
  engines not disposed).
- Neutral product keeps only the neutral's parts; portfolio `assumed_leaves` are `SITE:leaf`.

## Not verified

Mechanism-template tests (rebuild could drop another lane's template); Docker runner.
