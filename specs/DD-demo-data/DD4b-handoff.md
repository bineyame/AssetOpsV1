# DD4b handoff (PARTIAL: DD4.3, the rejoin, DD4.4 and the writer memory fix done; DD4.5 part built, its M chain next; DD4.6 after)

Branch `task/DD4b-ev-measured`, worktree `/opt/assetecon/AssetOpsV1-dd4b`. Main merged at `0c44ae75b` (`12af8de92`).
Packet `packet-DD4b.md`.

## Done
- Run 2 (rejoin, D-DD.98, D-DD.123): see the packet.
- Run 3 (DD4.4, part):
  - `95f50faa4` tests first `world/test_dd4_measured.py` m1-m7 (6 failed first; m6 is the Kobo parity golden
    `golden/measured_kobo_main.json`, captured from main 0c44ae75b before the change).
  - `200ad01f4` measured hooks: `ColdSiteRun.measured_months()` (`room_kwh`: compressor-meter 5-minute means x slot
    hours, exact, by local month), `EvSiteRun.measured_months()` (bands per price class of the TARIFF_SCHEDULE in force
    each local day, class = band name before `-`; `demand_kw` = max 30-minute :00/:30 mean of the minute import;
    `import_kwh` = sum of bands; TEL_BOOKS when no single schedule is in force), `SiteRun.measured_months()` (DD3a's
    months), `end_local` on both vertical runs; `measured_for` asks every run, writes `departures` for EV only
    (sorted site, departure_at, vehicle; `kwh_at_departure` = exact delivered rounded once); `_vertical` returns a
    light `_measured_view` so day rows are not held. `QUANTUM_KW` -> `SHARE_STEP_KW` (manifest key `share_step_kw`).
    `test_dd4_ev_join` j2 now passes real tariffs (the frame needs them) and asserts measured.json.
  - `test_dd4_exports_measured.py` e1-e9 (`daecd9589`, failed first: no module), e10-e11 CLI (failed
    first), then `world/exports_measured.py`, `cold-electricity-bill-illustrative.profile.json`, `world_history.py
    exports --telemetry DIR` (repeatable; each cold/EV tenant kept needs exactly one measured.json; TEL_ exit 3).

- Run 4 (DD4.4, rest; packet "Run 4"): `c5b019832`, `5aacad343` samples (HAND_SAMPLES empty, nine profiles, samples
  sliced from `exports_measured` over the committed fixtures via `books_support.emulated_files()`); `4cb1eca8b`,
  `e287a2604`, `7ea87a2c9` C-DD5, C-DD6 EV clauses, C-DD7, C-DD20 live in `tools/dd_check.py`, tested in
  `backend/tests/test_dd4_check.py` and `simulator/tests/world/test_dd4_checker_on_emulated_rows.py`.

- Run 5 (writer memory, DD4.5 part; main merged `a173abde9`; packet "Run 5"):
  - `98ef8bf86` tests first `simulator/tests/world/test_dd4_writer_memory.py` w1-w3 (3 failed first), w4 (failed on a
    no-op `undo`); `45afb3992` `build_telemetry(..., sink=)`, `tools/world_history.py` `FileSink` (writes each file as
    made; `undo()` on a refusal), `release_day` on both vertical runs (the frame drops a day's rows once written),
    `EvSiteRun` keeps one day of charger draw (`test_dd4_telemetry_ev` e2 reads it each day). `_import` is unchanged
    (one Fraction per non-zero minute; `measured_months` and two tests read the span).
  - `51993d295` tests first `backend/tests/test_dd45_charger_bound.py` b1-b3 and the 3B6 pins (43 rows; 7 failed
    first); then `rows_ev_depot.py` and `M` `structures` + `home_categories` (`buses_full_by_charger`, Protect P1;
    `buses_short_per_night` = max of the energy and the charger bound), committed with M's header note rev 16.20.

## Next
1. DD4.5 rest (D-DD.125), one `M` commit: regenerate the D-DD.30 chain as rev 16.19 did (`0c5d5fab7`):
   `derived-values.json` + `fixtures.js` (`interactive-mockup-vNEXT` gen_fixtures.py), `index.html` (build.mjs),
   `check_manifest.py` re-based with a dated note, `world_history.py check`; sweep hand-typed Kasarani figures
   (`grep -rn "240.00\|departures_missed\|spare bus" Docs/demo-sprint/product-direction-layer4`, mock JS, docs).
   Expected: Kasarani November `buses_short_per_night` 1 -> 2, `departures_missed` 2 -> 7, `penalties` 240.00 -> 840.00,
   `departures_met` 38 -> 33, cost_to_serve 1027.50 -> 1627.50; KAS-OEM-STOPGAP covered bus-nights and the
   ruiru cost line, KAS-OEM-WAIT and KAS-LOCAL protect figures move with them; the typed `expected_penalties: 240.00`
   and "one bus short a night" text follow. A figure that does not follow the readings stops for the Architect.
   Then `backend/tests/test_6h_parity.py`: list the moved keys (Kasarani from 1 Nov only) and assert the rest; run
   `test_6c_*`, `test_3b*_structure*`, `test_6h*` and the readers of `6h_parity.json` (`--db-lane`).
2. DD4.6 (D-DD.144): the cold energy rebuild.
3. At DD4b's end: spec Status `in_review`, a `.ai/state/` entry and its index line (not written yet: DD4b is not done).
4. Open for the Architect (packet deviations 8-10): the EV hour sums (C-DD7 pending, question (a)), C-DD5's "on
   change" reading, C-DD7's mini clause.

## Plants (run 3, revision 059f211ad, scratch /tmp/claude-1001/.../ce5c6176.../scratchpad/dd44)
- Main goldens (main 0c44ae75b): exports + extras sha256, COLD-MWEA full-span telemetry (31.1 s), Kobo W1 hashes.
- Branch: cold 3 rooms one process 87.8 s, 199 MB peak. COLD-MWEA's 129 day files + manifest byte-identical to main;
  every mini-grid and cold book and the extras identical to main; only `metro-bus.profile.ev-fleet-roster.csv`
  differs (DD4.3's roster to 6 Nov, run 1).
- Cold measured October (kWh / bill): Mwea 1576.300 / 315.26, Thika 1771.350 / 354.27, Kirinyaga 2113.603 / 422.72
  (D-DD.144 projected 315.26, 354.26, 422.72). Statement Oct: revenue 4588.00, energy_cost 1092.25.
- EV plant: 3 depots one process 1608.9 s, **3.8 GB peak** (risk: the minute import dict and day rows; check before
  DD6's world build). 5,379 departures: Embakasi 2560 met, Ruiru 1792 met, Kasarani 1017 met / 10 short (B03, B04 on
  1 Nov; B07, B08 on 2-5 Nov), as run 2's plant. October invoice: Embakasi PEAK 40579.000 kWh 9738.96, OFFPEAK
  46355.767 kWh 5562.69, DEMAND 492.667 kW 5912.00 (peak share 46.7 %); Ruiru PEAK 12193.333, OFFPEAK 48566.667,
  DEMAND 400.000 kW; Kasarani FLAT 37200.000 kWh 5580.00.
- Both tenants' measured.json are committed as `simulator/tests/world/fixtures/measured/*.measured.json` (from this
  run, revision 059f211ad) for step 1's samples; the scratch plant files are deleted.

## Risks
- `meter_billed` EV leaves `kwh_2200_2400`, `kwh_0000_0500` are written `metered: null` and C-DD7's clause for them is
  PENDING (packet deviation 8): `M`'s EV structure reads them.
- EV writer memory (3.8 GB, 1609 s for three depots): cause and proposed fix in the packet ("Risk for DD6's world
  build"); not built.
- `_vertical`'s run is dropped after `_measured_view`; a caller wanting the run must keep its own.
