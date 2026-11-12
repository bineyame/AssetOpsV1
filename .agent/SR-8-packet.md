# SR-8 packet: mini-grid Renewable over the whole date range (server part)

Branch `task/SR-8-renewable-range` (worktree `/opt/assetecon/AssetOpsV1-sr8`), main merged at cdd65115c.
Spec: rev 10 §10.4, rev 10a §10a.3, D-SR.15/16/23/27. Page not started (waits for SR-4 merge).

## Done

- `backend/assetops_backend/sites/renewable_range.py`: pure composer, schema `site-renewable-range-1`.
  Per day `{local_day, grade, low_kw, high_kw, decision, window_hours, covered_hours, operating_hours, state, link}`.
  State: a grade gap first (no row or NO_DATA → NO_DATA; PENDING; NOT_EXPECTED), else the stored value: ELIGIBLE →
  COUNTED, EXCLUDED → EXCLUDED (bounds shown), `result_state` CONFLICT / LIMITED / MISSING_HOUR (band null), graded
  row with no value → NO_VALUE. Hours = row `covered_seconds` / `required_seconds` ÷ 3600 (operating hours).
  Totals `{days_requested, days_counted, average_low_kw, average_high_kw, average_label: "average daylight
  headroom", partial}`: averages over COUNTED days with both bounds, low and high separately.
  Link `/sites/{code}/performance/renewable?from=<local midnight UTC>&to=<+1 day>`.
- `mini_depth_api.py`: `RENEWABLE_RANGE_ROUTE` + `build_renewable_range_router(chain_reader, registry, access,
  unavailable, responses)`; `perf.route`; StoredRoute key `{site, from, to, known_at}`, `sites`/`watermark_sites` =
  the Site. Refusals 401/403/404 `SITE_NOT_FOUND`/404 `RENEWABLE_RANGE_NOT_APPLICABLE` (Cold/EV)/422
  `INVALID_WINDOW` (estate rule via `estate_request`: UTC midnights, ≤31 days)/422 `INVALID_KNOWN_AT`/503
  `SITE_RENEWABLE_RANGE_UNAVAILABLE`. One `ChainRequest.day` read over `window_days(from, to, tz)`.
- `main.py`: router included after `build_chain_router` (after `responses`, `estate_portfolio`, `outcome_board`;
  D-SR.23), chain reader = `outcome_board.s.chain_reader`. `MAX_DAYS = 5` depth read untouched.

## Tests

- `backend/tests/test_sr8_renewable_range_route.py` (stubs, real `ChainReader` over a fake port): **26 passed** (incl. D-SR.47 LOW-with-value and PARTIAL-counted tests).
  Covers every state, absent-row NO_DATA (D-SR.16), averages/partial, hours, link, known_at passed to the read,
  31-day window, 7 window refusals, admission/type/503 refusals, stored-route key + watermark, perf line.
  Non-vacuity: mapping EXCLUDED → COUNTED fails 2 tests (reverted).
- Adjacent: `test_w402_reads.py`, `test_ch5a2_contract.py` with the above: 71 passed, 3 skipped (no DB).
- `backend/tests/test_sr8_renewable_range_postgres.py` (DB `assetops_sr8_test`): **1 passed** (61 s). Covers stored-row equality,
  MISSING_HOUR day, absent-row day, 3 sampled days vs the one-day depth `headroom_kw` card, totals.
- check-all: **All 19 guards passed** (957 s under load ~10; a first run hit a 900 s cap I set, not a failure).

## Pending (coordinator turn)

1. (done) Postgres file run.
2. Parity and timing (KOBO-001, KISIWA-001 × 7/14/31 days), output `.agent/SR-8-parity.json`.
3. Page (Renewable tab, R726), vitest, `sr2RequestUrls` pin, `RANGE_MATRIX` Renewable D→R: after SR-4 merges.

## Rulings applied

- D-SR.45: `window_days` (Q1). D-SR.47: NO_VALUE, 0.01 rounding on averages only, codes and `known_at` in the key
  confirmed; LOW grade -> NOT_ENOUGH_READINGS, never counted; PARTIAL-grade COUNTED/EXCLUDED day has `partial: true`.

## Q6 resolved by D-SR.48 (server part built)

- Depth `cards.all_hours_headroom_kw` {low, high} (`mini_depth/rules.py summarize_renewable`, `read.py compose_renewable`
  and `NULL_CARDS`): min low and min high over ELIGIBLE hours of ELIGIBLE days; null when `headroom_kw` is null. The
  existing `headroom_kw` card is unchanged. The stored day value equals it exactly (Postgres test); card high >= stored high.
- Tests: `test_w402_rules.py` (field, low==card low, high<=card high, null on excluded), `test_w402_reads.py`
  (compose value and null cards), `test_sr8_renewable_range_postgres.py` (exact equality on sampled days).
- Server bodies carry no label text for this figure; wording lives in the page.
- Page resume points (frontend, after SR-4): range per-day and totals wording "Headroom available in every eligible
  hour: low-high kW" / totals "average headroom available in every eligible hour"; one-day Renewable line under the
  card with the same words from `cards.all_hours_headroom_kw`; relabel the existing card "Range across eligible
  hours"; record MOCK DEVIATION R726; vitest pins the one-day line and range wording; parity JSON compares stored day
  value to `all_hours_headroom_kw`, gate 0 mismatches. Add `all_hours_headroom_kw` to `miniDepthClient.ts` cards type.

## D-SR.62 fix (one-day read follows the stored measure's missing-hour rule; sequence doc §10e.1)

- Commits 6377fea9e (code + pure tests), b28fec415 (Postgres sample). main merged at 26c4845a7.
- `read._Hour.missing` (last field, default False) = the hour is in `daylight_hours(...).missing` at the cutoff.
  Set by `hour_windows(..., missing=<set>)` (new optional collector of `(day, window.start)`), passed through
  `_hour(..., missing)` on the compose path (`_read`) and in `build_period`; `_job_fallback` keeps a row's flag
  (`dataclasses.replace`). Stored: `period_rows.hour_json` writes `"missing"`, `hour_from_json` reads it (absent =
  False). `BUILDER_VERSION` = `mini-depth-rows-2` (a `-1` row reads PENDING_RECOMPUTE by the existing version rule).
- `compose_renewable(hours, *, missing=frozenset())`: missing hours leave the decision, cards and UNKNOWN test; a day
  is missing only when a non-missing hour has no head. `rules.summarize_renewable(..., partial_days=())`: any partial
  day blocks `recurrence_established` (not exposed on the wire today).
- **Interpretation for Architect confirmation (commit 1a4d94dd5):** a day whose every hour is missing (no pv reading
  at all, so no measured daylight hour) is still a missing day (UNKNOWN), not dropped. The literal rule ("missing only
  when a non-missing hour has no head") dropped it and turned `test_w402_reads_postgres` 10-11 from UNKNOWN to
  LIMITED; the stored measure gives such a day no inputs and no value, so this keeps the one rule.
- Envelope: renewable gains `missing_hours` (count of missing windows); other domains unchanged.
- **Shared functions touched (SR-10 merge note):** `read.hour_windows` (new kwarg), `read._Hour` (new field),
  `MiniDepthRead._hour` (new trailing param), `_read`, `_job_fallback`, `build_period` (renewable branch only),
  `renewable_envelope`, `_envelope`; `period_rows.hour_json`/`hour_from_json`/`BUILDER_VERSION`;
  `rules.summarize_renewable`. Fuel/service/backup paths unchanged except the shared version bump.
- Tests: `test_w402_reads.py` +6 (Finding-day shape SUPPORTED 25-31, 1/1, `missing_hours` 16; headless daylight hour
  UNKNOWN; partial day no recurrence; shared-rule pin vs `RenewableHeadroom.measure` for complete/partial/headless);
  `test_ar2_mini_period_rows.py` +1 (round-trip, v1 body). `test_sr8_renewable_range_postgres.py`: DAYS[2] gets 4
  hours with no pv reading; asserts one-day `missing_hours` = range uncovered hours = 4, PARTIAL, and value equality.
  Non-vacuity: dropping the missing filter fails the Postgres test and 2 pure tests (reverted).
- Runs (final rev 1a4d94dd5): no-DB SR-8 + w402 rules/reads + AR-2 + board neighbours 193 passed / 3 skipped;
  Postgres on `assetops_sr8_test`: w402_reads + SR-8 + ar2_mini_period_rows 11 passed (5 m 11 s). check-all: for coordinator.
- Parity JSON: the "all 7 rows EXCLUDED" note corrected (`correction_d_sr62`). Coordinator: rebuild `mini_depth.*`
  rows (KOBO-001, KISIWA-001), rerun parity with gate 0, `missing_hours` equal, decisions from `rows[].decision`.
- Grow board (expected effect): a 5-day board window holding a Finding day (27 Oct, 3 Nov, 10 Nov on Kobo) now counts
  that day as assessed (ELIGIBLE, 25-31 kW) instead of missing; it never sets recurrence. Board fixtures unchanged.
- Page resume point (page not built): the one-day Renewable page shows the D-E5.45 PARTIAL label when
  `missing_hours` > 0, with the range row's words, inside R726; add `missing_hours` to `miniDepthClient.ts`.

## Questions (Architect, answered by D-SR.45/47)

- Q1 Days of the window: used `window_days` (UTC-midnight window → its UTC dates read as Site-local days, the
  estate frame rule), so 7 UTC days = 7 rows. `local_days(from, to, tz)` (as rev 10.3 names for SR-7) would give 8
  Site-local days for a UTC+3 Site. SR-7 should use the same rule; confirm which.
- Q2 A graded row with no value (or an unknown decision) reads `NO_VALUE` (borrowed from D-SR.26); not in D-SR.27's
  state list. Confirm.
- Q3 Averages are rounded to 0.01 kW (half-up). Confirm the step.
- Q4 Grade-gap precedence: a PENDING/NO_DATA/NOT_EXPECTED grade wins over any stored value; LOW/PARTIAL/COMPLETE
  grades read the value (so a PARTIAL-grade ELIGIBLE day is COUNTED). Confirm.
- Q5 Refusal codes `RENEWABLE_RANGE_NOT_APPLICABLE` / `SITE_RENEWABLE_RANGE_UNAVAILABLE` by analogy with SR-6; the
  route also accepts optional `known_at` (spec lists only from/to). Confirm.

## Resume

Run pending 1-2 when the DB is free; then the page after SR-4 merges (rev 10 §10.4 page bullet).

Checks (D-SR.48 follow-up): no-DB neighbours 58 passed/3 skipped; Postgres SR-8 file 1 passed (assetops_sr8_test); w402_reads_postgres + w501_cold_depth_postgres 19 passed; check-all: All 19 guards passed.
