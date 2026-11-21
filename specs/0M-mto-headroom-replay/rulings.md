# 0M rulings

Architect (Claude), 2026-11-21, on the owner's delegation (`owner/owner-away-architect-decides-2026-11-21.md`).
D-0M.1 to D-0M.11 are applied by `spec.md` rev 1. Checked against `main` (`a53a77a2e`) by running an 8-day Mto
season (full and 25 kW inverter) through `HostForwardReplay`. Owner-level calls: owner-away row 37 (held, shared
with 0K2) and row 39.

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
