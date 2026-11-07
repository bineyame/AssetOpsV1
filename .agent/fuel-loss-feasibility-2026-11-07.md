# Unexplained fuel (loss, siphoning, short deliveries) at Kisiwa: feasibility and sizing

- Architect: Claude (fresh Architect), 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude (owner 2026-10-27). Main at `e31ccbbb8`.
- Owner question, verbatim: "is the diesel scenario we are considering the most accute one the operators relate to? do we have unexplained fuel loss or siphoning scenario?"
- This was a read-only study. No product code, DB, tick, prepare or suite was used, and the simulator was not run. D0 is still running. Its builder's estimate, written before the measured run, was read from the D0 worktree without changing anything (`AssetOpsV1-d0/.agent/DIESEL-D0-probe-results.md:11-16`).
- Paths: `B/` = `backend/assetops_backend/`, `F/` = `frontend/src/`, `C/` = `config/`, `V/` = `backend/conversions/`, `S/` = `simulator/assetops_simulator/`.

---

## Part A: Owner summary (plain language)

### 1. Which fuel problem do operators feel most?

**Short answer: probably not the one we are building.** Missing fuel is very likely the problem operators recognise first. Generator settings come second.

What is well known:
- Diesel going missing is a common, openly discussed problem wherever generators run at remote sites in Africa: siphoning from the tank, fuel taken during deliveries, deliveries that arrive short, and logbooks that don't match the tank. Tower companies and diesel-hybrid operators fit tank sensors and fuel locks mainly for this reason. A whole industry of fuel-monitoring products is sold on it.
- A finance director understands "fuel we paid for that we can't account for" straight away. It needs no engineering. It also leads to an obvious action: lock the tank, seal the dip log, fix the sensor, check deliveries.
- Wasteful generator running is real and well documented in mini-grid design work: idling, charging the battery with diesel when the sun would do it, and running at low load. But it is an engineering topic. An operations director recognises it; a finance director usually needs it explained.

What is uncertain:
- **How much fuel goes missing.** Published figures are mostly from companies that sell monitoring equipment, and they vary widely. We have no reliable figure, and we should not quote one.
- **Whether it matters for this client.** It depends on how much diesel they burn. A mostly-solar operator, like our Kobo example, burns little diesel, so missing fuel is a small sum for them. An island or diesel-heavy operator feels it sharply.
- **Whether our client has raised it.** Only you know that.

**One more honest point.** Our product can never say "theft". It can say: "This much fuel left the tank and isn't explained by the generator running or by deliveries, give or take this much." The mock-up and our product rules say exactly that.

### 2. What we have today

- **In the Lab** (the simulator workbench, not the client screens), yes. There is a "Fuel Loss Event" example: 120 litres removed at night while the tank sensor is silent, an operator's hand reading afterwards, and a delivery that overfills the tank. It runs on a simple fuel-only model, not on a real site model, and nothing on the client screens uses it.
- **On the client screens:** there is a Fuel page that shows the right layout, with an empty state. It says "No complete fuel balance yet" because, on every site:
  - no tank level is reported (Kobo's tank sensor is configured but never sends readings);
  - there is no way to record a fuel delivery or a hand dip;
  - the calculation never produces an "unexplained" figure, by design, until those exist.
- There is no "unexplained fuel" problem card, no action for it, and no check afterwards.
- The full version was planned once (task T030) and set aside when we moved to the site-first plan.

So the answer is: **we have the idea, the page layout and a Lab example, but no client-facing missing-fuel story.**

### 3. What an honest missing-fuel story at Kisiwa would look like

| Step | What the client would see (example data, labelled) |
|---|---|
| Outcome | Protect the asset: fuel paid for is fuel in the tank |
| Drivers | Fuel leaves the tank at night when the generator isn't running and no delivery is due |
| Evidence | Tank readings before and after, the delivery tickets, and what the generator should have burned. The result reads: "Between 95 and 145 litres left the tank between 1:00 and 2:30 am that the generator and deliveries don't explain. The tank sensor wasn't reporting at the time." |
| Lever | Seal the tank and sign the dip log at each shift change, and fix the sensor's power so it can't go quiet |
| Action | The change is agreed and recorded |
| Verify | On 3 fully checked nights afterwards, the unexplained amount is within the normal margin, and the sensor reported all night |

Two things you should know before choosing it:
1. **The "after" part is written by us, not worked out by the simulator.** With the generator setting, the simulator really works out how much diesel the new setting saves. A tank lock can't be simulated: the "after" nights look clean only because we don't write any fuel removals into them. The finding of the missing fuel is real product work, done from readings. The "it worked" part only shows how the check works; it is not proof that a lock helps. We would have to say that plainly.
2. **Small, steady siphoning is hard to see.** A tank sensor reads to within about 1% of the tank, roughly ±10 L on a 1,000 L tank. One night's figure only stands out if the loss is clearly bigger than the margin, say over 30–40 L. A few litres a night can only be seen over a week or more. We would say this too.

### 4. Cost, risk, and whether it fits before the demo

| Choice | Extra work | Demo date | Risk |
|---|---|---|---|
| **Keep the generator-setting story only** (today's plan) | 0 | as planned (about +2 days, D0 permitting) | as planned |
| **Swap it for missing fuel** | about **+6** units (range +4.5 to +8) | about **+2 to 3 more working days** | high |
| **Do both** | about **+8.5** units (range +7 to +11) | about **+3 more working days** (range +2.5 to +4) | high |
| **Missing fuel after the demo** | 0 now; about 8.5 later (about 13 if Kisiwa isn't built) | as planned | none now |

It is large because almost every piece is new: a tank reading for Kisiwa, a way to record deliveries and dips, the fuel balance calculation with its margin, a new kind of problem card, a new kind of after-check, and the screens and checks for all of them.

### 5. Recommendation

**Keep the generator-setting story, and do missing fuel first thing after the demo.** Before the demo, add one honest spoken line to the demo script (no build work): "The Fuel page is where unexplained fuel shows up once a site reports its tank and records its deliveries; today it says what's missing rather than guessing."

There is one exception. **D0 may well miss your 20% pass mark;** its builder expected that before the run. If it does, the generator-setting story stops. You would then choose between:
- (a) the demo without Kisiwa, on the earlier date (our recommendation, unless the client is diesel-heavy and has raised missing fuel); or
- (b) Kisiwa with the missing-fuel story instead, about 4–5 working days later than the plan without Kisiwa.

### 6. Your decisions

1. **Has this client raised missing fuel, or are they a diesel-heavy operator?** If yes, missing fuel is worth more to them than the generator setting, and option (b) above becomes reasonable.
2. **If D0 misses the 20% mark:** (a) demo without Kisiwa, on the earlier date; or (b) Kisiwa with the missing-fuel story, about 4–5 working days later?
3. **If we ever build missing fuel:** is it acceptable that the "after" nights are written by us, and labelled as such, because a lock can't be simulated?
4. **Wording:** we say "unexplained fuel" and never "theft" or "stolen". Agreed?
5. **Demo script:** add the one spoken line about the Fuel page (no build work)?

---

## Part B: Technical basis

### B1. Domain assessment

- Known and uncontroversial:
  - Diesel pilferage and delivery shortfall are a standard operating risk for remote gensets (telecom towers, island and off-grid hybrids).
  - Tank-level telemetry and fuel locks are sold mainly as loss controls.
  - Dispatch inefficiency (low-load running, idling, cycle-charging to a high SOC) is standard hybrid-design material (fuel-curve intercepts, load-following versus cycle-charging), and it is how DIESEL-1 frames the lever (`.agent/build-sheet-DIESEL-1.md:108`).
- Not known: loss magnitudes. Vendor figures are marketing, not audited. **No statistic goes into any document or the demo.**
- Product intent is fixed and compatible:
  - `.ai/PRODUCT.md:90-91` "Fuel reconciliation establishes an unexplained residual with uncertainty; it does not establish theft";
  - `.ai/DECISIONS.md:414-419` "a fuel discrepancy becomes a Finding only when materiality and confidence criteria warrant … must not infer theft";
  - `Docs/mini-grid-demo-architecture-and-roadmap.md:482-486` and `:1178` ("Material fuel movement is currently unexplained…", not "fuel theft").
- Outcome category: **Protect asset & capital** (not Optimize), per the four categories (owner 2026-10-29).

### B2. What exists on the site-first product path (versus Lab, archived, missing)

| Element | State | Where |
|---|---|---|
| Tank-level binding role | **Exists** | `fuel_level` role on FUEL_TANK, unit L: `B/sites/binding_roles.py:102` |
| Tank sensor in Kobo's Foundation | **Configured, never published** | Template device and mapping: `C/site-templates/kobo-mini-grid-60kw.yaml:321-327`, `:387-390`. Binding: `V/kobo-001-bindings.json:23`. The registered Kobo publication profile (`B/runs/profiles.py:1845` onward) declares no fuel-level signal, so Kobo has 0 `fuel_level` rows (`.agent/build-sheet-DD-1.md:1934`) |
| Tank publication with reporting gap | **Lab only** | Lab publication profile v3: 15-min cadence, −0.5 L bias, 40/1000 dropout, a forceable `fuel-level-reporting-availability` gap: `B/runs/profiles.py:1408-1470` |
| Simulator tank stock (site model) | **Exists, generator-only** | mini-grid `fuel-tank-volume-stock`, "moved only by accepted generator energy", linear law with no idle burn: `S/packs/mini_grid.py:192-207` (law `:24-27`, `:85-89`, `:732-734` per the FUEL design B1). Whether mini-grid v6 accepts an authored CAUSAL_INPUT removal or delivery event on that stock is **unverified**. The kernel has generic INCREASE/DECREASE causes (`contracts/assetops_contracts/world_inputs.py:56`, `S/kernel/execute.py:929`), and run setup freezes `state_effect` (`B/runs/service.py:2597`), but only the minimal fuel model has exercised it (`S/packs/fuel.py:93-101`, `:300-316`) |
| Fuel delivery and hand-dip records | **Missing** | Contract `OPERATIONAL_RECORD_KINDS = {"OVERRIDE_COMMAND"}`, "T030 extends it (delivery, hand dip)": `contracts/assetops_contracts/source_envelope.py:123-125`. Work operational records are `OPERATOR_LOG`, `MANUAL_READING`, `SHIFT_NOTE`, `SITE_VISIT` with a free quantity and unit and no tank link (`B/work/service.py:38`, `:470-487`). The analytic cannot read them as deliveries |
| Reconciliation analytic | **Shell only, by design** | `B/mini_depth/rules.py:614-768` `assess_fuel_hour`: one selected hour; USE = {0, 1.10 × SFC × kWh} (`:722`); DELIVERIES always `COMPLETENESS_UNCONFIRMED` (`:741`); tank terms never give a bound, because there is no tank-uncertainty property (`:677-695`); RESIDUAL always MISSING; "no fuel hour is SUPPORTED" (`:760-761`) |
| Finding | **Missing** | No unexplained-fuel Finding kind. Fuel money exists only as the dispatch consequence (fuel-cost-1; fuel-cost-2 in A1). Board contributor `NO_FUEL_BALANCE` "No complete fuel balance yet": `B/site_outcomes/mini.py:77`, `:876` |
| Screen | **Exists, empty state** | Site Performance › Fuel: `F/sites/MiniPerformance.tsx:62`, `:338-344`, `:1308-1316` (`FUEL_NOTICE` copies the mock); API `B/mini_depth_api.py:38`; evidence overview tank metric `B/evidence/overview.py:80`, `:428` |
| Mock | Spec | v69 `frontend/mockups/v69/index.html:623-630`: four terms, residual "Cannot compute", notice "cannot establish theft" (`:628`), "Shows the missing-evidence state instead of inventing a fuel-loss story for Kobo", "deferred: Fuel ERP and theft detection" (`:630`); manifest `frontend/mockups/v69/screen-manifest.json:597-612` |
| Lab scenario | **Lab only** | `C/scenarios/fuel-loss-event.yaml`: 120 L removal (`:329-357`), reporting gap (`:359-386`), sensor and hand readings (`:388-450`), 300 L delivery capped by capacity with 54.02 L refused (`:452-478`, `:507-527`), private expectations (`:491-558`). It runs on the `minimal-fuel-tank` model with forced generator output, not on mini-grid. No product path reads it |
| T021 kernel, T017 | Done (Lab) | `tasks/completed/T021-minimal-fuel-loss-causal-kernel.md`, `tasks/completed/T017-scenario-catalog-fuel-loss-detail.md` |
| T030 reconciliation | **Archived, never built** | `tasks/archive/pre-site-first-2026-10-07/T030-fuel-records-and-reconciliation.md` (AC1–20: records, FuelBalanceWindow, separate uncertainty contributions, no theft, no double count with dispatch) |

### B3. Design: "unexplained fuel" at Kisiwa (mechanism, honesty, changes)

**Chain (every step from stored rows):**
1. **Outcome:** Protect asset & capital.
2. **Driver:** tank volume falls outside generator running and outside any delivery.
3. **Evidence:** a `fuel-balance-1` window assessment, SUPPORTED, whose residual band lies wholly above 0. It reads tank readings, delivery records and modelled use. It becomes an UNEXPLAINED_FUEL Finding when the band's low end exceeds a materiality threshold, declared before any probe.
4. **Lever:** a process control (a sealed tank cap and shift-change dip log; the sensor power restored). It is recorded as a W1 Action from the Finding thread.
5. **Action:** agreed and recorded.
6. **Verify:** family `fuel-residual-within-band-1` (proposed name). The first 3 COMPLETE nights after the action each have a residual band containing 0, and zero tank reporting gaps. Verdicts use the existing vocabulary.

**Authored world** (fixed before any probe; never tuned):
- Kisiwa's existing D0 physics, plus one removal of 120 L (the Lab scenario's figure, reused rather than chosen) over 45 min, 01:00–01:45 local, on one before-night;
- a tank reporting gap 00:50–02:20;
- deliveries of 400 L kept below free capacity, so no capacity spill. The Lab's 54 L capped-delivery false positive (`fuel-loss-event.yaml:517-527`) is excluded from the demo story;
- one hand dip after the gap.

**Uncertainty band** (new reviewed `fuel-balance-1`; T030 AC7: separate contributions plus a reproducible combined bound):
- Tank: a declared Foundation property `fuel-level-sensor-accuracy` (L, with basis), applied to the opening and the closing readings. With ±1 % of 1000 L that is ±10 L each, combined linearly to ±20 L (conservative).
- Delivery: a ticket volume ± declared tolerance (or 0 with basis "ticket").
- Use: low = 0.90 × loaded SFC × kWh, plus 0 for idle; high = 1.10 × (loaded SFC × kWh + idle h × r).
- Residual = opening + deliveries − use − closing, as [low, high]. "Unexplained" only when low > 0 and low ≥ the materiality threshold.
- Rough figures: a night of about 41 L (`DIESEL-D0-probe-results.md:12`) gives a use band of about 37–45 L; with a ±20 L tank band, a 120 L removal reads as about 95–145 L unexplained.

**The idle-burn conflict, and how it stays honest:**
- The simulator's tank drops only by loaded fuel (`mini_grid.py:192-207`). fuel-cost-2 adds idle h × r (FUEL-1 §4.1).
- The reconciliation's use band therefore runs from **no idle burn** (low) to **the generic rate** (high). This is a genuine uncertainty: r is `GENERIC_DEFAULT`, not this generator's figure. The example world sits at the low edge, inside the band, so nothing is tuned and nothing contradicts.
- Under cycle charging Kisiwa idles little (D0 reports idle minutes), so the band widening is small.
- The alternative is a Kisiwa-only simulator idle law (+1.0–1.5, FUEL-1 §5.3). It is not needed for honesty, only for a tighter band.
- The low-side rule must be fixed in the `fuel-balance-1` parameter version before F0 runs.
- **No double count:** the residual never feeds the dispatch fuel consequence, and the two money lines are never added (`v69 :628`, `:131`, `:482`).

**Honesty limits to state on screen and in DS-1:**
- The after-nights are authored without removals. The lever has no physical model, unlike the setpoint lever, which the simulator computes. Verification demonstrates the check; it is not evidence of the control's effect.
- Removals below about 30–40 L a night are inside the band. Sensor error does not accumulate over a window, but use error does.

**Coexistence with the 60 % setpoint story:**
- Physically compatible. A removal changes only the tank stock; dispatch is unaffected unless fuel-limited (1000 L start, about 41 L a night, so G5 holds).
- The setpoint metric reads generator kWh, not the tank, so its verdict is unchanged.
- Cost of coexisting: D0's committed `probe-result.json` (G6) does not include tank events. F0 is a separate probe, and D3's per-day scenarios gain tank events, which changes their digests (Kisiwa-only).
- Replacing the setpoint instead removes D2 (1.75) but still needs D1, D3, D4 and D5.

**Changes needed:**

| Area | Change | Units |
|---|---|---|
| F0 probe (in memory) | mini-grid v6 accepts the authored removal and delivery on `fuel-tank-volume@fuel-tank`; the tank publishes with the gap; hand reconciliation versus the band. **Stop if mini-grid refuses** (a Kisiwa model version is then +0.5–1.0) | 0.5 |
| Simulator | none if F0 passes | 0 (+0.5–1.0 risk) |
| Publication | Kisiwa registered publication version with `fuel-level-sensor`/`fuel-level` and the reporting-gap capability (overlaps D1 pre-flight (a)); the Foundation sensor-accuracy property | 0.5 |
| Records | `FUEL_DELIVERY` and `TANK_DIP` operational records with a tank link, through normal ingestion; migration (0055 after D2's 0054); demo loader | 0.75 |
| Analytic | `fuel-balance-1` window assessment (night 18:00–12:00, reusing D2's window), stored and versioned, with limitations (gap, missing record, conflict between dip and sensor, T030 AC11) | 1.5 |
| Finding | UNEXPLAINED_FUEL Finding kind and consequence (litres band × declared price, own basis); thread; board **Protect** row; Portfolio Protect card line; chain vocabulary | 2.0 |
| Screen | Fuel page window mode (the v69 `:623-630` waterfall filled), Finding detail; MOCK DEVIATION for the Kisiwa window (the mock is a Kobo hour) | 1.0 |
| Verify | `fuel-residual-within-band-1` family and page (reusing D2's night choice and page components) | 0.75 (1.25 without D2) |
| Story data | removal, gap, deliveries, dip and Action in the Kisiwa calendar; handover | 0.75 (on top of D3) |
| Checks | finish rows (FUEL-K1…K5: band reproduces from stored terms; Finding only when low > threshold; no "theft"/"stolen" string, guarded; residual never summed with dispatch money); COH | 0.5 |
| Contingency | | 0.5 |
| **Total, both stories** | | **≈ 8.5 (range 7–11)** |

- **Replace instead:** D-lane 7.0 − D2 1.75 + about 8.5 (+0.5 for the verify family without D2, and the D5 rows) ≈ **13.25** (range 11.5–15), i.e. **+6.25** over today's D lane.
- **E3:** tank events add no runs; Kisiwa readings grow by one 15-min signal (+1–3 min). One Kisiwa scratch prepare is already planned (D3).
- **Risk: high.**
  - A new Finding kind touches chain threads, the board, the Portfolio Protect card, COH and the all-26 audit.
  - The new reviewed uncertainty maths is a first in the product.
  - The simulator's acceptance of tank events is unverified (F0).
  - The fuel chain is serial (records → analytic → Finding → verify, about 5 units), so a third lane barely shortens it.

### B4. Recommendation and effect on totals and dates

- **Recommended: keep the setpoint story (gated by D0); unexplained fuel after the demo.** Total ≈ 124.3 unchanged. The DS-1 spoken line is inside DS-1. Post-demo backlog: "Kisiwa unexplained fuel, ≈ 8.5 (≈ 13 without Kisiwa)", superseding T030 as the plan of record and BL-16's tank half.
- **Do both:** ≈ 124.3 + 8.5 ≈ **132.8**. The demo moves about **+3 more working days** (range 2.5–4), about **+5** in total against the lanes-1–2 plan.
- **Replace:** ≈ 124.3 + 6.25 ≈ **130.5**. The demo moves about **+4–5 working days** against the lanes-1–2 plan.
- **If D0 is NOT MET** (the builder expects this, `DIESEL-D0-probe-results.md:15`): the D lane stops at 0.5 (DIESEL-1 §1.2). Recommended: demo without Kisiwa; unexplained fuel post-demo. The replace path (≈ 13.25 units) is worth it only if the client is diesel-heavy and has raised fuel loss (owner Q1–Q2).
- A detection-only variant (≈ 5 units: no Finding kind, no Action, no verify) is **not offered**, because it breaks the outcome-mechanism rule (no lever, action or verify).
