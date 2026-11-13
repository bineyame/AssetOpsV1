# UP-1 packet (lane F) - client reading upload, Kobo only - server + frontend built (Fri 13 Nov); client4 run pending

Branch `task/UP-1-reading-upload` (worktree `AssetOpsV1-up1`; main 506eae7fc merged in at a77a870bd). Spec: rev 7
section 7.5 of `.agent/architect-sequence-client-scope-2026-11-11.md`; D-17N.5 and rulings **D-UP.1-11** in
`.agent/build-sheet-OWN-GAPS-2026-11-08.md`. MB-1 follows in this lane after UP-1's server.

## Landed (commits)
- 2dde422db mockup `frontend/mockups/v72/upload-readings.html` (owner approval draft).
- e331827ba `field/assetops_field/csv_upload.py`: `preview()` and the CLI `check` / `send` (D-UP.1: the host runs it
  as a separate process; no guard exception).
- eb05fa18f server: `reading_upload/service.py`, `reading_upload_api.py`, migration `0061_reading_upload`
  (`down_revision = 0059_site_period_read`, D-UP.8), words, `host/reading_upload_process.py`, `host/lab_app.py`
  (`ASSETOPS_READING_UPLOAD_SITES`, `ASSETOPS_READING_UPLOAD_GATEWAY`).
- 6fdd4d62a **guard fix (D-UP.10)**: store moved to
  `backend/assetops_backend/reading_upload/adapters/postgres_reading_upload_store.py`, INSERT column list literal;
  `tools/checks/configuration-persistence.ps1` registers `$uploadWriter` as the sole INSERT-only writer of
  `reading_upload` (driver allowlist, action-forbidden line rule, only-inserts rule, sole-writer rule, anti-vacuity),
  on the `$periodWriter` pattern.
- 10be5c277 **demo upload gateway (D-UP.2)**: `tools/demo_upload_gateway.py` (`prepare` / `activate`) and
  `Demo.start_upload_gateway` in `tools/demo_combined.py serve`, only when `ASSETOPS_READING_UPLOAD_SITES` is set:
  - (a) `python -m assetops_backend.serve_tls` on 127.0.0.1:8443, self-signed cert generated once into `<work>/tls/`
    (openssl, SAN 127.0.0.1); the credential issued once via `provision_gateway issue` (actor
    `service:demo-upload`, the CSV profile's sources enabled), reissued only when the file it names is missing.
  - (b) one persistent state `<work>/gateways/kobo-edge/`; epoch `kobo-edge-<hex>` minted once into
    `sequence_epoch.txt`, refused if equal to any `<work>/kobo-*/gw-*` epoch; a changed provisioning is refused
    (never re-provisioned).
  - (c) basis: `RegisteredLabBasis(...).select("KOBO-001", <latest prepared Kobo day in days.json>)` - the same
    `select_registered_basis` the day's run used; no draft run written. Saved as `basis.json` (snapshot + claimed).
  - (d) `host/reading_upload_process.deliver_now`: after `send` exits 0 the host calls `deliver` (50 per pass)
    over the IPC link until a pass attempts none, bounded at 30 s, never raises; gateway `interval_seconds` = 60.
  - Serve writes `<work>/reading-upload-gateway.json` after activation and passes it to the API; both helpers are
    killed with serve. The demo tree's `git archive` now includes `field` (the host runs the collector from it).
- f985c179e **template route and D-UP.5/6**: `GET /api/sites/{site_code}/reading-uploads/template` (declared before
  `/{upload_id}`), body = the profile header row built by the host (`template_csv`, ASCII, no BOM, CRLF),
  `text/csv`, `attachment; filename="KOBO-001-readings-template.csv"`; 503 `READING_UPLOAD_TEMPLATE_UNAVAILABLE` when
  no template is wired. POST: 415 `READING_UPLOAD_UNSUPPORTED_TYPE` for any media type but `text/csv`;
  `file_name` at most 200. Words: `reading_upload.refused.encoding` and `reading_upload.template_note` both say
  "save as 'CSV (Comma delimited)', not 'CSV UTF-8'".
- 831d1b354 `backend/tests/test_up1_reading_upload_postgres.py` (resume point 3).
- a8c948551 estate self-test probe anchor follows `$uploadWriter` in `$pgWriters`.

- (13 Nov) mockup v72 rebuild committed; `git merge main` (clean). **D-UP.8 done**: PR-3's 0060 is on main, so
  `0061.down_revision = 0060_site_admin_price_entry`; one head. PR-3's migration test asserts the tree's one head
  (`test_pr3_price_entry_postgres.py` lines 82/91/174) instead of `[0060]`.
- **Analysed read (D-UP.3)** in `postgres_reading_upload_store.py` `_ANALYSIS` (the injected callable is gone): once
  all admitted readings are accepted, `analytic_run` (`dispatch`, DEFAULT, `job_id IS NOT NULL`, window covers
  `period_start`, `knowledge_cutoff >=` max ACCEPTED `ingestion_disposition.decided_at` of the message IDs - the
  ledger has no `accepted_at` column; the disposition's decision time is that time); PENDING/LEASED job in any domain
  over [period_start, period_end) -> Still processing; FAILED there -> `NOT_ANALYSED`
  (`reading_upload.state.not_analysed`, the ruling's words); `board_day` (Site-local day of `period_start`) only when
  ANALYSED. Order: pending > failed > run.
- **Postgres flow test** `host/tests/test_up1_reading_upload_flow_postgres.py` (resume point 2): TEL-06b setup, the
  host's real checker/sender processes, real gateway process, real ingestion behind the fake TLS central. Dry run
  writes nothing -> SENT (196 admitted) -> PROCESSING (196/196 accepted; 1 dispatch job PENDING) ->
  `assess_dispatch process-jobs` DONE -> `analytic_run` dispatch/DEFAULT/by job, window 2026-09-30 -> **ANALYSED**,
  `board_day` 2026-09-30. Send-to-Analysed **2.3-4.0 s** with the test's drain (the serve tick's interval is not in it).
- Server additions for the page: `GET /api/sites/{code}/reading-uploads` (200 `{enabled, template_note}` when the
  switch names the Site, else the POST's 403s); dry run `latest_saved` (latest accepted reading over the file's
  roles); per column `meter_text` / `role_name_text` (new keys `reading_upload.meter.*`, `reading_upload.role_name.*`).
- **Frontend** (490c92fa0): `sites/readingUploadClient.ts`, `sites/ReadingUpload.tsx` (+ `readingUpload.css` on app
  tokens), `SiteUploadsFrame` + Health panel in `shell/SiteHealthFrames.tsx`, route `SITE_UPLOADS_ROUTE_PATH`
  (`/sites/:siteId/uploads`) in `operatorSiteRoutes.ts` / `App.tsx`; `test/settled.ts` knows "Loading the upload
  page". Panel only when the entry read is 200 (mini-grid Health, not on the gateway detail). Polls every 3 s until
  ANALYSED / NOT_ANALYSED / REFUSED. Links via `RangeLink`.

## Checks (Fri 13 Nov, VPS)
- No DB: `test_up1_reading_upload.py` + `test_uq6a_message_seam.py` + host `test_up1_reading_upload_process.py` +
  `test_up1_demo_upload_gateway.py`: **108 passed**. (`test_up1_demo_upload_gateway.py` fakes main's new D-SR.67
  `evidence_comparisons` serve step.) `test_e4_prebuilt_routes_generator.py::test_the_list_is_written_before_every_
  prebuild_and_at_serve_start` fails **on main too** (`'Done' object has no attribute 'returncode'`), not UP-1.
- Postgres (own `assetops_up1_test`, created today): flow test + `test_up1_reading_upload_postgres.py` 3 passed;
  `test_pr3_price_entry_postgres.py` 4 passed.
- vitest: `src/sites/__tests__/readingUpload.test.tsx` **10 passed**; range/link + Health set: see report.
- tsc `--noEmit`: exit 0. Guards: check-all for coordinator.

## Checks (Thu 12 Nov)
- No DB: `backend/tests/test_up1_reading_upload.py` + `test_uq6a_message_seam.py` +
  `host/tests/test_up1_reading_upload_process.py` + `host/tests/test_up1_demo_upload_gateway.py`: **103 passed**.
  Adjacent serve tests `test_dd1b2b_drain_failure.py` + `test_e4_prebuilt_routes_generator.py`: pass (38 with the
  gateway file).
- Postgres (own DB `assetops_up1_test`, via `tools/run-host-tests.ps1`): `test_up1_reading_upload_postgres.py`
  **2 passed** in 18 s (0061 objects, round trip, UPDATE/DELETE refused, three CHECK refusals, empty-ledger reads,
  downgrade refused with rows then allowed).
- Guard non-vacuity: a second writer (`INSERT INTO reading_upload` in `postgres_period_read_store.py`) gave 2
  failures ("Only ...postgres_reading_upload_store.py writes reading-upload table" and the period store's
  only-inserts rule); reverted with `git checkout`. Clean run: 0 failures (48 s).
- `tools/check-all.ps1` on a8c948551: **All 19 guards passed** (1784 s; estate self-tests 16 passed in 1433 s).
  The first run (on 6fdd4d62a + WIP) failed 1 of 19: `test_estate_guard.py::test_trial_comparison_writer_registered`
  patches the literal `$pgWriters` tail `, $trialComparisonWriter, $periodWriter)`, which the new `$uploadWriter`
  entry changed; a8c948551 moves the probe's anchor (as ANY-1 AR-1 did). The node `Cannot find module` failures are
  gone with `node_modules` present.
- `frontend/node_modules` is an untracked junction to plan2's (identical `package-lock.json`).

## Review fix round (13 Nov, REJECT M1/M2 + L1/L3 + D-UP.12)
- M1: the server sends `refusal: {code, where}` only (`row 7 · timestamp_utc`, `column 3`, or the meter role in words); no path,
  no ISO time. ALREADY_RECORDED words give the latest reading in Site time ("17 Nov, 02:45 (site time)"), from the new
  store method `site_timezone`. The page chip shows `where`; MOCK DEVIATION note corrected. Vitest feeds the real server
  shapes (`__tests__/readingUploadServerShapes.json`, generated from the backend test client).
- M2: `run_in_threadpool` for upload and status; tests: delegation spy, and a GET served while an upload is inside its check.
- L1: `csv_upload` maps `csv.Error`/`UnicodeError` to INVALID_VALUE/FIELD_TOO_LARGE (422, plain words); a port `RuntimeError` is
  a 503 in words; the page shows a fallback sentence when a 5xx has none. Tests: field, backend, page.
- Site sentences (Health panel text, "four meters") come from the entry read (`health_text`, `template_step`).
- D-UP.12: `_ANALYSIS` counts a FAILED job only when `created_at` or `lease_until` is at/after the upload's decision, and a
  qualifying run wins over any FAILED job (PENDING/LEASED still first). Five Postgres cases in `test_up1_reading_upload_postgres.py`.
- Merged main (SR-6b Health range): `SiteHealthFrames.tsx` conflict resolved; the entry panel sits in both Health branches.
- NOT BUILT (L3): the demo-file `--day` option, and the TEL-06b byte-equal comparison of the template/demo file.

## Known deviations
- MOCK DEVIATIONs (labelled in `ReadingUpload.tsx` / `SiteHealthFrames.tsx`): no per-step clock times in the tracker
  (one stored time, shown in the head); refusal = the server's one sentence + field, not headline + explanation; the
  mock's "Every refusal" table and drop-zone state bar are review aids, not built; breadcrumb keeps Site / Health.
- Step descriptions for done tracker steps ("The whole file passed.", "Handed to the site's data gateway.") and the
  Health panel copy are the mockup's words in the page, not server keys; state sentences are the server's.
- **SPEC DEVIATION (transport, D-UP.5)**: raw `text/csv` body with `?file_name=`, not multipart (stated in the
  `reading_upload_api.py` docstring).
- D-UP.9: `message_ids` is `text[]`, not jsonb (the ruling's word); same content, append-only.
- Process: one earlier `service.py` edit was by a Python heredoc (D-UP.11: reviewer re-reads that file).

## Open risks (state, not designed around)
- **Not run against a real demo build**: `prepare`/`activate` need a demo DB with prepared Kobo days; no demo DB may
  be touched today. The serve wiring is tested with every process faked.
- `--actor service:demo-upload` is not proven accepted by `issue_credential` (first real run shows it).
- Analysed risk (D-UP.3) has a second edge: `field_bench.cohort_members` keys cohort members by
  `gateway:source:epoch`, so the new `kobo-edge-*` epoch's sources may be outside the DEFAULT cohort. The flow test
  must show the `analytic_run`.
- A work folder prepared before 10be5c277 has no `field` in its tree: re-prepare (or copy `field/` into the tree)
  before serving with the switch on.
- If the gateway's `activate` is not idempotent across a serve restart, the second serve's activation fails loudly.

## Resume points (13 Nov onward)
- Done: 1 (Analysed read), 2 (flow test), 4 (frontend), 5 (0061 repoint).
- Next: 3 (client4 copy with `demo_combined.py serve` and the switch on: the cohort risk for `kobo-edge-*` epochs and
  `--actor service:demo-upload` are only proven there); a page capture in each state (gate); MB-1.

## Resume points (as of 12 Nov)
1. The `analysed(row)` read (D-UP.3): `analytic_run` (dispatch_v3 `ANALYTIC_ID`, `DEFAULT`, `job_id IS NOT NULL`,
   window covers first interval start, `knowledge_cutoff` >= latest `accepted_at` of the upload's evidence) and no
   PENDING/LEASED `recompute_job` in any domain over [first start, last end); FAILED -> `NOT_ANALYSED` with
   `reading_upload.state.not_analysed` (no-DB test with a fake store); "Analysed" links to `/sites/KOBO-001?date=`.
2. Postgres flow test on a `*_test` DB built like Kobo's demo: upload -> accepted evidence -> drain -> the
   `analytic_run` row; record send-to-Analysed time. Fallback by Sat 20:00 if no run: the reduced version in D-UP.3.
3. The same flow once on a client4 copy (first VPS heavy slot), with `demo_combined.py serve` and the switch on.
4. Frontend `/sites/:id/uploads` from Kobo **Health** (D-UP.4) after the owner approves the mockup (Fri 09:00).
5. When PR-3 merges: repoint `0061.down_revision` if PR-3 lands second-to-UP-1 (D-UP.8); one `alembic heads`.
6. MB-1 on the same `kobo-edge` gateway and central.

## User review
Mockup provisionally approved by the owner (13 Nov). Server + page ready for review behind the switch (off by
default); the demo-build run (resume point 3) and state captures remain before merge.
