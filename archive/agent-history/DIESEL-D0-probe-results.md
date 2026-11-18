# DIESEL-D0: Kisiwa simulator trial, results

Ruling: `.agent/build-sheet-DIESEL-1.md` §2 (f755f085b). Owner decisions: `.agent/owner-diesel-site-2026-11-07.md`,
`.agent/owner-diesel-night-window-2026-11-07.md`.

## Expected outcome (recorded before the measured run, committed before the tool exists)

- Architect's pre-registered expectation (DIESEL-1 §2.9 S1, verbatim): "under cycle charging the saving comes only
  from diesel-charged energy still in the battery when the sun rises, so it depends on whether the overnight run
  reaches past dawn. A result below 20 % is plausible."
- Builder's hand estimate from the §2.2 values (no simulator run yet): with stop 90 % the generator runs about twice a
  night (about 20:00-22:00 at 38 kW, about 00:40-02:30 at 27 kW), about 115 kWh, about 41 L; the battery then drains to
  about 36-37 % by 08:00, so almost no diesel-charged energy is left when the sun takes over. With stop 60 % each run
  is shorter but the battery reaches the 35 % start setting more often (about four or five starts a night, one of
  them after 06:00), and the generator energy is about the same or higher. **Expected: NOT MET (S1), with a
  reduction near 0 % or negative.** Cold store: expected no power cut. Battery: expected never below 30 %.

The measured result is below; nothing in §2.2-§2.7 was changed after this was written.

## (a) Result

Kisiwa trial (example data, simulator): 43.4 L → 41.5 L of modelled diesel per night (6 pm to noon), 4.4 % less, on 3 nights before and 3 after stopping the generator at 60 % instead of 90 %. Cold store power cuts: 0. Pass mark (at least 20 % less, declared by the owner on 7 Nov 2026): not met.

- Result: **NOT MET** (rule 1 fails; rules 2 and 3 hold). Exact: mean before 26057/600 L, mean after 99613/2400 L,
  reduction 65/1468 = 4.43 %. All nights (1-5 against 6-9): 4.4 % (FRAGILE does not apply; it qualifies only a PASS).
- Money, information only: about 2.40 USD a night ((43.428 − 41.505) × 1.25 USD/L), modelled from a generic fuel
  curve, not measured by a fuel meter. Not annualised.
- Source: `.agent/DIESEL-D0/probe-result.json`, written by `tools/probe_kisiwa_nights.py --write`.

## (b) Per night (night k = 18:00 local on run k's day to 12:00 the next day)

| Night | Stop | Litres (6 pm-noon) | Loaded / idle L | Tank drop L | Gen kWh | Running min | Starts | Battery 18:00 / 06:00 / 12:00 % | Min battery % | Cold store unserved kWh | All loads unserved kWh |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (margin) | 90 % | 43.428 | 43.428 / 0 | 43.428 | 122.333 | 225 | 2 | 89.474 / 57.931 / 100.000 | 31.579 | 0 | 0 |
| 2 (margin) | 90 % | 43.428 | 43.428 / 0 | 43.428 | 122.333 | 225 | 2 | 89.474 / 57.931 / 100.000 | 31.579 | 0 | 0 |
| **3** | 90 % | **43.428** | 43.428 / 0 | 43.428 | 122.333 | 225 | 2 | 89.474 / 57.931 / 100.000 | 31.579 | 0 | 0 |
| **4** | 90 % | **43.428** | 43.428 / 0 | 43.428 | 122.333 | 225 | 2 | 89.474 / 57.931 / 100.000 | 31.579 | 0 | 0 |
| **5** | 90 % | **43.428** | 43.428 / 0 | 43.428 | 122.333 | 225 | 2 | 89.474 / 57.931 / 100.000 | 31.579 | 0 | 0 |
| **6** | 60 % | **41.505** | 41.505 / 0 | 41.505 | 116.917 | 215 | 4 | 89.474 / 48.999 / 92.306 | 31.579 | 0 | 0 |
| **7** | 60 % | **41.505** | 41.505 / 0 | 41.505 | 116.917 | 215 | 4 | 89.474 / 48.999 / 92.306 | 31.579 | 0 | 0 |
| **8** | 60 % | **41.505** | 41.505 / 0 | 41.505 | 116.917 | 215 | 4 | 89.474 / 48.999 / 92.306 | 31.579 | 0 | 0 |
| 9 (margin) | 60 % | 41.505 | 41.505 / 0 | 41.505 | 116.917 | 215 | 4 | 89.474 / 48.999 / 92.306 | 31.579 | 0 | 0 |

- Battery at every 15:00 cut: 100.000 % (runs 1-9); generator STOPPED at every cut. Reserve in effect 30 % at every
  step; no boundary of any night below it. Cold store unserved over all steps of all 9 runs: 0 kWh.
- Every night is identical within its phase: the weather and loads are the same every day and the battery is full at
  every 15:00 cut, so each day starts from the same state.
- No idle minutes: with cycle charging the running generator always carries load or charging, so the 4.9 L/h no-load
  rate never applies. Tank drop equals loaded litres on every night.

## (c) Gates

| Gate | Result | Detail |
|---|---|---|
| G1 | pass | every run READY at setup; `run_to_end` completed (9 day-runs and the 5-day run) |
| G2 | pass | accepted generator energy × 0.355 equals the tank drop at every step of every run, exactly (0 failing) |
| G3 | pass | generator STOPPED at all nine 15:00 cuts |
| G4 | pass | chained runs 1-5 equal the continuous 2026-10-01T12:00Z-10-06T12:00Z run (stop 90) at every boundary: battery, fuel, generator state, exactly; every seam carries exactly |
| G5 | pass | 0 fuel-limited steps |
| G6 | pass | `--check` on a fresh run: "probe result current" (byte-equal) |

G4 note: the continuous 5-day scenario, built with the same 10 windows per day, was refused by the scenario parser
("Scenario document in a Kisiwa probe scenario has more than 4000 nodes"). The 5-day document now joins adjacent
windows with the same level (the level at every minute is unchanged; the measured day-runs are unaffected). This is
the G4 comparison document only; the Architect may rule on it.

## (d) Information only

- 18:00-06:00 litres: before 43.428 L, after 41.505 L, 4.4 % less. All generator running falls before 06:00 in both
  phases, so the noon-ended window adds nothing here. **Never the pass figure.**
- Indicative avoidable minutes (labelled indicative; the product's classification runs at D3): 190 min a night before,
  145 min a night after. Not zero on nights 3-5, so S7 does not apply.

## (e) Speed

In-memory seconds per 24-hour run: 0.92, 1.01, 0.95, 1.12, 0.94, 1.06, 1.02, 0.97, 1.25 (about 1 s). Whole tool
(9 day-runs and the 5-day G4 run, Site build and setup included): about 18 s wall.

## (f) Stop

**S1, NOT MET.** The reduction is 4.4 %, below the owner's 20 %. Per DIESEL-1 §1.2 the D lane stops at D0; nothing in
§2.2-§2.7 was changed. Reading: with stop 90 % the battery is at 57.9 % at 06:00 and the sun refills it by 12:00, so
little diesel-charged energy is left at sunrise; with stop 60 % the generator starts 4 times a night instead of 2 and
saves about 5.4 kWh of generator output (122.3 → 116.9 kWh). This matches the pre-registered expectation.
