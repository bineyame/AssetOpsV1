# Architect answer: why the non-Kobo Site pages look empty (walkthrough item 11, 2026-11-10)

Architect: Claude (the binding in `.ai/ROLE_CONFIG.md` is Claude, set by the owner on 2026-10-27), working under the
owner's delegation (`.agent/owner-away-architect-decides-2026-11-08.md`: "make sure it makes decisions based on
understanding of how real sites work and what assetops is trying to achieve, no cutting corners on fundamentals").
Build audited: `assetops_polish_client4_test`, S = 2026-11-08, code b234cea2a, live app 8990/5490 (GET only, one page
at a time). Sources: 74 page texts captured from the live app (scratchpad `audit/out`, `audit/out2`), the E5 captures,
the code, and read-only SQL.

## For the owner, in plain words

**Short answer: it is both. Two root causes explain most of the empty values, and neither is "no data".**

1. **Product bug, Cold room and EV depot.** The readings are there and the product has analysed them. But the Site
   pages find an analysis only when the period you pick matches the analysed period exactly. The story analyses the
   cold room from 16:00 to 17:05 and the depot from 08:00 to 09:05. If you open a whole day or a week, which is what
   the day picker and our story links do, every panel says "Unknown", "Not assessed" or "No cold assessment". If you
   open exactly 16:00–17:05 on 8 Nov, the same page shows the 4.9 °C peak, "Service affected" and "Stock may be at
   risk". On a week it even says the temperature objective is "not declared", while the card beside it shows the
   declared 2–4 °C. A real cold room or depot is analysed in many short periods a day, so this is a real product
   defect, not a demo quirk.
2. **Story data defect, Kisiwa.** Our story builder sends each Kisiwa night as if a different recorder had been
   switched on. A night runs from 6 pm to noon, so every calendar day mixes two "recorders". The product correctly
   refuses to blend them, so 9 of Kisiwa's 11 days were never analysed (database: 9 dispatch runs "ambiguous").
   That one defect is behind "Two overlapping series…", "no generator period assessed", "No fuel cost estimated",
   and the Portfolio's "Kisiwa 0 of 7 days checked". An earlier ruling put that last one down to the data and the
   design; it was this defect. A real island gateway keeps one recording session, and the product already supports
   that (Kobo uses it). The fix is in the story tool only.
3. **Honest gaps that need integrations we have not built** (billing and collections, bus roster, odometer,
   stock value, work-order costs, sign-in): these values are correct to say "not available". For the client they
   should read as a clear roadmap, not as errors.
4. **Smaller product defects found on the way:** Kisiwa's chart shows Kobo's meter names ("Clinic meter", "Mill meter");
   Kisiwa days that could not be analysed are shown as "Checked: nothing to report" (an over-claim); the Fuel tab
   shows "Unknown" for about 3 s before the nights load; the EV revenue card says "Not known yet" next to a stated
   USD 4.50 estimate; the "of the last 31 days" counts include days before the Site existed.

**For Thursday's technical demo:** fix the Kisiwa story tonight (tool change, before the build). Give the presenter
story links to the exact analysed periods for Cold and EV, and land three small screen fixes. **Before the client
session:** fix the product so a day or week shows its analysed periods. That is the main fix, about 2 units.
Declare Kisiwa's objectives, and turn the "not built" lines into a short roadmap. **Story order:** lead with Kobo
and then Kisiwa; show Cold and EV briefly, each on its analysed period.

Counts (56 unresolved values, one row each below): **A DATA 17 · B PRODUCT BUG 17 · C NOT BUILT 16 · D CORRECT 6.**
Two root causes produce the empty-looking pages. PB-1 explains 9 of the 17 B rows, and those 9 blank most Cold and
EV panels. DATA-1 explains 5 of the 17 A rows, the most visible Kisiwa ones.

## Key evidence

- Cold default selection: `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py:2222-2228`.
  It requires `sel.window_start <= :lo AND sel.window_end >= :hi`, so a stored window has to contain the request.
- EV default selection: the same file, `:2933-2941`. It requires `sel.window_start = :lo AND sel.window_end = :hi`,
  an exact match. The story stores 2 selections per EV day, 08:00–09:00 and 08:00–09:05.
- DB `analytic_run_selection`. Cold: 4 days × 2 analytics, each 16:00–17:05. EV: 3 days × 2 windows. Kisiwa:
  11 daily dispatch runs. 30 Oct and 9 Nov are `SELECTED_UNIQUE`; the other 9 are `AMBIGUOUS`.
- Kisiwa epochs: DB `accepted_evidence` has `epoch-1`…`epoch-10`, each spanning 2 calendar days.
  `tools/demo_combined_kisiwa.py:789` publishes `f"epoch-{item}"` on a fresh gateway state, and `:1189` publishes
  `f"epoch-add-{ymd}"` in the same way. `backend/assetops_backend/analytics/cohort.py:93-101` (`_multi_epoch`) then
  refuses to blend them, as designed. The fix mechanism already exists: `host/tests/test_s6_verification_replay.py:195-201`
  `gateway_dir` (DD1a1-R5), used by Kobo in `tools/demo_combined_kobo.py:369-385`.
- Live probes. The exact window `/sites/COLD-LAB-001?from=2026-11-08T16:00:00Z&to=2026-11-08T17:05:00Z` shows "Service
  affected · Confidence: partial · Stock may be at risk · Peak 4.9 °C". The exact EV window shows "USD 4.50 … 15.000 kWh".
  The left-menu default (no window) works, because it uses the latest analysed window. The day and week links do not.
- Story links are written as whole UTC days on purpose (`tools/demo_combined.py:308-315`, DD1b1-R2 S1), so that
  the Action agreed after the event is listed.

## The table

Class: A DATA · B PRODUCT BUG · C NOT BUILT · D CORRECT AND HONEST. "Day/week" means any window that is not the
exact analysed period, including the story links and the day picker.

### GreenHarvest Cold Room (COLD-LAB-001)

| # | page | element | value shown | class | root cause | fix |
|---|---|---|---|---|---|---|
| C1 | Overview (day/week) | status bar | "Unknown · Confidence: Unknown · Stock risk not known yet" | B | `postgres_assessment_store.py:2222-2228` containment rule; analysed period is 16:00–17:05 | PB-1 |
| C2 | Overview (day/week) | objective line | "Chamber temperature objective not declared for this window" (the Protect card on the same page shows declared 2–4 °C) | B | `cold_site_reads.py:94,403` falls to `OBJECTIVE_ABSENT` when nothing is selected | PB-1 |
| C3 | Overview (day/week) | What happened, Chamber temperature, Needs attention | "No cold assessment for this window" ×3 | B | as C1 (`coldSiteViews.tsx:711,735,751`) | PB-1 |
| C4 | Overview (day/week) | Possible cost, Next step | "No product exposure consequence assessed", "No recorded next step" | B | as C1 | PB-1 |
| C5 | Health, Performance › Temperature, Findings, Evidence, Financials › Scenarios (day/week) | tiles and lists | "Unknown" ×3, "Not assessed" ×6, "0 open", "No selected cold assessment covers this window yet" | B | as C1 | PB-1 |
| C6 | Health | asset column | raw asset IDs beside names (`f1fbff69-…`) | B (Low) | `ColdHealthDepth.tsx:139` `AssetCell` prints the id | PB-6 |
| C7 | Overview › Grow revenue | outcome | "Not measured yet · Needs occupancy, storage contract, income and sales records" | C | no occupancy, contract or sales integration; no cold revenue measure in `outcomes/objectives.py:57-73` | RM-1 roadmap wording |
| C8 | Overview › Optimize | Repair and call-out | "No cost on work record WR-006 · Unknown" | C | `maintenance_record` has no cost column (DB schema) | RM-1; integration rank 3 |
| C9 | Overview › Optimize | Cooling energy | "Not available yet · no cooling energy meter" | A | Cold Foundation declares no cooling-energy meter | none for the demo (it would need a new simulated sensor) |
| C10 | Overview › Protect | Cooling recovery | "no reading confirms that cooling restarted" | A | failure-day fixture ends at 17:05, before any recovery reading | optional DATA-12 (a longer failure window) |
| C11 | Overview › Protect | Compressor and backup condition | "not assessed" | C | no condition model | RM-1 |
| C12 | Overview › Assure | Storage service level, Loading and door records | "Not available yet" | C | no storage-contract or door-log integration | RM-1 |
| C13 | Financials | Stock value, Product exposure rule, Currency; exposure line | "Not declared"; "Not priced yet" / "Unpriced" | C | `financials/cold_consequence.py:51,333` is always `COLD_VALUATION_NOT_APPROVED` (no approved product valuation exists); DB has 0 Cold assumptions | keep honest; integration rank 5 |
| C14 | Financials | Confirmed loss | "Unknown · Temperature exposure does not prove spoilage" | D | correct boundary | keep |
| C15 | Findings, Work | scope notes | "Cold-chain Findings are not in the global Findings list", "Global Actions does not include cold-chain Actions yet", "Manage in Findings · Not available yet" | C | no estate domain-Action join (D-E5.27) | RM-1 plain roadmap wording |
| C16 | Findings (all three Sites) | lens chips | "Cost / Risks / Opportunities · Not available yet" | C | Site-level lens filtering is not built for these Sites | RM-2: hide on client screens (**owner approval: mockup**) |
| C17 | Work › Actions | Due | "Due dates are not yet set · Not set" | A | the story Action has no due date | DATA-13, if the Action path takes a due date (pre-flight); otherwise RM-1 |

### Depot Charging Hub (EV-LAB-001)

| # | page | element | value shown | class | root cause | fix |
|---|---|---|---|---|---|---|
| E1 | Overview, Health, Performance › Availability and Sessions, Financials (day/range) | status and tiles | "Unknown · Confidence: Unknown", "No selected EV session assessment covers this window yet", "Delivered energy Unknown", "Lower bound: Unknown. Upper bound: Unknown" | B | `postgres_assessment_store.py:2933-2941` exact-equality rule | PB-1 |
| E2 | Financials (range) | consequence row | "Tariff not declared" while "Assumptions in use: Tariff 0.30 USD/kWh" | B | the no-consequence row blames the tariff | PB-1; copy in PB-6 |
| E3 | Financials | header total | " USD · selected window" (empty amount) | B (Low) | an empty total still renders its unit | PB-6 |
| E4 | Overview › What happened, Sessions (range) | note | "EV source provenance is mixed or unverified; session outcomes cannot be assessed." | B | `evidence/source_provenance.py` `MULTIPLE_RUNS_WITHOUT_COMPATIBLE_BASIS`: every story day is its own registered run, so any multi-day union is MIXED | PB-1b (provenance per analysed period) |
| E5 | Overview › Grow revenue | Estimated income, Charging delivered | "Not known yet · 0 of 1 day checked · 1 with too little data, not counted", next to the stated USD 4.50 estimate | B | `chain/grading.py` `classify_day` grades meter-interval coverage of the 08:00–16:00 operating hours; a charger meter reports only while charging (15 min, so LOW) | PB-3 |
| E6 | Overview › Grow revenue | Target | "No target set yet" | C | no EV revenue measure in `outcomes/objectives.py:57-73` | RM-1; backlog |
| E7 | Overview › Grow revenue | Charger use | "Not available yet · connector capacity not read" | A | EV Foundation declares no connector rating (single-line diagram: "Rating not declared · No connector declared") | DATA-4 (**owner approval: story**) |
| E8 | Overview › Optimize | Energy cost per km | "Not measured yet · needs odometer readings" | C | no telematics or odometer integration (objective EV-2 is declared) | RM-1; integration rank 4 |
| E9 | Protect, Assure | Departures affected, Departures against the timetable | "not known yet", "no bus roster connected" | C | no roster integration | RM-1; integration rank 4 |
| E10 | Grow, Assure, Financials, Evidence | Energy billed vs metered, Collections, Billing system | "no settlement records", "Not recorded", "Unknown · No payment feed" | C | no billing integration | RM-1; integration rank 1 |
| E11 | Protect | Warranty | "Not available yet · no warranty record" | C | no warranty record type | RM-1 |
| E12 | Protect, Assure | connector status | "16 min unknown", "Missing 3 Nov 08:00–08:16" | D | the fault fixture has a real status gap | keep |
| E13 | Overview, Finding | Review recommendation | "Not available yet" | C | review needs sign-in (BL-54) | RM-1 ("needs sign-in, coming") |
| E14 | Evidence › Sources | diagnostics | "Source 1 · Unknown · diagnostic received No source-specific record · cadence … · contact …" | A | the story harness drops gateway diagnostics: `host/tests/test_s6_verification_replay.py:221-222` answers 201 and stores nothing; DB `gateway_diagnostic` has Kobo rows only | DATA-5 |
| E15 | Evidence › claim rows (range) | coverage | "Coverage duration cannot be calculated from the selected records" ×5 | B | as E1 and E4 | PB-1 |
| E16 | Foundation › Single line diagram | slots | "Main CB not declared"; "Grid supply, breakers, feeder meters … not declared" | A | minimal EV Foundation | DATA-4 |
| E17 | Financials | Lost revenue | "Unknown · Unmet demand not established" | D | needs a roster; correct boundary | keep |
| E18 | Financials | Portfolio roll-up | "Not available yet" | C | EV money is not rolled up to the estate | RM-1 |

### Kisiwa island mini-grid (KISIWA-001)

| # | page | element | value shown | class | root cause | fix |
|---|---|---|---|---|---|---|
| K1 | Overview, every day except 30 Oct and 9 Nov | What happened | "Two overlapping series of records report the same times; neither is chosen, so the day is not assessed"; "Checked (cannot determine): generator not used"; "No assessed period is selected" | A (story build defect) | `tools/demo_combined_kisiwa.py:789,1189`: one epoch per night on a fresh gateway; nights run 18:00–12:00, so each day holds 2 epochs; `cohort.py:93-101` returns AMBIGUOUS (DB: 9 of 11 runs) | DATA-1 |
| K2 | Overview › Optimize, Protect | Fuel cost, Battery, Service delivery | "No fuel cost estimated for this day", "no generator period assessed on this day", "demand not measured · Unknown" | A | as K1 | DATA-1 (confirm after the build) |
| K3 | Portfolio | Kisiwa days checked | "0 of 7 days checked" | A | as K1. This corrects `.agent/architect-combined-pass-2026-11-08.md` row 4, which put it down to the data and the ruled design | DATA-1 |
| K4 | Overview, Findings | claim | "Checked: nothing to report"; "Every day in this window was assessed and matched for Findings"; "A complete, current search found no Finding" on days that were never analysed | B (Medium, honesty) | the list state is CURRENT when a day's run is COMPLETED, even with cohort AMBIGUOUS (`SiteFindingIndex.tsx:727-740`, `OverviewFindingList.tsx:343`; backend Site Findings list state) | PB-4 |
| K5 | Overview | limitation wording | "…report the same times…" when the two epochs follow one another | B (Low) | `dispatchWords.ts:59-60`: one sentence for both `cohort.py` reasons | PB-6 |
| K6 | Overview chart | series legend | "Feeder demand · Clinic meter / Mill meter / Residential meter" (Kobo names, on a Site with Households, Cold store and Water pump) | B | `SiteWindowOverview.tsx:701` `idWords(c.device_id)`, not the Foundation `display_name` (R-LOAD, DIESEL-1 §9p.5, missed this legend) | PB-5 |
| K7 | Overview › Grow, Optimize, Protect | objective | "No objective declared", "No target set yet" | A | ruled "none for the demo" (`.agent/build-sheet-DIESEL-1.md` §9p.4; `tools/demo_combined.py:121`) | DATA-6 |
| K8 | Overview › Assure | coverage line | "20 of the last 31 days have no checked readings yet" | B + A | `site_outcomes/mini.py:362-392` always counts 31 days (the Site was created 28 Oct and its readings begin 30 Oct); the story has 11 nights | PB-7; existing `add-dates` |
| K9 | Overview › Assure | coverage line | "8 of the last 31 days are only partly checked" | A | the story simulates only 18:00–12:00; 12:00–18:00 is never seeded | DATA-7 (backlog, **owner approval: story**) |
| K10 | Overview › Grow, Assure | Productive use | "Productive use not assessed: no productive-use equipment declared for this site (0 kWh)" | A | the Kisiwa template marks no load as productive, though the Water pump and Cold store (ice and fish) are | DATA-8 (**owner approval: story**) |
| K11 | Overview › Grow; Financials › Assumptions | Price per kWh | "Not available yet · no price per kWh declared" | A | DB: Kisiwa has a fuel price only (1.25 USD/L) | DATA-8 (with K10) |
| K12 | Overview › Grow | Cash collected, Site earnings | "no billing or payment records", "needs site income, operating cost and capital records" | C | no billing or accounting integration | RM-1; integration rank 1 |
| K13 | Overview › Protect | Battery and generator condition | "not assessed … early warnings only" | C | no tested wear model (`outcomes/warnings.py` PRICE_NEEDS) | RM-1 |
| K14 | Overview › Protect | Generator | "No preventive plan recorded" | A | DB `maintenance_plan`: 0 Kisiwa rows | DATA-10 |
| K15 | Overview › Protect | Backup readiness | "No backup event in this window · Unknown" | D | no event happened | keep |
| K16 | Health | inputs | "Not in the gateway's latest report · Unknown" ×8; Battery "Inputs missing" | A | as E14 (diagnostics dropped by the harness) | DATA-5 |
| K17 | Performance › Fuel | first view | about 3 s of hour mode: "Fuel balance: Unknown" ×7 for 10 Nov, then the nights | B | `MiniPerformance.tsx:1633` renders hour mode while `useFuelNights` is still null (loading); the nights read took 2.9 s live | PB-8 |
| K18 | Performance › Service, Backup, Renewable, Dispatch (week) | tiles | "Not assessed", "We have not checked this period" | A | as K1 | DATA-1 (confirm) |
| K19 | Overview, 10 Nov (S+2) | day | "We have not checked this period · No amount: day not checked · This is not zero" | D | no day built after S+1 | existing `add-dates` |
| K20 | Performance › Renewable, 29 Oct hours | rows | "No selected assessment for this hour" | D | before the first story night | keep |
| K21 | Financials | overview tiles | "Not established" ×3, "Data confidence: not assessed" | A | dispatch-derived fuel cost blocked by K1 | DATA-1 |

Not a defect: `DEVELOPMENT_TENANT_OPERATOR_CONTEXT` and `SERVER_ADMINISTRATIVE_TRIGGER` appear only inside closed
"Technical details" (they were captured with details opened; this exemption is in Addendum 5). EV's
"Investigate connector 2" is already fixed in tonight's rebuild (D-E5.9).

## Rulings

- **D-E5.29 Verdict.** Item 11 is a product bug for Cold and EV (PB-1) and a story data defect for Kisiwa (DATA-1).
  The rest is honest NOT BUILT (C) plus small product defects. "No data" is not the main explanation for any Site.
- **D-E5.30 DATA-1 lands tonight.** One recording session for Kisiwa. It is faithful to a real island gateway and
  uses a mechanism the product already has. Kisiwa's daily boards, the Portfolio coverage and the fuel cost come
  alive. Kisiwa may gain dispatch Findings it has never had (for example, generator minutes). This content has not
  been seen before: the coordinator reads the Kisiwa board for 2–8 Nov in the fresh build before the demo, and the
  demo script quotes Kisiwa figures from the build, as in D-E5.14. If DATA-1 misses the build or its review, keep
  the current tool and present Kisiwa through Fuel nights, the fuel Finding and verification only.
- **D-E5.31 PB-1 is the main product fix, before the client session.** Rule for Cold and EV Site reads with a
  window: (i) a stored selection that contains or equals the window: unchanged. (ii) otherwise, the selected
  analysed periods lying wholly inside the window are listed, and the status bar and Needs attention use the most
  recent one with an open Finding, or else the most recent one. The window bar adds `Analysed period: {from}–{to}`
  (one period) or `Analysed periods in this range: {n} · showing {from}–{to}`, with each period a link to its exact
  window. (iii) none inside: today's empty state, with the words `No analysed period in this range`. Pinned mode
  is unchanged. EV source provenance is judged per analysed period, never over the union. Real sites are analysed
  in many short periods a day; showing a range as "Unknown" is not honest. **MOCK DEVIATION** (one added line
  under the v6.9 window bar): logged; the owner is informed and sees it at the walkthrough.
- **D-E5.32 Thursday mitigation for Cold and EV.** Story links gain a second link per Cold and EV story day for the
  exact analysed period. The whole-day link stays, because it still lists the Action agreed after the event.
  Presenter rule: open the analysed-period link for what happened and the money; open the whole-day link only
  for Work and Actions.
- **D-E5.33 Kisiwa objectives (reverses DIESEL-1 §9p.4).** Declare MG-2 (avoidable generator minutes, target 0) and
  MG-5 (unserved critical kWh, target 0) for Kisiwa, after DATA-1. The earlier "no demo beat" reason fails now: the
  board shows three "No objective declared" lines to a client. MG-1 waits for DATA-8. This is a story change; the
  owner is informed, and no mockup changes.
- **D-E5.34 NOT BUILT wording (RM-1).** Every C value keeps its slot (the mockup is the layout spec) but reads as a
  short roadmap fact in plain words. Examples: `Billing records are not connected yet`, `Reviewing a recommendation
  needs sign-in, which is coming`, `Cold-room findings are listed here; the estate list adds them later`. Never
  "error", never a code. **RM-2:** on client screens, hide the Site Findings lens chips on Sites where no lens is
  supported (Cold, EV, Kisiwa). **Owner approval needed** (this changes the v6.9 layout).
- **D-E5.35 Integration ranking for the client** (what would remove the most C values and matters most to a buyer):
  1. billing and collections (Grow revenue on all four Sites; verifies revenue);
  2. sign-in (unlocks price editing, recommendation review and named approvals, BL-54);
  3. work-order cost and CMMS (repair cost; prices early warnings);
  4. fleet roster and telematics (EV departures, cost per km);
  5. cold stock value and occupancy (WMS).
- **D-E5.36 Story order.** Lead with Kobo (the full chain), then Kisiwa (fuel night → Finding → Action →
  verification, and after DATA-1 its board). Show Cold and EV as short "same engine, other asset types" beats on
  their analysed periods: the Overview Protect card and one Finding each. Until PB-1 lands, do not open Cold or EV
  Health, Performance or Financials on a day or week window.
- **D-E5.37 More Cold and EV days.** Not before PB-1: extra days on today's code only add more blank day views.
  After PB-1, fill the story week with ordinary days through the existing prepare path. This is DATA-11: Cold for
  2, 3, 4, 6 and 7 Nov; EV for S-6 to S-1, one ordinary session a day. Estimated prepare cost is about +10 min;
  the pre-flight confirms it from the last run's per-day seconds. Owner informed (story change).

## Cards

### Thursday (tools and backend MUST merge before tonight's build; frontend may land after)

**DATA-1 Kisiwa one recording session (Opus, 0.5 unit, about 80 lines; fresh Claude review; before the build).**
- `tools/demo_combined_kisiwa.py`:
  - `:789`: publish every night with one epoch, `kisiwa-gw-1`, on one persistent gateway state
    `work / "kisiwa-gateway"`, passed as `gateway_dir=` (`host/tests/test_s6_verification_replay.py:195-201`,
    the Kobo pattern `tools/demo_combined_kobo.py:369-385`).
  - `:1189` (add-dates): the same epoch and the same `work / "kisiwa-gateway"`, so the sequence continues across
    processes.
  - Docstrings cite D-E5.30.
- New finish check `KISIWA-COHORT` in `tools/demo_combined_finish.py`: every Kisiwa `dispatch` selection whose day
  has readings has `cohort_status = 'SELECTED_UNIQUE'`; it raises otherwise.
- Tests:
  - `backend/tests/test_demo_combined_finish_rows.py`: KISIWA-COHORT, pass and fail rows.
  - A unit test in `backend/tests/test_k1_kisiwa_fixtures.py`: the publish call gets one epoch and one gateway dir
    for every night.
- Do not change night figures. The fuel-balance guards (`run_guards`) must pass unchanged.
- Prepare time is about +0–3 min, because dispatch now analyses 10 days.

**DATA-2 Analysed-period story links (Sonnet, 0.25 unit; before the build).**
- `tools/demo_combined.py:308-315`: for each Cold and EV day with `start` and `end`, add a row
  `"{code} analysed period, {kind} day S{offset}d ({day} {start:%H:%M}–{end:%H:%M})"` → `?from={start}&to={end}`
  (`/ev` for EV). Keep the whole-day row.
- Tests: `backend/tests/test_demo_combined_links.py`.

**PB-5 Kisiwa feeder legend (Sonnet, 0.25 unit; frontend, after the build).**
- `frontend/src/sites/SiteWindowOverview.tsx:701`: label = the Foundation device `display_name` for `c.device_id`.
  Use the same map as `siteViewModel.ts:778-801`, falling back to `idWords`. Kobo bytes are unchanged (R-LOAD).
- Test: a Kisiwa fixture expects "Households meter", "Cold store meter" and "Water pump meter".

**PB-8 Fuel tab loading (Sonnet, 0.1 unit; frontend).**
- `frontend/src/sites/MiniFuelNights.tsx` `useFuelNights` returns `{ loading | nights | none }`.
- `MiniPerformance.tsx:1633`: while loading, show `MINI_LOADING`; hour mode only for `none` or failed.
- Test: no "Fuel balance: Unknown" before the nights resolve.

**PB-6 Copy batch (Sonnet, 0.25 unit; frontend).**
- `dispatchWords.ts:59-60`: split AMBIGUOUS_COHORT by reason. Epochs that follow one another read `Readings
  for this day came from two separate recording sessions of one source; they are not joined, so the day is not
  analysed`. The overlapping case keeps today's sentence.
- EV Financials:
  - The no-consequence row reads `No analysed charging session in this window` (not "Tariff not declared").
  - Hide the empty " USD" total.
- `ColdHealthDepth.tsx:139`: the asset id moves to Technical details.
- Tests: the matching component tests.

### Before the client session

**PB-1a Cold analysed periods (Opus, 1 unit; backend).**
- `postgres_assessment_store.py:2168-2240` `_snapshot`, default mode only: the D-E5.31 rule.
- `analytics/cold_site_reads.py` carries `analysed_periods: [{from, to, href}]` and `shown_period`.
- Tests:
  - Cold store tests: day window over one period; week over four (the failure day wins, because it has the open
    Finding); a window with none; pinned unchanged.
  - Site read and API tests.
- The prebuilt variants pick it up in the build.

**PB-1b EV analysed periods (Opus, 1 unit; backend).**
- The same rule at `postgres_assessment_store.py:2895-2945`.
- When two stored windows share a start, the widest wins (08:00–09:05).
- `ev_site_reads.py` gives provenance per period (E4).
- Tests: as PB-1a, plus E4.

**PB-1c Window bar line (Sonnet, 0.25 unit; frontend).**
- The D-E5.31 literals in the Cold and EV window bars, with period links.
- Tests: Cold and EV view tests. MOCK DEVIATION header comment.

**PB-3 EV event-driven grading (Opus, 0.75 unit; backend).**
- `chain/grading.py` and the EV delivered-energy measure entry in `config/chain/coverage-policy-v1.json`.
- For a metered-when-charging measure, covered time is connector-status-known time (idle with known status counts
  as zero energy), not meter-interval time.
- The EV story's status reports cover only about 16 min, so pair this with DATA-11's status heartbeat; otherwise
  E5 stays honestly LOW.
- Tests: chain grading tests.

**PB-4 Unanalysed days are not "checked" (Opus, 0.5 unit; backend and frontend).**
- A day whose selected run has cohort AMBIGUOUS or NO_COHORT makes the Site Findings list PARTIAL with the
  accepted term "not analysed yet", never CURRENT or "Checked: nothing to report".
- The pre-flight pins the list-state builder behind `sfi2` (Site Findings) and the Overview list. The frontend
  words exist (`SiteFindingIndex.tsx:727`, `OverviewFindingList.tsx:343`).
- Tests: one backend list-state test with an AMBIGUOUS day; one frontend test.

**PB-7 Coverage denominator (Sonnet, 0.25 unit; backend).**
- `site_outcomes/mini.py:362-392`: `requested = min(31, days since the Site's first accepted reading)`.
- Literal: `since readings began on {d}: {g} of {n} days …`.
- Tests: mini outcome tests; update the golden rows.

**DATA-6 Kisiwa objectives (Sonnet, 0.25 unit; tools; after DATA-1).**
- `backend/conversions/demo-objectives.json`: add MG-2 and MG-5 lines for KISIWA-001 (target 0, the same
  source note).
- `tools/demo_combined.py:114-121`: Kisiwa instant = `install_at + TARIFF_AFTER_INSTALL`.
- `objective_site_count` and CO-6 change from 3 to 4 (`tools/demo_combined_finish.py`).
- Tests: `test_demo_combined_finish_co1.py`.

**RM-1 Roadmap wording (Sonnet, 0.5 unit; frontend and backend vocabulary).**
- Every C row's literal, per D-E5.34. A reviewer checks that each one names what is missing and that none reads
  as an error.

**RM-2 Hide unsupported lens chips (Sonnet, 0.1 unit; frontend).** Only after the owner approves.

**DATA-5 Story diagnostics (Opus, 0.5 unit; harness).**
- `host/tests/test_s6_verification_replay.py:220-222`: forward gateway diagnostics to the product's diagnostics
  ingestion, the path behind Kobo's `gateway_diagnostic` rows. The pre-flight confirms the endpoint.
- This touches every story Site, Kobo included: recapture Kobo Health.

**DATA-10 Kisiwa generator service plan (Sonnet, 0.25 unit; tools).**
- Use the plan path that seeds Cold PM-009 and PM-010 (the pre-flight names it). One 250-hour generator service,
  due within the story month.

**DATA-11 Cold and EV story week (Sonnet, 0.5 unit; tools; after PB-1).** Per D-E5.37. Prepare time is about
+10 min (to confirm).

**Backlog (not demo-critical, owner 2026-11-05):**
- DATA-7 Kisiwa full-day runs (Opus, 1.5 units, story re-tune; **owner approval**).
- DATA-4 EV Foundation v2: connector rating, grid supply meter (Sonnet, 0.5; **owner approval: story**).
- DATA-8 Kisiwa productive-use loads and price per kWh (Sonnet, 0.5; **owner approval: story**).
- DATA-12 longer Cold failure window.
- DATA-13 Action due dates.
- An EV revenue measure.
- Work-record cost.

### Size summary

- Thursday: 1.35 units (DATA-1 0.5 and DATA-2 0.25 before the build; PB-5, PB-6 and PB-8, 0.6, after it).
- Before the client session: about 4.6 units (PB-1a/b/c 2.25, PB-3 0.75, PB-4 0.5, PB-7 0.25, DATA-6 0.25,
  RM-1 0.5, RM-2 0.1). Optional, about 1.25 more: DATA-5 0.5, DATA-10 0.25, DATA-11 0.5.

### Owner approvals needed

- RM-2: hide the lens chips on client screens (mockup change).
- PB-1c: the added "Analysed period" line (MOCK DEVIATION, informed; approve at the walkthrough).
- Story changes, informed: D-E5.33 Kisiwa objectives and D-E5.37 more Cold and EV days. Backlog items that need
  approval: DATA-4, DATA-7, DATA-8.
