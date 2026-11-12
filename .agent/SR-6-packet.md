# SR-6 packet (lane I) — SR-6a server

Branch `task/SR-6-health-range`. Spec: rev 10 §10.2, rev 10a §10a.1, D-SR.19-23 (rev 10b/10c: no SR-6a change). Merged main cdd65115c and 9afb0bcee and lane H's
`range_days.py` commit 034852bb2 (D-SR.22 "SR-6 merges that commit"; brings the SR-5 branch up to that commit).

## Done (SR-6a)

- `backend/assetops_backend/sites/site_health_range.py`: `health_range_body(service, tenant_id, site_code, req)` on one
  `read_snapshot`: `PostgresGatewayAccess._health_registration(snap._c, ...)` (called), the grouped counts, then
  `select_finding_scope` (coverage only) + `estate.range_days.range_day_states` (ANALYSED kept). Contact rule D-SR.20
  (IN/PARTIAL by `diagnostics x cadence >= 0.9 x` day seconds in `[from, min(to,k))`, READINGS_ONLY, NOT_EXPECTED
  before the registered day, NO_CONTACT); source-day NOT_EXPECTED from `days[].state` (D-SR.23). No dead branches
  (D-SR.21).
- `backend/assetops_backend/sites/adapters/postgres_health_range.py`: the two grouped reads. Readings join
  `ingestion_disposition` (ACCEPTED, `accepted_evidence_id = e.id`, `decided_at <= k`, `tenant_id`), bucketed on
  `COALESCE(interval_start, source_time)`; diagnostics on `received_at <= k` (D-SR.19).
- `source_health_api.py`: `build_health_range_router` (new builder), `GET /api/sites/{code}/health-range`; admission as
  source-health; Cold/EV 404 `HEALTH_RANGE_NOT_APPLICABLE` (from the registry's site type, before the window); 422
  `INVALID_WINDOW` via `estate_request`; 503 `SITE_HEALTH_RANGE_UNAVAILABLE`; stored route key
  `{site, from, to, known_at}`, `sites`/`watermark_sites` = the Site; `perf.route` line. `battery` = the existing
  `battery_entry` body. `main.py`: included right after `estate_portfolio` (D-SR.23); source-health router unchanged.

## Tests (commits 5bf2a45a9, 89f7b5866)

- `backend/tests/test_sr6_health_range_route.py` (no DB): **29 passed** (with `test_sr5_range_overview.py`: 60 passed).
  Day pin vs SR-5a body on SR-5a's world; contact/source rule tables; 422 x5, 404 Cold/EV/unknown/out-of-scope,
  401/403, 503 x2, stored key + watermark + perf line.
- `backend/tests/test_sr6_health_range_postgres.py` on `assetops_sr6_test` (created): **5 passed, 0 skipped**, 25.6 s.
  IN/PARTIAL/NO_CONTACT + pre-registration NOT_EXPECTED; READINGS_ONLY (readings on 10-06 via a gateway registered
  10-07); D-SR.19 cutoffs (all readings at max `decided_at`, none before the first, diagnostics cut at receipt);
  days equal SR-5a; rows on (absent `dispatch.day` rows) == rows off (D-SR.16).
- Adjacent: `test_s7_source_health_rules.py` 6 passed.
- Guards: see report (`check-all`, 19 guards).

## Pending / resume

- Parity + timing (KOBO-001, KISIWA-001 x 7/14/31 on a `<prefix>_audit` copy, D-SR.29) → `.agent/SR-6-parity.json`,
  incl. `gateway_diagnostic` counts per Site and the contact histogram (D-SR.20): waits for the coordinator.
- SR-6b page (SiteHealthRange.tsx, client, R724 register row, sr2RequestUrls pin, RANGE_MATRIX N→R): waits for SR-4.

## Questions for the Architect

1. `summary.days_without_readings`: built as days whose state is NO_READINGS (SR-5a rule). On the Postgres world it is
   0 while 3 of 4 days have no readings (they are NOT_ANALYSED). `days_with_readings` = days with any accepted reading
   (step 3). Is that the intended pair, or should "without" be `days_requested - days_with_readings` (minus
   NOT_EXPECTED)?
2. `summary.gateways_in_contact_all_days`: built as gateways whose every day is IN_CONTACT (a NOT_EXPECTED or
   READINGS_ONLY day breaks it). Confirm.
3. `days[].accepted_readings`: built as SR-5a's (the dispatch row's `accepted_reading_count`, null on gap states),
   not the step-3 sum. Confirm.
4. A window day wholly after k (e.g. today+1): no diagnostics/readings → NO_CONTACT / NO_READINGS. Should such days
   read NOT_EXPECTED (or be excluded)? Not designed; left as the rule's fallthrough.
5. Battery: built outside the snapshot (Foundation read, as `/battery`); a Foundation refusal makes the whole route
   409 `FOUNDATION_BASIS_UNAVAILABLE`, a store outage 503. The stored response's watermark is the Site's chain
   watermark, so a Foundation battery change may serve a stale battery block until the watermark moves. Accept, or
   should the page fetch `/battery` itself (drop `battery` from the body)?
