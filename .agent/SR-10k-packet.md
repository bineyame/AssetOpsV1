# SR-10k review packet: Kisiwa fuel-check nights over the date range (0.25 u)

Branch `task/SR-10k-kisiwa-fuel-nights` (merged main e5a033a3b). Spec: architect sequence rev 10b.4 "SR-10k", 10c (IN), 10d.3 (Fuel R via SR-10k); D-SR.34, D-SR.37, D-SR.45 (J1 `window_days`).

## Delivered
- Server (931c4b783): `GET /api/sites/{code}/fuel-balance/nights` also takes the date range's UTC instants `from`/`to` (detected by a `T` in either value). Both or neither, `from < to`, else 422 `INVALID_WINDOW`. `FuelNightRead.nights(window=...)` lists the nights whose `night_date` is one of `chain.read.window_days(from, to, site tz)` (D-SR.45), at most 31, else `INVALID_WINDOW`. No params: unchanged (latest 14). The existing date form (`from=YYYY-MM-DD`) and its `FUEL_BALANCE_RANGE_INVALID` refusals: unchanged (K5 Postgres B2 still passes).
- Page (bf9ca80e6): `useFuelNights(client, siteCode, range)`; `MiniFuel` passes `rangeWindow(useSharedRange())` when the address range is set, else `null` (request unchanged). `getNights(code, range?)` adds `?from=&to=`. A range with no night shows "No fuel checks in this date range" (`[data-fuel-nights-empty]`) and opens no night. Night detail (`?night=`) stays the drill-in. Did not need SR-4's RangeLink/rangeFocus.

## Files
- `backend/assetops_backend/fuel_balance_api.py`, `backend/assetops_backend/fuel_balance/night_read.py`
- `backend/tests/test_sr10k_fuel_nights_range.py` (route stub, no DB, 8 tests), `backend/tests/test_sr10k_fuel_nights_range_postgres.py` (1 test)
- `frontend/src/sites/fuelBalanceClient.ts`, `MiniFuelNights.tsx`, `MiniPerformance.tsx`
- `frontend/src/sites/__tests__/miniFuelNights.test.tsx` (+4), `frontend/src/shell/__tests__/sr2RequestUrls.test.tsx` (+1 pin)

## Acceptance (rev 10b.4)
- Route takes optional from/to, both or neither, else 422 INVALID_WINDOW: met (instant form).
- Filters nights by Site-local day of `[from, to)`: met via `window_days` (UTC-midnight bounds name UTC dates, other bounds Site-local days; D-SR.45).
- No params unchanged: met (stub + Postgres).
- `useFuelNights(client, siteCode, range)` sends the range; empty state text; night detail stays drill-in: met.
- Tests: route stub, Postgres filter test, vitest, pin: met.

## Checks
- No-DB: `pytest test_sr10k_fuel_nights_range.py test_k5_fuel_night_text.py` 32 passed.
- Postgres (DB `assetops_sr10k_test`, rev 931c4b783 code): `test_sr10k_fuel_nights_range_postgres.py` + `test_k5_fuel_night_api_postgres.py` 7 passed, 0 skipped, 29.5 s.
- vitest: `miniFuelNights.test.tsx` 13 passed; `sr2RequestUrls.test.tsx` 16 passed. `tsc --noEmit` clean.
- Mutation proof: removing the empty state and dropping the range made the 4 new vitest cases fail (4 failed / 25 passed); reverted by `git checkout`.
- check-all (rev bf9ca80e6): "All 19 guards passed."

## Known deviations / questions for the Architect
1. The route already took `from`/`to` as **night dates** (K5, `FUEL_BALANCE_RANGE_INVALID`, pinned by K5 B2). The spec reads as if it took none. I kept the date form and added the instant form beside it. Is that right, or should the date form go?
2. Refusal message for `INVALID_WINDOW`: no wording was specified, so it reuses the nights sentence ("Choose up to 31 nights, with the first night before the last.") rather than the mini-depth hour sentence. Confirm.
3. `known_at` of the range is **not** sent on the nights list (the night detail sends none either, so list and detail stay at the same knowledge time). Should both carry the range's `known_at`?
4. A `?night=` link (demo story links, no range) with a range in the address that does not hold that night opens the range's latest night instead. Story links carry no range today, so their request is unchanged.

## Residual risk
- Range bounds that are not UTC or Site-local midnights rely on `window_days`' frame rule; 31-day non-aligned windows can name 32 days and are refused (shell writes UTC-midnight bounds, so not reachable from the bar).

## User review
Not required (lane rules: merge on review ACCEPT).
