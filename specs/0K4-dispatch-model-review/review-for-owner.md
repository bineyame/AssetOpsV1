# Kobo's generator setting: is the model realistic, and what next?

Architect (Claude), 2026-11-21, for the owner. Answers `owner/owner-decisions-list-2026-11-21.md`, answer 3 (row 42).
Proposals only: nothing here changes code, figures or labels until you accept it.
**Accepted by the owner 2026-11-21** (`owner/owner-one-figure-loyal-to-operating-world-2026-11-21.md`). Unit specs and
rulings D-0K4.1 to D-0K4.18: `rulings.md`; one-figure change list: `one-figure-change-list.md`; operator request:
`operator-request.md`.

## 1. What exists today

- **The claim in the design pack.** Moving Kobo's generator stop from 90% to 70% is worth 2,916.00 a year. It saves
  210 L a month, adds 150 kWh a month of battery use, and leaves "0 of 61 dawns below 35%". All three are design
  values, and they are labelled as such.
- **The simulated check.** We replayed a made-up 61-day season of Kobo through the simulator, setting by setting. The
  replay reproduces itself exactly, so the plumbing is sound. Its answers differ from the design:

| Stop 70% vs no change | Design value | Simulated replay |
|---|---|---|
| Fuel avoided | 210 L a month | about 85 L a month |
| Extra battery use | 150 kWh a month | 0 kWh |
| Dawns below 35% | 0 of 61 | 16 of 61, even with nothing changed |

The useful part already works. The product can take one controller setting, replay a season under it, and say what
moves. What follows is about whether the simulator's rules behave like a real mini-grid controller.

## 2. How real controllers run a solar, battery and diesel mini-grid

1. **Two ways of running the generator.**
   - *Load following*: the generator covers only what solar and battery cannot.
   - *Cycle charging*: once started, the generator carries the load and puts its spare output into the battery until
     a stop charge. This is the usual way at sites like Kobo, because a well-loaded diesel is efficient and a
     lightly-loaded one wastes fuel.
2. **Start and stop by charge.** The generator starts at a low charge (often 30-40%) and stops at a high one (often
   80-95%). It also has a minimum run (30-60 min) and a short warm-up (seconds to a few minutes). Many controllers
   also start on high load, and some keep quiet hours.
3. **When the generator runs, it takes the load.** The battery stops discharging and starts charging. The battery
   helps only if the load is more than the generator can give ("generator support"). A battery that keeps emptying
   while the generator runs is a fault an operator's engineer would notice at once.
4. **Minimum generator load.** Diesels should not run long below about 30% of their rating, because they foul
   ("wet stacking"). Controllers hold the generator up by charging the battery harder, or by cutting solar back.
5. **Fuel is not proportional to output.** A 40 kW set uses roughly 1.5-3 L an hour doing nothing. At full load it
   uses about 0.27 L/kWh, and at a quarter load 0.4-0.5 L/kWh. Every hour of running costs fuel, even at no load.
6. **Charging slows near full.** Batteries take full current until about 80% (lead-acid) or about 90-95% (lithium),
   then taper. The last band to 90% is slow, and the generator idles through it. That band is exactly what a lower
   stop setting removes.
7. **Reserve and depth of discharge.** Lithium (LFP) is usually floored at 10-20%, lead-acid at 40-50%. The reserve
   protects the battery's life and leaves a buffer for the morning peak before solar rises. Lithium also needs a
   periodic full charge (often weekly) so the battery's management can rebalance its cells and correct its
   charge reading. Lead-acid needs one too, or it sulphates.
8. **Cloudy spells.** The real risk is two or three overcast days in a row. The battery then starts each evening
   lower, and the generator runs at night.

## 3. Where the simulator is realistic, and where it is not

| Rule in the simulator | Where | Realistic? | Effect on the Kobo result |
|---|---|---|---|
| Start at or below the start charge, stop at or above the stop charge after the minimum run, with a 5-minute warm-up | `simulator/.../packs/mini_grid.py:515-545` | Yes | none |
| Start at the lower of the start charge and the reserve plus 5 points | `mini_grid.py:1150-1157` | A fair simplification | none at Kobo (both 35%) |
| **The battery serves load ahead of a running generator; the generator charges only while the battery is idle** | `mini_grid.py:19-23`, `:574` (discharge requested whenever charge > reserve), `:721-731` | **No**: the main fault | Causes 15 of the 16 failed dawns. On a night after an overcast day the generator starts at 35%, gives nothing, and the battery keeps falling to about 31% at 05:00. A real controller would be charging from 35% by then |
| Fuel = output × 0.3 L/kWh, with no fuel at idle or start | `mini_grid.py:86-90`, `:734` | No | A generator running with no output burns nothing, so cutting running hours saves too little. This understates stop 70 |
| No minimum generator load, and no cutting back of solar to hold it | `mini_grid.py:708-731` | No | Late-morning running beside strong solar is too cheap. This understates stop 70 |
| Full charging rate all the way to 100% | `mini_grid.py:699` | No (the effect is larger for lead-acid) | The 70-90% band charges too fast. This understates stop 70 |
| Efficiency 95% each way, fixed limits, generator always available | `packs/minigrid.py`; Kobo template | Acceptable for now | small |

**The 330 L the design value is drawn from.** The 210 L comes from 330 "avoidable" litres in Kobo's generator log. A
running hour counts as avoidable if solar plus the battery's *power* could have carried the load at that moment
(`backend/.../analytics/dispatch_v3.py:290-305`). That test never asks whether the battery had the *energy* to last
until sunrise. Mto's replay review found the same mistake (`specs/0M-mto-headroom-replay/review.md`, "same-step
reading"). So this source overstates the litres.

**Size of the biases.** These are engineering estimates for this review, not product figures.
- The fuel faults (no idle fuel, no minimum load, no taper) all push the same way. Correcting them would likely raise
  stop 70's saving to roughly 1.5 to 2 times the replay's 85 L: about 130-170 L a month.
- Correcting the dawn fault would likely clear the 15 overcast-night failures. The remaining one is the made-up
  season's own starting charge (1 Sep).

## 4. The dawn rule

**35% at dawn is a sensible warning line, but a poor test for a stop setting.**
- A controller that starts the generator at 35% defends that line itself, so almost any stop setting passes it.
- A dawn line tests the start and reserve settings, and whether the generator actually started. It says little about
  the stop setting.

**What operators actually judge** (in their usual order):
1. Energy not served: customer-hours without power.
2. Times the battery fell below its reserve.
3. Generator starts and running hours, which drive maintenance.
4. Litres.
5. Whether the battery gets its regular full charge.

**Proposed admission rule for a generator setting.** Compare it with no change, over the same days. Admit it only
if:
- energy not served does not rise;
- times below the reserve do not rise;
- starts stay within the generator maker's limit;
- the battery still reaches full charge at least as often as its chemistry needs (default: once a week).

Show the dawn margin beside the result as information, not as a gate.

## 5. Why the replay sits so far below the design

| Gap | Model | Season | Design value |
|---|---|---|---|
| Fuel: 85 L vs 210 L | **Too low.** No idle fuel, minimum load or taper | **Too kind.** Overcast every fourth day exactly, never two in a row, same load every day | **Too high.** Built on the 330 L "power, not energy" count |
| Battery use: 0 vs 150 kWh | Partly. The battery never helps a running generator | **Mostly.** Solar refills the battery every clear day, so the evening is identical in every case | Unsupported. 150 kWh is an assumption with no replay behind it |
| Dawns: 16 vs 0 of 61 | **Mostly.** The battery-before-generator rule | One failure is the season's starting charge | Probably right in outcome (about 0), but true by construction, so not evidence |

## 6. Recommended path

**Mechanism first, then figures.**
1. Correct the generator's behaviour, as a new simulator version so that past runs stay unchanged.
2. Give it a realistic fuel curve.
3. Give it a season with realistic weather.
4. Rerun the two studies.
5. Only then let a figure stand beside the design value.
6. Real records settle it.

| Step | What it does | Proven by | Size |
|---|---|---|---|
| **0K4a**: the generator takes the load | A running generator carries the load and charges the battery. The battery helps only above the generator's rating. The generator is held at or above 30% load, by charging or by cutting solar | Named behaviour tests: started at 35%, the charge rises; the battery discharges beside the generator only when the load is above 40 kW; low-load running never falls below 30% while solar is cut | 2 units |
| **0K4b**: fuel curve and taper | Fuel = hourly no-load fuel + L/kWh, both on the Site's generator record. Defaults come from typical data sheets and are labelled assumed until Kobo's are known. Charging tapers above a chemistry-set charge | Tests: fuel at no load, half load and full load match the declared curve. Charging reaches 100% more slowly than 90% | 1.5 units |
| **0K4c**: season with weather | Overcast spells of 1-4 days drawn from a declared, repeatable pattern for Sep-Oct. Load varies ±15% day to day. Mill days follow the week. Still labelled SIMULATED | Tests: the declared spell lengths and load spread appear in the series | 1 unit |
| **0K4d**: rerun and restate | Rerun the Kobo and Mto studies. Apply the admission rule above. Correct the pack's MG-T2 lines (remove "0 of 61 / dawn PASS", and say which rule admits the setting) | Reviewer reproduces the figures. Design values and their labels are unchanged (row 37) | 1 unit |

**Total: about 5.5 units.** It fits beside `6c` (the option evaluator): `6c` can be built now, because the replay's
inputs and outputs do not change. Its figures wait for 0K4d.

**What changes on screen** (the option card that `6f` will show, fed by `6c`):

| | Now | After 0K4d |
|---|---|---|
| Value | 2,916.00, labelled design value | unchanged |
| Simulated replay beside it | **"not available yet"** (proposed: the current 85 L comes from a rule we know is wrong) | the corrected figure, labelled SIMULATED |
| Safety line | none (the "dawn PASS" claim is removed) | "no more outages, no more reserve breaches, starts within limit", labelled SIMULATED |

**What the demo can claim now.** The demo can show:
- the mechanism: this setting changes how long the generator runs, and here is how we will check it;
- the design value, labelled as a design value;
- the next step: confirm against your own records.

It should not claim "0 of 61 dawns" or any replayed litres until 0K4d.

This is the value beyond monitoring tools: we tell an executive which controller setting costs diesel, and we check
it against their records. A model that an operator's engineer can fault in one look undoes that, so the
generator-takes-load fix comes first.

**What needs Kobo's real records** (no model replaces these):
- at least 61 days of 5-minute solar, load, generator on/off and output, battery charge, and the fuel log;
- the controller's actual settings (start, stop, reserve, minimum run, generator support);
- the generator's model and fuel sheet;
- the battery's chemistry and warranty floor.

With these, the existing calibration step (within 5% on generator energy, 10% on starts, 5 points on charge) tests
the corrected model against Kobo itself.

## 7. Your decisions (each has my default)

1. **Admission rule** for any generator setting: the four-part rule in §4, with the dawn margin shown as
   information. *Default: accept.*
2. **Replay column until 0K4d.** *Default:* it says "not available yet" rather than showing the 85 L. This is a timing
   refinement of your row 37 choice, not a reversal.
3. **Assumed equipment.** Until Kobo's sheets arrive, assume a lithium (LFP) battery and a typical 40 kW diesel fuel
   curve, labelled assumed. *Default: accept.*
4. **Kobo's records and settings.** *Default:* the coordinator lists them in the operator request; nothing waits on
   them except the final check.
5. **A later option, noted only.** Real operators often stop night-time charging low, just enough to reach sunrise,
   and let solar finish the job. *Default:* backlog, not demo scope.
