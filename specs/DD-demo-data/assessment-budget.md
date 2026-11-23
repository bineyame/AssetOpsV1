# DD: budget check for Lakeside (and a brief check of cold and EV)

Architect (Claude, DD lane), 2026-11-23. Asked by the owner (`owner/owner-demo-data-answers-2026-11-22.md`
§"Budget check": "have the architect check the budget"). Read-only analysis: no run, no database touched.

Read: `M` (`Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml`) Lakeside `period.plan`,
`history.rules` plan block (line 2160), cold and EV plan blocks; `history.json` plan leaves; `derived-values.json`
Lakeside plan nodes; `world/history.py` (`per_day`, `plan_value`); on `task/DD3b-mini-plant`: `M` rev 16.20 actual
leaves, `config/world/fuel-leaves.json`, `config/world/fuel-notes.json`; D-DD.92, D-DD.125, D-DD.130, D-DD.131,
D-DD.144, D-DD.147, D-DD.163; the design pack for any budget rationale (none found).

## 1. How the Lakeside budget was made

| Leaf | How it was set | Rule or typed |
| --- | --- | --- |
| October `plan.diesel_l` (Kobo 700, Kisiwa 2,300, Mto 300 L) | typed in `M` `period.plan` beside the typed actual | typed |
| October `plan.diesel_cost` (875.00 / 2,990.00 / 375.00) | litres x `prices.diesel_usd_per_l` (1.25 / 1.30 / 1.25) | identity on a typed leaf |
| plan necessary / candidate / unexplained litres | all plan litres necessary; candidate 0, unexplained 0 (`derived-values.json`) | structure default |
| October `plan.billed_kwh`, `om`, `staff` | typed; revenue = kWh x tariff | typed, not fuel-dependent |
| July-September plan (`history.json`) | October's plan x days in month / 31 (`per_day`; om, staff `fixed`) | rule on the typed October figure |
| Plan contribution (1,445.00 / -65.00 / 915.00; Portfolio 2,295.00) | revenue - fuel - O&M - staff | identity |

**Does it rest on the old fuel figures? Yes.** Each plan litre figure is the old typed actual minus the variance the
story was designed to show:

| Site | Old typed actual | Designed fuel variance (bridge lines) | Plan |
| --- | --- | --- | --- |
| Kobo | 1,180 L | 330 candidate + 30 evening growth + 120 unexplained = 480 L | 700 L |
| Kisiwa | 2,400 L | 80 rainy-month necessary + 20 unexplained = 100 L | 2,300 L |
| Mto | 320 L | 20 evening necessary | 300 L |

No plant, record or budgeting rule produced 700 / 2,300 / 300 L. D-DD.147 kept them as "the operator's budget", but
that was a label, not a derivation. Now that consumption is the declared plant's (Kobo 634, Kisiwa 904, Mto 32 L in
October; Jul-Sep about 797, 3,237 and 0 L), an operator who budgeted 2,300 L a month for Kisiwa would have seen it
under-run by about half or more every month since July. No operator keeps that budget. The +$2,135.30 headline is
therefore mostly the gap between an invented budget and the simulated plant, not a performance result. This is the
class D-DD.92 fixed on the actual side (two figures for one quantity, the typed one not loyal to the operating
world), still open on the plan side.

**Cold (after D-DD.144): keep.** Plan `kwh` is the meter-fitted model (1,304 + 0.0554 x planned crate-days, fitted on
the metered Jul-Sep room-months) at the planned occupancy, whole kWh (1,716 / 1,785 / 1,854); energy = kWh x 0.20.
Planned crate-days are occupancy targets x capacity; staff and maintenance are fixed contract costs. A rule from
measured data, which is how an operator would budget. Nothing rests on an invented consumption.

**EV (after D-DD.125): keep.** Plan kWh is the roster's energy (Embakasi and Kasarani plan kWh equal the energy
delivered); peak share 30 %, peak 450 kW and departures required are operator targets and roster facts; Ruiru's plan
is a bill total (12,600.00 against 12,580.32). D-DD.125 restated November capacity, not the plan. These are targets
an operator sets, not guesses of a simulated quantity.

## 2. Proposed budgeting rule (Assumed)

**Run-rate budget:** each Site's monthly fuel budget = the average monthly fuel consumed in the last booked quarter
(July-September: tank at 1 Jul + litres delivered - tank at 1 Oct, over 3 months), plus a 10 % contingency,
whole litres (half-even), priced at the Site's declared diesel price. July-September plans follow by the existing
`per_day` rule. Labelled **Assumed**: "Budget set from last quarter's fuel use plus 10 % contingency (assumed
operator practice)". The world has no prior year, so the first booked quarter stands in for it, stated as such.

Why this rule:
- It is the commonest way an operator budgets a running cost: last period's actuals plus an allowance. It needs only
  records the operator holds (dips and deliveries). Design-stage fuel forecasts come from a dispatch model such as
  HOMER on a typical year ([IRENA and FS-UNEP, hybrid mini-grids, 2015](https://www.irena.org/-/media/Files/IRENA/Agency/Publication/2015/IRENA_FS_UNEP_Hybrid_Minigrids_2015.pdf));
  fuel is the dominant OPEX line of hybrid mini-grids
  ([SEforALL mini-grid CAPEX/OPEX, 2024](https://seforall.org/system/files/2024-08/CAPEXOPEX%20PPT_final.pdf)).
  I found no published source stating a standard monthly budgeting method for operating mini-grids; "run-rate
  plus contingency" is general budgeting practice, so the rule is labelled Assumed, not cited as an industry norm.
- It is the same class as the cold plan (D-DD.144): a budget computed from last quarter's measured data (W6).
- It adds no plant figure and needs no new run: the run already made gives the quarter (`fuel-leaves.json` tank at
  1 Oct, `fuel-notes.json`). Neither the 10 % nor the rule was chosen for its headline; the 0 % case is shown.

Resulting October figures (projected from the DD3b run on `task/DD3b-mini-plant`; the tool prints the served ones):

| Site | Jul-Sep fuel used | Budget litres (avg x 1.10) | Budget fuel | Plan contribution | Actual contribution | Against plan | Today (typed plan) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Kobo | 797.2 L | 292 L | 365.00 | 1,955.00 | 1,565.50 | **-389.50** | +120.50 |
| Kisiwa | 3,237.5 L | 1,187 L | 1,543.10 | 1,381.90 | 1,694.80 | **+312.90** | +1,759.80 |
| Mto | 0 L | 0 L | 0.00 | 1,290.00 | 1,170.00 | **-120.00** | +255.00 |
| Portfolio | | | 1,908.10 | 4,626.90 | 4,430.30 | **-196.60** | +2,135.30 |

Portfolio split: Grow (revenue) -97.00, unchanged; Optimize (fuel) -99.60 (actual 2,007.70 against 1,908.10).
At 0 % contingency: Kobo -422.00, Kisiwa +172.50, Mto -120.00, Portfolio -369.50.

What the result says, plainly: Kobo burns more than last quarter's run-rate (overcast October plus the candidate
running the story is about); Kisiwa burns less than its run-rate; Mto bought and budgeted no fuel and burned 32 L
after its inverter failed on 28 Oct. The Portfolio is about $197 behind plan, close to the -$852 the old story showed
in sign, for a reason the screen can now explain.

Known limits, stated: Mto's zero budget is what the rule gives (no fuel used in the quarter), not an operator's
judgement about a genset site; a run-rate budget carries no seasonality (Kobo's sunny July-August pull its budget
down). Both are visible on the Fuel line as Assumed.

## 3. Alternatives

- **(a) Keep the typed plan** (D-DD.147 as written). Headline +2,135.30. It must then be described honestly: a budget
  set before the fuel was simulated, about 2.5 times what the plant burns at Kisiwa and 9 times at Mto. No change, 0 u.
- **(b) Engineering budget:** expected burn of the declared plant on a typical month (season-mean sun, booked load) x
  declared price + contingency, the design-tool method. More defensible for a new Site, but it needs a new pure-run
  mode and a declared "typical sun", an Assumed input that would invite tuning. About 2.5 u; not computed here.

## 4. DRAFT ruling, awaiting owner

**D-DD.166 (DRAFT, awaiting owner). The Lakeside fuel budget is the run-rate rule of §2, labelled Assumed; the typed
plan litres leave `M`. Cold and EV plans stand.** (Amends D-DD.147's "plan leaves stay the operator's budget" for the
fuel leaves only; W6 class with D-DD.92 and D-DD.144; nothing fitted.)
- *Rule.* October `plan.diesel_l` = round_half_even(1.10 x (tank 1 Jul + Jul-Sep deliveries - tank 1 Oct) / 3);
  `plan.diesel_cost` = litres x declared price; contribution and variance by `M`'s identities; July-September by
  `per_day`. Plan necessary = plan litres, candidate and unexplained 0, as today. `M` carries the basis string of §2
  and the class ASSUMED on the fuel plan line.
- *Where the figure comes from.* `tools/dd3_pure_run.py --leaves` also prints the plan litres from the run's ledger
  (quarter consumption recorded in `fuel-leaves.json`); a test asserts `M` equals the tool (D-DD.93). Never typed.
- *What follows.* Bridges by their stated formulas (D-DD.131: necessary lines against the new plan necessary), the
  Portfolio totals, `history.json`, `derived-values.json`, `missing-records.json`, mock fixtures (D-DD.30 chain), the
  DDR expect file's headline literals (re-pinned to served values, D-DD.163's procedure) and the anchored-figure doc
  sweep. A served figure that differs from this table by more than money rounding stops for the Architect.
- *Also to confirm in pre-flight.* `history.json` July-September *actual* litre leaves (Kisiwa necessary about
  2,333 L) are still the history generator's family (D-DD.130 kept them). If any reader serves them, they are the
  same class and stop for the Architect.
- *Size and place.* DD3d.5, after DD3d.4 so the screen literals re-pin once: tool and test 0.5, `M` restatement and
  regeneration 0.5, re-pins, DDR expect file and doc sweep 0.75 = **+1.75 u**; DD 58.0 -> **59.75 u**. Alternative
  (a) 0 u; alternative (b) about +2.5 u.
- *Owner.* Asked to choose: default run-rate (Portfolio about -197 behind plan), (a) keep (+2,135.30), or (b)
  engineering budget (not computed). Until the owner answers, nothing is built; D-DD.147 stands.
