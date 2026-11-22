# DD4b handoff (PARTIAL: rejoin done; DD4.4 run 3 stopped at the context budget)

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

## Next (rest of DD4.4)
1. Samples (D-DD.65a L1): `HAND_SAMPLES` empty. Service tickets -> `SAMPLES` slice (2 emulated rows) + the 3 hand
   tickets in `SAMPLE_EXTRAS` (statuses). Invoice, departures and the new cold bill: slices of `exports_measured` rows
   over committed fixture docs `simulator/tests/world/fixtures/measured/{harvest-cold,metro-bus}.measured.json`, copied
   from the plant run below; then `--update-golden` for sample/expected; `test_dd2b_books` b4 list + backend
   `test_dd2b_profile_admission` a0 (nine profiles); `test_dd2b_round7` r12 reads the sample/fixture invoice rows.
2. `tools/dd_check.py`: C-DD5, C-DD7, C-DD20 out of `STUBS`; C-DD6 EV clauses out of `PENDING` (Kisiwa/Mto stay DD3b,
   D-DD.146). Judges on rows (D-DD.55/124), fetch returns {} until DD5. `backend/tests/test_dd4_check.py` (new) on hand
   rows, plus simulator tests on emulated rows. Open point: the readings manifest declares no cadence and rows carry no
   `source_mode` (a store field): judge against the checker's own table and take source modes as a separate input.
   C-DD20 cold needs crate-days per month (history `crate_days`, or the ledger).
3. Reach set once at the end (preflight-remaining §4 DD4b list); architecture guard; statement catalogue.
4. Packet: evidence below; Known deviations 5-7 (see packet).

## Plants (run 3, revision 059f211ad, scratch /tmp/claude-1001/.../ce5c6176.../scratchpad/dd44)
- Main goldens (main 0c44ae75b): exports + extras sha256, COLD-MWEA full-span telemetry (31.1 s), Kobo W1 hashes.
- Branch: cold 3 rooms one process 87.8 s, 199 MB peak. COLD-MWEA's 129 day files + manifest byte-identical to main;
  every mini-grid and cold book and the extras identical to main; only `metro-bus.profile.ev-fleet-roster.csv`
  differs (DD4.3's roster to 6 Nov, run 1).
- Cold measured October (kWh / bill): Mwea 1576.300 / 315.26, Thika 1771.350 / 354.27, Kirinyaga 2113.603 / 422.72
  (D-DD.144 projected 315.26, 354.26, 422.72). Statement Oct: revenue 4588.00, energy_cost 1092.25.
- EV plant: EV_PLANT_LINE

## Risks
- `meter_billed` EV leaves `kwh_2200_2400`, `kwh_0000_0500` are written `metered: null`: D-DD.99's EV key set has no
  hour sums (question for the Architect; default: not measured, never derived).
- `_vertical`'s run is dropped after `_measured_view`; a caller wanting the run must keep its own.
