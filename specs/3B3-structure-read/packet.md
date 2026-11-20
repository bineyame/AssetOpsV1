# 3B3 packet: structure read and evaluator

Branch `task/3B3-structure-read` off `bf72c735d`, worktree `/opt/assetecon/AssetOpsV1-3b3`. Spec rev 2. Not merged.
`USER_REVIEW_REQUIRED`: false. Review: discovery.

Commits: round 1 (this fix round) after merging `26dec2003`; `b934fd52f` code+tests; `590ca267f` guard fix + R7 test; `e480873eb` and the next one, bookkeeping.

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
- check-all fast (round 1): 40 guards passed, 78.0 s.

## Plants

22 plants, each failed its test (checks off, bad rows, zero short cuts, open or partial month, blocks order,
currency, `/0`, coverage rule).

## Round 1 (Architect answers, rulings.md "Mid-build answers")

| Answer | Status |
|---|---|
| Q1 5-arg `month_sum` | as built |
| Q2 / D-3B3.17 | `month_sum` returns `unstated`; leaf drops those days, NOT_RECEIVED, `VALUE_NOT_STATED:n`; 3 tests (None, `{}`, PARTIAL listing) |
| Q3 | 1 test: `now` one second before the window end (no value), at it (value) |
| Q4 | `read.site_count` + `SiteCount`; test k + len(out) = n, cold room named out |
| Deviation | `financials.composition.build_window_price_selection` (`select`, `dispose`); `structure/composition.py` uses only it; PG diesel-parity test and fake-store dispose test; deviation line removed |
| 32 failing files | `/opt/assetecon/evidence/3B3/failing-files-branch-vs-base.md`: 29 identical at base; 3 flakes, rerun alone: pass |
| Template | coordinator's; 11 errored tests still under Not verified |

Plants (each failed its test, then reverted): unstated ignored (a gap day summed as 0); no dispose; closed
`<` for `<=`; n = included; covered ignores unknown. Focused: 149 passed; PG 5 passed (`--db`).

## Mid-build: 4

Q1 `month_sum` 5-arg form; Q2 COMPLETE day with no value; Q3 "closed" clock; Q4 "n" of k of n.

## Deviations

- Neutral product keeps only the neutral's parts; portfolio `assumed_leaves` are `SITE:leaf`.

## Not verified

Mechanism-template tests (rebuild could drop another lane's template); Docker runner.

## Fix round 2 (review r1: M1, L1)

- M1: `evaluate.py` `_node` names the node itself in `missing_leaves` when its value is None for a node-level cause
  (CURRENCY_MISMATCH, ZERO_DENOMINATOR), so every ancestor and the portfolio keep a reason; `read.py` `site_count`
  tests `code in value.excluded`. Probe (Kobo productive_tariff KES): `out == (("Kobo", ("revenue",)),)`, never
  STRUCTURE_NOT_DECLARED. Tests: `test_m1_currency_mismatch_...`, `test_m1_zero_denominator_...` (include the
  every-None-has-a-reason check). Plant: old evaluate.py/read.py restored -> both m1 tests fail (2 failed).
- L1: `composition.py` disposes the snapshot store if the price builder raises; `test_l1_...` (fake store).
- Runs (worktree module paths verified): focused 152 passed; outcome regressions 78 passed; PG file
  (`heavy-slot.sh --db`, assetops_test) 5 passed; check-all fast: 40 guards passed (76.7 s).
