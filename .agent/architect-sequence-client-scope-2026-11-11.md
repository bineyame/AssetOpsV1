# Architect: one sequenced view of walkthrough comments and backlog, for the client-demo scope (2026-11-11)

## Revision 10b (Architect, Claude, 2026-11-12 night): every tab follows the range; SR-10 to SR-14; nothing drops before Saturday

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Rulings **D-SR.31-38** (build sheet), owner-directed, logged for owner review.
- Owner, verbatim (`.agent/owner-all-tabs-respect-range-2026-11-12.md`): "all tabs should respect the date range without exception", and then "we have to work on the items and reassess on saturday and not limit what is in or not now".
- **Correction to 10a.** 10a.5 said Fuel could read the chain day measure `avoidable_gen_min`. That was wrong. `avoidable_gen_min` is dispatch minutes (`chain/measure_impls.py` `DispatchMinutes`), not fuel. Fuel and Backup both get their range from the stored **hourly `mini_depth` heads** (`mini_depth_selection` with domain `fuel`/`backup`, one per Site-local hour, as `critical_served` reads the `service` heads). It is new **stored day rows**, not a new chain measure. A new MINIGRID entry in `chain/measures.py` `MEASURES` would change every day grade (`chain/read.py` `day_grade` takes the weakest grade over all the Site type's measures), and so the Portfolio, the claims and every SR-5 parity. That is ruled out.

### 10b.1 SR-10 and SR-11 shared core: two local-day period kinds (SR-10a, 0.35)

- **Storage.** Use the existing `site_period_read` (AR-1, migration 0059). No migration. Two new kinds, grain `local_day`:
  - `mini_depth.fuel_day`
  - `mini_depth.backup_day`
  - Each stores **every Site-local hour** of the day. The existing `mini_depth.fuel`/`.backup` kinds keep only the noon hour and stay unchanged, because the board reads them.
- **Event register** (`config/chain/event-register-v1.yaml`, `kinds:`). Add two lines with the inputs of `mini_depth.fuel` and `mini_depth.backup` (`roles: *mini_roles`, `mini_depth: [fuel]`/`[backup]`, `job_domains: [mini_fuel]`/`[mini_backup]`, `foundation: true`). The same `snapshot_dirty` queue then rebuilds them in the tick.
- **Builder.**
  - `mini_depth/read.py` `build_period(..., whole_day: bool = False)`. When `whole_day` is set and the domain is `fuel` or `backup`, the windows are every Site-local hour of `local_day`, by `mini_depth/worker.py:135` `hours_within(local midnight, next local midnight, tz)`. A nonexistent local hour is skipped, as today. Each hour goes through the existing `self._hour(...)` (head, live jobs, `_cutoff_sha`, pending IDs), so nothing is recomputed differently.
  - `mini_depth/period_rows.py`: `DAY_KINDS = {"mini_depth.fuel_day": "fuel", "mini_depth.backup_day": "backup"}`. Add a class `MiniDepthDayKindBuilder(domain, mini)` with the same body as `MiniDepthKindBuilder.fragments`, calling `build_period(..., whole_day=True)`. `kind_builders` returns these two as well, and `KINDS` lists them.
  - `BUILDER_VERSION` is **not** bumped, so no existing row goes stale. `chain/composition.py:77` `period_kind_builders` picks them up through `kind_builders`; the builder confirms this, without adding a second registration.
- **Reducers (pure), new `mini_depth/day_summary.py`.** Both read the stored hour facts (`period_rows.hour_from_json`) and the head `result` (`mini_depth/projection.py` `_fuel` / `_backup` shapes):
  - `fuel_day_summary(local_day, hours) -> {"local_day", "hours_expected", "hours_assessed", "hours_pending", "hours_missing", "status_counts": {"SUPPORTED", "LIMITED", "UNKNOWN"}, "expected_use_l": {"low", "high"} | null, "hours_with_use", "limitations": [code]}`.
    - `expected_use_l` is the sum of `cards.expected_use_l` bounds over the hours that have one; null when none do.
    - Residual, opening, closing and deliveries are never summed: W4-02 never has them.
  - `backup_day_summary(local_day, hours) -> {..., "status_counts", "sequences": [{"chain_id", "outage_start", "result", "service_outcome", "critical_recovery"}], "sequence_counts": {"PASS", "FAIL", "INCOMPLETE"}, "start_success_count": int | null, "slowest_recovery": {"seconds", "target_seconds"} | null, "limitations"}`.
    - `sequences` is deduplicated by `chain_id`; the latest hour wins.
    - `start_success_count` is the sum of the non-null hour values, and null if all of them are null.
    - **No outage count, ever.** Rows are worded "backup start sequences", never "outages" (`projection.py` q3 ruling 8).
- **Day state** (both kinds), first match wins:
  1. `NOT_EXPECTED`: the chain day grade is NOT_EXPECTED (`ChainRequest.day` → `chain/read.py` `day_grade`).
  2. `STILL_PROCESSING`: the row is absent, or `hours_pending > 0`.
  3. `NO_ASSESSMENT`: `hours_assessed == 0`.
  4. Fuel: `ASSESSED`. Backup: `SEQUENCE_FAILED` if any FAIL, else `SEQUENCE_INCOMPLETE` if any INCOMPLETE, else `SEQUENCES_PASSED` if there are any sequences, else `NO_SEQUENCE` ("No backup start recorded").
  - Plus `partial: bool` = `hours_missing > 0` or any LIMITED hour (the D-E5.45 PARTIAL label).
- **No compose fallback.** An absent row reads STILL_PROCESSING ("Still being prepared"), never "nothing known" (D-SR.16). Composing 24 hours × 31 days on read would break the 2 s gate. The backfill and the tick keep the rows built, and parity gates 0 absent rows.
- **Backfill on the demo DB.**
  - After the VPS scratch prepare, for KOBO-001 and KISIWA-001 over the data window (D-SR.29), run `python -m assetops_backend.chain.period_backfill build --site <code> --kind mini_depth.fuel_day --kind mini_depth.backup_day --from <first day> --to <last day + 1>`.
  - Add the same two kinds wherever the demo prepare already builds the AR-2 kinds (nothing to add if it builds every declared kind).
  - **Pre-flight gate.** On the scratch DB, count the selected heads per domain per local day. If `fuel` or `backup` heads are missing for hours that have `service` heads, stop and ask the Architect. Do not run `mini_depth.worker reconcile` without a ruling.

### 10b.2 SR-10: Fuel over the range (Kobo; 0.9 with the core)

- **Route (SR-10b, 0.2).**
  - `GET /api/sites/{site_code}/fuel-range?from&to[&known_at]`, schema `site-fuel-range-1`.
  - It goes in the late `mini_depth_api.py` range builder with SR-7a/SR-8 (D-SR.23). Admission, window (≤31 days, 422 `INVALID_WINDOW`), Cold/EV 404 `FUEL_RANGE_NOT_APPLICABLE`, 503 `SITE_FUEL_RANGE_UNAVAILABLE`, and `StoredRoute("fuel-range", tenant, {site, from, to, known_at}, sites=(site,), watermark_sites=(site,))`, all as SR-6.
  - Read: the period reader the AR-2 board read uses (`chain/period_read.py`), kind `mini_depth.fuel_day`, over `local_days(from, to, tz)` at `known_at`, plus one `ChainRequest.day` for the grades.
  - Body: `{schema_version, site, window, days: [<fuel_day_summary> + state + partial + "hour_link": "/sites/{code}/performance/fuel?from=<local noon>&to=<+1 h>"], totals: {expected_use_l, days_counted, days_requested, partial}}`.
  - `days_counted` counts the ASSESSED days. Totals sum the counted days only.
- **Page (SR-10c, 0.25).** In `MiniPerformance.tsx` `MiniFuel`: when the Site is **not** in nights mode, a range without `hour` renders new `sites/MiniFuelRange.tsx`, using client `getFuelRange` in `sites/miniDepthClient.ts`. It has:
  1. a status line ("Fuel use modelled on 6 of 7 days · 4 Nov: no assessment");
  2. a per-day bar chart of expected use (low–high) with the existing `ValueBars`;
  3. a day table: date, "Expected use (modelled) x–y L", "n of 24 hours assessed", state words, and "Open the 12:00 hour";
  4. "Residual: not available" (the hourly page's words).
  - An hour link keeps the existing hour page, with "Back to the whole range". SR-4b's noon default is removed from the range view, and the bar declares nothing.
  - **MOCK DEVIATION R727**: v69 `fuel` (8.22) is one reconciliation window. The range form keeps its "Residual, uncertainty and expected-consumption basis stay explicit" rule.

### 10b.3 SR-11: Backup over the range (Kobo and Kisiwa; 0.6)

- **Route (0.25).** `GET /api/sites/{site_code}/backup-range`, schema `site-backup-range-1`. Everything is as SR-10b, with kind `mini_depth.backup_day`, error codes `BACKUP_RANGE_NOT_APPLICABLE` / `SITE_BACKUP_RANGE_UNAVAILABLE`, and `hour_link` to `performance/backup`. Totals are `{sequence_counts, start_success_count, days_counted, days_requested, partial}`.
- **Page (0.3).** `MiniBackup`: a range without `hour` renders new `sites/MiniBackupRange.tsx` (client `getBackupRange`). It has:
  - a status line;
  - a day table: date, "n backup starts: p passed, f failed, i incomplete", "slowest recovery m min (target t)", state words, and "Open the 12:00 hour";
  - "Sequences in this range": the existing backup chain table component fed with the days' `sequences`.
  - **MOCK DEVIATION R728**: v69 `backup` (8.24).
- **Tests for SR-10/11.**
  - `backend/tests/test_sr10_day_summary.py` (pure): bound sums, missing/pending hours, the union of limitations, de-duplication by chain_id, the null rule for start successes, and no `outage` key.
  - `test_sr10_fuel_range_route.py` and `test_sr11_backup_range_route.py` (stubs): 422, 404, 401/403, 503, the stored key and watermark Site, the perf line.
  - `test_sr10_day_kinds_postgres.py` (`*_test`):
    - a built day row's hours equal live `_hour` reads of every hour;
    - an absent row reads STILL_PROCESSING;
    - a new accepted reading dirties and rebuilds the row;
    - for 3 sampled hours, the row equals the one-hour route's card (the drill-in link).
  - `python -m assetops_backend.chain.graph check` passes. `test_ch1b_register` is updated if it lists kinds.
  - Vitest `sites/__tests__/miniFuelRange.test.tsx` and `miniBackupRange.test.tsx`, the `sr2RequestUrls` pins, and the `RANGE_MATRIX` Fuel/Backup entries D→R.
- **Parity and timing.** On the scratch audit copy, one heavy job each: KOBO-001 and KISIWA-001 × 7/14/31 days (D-SR.29 windows).
  - 0 absent rows after the backfill.
  - For 3 days × 24 hours per Site, the stored hour facts equal a live `_hour` read.
  - The stored response is ≤ 2.0 s.
  - Output `.agent/SR-10-parity.json` and `.agent/SR-11-parity.json`; the gate is 0 mismatches.

### 10b.4 Sweep: every tab and subtab of every Site type ("without exception")

| Tab / subtab | Kobo | Kisiwa (diesel) | Cold | EV | Disposition |
|---|---|---|---|---|---|
| Overview, Dispatch, nights day table, Financials range money | SR-5 | SR-5 | R | R | as rev 9 |
| Health | SR-6 | SR-6 | R | R | as 10.2. The "Contact now" panel stays below the range page, labelled point-in-time |
| Performance: Service, Renewable | SR-7a, SR-8 | SR-7a, SR-8 | n/a | n/a | as 10.3/10.4 |
| Performance: **Fuel** | **SR-10** | **SR-10k** (the Fuel tab is the fuel-check nights list, `/fuel-balance/nights`, no from/to today) | n/a | n/a | new |
| Performance: **Backup** | **SR-11** | **SR-11** | R (temperature, backup, cooling read the window) | n/a | new |
| Performance: Cold/EV subtabs | n/a | n/a | R | R (sessions, availability, energy) | OK |
| Evidence ledger | R | R | R | R | OK |
| Evidence claim limit | SR-7b | SR-7b | n/a | n/a | as 10.3 |
| Evidence **rejections** ("All dates" line, SR-4c) | **SR-12a** | **SR-12a** | **SR-12a** | **SR-12a** | new (`evidence_api.py:161`, no from/to today) |
| Evidence **analytics readiness** ("All dates" line) | **SR-12b** | **SR-12b** | **SR-12b** | **SR-12b** | new (`analytics_api.py:105` scores readiness on all active assessments) |
| Findings, Work (incidents, maintenance), Scenarios | R | R | R | R | OK. The SR-5e matrix test proves it, otherwise SR-9 |
| **Foundation changes list** | **SR-13** | **SR-13** | **SR-13** | **SR-13** | was N. It is dated records, so it is a data list |
| **Prices / EV financial assumptions** (history) | **SR-14** | **SR-14** | **SR-14** | **SR-14** | was N. A price history is dated, so it shows "Prices that applied in this range" |
| Foundation, its views, SLD | N | N | N | N | **not a period**: the configuration in force (dated changes are in SR-13) |
| Battery and asset pages | N | N | pending SR-4 list | pending SR-4 list | **not a period**: Foundation configuration, and condition is never invented (D-SR.14). Any asset page with readings becomes SR-9 |
| Sites index | N | N | N | N | **not a period**: a directory |
| Finding, Action, Opportunity, verification, fuel-finding, Foundation-change and maintenance-request detail | N | N | N | N | **not a period**: one record, and its links carry the range |

After SR-4 to SR-14 (and SR-9 if any), no data tab is left with a label instead of range output. The N rows are configuration, a directory or one record. The owner confirms that list on Saturday.

**New cards (designs; builders do not design).**
- **SR-10k Kisiwa fuel checks over the range (0.25).**
  - `fuel_balance_api.py:98` `/fuel-balance/nights` takes optional `from`/`to` (both or neither, else 422 `INVALID_WINDOW`). It filters the nights whose Site-local `night_date` lies in the Site-local days of `[from, to)`. With no params, behaviour is unchanged.
  - Page: `useFuelNights(client, siteCode, range)` sends the range. The empty state reads "No fuel checks in this date range". The night detail stays the drill-in.
  - Tests: a route stub, a Postgres filter test, vitest, and a pin.
- **SR-12a Evidence rejections over the range (0.3).**
  - `SITE_EVIDENCE_REJECTIONS_ROUTE` takes optional `from`/`to` (both or neither). `PostgresEvidenceLedger.rejections` (`evidence/adapters/postgres_evidence_ledger.py:955`) and the imported-reads path filter every list in the body on the batch `received_at` in `[from, to)`, and the recompute-job list on `created_at`.
  - `SiteEvidenceFrame` passes the range, and SR-4c's "All dates" line is removed from that panel.
  - Pre-flight: list each list in the body with its time column. A list with no time goes to the Architect.
- **SR-12b Analytics readiness over the range (0.25).**
  - `SITE_ANALYTICS_ROUTE` takes optional `from`/`to`. The declaration (which analytics apply) is unchanged. Readiness counts only the active assessments whose window intersects `[from, to)`.
  - The "All dates" line is removed. Pre-flight: the window fields on `service.dispatch(...)` assessments.
- **SR-13 Foundation changes over the range (0.2).**
  - The changes list shows the changes recorded in `[from, to)`, plus a line "n changes before this range" with a link to open them (the range from the first change to `from`).
  - The Foundation page itself stays configuration now. The filter is done on the frontend if the list endpoint returns the whole history in one response; otherwise the endpoint takes `from`/`to`. That is a pre-flight question, not a builder choice.
- **SR-14 Prices that applied in the range (0.3).**
  - The Site Prices page (`price_page_api.py:48`, PR-2a history) and the EV financial assumptions show the revisions whose validity meets `[from, to)`, headed "Prices that applied in this range", and keep a "Valid now" row.
  - SR-5d's "Prices valid now" section uses the same component under the range heading.
  - The filter is on the frontend over the existing history. Pre-flight: whether the history is complete in one response.
  - **MOCK DEVIATION R729** (v69 `site-financials` assumptions show current values).

### 10b.5 Sizes, lanes, order (D-SR.37), and the Saturday reassessment (D-SR.38)

- **New range units:** SR-10 0.9, SR-11 0.6, SR-10k 0.25, SR-12a 0.3, SR-12b 0.25, SR-13 0.2, SR-14 0.3, which is **2.8**. The package grows from 15.8 to **about 18.6 units**.
- **Capacity, for information:** the window was 11-13 units. Rev 10 expected about 15.65 to fit by the freeze with the VPS lanes, with UP-1 and MB-1 already at risk. 18.6 is about 3-5 units beyond that on present throughput, so the **Sat 14 Nov 20:00 freeze is at risk for the tail of the list**. Tue 17 Nov is at risk only if every item must merge before the freeze. Nothing is dropped now (owner).
- **Lanes (5 on the VPS; each takes its next item when it frees; range items first):**

| Lane | Now | Then, in order |
|---|---|---|
| G | SR-4 | SR-12a → SR-12b → SR-13 |
| H | SR-5 (`range_days.py`, Postgres, core b/e) | SR-5c → SR-5d → SR-14 (shares the price component with SR-5d) |
| I | SR-6 | SR-10k |
| J | SR-7 | SR-11 (starts on SR-10a's core commit from lane K) |
| K | SR-8 | SR-10 (core first, committed and server-reviewed before the routes) |

- AR-4 and WARM-1 keep their rev 10.6 place above SR-4: if either is unmerged, the first lane that frees takes it before any new SR card. After a lane's range list, the non-range package follows in priority order: UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > UQ-FI-3 > FR-B > DATA-10/13.
- **Merge order:** SR-4, SR-5 core, SR-6, SR-7, SR-8, SR-5c, SR-5d, SR-10, SR-11, SR-10k, SR-12a, SR-12b, SR-13, SR-14, then the non-range items by priority. Shared files (`sr2RequestUrls.test.tsx`, `ui/rangeMatrix.ts`, `mini_depth_api.py`'s late builder, the event register): the second merger resolves.
- **Heavy DB jobs** run one at a time, in this queue: SR-5, SR-6, SR-7, SR-8, SR-10, SR-11 parity. 24 GB is enough for 5 builders plus one heavy job. Short `*_test` runs are queued by the coordinator.
- **Saturday reassessment (D-SR.38): Sat 14 Nov 12:00, Architect, then to the owner.** Inputs:
  1. the units merged, and the ACCEPTed-but-unmerged branches, against this list;
  2. open High/Medium review findings;
  3. the parity and timing gates (`SR-5/6/7/8/10/11-parity.json`: 0 mismatches, stored ≤ 2.0 s);
  4. the D-17N.4 rehearsal finish check;
  5. the units left per lane against the hours to 20:00.
- **Candidates to put to the owner then, in the order I would defer them** (the owner decides; nothing moves before): DATA-10/13, FR-B, UQ-FI-3, DATA-5/4/8, MB-1, UP-1, then the range tail SR-14, SR-13, SR-12b. Each one is either "after the freeze" or "before 17 Nov with the freeze moved to Sun 15 Nov 20:00". The owner also confirms the N list in 10b.4.

## Revision 10a (Architect, Claude, 2026-11-12 evening): SR-5 and SR-6/7/8 pre-flight rulings

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Rulings **D-SR.19-30** (`build-sheet-OWN-GAPS-2026-11-08.md`), owner-delegated, logged for owner review. Inputs: `task/SR-6-health-range` 4db92b874 `.agent/SR-678-preflight.md` (Q1-Q9); `task/SR-5-range-board` 7ae69039b `.agent/SR-5-packet.md` (safe readings, (d), (f)) and the coordinator's two added questions (demo window, route classes). No new scope: every ruling below uses existing tables, functions and rows.
- **Corrections to rev 10 text.** 10.1: `daylight_headroom_kw` covers the declared **operating** hours (`chain/measures.py:49-50`), not "measured daylight hours". 10.2 step 3: the cutoff is the disposition time, not `received_at` (D-SR.19). 9.4 step 5: an unmatched selected day is STILL_PROCESSING, not NOT_ANALYSED (D-SR.28).

### 10a.1 SR-6 (lane I)

| Q | Ruling |
|---|---|
| Q1 | Use the accepted-reading convention of the dispatch read (`analytics/adapters/postgres_assessment_store.py:118-127`): `JOIN ingestion_disposition d ON d.batch_id = e.batch_id AND d.ordinal = e.ordinal`, `d.decision = 'ACCEPTED' AND d.accepted_evidence_id = e.id AND d.decided_at <= :k`, plus `e.tenant_id = :t`. Day bucket and window on `COALESCE(e.interval_start, e.source_time)` (`>= :from`, `< :to`), so each reading counts once on the day its interval starts. `last_received_at` stays `max(e.received_at)` (a receipt fact). Diagnostics keep `received_at <= :k` (no disposition exists for them). D-SR.19. |
| Q2 | No demo data work. Gateway-day `contact` gains one state, **READINGS_ONLY** ("Readings received; no status reports"), derived from step 3: a gateway's day readings = the sum of its sources' counts (`RegisteredSource.gateway_id`). Precedence: diagnostics > 0 → the cadence rule (IN/PARTIAL); else readings > 0 → READINGS_ONLY; else day before the gateway's `registered_at` day → NOT_EXPECTED; else NO_CONTACT. So a demo Site with readings never reads "No contact" or "Before it was registered" on a day its readings arrived. The SR-6 parity job reports `gateway_diagnostic` row counts per mini-grid Site and the contact-state histogram. D-SR.20. |
| Q3 | Drop both dead branches: no `gateways: []` file-import text, no null-cadence rule; `cadence_seconds` is an int. An empty gateway list renders the table's ordinary empty row. D-SR.21. |
| Q4 | Health `days[].state` is the SR-5a precedence with step 6 collapsed to **ANALYSED** ("Analysed"); Health shows no finding counts. To keep one rule, lane H extracts the precedence and the coverage-wins step from `site_range.py` into a new public module `estate/range_days.py`, `range_day_states(snap, tenant_id, site, req, scope, cov) -> dict[date, dict]` (state, row), returning ANALYSED for step 6; `site_range.py` maps ANALYSED to FINDINGS/CLEAR by its count. SR-6a calls `select_finding_scope` once only to obtain `cov` (`f_sites[0][2]`) and then `range_day_states`. Pin: Health ANALYSED days ⇔ SR-5a FINDINGS/CLEAR days, other states equal, on the same fixture. If SR-5 core is held, `range_days.py` and its unit test merge with SR-6 (the file has no route). D-SR.22. |
| Q5 | Confirmed shape. Inside `EstatePortfolioService.read_snapshot(work)`: registration by calling `PostgresGatewayAccess._health_registration(snap._c, t, s)` (called, not copied; private-on-snapshot precedent `estate/period_rows.py:224`); steps 2-3 SQL in a new adapter `sites/adapters/postgres_health_range.py`, one function taking the `Connection`; day states per Q4. Source-day NOT_EXPECTED comes from the day's `days[].state == NOT_EXPECTED` (the chain grade, built from `readings_began`), so no separate `readings_began` call. Wiring: a new builder `build_health_range_router(...)` in `source_health_api.py`, included in `main.py` after `responses` and `estate_portfolio` exist (after line ~618); the existing source-health router stays where it is. The same rule covers SR-7/SR-8 routers (new builders, included late). D-SR.23. |

### 10a.2 SR-7 (lane J)

| Q | Ruling |
|---|---|
| Q6 | Confirmed: no `claim_days`, no edit to `estate/period_rows.py`. SR-7b runs inside `read_snapshot` with the `estate/evidence_money.py:252-268` pattern (`dispatch_days` → `note_page_days` → `day_revision` → `snap.claim_limit_on` → `w1.reduce_day`). If the builder finds `read_snapshot` does not yield an `EvidenceMoneySnapshot`, stop and ask; do not add a reader. D-SR.24. |
| Q7 | Day row = `w1.reduce_day(projection)`: `{day, revision_id (day_revision), available, state, current_ceiling, ceiling_statement, window_assessment_revision_id, gap_count, reasons[]}`; no invented day ceiling (`current_ceiling` is null unless `reduce_day` gives one). `revision_id` null → state `NO_SELECTION`, no link. Link: the existing address, `/sites/{code}/evidence?day={day}&revision={revision_id}`. The range day table lives in the claim-limit section of Site Evidence (`EvidenceClaimLimit.tsx`): no `day` → table; `day&revision` → the existing one-day section plus "Back to the whole range". Test: each row equals `reduce_day` of the one-day route's projection for the same `day&revision`. Summary: `days_with_positive_claim` (`current_ceiling` not null), `days_indeterminate` (UNKNOWN or CONTRADICTORY), `days_without_selection`. D-SR.25. |
| Q8 | `covered_hours` / `operating_hours` = the snapshot row's `covered_seconds` / `required_seconds` ÷ 3600 (stored row, D-SR.15 holds). Drop `NO_CRITICAL_LOAD` (no chain change). A day whose grade is analysed but whose `critical_served` value is absent reads **NO_VALUE** ("No critical-load figure for this day"); gap states come from the grade as before. The parity job reports, per Site, the days with a value; a demo Site with none across its window is reported to the Architect before merge. D-SR.26. |

### 10a.3 SR-8 (lane K)

| Q | Ruling |
|---|---|
| Q9 | Per day: `{local_day, grade, low_kw, high_kw, decision, window_hours, covered_hours, operating_hours, state, link}`; the page shows the band "low–high kW". States: COUNTED (ELIGIBLE), EXCLUDED (bounds shown, labelled "excluded"), CONFLICT, LIMITED, MISSING_HOUR ("Partial: an hour is missing"; this is the rev 10 PARTIAL day), plus grade gap states. `measured_hours`/`missing_hours` are dropped; `window_hours` is "eligible hours", covered/operating hours from the row's seconds over **operating** hours. Totals: `days_counted` = ELIGIBLE days with both bounds; "average daylight headroom" = mean of `low_kw` and mean of `high_kw` separately over those days; PARTIAL label when `days_counted < days_requested`. D-SR.27. |

### 10a.4 SR-5 (lane H)

| Item | Ruling |
|---|---|
| `select_evidence_scope` in the snapshot | Confirmed (status equality with the Portfolio needs E). |
| `actions.open` | Confirmed reading, but import `site_outcomes/mini.py:125 CLOSED_LABELS` (B-Q18) instead of the local `_CLOSED_LABELS`. Null unless Action coverage is complete; `awaiting_verification` = `pending_trial_count`. |
| `findings.count` | **Corrected.** Follow the Portfolio's `finding_known` rule for this Site (`estate/portfolio.py:870-872,886`): numeric when F coverage is COMPLETE/EMPTY, or the status is PARTIAL (checked days); else null, with `confirmed` and `not_confirmed`. `awaiting_verification` by FC-2: confirmed. |
| (c) Site-local grade → UTC day | Confirmed: same date, the coverage's D-E5.42 rule. |
| Unmatched selected day | Confirmed STILL_PROCESSING (9.4 step 5 text corrected). |
| Coverage-wins with no coverage gap | Confirmed: FINDINGS/CLEAR (ANALYSED in `range_days.py`), logged. The parity JSON counts `site_range_day_mismatch` lines; a non-zero count goes to the Architect before merge. |
| Route tests in one file | Accepted, recorded as a spec deviation. |
| New work | Extract `estate/range_days.py` (D-SR.22) as the next commit, before the Postgres steps; SR-6 merges that commit. |
| (6) Demo Sites and window | KOBO-001 and KISIWA-001, confirmed. After the VPS scratch prepare (`tools/demo_combined.py`), each Site's window ends at the last **complete** UTC day with accepted readings (decided ≤ now); ranges 7, 14 and 31 days ending there (31 may start before readings began: that exercises NOT_EXPECTED). Chosen windows are written into each `SR-*-parity.json`. D-SR.29. |

### 10a.5 Route classes (D-SR.17 → D-SR.30)

- **N (one record, links carry the range):** `opportunities/:id`, `actions/:id(/:view)`, `domain-actions/:id/verification`, `domain-actions/:id/fuel-verification`, `fuel-findings/:id`, `foundation/changes/:id`, `/maintenance/requests/:id(/record|/history)`.
- **Covered by the Work row (OK as rev 9):** `work/incidents`, `work/maintenance`. The SR-5e matrix test proves it; if either request lacks `from`/`to`, it becomes an SR-9 card (≤0.25).
- **Performance subtabs:** Cold and EV subtabs read the window already (R). Mini-grid **Fuel** and **Backup** are one-hour depth pages (`serviceWindowFromParams`) with no range form: class D with SR-4c's honest tag for now. **Owner item:** under D-SR.9 they are the last mini-grid range gaps; Backup has no stored per-day measure, so a range form needs new chain work (not scoped); Fuel could read the chain day measure `avoidable_gen_min` like SR-8 (estimate 0.5, not added; owner decides).
- **Cold/EV asset pages:** pending the SR-4 builder's route list (not landed on `task/SR-4-site-range` e7c103b4a). Rule unchanged: any asset page showing readings without `from`/`to` is an SR-9 card.

### 10a.6 Sizes and start

- SR-5a +0.05 (extraction) → SR-5 all 2.1. SR-6 +0.1 (finding scope call, READINGS_ONLY, adapter; dead branches −0.05) → **1.1**. SR-7 0.75 unchanged (7b reader smaller, page inside Site Evidence). SR-8 0.5 unchanged. Package about **15.8 units**; drop order D-SR.18 unchanged.
- **Start now:** SR-7 and SR-8 builders, server first. SR-6a starts now on steps 1-3, the adapter and the route; its day states wait for lane H's `range_days.py` commit (expected first on lane H's resume list). Pages still wait for SR-4.

## Revision 10 (Architect, Claude, 2026-11-12 ~14:30): SR-6, SR-7, SR-8 IN now; every range disparity fixed; lanes for today

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Rulings **D-SR.13-18** (`build-sheet-OWN-GAPS-2026-11-08.md`), owner-directed, logged for owner review.
- Owner, verbatim (`.agent/owner-everything-fixed-now-demo-off-2026-11-12.md`): "Everything must be fixed now, demo today is called off because of this".
- **What this revision changes.** Rev 9's 9.3 "GAP" rows and its "Known gaps for 17 Nov" list are superseded: SR-6, SR-7 and SR-8 are **IN, starting now**. The rule stays D-SR.9. Written under a 10-minute cut (work moving to the VPS). Sections marked **TO FINISH ON VPS** are closed by the builder's pre-flight answer to the Architect, never by the builder designing.

### 10.1 Stored data every SR-6/7/8 read reuses (code on main, cited)

- **Chain day snapshots** (`chain/read.py` `ChainRequest.day(site_id, "MINIGRID", days)`): one memoised read (`chain.day`) per Site and day range, returning per Site-local day the grade and stored value of each mini-grid measure: `productive_kwh`, `daylight_headroom_kw` (all measured daylight hours of the day, CH-9 R5), `critical_served` (all declared operating hours of the day, from the stored hourly `mini_service` heads, CH-9 R9), `avoidable_gen_min`. This is the range source. No hour is recomputed on read.
- **`mini_depth.*` rows (AR-2, `mini_depth/period_rows.py`)**: renewable is one row per local day; fuel, service and backup hold the local-noon hour only. They stay the **drill-in** source (one hour, or up to 5 days), unchanged.
- **`dispatch.day` rows (AR-3)** through `estate/coverage.dispatch_days` (D-ANY.10 absent-run compose), plus `local_day_grades_kw` and `data_gap_days` (D-E5.46): the per-day state and gap words, exactly as SR-5a uses them.
- **`evidence.claim` rows (AR-4, `estate/period_rows.py`)**: the claim limit per UTC day.
- **Gateway contact and readings**: `gateway_diagnostic` (index `gateway_diagnostic_gateway_received (gateway_id, received_at DESC)`) and `accepted_evidence` (index `accepted_evidence_site_time (site_id, source_time DESC)`).
- **BL-ANY-absent comes back IN, as a test (D-SR.16):** every new range read is tested with an absent historical-k row inside the range. It must read through D-ANY.10's compose (dispatch) or the chain read's own NO_DATA/PENDING grade (chain), never as "nothing known". New fallback code is added only if that test fails (then 0.25, in the failing read's branch).

### 10.2 SR-6: mini-grid Health over the range (1.0)

**SR-6a server (0.6, Postgres).** New module `backend/assetops_backend/sites/site_health_range.py`. New route in the router file that serves `/api/sites/{site}/source-health`: `GET /api/sites/{site_code}/health-range?from&to[&known_at]`, schema `site-health-range-1`.
- Admission as `source-health`. Window by `estate.scope.estate_request("portfolio", ...)` (midnight UTC, at most 31 days; else 422 `INVALID_WINDOW`). Cold/EV: 404 `HEALTH_RANGE_NOT_APPLICABLE` (their Health already reads the range). Store failure: 503 `SITE_HEALTH_RANGE_UNAVAILABLE`. Stored response: `ResponseStore.serve(StoredRoute("health-range", tenant, key={site, from, to, known_at}, sites=(site,), watermark_sites=(site,)), compose)`.
- One REPEATABLE READ, READ ONLY transaction. Reads, in order:
  1. registration: `_health_registration` (gateways, sources; called, not copied);
  2. per gateway per UTC day: `SELECT gateway_id, date_trunc('day', received_at AT TIME ZONE 'UTC') AS d, count(*), min(received_at), max(received_at) FROM gateway_diagnostic WHERE tenant_id=:t AND site_id=:s AND received_at >= :from AND received_at < :to AND received_at <= :k GROUP BY 1, 2`;
  3. per source per UTC day: `SELECT <source column>, date_trunc('day', source_time AT TIME ZONE 'UTC') AS d, count(*), max(received_at) FROM accepted_evidence WHERE site_id=:s AND source_time >= :from AND source_time < :to AND received_at <= :k GROUP BY 1, 2`. **TO FINISH ON VPS:** pre-flight (a) names the source and receipt columns; no join to reading bodies;
  4. day states: `dispatch_days` + `local_day_grades_kw` + `data_gap_days`, called as SR-5a steps 5-6.
- Body:
```
{ "schema_version": "site-health-range-1",
  "site": {"site_code", "site_name", "timezone"}, "window": {"from", "to", "known_at", "basis"},
  "gateways": [ {"gateway_external_id", "mode", "disabled", "cadence_seconds",
                 "days": [ {"day", "diagnostics": int, "first_received_at", "last_received_at",
                            "contact": "IN_CONTACT" | "PARTIAL_CONTACT" | "NO_CONTACT" | "NOT_EXPECTED"} ] } ],
  "sources": [ {"source_external_id", "disabled",
                "days": [ {"day", "accepted_readings": int, "last_received_at",
                           "state": "READINGS" | "NO_READINGS" | "NOT_EXPECTED"} ] } ],
  "days": [ {"day", "state": <the SR-5a day state set>, "accepted_readings": int | null} ],
  "summary": {"days_requested", "days_with_readings", "days_without_readings", "gateways_in_contact_all_days"},
  "battery": <the existing battery entry body, unchanged>,
  "links": {"day": "/sites/{code}/health?day={day}"} }
```
- Rules:
  - Gateway-day `contact`: NOT_EXPECTED before the gateway's `registered_at` day; NO_CONTACT at 0 diagnostics; IN_CONTACT when `diagnostics x cadence_seconds >= 0.9 x` the seconds of the day inside `[from, min(to, k))`; else PARTIAL_CONTACT. With no cadence: IN_CONTACT when at least one, and the limitation text says the cadence is not configured.
  - Source-day: NOT_EXPECTED before the Site's readings began (`ChainRequest.readings_began`); READINGS when the count is above 0; else NO_READINGS.
  - `days[]` and `summary` use the SR-5a day rules, so Health and the range Overview agree day by day (test pin).
  - A Site with no gateway (file import): `gateways: []`, and the page says "This site's readings arrive by file import, so there is no gateway contact to report."
- **Battery (D-SR.14):** the battery entry is Foundation configuration, and its condition is always Unknown (no read supplies condition inputs; `sites/battery_boundary.py`). It is point-in-time by nature. The section is headed "Battery (current settings)". No battery figure over the range is invented.

**SR-6b page (0.4).** In `sites/SiteHealth.tsx`, MINIGRID branch: with a range and no `day`, render new `sites/SiteHealthRange.tsx` (client `sites/healthRangeClient.ts`, refusals mapped like `outcomeBoardClient.ts`):
1. status line, for example "Readings on 6 of 7 days · 4 Nov: no readings" (D-E5.46 words);
2. gateway table: one row per gateway, one cell per day (`aria-label` "Gateway G1, 4 Nov: no contact"), words In contact / Partial contact / No contact / Before it was registered;
3. source table, same shape, with reading counts;
4. "Battery (current settings)": the existing `ConditionStrip`/`ConditionBody`, unchanged.
- With `day=`: the drill-in is the same range page for that one day (request `from=day&to=day+1`, `day` kept in the address), with "Back to the whole range". The existing `source-health` panel stays below, headed "Contact now" and labelled point-in-time.
- Bar: the range view declares nothing ("All pages"); the drill-in declares `span(day, day)`. SR-4c's `now` declaration on mini-grid Health is removed.
- MOCK DEVIATION R724 (v69 `health:1/2` is current contact only). The builder adds the register row.

**SR-6 tests.**
- `backend/tests/test_sr6_health_range_route.py` (stubs): 422, 404, 401/403, stored-response key and watermark Site, perf line.
- `backend/tests/test_sr6_health_range_postgres.py` (`assetops_test`): a gateway with full, partial and no-contact days; a pre-registration day; sources with and without readings; a reading received after `known_at` excluded; `days[]` equal to SR-5a's days on the same fixture; the absent-row test (10.1).
- Vitest `sites/__tests__/siteHealthRange.test.tsx`; `sr2RequestUrls` pin (mini-grid Health with a range requests `health-range?from&to`); the SR-5e `RANGE_MATRIX` entry for mini-grid Health changes N to R (the range-ignore test then covers it).
- Parity and timing, on the `<prefix>_audit` copy, one heavy job: KOBO-001 and KISIWA-001 x (7, 14, 31 days). Per-day `accepted_readings` for dispatch-role sources against the `dispatch.day` `accepted_reading_count` (reported; any difference is explained by role, not gated). Gate: stored response at most 2.0 s; cold recorded. Output `.agent/SR-6-parity.json`.

### 10.3 SR-7: Service and the claim limit over the range (0.75)

**SR-7a Service range (0.4).** Route `GET /api/sites/{site_code}/service-range?from&to[&known_at]`, schema `site-service-range-1`, in `mini_depth_api.py` beside the depth router. Admission, window, 404/503 and StoredRoute as SR-6. Read: `ChainRequest.day(site_id, "MINIGRID", local_days(from, to, tz))` (`chain/read.py`), measure `critical_served` only; ChainRequest built with the `chain_api.py` `opened(ref)` pattern.
```
{ "schema_version": "site-service-range-1", "site": {...}, "window": {...},
  "days": [ {"local_day", "grade", "served_kwh", "unserved_kwh", "demand_kwh", "covered_hours", "operating_hours",
             "state": "SERVED_ALL" | "SHORTFALL" | "NO_CRITICAL_LOAD" | <the SR-5a gap states>,
             "hour_link": "/sites/{code}/performance/service?from=<local noon>&to=<+1 h>"} ],
  "totals": {"served_kwh", "unserved_kwh", "demand_kwh", "days_counted", "days_requested"} }
```
- Values are the stored `critical_served` snapshot value only (served, unserved, covered span, the `CriticalServed.inputs` shape). NO_CRITICAL_LOAD where the measure is declared absent (K10 v2 `none_declared`), words "No critical load declared". Totals sum counted days only; `days_counted < days_requested` gives the D-E5.45 PARTIAL label.
- No all-load or interruption figure is invented over the range (those cards exist per hour only). The page says "Delivered load and interruptions: open a day".
- Page (`MiniPerformance.tsx` Service tab): a range without `hour`/`day` shows the day table (served, unserved, state, "Open the 12:00 hour"). A one-hour story link keeps the existing page, with "Back to the whole range". SR-4b's 12:00-hour default is removed from the range view. MOCK DEVIATION R725.

**SR-7b claim limit range (0.35).** Route `GET /api/sites/{site_code}/claim-limit-range?from&to`, schema `site-claim-limit-range-1`, in the claim-limit router file.
- Read: for each UTC day of the range, the `evidence.claim` stored row (AR-4 reader). A row miss falls back to today's `claim_limit_on` compose for that day, counted by `row_misses` (the existing rule).
- Body: `days[{day, window_status, ceiling, current_positive_claim, reasons[], revision_id, link: "/sites/{code}/evidence/claim-limit?day={day}"}]` and `summary {days_with_positive_claim, days_indeterminate, days_without_selection}`.
- Page `EvidenceClaimLimit.tsx`: a range shows the day table; `day=` shows the existing one-day page with a back link.
- **TO FINISH ON VPS:** the pre-flight names the AR-4 reader for one Site's claim rows over a day list. If none exists without editing AR-4's files, one public function `claim_days(snap, t, s, days, k)` is added to `estate/period_rows.py`, and that is the only change there.

**SR-7 tests.** Route stubs; `test_sr7_service_range_postgres.py` (a shortfall day, a fully served day, a declared-none day, a gap day, a PENDING day, the absent-row test, totals; and for 3 sampled hours, the stored day value agrees with the hourly `mini_service` CRITICAL rows read through the one-hour route: the range-to-drill-in link); `test_sr7_claim_limit_range_postgres.py` (each day equals the one-day route's fields; rows on and off identical). Vitest for both pages; `sr2RequestUrls` pins; `RANGE_MATRIX` Service and claim-limit entries D to R. Parity and timing as SR-6, output `.agent/SR-7-parity.json`.

### 10.4 SR-8: Renewable over the whole range (0.5)

- `MAX_DAYS = 5` stays for the drill-in depth read (its envelope is per hour).
- New route `GET /api/sites/{site_code}/renewable-range?from&to`, schema `site-renewable-range-1`, in `mini_depth_api.py`. One `ChainRequest.day` read, measure `daylight_headroom_kw`. Per local day: `{local_day, grade, headroom_kw (stored value), measured_hours, missing_hours, state, link: "/sites/{code}/performance/renewable?from=<local midnight>&to=<+1 day>"}`. Totals: days counted, and the mean headroom over counted days, labelled "average daylight headroom"; the PARTIAL label when days are missing. Up to 31 days (estate window rule).
- Page (Renewable tab): a range of any length shows the day table and a per-day headroom bar chart (the chart component the Renewable tab already uses; no new library). A day opens the existing one-day depth page. A story window of at most 5 days keeps the existing page. SR-4b's "last 5 days" clamp and its span declaration are removed. MOCK DEVIATION R726.
- Tests: Postgres (each day's value equals the stored snapshot; a missing-hour day reads PARTIAL; the absent-row test; for 3 sampled days, the row equals the one-day depth envelope's headroom card). Vitest; pins; `RANGE_MATRIX` Renewable D to R. Parity and timing, output `.agent/SR-8-parity.json`.

### 10.5 Re-audit: every Site page x Site type (supersedes 9.3's GAP rows)

| Page | Kobo / Kisiwa | Cold | EV | Disposition |
|---|---|---|---|---|
| Overview, Dispatch, Kisiwa nights, Financials | SR-5 | OK | OK | as rev 9 |
| Health | **SR-6** | OK | OK | fixed |
| Service, claim limit | **SR-7** | n/a | n/a | fixed |
| Renewable | **SR-8** | n/a | n/a | fixed |
| Scenarios, Findings, Work, Evidence ledger | OK | OK | OK | as rev 9 |
| Evidence rejections and analytics panels | SR-4c | SR-4c | SR-4c | as rev 8 |
| EV `/ev/financials` same fingerprint | n/a | n/a | SR-4 pre-flight (f) | as rev 9 |
| Finding detail | N: one Finding's own episode | N | N | one record, not a period; links carry the range (SR-4a); its claim-limit panel is the Finding's own day, which is correct |
| Assets list, battery page | N (configuration) | **TO FINISH ON VPS** | **TO FINISH ON VPS** | the SR-4 pre-flight route list classifies each asset page; any asset page that shows readings without from/to becomes card **SR-9** (frontend, existing route params, at most 0.25 each) |
| Foundation, Foundation changes, `foundation/sld` | N | N | N | the configuration in force; the changes page is an edit history, not a measured period; the SLD is a drawing of configuration |
| Prices | N | N | N | a price is in force at an instant; range money already uses each day's price (SR-5d) |
| Sites index | N | N | N | a directory, not data |

- After SR-4 to SR-8 (and SR-9 if any), nothing is a labelled gap except the N rows, each point-in-time by nature for the reason given.
- The SR-4 pre-flight route list (8.5 step 1a) is the completeness check. Any route it lists that is not in this table goes to the Architect as a pre-flight question, never a builder choice (D-SR.17).

### 10.6 Lanes, order, capacity (D-SR.18)

| Lane | Work | Branch | Worktree | Depends on |
|---|---|---|---|---|
| G (running) | SR-4 | `task/SR-4-site-range` | AssetOpsV1-sr4 | none |
| H (running) | SR-5 server, core, then c, d | `task/SR-5-range-board` | AssetOpsV1-sr5 | SR-4 for b, c, d |
| **I** (now) | **SR-6** a then b | `task/SR-6-health-range` | AssetOpsV1-sr6 | 6a none (calls `estate/coverage` functions directly, not SR-5a's module); 6b on SR-4 (`RangeLink`, `rangeFocus`) |
| **J** (now) | **SR-7** a then b | `task/SR-7-service-claim-range` | AssetOpsV1-sr7 | servers none; pages on SR-4 |
| **K** (now if a 4th lane is free, else VPS) | **SR-8** | `task/SR-8-renewable-range` | AssetOpsV1-sr8 | server none; page on SR-4 |

- Heavy DB jobs one at a time, queue order: SR-5a parity, SR-6 parity, SR-7 parity, SR-8 parity. Short `*_test` Postgres runs are queued by the coordinator.
- Reviews: a fresh Claude reviewer per branch per round; Sonnet fix rounds. Each server unit may be reviewed before its page so pages build on ACCEPTed servers.
- Merge order: SR-4, SR-5 core, SR-6, SR-7, SR-8, SR-5c, SR-5d. `sr2RequestUrls.test.tsx` and `ui/rangeMatrix.ts` are shared: the second merger resolves. SR-5e's matrix lands with SR-5 core; SR-6/7/8 each flip their own entries.
- **Capacity:** 13.4 + SR-6 1.0 + SR-7 0.75 + SR-8 0.5 = **about 15.65 units**, over the 11-13 window. The owner's priority is range correctness, so SR-4 to SR-8 are protected and the drop order (first dropped first) is **DATA-10/13, FR-B, UQ-FI-3, DATA-5/4/8, MB-1, UP-1**. With the VPS lanes tonight, the range set plus AR-4, WARM-1 and UQ-FI-1/2 is expected to fit by the Sat 20:00 freeze; UP-1 and MB-1 are at risk, confirmed or dropped by the Architect at Fri 12:00 from merged units.
- **Priority line:** AR-4 > WARM-1 > SR-4 > SR-5 core > SR-6 > SR-7 > SR-8 > SR-5c > SR-5d > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > UQ-FI-3 > FR-B > DATA-10/13.

### 10.7 First builder steps

- **Lane I (SR-6):** worktree from main. Pre-flight batch to the Architect: (a) `accepted_evidence` source and receipt column names; (b) the Health router file and its admission helper; (c) whether the demo mini-grid Sites have gateways (`registered_at`, cadence) or arrive by file import; (d) the mini-grid Health frame file. Then SR-6a, commit, server review; then SR-6b.
- **Lane J (SR-7):** pre-flight: (a) building a `ChainRequest` in a route (`chain_api.py` `opened(ref)`); (b) the stored `critical_served` value shape; (c) the AR-4 claim-day reader (10.3); (d) the Service and claim-limit page files. Then SR-7a, SR-7b, pages.
- **Lane K (SR-8):** pre-flight: (a) as J (a); (b) the stored `daylight_headroom_kw` value shape (measured and missing hours); (c) the Renewable page and chart files. Then server, page.

## Revision 9 (Architect, Claude, 2026-11-12 ~13:30): data in the range means output for the range, on every Site type (SR-5 IN)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Rulings **D-SR.9-12** (`build-sheet-OWN-GAPS-2026-11-08.md`), owner-directed or owner-delegated, logged for owner review.
- Owner, verbatim (`.agent/owner-range-output-rule-2026-11-12.md`): "this should not have been the case to begin with, if there is data in the range, then there should be corresponding output, why was such a site specific disparity in design introduced to being with?" Earlier: "fix it now" (`.agent/owner-site-range-fix-now-2026-11-12.md`).
- **What this revision changes.** Rev 8's 8.1 table and its "Honest limit" are superseded where they disagree with D-SR.9. SR-5 moves from the backlog to **IN for 17 Nov**. SR-4 (lane G) is unchanged and still ships first. SR-4d (day strip) is OUT, because SR-5's day table replaces it.

### 9.1 The rule (D-SR.9, a standing product rule)

1. **When the selected range has data, every Site page shows output for that range.** This holds on every Site type: Kobo and Kisiwa (mini-grid), Cold, and EV. The page covers the whole range: totals, per-day states, and Findings in the range.
2. **A single-day (or single-hour, or single-night) view is only a drill-in from a range view.** It is never what a page shows by default. The drill-in always has a link back to the range view, and the bar says "Showing 9 Nov of the range" (R718).
3. **Point-in-time pages say so.** These are Health now (mini-grid, until SR-6), Prices valid now, Foundation (current settings) and the Sites index. They carry the R719 tags. A page that mixes range content with a point-in-time section labels the section ("Prices valid now"), and its bar tag stays "All pages".
4. **Days in the range without a usable result** use the D-E5.46 words, one reason per day. A range with no readings at all says "No readings received in this date range". Data-fact gaps never read "not analysed yet".
5. **The same page reads the same way on every Site type.** If one type covers the range and another shows one day, that is a defect, not a design choice.
6. **Supersedes:** the one-day default of S5-01, for what the Site Overview shows by default. The S5-01 one-day read stays, unchanged, as the drill-in (`?day=`). Decision `D-2026-10-14-s5-selected-window-overview` ("selected half-open UTC window") now holds as written for the page.

### 9.2 Root cause, for the owner (plain words)

1. Each Site type was built in its own slice, against its own read contract. Cold and EV were specified later, to cover the analysed periods in the window (PB-1a/b, D-E5.31). The mini-grid Overview was specified earlier, for one day (S5-01).
2. The mini-grid decision said "selected window". The S5-01 build narrowed that to exactly one UTC day so it could ship. That narrowing was accepted, and no one revisited it when the shared date range arrived.
3. When the range bar came (SR-2b), and again in my rev 8, day-shaped pages got a "focus day" inside the range. The range board was put in the backlog. I treated a cross-Site inconsistency as a feature to add later, when it was a defect.
4. Nothing checked the same page across Site types against the range. Each slice was reviewed only against its own contract, so the disparity was invisible until you used the product.
5. Fix: D-SR.9 is now a standing rule. Every UI plan and review carries a page × Site-type range table. A test (`RANGE_MATRIX`, SR-5e) fails any Site page whose data ignores the range without declaring why.

### 9.3 Audit: every Site page × Site type against D-SR.9

Evidence: the verifier's run (`results2.json`, two ranges, 3–9 Nov and 27 Oct – 2 Nov, on build E3e) and code on main. Key: **OK** follows the range today. **SR-4** fixed by SR-4 (links, tags, redirects). **SR-5x** fixed by that SR-5 unit. **GAP** is a known gap for 17 Nov: the page carries an honest tag, and the fix goes to the backlog.

| Page | Kobo (mini-grid) | Kisiwa (mini-grid) | Cold | EV | Evidence |
|---|---|---|---|---|---|
| Sites index → Site | SR-4a (links lose range today) | SR-4a | SR-4a | SR-4a | `siteDetailHref` bare; tabs 0/9 |
| **Overview** | **SR-5a/b**: today `/overview` with no date, so it shows today (11-12) on both ranges, same fingerprint. SR-4b's last-day view is the fallback only if SR-5 is held | **SR-5a/b** (same) | OK (`cold/overview?from&to`) | OK (`ev/overview?from&to`) | fp SAME A/B on Kobo/Kisiwa |
| **Performance: Dispatch** | **SR-5c**: today `dispatch/windows/2026-11-12` on both ranges. SR-5c adds a range day table, and the dispatch day becomes its drill-in | **SR-5c** | OK (temperature, backup-chain, findings) | OK (`ev/sessions`) | apis identical A/B |
| Performance: Kisiwa nights | n/a | **SR-5c**: today `finding-windows/2026-11-12`. Nights become a drill-in from the same day table | n/a | n/a | |
| Performance: Service | **GAP** (one hour by server design). SR-4b picks the 12:00 hour of the last day and declares it. Backlog **SR-7**: a per-day Service summary over the range from `mini_depth` rows, 0.5 | GAP (same) | n/a | n/a | |
| Performance: Renewable | OK up to 5 days. **GAP** over 5 days (server `MINI_RENEWABLE_DAYS` limit): SR-4b shows the last 5 days and declares them. Backlog **SR-8**: lift to 31 days on stored rows, 0.5 | same | n/a | n/a | |
| Performance: Scenarios | OK | OK | OK | OK | |
| Evidence claim limit (mini-grid) | **GAP**: one day, declared by SR-4b. Backlog with SR-7 | same | n/a | n/a | |
| Findings | OK | OK | OK | OK | request carries from/to |
| Work (Actions, Incidents, Maintenance) | OK (SR-4a carries range into links) | OK | OK | OK | |
| **Health** | **GAP**: shows now (`source-health`, `battery`); "Range not used · shows now" (SR-4c). Cold/EV Health follow the range, so this is a cross-Site disparity. Backlog **SR-6**: per-day source uptime and battery range over the range, about 1.0 (new read) | GAP (same) | OK (`cold/health?from&to`) | OK (`ev/health?from&to`) | |
| **Financials** | **SR-5d**: today only the diesel price valid now. SR-5d adds the range money block (from SR-5a) above the price list; the price section is headed "Prices valid now" | **SR-5d** | OK (`cold/financials?from&to`) | SR-4c: generic `/financials` redirects to `/ev/financials` (OK) | Kobo fp SAME A/B |
| Prices | N (valid now, R719) | N | N | N | point in time by nature |
| Evidence ledger | OK | OK | OK | OK, except the rejections/analytics panels: SR-4c (range or "All dates") | `/evidence/rejections`, `/analytics` without from/to |
| EV `/ev/financials` | n/a | n/a | n/a | OK on requests; fingerprint SAME across both ranges. **SR-4 pre-flight (f)** confirms that both ranges have no priced session (honest same content) or files a defect | |
| Foundation, Foundation changes | N (current settings) | N | N | N | |

- **After SR-4 and SR-5 (a-e):** every Site page either follows the range, is a declared drill-in from a range view, or is point-in-time by nature. Five known gaps remain, each tagged honestly on screen: mini-grid Health (SR-6), Service (SR-7), the claim limit (with SR-7), Renewable over 5 days (SR-8), and the cross-Site Health disparity. These are named in the presenter notes and the 17 Nov known-gap list.
- **Out of reach for 17 Nov, and why:** SR-6, SR-7 and SR-8 each need a new server read over the range plus parity. Each touches the core read path under the freeze, and no lane is free. **Backlog, first after 17 Nov**, in the order SR-6 > SR-7 > SR-8, about 2.0 units.

### 9.4 SR-5 technical design (builders do not design)

**Shape.** A new one-Site range read for mini-grid Sites. It is composed on one estate snapshot from **the same selectors the Portfolio uses**, so the Site's numbers equal the Portfolio's for the same range and cutoff by construction. A per-day breakdown comes from the stored `dispatch.day` rows (AR-3) and claim rows (AR-4), with D-ANY.10's absent-run compose. The page shows the range by default. The existing S5-01 one-day board is the drill-in (`?day=`).

**SR-5a: server read (Opus, Postgres, 0.75).**
- **New module `backend/assetops_backend/estate/site_range.py`.**
  - It has one public function, `site_range_body(service, tenant_id, site_code, req) -> dict | None`, where `service` is the `EstatePortfolioService` instance (`estate/portfolio.py`). It runs inside `service.read_snapshot(work)`.
  - **No edits** to `coverage.py`, `evidence_money.py`, `financials.py` or `portfolio.py`. These are AR-4's files. The module only imports from them. One exception: if the pre-flight shows `_scope` cannot be reached, one public alias `scope_for(snap, tenant_id, req, admit)` is added to `portfolio.py`, and that line is the only change to the file.
- **Inside `work(snap)`, in this order, on the one snapshot:**
  1. `scope = service._scope(snap, tenant_id, req, lambda code: code == site_code)`. Return None when `scope["sites"]` is empty (route 404). Refuse a Site whose `DOMAIN_OF_SITE_TYPE` is not `MINI_GRID` (route 404 `RANGE_OVERVIEW_NOT_APPLICABLE`).
  2. `f_sites, f_rows = select_finding_scope(snap, tenant_id, req, scope, {})`.
  3. `a_sites, a_rows = select_action_scope(...)`, then `attach_threads(...)` exactly as `_portfolio` does.
  4. `m_sites, m_lines, applicable, groups, _, _ = select_financial_scope(snap, tenant_id, req, scope)`.
  5. `days = dispatch_days(snap, tenant_id, site_id, req.from_, req.to, scope["k"])` (`estate/coverage.py`). This uses the AR-3 rows when served, and the D-ANY.10 absent-run compose otherwise.
  6. `gap_reasons = data_gap_days(days)` (D-E5.46). `grades = local_day_grades_kw(site, req, scope, tenant_id)`.
  7. Build the body below. Every count and amount is derived from steps 2-6, never recomputed another way.
- **Response body, schema `site-range-overview-1`:**
```
{ "schema_version": "site-range-overview-1",
  "site": {"site_code", "site_name", "site_type", "timezone"},
  "window": {"from", "to", "known_at": wire_time(k), "basis": "CURRENT" | "HISTORICAL"},
  "status": one of the Portfolio statuses (CURRENT, PENDING, PARTIAL, UNKNOWN, HISTORICAL), by _portfolio's rule over this one Site,
  "coverage": _coverage_site(site, cov),          # state, days {requested, checked, gaps[{day, reason}], text}
  "money": {
     "card": public(operating_cost_card(m_lines, applicable, groups)),   # the Portfolio's card, same states
     "partial": partial_money(site, m_cov, m_lines) | null,              # PARTIAL-MONEY, D-E5.45/46 label inputs
     "quantity": {"low", "high", "unit"} | null    # sum of ELIGIBLE lines' quantity; null on mixed units or an overlap group, by partial_money's rule
  },
  "findings": {"count", "confirmed", "not_confirmed", "awaiting_verification"},   # f_rows with lifecycle in MEMBERS; FC-1 (R715) definitions
  "actions": {"open", "awaiting_verification", "verified_resolution_count"},     # progress(...) for this Site
  "dispatch": {"days_requested", "days_analysed", "days_with_findings", "accepted_readings"},
  "days": [ { "day": "YYYY-MM-DD",
              "state": "FINDINGS" | "CLEAR" | "NO_READINGS" | "READINGS_CONFLICT" | "NOT_ENOUGH_READINGS"
                       | "NOT_ANALYSED" | "STILL_PROCESSING" | "NOT_EXPECTED",
              "finding_count": int | null,        # null on a gap day
              "money": {"low", "high", "currency"} | null,
              "money_state": "SUMMED" | "NO_ELIGIBLE_LINES" | "CURRENCY_MIXED" | "OVERLAPPING" | "WITHHELD",
              "accepted_readings": int | null } ],
  "links": {"findings": "/sites/{code}/findings", "day": "/sites/{code}?day={day}"} }
```
- **Rules for the days list:**
  - Days are the UTC calendar days of `[from, to)`. That is the `dispatch.day` grain, and the same day `?day=` opens on the S5-01 board, so a row and its drill-in name the same day.
  - **State precedence** (D-E5.46 table order):
    1. `NOT_EXPECTED` when the day's grade is NOT_EXPECTED (before readings began).
    2. `NO_READINGS` when the grade is NO_DATA.
    3. `STILL_PROCESSING` when the grade is PENDING, or the day has PENDING/LEASED jobs.
    4. `READINGS_CONFLICT` or `NOT_ENOUGH_READINGS` from `gap_reasons`.
    5. `NOT_ANALYSED` when the day has no available selection, or is unmatched.
    6. Else `FINDINGS` when `finding_count > 0`, otherwise `CLEAR`.
  - **Consistency requirement.** The set of non-`FINDINGS`/`CLEAR`/`NOT_EXPECTED` days, with their reasons, must equal `coverage.days.gaps`. When they disagree, the coverage wins. The day takes the coverage's reason, and the disagreement is logged `site_range_day_mismatch`. A test pins equality on every fixture.
  - `finding_count` counts the members whose episode intersects the day (half-open; `site_overview.read.intersects`).
  - Day `money` sums the ELIGIBLE `m_lines` whose `window_start` falls on that day, by `partial_money`'s single-currency and no-overlap rule.
  - `accepted_readings` is the day's `accepted_reading_count`.
- **Totals:**
  - `dispatch.days_requested` and `days_analysed` are taken from `coverage.days`.
  - `days_with_findings` counts the FINDINGS days.
  - `accepted_readings` sums the day values; it is null if any analysed day is null.
  - **No physical total is invented.** Generator hours and fuel litres are not in the stored day body. Litres appear only as `money.quantity`, the at-stake litres of the priced lines.
- **Route, in `backend/assetops_backend/outcome_api.py`:** `GET /api/sites/{site_code}/range-overview`, constant `RANGE_ROUTE`, with `perf.route`.
  - **Admission:** the same as the outcome board (`board_site`, then `disclosed`), so 401/403/404 behave as the board does.
  - **Window:** `from`/`to` are required and parsed with `estate.scope.estate_request("portfolio", ...)`. That means midnight UTC and at most 31 days; anything else is 422 `INVALID_WINDOW` (the estate code). `known_at` is optional.
  - **Errors:** a Cold or EV Site gets 404 `RANGE_OVERVIEW_NOT_APPLICABLE`, because their Overviews already read the range. A store failure is 503 `SITE_RANGE_OVERVIEW_UNAVAILABLE`.
  - **Stored response:** `ResponseStore.serve(StoredRoute(RANGE_ROUTE, tenant_id, key={"site", "from", "to", "known_at"}, sites=(site,), watermark_sites=(site,)), compose)`, the same pattern as the board. A new reading on this Site invalidates its entries; other Sites' readings do not.
  - Wired in `main.py` beside the board, with the existing portfolio service instance.
- **WARM-1 hook:** `tools/warm_ranges.py` adds `range-overview` for each mini-grid demo Site to its per-range route list. This is one list entry. Whichever of WARM-1 and SR-5 merges second adds it, and the `--verify` gate then covers it.

**SR-5b: the range Overview page (Opus, frontend, 0.5).**
- **Switch** in `sites/SiteOverview.tsx`, MINIGRID branch only:
  - the address has a valid range and no `day` (and no `date`): render `<SiteRangeOverview>`;
  - `day=` present: render the existing `SiteWindowOverview` (the drill-in), unchanged except for a "Back to the whole range" `RangeLink` (same path, `day` removed) above the board heading;
  - no valid range: unchanged (the SR-4a safety net gives one).
  - SR-4b's `pageDay` stays for the drill-in and for the fallback if SR-5 is held.
- **New `sites/SiteRangeOverview.tsx` + `sites/rangeOverviewClient.ts`** (typed client for the schema above; refusals mapped like `outcomeBoardClient.ts`). Layout follows the v69 `site-overview` skeleton:
  1. **Status line:** the coverage state in plain words, plus the days text, for example "6 of 7 days analysed · 4 Nov: no readings" (D-E5.46 money/days label).
  2. **Four outcome tiles:**
     - Fuel cost at stake: the money card, with the PARTIAL label when partial; when withheld, the Portfolio card's own words.
     - Findings: count, confirmed and not yet confirmed (R715 wording).
     - Actions: open and awaiting verification.
     - Days analysed: n of m.
     - Reuse the Portfolio's money card and tile components; no new money wording.
  3. **Day table, "Day by day":** one row per day.
     - Columns: date (Site-local label of the UTC day), state in D-E5.46 full words (`FINDINGS` → "n findings"; `CLEAR` → "Checked: nothing to report"; `NOT_EXPECTED` → "Before readings began"), money, and an "Open day" `RangeLink` to `?day=<day>` (the range carries).
     - Above the table, a compact strip of day cells coloured by state (`aria-label` per cell, keyboard focusable, linking to the same day). It uses `StatusPill` if UQ-FI-3 has merged, otherwise the existing state classes.
     - Over 14 days, the strip wraps by week.
  4. **"Findings in this range":** the existing Site Findings list component, fed by `finding-index?domain=mini-grid-dispatch&from&to` (already range-correct), first 5 rows, with a "See all findings in this range" link.
  5. **Next step:** the first Finding row's next step link, if any (existing component).
- **Empty and failure states:**
  - No readings in the whole range: the status line reads "No readings received in this date range", the tiles show "–", and the day table still lists the days.
  - 503: the page's existing unavailable panel. A 422 cannot happen (the bar sends valid ranges); if it does, "This date range can't be shown here".
- **Bar:** the range view declares nothing ("All pages"). The drill-in declares `span(day, day)` (SR-4c), giving "Showing 9 Nov of the range".
- **MOCK DEVIATION R721:** v69 `site-overview` is one window and has no day table. The range view keeps the skeleton (status → outcome tiles → needs attention → next step) and adds the day table as its range form. This follows D-SR.9, not a guard. The builder adds the register row.

**SR-5c: Performance over the range (Opus, frontend, 0.35).**
- Kobo/Kisiwa `PerformanceDispatch`, with a range and no `day`: show the same day table component (from the same `range-overview` request, so no new server call shape) under the heading "Dispatch by day". Each day links to `performance?day=<day>`.
- With `day=`: the existing dispatch detail, plus "Back to the whole range".
- The Kisiwa night window (`finding-windows/<day>`) is read only on the drill-in.
- The bar tag follows SR-5b's rule.
- MOCK DEVIATION R722 (v69 `performance-dispatch` is one window).

**SR-5d: mini-grid Financials over the range (Opus, frontend, 0.3).**
- The Kobo/Kisiwa Financials frame gets, above the existing diesel price section:
  - "Fuel cost at stake in this range": the `range-overview` money card, the PARTIAL label, and a per-day money list (non-null days only) with links to the drill-in day;
  - the existing price list under the heading "Prices valid now".
- With SR-5d merged, the frame's declaration changes from SR-4c's `now`/"prices valid now" to none ("All pages"). `SitePricesFrame` keeps "prices valid now".
- MOCK DEVIATION R723 (v69 `site-financials` mini-grid shows assumptions only).

**SR-5e: the guard (frontend, 0.15).**
- **New `frontend/src/ui/rangeMatrix.ts`:** `RANGE_MATRIX`, one entry per Site route pattern × Site type, each with `class: "R" | "D" | "N"` and `why` text. This is the 9.3 table, after SR-5.
- **New `shell/__tests__/siteRangeMatrix.test.tsx`:** the whole `App` with the SR-4a fixtures (four Site types) and the stub fetch recording requests.
  - For each entry, open the route with range 3–9 Nov.
  - **R entries:** every data request (excluding the registry, lineage, capabilities and cutover reads listed in the file) carries `from`/`to` equal to the range, or `range-overview` with them. The bar tag is "All pages".
  - **D entries:** they are reachable only with `day=`; without `day`, the page renders the range view.
  - **N entries:** the page declares `now`.
  - **A Site route in `App.tsx` with no matrix entry fails the test** (route list read from the router config).
- This is the process fix in code. Plans and reviews cite the matrix row for any Site page they touch (D-SR.10).

**Tests (one file at a time; no full suites; Postgres only on `*_test` DBs).**
- `backend/tests/test_sr5_range_overview_route.py` (no DB, stubs): 422 on a non-midnight window, a window over 31 days, or a missing `to`; 404 for Cold/EV and unknown Sites; 401/403 through the board seams; the stored-response key and watermark Site; perf line present.
- `backend/tests/test_sr5_range_overview_postgres.py` (fixtures on `assetops_test`):
  - a 7-day Site with one FINDINGS day, one CLEAR, one NO_READINGS, one READINGS_CONFLICT, one STILL_PROCESSING (open job) and one NOT_EXPECTED day (before first reading);
  - per-day states and precedence;
  - the gaps-equal-coverage pin;
  - day money sums and an overlap day giving `OVERLAPPING`;
  - totals;
  - **Portfolio equality:** for the same range and `known_at`, `coverage`, `money.card` and `money.partial` equal the estate Portfolio's `coverage.sites[]` entry, OPERATING_COST card and partial money for this Site, run on a one-Site estate;
  - **drill-in consistency:** for each analysed day D, the day's FINDINGS/CLEAR agrees with whether `GET /overview?date=D` selects a Finding;
  - **rows on/off:** the body is byte-identical with `ASSETOPS_PERIOD_READ_KINDS` including and excluding `dispatch.day` and `evidence.claim`, including one absent-row run (D-ANY.10).
- **Frontend (vitest):**
  - `sites/__tests__/siteRangeOverview.test.tsx`: tiles, each state's words, the partial label, the empty-range words, the "Open day" href keeping the range, the strip's `aria-label`s.
  - `SiteOverview` switch: range without day → `range-overview?from&to`; `day=` → the board request; back link.
  - `PerformanceDispatch`: range → day table, with no `dispatch/windows` request; `day=` → `windows/<day>`.
  - The Financials frame money block and its headings.
  - `sr2RequestUrls.test.tsx` pins: the Kobo/Kisiwa Overview and Dispatch with a range and no day now request `range-overview`, replacing SR-4b's `date=<range.to>` pins. Every other pin is unchanged.
  - `siteRangeMatrix.test.tsx`.
- `tsc --noEmit`, `tools\check-architecture.ps1`.

**Parity and timing evidence (gate for merge).**
- Run on a scratch `<prefix>_audit` copy of the demo DB (authorised), as **one heavy job**, never beside a parity or prepare run.
- **Ranges:** KOBO-001 and KISIWA-001 (or the demo DB's two mini-grid Sites, named in the pre-flight), each over 3 ranges: the bar's "Last 7 days", a 14-day range and a 31-day range ending on the data window's last day.
- **Checks:**
  1. The range body equals the estate Portfolio's entry for that Site (the same equality as the test, on real data).
  2. The body is identical with rows on and off.
  3. Each analysed day agrees with the one-day board.
- **Written to `.agent/SR-5-parity.json`; gate 0 mismatches.**
- **Timing:** cold, unprepared, then stored (second request), per range. **Gate: the stored response is ≤2.0 s on every range.** Cold times are recorded, not gated; the estimate is 1-4 s for a week. The ranges the bar offers are pre-built by WARM-1, so the presenter only sees stored times.

**Units, lane, deadline.**

| Unit | What | Units |
|---|---|---|
| SR-5a | server read, route, stored response, tests, parity and timing | 0.75 |
| SR-5b | range Overview page, switch, drill-back, tests | 0.5 |
| SR-5e | `RANGE_MATRIX` + matrix test | 0.15 |
| **SR-5 core** | a + b + e, one review | **1.4** |
| SR-5c | Performance day table, nights as drill-in | 0.35 |
| SR-5d | mini-grid Financials range money | 0.3 |
| **SR-5 all** | | **2.05** |

- **Lane H, VPS, from tonight.**
  - Opus builder, worktree `AssetOpsV1-sr5`, branch `task/SR-5-range-board` from main.
  - **Order:** pre-flight → SR-5a (needs no SR-4 code; starts tonight) → merge main once SR-4 has merged (SR-5b/c/d need `RangeLink`, `pageDay` and `rangeFocus`), or else build on SR-4's ACCEPTed commits → SR-5b → SR-5e → SR-5c → SR-5d. There is one commit per unit.
  - Fresh Claude reviewer per review round; Sonnet fix rounds.
- **Deadline: SR-5 core ACCEPTed by Sat 16:00, merged by the Sat 20:00 freeze, or held whole.**
  - If held, SR-4b's last-day Overview stays, tagged "Showing 9 Nov of the range". The known-gap list then names the mini-grid Overview.
  - SR-5c and SR-5d merge only after the core. Each one that is not ACCEPTed by Sat 16:00 drops alone, and its page keeps SR-4's honest tag.
- **Pre-flight (one batch to the Architect, before code):**
  - (a) the `EstatePortfolioService` names (`_scope`, `read_snapshot`, `select_finding_scope`, `select_action_scope`, `progress`), the `EstateRequest` fields they need (lens "all"), and whether a one-Site `admit` returns the same coverage entry as the estate run;
  - (b) the OPERATING_COST card's public fields that carry the amount;
  - (c) whether `local_day_grades_kw` grades are Site-local days, and how they map to UTC `dispatch.day` days (the D-E5.42 rule); state the mapping used for `NOT_EXPECTED`/`NO_READINGS` per UTC day;
  - (d) the two mini-grid Sites and the data window in the demo DB;
  - (e) the Financials frame file;
  - (f) the route list for `RANGE_MATRIX`.
- **Collisions:**
  - SR-5a only imports AR-4's files (`coverage.py`, `evidence_money.py`), so it does not conflict with AR-4. If AR-4 merges first, SR-5 merges main and re-runs its rows on/off test.
  - `outcome_api.py` and `main.py` take one route and one wiring line each.
  - The frontend overlaps SR-4 (`SiteOverview`, `PerformanceDispatch`) and UQ-FI (copy). SR-5 merges after SR-4, and whichever of SR-5 and UQ-FI merges second resolves.
  - WARM-1 needs its one list entry (above).

### 9.5 17 Nov package capacity, honestly (D-SR.12)

- **Before:** about 11.75 units committed, in the 11-13 window (rev 8). BL-ANY-absent (0.5) and SR-4d (0.25) were not counted.
- **Added:** SR-5, 2.05 (core 1.4 + c 0.35 + d 0.3). Lane H brings its own builder hours. The binding limits are review throughput and the one-at-a-time heavy-job slot. SR-5a needs two short slots: its Postgres test (~15 min) and the parity/timing run (~40 min).
- **What moves:**
  - **SR-4d OUT** (subsumed by SR-5's day table; no owner approval needed now).
  - **BL-ANY-absent OUT** (it was IN-if; backlog).
  - **DATA-10/13 (0.4) becomes IN-if-free.** It is the first to drop, ahead of SR-5c/d.
  - **Firm package: about 13.4 units, slightly over the 11-13 window.** The risk is stated: if lanes run late, the drop order from the right is DATA-10/13, then SR-5d, then SR-5c, then UQ-FI-3. SR-5 core is protected.
- **Priority line** (replaces rev 8's): AR-4 > WARM-1 > SR-4 > **SR-5 core** > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > **SR-5c > SR-5d** > UQ-FI-3 > FR-B > DATA-10/13.
  - Why SR-5 core is above UQ-FI: the owner calls the disparity a defect that "should not have been the case to begin with". A demo that shows one day on two Site types and the range on the other two contradicts the product's own story.
  - Why SR-5 core is below SR-4: SR-4 is the precondition, and alone it already leaves every screen honest.
- **Known gaps for 17 Nov** (named on screen and in the presenter notes): mini-grid Health shows now (SR-6); Service is one hour (SR-7); the claim limit is one day (SR-7); Renewable is the last 5 days on long ranges (SR-8). Backlog order after 17 Nov: SR-6 > SR-7 > SR-8, about 2.0 units.

## Revision 8 (Architect, Claude, 2026-11-12): Site pages on the date range (SR-4)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude. Owner-delegated rulings **D-SR.1-8** (`build-sheet-OWN-GAPS-2026-11-08.md`), logged for owner review. Register rows R718-R719.
- Owner, verbatim: "when i navigate into sites, it appears the date range is not used to inform the content, verify this".
- **Verified: true.** Evidence: the verifier's run on the demo build (two ranges, 56 page loads; `results2.json` in the coordinator scratchpad). Code cited from main `feea059b0`.
  1. **The range is lost on the way in.** No Site link carries the range: the Sites index, breadcrumbs, Kobo/Kisiwa tabs (0/9 to 0/15), and most in-page links. Cold and EV keep it on 11/13 to 21/22 links because their frames pass a window `search`. `/ev/financials` keeps it on 3/12. `OperatorSiteTabs` only appends a `search` a frame passes in. Kobo/Kisiwa frames pass none.
  2. **The Kobo/Kisiwa Overview shows today.** `SiteOverview.tsx:132` sends `getOverview(siteId, {}, selection)`. `selectionOf` (:84-93) reads only `day`. With no `day`, the server serves today (11-12), outside both ranges.
  3. **Kobo/Kisiwa Performance shows today.** `PerformanceDispatch.tsx:108` defaults to `todayUtc()`, so the request is `dispatch/windows/2026-11-12`. Kisiwa `finding-windows/<day>` does the same. `miniDepthClient.ts:341/365` falls back to today when there is no range. When there is a range, Service sends the whole range as its "hour" window and Renewable sends more than its 5-day limit.
  4. **Health and Financials on Kobo/Kisiwa are point-in-time by nature.** `/source-health` and `/battery` are read on the server clock. Financials is the price list `valid_at=now`.
  5. **The bar overclaims.** `readsSharedRange` (`ui/sharedRange.ts:195`) returns true for any `/sites/<id>...` address that has from/to. So Health, Financials and Overview say "All pages" over content that ignores the range.
- **Not affected:** Findings and Work on every Site type, and Cold and EV content pages (their requests carry from/to).

### 8.1 Which Site pages should follow the range (D-SR.1)

| Class | Meaning on screen | Pages |
|---|---|---|
| **R: follows the range** | The content covers the range's days. Tag "All pages" (mock v71 Change 0b). | Every Site type: Findings, Work (Actions, Incidents, Maintenance), Evidence ledger. Kobo/Kisiwa: Scenarios, Renewable (range up to 5 days). Cold: Overview, Performance, Findings, Health, Financials, Evidence and event pages, where the selected event lies inside the range. EV: every `/ev/...` page, Performance, Findings, Health. |
| **D: one day or one part of the range** | The page shows a day (or part) **inside** the range. It defaults to the range's last day, never to today when today is outside the range. Tag "Showing 9 Nov of the range" or "Showing 5–9 Nov of the range". | Kobo/Kisiwa: Overview (the board is one UTC day by server contract, `site_overview/route.py:13`), Performance/Dispatch, Kisiwa night window, Service (one hour of the focus day), Evidence claim limit, Renewable when the range is longer than 5 days (its last 5 days). |
| **N: point in time** | The page shows "now" by nature. Tag "Range not used · shows now", "· current settings" or "· prices valid now". | Kobo/Kisiwa Health (server clock); Kobo/Kisiwa Financials and every Prices page (valid now); Foundation for every type; Foundation changes; the Sites index (a directory). These keep the old tag "Not used on this page". |

- **Honest limit, called one:** the Kobo/Kisiwa Overview stays **one day of the range** for 17 Nov. A board that totals the range needs a new server composition over the stored day rows, then parity and WARM-1 work. That is about 1.5 units of read-path work, and it falls under the core freeze. It goes to the backlog as **SR-5 range board for mini-grid Sites**. Range totals for these Sites are on the Portfolio and estate Financials today.

### 8.2 The fixes (D-SR.2-7)

**SR-4a: every Site link carries the range (D-SR.2, D-SR.3).**
- **New `frontend/src/ui/RangeLink.tsx`:** `RangeLink` is `forwardRef<HTMLAnchorElement, LinkProps>`. It renders react-router `Link` with `to={carryRange(to, params)}`, where `params` comes from `useSearchParams()`.
- **New `carryRange(to, params)` in `ui/sharedRange.ts`:**
  - A string or `{pathname, search}` target whose pathname matches `SITE_PATH = /^\/(?:sites(?:\/.*)?|performance\/.+)$/` gets `withRange` applied. Split off `#hash` first and re-append it.
  - A target that names its own `from`/`to` keeps them (existing `withRange` rule).
  - Relative targets, non-Site targets and an invalid or absent address range are returned unchanged.
  - Page-only parameters (`day`, `hour`, `event`, `cursor`) never travel.
- **Codemod:** in every non-test `.tsx` under `frontend/src`, `Link` from `react-router-dom` becomes `RangeLink` (alias `RangeLink as Link` is allowed). Exempt: `ui/RangeLink.tsx`, `ui/NavRail.tsx` and the rail `NavLink` in `shell/OperatorShellLayout.tsx`, which already carry through `railSearch`.
  - This one change covers `OperatorSiteTabs`, `Breadcrumbs`, the `SitesIndex` cards (`siteDetailHref`) and in-page links.
  - The tab `search` that Cold and EV frames pass still wins, because it names its own range.
- **Navigation safety net in `SharedRangeOutlet`** (`shell/SharedRangeBar.tsx:86`). It covers `navigate()` calls and data-built links. Before the page mounts, when the address has **no** from/to and the pathname is a Site content route (see the pre-flight list), it renders `<Navigate replace>` to the same path and hash, the existing params, and a range chosen in this order:
  1. The range of the previous in-app address. Keep a `useRef` updated on every render where `readSharedRange` is `set`, including `known_at`.
  2. Else, when the address names `day`/`date`: the 7 days ending on that day.
  3. Else `entryRange()`, which is byte-identical to the bar's presets, so WARM-1's stored answers still hit.
  - An `invalid` range is left alone, as today: the page explains it.
  - **Consequence, intended:** Site Work pages now open on the shared range, not on R338's own default. This closes SR-2b item 3 for Site pages. Global Work pages are unchanged.
- **Guard** `tools/checks/site-links-carry-range.ps1`, registered in `tools/check-architecture.ps1` as "Site links carry the shared range".
  - It fails any non-test `.tsx` under `frontend/src` that imports `Link` or `NavLink` from `react-router-dom`, outside the three exempt files.
  - Built-in self-test: a violating fixture fails, the exempt file passes, and an aliased `RangeLink as Link` passes.
  - Non-vacuous: it must fail on main's `shell/operatorSiteTabs.tsx`.

**SR-4b: day pages default inside the range (D-SR.4, D-SR.5).**
- **New `pageDay(params, now = Date.now())` in `ui/sharedRange.ts`:** a valid `focusDayOf(params)`, else the address range's `to` day when `readSharedRange` is `set`, else today's UTC day (reached only when the address has no valid range).
- **Uses:**
  - `SiteOverview.selectionOf`: `date: pageDay(params)`. The request now always names a day. The served-day write-back to `day=` is unchanged. Remove the dead `?? params.get(...)` fallbacks.
  - `PerformanceDispatch.tsx:108`: `pageDay(params)` replaces `todayUtc()`. Delete `todayUtc`.
  - The Kisiwa `finding-windows/<day>` read takes the same day.
  - `miniDepthClient.ts:341/365`: `pageDay(params, now)` replaces `focusDayOf(params) ?? today`.
  - Every other `new Date().toISOString().slice(0, 10)` used as a page day under `sites/` and `shell/` (the pre-flight lists them, e.g. `SiteAnalyticsFrames.tsx:456 todayWindow`).
- **Service** (`serviceWindowFromParams`): it uses the address from/to only when they span exactly one hour or exactly one day (story links). Otherwise it uses the 12:00-13:00 local hour of `pageDay`. It declares that day.
- **Renewable** (`renewableWindowFromParams`): it uses the address from/to when they span at most 5 days. Otherwise it uses the 5 Site-local days ending on the local date of the range's last UTC day (`localDaysWindow(tz, addDays(lastLocal, -4), 5)`). It declares that span. The pre-flight confirms the 5-day server limit (`MINI_RENEWABLE_DAYS`).
- **Previous/Next day on the Kobo/Kisiwa board** (`SiteWindowOverview`):
  - When the shown day is inside the range, they stay inside it. At an edge, the link is replaced by plain text "First day of the range" or "Last day of the range", with `data-day-step-edge`.
  - When the shown day is outside the range (an explicit story `day=`), they behave as today, and FocusPicker's "Show <day>" stays.

**SR-4c: the bar says what each page does (D-SR.6, D-SR.7).**
- **`ui/rangeFocus.tsx`:**
  - `RangeFocus` becomes `{ kind: "span"; from: string; to: string } | { kind: "now"; note: "shows now" | "current settings" | "prices valid now" }`.
  - `useDeclareRangeFocus(day)` stays as a wrapper for `span(day, day)`.
  - Add `useDeclareRangeSpan(from, to)` and `useDeclareRangeNotUsed(note)`.
  - All declarations use `useLayoutEffect`, so the bar never paints "All pages" first.
- **`SharedRangeBar` tag** (constants in the file):

| Page state | Tag | Spoken name of the button |
|---|---|---|
| span inside the range, one day | `Showing 9 Nov of the range` | "Date range: … This page shows one day of it: 9 November 2026" |
| span inside the range, several days | `Showing 5–9 Nov of the range` | "… This page shows part of it: 5 to 9 November 2026" |
| span outside the range | `Showing 24 Oct · range not used` (unchanged) | unchanged |
| now | `Range not used · shows now` / `· current settings` / `· prices valid now` (class `shared-range__tag--elsewhere`, `data-shared-range-focus="now"`) | "Date range for the other pages: … This page shows <note>; the range is not used here" |
| a Site content page that follows the range | `All pages` (unchanged) | unchanged |
| the Sites index, record pages | `Not used on this page` (unchanged) | unchanged |

- **Declarations** (the pre-flight confirms the frame for each):
  - `now` / "shows now": the mini-grid branch of `SiteHealthFrames`.
  - "prices valid now": the mini-grid Financials frame and `SitePricesFrame`.
  - "current settings": every Foundation frame (`SiteFoundationFrame` and `SiteAnalyticsFrames` ~2151/2180) and Foundation changes.
  - span: Renewable (long range) and Service (its day).
  - Pages already on FocusPicker keep declaring through it.
- **EV on the generic paths:**
  - `/sites/<EV>/financials` (a diesel price page that does not apply to EV) renders `<Navigate replace>` to the EV financials route, keeping the query.
  - On the generic Site Evidence page, the rejections panel and the analytics panel get `from`/`to` when the pre-flight shows their routes accept them. Otherwise each panel heading gains the line "All dates, not only the date range" (`data-panel-range="all-dates"`).

**SR-4d (optional, needs owner approval by Fri 12:00): a day strip on the Kobo/Kisiwa board.**
- A row of the range's days as links (`day=`), with the current day marked (`aria-current="date"`). It goes under the board heading, next to FocusPicker.
- MOCK DEVIATION: v69 `site-overview` has no strip. It would be register R720 if built. 0.25 units.
- Without approval it is OUT; FocusPicker already lets the presenter pick any day of the range.

### 8.3 Tests (vitest one file at a time; no full suites, D-17N freeze rules)
- `ui/__tests__/rangeLink.test.tsx` (new). `carryRange` cases:
  - a Site path gains the range;
  - `/performance/...` gains the range;
  - a target that names its own range keeps it;
  - a `#hash` is kept after the query;
  - an object `to`;
  - relative and non-Site paths are untouched;
  - an absent or invalid range adds nothing;
  - `day`, `cursor` and `event` never travel;
  - `known_at` travels.
  - `RangeLink` renders the carried href.
- `shell/__tests__/siteRangeCarry.test.tsx` (new, **the runtime guard**). Whole `App` in a memory router, real clients over a stub fetch, with Site-detail fixtures for KOBO-001 (MINIGRID), KISIWA-001 (MINIGRID), COLD-LAB-001 and EV-LAB-001. Other reads may answer 503: the test is about links.
  - Start at `/portfolio?from=…&to=…`, open the Sites rail item, and check that every Site card href carries the range.
  - For each Site type and each tab on its tab row: open the page, then check that **every** `a[href]` whose path matches `SITE_PATH` carries `from` and `to`, or names its own range.
  - Click each tab: the address keeps the range.
  - Safety net:
    - a fresh `/sites/KOBO-001` gets the 7-day preset;
    - `/sites/KOBO-001?day=2026-10-24` gets 18-24 Oct and keeps `day`;
    - `navigate("/sites/KISIWA-001/performance")` from a ranged page carries the range;
    - an invalid range is left alone.
- `ui/__tests__/sharedRange.test.tsx` (extend):
  - `pageDay`: day wins; else `range.to`; else today only with no range.
  - Service with a 7-day range gives the 12:00 hour of the last day; with a story one-hour window it is unchanged.
  - Renewable with a 7-day range gives the last 5 local days; with 3 days it is unchanged.
- `shell/__tests__/sharedRange.test.tsx` (extend): the tag and spoken name per row of the 8.2 table, for each Site type's Overview, Performance, Health, Financials, Prices and Foundation, with a range in the address.
- Per page:
  - `SiteOverview` and `s502OverviewFindingList`: the request sends `date=<range.to>`, `day=` wins, the write-back is unchanged.
  - `PerformanceDispatch`: `windows/<range.to>`.
  - `SiteWindowOverview`: the edge text at the first and last range day, and unclamped stepping outside the range.
  - The EV generic financials redirect.
  - The Evidence panels' range or their "All dates" line.
- `sr2RequestUrls.test.tsx`: update the pins for Kobo/Kisiwa with a range and no `day` (board `date=<range.to>`, Dispatch `windows/<range.to>`). Every other pin stays byte-identical.
- Existing tests that assert bare Site hrefs: compare the path part, as SR-2 did. Never delete an assertion.
- Guard self-test plus `tools\check-architecture.ps1` (19 → 20 checks). `tsc --noEmit` clean.
- Captures: none in this slice. The tag wording changes are in UQ-FI's after-captures if UQ-FI merges later; otherwise the coordinator recaptures the four Site Overviews once before the freeze.

### 8.4 Size, lane, order, and the 17 Nov verdict (D-SR.8)

| Unit | What | Units |
|---|---|---|
| SR-4a | RangeLink, codemod, safety net, guard, runtime guard test | 0.75 |
| SR-4b | `pageDay`, Overview/Dispatch/Service/Renewable defaults, edge stepping | 0.4 |
| SR-4c | Declarations, tags, EV generic redirect, Evidence panels | 0.35 |
| **SR-4** | one branch, one review | **1.5** |
| SR-4d | day strip, only on approval | +0.25 |

- **Lane G, frontend only, no Postgres.**
  - Opus builder, wt `AssetOpsV1-sr4`, branch `task/SR-4-site-range` from main. Commits in the order a → b → c.
  - Start on the first free laptop lane today; otherwise on the VPS at Thu 16:00.
  - Fresh Claude reviewer; a Sonnet fix round.
- **Collisions:**
  - UQ-FI-1 and UQ-FI-2 (lanes D/E) touch the same frames, for copy and classes.
  - SR-4a's codemod changes only import lines, so whichever merges second merges main and resolves.
  - No AR-4, WARM-1 or DATA file is touched. Mini-grid board days are stored rows (ANY-1), so `date=<range.to>` is under 2 s with no WARM-1 change.
  - WARM-1's preset strings are reused by the safety net, so they are unchanged.
- **Priority** (replaces 7.7's line): AR-4 > WARM-1 > **SR-4** > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > UQ-FI-3 > DATA-10/13 > FR-B > BL-ANY-absent. PR-3 and CLEAN-1 have merged.
- **Capacity:** PR-3 and CLEAN-1 merged after rev 7. That frees about 0.75 of the 4.2 committed units. With SR-4, the package is about 11.75 units, inside the 11-13 window.
- **Verdict: IN for 17 Nov**, under the **core freeze Sat 20:00**, because it changes existing requests (the Overview and Dispatch day).
  - Review ACCEPT by Sat 16:00, merge by Sat 20:00, then the Sat-night rehearsal build.
  - **Owner, relayed: "fix it now".** SR-4 starts immediately, in the owner's order: (1) links carry the range, including the Sites index (4a); (2) the Overview day comes from the range; (3) the focus day defaults to the range's last day (4b); (4) honest tags (4c). Only SR-4d can drop; a, b and c all ship. If time runs short, merge each commit as it is ACCEPTed (a, then b, then c). Every commit leaves the screen honest.
- **OUT, backlog:**
  - **SR-5**, a range board for Kobo/Kisiwa (about 1.5 units, read path plus parity).
  - Range money on mini-grid Site Financials (about 0.75).
  - The Cold/EV "No event in <range>" wording (SR-2b item 4), unless the pre-flight shows a Cold/EV page blank or misleading on a range with no event. In that case it joins SR-4 at +0.25.

### 8.5 Builder steps (SR-4)
1. **Pre-flight, one batch to the Architect, before any code:**
   - (a) every route under `/sites` and `/performance` in `App.tsx`, classed R/D/N per 8.1, with its frame file;
   - (b) every today-default page day under `sites/` and `shell/`;
   - (c) whether `/evidence/rejections` and `/analytics` accept from/to;
   - (d) Renewable's server day limit;
   - (e) the list of files the codemod changes;
   - (f) a Cold and an EV Site page opened on a range with no event: what they show.
2. **SR-4a:** `carryRange` + `RangeLink` + test → codemod → safety net → guard + registration → runtime guard test. Commit.
3. **SR-4b:** `pageDay` + uses + Service/Renewable windows + edge stepping + tests + `sr2RequestUrls` pins. Commit.
4. **SR-4c:** focus kinds + bar tags + declarations + EV redirect + Evidence panels + tests. Commit.
5. Run `tsc`, the named vitest files one at a time and `check-architecture`. Write the packet with outcome, files, checks and register rows R718/R719. Then a fresh Claude review.

## Revision 7 (Architect, Claude, 2026-11-12 ~07:10): the owner's 17 Nov expectations, answered item by item

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (since 2026-10-27).
- Owner, verbatim (`.agent/owner-17nov-expectations-2026-11-12.md`): "why is the ~2 sec target not done sooner than nov 17, especially with the new macine, i expect both a super modern UI and all performance related things as well as signifiant data converage to be in for client demo. i also expect client data upload and modbus to be in by then."
- Rulings **D-17N.1-7** (`build-sheet-OWN-GAPS-2026-11-08.md`), logged for owner review. Revisions 4-6 stand except where 7.8 changes the lanes, the priority and the late-merge window.
- Units are agent-pace build units (each includes review and one fix round). Measured rate (section 0.1): about 1.75 units per lane per day, 4-8 units per calendar day across 3-4 lanes; lower on days with a prepare or a walkthrough.

### 7.0 Capacity (what the new machine changes, and what it does not)

| | Laptop (until Thu ~16:00) | VPS (from Thu ~16:00) |
|---|---|---|
| Builder lanes | 3 (16 GB; Docker VM crashed once) | 5-6; 2 of them frontend-only (no Postgres) |
| Heavy jobs (parity, prepare, Postgres suites, bench run) | one at a time | still **one at a time**: they compete for the same Postgres and disk; this, not RAM, is the real limit |
| DB connections | default 100; BL-71 exhaustion seen | `max_connections 300` (D-E5.47 mitigation in place) |
| Speed of ONE request | about 8 s for an unprepared Portfolio week | **about the same** (see 7.1); measured once as the VPS's first job |

- **Window to the freeze:** Thu 16:00 to Sat 20:00 is about 52 hours. After VPS set-up (DB restore of client4/client7, venv, `node_modules`; about 2-4 hours, Thu evening), about 48 lane-hours remain. At the measured rate that is **about 11-13 units across 5-6 lanes**, after review and fix rounds.
- **Already committed in that window (rev 4-6): about 4.2 units.** AR-4 remainder 1.0, PR-2a merge, PR-3 remainder 0.5, UQ-FI 1.9, FR-B 0.5, CLEAN-1 0.25.
- **So about 7-8 units are free.** The six asks, in full, add about 22 units. The rest of this revision chooses which 7-8.

### 7.1 Ask 1: "~2 s for any range" (D-17N.1)

**Why the bigger machine does not fix it by itself (plain words).**
- One page request runs as **one sequential piece of work in one Python process**. It reads every Site, works out each day's dispatch selection, the evidence, the money and where each figure came from, and then writes the answer.
- 8 cores let us run **more requests and more builders at the same time**. They do not split one request into eight. A cloud vCPU is usually no faster on one thread than a recent laptop core, and is often slower.
- So the fix is to **do less work per request**: store each day's answer once, as revisioned rows, and read the rows (BL-66, cards AR-0 to AR-7). Each stored kind must be proven byte-for-byte equal to today's answer before it is switched on (parity). Each proof run takes 25-40 minutes, and two of them found real defects that would have shown wrong answers (D-ANY.7, D-ANY.10). That proof is why it is not done sooner. It is also what makes the fast answer the same as the slow one.

**Where it stands today (cited).**
- **Site boards: done.** ANY-1 (AR-0, AR-1, AR-2) merged `5ffe50d09`. It gates every mini-grid board day at ≤2 s cold, with parity 59/0/0. AR-6 (Cold/EV boards under 1 s) merged `ef02bd649`. The rows serve only when `ASSETOPS_PERIOD_READ_KINDS` names them. The walk7 serve sets the four `mini_depth.*` kinds; `dispatch.day` stays off until combined parity passes (handoff 06:40).
- **Portfolio: not done.** AR-4 (`task/ANY-2-AR4`, packet `AssetOpsV1-ar4/.agent/AR-4-packet.md`). Client4, cold, store off:

| Request | rows off | claim + dispatch.day rows, first switch | after the second switch (D-ANY.10 item 4) |
|---|---|---|---|
| week 10-19..10-26 | 10.9 s | 9.3 s | **8.1 s** |
| 22 days | 27.0 s | 24.8 s | not yet measured |
| 31 days | 33.0 s | 29.0 s | not yet measured |

- **Where the 8.1 s goes** (packet, profile after the second switch):
  - `select_dispatch_days_on`: 4 calls, about **2.2 s**, all from `coverage._mini_grid_basis` / `evidence_money.mini_grid_rows`. That is dispatch-day composing on a path that should read rows. Not yet explained. Candidates: absent rows composed under D-ANY.10, or `_mini_grid_basis` reading three times.
  - `_mini_grid_money` + `consequence_provenance`: about **4 s**. Not stored by any kind (D-ANY.9 backlog `evidence.consequence_money`).
  - The other ~1.9 s has not been profiled (the summary, the Cold/EV Sites, serialisation).

**What ≤2 s for any range would take, honestly.**

| Step | What | Units | Order |
|---|---|---|---|
| S1 | Finish AR-4: merge main (D-ANY.10 is on main), combined parity 0/61, timings week/22/31 with profiles (resume point 0) | in the 1.0 already committed | Thu eve |
| S2 | **DISP-1**: explain and remove the 2.2 s of dispatch lookups. If the cause is fixable in AR-4's files at ≤0.3 units, fix it on AR-4; otherwise it is its own card after AR-4 merges | 0.3 | Fri, on AR-4 |
| S3 | money.lines read side (MN-2 rest) | in the 1.0 already committed; IN only if parity passes by Sat 12:00 (D-ANY.8) | Fri |
| S4 | `evidence.consequence_money`: a new stored kind per (Site, consequence revision, Finding revision), invalidated by Finding recompute, consequence revision and price revision; parity + price-save case | 1.5 | after S1-S3, same files |
| S5 | Profile and remove the remaining ~1.9 s | 0.5-1.0 (unknown until profiled) | after S4 |

- S1-S5 run in **one lane, in sequence**, because they edit the same two files (`estate/coverage.py`, `estate/evidence_money.py`) and each needs the previous profile. That is about 2.5-3 units of serial work after AR-4's own review, so it ends **Mon at the earliest**. Even then, ≤2 s on the 31-day Portfolio is not certain. Every step so far gained less than its profile promised (13 s expected, 1.7-4 s measured).
- **Verdict: ≤2 s for any range, unprepared (computed live), is OUT for 17 Nov.** S4-S5 go to the backlog as `ANY-3` (D-ANY.9 shape, confirmed after the S1 profile).

**What we can honestly deliver instead: ≤2 s on every range the presenter can reach by clicking, prepared ahead.** This is a **workaround**, and it is called one.
- **WARM-1 (0.6 units, IN):** after each data change, the demo machine pre-computes and stores the answer for every range the shared date bar offers, plus every day-aligned 7-, 14-, 30- and 31-day range in the demo data window. A stored answer serves in well under a second (the D-ANY.4 pre-built ranges today).
- **This reverses D-ANY.3 for the 17 Nov build only.** D-ANY.3 refused it as throw-away work. It still is throw-away once ANY-3 lands, but ANY-3 cannot land by 17 Nov, and the owner has raised the bar. The tool lives in `tools/`, and the product code gains only the HTTP prebuild path (BL-71, part 2).
- **Custom ranges** (the bar's "Custom" dates outside the set) still compute live: about 8 s for a Portfolio week, 25-30 s for a month, and less once DISP-1 and money.lines land. The page shows its existing loading state. Presenter rule D-ANY.4 is narrowed to "Custom on the Portfolio".
- **Verdict: IN-if WARM-1 passes its gate. ≤2 s is then true for every preset and every 7/14/30/31-day range in the data window, on every page; it is not true for arbitrary custom ranges.**

**WARM-1 technical design (builders do not design).**
- Branch `task/WARM-1-range-warm` from main. Opus builder. Files: `tools/warm_ranges.py` (new), `chain/prebuild.py` (an HTTP mode), `tools/demo_combined.py` (calls it after its prebuild), `backend/tests/test_warm1_ranges.py` (no DB).
- **Range set**, generated from the demo clock and each Site's first reading day:
  1. The five presets as the shared bar sends them: Yesterday, Last 7 days, Last 30 days, This month, Last month. The query strings must be byte-identical to what `RANGE_PRESETS` produces, or the store misses. The pre-flight captures them from the live bar.
  2. Every window of 7, 14, 30 and 31 days that ends on a day boundary and lies inside the data window. The day boundaries are the ones the bar uses, which the pre-flight confirms (UTC or Site-local).
  3. The story ranges already in `config/chain/prebuilt-routes-v1.json`.
  - Expected size: about 75 ranges.
- **Routes per range:** every API request the script pages make for that range: Portfolio (each PF-T tab's request), outcome summary, Findings index page 1, each demo Site board, and the Site Findings page. The pre-flight lists them from DS-1f's `links` output; nothing is guessed.
- **Execution:** over HTTP against the running serve, not an in-process `TestClient` (BL-71: the in-process path doubled the connection pools and caused D-E5.47).
  - `--workers 4` by default. Newest ranges first, presets first of all.
  - Before each batch, it waits while `pg_stat_activity` is above 150.
  - A 503 or `stale` response is retried 2, 5 and 10 s later (D-E5.47 rule). A response that stays degraded fails the run with exit code non-zero.
- **Verify pass**, the same tool with `--verify`: it replays every URL and records the client-side time. Every request must be a store hit, and the maximum must be ≤2.0 s. It writes `warm-report.json` with per-request milliseconds, hit or stored, and total wall time.
- **Re-warm** after anything that moves the estate watermark: add-dates, a drain, the live dip, UP-1 and MB-1. The estate response key carries the estate-wide `cic:` count (D-E4.8), so **any new reading on any Site invalidates every stored estate page.** The measured re-warm time goes into the presenter notes. The estimate is 20-25 minutes with 4 workers; the first job measures it.
- **Tests (no DB):** the range enumeration (presets byte-equal to the frontend's, window edges, no range before a Site's first day), the worker throttle, the retry and degraded rules, and that `--verify` fails on one miss or on one request over 2 s.
- **Gate for merge:** on the VPS, with a prepared DB (client4, or the rehearsal DB when it exists): warm, then verify. The gate is 100% hits, maximum ≤2.0 s, 0 degraded, and re-warm wall time recorded. Fresh Claude reviewer.

**Also required for the demo build (SPEED-0, 0.1 units, coordinator checklist):** the final build's serve sets `ASSETOPS_PERIOD_READ_KINDS` to every kind whose parity passed on that build: the four `mini_depth.*`, `dispatch.day`, `evidence.claim`, and `money.lines` if it is IN. The prepare builds those rows. The VPS's first job is one cold timing of the unprepared Portfolio week on client4 (10 min), to replace the laptop's number.

### 7.2 Ask 2: "a super modern UI" (D-17N.2)

| | UQ-FI (rev 6, owner chose option 1) | Full plan (`architect-answer-ui-quality-2026-11-10.md`) |
|---|---|---|
| What | Inter, the 8-step type scale with a 12 px floor, the spacing scale on demo pages, one headline per demo page, repeated gap lines collapsed, the style ratchet | Stage 1 (3.5): three-tier tokens, 13 components, the chart standard, guards incl. axe. Stage 2 (4.5): page-by-page uplift of 7 page families, each from an owner-approved page mockup |
| Units | 1.9 | about 8.0, plus about 0.25 per page-family mockup |
| Mockups | the v7.2 sheet (built, `task/UQ-0-v72-sheet`, parked) | the sheet + 7 page-family mockups that **do not exist yet** |

- **Why the full plan cannot land by 17 Nov, even with 3 UI lanes:**
  - Stage 2 needs stage 1's components.
  - Each page family needs a mockup that you approve before its build (the standing mockup-first rule). None of the 7 is drawn.
  - All three lanes would edit the same shell, tokens and page CSS, so they collide.
  - Every demo page would change two days before the session, with no walkthrough slack. A mismatch with the mock is a High finding.
- **What can honestly be in, mockup-first, from the sheet you see after today's 14:00 demo:**

| Card | What | Units | Needs |
|---|---|---|---|
| UQ-FI-1, -2 | as rev 6 | 1.9 | sheet approval (type, Inter) by Fri 12:00 (rev 6) |
| **UQ-FI-3** (new) | **The one-figure Portfolio outcome card** that is already drawn on the v7.2 sheet: one figure, one sentence, the basis line, qualifiers behind "Why?". **The new status colours and symbols** for the six reading states (on the sheet), applied through one `StatusPill` used by the Portfolio and the board outcome rows. Light theme only | 0.75 | owner approves those two sheet panels for 17 Nov |

- **IN:** UQ-FI-1 and UQ-FI-2 as in rev 6.
- **IN-if:** UQ-FI-3, if you approve its two sheet panels by **Fri 09:00**. It goes in lane D after UQ-FI-1. It is held whole if it is not ACCEPTed by Sat 20:00, and it never holds UQ-FI-1/2.
  - Design: the card renders today's server fields only, so no new words. The figure is the outcome's existing headline value, the sentence its existing summary, and the basis its existing coverage line. Anything else moves behind the existing "Why?" disclosure.
  - `StatusPill` in `frontend/src/ui/StatusPill.tsx` maps the six existing state codes to the sheet's colour + symbol + word. It adds no `site_type` branch (hard-wiring ratchet).
  - Tests: one per state, and the Portfolio page test (one figure per card, the "Why?" content set unchanged).
  - Evidence: before/after captures in the UQ-FI capture run.
- **OUT for 17 Nov:**
  - the component library and catalogue (1.5) and the chart standard (0.75);
  - the dark theme and theme switch (0.5);
  - stage 2 for the Site board, Finding, lists, Financials, Work and Foundation pages (3.75 + mockups);
  - the axe pass.
- **Verdict:** "super modern" across the whole app is **OUT** (about 8 units plus 7 mockups). The demo path looks modern: new type, clean headlines, one gap line per section, and a modern Portfolio card. That is **IN / IN-if** (2.65 units), and each part rests on your sheet approval.

### 7.3 Ask 3: "all performance-related things" (D-17N.3)

| Item | What it does | Units | Verdict for 17 Nov | Why |
|---|---|---|---|---|
| AR-4 claim rows + both switches | Portfolio evidence on rows | committed | **IN** | built; parity after the D-ANY.10 merge is the gate (D-ANY.8) |
| money.lines (MN-1/2/3) | Portfolio potential money on rows; price save rebuilds them | committed | **IN-if** parity incl. price-save passes by Sat 12:00 | D-ANY.8 unchanged |
| DISP-1 | the 2.2 s of dispatch lookups | 0.3 | **IN** | largest known, unexplained cost; small |
| WARM-1 + SPEED-0 | ≤2 s on every clickable range (workaround) | 0.7 | **IN** | the only route to ≤2 s on the Portfolio by 17 Nov |
| BL-71 part 2 | prebuild over HTTP, not in-process | inside WARM-1 | **IN** | WARM-1 needs it; it avoids connection exhaustion |
| BL-ANY-absent | AR-2 kinds compose an absent row per run (as D-ANY.10 did for dispatch.day) | 0.5 | **IN-if** a lane is free after FR-B (Sonnet, lane A) | correctness on historical reads, not speed; the demo reads live or post-prepare k |
| `evidence.consequence_money` (ANY-3a) | the ~4 s money and provenance | 1.5 | **OUT** (backlog ANY-3) | new stored kind; serial after AR-4; cannot pass parity by the freeze |
| Remaining ~1.9 s (ANY-3b) | not profiled | 0.5-1.0 | **OUT** | unknown until S4 |
| `evidence.provenance` | Cold/EV pinned windows | ~0.5 | **OUT** | D-ANY.8 backlog; Cold/EV are already under 1 s |
| AR-5 | retire the pre-load list | 0.75 | **OUT** | it is the opposite of WARM-1; it only makes sense once every kind is stored |
| AR-7 | outcome rows from stored rows for 100+ Sites | 0.75 | **OUT** | invisible below about 25 Sites |
| BL-71 part 1 | one shared engine factory with a capped pool | ~0.5 | **OUT** | `max_connections 300` on the VPS covers 17 Nov |

- **Verdict:** every performance item that changes what the client sees by 17 Nov is IN or IN-if. "All" of them is OUT. ANY-3 (consequence money + the rest, about 2-2.5 units) is the honest remainder, and it is first in the queue after the demo.

### 7.4 Ask 4: "significant data coverage" (D-17N.4)

**Definition for 17 Nov.**
- On each demo Site, every board outcome row and every tab on the script path shows a figure, a dated event or a roadmap line (RM-1), not "Unknown", "Not known yet" or "No objective declared".
- Day coverage in the demo window is stated as it is:
  - Kobo: whole days;
  - Kisiwa: 6 pm to noon ("partly covered"), unless DATA-7;
  - Cold room: one recording session a day (D-E5.48);
  - EV depot: declared charging hours 08:00-16:00 (EV-HB).
- **Measure:** the count of visible gap lines per script page, from UQ-FI's `measure.json` (it already counts them). It is taken before and after.

**Already done:** PB-1a/b, PB-4, PB-7, DATA-1, DATA-2, DATA-6, DATA-11 + PB-3 (merged; EV charging graded by charger status, ordinary Cold/EV weeks), EV-HB, DATA-12, RM-1/RM-2.

| Item | Site | Visible effect | Units | Prepare cost | Approval | Verdict |
|---|---|---|---|---|---|---|
| DATA-5 | Cold, EV, Kisiwa | Health tab: 8 "Unknown" become gateway health values | 0.5 | small (health records) | no | **IN** |
| DATA-4 | EV depot | site diagram: connector rating and grid meter; removes "connector capacity not read" | 0.5 | none (configuration) | yes | **IN-if** approved by Fri 09:00; **an EV buyer is in the room** |
| DATA-8 | Kisiwa | productive loads (pump, cold store) + a price per kWh: the Grow card gains a figure | 0.5 | small | yes | **IN-if** approved by Fri 09:00 |
| DATA-10, DATA-13 | Kisiwa; story Actions | generator service plan; due dates on story Actions | 0.4 | none | no | **IN** (drops first if lane B runs late) |
| BL-48 | Kobo/Kisiwa | Grow lines on days without complete readings | 0.25 | none | no | **OUT** (partly addressed already; low) |
| FCF-1 (+BL-47) | Cold, EV | Findings card counts Cold/EV "awaiting verification"; Portfolio rows read "Action agreed" | 1.0 | none | no | **OUT** (no lane; the note it removes is honest) |
| DATA-7 | Kisiwa | whole simulated days instead of 6 pm-noon; removes "partly covered" on every Kisiwa day | 1.5 | **+15-25 min per prepare** (about +33% Kisiwa readings); all Kisiwa finish rows and story words re-proven | yes | **OUT**: it changes the diesel story's evidence two days before the session, with only the Saturday rehearsal to prove it. Presenter line: "this Site's logger records 6 pm to noon" |

- **Lane B, after PR-3's builder finishes (Fri evening):** DATA-5 → DATA-4 → DATA-8 → DATA-10/13, about 1.9 units, merging by Sat 20:00.
- **The Saturday-night rehearsal build is their gate:** the finish check must be green, as with the EV-HB gate. A failure reverts that merge before Sunday.
- **Verdict: IN / IN-if, about 1.9 units.** Every demo Site gains visible values: EV (Health, connector), Cold (Health), Kisiwa (Health, Grow figure, service plan). Kisiwa's partial days stay and are stated.

### 7.5 Ask 5: client data upload (D-17N.5)

**What exists (cited).**
- `field/assetops_field/export_csv.py` (TEL-06, merged `2599d34b7`): `CsvCollector` validates a whole file in the illustrative format `assetops-generic-interval-csv/1` (8 refusal codes), then admits it to a gateway over IPC and seals it.
- The profile is `field/profiles/generic-interval-csv-illustrative-1.json`: Kobo's PV and three feeder meters, 4 kW rows.
- TEL-06b (`host/tests/test_field_modbus_tcp_acceptance_postgres.py`) proved the path CSV → gateway → upload over TLS (`serve_tls`, port 8443) → **accepted evidence** for KOBO-001, on a test DB.
- The gateway uploads over the Batch path (`gateway/assetops_gateway/uploader.py`).
- **Not there:**
  - a browser file upload anywhere (no `type="file"` in `frontend/src`);
  - an API that takes a file from a person;
  - any mapping of unknown columns, any vendor format, and creating a Site from a file;
  - historical bulk import (BL-59) and the public upload path (BL-57) are backlog;
  - there is no sign-in (BL-54).

**What "upload" means for 17 Nov (UP-1, minimal and honest).**
- On **Kobo** (the only Site with a CSV profile), a site admin opens **Upload readings**. They download the template, choose a CSV in that format and see a dry-run preview: the period, the row count, each column matched to a meter, and the blanks. They confirm. The page then follows the readings through these states:
  - **Checked**;
  - **Sent**;
  - **Accepted** (n of m readings);
  - **Still processing**;
  - **Analysed**, which links to that day on the board.
- A refusal says which of the 8 file rules failed, in plain words. The whole file is refused, and nothing is admitted.
- A wrong unit is "held" at the gateway, as TEL-06 does, and the page says so.
- Attribution follows D-PRICE.1: "Uploaded by site admin". The entry service is server-configured; there is no signed-in person, and `HUMAN_PRINCIPAL_REQUIRED` is unchanged elsewhere.
- **Demo beat:** the presenter uploads a prepared file for the demo day's early hours (00:00 to one hour before the session). Kobo's board then shows that day analysed. The file is generated by `host/tests/field_observation_fixtures.py interval-csv`, extended with a `--day` option.
- **Not in UP-1:** any other format or Site, column mapping, corrections or re-uploads of days that already have readings, bulk history, a new Site.

**Technical design (pre-flight confirms the starred items).**
- Server, `POST /api/sites/{site_id}/reading-uploads?dry_run=true|false` (multipart, one file, ≤ 2 MB).
  - Steps: validate with `CsvCollector.reports` (no IPC); run the overlap rule; then admit it.
  - Overlap rule: refuse the whole file with `ALREADY_RECORDED` if any interval ends at or before the Site's latest accepted evidence for that role.
  - Admit through a **demo upload gateway**: a normal gateway process with its own provisioned credential, started by `tools/demo_combined.py serve` (the TEL-06a Bench start sequence*). Nothing new is admitted inside the API process, so the gateway stays the only way in.
- `GET /api/sites/{site_id}/reading-uploads/{upload_id}` returns the state above. "Still processing" ends when the serve tick drains and assesses that day*.
- New table `reading_upload` (id, site, file SHA-256, profile SHA-256, state, counts, refusal code, entered_by, timestamps). Migration number: the next free one.
- Words are server-side, through the UQ-6a message keys.
- Frontend: `/sites/:id/uploads`, reached from the Site's data or Health area*. **Mockup first:** one page in `frontend/mockups/v72/upload-readings.html` (0.25 units), shown to you with the v7.2 sheet tonight. Light theme, UQ-FI tokens.
- Tests:
  - no-DB: the 8 codes + `ALREADY_RECORDED` + too large + wrong Site + not Kobo; a dry run writes nothing;
  - Postgres flow on its own `*_test` DB: upload → accepted evidence → drain → that day assessed. The result is byte-equal to the same file admitted through the TEL-06b path.
- Gate: the flow test, the refusal table as tested, and a capture of the page in each state.

- **Units:** server 1.0, page 0.5 + mockup 0.25, flow and demo file 0.5 = **2.25**.
- **Risks:**
  1. **The watermark.** An upload moves the estate watermark, so every warmed page misses (7.1). The field beats therefore go **last in the script**. A Portfolio visit after them is unprepared, unless a re-warm has finished.
  2. **Time to "Analysed"** is a drain and an assessment, possibly minutes. The page states "Still processing" honestly. The flow test measures the time, and the script fills it.
  3. It is a new way in for data, without sign-in. It is reachable only on the demo build, behind `ASSETOPS_READING_UPLOAD_SITES=KOBO-001` (off by default).
- **Verdict: IN-if.**
  - You approve the one-page mockup by **Fri 09:00**.
  - Lane F starts the server half Thu 16:00 on the VPS; the server needs no mockup.
  - It merges in the **late window, by Sun 12:00** (7.8), behind its switch.
  - Not ACCEPTed by then: held, and the presenter shows the format and the TEL-06b proof on a slide.

### 7.6 Ask 6: Modbus (D-17N.6)

**What exists (cited).**
- `field/assetops_field/modbus_tcp.py` (TEL-02): a read-only client for function codes 01-04; any write is refused before a byte is sent.
- `field/assetops_field/modbus_poller.py` (TEL-04): the CLI that polls, aggregates and admits to the gateway.
- The GX-shaped emulator `field/tests/field_emulators/gx_server.py` (port 5020).
- Host proofs:
  - `host/tests/test_field_modbus_tcp_proof.py`;
  - `test_field_modbus_tcp_acceptance_postgres.py` (TEL-05/05b: accepted evidence, the assessment completes, Finding money withheld where it should be).
- **Not built:**
  - TEL-08: `host/tests/field_bench.py` has helpers only; `setup`, `activate` and `read` do not exist (section 0.5);
  - TEL-07: the runbook is parked on `task/TEL-07-claims-runbook`;
  - the BeagleBone's readiness is unknown (you have the SD card).

**What "Modbus in" means for 17 Nov.**
- **MB-1 (IN-if, 1.0 unit): live Modbus on the demo stack.**
  - The GX-shaped emulator replays Kobo's readings for the demo day at real time. The poller reads it over Modbus TCP and passes the readings to a gateway, which uploads them over TLS to the demo server. Kobo's **today** then fills on screen, and the Health tab shows the gateway's last upload.
  - Design: the TEL-08 `setup`, `activate` and `read` commands are built as specified in §TEL-08, and they also serve MB-1. `tools/demo_combined.py live-field --site KOBO-001 --from <session start>` starts the emulator, poller and gateway. It never writes an interval that UP-1's file covers (MB-1 starts after UP-1's span). A finish check confirms no overlapping (Site, role, interval).
  - Gate: TEL-05's gates on the demo DB copy: every upload receipt COMPLETED, accepted evidence for every role, and the day assessed. Plus a 5-minute uplink stop with the queue draining to 0 and no evidence gap.
  - Same watermark rule as UP-1: script beat last.
- **TEL-08 BeagleBone (IN-if, +0.5 unit on top of MB-1, plus one 1-hour heavy slot):** only if the board is reachable by **Fri 12:00**. That means SSH working, Debian 13 IoT, Python 3.13 and `NTPSynchronized=yes` (owner steps in section 0.5).
  - The poller and gateway run on the board and upload to the **VPS's** `serve_tls` on 8443. That is the realistic shape: an edge box uploading to the cloud. The VPS firewall opens 8443 to the board's public IP only.
  - **Shown as a recorded 2-minute clip and a claim line, not live in the room.** A live board adds the room's network and the clock to the session's risks.
- **Verdict:** MB-1 is **IN-if** it is ACCEPTed by the Sun 12:00 late window. The BeagleBone is **IN-if** the board is up by Fri 12:00; otherwise it stays OPTIONAL (section 0.5).

### 7.7 The recommended package (fits; D-17N.7)

| Lane (VPS from Thu 16:00) | Thu eve | Fri | Sat (core freeze 20:00) | Sun (late window to 12:00) |
|---|---|---|---|---|
| **C speed** (Opus) | AR-4: merge main, parity, timings | DISP-1, money.lines read side + Postgres | review by 12:00, merge by 16:00 | - |
| **A tools** (Opus, then Sonnet) | VPS set-up help; CLEAN-1 | **WARM-1** | FR-B trimmed; BL-ANY-absent if free | WARM-1 runs in the final build Mon |
| **B price + data** (Opus) | PR-3 frontend | PR-3 flow; then DATA-5 → DATA-4 → DATA-8 | DATA-10/13; merges by 20:00 | - |
| **D UI** (Opus, frontend only) | - | UQ-FI-1 (starts on your sheet approval), then UQ-FI-3 | captures, review, merge by 18:00 | - |
| **E UI** (Opus, frontend only) | - | UQ-FI-2 | as rev 6 | - |
| **F field** (Opus) | UP-1 server | UP-1 page (after mockup approval), flow test | MB-1 (+ TEL-08 if the board is up) | UP-1 + MB-1 review, merge by 12:00 behind switches |

- **New units:**

| Item | Units |
|---|---|
| DISP-1 | 0.3 |
| WARM-1 + SPEED-0 | 0.7 |
| UQ-FI-3 | 0.75 |
| DATA-5, -4, -8, -10/13 | 1.9 |
| UP-1 | 2.25 |
| MB-1 | 1.0 |
| **Total** | **≈ 6.9** (+0.5 for the BeagleBone, +0.5 for BL-ANY-absent if lanes allow) |

  With the 4.2 already committed, that is about 11 units. It sits at the measured rate's lower-middle, which is right for a week with a rehearsal build and a walkthrough.
- **Priority when anything clashes:** AR-4 > PR-3 > WARM-1 > UQ-FI-1/2 > UP-1 > MB-1 > DATA-5/4/8 > UQ-FI-3 > DATA-10/13 > FR-B > CLEAN-1 > BL-ANY-absent. Items drop from the right.
- **Heavy-job queue (one at a time):** AR-4 parity > money.lines parity > PR-3 flow > UP-1 flow > WARM-1 gate run > MB-1 bench (1 h) > the Sat-night rehearsal build (about 2 h 45).
- **Freeze, D-17N.7:**
  - The **core freeze stays Sat 20:00** for anything that changes existing reads, money, analysis or demo data: AR-4, PR-3, UQ-FI, DATA.
  - A **late window to Sun 12:00** is opened **only for additive, switched features**: UP-1 and MB-1, each off by default. WARM-1 is a tool and also merges by Sat 20:00.
  - After a Sun merge, the serve restarts on main against the rehearsal DB, with migrations applied. The 15:00 walkthrough then includes them. The Mon final build turns their switches on, and Monday's live checks cover them.
  - **Risk this adds:** UP-1 and MB-1 miss Saturday's full suite. Their proof is their own tests, the Postgres flow and Monday's live checks. If a Monday live check fails, the switch stays off and the presenter uses the slide fallback. Because they are switched off by default, they cannot break the existing pages.
- **Merge evidence (every item):** a fresh Claude reviewer ACCEPT, plus the per-item gate named above (parity, the WARM-1 verify, the flow tests, the before/after captures, the rehearsal finish check for DATA). Only High and Medium findings block.

**Alternative if you insist on everything (not recommended).**
- It adds:

| Item | Units |
|---|---|
| ANY-3 (consequence money + the rest), for ≤2 s computed live | 2.0-2.5 |
| DATA-7 | 1.5 |
| FCF-1 | 1.0 |
| Stage 1 components + charts | 2.25 |
| Stage 2 board, Finding and lists, with mockups | 2.5 |
| Dark theme | 0.5 |
| **Total** | **about +10 units, about 21 units in all** |

- **It does not fit even with the freeze moved to Mon 16 12:00.**
  - With that move, the most that fits is ANY-3, DATA-7 and FCF-1 (about +5 units).
  - The UI stages do not fit at any freeze: they need 7 page mockups and your approval of each first.
- **Risks the Mon 12:00 freeze adds:**
  - (1) no full suite before the final build;
  - (2) your Sunday walkthrough sees a build without most of it, so the demo shows work you never walked;
  - (3) the final build (about 3 hours) and live checks run Monday afternoon on an untested tree; a defect found Monday evening or Tuesday morning has no fix time;
  - (4) DATA-7 changes the Kisiwa story's evidence the day before the session;
  - (5) ANY-3 is a new stored money kind whose first full parity would run Monday morning. **Even then, ≤2 s computed live for a 31-day Portfolio is not certain.**

### 7.8 Changes to earlier revisions

- Rev 6, 6.5 "Nothing" pushed out and the priority line: replaced by 7.7's priority. FR-B and CLEAN-1 now sit below the owner's new asks.
- D-ANY.3 is reversed for the 17 Nov build only (WARM-1). D-ANY.4 is narrowed to "Custom ranges on the Portfolio".
- Section 0.5: the BeagleBone becomes IN-if (board up by Fri 12:00), uploads to the VPS, and is shown as a recorded clip.
- Section 2.1: DATA-5 and DATA-10/13 move to IN. DATA-4 and DATA-8 become IN-if approved by Fri 09:00. DATA-7 and FCF-1 stay OUT.

### 7.9 For the owner (the coordinator relays these)

1. **Why 2 s is not there yet:** the new machine runs more work side by side, but one page is still one sequence of work. Speed comes from storing each day's answer and proving it equal to the slow answer, and each proof caught real errors. The boards already open in under 2 s. The Portfolio is down to about 8 s for an unprepared week.
2. **≤2 s for *any* range, computed live, will not be ready by 17 Nov.** About 2.5 units of work remain, in sequence, and they would end Monday at the earliest with no guarantee.
3. **What you get instead: under 2 s on every range the date bar offers,** and every 7, 14, 30 and 31-day range in the demo data, because the demo machine prepares them ahead. This is a workaround, and we call it one. Only hand-typed custom dates on the Portfolio still take 8-30 s.
4. **Modern UI for 17 Nov:** the new font and type sizes, clean page headlines and fewer repeated "not available" lines (as you chose), **plus** the modern one-figure Portfolio card and new status colours from the same sheet, if you approve them by Fri 09:00. A full redesign of every page (about 8 units plus 7 page mockups) comes after 17 Nov.
5. **Data coverage:** Health values for Cold, EV and Kisiwa, the EV connector and grid meter, Kisiwa's productive loads with a figure, and Kisiwa's service plan. Please approve DATA-4 and DATA-8 by Fri 09:00. Kisiwa's 6 pm-to-noon days stay as they are and are stated.
6. **Client data upload: in, in a first honest form.** Upload a CSV of a Site's readings in our standard format on Kobo, see it checked, accepted and analysed on the board. One page mockup comes to you tonight with the v7.2 sheet. Other formats, column mapping and history import come after 17 Nov.
7. **Modbus: in, live on the demo machine.** A device emulator is read over Modbus, and the readings flow through the gateway into Kobo's today. The BeagleBone joins as a recorded clip if it is reachable by Fri 12:00.
8. **Freeze:** the core stays at Sat 20:00. Upload and Modbus may merge until Sun 12:00, switched off by default, so they cannot break the rest. You see them at the Sun 15:00 walkthrough.
9. **Upload and Modbus go last in the script.** New readings make the system refresh the prepared ranges, which takes about 20-25 minutes (estimated, to be measured).
10. **If you want everything:** it is about 21 units. It does not fit even with the freeze moved to Monday noon, and that move would leave no tested build and no fix time before Tuesday. I recommend against it.

### Dispatch briefs (revision 7)

- **DISP-1** (lane C, on AR-4). First the S1 profile after the merge of main. Then the cause of the four `select_dispatch_days_on` calls. Fix on AR-4 only if it is ≤0.3 units and inside AR-4's files; otherwise report to the Architect. **Update D-ANY.11:** the cause is `for_finding_on` (money eligibility); fix on `fix/DISP-1-money-eligibility` off main, 0.25 units, IN, parity and timings after AR-4 merges.
- **WARM-1** (lane A, Opus, wt `AssetOpsV1-warm1`, branch `task/WARM-1-range-warm`). Spec 7.1. Pre-flight, in one batch: the exact query strings the bar sends per preset, its day boundary, and the route list per page from DS-1f `links`.
- **UQ-FI-3** (lane D after UQ-FI-1). Spec 7.2 + the two approved sheet panels. Starts only on approval.
- **DATA-5/-4/-8/-10/13** (lane B after PR-3). Specs in section 2.1 and the W-11 rulings. DATA-4 and DATA-8 start only on approval. Each changes producer data, so each merge is gated by the Sat-night rehearsal finish check.
- **UP-1** (lane F, Opus, wt `AssetOpsV1-up1`, branch `task/UP-1-reading-upload`). Spec 7.5. Thu: server and no-DB tests. Pre-flight: the TEL-06a gateway start sequence, how the serve tick drains an upload, and the Site page that links to it. The mockup page goes to the coordinator by Thu 20:00.
- **MB-1** (lane F after UP-1's server, Opus, branch `task/MB-1-live-modbus`). Spec 7.6 + §TEL-08. The bench run uses its own `*_test` DB copy, never the rehearsal DB.

## Revision 6 (Architect, Claude, 2026-11-12): UQ-FI, a first-impression UI pass for 17 Nov

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (since 2026-10-27).
- Owner, verbatim (`.agent/owner-ui-first-impression-2026-11-12.md`): "option 1, show me the design sheet after the demo". Option 1 = UQ-1-level type, spacing and Inter across the app, plus one headline per demo page and repeated "not available" lines collapsed to one per section; own lane from Fri; starts only after the owner approves the parked v7.2 sheet; held whole if not ACCEPTed by Sat 20:00.
- Supersedes revision 3's "UQ-1 out" line for this subset only. UQ-0's other parts, UQ-2 (dark), UQ-3, UQ-4 and UQ-5..8 stay in the backlog (BL-69). Rulings **D-UQFI.1-5** below, logged for owner review.
- Basis: `.agent/architect-answer-ui-quality-2026-11-10.md` problems 1-3 (type, no headline, honesty wording crowding the page). Problems 4 (charts) and 5 (i18n) are not touched.

### 6.1 Scope: UQ-FI, 1.9 units (D-UQFI.1)

| Card | What | Units |
|---|---|---|
| UQ-FI-0 | One extra panel on the v7.2 sheet, "One headline, one gap line per section": a before/after of the Kobo Finding header and the Cold board's empty lower half, drawn from today's words. Optional; only if it can reach the owner with the sheet tonight | 0.1 |
| UQ-FI-1 | (a) Tokens across the whole app: the 8-step type scale, a 12 px floor, 14 px body, Inter self-hosted, tabular figures, the 4 px spacing scale (tokens defined; snapped only on demo-path files); every raw `font-size` in `frontend/src` moved onto the scale by a committed codemod; the style ratchet | 0.9 |
| UQ-FI-2 | (b) Demo-path pages only: one headline per page; repeated gap lines collapsed to one per section through one shared component | 0.7 |
| Evidence | Before/after captures of every demo-path page at 1440 and 1280 px, with measurements; packet | 0.2 |
| **Total** | | **1.9** (1.8 without UQ-FI-0) |

**Rules that bound it:**
- Light theme only (today's colours). English only.
- No layout restructure: no grid, column or panel moves, no new panels, tabs or controls, no new charts, no new words. Two moves only: the headline element goes first in its page header, and a section's repeated gap lines become one line.
- Gap wording keeps D-E5.46: the fact is stated once per section, with every subject it applies to named; never hidden, softened, re-worded or merged across different facts.
- Tables, the Portfolio outcome matrix and tab rows are out of the collapse: each cell and each "Label · Not available yet" tab keeps its own words (collapsing them would change layout).

**Demo-path pages (from DS-1f `demo-script-client.html` checklist and DS-1b; both are on branch `task/DS-1f-fill`, not on main):**

| # | Page (frame) | Script step | Headline (existing text, moved first; nothing new) |
|---|---|---|---|
| P1 | Portfolio, all tabs (`EstatePortfolioFrame`) | 0, 1 | page title "Portfolio" + its existing subtitle sentence |
| P2 | Site board / Overview, Kobo, Cold room, EV depot, Kisiwa (Site board frame under `SiteDetailFrame`) | 2, 3, 3b, 4, 5, K, 7 | Site name + the board's day line |
| P3 | Finding detail: Kobo generator, Kisiwa unexplained fuel (incl. `SiteFuelFindingFrame`) | 2, K | the Finding's title (what happened), then its first sentence; the "Priority · Confidence · Earlier version n of m" line moves under them |
| P4 | Verification ("check") pages: Kobo ACT-001, Kisiwa ACT-004 (`SiteMillVerificationFrame`, `SiteFuelVerificationFrame`, or the action verification frame the pre-flight confirms) | 2, K | the page title; the verdict chip stays in the header |
| P5 | Daytime solar opportunity page | 3 | "Daytime solar unused at Kobo mini-grid" |
| P6 | Findings index, all lenses and the Opportunities tab (`EstateFindingsFrame`); Kisiwa Site Findings | 3, 6, K | "Findings across the estate" / the Site Findings title |
| P7 | Kisiwa Fuel night page; Kisiwa Service page; Operational records (live dip) | K | each page's title |
| P8 | Maintenance (optional step 4); Site price page (PR-2a/PR-3, if merged; demo beat 5.4 #10) | 4, price beat | page title; tokens only, no collapse work on the price page |

### 6.2 What the owner approves on the v7.2 sheet for UQ-FI (the coordinator presents these, in plain words)

1. **Inter** becomes the app's font, stored with the app (no internet needed), with the computer's own font as fallback; numbers in tables and money line up (tabular figures).
2. **Type sizes:** one scale of 8 sizes (12, 13, 14, 16, 18, 20, 24, 30 px); nothing smaller than 12 px; normal text 14 px.
3. **Headings:** page titles 24 px (today 27), section titles 16 px (today 15). Table text 13 px with 12 px column heads, and table rows keep today's height; the sheet's taller 44 px rows come after 17 Nov.
4. **Spacing:** the sheet's 4 px spacing steps, applied to the demo pages only.
5. **Colours stay as today, light theme only.**
6. **Left menu:** same items and order; group names 12 px (today 9 px), items 13 px.
7. **Not on the sheet, approved as a rule (or from the UQ-FI-0 panel):** one headline per demo page, and a repeated "not available / not assessed / no assessment" line said once per section, naming everything it applies to. You see the before/after pictures on Saturday.
8. **Not for 17 Nov (after the demo, from the same sheet):** the dark theme and the System/Light/Dark switch, the new colour palette, the reading-state colours and symbols, the outcome-category colours, new corners and shadows, the one-figure outcome card, taller table rows, and the French and Swahili samples.

### 6.3 Technical design (builders do not design)

**D-UQFI.2 Type scale and mapping.**
- New file `frontend/src/ui/fonts.css`, imported in `main.tsx` **before** `ui/tokens.css`:
  - `@font-face { font-family: "Inter"; src: url("/fonts/InterVariable.woff2") format("woff2-variations"), url("/fonts/InterVariable.woff2") format("woff2"); font-weight: 100 900; font-style: normal; font-display: swap; }`.
  - Files: `frontend/public/fonts/InterVariable.woff2` and `frontend/public/fonts/OFL.txt`, from the rsms/inter v4.1 GitHub release zip (fetched on the VPS). The packet records the release URL and the SHA-256 of both files. No CDN at runtime, no npm dependency.
- `ui/tokens.css`, primitive tier (new):
  - `--font-size-100: 0.75rem` (12), `-200: 0.8125rem` (13), `-300: 0.875rem` (14), `-400: 1rem` (16), `-500: 1.125rem` (18), `-600: 1.25rem` (20), `-700: 1.5rem` (24), `-800: 1.875rem` (30).
  - `--space-1: 4px` … `--space-2: 8px`, `-3: 12px`, `-4: 16px`, `-5: 20px`, `-6: 24px`, `-8: 32px`, `-10: 40px`, `-12: 48px`, `-16: 64px`.
  - `--font-sans: "Inter", system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif;` `--font-mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;` `--leading-body: 1.5`.
- Existing role tokens are **re-pointed, not renamed** (no call-site churn):

| Token | Today | UQ-FI |
|---|---|---|
| `--text-xs` | 11 | `--font-size-100` (12) |
| `--text-sm` | 13 | `--font-size-200` (13) |
| `--text-base` | 14 | `--font-size-300` (14) |
| `--text-lg` | 17 | `--font-size-400` (16) |
| `--text-xl` | 22 | `--font-size-600` (20) |
| `--text-2xl` | 28 | `--font-size-700` (24) |
| `--text-page-title` | 27 | `--font-size-700` (24) |
| `--text-panel-title` | 15 | `--font-size-400` (16) |
| `--text-subsection-title` | 13 | `--font-size-300` (14) |
| `--text-panel-note` | 11 | `--font-size-200` (13) |
| `--text-table` | 11 | `--font-size-200` (13) |
| `--text-table-head` | 9 | `--font-size-100` (12) |
| `--text-cell-secondary` | 10 | `--font-size-100` (12) |
| `--text-tab` | 12 | `--font-size-300` (14) |
| `--text-subtab` | 11 | `--font-size-200` (13) |
| `--text-rail` | 12 | `--font-size-200` (13) |
| `--text-rail-eyebrow` | 9 | `--font-size-100` (12) |

- `body` (in `ui/primitives.css`): `font-size: var(--text-base); line-height: var(--leading-body); font-family: var(--font-sans);`. Tabular figures: `font-variant-numeric: tabular-nums` on `table`, money and figure classes (`.money`, `[data-figure]`, card figure classes; the pre-flight lists the exact selectors).
- **Codemod** `tools/uqfi-type-codemod.mjs` (committed, idempotent, rerun by any branch that merges after it). Over `frontend/src/**/*.css` except `ui/tokens.css` and `ui/fonts.css`, each `font-size` value becomes a role or primitive variable:
  - any px value ≤ 12 (7, 8, 9, 9.5, 10, 10.5, 11, 12), `0.75rem`, `var(--text-xs, …)`, `var(--font-size-sm, 0.85em)` → `var(--font-size-100)`;
  - 13 px, `0.8125rem` → `-200`; 14 px, `0.875rem` → `-300`; 15, 16 px, `1rem` → `-400`; 17, 18, 19 px → `-500`; 20, 22 px → `-600`; 23, 24, 25, 27 px → `-700`;
  - an existing `var(--text-*)` stays (its token was re-pointed); `inherit`, `1em` and `100%` stay;
  - a fallback inside `var(…, x)` is dropped;
  - any value it cannot map is printed and fails the run (the builder maps it by this table's nearest-step rule, ties go up, and adds it to the script).
  - The one inline `fontSize` in TSX (outside tests) uses the variable.
  - Monospace literals (`Consolas, monospace`, `ui-monospace, …`) become `var(--font-mono)`.
- **Spacing, demo-path files only:** padding, margin and gap px values in the CSS files the P1-P8 frames load are snapped to the nearest `--space-*` (ties down, so nothing grows by more than 2 px); 1 px and 2 px hairlines stay. Other files keep their values (the ratchet does not count spacing for 17 Nov).

**D-UQFI.3 Style ratchet (shrink-only), `tools/checks/style-ratchet.mjs`.**
- Same contract and code shape as `frontend-hardwiring.mjs`: per-file counts compared with `tools/checks/fixtures/style-ratchet-baseline.json`; any cell above baseline fails; a file outside the baseline counts from 0; the baseline changes only by `--shrink` (refused while any cell has risen); `--print` shows counts.
- Scan: `frontend/src/**/*.css` and `frontend/src/**/*.tsx` (not `__tests__`), excluding `ui/tokens.css` and `ui/fonts.css`. Cells per file:
  - `rawFontSize`: `font-size` values that are not `var(--text-*)`/`var(--font-size-*)`/`inherit`/`1em`/`100%`, plus inline TSX `fontSize`;
  - `rawFontFamily`: `font-family` not `var(--font-*)` or `inherit`;
  - `rawHex`: hex colour literals.
- **Wall, not ratchet (whole tree, tokens.css included):** any font-size resolving below 12 px fails. After the codemod, `rawFontSize` and `rawFontFamily` are 0 in every file, so those two baselines hold no rows; `rawHex` gets today's per-file counts (to shrink later, stage 1).
- `tools/checks/test_style_ratchet.mjs` (node test, like `test_frontend_hardwiring.mjs`): a rise fails, a new file counts from 0, `--shrink` refused on a rise, the 12 px wall, the allowed relative values.
- Wire into `tools/check-all.ps1` beside the hard-wiring guard: `Invoke-Guard "Style ratchet (UQ-FI)" $Node @("tools/checks/style-ratchet.mjs")`.

**D-UQFI.4 One headline, one gap line per section.**
- **Headline:** each P1-P8 page has exactly one `h1`, rendered through `PageHeader` (or `V69Layout`'s title slot) at `--text-page-title`, and it is the headline text in the 6.1 table. No other element on the page uses `--text-page-title` or a larger size. Elements that are visually headline-sized today (outcome row titles, card titles) drop to `--text-panel-title`. On P3 the status line moves below the title and first sentence; nothing is removed.
- **Gap grouping**, new `frontend/src/ui/gapGroup.ts` (pure) and `frontend/src/ui/GapGroup.tsx`:
  - `groupGaps(items: GapItem[]): GapGroupLine[]`, where `GapItem = { subject: string; fact: string; reason?: string; gapId?: string }` and `GapGroupLine = { fact: string; reason?: string; subjects: { subject: string; gapId?: string }[] }`.
  - Group key is `(reason ?? fact)` with exact string equality on `fact`; different facts or reasons never merge. Lines keep D-E5.46 precedence order (no readings, conflicting, not enough, not analysed yet, still processing), then other facts in first-seen order. Subjects keep their original order.
  - A group with one subject renders exactly as today (no change for single gaps).
  - `<GapGroup items={…} />` renders one `<p class="gap-group">` per line: `<span class="gap-group__fact">{fact}</span>` followed by `<ul class="gap-group__subjects">` with one `<li data-gap-id={gapId}>{subject}</li>` per subject (separators in CSS). The words are the server's or the page's existing words; the component concatenates no strings.
  - A section is one panel or card. Grouping never crosses sections. Where every block of a section says only a gap (for example the Cold board's lower-half cards "No cold assessment for this window"), those blocks become one `GapGroup` line in that section, naming each block's title as a subject.
  - Where the gap words come from `MissingClaim`, the subject `<li>` renders `MissingClaim` for that gap, so `missing-claim-scan.mjs` and the gap ids still see every gap.
- Site-type agnostic: no `site_type` or outcome-id branch (hard-wiring ratchet). Words never composed from codes.
- Collapse targets the pre-flight confirms on the live pages (at least): the Finding header's "Priority: not assessed · Confidence: not assessed"; the Cold board's four "No cold assessment for this window" cards; repeated "Not available yet"/"Unknown"/"not worked out yet" lines inside one Portfolio card or one board outcome row. Not: tables, the outcome matrix, tab rows, lens chips.
- **MOCK DEVIATION:** the type sizes need no label once the owner approves the sheet (the v7.2 sheet replaces the v6.9 type scale for what it covers). Each collapsed section carries a MOCK DEVIATION label citing D-UQFI.4 unless the UQ-FI-0 panel is approved (then it cites the sheet).

**Tests.**
- Frontend (vitest, named files only):
  - `ui/__tests__/gapGroup.test.tsx`: grouping by fact; different reasons never merge; D-E5.46 order; subject order; a single gap unchanged; gap ids preserved on every subject; no text composed (fact and subjects appear as separate nodes).
  - One test per P1-P7 frame (added to its existing test file, named in the pre-flight): exactly one `h1`, with the headline text; the set of gap ids and gap facts on the page is the same before and after (no gap lost).
  - `ui/__tests__/tokens.test.ts`: every `--text-*` and `--font-size-*` resolves to ≥ 0.75rem; `main.tsx` imports `fonts.css` before `tokens.css`.
  - Existing tests that assert removed duplicate lines are updated; each is listed in the packet with the reason.
- Guards: style ratchet (new), hard-wiring, missing-claim, mock-deviation labels, architecture check.
- **Visual evidence (required for review)**, new `tools/uqfi-captures.mjs`, the CDP approach of `tools/layout-evidence.mjs` (no new dependency):
  - `capture <links.json> <out-dir> [web-base] --widths 1440,1280` takes full-page PNGs of every P1-P8 URL (the DS-1f links output for the chosen DB) into `Docs/demo-sprint/uqfi-img/{before,after}/{nn}-{page}-{width}.png`.
  - Per page and width it records in `measure.json`: the smallest computed font-size of visible text (must be ≥ 12), page-level sideways scroll (must be none), the `h1` count (must be 1 after), the count of visible gap-fact lines before and after, and whether Inter is the rendered font (`document.fonts.check`).
  - **Before** captures from main at the lane's start, **after** from the branch; same DB, same serve, same URLs, light theme.
  - Also measured, no picture: sideways scroll at 390 px on P1-P3 (no regression).
- Packet: the codemod output (counts per file), distinct font-size values before and after (62 strings today, target the 8 steps plus `inherit`/`1em`/`100%`), the ratchet baseline, font SHA-256, the before/after index (an HTML page pairing the pictures), and the list of collapsed sections per page.

**D-UQFI.5 Collisions with work merging this week.**
- **Already merged** (PF-T, PF-C/PF-W, SR-1, SR-2, SR-2b, C1, PB-1c): UQ-FI is cut from main after them; nothing to do.
- **PR-2a / PR-3** (`sites/SitePrices.tsx`, `sitePrices.css`, `priceAction.css`, the PR-3 form):
  - From now, PR-2a and PR-3 CSS uses `var(--text-*)` only, no px font sizes (the coordinator relays this to both builders today).
  - Whichever merges first, the other rebases. If PR-2a/PR-3 merges first, UQ-FI reruns the codemod and the ratchet after the rebase and retakes the P8 price-page capture. If UQ-FI merges first, PR-3 runs the codemod on its own CSS and must pass the ratchet (new files count from 0).
  - UQ-FI does no collapse or headline work on the price page and does not touch PR-3's TSX.
  - Sat order: PR-3 merges first if ACCEPTed by 15:00; otherwise UQ-FI merges first (by 18:00) and PR-3 rebases.
- **AR-4:** backend only, no collision. If AR-4 changes a server word that a P-page groups, the grouping still works (exact fact match), and the before/after gap-count check in `measure.json` shows any change.
- **Any other branch merging after UQ-FI** that touches frontend CSS reruns the codemod and passes the ratchet.

### 6.4 Lane and order

| When | What |
|---|---|
| Thu evening (after the 14:00 demo) | The coordinator shows the owner the sheet with the 6.2 bullets (+ the UQ-FI-0 panel, if a Sonnet builder adds it on `task/UQ-0-v72-sheet` by then). |
| Fri 07:00, VPS | **Starts only on owner approval.** Lane D: UQ-FI-1, Opus, branch `task/UQ-FI-1-tokens` from main. First job: the before captures (one serve, read-only, the DB the coordinator names; not beside AR-4 parity). Then tokens, Inter, codemod, ratchet. |
| Fri 09:00, VPS | Lane E: UQ-FI-2, Opus, branch `task/UQ-FI-2-declutter`, stacked on UQ-FI-1's first commit (its logic and tests do not depend on token values). Pre-flight first: the frames, test files and collapse targets per page, in one batch. |
| Fri ~20:00 | UQ-FI-1 done; UQ-FI-2 rebases onto it. Rebase onto PR-2a if merged. |
| Sat 08:00 | After captures, `measure.json`, packet; both branches reviewed as one diff by one fresh Claude reviewer. |
| **Sat 14:00** | Review verdict. Sonnet fix round and re-review follow. |
| **Sat 18:00** | Merge, UQ-FI-1 then UQ-FI-2, together. |
| **Sat 20:00** | Not ACCEPTed → **held whole**, both branches unmerged. 17 Nov uses today's look; Saturday's suites and Sunday's recapture run on today's look. |

- **No approval by Fri 12:00:** UQ-FI does not start and returns to BL-69. There is not enough time left for a build and a review.
- Saturday's suites (from 20:00) and Sunday's recapture and DS-1f picture refresh then run on whatever look merged. The recapture is light theme only.
- VPS jobs: captures are one serve and one Chrome at a time, never beside a Postgres parity run or a prepare. UQ-FI needs no Postgres.

### 6.5 What it pushes out

- **Nothing.** Lanes A (CLEAN-1, FR-B trimmed), B (PR-2a, PR-3) and C (AR-4) stand as in 5.5. UQ-FI takes lanes D and E on the VPS, which has room for 4-5 lanes.
- What it costs instead: Saturday review load (AR-4, PR-3 and UQ-FI all reviewed Sat; separate fresh reviewers), and the VPS RAM during the before and after captures.
- **If they clash, priority:** AR-4 > PR-3 > UQ-FI > FR-B > CLEAN-1. FR-B drops first, as already ruled.

**Risks, stated plainly.**
1. **Bigger type breaks fits.** 11→13 px table text and 9→12 px heads can push a wide table (the Findings index was fitted at desktop width in W1-F5b) into sideways scroll at 1280 px. The fix is wrapping inside the cell, never a size under 12 px and never a layout change; `measure.json` catches it.
2. **The codemod touches 37 CSS files.** Snapshot and text tests that read CSS may fail. Only CSS-reading tests should change; any other failing test is a defect, not a golden to update.
3. **Owner approval is the gate.** If it slips past Fri 12:00, UQ-FI is off for 17 Nov.
4. **Collapse can hide a fact by accident.** The gap-id and gap-fact set test per page and the before/after counts guard it; a lost gap is High in review.
5. **DS-1f pictures** are from the old look. If UQ-FI merges, Sunday's recapture refreshes them (already planned); if held, nothing changes.

### Dispatch briefs (revision 6)

**UQ-FI-1 tokens, type, Inter, ratchet.** Opus. VPS wt `AssetOpsV1-uqfi1`, branch `task/UQ-FI-1-tokens` from main. 0.9 unit plus the before captures. Spec: 6.1, 6.3 (D-UQFI.2, D-UQFI.3), the approved v7.2 sheet (type section), 6.4. Pre-flight: unmappable font-size values, the money/figure selectors for tabular figures, the demo-path CSS file list. Vitest and node tests on named files only.

**UQ-FI-2 headline and gap lines.** Opus. VPS wt `AssetOpsV1-uqfi2`, branch `task/UQ-FI-2-declutter` stacked on UQ-FI-1. 0.7 unit plus the after captures and the packet (0.2). Spec: 6.1 page table, 6.3 (D-UQFI.4), D-E5.46. Pre-flight: per page, the frame, the test file, and the exact sections and lines to group, in one batch, before code.

## Revision 5a (Architect, Claude, 2026-11-12): order of the remaining any-range speed work

- Ruling **D-ANY.8** (`build-sheet-OWN-GAPS-2026-11-08.md`). Lanes and the freeze in 5.5 are unchanged.
- **Order:**
  1. AR-3 + AR-6 merge as they are.
  2. AR-4 rebases onto main (it does not merge the AR-3 branch) and switches `evidence_money.mini_grid_rows` to `coverage.dispatch_days`.
  3. money.lines (MN-1/2/3, with the PR-3 price-save refresh) is built meanwhile, code and no-DB tests first.
  4. evidence.provenance goes to the backlog.
- **AR-4 minimum for 17 Nov:** claim rows + the switch. money.lines is IN only if its parity passes by Sat 12:00; otherwise it moves to `task/ANY-2-AR4b`. The ≤2 s target is reported, not gated.

## Revision 5 (Architect, Claude, 2026-11-12): price entry back IN, saved as "Entered by site admin"

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude (since 2026-10-27).
- Owner, verbatim (`.agent/owner-price-entry-in-scope-2026-11-12.md`): "yes, price entry in scope as site admin"
- Supersedes revision 4's "PR-3 out" line only. AR-3+AR-6, AR-4, PR-1 and PR-2a stand as written. The attribution rule is **D-PRICE.1** (`build-sheet-OWN-GAPS-2026-11-08.md`).

### 5.1 What PR-3 is for 17 Nov (scope ruling)

- **IN:** a price form on the Site price page that saves one of the **three stored keys** (`diesel_price_per_litre`, `ev_gross_tariff_per_kwh`, `productive_use_price_per_kwh`, `financials/assumptions.py:30`), recorded as "Entered by site admin". It uses the dip-form precedent, and the same entry service and switch.
- **OUT of PR-3, kept out:**
  - New keys (`repair_visit_cost`, `planned_service_cost`, `charger_repair_cost`, `interrupted_session_cost`, `stock_value_at_risk`). No figure reads them. Saving one would change nothing on screen, and the page would then say something untrue ("the figures update once it is set"). Early warnings carry no money today (`test_out_c1_never_money`), so pricing a warning is a new money consumer, not a form.
  - Roles, sign-in and the human route. `POST /financial-assumptions` stays refused (`HUMAN_PRINCIPAL_REQUIRED`), and its tests are unchanged.
  - The "N figures change" preview count.
- **PR-4: not needed.** The recalculation path already exists:
  - a revision insert raises `price.revised` in `event_outbox` (trigger, migration `0044_chain_events.py:57-60`; register `config/chain/event-register-v1.yaml:13`, `by_assumption_key`);
  - diesel and EV publications queue consequence work (0011/0026 triggers);
  - the demo serve's tick (every 120 s, `tools/demo_combined.py:23`) drains `consequence`, `ev_consequence` and `chain_snapshots`;
  - affected figures read the existing `PENDING_RECOMPUTE` "Updating…" until then;
  - the productive-use price is read at request time (0040), so it shows at once.
  "Priced on" and "Restated on" notes (BL-67c) stay out.
- **PR-5: not needed** for a stored key; stays out.
- **Owner option, not the default (needs sign-off and pushes FR-B out): PR-3b, "price the visits warning", +0.75.** It adds the key `repair_visit_cost` (migration and unit), a priced part on REPEATED ("3 visits × 120 USD (your price)", never summed with the open part), and a ruling that relaxes never-money for that one warning. Only if the owner asks.

### 5.2 Where the dip form writes and how it is attributed (precedent, cited)

- Route: `POST /api/sites/{site_code}/work/operational-entries` (`backend/assetops_backend/work_api.py:198-216`).
- Actor: the server-configured entry service `ENTRY_PRINCIPAL = "service:operator-entry"` with attestation `service=operator-entry;job=site-admin-entry;rule=oprec-entry/1` (`backend/assetops_backend/work/operational_entry.py:25-27`). The browser never sends an actor.
- Switch: `ASSETOPS_OPERATIONAL_ENTRY=on`, read in `host/lab_app.py:77-97` (`operational_entry_from_environment`) and injected as `operational_entry_principal` (`main.py:248, 627`). The demo serve sets it (`tools/demo_combined.py:779`).
- Label: `OPERATOR_ENTRY_LABEL = "Entered by site admin"` (`frontend/src/work/OperationalRecords.tsx:89-90`; owner Q3, build sheet §3.1 line ~686).

### 5.3 PR-3 technical design (builders do not design)

**Server constants (new, in `financials/assumptions.py`):**
- `SITE_ADMIN_CHANNEL = "SITE_ADMIN_ENTRY"`; `SYSTEM_CHANNELS` becomes `("SYSTEM_CLI", "SYSTEM_FIXTURE", "SITE_ADMIN_ENTRY")`.
- `SITE_ADMIN_PRICE_PUBLISHER = SystemPrincipal(actor_id="service:operator-entry", authorization_basis="SITE_ADMIN_ENTRY: entered on screen through the server-configured entry service, labelled 'Entered by site admin'; no signed-in person (D-PRICE.1)", actor_kind="SYSTEM")`. The actor id is `ENTRY_PRINCIPAL` imported from `work/operational_entry.py`, not retyped.
- Provenance on every entry: `{"service": "operator-entry", "job": "site-admin-price-entry", "rule": "price-entry/1"}`, plus `"entry_note": <reason>` only when a reason is sent for a non-correction (below).

**Migration (next free number; `0060_site_admin_price_entry` expected).**
- Widen the `financial_assumption_revision` channel CHECK to `('SYSTEM_CLI','SYSTEM_FIXTURE','HUMAN_API','SITE_ADMIN_ENTRY')`. Guard on the installed constraint name, as 0040 does.
- The actor CHECK (`0010:76-78`) is unchanged and still holds: SYSTEM actor, no `author_id`, channel ≠ `HUMAN_API`.
- Downgrade refuses while any row has channel `SITE_ADMIN_ENTRY`, then restores the 0010 CHECK.
- No new table. If AR-4 or another branch takes the number first, whoever merges second renumbers and re-chains `down_revision`.

**Route.** `POST /api/sites/{site_code}/financial-assumptions/entries`, in `financial_api.py` `build_financial_assumption_router`. New keywords: `entry_principal: Principal = no_service_principal` (the same injected `operational_entry_principal`, so the one switch `ASSETOPS_OPERATIONAL_ENTRY` covers dips and prices), `store` (the assumption store or None), `site_zone` (`(tenant_id, site_id) -> ZoneInfo`, using the Site time-zone lookup that `entry_site_context` uses) and `read_access` (the price read's access). The existing human route is untouched.

Request, a closed JSON object; any other key gives 422 `PRICE_ENTRY_INVALID` with `fields`:

```json
{"key": "diesel_price_per_litre" | "ev_gross_tariff_per_kwh" | "productive_use_price_per_kwh",
 "value": "1.45", "currency": "USD",
 "basis": "AUTHORED_ESTIMATE" | "CONTRACT_RATE" | "RECORDED_PURCHASE",
 "source": "Supplier contract SC-88", "applies_from": "2026-11-10",
 "reason": "Contract rate replaces the estimate" | null,
 "dry_run": false, "idempotency_key": "price-entry-<32 lowercase hex>"}
```

Refusal order (fixed and tested); every refusal is `{"detail": {"code", "message"}}` and nothing is written:
1. 404 when `scope(site_code)` is None.
2. 403 `SITE_SCOPE_FORBIDDEN` from `read_access`.
3. 403 `PRICE_ENTRY_OFF`, "Saving prices is switched off on this server.", when `entry_principal` is None.
4. 422 `BODY_NOT_JSON`.
5. 422 `CLIENT_ACTOR_FORBIDDEN` (the existing `_client_actor_fields`).
6. 422 `PRICE_ENTRY_INVALID` for shape:
   - `key` one of the three;
   - `value` matches `^[0-9]{1,6}(\.[0-9]{1,4})?$` and is > 0;
   - `currency` in `ISO_4217`;
   - `basis` one of `BASES`;
   - `source` 1-120 characters after trimming, with no control characters;
   - `applies_from` an ISO date;
   - `reason` null or 1-200 characters;
   - `dry_run` a boolean, optional (default false);
   - `idempotency_key` matches `^price-entry-[0-9a-f]{32}$`.
7. 422 `PRICE_KEY_NOT_ENTERABLE` for a known future key (the PR-1 `PRICE_NOUN` keys outside `STORED_KEYS`): "No figure uses this price yet, so it cannot be saved here."
8. 503 `ASSUMPTION_STORE_UNAVAILABLE` when there is no store.
9. Derivation (below), then 422 `APPLIES_FROM_OUT_OF_RANGE`, `CURRENCY_DIFFERS` or `REASON_REQUIRED`.
10. The store's own `PublicationRefused` status and code pass through unchanged (409 overlap codes, idempotency conflict).

**Derivation (server only; the browser never sends a change kind, an instant or an actor).**
- `valid_from` is Site-local midnight of `applies_from`, as UTC. `valid_to` is None.
- Bounds: from Site-local today − 400 days to today + 366 days.
- The current series is read once (`store.snapshot`, current). `expected_prior_revision_id` is the series' highest revision, or None.
- Change kind:
  - no current assignment overlaps `[valid_from, ∞)` → `INITIAL`;
  - an overlap, and `valid_from` ≥ server now → `SUCCESSION`;
  - an overlap, and `valid_from` < server now (today or earlier) → `CORRECTION`. `reason` is required here, else 422 `REASON_REQUIRED`: "This date changes figures already shown. Say why."
- A reason sent with INITIAL or SUCCESSION is kept as `provenance.entry_note`, never as `correction_reason` (the store refuses that, `assumptions.py:147`).
- Currency must equal the series' current currency when a series exists ("This site's {noun} is kept in {CUR}."). With no series, any active ISO code is allowed.

**Dry run** (`"dry_run": true`). Runs steps 1-9 and `plan_assignments` (pure). It never calls `publish`. The response is 200:
`{"dry_run": true, "change_kind", "applies_from", "reason_required": bool, "summary"}`. The summary is server words:
- INITIAL: "First {noun} for {Site}: {value} {CUR} per {unit} from {d MMM yyyy}. Figures from that date get a price."
- SUCCESSION: "New {noun} from {date}. Earlier figures keep the current price."
- CORRECTION: "Correction from {date}. Figures from {date} are recalculated with this price; the earlier version is kept in the history."

**Save.** `store.publish(tenant_id, site_id, Publication(..., channel="SITE_ADMIN_ENTRY", source_reference=source, provenance=...), SITE_ADMIN_PRICE_PUBLISHER)`.
- The response is 201 for new, or 200 when `replayed` (same idempotency key and digest):
  `{"revision_id", "revision_no", "change_kind", "applies_from", "recorded_at", "replayed", "set_by": "Entered by site admin", "summary"}`.
- The summary reads: "Saved. {Noun} {value} {CUR} per {unit} from {date}. Figures that use it read "Updating…" for a few minutes, then show the new price."
- No recompute runs inline. The tick does it (5.1).

**How a saved price reaches PR-1 and PR-2a reads.** No new read code:
- PR-1 `price_action` is attached only to UNPRICED items. Once the price covers the window, the item reads priced and the link disappears.
- PR-2a's page read lists the new revision in History. It must map `actor_id` to `set_by_label`: `service:assetops-assumption-publisher` → "AssetOps administrator"; `service:operator-entry` → "Entered by site admin". The words are the server's. If PR-2a merges first, it ships the map with both entries.
- PR-2a's page read gains `entry: {"enabled": bool, "keys": [the stored keys this Site uses]}`. `enabled` is false when the principal is not configured, or when the request carries `known_at`.
- **AR-4 contract line:** the `money.lines` kind must declare `price.revised@1` (`by_assumption_key`, days from the valid date to today) in the register. PR-3's Postgres flow test must pass on whichever path is live, and whichever of AR-4 and PR-3 merges second reruns it.
- The response store needs nothing new. The outbox insert moves the watermark, and a test pins that a stored Financials body is not served after a save.

**UI (on the PR-2a page; `price-it.html` Part B is the base layout).**
- Rows of entry keys gain a **"Set a new price"** button. When the page opens with `?key=` set to an entry key, that row's form is open on arrival.
- The form opens **inline under its row** and stacks to one column at 390 px. Fields, all words from the server or one words file:
  - **Amount**, with its unit suffix ("USD per litre");
  - **Currency**: read-only text when a series exists, otherwise a select;
  - **Basis**: three radios, "An estimate", "A contract rate", "A recorded purchase";
  - **Where this price comes from** (required);
  - **Applies from**: date, default Site-local today;
  - **Reason**: shown when the dry run says `reason_required`.
- Two steps: **Continue** sends the dry run and shows its `summary` in a confirm panel; **Save price** posts.
- One idempotency key per opened form, reused on every retry.
- After save: the page stays, shows the server `summary` as a success note, re-reads the page (the row shows the new value; History's top entry reads "Entered by site admin"), and keeps "← Back to where you were" prominent.
- The sign-in sentence becomes: "Prices saved here are recorded as entered by site admin until sign-in is available."
- PR-1 label, server words in `price_action.wire`: a `SET_PRICE` key outside `STORED_KEYS` reads **"What pricing this needs →"** instead of "Set a {noun} …", so no link promises a save that cannot happen.

**Honest states.**

| State | What the user sees |
|---|---|
| Entry off (`enabled` false, no `known_at`) | The draft's sentence, "Prices are set by your AssetOps administrator until sign-in is available.", and no form |
| `known_at` view | "You are viewing prices as known at {k}. Set a price from the live view →" (the link drops `known_at`); no form |
| Future key row | "Not set" and "Saving this price comes once a figure uses it."; no button |
| 422 or 409 | The server message inline, and "Nothing was saved." |
| 503 | "Prices cannot be saved right now. Nothing was saved." |
| Network loss on save | "We could not confirm the save. Saving again is safe." (same key) |
| After save | Affected figures elsewhere show the existing "Updating…" until the tick; no new state |

**Tests.**
- **Backend, no DB** (`test_pr3_price_entry.py`):
  - each refusal in order;
  - each shape field;
  - a future key refused;
  - the change-kind table (none → INITIAL; tomorrow → SUCCESSION; today and past → CORRECTION, with REASON_REQUIRED);
  - `valid_from` at Site-local midnight for a non-UTC zone;
  - a dry run never calls `publish` (spy);
  - the actor, channel, attestation and provenance literals;
  - `entry_note`;
  - `set_by` and summary words;
  - the PR-1 label for future keys;
  - `entry.enabled` false under `known_at`.
- **Postgres** (own `*_test` DB, `test_pr3_price_entry_postgres.py`):
  - 0060 up and down, and down refused while a row exists;
  - a saved row has channel `SITE_ADMIN_ENTRY`, actor `service:operator-entry` and no `author_id`;
  - a `price.revised` outbox row;
  - a diesel CORRECTION queues consequence work, and after one drain (`recompute.run`, plus the chain snapshot consume and drain) the fuel-cost money line reads the new price, while the same read "as known at" before the save reads the old one;
  - a replay returns 200 with one row;
  - a productive-use INITIAL on a Site without one makes the mill value priced on the next read, and its `price_action` disappears;
  - a stored Financials response is not served after a save.
- **Frontend** (`sitePriceEntry.test.tsx`):
  - the form shows only on entry keys and only when `enabled`;
  - `?key=` opens the form;
  - Continue → dry run → summary;
  - the reason field appears on `reason_required`;
  - the save body has no actor field and reuses the key on retry;
  - the success note and re-read;
  - each honest state.
- **Guards:** hardwiring, missing-claim, mock-deviation labels and architecture check.
- Layout evidence at 1440 and 390 px for the open form and the success note.

**Units: 1.0 agent unit.** Server, migration and tests 0.55; frontend form and states 0.35; the Postgres flow test 0.1. Opus for the first build, Sonnet for fix rounds.

### 5.4 Defaults: owner sign-off needed, and which can stand

| # | Default | Owner sign-off? |
|---|---|---|
| 1 | Address `/sites/:code/financials/prices` (draft choice 1; PR-1 built it) | yes, draft choice |
| 2 | "Assumptions" subtab becomes "Prices"; the old address forwards (choice 2) | yes, draft choice |
| 3 | Future keys listed as "Not set", with "Saving this price comes once a figure uses it." and no button (choice 3, sharpened) | **yes** |
| 4 | Half-simple warnings link their simple part (choice 4). Their keys are future keys, so the link reads "What pricing this needs →" for 17 Nov | **yes** (changes PR-1 words) |
| 5 | Model items open Part C, with no "Tell your contact" (choice 5) | yes, draft choice |
| 6 | Form inline under the row; Continue → confirm → Save price; stay on the page with the success note and Back link | **yes** |
| 7 | Sentence: "Prices saved here are recorded as entered by site admin until sign-in is available." | **yes** (copy) |
| 8 | Preview is the change-kind sentence only, with no "N figures change" count (spec §4.2 reduced) | **yes** |
| 9 | Applies-from defaults to today; today or earlier over an existing price is a correction and needs a reason | no (follows spec §4.2, §4.5) |
| 10 | Demo beat: the presenter corrects Kobo's diesel price from a past story day with a reason, on the live view (no `known_at`), waits for "Updating…" (2-4 min), then shows the fuel cost and History "Entered by site admin". The save persists in that database, so it goes last in the session. | **yes** (script) |
| 11 | PR-3b (price the visits warning) stays out | **yes**, only if the owner wants warnings priced |

The coordinator sends items 3, 4, 6, 7, 8, 10 and 11 to the owner in one message, with the draft's choices 1, 2 and 5. Nothing waits on them before Friday morning: the server half needs no sign-off.

### 5.5 Lanes and order, from Thu 12 Nov ~12:30 to the freeze (last merge Sat 14 Nov 20:00)

| Lane | Thu pm | Fri | Sat (to 20:00) |
|---|---|---|---|
| A | AR-3 + AR-6: Postgres and client4 parity | review, merge by 14:00; then CLEAN-1 (0.25), moved from B | FR-B trimmed (0.5), moved from B; buffer gone |
| C | AR-4 (2.0): code; Postgres after AR-3's slot | Postgres and parity on client4 | review, merge by 16:00; held if not ACCEPTed by 20:00 |
| B | PR-1 Postgres files, review, merge; **PR-3 server** (0.55) code and no-DB tests on `task/PR-3-price-entry` from PR-1 | owner signs the draft (needed by Fri 09:00) → PR-2a (0.4) → review, merge Fri evening; **PR-3 frontend** (0.35) stacked on PR-2a; PR-3 Postgres flow test (slot after AR-4) | PR-3 review by 12:00, Sonnet fix round, merge by 18:00; held if not ACCEPTed by 20:00 |

- **Postgres priority:** AR-3 > AR-4 > PR-1/PR-2a/PR-3 > FR-B. PR-3's migration test is one short slot, never beside a parity run.
- **What moves:** FR-B (0.5) and CLEAN-1 (0.25) go from lane B to lane A. Lane A's buffer (EV-HB gate slack, Sunday fix-round prep) is used up. **Nothing new is pushed out of 17 Nov.** If AR-3 + AR-6 slips past Fri 14:00, FR-B drops first, then CLEAN-1. PR-3 does not touch AR files and does not compete with AR-4, except for the one register line in 5.3.
- **If the owner's draft sign-off slips past Fri 12:00:** PR-2a and PR-3's frontend build to the defaults above, labelled MOCK DEVIATION where they differ from the draft. The owner checks them at the Sunday walkthrough, and the Sunday Sonnet round fixes the words.
- **Hold rule for PR-3:** not ACCEPTed by Sat 20:00 means held unmerged, server and frontend together (a route with no screen is not shown, so there is no partial merge). PR-2a's read-only page then stands, with the administrator sentence, and the presenter says that prices are set by the AssetOps administrator. If PR-2a is also held, PR-1's honest "not available yet" target stands. PR-3 is stacked on PR-2a and never merges without it.
- **Walkthrough and final build:** PR-3 is in the Sat rehearsal build and the Sun 15:00 walkthrough. Saves made during the walkthrough stay in that database only. The Mon 16 final build is fresh, so they do not carry into 17 Nov. The prepare applies 0060 like any migration.

### Dispatch brief (revision 5)

**PR-3 site-admin price entry.** Opus. Wt `AssetOpsV1-pr3`, branch `task/PR-3-price-entry` from `task/PR-1-price-action` (rebase onto main after PR-1 merges, then onto PR-2a for the frontend). 1.0 unit.
- Spec: this revision, 5.2-5.4; D-PRICE.1; `.agent/architect-answer-price-it-2026-11-10.md` §4.2 and §4.5 (form fields, change kinds); precedent `work/operational_entry.py`, `work_api.py:198-216`.
- Thu pm: server, migration and no-DB tests only. Postgres only on the coordinator's go, own `*_test` DB, never client4, client6 or client7.
- Pre-flight questions (one batch, before code): the Site time-zone lookup to reuse; whether `store.snapshot` gives the current assignments the derivation needs; the migration number free at that moment.
- Packet: the refusal table as tested, the derivation table, the Postgres flow output (the before and after money line, and as-known-at), layout evidence, and any MOCK DEVIATION labels.

## Revision 4 (Architect, Claude, 2026-11-11 ~18:00): any-range speed first, "price it" next

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude.
- Owner, verbatim (`.agent/owner-price-it-and-speed-priority-2026-11-11.md`): "i want pricing early warnings and unpriced items to be done and the speedup for any date range priortised"
- Tonight is unchanged (D-ANY.6, build sheet): AR-0 baseline, AR-2, prepare by 22:30. The machine is reserved 22:15 to about 03:30. HON-1 and OPEN-NOW merge after the tag.

**Ruling on AR-4 and PF-O2: PF-O2 is not required.**
- PF-O2 is a new in-memory route over `summary()`. AR-4 changes what `summary()` reads (evidence and money from rows); it does not need the route.
- The dependency was only a guard against changing the same Portfolio read twice. PF-O1/O2 stays out for 17 Nov, so there is nothing to change twice. If PF-O2 is built later, it inherits the rows.
- PF-C is merged, so its money receipts are in place. AR-4 = 1.5 (spec) + 0.5 for parity on the PF-C receipt lines = **2.0**.
- AR-4 needs only AR-1 merged (tonight, if the baseline parity passes). It runs in its own lane beside AR-3 (spec: "AR-3/AR-4 can run in two lanes after AR-1").

**"Price it" for 17 Nov: the honest half only.**
- PR-1 `price_action` on unpriced items: early warnings, money cells, Finding cost tiles, verification value (0.5).
- PR-2a read-only Site price page: current prices, history, and "Prices are set by your AssetOps administrator until sign-in is available" (0.4). A v7.1 page draft goes to the owner first.
- **Out, and why:** PR-3 write path and PR-4 recalculation-on-publish need BL-54 sign-in (a hard dependency). PR-5 "what is needed" blocks (0.5) are out unless buffer remains on Fri. Without sign-in, saving a price is not possible in the session; the presenter says so.

**Order, Thu ~12:30 to Sat 20:00 (last merge), all Postgres one job at a time.**

| Lane | Thu pm | Fri | Sat (to 20:00) |
|---|---|---|---|
| A | AR-3 + AR-6 (1.5): code started tonight; Postgres and client4 parity Thu pm | review, merge by Fri 14:00 | buffer, Sunday fix round prep |
| C | AR-4 (2.0): code started tonight; parity Fri on client4 | Postgres and parity Fri pm (Postgres priority 2) | review, merge by Sat 16:00; held unmerged if not ACCEPTed by 20:00 |
| B | price-page v7.1 draft to the owner (tonight); PR-1 (0.5) | PR-2a (0.4) after owner approval | FR-B trimmed (0.5), CLEAN-1 (0.25) |

- **Postgres priority when slots clash:** AR-3 > AR-4 > PR-1/PR-2a > FR-B.
- **Moves out to fit:** PR-3, PR-4, PR-5; FR-B halved (only failures in the Sat freeze suites); AR-5 (pre-load stays as the safety net). Already out: PF-O1/O2 and UQ.
- **Honest risk:** AR-4 is the long pole. Its slack is about 4 h, and its parity gates the merge. If it slips, the Portfolio is fast for any range on coverage (AR-3) but money and evidence stay on pre-built ranges, and price-it is unaffected.
- Price-it does not compete with AR-4: different files and lane, and only light Postgres. Both land if AR-4's parity passes first time.

### Dispatch briefs (revision 4)

**AR-3 + AR-6.** Opus. Wt `AssetOpsV1-ar3`, branch `task/ANY-2-AR3-AR6` from `task/ANY-1-rows` (rebase onto main after ANY-1 merges). 1.5 units.
- Spec: `.agent/architect-answer-any-range-speed-2026-11-10.md` AR-3, AR-6, D-ANY.1-6.
- AR-3: kind `dispatch.day` on DATA-12 graded local days (not `dispatch_days`); `coverage._mini_grid_basis` reads rows; match pass unchanged.
- AR-6: the board's 4 work-index reads become one; Cold/EV boards under 1 s cold.
- Kill switch: the D-ANY.6 env list (an omitted kind = old path).
- Tonight: code and no-DB tests only, no heavy CPU after 22:15. Thu after 12:30: Postgres tests on the own `*_test` DB, then parity `--kinds dispatch.day` on client4 (never client6).
- Packet lists the added parity cases and the `perf_budget --any-range` before/after.

**AR-4 Portfolio evidence and money rows.** Opus. Wt `AssetOpsV1-ar4`, branch `task/ANY-2-AR4` from `task/ANY-1-rows` (rebase onto main after ANY-1 merges). 2.0 units.
- Kinds `evidence.claim`, `evidence.provenance`, `money.lines`; roll-ups read by `summary()`; no PF-O2.
- Every kind is proven byte-equal by AR-0 parity, including PF-C receipt lines and unaligned UTC windows. A kind that fails stays on the old path and is reported, never approximated.
- Tonight: code and no-DB tests only. Postgres from Thu 12:30, after AR-3's slot; parity on client4.
- Do not touch `estate/coverage` (AR-3's files); coordinate the shared register file by rebasing.

**PR-1 + price-page draft.** Opus. Wt `AssetOpsV1-pr1`, branch `task/PR-1-price-action` from main. 0.5 unit plus the draft.
- Spec: `.agent/architect-answer-price-it-2026-11-10.md` sections 3 and 7.
- Tonight: a v7.1 price-page mockup draft (read-only view, history, the administrator sentence) for the owner, in `frontend/mockups/`.
- PR-1: server `price_action` (two shapes) on every unpriced item; words server-side; frontend link to `/sites/:id/prices` with `return`. Until PR-2a lands, the target shows an honest "not available yet".
- No write path; `HUMAN_PRINCIPAL_REQUIRED` unchanged.
- Postgres tests only from Thu 12:30, own `*_test` DB.

## Revision 3 (Architect, Claude, 2026-11-11 evening): UI deferred, functional pull-in

- Owner, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "lets depriortize the UI asepct for now in the backlog and we'll come back to it later, lets focus on the functional ones".
- **Out of 17 Nov, to the backlog (BL-69):** UQ-0 sheet (built, branch `task/UQ-0-v72-sheet`, kept unmerged, awaits approval later), UQ-1 tokens/type/Inter, UQ-2 themes, UQ-3 states/quick wins, UQ-4..UQ-8. The session uses today's light look, English only. Lane D's C1 (PB-5/6/8, RM-1, RM-2, in review) stays IN: it is honesty and wording, not look. The C.5 collision rules about UQ-1 and UQ-2 no longer apply.
- **Freed: about 4 units** (UQ-0 0.5 done but parked, UQ-1 1.25, UQ-3 0.5, UQ-2 1.0, plus lane D time from Thu ~13:00).

**Pull-in, in order (functional only; each is small, reviewable and has no hidden dependency):**

| # | Id | What | Units | Why now | Depends on |
|---|---|---|---|---|---|
| 1 | HON-1 | "Complete readings" count excludes READINGS_CONFLICT and NOT_ENOUGH_READINGS days (Architect ruling on question 1: count them out) | 0.3 | The opening page now reads "complete readings on 7 of 7 days" next to "4 Nov: conflicting readings" (PARTIAL-MONEY packet residual risk). An executive sees a contradiction on page one; the owner's 2026-11-11 wording rule says incomplete or invalid data must be stated | none |
| 2 | OPEN-NOW | Server read of items open now, unfiltered by the range, and the Work pages' one line "Open now: 3 requests, whatever the dates" (approved Portfolio layout proposal, line 581) | 0.5 | Work pages now default to the last 7 full days (PB-1c), so an older open item is hidden. Operators ask "what is open"; this is the honesty half of R338 | none (SR merged) |
| 3 | AR-3 + AR-6 | ANY-2 core, already IN: coverage on rows; Cold/EV board work lists in one read | 1.5 | Starts now stacked on `task/ANY-1-rows` (code and unit tests only); Postgres tests after Thursday's demo and never beside the scratch prepare or the ANY-1 baseline | AR-1 (on the stack); merges only after ANY-1 merges |
| 4 | FR-B | Test hygiene fix round (carry list in the handoff "Carry to FR-B") | 1.0 | Saturday 20:00 suites decide whether the freeze build is trusted; fewer known failures means a break is visible. Lane D after Thursday's demo, targeted test files only | none |
| 5 | CLEAN-1 | Sonnet cleanup card: handoff follow-ups (UQ-6a unhandled-500 Content-Language, ch5c2 rerun when quiet) plus the F05 check below | 0.25 | Cheap; before the Sat suites | none |

- **Kept out (unchanged, still option X):**
  - **AR-4** (2.5). It needs AR-1 merged (Fri at best, after Thursday's baseline and AR-2) and PF-O2, which is not built. Freed units do not shorten that chain. The named workaround stays: Portfolio fast on pre-built ranges only (script ranges, lens variants, last 7 and 30 days).
  - **PF-O1/O2** (1.5). Layout work; today's grid fits 4-5 Sites; the owner's instruction puts layout after.
  - **UQ-4** (formats, language switcher). UI; English session.
- **Ruling on question 2 (F05 placement after s602b moved to PARTIAL):** a test gap, not a demo defect. CLEAN-1 confirms that one of `test_w303_selectors_postgres`, `test_w303_portfolio_scope_snapshot_postgres` or `test_s4_finding_index_postgres` asserts a Portfolio Finding row's placement on a fixture with chain day grades (AVAILABLE Site). If none does, add one assertion to the first of them by seeding grades, and drop the `rows.F05` expectation from `tools/s602b-verification-evidence.mjs` with a comment citing D-E5.38. Do not re-seed the s602b estate fixture.
- **Machine rule (unchanged, sharpened):** one heavy job at a time. Thu 06:30-12:30 every lane pauses. Thu afternoon the scratch prepare (about 2 h 45, EV-HB gate by Fri 18:00), then the ANY-1 baseline, run alone: builders write code and run non-Postgres tests only while either runs. Last merge Sat 20:00; anything not ACCEPTed is held unmerged.
- **Buffer:** about 0.5-1.0 of the freed units is left unassigned on purpose, for the EV-HB gate (revert or fix) and the Sunday fix round. ANY-1 still has no slack.

### Start-now briefs (revision 3)

**HON-1 complete-readings honesty.** Opus. Wt `AssetOpsV1-hon1`, branch `task/HON-1-complete-readings` from main. 0.3 unit. Lane C (or the first free lane).
- **Ruling:** a day graded READINGS_CONFLICT or NOT_ENOUGH_READINGS is not a "complete readings" day. The count reads "complete readings on 6 of 7 days" and the existing gap clause names the day and reason. No new wording beyond what GAP-REASONS already composes; if a count phrase must change, server text only via `card_text` (CH-6b2).
- **Where:** the day counts behind `portfolio_coverage` / `_coverage_days` (`backend/assetops_backend/site_outcomes/read.py` ~758-812) and the source of `day_counts` / `days_line` (`chain/vocabulary.py`). A Site with a conflict day is `complete: False`, so the Portfolio lead reads incomplete.
- **Check the same count on the Site Overview readings line and the Finding/cards "Why?" days**; one rule everywhere (the line and the cards cannot disagree, PF-C1).
- **Tests:** a targeted test per reason (conflict, not-enough) and one all-good week unchanged; update only goldens the change explains, listing each in the packet.
- Named test files only, own `*_test` DB, no prepare. Do not touch wt `AssetOpsV1-e3d`, DB client6, ports 8990/5490, Docker until Thursday's demo ends.

**OPEN-NOW Work pages "open now" line.** Opus. Wt `AssetOpsV1-opennow`, branch `task/OPEN-NOW-work-read` from main. 0.5 unit. Lane B.
- **Spec:** `.agent/architect-proposal-portfolio-layout-2026-11-10.md` line ~581; PB-1c packet note (global Work `state_counts` are window-filtered).
- **Backend:** add `open_now` counts (by work kind: requests, actions, as the Work pages show them) to the existing global and Site Work list responses, computed with no date filter but the same `known_at` cutoff and Site scope. No new endpoint unless the list contract cannot carry it; contract type in `contracts`.
- **Frontend:** one line above each Work list, "Open now: 3 requests, 1 action, whatever the dates"; zero reads "Nothing open now". Words server-side or in the existing Work words file, never composed from raw codes.
- **Tests:** backend count ignores the range but obeys `known_at`; one frontend test per Work page; revise register rows R338/S17 if found, else note in packet.
- Same machine rules as HON-1.

**AR-3 + AR-6 (ANY-2 core).** Opus. Wt `AssetOpsV1-ar3`, branch `task/ANY-2-AR3-AR6` from `task/ANY-1-rows` (bb3d7645c). 1.5 units. Lane A or C.
- **Spec:** `.agent/architect-answer-any-range-speed-2026-11-10.md` rows AR-3, AR-6 and D-ANY.1-5. AR-3 builds on DATA-12's graded local days, not `dispatch_days` (C.5).
- **Now:** code and non-Postgres tests only. Postgres tests only after the coordinator's go (after Thursday's demo, never beside the scratch prepare or the ANY-1 baseline).
- **Merge:** after ANY-1 (AR-0..AR-2) merges; rebase then. Held unmerged if not ACCEPTed by Sat 20:00; the Portfolio then uses pre-built ranges.
- Packet lists the parity cases it adds to AR-0's harness.

## Client demo Tue 17 Nov: cut and start order (Architect, Claude, 2026-11-11; revision 2 after the owner's answers; revision 1 is in git at 22d877b1d)

- Binding checked: `.ai/ROLE_CONFIG.md` Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-tag-optionb-client-date-2026-11-11.md`): "yes tag it and add the backlog item, lets go with option B for now. Also, lets proceed with the items for today right away, and i want my walkthrough comment items to start building. THe client demo will be on 17-Nov"
- Owner answers, verbatim (`.agent/owner-answers-17nov-scope-2026-11-11.md`): "here is my response 1. No 2.No 3. yes 4. yes 5.I need more context on this 6. I need more context on this 7.I will start talking to different client starting with Minigrid and EV , likely executives 8.Sunday 3PM ready for walkthrough or am available finished earlier too"
- What that means:
  - **IN for 17 Nov:** any-range speed (ANY-1 and ANY-2), the shared date range (SR), and the design foundation with light and dark themes. (Revision 3: the design foundation moved to the backlog, owner 2026-11-11.)
  - **Approved:** `portfolio-tabs.html` is the layout spec, and RM-2 is approved.
  - **Pending, being explained to the owner:** PB-1c and DATA-6.
  - **Audience:** mini-grid and EV operators, likely executives. EV fixes (PB-3 + DATA-11) and visual quality gain value. BeagleBone loses it, so it moves to after.
  - **Walkthrough:** Sun 15 at 15:00, or earlier.
- Status at writing: A1 DATA-12 is built (fd85f1d31) and in review. B1 PF-T is building.

### C.1 Schedule (skeleton kept; one adjustment recommended)

| When | What |
|---|---|
| Tue 17 | Client demo. 30-min smoke check in the morning. |
| Mon 16 | **Final demo build** (S = Mon 16, prepare about 2 h 45), finish and live checks, figures into both scripts, tag `demo/2026-11-16-final`. Only a blocking frontend fix may land. |
| Sun 15 | **Owner walkthrough at 15:00.** One Sonnet fix round afterwards, merged by 22:00. |
| Sat 14 | **Last feature merge 12:00 (kept).** Then full suites and check-all with the lanes stopped (about 6 h). Rehearsal build overnight. Sun morning: live checks, recapture in both themes, script refresh with PILOT-1 (0.25). |

- **Recommended adjustment, for the owner to choose (C.4 option Y):** last merge **Sat 20:00** instead of 12:00.
  - Suites run overnight (20:00 to 02:00) and the rehearsal build runs 02:00 to 05:00.
  - Checks, recapture and script run Sun 05:00 to 14:00. The 15:00 walkthrough stays.
  - It buys about 8 hours on 3 lanes, about 1.5-2 units.
  - The cost: no buffer on Sunday morning. If the suites or the build find a break, the walkthrough runs on a build with known issues, listed for the owner.

### C.2 Demand against capacity (honest)

**What the owner now wants IN, in units:**

| Group | Items | Units |
|---|---|---|
| Honesty and Site pages | DATA-12 (built), PB-4, PB-7, BL-50, L2, PB-1a, PB-1b, PB-5/6/8, RM-1, RM-2; PB-1c and DATA-6 if approved | 6.4 |
| EV for EV executives | PB-3 + DATA-11 | 1.25 |
| Portfolio | PF-T (building), PF-C + PF-W, PF-O2 + PF-O1 | 3.75 |
| Shared date range | SR-1, SR-2, SR-3 | 1.75 |
| Design foundation | UQ-0 sheet, UQ-1 tokens/type/Inter, UQ-3 states + quick wins, UQ-2 light/dark, UQ-4 formats | 4.0 |
| Any-range speed | UQ-6a 0.25; ANY-1 = AR-0, AR-1, AR-2 (3.0); ANY-2 core = AR-3, AR-6 (1.5), AR-4 with money receipts (2.5) | 7.25 |
| Test hygiene | FR-B | 1.0 |
| **Total** | | **about 25.4** |

**Capacity to Sat 12:00, at the observed 1.5-1.75 units per lane-day:**
- 3 lanes from now and a 4th from Thu ~13:00 (only if the e3d serve is stopped after the demo and free RAM stays at 3 GB or more): about 10.5 lane-days, so **15.5-18 units**.
- With option Y (Sat 20:00): **17-20 units**.

**It does not fit. The gap is about 6-10 units.**
- More lanes do not close it. The screens work shares the shell, the tokens and the Portfolio files, and ANY is a serial chain: PB-1 → AR-0 baseline → AR-1 → AR-2, AR-3, AR-4.
- **ANY-2's AR-4 is the item that cannot land in any arrangement.** It needs AR-1, PF-C and PF-O2 merged first, that is Fri afternoon at best, and it is 2.5 units.

### C.3 What a third lane starting NOW buys
- **About 1.2 lane-days (about 2 units) before Thursday noon.**
- **More importantly, it makes ANY-1 possible at all.** Lane C builds PB-1a, then PB-1b, while lane A builds PB-4/PB-7, so all of them merge by about Thu 12:00-15:00. AR-0's baseline can then run Thursday afternoon.
- Without lane C, PB-1b merges about Fri midday, AR-1/AR-2 cannot finish by Saturday, and ANY-1 drops.
- **Memory rule:**
  - Lane C pauses during the E5b live capture and Thu 07:00-12:30.
  - Targeted tests only.
  - The coordinator checks free RAM before each dispatch and pauses lane D first, then C.
  - AR-1's migration tests are the single heavy slot, never beside a build or serve.
- **Recommend yes: start lane C now with PB-1a.**

### C.4 The trade the owner must make (one answer; my recommendation first)

**Option X (recommended): keep the skeleton; move about 7 units after 17 Nov.**
- **Trades (moved after 17 Nov):**
  - AR-4, Portfolio money and evidence on stored rows (2.5). This is a workaround, named as one: the Portfolio stays fast only on pre-built ranges, which are the script ranges, the lens variants and the shared-range presets (last 7 days, last 30 days) added to the pre-build list. Other Portfolio ranges take about 10 s.
  - UQ-4, formats and language switcher (1.0 with its share of UQ-6a's formatting). The session is in English; thousands separators come with the quick wins.
  - FR-B (1.0). Its known failures are listed as known in Saturday's suite run.
  - PF-O1/O2, the scalable outcomes list (1.5). With 4-5 Sites today's grid fits. The approved design is built first thing after the demo.
  - Total about 6.0, plus option Y as the buffer.
- **Kept IN:**
  - every honesty and Site-page fix;
  - PB-3 + DATA-11 (EV);
  - Portfolio tabs, coverage once and the new words;
  - the shared date range;
  - the design foundation with **both** themes;
  - UQ-6a, ANY-1 (Site boards fast for any range) and AR-3 + AR-6 (Portfolio coverage on rows; Cold/EV boards under 1 s).
- **Risk stated plainly:**
  - ANY-1 finishes at the end of lane A with no slack. If AR-2 is not ACCEPTed by the freeze, it is held unmerged, and the boards use the pre-built ranges in the session.
  - UQ-2 (dark theme) is last in lane D. If it misses, the session uses the light theme.

**Option Z: everything IN.** Only by moving the session, or by accepting unreviewed merges. Neither is recommended.

### C.5 Order and lanes (option X)

| Lane | Order | Start rule |
|---|---|---|
| **A, server** | A2 PB-4 + PB-7 + BL-50 + L2 (+DATA-6 if approved) → A5 UQ-6a → A6 AR-0 + AR-1 → AR-2 | A2 the moment A1 merges |
| **B, Portfolio and shell** | PF-T (building) → B2 PF-C + PF-W → B4 SR-1 → SR-2 + SR-3 | B2 the moment B1 merges (A1 merged too) |
| **C, Cold/EV then server** (**now**) | A3 PB-1a → A4 PB-1b → AR-3 + AR-6 (after AR-1 merges) → PB-3 + DATA-11 → PB-1c if approved | now |
| **D, look** (Thu ~13:00, memory permitting) | UQ-0 sheet (owner approves Thu evening) → UQ-1 → UQ-3 + quick wins → C1 PB-5/6/8 + RM-1 + RM-2 → UQ-2 themes | after Thursday's demo |

**ANY-1 baseline ordering (rule 1 of section 0.2, kept):**
- AR-0's harness code may be written as soon as UQ-6a merges.
- The **baseline run** happens only after PB-4, PB-7, PB-1a and PB-1b have all merged. Expected Thu ~15:00 with lane C now.
- AR-1's migration freezes the stored body shape, so UQ-6a must merge before AR-1's first commit.
- AR-1's Postgres tests wait until the Thursday demo has ended.
- **DATA-12 already changed coverage, so AR-3 builds on the graded local days,** not on `dispatch_days`.

**Collision rules:**
- UQ-1 touches about 35 CSS files. Lane B rebases on UQ-1 once, and new lane B CSS uses semantic tokens only.
- SR-1 lays the top-bar row once. UQ-2's theme control goes into that row.
- C1 runs in lane D after UQ-3 because its files (Site pages) are the ones UQ-3's empty/loading states touch.

### C.6 Machine rules for every brief
- 16 GB machine, about 3.5 GB free with the demo app up. Docker's VM crashed once.
- **One heavy job at a time.** Named test files only: no full suites, prepares, recaptures or captures until the freeze.
- **Until Thursday's demo ends, do not touch:**
  - wt `AssetOpsV1-e3d`;
  - DB `assetops_polish_client6_test`;
  - ports 8990/5490;
  - Docker (no restarts).
- Each builder uses its own `*_test` DB.
- Builders:
  - Write/Edit only, no subagents.
  - PYTHONPATH absolute under the worktree (incl. `contracts`, `simulator`).
  - Commits end with the Co-Authored-By line. Never push. `git add -f` for `.agent`.

### C.7 Briefs

Briefs already written, unchanged in content (dispatch per C.5):
- **A2** PB-4 + PB-7 + BL-50 + L2: Opus, 1.1. Dispatch on A1 merge.
- **A3** PB-1a: Opus, 1.0. **Now, lane C.** Wt `AssetOpsV1-pb1`.
- **A4** PB-1b: Opus, 1.0. Lane C, after A3.
- **B2** PF-C + PF-W: Opus, 1.25. On B1 merge.
- **C1** PB-5/6/8 + RM-1: Sonnet, 1.1. Lane D. RM-2 is now approved, so it is added (0.1): hide the Findings lens chips on Cold, EV and Kisiwa client screens, with a test per Site type.
- **C2** PB-1c: on approval only.

Moved after 17 Nov: B3 PF-O and C3 FR-B.

**A5 UQ-6a server message seam.** Opus. Wt `AssetOpsV1-uq6a`, branch `task/UQ-6a-message-seam`. 0.25 unit. Lane A, after A2. **Must merge before AR-1's first commit.**
- **Goal:** server words are stored and sent as `{key, params}` and rendered for the request locale at read; never stored as composed text.
- **Spec:** `.agent/architect-plan-pre-client-2026-11-10.md` UQ-6a row (section 1 table) and §4.3 D-I18N.1, D-I18N.2.
- **Scope now, English only:**
  - the contract type and the render function;
  - `Accept-Language` resolution falling back to `en`, and `Content-Language` on responses;
  - the locale in the response-store key.
  - No catalogue move of existing words (UQ-6b, after).
  - No Babel formatting: it goes with UQ-4, after.
- **Files:** a new `backend/assetops_backend/i18n/` module (messages, render, locale); the response-store key builder; one existing server body converted as the reference user (the Pre-flight names the smallest one).
- **Tests:** render of `{key, params}`; unknown locale falls back to `en`; the cache key differs by locale; `Content-Language` header; the converted body is byte-equal in English to today.

**A6 AR-0 + AR-1 parity guard and read-row foundation (start of ANY-1).** Opus. Wt `AssetOpsV1-any1`, branch `task/ANY-1-rows`. 1.5 units. Lane A after A5.
- **Spec:** `.agent/architect-answer-any-range-speed-2026-11-10.md` §4 (cards AR-0, AR-1; risks table); D-ANY.1-4 and D-MONEY.1-4 in `build-sheet-OWN-GAPS-2026-11-08.md` (the generic row contract carries money receipts); D-I18N.1 (row bodies hold keys).
- **Order inside the slice:**
  1. The AR-0 harness: every story request plus seeded random ranges (board any day; Portfolio any from/to up to 31 days; historical `known_at`); row-based compose equals today's compose byte for byte. `perf_budget.py` arbitrary-range cases with the store off and no pre-build: board 2 s or less, Portfolio month 2 s or less.
  2. **The baseline run only after PB-4, PB-7, PB-1a and PB-1b are on main** (the coordinator confirms).
  3. AR-1: migration at the next free number (`0059` on main today) (`site_period_read`, `revision_provenance`); port and Postgres adapter; one query per Sites x range x kinds; PENDING-at-k from outbox/consumption; register schema accepts the new kinds; backfill CLI.
- **Tests:** migration up/down on the builder's own `*_test` DB (heavy slot, after the Thursday demo); adapter round-trip; PENDING-at-k; register accepts kinds; parity harness self-test (one deliberate mismatch fails).
- **Next card (AR-2, lane A) and AR-3 + AR-6 (lane C)** are dispatched on AR-1's merge, from the same answer file.

**B4 SR-1 shared range bar and state.** Opus. Wt `AssetOpsV1-pft`, branch `task/SR-1-shared-range`. 0.5 unit. Lane B after B2.
- **Goal:** one date range in a new top-bar row on every page; left menu unchanged.
- **Spec:** `.agent/architect-proposal-portfolio-layout-2026-11-10.md` "Item 12.5", SR.3 and SR.4; layout: `frontend/mockups/v71/portfolio-tabs.html` Change 0b (approved spec), top bar "All pages" in `estate-outcomes-scale.html`; D-UI.2 (the range lives in the address only).
- **Files:**
  - `SharedRangeBar` in `OperatorShellLayout`; the demonstration banner stays;
  - `useSharedRange`, returning `{from, to, known_at, preset}` and reading both address forms;
  - `withRange`; the rail `search`;
  - filling in the address on entry;
  - presets (no "Today" preset); the `known_at` label;
  - phone sheet; button 44 px, dates only;
  - picker accessibility (`aria-pressed` presets, labelled inputs, Escape and Cancel return focus).
  - PF-T's Portfolio date bar is replaced by this bar.
- **Tests:** the hook parses both address forms; rail links carry the range; presets; focus handling; the Portfolio reads the shared range. Vitest on the named files only. SR-2 (pages onto the range) follows on merge.

### C.8 Still pending with the owner
- **PB-1c** ("Analysed period" line): context being given.
- **DATA-6** (Kisiwa targets): context being given.
- **Choose option X (recommended) or say which trade differs, and option Y (last merge Sat 20:00) yes or no.**
- **Approve the UQ-0 v7.2 sheet** on Thu evening when it is drawn.

## 0. Agent-pace plan, re-assess Thu 12 Nov morning (added 2026-11-11; replaces the working-day calendar in sections 1 and 3.2; scope, order and decisions stay)

Owner, verbatim (`.agent/owner-units-by-friday-2026-11-11.md`): "the time estimates are for human developement, we should be able to do the indicated units in time for Friday" and then "let it not say which would land by Friday, we wait until Thursday morning for re-assessment".

- **You are right that my calendar was too slow.** I sized lanes at 1.5 units per *working* day. Agents run most of the 24 hours, every day of the week.
- **This section therefore sets the lanes and the order at agent pace, starting now.** It does not forecast what lands by Friday. Progress is re-assessed Thursday morning against the actual merges.

### 0.1 What agents actually delivered (git log on main, 8-11 Nov)

| Day | Merged slices (unit sizes from the build sheets; a few estimated) | Units merged | What else that day used |
|---|---|---|---|
| Sun 8 | Kisiwa K4b, K5, K6a, K6b, K6c, K7-D/F, K8, K9, K10; G3a; R-1; idle fuel A3 | about 7 | four lanes, owner away, specs already closed |
| Mon 9 | G1 1.75, G2 2.25, G3b 1.25, R4.1, POLISH-1, E2 fix A, C1-C4 (about 2.0) | about 8 | G1-G3b built mostly on Sun 8; E2 suites and E3 build |
| Tue 10 | C5, E5-FX, FX-EV-TITLE, FX-COLD-LINKED, FX-KOBO-GAPS 0.6, V3, PL-1, PL-2, DATA-2, FC 0.75 | about 3.8 | E3c/E4 checks, your walkthrough, six Architect answers |
| Wed 11 (to 05:00) | DATA-1 0.5 | 0.5 | E3d demo build |

- **Average: about 6 units per calendar day across 3-4 lanes, about 1.75 per lane per day.** It fell to about 4 on a day with a demo build and a walkthrough.
- **Review and fix rounds are part of that rate.** The four days had 110 review commits and 34 fix commits. Most slices take one fix round, and DATA-1, PL-1 and FX-COLD-LINKED were each rejected once first.
- **Those were small fixes to closed specs. The IN list is heavier, so expect the lower end of the rate:**
  - ANY-1/2 is a new migration with byte-for-byte parity proofs;
  - the tokens and dark theme touch 35 CSS files and about 19 SVGs, and need recaptures;
  - the Portfolio is a new tab layout.
- **At that rate the 22.7 IN units are several calendar days of agent work, not hours.** Thursday's re-assessment measures the real rate on this work.

**What bounds the pace:**
- **Your approvals.** Mockup first:
  - SR and PF need the final v7.1 mockup approved.
  - UQ-1 to UQ-3 need the v7.2 sheet, which does not exist yet (0.5 units to draw).
  - PB-1c and RM-2 need your nod.
  - No approval, no build.
- **Review gates.** One Opus review per slice; only High and Medium findings block a merge.
- **This machine (16 GB):**
  - Free RAM fell to 1.71 GB with one build plus serve, and Docker's VM crashed once at 02:05.
  - Safe limit: **3 builder lanes on targeted tests only**, and one heavy job at a time.
  - Until the Thursday demo ends, **2 lanes**, so the e3d serve and `assetops_polish_client6_test` are not disturbed.
- **Wednesday's fixed work** takes the coordinator and 1-2 lanes:
  - add-dates and the live dip capture, retakes;
  - the script pass and the DS-1f/DS-1b merge;
  - the D-E5.29-37 frontend fixes, E4-RESUME (b), KD-COVERAGE;
  - your afternoon walkthrough.
- **The end check** needs about 6-8 hours of a quiet machine: full suites, check-all, a fresh demo build (about 2 h 45 min) and live checks.

### 0.2 Lane setup and order, starting now

- **Lanes.** Three lanes at most, each in its own worktree and branch. Every lane runs targeted tests only. No full suites, no demo prepares and no recaptures until the end check.
- **Lanes A and B always run.** Lane C runs only while memory allows: the coordinator checks free RAM before each dispatch and pauses C first.
- **Lane C runs FR-B first.** FR-B was planned Wed 11-Fri 13 beside the IN work, and Wednesday's fixed work comes before both.

| Lane | Order (each item merges on review ACCEPT before the next one that depends on it starts) |
|---|---|
| **A, server and data** | PB-1a Cold analysed periods (1.0) → PB-1b EV (1.0) → PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 (1.35) → UQ-6a message seam (0.25) → ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth (3.0) → ANY-2: AR-3, AR-6 (1.5) → AR-4 money and evidence rows (2.5, after PF-C and PF-O2 merge) |
| **B, screens** | UQ-0 v7.2 sheet (0.5, then your approval) → UQ-1 tokens, type, Inter (1.25) → SR-1 shared bar (0.5, after v7.1 approval) → UQ-2 themes, UQ-3 states (1.5) → PF-C, PF-W, PF-T, PF-O2, PF-O1 (3.75) → SR-2/3, PB-1c (1.5) → UQ-4 formats (0.75) |
| **C, fixes (memory permitting)** | FR-B (about 1.0) → RM-1 roadmap words + RM-2 (0.6) → then OPTIONAL items in the section 3.3 order. Before Thursday's demo ends, lane C waits. |

**Why only one screens lane:** a second one would collide in the same files (the shell, the tokens and the Portfolio). Lane C takes the screens work that does not touch them.

**Rules that keep it safe at speed:**
1. **ANY-1's parity baseline (AR-0) is taken only after PB-1, PB-4 and PB-7 merge.** Otherwise its proofs are redone.
2. **AR-1's migration tests run in a quiet window,** never beside a build or serve.
3. **Builder briefs stay small** (code and tests first, captures last). The end check does every recapture once.
4. **Small fix rounds go to Sonnet,** and the coordinator verifies mechanical closures from the diff.

### 0.3 The end check: once, at the end

- **It runs once, after every IN item has merged:** full suites, check-all, one fresh demo build, live checks, recapture in both themes, and the PILOT-1 page with the script refresh. Your full walkthrough follows it.
- **Check-all alone runs on main after each batch of merges** (it is light).
- **No mid-way demo build.** It would test a half-built Portfolio and repeat the 6-8 heavy hours, which goes against your overnight instruction to batch heavy work at the end.
- **On Thursday morning I re-assess from the merges and the measured rate:** the order, the session date (sections 3.2 and 5), and whether any OPTIONAL items fit.

### 0.4 Approvals needed today to unblock this

1. **The final v7.1 Portfolio mockup** (`frontend/mockups/v71/portfolio-tabs.html`, with the shared date range in Change 0b). It gates SR-1 and all of PF.
2. **The v7.2 foundation sheet** as soon as it is drawn (lane B's first item). Also **Inter** as the font, and **the theme follows the computer's setting**. They gate UQ-1, which every later screens item builds on.
3. **The item 11 changes:** hide the lens chips (RM-2), the "Analysed period" line (PB-1c), the Kisiwa targets (DATA-6), and the extra Cold and EV days (DATA-11, for OPTIONAL #1).
4. **Present the session in English.** French and Swahili stay OPTIONAL, so lane B does not carry 3.25 units of catalogue work.
5. **Three lanes, with agents running overnight and at the weekend.** The coordinator keeps heavy jobs to one at a time and pauses lane C when memory is short.

### 0.5 BeagleBone (TEL-08): OPTIONAL for the client demo, after the IN items in lane C

Owner, verbatim (same file): "on a side note, i have also obtained SD card and will get the beaglebone ready by EOD today"

**Where it stands.** The spec is `.agent/build-spec-telemetry-2026-10-27.md` §TEL-08; the board ruling is `.agent/architect-beaglebone-wheezy-2026-10-29.md`.
- The field poller (`field/assetops_field`), the GX-shaped emulator and the gateway are built and proven on the laptop (TEL-01 to TEL-06).
- TEL-08 itself was never built. `host/tests/field_bench.py` has helpers only; its `setup`, `activate` and `read` commands do not exist yet.
- The board's own OS (Debian 7, Python 2.7) cannot run the code (requires Python 3.12+). Hence the SD card.

**What you do (about 30-40 min, no code):**
1. **Flash the card.** Write the official BeagleBone Black **Debian 13 IoT** microSD image (kernel 6.x, Python 3.13) from beagleboard.org to the card with Balena Etcher or Raspberry Pi Imager. If only an "eMMC flasher" image is offered, do not use it.
2. **Boot from the card.** Hold the **S2 button** while you power on (5 V 2 A barrel, or USB power). The board's own memory is left untouched, so this is reversible.
3. **Network.** Connect the board by **Ethernet to the same router as the laptop**, with internet through it (for `apt` and time sync). Do not use USB networking.
4. **Access.** Log in once (default user `debian`) and add the coordinator's SSH public key to `~/.ssh/authorized_keys`. No passwords are shared in chat. The coordinator then creates the non-root `assetops` user.
5. **Laptop firewall (admin).** Allow inbound TCP **8443** (upload server) and **5020** (device emulator) on the Private/LAN profile.
6. **Report:** the board's IP, `uname -r`, `python3 --version`, and `timedatectl show -p NTPSynchronized` (must be `yes`).

You create no upload credentials. The bench `setup` command issues the gateway's upload credential and a 7-day self-signed TLS certificate, and they are copied to the board.

**What we build and verify once it is up (about 0.75 units, plus one heavy run slot of about 1 hour):**
- **Build** `field_bench.py` `setup`, `activate` and `read`, per §TEL-08. They use their own test database, `assetops_tel_bbb_test`, never the demo database.
- **Copy** the code to `/opt/assetops/src` and record matching tree hashes on the laptop and the board. Nothing is pip-installed on the board.
- **Run** gateway and poller on the board, with the emulator and the TLS upload server on the laptop. The replay is the Kobo GX-shaped window at rate 12.
- **Gates (TEL-05):** every upload receipt COMPLETED, accepted evidence for every role, and the assessment completes.
- **Uplink fault test:** stop the laptop upload server for 5 min. The board's queue must rise and drain back to 0, with no gap in the evidence.
- **Clock:** offsets within ±50 ms on the board and the laptop.
- **Record:** a claim line, "BeagleBone Black · Debian 13 IoT · kernel … · Python … · commit … · tree …".
- **Stop and report** if Linux needs any code change, or if the clock offset cannot be met.

**Where it sits.**
- Lane C, after FR-B and RM-1/RM-2, ahead of the other OPTIONAL items.
- Its 1-hour run takes the single heavy-job slot, never beside a build, a serve or AR-1's migration tests.
- It must finish before the end check. It never touches the Thursday e3d build.
- The code copy and the clock setup can be done as soon as you report the IP. They are light.

**Why OPTIONAL, not IN:**
- **For a business buyer the value is Low-Med.** The story screens already show the readings arriving.
- **For a technical buyer, or a client asking "what hardware sits on site?", the value is Med-High.** It turns "the gateway was tested on a laptop" into "it runs on a $60 edge box and survives a 5-minute uplink loss without losing data".
- **Best use:** one slide or a 2-minute live clip in the technical script, and a pilot-readiness line in PILOT-1 ("tested on BeagleBone Black"). It is not a beat in the client story.
- **Not shown live in the session.** A live board adds a network and clock dependency to the room.
- **It moves to IN** if you tell me the client's evaluator is technical or asks about on-site hardware.

## 1. In plain words

- **The test I used:** would a client deciding whether to buy notice it, and would leaving it out make something on screen look broken, contradictory or untrue? Speed, honesty and the first impression score high. Things that only matter at 100+ Sites, in a second language nobody has reviewed, or behind sign-in score low for this session.
- **IN for the client demo: about 22.7 units** (plus FR-B this week). That is **3.3 units less than my 26-unit plan**, even though the non-Kobo fixes turned out 2.7 units bigger than the placeholder (section 3).
- **OPTIONAL, if time: about 10 units**, ranked. **AFTER the client demo:** everything else, including sign-in, multi-currency, the full UI uplift and the engineering clean-up.
- **Dates (working days from Mon 16 Nov, weekends not assumed):** the IN build work finishes **Wed 25 to Thu 26 Nov**. With 5 working days for the final build, checks, your walkthrough and the script refresh:
  - **Tue 8 Dec: all IN items fit, plus about 6-7 units of OPTIONAL items, plus a 1-unit reserve for Thursday's feedback.** Recommended.
  - **Tue 1 Dec: fits only with two cuts** (Portfolio money/evidence speed AR-4, and the dark theme), so about 19.2 units, no reserve, and the Portfolio stays on its pre-built ranges in the session.
- **Pushback, honestly:** French and Swahili (3.25 units) show nothing in an English session and cannot be switched on without reviewers you have not named yet; scale features (region, 100-Site rows, condensed dots; 1.25 units) are invisible with 4 demo Sites. I moved them out of IN. Your approvals of them stand; only the timing changes.

## 2. Every open item

Value = what a converting client would notice. Rec = IN client demo / OPTIONAL (if time, ranked in section 3.3) / AFTER. Source: W-n = your 2026-11-10 walkthrough item n; BL = backlog; owner dates as given. Sizes in build units (about half a lane-day each at today's pace).

### 2.1 Walkthrough comments not yet built

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| PB-1a | Cold room pages show their analysed periods on any day or week | W-11 | 1.0 | - | **High:** today a day or week reads "Unknown" everywhere; after, the 4.9 °C event and stock risk show | Cold pages look broken the moment anyone leaves the script | IN |
| PB-1b | The same for the EV depot (source judged per period) | W-11 | 1.0 | - | **High:** same as PB-1a | EV pages look broken off-script | IN |
| PB-1c | "Analysed period" line with links under the date bar | W-11 | 0.25 | PB-1a/b, SR-1; your nod | Med: says which hours the figures cover | figures without their period | IN |
| PB-4 | Days never analysed stop saying "Checked: nothing to report" | W-11 | 0.5 | - | Med: removes an over-claim a sharp client can catch | honesty defect on real Sites | IN |
| PB-7 | Coverage counts start when a Site's readings began, not 31 days back | W-11 | 0.25 | - | Med: "20 of the last 31 days have no readings" on a new Site reads as failure | Kisiwa looks unreliable | IN |
| DATA-6 | Kisiwa targets: avoidable generator minutes 0, unserved critical supply 0 | W-11 (story change) | 0.25 | DATA-1 (done) | Med: removes three "No objective declared" lines on the diesel story | the board looks unconfigured | IN |
| RM-1 | Unbuilt integrations read as a short roadmap ("Billing records are not connected yet") | W-11 | 0.5 | - | **High:** 16 error-looking values become a credible roadmap | pages read as broken, not as "coming" | IN |
| RM-2 | Hide the Findings lens chips on Cold, EV and Kisiwa | W-11 (needs approval) | 0.1 | your approval | Low-Med: removes dead "Not available yet" chips | a small dead end | IN if approved |
| PB-3 + DATA-11 | EV charging graded by charger status, plus an ordinary story week for Cold and EV | W-11 | 1.25 | PB-1 | Med (**High if the client runs EV or cold rooms**): the EV income card stops saying "Not known yet" beside USD 4.50; weeks show more than one event | one contradiction on the EV Grow card; presenter avoids it (D-E5.36) | OPTIONAL #1 |
| DATA-8 | Kisiwa productive loads (pump, cold store) and a price per kWh | W-11 (needs approval) | 0.5 | your approval | Med: Kisiwa's Grow card gains a figure | Grow empty on the diesel Site | OPTIONAL #4 |
| DATA-5 | Gateway health records for Cold, EV and Kisiwa | W-11 | 0.5 | Kobo Health recapture | Low-Med: Health tab shows "Unknown" x8 | Health tab not shown | OPTIONAL #5 |
| DATA-4 | EV site diagram: connector rating, grid meter | W-11 (needs approval) | 0.5 | your approval | Med for an EV client, else Low | "connector capacity not read" | OPTIONAL #6 |
| DATA-10, DATA-13, BL-48 | Kisiwa generator service plan; due dates on story Actions; Grow lines on days with no complete readings | W-11, BL | 0.65 | - | Low-Med: three small "not set" lines | minor gaps a client may ask about | OPTIONAL #7 |
| DATA-7 | Kisiwa simulated over whole days, not only 6 pm to noon | W-11 (needs approval) | 1.5 | your approval; +prepare time | Med: today every Kisiwa day is "partly" covered, the pattern you rejected for Kobo | a client asks why every day is partial | OPTIONAL #8 (decision 6) |
| DATA-12; EV revenue measure; work-record cost | Longer Cold failure window; EV revenue target; repair costs on work records | W-11 | ~0.25; ~1; ~1 (est.) | billing / work-order integration | Low: RM-1 wording covers them | none | AFTER |
| PF-C | Evidence coverage shown once on the Portfolio | W-2 | 0.5 | SR-1 | **High:** the opening page reads cleaner | repetition on the first page | IN |
| PF-T | Portfolio tabs (Overview, Act first, Outcomes by site, Opportunity, What changed, Scope & coverage) | W-2, W-5.1/5.2 | 1.0 | SR-1, UQ-3, v7.1 approval | **High:** the opening page | crowded first page | IN |
| PF-W | "Checked" becomes complete / partial / too few / no readings received / still processing / not analysed yet | W-3, W-5.3 | 0.75 | - | **High:** "7 of 8 hours checked" stops implying the system failed to look | the main coverage words confuse | IN |
| SR-1..3 | One shared date range at the top of every page; left menu unchanged | W-4, W-12.5 | 1.75 | v7.1 approval, UQ-1 | **High:** one control, any page, any range | each page keeps its own date form | IN |
| PF-O1, PF-O2 | Scalable "Outcomes across the estate", grouped by outcome | W-9, W-12.1/12.3 | 1.5 | PF-T | Med-High: the list shows it will handle a large estate | grid looks cramped as Sites grow | IN |
| PF-O3 | Overview card dots condense above 8 Sites | W-9 | 0.25 | PF-O1 | Low: invisible with 4 Sites | none in the demo | AFTER |
| PF-R | Region attribute on Sites, with filter and grouping | W-12.2 | 0.25 | region values | Low: the control is hidden until Sites have regions | none with 4 Sites | AFTER (IN if the client asks about regions) |
| AR-7 | Outcome rows from stored rows (for 100+ Sites) | W-9 | 0.75 | ANY-2 | Low: invisible under about 25 Sites | none in the demo | AFTER |
| T-5.4 | "Complete readings" threshold per portfolio (80% today, one global file) | W-5.4 | ~0.5 (est.) | tenant settings | Low | none | AFTER |
| T-5.5 | Outcome map as a config file (today a reviewed code table) | W-5.5 | ~0.75 (est.) | - | Low: the client never sees it | none | AFTER |
| FCF-1 | Findings card counts Cold/EV "awaiting verification"; Portfolio Cold/EV rows read "Action agreed" (with BL-47) | W-7 | 1.0 | FC (done) | Med: removes the "mini-grid Sites only" note and a gap between screens | the note stays, which is honest | OPTIONAL #2 |
| D-E5.25 | An "Act first" count on the Findings page | W-7 | 1.0 | - | Low | none | AFTER |
| PR-1/2a | Price-it, first step: "Set a price" / "What is needed" on every unpriced item, and a read-only price page with history | W-10, W-12.4 | 0.75 | mockup first | Med-High for a commercial buyer: answers "how would I price this?" on screen | presenter answers verbally; the admin tool exists | OPTIONAL #3 |
| PR-2b..5 | Price-it editing: sign-in write path, recalculation, model blocks | W-10 | 2.0 | BL-54 sign-in | Med | - | AFTER |
| UQ-0..4 | Design foundation: v7.2 sheet, tokens, 12/14 px type, Inter, light and dark themes, empty/loading states, number and date formats | W-12.1, W-13 | 4.0 | v7.2 approval | **High:** first impression, "modern" | the app looks dated next to the story | IN (dark theme cut on 1 Dec) |
| UQ-6a | Server words stored as message keys, not sentences | W-13 | 0.25 | - | none visible | stored speed rows rebuilt later (~1-2 units) | IN |
| UQ-5, 6b, 7, 8 | French and Swahili: all words into catalogues, drafts, long-text guard | W-13 | 3.25 | reviewers named | Low unless the client works in French or Swahili; nothing changes in English | none in an English session | OPTIONAL #9 (decision 2) |
| BL-69 rest | Component library, chart standard, page-by-page uplift, accessibility pass | W-12.1 | ~7.25-8.0 | UQ | Med, long term | - | AFTER (first focused work after) |
| BL-67 | Several currencies, structured tariffs, restatement notes | W-1 | 3.0-3.5 | your currency answers | Low now: demo Sites use one flat price each | - | AFTER |

### 2.2 Backlog items

| Id | What it is | Source | Size | Depends on | Value to a converting client | Risk if left out | Rec |
|---|---|---|---|---|---|---|---|
| ANY-1 (BL-66) | Site boards fast for any range (under 2 s) | owner 11-03, 11-10 | 3.0 | PB-1, PB-4, PB-7, UQ-6a | **High:** off-script boards take 10-36 s today | "try another week" stalls live | IN |
| ANY-2 core (BL-66: AR-3, AR-6, AR-4 with money receipts) | Portfolio fast for any range; Cold/EV boards under 1 s | owner 11-10 | 4.0 | ANY-1, PF-C, PF-O2 | **High:** the Portfolio is the opening page | presenter stays on pre-built ranges | IN (AR-4 cut on 1 Dec) |
| AR-5 (BL-66, with BL-64/65) | Retire pre-loading | - | 0.75 | ANY-2 | none visible | - | AFTER |
| BL-50 | Site "Why?" sees the same issues as the board | BL | 0.25 | - | Med: "Why?" is a presented beat; on the Cold failure day it misses one issue | "why" gets an incomplete answer | IN |
| DATA-1 L2 | Kisiwa finish check covers windows without a selection | DATA-1 review | 0.1 | - | none; protects the build | a bad Kisiwa day slips into the build | IN |
| PILOT-1 (new) | One page in the client script: how a client starts (onboarding steps, integration ranking D-E5.35, what sign-in adds) | Architect | 0.25 | RM-1 | **High:** a converting client asks "what happens next?" | no path to pilot on paper | IN |
| BL-54 | Sign-in, named users and roles | BL | not sized (~3-5) | - | Med: asked about, answered by PILOT-1 | - | AFTER (pilot-critical) |
| BL-53, 55, 57, 59 | Real-source clock proof; production scheduler and onboarding runbook; public upload path for the demo build; historical data import | BL | not sized | BL-54 for some | Med as questions; PILOT-1 answers them | - | AFTER (pilot-critical) |
| BL-31, BL-45 | A real later "Change made" for Cold/EV; mill Actions on the Site boards | BL | 0.5; 1.0-1.5 | - | Low-Med: the script uses Kobo and the mill route | - | AFTER |
| BL-13, BL-16, BL-56 | Days line under board rows; idle fuel in the Kobo generator law (disclosed); demo banner only on demo data | BL | 0.25; 1.0; ~0.1 | - | Low | - | AFTER |
| BL-01..05, 08, 11, 12, 15, 22, 35, 51, 58 | Clean-up, refactors, renames and internal guards | BL | ~4.0 | - | none visible | - | AFTER |
| BL-06, 07, 09, 10, 14, 17, 18, 20, 21, 23-26, 32-34, 36-44 | Story-depth edge cases not on the script (each has a presenter rule) | BL | ~5+ (several unsized) | - | Low: only off-script | covered by "present less" rules | AFTER |
| BL-30, 46, 49, 52, 60-63 | Demo tooling and test debt (BL-63 is a producer fix the build check already covers) | BL | ~1.5 | - | none visible | - | AFTER |

## 3. Sequence of the IN items

### 3.1 Two lanes (pace about 1.5 units per lane per working day, including review and one fix round; 1.25 when slow)

Lane A, server and data (10.6 units):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| A1 | PB-1a Cold analysed periods | 1.0 | 1.0 | Mon 16 |
| A2 | PB-1b EV analysed periods | 1.0 | 2.0 | Tue 17 |
| A3 | PB-4, PB-7, DATA-6 + DATA-1 L2, BL-50 | 1.35 | 3.35 | Wed 18 |
| A4 | UQ-6a server message seam | 0.25 | 3.6 | Wed 18 |
| A5 | ANY-1: AR-0 parity baseline, AR-1 stored rows, AR-2 board depth | 3.0 | 6.6 | Fri 20 |
| A6 | ANY-2: AR-3 coverage rows, AR-6 work lists | 1.5 | 8.1 | Mon 23 |
| A7 | ANY-2: AR-4 evidence and money rows with receipts (MN-1/2/3) | 2.5 | 10.6 | Wed 25 (Thu 26 slow) |

Lane B, screens (10.35 units; UQ-0 this week):

| # | Item | Size | Cum. | Done by (1.5/day) |
|---|---|---|---|---|
| B0 | UQ-0 v7.2 foundation sheet (you approve it by Mon 16) | 0.5 | 0.5 | Fri 13 |
| B1 | UQ-1 tokens, type, Inter, style ratchet | 1.25 | 1.75 | Mon 16 |
| B2 | SR-1 shared date bar (v7.1 approved by Tue 17) | 0.5 | 2.25 | Tue 17 |
| B3 | UQ-2 light and dark themes; UQ-3 empty and loading states | 1.5 | 3.75 | Wed 18 |
| B4 | PF-C, PF-W, PF-T, PF-O2, PF-O1 (Portfolio tabs, words, outcomes list) | 3.75 | 7.5 | Fri 20 |
| B5 | SR-2/3 every page on the shared range; PB-1c analysed-period line | 1.5 | 9.0 | Mon 23 |
| B6 | UQ-4 formats; RM-1 roadmap words; RM-2 | 1.35 | 10.35 | Tue 24 (Wed 25 slow) |

Shared: PILOT-1 0.25 (with the script refresh) and E-final 1.5 (one demo build, end-game suites, live checks, recapture in both themes, both scripts refreshed). **IN total: 10.6 + 10.35 + 0.25 + 1.5 = 22.7 units.**

Why this order (causal, not convenient):
1. PB-1, PB-4 and PB-7 change what boards compose, so they land before AR-0 takes its byte-for-byte baseline; otherwise ANY-1's proofs are redone.
2. UQ-6a lands before AR-1 freezes the stored-row shape (words as keys from day one).
3. **Changed from the 26-unit plan:** lane B now builds the Portfolio (B4) before moving every page to the shared range (B5), so PF-C and PF-O2 are merged by Fri 20 and AR-4 (which touches the same Portfolio read) never waits.
4. SR-1 before PB-1c, UQ-2 and UQ-4: the top bar is laid out once. SR-2 after PB-1: Cold and EV "latest event inside the range" uses PB-1's rule.
5. UQ-1 and UQ-3 before the Portfolio, so it is written on the new tokens and states and never restyled.
6. OPTIONAL items fill gaps: lane A after A7, lane B after B6.

### 3.2 Date cut-offs (working calendar; no demo build is prepared on the 3rd-5th of a month)

E-final needs **5 working days**: (1) freeze, end-game suites, fixes; (2) demo build and live checks; (3) recapture and script refresh with PILOT-1; (4) your walkthrough; (5) one fix round and rebuild, or buffer. The final build is prepared the day before the session so "yesterday arrives" can be shown live.

| Session | Build freeze | E-final days | What fits |
|---|---|---|---|
| **Tue 1 Dec** | Tue 24 Nov | Wed 25, Thu 26, Fri 27, Mon 30 (prepare Mon 30) - only 4 days, no buffer | IN minus AR-4 (2.5) and UQ-2 dark theme (1.0) = **about 19.2 units**. Portfolio money and evidence stay computed on request: presenter stays on pre-built Portfolio ranges. No OPTIONAL items, no reserve for Thursday's feedback. You approve v7.2 and v7.1 by Mon 16. |
| **Tue 8 Dec (recommended)** | Mon 30 Nov | Tue 1, Wed 2 (rehearsal build allowed on the 2nd), Thu 3, Fri 4 (walkthrough, script), Mon 7 (final prepare) | **All IN (22.7)**, plus about 6-7 OPTIONAL units in the 3 spare lane-days (Wed 25 to Mon 30), plus a 1-unit reserve for Thursday's associates' feedback. |

A session on Thu 3 or Fri 4 Dec is possible only with the final build on Wed 2 and no slip at all; I do not recommend it.

### 3.3 OPTIONAL ranking (what to add, in order, if the 8 Dec date is set)

1. PB-3 + DATA-11 (1.25, lane A): first if the client runs EV or cold rooms.
2. FCF-1 with BL-47 (1.0, lane A).
3. PR-1/2a price-it first step (0.75, lane B; mockup first).
4. DATA-8 Kisiwa productive use and price (0.5; needs approval).
5. DATA-5 health records (0.5). 6. DATA-4 EV diagram (0.5; approval). 7. DATA-10, DATA-13, BL-48 (0.65).
8. DATA-7 Kisiwa whole days (1.5; approval; adds prepare time).
9. French and Swahili (3.25): only if a reviewer is named by Fri 20 Nov and the client prefers that language.

With 8 Dec, items 1-7 fit (about 5.2 units, at the slower pace) plus the 1-unit reserve; 8 and 9 fit only if the build runs at the faster pace and the reserve is unused.

## 4. Where the 26-unit plan changes, and why

| Change | Units | Why |
|---|---|---|
| Non-Kobo fixes: placeholder 1.5 becomes 4.2 (PB-1a/b/c, PB-4, PB-7, DATA-6, RM-1, RM-2, BL-50, L2) | +2.7 | The audit reported. PB-3 goes to OPTIONAL with DATA-11: alone it shows nothing, because the EV story has only 16 min of charger status. |
| French and Swahili catalogue work (UQ-5, 6b, 7, 8) to OPTIONAL | -3.25 | Nothing changes on screen in English, no reviewer is named, and the release rule keeps both languages off until reviewed. The seam (UQ-6a) and formats (UQ-4) stay IN, so nothing is redone later. |
| AR-5 and AR-7 to AFTER | -1.5 | Invisible with 4 Sites; the in-memory outcomes route is correct up to about 25 Sites. |
| FCF-1 to OPTIONAL | -1.0 | It was already cut #2; the card's "mini-grid Sites only" note is honest. |
| PF-O3 and region to AFTER | -0.5 | Invisible with 4 demo Sites. |
| PILOT-1 added | +0.25 | A converting client needs a path to a pilot; RM-1 and the integration ranking make one page cheap. |
| Lane B order: Portfolio before SR-2 | 0 | AR-4 no longer waits for the Portfolio. |
| Calendar | - | Earlier "earliest credible Mon 30 Nov" is withdrawn: full IN needs Tue 8 Dec; 1 Dec only with the section 3.2 cut. |
| **Net** | **26.0 to 22.7** | |

## 5. Your decisions that change the scope (my recommendation in bold)

1. **Client session date. Recommend Tue 8 Dec.** 1 Dec drops Portfolio any-range speed (AR-4) and the dark theme, with no buffer and no room for Thursday's feedback.
2. **French and Swahili before the session? Recommend no: present in English.** Keep the approval; build the catalogues after the session, or as OPTIONAL #9 only if you name a native Swahili and a fluent French reviewer by Fri 20 Nov and the client prefers that language.
3. **What does the client operate (diesel or solar mini-grids, cold rooms, EV depots)? Recommend telling me before Mon 23.** If EV or cold rooms, PB-3 + DATA-11 and DATA-4 move up to IN; if mini-grids, Kobo and Kisiwa lead (D-E5.36) and DATA-8 moves up.
4. **Approve the v7.2 foundation sheet and Inter by Mon 16, and the final v7.1 Portfolio mockup by Tue 17. Recommend yes, theme follows the computer's setting.** Each day of delay moves lane B and the date by a day.
5. **Approve the item 11 story and screen changes: RM-2 hide lens chips, the "Analysed period" line, Kisiwa targets, extra Cold and EV days. Recommend yes to all.**
6. **Kisiwa whole-day simulation (DATA-7, 1.5) and productive use (DATA-8, 0.5). Recommend DATA-8 yes (OPTIONAL #4), DATA-7 after the session**, with a presenter line: "Kisiwa's recorder in this story runs 6 pm to noon, so each day is partly covered." If you find that as indefensible as the Kobo pattern, DATA-7 moves into the reserve.
7. **Scale and region (PF-O3, region, AR-7). Recommend after**, unless the client has more than about 8 Sites or asks about regions; the demo data has no large estate to show it on.
8. **Per-portfolio threshold and outcome-map config file. Recommend after**; neither is visible to a client.
