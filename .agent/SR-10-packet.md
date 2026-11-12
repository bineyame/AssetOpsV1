# SR-10 packet: SR-10/11 shared core + SR-10b Fuel range server (lane K)

Branch `task/SR-10-fuel-range` from main bbec56c26. Spec: rev 10b.1-10b.3, rev 10d.4 (D-SR.45 Q-J1), D-SR.31-33/36.

## Outcome
- **Core (commit 7f928edb2, SR-11 builds on it).** Two `site_period_read` kinds, grain `local_day`,
  `mini_depth.fuel_day` / `mini_depth.backup_day`, each storing every Site-local hour through
  `MiniDepthRead.build_period(..., whole_day=True)` -> `worker.hours_within(local midnight, next midnight)` ->
  the existing `_hour`. No migration, no `BUILDER_VERSION` bump; the noon kinds are unchanged.
  Register entries (same inputs as the noon kinds) make the tick's consume + drain rebuild them;
  `chain/composition.period_kind_builders` picks them up via `kind_builders` (no second registration).
  `mini_depth/day_summary.py`: pure `fuel_day_summary`, `backup_day_summary`, `day_state` (rev 10b.1 order + `partial`),
  and a shared range composer (`compose`, `range_days`, `totals`, `hour_link`, `day_grades`) for both domains.
  An absent row reads STILL_PROCESSING; nothing is composed on read.
- **SR-10b route (commit 3fc8c4c23).** `GET /api/sites/{code}/fuel-range`, `site-fuel-range-1`, via a generic
  `mini_depth_api.build_day_range_router(domain, period_reader, chain_reader, ...)`; `main.py` wires `"fuel"` only
  (SR-11 wires `"backup"` with the same builder; its refusal codes are already in `DAY_RANGE_REFUSALS`).
  Days = `window_days(from, to, tz)` (D-SR.45, corrects 10b.2's `local_days`); one period read + one `ChainRequest.day`.
  StoredRoute keyed `{site, from, to, known_at}`, `sites`/`watermark_sites` = the Site.

## Files
- `backend/assetops_backend/mini_depth/{read.py,period_rows.py,day_summary.py}`, `config/chain/event-register-v1.yaml`
- `backend/assetops_backend/mini_depth_api.py`, `backend/assetops_backend/main.py`
- Tests: `test_sr10_day_summary.py` (new, 9), `test_sr10_fuel_range_route.py` (new, 14),
  `test_sr10_day_kinds_postgres.py` (new, 4); kind lists updated in `test_ch1b_register.py`, `test_ch1b_drain.py`,
  `test_any1_period_read.py`; `test_ar2_mini_period_rows_postgres.py` builds only the four board kinds.

## Acceptance (rev 10b.1-10b.3, server part)
| Item | Status |
|---|---|
| Two local_day kinds, every local hour via `_hour`, no migration/version bump | Done; Postgres pin: 24 stored hours == 24 live `_hour` reads, both kinds |
| Register lines, tick rebuild | Done; Postgres: accepted-reading event -> pending -> `consume` + `drain` -> revision+1 |
| Reducers: bound sums, missing/pending, limitations union, chain dedupe, start-success null rule, no outage key | Done (pure tests) |
| Day state order + `partial`; absent row STILL_PROCESSING | Done (pure + Postgres) |
| Route: 422/404 (Cold, EV)/401/403/503, stored key + watermark, perf line, 7-day Nairobi = 7 rows | Done (stub tests) |
| 3 sampled hours == one-hour route card (12:00 = drill-in link) | Done (Postgres) |
| `chain.graph check` | exit 0 |
| Page `MiniFuelRange.tsx`, vitest, RANGE_MATRIX, sr2RequestUrls | **Not started** (waits for SR-4, per brief) |
| D-SR.36 backfill, parity `.agent/SR-10-parity.json`, 2 s timing | **Pending** (coordinator) |

## Checks
- No-DB: `test_sr10_day_summary.py` + `test_sr10_fuel_range_route.py` 23 passed; adjacent register/drain/AR-1/AR-2/AR-3
  no-DB files 124 passed.
- Postgres (`assetops_sr10_test`, one file at a time): `test_sr10_day_kinds_postgres.py` 4 passed (174 s);
  `test_ar2_mini_period_rows_postgres.py` 3 passed (243 s). Commits: core 7f928edb2, route 3fc8c4c23, Postgres pins 3ed855559.
- Guards: `check-all.ps1` on 3ed855559: "All 19 guards passed." `chain.graph check` exit 0.

## Interpretations (please confirm; no design beyond these)
1. Hour classes: pending = `PENDING_RECOMPUTE` or a live job (PENDING/LEASED); assessed = not pending with a head;
   missing = the rest. `expected_use_l`, `status_counts`, limitations, sequences and start successes are over
   assessed hours only (a pending hour's stored head is not summed; its day is STILL_PROCESSING anyway).
2. `slowest_recovery` = the largest `critical_recovery.seconds` over the de-duplicated sequences (not the hour cards).
3. An absent day's entry carries the zero-hour summary (`hours_expected: 0`) with `state: STILL_PROCESSING`.
4. Totals `partial` = a requested day not counted, or a counted day `partial`. Backup `days_counted` counts
   SEQUENCE_FAILED/INCOMPLETE/PASSED and NO_SEQUENCE days.
5. The route ignores the `ASSETOPS_PERIOD_READ_KINDS` kill switch (no compose fallback exists, D-SR.31).
6. The "new accepted reading" in the Postgres test is its `reading.accepted` outbox event (as AR-1's test), plus a
   live job so the rebuilt row differs.

## Residual risk / for the coordinator
- `tools/demo_combined.py build_period_rows` builds every declared kind, so the day kinds are included without a
  change, but each day now builds 48 more `_hour` reads per mini Site inside the prepare's 15-minute cap: time it on
  the VPS backfill (D-SR.36), with the head-count pre-flight first.
- Merge: SR-8 adds `build_renewable_range_router` to the same `mini_depth_api.py` imports/`__all__` and `main.py`
  after the chain router; the second merger resolves (rev 10b.5).

USER_REVIEW_REQUIRED: no (server slice; the page waits for SR-4).
