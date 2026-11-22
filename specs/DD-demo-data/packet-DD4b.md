# DD4b review packet (PARTIAL: DD4.3 and the rejoin; DD4.4 and DD4.5 to come)

Branch `task/DD4b-ev-measured`. Spec `spec.md` §4.5 and §5.6; rulings D-DD.81, D-DD.91, D-DD.98, D-DD.100, D-DD.123;
pre-flight `DD4b-preflight.md`, `preflight-remaining.md` §DD4b. Not ready for review until DD4.4 lands. The
handoff is `DD4b-handoff.md`.

## Run 1 (DD4.3, before main held DD3a/DD4a)
`22275cdaa`, `8a0699b49`, `8d519ef49`: the roster to 6 Nov, `EvSiteRun` on D-DD.81's protocol, ev-charger/1
`max_plugs`, the pre-flight and its plants.

## Run 2 (rejoin, D-DD.98 rebuild): main merged at `a4dd5e801`
| Commit | What | Tests first |
|---|---|---|
| `724d95113` | rotation, daytime-spare tests; plant-day physics golden (Embakasi 15 Oct, Ruiru 5-7 Oct + CH-R7 c2) computed on the pre-rotation code | v2, v3 failed (`ROTATION_MINUTES` missing); v1 passed (golden) |
| `313330d02` | D-DD.98 rotation rule, `ROTATION_MINUTES = 5`, `SPARE_ARRIVAL` 10:00; `test_r3` now asserts 10:00 | v1-v3 pass |
| `03ad50d4a` | D-DD.123 rejoin (see the handoff's Done) | `test_dd4_ev_join.py` j1-j5 failed first (KeyError `ev-charger`, no `EV_FAULTS`, `ValueError` not `TelemetryRefused`, no `ROSTER_KEY`), then pass |

## Evidence
- Focused (revision `03ad50d4a`, plain pytest from `simulator/`):
  `test_dd4_telemetry_ev, test_dd4_ev_rotation, test_dd4_ev_join, test_telemetry_join_parity, test_dd4_telemetry_cold`:
  all passed after the e5/e7/e8 updates (35 tests in the combined run before the fixes: 31 passed, 4 failed on the
  old row shape; each fixed); `test_dd4_cold_books, test_dd4_span_end, test_dd4_ev_roster, test_dd4_ev_join`: 23
  passed; `test_dd2b_ev`: passed.
- Parity: the Kobo join golden (`test_telemetry_join_parity`) and the cold suite are unchanged; Embakasi and Ruiru
  physics byte-identical to the pre-rotation code (v1).
- `tools/check-architecture.ps1`: passed. `tools/checks/statement_catalogue.py`: exit 0.
- Plant, Kasarani 1 Nov to 6 Nov 06:00 with CH-K2 (9.3 s): see the handoff's Risks (7 missed = 10 short - 3 spare).

## Known deviations (so far)
1. `VERTICAL_RUNS` is read through the frame module's `__getattr__`: a module-level table would import the vertical
   modules while they import the frame (circular). One table, one place (`_vertical_runs`).
2. `VerticalBinding` resolves a channel by `asset_code` when no `device_id` matches (EV rows name the bound asset,
   pre-flight Q4); an asset bound twice for a signal refuses `TEL_BINDING`.
3. The telemetry CLI byte-checks the roster and the cold ledger only for tenants the run writes (`--site`).
4. An EV FAULT event carries `correlation: ["fault", n]` (per-connector episode) and session events `correlation:
   null` with `session_id` (the id is formed at sealing, D-DD.139).
