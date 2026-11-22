# DD4b handoff (PARTIAL: rejoin done; DD4.4 not started)

Branch `task/DD4b-ev-measured`, worktree `/opt/assetecon/AssetOpsV1-dd4b`. Main merged at `a4dd5e801` (DD3a, DD4a,
T1b, rulings through D-DD.144). Packet `packet-DD4b.md`. Stopped at the context budget, before DD4.4's code.

## Done (this run)
- `724d95113` tests first: `world/test_dd4_ev_rotation.py` (plant-day physics golden from the pre-rotation code).
- `313330d02` D-DD.98: `ROTATION_MINUTES = 5` rotation rule; spare `EV-KAS-S01` returns 10:00 (`SPARE_ARRIVAL`).
- `03ad50d4a` (tests first in the commit before it) D-DD.123 rejoin: `VERTICAL_PACKS["ev-charger"]`,
  `VERTICAL_RUNS` (lazy, module `__getattr__`: the vertical modules import the frame), seven-element rows with
  D-DD.91 event objects + `session_id`/`connector_id`, `TelemetryRefused`, `span_days` end instant,
  `VerticalBinding.by_asset`, `EV_FAULTS`/`EV_CLOCK` (pinned to `M`), `ev_roster_files`/`ev_books_for`, CLI
  `TEL_BOOKS` byte check of the roster (only for tenants the run writes).

## Anchors
- `world/telemetry_ev.py`: `_minute` (rotation after assignment), `_plug`, `_manage`, `_event`, `unplugs()`,
  `departures()` (exact `delivered_kwh`), `import_by_minute()`, `ev_books_for` (gives `tariffs`: TARIFF_SCHEDULE).
- `world/telemetry.py`: `_vertical`, `_vertical_runs`, `measured_for` (mini-grid only so far).
- `tools/world_history.py` `_telemetry`.

## Next (DD4.4, 1.5 u; tests first)
1. Measured hooks (D-DD.99/.123): `ColdSiteRun.measured_months()` -> `{"room_kwh"}` (compressor-meter/power means x
   interval, exact); `EvSiteRun.measured_months()` -> `{"bands", "demand_kw", "import_kwh"}` with price classes from
   `books["tariffs"]` (band name before `-`: OFFPEAK-AM/PM -> OFFPEAK), demand = max 30-min aligned mean of minute
   import; `partial_to` for November. `_vertical` collects runs; `measured_for` takes every run (mini-grid bytes =
   DD3a's, parity test) and writes `departures` only for EV tenants (sorted site, departure_at, vehicle).
2. `world/exports_measured.py`: cold bill (`T-GRID-COLD` 0.20 with `M` parity, `<CODE>-UTIL`), EV invoice
   (`body.band`, DEMAND row, D-DD.81 flat key `tariff.usd_per_kwh`), departure log, `<slug>.meter-billed.json`,
   statements (EV without `revenue`); `exports --telemetry DIR`; `HAND_SAMPLES` empty; profile
   `cold-electricity-bill-illustrative` + sample + expected.
3. `tools/dd_check.py`: C-DD5, C-DD6 (EV clauses), C-DD7, C-DD20 live; `backend/tests/test_dd4_check.py` (new).
4. Reach set once at the end (preflight-remaining §4 DD4b list) and the plants.

## Risks
- Kasarani 1-5 Nov plant (rotation, spare): 10 short rows (night 1 B03/B04 63.33 kWh; nights 2-5 B07/B08 22-26
  kWh), 3 spare rows met -> 7 missed, as D-DD.98 projected. Night shortfalls are smaller than the projection's 46 kWh.
- `QUANTUM_KW` and `_milli` (meter 0.001) remain in `telemetry_ev.py`: pack quanta and the meter's register, not the
  frame's rounding; the reviewer's D-DD.81 grep will hit `QUANTUM`.
- Not run yet: the DD4b reach set (only focused files ran), the full-span EV writer run.
