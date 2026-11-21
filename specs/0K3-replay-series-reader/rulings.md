# 0K3 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0K3.1 to D-0K3.9 are applied by `spec.md` rev 1. Checked against `main` (`315e75fc7`) by reading the evidence
query, the cohort selection, the two harness Sites' binding files (`backend/conversions/kobo-001-bindings.json`,
`mg-w402-001-minigrid-roles-4.json`) and 0K2's season publisher. Owner-level calls: row 48 of
`specs/OWNER-AWAY/decisions-2026-11-21.md` (owner to weigh in).

## D-0K3.1 What 0K3 builds now, and what it waits for (amends D-0K2.1's reason for waiting)

- **Ruling.** 0K3 builds the producer of 0K2's seam: a reader from accepted readings to `ObservedSeries`, every
  refusal, and a Postgres builder. It is proven on three fixtures: hand-written readings (no database), the two
  harness Sites in a test database (MG-W402-001 for the positive path, DS3's converted Kobo for an honest refusal),
  and 0K2's simulated season published as readings, read back to the season's own series. It runs no study on stored
  readings and adds no tool mode.
- **It waits for:**
  1. a stored series to read: a Site with the six roles bound and 61 days of 5-minute readings. Today that means DS2's
     writer at a configured world Site (D-DS4.1: none this fortnight, plus the queued Site-configuration unit) or a
     pilot's EMS export through the product's import path;
  2. for Kobo, a binding of `pv_available_power` (D-0K3.4);
  3. `6c`, the evaluator, which chooses the Site's frozen base run and calls `read`, then `replay_study`.
- **Why build now.** D-0K2.1 deferred the reader because "a reader built now could only be tested on rows its own
  test invents". Three things changed the weighing: the harness Sites give real accepted readings through the real
  ledger (not rows the reader's test invents in memory), the season publisher gives a kernel-backed equivalence (T1),
  and every refusal the reader needs is visible today on the harness data (an unbound role, 15-minute instants). The
  reader then exists, reviewed, when the first series lands, and `6c` adds a call, not a mechanism.

## D-0K3.2 Each reading is placed by its own interval or instant; nothing is spread or filled

- **Ruling.** A kW role needs interval means inside one 5-minute step; means that tile a step exactly give its exact
  time-weighted value; a mean longer than the step (15 minutes) or crossing a step or the window edge is refused
  `READER_RESOLUTION`. Charge, fuel and generator state need an instant on a step start. A gap, a non-GOOD part or a
  missing instant leaves the step `None`.
- **Why refuse 15 minutes rather than split it.** Holding a 15-minute mean flat over three steps invents the shape
  inside it, and the replay's dispatch reacts to that shape (a load peak inside 15 minutes changes when the generator
  starts). D-0K2.6 already refused fill rules until real series show what they need. Averaging finer means is exact
  and invents nothing.
- **Consequence to the owner (row 48).** The one real-data channel built today, UP-1's reading upload, is a
  15-minute CSV of PV output and feeder power. Readings it admits can never feed the study as specified. The study
  needs an EMS or gateway feed at 5 minutes or finer.

## D-0K3.3 An instant is read only on a step start; no state is carried forward

- **Ruling.** Charge, fuel and state readings count only when `source_time` equals a step start. Other instants are
  counted per role in `off_grid` and not read.
- **Why.** A charge sampled at 00:02 is not the charge at 00:00, and a state reported only on change is a different
  signal shape from a sampled state: reading either needs a rule (a tolerance, a carry-forward with a staleness bound)
  that only a real feed can justify. `dispatch_v3`'s 10-minute instant tolerance is sized for hour windows, not for
  5-minute steps. Default: strict; counted, so a real feed's shape is visible in the first read; a ruling follows
  the first real feed (queue Q3).

## D-0K3.4 `pv_power` is never read as available PV (owner-level; row 48)

- **Ruling.** The PV series is `pv_available_power` only. A Site that binds only `pv_power` is refused
  `READER_ROLE_UNBOUND` `pv_available_power`.
- **Why.** The replay needs what the array could have given (0K2: "average PV-available kW per step, after the
  inverter limit"); `pv_power` is what the inverter did give, which is curtailed whenever the battery is full and the
  load is low. Reading output as availability would understate PV on exactly the clear days where a lower generator
  stop saves fuel, and bias every avoided-litre figure. The owner's honesty rule forbids the substitution.
- **Consequence.** Kobo's binding file binds `pv_power`, `pv_irradiance` and the feeders, not `pv_available_power`.
  Even with stored telemetry, Kobo cannot run the study until its binding set gains `pv_available_power` (an inverter
  register or an EMS export of available power). **Owner to weigh in**; an irradiance-based estimate is a model, not a
  reading, and would need its own ruling and label.

## D-0K3.5 Loads are delivered feeder power, by asset code

- **Ruling.** Each load series is the `feeder_demand` role of one bound load asset, its `load_id` the asset's
  `asset_code` (the component id rule `sites/battery_boundary.py:130` already uses). The port refuses a code that is
  not a load of the run (`REPLAY_ADDRESS_UNKNOWN`), so the reader does not restate the plant.
- **Why `feeder_demand`.** It is the required MINIGRID role, bound at every mini-grid Site, and what a meter
  measures. The replay's load is requested power; the two differ only while load goes unserved. On a Site with
  unserved energy the replay's load is understated by it, so `SeriesRead.load_role` states which role was read, and
  `6c` reads unserved energy with that in mind. Preferring `feeder_requested_power` where bound is queued (Q4): it is
  bound at MG-W402-001 for two of three feeders only, so a per-feeder rule would mix two meanings in one series.

## D-0K3.6 The input class comes from the readings' own source mode

- **Ruling.** `LIVE` reads as `RECORDED`, `SIMULATED` as `SIMULATED`; a mix, or any other mode, is refused
  `READER_INPUT_CLASS`. Only readings that set a value count.
- **Why.** 0K2 made the class travel with the series (D-0K2.20) so `6c` never reads a simulated calibration as a real
  one. The class must come from the evidence, not from the caller.

## D-0K3.7 Order: configuration before readings, the cohort's status named

- **Ruling.** Request, Site, query, bindings, cohort, readings (spec §2.2). A role that is not bound is named first,
  whatever the readings; a cohort that is not usable is refused with its own status (`AMBIGUOUS`, `EMPTY`), reusing
  `select_cohort` and `build_input_set` unchanged; the input set's `input_sha256` is returned as the read's basis
  identity.
- **Why.** The analyst's first question at a new Site is "what is missing from the configuration", and the cohort
  rules are the product's one definition of which source to believe.

## D-0K3.8 The 0K1 seam test's allow-list grows by the reader and its test

- **Ruling.** `runs/replay_series.py` and `tests/test_0k3_replay_series.py` join the allow-list of
  `test_nothing_else_in_the_backend_names_the_replay` (the reader builds `LoadSeries` from
  `assetops_contracts.forward_replay`). A test allow-list, as D-0K2.14; not a guard change.

## D-0K3.9 No served text, no migration, no guard change

- **Ruling.** Nothing is served or rendered; `SeriesRefused.detail` is a developer diagnostic. No table or column is
  added; the reader reads through the existing evidence query and Foundation store. D-SC1.28 is not engaged. After main's SC-1a merge the unit declares the class unserved by the D-SC1.34 route: `SeriesRefused` is added to
  `schema.UNSERVED` (and to the two tests that pin that tuple); the guard, baseline and allow file are unchanged.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Each answer is checked against `main` (`5f8ae6c94`) and
folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. None is owner-level: row 48 (D-0K3.2, D-0K3.4) is
unchanged.

### D-0K3.10 `interval_start` is the study's own instant form; the study's window check runs in B11 (R4, a spec bug)

- **Ruling.** R4 is right: `assessment_inputs.iso` gives `"%Y-%m-%dT%H:%M:%S.%fZ"` (`assessment_inputs.py:41-42`),
  and `replay_study._start_instant` (`replay_study.py:264-272`) refuses any text that is not exactly
  `"%Y-%m-%dT%H:%M:%SZ"` with `STUDY_WINDOW_INVALID` `start`. Every series rev 1 would have made was refused by the
  study. The reader sets `interval_start = window.start.strftime(INSTANT)` with its own constant `INSTANT =
  "%Y-%m-%dT%H:%M:%SZ"` (the study's `_INSTANT` is private; B1 pins the literal). Subjects keep `iso` (developer
  diagnostics).
- **Tests beyond T2.** B1 pins `interval_start == "2026-10-11T21:00:00Z"`. B11 calls the study's public
  `study_days(read.series, frame)` (D-0K2.16 made it public) and asserts one `StudyDay("2026-10-12", 0, 288)`, then
  `replay_study` returns `SAMPLE_TOO_SHORT`, not `STUDY_WINDOW_INVALID`. G1 asserts the same `study_days` result on
  the Postgres read. Plant P14 (`interval_start = iso(window.start)`) fails B1, B11 and G1.
- **The class (W6).** Every field the reader hands the study is checked by the study's own validator in a test:
  `study_days` covers `interval_start` and `timestep_minutes` and the 288-step days; B11 also asserts every series of
  the read has 288 values (the study's `STUDY_SERIES_MISALIGNED` check).

### D-0K3.11 The rule "inverter output is never available PV" gets fixtures that can fail it (R1)

- **Ruling.** Three cases, each with `pv_power` bound and read:
  - **B7b** (no database): R0 with the PV binding's role `pv_power` (asset `pv-inverter`) and its 288 readings as
    `pv_power`, served by a stub evidence source that returns them whatever the query's roles: `SeriesReader.read`
    refuses `READER_ROLE_UNBOUND` `pv_available_power`.
  - **G1b** (Postgres): MG-W402-001 binds both `pv_power` (`pv-inverter-controller`/`ac-power`) and
    `pv_available_power` (`.../available-power`) on asset `pv-inverter` (checked in
    `backend/conversions/mg-w402-001-minigrid-roles-4.json`). G1 plus `MEAN` rows of `ac-power` at `"9.00"` kW every
    step: the PV series is still all `Fraction(25, 2)`.
  - **G4a** (Postgres): K1 plus Kobo's own inverter readings, 15-minute `POINT`s of `pv-inverter-controller`/
    `ac-power` (`"5"`) sealed by `seal_rows` beside K1 (Kobo binds that channel as `pv_power`): refuses
    `READER_ROLE_UNBOUND` `pv_available_power`.
- **P4 rewritten so it can fail:** "the query adds `pv_power` and PV falls back to it when `pv_available_power` is
  unbound" fails B7b, B10 (the query's roles) and G4a (it would reach `READER_RESOLUTION` instead); P4b "PV reads
  `pv_power` whenever it is bound" fails G1b. Pre-flight (b) prints whether K1 holds `pv_power` readings (it does
  not: `day_rows` writes generator status, three feeders and charge), so G4a adds them.

### D-0K3.12 Kobo's own readings meet a real readings refusal; the 15-minute mean is proven on W402 only (R2)

- **Ruling.** **G4b**: K1's accepted readings read through the real store with the reader's own query (local day
  2026-10-06, `Africa/Nairobi`, window 2026-10-05T21:00Z to 2026-10-06T21:00Z), then `bound_assets` over Kobo's real
  bindings plus one test-only `RoleBinding` of `pv_available_power` on Kobo's `pv-inverter` asset, then
  `series_from_readings`: `READER_RESOLUTION` subject `feeder_demand:load-clinic@2026-10-06T00:00:00.000000Z`, detail
  "an instant where an interval mean is needed". K1's feeders are 15-minute instants (`day_rows`), so Kobo's harness
  day is refused on its readings, not only its configuration.
- **Stated plainly (spec §1 and the packet):** the refusal of a 15-minute *mean*, the shape UP-1's CSV admits
  (`[t - 15 min, t)` interval means), is proven on stored readings at MG-W402-001 (G2, the real ledger) and on
  synthetic readings (B3), not on a UP-1 upload at Kobo: that needs the UP-1 gateway flow
  (`host/tests/test_up1_reading_upload_flow_postgres.py`), which 0K3 does not run.

### D-0K3.13 "Nothing carried forward" is tested on every instant role (R3)

- **Ruling.** B6 is parametrised over the three `INSTANT_ROLES`: SOC instants at `t_k + 2 min` leave `soc_pct` all
  `None`, `off_grid == (("battery_soc", 288),)`; state the same for `generator_state`; fuel only at `t_0 + 2 min`
  refuses `READER_START_FUEL_UNKNOWN`. **B6b** (K1's shape): SOC and state instants only at every third step start
  (`t_0, t_3, ...`, 96 each): steps `3j` take them, steps `3j + 1` and `3j + 2` are `None`, `off_grid == ()`. Plant
  P13 "a step without an instant takes the previous step's state or SOC" fails B6b.

### D-0K3.14 One read is bounded by days; the cohort's `EMPTY` is the only empty answer (R5)

- **Ruling.** `MAX_DAYS = 92` (was 366): the study needs 61 days, and 92 covers a quarter. The stated bound: at
  5-minute readings one read holds about 92 × 288 × (5 + loads) readings plus the 6-hour bracket, about 212,000 for
  three loads (five times that for the kW roles at 1-minute means). No separate count cap. B10 refuses `days` 93.
- **`EMPTY`.** Step 5 raises it (`select_cohort` returns `EMPTY` when no reading of the queried roles lies in the
  window); G3 tests it. Step 7's "no reading set a value" branch is removed: it is unreachable, because step 6 has
  already refused unless a GOOD fuel reading at `t_0` set `start_fuel_l`.

### D-0K3.15 G1's load codes are R0's (I1)

- **Ruling.** Checked: MG-W402-001's `feeder_demand` bindings are assets `load-res`, `load-clinic`, `load-mill`
  (`mg-w402-001-minigrid-roles-4.json`), the codes R0 uses. G1's expected loads are R0's literals, ids and values;
  pre-flight (a) also prints each bound load's asset code, and a different code is a pre-flight question.

### D-0K3.16 The study does not depend on load order (I2)

- **Ruling.** Confirmed: `replay_study` iterates loads sorted by `load_id` (`replay_study.py:310`) and the host port
  keys them by `load_id` (`host/forward_replay.py:197-216`), so T2 is order-independent and the reader keeps
  ascending codes. Note for T1: the season's loads are `load-requested-power@<id>`; S8 publishes those values as
  `feeder_demand`, so T1 proves placement, not D-0K3.5's meaning (stated in the packet).

### D-0K3.17 The last step's mean is read (I3)

- **Ruling.** W402's `MEAN` rows carry `interval_end = source_time` (`tools/w402_mini_depth_cases.py` `_envelope`), so
  `placed_at` is the interval end. `cohort.py:67` uses `window.contains(placed_at)` only to decide which streams are
  candidates; `build_input_set` (`assessment_inputs.py:351`) keeps every reading of a chosen stream over the read
  range. The mean `[t_287, window.end)` is therefore kept, and §2.3 step 1 keeps it (it neither ends at or before the
  start nor starts at or after the end). Tests: G1 asserts step 287 of PV, each load and generator power is set, and
  B10 (stub through the real `select_cohort` and `build_input_set`) the same. Pre-flight (a) prints `(interval_start,
  interval_end, source_time)` of the last step's PV row. A stream whose only in-window readings end at `window.end`
  is not a candidate and its step stays `None` (no fill; stated).

### D-0K3.18 Every local day must have 288 steps; a clock-change day is refused before the query (I4)

- **Ruling.** The study refuses any local day that is not 288 steps (`replay_study.py:301-304`, D-0K2.7). The reader
  refuses it first, at step 2: for each local day of the window, `local midnight of the next day − local midnight`
  must be 24 hours, else `READER_WINDOW_INVALID` subject `day:<local date>`. This replaces rev 1's `steps` subject (a
  24-hour day is 288 steps in any zone). B10: `Europe/London`, first day 2026-10-25 (25 hours) refuses `day:2026-10-25`
  with zero queries; `Asia/Kathmandu` (UTC+5:45) for one day reads.

### D-0K3.19 Confirmations (I5, I6)

- **I5.** `test_nothing_else_in_the_backend_names_the_replay` scans for the text `forward_replay`;
  `runs/composition.py` and `build_series_reader` never contain it, so the allow-list grows by exactly D-0K3.8's two
  names. `test_0k3_replay_series_postgres.py` must not contain the text either: it compares loads by `load_id` and
  `kw` and imports no `LoadSeries`. A seam-test failure on any other file is a mid-build question, as proposed.
- **I6.** `pwsh` is installed (`/usr/bin/pwsh`); run `tools/heavy-slot.sh -- pwsh -NoProfile -File
  tools/run-host-tests.ps1 -- host/tests/test_0k3_series_equivalence.py` and print it in the packet. If it cannot
  run, T1 and T2 are reported not run, never passed.

### D-0K3.20 Size: 2.5 units (was 2)

- Unit 1 1.1 (B6 over three roles, B6b, B7b, the `interval_start` fix); unit 2 1.4 (the clock-change refusal, B11's
  study check, G1b, G4a, G4b, step 287).
