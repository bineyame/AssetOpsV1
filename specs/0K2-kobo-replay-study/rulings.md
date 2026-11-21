# 0K2 rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0K2.1 to D-0K2.16 are applied by `spec.md` rev 1 (D-0K2.16 added with the 0M spec, before the handshake). Checked against `main` (`a53a77a2e`) by running the kernel on an
8- and a 14-day season through `HostForwardReplay`. Owner-level calls are logged in
`specs/OWNER-AWAY/decisions-2026-11-21.md` rows 37 (held for the owner) and 38.

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
  confirms state carries for days after a change. Cost: about 2.5 ms a step, 44 s per 61-day replay.

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
  probe already shows the baseline below 35% at dawn on days after overcast ones, so the bound may fail under no
  action too; hiding that would misstate the Site. Whether an option is admissible relative to no action is the
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
  wear basis (0.08 a kWh); discharge throughput is the usual warranty measure. PCS losses are not in it; the packet
  says so beside the figure.

## D-0K2.12 No money in the spike

- **Ruling.** The study returns litres, kWh, starts, steps and SOC. Litres × price, wear cost, one-off and the
  12-month value are the evaluator's (`6c`, design §4.1). The CANDIDATE share of avoided litres is `avoided_l_on`,
  with `6c` supplying dispatch-3.2's offsets. This amends 0K1 spec §7 ("litres to money ... 0K2").
- **Why.** One valuation identity; prices are declared per tenant and belong to the evaluator's inputs. The manifest
  carries the spike's figures as option parameters (`design_value: K`), and money follows from them.

## D-0K2.13 Results carry their input class; replacing the design values is held for the owner

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
