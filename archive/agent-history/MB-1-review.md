# MB-1 review (fresh Claude reviewer, 2026-11-13)

Branch `task/MB-1-modbus`, MB-1's own commits `task/UP-1-reading-upload..HEAD` (92a6d4368, 903d0db96, a078ddb2a, a850a4e31).
Judged against rev 7 section 7.6 (D-17N.6), D-MB.1-2, D-UP.2, the packet, and the VPS lane rules.

## Verdict: ACCEPT WITH NOTES

No High or Medium findings. The switch is off by default, the edge gateway is shared (never a second Kobo gateway),
children detach and are stopped by PID, listeners are loopback-only, and the Postgres flow is real (backlog forms during
a 503 stop and drains to 0; no gap, no overlap; analysed by job). The Lows below can be fixed on the branch or carried.

## Checks I ran (worktree HEAD a850a4e31, PYTHONPATH = worktree parts)
- No-DB: `pytest host/tests/test_mb1_live_field.py host/tests/test_up1_demo_upload_gateway.py field/tests/test_field_gx_emulator.py`
  -> **55 passed** in 6.5 s.
- Postgres flow on `assetops_mb1_test`: `pytest -s host/tests/test_mb1_live_field_flow_postgres.py` -> **1 passed, 134 s**.
- By hand against the flow's leftover data on `assetops_mb1_test` (read-only, plus one rolled-back UPDATE):
  - `latest_accepted` + `overlap_refusal`: a window starting at the flow START is refused for the 6 sourced signals; a
    window starting at STOP is not refused. `disabled_sources` returns `[]`. The SQL behind the refusal works.
  - `OVERLAP_SQL`: empty on the flow data; after extending one mill-meter interval by 150 s (rolled back) it returns
    `('mill-meter','active-power','feeder_demand',2)`. The finish check is not vacuous.
- No orphan processes after the runs (`gx_server`, `modbus_poller`, `assetops_gateway serve`: none). Worktree clean;
  the diff is the 7 files the packet names.
- Security: emulator `--host` 127.0.0.1 (gx_server default too), TLS central 127.0.0.1:8443, gateway IPC is a Unix
  socket in the state dir. No credentials in MB-1 files; the flow test mints a random token. Only the documented
  local-dev Postgres URL is used, via env.
- Not run: check-all (coordinator), the demo-copy bench run (5-min wall stop, board lag per D-MB.2, `enable-source`
  and profile -2 binding on the demo DB), `demo_live_field start/status/stop/check` against a live serve. These stay
  as the packet's open risks.

## Findings
- **L1** `tools/demo_combined.py:1721-1725` - stopping `serve` kills UP-1's helpers but not the detached live-field
  children. The poller exits on its own after repeated gateway-unavailable; the emulator keeps listening on
  127.0.0.1:5020 until window end (up to 8 h), and the next `live-field start` refuses ("already running") until
  `live-field stop`. Not a leak beyond loopback, but an orphan by the dispatch's definition. Fix: call
  `live_field.stop(self.work)` in serve's `finally` (or state the required `live-field stop` in the demo script).
- **L2** `tools/demo_live_field.py:289` - the emulator's READY wait is outside the `try` that calls `stop(work)`; a
  READY timeout leaves the emulator running (PID is recorded, so `stop` recovers it). Fix: widen the `try` to cover
  line 289.
- **L3** `tools/demo_live_field.py:150-157, 262` - `pids.json` outlives children that exit by themselves at window end;
  a later `stop` (or `start`'s "already running" check) trusts the PID, and `os.killpg` would signal a reused PID's
  group. Low probability. Fix: confirm `/proc/<pid>/cmdline` names `gx_server`/`modbus_poller` before signalling, or
  drop stale entries.
- **L4** tests - the DB paths of the tool (`latest_accepted`, `disabled_sources`, `check()`'s `lo` query) and a positive
  case for `OVERLAP_SQL` have no automated test; I verified them by hand above. The serve-switch test
  (`host/tests/test_mb1_live_field.py:133`) is a source-string match, not behaviour. Fix: in the flow test, assert
  `overlap_refusal(latest_accepted(expect), START)` is non-empty and empty at STOP, and that a shifted interval makes
  `OVERLAP_SQL` non-empty (rolled back).
- Nit `tools/demo_live_field.py:174` - `{source: signal}` keeps one signal per source, so a refusal message names 6 of 9
  signals (PV ac-power / available-power share a source). Refusal itself is correct.
- Nit `tools/demo_combined.py:1715` - any non-empty `ASSETOPS_LIVE_FIELD_SITES` starts the Kobo gateway (not validated
  to KOBO-001, unlike UP-1's `sites_from_environment`); `start` still refuses other Sites.

## Switch matrix (read, not run live)
- Neither switch: no gateway, no TLS central, upload routes 403 (unchanged).
- Live only: gateway + central start; API gets `ASSETOPS_READING_UPLOAD_GATEWAY` but upload routes stay off because
  `reading_uploads_from_environment` keys on `ASSETOPS_READING_UPLOAD_SITES` (host/lab_app.py:89-104).
- Upload only / both: one gateway; `start` does not re-issue the credential (UP-1's stays valid); overlap rule keeps
  MB-1's window after UP-1's file.

## Residual risk
Demo-DB behaviour (profile -2 binding on the demo Kobo basis, `enable-source`, Health "last upload", the
`kobo-edge-*` epoch cohort) and the real 60 s backstop lag are proven only by the pending bench run. Live readings void
warmed pages (D-WARM.4): keep the beat last and re-warm after.
