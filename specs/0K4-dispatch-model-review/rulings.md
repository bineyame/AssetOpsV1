# 0K4 rulings (D-0K4.1 to D-0K4.30)

Architect (Claude), 2026-11-21. Builds the 0K4 path the owner accepted the same day
(`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`: "Accept all (Recommended)", and the one-figure rule).
Review: `review-for-owner.md`. Unit specs: `specs/0K4a-dispatch-v8/`, `specs/0K4b-fuel-curve-taper/`,
`specs/0K4c-declared-season/`, `specs/0K4d-rerun-restate/`, `specs/0K4e-candidate-energy/`. Change list:
`one-figure-change-list.md`. Operator request: `operator-request.md`. Owner-level calls: owner-away rows 56 and 57. Handshake answers (rev 2 of
0K4a, 0K4b and 0K4e): D-0K4.19 to D-0K4.25.

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
  0.5475 L/kWh at a quarter load, 0.3825 at half and 0.30 at full (exact on the curve; corrected at the 0K4b review, L4). Labelled assumed until Kobo's fuel sheet arrives.
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
  `"<property key> <value> <unit> (<basis>)"` strings read from the run's frozen Foundation for the four properties of
  D-0K4.4 to D-0K4.6 and SFC, each with its basis and derivation (0K4d; amended by D-0K4.27). The template, the product world and DS2's telemetry writer adopt v8 and these properties in
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
  `reserve_soc_pct`; `max_starts_in_a_day` = the largest count of STOPPED to STARTING/RUNNING transitions (corrected by D-0K4.28)
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

## Handshake answers (rev 2 of 0K4a, 0K4b, 0K4e; 2026-11-21)

Architect (Claude), on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`). The questions
are in `handshake.md` (reviewer, R) and `handshake-I.md` (implementer, I) in each unit's folder. Where the two sides
ask the same thing, it is answered once. Every question is answered either by a D-ID below or by accepting its
default, as the table says. Owner-level call: row 57 (D-0K4.19).

| Unit | Question | Answer |
|---|---|---|
| 0K4b | I1 | D-0K4.19 (class) |
| 0K4b | R1 | D-0K4.21: F11 runs the contract's own conversion; P4 and guide check 2 reworded |
| 0K4b | R2 | D-0K4.20: F12 pins the constants (default accepted) |
| 0K4b | R3 = I2 | D-0K4.20: the run is unchanged, plus a trajectory comparison with and without `assumed_site` |
| 0K4b | R4 | default accepted (D-0K4.21) |
| 0K4b | R5 | D-0K4.21: inline parse in `backend/tests`, plus host test P5; no `sys.path` edit |
| 0K4b | R6 = I4 | D-0K4.21: local `_share_of_rating` |
| 0K4b | I3 | defaults accepted, except the third point (superseded by R5) |
| 0K4a | I5 | D-0K4.19 (class) |
| 0K4a | R1 = I1 | default accepted (D-0K4.22): `host/tests/kobo.py` added to Files |
| 0K4a | R2 = I2 | D-0K4.22: no `ValueError`; `below_minimum` tightened; S10 |
| 0K4a | R3 | D-0K4.22: N3 restated as three assertions |
| 0K4a | R4 | D-0K4.22: N5's reader takes the model's whole `C` |
| 0K4a | R5 | D-0K4.20: N12 pins the v8 digest |
| 0K4a | R6 | D-0K4.22: view-bound rule kept, note added, N13 |
| 0K4a | I3 | D-0K4.20: one digest helper, owned by 0K4a |
| 0K4a | I4 | default accepted (D-0K4.22) |
| 0K4a | I6 | default accepted (D-0K4.22) |
| 0K4e | I3 | D-0K4.19 (class), applied by D-0K4.24 |
| 0K4e | R1 = I1 | default accepted (D-0K4.23): `energy_to_cover(t)` |
| 0K4e | R2 | D-0K4.23: E5b redesigned (the reviewer's case cannot fail), plant P10 |
| 0K4e | R3 = I6(d) | default accepted (D-0K4.23): role coverage stays per instant; readiness queued (Q10) |
| 0K4e | R4 = I5 | D-0K4.23: I5's `CaseRunner` world, in R4's run-owned database |
| 0K4e | R5 = I4 | D-0K4.23: a memoised per-slot recurrence (covers both) |
| 0K4e | I2 | D-0K4.23: `_num`, applied to the stored figures |
| 0K4e | I6 (a)-(c) | D-0K4.23: (a) and (b) as proposed; (c) the version token is corrected |

## D-0K4.19 New served text is composed, never added to the hand-built baseline (class; owner-away row 57)

- **Question.** 0K4b I1, 0K4a I5 and 0K4e I3 all report the same thing. The units add served English, which the SC-1
  ratchet reports as `HAND_BUILT_NEW`: four Foundation property names, three profile need statements, v8's profile
  statement and its restated fuel-tank statement, and four dispatch reason and missing texts. The implementer
  proposed a ruling naming these strings for `statement-handbuilt-baseline.json` under D-SC1.34's exception.
- **Ruling: no.** D-SC1.34's exception stays unused ("none is foreseen"). No 0K4 unit adds a fingerprint to the
  hand-built baseline or an entry to `statement-handbuilt-allow.json`. Each new string goes by its kind:
  1. **Served words** become SC-1 statements or vocabulary entries (D-SC1.28). They are rendered by the read that
     serves them.
  2. **A new string that joins a legacy family served through one field.** The field's type widens to
     `str | Message`. The family's serving read renders the field through one helper, `served_text(value) -> str` in
     the new module `backend/assetops_backend/served_text.py`: a `str` passes through unchanged, and a `Message` is
     rendered by `i18n.render` for the request's locale. The legacy strings stay as baselined debt, and nothing new
     joins them. Two families are touched:
     - Foundation property names: `PropertyDefinition.display_name`, served by `sites_api.py`. This is 0K4b's.
     - Model-profile and supported-state statements: `ModelProfile.statement` and `SupportedState.statement`,
       served by `simulator_lab_api.run_profile_summary`. 0K4b creates the need statements and 0K4a adds the seam.
  3. **Outcome text that a later reader parses back.** Dispatch segment `reasons` and `missing` are read back by
     `plain.py`, `finding_read.py` and `claim_limit_read.py`. They are not extended. The new outcome is stored as
     codes and figures in its own payload field, and each reader that explains it renders an SC-1 statement from
     those facts (D-0K4.24).
  4. **Text no person reads** becomes a code, or its exception class goes to `schema.UNSERVED` through the unit's
     spec (D-SC1.34). No such string arises in 0K4.
  5. **A baselined string whose only change is the version code it names** may be edited. This is a fingerprint swap,
     not new English: the old fingerprint is pruned, its replacement takes its place, and the count does not change.
     The packet lists each swap with its old and new fingerprint, and the reviewer checks that the diff is the
     version token only. 0K4e has one swap (D-0K4.23, I6 (c)).
  6. **Simulator texts.** The SC-1 scan does not read `simulator/` (`PKG = backend/assetops_backend`), so simulator
     refusal and note texts keep the package's existing form. Widening the scan would be a guard change, which the
     delegation holds for the owner.
- **Cost per unit.** 0K4b +0.5: the vocabulary `foundation_property`, the statements `foundation.property_name` and
  `model_profile.need`, their cases, `served_text.py` and the `sites_api` seam. 0K4a +0.25: the statements
  `model_profile.description` and `model_profile.state`, their cases and the lab seam. 0K4e +0.75: the structured
  `energy_cover` field, two statements, two vocabularies, their cases, and the `plain.py` and `finding_read.py`
  readers. +1.5 in all.
- **Checked.** Every statement and vocabulary literal named in the three specs was loaded in a scratch copy of the
  `i18n` package and rendered from the specs' facts. Each one loads: no `LITERAL_DIGIT`, no `LITERAL_NUMBER_WORD`, no
  `EVIDENCE_UNSHOWN`.
- **Why.** The owner's rule of 2026-11-21 (`owner/owner-text-composition-clean-2026-11-21.md`) is that product text
  is composed cleanly, "not brittle hard coding and if else mess". SC-1a baselined only text that was already
  merged, as debt to pay down. Adding new English to that debt is what the rule forbids. A reason string that a
  second module parses back by its prefix (dispatch `missing`) is the brittle form itself, so extending it is
  refused. One typed seam per family is the declared migration point, not a branch per string. Each family's whole
  migration is queued (Q9), and that migration deletes the `str` branch.
- **Not accepted:**
  - Rendering at import into a `str`: that binds the reference locale into a constant, against D-I18N.1's
    render-at-read.
  - Moving the whole property-name family now: two existing names hold a digit and a number word ("PV rated power at
    1000 W/m2", "PCS one-way conversion efficiency") and would need rewording the owner can see.
  - New labels in `dispatch_v3.LABELS`: each would be a per-entry fingerprint (D-SC1.37), and a reader would still
    parse them.
- **Reverse by:** naming the strings in the baseline per D-SC1.34 (the implementer's proposal) and dropping the seams.

## D-0K4.20 v8 is pinned against silent change, and one trajectory digest helper serves both pins

- **0K4b R2.** F12 asserts the module's constants as literals: `DIESEL_ENERGY_KWH_PER_L == Fraction(10)`,
  `MIN_SFC_L_PER_KWH == Fraction(1, 10)` and `TAPER_FLOOR_SHARE == Fraction(1, 20)`. The module docstring says:
  "these are `mini-grid` v8's physics: changing one is a new model version, never an edit".
- **0K4a I3.** No kernel trajectory digest helper exists. 0K4a commit 1 adds `host/tests/trajectory_digest.py` with
  `trajectory_digest(result) -> str`. It returns the sha256 hex of a canonical UTF-8 text with one line per
  boundary. Each line holds the offset in minutes, then sorted `key=value` pairs for stocks, interval measurements and
  discrete states. Exact values are written as `str(Fraction(v))` and states as their code. N9 pins, as a literal,
  the v7 8-day season digest computed on `main` at pre-flight (`base_run(8)` with the default `site_edit=season_site`,
  and `season_inputs(run, 8)`).
- **0K4a R5.** N12 pins, as a literal, the v8 8-day season digest (`base_run(8, version=8, site_edit=site)` and
  `season_inputs(run, 8)`), and the packet prints it. The test docstring says: "a change here is a new model version,
  never an edit".
- **0K4b R3 = I2.** The pre-flight runs `host/tests/test_registered_kobo_execution.py` unchanged and records it green.
  It then compares a v7 `kobo_draft(...)` run with and without `site_edit=assumed_site`, boundary by boundary:
  stocks, interval measurements and discrete states. The packet says equal, or which values differ and why (whether
  the frozen Foundation carries every Site property or only the model's needs). No existing file is edited. 0K4b does
  not use the helper: 0K4b merges first, and the helper is 0K4a's.
- **Why.** Simulator-version reproducibility. 0K4d's SIMULATED litres and admission results come from v8. A later
  edit to the module or to `_resolve_cycle` must fail a test rather than move those figures under the same identity.

## D-0K4.21 0K4b's test-path answers

- **R1.** A new test, F11, runs the frozen-record path: `value, unit, _ = frozen_canonical_value(3.3, "L/h")`
  (`contracts/assetops_contracts/execution_contract.py:1743`), then `rate = normalize_authored_float(value)`. It
  asserts `unit == "L/min"` and `rate == Fraction(11, 200)`, and that a 5-minute STARTING step burns exactly
  `Fraction(11, 40)` L (0.275). The /60 is never written by hand in a test. Plant P4 becomes "`fuel_litres`
  multiplies the rate by `minutes / 60` (reads the L/min input as L/h)", and it must fail F4 and F11. Guide check 2
  becomes "the only 60 in the module is the slope's `60 x no_load / rated`".
- **R4.** In the packet's F3 table, the 0 % row's litres-per-kWh cell reads "not defined (no output)", and its
  litres-an-hour cell reads 3.3. The table is headed "assumed (GENERIC_DEFAULT)", with no design value beside it.
- **R5.** P1-P3 render the Kobo template into a site document (`render_site_document(site_from_template(...))`, as
  `host/tests/kobo.py:kobo_site` does). They append the six rows inline, as the test's own literal (W2), and parse
  with `sites/foundation_parsing.py:parse_foundation_content`. A new host test, `host/tests/test_0k4b_kobo_assumed.py`
  (P5), checks that `assumed_site` writes exactly those six rows on their components and raises `KeyError` on a key
  already present. `backend/tests` gets no `sys.path` edit (this supersedes I3's third point).
- **R6 = I4.** `generator_curve.py` gets a local `_share_of_rating(v)`. It refuses a value outside `[0, 100]` with
  `PhysicallyUnacceptable("a minimum generator load of {v} % is not a share of the generator's rating")`. F10
  asserts that text. `packs/minigrid.py` stays untouched. This is simulator text, outside the scan (D-0K4.19 item 6).
- **I3.** Accepted: `_need` is at `runs/profiles.py:953`, and the module also imports `dataclasses` and
  `kernel.model.StateHandler`.

## D-0K4.22 0K4a's dispatch answers

- **R1 = I1.** Commit 3 adds the backend `MINI_GRID_V8_MODEL` to `kobo_draft`'s profile tuple
  (`host/tests/kobo.py:131-141`), as a fixture edit listed in §0 Files. v7 callers do not change.
- **R2 = I2.** `cycle_charge_split` raises no `ValueError` for `M > R`. `g` is always capped by `R`, so that case is
  legal everywhere. The function sets `below_minimum = D + C < M and D + C < R`, which is true only when the `D + C`
  cap binds below the minimum. S8 enumerates every combination, `M > R` included. A new case, S10 (`D 5, A 15, R 0,
  C 2, M 12, dis 0`), expects PV `5, 2, 8`, generator `0, 0`, battery `0, 0`, unserved `0`, and below minimum "no".
  S9 checks a float argument and a negative one. Step 5's rerun with `generator_kw = 0` therefore never notes "below
  minimum load": the fuel note names the cause.
- **R3.** N3 makes three assertions:
  - (a) precondition: v7's 05:00 local SOC on day 1 is below 35;
  - (b) let `s0` be v8's SOC at the boundary that ends night 1's STARTING step; every boundary from that one to 05:00
    has SOC at least `s0`;
  - (c) v8's 05:00 SOC is above v7's.

  The packet shows both 05:00 readings as the model-change reconciliation.
- **R4.** N5's reader computes `C = min(A + 40 - D, 30 x f(soc), (200 - stored) / (95/100 x 5/60))` from its own SOC,
  with `f(soc) = 1` at or below 95 and `max(1/20, (100 - soc) / 5)` above it. The exact `1` kWh assertion applies on
  every RUNNING step where `D + C - A < 12 <= D + C`. The "at least 1 kWh unless the step notes below minimum load"
  assertion stays. Precondition: at least one exact step exists.
- **R6.** The view-bound rule is kept: it is v7's, and the physics need no change. When a RUNNING step's view asked
  for charge (`requested <= 0`) but a segment has `D > A + R`, `limited` gains v7's "differed from the view at T" note
  (the same text as `mini_grid.py:849-851`). A new test, N13, runs `run8(1)` from start SOC 34, with res 25 and
  clinic 10 kW all night and the mill at 40 kW over offsets `[62, 90)`, the windows cut as N4 cuts them. On the step
  `[60, 65)`: unserved energy is exactly `35 x 3/60 = 7/4` kWh, the battery AC energy is at most 0, and the step's
  `limited` notes hold the "differed from the view" text. On each step of `[65, 90)`, N4's per-step figures hold.
- **I4.** N11 builds `ForwardReplayRequest(BASELINE, observed.pv_available_kw, observed.loads,
  start_state(observed), ...)` as `runs/replay_study.py:516` does, with `observed = kobo_season.observed_series(<N1's
  trajectory>, 576)`. It asserts that the request is not refused, the result has 576 steps, and `generator_kwh` is
  within 1 % of the site run's. v8 is not added to T1, whose hand anchors are v7's linear law. `REPLAY_MODELS`'
  comment cites N11 for v8.
- **I6.** Build by the content §2.4 describes, using the line anchors I6 lists for `main`. v8's notes are
  `(CURVE_FUEL_NOTE,)` alone, replacing `LINEAR_FUEL_NOTE`. v7's "RUNNING with nothing to absorb" note stays where v7
  sets it.

## D-0K4.23 0K4e's dispatch-3.3 answers

- **R1 = I1.** The walk takes one argument, `energy_to_cover(t)`, and re-reads the feeders at each slot
  (`self.assets(LOAD, s)`), so a feeder bound later in the night counts from its binding on. The decision table's 3.3
  row says so.
- **R5 = I4.** A memoised per-slot recurrence on `_Index`, built once per `assess()` and keyed by slot instant:
  - `cover(s) = END(read_range.end)` when `s > read_range.end`;
  - `cover(s) = GAP(role, problem, s)` when a load or PV lookup at `s` fails after the interval fallback;
  - `cover(s) = REACHED` when `pv(s) >= load(s) x (1 + CAPABILITY_HEADROOM)`;
  - otherwise `need(s) = (load(s) - pv(s)) x 5/60 + need(s + 5 min)`, where `GAP` and `END` propagate unchanged.

  It is computed iteratively: walk forward until a memo hit or a terminal, then fill the memo backward. Arithmetic is
  exact `Fraction`. Each slot's lookups run once per assessment, however many points reach the branch. The figures
  equal §2.2's walk, so E1-E6 decide it. The packet reports E9's `assess()` wall time on 3.2 and on 3.3. A ratio
  above 2x is a mid-build question.
- **R2.** The reviewer's E5b cannot fail. `lookup_asset` reads a reading that ends exactly at `s` before any
  fallback, so the fallback's inequality matters only at a slot that starts a mean's interval with no reading ending
  at it. E5b is redesigned to hit that slot:
  - the point at 18:00, with E2's SOC, reserve, capacity and efficiency;
  - load as 5-minute means ending 18:00, 18:05 and 18:10 (10 kW), no load reading ending 18:15, and one 15-minute load
    mean over `(18:15, 18:30]` of 20 kW;
  - PV 0 at every slot to 18:30, and 30 kW from 18:35.

  Expected, under the spec's convention: `energy_cover` state `GAP`, input `feeder_demand`, problem `MISSING`, at
  18:15. Plant P10 swaps the fallback to `interval_start <= s < interval_end`. It then reads 20 kW at 18:15, reaches
  cover at 18:35 with need `55/6` kWh, and fails E5b. E5 (constant values) stays.
- **R3 = I6(d).** Role coverage stays per instant, and no role is added. D-0K4.24 stores the energy-cover outcomes
  outside `missing`, so `segment_roles` never sees them. E10 asserts that a 3.3 segment Indeterminate for `SHORT`,
  `GAP` or `NOT_CONFIGURED`, whose own instant inputs are whole, reads every role COVERED. The decision table's 3.3
  row says that an energy-cover Indeterminate is a limit of the rule, not an input-role gap. Having readiness name it
  is queued (Q10).
- **R4 = I5.** E9-E11 run on the `CaseRunner` world (`backend/tests/test_4d_litre_split_postgres.py:17`) plus one
  planted night of battery-support points. Precondition, on 3.2: at least one Candidate segment reaches the
  battery-support branch, so E9's "at most" is proved on a set that is not empty. The database is run-owned, named
  per `backend/TESTING.md` (`..._pt<run>_<tag>_test`) and reached through `tools/heavy-slot.sh --db`; the packet
  names it. Pre-flight item 3's counts cover that fixture's days and are labelled so, not as "1-31 Oct".
- **I2.** Use the module's `_num`, with no new formatter. The stored figures read `"95"`, `"120"` and `"133"`.
- **I6.**
  - (a) §5 and the packet state that a verification whose baseline days mix model versions refuses
    (`VERIFICATION_MODEL_NOT_COMPARABLE`) from deploy until the reconcile pass ends. The coordinator runs the pass
    straight after deploy.
  - (b) No code change: the S3 lineage and performance reads follow `MODEL_VERSION`. The sweep classes them as *pins
    a version (follows the constant)*.
  - (c) `structure/rows_mini_grid.py:62-67` names the analytic behind three factor sources, and after 3.3 the token
    `dispatch-3.2` there is false. The two code-form sources (`necessary_l`, `candidate_l`; not prose, so not
    fingerprinted) are edited to `dispatch-3.3`. The prose source of `unexplained_l` ("fuel balance (FUEL_DELIVERY,
    TANK_DIP) minus dispatch-3.2") is edited the same way as a fingerprint swap (D-0K4.19 item 5). The sweep classes
    all three as *pins a version*.

## D-0K4.24 0K4e stores the energy-cover outcome as facts and renders it by statement

- **Ruling.** The new branch adds no English to `reasons` or `missing`. Each evaluated point that reaches the
  battery-support test carries one `energy_cover` entry. It holds codes and exact decimal strings only:
  `{"at", "state", "held_kwh", "need_kwh", "input", "problem", "gap_at", "range_end", "controls"}`, where `state` is
  one of `COVERED`, `SHORT`, `GAP`, `NOT_REACHED` or `NOT_CONFIGURED`, and the fields a state does not use are
  `null` (`controls` is `[]`). A segment's payload gains `"energy_cover"`: its points' entries, deduplicated and
  sorted by `at`. The key is omitted when the list is empty, so a segment that never reaches the branch is
  byte-equal to 3.2's form (E8). A Candidate keeps 3.2's existing reason string, unchanged. Two readers explain the
  entries through the new statements in `i18n/statements/en/dispatch.py`:
  - `plain._segment`: a segment's reason is `dispatch.energy_cover` rendered for its lead entry. The order is
    `NOT_CONFIGURED`, `GAP`, `NOT_REACHED`, `SHORT`, `COVERED`, then the earliest `at`. This applies when the segment
    is Candidate with a `COVERED` entry, or Indeterminate with no legacy `missing` text and a non-`COVERED` entry.
    Otherwise the existing branches apply, because a record gap in the legacy texts wins.
  - `finding_read.portion_cause(missing, cover=())`: a `GAP` or `NOT_CONFIGURED` entry makes the portion
    `RECORD_GAP`. A `SHORT` or `NOT_REACHED` entry adds the fragment `dispatch.energy_cover_cause` to the `MODELLING`
    words.

  `claim_limit_read` and `stored_declaration` are unchanged, apart from `SUPPORTED_MODELS`.
- **Why.** This is D-0K4.19 item 3. The facts are stored once, and the words come from the catalogue at read time, so
  no reader parses English. If `plain.py` and `finding_read.py` did not learn the field, a 3.3 Indeterminate segment
  would read "too close to decide" or "does not say why", which is false.
- **Reverse by:** dropping the field and the statements, and appending rev 1's texts to `missing` with D-0K4.19
  reversed.

## D-0K4.25 Sizes and lane order after the handshake (amends D-0K4.1)

| Unit | Rev 1 | Rev 2 | Why it moved |
|---|---|---|---|
| `0K4a` | 2.0 | 2.5 | +0.25 SC-1 statements and the lab seam (D-0K4.19); +0.25 N12, N13, S10 and the digest helper |
| `0K4b` | 1.5 | 2.0 | +0.5 SC-1 names, need statements and the `sites_api` seam (D-0K4.19); F11, F12 and P5 absorbed |
| `0K4c` | 1.0 | 1.0 | not in this round |
| `0K4d` | 1.5 | 1.5 | not in this round |
| `0K4e` | 2.0 | 2.75 | +0.75 structured `energy_cover`, two statements, two readers (D-0K4.24); E5b and the memo absorbed |
| `0K4m` | 0.75 | 0.75 | |

- **Total 10.5 units** (was 8.75).
- **Lane order, checked.**
  - Lane 2: 0K4b, then 0K4c.
  - Lane 1: 0K4a, then 0K4d. 0K4a's commits 1-2 come to 1.5 (the digest helper and S10 go in commit 1), and its
    SC-1 part goes in commit 3, because it uses 0K4b's `served_text.py`. That leaves 0K4b (2.0) finishing about 0.5
    after commits 1-2. Lane 1 fills the gap with
    0K4d's commit 1 (0.75; `main` only, stub-tested), then takes 0K4a's commit 3 once 0K4b is on `main`, then 0K4d's
    commits 2-3 once 0K4a and 0K4c are both merged.
  - The critical path is now about 4.0 units (was 3.5): 1.5 + 0.75 + 1.0 + 0.75, with no idle wait.
  - 0K4e is independent. It runs in a third slot as soon as one is free, or in lane 2 after 0K4c if only two lanes
    run. Its reassessment is a heavy database job, one at a time.
  - Shared files: 0K4b, 0K4e and 1a each append to `i18n/statements/en/vocabulary.py`, a trivial merge; the
    statement modules are separate files.
- **Ready to build:** 0K4b and 0K4e now. 0K4a now for commits 1-2, and commit 3 after 0K4b merges. Each still needs
  its reviewer to confirm that no question is open (RULES §4, handshake step 3).

## Handshake answers (rev 2 of 0K4c and 0K4d; 2026-11-21)

Architect (Claude), on the owner's delegation (`owner/owner-away-architect-stands-in-2026-11-21b.md`). The questions
are in each unit's `handshake.md` (branch `task/0K4cd-handshake`, `0aa2cb3fb`). Each is answered once, by a D-ID or by
accepting its default. Where the two units ask the same thing, the first row answers it and the second points to it.
Owner-level call: row 63 (D-0K4.27, Mto's assumed no-load rate).

| Unit | Question | Answer |
|---|---|---|
| 0K4c | R1 | D-0K4.26: S9 pins the v2 inputs digest (default accepted, in R2's canonical form); plant P8 |
| 0K4c | R2 | default accepted (D-0K4.26): one canonical digest form for S6, S9 and 0K4d's header |
| 0K4c | R3 | D-0K4.26: both, an own `yaml.safe_load` reader and the night literals; plus the `load_scale` case |
| 0K4c | I1 (blocks) | D-0K4.26: default accepted, with an ancestor check deciding the split; V0 in 0K4d commit 2 |
| 0K4c | I2 | default accepted (D-0K4.26); it now serves 0K4d's V0 and D-0K4.27's values |
| 0K4c | I3 | default accepted: `season_inputs(..., overcast=None)`; unknown season `ValueError` |
| 0K4c | I4 | default accepted: two 61-character rows (weather, Sundays) |
| 0K4d | R1 (blocks) | D-0K4.28: default accepted; V5 in-process with no flags against `main`'s recorded literals |
| 0K4d | R2 | D-0K4.29: every figure in §4.2 is classed, and each design value or dawn gate has its replacement |
| 0K4d | R3 | = 0K4c R1, plus default accepted (D-0K4.28): the `study.json` identity header |
| 0K4d | R4 | default accepted (D-0K4.28) |
| 0K4d | R5 | default accepted (D-0K4.28) |
| 0K4d | R6 | default accepted (D-0K4.28) |
| 0K4d | I1 | = 0K4c I1 for the order; default accepted (D-0K4.28): the pre-flight opens commit 2; Mto `--time-one` |
| 0K4d | I2 | D-0K4.28: `start_steps` unchanged; D-0K4.16's "/FAILED" corrected |
| 0K4d | I3 | default accepted (D-0K4.28): public `admission_measures`; AD7 with reserves 30 and 25 |
| 0K4d | I4 | D-0K4.27 (class): four Site strings, each with its basis and derivation; Mto 2.4 L/h by the generic rule |
| 0K4d | I5 | default accepted (D-0K4.28); the mixed-pair refusal is a code |
| 0K4d | I6 | D-0K4.28: anchors by text, and the figure definitions as proposed |

## D-0K4.26 0K4c's answers: one digest form, independent readers, and the split of S7 and S8

- **Digest form (R2, used by S6, S9 and 0K4d).** `inputs_digest(inputs)` lives in `host/tests/kobo_season.py`
  (0K4c). It is the sha256 hex of a UTF-8 text with one line per forcing, sorted, each holding every `ForcingInput`
  field in declaration order as `name=value` joined by `|` (numbers as `str(Fraction)`). Then come the initial values,
  one line each: `initial|<address>|<str(value)>|<unit>`, in the inputs' frozen order, not sorted (clarified at the 0K4c review, L2). The test recomputes it with its own loop, written beside the
  literal. A second digest covers `day_windows(d)` for d = 0 to 60 (v1), in the same line form. S6 pins both v1
  digests as literals. The packet calls this "v1 inputs unchanged".
- **S9 (R1).** `inputs_digest(season_inputs(base_run(61), 61, season="v2"))` equals a literal recorded in the
  pre-flight. It is a v7 base: inputs only, with no kernel run, so it does not need v8. Its docstring says "a change here is a new
  season, never an edit". Plant P8: `mill_on_v2` returns `True` from day 41 onwards (S4 stays green, S9 fails). 0K4d
  records the same digest in each `study.json` header (D-0K4.28).
- **Independent expected values (R3).** S3 and S4 read the day-type YAML files `kobo_season` loads with the test's
  own `yaml.safe_load` loop, never through `_series_events` or `day_windows`. S3 also asserts the night literals of
  day 9: res 3 kW to 21/8 and clinic 2 kW to 7/4. S3 adds a `load_scale=Fraction(1, 2)` case on day 9: res and clinic
  equal the file times 1/2 times 7/8, and the mill equals the file times 1/2 (0K4d's Mto path).
- **The split (I1).** At 0K4c's start, `git merge-base --is-ancestor <0K4a merge> main` decides it. If 0K4a is not
  on `main`, 0K4c builds S1-S6, S9 and S7's document half: `kobo_site(season_site_v2)` carries the three basis rows
  `GENERIC_DEFAULT` and the 20,000 L tank (P7 fails it). S7's frozen half and S8 become **V0** in 0K4d commit 2.
  V0 is a 1-day `base_run(1, version=8, site_edit=season_site_v2)` whose `frozen_world_inputs(run).initial_values`
  hold `model-need:generator-no-load-fuel-rate` `11/200`, `model-need:generator-minimum-load` `30` and
  `model-need:battery-charge-taper-start` `95` (I2), plus a 2-day v2 season on v8 that executes COMPLETED. If 0K4a is
  on `main`, 0K4c keeps S7 and S8 whole and V0 is dropped from 0K4d. The packet says which applied.
- **Why.** A season named v2 must mean one input set, as a model version does (D-0K4.20's class). An expected value
  read through the code under test proves nothing (W2). The split keeps lane 2 from waiting on lane 1.

## D-0K4.27 Every assumed value carries its basis and its derivation (class; owner-away row 63)

- **Ruling.** An assumed value is labelled as an assumption, with its basis code and one line saying where the
  number comes from. It is never a bare value with a code. The study's `assumptions` are four strings in this order:
  `generator-no-load-fuel-rate`, `generator-minimum-load`, `battery-charge-taper-start`, `specific-fuel-consumption`.
  Each reads `"<key> <value> <unit> (<label>, <BASIS>: <derivation>)"`, where the label is `assumed` or `declared`. The
  value and unit are the frozen `model_needs`' authored form. The basis and derivation come from a per-Site constant
  beside the value in its fixture: `ASSUMED_DERIVATION` in `host/tests/kobo_assumed.py` and `MTO_ASSUMED_DERIVATION`
  in `host/tests/mto.py`, both added in 0K4d commit 2. A key with no entry is `KeyError`, never a blank.
  - Kobo: no-load `3.3 L/h (assumed, GENERIC_DEFAULT: the owner's value of 2026-11-07 for a 40 kW set; the generic
    rule of about 0.08 L/h per kW of rating gives 3.2)`. Minimum load `30 % (assumed, GENERIC_DEFAULT: a typical
    diesel controller setting, until Kobo's controller settings)`. Taper start `95 % (assumed, GENERIC_DEFAULT: a
    lithium iron phosphate battery, until Kobo's battery sheet)`. SFC `0.3 L/kWh (assumed, TEMPLATE: the Kobo
    template's value, read as consumption at rated output, until Kobo's fuel sheet)`.
  - Mto: no-load `2.4 L/h (assumed, GENERIC_DEFAULT: the generic rule of 0.08 L/h per kW of rating x 30 kW; no owner
    value for Mto)`. Minimum load and taper start as Kobo's, with the same words. SFC `0.33 L/kWh (declared, MANIFEST:
    Mto's physical line, read as consumption at rated output)`.
  - The admission rule's two limits are assumed values too. The Kobo tool writes them in the JSON header as
    `admission_rule`, as two strings in the same form: `max-starts-per-day 6 per day (assumed, GENERIC_DEFAULT: a
    typical maker's limit, until Kobo's generator sheet)` and `full-charge-every-days 7 days (assumed,
    GENERIC_DEFAULT: lithium iron phosphate, until Kobo's battery sheet)`. The words live in the tool, never in
    `admission.py` (D-0K4.28, R6).
- **Mto's no-load value.** 2.4 L/h, by the stated generic rule. It is not scaled from Kobo's 3.3: that is the owner's
  rounded value for one set, not a per-kW rule, and scaling it (2.475) would claim a precision nobody declared. The
  two Sites' values differ by their stated bases, and each says why.
- **Amends** D-0K4.7: "the five properties" reads "the four properties of D-0K4.4 to D-0K4.6 and SFC". The admission
  limits travel separately. `HeadroomResult` does not change. The Mto JSON header carries `assumptions`.
- **Why.** The owner's one-figure rule: a figure stays loyal to the operating world, so a reader must see what each
  input stands on. "Assumed" plus a code says how weak a number is, but not where it came from. The handshake found
  the spec's "same rule as Kobo's" untrue, which is exactly the slip a derivation line exposes.

## D-0K4.28 0K4d's answers: reproducibility, identity, missing values, and the definitions

- **V5 (R1).** In commit 2's pre-flight, before the tool is edited, `main`'s `tools/kobo_replay_study.py --days 8`
  runs, and each case's `avoided_l` is recorded exactly. V5 calls the edited tool's `main([...])` in-process with no
  model or season flag and asserts those literals and the header `model=mini-grid/7 season=v1`. P7 fails both.
- **Identity (R3).** Each `study.json` header holds `git rev-parse HEAD`, the model id and version, the season, the
  season's `inputs_digest` (D-0K4.26) and each site run's `trajectory_digest` (0K4a's helper). The packet prints them,
  and the reviewer's reproduction quotes them.
- **Missing values (R4).** A v7 cell with no measure reads "not computed on v7". A study that is not calibrated prints
  `admission not available (<status>)`, and its MG-T cells read "Not available yet (replay not calibrated)". The cause
  column reads "model v7 to v8 and season v1 to v2 together (not separated)". No separating run is added.
- **Grep (R5) and SC-1 (R6).** Guide check 5 is the regex pair of R5's default, each hit listed with its class.
  `admission.py` and the `replay_study.py` additions raise only built-in exceptions and hold codes, never English. The
  packet records the statement-catalogue check (no `HAND_BUILT_NEW`), and both baseline files are untouched.
- **Order (I1).** Commit 1 has no pre-flight beyond B1-B13 green. Commit 2 opens by merging `main` (0K4a and 0K4c on
  it), then runs V5's literals, `--time-one` on both tools, and the caps. The Mto tool gains `--time-one` in
  D-0K2.24's form, with cap `max(25, ceil(2 x (site + 6 x replay) / 60))` minutes.
- **Start rule (I2).** `max_starts_in_a_day` reuses `start_steps(states, start.generator_state)` unchanged, grouped
  by each step's local start date. D-0K4.16's "STOPPED/FAILED" was a slip for "STOPPED" (0K2's B6: FAILED to RUNNING
  is not a start).
- **Measures (I3).** Public pure `admission_measures(p, local_times, first_previous)` in `replay_study.py` and its
  `__all__`. It reads `p.reserve_soc_pct`, and `_outcome` calls it. AD7's stubs: baseline reserve 30, case reserve 25,
  one step at SOC 27; the case counts 0 and the baseline 1.
- **Flags (I5).** Only (7, v1) and (8, v2) run. A mixed pair exits 2 with `STUDY_FLAGS_INVALID model=<v> season=<s>`
  on stderr. v8 uses `season_site_v2` and `mto_site_v2`, the reduced Mto run included. `dawn_class` takes the
  season's overcast function. `mto_base_run(days, *, inverter_limit_kw, version=7, site=mto_site)` and `mto_season(run,
  days, season="v1")`. Every line and header carries `model=` and `season=`; on (7, v1) no figure changes.
- **Definitions (I6).** Anchor by text. A month is `scaled_to_30_days` (window x 30 / 61). Starts is `added_starts`
  scaled the same way, with `max_starts_in_a_day` in the admission cell. Stop 70 is `stop-70-reserve-30` and reserve 25
  is `stop-90-reserve-25`. Dawn margin is `worst - 35`. Huller is `mto-huller` `extra_fuel_l` x 30 / 61. Reduced
  inverter is `extra_fuel_l_per_day`.
- **Why.** Each figure going to the option card must be reproducible by its recorded command and identity, and must
  say "not available" rather than show 0. Every definition is fixed before the run, so no figure picks its own.

## D-0K4.29 The MG-T restatement as a class: every figure in §4.2 is one of four kinds

- **Ruling.** After 0K4d, each number in `domain-and-decision-models.md` §4.2's Kobo option text (from the `F(π)`
  block to the vectors line) is one of four kinds. Anything else is removed:
  1. a declared setting or record fact (reserve 30 and 25, start 35 %, stop 90 and 70, 60 kW PV on 50 kW AC, the
     error-mode thresholds, the proposed grid);
  2. a v8 study figure, labelled SIMULATED with its definition (D-0K4.28);
  3. "Not available yet (<record or unit>)";
  4. a rule in `runs/admission.py`, or information beside it.
  The packet lists every numeral of the restated text with its kind. The reviewer checks the list against the text.
- **The places (R2).**
  - The `dawn_ok(π) ... → bound` line becomes `admitted(π) = admit(baseline, π)  → runs/admission.py (four parts)`
    and `dawn(π) = min_d SOC_π(d, 05:00) − 35 → information, never a bound`.
  - "Design values:" before the table becomes "Figures from the v8 study (SIMULATED, MODELLED; assumptions as listed
    in the study):".
  - The table's "Bound result" column carries "admitted" or "not admitted (<first failing part>)". The dawn column is
    headed "Dawn (information)". Both rows' Value cells read "Not available yet (`6c` values it)"; "REJECTED" goes.
  - Stop 70's cell loses "of the 330 candidate L (120 L of candidate running remain needed)": candidate litres are
    another quantity. A line under the table reads "Kobo's candidate running litres: Not available yet (dispatch-3.3
    on Kobo's October telemetry; 0K4e, 4d)". The Calibration paragraph's "The 120 L residual" becomes "The residual
    (candidate litres no setting avoids)".
  - "lowest charge 30% ≥ warranty floor 10%" becomes the study's `min_soc_pct`, SIMULATED, with "warranty floor: Not
    available yet (Kobo's battery sheet)" as information (Q6). "wear costed 12.00" and the formula
    `(262.50 − 12.00) × 12 − 90.00 = 2,916.00` go. Wear and value read "Not available yet (`6c`)".
  - "Choose the highest value that passes every hard bound with the worst replayed day at least 2 points above the dawn
    limit" becomes "`6c` chooses among the settings `runs/admission.py` admits; the dawn margin is shown and never
    gates". The 10 % tie rule stays as `6c`'s.
  - "Design values as calibration-spike inputs" becomes four of the five inputs as the v8 studies' figures (stop 70 and
    reserve 25 from Kobo; the huller and the reduced inverter from Mto), SIMULATED, with the assumptions of
    D-0K4.27. KIS-BATT60's 150 L and its 195.00 read "Not available yet (a Kisiwa battery replay; queue Q7)".
  - "Minimum sample: 61 days for the dawn bound (…rule of three…)" becomes "the dawn information is read over the
    study's 61 days; ≥ 14 days for the litres". With no dawn bound, the rule-of-three claim has nothing to bound.
  - "Sensitivity / break-even" (2,286.00, 2,166.00, 15.6 L/month, 1.70/kWh) reads "Not available yet (`6c`)".
  - Vectors: MG-T1 and MG-T2 carry the study's litres, the admission result and the dawn information. MG-T2's value
    reads "Not available yet (`6c`)". MG-T3 reads "Not available yet (`6c`)", and MG-T4 is unchanged.
  - Each `<!--fig:...-->` anchor on a removed figure goes with it. `check_manifest.py`'s output goes in the packet,
    and the manifest is 0K4m's.
- **Why.** The owner's rule: no design value beside the model's figure, and the dawn margin is information (owner
  default 1). Listing the places one by one leaves the next one unfound. A rule of four kinds, checked numeral by
  numeral, finds every place (W6).

## D-0K4.30 Sizes and lane order after the 0K4c and 0K4d handshake (amends D-0K4.25)

| Unit | Rev 1 | Rev 2 | Why it moved |
|---|---|---|---|
| `0K4c` | 1.0 | 1.0 | +0.1 S9, the canonical digest and R3's readers; −0.1 S7's frozen half and S8 to 0K4d V0 |
| `0K4d` | 1.5 | 2.25 | commit 1 0.75 (unchanged; `admission_measures` absorbed); commit 2 0.5 to 1.0 (V0, Mto `--time-one`, flag pairs, V5 literals, identity header, derivations); commit 3 0.25 to 0.5 (the classed restatement, R4's cells) |

- **Total 11.25 units** (was 10.5). The critical path is about 4.75 units (was 4.0), all on lane 1: 0K4a commits 1-2
  (1.5), 0K4d commit 1 (0.75), 0K4a commit 3 (1.0), 0K4d commits 2-3 (1.5).
- **Lane order, confirmed.**
  - Lane 2: 0K4b (2.0), then 0K4c (1.0), done at about 3.0.
  - Lane 1: 0K4a commits 1-2, then 0K4d commit 1, which needs only `main` and can start now. Next, 0K4a commit 3
    once 0K4b is on `main` (about 2.0; lane 1 reaches it at 2.25). Then 0K4d commits 2-3, once 0K4a and 0K4c are both
    on `main` (about 3.0 and 3.25; lane 1 reaches it at 3.25). No idle wait.
- **Ready to build:** 0K4d commit 1 now, and 0K4c once 0K4b merges. Each still needs its reviewer to confirm that no
  question is open (RULES §4, handshake step 3).

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
| Q9 | When do the three legacy text families move to SC-1 whole (Foundation property names, of which two need rewording; model-profile and supported-state statements; dispatch segment texts with their readers)? | One queued unit per family after the walkthrough; each deletes its `served_text` branch or its parsing reader (D-0K4.19) |
| Q10 | Should readiness (`stored_declaration`, AP-1) name an energy-cover Indeterminate? | Not in 0K4e; queued. The `energy_cover` field makes it a read-only change (D-0K4.23) |
