# WARM-1 packet: warm every date-bar range (labelled workaround)

- **Task:** rev 7 §7.1 of `.agent/architect-sequence-client-scope-2026-11-11.md`, ruling D-17N.1. Packet questions answered by **D-WARM.1-6** (`build-sheet-OWN-GAPS-2026-11-08.md`, main 506eae7fc).
- Reverses D-ANY.3 for the 17 Nov build only.
- **Branch:** `task/WARM-1-range-warm`, from main e42af8411. Main not merged in since.
- **Laptop phase done:** code and no-DB tests. **Merge gate not yet run** (VPS).
- **Claim wording (D-WARM.2):** "≤2 s on every stored request of every clickable range".

## Pre-flight answers (from code)

- **Preset query strings.**
  - `frontend/src/ui/sharedRange.ts` `presetRange` gives full UTC days ending yesterday, taken from the browser's `Date.now()`.
  - No demo clock: the store clock is `read_scope.clock()`, wall UTC.
  - Apply writes `from=YYYY-MM-DDT00:00:00Z&to=<day after last>T00:00:00Z` (`rangeParams` / `URLSearchParams`: `:` becomes `%3A`).
  - `7dwork` is offered on Work pages only, and those are not stored routes.
- **Day boundary:** UTC for every range. Kobo and Kisiwa boards read one day (`date=`).
- **Requests per page.**
  - `estateQueryString` drops `lens=all` and `state=all`. The store keys on the parsed request (`parsed_key`), so defaulted twins share a key.
  - Portfolio, every PF-T tab: `/api/estate/portfolio?from&to&limit=50`. Act first lens chips add `&lens=cost|risks|opportunities`.
  - Portfolio summary: `/api/estate/outcome-summary?from&to`.
  - Findings page 1: `/api/estate/findings?from&to[&lens=..]`.
  - Cold and EV boards, and their Site Findings warnings panel: `/api/sites/{code}/outcome-board?from&to`.
  - Kobo and Kisiwa Site Findings panel: `?date=miniBoardDay(to)`.
  - Kobo and Kisiwa Site Overview board: `?date=D` is warmed for each mini-grid day. On a day with an intersecting Finding the page adds `finding_id` and `finding_revision_id` (a different board key), so those pinned requests are not warmed (see the outside list).
- **DS-1f `links`:** `demo_combined.py links` (`story_links`). Its API requests are `<work>/prebuilt-routes.json` (`prebuilt_routes`), which is part 3 of the set.

## What landed

- **`tools/warm_ranges.py`** (new).
  - `plan()` orders the stored requests:
    1. the 5 presets, plus their Findings lens pages (D-WARM.5);
    2. every 7/14/30/31-day window, newest first;
    3. mini-grid days;
    4. the story list, plus the story ranges' Findings lens pages;
    5. (review M1) every story window on UTC midnights, incl. the S day, the month and windows before the data window, gets the full `range_requests` set (Findings page 1, Cold and EV boards). `--verify` replays the same plan.
  - `unstored_plan()` (D-WARM.2) lists the unstored reads for the presets and the story ranges:
    - estate `scope`, `actions`, `evidence`, `financials`;
    - Kobo and Kisiwa: `overview?date=` and `findings?from&to`;
    - Cold and EV: `cold|ev/overview?from&to` and `cold|ev/findings?from&to`.
  - `run()`:
    - `--workers 4`;
    - before each batch, waits while `pg_stat_activity` is above 150;
    - retries 2/5/10 s on 503, `stale`, `race`, `unstored` or `composed` (D-WARM.6).
  - `--verify`:
    - 1 worker, client-side ms;
    - passes only on 100% `hit` and max ≤ 2000 ms;
    - also times the unstored reads under `report.unstored`, outside `pass`.
  - Report: `warm-report.json`, with `reasons` per failing request (D-WARM.6).
  - `--dry-run [--list]` counts and sends nothing.
- **Prebuild HTTP mode (BL-71 part 2).**
  - `chain/prebuild.py` uses an HTTP client when `ASSETOPS_PREBUILD_BASE_URL` is set.
  - The client is `chain/adapters/http_prebuild_client.py`, wired through `chain/composition.build_prebuild_http_client` (the adapter-seam guard).
- **`tools/demo_combined.py` `serve`.**
  - Once the API answers, each tick's prebuild runs over HTTP.
  - After each tick it starts `warm_ranges` in the background (`start_warm`, log `logs/warm-{port}.log`) when none is running.
  - `serve --no-warm` turns this off.
- **`backend/tests/test_warm1_ranges.py`:** 18 tests, no DB.

## Checks (laptop, bd3568399)

- `test_warm1_ranges.py`: 18 passed.
- Adjacent no-DB files: 54 + 112 passed, 4 skipped. Files:
  - `test_infra1_degraded_store`, `test_ch5c_store_off`;
  - `test_dd1b2b_drain`, `test_dd1b2b_drain_failure`;
  - `test_ch5c_env_parity`, `test_e4_prebuilt_routes_generator`, `test_e4_performance_on_change`;
  - `test_demo_combined_links`, `test_demo_combined_ex1`, `test_own_g1_add_dates`;
  - `test_dd1b1_prepare_clock`, `test_ar2_prepare_period_rows`.
- **Non-vacuous proofs.** Each mutation was made on committed code, run, then reverted with `git checkout`:

  | Mutation | Result |
  |---|---|
  | preset 7d set to today-6 | 2 failed |
  | verify's >2 s rule removed | 1 failed |
  | throttle disabled | 1 failed |
  | preset lens pages removed | 1 failed |

- **`check-all.ps1`, first run (07:59, pre-fix):** 4 of 19 failed.
  - Architecture seams and the estate guard self-tests: both flagged `urlopen` in `chain/prebuild.py`. Fixed: the client moved to `chain/adapters`, then wired through composition.
  - Re-run after the fix: `check-architecture.ps1` passed (with `ASSETOPS_GUARD_PYTHON` set); `tools/checks/test_estate_guard.py` 16 passed (21m53s).
  - Missing-claim scan and its fixtures: `frontend/node_modules` is absent in this new worktree (`Cannot find module 'typescript'`). That is environment, not code. On the VPS, run it after `npm ci`.
- **Postgres:** none run. **Gate run: not run** (VPS).

## Dry run on client4 (read-only, `AssetOpsV1-e3c/var/polish_client4`, `--today 2026-11-17`)

- **Sites:** KOBO 10-11..11-09, EV 10-20..11-03, KISIWA 10-30..11-08, COLD 11-01..11-09. Data window 10-11..11-09.
- **47 ranges, 469 stored requests:**
  - 191 Portfolio;
  - 49 summary;
  - 72 Findings, of which 24 are lens pages;
  - 157 boards.
- **Unstored (verify only):** about 66 per the 5 presets, plus 12 per story range.
- **Estimated cold warm** (AR-4 cold figures, times 6 estate requests per range): about 3,900 s serial, so **about 16-25 min** with 4 workers.
- A DB brought up to 16 Nov gives about 75 ranges and **about 25-35 min**.
- A re-warm with nothing changed is all hits, under 1 min.

## Resume points (VPS)

1. Restore client4, then `npm ci` in `frontend/` (for check-all). Run `tools/check-all.ps1 -Python <venv python>`; expect 19/19.
2. Serve:
   ```
   python tools/demo_combined.py --db <client4 db> --work var/polish_client4 serve --port <p> --web-port <w>
   ```
   It warms after the first tick. To warm by hand instead:
   ```
   python tools/warm_ranges.py --base-url http://127.0.0.1:<p> --work var/polish_client4 --db-url <url>
   ```
   Record the warm `wall_seconds`.
3. Run `... --verify` (writes `<work>/warm-verify.json`, not serve's `warm-report.json`; run it under `serve --no-warm` after a manual warm, so no background warm competes).
   - **Gate:** `pass: true`, `hit_percent` 100, `max_ms` ≤ 2000, `degraded` [].
   - Copy `unstored.max_ms` and `unstored.over_2s` into the packet. Any of those over 2 s goes to the presenter notes and to the Architect as a finding. It is not a blocker (D-WARM.2).
4. A miss: compare `reasons` and `url` with the page's network request.
5. A fresh Claude reviewer; the packet gets the gate numbers.
6. **Demo day, 17 Nov (D-WARM.3).** These are coordinator checklist items, not code:
   - The final warm runs that morning, after 00:00 UTC and after that morning's add-dates or drain.
   - `--verify` passes within 60 min before the session. Record the time and `wall_seconds`.
   - No data change before the field beats.
   - MB-1's feed stays off until its beat (D-WARM.4).

## Outside the ≤2 s claim (D-WARM.5, accepted)

- Custom ranges outside the set;
- `known_at` ranges;
- Portfolio page 2 and later;
- chain "Why?" routes outside `prebuilt-routes.json`;
- `7dwork`;
- a Portfolio visit after the MB-1 or UP-1 field beats;
- the unstored reads (measured, not gated);
- the Site Overview board with a Finding pin (`finding_id`/`finding_revision_id`) on mini-grid Finding days (ANY-1 gates it cold);
- a Cold or EV Site page opened with no range (parameterless board request).

## Residual risks

- **The mini-grid Site Findings read path is an inference.** It is `/api/sites/{code}/findings?from&to`, from D-WARM.2's wording. `siteAnalyticsClient.getSiteFindings` sends no query. A mismatch only affects an ungated timing.
- **Estimates are from AR-4 single-request figures.** The 4-worker contention on one Postgres has not been measured.

## Review fix round (VPS, review-vps.md)

- M1 fixed (`midnight_range`, `plan`); no-DB test `test_story_windows_get_every_page_site_request` fails on the old `warm_ranges.py` (checked by stashing it: 2 new tests failed, 18 passed), passes now.
- L1 wording corrected above. L3: `report_path`, test `test_verify_report_has_its_own_default_file`.
- L4: the warm child starts with `start_new_session=True` on POSIX. The API Popen on main has the same group pattern (a kill of the API's group would reach serve); left alone, noted for the coordinator.
- **L2 -> D-WARM.7 (coordinator ruling):** `range_requests` now also warms `/api/estate/findings?from&to&state=<v>` for the four chip values and `/api/estate/portfolio/scope-ids?from&to` page 1 (the all-lens disclosure), per warmed range; `--verify` replays them. URL equality: `test_state_chip_and_scope_ids_urls_equal_the_frontend_request` and `frontend/src/estate/__tests__/warmUrls.test.ts` (the real client, same literals).
- **Added to outside the claim:** lens x state combinations, `scope-ids` page 2+, and `scope-ids` under a non-all lens (the ruling names one query per range; say if lens variants should be warmed).
