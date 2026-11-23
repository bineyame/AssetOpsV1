# DD4b handoff (PARTIAL: DD4.3-DD4.5 done; DD4.6 built to the doc sweep, re-base and slice end open)

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

- Run 6 (DD4.5 rest; main merged `2d325b04a`; packet "Run 6"): `bbeaf1c76` M stated fields, D-DD.30 chain, sweep,
  `check_manifest.py` re-based (6 FAIL = main's 6). 3B6 test_4 and K13 pass; 6h parity unedited (no key moves);
  6c+6h 199 passed. vNEXT mock JS, gen_docs.cjs, CHANGE-REGISTER, fixture-mapping left for the alignment pass.

- Run 7 (DD4.6, D-DD.144; main merged `9c7d50156` at 2bedbecf2): `b2c0f98d1` tests first
  `simulator/tests/world/test_dd46_cold_energy_model.py` (4 failed first, log `/opt/assetecon/evidence/DD4b/t46-first-fail.log`)
  + golden `golden/efficiency_condition_main.json` (old `_efficiency` over 6e3c02ab5's M); `8acfaab77`
  `telemetry_cold.EFFICIENCY_CONDITION`; `5ddf77777` + `83e83cbff` M rev 16.21 (1304 + 0.0554, reproduced exactly by the
  test's OLS), October kwh = meter (Kiri 2113.60 at the checker's 2-decimal precision), plan kwh whole (1716/1785/1854:
  the budget export refuses non-whole, EMU_QUANTITY), Thika gains an ENERGY_EFFICIENCY bridge row (+2.73, RC2);
  evaluator vs stated 0 differences; history.json (only cold kwh + digests move), derived-values, fixtures.js, index.html
  regenerated. Moved: Mwea contribution 202.74 (+2.1 %), Thika 843.73, Kiri 1081.28 (+14 %, -52.01/month), KIRI-REPAIR
  41.61/month, +149.26 net 12m, KIRI-REPLACE -3,953.50, MWEA-AGG +2,370.56 (energy 49.86/month; not in the ruling's
  table, follows mechanically), plan +2,519.82, downside 149.26. Bills 315.26 / 354.27 / 422.72.
  Plant before (8acfaab77): cold measured.json identical to the committed fixture, 91 s, 42,800 kB.
  Plant after (83e83cbff): 3 cold rooms' 391 telemetry files byte-identical to before; only
  `harvest-cold.profile.cold-budget.csv` (plan kwh lines) and `extras/harvest-cold.meter-billed.json` (M's figures beside
  the meter) differ; the measured cold bill is unchanged. Hash lists `/opt/assetecon/evidence/DD4b/before.sha`, `after.sha`.

## Next
1. DD4.6 rest: doc sweep DONE `2d7fa12a1` (9 layer4 docs + design .html, walkthroughs.md 3 figures the checker named,
   go-to-market commercial-plan/website-content + .html because the checker reads them; log `cm46-sweep.log`: only H8,
   H10, H9, K8, 3 K13 + main's 6 left). Packet points from the sweep: derived k rounds to 0.06 so MWEA-AGG energy is
   `rec`-tagged (49.86); new figures worked in domain-and-decision-models §4.5 (repair break-even 56 % recovery, replace
   payback 68 months, Mwea break-even rate 0.048) need a reviewer glance; Thika's negative control swapped to occupancy
   (line 150); 52.01 (excess vs model) and -51.92 (vs plan) both appear. Next: re-base check_manifest H8,
   H10, K8, K13 (sites, portfolio, history) with a dated note as run 6 did, until 6 FAIL = main's 6
   (main 2bedbecf2: `cm46-main.log`).
2. Then the slice end: 6h parity (test_6h_parity unedited; cold keys in golden/6h_parity.json: one `cold_room` hit,
   check whether it moves), focused tests (test_dd46*, test_dd4_cold_books, test_dd4_telemetry_cold, test_3b6), guards,
   the reach set once in one `--db-lane` call (cite `.agent/main-baseline/`), packet Run 7 (note: vNEXT mock JS left for
   the alignment pass), state entry, spec Status in_review.
## Next
2. At DD4b's end: spec Status `in_review`, a `.ai/state/` entry and its index line (not written yet: DD4b is not done).
3. Open for the Architect (packet deviations 8-10): the EV hour sums (C-DD7 pending, question (a)), C-DD5's "on
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
- EV writer memory: fixed in run 5 (3.8 GB -> 149 MB peak, 1,620 s -> 1,567 s, three depots; bytes identical).
  `_import` (one Fraction per non-zero minute) is still held for the span.
- The vNEXT mock still shows Kasarani's old figures in hand-typed JS text (alignment pass).
- `_vertical`'s run is dropped after `_measured_view`; a caller wanting the run must keep its own.
