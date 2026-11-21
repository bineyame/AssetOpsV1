# 0K3 review packet

Branch `task/0K3-replay-reader` off `main` `e9d6cdfb1`. Spec rev 2, rulings D-0K3.1-20. 2.5 units, two commits
(`898ddae00` unit 1, `afef9c26d` unit 2). No migration, no served text, no guard change, no consumer edited.
`USER_REVIEW_REQUIRED: false`.

## Pre-flight print (§0)

- (a) MG-W402-001 snapshot: `pv_available_power` pv-inverter-controller/available-power; `pv_power`
  pv-inverter-controller/ac-power; `generator_power` generator-controller/ac-power; `generator_state`
  generator-controller/status; `battery_soc` battery-pcs-controller/state-of-charge; `fuel_level`
  fuel-level-sensor/fuel-level; `feeder_demand` clinic/mill/residential-meter active-power. One row per role at
  2026-10-12 00:00 local read back: kW roles `interval_start 21:00Z, interval_end = source_time = 21:05Z`, unit `kW`;
  SOC `%`, fuel `L`, state `state`, no interval; all `SIMULATED`; bound loads `load-clinic, load-mill, load-res`; the
  last step's PV row `[20:55Z, 21:00Z)` ends at the window's end (2026-10-12T21:00Z).
- (b) DS3 Kobo: role set `minigrid-roles-1`, bound roles battery_power, battery_soc, feeder_demand, fuel_level,
  generator_power, generator_state, pv_irradiance, pv_power (no `pv_available_power`); K1 holds 0 `pv_power`
  readings (roles read: battery_soc, feeder_demand, generator_state).
- (c) W402 `Africa/Nairobi`; **Kobo `Africa/Addis_Ababa`** (spec expected Nairobi): mid-build Q1, default applied
  (both UTC+3, no clock change; G4b's window and subject unchanged).

## What was built

- `backend/assetops_backend/runs/replay_series.py`: types and constants of §2.1, `local_window` (24-hour local days,
  D-0K3.18), `bound_assets`, `series_from_readings` (§2.3), `SeriesReader.read` (§2.2 order).
- `runs/composition.py`: `build_series_reader(database_url)` (lazy imports of the two builders and the reader).
- Tests: `backend/tests/test_0k3_replay_series.py` (B1-B12, 33), `test_0k3_replay_series_postgres.py` (G1/G1b, G2,
  G3, G4, G4a, G4b; 6), `host/tests/test_0k3_series_equivalence.py` (T1, T2). Seam allow-list +2 names (D-0K3.8).

## G1 totals beside R0's literals (asserted in G1)

| | R0 literal | G1 (MG-W402-001, stored) |
|---|---|---|
| PV | 300 kWh (12.5 kW x 24 h) | 300 |
| loads clinic / mill / res | 30 / 72 / 186 kWh | 30 / 72 / 186 |
| generator | 48 kWh (24 kW, 06:00-08:00) | 48 |
| starts | 1 | 1 |
| min SOC | 60 % | 60 |

Every field of G1 also equals R0's 288-value tuples; `study_days` gives one `StudyDay("2026-10-12", 0, 288)`.

## T1 (field by field) and T2

`pwsh -NoProfile -File tools/run-host-tests.ps1 -- host/tests/test_0k3_series_equivalence.py` (via
`tools/heavy-slot.sh`): 2 passed, 17.9 s. T1: `interval_start`, `timestep_minutes`, `pv_available_kw`, loads by
`load_id`, `generator_kwh`, `generator_state`, `soc_pct`, `start_fuel_l`, `input_class` all equal
`observed_series(trajectory, 2304)`; `off_grid == ()`. T2: `replay_study(..., grid=())` with `frame(min_litre_days=8)`
gives the same status and `Calibration` on the read as on the season. Note (D-0K3.16): the season's loads are
requested power published as `feeder_demand`, so T1 proves placement, not D-0K3.5's meaning.

## Refusal table

| Code | Subject | Test |
|---|---|---|
| READER_WINDOW_INVALID | days, first_local_date, knowledge_at, timezone, `day:2026-10-25` | B10 (zero queries) |
| READER_SITE_UNKNOWN | the site id | B10 (zero queries) |
| READER_ROLE_UNBOUND | pv_available_power | B7, B7b, B10, G4, G4a |
| READER_BINDING_CHANGED | generator_power | B7 |
| READER_ASSET_UNKNOWN | `feeder_demand:<id>`, `feeder_demand:None` | B7 |
| READER_COHORT | AMBIGUOUS / EMPTY | B10 / G3 |
| READER_RESOLUTION | coarser, instant-for-mean, interval-for-instant, crosses edge (start and end) | B3, G2, G4b |
| READER_READINGS_CONFLICT | overlapping means; two instants at one step | B4 |
| READER_UNIT / READER_VALUE / READER_STATE_UNKNOWN | `<role>@<iso>` | B5 |
| READER_INPUT_CLASS | mixed, REPLAY | B8 |
| READER_START_FUEL_UNKNOWN | fuel_level | B6 (fuel), B9 |

## Plants (throwaway worktree `AssetOpsV1-0k3-plant`, removed after)

Each plant applied to `replay_series.py` alone (`git checkout` between), `tools/heavy-slot.sh --db`, 4 m 30 s; the
clean file passes B1 after. Every named test failed:

| # | Plant | Failed (count) |
|---|---|---|
| P1 | 15-min mean split into three steps | B3 (1), G2 (1) |
| P2 | missing minute: mean of present minutes | B2 (1) |
| P3 | SOC at `t_k + 2 min` read as step k | B6[battery_soc] (1) |
| P4 | query adds `pv_power`, PV falls back to it | B7b (1), B10 query (1), G4a (1) |
| P4b | PV reads `pv_power` whenever bound | G1/G1b (1) |
| P5 | bindings after the cohort | B10 order (1) |
| P6 | `input_class` hard-coded SIMULATED | B8 (1) |
| P7 | `generator_kwh = gen_kw` | B1 (1), T1 (1) |
| P8 | loads by asset id | B1 (1) (test ids run against code order) |
| P9 | second SOC instant wins | B4 (1) |
| P10 | non-GOOD bad unit refuses | B5 (1 of 6) |
| P11 | start fuel from any step | B9 (1) |
| P12 | `Fraction(float(value))` | B2 (1, `"10.1"`/`"1.3"`), B12 (1) |
| P13 | state/SOC carried forward | B6b (1) |
| P14 | `interval_start = iso(window.start)` | B1 (1), B11 (1), G1 (1) |
| P15 | clock-change check removed | B10 window refusals (2 of 8: the two London cases) |
| P16 | mean ending at `window.end` outside | B1 (1), G1 (1) |

## Stated plainly (D-0K3.12, D-0K3.1)

- Kobo's harness day is refused on its configuration (G4, G4a: `pv_power` bound and read, still unbound
  `pv_available_power`) and on its own 15-minute instants (G4b). The refusal of a 15-minute *mean* (UP-1's shape) is
  proven on stored readings at MG-W402-001 (G2) and on synthetic readings (B3), **not** on a UP-1 upload at Kobo.
- No study ran on stored readings. It waits for (a) a Site with the six roles bound and 61 days of 5-minute
  readings, (b) for Kobo, a binding of `pv_available_power` (row 48), (c) `6c`, which calls `read`.

## Risks for 6c

- Means tiling tolerance: a real feed's 5-minute means may not tile a step exactly (small gaps or overlaps at the
  edges); the reader refuses overlap and sums exact fractions, so `6c` may need a stated tolerance for real feeds.
- `readings_used` counts readings placed on a read step whatever their quality (non-GOOD included), so coverage
  should be judged from the empty steps, not from `readings_used`.
- Build `StudyFrame` from `read.timezone`, never from a literal.

## Known deviations

1. `types` joins §2.1's import set: §2.1's own `UNITS`/`INPUT_CLASS_BY_MODE` are `MappingProxyType`, which lives in
   `types` (B10 pins the set with it).
2. §2.3 step 1 read literally (`COALESCE(interval_end, source_time) <= window.start` skipped) would skip every instant
   at `t_0`, the start fuel included. Instants are skipped only outside `[start, end)`; means as written.
3. G1's stored values are canonical decimals (`"12.5"`, `"3"`, `"24"`, `"80"`, `"15000"`, G1b `"9"`): the envelope
   contract refuses `"12.50"`. The values, and every expected tuple, are R0's.
4. `readings_used` counts readings placed on a step the series reads (means in a step, instants at a step start),
   whatever their quality; a fuel instant after `t_0` is not read and not counted.
5. A mean with `interval_end <= interval_start` is refused `READER_RESOLUTION` ("an empty or reversed interval"),
   a branch §2.3 implies but does not name.
6. Unit 1's commit carries `SeriesReader` too (one module); B10/B11 and the builder are in unit 2's scope as run.

## Verification

All through `tools/heavy-slot.sh` (`--db` for Postgres), PYTHONPATH = this worktree's backend, contracts, simulator,
tools; revision `afef9c26d` (code) unless stated.

| Command | Result | Wall |
|---|---|---|
| pytest `test_0k3_replay_series.py test_0k1_replay_port_seam.py test_0k2_replay_study.py` | 62 passed | 4.6 s |
| `pwsh tools/run-host-tests.ps1 -- backend/tests/test_0k3_replay_series_postgres.py` (with the pre-flight file, since deleted) | 7 passed (6 + pre-flight) | 3 m 12 s |
| `pwsh tools/run-host-tests.ps1 -- host/tests/test_0k3_series_equivalence.py` | 2 passed | 20 s |
| pytest `contracts/tests` | 190 passed | 69 s |
| `tools/check-architecture.ps1` (ASSETOPS_GUARD_PYTHON set) | Architecture check passed | 1.5 m |
| `tools/check-agent-workflow.ps1` | Agent workflow check passed | |
| `tools/check-all.ps1` (fast, after the index fix) | no FAIL line, no "Check failed" (40 blocking guards) | 121 s |
| `tools/select-tests.py --base main` | 282 of 575 backend files (runs/composition.py is widely imported); not run: full suites are the coordinator's | |

A first check-architecture run without `ASSETOPS_GUARD_PYTHON` failed only on "the chain structure guard cannot run:
no Python interpreter" (environment, not code); the first check-all failed on `.ai/state/index-2.md` over its
8000-byte cap from this slice's index line, shortened, then rerun.

Mid-build count: 4 (corrected at review, L3): deviations 1 (`types` import), 2 (instants outside `[start, end)` only), 5 (the empty or reversed interval) and Q1 (Kobo's zone, Addis Ababa not Nairobi); defaults applied, nothing stopped. Spec rev 3 amends the text to match.


## Change after merging main (SC-1a)

The statement guard found 18 HAND_BUILT_NEW fingerprints in `runs/replay_series.py` (the English `detail` arguments). Route taken: D-SC1.34's declared-unserved class (D-0K3.9: `detail` is never served). `SeriesRefused` is added to `schema.UNSERVED` in `i18n/schema.py`, and to the two tests that pin the tuple (`backend/tests/test_sc1_statements.py`, `tools/checks/test_statement_catalogue.py`). No detail text, code, subject or behaviour changed; baseline, allow file and guard untouched. `statement_catalogue.py` exits 0.
