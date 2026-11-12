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

- Guard fit (ae2759e59): the module receives `registration` (`evidence.composition.health_registration`) and
  `counts` (`sites.composition.health_range_counts`) by injection (adapter imports only from compositions); the new
  adapter is named as a read-only reader in `configuration-persistence.ps1` `$pgReaders` (the W3-01/W4-01 precedent;
  the SQL-write refusal still applies to it). No guard loosened.

## Tests (commits 5bf2a45a9, 89f7b5866, ae2759e59)

- `backend/tests/test_sr6_health_range_route.py` (no DB): **29 passed** (with `test_sr5_range_overview.py`: 60 passed).
  Day pin vs SR-5a body on SR-5a's world; contact/source rule tables; 422 x5, 404 Cold/EV/unknown/out-of-scope,
  401/403, 503 x2, stored key + watermark + perf line.
- `backend/tests/test_sr6_health_range_postgres.py` on `assetops_sr6_test` (created): **5 passed, 0 skipped**, 25.6 s.
  IN/PARTIAL/NO_CONTACT + pre-registration NOT_EXPECTED; READINGS_ONLY (readings on 10-06 via a gateway registered
  10-07); D-SR.19 cutoffs (all readings at max `decided_at`, none before the first, diagnostics cut at receipt);
  days equal SR-5a; rows on (absent `dispatch.day` rows) == rows off (D-SR.16).
- Adjacent: `test_s7_source_health_rules.py` 6 passed.
- Guards: `check-all` on ae2759e59: **All 19 guards passed** (first run failed 2 guards on the direct adapter
  imports; fixed as above).

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

## Fix round: D-SR.49 (Q1-Q5) applied
- Q1: `days_without_readings` = expected days with no accepted readings; added `days_not_expected`, `days_after_cutoff`; the four sum to `days_requested` (one class per day). 4-day Postgres world: with 1, without 3.
- Q2: `gateways_in_contact_all_days` over expected days only; a gateway with no expected day is not counted.
- Q3: labels are page wording (SR-6b); the body is unchanged.
- Q4: `AFTER_CUTOFF` for gateway `contact` and source `state` on days wholly at or after `min(to, k)`; `days[].state` unchanged.
- Q5: `battery` and the route's Foundation 409 removed (`source_health_api.py`); the page uses `/battery`.
- Tests: route (no-DB) 31 passed incl. new AFTER_CUTOFF/no-battery tests; `test_sr6_health_range_postgres.py` 5 passed on assetops_sr6_test. check-all: All 19 guards passed.

## Server review fix round (2026-11-12)
- M1: `gateways_in_contact_all_days` now uses each gateway's own non-NOT_EXPECTED/AFTER_CUTOFF days (intersected with Site expected days); test `test_gateway_registered_mid_window_counts_when_in_contact_after` (edge-2 registered day 2, in contact after, counts 1).
- M2: accepted readings > 0 win in `source_state` and the summary class (D-SR.56); route test rewritten, probe case (288 readings on a NOT_EXPECTED day, with=3) and a `source_state` param added. `range_days.py` untouched.
- L2: `test_health_range_reader_write_rejected` in `tools/checks/test_estate_guard.py`.
- L1 named limit (D-SR.56): `gateway_diagnostic`, `gateway`, `source` are not watermark inputs, so a stored live body's contact state or `disabled` flag may lag until local midnight or a readings arrival. Comment in `site_health_range.py`.
- L3: unchanged (merge SR-5 first). Main merged (D-SR.56).
- Checks: no-DB SR-6/SR-5/S7 files 70 passed; `test_sr6_health_range_postgres.py` + route on assetops_sr6_test 38 passed, 0 skipped; test_estate_guard.py 17 passed (745 s). check-all: for coordinator.
