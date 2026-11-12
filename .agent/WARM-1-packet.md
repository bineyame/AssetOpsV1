# WARM-1 packet: warm every date-bar range (labelled workaround)

Task: rev 7 §7.1 of `.agent/architect-sequence-client-scope-2026-11-11.md`, ruling D-17N.1 (`build-sheet-OWN-GAPS-2026-11-08.md`). Reverses D-ANY.3 for the 17 Nov build only. Branch `task/WARM-1-range-warm` (from main e42af8411). Laptop phase done: code and no-DB tests. **Merge gate not yet run** (VPS).

## Pre-flight answers (from code, not guessed)

- **Preset query strings.** `frontend/src/ui/sharedRange.ts` `presetRange` uses full UTC days ending yesterday, from the browser's `Date.now()`. There is no demo clock: the store's clock is `read_scope.clock()` = wall UTC. Apply writes `from=YYYY-MM-DDT00:00:00Z&to=<day after last>T00:00:00Z` (`rangeParams`, `URLSearchParams`, so `:` becomes `%3A`). `7dwork` is offered on Work pages only, and no Work page is a stored route, so it is not warmed.
- **Day boundary:** UTC for every range. Kobo and Kisiwa boards read one day, `date=`.
- **Requests per page** (`estateQueryString` leaves out `lens=all` and `state=all`; the store keys on the parsed request, `response_store.parsed_key`, so defaulted twins share a key):
  - Portfolio, every PF-T tab: `/api/estate/portfolio?from&to&limit=50`. The Act first lens chips add `&lens=cost|risks|opportunities` before `limit`. The page also sends `/api/estate/outcome-summary?from&to`.
  - Findings index page 1: `/api/estate/findings?from&to`.
  - Cold and EV Site board, and their Site Findings warnings panel: `/api/sites/{code}/outcome-board?from&to` (`coldWindowFromParams`).
  - Kobo and Kisiwa Site Findings warnings panel: `?date=miniBoardDay(to)`, which is the range's last day. Their Site Overview board reads the served day (`SiteOverview.tsx` `servedSelection`), not the range, so every day of each mini-grid Site is warmed.
- **DS-1f `links`:** `tools/demo_combined.py links` prints `story_links` (DS-1f only changed `demo-script-client.html`). Its API requests are already `<work>/prebuilt-routes.json` (`prebuilt_routes`), and WARM-1 replays that file as part 3 of the set.
- **Stored routes** (the only ones that can be a hit): estate portfolio and scope-ids, outcome-summary, estate findings, the Site outcome-board, and the chain/why routes. Not stored: `/api/estate/scope` (sent by the Findings page), the Site overview and evidence reads, Site findings, actions, evidence, financials.

## What landed

- `tools/warm_ranges.py` (new): `plan()` builds the range set (5 presets, then every 7/14/30/31-day window newest first, then mini-grid days, then the story list, de-duplicated). `run()` uses `--workers 4`, waits while `pg_stat_activity` is above 150 before each batch, and retries 2/5/10 s. `--verify` replays each request once with 1 worker and records client-side ms. Both write `warm-report.json`. `--dry-run [--list]` counts and sends nothing.
- `backend/assetops_backend/chain/prebuild.py`: HTTP mode (BL-71 part 2). When `ASSETOPS_PREBUILD_BASE_URL` is set, it uses `HttpClient` instead of the in-process `TestClient`.
- `tools/demo_combined.py` `serve`: once the API answers, it sets `prebuild_base`, so each tick's prebuild env gets the base URL (HTTP). After each tick it starts `warm_ranges` in the background (`start_warm`, log `logs/warm-{port}.log`) unless one is already running. `serve --no-warm` turns it off.
- `backend/tests/test_warm1_ranges.py` (no DB, 14 tests).

## Checks

- `test_warm1_ranges.py`: 14 passed. Adjacent no-DB files: `test_infra1_degraded_store`, `test_ch5c_store_off`, `test_dd1b2b_drain`, `test_dd1b2b_drain_failure`, `test_ch5c_env_parity`, `test_e4_prebuilt_routes_generator`, `test_e4_performance_on_change`, `test_demo_combined_links`, `test_demo_combined_ex1`, `test_own_g1_add_dates`, `test_dd1b1_prepare_clock` and `test_ar2_prepare_period_rows` gave 54 + 112 passed, 4 skipped.
- Non-vacuous proofs. Each mutation was made on the committed file, run, then reverted with `git checkout`:
  - preset 7d set to today-6: 2 tests failed;
  - the verify >2 s rule removed: 1 failed;
  - the throttle disabled: 1 failed.
- `tools/check-all.ps1`: see the commit message / final report.
- Postgres: none run, and none needed for these files. **Gate run: not run** (VPS job).

## Dry run on client4 (read-only, `AssetOpsV1-e3c/var/polish_client4`, `--today 2026-11-17`)

- Sites: KOBO 10-11..11-09, EV 10-20..11-03, KISIWA 10-30..11-08, COLD 11-01..11-09. Data window 10-11..11-09 (30 days).
- **47 ranges, 445 requests**: 191 Portfolio, 49 summary, 48 Findings, 157 boards.
- Estimated cold warm time, from the AR-4 cold figures (about 8 s for a week, 15 s for 14 days, 30 s for a month, times 6 estate requests per range; boards about 1 s): about 3,800 s of serial work, so **about 16-25 min with 4 workers** if Postgres scales.
- A DB brought up to 16 Nov (about 37 days) gives about 75 ranges and **about 25-35 min**.
- A re-warm with no data change is all hits: about 445 × 50 ms, under 1 min.

## Resume points (VPS)

1. Restore client4 and serve it: `python tools/demo_combined.py --db <client4 db> --work var/polish_client4 serve --port <p> --web-port <w>`. Serve now warms after the first tick on its own. Or run the tool by hand: `python tools/warm_ranges.py --base-url http://127.0.0.1:<p> --work var/polish_client4 --db-url <url>`.
2. Then `... --verify`. Gate: `pass: true`, `hit_percent` 100, `max_ms` ≤ 2000, `degraded` []. Record warm `wall_seconds` (re-warm time) for the presenter notes.
3. If verify shows misses on a route, compare its `url` in the report with the page's network request.
4. Fresh Claude reviewer; the packet gets the gate numbers.

## Known deviations and questions (for the Architect; not designed around)

- **Q1 Data window start.** Implemented as the earliest Site's first day. The windows that start before the later Sites' first days are still warmed, and every Site's board is warmed for every range. Confirm, or rule "the latest first day".
- **Q2 Unstored reads are outside the gate.** These requests are not stored routes, so they cannot be hits:
  - `/api/estate/scope` (Findings page);
  - the Site Overview's `getOverview`;
  - `/api/sites/{id}/findings`;
  - estate actions, evidence and financials.

  Their live times are unmeasured, so the "≤2 s on every page" claim holds only for the stored requests. Rule: measure them in the gate run, or accept.
- **Q3 Expiry.** A live body (no `known_at`) expires at the earliest next Site-local midnight (`response_store.valid_until`), and the presets move at UTC midnight. So on 17 Nov the warm must finish after the last Site midnight and before the client joins. The serve loop re-warms each tick, but a full re-warm takes 25-35 min.
- **Q4 MB-1 conflicts with the warm.** MB-1 feeds Kobo's today live, and each reading moves the estate `cic:` count (D-E4.8), which invalidates every stored estate page. During a live feed the Portfolio will not stay warm. This needs a ruling: a frozen feed during the demo, or the feed outside the estate scope.
- **Q5 Not warmed:**
  - the Findings lens pages (`/findings/cost|risks|opportunities`);
  - `known_at` ranges;
  - Portfolio pages after page 1;
  - chain "Why?" routes;
  - `7dwork`.
- **Q6 Retries.** Warm also retries, and then fails on, a 200 that was served but not stored (`race`, `unstored`, `composed`). The spec names only 503 and `stale`.
