# Fuel story: why today's example data can't carry it, an honest design, and the idle-fuel probe

- Architect: Claude, 2026-11-07. Binding checked: `.ai/ROLE_CONFIG.md:9`, Architect = Claude since 2026-10-27.
- Owner, verbatim (`.agent/owner-feature-shortlist-answers-2026-11-07.md:6`, `:9`, `:12`):
  - "what is wrong with example data and what does it take to actually inject days and show honest and interesting fuel story"
  - "Fuel is a sensitive cost issue, isn't there no honest way to extend our data to accommodate such operational and cost relevant topic?"
  - "Run the probe"
- Basis: main `26ffe4353`. A design study plus the approved 0.25-unit probe. No product code was written. No DB was created, ticked or prepared, and no suite was run.
- The probe ran the example days through the simulator in memory, the same way `tools/probe_kobo_nights.py` measures them. It used the plan2 sources with no database. The scratch script is outside the repo. No `*_test` DB with the Kobo story was needed.
- These are proposals. Nothing is scheduled until the owner picks.

---

## Part A: Owner summary (plain language)

### What is wrong with the example data today

1. **Kobo is a solar site that rarely needs diesel.** It has 60 kW of solar panels, a 200 kWh battery and a 40 kW diesel generator. On most example days the generator either does not run, or runs for an hour before dawn.
2. **On the days the generator does burn real diesel, it was needed.** On four example mornings the generator runs for 7½ hours and burns about **82 litres** each time (we measured this). It runs because the battery is empty and the sun isn't up. That is necessary diesel, so there is nothing to save.
3. **On the days the generator runs without need, the example data says it burned nothing.** On three example mornings the generator is switched on and then runs for almost 4 hours while the sun alone powers everything. It is idling: switched on, but delivering no power. A real generator burns roughly 1 to 3 litres an hour while idling. Our example data and our fuel calculation both count fuel only for power delivered. So these mornings show "0 litres, 0 USD". That is why the screen says "No fuel cost estimated: the generator was on but delivered no measured power".
4. **So the verified trial finds no fuel saving.** The change we tested (letting the battery go a little lower before the generator starts) does stop the generator idling. We checked that it worked. But the system priced the idling at 0 litres before the change and 0 litres after it, so it reports "no modelled improvement".
5. **Nothing measures fuel at Kobo.** There is no tank-level or fuel-flow reading in the example data, so every litre we show is calculated, not measured.

In short, the example data hides the one honest fuel waste it contains, which is idling. It does this because it leaves out idle fuel. It is not that the data has no fuel story.

### The honest fuel story we can tell (recommended)

**Count idle fuel, using the generator's own datasheet.** Diesel generator manufacturers publish how much fuel the machine burns at no load and at each load level. We declare that figure once for the Kobo generator, with its source. The system then counts:
- loaded running as today, as power delivered × litres per kWh; and
- idling as hours running at no load × the datasheet's no-load litres per hour.

Then the existing mechanism produces the result by itself, with no new example days:

| Step | What the client sees (example data, labelled as such) |
|---|---|
| Outcome | Lower fuel cost |
| Driver | The generator idles in the morning while the sun is already powering the site |
| Evidence | Three mornings: "Generator ran about 3 h 20 min with no load: about 8 L, 10.00 USD of possible extra fuel" (figures at 2.4 L/h, see the probe) |
| Lever | Let the battery go to 25 % instead of 30 % before the generator starts |
| Action | The change is agreed and made |
| Verify | "Target met" on the trial hour, then: "About 2.4 L less diesel in the trial hour, about 3.00 USD at 1.25 USD per litre. Modelled from the generator's datasheet, not measured by a fuel meter" |

What makes this honest:
- The running time is measured.
- The litres per hour come from a named datasheet.
- The diesel price is the one you declared.
- The system does the arithmetic.
- Every screen already says "example data".
- The figures are small, because Kobo is mostly solar. We say that plainly; we do not inflate it.

**Effort:** about **2.0–2.5 units**, including the probe already done. That is 0 new example days, about 1.25 units of product change, 0.5 of checks and 0.25 of review.
**Risk:** medium. It changes a reviewed fuel calculation (as a new version, never in place), Kobo's money checks on three mornings, and the trial's result. It does not touch the mill, the recurring problems or the other Sites. The final demo build takes the same time; one Kobo-only trial build is needed first.

### The other options

- **Add a diesel-heavy stretch to Kobo**, for example a rainy week where the generator is loaded and wastes fuel charging the battery. It would give bigger numbers, but it needs 10 or more new example days and a new kind of change to test. It is about **4–6 units**, and the result is uncertain: four earlier attempts to make a Kobo trial both show a lever and pass its check did not succeed. It could also break checks that pass today (the mill, the recurring problems). Not before the demo.
- **Add a fourth, diesel-hybrid example Site.** It is the cleanest way to show big, CFO-sized fuel numbers, and it keeps Kobo safe. But it means a new Site, all its example days, its screens and a 4-Site Portfolio, so it is about **6–9 units**. Recommended **after the demo**, for a diesel-heavy prospect.

### Measured or calculated fuel?

A CFO will ask "measured or modelled?". A fuel-flow meter is the gold standard. A tank-level sensor sounds measured, but it reads only to a few litres. That is about the size of a morning's idling, so it cannot prove a saving this small. Our calculated figure, from the datasheet × measured running time, is the more defensible one here, as long as the screen says so. The mock-up already plans the next step: "Generator fuel curve: Not declared → Site fuel curve or a fuel-meter test".

### Probe result (approved, 0.25 unit), plain words

- On each "generator kept running" morning the generator ran **230 minutes and delivered no power at all** (07:05–10:55 local). The system calls **200 of those minutes avoidable**. The other 30 are unclear and are never priced.
- The trial hour (09:00–10:00 local) idled the full hour before the change. After the change the generator never started.
- Idle fuel figures, at the declared 1.25 USD per litre:

| No-load fuel use (from a datasheet) | Per idle morning (200 min) | Three mornings | Trial hour saved |
|---|---|---|---|
| 1.2 L/h (low end: a typical datasheet's load table extended to zero load) | 4.0 L · 5.00 USD | 12 L · 15.00 USD | 1.2 L · 1.50 USD |
| 2.4 L/h (about a fifth of full-load fuel, a common rule) | 8.0 L · 10.00 USD | 24 L · 30.00 USD | 2.4 L · 3.00 USD |
| 3.3 L/h (generic design-software default for a 40 kW set) | 11.0 L · 13.75 USD | 33 L · 41.25 USD | 3.3 L · 4.13 USD |

- **Is it worth building?** Yes, if you accept small numbers. It turns three "0 USD" mornings into real idle litres. It also turns the verified trial into a verified fuel saving, closing the whole problem → change → checked → litres-and-dollars loop. And it needs no new example days. It is not worth building if the demo needs a large fuel figure. Then the fourth Site, after the demo, is the answer.

### Your decisions

1. **Build idle fuel now (about 2.0–2.5 units, before the demo script)?** Options: yes / no / after the demo.
2. **Which generator datasheet do we use for the no-load figure?** Give us a make and model, or a datasheet you trust, and we take its no-load figure (or extend its load table to zero). If you have none, should we use the generic design-software figure (3.3 L/h), clearly labelled as generic?
3. **Is it OK that the example data's own fuel tank does not include idle fuel, while the system's estimate does?** Nobody sees the example tank, because there is no tank reading at Kobo. Fixing the example data too costs about 1 more unit and rebuilds every Kobo day. Recommended: leave it, and say so in the "Why?" line.
4. **Put the fourth diesel-hybrid Site on the post-demo list** as the "big fuel numbers" story for diesel-heavy prospects?
5. **Shortlist items 1–4 (mill dollars, mill on the board, Portfolio value lines, money wording)** are still open. Idle fuel fits with them (see B6). Approve them together?

---

## Part B: Technical basis

### B1. Diagnosis, with references

**Site sizing.** Template `config/site-templates/kobo-mini-grid-60kw.yaml`:
- PV 60 kW (`:58-70`), inverter 50 kW (`:71-84`);
- battery 200 kWh with 30 % reserve (`:85-104`), PCS ±30 kW at 95 % (`:105-128`);
- generator 40 kW, SFC 0.3 L/kWh, minimum runtime 30 min, start 35 %, stop 90 %, start delay 5 min (`:129-164`);
- tank 400 L (`:165-176`).

Sanity check: 40 kW × 0.3 L/kWh = 12 L/h at full load, which is ordinary for a 50 kVA prime set.

**Generator hours per kind of day.** Measured in memory on mini-grid v5/v6 at 5 min, 06:00–14:00 local unless noted. Sources: this probe, and `backend/conversions/kobo-night-handover-v1.json` for the nights.

| Day kind (calendar `backend/conversions/demo-story-days-v3.json`) | Days | Generator running | Delivered | Fuel (linear law) | Classification |
|---|---|---|---|---|---|
| `normal` / `overcast` / `late` (`kobo-s3-dispatch-necessary-run`) | S-28, S-21, S-3, S-1 | 455 min | loaded throughout | **82.35 L** (probe) | NECESSARY 0/455/0 (`.agent/DEMO-SPARSE-trial-probe.md:16`) |
| `overuse`, `trial-before` (`kobo-mini-grid-reserve-trial`) | S-14, S-7, S | 230 min, 07:05–10:55 local | **0 kWh in every step** (probe) | 0 L | 200 Candidate / 30 Indeterminate (`DEMO-SPARSE-trial-probe.md:21`) |
| `trial-after` (reserve 25 %) | S+1 | 0 (v5 start threshold 30 %, min SOC 34.6 %) | 0 | 0 L | none |
| steady night after the mill (`kobo-night-early`) | S-9, S-8, S-6, S-5 | 55 min, 05:05–06:00 | about 0 | 0.0 L | needed (`build-sheet-DD-1.md:255-261`) |
| steady-before night | S-19…S-11 (not S-13/S-20) | 120 min, 04:00–06:00 | 3.244 kWh | 0.973 L | needed; O15 "about 15 minutes" in DS-1 (`build-sheet-DD-1.md:2459`, `review-packet-DD-1b2b.md:21`) |
| steady / mill days 06:00–24:00 | | 0 | 0 | 0 L | `kobo-night-handover-v1.json` `full_days` |

**Missing fuel signal.**
- Kobo has 0 `fuel_level` rows (`build-sheet-DD-1.md:1934`).
- The fuel balance needs five terms and is never SUPPORTED (`mini_depth/rules.py:760`).
- The simulator keeps a tank stock (`simulator/assetops_simulator/packs/mini_grid.py:192-207`), but no publication maps it.

**Idle-burn rule (BL-16).**
- The fuel law is linear on accepted energy, with no idle or start fuel (`mini_grid.py:24-27`, `:85-89`, `:732-734`).
- The product mirrors this. `fuel-cost-1` quantity high = 1.10 × Σ(P × h × SFC) over observed Candidate time (`backend/assetops_backend/financials/fuel_cost.py:13-22`, `:57-81`, `:398`). At P = 0 the result is 0.
- Consequence: S-14, S-7 and S are PRICED at 0 L, 0.00 USD (`review-packet-DD-1b2b.md:25`), with copy `COST_ZERO` (`site_outcomes/mini.py:64-65`).
- The generator idles because PV covers the load and fills the PCS's 30 kW charge limit, while the 90 % stop setting keeps the generator requested. The scenario's own text says so: "keeps the generator requested, unloaded, for most of the morning" (`config/scenarios/kobo-mini-grid-reserve-trial.yaml` purpose). In code, generator charging happens only from what is left after load and PV (`mini_grid.py:720-733`), and the RUNNING-at-0 note is at `:851-852`.

**Reserve-trial result.**
- `trial-fuel-comparison/1` computes fuel = SFC × generator kWh per window (`financials/trial_fuel_comparison.py:108-119`). It gives MODELLED_IMPROVEMENT only if the nominal change is > 0 (`:133`).
- Baseline 0 kWh and later 0 kWh give 0 − 0, so the result is MODELLED_NO_IMPROVEMENT (`DEMO-SPARSE-trial-probe.md:67`, `tools/demo_combined_finish.py:40`).
- The verdict itself is VERIFIED, `TARGET_AND_GUARDRAILS_PASS`: Candidate seconds in the 06:00–07:00 UTC hour went from 3600 to 0 (`actions/verification_rules.py:603-656`).

**Correction to the shortlist.** `.agent/feature-shortlist-2026-11-07.md:12` says the generator "runs for only about 15 minutes on some mornings". That is the DS-1 night line. The full picture is in the table above: Kobo does burn about 82 L on four needed mornings, and the avoidable mornings idle for 230 min at 0 kW.

### B2. The probe (approved 0.25), method and result

**Method.**
- `kobo_draft` (`host/tests/kobo.py`) with `run_to_end` (`execution_adapter`), as `tools/probe_kobo_nights.py:78-127` does.
- Template Site, mini-grid v5, 5 min, interval 03:00–11:00Z.
- PYTHONPATH pinned to plan2's `backend/contracts/simulator/field/gateway/host`, because the shared `.venv` resolves editable installs to the other checkout.
- Per step: generator state, and fuel delta, which equals the generator energy × 0.3.

**Results.**
- `kobo-mini-grid-reserve-trial` (30 %): running 230 min, loaded 0 min, idle 230 min, span 07:05–10:55 local; SOC 42.5 → min 34.6 → 100; fuel 0.0 L.
- `kobo-s3-dispatch-necessary-run`: running 455 min, loaded 455 min, idle 0; fuel 82.351 L; SOC 40 → 30 → 30.
- Candidate span 04:35–07:55Z = 200 min (`DEMO-SPARSE-trial-probe.md:21`). Every 5-min power mean in it is 0 kW, because the stored rows are PRICED with quantity AVAILABLE at 0 L (`review-packet-DD-1b2b.md:25`). Coverage therefore already passes `fuel_cost.quantify` (`:352-354`).
- Trial hour 06:00–07:00Z (`demo-story-days-v3.json` `trial.window_hour`):
  - baseline: 12 of 12 slots RUNNING at 0 kWh;
  - later: 0 slots RUNNING;
  - feeder demand 15 kWh in both (residential 10 kW + clinic 5 kW + mill 0 kW, scenario timeline), so the comparability band passes as it does today.

**Idle figure needed.** No-load fuel rate r in L/h for the 40 kW set, declared as a Foundation fact with its source. Three datasheet-style assumptions:
- **1.2 L/h:** a typical 50 kVA datasheet's 25/50/75/100 % fuel table extended linearly to 0 % (the Willans-line intercept, about 10 % of full-load flow).
- **2.4 L/h:** about 20 % of full-load flow (12 L/h). A common field rule for no-load diesel use.
- **3.3 L/h:** the generic fuel-curve intercept used by common mini-grid design software (about 0.08 L/h per kW of rating × 40 kW).

None is Kobo-specific. The owner's named datasheet decides, and the value is never chosen to hit a result.

**Resulting figures.** Price 1.25 USD/L, `demo-diesel-price-publications.json` v1; only v1 is published at Kobo (`tools/demo_combined_kobo.py:137-145`). Upper = 1.10 × nominal if fuel-cost-2 extends the reviewed allowance to the idle term.

| r (L/h) | Per Finding, 200 min: nominal (upper) | S-14 + S-7 + S | Trial hour: baseline − later | As a rate per kWh of demand (15 kWh) |
|---|---|---|---|---|
| 1.2 | 4.00 L, 5.00 USD (4.40 L, 5.50) | 12.0 L, 15.00 USD | 1.20 L, 1.50 USD | 0.10 USD/kWh |
| 2.4 | 8.00 L, 10.00 USD (8.80 L, 11.00) | 24.0 L, 30.00 USD | 2.40 L, 3.00 USD | 0.20 USD/kWh |
| 3.3 | 11.00 L, 13.75 USD (12.10 L, 15.13) | 33.0 L, 41.25 USD | 3.30 L, 4.13 USD | 0.275 USD/kWh |

The 30 Indeterminate minutes (07:05–07:35) are never priced (`fuel_cost.py:481-482`). Running at 0 kW over the whole morning is 230 min.

**Verdict.** Defensible, provided:
- the screen names the basis (measured running time × declared datasheet no-load rate × declared price, modelled);
- the rate has a source;
- no annualising.

Worth 1.5–2 units for the Findings alone, and about 2.0–2.5 with the trial's priced result, which is the part that completes the VERIFIED loop.

### B3. Options

Common rules for every option:
- money only from evidence and declared prices;
- authored causes only: weather, load, start state;
- no generator output is authored;
- "example data" stays on every surface;
- the mock is the layout spec, and any deviation is labelled MOCK DEVIATION.

#### Option A (recommended): idle fuel on the existing Kobo days (BL-16, product side)

**Fuel signal.**
- Modelled litres: loaded intervals as today (P × h × SFC), plus idle intervals (P = 0 while RUNNING) × r.
- Running time is evidence: power means at 0 kW over observed Candidate segments for Findings, and the sampled `generator_state` per 5-min slot for trial windows (`verification_rules.py:472-480`).
- More defensible to a CFO than a tank sensor at these quantities. A 400 L tank read to ±1–2 % (±4–8 L) cannot resolve a 4–11 L morning. Only a flow meter could. That is the mock's own next step (v69 `:426` "Site fuel curve or a fuel-meter test").

**Idle fix.**
- New reviewed model `fuel-cost-2`. `fuel-cost-1`'s parameter block is immutable (`fuel_cost.py:55-56`).
- Idle term only where the interval mean is exactly 0 kW, so there is no double count with SFC at load. Formula: high = 1.10 × [Σ_loaded P·h·SFC + Σ_idle h·r].
- New Foundation property `generator-no-load-fuel-rate` (L/h, with source), read from the as-accepted Foundation revision under the same validity rules as SFC (`fuel_cost.py:356-391`).
- New `trial-fuel-comparison/2`:
  - window fuel = SFC × generator kWh + r × RUNNING-and-0-kWh slot hours;
  - stores `fuel_change_l` and a `priced_total` {amount = baseline cost − later cost, currency, basis "trial hour, modelled"}, which `outcomes/credit.py:56-71` already expects ("No stored priced total exists today");
  - the per-kWh rate stays as stored.
- The simulator is unchanged. The Lab law stays 0 L idle (owner decision 3), so there is no re-baseline.

**Authored days.** None. One Foundation fact is declared in `configure_at` (`tools/demo_combined_kobo.py`), recorded before S-28 like the price.

**Product and analytics changes.**
- `financials/fuel_cost.py`: v2 beside v1, and the consequence store's version selection.
- `financials/trial_fuel_comparison.py` v2, and `actions/verification.py:995-1026` (`_cost_check`): window running seconds and r.
- Foundation parsing: `sites/foundation_parsing.py`, plus the template or Site declaration.
- Copy:
  - `COST_ZERO` (`site_outcomes/mini.py:64-65`) becomes an idle line;
  - board `cost_line` (`site_outcomes/board.py:495-510`) shows L and USD from `priced_total`, not only the rate;
  - Assure `VERIFIED_WITH_COST` (`mini.py:986-988`);
  - Portfolio `recovered` (`estate/portfolio.py:670-680`) is read per basis (see B6).

**Screens (v69 as spec).**
- Finding fuel panel: v69 `:459` "Associated fuel … Modelled; not fuel-meter measurement" and the worked formula `:468-472`. Add an idle line: "3.33 h × r L/h (datasheet no-load)".
- Kobo Financials, assumptions in use: v69 `:479-481`. Add the no-load rate with its source.
- Readiness: v69 `:426` "Generator fuel curve" changes from "Not declared" to "Declared: no-load r L/h, source …". Also v69 `:259`.
- Verification: v69 `:498-505`. Add a fuel result line under "Target met". MOCK DEVIATION label: the mock shows no money on this page.
- Site board Cost row and Assure row.
- Portfolio "Verified value recovered": v69 `:129`, as one line per basis.

**Checks and finish rows.**
- O16/MONEY-B (`build-sheet-DD-1.md:2100`, `:2455`): S-14, S-7 and S become PRICED with quantity > 0. Expected values are computed from r, never typed from a run.
- `PROBE_CHOSEN` cost_state becomes MODELLED_IMPROVEMENT with its nominal (`tools/demo_combined_finish.py:40`).
- COH chain-coherence: `tools/checks/chain_coherence.py`.
- New unit tests: v1 and v2 side by side; an idle-only interval; a loaded-only interval that must equal v1; a mixed interval; a missing r giving SFC-only plus a stated limitation, never a guess.

**Effect on E3.**
- Same day list, so the prepare time is unchanged (about 1 h, 3 h cap).
- Before E3: one Kobo-only scratch prepare (`--sites kobo`) in an own `*_test` DB to confirm the stored figures equal B2's table. Then drop it.

**Risk to what passes now.** Medium.
- Touches the Kobo fuel rows on three days, the ACT-001 cost check, board and Assure copy, Portfolio recovered value, COH and MONEY-B.
- Does not touch: the mill (no fuel claim, `build-sheet-DD-1.md:1934`), recurrence, gap counts, Cold, EV, or any scenario or handover digest.
- Night labels: "idle fuel is not modelled, so this hour shows no fuel" (`build-sheet-DD-1.md:261`) stays true of the example data. Those nights are NECESSARY and carry no fuel line. Product "Why?" copy adds "the system estimates idle fuel only where running was avoidable". The scenario text is not edited, because that would change digests.

**Size.**

| Part | Units |
|---|---|
| Probe | 0.25 (done) |
| Data | 0.1 |
| Product | 1.25: fuel-cost-2 0.4, tfc/2 + priced_total 0.45, Foundation fact 0.15, copy 0.25 |
| Tests | 0.4 |
| Review | 0.25 |
| E3 rows | 0.1 |
| **Total** | **about 2.35, range 2.0–2.5** |

#### Option (i): extend Kobo with a diesel-heavy stretch and a loaded-generator lever

**Story.**
- A rainy-season week where mornings are overcast and evenings carry extra load (a water pump or night mill shift).
- The generator runs loaded and, with the 90 % stop setting, charges the battery at night that the next day's sun would have filled. That loaded fuel is avoidable.
- Lever: stop setting 90 % → 70 %. This is exactly v69's ACT-048 / CHG-019 (`:335`, `:431-433`). Alternatives: shift the night load to solar hours, or reserve 30 → 25 %.

**Fuel signal.**
- Modelled, as in A. The numbers are larger: tens of litres a day, like the 82 L necessary mornings.
- A measured signal would need a tank publication and BL-16 in the simulator. Otherwise the Lab tank would contradict the product. That is +1.0 and a re-baseline of every Kobo day.

**Idle fix.** Not required for loaded waste, but A's idle term is still advisable, because stopping earlier also removes idle time.

**Authored days.**
- About 10–14 new days: a before week and an after week of comparable weather, with night and rest complements and handover probes (DD-1a style, `tools/probe_kobo_nights.py`).
- An assessed S-1-style day for any window before 06:00Z (`actions/verification.py:86-93`).
- A window clear of open bounds (`DEMO-SPARSE-trial-probe.md:116`).

**Product changes.**
- A stop-setting Action family. Today only the reserve trial exists (`actions/verification.py`, `reserve_trial`). Alternatively, re-target the reserve family.
- The day-level fuel ledger is optional.

**Screens.** As A, plus the v69 Change (`:431-433`) and Verification (`:498-505`) pages for a stop-setting change.

**Checks.** New story rows; every Kobo calendar-derived count (SP-3 gap g = 24, `DEMO-SPARSE-trial-probe.md:124-125`), the mill's 3+3 complete-day selection, recurrence and the COH expectations all change.

**Effect on E3.** More days, so roughly +15–25 min prepare. At least two partial probe prepares beforehand.

**Risk.** High. Four earlier trial candidates failed "shows the lever and VERIFIES" (`DEMO-SPARSE-trial-probe.md:63-126`). The added days sit inside the mill's before and after windows (mill change S-9) and the recurrence span.

**Size.**

| Part | Units |
|---|---|
| Probe | 0.5–1.0 |
| Data | 1.5–2.0 |
| Product | 1.0–2.0 |
| Tests | 0.5 |
| Review | 0.5 |
| **Total** | **4–6**, uncertain outcome |

#### Option (ii): a fourth "diesel-hybrid" Site

**Story.**
- An island or off-road site where diesel is the main source: for example 20 kWp PV, 60 kWh battery, a 60 kW set, and night-heavy load (water pumping, cold store).
- The generator runs most nights, loaded, and idles after the battery fills.
- Lever: stop setting, load scheduling of the pump into solar hours, or reserve.
- Numbers are CFO-sized: hundreds of litres a month.

**Fuel signal.**
- Modelled from the datasheet curve (no-load intercept plus slope), as in A.
- Optionally a published tank level with a simulator idle law (BL-16 inside the new Site's own model version, so Kobo is not re-baselined). This is the only option where a "measured tank drop agrees with modelled" panel (v69 fuel balance `:623-630`) becomes possible, because daily burn exceeds sensor resolution.

**Idle fix.** A's product term, plus a new simulator model version for the new Site only.

**Authored days.** A full calendar for the Site (about 15–20 days), its template, import, configure and price, and a new `demo_combined` child.

**Product changes.**
- 4-Site Portfolio and estate reads.
- Site navigation.
- The Site-type board (shared `board.py`).
- Layout audit recaptures (all-26 index).
- MOCK DEVIATION: v69 shows 3 Sites (`:131` "3 priority sites").

**Checks.** New child finish rows. Portfolio tests (`test_ch6b2_portfolio_cards.py`, `estatePortfolio.test.tsx`) and COH need new expected values.

**Effect on E3.** +20–30 min prepare. Rehearsal prepares are needed.

**Risk.** Kobo checks are isolated (low risk there). Medium-high for Portfolio and estate checks, layout captures and schedule.

**Size.**

| Part | Units |
|---|---|
| Probe | 0.5 |
| Data | 2.5–3.5 |
| Product | 2–3 |
| Tests | 0.75 |
| Review | 0.5–0.75 |
| **Total** | **6–9** |

#### Recommendation

1. **Option A before the demo**, if owner decisions 1–3 allow it.
2. **Option (ii) post-demo**, as the diesel-prospect story. It reuses A's fuel-cost-2 and tfc/2 unchanged, so A is not throwaway.
3. **Option (i) not recommended.** It has the most risk to passing Kobo checks for numbers that (ii) shows better.

### B4. Outcome mechanism (Option A), each step from stored rows

1. **Outcome:** Optimize cost (`.agent/owner-feature-shortlist-answers-2026-11-07.md` context; four outcome categories).
2. **Drivers:** avoidable generator running while PV serves the load. This is dispatch Candidate time, stored segments.
3. **Evidence:** three SUPPORTED Findings (S-14, S-7, S) with fuel-cost-2 consequence rows. Quantity = 1.10 × (200/60 h × r); price 1.25 v1.
4. **Lever:** battery reserve 30 → 25 %. The v5 start threshold falls to 30 % (`mini_grid.py:1142-1155`).
5. **Action:** ACT-001 agreed and applied on S (`tools/demo_combined_kobo.py`).
6. **Verify:**
   - Verdict VERIFIED (target 3600 → 0 s, guardrails pass).
   - Cost check `trial-fuel-comparison/2`: MODELLED_IMPROVEMENT with `fuel_change_l` = r × 1 h and `priced_total` = r × 1.25 USD.
   - Label stays "Modelled change after the trial · not realised savings" (`trial_fuel_comparison.py:26`).
   - Intervention cost "no direct cost declared" (`verification.py:49`, `:1025`).

### B5. Pre-flight literals (to pin before any build)

- **Foundation fact:** key `generator-no-load-fuel-rate`, unit L/h, value r, source text naming the datasheet (owner decision 2), and recorded time (same instant as price v1).
- **Finding line:** "Generator ran {h} h {m} min with no load: about {L} L, {USD} USD of possible extra fuel · modelled from the datasheet no-load rate {r} L/h · not measured".
- **Verdict line:** "About {L} L less diesel in the trial hour, about {USD} USD at {price} USD per litre · modelled from the generator's datasheet, not measured by a fuel meter".
- **Rounding:** litres to 0.1, USD to cents. Exact Fraction is stored.
- **Missing r:** v2 equals v1 plus the limitation "No no-load fuel rate is declared, so idle running is not costed". Never a default.

### B6. Fit with shortlist items 1–4 and the "no combined savings total" rule

- **Item 1, mill dollars:** independent files (`verification_families.py`, `SiteMillVerification.tsx`). It runs in parallel with A.
- **Item 2, mill on the board (BL-45):** shares `site_outcomes/board.py` with A's cost line. Same lane, or sequence A's copy change after item 2.
- **Item 3, Portfolio verified value lines:**
  - With A there are two positive verified values: the mill's estimated sales (kWh × declared productive price, per day) and ACT-001's modelled fuel saving (litres and USD per trial hour).
  - `outcomes/credit.py:74-80` `recovered_value` sums credited amounts per currency. Once A stores a `priced_total`, that sum is live.
  - Item 3 must list one line per basis, and `recovered_value` must not add the two.
  - Item 3 becomes more valuable with A. It is no longer "one positive line plus 'no fuel saving found'".
- **Item 4, BL-48 wording:** independent.
- **The rule still holds, and matters more.** v69 `:131` "Distinct consequence categories · no combined savings total" and `:482` "lines with different bases are not added together" both apply. Fuel (modelled cost, per trial hour) and mill (estimated sales at a declared price, per day) differ in basis, unit of time and beneficiary. They are never added. Nothing is annualised.
- **Suggested order if all are approved:**
  - Lane 1: item 1, then item 3.
  - Lane 2: item 2, then A's board copy.
  - A's backend (fuel-cost-2, tfc/2) runs in parallel with item 1.
  - Item 4 any time.
  - Then one Kobo-only scratch prepare, then DS-1, then E3.
  - Total about 3.0 + 2.35 ≈ 5.4 units.
