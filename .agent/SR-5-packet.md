# SR-5 packet (WIP, stopped for the VPS move 2026-11-12)

Branch `task/SR-5-range-board` (worktree `AssetOpsV1-sr5`, from main a9159c945). Spec: rev 9 §9.4 of
`.agent/architect-sequence-client-scope-2026-11-11.md`; D-SR.9-12 in `.agent/build-sheet-OWN-GAPS-2026-11-08.md`.

## State
- Landed (WIP, not run, not imported by anything yet): `backend/assetops_backend/estate/site_range.py`,
  `site_range_body(service, tenant_id, site_code, req)` on one `service.read_snapshot`, Portfolio selectors with a
  one-Site admit, `dispatch_days` (AR-3 rows / D-ANY.10 compose), D-E5.46 day states, coverage-wins consistency with
  `site_range_day_mismatch` log. No AR-4 file edited; `portfolio.py` untouched (`_scope` reachable as
  `service._scope`, a staticmethod on `EstateIndexService`, `estate/index.py:310`, so no `scope_for` alias needed).
- No tests run (no-DB or Postgres). No commit of route, fixture or tests yet.

## Resume points, in order
1. Fix `_status` in `site_range.py`: pass the evidence tuple's own domain (`e_sites[0][1]`) to `evidence_unit`,
   as `_portfolio` does (`portfolio.py:804-807`).
2. Route in `backend/assetops_backend/outcome_api.py`: `RANGE_ROUTE = "/api/sites/{site_code}/range-overview"`,
   inside `build_outcome_router` beside the board. `estate` there is already the `EstatePortfolioService`
   (`main.py:685-688`), so no `main.py` change. Order: `board_site` -> `ref.domain != MINI` 404
   `RANGE_OVERVIEW_NOT_APPLICABLE` -> `disclosed` -> `from`/`to` required (`_instant`), then
   `estate_request("portfolio", lo, hi, known_at)` (EstateRefusal INVALID_WINDOW 422) with `lens="all"`
   (dataclasses.replace) -> `estate is None` 503 `SITE_RANGE_OVERVIEW_UNAVAILABLE`. Compose maps
   `RangeOverviewNotApplicable` 404, None 404 SITE_NOT_FOUND, EstateStoreUnavailable / SiteStoreUnavailable /
   EstateRefusal status 503 -> 503 SITE_RANGE_OVERVIEW_UNAVAILABLE, other EstateRefusal by its status/code.
   Stored: `responses.serve(StoredRoute(RANGE_ROUTE, ref.tenant_id, {"site","from","to","known_at"},
   sites=(site,), watermark_sites=(site,)), compose)`; wrap in `perf.route`.
3. No-DB tests `backend/tests/test_sr5_range_overview.py`: reuse `test_cov_partial_portfolio.partial_estate`'s world
   (PortfolioSnap over `MoneySnapshot`, `site_coverage` monkeypatched to `test_cov_partial.Snap(PARTIAL_DAYS, ...)`;
   the PortfolioSnap also needs `dispatch_days` returning PARTIAL_DAYS and `finding_index`). Pin: coverage entry and
   partial money equal the Portfolio's `coverage.sites[KOBO]`; days gap set == `coverage.days.gaps`; Cold/EV 404;
   bad window 422; empty scope 404; day precedence table unit test on `_day_state`.
4. Contract golden `backend/tests/fixtures/sr5_range_overview/kobo_partial.json` from that world (regen env var,
   like `test_ch5a1_board_contract.py`).
5. WARM-1: add `range-overview` to `tools/warm_ranges.py` if WARM-1 merged first.
6. Postgres (one file at a time, `tools/run-host-tests.ps1`, own `*_test` DB): range body vs Portfolio entry; rows
   on vs off (`coverage.dispatch_rows_provider` set / None).
7. Merge gates on a scratch `<prefix>_audit` copy (one heavy job): 0 mismatches vs Portfolio, rows-on vs rows-off,
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
- (d) demo mini-grid Sites/window, (e) Financials frame file, (f) RANGE_MATRIX route list: not yet surveyed.
