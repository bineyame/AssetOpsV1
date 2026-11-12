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

- `backend/tests/test_sr8_renewable_range_route.py` (stubs, real `ChainReader` over a fake port): **24 passed**.
  Covers every state, absent-row NO_DATA (D-SR.16), averages/partial, hours, link, known_at passed to the read,
  31-day window, 7 window refusals, admission/type/503 refusals, stored-route key + watermark, perf line.
  Non-vacuity: mapping EXCLUDED → COUNTED fails 2 tests (reverted).
- Adjacent: `test_w402_reads.py`, `test_ch5a2_contract.py` with the above: 71 passed, 3 skipped (no DB).
- `backend/tests/test_sr8_renewable_range_postgres.py` (DB `assetops_sr8_test`): **written, NOT RUN** (lane rule:
  Postgres only when the coordinator frees the DB; load avg ~8 with the demo build). Covers stored-row equality,
  MISSING_HOUR day, absent-row day, 3 sampled days vs the one-day depth `headroom_kw` card, totals.
- check-all: **All 19 guards passed** (957 s under load ~10; a first run hit a 900 s cap I set, not a failure).

## Pending (coordinator turn)

1. `ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_sr8_test`
   run of the Postgres file (single file). Risk: if a sampled day is EXCLUDED, the depth card may be null while the
   range shows the bounds; the assertion would then show it.
2. Parity and timing (KOBO-001, KISIWA-001 × 7/14/31 days), output `.agent/SR-8-parity.json`.
3. Page (Renewable tab, R726), vitest, `sr2RequestUrls` pin, `RANGE_MATRIX` Renewable D→R: after SR-4 merges.

## Questions (Architect)

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
