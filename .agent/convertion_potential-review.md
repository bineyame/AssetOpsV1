# Review: `.agent/convertion_potential.html` (Architect, 14 Nov 2026)

Reviewer: fresh Claude reviewer, independent of the author. Review only; nothing changed.
Spec: `.agent/owner-conversion-potential-request-2026-11-14.md`. Code checked against `main` at `bc8fe7077`.

## Verdict: ACCEPT WITH NOTES

The code traces are accurate. I checked about 40 file:line claims and found one wrong conclusion (CC-3 "can read On track") and some small line drift. All five suspected disconnects (a)–(e) hold, and so do the new (g) and (h). The research is mostly attributed correctly, and the document marks its own uncertain figures honestly. One mesh-grid figure does not match its source, and a few company claims are labelled as plain facts.

The document covers every part of the owner's request. Its biggest gap is that it does not mention the Architect's own accepted "Price it" design (BL-68, PR-1 to PR-5, with PR-3 already merged). As a result, it misses some of what exists today, and two of its ranked build gaps repeat or diverge from work already planned. None of the findings blocks it as a discussion document. Fix the Medium items before any part of it is used with a client.

---

## Findings

### Medium

**M1. Disconnect (f) overstates the defect: CC-3 cannot read "On track".**
- Doc §7(f): "yet CC-3 can read On track". The same claim is in the summary bullet 4, §3 "Hard-wired limits" ("a state that implies a cost is known") and gap #6.
- Evidence: `outcomes/status.py:88-102`. "On track" requires an objective verdict of MET or ON_PACE. `outcomes/objectives.py:57-72` defines no measure for CC-3. The six declarable measures cover MG-2, MG-1, MG-5, CC-6, EV-1 and EV-2. So with no warning, CC-3 reads "No objective declared" (gray). With the repeat warning, it reads Needs attention or Watch.
- What is true: CC-3 is `measured=True` (`catalogue.py:63`), so the row says "No objective declared" where it should say "Not measured yet · …". That is a smaller honesty issue.
- Why it matters: (f) is one of three headline "new" disconnects and justifies gap #6.
- Fix: restate (f) as "reads 'No objective declared' rather than 'Not measured yet'", and lower gap #6 to Low.

**M2. The "Price it" design and the shipped price entry are missing. The exists/doesn't inventory is incomplete, and gaps #5 and #7 repeat planned work.**
- Evidence:
  - `financials/price_page.py:58-87` already lists these per-Site-type keys on the read-only price page:
    - `repair_visit_cost`
    - `planned_service_cost`
    - `charger_repair_cost`
    - `interrupted_session_cost`
    - `stock_value_at_risk` ("per chamber load, an upper bound").
  - `outcomes/price_action.py:24-31` builds "Set a … →" actions for them.
  - Site-admin price entry (PR-3, migration 0060) is merged (`8fdb0cf76`).
  - `.agent/architect-answer-price-it-2026-11-10.md:62-66, 199-201` already plans to price the repeat-visit warning (`repair_visit_cost`), EV interruptions (`interrupted_session_cost`) and cold stock (`stock_value_at_risk`, "never a loss").
- The doc does not mention any of this:
  - Gap #5 ("Cost on maintenance / work records; price the @COST repeat-visit warning") proposes cost columns on work records. The accepted design uses a declared per-visit price instead.
  - Gap #7 ("Declared produce value per crate") departs from the accepted per-chamber-load upper bound without saying so.
  - The lever "change the price live" (§11) depends on PR-3 but does not cite it.
- Why it matters: the owner may queue duplicate or conflicting work. "What exists today" also understates the product: price entry exists, and the loss prices are designed and queued.
- Fix:
  - Add the price page, PR-3 and the planned PR keys to §8, §10 and §13.
  - Recast #5 and #7 as "finish PR-3 keys + PR-4/PR-5" or justify the difference explicitly.
  - Keep "cost columns on work records" as a later step for real invoices.

**M3. A research figure does not match its source and should not go in front of a CEO, COO or CFO.**
- Doc §9 Mini-grids, Benchmarks: "A CrossBoundary meshgrid study reports 99% reliability against 27% at a control site and 213% higher ARPU, self-reported (snippet)".
- Evidence: Duke Energy Access Project's summary of the same June 2025 CrossBoundary mesh-grid study (energyaccess.duke.edu) gives ">96% reliability compared to 27-60% reliability at the mini-grid sites". It frames the mini-grid sites as a comparison group and reports no ARPU uplift. I found no source for "213%". The cited PDF was too large to fetch.
- Why it matters:
  - The number is wrong or unverified.
  - The 27–60% figure is the reliability of the mini-grids themselves. Quoted to a mini-grid operator, it disparages the buyer's own asset class.
- Fix: replace it with the Duke-confirmed wording or remove it, and mark it "do not quote".

**M4. A demo lever relies on a capability the product does not have.**
- Doc §11 EV: "Estimated charging income at their tariff, with the peak/off-peak what-if (KSh 8 against 16)".
- Evidence:
  - No time-of-use logic exists in the backend. A grep for off-peak, time-of-use or TOU returns nothing in product code.
  - `financials/assumptions.py:32` holds one `ev_gross_tariff_per_kwh`.
  - `ev_scenarios/rules.py:31` takes a single `tariff_per_kwh`.
  - §10 itself marks this as "partial · one declared tariff".
- So the demo can show two separate single-tariff scenarios, but not a peak/off-peak split of the real sessions.
- Fix: reword it as "re-price at 8 vs 16 KSh as two scenarios", or move it to the build-gap list (#10).

**M5. Gap #1 understates what it needs and what it delivers.**
- Doc §13 #1: "Mini-grid supply-interruption Finding over existing critical_served / feeder-demand intervals … No [new client data] … uptime is the investors' second KPI".
- Evidence: `chain/measure_impls.py:225-280` (`CriticalServed`). The measure counts an hour only when:
  - a stored `mini-service/2` head has exactly one SUPPORTED `role == "CRITICAL"` load row that states `unserved_kwh`;
  - and the hour falls in declared operating hours.
- This requires classifying critical loads per Site and per client. The measure covers the critical load only. It is unserved kWh, not customer-facing interruption hours (SAIDI/SAIFI), which is the "power reliability" KPI funders mean (Odyssey/CBEA).
- Fix:
  - State the precondition: a critical feeder classified and declared operating hours.
  - Name the output honestly: "critical demand not served", not "uptime".
  - Keep it at #1 if the owner agrees. It is still the cheapest way for a mini-grid to raise Protect.

### Low

**L1. The pipeline diagram says "7 are 'not measured' (no data)".** The catalogue has six such outcomes (MG-6, MG-3, CC-2, CC-4, EV-6, EV-2; `catalogue.py:45-62`), and the doc's own text says six (§1, §7e). Fix the diagram label.

**L2. Line-number drift in a few citations.** Each conclusion holds, but the cited lines are off:
- §2 map ref ":25, 33, 36": line 33 is `CHARGER_FAULT_OVERDUE_INSPECTION`. The EV Grow entry is `:22` (`EV_INTERRUPTION`).
- §7(d) "target … :159-160, money :161-163": the MG-2 target is `:161-162` and its money record is `:163-166`. Lines 159-160 are the headroom potential money.
- §7(b) "read.py:936-943" (Assure detail): the code is at `:944-951`.

**L3. Wrong internal cross-reference.** Summary bullet 4 says "nuances in section 3". The disconnect nuances are in section 7.

**L4. Source attributions need small corrections.**
- "$6,824/kW capex in AMDA 2024": Microgrid Knowledge attributes the $6,824/kW to a SEforALL presentation. Only the 20% decline is attributed to AMDA.
- "TNO review": this is Come Zebra et al. 2021 in *Renewable and Sustainable Energy Reviews* (TNO hosts the PDF). It is a review of developing countries generally, not an African field benchmark.
- ColdHubs "$60 to $120/month": the MIT Solve page describes this as a "50% increase" while giving the same numbers. The source is internally inconsistent and self-reported (2019).

**L5. Company claims are tagged "checked" without being marked as company claims.** These include SokoFresh "40% more produce", Spiro "up to $3/day" and "~30% lower per km" (CEO quote), and ColdHubs "2 → 21 days". They are correctly attributed to the company. For a CFO they should carry "company-reported" in the tag. The doc already tags the CrossBoundary item "self-reported", so the same convention applies.

**L6. The data-request script promises features that are not built.** Script lines 1, 2, 4 and 6 say "we'll show what was actually collected", "turns 'possible extra cost' into your real cost per kWh", and so on. Gaps #3, #4, #5 and #8 are not built. Add an internal note or rephrase as "we can build towards …", so the client does not hear a commitment.

**L7. The diagrams are hard to read on phones.**
- The six SVGs use `viewBox` 980 wide with fixed 10.5–13px text and scale to the container (`svg{width:100%}`). At 360px width the text renders at about 4–5px.
- Nothing wraps the SVGs in a horizontal-scroll container or provides a stacked layout for narrow screens.
- Desktop legibility is fine. Light and dark tokens are defined correctly: `:root` and `prefers-color-scheme` guarded by `:root:not([data-theme="light"])`, plus `[data-theme="dark"]`, and all SVG fills use variables.
- Fix: wrap each figure in `overflow-x:auto` with `min-width:720px`, or reduce the text count per box.

**L8. Africa-specific items that are missing.** These are suggestions, not acceptance gaps.
- **Currency.** Local-currency billing (NGN, KES, UGX) set against a USD investor view. Naira volatility is a live CFO topic. The product's one-currency sum rule is relevant.
- **Customer data consent.** Kenya Data Protection Act and Nigeria NDPA requirements when asking for per-customer billing exports. This belongs in the data-request script.
- **Non-technical loss.** Generation kWh against billed kWh. The COO row names it, but it is the strongest lever once billing (#3) lands, and it does not appear among the levers or gaps.
- **Mini-grid carbon.** The doc covers carbon for EV only. Mini-grid carbon (diesel displaced) is also a revenue line.

---

## Coverage against the owner's request

| Requested | Present | Note |
|---|---|---|
| Four pillars × three verticals: signal → outcome map → catalogue → category → card | Yes (§2–5 tables per vertical, §1 pipeline) | Accurate apart from M1 |
| Money composition in detail | Yes (§6 table + diagram) | Matches `priced_energy.py`, `avoided_cost`, `recorded_amount.py`, `vocabulary.py:323` |
| Flexibility and limits | Yes (per pillar) | |
| Structural data points with sources and integration paths | Yes (§10 three tables with source system, path, effort, priority) | Misses the Price-it keys (M2) |
| Research per vertical, African market | Yes (§9) | M3, L4, L5 |
| Conversion levers | Yes (§11) | M4 |
| Data-request script | Yes (§12) | L6, L8 |
| What exists today and what doesn't | Yes (§8 matrix, §10 "Today" column) | Incomplete (M2) |
| Exceptionally illustrated | Six SVGs, legend-coded matrix | L1, L7 |

## Code claims I verified (all against `main`)

All of these hold unless the finding noted says otherwise.

**Outcome map** (`outcome_map.py`)
- `:17-40` ENTRIES and DOMAIN_ALIAS: GENERATOR_SUPPORT moves MG-2 and checks MG-5 and MG-4; HEADROOM moves MG-1; EVIDENCE_GAP and EVIDENCE_READINESS route to Assure.
- `:36, :177-180`: idle-charger entry and record.
- `:149`: "MG-5 has none (R9)".
- `:150-180`: CONTRIBUTIONS. Only mini and EV earnings records exist; there are no cold or CC money records.

**Catalogue** (`catalogue.py`)
- `:38-39`: `measured = missing is None`.
- `:43-68`: 22 outcomes, of which 6 are not measured.
- `:72-83`: row sentences.

**Status** (`status.py:67-102`): the gate order, and the On-track rule used in M1.

**Claims** (`chain/claims.py`)
- `:42-43`: DISRUPTED_STATES and NOT_DISRUPTION_MECHANISMS.
- `:124-134`: warnings are not threads.
- `:151-161`: primary-Protect rule.
- `:202, :210, :212`: verified_n and disrupted_n.
- This confirms (a) and (b).

**Warnings and graph**
- `outcomes/warnings.py:29`: KINDS has no CHARGERS_MOSTLY_IDLE.
- `chain/graph.py:47-50`: KNOWN_GAPS BL-06.
- This confirms (g).

**Card builder and labels**
- `site_outcomes/read.py:855-977`: the four card builders. Optimize is never summed; Assure value lines and Protect fuel lines are not summed.
- `chain/vocabulary.py:298, 318, 323, 537, 544-553, 580`: the basis texts and INCOME_LABELS.

**Money strategies**
- `chain/strategies/base.py`: "No strategy computes new money".
- `recorded_amount.py`: always NO_RECORDS.
- `priced_energy.py`: counts only COMPLETE and PARTIAL days; potential only when SUPPORTED.

**Data stores**
- `financials/assumptions.py:32`: three declared keys.
- `migrations/versions/0054`: fuel quantity in L only, no price column.
- No customer, billing, payment, odometer, crate or occupancy table in any migration. The table list was grepped.
- No cost column on work_case or maintenance_record.

**Site composers**
- `site_outcomes/mini.py:596-603` settled; `:846-853` MG-5 reading "kWh not served over the whole day"; `:1144-1146` the fixed Cash collected and Site earnings contributors. This confirms (c).
- `site_outcomes/cold.py:71-72, 164-168, 181-191`: no Grow or Cost contributors before warnings.
- `site_outcomes/ev.py:45-46, 171-174, 201-215`: the billing "not connected" lines.
- `site_outcomes/board.py:60-61`: the trial cost-change text. This confirms the nuance in (d).

**Mock**: `frontend/mockups/v70/outcomes.js:189-192`, the Grow, Optimize, Protect and Assure card texts as quoted.

**Field ingestion**: `field/assetops_field/{csv_upload,modbus_poller}.py` exist. The profiles in `field/profiles/` are named "illustrative".

## Research checks (WebFetch or WebSearch)

**Confirmed at source**
- World Bank/ESMAP: $0.55 → $0.38 → $0.20/kWh.
- AMDA 2020 via Green Building Africa: $733 per connection, 99.1%, under $5 ARPU, more than 52 weeks.
- SEforALL UEF: USD 592 per connection, with remote verification.
- Microgrid Knowledge: $6,824/kW, -20%, $3,000 benchmark (see L4).
- CleanTechnica: KSh 8/16 tariff; BasiGo KSh 20/km against KSh 30–50/km.
- Mongabay: KSh 1M upfront, $3,000/month minimum, midday top-ups.
- FAO: 23% and 13.3%.
- Rockefeller YieldWise: 20–30%. The source page itself lists Nigeria under "East Africa".
- MIT Solve: 2 → 21 days, ₦100 per crate per day (see L4).
- SokoFresh: lease and lease-to-own, 40% (company claim).
- TechCrunch Spiro: 60,000+ bikes, 1,500 stations, 150–200 km/day, $3/day, 30% lower per km (CEO claims).
- Acumen Ampersand: 41% of earnings on fuel, +46% take-home.

**Corroborated by search snippet**: Odyssey/CBEA name "Average Revenue per User" and "Power Reliability" as essential KPIs.

**Diesel LCOE**: Zebra et al. 2021 gives $0.92–1.30/kWh diesel against $0.54–0.77/kWh hybrid, matched by search. I did not open the full paper.

**Not matched**: CrossBoundary mesh-grid 99% / 27% / 213% (M3).

**Not checked**: REPP roundtable, DARES IVA ToR, BASE CaaS, GET.invest, Verra, South Pole and AERA. These were not individually fetched; the doc tags most of them "snippet".

## Soundness of the ranked gaps

The order is defensible.
- #1 and #2 need no client data and are relevant to the demo. M5 still needs to state #1's precondition.
- #3, billing and payments plus customer meters, is correctly called the highest client value. The ARPU and collections ask is what African mini-grid funders and RBF programmes (NEP/DARES, UEF) verify against.

Changes I recommend:
- Fold #5, #7 and loss pricing into the existing PR-3 keys and PR-4/PR-5 (M2).
- Consider moving #9, the verification export pack, up. RBF verification is the most direct conversion lever for funded developers, and it largely reuses evidence that already exists.
- Add non-technical loss as a follow-on to #3 (L8).

The "beside, never added" ruling for collected against estimated income is consistent with the never-sum rules for Optimize and Assure. It should go to the owner as the doc proposes.

## Residual risk

- Several research figures are older than two years: AMDA 2020, the 2022 ESMAP cost, ColdHubs 2019. Refresh them before any client deck.
- The AMDA 2024 KPIs were not extracted, as the doc itself says.
- The document mixes owner-facing code vocabulary with client-ready lines. Before reuse, separate §11–12 into a client-safe extract with no MG-x or strategy names.
