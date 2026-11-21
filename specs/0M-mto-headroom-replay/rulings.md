# 0M rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0M.1 to D-0M.11 are applied by `spec.md` rev 1; D-0M.12 to
D-0M.22 (handshake round 1) by rev 2. Checked against `main` (`a53a77a2e`) by running an 8-day Mto
season (full and 25 kW inverter) through `HostForwardReplay`. Owner-level calls: owner-away row 37 (held, shared
with 0K2), row 39 and row 42 (shared with 0K2).

## D-0M.1 0M starts on 0K2's merge

- **Ruling.** 0M reuses 0K2's `ObservedSeries`, `StudyFrame`, window, sample, start, calibration, start rule, burns,
  months and dawn helpers (0K2 spec §2.5, D-0K2.16) and its season fixture. Its build starts when 0K2 is merged; its
  handshake may run earlier. This amends `delivery-plan.md` §2, where `0M` depends on `0K1` only.
- **Why.** Design §4.3: "Error modes: as §4.2", the same calibration; one rule of each (W6). Writing a second
  calibration in 0M to keep the old dependency would let the two drift. The schedule is unchanged: in
  `two-week-build-plan.md` §0.2 lane C runs 0K2 (days 8 to 10), then 0M (10 to 12).

## D-0M.2 The Mto plant: the Kobo template edited to the manifest's Mto facts

- **Ruling.** `host/tests/mto.py` edits the Kobo template with the manifest's Mto `physical` values (PV 50 kW,
  battery 150 kWh, reserve 30%, generator 30 kW, SFC 0.33) and the inverter limit 50 kW (both inverters) or 25 kW
  (INV-MT-02 failed). Facts Mto does not state keep the Kobo template's values, listed in the packet.
- **Why.** The manifest names `hybrid-mini-grid-100kw` as Mto's base, but that template lacks the properties the
  mini-grid models v5 to v7 resolve (`pv-rated-power`, `inverter-ac-limit`, `battery-energy-capacity`, the PCS
  limits); 0K1's adapter replays only those models (D-0K1.3). The kernel models one AC limit, so two 25 kW inverters
  are one 50 kW limit, and one failed is 25 kW. Probed: both runs READY.

## D-0M.3 Mto's season: Kobo's day types and calendar, loads halved

- **Ruling.** `season_inputs(run, days, load_scale=Fraction(1, 2))`: the same irradiance windows and overcast
  calendar as Kobo's season (the same declared weather for two Lakeside Sites), each load's value × ½.
- **Why.** Mto has no shipped day type. Its October delivered energy is 6,000 kWh (manifest); the Kobo profile
  delivers about 386 kWh a day, 11,580 a month, so about 0.52; ½ is declared. Every other value is shipped and
  labelled example data; the scale is stated as a fixture choice, and the figures are outputs (W1).

## D-0M.4 A customer joins one named Site load

- **Ruling.** The customer's kW is added to the series of `host_load_id`; the Mto fixtures use `load-mill`, the
  productive feeder. A load id the Site does not have is `CUSTOMER_LOAD_UNKNOWN`.
- **Why.** The port takes exactly the plant's loads (`REPLAY_ADDRESS_UNKNOWN` otherwise, 0K1 §2.4 step 5), so a new
  load needs a host. The kernel serves loads by their total (D-0K1.19), so which load hosts it changes nothing in
  the replay; the productive feeder is where a huller would be metered.

## D-0M.5 "22 days a month" is Monday to Friday local

- **Ruling.** `weekdays = {0, 1, 2, 3, 4}` for both customers; September and October 2026 each have 22 weekdays
  (pinned in H6).
- **Why.** The LOI states a day count, not dates; weekdays give exactly 22 in both months of the window, so the
  monthly figures match the LOI's 1,650 kWh without a declared day list.

## D-0M.6 Headroom is observed: PV available minus the Site's load

- **Ruling.** Per step `h = max(0, PV available − Σ observed loads)`; a customer day is without headroom when any of
  its customer steps has `h < kW`; `kwh_beyond_headroom = Σ max(0, kW − h) × 5/60` over customer steps.
- **Why.** Design §3.10 keeps unused capacity as a capacity factor read from the Site's own series; §4.3 says days
  without headroom "are weather-driven". The design's 225 kWh is 3 days × 75 kWh, the customer's whole energy on
  those days; the step-level sum is the same idea measured, and never more. PV that would have charged the battery
  counts as headroom here; what taking it costs is the replay's extra litres, not this figure.

## D-0M.7 The cost of a customer is a pair of whole-window replays

- **Ruling.** Each figure is the customer's replay minus the no-customer replay at the same capacity (the baseline,
  or the reduced run), both over the whole window.
- **Why.** The probe showed the battery state carried for days after each customer day: 11 of 14 days differed for
  10 customer days. A per-day test of "did the trajectory change" would count those carried days; a per-day replay
  restarted from the observed state would drop the carried cost. Design §4.3: marginal fuel = F(with) − F(without).

## D-0M.8 Reduced capacity: a second base run and `min(PV, limit)`

- **Ruling.** The reduced case replays a base run frozen with the reduced inverter limit, fed `min(observed PV,
  limit)`; the limit is the caller's, from the Site's Foundation.
- **Why.** The observed PV-available equals the potential wherever it is below the full limit and equals the full
  limit where clipped; under any lower limit, `min` of either gives exactly `min(potential, lower limit)`, the
  kernel's own value (`minigrid.py` `min(potential, limit)`). It needs the series to be published under a limit at
  least the reduced one, which holds for a failure that lowers capacity. No inverter law is otherwise applied.

## D-0M.9 The customer's evidence word is carried, not judged

- **Ruling.** `evidence` is `SIGNED` or `VERBAL` and is carried to each outcome. The welder (verbal) is replayed as
  the negative control. `NO_CUSTOMER_EVIDENCE` (no value without customer evidence) is the evaluator's, in `6g`.
- **Why.** Design §4.3's refusal is about value; a replay is a physical consequence, and the negative control is the
  welder (MG-T6). Refusing the replay would lose the control.

## D-0M.10 Sample and calibration

- **Ruling.** At least 28 admissible days (`MIN_DEMAND_DAYS`), else `SAMPLE_TOO_SHORT` with no replay; the baseline
  is calibrated by 0K2's rule (D-0K2.5); reduced runs are counterfactual and are not calibrated.
- **Why.** Design §4.3: "≥ 28 days covering the window"; calibration "as §4.2".

## D-0M.11 No money, no record, no served text, no migration

- **Ruling.** No tariff, price, collection cost or connection cost; no PRODUCTIVE_LOAD calculation record; nothing
  served; no migration. Every result carries its input class and MODELLED; replacing a design value is held for the
  owner (owner-away row 37, as D-0K2.13).
- **Why.** Money is the valuation identity's (`6g`); the calculation record is the option's (`6g`); D-SC1.28 governs
  served text and there is none.

## Handshake answers (round 1)

Architect (Claude), 2026-11-21, on the owner's delegation. Questions: `handshake.md` R1 to R6, I1 to I4 (branch
`task/0M-handshake` `ed8d4e2fe`), answered with 0K2's (D-0K2.17 to D-0K2.29), whose helpers and labels 0M reuses. Each
question is answered once below and folded into `spec.md` rev 2 and `reviewer-guide.md` rev 2. Owner-level: the dawn
finding is owner-away row 42 (shared with 0K2); nothing else here is owner-level.

## D-0M.12 (R1) The monthly customer claim is asserted

- **Ruling.** **M8:** a stub port over a 61-day window from `2026-08-31T21:00:00Z`: the huller's `customer_days` has 44
  dates, `customer_kwh == 44 × 75`, and `customer_kwh_by_month` is 1,650 for each of `2026-09` and `2026-10`. P2 fails
  M1 and M8; H6's weekday count is a calendar pin, not P2's test.
- **Why.** A calendar fact no implementation can break catches nothing; the 22-day claim lives in the customer steps.

## D-0M.13 (R2) The demand sample is admissible days of the window

- **Ruling.** `MIN_DEMAND_DAYS` counts admissible days of the window (0K2's rule), whatever the customer's weekdays; the
  comment reads "design §4.3: >= 28 admissible days covering the window". **M5 gains** the boundary at the default
  `min_days`: 27 admissible days is `SAMPLE_TOO_SHORT` with zero calls, 28 proceeds. P15 fails H6 and M5.
- **Why.** Design §4.3: "≥ 28 days covering the window (days without headroom are weather-driven)": the sample is of
  weather, so of days, not of customer days.

## D-0M.14 (R3) Labels on every outcome; no adopting word

- **Ruling.** `DemandOutcome` and `CapacityOutcome` carry `input_class` and `evidence_class = "MODELLED"`, copied and
  validated as D-0K2.20. The tool prefixes each line and the JSON header with both, and writes `plant` = `MTO_PLANT_NOTE`
  ("Kobo template edited to Mto's manifest facts; loads halved; simulated season", a constant in `host/tests/mto.py`). M7
  gains the D-0K2.20 string scan over `runs/headroom_replay.py` and `tools/mto_headroom_study.py`. The packet's design
  column is headed "design value, unchanged (held, row 37)". Spec §0 "Why next" reads "design values until the owner
  rules (owner-away row 37)".
- **Why.** `6g` takes outcomes one at a time; an unlabelled figure leaves as a result.

## D-0M.15 (R4) Month splits for every figure the design states per month

- **Ruling.** `DemandOutcome` gains `customer_kwh_by_month`, `kwh_beyond_headroom_by_month` and
  `days_without_headroom_by_month` (`by_month` over per-step values: `c_i × H`; `max(0, c_i − h_i) × H` at customer steps;
  1 at the first customer step of each date without headroom, else 0), each summing to its total. H2 checks each against
  the reader's own loop; the packet sets October beside the design's October values.
- **Why.** The design values are a month's (3 days, 225 kWh, 68 L in October); a hand cut outside any test would be an
  unchecked figure.

## D-0M.16 (R5) Plants on the host load, the reduced headroom and the window edges

- **Ruling.** (a) H5 asserts, on the real run's recorded request, per-step equality by load id: `load-mill` = observed +
  the reader's `c_i`, every other load = observed. (b) H4 asserts every REDUCED `DemandOutcome` field equals the reader's
  (headroom from `pv_r`), with the precondition that the huller's REDUCED `kwh_beyond_headroom` strictly exceeds its FULL
  one; plant **P18** (reduced headroom read from the full PV) fails H4. (c) M1 also asserts: 06:55Z and 12:00Z on 1 Sep
  carry no customer, 11:55Z does.
- **Why.** The kernel serves loads by their total (D-0K1.19), so only the request shows a wrong host; equal-set
  inclusion cannot see the wrong PV; the window's last step is as easy to miss as its first.

## D-0M.17 (R6) The dependency on 0K2 stands; no stacking

- **Ruling.** The start gate stays "0K2 merged to `main`"; the packet records the 0K2 merge commit. Unit 1 does not start
  on frozen 0K2 signatures: 0K2 rev 2 changes the helpers 0M calls (`dawn_outcome`'s readings, `dates_below`,
  `start_steps`, the labels), and lane C already runs 0K2 (days 8 to 10) before 0M (10 to 12), so stacking gains nothing.
- **Why.** 0M needs every §2.5 helper and the season fixture, not only the calibration rule; a stub would unblock
  nothing, and two copies are what D-0M.1 forbids.

## D-0M.18 (I1) Every derived case id is checked before any port call

- **Ruling.** Step 1 refuses `CUSTOMER_ID_INVALID` unless both `customer_id` and `reduced-<customer_id>` fullmatch
  `CASE_ID` (so at most 32 characters), as well as the rev 1 rules. M5 gains a 33-character id: refused, zero calls. Same
  class as D-0K2.29.
- **Why.** The reduced id was formed only after `1 + k` replays had run; every refusal precedes the port.

## D-0M.19 (I2) The reduced run is checked against its frozen Foundation before any port call

- **Ruling.** Step 1 (when `reduced` is given) reads `deterministic_identity.model_needs` of `run` and `reduced.run`.
  `REDUCED_CAPACITY_INVALID` subject `reduced` unless: each run has exactly one need with `property_key ==
  "inverter-ac-limit"` and unit `kW` (`INVERTER_LIMIT_KEY`); `Fraction(str(value))` of the reduced run's equals
  `inverter_limit_kw`; the full run's is strictly greater; every other need is equal on (`state_ref`, `property_key`,
  `canonical_value`, `canonical_unit`) and the two `interval`s are equal (the detail names the first difference). M4 gains
  stub cases (a stand-in exposing `deterministic_identity.model_needs` and `.interval`): limit mismatch, full run not
  above, another need differing; each zero calls. H1 gains: `ReducedCapacity(mto_base_run(8, inverter_limit_kw=25),
  Fraction(30))` and `ReducedCapacity(run, Fraction(25))` (the full run) each refused, zero calls. The pre-flight prints
  both runs' `inverter-ac-limit` rows; a unit other than `kW` is a mid-build question.
- **Why.** The frozen identity is the run's own record of its Foundation; reading it is not a law, and it turns a
  mislabelled "reduced" replay, or a refusal after `1 + k` replays, into a refusal before any.

## D-0M.20 (I3) `mto_site` starts from `season_site`

- **Ruling.** Yes: `mto_site`'s first line calls `season_site(doc)`, with a comment that the run is `BLOCKED` without its
  `valid_from`; H1 asserts `execution_status == "READY"` for both runs.
- **Why.** An order dependency that fails silently should fail loudly.

## D-0M.21 (I4) The complete list of kept values; one derivation

- **Ruling.** The packet lists, each against its source: edited to the manifest (PV 50, battery 150, reserve 30 — the
  template's value, a traced no-op — generator 30, SFC 0.33, inverter 50 or 25); kept from the template (PCS 30 kW,
  start 35, stop 90, minimum runtime 30, start delay 5, efficiency 95%, load ratings 25, 10 and 40 kW, site id
  `KOBO-001`); kept from the season (irradiance windows, overcast calendar, tank 20,000 L and its rating, start fuel
  15,000 L, start SOC 48%). H6 pins the three the replay reads from the season (tank 20,000, start SOC 48, start fuel
  15,000). The only derivation is the load scale: 6,000 / 11,580 ≈ 0.52, declared ½. With PV 50 on a 50 kW limit Mto
  clips nowhere at full capacity (Kobo's 60 on 50 did); the packet says so.
- **Why.** D-0M.2's "every edit traced" needs the full list; removing a margin is a stated consequence, not a hidden one.

## D-0M.22 (from D-0K2.17) Dawn on Mto means what it means on Kobo

- **Ruling.** `DemandOutcome` and `CapacityOutcome` carry `new_dawn_days_below` and `cleared_dawn_days_below` against
  their no-customer replay (the baseline at FULL, `reduced` at REDUCED; the capacity outcome against the baseline), from
  0K2's `dates_below`, beside the absolute `dawn_verdict`. Mto keeps the template's start 35 and reserve 30, so the same
  dispatch law applies; the packet states D-0K2.17's cause beside Mto's dawn figures.
- **Why.** One meaning of the dawn bound across both spikes; a customer's dawn effect is the dates it adds.
