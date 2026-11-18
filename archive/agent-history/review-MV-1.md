# Review MV-1: mill dollars on the verdict page (first review)

- Reviewer: fresh Claude (Opus), independent of the builder. 2026-11-07.
- Branch `task/FUEL-MV1-mill-dollars`, worktree `C:\Users\assef\Bineyame\AssetOpsV1-mv1`, reviewed at `ceab577a7`
  (merge base `f63b46a01`). Diff: `git diff main...HEAD` (15 files).
- Judged against `.agent/build-sheet-FUEL-1.md` §2, `.agent/owner-diesel-site-2026-11-07.md` (Q4 on main `8032040e8`)
  and `.agent/owner-fuel-scope-2026-11-07.md`.

## Verdict: ACCEPT

The build follows §2.2–§2.4 almost line for line. There are no High or Medium findings. Four Low findings follow.
None of them blocks the merge. L1 and L2 are cheap to fix on the branch if a Sonnet round is open anyway. L4 is for
the Architect.

## Is the dollar figure defensible

- **Price in force across both periods, as known at verdict time.** `_mill_price` (`B/actions/verification.py:403-419`)
  uses one window, `[local midnight of the first baseline day, local midnight after the last later day)`, in the plan's
  Site timezone. It calls `select_window_price`, which returns PRICED only when a single assignment covers the whole
  window (`fuel_cost.py:445-464`). Any change, gap or overlap returns UNPRICED. The window includes the days between
  the two periods, so it errs on the conservative side. `known_at = recorded_at` of the stored outcome. In the demo,
  both timestamps are story time. The price is recorded at install + 1 h (`T/demo_combined_kobo.py` `publish_price`,
  test clock override), and the outcome at `evaluate_at` (`T/demo_combined_mill.py:290`). So the v1 price is visible
  at the verdict's cutoff on the real dataset, not only on L2.
- **Hand-checkable.** The arithmetic uses the stored cent means that the R7 line and the table show, times the shown
  price text. `_price_text` keeps every stored decimal, so the shown price equals the price used. `money2` rounds half
  even.
- **Fully checked days only.** A value is produced only for a stored VERIFIED outcome, with the `nb == nl == MIN_DAYS`
  guard. Every other state carries `value: null`. LIMITED is not a state on this path: a mill outcome is VERIFIED,
  INEFFECTIVE or INCONCLUSIVE, and only VERIFIED gets a value.
- **No annualising, no summing.** Only per-day figures appear, and there is one basis (`VALUE_BASIS`). Nothing adds the
  value to another line.
- **UNPRICED.** NO_PRICE and PRICE_SPANS_WINDOW have their own reasons. Every other reason, and a missing port, reads
  "could not be read". `per_day` stays null, never 0.

## Client wording

The literals are §2.2(e) verbatim, with U+2212 in the text. The cost line reads "No cost is recorded for this change",
which matches the owner's Q4 answer exactly. The page shows the server strings and formats nothing itself. The
`PRICED`/`UNPRICED` values sit only in a `data-` attribute. I found no system vocabulary in the visible text. See L4 for
one reason text that can be inaccurate.

## Findings

### L1 (Low): a price-store error turns the whole verdict page into an error
- Where: `backend/assetops_backend/actions/verification.py:400` and `:403-419`.
- What: `_mill_price` calls the port without a guard. Before MV-1 the verdict read never touched the assumption store.
  Now any exception from `PostgresAssumptionStore.snapshot` reaches `action_api.run` (`action_api.py:83-89`). Unless it
  is in `down`, that is a 500. The page then shows `MILL_UNEXPECTED` instead of "Target met".
- Scenario: a transient failure while reading the assumption tables during the demo. The client loses the verdict
  because of a secondary money line.
- Fix: in `_mill_price`, catch the store-unavailable or DB error, `LOG.exception` it, and return None.
  `mill_value(price=None)` already renders "No sales estimate: the declared price per kWh could not be read".
- Risk is low: the price is read from the same DB as the outcome.

### L2 (Low): the "as known at verdict time" rule and the window end are not pinned by any test
- Where: `backend/assetops_backend/actions/verification.py:415-416`, and `backend/tests/test_ch9b3_mill_verdict_postgres.py`
  (the two MV-1 tests).
- What: both L2 tests publish the price before the verdict is recorded. Neither publishes a later revision. Two
  mutations would pass every MV-1 test:
  - passing `known_at=None` (current), or `datetime.now(...)`, to the port;
  - dropping `+ timedelta(days=1)` from `hi`.
  The packet's non-vacuity list covers `lo`, but not `known_at` or `hi`.
- Scenario: a later edit swaps the cutoff for "current". A v2 price published after the verdict then silently changes
  the dollars on a recorded verdict, which is the property §2.2(c) names, and nothing goes red.
- Fix: one L2 test. Record the VERIFIED outcome, then publish a v2 productive price at a later recorded time (same
  `valid_from`, different value). Assert the value still cites v1's revision id and 17.00. Optionally, publish a price
  whose `valid_to` falls inside the last later day and assert PRICE_SPANS_WINDOW.
- The code is correct today. This is a test gap only.

### L3 (Low): MILL-3b takes the currency from the page, and the row does not check the revision
- Where: `tools/demo_combined_rows.py:263`, `cur=value.get("currency")`.
- What: the expected text is built with the page's own currency. A wrong currency on the served value would satisfy
  the text check. `per_day` is recomputed independently, which is the main point of the row. The fixture's currency
  (USD) is not compared.
- Fix: return `(value, currency)` from `productive_price_v1` and assert `value.currency` equals the fixture's currency.
- This is minor for the demo dataset, where there is only one currency.

### L4 (Low, for the Architect, not the builder): the PRICE_SPANS_WINDOW reason text can be wrong
- Where: `backend/assetops_backend/actions/verification_families.py:247`. The §2.2(e) literal is copied verbatim.
- What: `select_window_price` returns PRICE_SPANS_WINDOW whenever no single assignment covers the whole window. That
  includes a price that starts inside the window with nothing before it, which is exactly the L2 span test, and a
  change inside one period. The client still reads "the declared price per kWh changed between the two periods".
- Scenario: a Site whose price was first declared halfway through the baseline week. The page claims the price
  changed, but it was never set for the earlier days.
- Fix (Architect's call): neutral wording, for example "one declared price per kWh does not cover both periods".
- This is not reachable on the demo dataset: v1 starts on 2026-01-01 and is open-ended.

## Deviations

- **KD-1 (pure row functions in `T/demo_combined_rows.py`)**: justified. It is the same pattern as MILL-3's `mill_page`,
  and it is what makes the L0 self-test possible without a database.
- **KD-2 (the parser also requires state PRICED or UNPRICED)**: justified, because it matches the declared type. Side
  effect: if the server ever adds a third value state, the whole page reads as a parse error rather than dropping only
  the value line. That is acceptable while the backend emits only these two.
- **MD-FUEL-MV1-1**: present in the header comment of `SiteMillVerification.tsx` and in the packet row. The visible
  mock-deviation line is unchanged. The new `<p>` elements carry no class, like the existing lines. No new CSS.

## Tests: do they fail when broken

- L0 1 and the grid compute the expected values independently of `money2`, using local half-even quantize. Test 1
  also pins the literal 17.00 / 10.50 / 27.50. A wrong multiplier, wrong rounding or swapped means fails.
- L0 3 and 4 cover every UNPRICED branch and every null path, including the equal-means, lower-means, missing-mean and
  short-days guards.
- Key order is pinned for the stored, NOT_JUDGED and NO_PLAN bodies, so S1 is covered.
- `test_s4_fuel_cost`: the default call still gives PRICE_UNIT_MISMATCH, so existing callers keep their behaviour.
- L2: priced through the composed builder with the real fixture; the span test catches a `lo` regression. Gaps as in L2.
- vitest:
  - PRICED renders both lines, before the table.
  - UNPRICED renders its text and the cost line.
  - A null value renders neither.
  - The parser accepts a missing `value` and rejects a non-string `text` or `cost_text`.
- MILL-3b self-test: rejects `per_day` 17.01, UNPRICED, a wrong text, a wrong cost text, a null value and a different
  price (0.26). The fixture page is built by `mill_value` itself, so the text check depends on the same constant, which
  §2.4 allows. `per_day` is recomputed independently.
- I did not run mutations myself: the dispatch says no code edits. The claims above come from reading the assertions.

## Regression risk

- `select_window_price` has keyword-only additions with defaults. The other callers (`recompute.py:165`,
  `consequence_read.py:354`, `composition.py` diesel `price_selection`) pass no keyword, so their behaviour is
  byte-equal.
- `summary_wire` and `domain_summary` are used only by the mill route (`action_api.py:318`) and by two tools:
  `T/demo_combined_mill.py:293` (writes the summary into a JSON doc, which now has a `value` key; harmless) and
  `T/dd1b2a_probe.py`.
- Cold and EV verdict pages do not share this code. The added `value: null` key is additive for every state.
- Frontend: `MillVerification` gains a required `value` field. `tsc --noEmit` is clean, so no other constructor of the
  type broke.

## Checks I ran (worktree, `assetops_backend.__file__` resolved to `C:\Users\assef\Bineyame\AssetOpsV1-mv1\backend\assetops_backend\__init__.py`)

| Check | Result |
|---|---|
| `pytest test_ch9b3_mill_verdict.py test_s4_fuel_cost.py test_demo_combined_finish_rows.py -q` | 89 passed, 2.96 s |
| Free RAM before Postgres | 3.99 GB |
| `pytest test_ch9b3_mill_verdict_postgres.py -q` on `assetops_mv1_test` | 8 passed, 38.4 s |
| `npx.cmd vitest run src/sites/__tests__/millVerification.test.tsx` | 10 passed (it ran here despite the usual esbuild sandbox issue) |
| `npx.cmd tsc --noEmit` | exit 0 |

## Not run / not verified

- Guards A, N, V, M, W and frontend-hardwiring: the dispatch limited me to the touched test files. The packet's guard
  results are unverified by me.
- MILL-3b on a built dataset: it runs at E3. The real `actions/composition.py` wiring line is exercised only there and
  in the served app, as the packet says.
- The full frontend suite and the production build were not run.
