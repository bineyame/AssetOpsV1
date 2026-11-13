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
- `backend/tests/test_sr7_service_range_postgres.py` WRITTEN, on `assetops_sr7_test`: **2 passed** in 72 s (day 1 derived from 24 `mini-service/2` heads via `CriticalServed` = 144/156.0/12.0 kWh, 24 h; PARTIAL 5.5 h of 8; NO_VALUE; LOW -> NOT_ENOUGH_READINGS value hidden/not counted; NO_DATA; absent row; totals 164/12.0/176.0, 2 of 6 days; stored (first serve + hit) == live). Depends on Q-J1 (UTC dates as local days) and Q-J2 (LOW never counted). Not done: the 3 sampled hours vs `/performance/mini/service` CRITICAL rows.
- (superseded plan) `test_sr7_service_range_postgres.py` (needs `mini_service` heads → chain snapshots; start from
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

## D-SR.45 folded (Q-J1-5 confirmed)

- J2: service-range day rows carry `partial` (true for a counted PARTIAL day); pinned in the no-DB test (13 passed) and the Postgres test (2 passed, 111 s).
- J4: `test_each_row_link_opens_to_a_200` added to the claim-limit Postgres test (3 passed, 22 s): each selected-day link's one-day claim-limit data route returns 200. The page link itself (`/sites/{code}/evidence?...`) is a frontend route and is not fetched.
- Parity must report per Site the days with readings but no `critical_served` row (not yet run; waits for the DB slot).

## Pages (lane J, branch `task/SR-7-11-pages` from main e8f2bdea5)
Commits: 5a3767899 (SR-7 pages), f7ea60304 (review L1-L3 pins). SR-11 page: 8e8bb73d8 (see SR-11 packet).
- **Service range view** `sites/MiniServiceRange.tsx` (MOCK DEVIATION R725). `MiniService` (`MiniPerformance.tsx`) branches on
  `miniRangeView` (`miniDepthClient.ts`): a valid shared range with no `day=` and not one Site-local clock hour (new
  `isOneLocalHour`, also used by `serviceWindowFromParams`) reads `service-range` with the range's instants + `known_at`.
  Status line: "{served} critical load served, {unserved} not served, for n of m days analysed · <gap days>"
  (D-E5.45 grouping, >3 gap days counted). Day table: Day / Served / Not served / Hours covered / State / "Open the 12:00
  hour" (server `hour_link`). Counted days show values; every other state spans the row in words (NO_VALUE "No
  critical-load figure for this day", D-SR.26; NO_READINGS "No readings received for this day"; NOT_ENOUGH_READINGS;
  STILL_PROCESSING "Still being prepared"; NOT_EXPECTED). A counted `partial` day reads "· Partial day: x h of y h covered"
  plus a status count (D-SR.45 J2). Line "Delivered load and interruptions: open a day."
- **Claim limit range** `sites/ClaimLimitRange.tsx` inside `EvidenceClaimLimit.tsx`: no `day` + valid range →
  `claim-limit-range` table (Day / What the readings support / Reading gaps / "Open this day"); NO_SELECTION row has no
  link; a ceiling is shown only from `current_ceiling` (server `ceiling_statement` is system wording and is not shown).
  `day` present → the existing one-day section plus "Back to the whole range" (drops day/revision, keeps range and view).
- **Shared:** `sites/siteRangeClient.ts` (service/backup/claim-limit range reads; 503 `SITE_*_RANGE_UNAVAILABLE` or
  `TEMPORARILY_UNAVAILABLE` retried after 2/4/8 s with "Temporarily unavailable. Retrying…", then "Still unavailable.
  Refresh to try again."); `sites/SiteRangeParts.tsx` (read hook, refusal words, `gapDaysText`, `BackToRange`).
- **D-SR.57:** WindowSpan was already gone from the Service hour view (SR-4 fix round 2); the range view declares nothing
  (bar "All pages"); the hour view declares once (FocusPicker): vitest in `miniServiceRange.test.tsx` counts mounted
  declarers via a wrapped `rangeFocus` (0 in the range view, 1 in the hour view).
- **Back to the whole range (labelled reading):** the hour address names only its hour (server `hour_link`; D-SR.57 L3),
  so the "Open the 12:00 hour" link carries the whole range in react-router history state; the hour page's Back uses it,
  else the range its address names (its own day); a `day=` drill-in drops `day`. The link sits inside the hour bar
  (`.site-date-bar`) so the v69 panel-order guard is unchanged.

### Tests (vitest, one file or small sets; tsc clean)
- New: `miniServiceRange.test.tsx` 8, `claimLimitRange.test.tsx` 11.
- Re-pinned (positive, none deleted): `miniServiceRoutes` "two-hour address" and the R313 "unprovable cause" (an
  off-clock hour) now open the range view for their day (2 cases); `siteRangeTags` bare Service = "All pages", story hour
  = "Showing 9 Nov"; `sr2RequestUrls` SR-4 H-1 Service-under-Yesterday → new describe: Service Yesterday and 7 days at a
  cutoff send exactly `service-range?from&to[&known_at]`, no `/performance/mini/service`.
- Backend no-DB (review L1-L3): `test_sr7_service_range.py` 14, `test_sr7_claim_limit_range.py` 11 passed (L2 non-vacuous:
  `local_days` in the route → 1 failed, reverted).
- Not done: `RANGE_MATRIX` D→R — the matrix (SR-5e, `ui/rangeMatrix.ts`) is not on main; nothing to flip.
- **Fix round (coordinator, plain words):** `EvidenceClaimLimit` refusal disclosure showed "CODE: message"; now the
  message only. `evidenceClaimLimit.test` refusal table asserts no code string in the section text (old source: 6 failed).
  Wording question Q-J7 below.
- `test/settled.ts` registers "Loading the days of the date range."; `v01bEvidenceVisual` re-pinned (range read replaces
  the no-selection line); the range caption is a `<p>` (the panel keeps one heading).
- **Checks:** App-level Site + Site-href + `sites/__tests__/mini*` vitest, 122 files in 16 batches of 8: 3163 tests,
  2 failures (V-01b, a settle race in `claimLimitRange`), both fixed and rerun green (132 passed). tsc clean.
  check-all: for coordinator.
- **Questions:** Q-J6 (SR-11 sequences table, see SR-11 packet). Q-J7: the one-day claim-limit read's 503 keeps its
  existing plain sentence ("The assessment store could not be read…"), not a retry: retrying the one-day read is outside
  this slice; confirm or rule. Cold/EV Evidence pages that render this section would show the range read's 404 words
  ("…read for mini-grid sites only") if any reaches it with a range; confirm whether to hide instead.

## Fix round (review SR-7-11-pages-review.md; D-SR.76)
- M-1: register rows R725 and R728 added to `.agent/mock-departure-register.md`.
- Q11: the one-day 503 sentence stays, no retry. A 404 `CLAIM_LIMIT_RANGE_NOT_APPLICABLE` (Cold/EV) now hides the claim-limit
  section (`EvidenceClaimLimit` `hidden`, `ClaimLimitRange` `onNotApplicable`); the not-applicable string stays only for other 404s.
  Vitest in `claimLimitRange.test.tsx`.
- Hour addresses: a non-whole-day address (two hours, off the clock hour) opens the day table with the frame "Whole days that
  include the selected time" (`WHOLE_DAYS_FRAME`, `isPartialDayAddress`); D-SR.40's two-hour tests re-pinned with the frame, none deleted.
- L-2: hour picker Apply keeps `location.state` (Service and Backup); test in `miniServiceRange.test.tsx`.
- L-3: backup fields removed from the service-range test stub.
- Checks: vitest 9 files / 123 tests pass (touched + miniService*/miniBackup*/siteEvidence*/sr2RequestUrls/siteRangeTags/v01bEvidenceVisual/miniFuelRoutes); tsc clean. check-all: for coordinator.
