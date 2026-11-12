# SR-7 packet: mini-grid Service and claim limit over the date range (servers only)

Branch `task/SR-7-service-claim-range` (worktree `/opt/assetecon/AssetOpsV1-sr7`), main cdd65115c merged.
Spec: sequence doc rev 10 §10.3 + rev 10a §10a.2; D-SR.15/16/23-26. Pages not started (wait for SR-4 merge).

## Done

- **SR-7a** `GET /api/sites/{site_code}/service-range?from&to[&known_at]`, schema `site-service-range-1`.
  - Body: `backend/assetops_backend/mini_depth/service_range.py` (`service_range_body`, `day_state`, `hour_link`).
    One `ChainRequest.day(site, "MINIGRID", days)`; per day the stored `critical_served` value + the row's
    `covered_seconds`/`required_seconds` ÷ 3600 (D-SR.26). States: SERVED_ALL / SHORTFALL (unserved > 0) /
    NO_VALUE (COMPLETE|PARTIAL, no value); grade gaps NO_DATA→NO_READINGS, LOW→NOT_ENOUGH_READINGS,
    PENDING→STILL_PROCESSING, NOT_EXPECTED→NOT_EXPECTED; no snapshot row = NO_DATA (chain `day_gaps` rule, the
    D-SR.16 absent-row case). Totals sum counted (SERVED_ALL/SHORTFALL) days only; null sums when none counted.
    `hour_link` = Site-local 12:00 hour as UTC `from`/`to`.
  - Route: `build_service_range_router` in `mini_depth_api.py`. Admission `outcome_api.board_site`; cold/EV 404
    `SERVICE_RANGE_NOT_APPLICABLE`; window `estate_request` (422 INVALID_WINDOW); no chain reader / outage 503
    `SITE_SERVICE_RANGE_UNAVAILABLE`; StoredRoute key `{site, from, to, known_at}`, sites = watermark = the Site.
- **SR-7b** `GET /api/sites/{site_code}/claim-limit-range?from&to[&known_at]`, schema `site-claim-limit-range-1`.
  - Body: `backend/assetops_backend/estate/claim_limit_range.py` (`claim_limit_range_body`, `day_row`). Inside
    `read_snapshot` (confirmed `EvidenceMoneySnapshot`: `PostgresEvidenceMoneyRead`, `estate/composition.py:83`):
    `_scope` → `dispatch_days` → `note_page_days` → `day_revision` → `snap.claim_limit_on` → `w1.reduce_day`
    (D-SR.24). Row and summary per D-SR.25; null revision → NO_SELECTION, no link; link
    `/sites/{code}/evidence?day=&revision=`. Summary adds `days_requested`.
  - Route: `build_claim_limit_range_router` in `claim_limit_api.py`; admission as SR-7a; cold/EV 404
    `CLAIM_LIMIT_RANGE_NOT_APPLICABLE`; the one-day route's Performance gate (409 `PERFORMANCE_CUTOVER_CLOSED`);
    503 `SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE`; StoredRoute as SR-7a.
- `main.py`: both routers included after `build_chain_router` (after `responses`/`estate_portfolio`, D-SR.23).

## Tests

- `backend/tests/test_sr7_service_range.py` (no DB): **13 passed** (states, hours, totals, LOW, absent row, link,
  window, stored-route key/watermark, one chain read, 422 x5, 401/403/404/503, perf line).
- `backend/tests/test_sr7_claim_limit_range.py` (no DB): **10 passed** (rows = `reduce_day`, NO_SELECTION, no
  invented ceiling, unreconstructable reasons, note_page_days + cutoff/mode, summary, historical mode, 404 cold,
  stored route, 422 x3, 401/403/404/409/503, perf line).
- Adjacent no-DB: `test_w402_reads.py`, `test_qw1_perf.py` 29 passed / 3 skipped; `test_out_b4_main_binding.py`,
  `test_e4_prebuilt_routes_source.py` 7 passed.
- `backend/tests/test_sr7_claim_limit_range_postgres.py` (written; S4 world as SR-5a): see "Postgres" below.
- Guards: `tools/check-all.ps1` on de8e18504: **All 19 guards passed.**

## Postgres / parity (pending)

- `test_sr7_claim_limit_range_postgres.py` on `assetops_sr7_test` (harness clone): **2 passed** in 15.5 s (rows =
  `reduce_day(claim_limit_on)` with at least one selected day compared; rows on with absent runs == rows off).
- **Not written:** `test_sr7_service_range_postgres.py` (needs `mini_service` heads → chain snapshots; start from
  `tests/test_ch9_service_v2_postgres.py` `_installed` + `append_selection`, then the chain snapshot writer, then
  the route with the real Postgres chain reader: shortfall / served / gap / PENDING / absent-row days, totals, and
  3 sampled hours vs the one-hour `/performance/mini/service` CRITICAL rows).
- Parity `.agent/SR-7-parity.json` waits for the coordinator (D-SR.29 windows; D-SR.26: report per Site the days
  with a `critical_served` value).

## Resume

1. SR-7a Postgres test (above), on `assetops_sr7_test`, one file at a time.
2. After SR-4 merges: pages (Service tab day table in `MiniPerformance.tsx`; claim-limit day table inside
   `EvidenceClaimLimit.tsx`, D-SR.25), vitest, `sr2RequestUrls` pins, `RANGE_MATRIX` D→R, MOCK DEVIATION R725.
3. Parity when the coordinator gives the DB slot.

## Questions (Architect)

- **Q-J1 (days of the range).** §10.3 says `local_days(from, to, tz)`. For a UTC-midnight window and a positive
  offset (Kobo, Africa/Nairobi) that names N+1 local days (the last one 3 h wide). Built with
  `chain.read.window_days` instead (the estate-window rule: UTC-midnight windows name their UTC dates, read as
  the Site's local day of that date, the same "same date" rule D-SR.28 confirmed for SR-5). Confirm, or revert to
  `local_days`.
- **Q-J2 (grade → state).** "SR-5a gap states from the grade": mapped NO_DATA→NO_READINGS, LOW→NOT_ENOUGH_READINGS,
  PENDING→STILL_PROCESSING, NOT_EXPECTED; PARTIAL with a value is counted (vocabulary: "shown, and named").
  Confirm LOW is never counted even when it carries a value, and PARTIAL is.
- **Q-J3 (refusal codes).** Not named in the spec: 404 `SERVICE_RANGE_NOT_APPLICABLE` /
  `CLAIM_LIMIT_RANGE_NOT_APPLICABLE` for cold/EV, 503 `SITE_SERVICE_RANGE_UNAVAILABLE` /
  `SITE_CLAIM_LIMIT_RANGE_UNAVAILABLE` (by analogy with SR-6). SR-7b also applies the one-day route's Performance
  gate (409) so a closed cutover never leaks a ceiling. Confirm.
- **Q-J4 (SR-7b test target).** The one-day route body is the `claim-limit` schema, not a `claim_limit_on`
  projection, so `reduce_day` cannot be applied to it. The Postgres test compares each row to `reduce_day` of
  `ClaimLimitReadService.claim_limit_on` (the projection the AR-4 fallback composes) for the same day, revision and
  cutoff. Acceptable, or should it also compare named fields of the one-day route body?
- **Q-J5 (SR-7b window kind).** Built with `estate_request("evidence", ...)` (same window rule); `"portfolio"`
  makes `_scope` require the Portfolio cursor key env for a one-Site read. Confirm.
