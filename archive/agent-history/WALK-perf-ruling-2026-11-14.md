> Finished; historical. Archived from .agent/WALK-perf-ruling-2026-11-14.md on 2026-11-18 (declutter step 4).
# WALK-perf ruling (2026-11-14): slow first hits on the walk server

Architect (Claude; ROLE_CONFIG "Architect Is Claude By Default"). Diagnosis only; nothing implemented, serve untouched, DB not written.
Line refs are the walk tree that serve runs (`/opt/assetecon/AssetOpsV1-walk/var/polish_walk1113/tree`, same content as the walk worktree for every file cited).

Method: the per-request `assetops.perf` lines in `logs/api-8990.log`; the serve log; read-only GETs against :8990; and cProfile of the same routes in a separate process. That process imported the same `lab_app` with serve's environment and `PGOPTIONS=-c default_transaction_read_only=on`, so it could not write.

## Problem 1: stored routes slow at first hit

**Hypothesis refuted.** Nothing invalidated or expired the entries.
- At 21:37 every slow request was a store **hit**. Each perf line carries only `store.lookup`, with no compose, recheck or insert timer (`api-8990.log` lines 5944-5960). For example, overview 10-25 was `total_ms 5663.7`, `store.lookup 3641.6`. The board was 2465 / 1152.
- Prebuild states over the whole serve log: 147 × `{"hit":193}` and 70 × `{"hit":85}`. Only 9 runs stored anything, which matches a day add or a code refresh.

**Root cause A: background load at the moment of the hits.** A tick was logged at `db_now 21:36:57` (serve log line 2523). Its prebuild of 193 sequential HTTP hits and `warm_ranges` were both running against the same single-process uvicorn and DB when the smoke ran (21:37:13-37).
- `warm_ranges` sends 1,672 requests with 4 workers, about 117 s of wall time (`warm-report.json`).
- It is restarted after every tick: `tools/demo_combined.py:1865`, `TICK_EVERY_SECONDS = 120` at :63.
- Every one of those requests is a hit, so the work is redundant. The API is under synthetic load nearly all of the time, with `pg_stat_activity` at 86-110.
- It is running again right now (PID 3531697).

**Root cause B: a hit has a fixed cost of about 750 ms, and the store lookup is the small part.** The Performance gate runs before `responses.serve` on every request:
- `site_overview/route.py:162`
- `finding_index_api.py:73`

`main.py:425 performance_gate` → `postgres_assessment_store.py:1201 lineage_breaks` runs 6 `count(*)` queries. That costs 300-440 ms idle and more under load. Profiled hit of overview 10-25: total 436 ms = gate 318 + lookup 96 (of which watermark `count(*)` 82, `postgres_response_store.py:41-53`) + about 20 ms of scope and access.
- Finding index: gate 307 + lookup 150.
- Outcome board: no gate; lookup 235, nearly all of it the watermark.

Under the warm load, the same hit measures about 800 ms live. That is the reported 750 ms against a lookup of about 160 ms.

**The schedule term is not the cost.** `schedule_term` measures 5 ms and `file_state` 1 ms.

**The known Low is real and has the same fix.** The gate verdict is not in the key, yet the stored body embeds it (`source_open`/`reason`). Every input of the gate is already inside W:
- The DB inputs (`analytic_run*`, `assessment_revision`, `ingestion_disposition`, `foundation_revision`) are watermark tables (migration `0047_chain_response.py:29-50`).
- The file inputs are the comparison report and the legacy claims file. They are F roots 1 and 3 of `config/chain/file-inputs-v1.json`.
- The environment and the model version are process constants.

So the gate can move inside `compose`. A hit then never evaluates it, and a stored body is always the one built under the W that includes the gate's inputs.

## Problem 2: Finding financials take 2.1-2.6 s on every hit

`finding_api.py:285 finding_financials` is **not a stored route**, so every request composes in full. Profile (2.2-2.4 s):

| step | cost |
|---|---|
| `dispatch_read.window` ×3 (`postgres_assessment_store.py:910 _window_read`) | 1.15-1.30 s |
| `money_eligibility.for_finding` | 0.98 s (most of it two of those window reads) |
| `finding_read.finding` / `_currentness` | 0.54 s |
| gate (`source_gate`, `finding_api.py:289`) → `lineage_breaks` | 0.42-0.44 s |

The three window reads are for days 2026-11-11, 2026-11-10 and 2026-11-11, so one is a **duplicate**. The route has no read scope, so `read_scope.memo` is a no-op. Measured with a scope around the request: 1,715 → 1,280 ms, and the second 11-11 read drops to 2 ms.

The query itself is reasonable. The fix is to store and prebuild the route, like its siblings. A query fix alone would still leave the gate plus about 1.3 s.

## Fix spec (one Sonnet slice, `fix/WALK-perf-gate-in-compose`)

**F1. The gate moves inside compose on the stored routes** (fixes most of P1B and the Low).
- `site_overview/route.py`: move `self.gate(...)` and `basis_reason(...)` (lines 162-163) into `compose()` (line 168). `day`/`db_today` and `pinned` stay outside. The no-database path (`responses is None`) keeps the same behaviour.
- `finding_index_api.py`: move the `gate(...)` call and its 409 `PERFORMANCE_CUTOVER_CLOSED` (lines 72-82) to the top of `compose()`.
  - An HTTPException raised in compose propagates through `ResponseStore.serve` before any insert, so refusals still never store.
  - Keep `except down` → `store_down`. The outer try already wraps `responses.serve`.

**F2. Financials become a stored, prebuilt route** (fixes P2).
- `finding_api.py`: add an optional `responses: Any = None` to `build_finding_router`, and pass `responses=responses` at `main.py:586`. Note that `responses` is built at `main.py:448`, before line 586.
- Add `FINANCIALS_ROUTE = "/api/sites/{site_code}/findings/{finding_id}/financials"`.
- In `finding_financials`: keep `open_scope` outside. Put everything from `source_gate` to the returned dict into `compose()`, including the `closed` 409 when `revision_id is None`. Then call `responses.serve(StoredRoute(FINANCIALS_ROUTE, tenant_id, {"site": str(site_id), "finding": str(finding_id), "revision": None if revision_id is None else str(revision_id)}, sites=(site,), watermark_sites=(site,)), compose)`.
  - With `responses is None`, return `compose()[ROUTE]`.
  - The compose runs inside `read_scope.fresh` (from `ResponseStore._composed`), which removes the duplicate window read.
- `chain/prebuild.py`: next to `pinned_board_path` (line 117), add `financials_paths(path, response)`. After a 200 Overview it returns the financials path for `known_finding` (`id` and `revision_id`). After a 200 finding-index it returns one path per row (`finding_id` and `finding_revision_id`).
  - Fetch each through the same `fetch` (INFRA-1 retries) in the loop at :96-102, de-duplicated within the run, and count them in `extra`.
- `tools/chain_watermark_guard.py:189 chain_paths`: add the financials path of the first prebuilt KOBO Overview `known_finding`, so the guard and W6 check the new route. Do this because `finding_api` is already in `stored-composer-modules-v1.json`. It needs no `route_terms` entry. If the guard reports an untracked input, stop and report it; do not add exemptions.

**F3. Warm ranges only when something changed** (fixes P1A).
- `tools/demo_combined.py`: `performance_and_prebuild` (around line 1351) returns the parsed prebuild `states`.
- At :1865, start `warm_ranges` only on the first tick, when `states` contains anything other than `hit`, or when 30 min have passed since the last warm finished.
- Factor the decision into a pure `warm_due(states, last_warm_end, now) -> bool`.
- `--no-warm` is unchanged.

**Tests (targeted only; no full suite, per the sprint policy).**
- Overview: a fake store hit means the gate spy is not called. A miss calls it once, and `source_open` and `reason` follow it.
- Finding index: a hit skips the gate. A closed gate on a miss gives 409 and inserts nothing.
- Financials, via the route with a fake store:
  - a hit skips the gate and the reads;
  - the key differs by finding and by revision;
  - `revision_id` absent with the gate closed gives 409 and nothing stored;
  - `X-AssetOps-Stored` is present.
- Prebuild: an Overview with `known_finding` and an index with 2 rows give 3 financials fetches (or 2 if they overlap), with the INFRA-1 retries.
- `warm_due` truth table.
- Rerun the existing `test_s5_overview_read`, `test_e4_prebuilt_routes_*`, `test_sr83_guard_route_terms`, `test_infra1_degraded_store`, `test_ch5c2_clock_guard` and the finding-api financials tests.
- Run `tools/chain_watermark_guard.py` on a `_test` DB.

## Deploy and verify on the live server

- **Needs a serve restart. Does not need a re-prepare.** There is no schema or data change.
  - Refresh the walk tree with the changed files: `route.py`, `finding_index_api.py`, `finding_api.py`, `main.py`, `chain/prebuild.py`, `tools/chain_watermark_guard.py`. Record the refresh in `tree-code-refreshed.txt`.
  - Then restart `demo_combined.py serve`. F3 is in the serve loop itself.
- `code_version` changes, so every stored row misses once. The first tick's prebuild re-stores all routes (about 5 min, as on the first build: `prebuild_ms 303419`), and `warm_ranges` then re-stores the 1,672 ranges.
  - **Do not walk until the second tick's prebuild shows all `hit` and `warm-report.json` shows `pass: true`.**
  - Old-version rows stay in `chain_response` (prune keeps them per version). This is harmless for the walkthrough.
- **Verify.**
  - Once warm is idle, curl the 11 smoke URLs once each. Each must show `X-AssetOps-Stored: hit` and take under 0.4 s, financials included.
  - In `logs/api-8990.log`, an overview hit's `total_ms - store.lookup` must be under 50 ms.
  - Rerun the smoke harness (smoke-check-3); the target is 0 first hits over 2 s.
  - Rerun it once while a tick and prebuild are in progress.
- **Pre-fix check with no rebuild (optional).** The financials gap can be confirmed now with read-only GETs: a repeated curl stays at 2.1-2.6 s with no `X-AssetOps-Stored` header.

## Residuals (not in this slice)

- The watermark `count(*)` over about 1.04 M `chain_input_change` rows costs 80-230 ms per hit idle and seconds under load: the outcome board 10-25 lookup took 1.15 s at 21:37. A follow-up could replace it with a per-(tenant, site) counter or max-id read, which needs a migration. That is out of scope for the walk.
- `lineage_breaks` still costs about 0.3-0.4 s on non-stored Finding routes (window state, finding detail and so on). The smoke found none of them over 2 s.
- Not covered by F1-F3: `/api/work/maintenance` (2,513 ms first hit / 377 ms repeat) and `cold/overview` (2,449 / 132). The pattern suggests the same load window. Recheck them in smoke-check-3 before ruling.
