# Delivery: the order, the slices, the gates and the demonstration build

**AssetEcon · Layer 4 pack document 6 · AssetOps Architect (Claude) · 19 Nov 2026 · derived from design rev 16.7, updated to `rev 16.12` (sign-in and roles in step 3C; OD-20; the engagement path tied to its steps; OD-21 to OD-23; checked against `rev 16.10` to `rev 16.12`: step 3C no longer waits for step 1, and `3B3` serves no stored figure as a source)**

**What this document is.** The whole path from today's product to the Layer 4 design, in the order the owner approved (OD-9, design §2.9 and Figure 10). It merges and replaces three earlier documents: `phase-plan-and-acceptance.md`, §3–§4 of the retired rev 4.2 of `product-transition-and-roadmap.md` (`.ai/history/layer4-roadmap-rev4.2/`), and `demo-build-cost-plan.md`. It adds slices, gates and tests beneath the design's constructs and no construct of its own. The first fortnight's schedule is a separate document, `two-week-build-plan.md`, which cites this document's slices by ID.

*Serves the objective:* operator executives adopt the product for economic value beyond their monitoring tools. The order below puts that value on their screens as early as the evidence allows, and never ahead of it.

## 1. Where delivery starts, and the order it follows
<!--derives: §2.9; Figure 10; OD-9; OD-13; OD-14; OD-20; OD-21; OD-22; OD-23; D13; D14; D1; Part 1; §2.0-->

**What exists, and stays.** Today's product is the start, not something to clear away (design Part 1). The evidence ledger, the analyses, Findings and threads, the act-and-track carriers, verification, the honesty rules and the screens' frame all stay. Each slice below extends one of them or adds a construct beside it. The single register of changes is design §2.9. Every slice that changes an existing construct names that row.

**The order** is design Figure 10, which is not redrawn here:
1. **Step 1:** correct the last-day figure, and show what the API already computes (CH5).
2. **Step 2:** agree the canonical format and the leaf factor IDs. This is a small step under W1, and it unblocks both lanes.
3. **Step 3:** build in parallel:
   - **3A**, the sources (B3): the record store, the emulators and the contract test;
   - **3B**, the structure (B1, CH1), on today's operational leaves;
   - **3C**, the recorded person (CH2): sign-in and roles first (OD-13, OD-14), then the person on every command.
4. **Step 4:** join the lanes at the money leaves.
5. **Step 5:** targets and the bridge (B2).
6. **Step 6:** decisions and options (CH3). Cost-side decisions start before the join; revenue-side options wait for it.
7. **Step 7:** the plan and the Portfolio (P, CH5).
8. **Step 8:** the three verdicts (CH4).
9. **Step 9:** rights, then cold rooms and EV depots, then pilot onboarding at scale: the EMS API transport, then the edge gateway over Modbus on hardware, tested on a BeagleBone Black (OD-22).

The calibration replays K, M and E (step 0) run in parallel throughout.

**Why this order** (design §2.9):
- **The sources and the structure are independent until the money leaves.** Lane B can read Kobo's actual diesel, 1,180<!--fig:sites.lakeside-power/Kobo.actual.nodes.diesel_l--> L, and its split by generator running, from today's telemetry and fuel records, while lane A builds the emulators.
- **The recorded person comes before decisions.** A decision that no one is recorded as choosing cannot be shown to an executive (G1).
- **Cost-side decisions start before the join** (the Architect's refinement in §2.9, D13). Kobo's stop threshold is valued from lane B's litres at the typed diesel price. So the first decision reaches a client sooner.
- **The step-2 format is version 1.** It is revised under the contract test when the first operator sample is pinned (the Architect's caution in §2.9; D1).
- **Emulated figures are never Recorded and never benefit** (D14). Every money leaf stays labelled *Emulated* until the operator's own exports replace the emulators.

**How each step is proven.** Every step is proven first on mini-grid, with a cold-room and an EV test case beside it (§2.9). So nothing is built for one vertical or one prospect.

**Structure approval (OD-20).** Approving the recreated pack also approves the structure of steps 1 and 3C (structure page `P1`), so their slices need no sitting. In the computed schedule step 1 starts on day 1 and step 3C on day 5, after spike `0K` on the same lane (`two-week-build-plan.md` §4). `3C0` has no dependency on `1a`: sign-in needs nothing from the Optimize card's correction (`rev 16.12`).

**The engagement path, tied to the steps** (design §2.9):
- **The deep-dive safeguard,** the operator's own target against actual within weeks, holds only once steps 3A, 4 and 5 are live.
- **The first deep-dive's sources** are onboarded by a person in the Analyst role, through 3A's intake and contract test (`3A2`, `3A3`). No step-9 work is needed.
- **Step 9's pilot onboarding** means onboarding at scale: real adapters per source type, replacing the emulators source by source, for more than one operator.
- **Operational integrations (OD-22).** EMS file upload works today and is all the deep-dive needs. The EMS API and the edge gateway on hardware come in step 9, in that order; the Modbus emulator proof stays green meanwhile. None is in the first fortnight.
- **The four categories (OD-21)** need no step of their own: each registry row carries its home category from `3B1`, and the cards read them in `7g`.
- **The daily snapshot (OD-23)** belongs beside the structure read in step 3B; the bridge (`5c`) and the cards (`7g`) read through it. Until its slice lands, `3B3` evaluates on read, under the rule that no stored figure is a source; the snapshot then serves those values without changing the rule. Its slice is not yet in the model (§7, question 4).

## 2. The slices
<!--derives: §2.1; §2.2; §2.3; §2.4; §2.5; §2.6; §2.7; §2.8; §2.9; Figure 10; plan_model-->

A slice is one reviewed unit of one to three commits (W4). Its review depth follows W5: a discovery review for a new schema, mechanism, protected seam or money figure, otherwise a standard review. A slice over 6 units is split before it is built.

The table is generated by `plan_model.py`, which also schedules the first fortnight. The units are the earlier backlog's ranges where the work is the same, and the Architect's estimates where it is new (marked *new*). The structure page is the W1 page the owner approves before that slice is built (§5).

<!--table:slices-->
| Slice | Step | Construct | What it builds | Lane | Units | Depends on | Structure page |
|---|---|---|---|---|---:|---|---|
| `T1` | T | tooling | Heavy-tool slot pool, enforced: tsc, vitest, Postgres test files, browser captures and the heavy database job take one of check-all's two slots; a hook refuses an unpooled run | Lane 4 | 2.5 | none | none |
| `0K` | 0 | CH3 | Spike K: the forward replay adapter behind a new port method, and Kobo's stop-threshold replay on the simulated series | Lane 3 | 7 | none | none |
| `0M` | 0 | CH3 | Spike M: Mto's demand-on-headroom replay through the same adapter | any lane's gaps | 3.5 | `0K` | none |
| `0E` | 0 | CH3 | Spike E: Embakasi's charging-schedule replay through the same adapter | any lane's gaps | 4.5 | `0K` | none |
| `1a` | 1 | CH5 | Pin the Optimize card's last-day behaviour, then correct it: the period's figure, or the day and scope stated | Lane 4 | 2.5 | none | P1 |
| `1b` | 1 | CH5 | Render the fields the API already computes on the Portfolio and the site board | Lane 4 | 4 | `1a` | P1 |
| `2a` | 2 | B3 | Canonical format version 1 per source type, and the leaf factor IDs, as code the store and the registry share | Lane 2 | 1.5 | none | P2 |
| `3A1` | 3A | B3 | Commercial record store: immutable raw payload, source-versioned revisions, every record kind of the three verticals declared | Lane 1 | 3 | `2a` | P3A |
| `3A2` | 3A | B3 | File intake on the authenticated site-bound path: dry run, plain-word refusals, late records revise closed periods | Lane 1 | 3 | `3A1` | P3A |
| `3A3` | 3A | B3 | Emulators for billing, collections, fuel purchases and budget lines, and the contract test every real source must pass | Lane 1 | 3 | `3A2` | P3A |
| `3A4` | 3A | B3 | Recorded amounts read by recognition period; a late record marks dependent reads as superseded | Lane 1 | 2 | `3A1` | P3A |
| `3A5` | 3A | B3 | Evidence labels: Emulated beside Recorded on every figure; no total above its weakest part; benefit only from field records (D14) | Lane 4 | 2.5 | `3A1` | P3A |
| `3B1` | 3B | B1 | Structure registry in code: mini-grid in full from leaves to outcomes; Protect and operations measures | Lane 2 | 4 | `2a` | P3B |
| `3B2` | 3B | CH1 | Findings pinned: one registry row per mechanism today; the outcome map's literal removed only after its parity test | Lane 2 | 2.5 | `3B1` | P3B |
| `3B3` | 3B | B1 | Structure read, Site and portfolio: bottom-up on today's operational leaves, coverage, evidence class; no stored figure is a source (its values are later served from the daily snapshot, OD-23) | Lane 2 | 3 | `3B1` | P3B |
| `3B4` | 3B | CH1 | Structure observer: deviations stored as Findings under the owner's rule and outside the factor's tolerance (OD-3) | Lane 2 | 2.5 (new) | `3B3`, `3C1` | P3B |
| `3B5` | 3B | B1 | Site board: driver lines become factor rows generated from the registry, with their Findings on their factors | Lane 4 | 4 | `3B2`, `3B3` | P3B |
| `3B6` | 3B | B1 | Cold-room and captive-EV structures declared and tested from the start (revenue not applicable, never zero) | Lane 2 | 1.5 | `3B1` | P3B |
| `3C0` | 3C | CH2 | Operator accounts: email-and-password sign-in, one set per operator (OD-13); the executive grants and removes roles in Organisation settings, each change recorded (OD-14) | Lane 3 | 3 (new) | none | P1 |
| `3C1` | 3C | CH2 | An authenticated user recorded on every command: trial, domain action and work case writes accept the person | Lane 3 | 3 (new) | `3C0` | P1 |
| `3C2` | 3C | CH2 | Every Action records creator, owner and due date; overdue computed as for maintenance schedules | Lane 3 | 2.5 (new) | `3C1` | P1 |
| `3C3` | 3C | CH2 | UI controls for the work routes that exist only in the API: raise, assign, complete and close, under the person's name | Lane 4 | 4 (new) | `3C2` | P1 |
| `4a` | 4 | B1 | Energy-to-cash observer: delivered, metered, billed, collected, with named leaks | Lane 1 | 2.5 | `3A4`, `3B3` | none |
| `4b` | 4 | B1 | Money leaves from records: revenue, collections, O&M, staff and fuel purchases into the structure read | Lane 1 | 2.5 (new) | `3A3`, `3A4`, `3B3` | none |
| `5a` | 5 | B2 | Targets and budget lines at factor level, declared by the operator with the declarer recorded; objectives become factor targets | Lane 1 | 3 (new) | `4b`, `3C1` | P5 |
| `5b` | 5 | B2 | Attribution: exact for sums, a declared rule for products, a residual only beside an unobserved leaf | Lane 2 | 3 | `5a` | P5 |
| `5c` | 5 | B2 | The bridge on screen, factor by factor, labelled Emulated until the operator's exports replace the emulators | Lane 4 | 3 | `5b`, `3A5`, `3B5` | P5 |
| `5d` | 5 | CH5 | Relabel the Assure line to Actual against target (OD-6) | Lane 4 | 1 | `5a` | P5 |
| `6a` | 6 | CH3 | Decision, option and evaluation records on a factor, with the Finding that opened it and the person who chose | Lane 3 | 3 | `3B3`, `3C2` | P6 |
| `6b` | 6 | CH3 | Bounds as rows: hard, costed, advisory; guardrails generated from them | Lane 3 | 2.5 | `6a` | P6 |
| `6c` | 6 | CH3 | Evaluator: options valued against no action, net of their one-off, through the replay port | Lane 3 | 3 | `6a`, `0K` | P6 |
| `6d` | 6 | CH3 | Stop-threshold carrier as a domain-action apply path, linked to its decision option | Lane 3 | 2.5 | `6a` | P6 |
| `6e` | 6 | CH4 | Stop-setting verification family (an unknown rule fails closed today) | Lane 3 | 2.5 | `6d` | P6 |
| `6f` | 6 | CH3 | Decision view from What can be done: options with no action, values, the rejected one's reason; the choice recorded | Lane 4 | 4 | `6b`, `6c`, `6d` | P6 |
| `6g` | 6 | CH3 | Mto demand and repair decisions (revenue side, after the join), with the quotes emulator | Lane 1 | 4 | `6c`, `4a`, `0M` | P6 |
| `7a` | 7 | P | Plan records (portfolio_plan): items with their chooser and owner (OD-16) and derived states, versions, settings, crew-visit limits by month; one origin and at most one membership, the origin checks widened in one migration | Lane 2 | 5 | `6a`, `3C2` | P7 |
| `7b` | 7 | P | Release: spend and crew-visit thresholds as Site or portfolio settings, the Site's winning (OD-2, OD-12, OD-18); capital items wait for the executive (OD-17); the fit checked at each creation; changes counted since the last version | Lane 2 | 4 (new) | `7a` | P7 |
| `7c` | 7 | P | Proposal: the nearest set that fits budget, crew visits and dates, every exclusion with its reason | Lane 2 | 4 | `7b`, `6c` | P7 |
| `7d` | 7 | P | Spend steps on the item: planned spend, released spend, and incurred spend from linked expense records, counted once | Lane 1 | 2.5 (new) | `7a`, `3A4` | P7 |
| `7e` | 7 | CH5 | Act first: the Finding triage first, the version awaiting approval beside it; approve or send back with a trade-off | Lane 4 | 5 | `7b`, `7c` | P7 |
| `7f` | 7 | P | Switches beside the proposal (budget; the letter of intent), recomputed visibly | Lane 4 | 1.5 | `7e` | P7 |
| `7g` | 7 | CH5 | Portfolio cards read from their factors against target, with their evidence class | Lane 4 | 2.5 | `5c` | P7 |
| `7h` | 7 | P | Period close: the plan review, predicted against observed factors; unfinished items carried into the next draft (OD-10) | Lane 2 | 2.5 (new) | `7c`, `7d`, `5b` | P7 |
| `8a` | 8 | CH4 | Economic and causal verdicts beside the operational one | Lane 3 | 4 | `6e` | P8 |
| `8b` | 8 | CH4 | Field evidence admitted with its label; the option's cost replaces 0 | Lane 3 | 2 | `8a` | P8 |
| `8c` | 8 | CH4 | Three verdicts on What changed, with Actions' owners and the plan review | Lane 4 | 2.5 | `8b`, `7h` | P8 |
| `9a` | 9 | B3 | Rights rows from contract documents, AI-assisted, a person approving each row; contract-document emulator | Lane 1 | 4 | `3A3`, `6a` | P9 |
| `9b` | 9 | B3 | Supplier-claim case and its states | Lane 1 | 3 | `9a` | P9 |
| `9c` | 9 | CH3 | Remedy paths inside decisions, with notice deadlines | Lane 1 | 3.5 | `9b`, `6c` | P9 |
| `9d` | 9 | B1 | Cold-room records and observers on emulated data; cold verification | Lane 2 | 6.5 | `3A3`, `3B6`, `8a` | P9 |
| `9e` | 9 | B1 | EV depot records and observers on emulated data; EV verification | Lane 2 | 7.5 | `9d` | P9 |
| `WK` | W | tooling | Prepare the clean day-14 walkthrough database at main | Lane 4 | 1 | none | DAY13 |
| **All** | | | | | **166.5** | | |
<!--/table-->

**Lanes.** Four build lanes split by area, as W4 is amended for this build (owner, sitting 1, item 7: four lanes, the heavy-tool slot pool `T1` merged and enforced first):
- **Lane 1, sources and money:** 3A, the join, targets, the Mto decisions, the spend steps and rights.
- **Lane 2, structure and the plan's records:** the registry, the structure read and observer, attribution, and the plan's records, release and proposal.
- **Lane 3, the person, decisions and proof:** 3C, the decision records, the evaluator, the carrier and the verdicts.
- **Lane 4, screens and tooling:** the slot pool, step 1, and every screen slice.

Only lane 2 edits the structure registry. Other lanes request rows on their unit card. Migrations are named in specs and numbered at merge preparation, in merge order.

## 3. Gates: what each step must answer before the next builds on it
<!--derives: §2.1; §2.2; §2.4; §2.5; §2.6; §2.7; §2.8; §2.9; Figure 5; Figure 10; OD-3; OD-6; OD-12; Rules; WP §1.1; WP §1.5-->

W1 states acceptance as questions the screens must answer. A step's gate is that every question has a computed answer equal to the independent model (§4). The figures are outputs of the demonstration world, never targets.

| Step | Gate questions |
|---|---|
| **1** | Can any figure on the Portfolio or the site board be read as a period total when it is one day's figure? (It must not.) Is every field the API computes and the screen hid now shown with its existing evidence wording? |
| **2** | Does every source type have a version 1 canonical format with its units and timezone? Does every leaf of the mini-grid structure have a shared factor ID that both the store and the registry use? |
| **3A** | Does a duplicate upload add nothing? Does a late record revise a closed period and keep the earlier revision? Is another operator's row refused at intake? Does each emulator's output pass the same contract test a real export must pass? Is every emulated figure labelled *Emulated*, never *Recorded*? |
| **3B** | Does every registry row carry one home category (OD-21)? Does every stored Finding mechanism resolve to the factor it observes, through one registry row? Does the structure reproduce today's outcome map before the literal is removed (the parity test)? Does Kobo read 330<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> L candidate and 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> L unexplained litres, from today's records? Is a deviation raised as a Finding only under the owner's rule and outside its tolerance (OD-3)? Does a captive EV depot show revenue as *not applicable*, never zero? |
| **3C** | Does each person sign in with an email-and-password account of their own operator, and is a command without a signed-in person refused (OD-13)? Are roles granted and removed only by the operator executive, in Organisation settings, each change on record (OD-14)? Is every command, from every role, recorded under the authenticated person, with no "SYSTEM demonstration" actor left on a new write? Does every Action carry its creator, owner and due date, and show overdue when late? |
| **4** | Do the money leaves appear from records: Kobo's 3,458.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.revenue--> billed, 3,180.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.collected--> collected and 278.00<!--fig:sites.lakeside-power/Kobo.actual.nodes.outstanding--> outstanding? Is each node built from mixed evidence given its weakest class, with every source named? |
| **5** | Is Lakeside's October contribution 1,443.00<!--fig:portfolio.lakeside-power.actual.sums.contribution--> against a target of 2,295.00<!--fig:portfolio.lakeside-power.plan.sums.contribution-->, to the cent? Does Kobo's gap of −562.00<!--figx:{sites.lakeside-power/Kobo.actual.nodes.contribution}-{sites.lakeside-power/Kobo.plan.nodes.contribution}--> split into candidate running −412.50<!--figx:-({sites.lakeside-power/Kobo.actual.nodes.candidate_l}-{sites.lakeside-power/Kobo.plan.nodes.candidate_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}-->, unexplained fuel −150.00<!--figx:-({sites.lakeside-power/Kobo.actual.nodes.unexplained_l}-{sites.lakeside-power/Kobo.plan.nodes.unexplained_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}-->, necessary running −37.50<!--figx:-({sites.lakeside-power/Kobo.actual.nodes.necessary_l}-{sites.lakeside-power/Kobo.plan.nodes.necessary_l})*{sites.lakeside-power/Kobo.actual.nodes.diesel_price}--> and kWh billed +38.00<!--figx:({sites.lakeside-power/Kobo.actual.nodes.billed_kwh}-{sites.lakeside-power/Kobo.plan.nodes.billed_kwh})*{sites.lakeside-power/Kobo.actual.nodes.tariff}-->? Is the declarer of each target recorded? Does the Assure line read "Actual against target" (OD-6)? |
| **6** | Does Kobo's Finding open a decision whose options include no action (design Figure 5)? Is the stop-threshold change worth +250.50<!--fig:options.KOB-STOPSOC.monthly_or_horizon_change--> a month against no action, and 2,916.00<!--fig:options.KOB-STOPSOC.value--> over twelve months net of its one-off, labelled a design value until replay K passes? Is the reserve change rejected by the dawn bound on 4<!--fig:options.KOB-RESERVE.protect.replayed_dawn_days_below_safeguard--> of 61 replayed days, before any recommendation? Is the choice recorded under the person who made it? Does the same evaluator pass a cold-room and an EV fixture with no vertical code? |
| **7** | Does Lakeside's proposal spend 3,750.00<!--fig:plans.lakeside-power.default.spend--> with 3 of 3 crew visits, modelled at +6,088.50<!--fig:plans.lakeside-power.default.value-->, with its downside of +2,548.50<!--fig:plans.lakeside-power.downside--> shown beside it? With a spend threshold of 250.00<!--rec:demo_workflow.tenants[lakeside-power].spend_threshold--> and a crew-visit threshold of 0 (WP §1.5), are exactly Kobo's two Actions released at creation, and do the rest wait for the executive? Does each item record who chose it as its owner (OD-16), and does the Mto huller connection wait as capital with no Action until approved (OD-17)? Is each item's state, Released for Kobo and Chosen for the rest on 6 Nov, derived rather than stored (design Figure 6c)? Does the Kisiwa generator service count its crew visit in December, not November? Is every item's spend counted once, as planned spend, then released spend, then incurred spend? Does each Action have one origin and at most one membership? Does a change above either threshold propose a new version? |
| **8** | Are the operational, economic and causal verdicts kept apart, with "not proven yet" a verdict rather than a pass? Does realised money come only from recorded records, with the option's cost subtracted, not 0? |
| **9** | Do three contract cases give three different recommended paths, with "Coverage is decided by the supplier or insurer." on every rights screen? Do the cold-room and EV verticals pass their gates on the same core, with no vertical code in it? Has every real adapter passed its source type's contract test before its emulator is retired? |

`plan-and-action-workflow.md` gives step 7's mechanics in full.

## 4. Checks first, and the release tests
<!--derives: §2.9; Rules; DA §6; WP §2; D14; D11-->

**Checks first (W2).** Each step's checker is written and reviewed before the code or figures it checks, and it shares no logic, list or expected figure with them. The pack already holds the core of it:
- `demo-site-scenario-manifest.yaml` holds the inputs only;
- `evaluate_structure.py` evaluates them into `derived-values.json`;
- `independent_model.py` recomputes them from `structure-specification.md`;
- `check_manifest.py` asserts every stated figure against that independent model.

The product's registry, structure read, evaluator and proposal must reproduce `derived-values.json` from the emulated records through the real intake path. A slice that changes a behaviour pins today's behaviour first, then changes the pin on purpose in the same unit.

**Release tests.** Each is a question every release must answer yes to, across all nine demonstration Sites:

| Test | Question |
|---|---|
| Identities | Does every Site and portfolio outcome equal its declared function of factors, for target and actual, and do the attributions plus any residual equal the deviation, to the cent? |
| Unknown is not zero | Is every missing leaf shown as "not available yet", with the record that would fill it and what it blocks, read from the value's `missing` field (never from a null alone), and is a zero shown only where its source is held? |
| Negative controls | Do the healthy controls show no Finding and no option beyond no action: Kisiwa's necessary running, Kobo's headroom with no customer, Mto's welder? |
| Bounds first | Is every option that breaks a hard bound rejected before any recommendation, with the bound named? |
| Isolation | Is another operator's row refused at intake, and does no read, cache or proposal cross operators? |
| Disorder | Do a duplicate, a late settlement, an out-of-order record and an unmapped meter each behave as the manifest states? |
| Valuation | Does every decision include no action, and is a modelled value never shown as realised, nor a gross value as net? |
| The plan | Is spend counted once on each item, released only within both thresholds or by an approved version, and does every left-out item carry its reason? |
| The person | Is every choice, approval, creation and completion recorded under a named person, and does the system never choose, approve or create an Action? |
| Labels | Does every figure say how it is known, does *Emulated* never read as *Recorded*, and does every figure resting on a replay that has not passed carry its design-value label? |
| Proof | Are the three verdicts separate, and is money credited only from an economic verdict on recorded records? |

**Where "Unknown is not zero" is built** (`rev 16.13`, `structure-specification.md` §3.1). `3B1` and `3B6` declare `filled_by` and `absent` on every registry leaf; `3B3` fills the `missing` field of each factor value; the daily snapshot's slice stores it on each node; the screens (`3B5`, `7g`, Scope & coverage) read it. No slice grows: each was already scoped to the rows, the read and the snapshot this field sits on. In the demonstration, `missing-records.json` holds the entries and `check_manifest.py` `empty_states()` checks that every leaf, stage, condition and missing record names its source and its slice.

**The illustration's documented limits** (DA §6) stay in force. The checker does not enforce the plan-facing value fields or some rendered copies, so a reviewer reads those.

## 5. The demonstration world: how it is built, and what it costs
<!--derives: WP §2; DA §6; D14; §2.3; Figure 4-->

**Built backwards from each executive choice** (WP §2). Three operators each have three Sites. Every Site carries one contrast and one negative control, and the rights contrast sits inside repair decisions. Ground truth lives only in the manifest's private oracle. Every product figure must be computed through the real intake and analysis path and compared against it.

**Three time scales keep it cheap** (WP §2):
1. **Monthly ledger history,** generated directly from coherent ledgers with no physics. The emulators of step 3A write it in each source's native file shape.
2. **Sparse operational context,** cached.
3. **Short high-fidelity evidence windows,** only where a claim needs them: five-minute dispatch and verification slots, chamber readings around an incident, event-level charging logs.

**What changes in the build for Layer 4.** The demonstration producer gains the emulators' output: billing, collections, fuel purchases and budget lines for step 3A, quotes for step 6, contract documents for step 9. Each passes its contract test, and each stays labelled *Emulated* (D14).

**What it costs today.** These figures are reported from the 13 Nov build and were not re-measured for this design (WP §2):
- about 2 hours for 49 built Site-days;
- about 62 s per built mini-grid Site-day for intake, assessment and matching;
- a fixed self-check of about 25 minutes.

Simulation is a small part of that cost. The product pipeline, idle stage start-ups and a matcher that re-reads a Site's whole history dominate it.

**Before any build budget is trusted,** one re-benchmark runs on a permitted scratch database, on a quiet machine. It measures each stage per Site and per day, and the change kinds: one option change, one late commercial record and one contract-term edit. Its results replace the targets.

**Targets** (not measurements): the whole three-operator world in under 45 minutes with one command, and a one-option change re-run in about 2 minutes.

**Who works on it.** The analyst maps sources and reviews contract rows (§2.6). The builders own the producer. The coordinator runs database jobs one at a time, only on `*_test` and `<prefix>_audit*` databases, and walkthroughs only on a clean, good database.

## 6. Owner checkpoints, and from pilot to SaaS
<!--derives: D1; D11; D15; D13; D14; OD-20; §2.3; §2.7; §2.9; DA §5; Introduction-->

**Structure approvals (W1).** Before each step is built, the owner approves its one-page structure and a figure in one sitting. Steps 1 and 3C are the exception: their structure is approved with the recreated pack (OD-20). The first fortnight's schedule batches the rest into sittings (`two-week-build-plan.md`).

**Walkthroughs of computed screens (W8):** one per phase, not per slice.

| After | The owner walks | It decides |
|---|---|---|
| Steps 1–4 | the site board with Findings on their factors, and the money leaves from emulated records | whether the structure reads the business correctly |
| Step 5 | Lakeside's contribution, target against actual, factor by factor | whether the bridge is the screen to open with |
| Step 6 | Kobo's decision view | whether the options and their reasons read plainly |
| Step 7 | Lakeside's proposal, its release and approval, at the 6 Nov state of WP §1.5 | whether approval fits how an executive works |
| Step 8 | the three verdicts on Kobo's change | whether proof reads as proof |
| Before step 9 | — | cold rooms or EV first; pilot consent, data protection and integration rights |

**From pilot to SaaS (D1).** The engagement path is an initial call, a deep-dive, an integration pack, a pilot, and then SaaS. W9 keeps the pilot calendar overlapping the build, so each step finishes before the stage that needs it:

| Stage | Needs built |
|---|---|
| Deep-dive on the operator's own exports | 3A's intake and contract test, through which the Analyst role onboards their exports; 3B; 4's money leaves and 5's bridge, which becomes the pilot's baseline once reconciled with their finance. Only with 3A, 4 and 5 live does the safeguard hold: their target against actual within weeks |
| The first change, agreed at the end of the deep-dive (D15, pending) | step 6, on a lever the evaluator already handles; step 8 merged before that change's after-window ends |
| Pilot | real adapters passing the contract test, replacing emulators source by source: step 9's onboarding at scale; the minimum asks per vertical (DA §5); one closed month reconciled before any money shows as *Recorded* |
| SaaS | a proven change: an economic verdict on the client's own Site (§2.7) |

## 7. Open questions, with defaults
<!--derives: Decisions; §2.9; OD-6; D15-->

| # | Question | Context and example | Default, applied until the owner answers |
|---|---|---|---|
| 1 | Where does the "Actual against target" relabel (OD-6) fall? | The design names the change (§2.8) but not its step. The word "target" first matters when targets are declared | In step 5, beside target declaration (slice `5d`). Architect's call |
| 2 | Where does the origin and membership migration fall? | §2.9 widens today's one-origin check with a plan-item arm. The arm needs plan items to exist | In step 7 (slice `7a`), not 3C. Step 3C records the person only. Architect's call |
| 3 | Is the order of steps 8 and 9 kept? | Figure 10 puts the three verdicts beside the plan, and rights after both | Kept, because D15's first change needs proof before rights |
| 4 | Where does the daily snapshot's slice (OD-23) fall, and how big is it? | It needs the structure read (`3B3`) and today's input-change log; its storage and incremental rebuild wait for the owner's strategy conversation on the database build | A slice in step 3B after `3B3`, cut after that conversation; then `plan_model.py` is re-run. Until then the fortnight's figures leave it out, so they are optimistic by its size. Architect's call |
| 5 | Is mini-grid usable capacity built in the fortnight? | The value chain's first stage. Its readings are held today; no slice computes it by time window, and it carries no money without a customer (N11) | No: deferred to queued slice `4c` (capacity by time window, about 2.5 units, lane 2, after `3B3` and `0M`), pulled when a lane is free after the must-keep set, at the latest when a pilot pins a real register profile. Until then the stage reads "Not available yet" with its readings named. Architect's call (`rev 16.13`) |

**Pushback, for the owner.** None on the order: Figure 10 holds against the slices. One caution. Steps 5 and 7 hold the most new money logic, so they get discovery reviews and should not be compressed to make a date.
