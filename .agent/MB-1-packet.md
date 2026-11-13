# MB-1 packet (lane F) - live Modbus into the Kobo edge gateway - built, switch off by default

Branch `task/MB-1-modbus` (worktree `AssetOpsV1-mb1`), based on `task/UP-1-reading-upload`; UP-1's fix round (M1, M2, L1, D-UP.12)
and main (D-MB.1-2) merged in at b2d6ebcfc. Spec: rev 7 section 7.6 / D-17N.6
(`architect-sequence-client-scope-2026-11-11.md`), D-UP.2 (one Kobo edge gateway), D-WARM.4, D-DATA.1.

## Landed
- 92a6d4368 `tools/demo_live_field.py` (`start | status | stop | check`) and `tools/demo_combined.py live-field
  [start|status|stop|check] --site KOBO-001 [--from <Z>] [--hours N]` (runs in the tree with the serve env).
  - Switch `ASSETOPS_LIVE_FIELD_SITES` (off by default). `serve` starts UP-1's edge gateway + `serve_tls` when this
    switch or `ASSETOPS_READING_UPLOAD_SITES` is set; MB-1 never starts a second Kobo gateway.
  - `start`: refuses unless the switch names KOBO-001 and `<work>/reading-upload-gateway.json` exists; window =
    `--from` (default now) floored to 5 min, 1..8 h; **overlap rule**: refuses if any profile signal already holds
    accepted evidence after the start (UP-1 file or story day); enables still-disabled profile sources via
    `provision_gateway enable-source` (credential NOT reissued, so UP-1's stays valid); writes the profile -2 expect
    identity on the edge epoch; generates the readings; spawns emulator (127.0.0.1:5020, rate 1, wall epoch = start,
    so source time = wall time) and wall-clock poller (`gx-system-illustrative-2`, stop at window end) in their own
    sessions; PIDs in `<work>/live-field/pids.json`, logs `<work>/logs/live-field-*.log`. `stop` kills by PID.
  - `check` (finish check): no two accepted readings on the same (Site, source, device/signal) with overlapping
    intervals (or equal state instants) where one came through the edge epoch (UP-1 or MB-1).
  - `host/tests/field_observation_fixtures.generate_live_window`: the registered `kobo-mini-grid-prolonged` run
    in an in-memory store over `[start, start+8h]` (the scenario needs its whole 8 h; `--hours` only stops earlier).
    No draft run is written to the demo DB.
  - `host/tests/field_bench.py`: TEL-08 `activate` and `read --what evidence|runs`.
- 903d0db96 `host/tests/test_mb1_live_field_flow_postgres.py`; overlap SQL pairs per signal (a source is per device).

## Tests (rerun at b2d6ebcfc, after the merges: same counts)
- No-DB: `host/tests/test_mb1_live_field.py` + `test_up1_demo_upload_gateway.py` + `field/tests/test_field_gx_emulator.py`:
  **55 passed**.
- Postgres flow on own DB `assetops_mb1_test` (created by me): **1 passed, 137 s wall** (135 s before the merges). Command: PYTHONPATH (worktree
  parts) `ASSETOPS_TEST_DATABASE_URL=.../assetops_mb1_test pytest -q -s host/tests/test_mb1_live_field_flow_postgres.py`.
  Output: 1036 observations generated; uplink stop (central 503 for 30 wall s = 30 source min at rate 60): 15
  refused posts, sealed backlog 6 -> 36, queue after recovery 0, no dead letters; all receipts COMPLETED; accepted
  evidence for all 9 profile rows; no interval gap; no overlap; `process-jobs` DONE -> `analytic_run` dispatch
  DEFAULT by job, window 2026-10-13. Non-vacuity of the overlap check: its first version flagged 2 x 24 pairs
  (PV ac-power vs available-power share one source), which is why it now pairs per signal.
- check-all: for coordinator. No guard touched; no backend, API or client-message change (coordinator M1/M2 n/a).

## Known deviations / questions (Architect)
1. TEL-08 `setup` and `read --what provenance|assess|findings|consequences` not built: they are the BeagleBone bench
   (out of scope per dispatch). MB-1 uses UP-1's `demo_upload_gateway prepare` in setup's place.
2. **D-MB.1 (ruled):** readings are the prolonged dispatch scenario for the live window, generated in memory. UP-1's
   file and the live window are separate periods: no smoothing, seeding or splicing, and no claim of continuity.
   **Presenter line: "This is a simulated field device (illustrative values) read live over Modbus through the
   site's gateway."** No page text is owned by MB-1.
3. The 5-minute wall uplink stop on a demo DB copy (gate, 1 h heavy slot) is pending; the flow test's stop is 30 s.
4. **D-MB.2 (ruled):** no delivery loop; the gateway's 60 s backstop is the real behaviour. Script line: "readings
   arrive within about two minutes" (presenter waits on Kobo's board "today"). The demo-copy bench run records the
   lag from emulator source time to first appearance on the board and reports it to the coordinator if over 3 min.
5. If `--from` is in the past, readings start at now (the poller cannot read the past): `--from` defaults to now.

## Open risks (state)
- Not run against a demo build: profile -2 binding on the demo Kobo basis, `enable-source` on the demo DB, the
  Health tab's "last upload" from the edge gateway, the `kobo-edge-*` epoch cohort (UP-1 risk) are proven only there.
- Watermark: live readings void warmed pages (D-WARM.4); beat last in the script, re-warm after.

## Resume
- Demo-copy bench run (`serve` with both switches, UP-1 file, then `live-field`,
  5-min `serve_tls` stop, record the board lag (D-MB.2), `live-field check`, `stop`). Nothing left running; `assetops_mb1_test` kept for reuse.

## User review
Not required before review (switched off by default); shown at the field beat walkthrough.

## Fix round (review L1-L4 + nits)
- L1 serve's `finally` calls `live_field.stop(self.work)`. L2 `start` wraps the emulator READY wait, poller spawn and poller wait
  in one `try`; any failure calls `stop`. L3 `is_ours(pid, name)` checks `/proc/<pid>/cmdline` (`gx_server`/`modbus_poller`)
  before any kill and before "already running"; `stop` clears `pids.json` either way.
- L4 tests: `test_serve_with_the_switch_...` / `..._without_the_switch_...` run `Demo.serve` with stubs (behavioural, replaced
  the source-string match); `test_stop_does_not_signal_a_pid_that_is_no_longer_ours`; the flow test now asserts
  `latest_accepted`, `overlap_refusal` (non-empty at START, empty at STOP), `disabled_sources == []`, and that `OVERLAP_SQL`
  finds a shifted interval (rolled back).
- Nits: `latest_accepted` keeps every signal of a shared source; `live_switched_on` requires KOBO-001 in the switch.
- Runs: no-DB 58 passed (6.5 s). Postgres flow on assetops_mb1_test: 1 passed, 134 s (trigger disabled only inside a rolled-back txn for the shifted-interval proof).
