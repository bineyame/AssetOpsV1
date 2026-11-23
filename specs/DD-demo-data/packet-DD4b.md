# DD4b review packet (PARTIAL: DD4.3, the rejoin and DD4.4 done; DD4.5, DD4.6 to come)

Branch `task/DD4b-ev-measured`. Spec `spec.md` §4.5 and §5.6; rulings D-DD.81, D-DD.91, D-DD.98, D-DD.100, D-DD.123;
pre-flight `DD4b-preflight.md`, `preflight-remaining.md` §DD4b. DD4.4 (D-DD.99, D-DD.123, D-DD.124) is complete and
reviewable; DD4.5 and DD4.6 are later runs. The handoff is `DD4b-handoff.md`.

## Run 1 (DD4.3, before main held DD3a/DD4a)
`22275cdaa`, `8a0699b49`, `8d519ef49`: the roster to 6 Nov, `EvSiteRun` on D-DD.81's protocol, ev-charger/1
`max_plugs`, the pre-flight and its plants.

## Run 2 (rejoin, D-DD.98 rebuild): main merged at `a4dd5e801`
| Commit | What | Tests first |
|---|---|---|
| `724d95113` | rotation, daytime-spare tests; plant-day physics golden (Embakasi 15 Oct, Ruiru 5-7 Oct + CH-R7 c2) computed on the pre-rotation code | v2, v3 failed (`ROTATION_MINUTES` missing); v1 passed (golden) |
| `313330d02` | D-DD.98 rotation rule, `ROTATION_MINUTES = 5`, `SPARE_ARRIVAL` 10:00; `test_r3` now asserts 10:00 | v1-v3 pass |
| `03ad50d4a` | D-DD.123 rejoin (see the handoff's Done) | `test_dd4_ev_join.py` j1-j5 failed first (KeyError `ev-charger`, no `EV_FAULTS`, `ValueError` not `TelemetryRefused`, no `ROSTER_KEY`), then pass |

## Run 3 (DD4.4, part; main merged at `0c44ae75b`)
| Commit | What | Tests first |
|---|---|---|
| `95f50faa4` | `test_dd4_measured.py` m1-m7; `golden/measured_kobo_main.json` from main 0c44ae75b | m1-m5, m7 failed (no `measured_months`/`end_local`); m6 passed (parity golden) |
| `200ad01f4` | measured hooks (D-DD.99, D-DD.123), `measured_for` over every run, EV departures, `SHARE_STEP_KW` | m1-m7 pass (m4's partial_to expectation corrected: a span ending 2 Nov 00:00 is inside November) |
| `daecd9589`, `312b95bfa`, `059f211ad` | `test_dd4_exports_measured.py` e1-e9, then `exports_measured.py` + cold bill profile (with e10-e11), then `exports --telemetry` | e1-e9 ImportError, e10-e11 failed, then 11 pass |

Run 3 evidence (plain pytest from `simulator/`, PYTHONPATH the worktree): `test_dd4_measured, test_dd4_ev_join,
test_telemetry_join_parity, test_dd4_telemetry_cold, test_dd4_telemetry_ev, test_dd4_ev_rotation, test_dd4_span_end,
test_dd3_telemetry`: 66 passed (121 s) after the j2 tariff fix; `test_dd4_exports_measured, test_dd2b_tenant_filter,
test_cli`: 18 passed. Plants and parity: `DD4b-handoff.md` "Plants". Reach set, guards: not run yet.

## Run 4 (DD4.4, rest; `git merge main`: already up to date at `0c44ae75b`)
| Commit | What | Tests first |
|---|---|---|
| `c5b019832` | `test_dd2b_books` b4 (nine profiles, `HAND_SAMPLES == {}`), b4b (each sampled row is a row of the emulated file); backend `test_dd2b_profile_admission` a0 nine profiles; `test_dd2b_round7` r12 on the measured invoice | ImportError (`emulated_files`), then with the loader: 6 failed (b3 cold bill, b4, b4b x4) |
| `5aacad343` | `books_support`: `emulated_files()` = books + `exports_measured` over the committed fixtures; `SAMPLES` for bill (Oct, 3 rooms), invoice (Oct, 3 depots, 7 lines), departures (Kasarani 1 Nov B02 Y, B03 N; Ruiru 6 Oct B01 Y), tickets (2 emulated + 3 `SAMPLE_EXTRAS` for the other states); `HAND_SAMPLES` empty; `--update-golden`; roster pin to DD4.3's file | 48 passed (books, round7, exports_measured) |
| `4cb1eca8b` | `backend/tests/test_dd4_check.py` (hand rows), `simulator/tests/world/test_dd4_checker_on_emulated_rows.py` (writer rows), `test_dd1_check` stub list, Thika C-DD6 test takes `sites` | backend 30 failed / 1 passed (no judges); simulator 5 failed |
| `e287a2604` | `tools/dd_check.py`: C-DD5, C-DD7, C-DD20 live; C-DD6 EV clauses live | backend 32 passed; simulator 4 passed (after the test fix below) |
| `7ea87a2c9` | C-DD7 pending clause for the EV hour sums (question (a)) | the added assertion failed first, then 32 passed |

- The samples: the cold bill sample is Oct 2026 for all three rooms (1576.300 / 2113.603 / 1771.350 kWh); the EV
  invoice sample is October's seven lines (NIGHT is not in a whole month: it starts 1 Nov); `ev-service-tickets`'s
  bytes are unchanged (the two emulated tickets plus the three hand rows equal the old hand sample).
- `test_r15` (the cold/EV byte pins) failed before this run on `metro-bus.profile.ev-fleet-roster.csv`: DD4.3's roster
  to 6 Nov (run 1). The pin now holds the new sha256 with that note.
- The simulator test's first run failed on test setup: a one-day Kasarani run holds no departure (the 1 Nov bus-night
  departs 2 Nov 05:00), and the cold probes write samples at the slot's start instant. The fixture now runs Kasarani
  1-2 Nov, and the cadence table admits a sample at a slot's start (deviation 9); a hand test proves an off-grid
  sample still fails.

### The checks (D-DD.55: judges on rows; the fetch returns nothing until DD5, so each FAILs on the clone)
- **C-DD5** `judge_cadence(readings, source_modes, sites, start, end, outages)`: every Site has rows; its
  `source_mode` (a separate input, question (b)) is SIMULATED; every row lies in the span (`span_of(M)`: 1 Jul 00:00
  to 6 Nov 06:00 +03:00, D-DD.103); the cadence table `CADENCE` (states and events on change; every other unit a mean
  inside one 5-minute slot, or a sample at its start); every 5-minute slot holds a mean unless a declared outage
  covers it. On the writer's rows (Kasarani 2 days, Ruiru, Mwea) it passes; an hour removed fails as a gap.
- **C-DD6** EV clauses live: CH-K2 FAULTED at 2026-11-01T23:40 on both connectors' controllers and no other channel;
  CH-R7 c2 FAULTED on 6 Oct (the day `M` names; 00:00 is the writer's Assumed instant). Kisiwa and Mto stay pending
  (DD3b, D-DD.146). On the writer's rows: pass; the fault moved 5 minutes fails.
- **C-DD7** exact: the cold bill kWh = the compressor meter (`compressor-meter/power`) energy of the month; each EV
  USAGE band = the Site meter (`site-meter/import`) energy in that price class of the schedule in force (class = band
  name before `-`); DEMAND = the largest :00/:30 30-minute mean; a metered class missing from an invoiced month fails;
  each departure's `block_met` = delivered >= roster required, delivered never above required, every roster
  bus-night has one departure. Cold metered kWh is printed beside `M`'s (`info:` lines). On the writer's rows
  (Kasarani 1-2 Nov with B03/B04 short, Ruiru 6 Oct with PEAK/OFFPEAK/DEMAND, Mwea 1 Oct): pass; DEMAND + 0.001 fails.
- **C-DD20** directions on the measured books: Mwea's and Kirinyaga's kWh per crate-day rise each month, July to
  October (crate-days: `history.json` July-September and `M`'s October actual, `crate_days_of`), Mwea's occupancy
  falls each month, Embakasi's peak share rises each month. On the plant fixtures' books: pass. Mwea 0.2390, 0.2655,
  0.3155, 0.3632; Kirinyaga 0.1881, 0.1900, 0.2101, 0.2131 kWh per crate-day. Kisiwa and Mto pending (DD3b).

### Run 4 evidence
- Reach set (`preflight-remaining.md` §4 DD4b, plus the files this run changed), ONCE at `7ea87a2c9`:
  `tools/heavy-slot.sh --db-lane -- pwsh tools/run-host-tests.ps1 -- simulator/tests/world/{test_dd4_telemetry_ev,
  test_dd4_ev_roster, test_dd2b_ev, test_dd2b_books, test_dd2b_round7, test_telemetry_join_parity, test_dd4_span_end,
  test_dd4_checker_on_emulated_rows, test_dd4_thika_incident, test_dd4_exports_measured, test_dd4_measured,
  test_dd4_ev_join}.py backend/tests/{test_dd4_check, test_dd2_check, test_dd1_check, test_dd2b_profile_admission}.py`:
  **167 passed, 1 warning, 0 failed** (pytest 138 s; 301 s wall with the slot wait).
- Main: `.agent/main-baseline/23d2cd9f6.md` (DD3c's 81 backend files) lists none of these files, so it gives no main
  count for them, and main was not rerun (one call only). Known main/branch differences: on main `test_dd4_check`,
  `test_dd4_checker_on_emulated_rows`, `test_dd4_exports_measured`, `test_dd4_measured` do not exist; b3/b4/a0 see eight
  profiles; r15 pins the pre-DD4.3 roster.
- `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set): passed. `tools/checks/statement_catalogue.py`: exit 0
  ("OK statement catalogue"). `tools/check-agent-workflow.ps1`: passed (`e287a2604`). Re-run at `7ea87a2c9`: architecture
  passed, statement catalogue exit 0.

### Plants (run 4)
At `7ea87a2c9` (writer code unchanged since run 3's `059f211ad`), `world_history.py site-inputs`, `exports`,
`telemetry` (cold: 3 rooms; EV: 3 depots, one process each), then `exports --telemetry` both directories, scratch under
the session scratchpad (deleted after):
- Cold: exit 0, 89.4 s, 198,740 kB peak RSS. EV: exit 0, 1,619.9 s, **3,818,860 kB peak RSS** (run 3: 1,608.9 s,
  3.8 GB; the risk below stands).
- Both tenants' `measured.json` are byte-identical to the committed fixtures, so the samples and C-DD20's books are the
  plant's. Exported measured books: cold bill 12 rows, EV invoice 28 rows, departures 5,379 rows.
- Parity as in run 3 (goldens unchanged; `test_telemetry_join_parity`, `test_dd4_measured` m6 pass in the reach set).
- Not run: C-DD5/C-DD6/C-DD7 over the full-span plant readings. Holding 130 days of EV rows as dicts for one judge
  call is beyond this machine for the same reason as the writer's memory; the judges are tested on writer days.

### Risk for DD6's world build: the EV writer's memory (run 3's plant: 3 depots in one process, 1608.9 s, 3.8 GB peak; fixed in run 5)
The cause is visible in the code; nothing was built for it (proposal only):
1. `build_telemetry` (`world/telemetry.py` 749-792) appends every day file's bytes to `files` and returns them; the CLI
   writes them at the end. An EV day file is large (Kasarani 1 Nov: 18,941 rows, of them 11,520 one-minute connector
   `state` rows; Embakasi and Ruiru have 60 and 50 connectors), so 130 days x 3 depots of JSON bytes are held at once.
   The cold plant (199 MB peak) writes about 3,400 rows a day per room.
2. `EvSiteRun._charger_draw` (`telemetry_ev.py` 162, 420) keeps a (charger, minute) Fraction for every non-zero draw
   over the whole span (85 chargers x up to 187,200 minutes); only two tests read it (`charger_draw()`).
   `_import` (one Fraction per minute per depot) is small beside it.
Proposed fix (for DD6, not built): let `build_telemetry` hand each day file to a writer callback (or yield it) so the
CLI writes and drops it; keep `_charger_draw` for the current day only (the tests read a day), and fold `_import` into
the month's bands and 30-minute windows at each day's end. Byte parity: the day files and `measured.json` must stay
identical (the run 3 goldens).

## Run 5 (writer memory; DD4.5 part; `git merge main` at `a173abde9`)
| Commit | What | Tests first |
|---|---|---|
| `98ef8bf86` | `test_dd4_writer_memory.py` w1-w3 | 3 failed first (no `sink`, no `release_day`, draw kept over 2 days) |
| `45afb3992` | `build_telemetry(..., sink=)`; `world_history.py` `FileSink` (+ `undo()` on refusal); `release_day` on cold and EV runs; one day of `_charger_draw`; e2 reads the draw per day; w4 | w4 failed on a no-op `undo` |
| `51993d295` | `test_dd45_charger_bound.py` b1-b3; 3B6 pins 43 rows | 7 failed first (`KeyError buses_full_by_charger`, 42 rows) |
| `eeeb62920` | `rows_ev_depot.py`, `M` `structures` + `home_categories` (rev 16.20 note) | b2, b3 pass; b1 after its home literal fix |

- Memory: see "Plants (run 5)". `_import` is kept (one Fraction per non-zero minute per depot; `measured_months` and
  m2/e2 read the span); a day's rows and day files are no longer held.
- DD4.5 model: `buses_full_by_charger = chargers_in_service * floor(charger_kw * window_h / kwh_per_bus_night)`,
  `buses_short_per_night = max(<energy bound>, max(buses - buses_full_by_charger, 0))`. Kasarani November (3 chargers,
  window 7 h, 150 kWh): 6 full by charger, 2 short a night (energy alone: 1), `departures_missed` 2 -> 7
  (= 2 x 5 - 3 spare; the departure log: 10 short rows B03/B04 1 Nov, B07/B08 2-5 Nov, less 3 S01 rows met),
  `penalties` 240.00 -> 840.00. Not binding with every charger in service (Embakasi, Ruiru, Kasarani: b3).
- Not done in run 5 (handoff "Next" 1): the D-DD.30 regeneration and sweep (`derived-values.json` still 2 / 240.00;
  `check_manifest.py` K13 FAILs on `structures` and `home_categories.nodes` until re-based; 3B6 test_4 fails on the
  seven EV sides until regenerated), the 6h parity moved-key list.
- Guards (at `eeeb62920`): `tools/check-architecture.ps1` passed; `tools/checks/statement_catalogue.py` exit 0.
  Writer reach set (`test_dd3_telemetry`, `test_dd4_*`, `test_telemetry_join_parity`, plain pytest from
  `simulator/`, at `45afb3992`): 105 passed, 182 s, 153 MB.

### Plants (run 5)
`world_history.py exports`, `site-inputs`, then `telemetry --site EV-EMB --site EV-RUI --site EV-KAS` (one process,
the full span), through `tools/heavy-slot.sh`, scratch `/tmp/claude-1001/dd45-plant` (deleted after):
- Golden: the same plant at `a173abde9` (writer code identical to run 4's `7ea87a2c9`) before the change: 390 day
  files + `measured.json`, sha256 of each. Its `/usr/bin/time` file was lost (a shared-scratchpad deletion by another
  session), so the "before" memory is run 4's at the same writer code: **1,619.9 s, 3,818,860 kB**.
- After (`eeeb62920`): exit 0, **1,567.3 s (26:07), 149,128 kB peak RSS** (25.6x less). All 391 files byte-identical
  to the golden; `measured.json` identical to `simulator/tests/world/fixtures/measured/metro-bus.measured.json`.
- Moved EV figures: none in the readings or the measured books (writer parity). The model figures that move are
  Kasarani November's (above); the depots' October and Embakasi/Ruiru figures do not move (b3: the bound does not bind).

## Evidence (runs 1-3)
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
5. `measured.json` for a vertical run is taken from a `_measured_view` snapshot when the run ends, so the frame does
   not hold 130 days of rows per Site until the tenant's file is written.
6. `meter_billed` rows carry `manifest_path` beside D-DD.124's five fields (where the manifest value was read), and
   EV `kwh_2200_2400` / `kwh_0000_0500` are `metered: null` (not in D-DD.99's EV key set).
7. `exports --telemetry` is repeatable (one directory per writer process); each kept cold/EV tenant needs exactly one
   `measured.json`, else `EMU_MEASURED` exit 3.
8. Question (a), default kept: the EV hour sums `kwh_2200_2400`, `kwh_0000_0500` are written `metered: null`. They are
   read: `M`'s EV structure (`backend/assetops_backend/structure/rows_ev_depot.py` leaves at lines 55-56, nodes
   `scheduled_kwh_night` and `offpeak_cost`) and the D-DD.20 rule that C-DD7 checks every `meter_billed` leaf exactly.
   C-DD7 lists that clause as PENDING, naming the gap (D-DD.99's EV month has no hour sums); for the Architect.
9. Question (b), default kept: C-DD5 judges against the checker's own cadence table (`CADENCE`), with source modes a
   separate input (`stored_source_modes`, empty until DD5); the readings manifest declares no cadence, so "the
   checker's table must equal the manifest's" is not judged. "States and events on change" is judged as "no grid":
   Kobo writes `status` every 5 minutes and EV connector `state` every minute, so a strict "only on a change" rule
   would fail the writers; a numeric sample at a slot's start instant (the cold probes) counts as that slot's reading.
10. C-DD7's mini-grid clause (served + unserved = `delivered_kwh`) is PENDING: unserved energy is not a readings
    channel (DD3a writes it to `measured.json` only). C-DD7 and C-DD20 read the book rows through `stored_books`,
    whose query does not yet fetch TARIFF_SCHEDULE, FLEET_ROSTER or DEPARTURE; DD5's loader widens the fetch.
11. C-DD20 also judges Mwea's occupancy falling each month (the spec's "as occupancy falls"); the series are printed
    as `info:` lines.
1. `VERTICAL_RUNS` is read through the frame module's `__getattr__`: a module-level table would import the vertical
   modules while they import the frame (circular). One table, one place (`_vertical_runs`).
2. `VerticalBinding` resolves a channel by `asset_code` when no `device_id` matches (EV rows name the bound asset,
   pre-flight Q4); an asset bound twice for a signal refuses `TEL_BINDING`.
3. The telemetry CLI byte-checks the roster and the cold ledger only for tenants the run writes (`--site`).
4. An EV FAULT event carries `correlation: ["fault", n]` (per-connector episode) and session events `correlation:
   null` with `session_id` (the id is formed at sealing, D-DD.139).
