# SR-5 packet (WIP, stopped for the VPS move 2026-11-12)

Branch `task/SR-5-range-board` (worktree `AssetOpsV1-sr5`, from main a9159c945). Spec: rev 9 §9.4 of
`.agent/architect-sequence-client-scope-2026-11-11.md`; D-SR.9-12 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`.

## State (VPS, 2026-11-12 evening)
- SR-5a server code committed (116eefafc): `estate/site_range.py` (`_status` now takes each scope tuple's own
  domain and the Site's per-site money lines, as `_portfolio`, `portfolio.py:801-818`; `money.partial` uses the
  same per-site lines as the Portfolio's coverage entry, `portfolio.py:856-858`), route `RANGE_ROUTE` in
  `outcome_api.py` (`_range_overview`), no `main.py` change (`estate=estate_portfolio`, `main.py:685-688`).
- No-DB tests `backend/tests/test_sr5_range_overview.py`: 29 passed (body vs Portfolio coverage entry and partial
  money; gaps == `coverage.days.gaps`; finding day; golden `fixtures/sr5_range_overview/kobo_partial.json`, regen
  `ASSETOPS_REGEN_SR5_GOLDEN=1`; 422 x5; Cold/EV/unknown 404; empty scope 404; 401/403; 503 store down and no
  estate; stored key/watermark/perf line; 12-row precedence table). Non-vacuous: disabling coverage-wins plus the
  NOT_ANALYSED rule fails 5 tests. Adjacent: cov_partial(_portfolio), out_b4_route, ch5a1_board_contract,
  qw1_perf: 60 passed.
- Spec deviation (route test file name): one file `test_sr5_range_overview.py` holds both the body and the route
  tests the spec splits into `..._route.py`.

## Update after rev 10a (D-SR.19-30)
- 034852bb2: day rule extracted to `backend/assetops_backend/estate/range_days.py` (D-SR.22):
  `range_day_states(snap, tenant_id, site, req, scope, cov) -> {date: {"state", "row"}}`, step 6 = ANALYSED,
  coverage-wins logged `site_range_day_mismatch`; `site_range.py` maps ANALYSED to FINDINGS/CLEAR. SR-6 merges
  this commit. D-SR.28: `CLOSED_LABELS` imported from `site_outcomes/mini.py`; `findings.count` null unless F is
  COMPLETE/EMPTY or the status is PARTIAL. No-DB file: 31 passed (adds coverage-wins log pin, finding_known pin).
- 66b800d3e: `backend/tests/test_sr5_range_overview_postgres.py` on `assetops_sr5_test`: 2 passed (re-run on
  034852bb2: 2 passed). Pins on the S4 F01 world (2 days): coverage entry, partial money and status equal the
  Portfolio's; days FINDINGS/NOT_ANALYSED equal the coverage gaps; rows on (provider served, every day an absent
  run, provider proven called) == rows off (D-SR.16).
- Still to add to the Postgres file (needs fixture work beyond the S4 cases): NO_READINGS / READINGS_CONFLICT /
  STILL_PROCESSING / NOT_EXPECTED days, the overlap day (OVERLAPPING), drill-in vs `/overview?date=D`.
- Gates waiting for the demo build on `assetops_polish_vps1_test` and WARM-1: parity (KOBO-001, KISIWA-001;
  7/14/31 days ending on the last complete UTC day with readings, D-SR.29; mismatch log count in the JSON),
  rows on/off on real data, stored <= 2.0 s.

## Update after rev 10b/10c (main 9afb0bcee merged)
- `test_sr5_range_overview_postgres.py` on `assetops_sr5_test`: **5 passed** (75 s); without the DB 5 skipped. Existing
  worlds only: S4 F01 (+ the stale step -> STILL_PROCESSING for an open job and for an unmatched day; + chain
  backfill step (a) with the real `EstateClaims.day_grades` -> NO_READINGS both days), and all S4 cases + the clean
  day (21 days: FINDINGS, CLEAR, NOT_ANALYSED; totals; Portfolio coverage/card/partial/status equality; gaps ==
  coverage; coverage-wins log pinned on F08's 10-19 READINGS_CONFLICT; drill-in vs `/overview?date=D`).
- Not reached on any existing Postgres world (question, not designed around): NOT_EXPECTED (S4 worlds hold no
  readings, so grades are NO_DATA, never before-first-reading); READINGS_CONFLICT with day grades on (needs a
  graded day with readings plus an ambiguous cohort; MD-0 `--variant states` template may have it, but it needs a
  ~15 min template build and cloned DBs outside `assetops_sr5_test`); SUMMED / OVERLAPPING day money (no priced
  mini-grid line in the S4 worlds; `overlap_group` fixtures exist for EV only).
- Spec conflict found (Architect): drill-in check fails on 10-21. F05's Finding there is NO_LONGER_SUPPORTED; the
  range day counts MEMBERS (SUPPORTED/UNCONFIRMED, §9.4), so CLEAR, while the one-day board's `known_finding`
  selects the latest revision of every canonical Finding, so it shows one. Test pins the disagreement set
  == {10-21} and its lifecycle; which side changes is for the Architect.
- No-DB: sr5 + cov_partial(_portfolio) + ch5a1_board_contract: 77 passed. check-all: All 19 guards passed (2nd run; the 1st hit my 900 s cap at load ~12).

## Resume points, in order
1. DONE. Fix `_status` in `site_range.py`: pass the evidence tuple's own domain (`e_sites[0][1]`) to `evidence_unit`,
   as `_portfolio` does (`portfolio.py:804-807`).
2. DONE. Route in `backend/assetops_backend/outcome_api.py`: `RANGE_ROUTE = "/api/sites/{site_code}/range-overview"`,
   inside `build_outcome_router` beside the board. `estate` there is already the `EstatePortfolioService`
   (`main.py:685-688`), so no `main.py` change. Order: `board_site` -> `ref.domain != MINI` 404
   `RANGE_OVERVIEW_NOT_APPLICABLE` -> `disclosed` -> `from`/`to` required (`_instant`), then
   `estate_request("portfolio", lo, hi, known_at)` (EstateRefusal INVALID_WINDOW 422) with `lens="all"`
   (dataclasses.replace) -> `estate is None` 503 `SITE_RANGE_OVERVIEW_UNAVAILABLE`. Compose maps
   `RangeOverviewNotApplicable` 404, None 404 SITE_NOT_FOUND, EstateStoreUnavailable / SiteStoreUnavailable /
   EstateRefusal status 503 -> 503 SITE_RANGE_OVERVIEW_UNAVAILABLE, other EstateRefusal by its status/code.
   Stored: `responses.serve(StoredRoute(RANGE_ROUTE, ref.tenant_id, {"site","from","to","known_at"},
   sites=(site,), watermark_sites=(site,)), compose)`; wrap in `perf.route`.
3. DONE. No-DB tests `backend/tests/test_sr5_range_overview.py`: reuse `test_cov_partial_portfolio.partial_estate`'s world
   (PortfolioSnap over `MoneySnapshot`, `site_coverage` monkeypatched to `test_cov_partial.Snap(PARTIAL_DAYS, ...)`;
   the PortfolioSnap also needs `dispatch_days` returning PARTIAL_DAYS and `finding_index`). Pin: coverage entry and
   partial money equal the Portfolio's `coverage.sites[KOBO]`; days gap set == `coverage.days.gaps`; Cold/EV 404;
   bad window 422; empty scope 404; day precedence table unit test on `_day_state`.
4. DONE. Contract golden `backend/tests/fixtures/sr5_range_overview/kobo_partial.json` from that world (regen env var,
   like `test_ch5a1_board_contract.py`).
5. PENDING (WARM-1 not on main yet, no `tools/warm_ranges.py`). WARM-1: add `range-overview` to `tools/warm_ranges.py` if WARM-1 merged first.
6. DONE except the states above (see "Update after rev 10b/10c"). New file `backend/tests/test_sr5_range_overview_postgres.py` (spec fixture:
   7 days FINDINGS/CLEAR/NO_READINGS/READINGS_CONFLICT/STILL_PROCESSING/NOT_EXPECTED, overlap day OVERLAPPING,
   Portfolio equality on a one-Site estate, drill-in vs `/overview?date=D`, rows on/off incl. one absent-k row,
   D-SR.16). Run: `cd backend && ASSETOPS_TEST_DATABASE_URL=postgresql+psycopg://assetops:assetops-local-dev@127.0.0.1:55432/assetops_sr5_test
   /opt/assetecon/AssetOpsV1/.venv/bin/python -m pytest -q tests/test_sr5_range_overview_postgres.py` (PYTHONPATH as lane
   rules; env var per `backend/TESTING.md:44`). Postgres (one file at a time, `tools/run-host-tests.ps1`, own `*_test` DB): range body vs Portfolio entry; rows
   on vs off (`coverage.dispatch_rows_provider` set / None).
7. PENDING, DB. Merge gates on a scratch `<prefix>_audit` copy (one heavy job): 0 mismatches vs Portfolio, rows-on vs rows-off,
   each analysed day vs the one-day board -> `.agent/SR-5-parity.json`; stored response <= 2.0 s per range.
8. Then SR-5b/e/c/d (page parts) after SR-4 merges.

## Pre-flight questions (one batch, Architect) and the safe readings used
- (a) `_scope`, `read_snapshot`, `select_*`, `progress` exist as named. One-Site admit vs estate run coverage
  entry: same `site_coverage` call per Site, so expected equal; to be proven by test 6.
- Status needs `select_evidence_scope` (the Portfolio's status uses E units); added to the one snapshot. OK?
- `actions.open` is not defined by `progress()`. Safe reading: Actions whose `workflow_label` is not Verified /
  Resolution withdrawn, null unless Action coverage is complete. `actions.awaiting_verification` =
  `pending_trial_count`.
- `findings.awaiting_verification`: FC-2's rule (`snap.awaiting_verification` over the Site's selected pairs).
  `findings.count` is numeric over rows read (FC-2), not nulled like the Portfolio's estate `finding_count`. OK?
- (c) Grades are Site-local dates; mapped to the UTC dispatch day of the same date (coverage's own D-E5.42 rule,
  `coverage.py:199-212`).
- Unmatched selected day: spec step 5 says NOT_ANALYSED; coverage treats it as PENDING (not a gap), so the code
  says STILL_PROCESSING to keep the coverage-equality rule. Confirm.
- Coverage-wins when coverage does not list a day the day rule calls a gap: the day falls to FINDINGS/CLEAR and is
  logged. Confirm, or prefer STILL_PROCESSING.
- (d) Demo mini-grid Sites: KOBO-001 and KISIWA-001 (spec). Demo DB and data window need the DB to confirm
  (handoff names `assetops_polish_client7_test`; Kobo 11-10 half-loaded); ranges then end on its last data day.
- (e) Financials frame: `frontend/src/shell/SiteAnalyticsFrames.tsx:1403` `SiteFinancialsFrame` (view
  "overview", `App.tsx:466`); price list in `sites/SiteFinancials.tsx`; prices route `SitePricesFrame`.
- (f) RANGE_MATRIX: Site routes from `App.tsx` route constants; not classified by rev 10.5 (D-SR.17, to the
  Architect): opportunities/:opportunityId, actions/:actionId(/:actionView), domain-actions/:id/verification
  (mill), domain-actions/:id/fuel-verification, fuel-findings/:findingId, work/incidents + work/maintenance
  subtabs, foundation/changes/:changeId, performance/:capabilityId subtabs other than Dispatch/Service/Renewable,
  /maintenance/requests/:caseId(/record|/history), Cold/EV assets ("TO FINISH ON VPS").

## Fix round D-SR.50 / 10d.10 (server)
- `site_range.py`: each day gains `retired_finding_count` (non-member latest revisions from the same `f_rows` read and `intersects` rule; null on gap days); `dispatch.days_with_retired_findings` added. State stays CLEAR. `f_rows` carries lifecycles, no second query.
- Postgres 10-21 pin now asserts agreement (board Findings = finding_count + retired_finding_count; 10-21 CLEAR, finding_count 0, retired 1; F05 NO_LONGER_SUPPORTED). Dispatch totals pin gained the new key.
- No-DB stubs: `_sum_lines` SUMMED / OVERLAPPING / NO_ELIGIBLE_LINES / CURRENCY_MIXED; retired-count shape test. Golden `kobo_partial.json` regenerated (new keys only).
- Results: no-DB file 33 passed; Postgres file (assetops_sr5_test) 5 passed, 66 s.
- Not done (page): row wording "Checked: no current findings · 1 finding no longer supported" and the totals line live in the range page, which is not in this server round; the API fields it needs are in place.

## Review fix round (SR-5 server review, 2026-11-12)
- M1: `test_day_money_composes_per_day_through_the_body` runs priced stub lines through `site_range_body` (SUMMED day 0,
  OVERLAPPING day 1, NO_ELIGIBLE_LINES day 2, WITHHELD on a gap day holding a line; `world` dispatch rows). Proven: with
  `day_lines = []` at the per-day filter it fails; reverted.
- M2: `findings.confirmed` and `findings.not_confirmed` are null whenever `findings.count` is null (10a.4 / D-SR.28, as the Portfolio).
- L1: malformed `known_at` -> 422 `INVALID_KNOWN_AT` (outcome_api range route). L2: guard removed, retired-count test non-zero
  (retired head on day 1). L3: no-DB pin of "coverage names no gap" -> ANALYSED + logged.
- D-SR.56 (wording only): a NOT_EXPECTED day with `accepted_reading_count > 0` keeps its state and carries
  `note: "Readings began late this day · not counted"` (key absent otherwise; golden unchanged). The page shows `note` in place of
  "Before readings began". One no-DB test.
- **Parity spec addition (D-SR.56).** `.agent/SR-5-parity.json` gains `not_expected_with_readings: [{site, day, accepted_readings,
  readings_began_local, readings_began_utc}]`. Gate: at most one such day per Site, and it must be the UTC day whose date is the last
  local day before `readings_began`; any other day, or more than `12 x UTC offset hours` readings on it (36 for UTC+3), fails the
  gate (the mapping would be wrong beyond the zone edge). The existing comparisons (gap set == coverage gaps, members == Portfolio)
  stay; they cannot see this, as both sides share the mapping.
