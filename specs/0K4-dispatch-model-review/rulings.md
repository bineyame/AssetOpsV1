# 0K4 rulings (D-0K4.1 to D-0K4.18)

Architect (Claude), 2026-11-21. Builds the 0K4 path the owner accepted the same day
(`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`: "Accept all (Recommended)", and the one-figure rule).
Review: `review-for-owner.md`. Unit specs: `specs/0K4a-dispatch-v8/`, `specs/0K4b-fuel-curve-taper/`,
`specs/0K4c-declared-season/`, `specs/0K4d-rerun-restate/`, `specs/0K4e-candidate-energy/`. Change list:
`one-figure-change-list.md`. Operator request: `operator-request.md`. Owner-level call: owner-away row 56.

## D-0K4.1 Units, sizes, order and lanes

| Unit | What | Size | Needs | Lane |
|---|---|---|---|---|
| `0K4b` | Fuel curve and charge taper: a pure module, three Foundation properties, the assumed Kobo values as a fixture | 1.5 | `main` | 2, first |
| `0K4a` | `mini-grid` v8: the generator takes the load (cycle charging, generator support, minimum load); assembles v8 with 0K4b's module | 2.0 | `main`; 0K4b merged before its commit 3 | 1, first |
| `0K4e` | `dispatch-3.3`: a battery-support Candidate also needs the energy to reach solar cover | 2.0 | `main` | 3, first |
| `0K4c` | Declared season v2: overcast spells of 1-4 days, loads ±15 % day to day, the mill off on Sundays | 1.0 | 0K4b merged (its fixture) | 2, after 0K4b |
| `0K4d` | Admission rule as code, rerun of the Kobo and Mto studies on v8 and season v2, MG-T lines restated | 1.5 | unit 1: `main`; units 2-3: 0K4a, 0K4c merged | 1, after 0K4a |
| `0K4m` | Pack and mock restated to one figure per quantity (manifest inputs, derived values, vNEXT fixtures) | 0.75 | 0K4d merged | any free lane |

- **Total 8.75 units** (the review's 5.5 for a-d, plus 0.5 for the admission rule as code in 0K4d, 2.0 for the
  candidate fix 0K4e and 0.75 for the pack restate 0K4m).
- **Fastest honest route to figures:** lane 1 is the critical path, 0K4a (2.0) then 0K4d (1.5): about 3.5 units. Lane 2
  (0K4b 1.5 then 0K4c 1.0) runs inside it: 0K4b merges while 0K4a builds its first two commits, and 0K4c merges while
  0K4d builds its unit 1 (stub-tested code that needs neither v8 nor the season). Lane 3 (0K4e, 2.0) is independent
  and starts at once, because its reassessment of stored windows is a heavy database job the coordinator schedules one
  at a time. 0K4m follows 0K4d in whichever lane is free.
- **Before the 5c walkthrough:** 0K4a, 0K4b, 0K4c, 0K4d and 0K4e. 0K4m does not gate it (nothing on the live product
  serves the pack's figures; `one-figure-change-list.md`).
- **Why.** Mechanism before figures (review §6). The two physics units share one version (D-0K4.2), so the version
  merges once, whole. The candidate fix touches a different layer (the product's dispatch analytic, its stored
  revisions and its consumers), has its own reviewer questions and its own database job, so it is its own unit.

## D-0K4.2 One new simulator version, `mini-grid` v8, holds both physics corrections

- **Ruling.** `mini-grid` v8 = v7 plus the dispatch rule of D-0K4.3 and D-0K4.4 (0K4a) and the fuel curve and charge
  taper of D-0K4.5 and D-0K4.6 (0K4b's module). v1-v7 are untouched: their trajectories and digests stay byte-equal
  (0K4a test N9). v8 reaches `main` only in 0K4a's merge, after 0K4b's module is on `main`; no run is ever made on a
  version holding one correction without the other. The backend profile `MINI_GRID_V8_MODEL`, the host's
  `EXECUTABLE_MODELS` and the replay port's `REPLAY_MODELS` gain v8 in the same merge.
- **Why.** Past runs stay reproducible (owner brief). A figure from a half-corrected model would be a second figure for
  the same quantity, which the owner's rule forbids.

## D-0K4.3 The generator takes the load (cycle charging)

- **Ruling.** While the generator is RUNNING over a step, in each segment, with `D` demand, `A` PV available, `R` the
  generator's usable rating (rating, or less by fuel), `C` the battery's charge acceptance (PCS charge limit, taper of
  D-0K4.6, headroom to full) and `M` the minimum load of D-0K4.4:
  1. `D > A + R`: **generator support.** The generator gives `R`, PV gives `A`, the battery discharges
     `min(D - A - R, discharge cap)` (the cap is v7's: PCS limit and energy above the reserve in effect); the rest is
     unserved.
  2. otherwise the generator gives `g = min(R, max(M, D + C - A), D + C)`; PV used is
     `u = max(0, min(A, D + C - g))`; PV curtailed is `A - u`; the battery charges `u + g - D` (never negative, never
     above `C`). PV serves load first (`min(u, D)`), the generator serves the rest of the load, and what is left of each
     charges the battery.
  The battery never discharges beside a running generator unless the load exceeds what PV and the generator can give.
  While the generator is STOPPED, STARTING or FAILED, v7's dispatch applies unchanged (the Site's source priority, the
  battery serves load before any start; the start delay delivers nothing), with D-0K4.6's taper on every charge.
  Start and stop rules are v5's, unchanged (`effective_start_threshold`, stop at or above the stop threshold after the
  minimum runtime). The Site's source priority orders PV and battery; while the generator runs it is ahead of the
  battery whatever that priority says, which v8's statement declares.
- **Why.** Review §2 points 1-3 and §3 row 3: a battery that keeps emptying while the generator runs is the fault an
  operator's engineer sees at once, and it causes 15 of the 16 failed dawns. Cycle charging is the usual mode at Sites
  like Kobo; a load-following Site stays on v7 until a load-following rule is specified (queue Q2).

## D-0K4.4 Minimum generator load

- **Ruling.** A new Foundation property `generator-minimum-load` (unit `%`, of the generator's rating, on the
  GENERATOR) with `generator-minimum-load-basis` (`GENERIC_DEFAULT`, `MANUFACTURER_DATASHEET`, `SITE_TEST`). v8 holds
  the generator at or above `M = rating x minimum-load / 100` by charging the battery first and then curtailing PV
  (D-0K4.3 step 2). When load plus charge acceptance is below `M` there is nothing more to absorb: the generator gives
  `D + C` and the step notes `below minimum load: nothing more to absorb`. Kobo's assumed value: 30 %, basis
  `GENERIC_DEFAULT` (review §2 point 4), until Kobo's controller settings arrive (`operator-request.md` item 3).
- **Why.** Wet stacking (review §2 point 4). It is a controller setting, so it belongs on the Site's record, not in the
  model, and the basis carries the "assumed" label.

## D-0K4.5 Fuel curve: the line through the no-load rate and the full-load consumption

- **Ruling.** Fuel per segment = `r x h_on + s x E`, where `h_on` is the hours the generator is STARTING or RUNNING,
  `E` its accepted output energy (kWh), `r` the Foundation's `generator-no-load-fuel-rate` (L/h, the key the product's
  fuel balance, fuel-cost-2 and 4d already read) and `s = SFC - r / rating`, with `SFC` the Foundation's
  `specific-fuel-consumption` read as the consumption at rated output. At full load the curve gives `SFC x rating`
  litres an hour, so the declared SFC is kept and only part load and idle change. STOPPED and FAILED burn nothing.
  Refused at `prepare` (`PHYSICAL_RESOLUTION_FAILURE`): `r <= 0`, `s < 0`, or `SFC < 1/10` L/kWh (below the energy
  content of diesel). The tank's stock account moves by litres x `DIESEL_ENERGY_KWH_PER_L = 10` through two new flows,
  `fuel_energy` (tank to generator) and `generator_conversion_loss` (generator to losses), under a new balance
  `generator-fuel`: `fuel_energy = generator_output + generator_conversion_loss`.
  Kobo's assumed values: `r = 3.3` L/h basis `GENERIC_DEFAULT` (the owner's value of 2026-11-07, already declared in
  `tools/demo_combined_kobo.py:NO_LOAD`) and `SFC = 0.3` (the template's), so `s = 0.2175` L/kWh: 3.3 L/h idle,
  about 0.54 L/kWh at a quarter load, 0.38 at half and 0.30 at full. Labelled assumed until Kobo's fuel sheet arrives.
- **Why.** Review §2 point 5 and §3 row 4. The product already declares a no-load rate with a basis; reusing it keeps
  one value per fact. A curve fixed by two declared points needs no new key. The energy constant lets the kernel's
  exact stock check stay whole now that litres are not proportional to output.

## D-0K4.6 Charge taper

- **Ruling.** A new Foundation property `battery-charge-taper-start` (`%` state of charge, on the BATTERY) with
  `battery-charge-taper-start-basis` (same three bases). Above it, charge acceptance falls linearly with the headroom:
  `acceptance = limit x max(1/20, (100 - soc) / (100 - taper start))`, evaluated at each segment's start; at or below it
  the full PCS charge limit applies; a taper start of 100 means no taper. It applies to every charge, from PV or the
  generator. Kobo's assumed value: 95 %, basis `GENERIC_DEFAULT` (a lithium iron phosphate battery, review §2 point 6).
- **Why.** The last band to full charges slowly and the generator idles through it. For LFP the band starts near 95 %,
  above the stop settings studied, so the taper changes the stop-70 saving little; the rule is general so that a
  lead-acid Site (taper near 80 %) is modelled honestly when its record says so.

## D-0K4.7 Where the assumed values live and how they are labelled

- **Ruling.** The shipped `config/site-templates/kobo-mini-grid-60kw.yaml` is not edited: every Kobo run, digest and
  golden test stays as it is. The assumed values enter through a fixture, `host/tests/kobo_assumed.py`
  (`ASSUMED_PROPERTIES`, `assumed_site(document)`), which appends each property with its basis `GENERIC_DEFAULT` and
  `source: "SITE"` (0K4b). Every study result made on v8 carries `assumptions`: the tuple of
  `"<property key> <value> <unit> (<basis>)"` strings read from the run's frozen Foundation for the five properties of
  D-0K4.4 to D-0K4.6 (0K4d). The template, the product world and DS2's telemetry writer adopt v8 and these properties in
  0K4f (D-0K4.13).
- **Why.** "Labelled assumed until Kobo's sheets arrive" (owner default 3): the basis is the label, carried as data,
  never as product copy (as FUEL-1 A1 did for the no-load rate).

## D-0K4.8 Season v2: a declared season with weather spells

- **Ruling.** `host/tests/kobo_season.py` gains season v2 beside v1 (v1 byte-equal): overcast days
  `OVERCAST_V2 = {2, 3, 7, 8, 9, 13, 17, 18, 19, 20, 24, 25, 28, 33, 38, 39, 45, 50, 51, 52, 57}` (21 of 61; spells of
  1, 2, 3 and 4 days; 13 in September, 8 in October); residential and clinic loads scaled per local day by
  `1 + 15/100 x (((7d + 3) mod 13) - 6) / 6` (0.85 to 1.15); the mill off on local Sundays (`d mod 7 == 5`, 1 Sep 2026
  being a Tuesday). Still SIMULATED, and declared, not climatology; Kobo's 61 days of readings replace it.
- **Why.** Review §5: the v1 season is "too kind" (overcast every fourth day, never two in a row, the same load every
  day), and cloudy spells are the real risk (review §2 point 8). A literal calendar is reviewable and reproducible; a
  random draw is neither without its seed.

## D-0K4.9 The admission rule for a generator setting (owner default 1)

- **Ruling.** A setting is admitted against no action, over the same days, when all four parts pass:
  1. `energy_not_served`: the case's unserved kWh is not above the baseline's;
  2. `reserve_breaches`: the case's count of steps whose start SOC is below its own reserve in effect is not above the
     baseline's;
  3. `starts`: the case's most starts in one local day is at most the maker's limit (`max_starts_per_day`, default 6,
     basis `GENERIC_DEFAULT` until Kobo's generator sheet);
  4. `full_charge`: the case's longest run of consecutive local days without the battery reaching 100 % is below
     `full_charge_every_days` (default 7, LFP assumed, basis `GENERIC_DEFAULT`).
  Parts 3 and 4 are absolute; where the baseline itself fails one, that part is judged against the baseline instead
  (no worse than no action) and says so (`RELATIVE_BASELINE_FAILS`). The dawn margin (worst 05:00 SOC, its distance
  to 35 %, the dates below) is reported beside the result as information and never admits or rejects. The rule is code
  (`backend/assetops_backend/runs/admission.py`, 0K4d) that `6c` imports.
- **Why.** Owner default 1, and review §4: a dawn line tests the start and reserve settings, not the stop setting. The
  relative fallback keeps a part that no action also fails from rejecting every setting, which would say nothing about
  the setting.

## D-0K4.10 The candidate count asks for energy, not only power: `dispatch-3.3`, its own unit 0K4e

- **Ruling.** `dispatch-3.3` = `dispatch-3.2` with one change: a point that is Candidate only because PV plus the PCS
  discharge capability covers load (the battery-support branch, `dispatch_v3.py:298-300`) stays Candidate only if the
  battery's energy above the reserve in effect covers the load that PV does not, from that point until PV alone covers
  load with the 10 % headroom, with the same headroom. Otherwise the point is Indeterminate, naming the shortfall or
  the missing record. The PV-alone branch is unchanged. It is a new model version (the decision table's rule), so
  stored 3.2 revisions stay readable history and the worker's reconcile pass reassesses every default window.
- **Downstream.**
  - `4d`: `candidate_l` falls and `necessary_l` rises by the same litres (necessary is the month less Candidate); `diesel_l`
    and `unexplained_l` do not move.
  - `fuel-cost-1`: a POTENTIAL_FUEL_COST consequence is bounded over Candidate time, so new runs give a lower upper
    bound. Pinned consequences stay as history; they are never repriced in place.
  - Findings: candidate-running Findings re-derive from the 3.3 selections on the next pass, so episodes shrink or
    close. They are living outputs.
  - `claim_limit_read.SUPPORTED_MODELS` gains 3.3.
  - The 5c walkthrough world has no telemetry (D-DS4.1), so its `candidate_l` already reads "Not available yet" and
    does not move. The 13 Nov demo database and every telemetry world change once they are reassessed.
- **Why.** Review §3 ("the 330 L") and the 0M review's same-step finding: one class, a moment's power read as a night's
  energy. It is a different layer from the simulator, with served figures, stored revisions and a database job, so it
  is its own unit and runs in parallel.

## D-0K4.11 One figure per quantity, as a class (owner rule, 2026-11-21)

- **Ruling.** On every screen, in every served payload and in every spec, a quantity has one figure, computed by a
  model from simulated or real inputs and labelled by its source (SIMULATED, RECORDED, ...). A hand-entered design value
  is never shown, served or specified beside it, nor alone in its place: it becomes the model's figure or "Not available
  yet" naming the record that would fill it. Two figures appear together only when they set up an operator action or a
  reconciliation (plan against actual, the records against the factors, a model change v7 against v8 in a review
  packet). A model fault is fixed in the model. Every place is listed in `one-figure-change-list.md` with the unit that
  owns it. Packets for the owner show the model figure; a design value may appear only in a reconciliation table that
  says why the two differ, never as a comparison column.
- **Amends** D-0K2.13 (row 37 is settled: no design value beside a replay figure), D-0K2.12 and D-0K2.17 (row 42 is settled
  by D-0K4.9), D-0M.11 and D-0M.14 (the packet's "design value, unchanged" column is withdrawn for later packets; the
  0K2 and 0M packets stay as records). Supersedes owner-away row 37 option (a).
- **Why.** The owner's words: "two numbers are confusing if there is no action pending from the operators or doesn't
  show something to fix or reconcile ... it should stay loyal to the operating world".

## D-0K4.12 Until 0K4d: "Not available yet", with the mechanism

- **Ruling.** Until 0K4d's figures are merged, any spec or build that would show a figure for Kobo's stop-70 option
  (litres, value, battery use, dawn) shows "Not available yet", naming the record (the corrected replay), and shows the
  mechanism: the setting changes how long the generator runs after it has charged the battery, and the figure will come
  from a replay of the season under the setting. The same holds for reserve 25 (20 L), the huller (68 L) and Mto's
  5 L a day; KIS-BATT60's 150 L a month reads "Not available yet" until a Kisiwa battery replay exists (not in 0K4,
  queue Q7). After 0K4d the figures are the v8 study's, labelled SIMULATED, with the assumptions of D-0K4.7.
- **Why.** Owner's rule, fourth point; the replay's 85 L comes from a rule we know is wrong.

## D-0K4.13 Two fuel laws, one world: the product law and the world adopt v8 in 0K4f (owner to weigh in)

- **Ruling.** The product's fuel law (fuel balance, fuel-cost-2, 4d: `SFC x kWh` loaded plus the no-load rate over
  idle time only) and v8's curve (D-0K4.5) agree only at full load and at idle. While they differ, no simulated Site's
  world is made on v8, so no fuel balance meets a tank that burned by another law (it would show unexplained fuel the
  world did not have). The 5c walkthrough world stays as built (D-DS4.1, no telemetry). Queued unit **0K4f** (about 2
  units, after the 5c walkthrough): the product's fuel law reads the same curve (the no-load rate over every running
  hour, the slope `s` over energy), the Kobo template and DS2's telemetry writer adopt v8 and the D-0K4.4 to D-0K4.6
  properties, and the demo database is rebuilt. Owner-away row 56.
- **Why.** One law per quantity is the owner's rule for figures; applying it to the product's fuel law changes served
  money and states at Kisiwa and needs its own discovery review, which the walkthrough date does not allow. Keeping the
  world off v8 until then is the honest interim. **Owner to weigh in** if the world should move before the walkthrough.

## D-0K4.14 Calibration when Kobo's records arrive

- **Ruling.** On Kobo's recorded series (0K3's reader), the existing calibration rule (generator kWh within 5 %, starts
  within 10 %, SOC within 5 points, D-0K2.5) runs on v8 with Kobo's declared properties. Until then every v8 figure is
  SIMULATED and "CALIBRATED" means adapter fidelity (D-0K2.20).
- **Why.** Review §6 "What needs Kobo's real records"; W8: a replay on simulated data never stands in for the
  real-data checkpoint.

## D-0K4.15 Interim pack and mock: one pass, after 0K4d (0K4m)

- **Ruling.** The pack's manifest inputs, `derived-values.json` and the vNEXT fixtures are restated once, in 0K4m,
  from 0K4d's figures. No interim pass: nothing on the live product serves them, and two regenerations of the
  pack cost a unit for no screen.
- **Why.** Demo-critical scope (owner, 2026-11-05).

## D-0K4.16 Reserve breaches, starts and full charge are read from the replay steps

- **Ruling.** In `CaseOutcome` (0K4d): `reserve_breach_steps` = steps whose `soc_start_pct` is below the case's
  `reserve_soc_pct`; `max_starts_in_a_day` = the largest count of STOPPED/FAILED to STARTING/RUNNING transitions
  (0K2's start rule, D-0K2.23) in one local day; `full_charge_dates` = local dates on which any step's
  `soc_start_pct`, or the window's end SOC on its last date, is at least 100; `longest_days_without_full_charge` =
  the longest run of consecutive local dates of the window not in `full_charge_dates`. The model's reserve law keeps
  `reserve_breach_steps` at 0 unless the start state is already below the reserve; the packet says so beside it.
- **Why.** The admission rule reads only replay outputs (W2: nothing modelled in the study).

## D-0K4.17 Specs are W4 units with one combined handshake each

- **Ruling.** Each unit's spec and reviewer guide go through one combined handshake round (RULES §4, spec handshake
  6) before code. 0K4a and 0K4b share one handshake round because 0K4a assembles 0K4b's module.
- **Why.** Owner, 2026-11-19.

## D-0K4.18 The operator request

- **Ruling.** No operator data request file exists (the pack's design appendix §5 lists minimum pilot asks per
  vertical, a frozen design document). `operator-request.md` is created here: the general mini-grid asks by reference
  and Kobo's five items with what each settles and which assumed value it replaces.
- **Why.** Owner default 4.

## Decision queue (W3; defaults applied)

| # | Question | Default |
|---|---|---|
| Q1 | Should the 5c walkthrough world move to v8 first? | No: 0K4f after the walkthrough (D-0K4.13, row 56); owner to weigh in |
| Q2 | Load-following Sites | Stay on v7 until a load-following rule is specified; not demo scope |
| Q3 | High-load starts and quiet hours | Backlog (review §2 point 2); no Kobo setting asks for them yet |
| Q4 | A lower stop for night charging (owner default 5) | Backlog |
| Q5 | Maker's start limit and full-charge interval | 6 a day and 7 days, `GENERIC_DEFAULT`, until Kobo's sheets |
| Q6 | Battery warranty floor | Recorded in the operator request; shown as information only, not an admission part (owner's rule names four parts) |
| Q7 | KIS-BATT60's 150 L | "Not available yet" until a Kisiwa battery replay exists; not in 0K4 |
| Q8 | An interim pack and mock pass before 0K4d | No (D-0K4.15) |
