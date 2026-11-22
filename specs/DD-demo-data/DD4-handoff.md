# DD4a handoff (run 2 done: D-DD.90, D-DD.103, the join; next: D-DD.89, writer run, C-DD6)

Branch `task/DD4-cold-ev-reality`, worktree `/opt/assetecon/AssetOpsV1-dd4`. Packet `packet-DD4a.md` ("Run 2").

## Done
Run 1 (D-DD.88 order): D-DD.87 grid (95507fa56), D-DD.83 hand start (ab38dcd9e), D-DD.85 lots (67323959a),
`ColdSiteRun` with D-DD.86 forcings.
Run 2 (main merged f131aa174): D-DD.90 seasons (d47713bd7), D-DD.103 `READINGS_SPAN` (cd71da771), the join with
D-DD.91 event rows (4ec8033db). Parity: Kobo 7 days byte-identical; 27 scope digests equal main.

## Anchors
- `world/telemetry.py`: `READINGS_SPAN`, `span_days`, `_span_hours`, `_draw`, `_rate_kwh`, `_months_without_books`,
  `PACK_FAMILIES`, `VerticalBinding`, `_vertical`, `SiteRun.advance_day/day_records`.
- `world/scope.py` `history_global`; `world/telemetry_cold.py` (`TelemetryRefused`, 7-element rows).
- Tests: `world/test_scope_seasons_parity.py`, `world/test_dd4_span_end.py`, `world/test_telemetry_join_parity.py`.

## Next (D-DD.96 order)
1. D-DD.89's `M` commit (B-1031 resize) and sweep.
2. Cold books for the writer (ledger from `exports_cold`, `cooling`/`seasons`/`day_classes` from the view, Thika's
   events from `M` `operations`), wired into `books_for` or the CLI; then the writer run to `READINGS_SPAN`.
3. `test_dd4_thika_incident.py` and C-DD6 (spec line 390).
- DD4b on its own branch after DD4a merges (EV dispatch slot: `PACK_FAMILIES["ev-roles"]`).

## Risks
- Packet run-2 deviations 7-12 (view_digest move, manifest ruled keys, `door-cycle`, family by role set).
- A full Kobo run to 6 Nov needs D-DD.92's notes (DD3b, D-DD.107).
