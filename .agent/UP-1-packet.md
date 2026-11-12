# UP-1 packet (lane F) - client reading upload, Kobo only - PARTIAL (Thu 12 Nov: guard, gateway, template, store test)

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

## Known deviations
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

## Resume points (VPS, after ~16:00)
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
Mockup needs owner approval (Fri 09:00). Slice not ready for review; the switch is off by default.
