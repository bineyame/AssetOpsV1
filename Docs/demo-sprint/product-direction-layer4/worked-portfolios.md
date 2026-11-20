# Worked portfolios: the three demonstration operators

**Companion to `layer4-transformation-design.md` (`rev 16.11`)** · AssetOps Architect (Claude) · 19 Nov 2026.

This file holds the full worked examples that the design document summarises: Lakeside Power (mini-grid), Harvest Cold Network (cold rooms) and Metro Bus Depots (EV depots), each read up from its factors, evaluated, planned and proved. The text was §7 and §10 of the design document up to rev 15. It moved here unchanged except for two things:
- the system's output is described as *recommended* or *proposed*, never as *chosen*. The accountable manager chooses within each decision and creates the Actions; the system checks the chosen set; and the executive approves the plan, which releases the Actions above the spend threshold (design §2.4–§2.5; owner, 19 Nov);
- section numbers are local to this file, and cross-references point to it or to design `rev 16.11`.

Every figure carries its marker and is checked by `check_manifest.py`. The roles are the five of design §2.6 (owner, Q-A2).

## 1. The worked portfolios: the loop, run three times

Each portfolio runs the same loop. **Observe** reads each Site's outcome up from its factors, target against actual. **Evaluate** writes every option as a change to factors and lets the structure give its value. **Choose**: the system recommends one option per decision, found by one search over all the decisions so that the recommended set fits the budget, the crew visits and each decision's rules. Each accountable manager chooses (this demo assumes the Recommended option) and creates the Actions. The system checks the chosen set and, if it does not fit, proposes the nearest set that does. The executive approves the plan, which releases the Actions above the spend threshold (design §2.4–§2.5). **Prove** names what will be measured afterwards. The tables below give every input a reader needs to follow each figure without opening the data file. Every decision is taken on 6 Nov, the demo's today (Declared input), and Protect effects are counted to 30 Nov, the reporting horizon (a limit set by the operator). Full models and test vectors are in `domain-and-decision-models.md`.

### 1.0 The shared structure across the three verticals

Moved from the design document's §2.1 in rev 16.2. The structure is shared, and each vertical fills it with its own factors, bounds and levers. The business model decides which nodes exist.

| | Mini-grid (metered, billed electricity) | Cold room (pay-as-you-store) | EV depot (captive fleet) |
|---|---|---|---|
| Outcome backbone | contribution = billed kWh × tariff − (fuel + O&M + staff) | contribution = chargeable crate-days × rate − (energy + staff + maintenance + customer compensation) | cost per required departure met = (energy + demand charge + maintenance + penalties) ÷ departures met; revenue NOT_APPLICABLE |
| Value chain | usable supply → delivered → metered → billed → collected / in transit / outstanding | crate-days available → occupied → chargeable → invoiced → received | deliverable kWh per night → delivered kWh → departures readied against required |
| Cost to serve | litres split necessary / candidate / unexplained × diesel price; O&M; staff | kWh = base + k × crate-days, ambient-corrected, + excess; electricity price | kWh by tariff interval; monthly peak kW × demand rate |
| Operations (O2, October) | asset availability 98.62%<!--fig:operations.lakeside-power.asset_availability.portfolio--> (428 of 434 asset-days; target 100%) | cooling availability 99.997%<!--fig:operations.harvest-cold.cooling_availability.portfolio--> (4 minutes lost at Thika) | deliverable energy used (import-limited) 56.23%<!--fig:operations.metro-bus.deliverable_energy_used.portfolio--> Σ/Σ (Embakasi 46.67%<!--fig:operations.metro-bus.deliverable_energy_used.sites.Embakasi-->, Kasarani 85.71%<!--fig:operations.metro-bus.deliverable_energy_used.sites.Kasarani-->, Ruiru 61.25%<!--fig:operations.metro-bus.deliverable_energy_used.sites.Ruiru-->) |
| Protect and bounds | clinic critical load; dawn battery charge ≥ 35%; evening redundancy | batch temperature ≤ commodity limit; backup start | every required departure; import limit |
| Contracts and capital | inverter, battery and genset warranties; O&M response SLA; replace-or-repair as a lifecycle comparison | EPC workmanship warranty; goods-in-custody insurance | charger parts warranty and service SLA |
| Home categories (design §2.0, OD-21; every node named, none inherited; `rev 16.11`) | **Grow:** energy delivered, metered kWh, billed kWh, tariff (G1); productive-use demand and its tariff, new connections (G3); headroom with no customer, beside Grow as potential, never its actual. **Optimize:** litres necessary, candidate and unexplained, the fuel balance that records them, diesel price, battery wear, O&M, staff, customer liability (O1); operations measures: asset availability, field visits, kWh per field visit, technical losses (O2); losses beyond expected (not priced), unmapped meters, adjustments, in transit, outstanding, collected (O3). **Protect:** clinic critical load, customer-hours interrupted, dawn charge, evening hours without redundancy or backup (P1); asset-days out of service, battery life (P2); warranty cover kept claimable (P4). **Assure** (A1 to A5, no money): the bridge's sources and coverage, options' evidence, Actions and verdicts, evidence kept, contract notices and remedies | **Grow:** occupied and chargeable crate-days, the storage rate (G1); room capacity (G2); new storage contracts (G3); idle capacity, beside Grow as potential. **Optimize:** cooling energy, as expected at the occupancy and above what occupancy explains, electricity price, staff, maintenance, customer compensation (Thika) (O1); cooling availability, crate-days without an excursion (O2); invoiced against received, outstanding (O3). **Protect:** batches exposed, crate-minutes above the limit, days with the backup start unproven, nights without backup cover (P1); stock at risk, at stake (P3); insured and warranted cover (P4). **Assure:** the same five | **Grow:** buses and required departures served on the chargers in place (G2), revenue *not applicable*; spare deliverable energy, beside Grow as potential. **Optimize:** energy charged by tariff interval and its prices, monthly peak import and the demand charge, maintenance, penalties, the part of a bill-total target that cannot be attributed (O1); deliverable energy used, departures per installed charger (O2). **Protect:** chargers in service, charging energy deliverable per night against required (Kasarani since 1 Nov), the import limit, departures met and missed, nights below required (P1); charger-days out of service, including Ruiru's charger 7, connector 2 (P2); charger cover kept claimable (P4). **Assure:** the same five |

Protect is a structure of measured factors too, and Assure reads the evidence class, coverage and verification state of every factor. That is why the four categories are never added together. Money a failure has already cost is never a Protect measure: Thika's compensation and Kasarani's penalties are Optimize cost lines, and Protect shows the batch exposed and the departures missed in their own units. The registry rows are in the manifest's `home_categories`, which `check_manifest.py` checks for completeness.

**Lakeside's value chain, October, at Portfolio level:** delivered 23,050 kWh → metered 21,700 → billed 21,445. Of the revenue, 150.00<!--rec--> was in transit and 668.00 outstanding.

**How each figure is known.** Every table says where its figures come from, in one of these words:

| Word | Meaning |
|---|---|
| Target | the operator's monthly target or budget line, from its budget spreadsheet: a figure the operator declares, not a record |
| Record | read from a meter, dip, invoice, log, roster or contract |
| Estimate | an actual cost whose invoice has not arrived; the budget amount is carried until it does, and it is left out of the recorded share |
| Calculated | computed by the structure from records and declared inputs (in this pack by `evaluate_structure.py`, rechecked by `independent_model.py`) |
| Declared input | typed into the demo data. Where marked *stands in for a calculation*, the product will compute it from records; the demo types it. Where marked *source not recorded*, the demo data holds the figure without saying whether it is a quote, a record or an assumption |
| Design value | a figure that re-running the Site's recorded data through the new setting (a replay) must reproduce before it is relied on |
| Quote / Assumption | a supplier or contractor price, lead time or duration / a value with no record or quote |
| Limit set by the operator | the budget, crew visits, horizon and service rules the operator sets |

In every factor table the Target column is a Target figure, and "How it is known" describes the Actual column. The money effect of a factor is always *(actual − target) × its price*. The checker confirms that each Site's effects add up to its deviation.

### 1.1 Mini-grid — Lakeside Power (Kobo, Kisiwa, Mto)

#### Observe

A mini-grid Site's contribution is revenue minus cost to serve. Revenue is billed kWh × tariff (plus productive-use kWh × the productive tariff, none in October). Cost to serve is fuel + O&M + staff (+ collection cost and battery wear, none in October). Fuel is litres × diesel price, and litres split into **necessary** running (load the solar and battery could not carry), **candidate** running (generator on while solar could have carried the load), **unexplained** litres (consumed but not accounted for by the generator's energy) and extra running caused by an option (none in October).

**Prices.**

| Site | Diesel per litre | Tariff per kWh | Generator consumption rate | How it is known |
|---|---:|---:|---:|---|
| Kobo | 1.25<!--fig:sites.lakeside-power/Kobo.actual.nodes.diesel_price--> | 0.40<!--fig:sites.lakeside-power/Kobo.actual.nodes.tariff--> | 0.30<!--rec:tenants[lakeside-power].sites[Kobo].physical.sfc_l_per_kwh--> L/kWh | Record |
| Kisiwa | 1.30<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.diesel_price--> | 0.55<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.tariff--> | 0.31<!--rec:tenants[lakeside-power].sites[Kisiwa].physical.sfc_l_per_kwh--> L/kWh | Record |
| Mto | 1.25<!--fig:sites.lakeside-power/Mto.actual.nodes.diesel_price--> | 0.40<!--fig:sites.lakeside-power/Mto.actual.nodes.tariff--> | 0.33<!--rec:tenants[lakeside-power].sites[Mto].physical.sfc_l_per_kwh--> L/kWh | Record |
| All three Sites | productive-use tariff 0.30<!--rec:tenants[lakeside-power].prices.productive_tariff_usd_per_kwh--> per kWh | | | Record (tariff schedule) |
| All three Sites | battery wear 0.08<!--rec:tenants[lakeside-power].prices.battery_wear_usd_per_kwh_throughput--> per kWh of battery throughput | | | Assumption, to be checked against the battery warranty's throughput terms |

The productive-use tariff and battery wear are not used in October (no productive-use load, no costed battery wear); they enter the options under Evaluate.

##### Kobo

**How the October litres are obtained.**

| Step | Figure | How it is known |
|---|---|---|
| Fuel balance: opening dip + deliveries − closing dip = litres consumed | 220<!--rec:tenants[lakeside-power].sites[Kobo].period.fuel_balance.opening_dip_l--> + 1,200<!--rec:tenants[lakeside-power].sites[Kobo].period.fuel_balance.deliveries_l--> − 240<!--rec:tenants[lakeside-power].sites[Kobo].period.fuel_balance.closing_dip_l--> = **1,180<!--fig:sites.lakeside-power/Kobo.actual.nodes.diesel_l--> L** | Record (dips and delivery notes) |
| What the generator should have used: metered generator energy × 0.30 L/kWh | 1,060<!--rec:tenants[lakeside-power].sites[Kobo].period.fuel_balance.model_implied_l--> L | Declared input. The generator-energy reading behind it is not in the demo data, so it cannot be shown |
| Classifying each generator interval splits the modelled litres | necessary 730<!--fig:sites.lakeside-power/Kobo.actual.nodes.necessary_l--> L + candidate 330<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> L = 1,060 L | Declared input, *stands in for a calculation*: the product classifies each generator interval; the demo types the result |
| Unexplained = consumed − modelled | 1,180 − 1,060 = 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> L | Declared input, *stands in for a calculation*. Tolerance 2% (Declared input): about 24 L of 1,180 L, so 120 L is far above it: investigate |

**Target against actual, per factor.**

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Necessary running (L) | 700<!--fig:sites.lakeside-power/Kobo.plan.nodes.necessary_l--> | 730 | +30 | 1.25 | −37.50<!--rec--> | Declared input, *stands in for a calculation* |
| Candidate running (L) | 0<!--fig:sites.lakeside-power/Kobo.plan.nodes.candidate_l--> | 330 | +330 | 1.25 | −412.50<!--rec--> | Declared input, *stands in for a calculation* |
| Unexplained litres (L) | 0 | 120 | +120 | 1.25 | −150.00<!--rec--> | Declared input, *stands in for a calculation* |
| *Diesel, all litres* | *700* | *1,180* | *+480* | | *fuel 875.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.fuel_cost--> → 1,475.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.fuel_cost-->* | Calculated |
| Billed kWh | 8,550<!--fig:sites.lakeside-power/Kobo.plan.nodes.billed_kwh--> | 8,645<!--fig:sites.lakeside-power/Kobo.actual.nodes.billed_kwh--> | +95 | 0.40 | +38.00<!--rec--> | Record |
| O&M | 600.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.om--> | 600.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.om--> | 0 | | 0.00 | Record |
| Staff | 500.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.staff--> | 500.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.staff--> | 0 | | 0.00 | Record |
| **Contribution** | **1,445.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.contribution-->** | **883.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.contribution-->** | | | **−562.00** | Calculated |

Sum of the effects: −412.50 − 37.50 − 150.00<!--rec--> + 38.00 = **−562.00**, which is 883.00 − 1,445.00. Revenue is 3,420.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.revenue--> → 3,458.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.revenue-->; cost to serve 1,975.00<!--fig:sites.lakeside-power/Kobo.plan.nodes.cost_to_serve--> → 2,575.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.cost_to_serve-->.

**Energy to cash (Record, then Calculated).** Delivered 9,100<!--fig:sites.lakeside-power/Kobo.actual.nodes.delivered_kwh--> kWh − technical losses 410<!--fig:sites.lakeside-power/Kobo.actual.nodes.technical_loss_kwh--> = metered 8,690<!--fig:sites.lakeside-power/Kobo.actual.nodes.metered_kwh--> − authorised adjustments 45<!--fig:sites.lakeside-power/Kobo.actual.nodes.adjustments_kwh--> = billed 8,645 kWh → revenue 3,458.00 − outstanding 278.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.outstanding--> = collected 3,180.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.collected-->.

##### Kisiwa

**How the October litres are obtained.** The fuel balance holds litres consumed 2,400<!--rec:tenants[lakeside-power].sites[Kisiwa].period.fuel_balance.consumed_l--> L (Record; the dips and deliveries behind it are not itemised in the demo data) and modelled litres 2,380<!--rec:tenants[lakeside-power].sites[Kisiwa].period.fuel_balance.model_implied_l--> L (Declared input; as at Kobo, the generator-energy reading behind it is not in the demo data). Every generator interval is classified necessary, because evening load exceeds what the solar and battery can carry: necessary 2,380<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.necessary_l--> L, candidate 0 L (Declared input, *stands in for a calculation*). Unexplained 2,400 − 2,380 = 20<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.unexplained_l--> L, inside the 2% tolerance (about 48 L): reported, not investigated.

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Necessary running (L), a rainy month | 2,300<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.necessary_l--> | 2,380 | +80 | 1.30 | −104.00<!--rec--> | Declared input, *stands in for a calculation* |
| Unexplained litres (L) | 0 | 20 | +20 | 1.30 | −26.00<!--rec--> | Declared input, *stands in for a calculation* |
| *Diesel, all litres* | *2,300* | *2,400<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.diesel_l-->* | *+100* | | *fuel 2,990.00<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.fuel_cost--> → 3,120.00<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.fuel_cost-->* | Calculated |
| Billed kWh | 7,500<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.billed_kwh--> | 7,400<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.billed_kwh--> | −100 | 0.55 | −55.00<!--rec--> | Record |
| O&M | 700.00<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.om--> | 700.00<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.om--> | 0 | | 0.00 | Estimate (the October invoice has not arrived) |
| Staff | 500.00 | 500.00 | 0 | | 0.00 | Record |
| **Contribution** | **−65.00<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.contribution-->** | **−250.00<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.contribution-->** | | | **−185.00** | Calculated |

Sum: −104.00 − 26.00 − 55.00 = **−185.00**, which is −250.00 − (−65.00). Energy to cash: delivered 7,950<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.delivered_kwh--> − losses 520<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.technical_loss_kwh--> = metered 7,430<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.metered_kwh--> − adjustments 30 = billed 7,400 → revenue 4,070.00<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.revenue--> (target 4,125.00<!--fig:sites.lakeside-power/Kisiwa.plan.nodes.revenue-->) → collected 3,800.00<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.collected-->.

Protect, observed: generator GEN-KS-01 failed on 30 Oct, so the evening supply (18:00–23:00, Record: service obligation) ran on GEN-KS-02 alone on 30 and 31 Oct: 2 days × 5 hours = 10<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.obligation_hours_without_redundancy--> evening hours with no backup (Calculated from the fault log).

##### Mto

**How the October litres are obtained.** Mto has no fuel balance record; its litres are the recorded 320<!--fig:sites.lakeside-power/Mto.actual.nodes.diesel_l--> L, all classified necessary evening running (the split is a Declared input, *stands in for a calculation*), against a target of 300<!--fig:sites.lakeside-power/Mto.plan.nodes.necessary_l--> L.

**Energy to cash, where Mto's revenue leaks (Record, then Calculated).**

| Stage | kWh | Note |
|---|---:|---|
| Delivered | 6,000<!--fig:sites.lakeside-power/Mto.actual.nodes.delivered_kwh--> | |
| − expected technical losses | 300<!--fig:sites.lakeside-power/Mto.actual.nodes.technical_loss_kwh--> | |
| − losses beyond expected | 120<!--fig:sites.lakeside-power/Mto.actual.nodes.unexplained_loss_kwh--> | not priced: investigated, not called theft |
| = Metered | 5,580<!--fig:sites.lakeside-power/Mto.actual.nodes.metered_kwh--> | |
| − unmapped meters (6 customers, meter swap on 3 Oct not applied) | 140<!--fig:sites.lakeside-power/Mto.actual.nodes.unmapped_kwh--> | |
| − authorised adjustment (clinic allowance) | 40<!--fig:sites.lakeside-power/Mto.actual.nodes.adjustments_kwh--> | |
| = Billed | 5,400<!--fig:sites.lakeside-power/Mto.actual.nodes.billed_kwh--> | target 5,600<!--fig:sites.lakeside-power/Mto.plan.nodes.billed_kwh--> |

The target states only billed kWh, so the comparison starts at the meter: target 5,600 kWh against metered 5,580 kWh, then the two billing leaks.

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Metered kWh | 5,600 | 5,580 | −20 | 0.40 | −8.00<!--rec--> | Record |
| Unmapped meters (kWh) | 0 | 140 | +140 not billed | 0.40 | −56.00<!--rec--> | Record |
| Authorised adjustment (kWh) | 0 | 40 | +40 not billed | 0.40 | −16.00<!--rec--> | Record |
| *Billed kWh* | *5,600* | *5,400* | *−200* | | *revenue 2,240.00<!--fig:sites.lakeside-power/Mto.plan.nodes.revenue--> → 2,160.00<!--fig:sites.lakeside-power/Mto.actual.nodes.revenue-->* | Calculated |
| Necessary running (L) | 300 | 320 | +20 | 1.25 | −25.00<!--rec--> | Declared input, *stands in for a calculation* |
| O&M | 500.00<!--fig:sites.lakeside-power/Mto.plan.nodes.om--> | 500.00 | 0 | | 0.00 | Record |
| Staff | 450.00<!--fig:sites.lakeside-power/Mto.plan.nodes.staff--> | 450.00<!--fig:sites.lakeside-power/Mto.actual.nodes.staff--> | 0 | | 0.00 | Record |
| **Contribution** | **915.00<!--fig:sites.lakeside-power/Mto.plan.nodes.contribution-->** | **810.00<!--fig:sites.lakeside-power/Mto.actual.nodes.contribution-->** | | | **−105.00** | Calculated |

Sum: −8.00 − 56.00 − 16.00 − 25.00 = **−105.00**, which is 810.00 − 915.00. Revenue of 2,160.00 splits into collected 1,890.00<!--fig:sites.lakeside-power/Mto.actual.nodes.collected-->, in transit 150.00<!--fig:sites.lakeside-power/Mto.actual.nodes.in_transit--> and outstanding 120.00<!--fig:sites.lakeside-power/Mto.actual.nodes.outstanding-->.

Protect, observed: inverter INV-MT-02 failed on 28 Oct, so the daytime supply (10:00–15:00, Record: service obligation) had 4 days × 5 hours = 20<!--fig:sites.lakeside-power/Mto.actual.nodes.obligation_hours_without_redundancy--> daytime hours at half inverter capacity (Calculated from the fault log); the idle generator backed the shortfall, so no hour was without backup.

##### The portfolio

| Site | Target contribution | Actual | Deviation | Of which revenue | Of which cost |
|---|---:|---:|---:|---:|---:|
| Kobo | 1,445.00 | 883.00 | −562.00 | +38.00 | −600.00 |
| Kisiwa | −65.00 | −250.00 | −185.00 | −55.00 | −130.00 |
| Mto | 915.00 | 810.00 | −105.00 | −80.00 | −25.00 |
| **Lakeside Power** | **2,295.00<!--fig:portfolio.lakeside-power.plan.sums.contribution-->** | **1,443.00<!--fig:portfolio.lakeside-power.actual.sums.contribution-->** | **−852.00** | **−97.00** | **−755.00** |

Each "of which" is the Site's change in revenue or in cost to serve from its table above: Kobo's cost is fuel 875.00 → 1,475.00 (−600.00), Kisiwa's fuel 2,990.00 → 3,120.00 (−130.00), Mto's revenue 2,240.00 → 2,160.00 (−80.00) and its fuel 300 L → 320 L (−25.00). Revenue 9,785.00<!--fig:portfolio.lakeside-power.plan.sums.revenue--> → 9,688.00<!--fig:portfolio.lakeside-power.actual.sums.revenue--> (−97.00); cost to serve 7,490.00<!--fig:portfolio.lakeside-power.plan.sums.cost_to_serve--> → 8,245.00<!--fig:portfolio.lakeside-power.actual.sums.cost_to_serve--> (−755.00). Of the 8,245.00, everything except Kisiwa's O&M (700.00, an Estimate) is recorded: 8,245.00 − 700.00 = 7,545.00<!--rec-->, or 91.5%.

**The surprise.** Kisiwa burns the most diesel (2,400 L) and has nothing to save: every generator interval is necessary. Kobo, with half the diesel, has 330 L of candidate running a month, which is what the next step acts on.

#### Evaluate

Each option is a change to factors. The structure re-evaluates the Site with the change and compares it with no action (or with the comparison stated for that decision): value = (change in monthly contribution × months) − the one-off. "One-off" always means the one-off cost the operator bears. An option is valued in money only when it changes a money factor; otherwise its effect is read on the Protect measures.

**Kobo: generator running after dawn** (no action: the 330 L of candidate running continues, 412.50<!--rec--> a month).

| Input | Figure | How it is known |
|---|---|---|
| Stop threshold 90% → 70%: candidate running avoided; added battery throughput; days with dawn charge below 35% | 210 L a month; 150 kWh a month; 0 of 61 replayed days | Design value |
| Battery reserve 30% → 25%: candidate running avoided; days with dawn charge below 35% | 20 L a month; 4 of 61 replayed days | Design value |
| Stop-threshold trial: vendor reconfiguration; trial supervision | 60.00<!--fig:options.KOB-STOPSOC.cost_lines.vendor_remote_reconfiguration.amount-->; 30.00<!--fig:options.KOB-STOPSOC.cost_lines.trial_supervision.amount--> | Declared input, source not recorded |
| 100 kWh battery | 28,000.00<!--rec:tenants[lakeside-power].sites[Kobo].decision.options[KOB-BATT100].capex--> | Declared input, source not recorded |
| No day with dawn charge below 35% (at 05:00) | service rule | Limit set by the operator |

| Option | Factor changes | How the value follows | Result |
|---|---|---|---|
| Lower the generator stop threshold 90% → 70% (remote, 14-day supervised trial) | candidate running −210<!--fig:-options.KOB-STOPSOC.params.avoided_candidate_l--> L a month; battery throughput +150<!--fig:options.KOB-STOPSOC.params.added_throughput_kwh--> kWh; dawn charge below 35% on 0<!--fig:options.KOB-STOPSOC.protect.replayed_dawn_days_below_safeguard--> of 61 replayed days | fuel 210 L × 1.25 = +262.50; battery wear 150 kWh × 0.08 = −12.00; monthly **+250.50<!--fig:options.KOB-STOPSOC.monthly_or_horizon_change-->**; 12 × 250.50<!--fig:options.KOB-STOPSOC.monthly_or_horizon_change--> − one-off 90.00<!--fig:options.KOB-STOPSOC.operator_one_off--> (60 + 30) | **+2,916.00<!--fig:options.KOB-STOPSOC.value--> over 12 months. Recommended** |
| Lower the battery reserve 30% → 25% (today's rule) | candidate running −20<!--fig:-options.KOB-RESERVE.params.avoided_candidate_l--> L; dawn charge below 35% on 4<!--fig:options.KOB-RESERVE.protect.replayed_dawn_days_below_safeguard--> replayed days | 20 L × 1.25 = +25.00 a month; 12 months, no one-off: +300.00<!--fig:options.KOB-RESERVE.value--> | **Rejected**: 4 days with dawn charge below 35%, and the service rule allows none |
| 100 kWh battery (28,000) | not valued | the candidate running is a setting problem; storage adds nothing the threshold change does not | Deferred |

The stop-threshold change leaves 330 − 210 = 120 L a month of candidate running that no setting the replay found feasible can avoid. That 120 L is a different quantity from the 120 L of unexplained litres in Observe.

**Kisiwa: generator GEN-KS-01 failed on 30 Oct.** From 6 Nov to 30 Nov there are 25<!--fig:options.KIS-NOACT.params.days_to_restore--> evenings of 5 hours. The evenings of 1–5 Nov (25 hours) were on one generator under every option and are observed, not an option's effect.

| Input | Figure | How it is known |
|---|---|---|
| Evening supply | 18:00–23:00, 5 hours a day | Record (service obligation) |
| What backs the evening load while GEN-KS-01 is out | nothing: GEN-KS-02 carries it, the battery is at reserve and there is no solar in the evening | Record (dispatch configuration) |
| GEN-KS-01 warranty; 1,000-hour service | ended 30 Jun; missed (1,240 run hours at failure), so the operator pays | Record (warranty contract; run-hours log) |
| Alternator repair: crew visit; repair time; cost | 8 Nov; 1 day; 1,800.00<!--fig:options.KIS-REPAIR.operator_one_off--> | visit date Declared input; repair time Quote (workshop estimate); cost Declared input, source not recorded |
| Generator replacement: lead time; cost | 21 days; 9,500.00<!--fig:options.KIS-REPLACE.operator_one_off--> | Declared input, source not recorded |

| Option | Factor changes | How the value follows | Evening hours with no backup, 6–30 Nov | Result |
|---|---|---|---:|---|
| No action | the unit stays out | no money factor changes | 25 days × 5 h = 125<!--fig:options.KIS-NOACT.protect.obligation_hours_without_backup--> | Rejected |
| Repair the alternator (crew visit 8 Nov + 1 repair day: restored 9 Nov) | days out: 3<!--fig:options.KIS-REPAIR.params.days_to_restore--> (6–8 Nov) | not valued in money; one-off 1,800.00<!--fig:options.KIS-REPAIR.operator_one_off--> | 3 × 5 = 15<!--fig:options.KIS-REPAIR.protect.obligation_hours_without_backup--> | **Recommended** |
| Replace the generator (21-day lead time: restored 27 Nov) | days out: 21<!--fig:options.KIS-REPLACE.params.days_to_restore--> | not valued in money; one-off 9,500.00<!--fig:options.KIS-REPLACE.operator_one_off--> | 21 × 5 = 105<!--fig:options.KIS-REPLACE.protect.obligation_hours_without_backup--> | Rejected |

No option restores a backup at once, so every option breaks the rule and all three stay in the recommendation search; the search breaks the service rules as little as possible before it weighs money, so it recommends the repair.

**Kisiwa: evening storage.** A separate decision, not an alternative to the repair: it looks forward from the repair with both generators in service and is compared with Kisiwa's October running (contribution −250.00). Its hours column does not compare with the 125, 15 and 105 above, which count 6–30 Nov while GEN-KS-01 is out.

| Input | Figure | How it is known |
|---|---|---|
| 60 kWh battery: necessary running moved to the battery | 150 L a month | Assumption (no Kisiwa replay exists) |
| 60 kWh battery: cost | 14,000.00<!--fig:options.KIS-BATT60.operator_one_off--> | Declared input, no quote held |

| Option | Factor changes | How the value follows | Evening hours with no backup | Result |
|---|---|---|---:|---|
| 60 kWh battery | necessary running −150<!--fig:-options.KIS-BATT60.params.shifted_fuel_l--> L a month | 150 L × 1.30 = +195.00<!--fig:options.KIS-BATT60.monthly_or_horizon_change--> a month (contribution −250.00 + 195.00<!--fig:options.KIS-BATT60.monthly_or_horizon_change--> = −55.00); 12 × 195.00<!--fig:options.KIS-BATT60.monthly_or_horizon_change--> − 14,000.00<!--fig:-options.KIS-BATT60.operator_one_off--> = −11,660.00<!--fig:options.KIS-BATT60.value--> | n/a: measured after the repair, when there are no such hours to remove | **Deferred**: over budget (a 14,000.00<!--fig:options.KIS-BATT60.operator_one_off--> one-off against the 5,000 budget for November and December) and negative over 12 months; it pays back in 14,000<!--fig:options.KIS-BATT60.operator_one_off--> ÷ 195<!--fig:options.KIS-BATT60.monthly_or_horizon_change--> ≈ 72 months, about 6 years |

**Mto: inverter INV-MT-02 failed on 28 Oct.** Money is compared with an immediate restore at no cost.

| Input | Figure | How it is known |
|---|---|---|
| Extra diesel while at half inverter capacity | 5<!--fig:options.MTO-INV-CLAIM.params.extra_l_per_day--> L a day | Design value |
| What backs the daytime shortfall while INV-MT-02 is out | the generator, idle 10:00–15:00 | Record (dispatch log) |
| Warranty: term; notice period; replacement lead time; cover | to 2029; 30 days (by 27 Nov); 21 days; the 2,600.00<!--fig:options.MTO-INV-CLAIM.cost_lines.replacement_unit.amount--> replacement unit at the supplier's cost, shipping at the owner's | Record (warranty contract) |
| Installation time; local supply time for a unit bought now | 1 day; 5 days | Quote (installer; local distributor) |
| Shipping the failed unit; installation; installing the returned unit as a spare | 150.00<!--fig:options.MTO-INV-CLAIM.cost_lines.shipping_failed_unit.amount-->; 80.00<!--fig:options.MTO-INV-CLAIM.cost_lines.install.amount-->; 80.00<!--fig:options.MTO-INV-BUYNOW.cost_lines.install_returned_unit_as_spare.amount--> | Declared input, source not recorded |
| Unit bought now | 2,600.00<!--fig:options.MTO-INV-BUYNOW.cost_lines.replacement_unit_bought.amount--> | Declared input, source not recorded |
| Local repair: time; cost | 2 days; 450.00<!--fig:options.MTO-INV-LOCAL.operator_one_off--> | time Assumption (no quote held); cost Declared input, source not recorded |

| Option | Restore date and factor changes | One-off | How the value follows | Rights | Result |
|---|---|---|---|---|---|
| Claim and wait | 6 Nov + 21 days + 1 installation day = 28 Nov; 22<!--fig:options.MTO-INV-CLAIM.params.days_to_restore--> days × 5 L = 110 L extra | shipping 150 + installation 80 = 230.00<!--fig:options.MTO-INV-CLAIM.operator_one_off-->; the 2,600.00<!--fig:options.MTO-INV-CLAIM.rights.claimable_cover--> unit is borne by the supplier | 110 L × 1.25 = −137.50<!--fig:options.MTO-INV-CLAIM.monthly_or_horizon_change-->; − 230.00<!--fig:-options.MTO-INV-CLAIM.operator_one_off--> | notice filed now; cover kept | **−367.50<!--fig:options.MTO-INV-CLAIM.value-->. Recommended** |
| Buy a unit now, claim the failed one as a spare | 6 Nov + 5 supply days + 1 install day = 12 Nov; 6<!--fig:options.MTO-INV-BUYNOW.params.days_to_restore--> days × 5 L = 30 L extra | unit 2,600 + installation 80 + shipping 150 + installing the returned spare 80 = 2,910.00<!--fig:options.MTO-INV-BUYNOW.operator_one_off--> | 30 L × 1.25 = −37.50<!--fig:options.MTO-INV-BUYNOW.monthly_or_horizon_change-->; − 2,910.00<!--fig:-options.MTO-INV-BUYNOW.operator_one_off--> | cover kept | −2,947.50<!--fig:options.MTO-INV-BUYNOW.value-->. Recommended only in the switch case below |
| Local repair | 6 Nov + 2 repair days = 8 Nov; 2 days × 5 L = 10 L extra | 450.00<!--fig:options.MTO-INV-LOCAL.operator_one_off--> | 10 L × 1.25 = −12.50<!--fig:options.MTO-INV-LOCAL.monthly_or_horizon_change-->; − 450.00<!--fig:-options.MTO-INV-LOCAL.operator_one_off--> = −462.50<!--fig:options.MTO-INV-LOCAL.value--> | opening the unit voids the warranty: 2,600.00<!--fig:options.MTO-INV-LOCAL.rights.cover_lost--> lost | Rejected: the warranty cover would be lost |
| No action | never restored; extra fuel over the 12-month horizon | none | 365 days × 5 L × 1.25 = −2,281.25<!--fig:options.MTO-INV-NOACT.value--> | no notice is filed, so the warranty lapses on 27 Nov: 2,600.00<!--fig:options.MTO-INV-NOACT.rights.cover_lost--> lost | Rejected: the warranty cover would be lost |

On every path the idle generator backs the daytime shortfall, so no hour is without backup; the daytime hours at half inverter capacity, 6–30 Nov, are 22 × 5 = 110<!--fig:options.MTO-INV-CLAIM.protect.obligation_hours_without_redundancy--> (claim), 6 × 5 = 30<!--fig:options.MTO-INV-BUYNOW.protect.obligation_hours_without_redundancy--> (buy now), 2 × 5 = 10<!--fig:options.MTO-INV-LOCAL.protect.obligation_hours_without_redundancy--> (local repair) and 25 × 5 = 125<!--fig:options.MTO-INV-NOACT.protect.obligation_hours_without_redundancy--> (no action).

**Mto: daytime demand** (no action: the daytime solar headroom stays unused).

| Input | Figure | How it is known |
|---|---|---|
| Huller load | 15 kW, 10:00–15:00 (5 hours), 22 days a month | Declared input (the cooperative's signed letter of intent) |
| Huller extra diesel on days without solar headroom | 68 L a month | Design value |
| Huller collection cost | 15.00 a month | Declared input, source not recorded |
| Huller connection: cost; lead time after the inverter is restored | 1,200.00<!--fig:options.MTO-HULLER.operator_one_off-->; 5 working days | Quote (connection contractor) |
| Huller letter of intent: lapses; extended to | 30 Nov; 31 Dec | lapse date Record; extension Assumption until signed (a condition a person sets) |
| Welding load | 10 kW, 18:00–21:00 (3 hours), 22 days a month | Declared input (verbal enquiry only) |
| Evening load is carried by the generator (no solar in the evening; battery at reserve) | the model's change rule: every evening kWh is generator energy | Assumption |

| Option | Factor changes | How the value follows | Result |
|---|---|---|---|
| Rice huller, Mto Farmers Cooperative | productive kWh +15<!--fig:options.MTO-HULLER.params.load_kw--> kW × 5 h × 22<!--fig:options.MTO-HULLER.params.days--> days = +1,650 kWh; extra fuel +68<!--fig:options.MTO-HULLER.params.added_fuel_l--> L; collection cost +15.00 | 1,650 kWh × 0.30 = +495.00<!--rec-->; fuel 68 L × 1.25 = −85.00<!--rec-->; collection −15.00; monthly **+395.00<!--fig:options.MTO-HULLER.monthly_or_horizon_change-->**; 12 × 395.00<!--fig:options.MTO-HULLER.monthly_or_horizon_change--> − one-off 1,200.00<!--fig:options.MTO-HULLER.operator_one_off--> | **+3,540.00<!--fig:options.MTO-HULLER.value--> over 12 months. Recommended**, if the inverter is restored and the meter connected (5 working days) before the letter lapses |
| Evening welding workshop | delivered and billed kWh +10<!--fig:options.MTO-WELDING.params.load_kw--> kW × 3 h × 22 days = +660 kWh; every evening kWh is generator energy (Assumption): 660 × 0.33 = 217.8 L | 660 × 0.40 = +264.00<!--rec-->; fuel 217.8 L × 1.25 = −272.25<!--rec-->; monthly −8.25<!--fig:options.MTO-WELDING.monthly_or_horizon_change-->; × 12 = −99.00<!--fig:options.MTO-WELDING.value--> | Rejected: negative margin; it breaks even only at a tariff of 272.25 ÷ 660 = 0.4125 per kWh, above the 0.40 charged |

**Mto billing.** Fixing the meter mapping restores 140 kWh × 0.40 = 56.00 a month of charges from the corrected billing run onward (12 × 56.00 = 672.00<!--rec--> over 12 months). It is not yet an evaluated option: the restored charges are listed beside the plan. That is a gap, not a rule: contribution is measured on what is billed, so restored billing moves it whether or not it is collected (design §2.0), and every decision is valued against no action (§2.4). Valuing it is queued with the other service-to-charge corrections (`decisions-register.md` §5, O3 data round); it needs no plan item, because it spends nothing. The meter audit (60, Declared input, paid from the routine O&M visit budget) looks for the 120 kWh lost beyond expected.

**Mto losses.** Its own decision, apart from the billing fix (D-RECON.7). Its Finding is on energy delivered but not explained after expected losses (unexplained loss, Optimize), a different factor from the unmapped meters. Its options are the meter audit, recommended, done on the inverter visit and paid from the routine maintenance budget, and no action, the reference. It is not valued in money, because losses are not priced. The Site manager chooses.

**Kobo battery BAT-001 warranty evidence.** There is no temperature record and no commissioning capacity test, so 64,000.00<!--fig:options.BAT-NOACT.rights.unclaimable_cover--> of cover cannot be claimed today.

| Input | Figure | How it is known |
|---|---|---|
| Warranty: term; cover | to 2034; 64,000.00<!--fig:options.BAT-EVIDENCE.rights.claimable_cover--> | Record (warranty contract) |
| Capacity test; temperature sensor | 250.00<!--fig:options.BAT-EVIDENCE.cost_lines.capacity_test.amount-->; 180.00<!--fig:options.BAT-EVIDENCE.cost_lines.temperature_sensor.amount--> | Declared input, source not recorded |

| Option | Factor changes | One-off | Result |
|---|---|---|---|
| No action | evidence stays incomplete | none | Rejected: 64,000.00 of cover stays unclaimable |
| Claim now | none | none | Rejected: a contested claim without evidence fails |
| Assemble evidence: capacity test and temperature sensor | the warranty cover becomes claimable | 250.00 + 180.00 = 430.00<!--fig:options.BAT-EVIDENCE.operator_one_off--> | **Recommended**; not valued in money |

#### Plan: proposed by the system, decided by people

**1. The plan and its limits.** Budget 5,000<!--rec:tenants[lakeside-power].portfolio_constraints.budget_usd_nov_dec--> for November and December; 3<!--fig:plans.lakeside-power.default.crew_visits_limit--> crew visits in November and 3<!--rec:tenants[lakeside-power].portfolio_constraints.crew_visits_dec--> in December, each visit counted in the month it falls (design §2.5); 12-month horizon (all limits set by the operator). Every option the search weighs has its crew visit in November. **How the recommendations are found:** one search over all the decisions together, so that the recommended set fits (design §2.4–§2.5). This demo assumes each manager chooses the Recommended option, so the chosen set is the combination below and fits, and the executive approves it. It tries every combination that takes one option per decision (a money-valued decision may take none, except the Mto inverter, which must be restored). An option that breaks one of its decision's rules (a service rule, or keeping warranty cover) is left out, unless no option of that decision can keep the rule, as at Kisiwa. A combination must fit the budget and the crew visits and meet the dates one option depends on (the huller needs the inverter first). The recommended set is the combination that breaks the rules least, then is worth most, then spends least.

| Item | One-off | Crew visits (Declared input) |
|---|---:|---|
| Kisiwa alternator repair | 1,800.00<!--fig:options.KIS-REPAIR.net_one_off--> | 1 |
| Kobo battery evidence | 430.00<!--fig:options.BAT-EVIDENCE.net_one_off--> | 1 |
| Kobo stop-threshold trial | 90.00<!--fig:options.KOB-STOPSOC.net_one_off--> | 0 (remote) |
| Mto inverter warranty claim | 230.00<!--fig:options.MTO-INV-CLAIM.net_one_off--> | 1 |
| Mto huller connection | 1,200.00<!--fig:options.MTO-HULLER.net_one_off--> | 0 (contractor) |
| **Spend** | **3,750.00<!--fig:plans.lakeside-power.default.spend-->** | **3<!--fig:plans.lakeside-power.default.crew_visits_used--> of 3** |

The Mto billing fix and meter audit go ahead beside the plan at no cost to this budget.

**A proactive item, declared beside the search** (design §2.5; OD-5). Halima, Kisiwa's Site manager, declares the scheduled service of the evening generator GEN-KS-02 for 8 Dec: oil, filters and a load test. It answers no Finding and is the origin of its own Actions. GEN-KS-02 has carried the evening supply alone since 30 Oct, so the service depends on the Kisiwa repair: GEN-KS-01 must be back, from 9 Nov, to keep a backup while GEN-KS-02 is off.

| Item | Factor it moves | One-off from this budget | Crew visits (Declared input) | Value |
|---|---|---:|---|---|
| Kisiwa generator service (proactive) | no factor (upkeep or compliance) | 0.00<!--rec:demo_workflow.tenants[lakeside-power].items[KIS-SERVICE].planned_spend--> (own technician; oil and filters already held in the O&M stock, Declared input) | 1, in December: 1 of 3 | none: upkeep carries no value (OD-5) |

It adds nothing to the 3,750.00<!--fig:plans.lakeside-power.default.spend--> spend and nothing to November's crew visits, so the search above is unchanged. It is not released at creation, because it uses a crew visit and the crew-visit threshold is 0 (OD-12); it is released when version 1 is approved.

**2. What is valued in money, and how the total is composed.**

| Valued option | 12-month value | One-off inside it |
|---|---:|---:|
| Kobo stop threshold | +2,916.00<!--fig:options.KOB-STOPSOC.value--> | 90.00<!--fig:options.KOB-STOPSOC.operator_one_off--> |
| Mto huller | +3,540.00<!--fig:options.MTO-HULLER.value--> | 1,200.00<!--fig:options.MTO-HULLER.operator_one_off--> |
| Mto inverter claim | −367.50<!--fig:options.MTO-INV-CLAIM.value--> | 230.00<!--fig:options.MTO-INV-CLAIM.operator_one_off--> |
| **The plan** | **+6,088.50<!--fig:plans.lakeside-power.default.value-->** | **1,520.00<!--fig:plans.lakeside-power.default.valued_option_costs-->** |

Each value is already net of its own one-off. It is a modelled change, not a realised one.

**3. Spend not valued in money, and what it protects.** 2,230.00<!--fig:plans.lakeside-power.default.not_valued_in_money--> of the spend changes no money factor; its effect is on the Protect measures, evaluated per option. The plan never shows a money figure that leaves part of its spend out.

| Item | One-off | Protect measure | No action | With the item |
|---|---:|---|---:|---:|
| Kisiwa repair (fewest evening hours with no backup) | 1,800.00<!--fig:options.KIS-REPAIR.operator_one_off--> | evening hours with no backup, 6–30 Nov | 125 | 15 |
| Kobo battery evidence (keeps the cover claimable) | 430.00<!--fig:options.BAT-EVIDENCE.operator_one_off--> | battery cover that can be claimed | 0 | 64,000.00 (at stake, never added to money) |
| | | tracked assets with complete contract evidence (Record count) | 1 of 3 | 2 of 3 |

**4. Downside and sensitivities.** Each case re-evaluates the plan with one factor or one item changed; one row per option it moves.

| Case | Option | How its value follows | 12-month value |
|---|---|---|---:|
| The plan as proposed | | | +6,088.50<!--fig:plans.lakeside-power.default.value--> |
| Diesel 20% cheaper: 1.00 a litre at Kobo and Mto | Kobo stop threshold | 12 × (210 × 1.00 − 12.00) − 90.00<!--fig:-options.KOB-STOPSOC.operator_one_off--> | +2,286.00<!--fig:options.KOB-STOPSOC.sensitivities.diesel_minus_20pct--> |
| | Mto huller | 12 × (495.00 − 68 × 1.00 − 15.00) − 1,200.00<!--fig:-options.MTO-HULLER.operator_one_off--> | +3,744.00<!--fig:options.MTO-HULLER.sensitivities.diesel_minus_20pct--> |
| | Mto inverter claim | −110 × 1.00 − 230.00<!--fig:-options.MTO-INV-CLAIM.operator_one_off--> | −340.00<!--fig:options.MTO-INV-CLAIM.sensitivities.diesel_minus_20pct--> |
| | *The plan* | sum of the three | *+5,690.00<!--fig:plans.lakeside-power.sensitivity_values.diesel_minus_20pct.value-->* |
| The stop-threshold change avoids 160 L, not 210 L | Kobo stop threshold | 12 × (160 × 1.25 − 12.00) − 90.00<!--fig:-options.KOB-STOPSOC.operator_one_off--> | +2,166.00<!--fig:options.KOB-STOPSOC.sensitivities.feasible_fuel_160l--> |
| | *The plan* | huller +3,540.00<!--fig:options.MTO-HULLER.value--> and inverter claim −367.50<!--fig:options.MTO-INV-CLAIM.value--> unchanged | *+5,338.50<!--fig:plans.lakeside-power.sensitivity_values.feasible_fuel_160l.value-->* |
| **Downside: the cooperative does not sign a supply contract** | Mto huller drops | 6,088.50<!--fig:plans.lakeside-power.default.value--> − 3,540.00<!--fig:-options.MTO-HULLER.value--> | **+2,548.50<!--fig:plans.lakeside-power.downside-->** |

The stop-threshold and huller values rest on Design values, and the screen says so until the replays have been run on the Sites' recorded data.

**5. Listed beside the plan, not added.**

| Item | Amount | Why it is not added |
|---|---:|---|
| Mto restored charges over 12 months | 672.00 | billed, not yet collected |
| Kisiwa O&M late-response credit: 10% of the 700.00 monthly fee (Record: O&M contract) | 70.00 | potential; review required; booked only on a credit note |
| Kobo battery cover | 64,000.00 | at stake, not money gained |

**6. When a condition changes (the switches).** Two conditions are set by a person, not computed: the budget, and whether the cooperative extends its letter of intent. The huller needs the inverter restored plus 5 working days for the connection, before the letter lapses on 30 Nov (or 31 Dec if extended). The claim restores on 28 Nov, which gives 4 Dec: too late unless the letter is extended. Buying now restores on 12 Nov, which gives 19 Nov.

| Budget | Letter extended | Inverter path | Huller | Spend | 12-month value |
|---:|---|---|---|---:|---:|
| 5,000 | yes (default) | claim | connected | 3,750.00<!--fig:plans.lakeside-power.switch_cases.5000/True.spend--> | +6,088.50<!--fig:plans.lakeside-power.switch_cases.5000/True.value--> |
| 5,000 | no | claim (buying now would need 6,430.00<!--fig:plans.lakeside-power.switch_cases.6500/False.spend-->) | lost | 2,550.00<!--fig:plans.lakeside-power.switch_cases.5000/False.spend--> | +2,548.50<!--fig:plans.lakeside-power.switch_cases.5000/False.value--> |
| 6,500 | yes | claim | connected | 3,750.00<!--fig:plans.lakeside-power.switch_cases.6500/True.spend--> | +6,088.50<!--fig:plans.lakeside-power.switch_cases.6500/True.value--> |
| 6,500 | no | **buy now** (only 6 days at half inverter capacity) | connected | 6,430.00<!--fig:plans.lakeside-power.switch_cases.6500/False.spend--> | +3,508.50<!--fig:plans.lakeside-power.switch_cases.6500/False.value--> |

Every figure in this table is Calculated: the recommendations are searched again under each pair of conditions. The spends and values follow from the items above: without the huller, 3,750.00<!--fig:plans.lakeside-power.default.spend--> − 1,200.00<!--fig:-options.MTO-HULLER.operator_one_off--> = 2,550.00<!--fig:plans.lakeside-power.switch_cases.5000/False.spend--> and 6,088.50<!--fig:plans.lakeside-power.default.value--> − 3,540.00<!--fig:-options.MTO-HULLER.value--> = 2,548.50<!--fig:plans.lakeside-power.switch_cases.5000/False.value-->; buying now instead of claiming, 3,750.00<!--fig:plans.lakeside-power.default.spend--> − 230.00<!--fig:-options.MTO-INV-CLAIM.operator_one_off--> + 2,910.00<!--fig:options.MTO-INV-BUYNOW.operator_one_off--> = 6,430.00<!--fig:plans.lakeside-power.switch_cases.6500/False.spend--> and 2,916.00<!--fig:options.KOB-STOPSOC.value--> + 3,540.00<!--fig:options.MTO-HULLER.value--> − 2,947.50<!--fig:options.MTO-INV-BUYNOW.value--> = 3,508.50<!--fig:plans.lakeside-power.switch_cases.6500/False.value-->. In the second row, dropping the Kisiwa repair would free enough to buy the inverter now and keep the huller, worth more, but would leave 125 evening hours with no backup instead of 15; least rule-breaking comes first, so the repair stays.

#### Prove

- **Kobo stop threshold.** 14 matched days before and after. Operational target: generator time after dawn down by 50% or more, with dawn charge at or above 35% every day. Money verdict from November dips and delivery notes per delivered kWh, weather-normalised. Kisiwa and Mto serve as untreated comparison Sites.
- **Mto huller.** Metered huller kWh → billed → collected.
- **Kisiwa repair.** Evening hours with no backup return to 0 from 9 Nov.

### 1.2 Cold rooms — Harvest Cold Network (Mwea, Thika, Kirinyaga)

#### Observe

A cold room's contribution is revenue minus cost to serve. Revenue is occupied crate-days × the storage rate. Energy is what the occupancy model expects plus any excess above it; the model is **base 1,550 kWh + 0.25 kWh per crate-day** a month (Declared input, to be fitted per room in a pilot). Cost to serve is energy × price + staff + maintenance + customer compensation (liability).

**Prices (Record).** Storage 0.20<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.rate--> per crate-day; electricity 0.20<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.elec_price--> per kWh. Room capacity 400 crates × 31 days = 12,400<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.capacity_crate_days--> crate-days.

##### Mwea

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Occupied crate-days (60% targeted, 35% actual) | 7,440<!--fig:sites.harvest-cold/Room A · Mwea.plan.nodes.crate_days--> | 4,340<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.crate_days--> | −3,100 | 0.20 | −620.00<!--rec--> | Record |
| Energy the model expects (kWh): 1,550 + 0.25 × crate-days | 3,410<!--fig:sites.harvest-cold/Room A · Mwea.plan.nodes.kwh_model--> | 2,635<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.kwh_model--> | −775 | 0.20 | +155.00<!--rec--> (less energy at lower occupancy, not a saving) | Calculated |
| Energy above the model (kWh) | 0 | 15<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.excess_kwh--> | +15 | 0.20 | −3.00<!--rec--> | Calculated from the meter: 2,650 kWh metered |
| Staff | 300.00<!--fig:sites.harvest-cold/Room A · Mwea.plan.nodes.staff--> | 300.00<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.staff--> | 0 | | 0.00 | Record |
| Maintenance | 50.00 | 50.00 | 0 | | 0.00 | Record |
| **Contribution** | **456.00<!--fig:sites.harvest-cold/Room A · Mwea.plan.nodes.contribution-->** | **−12.00<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.contribution-->** | | | **−468.00** | Calculated |

Sum: −620.00<!--rec--> + 155.00 − 3.00 = **−468.00**. Its 15 kWh above the model is 15 ÷ 2,635 = 0.6% of it, inside the 5% tolerance (Declared input): the equipment is fine; the room is under-occupied.

##### Thika

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Occupied crate-days (70%) | 8,680<!--fig:sites.harvest-cold/Room B · Thika.plan.nodes.crate_days--> | 8,680 | 0 | 0.20 | 0.00 | Record |
| Energy (kWh), on the model | 3,720<!--fig:sites.harvest-cold/Room B · Thika.plan.nodes.kwh--> | 3,720<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.kwh--> | 0 | 0.20 | 0.00 | Record |
| Customer compensation | 0.00 | 108.00<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.liability--> | +108.00 | | −108.00<!--rec--> | Record (credit note CN-0412) |
| Staff, maintenance | 350.00<!--fig:sites.harvest-cold/Room B · Thika.plan.nodes.staff-->, 80.00 | 350.00<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.staff-->, 80.00 | 0 | | 0.00 | staff Record; maintenance Estimate (the October service invoice has not arrived) |
| **Contribution** | **562.00<!--fig:sites.harvest-cold/Room B · Thika.plan.nodes.contribution-->** | **454.00<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.contribution-->** | | | **−108.00** | Calculated |

**Where the 108.00 comes from (Record).** On 6 Oct the grid failed at 19:11 and backup generator GEN-CR-01 did not start automatically (start-controller fault); it was started by hand at 19:14. The chamber was above its 2–4 °C band for 25–35 minutes, peaking at 8.2 °C at 19:19. Batch B-1031 (French beans, export grade, limit 5 °C) had 120<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.excursion_crates--> crates exposed, declared at 18.00<!--rec:tenants[harvest-cold].sites[Room B · Thika].incident.batches[B-1031].declared_value_per_crate--> a crate: 2,160.00<!--rec--> **at stake, not money**. QA downgraded 6 crates; 6 × 18.00 = 108.00 confirmed damage, which the customer contract makes the operator's liability. Avocados (limit 12 °C) were not exposed; the cabbage batch had left on 5 Oct.

Protect, observed: from 6 Oct the backup start was unproven and stock was present every night with no manual-start rota, so October had 26<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.nights_without_backup_cover--> nights with stock and no backup cover (Calculated from the stock register and the incident record).

##### Kirinyaga

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Occupied crate-days (80%) | 9,920<!--fig:sites.harvest-cold/Room C · Kirinyaga.plan.nodes.crate_days--> | 9,920 | 0 | 0.20 | 0.00 | Record |
| Energy the model expects (kWh) | 4,030<!--fig:sites.harvest-cold/Room C · Kirinyaga.plan.nodes.kwh_model--> | 4,030<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.kwh_model--> | 0 | 0.20 | 0.00 | Calculated |
| Energy above the model (kWh) | 0 | 970<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.excess_kwh--> | +970 | 0.20 | −194.00<!--rec--> | Calculated from the meter: 5,000<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.kwh--> kWh metered |
| Staff, maintenance | 400.00, 80.00 | 400.00, 80.00 | 0 | | 0.00 | Record |
| **Contribution** | **698.00<!--fig:sites.harvest-cold/Room C · Kirinyaga.plan.nodes.contribution-->** | **504.00<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.contribution-->** | | | **−194.00** | Calculated |

##### The portfolio

| Room | Target contribution | Actual | Deviation | Of which revenue | Of which cost |
|---|---:|---:|---:|---:|---:|
| Mwea | 456.00 | −12.00 | −468.00 | −620.00<!--rec--> | +155.00 − 3.00 |
| Thika | 562.00 | 454.00 | −108.00 | 0.00 | −108.00 |
| Kirinyaga | 698.00 | 504.00 | −194.00 | 0.00 | −194.00 |
| **Harvest Cold** | **1,716.00<!--fig:portfolio.harvest-cold.plan.sums.contribution-->** | **946.00<!--fig:portfolio.harvest-cold.actual.sums.contribution-->** | **−770.00** | **−620.00<!--rec-->** | **−150.00<!--rec-->** |

Occupied 22,940<!--fig:portfolio.harvest-cold.actual.sums.occupied_total_crate_days--> of 3 × 12,400 = 37,200 crate-days (target 26,040<!--fig:portfolio.harvest-cold.plan.sums.occupied_total_crate_days-->). Cost to serve 3,492.00<!--fig:portfolio.harvest-cold.plan.sums.cost_to_serve--> → 3,642.00<!--fig:portfolio.harvest-cold.actual.sums.cost_to_serve--> (+155.00 − 3.00 − 108.00 − 194.00 = −150.00<!--rec--> against target). Everything except Thika's maintenance (80.00, an Estimate) is recorded: (3,642.00 − 80.00) ÷ 3,642.00 = 97.8%.

**The surprise.** Mwea has the *highest* energy cost per crate-day (2,650 kWh × 0.20 = 530.00, ÷ 4,340 crate-days = 0.1221<!--rec:tenants[harvest-cold].sites[Room A · Mwea].period.energy_per_crate_day-->) and nothing wrong with its equipment. Kirinyaga looks efficient (5,000 kWh × 0.20 = 1,000.00, ÷ 9,920 = 0.1008<!--rec:tenants[harvest-cold].sites[Room C · Kirinyaga].period.energy_per_crate_day-->) but uses 970 ÷ 4,030 = 24% more energy than its occupancy explains.

#### Evaluate

**Mwea: low occupancy** (no action: contribution stays near −12.00 a month; acceptable but leaves the room 65% empty).

| Input | Figure | How it is known |
|---|---|---|
| Off-season contract: crates; days a month; months; rate | 150 crates; 30 days; December to March (4 months); 0.18 per crate-day | Quote (draft contract) |
| Contract handling | 100.00<!--fig:options.MWEA-AGG.params.handling--> a month | Assumption (a handling estimate; no quote) |
| Contract one-off: sales; ethylene curtain | 150.00<!--fig:options.MWEA-AGG.cost_lines.sales.amount-->; 120.00<!--fig:options.MWEA-AGG.cost_lines.ethylene_curtain.amount--> | Declared input, source not recorded |
| Compressor replacement | 4,800.00<!--fig:options.KIRI-REPLACE.operator_one_off--> | Declared input, source not recorded |

| Option | Factor changes | How the value follows | Result |
|---|---|---|---|
| Sign the aggregator's off-season contract | contract crate-days +150<!--fig:options.MWEA-AGG.params.crates--> crates × 30 days = +4,500 a month, December to March, at 0.18<!--fig:options.MWEA-AGG.params.contract_rate-->; model energy +0.25 kWh × 4,500; handling +100.00<!--fig:options.MWEA-AGG.params.handling--> a month | revenue 4,500 × 0.18 = +810.00<!--rec-->; energy 4,500 × 0.25 kWh × 0.20 = −225.00<!--rec-->; handling −100.00<!--fig:-options.MWEA-AGG.params.handling-->; monthly **+485.00<!--fig:options.MWEA-AGG.monthly_or_horizon_change-->**; 4 months × 485.00<!--fig:options.MWEA-AGG.monthly_or_horizon_change--> − one-off 270.00<!--fig:options.MWEA-AGG.operator_one_off--> (sales 150 + ethylene curtain 120, so avocado can share with cabbage) | **+1,670.00<!--fig:options.MWEA-AGG.value-->. Recommended** if the aggregator signs; on October's occupancy, 4,340 + 4,500 crate-days fit within the room's 12,400 |
| Replace the compressor | none: energy matches the model | 4,800<!--rec:tenants[harvest-cold].sites[Room A · Mwea].decision.options[MWEA-COMPRESSOR].capex--> for no factor change | Rejected: no equipment fault to fix |

**Kirinyaga: energy above the model** (no action: 194.00<!--rec--> a month continues).

| Input | Figure | How it is known |
|---|---|---|
| Condenser clean and leak repair: share of the excess recovered; cost | 0.80 (range 0.60–0.90); 350.00<!--fig:options.KIRI-REPAIR.operator_one_off--> | share Assumption; cost Declared input, source not recorded |
| A new compressor's energy, as a share of the model; its cost | 0.95; 4,800.00<!--fig:options.KIRI-REPLACE.operator_one_off--> | share Assumption (vendor datasheet); cost Declared input, source not recorded |

| Option | Factor changes | How the value follows | Result |
|---|---|---|---|
| Condenser clean and leak repair | excess × (1 − 0.80): 970 → 194 kWh, so 776 kWh less a month | 776 kWh × 0.20 = +155.20<!--fig:options.KIRI-REPAIR.monthly_or_horizon_change--> a month; 12 × 155.20<!--fig:options.KIRI-REPAIR.monthly_or_horizon_change--> − 350.00<!--fig:-options.KIRI-REPAIR.operator_one_off--> | **+1,512.40<!--fig:options.KIRI-REPAIR.value-->. Recommended** |
| Replace the compressor | excess → 0, and a new unit runs at 0.95<!--fig:options.KIRI-REPLACE.params.new_unit_factor--> of the model: 970 + (1 − 0.95) × 4,030 = 970 + 201.5 kWh less a month | (970 + 201.5) kWh × 0.20 = +234.30<!--fig:options.KIRI-REPLACE.monthly_or_horizon_change--> a month; 12 × 234.30<!--fig:options.KIRI-REPLACE.monthly_or_horizon_change--> − 4,800.00<!--fig:-options.KIRI-REPLACE.operator_one_off--> | −1,988.40<!--fig:options.KIRI-REPLACE.value_if_admissible-->. Deferred unless verified recovery after the repair is below 60% |

**Thika: backup start controller.**

| Input | Figure | How it is known |
|---|---|---|
| EPC workmanship warranty: term; claim; supplier's replacement date; cover | to 2027; accepted 17 Oct; 8 Nov; 710.00<!--fig:options.THIKA-EPC-WAIT.rights.claimable_cover--> | Record (EPC warranty claim) |
| Stopgap: SMS alarm relay; night rota labour | 40.00; 60.00 | Declared input, source not recorded |
| Goods-in-custody insurance deductible | 500.00 | Record (policy) |
| No night with stock and no backup cover | service rule | Limit set by the operator |

| Option | Factor changes | One-off | Nights with stock and no backup cover | Rights | Result |
|---|---|---|---:|---|---|
| Wait for the supplier | unproven until 8 Nov: 2<!--fig:options.THIKA-EPC-WAIT.params.days_to_restore--> nights | none | 2<!--fig:options.THIKA-EPC-WAIT.protect.nights_without_backup_cover--> | cover kept | Rejected: breaks the backup-cover rule on 2 nights |
| Stopgap: night manual-start rota and SMS alarm relay, then the supplier's replacement | covered from tonight | relay 40.00 + rota labour 60.00 = 100.00<!--fig:options.THIKA-EPC-STOPGAP.operator_one_off--> | 0<!--fig:options.THIKA-EPC-STOPGAP.protect.nights_without_backup_cover--> | cover kept | **Recommended**: the only option that keeps both the backup-cover rule and the warranty cover; not valued in money |
| Buy and fit a controller ourselves | covered from tonight | 710.00<!--fig:options.THIKA-SELF.operator_one_off--> | 0 | voids the EPC cover: 710.00<!--fig:options.THIKA-SELF.rights.cover_lost--> lost | Rejected: the warranty cover would be lost |

Goods-in-custody insurance is not claimed: the 108.00 loss is below the 500.00 deductible.

#### Plan: proposed by the system, decided by people

**1. The plan and its limits.** Budget 2,500<!--rec:tenants[harvest-cold].portfolio_constraints.budget_usd_nov_dec-->; 2<!--fig:plans.harvest-cold.default.crew_visits_limit--> crew visits in November; 12-month horizon (all limits set by the operator). Recommendations are found as at Lakeside: one search over all the decisions together, recommending the combination that breaks the rules least, then is worth most, then spends least. The demo's managers choose them, and the executive approves the plan.

| Item | One-off | Crew visits (Declared input) |
|---|---:|---|
| Thika stopgap | 100.00<!--fig:options.THIKA-EPC-STOPGAP.net_one_off--> | 0 |
| Kirinyaga repair | 350.00<!--fig:options.KIRI-REPAIR.net_one_off--> | 1 |
| Mwea contract | 270.00<!--fig:options.MWEA-AGG.net_one_off--> | 1 |
| **Spend** | **720.00<!--fig:plans.harvest-cold.default.spend-->** | **2<!--fig:plans.harvest-cold.default.crew_visits_used--> of 2** |

**2. What is valued in money.**

| Valued option | 12-month value | One-off inside it |
|---|---:|---:|
| Kirinyaga repair | +1,512.40<!--fig:options.KIRI-REPAIR.value--> | 350.00<!--fig:options.KIRI-REPAIR.operator_one_off--> |
| Mwea contract (its 4 months fall inside the horizon) | +1,670.00<!--fig:options.MWEA-AGG.value--> | 270.00<!--fig:options.MWEA-AGG.operator_one_off--> |
| **The plan** | **+3,182.40<!--fig:plans.harvest-cold.default.value-->** | **620.00<!--fig:plans.harvest-cold.default.valued_option_costs-->** |

**3. Spend not valued in money.** The Thika stopgap, 100.00<!--fig:plans.harvest-cold.default.not_valued_in_money-->: nights with stock and no backup cover from 6 Nov go from 2 (no action) to 0.

**4. Downside and sensitivities.**

| Case | Option | How its value follows | 12-month value |
|---|---|---|---:|
| The plan as proposed | | | +3,182.40<!--fig:plans.harvest-cold.default.value--> |
| Kirinyaga repair recovers 60%, not 80% | Kirinyaga repair | 12 × (970 × 0.60 × 0.20) − 350.00<!--fig:-options.KIRI-REPAIR.operator_one_off--> | +1,046.80<!--fig:options.KIRI-REPAIR.sensitivities.kirinyaga_recovery_60pct--> |
| | *The plan* | Mwea +1,670.00<!--fig:options.MWEA-AGG.value--> unchanged | *+2,716.80<!--fig:plans.harvest-cold.sensitivity_values.kirinyaga_recovery_60pct.value-->* |
| **Downside: the aggregator does not sign** | Mwea contract drops | 3,182.40<!--fig:plans.harvest-cold.default.value--> − 1,670.00<!--fig:-options.MWEA-AGG.value--> | **+1,512.40<!--fig:plans.harvest-cold.downside-->** |

**5. Listed beside, not added.** Thika's exposed batch, 2,160.00 at stake (customer-owned stock, not money); the 710.00<!--fig:options.THIKA-EPC-STOPGAP.rights.claimable_cover--> controller cover, kept.

**6. When a condition changes (the switch).** Whether the aggregator signs is set by a person. If it does not, the Mwea contract drops: spend 720.00<!--fig:plans.harvest-cold.default.spend--> − 270.00<!--fig:-options.MWEA-AGG.operator_one_off--> = 450.00<!--fig:plans.harvest-cold.switch_cases.False.spend-->, value +1,512.40<!--fig:plans.harvest-cold.switch_cases.False.value-->, 1<!--fig:plans.harvest-cold.switch_cases.False.crew_visits_used--> crew visit.

#### Prove

- **Kirinyaga.** Normalised kWh after the repair against the model over 30 days: at least 60% of the excess recovered, or the replacement decision reopens.
- **Thika.** A witnessed automatic-start test after the controller is replaced.
- **Mwea.** Crate-days and invoices under the contract.

### 1.3 EV depots — Metro Bus Depots, captive fleet (Embakasi, Kasarani, Ruiru)

#### Observe

Charging is a cost centre; there is no charging revenue. The outcome is **cost per departure met**: cost to serve ÷ departures met. Cost to serve is the energy bill (peak kWh × peak price + off-peak kWh × off-peak price + after-midnight kWh × night price + highest monthly kW × demand rate) + maintenance + penalties for missed departures. Departures depend on capacity: energy deliverable a night = min(chargers in service × charger kW, import limit) × charging window; a night is short when the buses need more than that.

##### Embakasi

**Inputs (Record).** Tariff C-114: peak (18:00–22:00) 0.24<!--fig:sites.metro-bus/Embakasi.actual.nodes.peak_price-->, off-peak 0.12<!--fig:sites.metro-bus/Embakasi.actual.nodes.offpeak_price-->, demand 12.00<!--fig:sites.metro-bus/Embakasi.actual.nodes.demand_rate--> per kW a month. A new 00:00–05:00 tier at 0.09<!--rec:tenants[metro-bus].sites[Embakasi].tariff.prices.night_from_1_nov--> starts on 1 Nov, so October's after-midnight energy was billed at 0.12. 20<!--fig:sites.metro-bus/Embakasi.actual.nodes.buses--> buses × 140 kWh = 2,800<!--fig:sites.metro-bus/Embakasi.actual.nodes.required_kwh_night--> kWh needed a night; the lower of 10 chargers × 60 kW = 600 kW and the import limit of 500<!--fig:sites.metro-bus/Embakasi.actual.nodes.import_limit_kw--> kW, over a 12-hour window: 500 × 12 = 6,000<!--fig:sites.metro-bus/Embakasi.actual.nodes.deliverable_kwh_night--> kWh deliverable.

| Factor | Target | Actual | Change | Price | Money effect | How it is known |
|---|---:|---:|---:|---:|---:|---|
| Energy, all hours (kWh) | 86,800 | 86,800 | 0 | | | Record |
| of which at peak (30% targeted, 55% actual) | 26,040<!--fig:sites.metro-bus/Embakasi.plan.nodes.peak_kwh--> | 47,740<!--fig:sites.metro-bus/Embakasi.actual.nodes.peak_kwh--> | +21,700 moved from 0.12 to 0.24 | +0.12 | −2,604.00<!--rec--> | Record (meter intervals) |
| Highest monthly kW | 450<!--fig:sites.metro-bus/Embakasi.plan.nodes.max_kw--> | 500<!--fig:sites.metro-bus/Embakasi.actual.nodes.max_kw--> | +50 | 12.00 | −600.00<!--rec--> | Record |
| Maintenance | 600.00 | 600.00 | 0 | | 0.00 | Record |
| *Bill lines* | *peak 26,040 × 0.24 = 6,249.60<!--fig:sites.metro-bus/Embakasi.plan.nodes.peak_cost-->, off-peak 60,760<!--fig:sites.metro-bus/Embakasi.plan.nodes.kwh_2200_2400--> × 0.12 = 7,291.20<!--fig:sites.metro-bus/Embakasi.plan.nodes.offpeak_cost-->, demand 450 × 12.00 = 5,400.00<!--fig:sites.metro-bus/Embakasi.plan.nodes.demand_cost-->* | *peak 47,740 × 0.24 = 11,457.60<!--fig:sites.metro-bus/Embakasi.actual.nodes.peak_cost-->, 22:00–24:00 15,500<!--fig:sites.metro-bus/Embakasi.actual.nodes.kwh_2200_2400--> × 0.12 = 1,860.00<!--fig:sites.metro-bus/Embakasi.actual.nodes.offpeak_cost-->, 00:00–05:00 23,560<!--fig:sites.metro-bus/Embakasi.actual.nodes.kwh_0000_0500--> × 0.12 = 2,827.20<!--fig:sites.metro-bus/Embakasi.actual.nodes.night_cost-->, demand 500 × 12.00 = 6,000.00<!--fig:sites.metro-bus/Embakasi.actual.nodes.demand_cost-->* | | | | Calculated |
| **Cost to serve** | **19,540.80<!--fig:sites.metro-bus/Embakasi.plan.nodes.cost_to_serve-->** | **22,744.80<!--fig:sites.metro-bus/Embakasi.actual.nodes.cost_to_serve-->** | | | **−3,204.00** | Calculated |

Sum: −2,604.00 − 600.00 = **−3,204.00**. All 620 departures met (Record); 22,744.80 ÷ 620 = 36.69<!--fig:sites.metro-bus/Embakasi.actual.nodes.cost_per_departure_met--> per departure (target 19,540.80 ÷ 620 = 31.52<!--fig:sites.metro-bus/Embakasi.plan.nodes.cost_per_departure_met-->).

##### Kasarani

**Inputs (Record).** Flat tariff 0.15<!--fig:sites.metro-bus/Kasarani.actual.nodes.offpeak_price--> per kWh, no demand charge. 8<!--fig:sites.metro-bus/Kasarani.actual.nodes.buses--> buses × 150 kWh = 1,200<!--fig:sites.metro-bus/Kasarani.actual.nodes.required_kwh_night--> kWh needed a night; the lower of 4 chargers × 50 kW = 200 kW and the import limit of 250 kW, over a 7-hour window: 200 × 7 = 1,400<!--fig:sites.metro-bus/Kasarani.actual.nodes.deliverable_kwh_night--> kWh deliverable. Penalty 120.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalty_rate--> per missed departure (service contract). One spare bus.

**October: on target.** Energy 1,200<!--fig:sites.metro-bus/Kasarani.actual.nodes.required_kwh_night--> kWh × 31 nights = 37,200 kWh × 0.15 = 5,580.00<!--fig:sites.metro-bus/Kasarani.actual.nodes.energy_cost--> + maintenance 300.00<!--fig:sites.metro-bus/Kasarani.actual.nodes.maintenance--> (Estimate: the invoice has not arrived) = 5,880.00<!--fig:sites.metro-bus/Kasarani.actual.nodes.cost_to_serve-->, the same as target; all 248 departures met (Record).

**November to date (1–5 Nov).** Charger CH-K2 failed at 23:40 on 1 Nov. The structure reads the consequence from the chargers-in-service factor before any invoice:

| Factor | October | November to date | How it is known |
|---|---:|---:|---|
| Chargers in service | 4 | 3<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.chargers_in_service--> | Record (fault log) |
| Energy deliverable a night (kWh) | 1,400 | 1,050<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.deliverable_kwh_night--> (3 × 50 kW × 7 h) | Calculated |
| Buses short a night | 0 | 1<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.buses_short_per_night--> (1,200<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.required_kwh_night--> needed − 1,050 = 150 kWh short, one bus's charge) | Calculated |
| Nights short | 0 | 5<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.short_nights--> | Calculated |
| Nights the spare bus covered | | 3<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.spare_bus_nights--> | Record (roster) |
| Departures missed | 0 | 5 − 3 = 2<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed--> | Calculated |
| Penalties | 0.00 | 2 × 120.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalty_rate--> = 240.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalties--> | Calculated |

##### Ruiru

**Inputs (Record).** Tariff C-117 (no after-midnight tier): peak 0.24, off-peak 0.12, demand 12.00 per kW. 14 buses × 140 kWh = 1,960<!--fig:sites.metro-bus/Ruiru.actual.nodes.required_kwh_night--> kWh needed a night; the lower of 12 chargers × 60 kW = 720 kW and the import limit of 400<!--fig:sites.metro-bus/Ruiru.actual.nodes.import_limit_kw--> kW, over an 8-hour window: 400 × 8 = 3,200<!--fig:sites.metro-bus/Ruiru.actual.nodes.deliverable_kwh_night--> kWh deliverable. The import limit, not the chargers, binds.

**October, actual by factor (Calculated).** Peak 6,076<!--fig:sites.metro-bus/Ruiru.actual.nodes.peak_kwh--> kWh × 0.24 = 1,458.24<!--fig:sites.metro-bus/Ruiru.actual.nodes.peak_cost-->; off-peak 54,684<!--fig:sites.metro-bus/Ruiru.actual.nodes.kwh_2200_2400--> kWh × 0.12 = 6,562.08<!--fig:sites.metro-bus/Ruiru.actual.nodes.offpeak_cost-->; demand 380<!--fig:sites.metro-bus/Ruiru.actual.nodes.max_kw--> kW × 12.00 = 4,560.00<!--fig:sites.metro-bus/Ruiru.actual.nodes.demand_cost-->; maintenance 500.00; cost to serve 1,458.24 + 6,562.08 + 4,560.00 + 500.00 = 13,080.32<!--fig:sites.metro-bus/Ruiru.actual.nodes.cost_to_serve-->; all 434 departures met (Record).

**Target: a stated total only.** Ruiru's target is 13,100.00<!--fig:sites.metro-bus/Ruiru.plan.stated_total--> (energy 12,600 + maintenance 500), with no kWh, peak share or kW behind it. So the target cannot be split into factors, and the deviation, 13,100.00 − 13,080.32 = +19.68, **cannot be attributed to factors**. This is an honest gap in the budget record, not a calculation.

Connector 2 of charger CH-R7 has been out since 6 Oct (26<!--fig:sites.metro-bus/Ruiru.actual.nodes.charger_days_out_of_service--> charger-days in October); no departure depended on it.

##### The portfolio

| Depot | Target cost to serve | Actual cost to serve | Deviation | Departures met |
|---|---:|---:|---:|---:|
| Embakasi | 19,540.80 | 22,744.80 | −3,204.00 | 620 of 620 |
| Kasarani | 5,880.00<!--fig:sites.metro-bus/Kasarani.plan.nodes.cost_to_serve--> | 5,880.00 | 0.00 | 248 of 248 |
| Ruiru | 13,100.00 (stated total) | 13,080.32 | +19.68 (not attributable) | 434 of 434 |
| **Metro Bus** | **38,520.80<!--fig:portfolio.metro-bus.plan.sums.outcome_total_with_stated_totals-->** | **41,705.12<!--fig:portfolio.metro-bus.actual.sums.cost_to_serve-->** | **−3,184.32** | **1,302<!--fig:portfolio.metro-bus.actual.sums.departures_met--> of 1,302** |

The deviation is −3,204.00 + 0.00 + 19.68 = −3,184.32. Cost per departure met: 41,705.12 ÷ 1,302 = **32.03<!--fig:portfolio.metro-bus.actual.sums.cost_per_departure_met-->** (target 38,520.80 ÷ 1,302 = 29.59<!--fig:portfolio.metro-bus.plan.sums.cost_per_departure_required-->). Everything except Kasarani's maintenance (300.00<!--fig:sites.metro-bus/Kasarani.actual.nodes.maintenance-->, an Estimate) is recorded: (41,705.12 − 300.00<!--fig:-sites.metro-bus/Kasarani.actual.nodes.maintenance-->) ÷ 41,705.12 = 99.3%.

#### Evaluate

**Embakasi: charging schedule.** No action is October's charging pattern billed under the November tariff. It is 23,560 kWh × (0.12 − 0.09) = 706.80 lower than October's energy bill of 22,144.80<!--fig:sites.metro-bus/Embakasi.actual.nodes.energy_cost--> because of the new tier; that drop is never credited to an option.

| Input | Figure | How it is known |
|---|---|---|
| Deadline-aware schedule: charging power; hours charged | 400 kW; 2 hours (22:00–24:00) + 5 hours (00:00–05:00), with 05:00–05:15 kept as slack | Declared input (the schedule's design) |
| Schedule: nights it would have met every departure | 31 of 31 replayed October nights | Design value |
| Schedule set-up and supervision | 1,500.00<!--fig:options.EMB-DEADLINE.operator_one_off--> | Declared input, source not recorded |
| Every required departure is met | service rule | Limit set by the operator |

| Option | Factor changes (a month) | Bill a month | How the value follows | Result |
|---|---|---:|---|---|
| No action | peak 47,740 kWh × 0.24 = 11,457.60; 22:00–24:00 15,500 kWh × 0.12 = 1,860.00; 00:00–05:00 23,560 kWh × 0.09 = 2,120.40; demand 500 kW × 12.00 = 6,000.00 | 21,438.00<!--fig:options.EMB-DEADLINE.energy_bill_reference--> | reference | |
| Deadline-aware schedule, 22:00–05:15 at 400<!--fig:options.EMB-DEADLINE.params.max_kw_option--> kW | billed hours 2 + 5 at 400 kW = 2,800 kWh a night, exactly the requirement (05:00–05:15 is slack for a late bus and is not billed); peak 0; 400 kW × 2 h × 31 = 24,800 kWh × 0.12 = 2,976.00; 400 kW × 5 h × 31 = 62,000 kWh × 0.09 = 5,580.00; demand 400 kW × 12.00 = 4,800.00<!--rec-->; meets every departure on 31<!--fig:options.EMB-DEADLINE.params.feasible_nights--> of 31 replayed nights | 13,356.00<!--fig:options.EMB-DEADLINE.energy_bill_option--> | 21,438.00 − 13,356.00 = **8,082.00<!--fig:options.EMB-DEADLINE.monthly_or_horizon_change-->** a month; 12 × 8,082.00<!--fig:options.EMB-DEADLINE.monthly_or_horizon_change--> − one-off 1,500.00<!--fig:options.EMB-DEADLINE.operator_one_off--> | **+95,484.00<!--fig:options.EMB-DEADLINE.value-->. Recommended**, once the tariff is confirmed from the invoice |
| Cheapest bill: 00:00–05:00 at the 500 kW limit | 500 kW × 5 h = 2,500<!--fig:options.EMB-CHEAPEST.bound.supplied_kwh_night--> kWh a night against 2,800 needed | 12,975.00<!--fig:options.EMB-CHEAPEST.energy_bill_option--> | 2,500 kWh × 31 nights × 0.09 + 500 kW × 12.00 = 12,975.00: cheaper only because it buys less energy | **Rejected**: 300 kWh short a night is 3<!--fig:options.EMB-CHEAPEST.bound.buses_short_per_night--> buses at 140 kWh, so 3 × 31 = 93<!--fig:options.EMB-CHEAPEST.protect.departures_missed--> departures missed a month; every departure must be met |

**Kasarani: charger CH-K2.** From 6 Nov there are 3<!--fig:options.KAS-OEM-WAIT.params.days_to_restore--> nights to the restore, one bus short each night, and the roster frees the spare bus on 1<!--fig:options.KAS-OEM-WAIT.params.spare_cover--> of them.

| Input | Figure | How it is known |
|---|---|---|
| Restore under the service agreement | notice 2 Nov + 5 business days = 9 Nov | Record (service agreement) |
| Contactor repair under the parts warranty | 380.00<!--fig:options.KAS-OEM-WAIT.rights.claimable_cover--> at the supplier's cost | Record (parts warranty) |
| Nights the roster frees the spare bus, 6–8 Nov | 1 | Record (roster) |
| Cover: charging an uncovered bus at Ruiru | 45.00<!--fig:options.KAS-OEM-STOPGAP.params.cost_per_bus_night--> a bus-night (driver overtime 35 + energy 10) | Quote |
| Local repair: time; cost | 1 day; 380.00<!--fig:options.KAS-LOCAL.operator_one_off--> | time Quote (local electrician); cost Declared input, source not recorded |
| Every required departure is met | service rule | Limit set by the operator |

| Option | Factor changes | One-off | Departures missed | How the value follows | Result |
|---|---|---:|---:|---|---|
| Wait for the supplier | 3 short nights − 1 spare-bus night | none | 2<!--fig:options.KAS-OEM-WAIT.protect.departures_missed--> | penalties 2 × 120.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalty_rate--> = 240.00<!--fig:-options.KAS-OEM-WAIT.monthly_or_horizon_change--> | Rejected: 2 departures missed; every departure must be met |
| Supplier remedy plus cover: the 2 uncovered buses charge at Ruiru | the 2 bus-nights covered | 2 × 45.00 = 90.00<!--fig:options.KAS-OEM-STOPGAP.operator_one_off--> | 0<!--fig:options.KAS-OEM-STOPGAP.protect.departures_missed--> | penalties avoided +240.00<!--fig:options.KAS-OEM-STOPGAP.monthly_or_horizon_change--> − 90.00<!--fig:-options.KAS-OEM-STOPGAP.operator_one_off--> | **+150.00<!--fig:options.KAS-OEM-STOPGAP.value-->. Recommended**: the only option that misses no departure and keeps the cover; valued in money because it changes the penalties factor |
| Local repair (restores 7 Nov) | 1 short night, no spare | 380.00<!--fig:options.KAS-LOCAL.operator_one_off--> | 1<!--fig:options.KAS-LOCAL.protect.departures_missed--> | 1 penalty fewer than waiting, +120.00<!--fig:options.KAS-LOCAL.monthly_or_horizon_change-->, − 380.00<!--fig:-options.KAS-LOCAL.operator_one_off--> = −260.00<!--fig:options.KAS-LOCAL.value--> | Rejected: voids the power-stage cover (380.00<!--fig:options.KAS-LOCAL.rights.cover_lost--> lost) and still misses a departure |
| Reschedule charging | none: the tariff is flat | | | nothing to save | Rejected |

**Ruiru: the city offers more buses.** These are compared with the import limit; their cost is a service expansion, so they are listed beside the plan, not valued.

| Input | Figure | How it is known |
|---|---|---|
| City offer | 6 or 10 more buses | Record (city route offer) |
| Charger purchase | 4 chargers × 15,000<!--fig:options.RUI-4CHARGERS.params.unit_cost--> | Quote (vendor proposal) |
| Added buses charge off-peak; the highest kW stays at 380 kW | the model's change rule | Assumption |

| Option | Factor changes | Energy needed vs deliverable a night | Departures missed a month | Result |
|---|---|---:|---:|---|
| Absorb 6 more buses on existing chargers | buses 14 → 20 | 2,800<!--fig:options.RUI-ABSORB6.bound.required_kwh_night--> vs 3,200 | 0<!--fig:options.RUI-ABSORB6.protect.departures_missed--> | **Recommended**; the bill rises 6 buses × 140 kWh × 31 nights = 26,040 kWh × 0.12 = 3,124.80<!--fig:-options.RUI-ABSORB6.monthly_or_horizon_change--> a month for the added service |
| Absorb 10 more buses | buses 14 → 24 | 3,360<!--fig:options.RUI-ABSORB10.bound.required_kwh_night--> vs 3,200 | 3,360 − 3,200 = 160 kWh short a night is 2 buses at 140 kWh, so 2 × 31 = 62<!--fig:options.RUI-ABSORB10.protect.departures_missed--> | Rejected: beyond the 400 kW import limit |
| Buy 4 chargers | chargers 12 → 16 | deliverable stays 3,200<!--fig:options.RUI-4CHARGERS.bound.deliverable_kwh_night--> (the import limit binds) | | Rejected: 4 × 15,000 = 60,000.00<!--fig:options.RUI-4CHARGERS.operator_one_off--> for no capacity gain |

The idle connector at Ruiru (CH-R7 connector 2, one interrupted session on 6 Oct) ranks **below** Kasarani's fault: no departure depends on it. It is claimed at the next routine visit.

#### Plan: proposed by the system, decided by people

**1. The plan and its limits.** Budget 5,000<!--rec:tenants[metro-bus].portfolio_constraints.budget_usd_nov_dec-->; 2<!--fig:plans.metro-bus.default.crew_visits_limit--> crew visits in November; 12-month horizon (all limits set by the operator). Recommendations are found as at Lakeside: one search over the Kasarani and Embakasi decisions together, recommending the combination that breaks the rules least, then is worth most, then spends least. The demo's managers choose them and create the Actions. Each change whose total one-off is above the spend threshold waits for the executive's approval of the plan (design §2.4). The Actions are taken up in this order (Declared input): Kasarani cover (departures at risk now), Embakasi schedule (largest money), Ruiru contract (a decision), CH-R7 claim (no consequence).

| Item | One-off | Crew visits (Declared input) |
|---|---:|---|
| Kasarani cover | 90.00<!--fig:options.KAS-OEM-STOPGAP.operator_one_off--> | 0 |
| Embakasi schedule | 1,500.00<!--fig:options.EMB-DEADLINE.operator_one_off--> | 0 (remote) |
| **Spend** | **1,590.00<!--fig:plans.metro-bus.default.spend-->** | **0<!--fig:plans.metro-bus.default.crew_visits_used--> of 2** |

**2. What is valued in money.**

| Valued option | 12-month value | One-off inside it |
|---|---:|---:|
| Embakasi schedule | +95,484.00<!--fig:options.EMB-DEADLINE.value--> | 1,500.00<!--fig:options.EMB-DEADLINE.operator_one_off--> |
| Kasarani cover | +150.00<!--fig:options.KAS-OEM-STOPGAP.value--> | 90.00<!--fig:options.KAS-OEM-STOPGAP.operator_one_off--> |
| **The plan** | **+95,634.00<!--fig:plans.metro-bus.default.value-->** | **1,590.00<!--fig:plans.metro-bus.default.valued_option_costs-->** |

**3. Spend not valued in money.** None (0.00<!--fig:plans.metro-bus.default.not_valued_in_money-->). Unlike the protective items in the other two portfolios, the Kasarani cover changes a money factor (penalties), so it is valued; its Protect effect is departures missed to 9 Nov, 2 → 0.

**4. Downside.** If Embakasi's time-of-use and demand-charge tariff does not apply (flat tariff), the schedule saves nothing: the plan is worth 95,634.00<!--fig:plans.metro-bus.default.value--> − 95,484.00<!--fig:-options.EMB-DEADLINE.value--> = +150.00<!--fig:plans.metro-bus.downside-->, the Kasarani cover only.

**5. Listed beside, not added.** Absorbing 6 buses at Ruiru avoids a 60,000.00<!--fig:options.RUI-4CHARGERS.operator_one_off--> charger purchase; a different comparison, so it is not added.

**6. When a condition changes (the switch).** Whether the tariff is confirmed from the invoice is set by a person: yes (default) gives the plan above; no gives spend 1,590.00<!--fig:plans.metro-bus.default.spend--> − 1,500.00<!--fig:-options.EMB-DEADLINE.operator_one_off--> = 90.00<!--fig:plans.metro-bus.switch_cases.False.spend--> and value +150.00<!--fig:plans.metro-bus.switch_cases.False.value-->.

#### Prove

- **Embakasi.** Peak share near 0%, about 62,000 kWh a month in 00:00–05:00, every departure met, on 14 supervised nights; money verdict from the next utility invoice.
- **Kasarani.** The service-agreement clock (responded in 31 h; restore due 9 Nov), departures met, and a service credit only when a credit note arrives.

### 1.4 The rights contrast inside repair decisions

The same physical event, a failed asset, leads to different choices because of the contract and the evidence:

| Asset | Contract position | Evidence | Best path | Operator cost |
|---|---|---|---|---|
| Mto inverter INV-MT-02 | warranty to 2029; replacement unit at supplier cost, shipping at owner cost; notice within 30 days (by 27 Nov) | installer certificate, ambient log, firmware, fault log on file | claim and wait — or buy now and claim the failed unit when the huller deadline is worth more (see "When a condition changes" in §1.1) | 367.50<!--fig:-options.MTO-INV-CLAIM.value--> / 2,947.50<!--fig:-options.MTO-INV-BUYNOW.value--> (one-off lines borne by the operator plus extra fuel to each path's restore date) |
| Kisiwa genset GEN-KS-01 | warranty ended 30 Jun 2026; 1,000-hour service missed | run hours 1,240 | operator-funded repair, now | 1,800.00<!--fig:options.KIS-REPAIR.operator_one_off--> |
| Kobo battery BAT-001 | warranty to 2034 with temperature and capacity conditions | no temperature sensor, no commissioning capacity test | assemble evidence first; a claim now would fail | 430.00<!--fig:options.BAT-EVIDENCE.operator_one_off-->; 64,000.00 of cover at stake |
| Thika GEN-CR-01 start controller | EPC workmanship warranty to 2027; quarterly tests 3 of 3 logged | event log, recorded inspection | supplier remedy + stopgap | 100.00<!--fig:options.THIKA-EPC-STOPGAP.operator_one_off--> |
| Kasarani CH-K2 | parts warranty + service agreement (48 h response, 5 business days to restore) | fault log, ticket | supplier remedy + cover | 90.00<!--fig:options.KAS-OEM-STOPGAP.operator_one_off--> |
| Kisiwa O&M contract | 48 h response; 10% fee credit when late; weather exclusion | 96 h response; calm weather bulletin | flag for human review | potential 70.00, never booked until a credit note |

Every state is set by a person from a recorded document or event. The screen always says: *This is not a legal decision. Coverage is decided by the supplier or insurer.*

---

### 1.5 Who acts in the demonstration, and the state of each operator's plan on 6 Nov

*Architect's demo choices, all illustrative* (`demo-site-scenario-manifest.yaml`, `demo_workflow`). They follow the design's rules (design §2.4 step 4, §2.5 and §2.6, and the owner's OD-16 and OD-17) and add no rule of their own. `check_manifest.py` checks them against those rules.

- **People.** Each role is shown by its title, with the Site for a Site manager, and a fictional first name, labelled *Illustrative*: for example "Site manager, Kobo · Peter". Every operator has an operator executive, a finance and commercial lead, a Site manager per Site, a field technician and an analyst.
- **Thresholds.** Each operator's spend threshold is 250.00<!--rec:demo_workflow.tenants[lakeside-power].spend_threshold-->, a portfolio setting with no Site setting. The crew-visit threshold is 0<!--rec:demo_workflow.tenants[lakeside-power].crew_visit_threshold--> (OD-12's default). So a change is released when it is created only if it spends no more than the threshold and uses no crew visit.
- **The plan's state.** The executive set the plan's period to November and December, to match the budget. The system opened the draft on 1 Nov (OD-10). On 6 Nov version 1 is *proposed*, awaiting the operator executive's approval. That is the moment the demonstration shows.
- **Who chose, and so owns, each item (OD-16).** Each item's owner is the person who chose its option or declared it. Each Action keeps its own creator and owner. So at Mto, David owns the inverter-claim item, while Joseph creates and owns the warranty notice.
- **Items' states on 6 Nov** (design Figure 6c). An item whose whole change is within both thresholds is *Released*; every other item is *Chosen*, waiting for version 1's approval.
- **A new connection (OD-17).** David proposed the Mto huller connection as a plan item. It is a capital item, so it waits for Amina's approval whatever its spend, and David creates its Action only after that approval. On 6 Nov it has none.

**Lakeside Power** (executive Amina; finance and commercial lead Joseph; Site managers Peter at Kobo, Halima at Kisiwa, David at Mto; field technician Musa; analyst Wanjiru).

| Item (chosen by, so owned by) | Item state | Action | Created by → owner | Due | On 6 Nov |
|---|---|---|---|---|---|
| Kobo stop threshold (Peter) | Released | Reconfigure the stop threshold 90% to 70% (vendor, remote) | Peter → Peter | 9 Nov | Released at creation: 90.00<!--fig:options.KOB-STOPSOC.operator_one_off--> over both Actions, no crew visit |
| Kobo stop threshold (Peter) | Released | Supervise the 14-day trial | Peter → Musa | 23 Nov | Released at creation, with the change above |
| Kisiwa repair (Halima) | Chosen | Repair the alternator | Halima → Musa | 9 Nov | Awaits approval: above the spend threshold, and one crew visit |
| Kobo battery evidence (Peter) | Chosen | Capacity test and temperature sensor | Joseph → Joseph | 20 Nov | Awaits approval: above the spend threshold, and one crew visit |
| Mto inverter claim (David) | Chosen | File the warranty notice (deadline 27 Nov) | Joseph → Joseph | 13 Nov | Awaits approval: within the spend threshold, but one crew visit |
| Mto inverter claim (David) | Chosen | Install the replacement unit | David → David | 28 Nov | Awaits approval, with the claim |
| Mto huller connection (David) | Chosen, capital (OD-17) | none yet: "Connect the huller (contractor), after the inverter", created by David after approval | – | 5 Dec | Awaits Amina's approval as capital |
| Kisiwa generator service (Halima), proactive | Chosen | none yet: Halima creates it when she books the 8 Dec visit | – | 8 Dec | Awaits approval: one crew visit in December; once version 1 is approved, its Action is released at creation |

**Harvest Cold Network** (executive Esther; finance and commercial lead Kevin; Site managers Ann at Mwea, Brian at Thika, Faith at Kirinyaga; field technician Samuel; analyst Njeri).

| Item | Action | Created by → owner | Due | On 6 Nov |
|---|---|---|---|---|
| Thika stopgap | Start the night manual-start rota and the SMS alarm relay | Brian → Brian | 6 Nov | Released at creation: within the threshold, no crew visit |
| Kirinyaga repair | Clean the condenser and repair the leak | Faith → Samuel | 13 Nov | Awaits approval: above the threshold, and one crew visit |
| Mwea aggregator | Sign the storage contract and prepare the room | Ann → Ann | 30 Nov | Awaits approval: above the threshold, and one crew visit |

**Metro Bus Depots** (executive Daniel; finance and commercial lead Lucy; Site managers Ibrahim at Embakasi, Mercy at Kasarani, Tom at Ruiru; field technician Otieno; analyst Achieng).

| Item | Action | Created by → owner | Due | On 6 Nov |
|---|---|---|---|---|
| Kasarani stopgap | Cover the short night with the spare bus until the restore | Mercy → Mercy | 9 Nov | Released at creation: within the threshold, no crew visit |
| Embakasi schedule | Set the staggered 22:00–05:15 charging schedule | Ibrahim → Ibrahim | 10 Nov | Awaits approval: above the threshold |

Harvest Cold's items are chosen by the Site managers who created their Actions (Brian, Faith and Ann), and Metro Bus's by Mercy and Ibrahim; the Thika and Kasarani stopgaps are Released, the rest Chosen.

Each released Action still counts in the plan, on its item (design §2.4 step 4). When the executive approves version 1, the waiting Actions are released together, and the items held in it become Released.

## 2. The demonstration world and its cost

`demo-site-scenario-manifest.yaml` defines three operators with three sites each, built backwards from each portfolio's executive choice: every site carries one contrast and one negative control, and the rights contrast is embedded in repair decisions rather than added as extra sites. The manifest's rev 4 re-expresses every site period as a factor structure with the value chain as backbone, re-bases Thika and Ruiru on the v7.0 incidents so the preserved drill-down pages and the figures describe one world, and values Embakasi's schedule against November no-action. Ground truth lives only in the manifest's private `oracle:`; every product figure must be computed through the real ingest and analytics path and compared against it.

**The illustration is itself evaluated, all the way down** (owner, 17 Nov, ninth to eleventh messages). The manifest holds only inputs. `structures:` declares every layer of each vertical: value-chain stages and leaks; physical splits and capacity (necessary and candidate running, normalised energy, chargers in service against the import limit, crate-days against room capacity); cost to serve and the outcome; and the Protect and O2 measures. `factor_map:` turns each site's source records into leaf factors, including dated records (a generator failed on 30 Oct, an inverter on 28 Oct, a backup start unproven since 6 Oct, a connector out since 6 Oct), so the period's own Protect measures — obligation hours without redundancy at Kisiwa 10<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.obligation_hours_without_redundancy--> and Mto 20<!--fig:sites.lakeside-power/Mto.actual.nodes.obligation_hours_without_redundancy-->, 26<!--fig:sites.harvest-cold/Room B · Thika.actual.nodes.nights_without_backup_cover--> nights without backup cover at Thika (unproven, stock present and no rota, each a record), 6 asset-days out; and for November to date at Kasarani 2<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.departures_missed--> departures missed — are evaluated, not typed, as are the 240.00<!--fig:sites.metro-bus/Kasarani.november_to_date.nodes.penalties--> of penalties those departures cost, a cost-to-serve line under Optimize. `evaluation:` gives each option's parameters with provenance, its factor changes as expressions, its cost lines with the right that could bear each (eligibility and claim progress kept apart), the rights it sets or voids, and restore dates derived from what drives them; it also declares the obligation bounds of each vertical with their reasons. `plans:` lists each portfolio's decisions with their bound policy: protective and valued decisions are searched together under the budget, the crew-visit limit and the dated dependencies; an option that breaks its decision's hard bounds is left out unless no option of that decision can keep them, and the recommended set breaks the bounds least, then is worth most, then spends least (Kisiwa: no option restores a backup at once, so all three stay in the search and the 15-hour repair is recommended over the 105-hour replacement). One redundancy rule applies to every Lakeside decision: obligation hours with no backup supply (owner question Q15). No option carries a typed admissibility: rights lapse at their notice deadlines, unauthorised repairs void cover, and the cover bound tests what is lost. `evaluate_structure.py` produces every figure in `derived-values.json`; the mock-up takes them from it; `check_manifest.py` asserts every stated figure in the manifest against the evaluation, every figure tagged in the documents (`<!--fig:path-->`) against its evaluated value with its sign, that the headline figures (spend, value and visits for each proposed plan; the period's Protect statement) are tagged, that no evaluated money figure of a proposed plan or option appears untagged in a figure-bearing document (record figures carry a record tag, checked against the manifest), the absence of superseded figures, and that untagged money figures are evaluated values or declared inputs. **Inputs by design, and flagged where shown:** the calibration-spike design values (Kobo avoided litres and dawn days, the huller's added fuel, fuel at half inverter capacity, Embakasi's feasible nights); quotes (repair, installation, the 45 per bus charged away from Kasarani, a 1-day local repair); the depot roster (the spare bus is free on 1 of the nights to a restore); one procurement assumption (Thika's self-funded controller fitted the same day); the batch-exposure observer's output (crate-minutes above the limit) and the battery-evidence record count; one assumption with no model (Kisiwa's 60 kWh battery saving, Q14). Ruiru's October target is a bill total and is labelled "not decomposed", never counted as evaluated.

**Documented limits of the illustration** (rev 13 final review, class ii; full list in `design-appendix.md` §6):
- **Unchecked rendered copies (F3).** Some manifest copies the screen renders are not checked against anything. These include listed-beside amounts, billing charges, the huller's revenue and fuel lines, replay-record copies, the budget copy, coverage shares, site variances and bridge amounts. All are correct today.
- **Plan-facing value fields (F4).** The plan-facing option value fields the screens read are neither defined in the specification nor compared by the checker.
- **Typed narrative counts (F6).** A few narrative counts restate evaluated figures.
- **Scan coverage (L1).** The influence scan left out the `oracle` and `checks` blocks, which are illustration expectations nothing enforces.
- **Summed violations (L2).** Violations of different bounds add when two decisions fall back at once (reachable, not binding here).
- **Static fallback (L3).** A decision falls back only when none of its options can meet its bound; this is owner question Q16.
- **Specification authority (L4).** The specification governs the independent model by review, not by a mechanical check.
- **Untagged figures (L5).** A wrong untagged figure that equals no key figure is not caught outside the scanned documents (the design's Parts 1–2, this file, the walkthroughs and the transition document's §1–§4).
- **Wording (L6).** Two wording defects remain on screen.

Three time scales keep it cheap (`delivery-plan.md`, in the pack file set the owner approved on 19 Nov): monthly ledger history generated directly from coherent ledgers (no physics), sparse cached operational context, and short high-fidelity evidence windows only where a claim needs them (5-minute dispatch and verification slots, 5-minute chamber readings around an incident, event-level OCPP). The historical cost (≈62 s per built site-day for ingest, assessment and matching; ≈147 s for the whole build) is [implementation-report] and must be re-measured; this commission was not authorised to run a build.
