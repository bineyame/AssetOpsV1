# vNEXT fixture mapping

**Rev 2 (fix round):** `fixtures.js` no longer contains the manifest's private `oracle:` block (stripped by `tools/gen_fixtures.py`, rule R1). Figures below reflect the corrected manifest (EV maintenance and super-off-peak tier, Harvest and Metro coverage, Kasarani 3-night stop-gap).

Every figure on the 36 decision screens is read at runtime from `MANIFEST` in `fixtures.js`. `fixtures.js` is **generated** from `../demo-site-scenario-manifest.yaml` by `python3 tools/gen_fixtures.py` (the file header carries the manifest's sha256). No figure is typed into a page template except where listed under "Derived" with its arithmetic, or under "Text constants" below. Every money figure on screen is also a button that opens the evidence drawer, whose last section ("Fixture reference") prints the manifest path it was read from.

The 110 v7.0 screens keep their own v7.0 fixture data (earlier demo estate); none of their figures changed.

Path shorthand: `L` = `tenants[0]` (Lakeside Power), `H` = `tenants[1]` (Harvest Cold Network), `M` = `tenants[2]` (Metro Bus Depots). Sites: `L.sites[0..2]` = Kobo, Kisiwa, Mto; `H.sites[0..2]` = Mwea, Thika, Kirinyaga; `M.sites[0..2]` = Embakasi, Kasarani, Ruiru. `{s}` = any site.

## 1. Decision home (`#/decide-{op}`)

| On screen | Source |
|---|---|
| Plan / actual / against plan contribution: $2,295 / $1,443 / −$852 (Lakeside); $1,716 / $946 / −$770 (Harvest) | `L.portfolio.plan_contribution`, `.actual_contribution`, `.variance`; same for `H` |
| Plan cost / actual cost / over plan: $38,520.80 / $41,705.12 / $3,184.32 (Metro; energy + demand + maintenance at every depot) | `M.portfolio.plan_cost`, `.actual_cost`, `−variance`; per site `{s}.period.plan.total`, `.actual.total` (Embakasi 19,540.80 / 22,744.80; Kasarani 5,880 / 5,880; Ruiru 13,100 / 13,080.32) |
| Departures met 1,302 of 1,302; $32.03 per departure | `M.portfolio.departures_met`, `.departures_required`, `.cost_per_departure_actual` |
| Per-site plan / actual bars | `{s}.period.plan.contribution`, `.actual.contribution` (EV: `.plan.total` or `.plan.energy_cost`, `.actual.total` or `.actual.energy_cost`) |
| Coverage "91.5% of costs from recorded invoices ($7,545 of $8,245)" | `L.portfolio.coverage.cost_recorded_share` (0.9151 shown 91.5%), `.cost_recorded_usd`, `.cost_total_usd` |
| Coverage "97.8% … ($3,562 of $3,642); Thika's maintenance cost ($80) is estimated" (Harvest) | `H.portfolio.coverage.*` (share 0.9780 shown to 1 decimal); estimated line from `H.sites[1].period.coverage.maint: ESTIMATED` |
| Coverage "99.3% … ($41,405.12 of $41,705.12); Kasarani's maintenance cost ($300) is estimated" (Metro) | `M.portfolio.coverage.*` (share 0.9928 shown as 99.3%; the evidence drawer shows 99.28%); estimated line from `M.sites[1].period.coverage.maintenance: ESTIMATED` |
| Coverage table (all operators) | `{s}.period.coverage` per line; columns by vertical (mini: revenue, diesel, maintenance, staff; cold: revenue, electricity, staff, maintenance, compensation; EV: energy, demand charge, maintenance) |
| Coverage drawer rows | **Derived**: each site's cost lines (mini: diesel, O&M, staff; cold: energy, staff, maint, liability; EV: energy_cost, maintenance) with their coverage; recorded sum = `cost_recorded_usd`, total = `cost_total_usd` (Harvest 880 + 1,282 + 1,480 = 3,642; Metro 22,744.80 + 5,880 + 13,080.32 = 41,705.12) |
| Contrast lines: Kisiwa 2,400 L, Kobo 1,180 L, 210 L avoidable | `L.sites[1].period.actual.diesel_l`, `L.sites[0].period.actual.diesel_l`, `L.sites[0].decision.options[2].forward_replay.avoidable_fuel_l` |
| Huller $395/month; welding −$8.25/month | `MTO-HULLER.economics.net_monthly`, `MTO-WELDING.economics.net_monthly` |
| Mwea 2,650 vs 2,635 kWh; Kirinyaga 24% | `H.sites[0].period.actual.kwh`, `.kwh_model`; Kirinyaga bridge basis "(24%)" |
| Thika exposed $2,160, damage $108 | `H.sites[1].incident.batches[0].exposed_value`, `.confirmed_damage` |
| Embakasi 55% vs 30% peak; 3 buses short | `M.sites[0].period.actual.peak_share`, `.plan.peak_share`; `EMB-CHEAPEST.buses_short` |
| Ruiru 31% charger use; 6 not 10 | `M.sites[2].period.actual.charger_hour_utilisation`; options `RUI-ABSORB6/10` |
| "What to do first" ranked list and order | `{op}.portfolio.allocation.recommended` (order kept); spend from `.spend_breakdown`; effect from each option's `economics.net_12m` etc. |
| Metro 4th item (Ruiru connector claim) | `M.portfolio.allocation.priority_order[3]`, `M.sites[2].incident` |
| "Only if conditions change" | options with `disposition: CONDITIONAL` (`MTO-INV-BUYNOW.condition`) |
| "Considered and not chosen" | `{op}.portfolio.allocation.excluded[]` + every other option with `disposition` REJECTED/DEFERRED, with its `reason` (plain-language rewrite: CHANGE-REGISTER §5.7) |
| Budget meter $3,880 of $5,000 / $720 of $2,500 / $1,590 of $5,000 | `{op}.portfolio.allocation.spend`, `{op}.portfolio_constraints.budget_usd_nov_dec` |
| Crew meter 3 of 3 / 2 of 2 / 0 of 2 | `allocation.crew_visits_used` or `.technician_visits_used`; `portfolio_constraints.crew_visits_nov` or `.technician_visits_nov` |
| Sites at a glance: plan, actual, variance | `{s}.period.plan.*`, `.actual.*`, `.variance` |
| Why off plan: largest driver per site | max \|amount\| of `{s}.period.bridge[]`; label from driver (plain names in `decisions.js` `DRIVER`) |
| Coverage table (Lakeside) | `L.sites[i].period.coverage.{revenue,diesel,om,staff}` |
| Kisiwa maintenance estimated $700 | `L.sites[1].period.actual.om` with `coverage.om: ESTIMATED` |
| Rights under contracts table | see §5 |

## 2. Variance bridge (`#/bridge-{op}`)

| On screen | Source |
|---|---|
| Plan and Actual bars | as §1 portfolio plan / actual |
| Each step: site, driver, amount, evidence label, basis | `{s}.period.bridge[i]` (`driver`, `amount`, `class`, `basis`); class → label: ECONOMIC_ACTUAL "Recorded" (solid), MODELLED "Modelled" (hatched), DERIVED "Not explained yet" (dotted, dashed outline) |
| Metro steps | sign flipped to show cost: step = −`amount` (e.g. Embakasi +$2,604, +$600) |
| Ruiru "Not broken down yet" step −$19.68 | **Derived**: Ruiru has `variance: 19.68` and no `bridge` lines, so the step is the site variance shown as not explained (cost −19.68). Running total: see the Metro row below. |
| Kasarani | `variance: 0.00`, no step |
| Metro running totals | 38,520.80 + 2,604 + 600 − 19.68 = 41,705.12 = `M.portfolio.actual_cost` |
| Running totals | cumulative sum of steps, rounded to the cent; ends exactly at the portfolio actual (audit-verified for all three operators) |

## 3. Site economics (`#/econ-{site}`, 9 sites)

| On screen | Source |
|---|---|
| P&L lines (mini-grid): revenue, diesel, O&M, staff, contribution | `{s}.period.plan.{revenue,diesel_cost,om,staff,contribution}`, `.actual.*` |
| P&L lines (cold): storage revenue, electricity, staff, maintenance, customer compensation | `{s}.period.plan/actual.{revenue,energy,staff,maint,liability}` |
| P&L lines (EV): peak, off-peak, demand, flat energy, maintenance, total | Embakasi `{peak_cost,offpeak_cost,demand_cost,energy_cost}`; Kasarani `{energy_cost,maintenance,total}`; Ruiru actual split, plan `energy_cost` only (plan split shown "not available yet") |
| "Effect on result" column | **Derived**: (actual − plan) × sign (+1 revenue, −1 cost) |
| Source badge | `{s}.period.coverage` for every site (EV peak/off-peak/flat energy → `energy`, demand → `demand`, maintenance → `maintenance`) |
| Kisiwa coverage note | `L.sites[1].period.coverage_note` |
| "What moved the result" table | `{s}.period.bridge[]` |
| Energy-to-cash chain, Kobo | `L.sites[0].period.actual.{delivered_kwh 9,100, technical_loss_kwh 410, metered_kwh 8,690, adjustments_kwh 45, billed_kwh 8,645, revenue 3,458, collected 3,180, in_transit 0, outstanding 278}` |
| Energy-to-cash chain, Mto | `L.sites[2].period.actual.{delivered_kwh 6,000, expected_technical_loss_kwh 300, unexplained_kwh 120, metered_kwh 5,580, unbilled_mapping_kwh 140, adjustments_kwh 40, billed_kwh 5,400, revenue 2,160, collected 1,890, in_transit 150, outstanding 120}`; settlement note from `disorder_tests` LATE-SETTLE-1 |
| Kisiwa chain | delivered / metered not in manifest → "not available yet"; billed 7,400 vs plan 7,500 |
| Fuel balance Kobo / Kisiwa | `{s}.period.fuel_balance.*`; "above / within tolerance" **derived**: residual ÷ consumed vs `tolerance_pct` (Kobo 120/1,180 = 10.2% > 2%; Kisiwa 20/2,400 = 0.8% < 2%) |
| Cold expected vs actual kWh, verdict | `{s}.period.actual.kwh_model`, `.kwh`, `.crate_days`, `.occupancy_pct`, plan `occupancy_pct`; `H.energy_model.form`, `.tolerance_pct`; **derived** % = (kwh − kwh_model)/kwh_model (Mwea +0.6%, Kirinyaga +24%, Thika 0%) |
| Thika outage and batches | `H.sites[1].incident.{grid_outage, backup, chamber.*, batches[]}` |
| Embakasi peak share chart and tariff text | `M.sites[0].period.plan/actual.{peak_share, peak_kwh, max_kw}`, `M.sites[0].tariff.*` |
| Kasarani facts | `M.sites[1].tariff.usd_per_kwh`, `.incident.{fault, capacity_after, november_to_date}` |
| Ruiru facts | `M.sites[2].period.actual.{charger_hour_utilisation, peak_kwh, kwh, max_kw}`, `.physical.import_limit_kw`, `.incident.service_consequence`; peak share 10% **derived** = 6,076 ÷ 60,760 |

## 4. Decision comparators (`#/choice-{decision}`, 12)

Option rows come from `{s}.decision.options[]` or `{s}.entitlement.options[]` by id:

| Column | Source |
|---|---|
| What it costs | first present of `capex`, `cost`, `residual_cost`, `economics.one_off`; NO_ACTION → $0 |
| Effect | first present of `economics.net_12m`, `net_12m`, `economics.net_contract`, `economics.charges_12m`, `economics.net_monthly`, `economics.monthly`, `economics.energy_cost_monthly`, `avoided_capex`, `−expected_penalties`; KOB-NOACT `monthly_net: 0` with its note's $262.50 |
| Evidence | `economics.class` / `avoided_capex_class`; else "Quoted cost" (cost fields) or "Baseline" (do nothing) |
| Safeguards | `safeguards[]` / `safeguard` (`policy`, `mode`, `result`, `cost_monthly`); KIS-NOACT fail from its `reason` |
| Decision | `disposition` |
| Why / why not | `reason` / `condition` / `note` (plain-language rewrites listed in CHANGE-REGISTER §5.7) |

Do-nothing rows the manifest does not list (no money invented):

| Row | On screen | Basis |
|---|---|---|
| Mto demand: "Do nothing: no new connection" | $0; reason text | Letter-of-intent lapse date from `MTO-HULLER.customer` |
| Mto billing: "Do nothing: leave the meter records" | −$56 a month | `L.sites[2].period.bridge[1].amount` (October's unbilled charges) |
| Ruiru: "Do nothing: decline the extra buses" | $0 | none |

Six-part answer text per decision (all numbers read from the paths shown; derivations in brackets):

| Decision | Figures and paths |
|---|---|
| Kobo generator | days "11 of 31" `findings_expected[0].days`; 1,180 / 700 L; 210 L; $262.50 / $12 / $250.50 / $2,916 / $90 `KOB-STOPSOC.economics.*`; one-off split `economics.one_off_detail`; reserve 20 L, 4 of 61 days `KOB-RESERVE.forward_replay`; $28,000 `KOB-BATT100.capex`; upper bound $412.50 `findings_expected[0].gross_exposure_usd[1]`; 120 L, 2% `fuel_balance`; sensitivity $2,286 / $2,166 `KOB-STOPSOC.sensitivity`; proof `decision.verification_plan` |
| Kobo battery | 184 kWh (92%) at 2.7 years and 95% interim guarantee from `entitlement.occurrence` and `contract.conditions`; 200 kWh `physical.battery_kwh`; cover to 1 Mar 2034 `contract.term_end`; $430 = 250 + 180 `BAT-EVIDENCE.cost`, `.detail`; cycles, throughput `entitlement.evidence`; $64,000 `allocation.listed_not_summed.BAT-001_cover_exposure` |
| Kisiwa generator | 2,400 L; $1,800 `KIS-REPAIR.cost`; $9,500 `KIS-REPLACE.capex`; $14,000, $195, −$11,660 `KIS-BATT60`; warranty end 30 Jun 2026 `entitlements[0].contract.term_end` |
| Mto inverter | failed 28 Oct `entitlement.occurrence.failed`; $360 and breakdown `MTO-INV-CLAIM.residual_cost`, `.detail`; 21 days `contract.lead_time_days`; restore 28 Nov / 12 Nov `restore_by`; $2,910 `MTO-INV-BUYNOW.residual_cost`; $450 `MTO-INV-LOCAL.cost`; notice 27 Nov `notice_deadline`; $6,430 `MTO-INV-BUYNOW.condition` |
| Mto demand | load 15 kW, 10:00–15:00, 22 days, 1,650 kWh `MTO-HULLER.load`; $495 / $85 / $15 / $395 / $3,540 / $1,200 `MTO-HULLER.economics`; 3 days, 225 kWh, 68 L `forward_replay`; welding 10 kW, $264 / $272.25 / −$8.25, $0.42 `MTO-WELDING` |
| Mto billing | 140 / 120 kWh `period.actual.unbilled_mapping_kwh`, `.unexplained_kwh`; $56 / $672 / $56 `MTO-BILLING.economics`; $60 `MTO-METER-AUDIT.cost` |
| Mwea | 35% / 60%, 4,340 / 7,440 crate-days; 2,650 / 2,635 kWh; +0.6% (`MWEA-COMPRESSOR.reason`); $4,800; $485, $1,670, 4 months, $270 `MWEA-AGG.economics`; 150 crates, $0.18 `MWEA-AGG.customer` |
| Thika | outage, 135 min, 9.8 °C `incident`; 120 crates, $2,160, $108 `incident.batches[0]`; 6 crates (`bridge[0].basis`); remedy 8 Nov `entitlement.remedy_scheduled`; $100 = 40 + 60 `THIKA-EPC-STOPGAP`; $710 `THIKA-SELF.cost`; $500 deductible `incident.insurance.deductible` |
| Kirinyaga | 80%, 5,000 / 4,030 kWh; 970 kWh (24%) and $194 `bridge[0]`; $350, 80% (60–90%), $155.20, $1,512.40 `KIRI-REPAIR`; $4,800, $234.30, −$1,988.40 `KIRI-REPLACE` |
| Embakasi | 620 departures; 55% / 30%; 500 / 450 kW; $22,144.80 / $18,940.80 (energy lines); deadline schedule bill $13,356, saving $8,788.80, 12-month net $103,965.60, one-off $1,500 and its parts (24,800 kWh × 0.12 = 2,976; 62,000 kWh × 0.09 = 5,580; demand 4,800) `EMB-DEADLINE.economics`; cheapest bill $12,975 = 77,500 kWh × 0.09 (6,975) + demand 6,000, 2,500 / 2,800 kWh, 3 buses, 9,300 kWh a month short `EMB-CHEAPEST`; **$381** = 13,356 − 12,975 (also in the manifest note); tariff tiers `M.sites[0].tariff.{peak,super_offpeak,offpeak}`; "none of October's energy used the 00:00–05:00 rate" from `period.actual.note` |
| Kasarani | 1,050 / 1,200 kWh, 1 bus `incident.capacity_after`; 2 missed, $240, $120 `incident.november_to_date`; about $240 and 2 broken departures if we wait `KAS-OEM-WAIT.expected_penalties`, `.reason`; $90 **in total for 3 nights** (6, 7, 8 Nov) = 70 + 20 `KAS-OEM-STOPGAP.residual_cost`, `.nights`, `.detail`; $380 `KAS-LOCAL.cost`; restore due 9 Nov `entitlement.sla_clock.restore_due` |
| Ruiru | 31%; 2,800 / 3,200 kWh, $60,000 avoided `RUI-ABSORB6`; 3,360 kWh `RUI-ABSORB10`; 400 kW `physical.import_limit_kw`; $60,000 `RUI-4CHARGERS.capex`; ~$45,000 grid upgrade from `RUI-4CHARGERS.reason` |

## 5. Contract rights panels

| Panel | Source | Derived |
|---|---|---|
| Kobo battery | `L.sites[0].entitlement` (`claim_state: POTENTIAL`, conditions, evidence) | — |
| Kisiwa generator 1 | `L.sites[1].entitlements[0]` (`EXPIRED_AND_EXCLUDED`, run hours 1,240, operator funded $1,800) | — |
| Kisiwa O&M contract | `L.sites[1].entitlements[1]` (48 h, 96 h, $70 credit as exposure, weather log, `EVIDENCE_ASSEMBLED`) | notice period not in manifest → "not available yet" |
| Mto inverter 2 | `L.sites[2].entitlement` (`EVIDENCE_ASSEMBLED`, notice 27 Nov) | **21 days left** = 27 Nov − as_of 6 Nov |
| Thika transfer switch | `H.sites[1].entitlement` (`claim_events` 16/18/25 Oct, `ACCEPTED`, remedy 8 Nov) | **2 days left** = 8 Nov − 6 Nov |
| Thika insurance | `H.sites[1].incident.insurance` (deductible $500, notified 16 Oct, not filed, $0 reimbursed) | — |
| Mto do-nothing path | "$0 now; cover lost after 27 Nov 2026" from `MTO-INV-NOACT.reason` and `entitlement.notice_deadline` |
| Kasarani charger 2 | `M.sites[1].entitlement` (`claim_events` 2 and 3 Nov, `ACKNOWLEDGED`, restore due 9 Nov, 31 h response) | **3 days left** = 9 Nov − 6 Nov; credit text "5% of the $400 monthly fee per business day late" from `contracts[1].service_credit` (not computed, not counted) |
| Ruiru connector | `M.sites[2].incident` (`POTENTIAL`, claim at next routine visit) | — |
| Cost to us under each path | option `residual_cost` / `cost` / `capex` (see §4) | — |
| Page references in clause drawer | not in manifest → marked "page reference shown in the pilot (illustrative here)" | — |

## 6. Plan and budget (`#/plan-{op}`)

| On screen | Source / derivation |
|---|---|
| Budget $5,000 / crew 3 (Lakeside), $2,500 / 2 (Harvest), $5,000 / 2 (Metro) | `{op}.portfolio_constraints` |
| Recommended set and spend | `allocation.recommended`, `allocation.spend_breakdown`, `allocation.spend` |
| Meter check $60 note | `L.portfolio.allocation.meter_audit_note` |
| Modelled 12-month change +$6,096 = 2,916 + 3,540 − 360 | `L.portfolio.allocation.modelled_12m_change` |
| Listed, not added: $672, $70, $64,000 | `L.portfolio.allocation.listed_not_summed` |
| Excluded options and reasons | `allocation.excluded` |
| Sensitivity bullets | `L.portfolio.allocation.sensitivity`; $2,286 from `KOB-STOPSOC.sensitivity` |
| Metro order of work | `M.portfolio.allocation.priority_order` |
| **Letter-of-intent control** (Lakeside, Yes / No; default Yes) | Manifest condition on `MTO-INV-BUYNOW` and `allocation.sensitivity[0]`: buy-now wins only with budget ≥ 6,430 **and** no extension. Without an extension the claim path brings the inverter back on 28 Nov, leaving no time to connect the huller before the 30 Nov lapse, so the huller drops (the Architect's brute-force case). |
| $5,000 + No: spend **$2,680**, **+$2,556** | **Derived**: 3,880 − 1,200 (`spend_breakdown.MTO-HULLER`) = 2,680; 6,096 − 3,540 (`modelled_12m_change.MTO-HULLER`) = 2,556 (= 2,916 − 360). Buy-now needs 6,430 > 5,000: not affordable. |
| $6,500 + Yes: claim and wait **+$6,096** vs buy now **+$3,546** | 6,096 = `modelled_12m_change.total`; 3,546 = 2,916 + 3,540 − 2,910 (below). Claim and wait wins. |
| $6,500 + No: buy now **+$3,546** vs claim and wait **+$2,556**, difference **+$990** | 3,546 − 2,556 = 990. Matches the Architect's brute-force check. |
| **$6,500 budget case** (Lakeside) | Budget value 6,500 is the commission's second case; it satisfies the manifest condition "budget ≥ 6,430" (`MTO-INV-BUYNOW.condition`, `allocation.sensitivity[0]`). |
| Spend at $6,500: **$6,430** | **Derived**: 3,880 − 360 (`spend_breakdown.MTO-INV-CLAIM`) + 2,910 (`MTO-INV-BUYNOW.residual_cost`) = 6,430, matching `allocation.excluded[0].reason` |
| Modelled 12-month change at $6,500: **+$3,546** | **Derived**: 2,916 + 3,540 − 2,910 = 3,546 (the buy-now path's cost replaces the claim path's −360). The earlier restoration (12 Nov vs 28 Nov) is not given a money value. |
| Harvest / Metro totals | No portfolio 12-month total in the manifest → effects listed, not added |
| Plain-language replacements | allocation `method` → "Recommended set: essential work first, then the best 12-month result that fits the budget and crew visits."; `meter_audit_note` → "The $60 meter check is paid from the routine maintenance visit budget, not the decision budget." |

## 7. Proof it worked (`#/verify-{op}`)

| On screen | Source |
|---|---|
| Lakeside tests and baseline | `L.sites[0].decision.verification_plan.{baseline, after, operational_target, economic, causal}` (plain-language rewrite) |
| Expected $250.50 a month | `KOB-STOPSOC.economics.net_monthly` |
| Harvest: 5% tolerance; $155.20 a month | `H.energy_model.tolerance_pct`; `KIRI-REPAIR.economics.monthly`; tests marked "Proposed in this mock-up" (not in manifest) |
| Metro: peak share 55% → near 0%, about 62,000 kWh a month at the 00:00–05:00 rate, ≤ 400 kW, $8,788.80 a month | `M.sites[0].period.actual/plan.peak_share`; `EMB-DEADLINE.max_kw`, `.economics.saving_monthly`; tests marked "Proposed in this mock-up" |
| All verdicts "Not yet" | as_of 6 Nov: no change applied in the manifest |

## 8. Pilot request (`#/pilot-{op}`)

| On screen | Source |
|---|---|
| Headline question | `{op}.opening_proposition` |
| Records we need | Lakeside: `sources.mini_grid` (7). Harvest: `sources.cold_chain` (4) + `sources.mini_grid[5]` (plan spreadsheet) + `[6]` (contract documents) = 6. Metro: `sources.ev_depot` (4) + the same two = 6. Shared categories are reused because the manifest lists them only under mini-grid. |
| Timeline (weeks 1–4) | Not in manifest; labelled "Proposed" |
| Price | Not in manifest; "set in the written proposal; not shown" |

## 9. Evidence drawer

| Section | Source |
|---|---|
| Figure and title | the clicked figure's manifest value |
| Source records | system names from `sources.*`; sample rows carry the manifest totals for that line (no per-customer amounts invented); Kobo late delivery note from `disorder_tests` OOO-1; Mto re-upload DUP-1 and meter swap MAP-1; Kisiwa KES invoice FX-1 (rate "not available yet"); OCPP clock offset CLOCK-1 |
| How it is worked out | manifest `basis` strings or stated arithmetic over manifest values (e.g. 8,645 kWh × $0.40 = $3,458) |
| Coverage | `{s}.period.coverage` or class label |
| Provenance | five labels shown; the active one from `sources[].provenance` (source-emulated → "Emulated source"; demo-simulated → "Simulated demo data"); none is field connected or observed financial |
| Fixture reference | manifest path + `MANIFEST_SHA` |

## 10. Text constants (non-money) used on screen and not in the manifest

- "Design value: to be reproduced from your data" label at first use of forward-replay figures (Kobo 210 L and 20 L, huller 68 L) and on the Kobo avoidable bridge step (review L8).
- Do-nothing reasons where the manifest has none: Embakasi ("peak-price charging continues at $22,144.80 a month" = `EMB-NOACT.economics.energy_cost_monthly`), Kobo ($262.50 = avoidable fuel, `KOB-STOPSOC.economics.gross_monthly`), Kirinyaga ($194 = `bridge[0]`), Mwea (no figure).

- "61 replayed days" (Kobo forward replay window Sep 1 – Oct 31, from `time_scales.sparse_operational_context.span`).
- Plain-language site stories (`SITE_STORY`), driver names (`DRIVER`), option labels (`OPT_LABEL`), safeguard names (`SAFEGUARD`): wording only, meaning from `role_in_story`, `driver`, option `kind`/`carrier`, `policy`.
- Role questions from the brief's L1.3 table.

## 11. Figures that could not be sourced (shown as "not available yet")

Kisiwa delivered/metered kWh; Ruiru plan split by time of day (plan has energy and maintenance only); Kisiwa O&M notice period; contract page references; the KES conversion rate; pilot price; per-customer billing rows.
