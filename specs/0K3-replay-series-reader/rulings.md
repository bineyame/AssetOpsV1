# 0K3 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0K3.1 to D-0K3.9 are applied by `spec.md` rev 1. Checked against `main` (`315e75fc7`) by reading the evidence
query, the cohort selection, the two harness Sites' binding files (`backend/conversions/kobo-001-bindings.json`,
`mg-w402-001-minigrid-roles-4.json`) and 0K2's season publisher. Owner-level calls: row 45 of
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
- **Consequence to the owner (row 45).** The one real-data channel built today, UP-1's reading upload, is a
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

## D-0K3.4 `pv_power` is never read as available PV (owner-level; row 45)

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
  added; the reader reads through the existing evidence query and Foundation store. D-SC1.28 is not engaged.
