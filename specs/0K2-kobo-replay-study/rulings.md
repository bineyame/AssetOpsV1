# 0K2 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0K2.1 to D-0K2.16 are applied by `spec.md` rev 1 (D-0K2.16 added with the 0M spec, before the handshake);
D-0K2.17 to D-0K2.29 (handshake round 1) by rev 2. Checked against `main` (`a53a77a2e`) by running the kernel on an
8- and a 14-day season through `HostForwardReplay`. Owner-level calls are logged in
`specs/OWNER-AWAY/decisions-2026-11-21.md` rows 37 (held for the owner), 38 and 42 (owner to weigh in).

## D-0K2.1 "The simulated series" is a declared season fixture; a reader from accepted readings is queued (0K3)

- **Ruling.** 0K2 proves the study on a 61-day Kobo season declared in `host/tests/kobo_season.py` and run on the
  kernel as the site. The product-side study takes a neutral `ObservedSeries`; reading that series from accepted
  readings (`EvidenceQuery` over `DISPATCH_ROLES`, the cohort, the binding from feeder asset to load component) is a
  queued unit, `0K3` (about 2 units), pulled when DS2's writer gives the world 5-minute telemetry (D-DS4.1) or a
  pilot sends an EMS export, and before `6c` runs on records. The season never enters a database or the world: it
  lives in the spike's tests and its tool's evidence file only, as D-DS4.1 requires of world telemetry. This amends 0K1 spec §7's list ("reading series from product
  readings (all 0K2)").
- **Why.** No Kobo series longer than a day exists in any store: DS3 loads two Kobo days (`specs/DS3-bulk-loader/
  spec.md` §3), and DS4 rules that world telemetry comes only from DS2's writer, none this fortnight (D-DS4.1,
  owner-away row 33). A reader
  built now could only be tested on rows its own test invents. The seam the reader will feed (`ObservedSeries`) is
  fixed here, so 0K3 adds a producer and changes no consumer.

## D-0K2.2 The season: shipped day types, one declared calendar, one continuous site run

- **Ruling.** 61 local days from 1 Sep 2026 00:00 Africa/Addis_Ababa; each day night (00-06, `kobo-night-early`),
  day (06-18, `kobo-steady-day` or `kobo-daytime-overcast`), dusk (18-20, `kobo-mini-grid-evening`'s 18-20 window)
  and late evening (20-24, `NIGHT_WINDOWS["late"]`); overcast when `day_index % 4 == 3` (15 of 61); start SOC 48%
  (`kobo-night-early`'s, the measured handover), STOPPED; tank 20,000 L holding 15,000 L; mini-grid v7 at 5 minutes.
- **Why.** Every value is a shipped Kobo value already labelled example data (DD1a1-R2); only the calendar is new,
  and it is stated as a fixture choice, not a weather record. The figures are outputs (W1): nothing was tuned to a
  design value. A large tank keeps the tank bound out of every litre difference (D-0K1.14), since Kobo's real
  deliveries are not part of this world. One scenario document cannot hold a season (`document_bounds.py` refuses
  "more than 4000 nodes" at 8 days, probed), so the fixture writes the season's frozen forcings directly, by code
  that shares nothing with the adapter (W2).

## D-0K2.3 The fixture publishes at a stated resolution

- **Ruling.** PV and load kW to 0.01, generator kWh per step to 0.001, SOC to 0.1 point, fuel to 0.1 L, half-even.
- **Why.** Published readings are decimals; a replay of the kernel's exact values would make the calibration check
  vacuous. Probed on `main`, 14 days: generator energy 7.5e-5 relative, starts equal, SOC MAE 0.02 points. T1 asserts
  the quantization changed at least one value.

## D-0K2.4 Every replay covers the whole window in one call

- **Ruling.** The baseline and each setting are one port call over the whole window; never a call per day.
- **Why.** The dawn bound depends on the charge carried from the evening before, and a lower stop threshold changes
  that charge; a per-day replay restarted from the observed (baseline) state would reset it daily. The 8-day probe
  confirms state carries for days after a change. Cost: about 2.5 ms a step, 44 s per 61-day replay (an
  estimate; measured before the run, D-0K2.24).

## D-0K2.5 The calibration rule, exactly

- **Ruling.** On admissible days (every step with observed generator energy, state and SOC): generator energy
  `|rep − obs| ≤ 5% × obs`; starts `|rep − obs| ≤ 10% × obs` by one start rule applied to both sides; SOC mean
  absolute error `≤ 5` points over admissible steps. Any failure is `NOT_CALIBRATED`; nothing else is replayed.
- **Why.** Design §4.2's tolerances, made exact and relative to the observed side. One start rule (a step in
  STARTING or RUNNING after a STOPPED one) on both sides compares like with like; the projection's own transition
  count is not used for the comparison.

## D-0K2.6 An input gap is the port's refusal; no fill rule

- **Ruling.** D-0K1.5 stands: a `None` in the PV or load series reaches the caller as the port's `INPUT_GAP`. A gap in
  the observed outputs only makes that day inadmissible. Clipped days are counted and kept (D-0K1.4).
- **Why.** The season has no gaps, so a fill rule would be untested here. The design's 20-minute rule belongs to real
  series (0K3 or the first pilot); on a 61-day real window one gap refuses the study, which is the honest answer until
  a fill rule is ruled with its own test.

## D-0K2.7 Whole local days of 288 steps; no clock change

- **Ruling.** The window starts at a local midnight and every local day holds 288 steps, else
  `STUDY_WINDOW_INVALID`.
- **Why.** Dawn and months are local; every demonstration Site is in an East African zone without a clock change. A
  zone with one needs its own day rule and test.

## D-0K2.8 The dawn bound: absolute, local, on every case; a verdict only on 61 days

- **Ruling.** The SOC at the step starting at 05:00 local, each local day; below 35% counts; `FAIL` if any, `PASS` if
  none, `NOT_CLAIMED` under 61 replayed days. Reported for every case, the baseline (no action) included. The time
  and limit come from the caller (`StudyFrame`), since MG5 is not yet a record (design §4.7, step 6).
- **Why.** Design §4.2: `dawn_ok(π) = ∀ d: SOC_π(d, 05:00) ≥ 35%`, minimum sample 61 days (rule of three). The 8-day
  probe already shows the baseline below 35% at dawn, so the bound may fail under no action too; hiding that would
  misstate the model. The cause (the dispatch law with the limit on the effective start) and what a verdict means when
  the baseline fails are ruled in D-0K2.17. Whether an option is admissible relative to no action is the
  evaluator's (`6c`), and its spec takes it to the owner.

## D-0K2.9 The grid and its case ids

- **Ruling.** Stop {90, 85, 80, 75, 70, 65, 60} × reserve {30, 25}, stop-major, 14 settings, ids
  `stop-<s>-reserve-<r>`; the baseline is the replay with no setting. The (90, 30) setting must reproduce the
  baseline exactly (T2).
- **Why.** Design §4.2's candidate grid. Passing the baseline values as settings exercises the setting path against
  the baseline path on the same series: any distortion the adapter added would show.

## D-0K2.10 Litres from the tank stock; a tank bound is refused

- **Ruling.** A case's litres are the projection's `fuel_burned_l`; avoided litres by month are sums of per-step stock
  differences between the baseline and the case. A replay whose tank reaches 0 is `TANK_BOUND_MET`.
- **Why.** No law is re-implemented (D-0K1.6). Declared causes sit on both runs and cancel in each difference; an
  empty tank stops the generator, so the difference would no longer be the setting's alone.

## D-0K2.11 Battery throughput is discharge at the stock

- **Ruling.** `Σ max(0, SOC drop) × capacity / 100`, capacity from the Site's declared battery energy capacity.
- **Why.** The projection carries SOC, not battery power, and 0K1's types do not change. The design's 150 kWh is the
  added throughput a month that its wear cost is priced on (0.08 a kWh), not a capacity; the capacity is the template's
  200 kWh (D-0K2.21). Discharge throughput is the usual warranty measure. PCS losses are not in it; the packet
  says so beside the figure.

## D-0K2.12 No money in the spike

- **Amended 2026-11-21 by D-0K4.11** (owner rule, one figure per quantity): row 37 is settled; a figure carried into
  the manifest is the v8 study's (0K4d, 0K4m), never a design value beside it.

- **Ruling.** The study returns litres, kWh, starts, steps and SOC. Litres × price, wear cost, one-off and the
  12-month value are the evaluator's (`6c`, design §4.1). The CANDIDATE share of avoided litres is `avoided_l_on`,
  with `6c` supplying dispatch-3.2's offsets. This amends 0K1 spec §7 ("litres to money ... 0K2").
- **Why.** One valuation identity; prices are declared per tenant and belong to the evaluator's inputs. Carrying a
  figure into the manifest as an option parameter is `6c`'s future use and is held by owner-away row 37; nothing in 0K2
  writes a manifest, a config or a label (D-0K2.20).

## D-0K2.13 Results carry their input class; replacing the design values is held for the owner

- **Amended 2026-11-21 by D-0K4.11 and D-0K4.12** (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`):
  no longer held. One model-computed figure per quantity, labelled by its source; no design value beside it; until
  0K4d's figures land the stop-70 option reads "Not available yet" with its mechanism. The labels ruled here stand.

- **Ruling.** Every `StudyResult` carries `input_class` (SIMULATED here) and `evidence_class` MODELLED. The packet
  sets the 61-day figures beside the design values. Whether a figure from a replay on a declared simulated season may
  replace a design value, or its label, anywhere is **held for the owner** (owner-away row 37). Meanwhile the design
  values and their label stay as they are and nothing is served.
- **Why.** Decision D6: replay figures are design values until each replay passes, and are "never used as a result
  until the replay runs on the operator's own records". Passing on simulated data is a step that D6 does not settle;
  that is the owner's client-exposure rule (Q13), not the Architect's.

## D-0K2.14 The 0K1 seam test's allow-list grows by the two new backend files

- **Ruling.** `test_nothing_else_in_the_backend_names_the_replay` allows `runs/replay_study.py` and
  `backend/tests/test_0k2_replay_study.py`; nothing else in it changes.
- **Why.** The study must import `assetops_contracts.forward_replay`; the test exists so each new caller is named,
  and this names them.

## D-0K2.15 No served text, no migration, no guard change

- **Ruling.** Nothing is served or rendered; `StudyRefused.detail` is a developer diagnostic. No table, no migration
  number is taken.
- **Why.** D-SC1.28 governs served text and there is none; the design's calibration replays "need no migration"
  (`reuse-and-gap-matrix.md`, calibration replays K, M and E).

## D-0K2.16 The study's steps are public helpers (`spec.md` §2.5)

- **Ruling.** `study_days`, `admissible_days`, `start_state`, `checked`, `calibrate`, `count_starts`, `burns`,
  `step_local_times`, `by_month` and `dawn_outcome`, with `StudyDay`, are public with the signatures of §2.5, and
  `replay_study` is composed of them.
- **Why.** `0M` replays demand through the same port with the same window, sample, calibration, start rule, months
  and dawn bound (`specs/0M-mto-headroom-replay/spec.md`). Naming them here keeps one rule of each and leaves `0M`
  nothing to design; the helper names were otherwise the implementer's (RULES §5).

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Questions: `handshake.md` R1 to R7, I1 to I5 (branches
`task/0K2-handshake` `8ee9e081c`). Each question is answered once below and folded into `spec.md` rev 2 and
`reviewer-guide.md` rev 2. The kernel law cited is read on `main` (`simulator/assetops_simulator/packs/mini_grid.py`
docstring lines 14-23 and the dispatch at 686-731). The reviewer's 61-day probe figures are taken as reported; they are
outputs, and the build's own run replaces them. Owner-level call: owner-away row 42 (**owner to weigh in**).

## D-0K2.17 (R1) The dawn bound: what the study measures, states and claims when the baseline fails it

- **Ruling.**
  1. **Nothing is moved to make a case pass.** The study applies the design's absolute rule unchanged (SOC at the step
     starting 05:00 local at or above 35%, the frame's values; D-0K2.8). The bound is the design's (MG5), the reserve the
     Site's or the setting's, the start charge the published series'. None of the three is the study's to change, and none
     is tuned (W1). The fixture keeps `SEASON_START_SOC = 48` (the shipped handover); no reading is excluded.
  2. **The model's behaviour is stated as the cause, in the packet and in D-0K2.8.** Kobo's frozen source priority is PV,
     battery, generator, and the kernel charges the battery from the generator only while the battery is not
     discharging. So once a night's charge falls to the effective start, min(35, 30 + 5) = 35%, the generator starts but the
     battery keeps serving load first, down to the reserve (30%); what the generator puts in one step is taken out the next,
     and the battery dwells just above the reserve until PV returns. The stop threshold (60 to 90) is never reached at night,
     so the stop setting cannot change such a night. With the dawn limit equal to the effective start and 5 points above the
     reserve, **every night that reaches the start before 05:00 fails the bound, in every reserve-30 case, the baseline
     included.** This is the shipped dispatch law (disclosed in the pack's docstring), not a defect and not a claim about
     Kobo's real controller; the packet says so in those words.
  3. **Each failing dawn is shown with its cause class** (packet, from the tool; `replay_study.py` holds no calendar):
     per case, every reading below the limit with its date, SOC and the projection's generator state, classed
     `window-start` (the window's first local date: driven by the declared start state, 48% crossing 35% at 04:55),
     `after-overcast` (the previous local day is overcast in the fixture calendar) or `other`. The packet also states the
     least reading at or above the limit and its margin (the probe: 45 of 61 at 35.26, 0.26 above), and that the design's
     choice rule ("worst replayed day at least 2 points above the dawn limit", `6c`'s) is not met by any case either.
  4. **What PASS and FAIL mean.** `dawn_verdict` is one case's absolute verdict and nothing more: PASS means no reading of
     that case is below the limit; FAIL does not say the setting made dawn worse. Because the baseline can fail, every
     `CaseOutcome` also carries `new_dawn_days_below` (local dates below the limit in this case and not in the baseline)
     and `cleared_dawn_days_below` (below in the baseline, not in this case), both `()` for the baseline. These are facts,
     not admissibility: whether an option is admissible relative to no action stays `6c`'s, for the owner (row 42).
     `DawnReading` gains `generator_state` (the projection's state at the dawn step), so the per-date table needs no
     second reader.
  5. **What the study claims.** On a declared simulated season, under the shipped dispatch law, each setting's dawn
     readings and the dates it adds or clears against no action. It does not claim that Kobo fails dawn (the input is
     simulated), nor that any setting is admissible or rejected.
- **Settled 2026-11-21 (D-0K4.9, D-0K4.11):** the owner accepted the 0K4 path and its admission rule (dawn margin as
  information, not a gate); the design value is withdrawn, not kept. The bullet below is the record of the question.
- **Owner to weigh in (row 42).** The pack's stop-70 row ("0 of 61", "dawn PASS") and MG-T2's value (2,916.00) need a
  dawn pass that this model cannot give under the absolute rule: by the law above, every reserve-30 case fails at least on
  the dawns after overcast days, and the reserve-25 cases start the generator later still. The design value and its label
  stay unchanged (row 37 holds). `6c`'s spec must put the admissibility rule to the owner before it admits or rejects any
  generator-setting option. The Architect's default for that question: admissible when the case adds no dawn day below the
  limit against no action, with the absolute readings shown beside it, since a failure no action shares is the Site's, not
  the setting's.
- **Why.** The finding is the model behaving as written on the Site's own settings: the design's dawn limit sits on the
  effective start threshold. Moving the bound, the reserve or the start charge in the spike would choose the answer; hiding
  the failure would misstate the model; a verdict alone cannot separate settings when every case fails. The date sets
  separate them without a judgement the spike is not entitled to make. Excluding day 0 would leave 60 days, under the
  61-day sample, so it is classed, not dropped.

## D-0K2.18 (R2) Position is tested against the site trajectory, not only totals

- **Ruling.** Three checks, each with a precondition that it can see a one-step shift:
  - **T11 (replay against the site, step by step, 8 days, baseline).** With `S` the site trajectory read by the test
    (SOC `B[i].stock(...)` exact, generator kWh `B[i+1].interval_measurement(...)`, state
    `B[i].discrete_state_for_step(...)`) and `p` the baseline projection: SOC mean absolute difference over all steps
    `<= 1/10` point; `Σ |p.steps[i].generator_kwh − S.kwh[i]| <= 1/100 × Σ S.kwh`; and the transition steps (indices where
    the state differs from the step before) of `p` and `S` differ in at most 10% of `S`'s. **Precondition:** `S` against
    itself shifted one step, each way, breaks each of the three bounds (so a shift is visible). The site's dawn dates below
    35% equal the baseline replay's.
  - **T12 (publication pins).** Every published value equals the test's own read of `B` at the index and quantum of spec
    §3, every step, every series (PV and loads from `B[i+1]`, generator kWh from `B[i+1]`, state and SOC from `B[i]`,
    start fuel from `B[0]`).
  - **T1 gains:** through a recording port, the baseline request's start state equals the test's read of `B[0]`
    (quantized SOC, state, fuel) exactly.
  If the unshifted replay breaks a T11 bound, that is a mid-build question; no bound is widened. Plants P21 (PV or a load
  from `B[i]`: T12, T11), P22 (SOC or state from `B[i+1]`: T12), P23 (start state from step 1: T1, T11).
- **Why.** The tolerances compare sums, and a reader that reads the replay's own steps moves with it; only a comparison
  with the site trajectory, and a precondition that proves the comparison sees one step, makes a shift fail. The bounds
  sit above the probe's quantization error (0.02 point MAE) and, by the precondition, below a one-step shift.

## D-0K2.19 (R3) A kernel-backed month boundary

- **Ruling.** `base_run` and `season_inputs` take the window start (`start: str = SEASON_START`); the calendar stays by
  day index from the window start. **T13:** 8 days from `2026-09-26T21:00:00Z` (27 Sep to 4 Oct local), `min_litre_days=8`,
  grid `(S(70, 30),)`: `CALIBRATED`; `avoided_l_by_month`, `added_throughput_kwh_by_month` and `added_starts_by_month`
  equal the reader's split by offset (`2026-09` the first 4 × 288 steps); precondition both months' avoided litres
  non-zero. P4 also fails T13.
- **Why.** The 8-day season lies inside September; only a window across 1 Oct local can show a UTC or off-by-one month
  boundary on kernel output. Three more 8-day kernel runs cost seconds.

## D-0K2.20 (R4) Labels on every record a reader can take out; no adopting word

- **Ruling.** (1) `Calibration` and `CaseOutcome` carry `input_class` and `evidence_class = "MODELLED"`, copied from the
  study and validated as on `StudyResult` (`input_class` in `INPUT_CLASSES`, `evidence_class == "MODELLED"`, else
  `ValueError`); `MonthFigure` and `DawnReading` are values inside a labelled record and are never written alone. (2)
  `Calibration`'s `*_observed` fields become `*_site` (`generator_kwh_site`, `starts_site`); `ObservedSeries` keeps its
  name as the seam's role (0K3 feeds recorded readings through it) and its docstring says the class travels in
  `input_class`; no printed line or packet text says "observed" alone, but "site series (SIMULATED)". (3) On SIMULATED
  input `CALIBRATED` means the replay path reproduces the kernel run that made the series (adapter fidelity), not that the
  model matches a Site; the docstring, the tool's first line and the packet say so, and `6c` reads `status` only with
  `input_class`. (4) The tool prefixes every printed line with `input_class=SIMULATED evidence_class=MODELLED` and writes
  both in the JSON header; the packet columns read "site (simulated)", "design value (unchanged, still labelled design)"
  and "season replay (SIMULATED, MODELLED)", with no verdict word and no pass/fail between the design and season columns.
  (5) B13 scans the string constants (not docstrings) of `runs/replay_study.py` and `tools/kobo_replay_study.py` for
  `reproduc`, `confirm`, `validat`, `replace`, `agree` (any case): none. (6) D-0K2.12's last sentence is replaced (below).
- **Why.** `6c` will take outcomes one at a time, and a figure that leaves its result unlabelled reads as a result; row 37
  is held. The field names travel into the JSON, so they must not say "observed" of a simulated series.
- **Amends D-0K2.12 "Why", last sentence, to:** "Carrying a figure into the manifest as an option parameter is `6c`'s
  future use and is held by owner-away row 37; nothing in 0K2 writes a manifest, a config or a label."

## D-0K2.21 (R5) Each design figure on its own basis

- **Ruling.** The design's bases (§4.2): avoided litres a month (210, 20); added throughput 150 kWh **a month** (the value
  formula's wear, 12.00 = 150 × 0.08, is monthly); dawn days as a count of 61. The 150 kWh is a throughput, not a
  capacity; the frame's 200 kWh is Kobo's battery capacity (D-0K2.11 reworded). `CaseOutcome` gains
  `added_throughput_kwh_by_month` and `added_starts_by_month` (`by_month` of the per-step differences against the
  baseline; each sums to its total). The packet shows September and October beside each per-month design value, and the
  window figure × 30 / 61 labelled "scaled to 30 days", computed by the tool, never by `replay_study.py`.
- **Why.** A 61-day total beside a monthly figure misleads by a factor of two; the month split is measured, the 30-day
  scaling is a stated arithmetic.

## D-0K2.22 (R6) The overcast day's evening reserve override stays out, stated beside the reserve figures

- **Ruling.** A declared simplification: the season's overcast days do not take `kobo-daytime-overcast`'s
  `evening-reserve-override` (reserve 15% from 16:00). The packet states it beside the reserve-25 figures and the
  after-overcast dawns, with its effect not estimated. Not a finding.
- **Why.** Taken as a frozen forcing it would give those hours a second reserve source beside the reserve lever, so the
  case ids would no longer name the reserve in effect; one reserve per case keeps each case's setting what its id says.

## D-0K2.23 (R7) One start count is read

- **Ruling.** `6c` reads `CaseOutcome.starts` (§2.3's rule, the one rule used for calibration). T3 asserts it equals the
  reader's own transition loop and, on the season (STOPPED start, first step STOPPED, asserted), `projection.starts`.
  B6 gains a scripted case where the two differ (a first step STARTING after a STOPPED start state): the study's count
  is the §2.3 count.
- **Why.** One rule on both sides of the calibration and in every outcome; the projection's own count stays the
  adapter's diagnostic.

## D-0K2.24 (I1) The run is timed before it is capped

- **Ruling.** `tools/kobo_replay_study.py --time-one` builds the 61-day site run and one baseline replay, prints the wall
  seconds of each and exits 0. It runs first, through the slot pool (`--label 0K2-time`, cap 10 minutes). The full run's
  cap is then `max(25, ceil(2 × (site + 15 × replay) / 60))` minutes, recorded in the packet with the wall time per
  replay. D-0K2.4's 44 s is an estimate only.
- **Why.** The forcing count grows about fivefold from 8 to 61 days; a cap set from an extrapolation could kill a healthy
  run. Twice the measured time is the standing cap rule.

## D-0K2.25 (I2) The tank check names the right fields

- **Ruling.** `TANK_BOUND_MET` when any step's `fuel_start_l == 0` or the projection's `fuel_end_l == 0`; B9 has one case
  of each.
- **Why.** `ReplayStep` has no end fuel; a tank that empties in the last step is seen only at the projection's end.

## D-0K2.26 (I3) `LATE_WINDOWS` is pinned by a stated mapping

- **Ruling.** T8 maps each `NIGHT_WINDOWS["late"]` row to `(minute of its "HH:MM" start, its minutes, {"load-res": res,
  "load-clinic": clinic})` and asserts row-by-row equality with `LATE_WINDOWS`, and that the start minutes are 1200 and
  1320.
- **Why.** The two shapes differ; "equals" needs the mapping written down.

## D-0K2.27 (I4) The seam scan

- **Ruling.** Yes: both new backend files go into `allowed`; no other new backend file names `forward_replay`, docstrings
  included; the packet shows the scan's file count (above 100).
- **Why.** The test exists so each caller is named.

## D-0K2.28 (I5) The kernel test file is cached

- **Ruling.** `functools.cache` on the 8-day site run, its observed series and the baseline replay (one module cache, as
  0K1); T4's 14-day site run and T13's 8-day run are each built once. Target about 1.5 minutes with T11 to T13.
- **Why.** Run time is a cost every later regression pays.

## D-0K2.29 (class of 0M I1) Every case id and grid value is checked before the first port call

- **Ruling.** §2.2 gains step 4a: for each grid setting, a given value that is not integral, or two settings with the same
  case id, is `STUDY_GRID_INVALID` (new code) subject `grid:<index>`; a value left `None` is written `site` in the id
  (`stop-site-reserve-25`), so every id is known before any call; each id must fullmatch `CASE_ID`. Amends D-0K2.9 for
  `None` values; `KOBO_GRID` has none.
- **Why.** Rev 1 formed ids after the baseline replay, from the projection's values, so a bad grid raised after the port
  had run; a refusal must precede every port call (spec §6 Q4). 0M's I1 found the same class for its customer ids
  (D-0M.18).
