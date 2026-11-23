# Website content: what the site says now, what it says is coming, and the rules every line passes

**AssetEcon · go-to-market document for the owner and the site editor · AssetOps Architect (Claude) · 19 Nov 2026 · recreated from the design (rev 16.7), updated for rev 16.9 and the owner's commercial answers of 19 Nov (T2 and T13 now met); copy pass of 19 Nov against the current design revision (`.agent/owner-website-copy-pass-2026-11-19.md`)**

**Refresh of 20 Nov (owner: `owner/owner-website-refresh-2026-11-20.md`).** Adds Operations (design §2.10: failures, repeats and maintenance as cost, warranties and contracts as decisions; §2.2, §2.3, §3.10), the honesty line "not available yet", never zero, with totals that name the sites they cover (§2.2, §3.8), and the approved app structure: Decisions, Results, a home for the plan and the "Waiting for you" inbox (§2.3, §3.6). Recommendation only: another agent maintains the site.

**Status.** Recreated from scratch at the owner's order (`.agent/owner-recreate-document-packs-2026-11-19.md`; document #10 in `regeneration/F-pack-recreation-plan.md`). It replaces the copy deck of 18 Nov. The copy pass of 19 Nov rewrote §2 and §3 so each page opens on outcomes, put portfolio allocation and proof on Home, frame every page in the four outcome categories, and move the honesty detail into one badge and the evidence page. No rule in §4 or §5 and no lint pattern was weakened. The recommendation for the owner's site repository (#11) follows from this document, later and separately.

**How this deck is organised.**
- **Now** is the design's Part 1: today's product, as the code runs it. Its lines carry the Today tag.
- **Coming** is the design's Part 2, in the delivery order of design §2.9 and Figure 10. Its lines carry the Coming tag. A coming line moves to "now" only when its trigger in §4 is met.
- **Every illustration** carries a badge in one of two forms, Demo data or Demo data · Emulated, the second when a figure comes from the demonstration world's commercial records (§5 rule 1, WC6). What the badge means is said once, on the evidence page (§3.8). Tags and badges render as small corner tags, never as words in the sentence (§3, "How tags render").
- **Every line of copy** is a quoted block in §2 and §3. `render_website_content_html.py` lints each one, enforces the stage gates and proves the lint on planted violations (`website-copy-lint-fixtures.txt`) before it renders the page.
- **Commercial facts** (the path, the price policy, durations) come from `commercial-plan.md`, which derives them from the owner's decisions.

## On one page
<!--derives: Introduction; Part 1; Part 2; D1; D12-->

*Serves the objective:* the site must make an operator executive want an initial call, because it shows, on one demo portfolio, the economic judgement their own tools do not give, and because every claim on it is one we can show.

| Question | Answer |
|---|---|
| Who it is for | CEOs, CFOs and COOs of mini-grid, cold-room and captive-EV operators in Africa; second, their heads of operations and finance |
| The one call to action | Book a conversation: the initial call of the engagement path (D1). The deep-dive page words it "Talk to us about a deep-dive" (T2, met) |
| The hero | Which sites earn, which leak, where this month's budget and crews go, and whether the money followed: shown on one demo portfolio, Lakeside Power |
| The frame | The four outcome categories in plain words: Grow revenue, Optimize cost and efficiency, Protect asset and capital, Assure performance and returns. Assure is the proof behind the other three, never a fourth pot of money (design §2.0, OD-21) |
| What it says is running now | Known generator running and unexplained fuel, what an issue might be worth as a labelled range, what to look at first, and whether a change worked, with proof before credit (Part 1) |
| What it says is coming | Their money explained against target, choices valued against doing nothing net of their cost, the Sites' changes in one plan approved by the executive, proof that the money followed, and who decided on record (Part 2, in delivery order) |
| What it never says | Savings, customer claims, competitor names, a comparison with any tool, a price, a duration not on the approved list, or a coming construct as available (§5) |
| What changes it | A trigger in §4, met and checked: a delivery step merged and live in the demo, a real file passing the contract test, or the owner's answer |

## 1. Audience and goal
<!--derives: §2.0; §2.6; D1; D12; WP §1.0-->

*Serves the objective:* an executive books a call only if the site speaks to their money question and earns their trust in the first minute.

| Visitor | Their question (the brief's four executive questions, and the cold-room one) | What they must come to believe | Where they meet it |
|---|---|---|---|
| CEO or MD | Which sites and investments earn the best return on the capital already in the ground? | "This shows which of my sites earn and which leak, and where the next budget goes" | Home, Mini-grids |
| COO | Where should limited crews work, and which changes can actually be done? | "This puts my crews where they protect the most service and money, within the visits I have" | Home, EV depots |
| CFO | Why is the month off target, which amounts are recorded and which estimated, and what can be recovered? | "Every figure shows how it is known, and the gap is split cause by cause" | Mini-grids, How we handle evidence |
| Commercial lead | Which demand can be sold profitably, and what limits it? | "Capacity is not called demand until a customer stands behind it" | Mini-grids, EV depots |
| Cold-room CEO | Is this room losing money because it is empty or because it is inefficient? | "This tells an empty room from an inefficient one before I spend on either" | Cold rooms |
| A financier or board member | Who decided, who approved and what followed? | "It is on record, and nothing is claimed before it is proven" (coming) | How it works |

**The goal of every page** is one action: book a conversation. The second-best action is to send the export checklist to the person who holds the data.

**How the pages are written.** Each page opens with the executive's question or the result they want, then shows one demo result that a reader would not have guessed, then the how. The site never names or argues against another tool: the unexpected result makes the point. Reassurance (people decide, no command to equipment) comes after the value, never as the opening tone.

## 2. Messages: now and coming
<!--derives: Part 1; §1.1; §1.2; §1.4; §1.5; Part 2; §2.9; Figure 10; Rules-->

*Serves the objective:* the message opens with the executive's money question and is honest about what runs now and what is coming.

### 2.1 The core message

> <!--tag:coming--> Know which sites earn, which leak, and where this month's budget and crews should go. Then know whether the money followed.

> Every figure shows how it's known.

### 2.2 Now: what the product does today

These lines come from design §1.1, §1.2 and §1.4. Each is something the product does on Site evidence as the code runs it, stated as what the executive gets.

> <!--tag:today--> **Every reading, trusted** · Each one keeps where it came from, its unit, its quality and whether it was live or simulated.

> <!--tag:today--> **Mini-grid generator running** · Know, interval by interval, which generator running was needed, which your solar and battery could have carried, and which cannot be judged yet.

> <!--tag:today--> **Mini-grid fuel** · Know, night by night, how much fuel your generators cannot explain.

> <!--tag:today--> **What it might be worth** · See what each issue could be worth, as a range labelled as modelled. Ranges of different kinds are never added up.

> <!--tag:today--> **What to do first** · Know what to look at first, the next step, and, where the rule allows, the setting to change.

> <!--tag:today--> **Whether it worked** · On mini-grids, follow each setting change from accepted to applied, then see whether it worked. Nothing counts as a result until that judgement is made.

> <!--tag:today--> **Cold rooms** · Know when each room left its temperature limit and whether its backup started.

> <!--tag:today--> **EV depots** · Know every charging session, the energy it took and which chargers were available.

> <!--tag:today--> **Four headings** · Every site and your portfolio, under four headings: Grow revenue, Optimize cost and efficiency, Protect asset and capital, Assure performance and returns. Each heading names the records it still lacks.

> <!--tag:coming--> **Headings from figures** · Each heading built from the figures that make it up, each figure saying how it is known.

> <!--tag:today--> **Failures and upkeep** · Every incident and maintenance request kept as one case from raised to closed, with the asset it concerns, and each asset's maintenance schedule showing what is due or overdue.

> <!--tag:not-connected--> **Commercial records** · Billing, payments, budgets and contracts. A missing record is named on screen, never shown as zero.

> <!--tag:today--> **Not available yet** · Where a record has no source, the screen says "not available yet", never zero. A total names the sites it covers.

### 2.3 Coming: in delivery order

These lines follow the delivery order of design §2.9 and Figure 10. None carries a figure. Each says "coming" until its trigger in §4 is met.

> <!--tag:coming--> **First: your files** · Your billing, collections, fuel purchases and budget, read from the files you already export, each checked before it is used.

> <!--tag:coming--> **Outcomes from drivers** · Every outcome built from what drives it, from the litre and the kWh up.

> <!--tag:coming--> **Who did what** · Who raised each action, who owns it, when it is due and who approved the spend, on record.

> <!--tag:coming--> **Site economics** · Contribution, cost to serve and collections for every site, from your own records, against your targets.

> <!--tag:coming--> **The gap, explained** · The month's gap to target, split cause by cause, so you know how much each cause took.

> <!--tag:coming--> **Choices, valued** · For each issue, options valued against doing nothing, net of their cost, within your service rules. One is recommended, and every option ruled out says why. The person accountable for the issue chooses.

> <!--tag:coming--> **Changes in one place** · The changes across your sites combined in one plan within your budget and crews, for your executive to approve or send back.

> <!--tag:coming--> **Proof** · After a change, three answers kept apart: did it happen, did the money follow in your records, and did the change cause it.

> <!--tag:coming--> **Failures as cost** · Each incident with how long the asset was out of service and what it cost, counted once. The same failure on the same asset, again, is flagged as a repeat.

> <!--tag:coming--> **Maintenance, weighed** · Scheduled visits and responsive repairs side by side, each with who pays: the fee, an invoice, or cover.

> <!--tag:coming--> **Warranties and contracts, decided** · Each asset's warranty, insurance and service contract beside it, with the notice deadline, so a repair decision starts from who pays.

> <!--tag:coming--> **One loop, three places** · Choose in Decisions. Your executive approves the plan. See in Results whether the money followed. A "Waiting for you" inbox holds what needs you.

> <!--tag:coming--> **After that** · Contract rights inside repair decisions, then cold rooms and EV depots on the same core.

### 2.4 Confident, and still a hypothesis

> We believe the value is in joining your operational, commercial and contract records into one economic judgement. A pilot on your own sites is how we both find out.

> <!--tag:coming--> Some sites may have nothing to save. The comparison against doing nothing says so, before anyone calls it a saving.

## 3. Copy deck by page
<!--derives: Part 1; §2.0; §2.1; §2.2; §2.4; §2.5; §2.6; §2.7; Figure 3; Figure 5; WP §1.1; WP §1.2; WP §1.3; D1; D14-->

*Serves the objective:* each page carries one vertical's money question to the same call to action, with claims a demo can back.

**How tags render** (owner, 19 Nov: "tighten the hero and badges").
*In the deck,* a tag is a marker at the start of a copy block, never a word in the sentence. There are five:

| Marker | Tag shown | Used on |
|---|---|---|
| `<!--tag:today-->` | Today | a line about what runs now (design Part 1) |
| `<!--tag:coming-->` | Coming | a line about a coming construct (design Part 2) |
| `<!--tag:not-connected-->` | Not yet connected | the line naming records not yet connected |
| `<!--tag:demo-->` | Demo data | an illustration on demonstration telemetry or replays |
| `<!--tag:demo-emulated-->` | Demo data · Emulated | an illustration with a figure from emulated billing, budget or contract records (D14) |

- *On the page.* Each copy block is a card. Its tags sit together in the card's top-right corner as small pills: Today green, Coming and Not yet connected amber, the demo badges grey. A block that opens `**Heading** · ` shows that heading as the card's title. On Home, `<!--fold-->` marks the end of the first fold.
- *What the lint checks* (§5). It reads each tag as words in front of its block, so every earlier rule reads what it read when the labels were typed. It also fails a block on any of these: an unknown tag; more than one of Today, Coming and Not yet connected; a coming construct anywhere in a Today block; a coming construct stated in a block with no state tag; a figure without a demo badge; or a tag typed as a prefix in the sentence. On Home it fails unless the first fold holds just the question, the promise and one badged example, and unless every block below the fold has a two-to-four-word heading, with the reassurance just before the call to action.

### 3.1 Sitemap

| Page | Its job |
|---|---|
| Home | the allocation question, one demo portfolio: its gap, the changes its executive approves, and the proof, the four headings, the call to action |
| Mini-grids · Cold rooms · EV depots | the vertical's question in its own words, one unexpected demo result, today's value, what is coming |
| How it works | the loop: see, decide, act, track, prove; where each step lives in the product (Decisions, Results, a home for the plan, "Waiting for you"); who decides at each step |
| Operations | incidents and repeats as visible cost, maintenance, and assets with their warranties and contracts, as decisions |
| The deep-dive and the pilot | the engagement path and what the operator gives and gets |
| Now and coming | the two lists of §2.2 and §2.3, kept in step with §4 |
| How we handle evidence | what the badge means and the figure rules, in plain words |
| Book a conversation | the form and what happens next |

The Now and coming page carries the lines of §2.2 and §2.3 unchanged, introduced by:

> The Today tag marks what the product does on site evidence now.

> The Coming tag marks what comes next, in the order shown. A line moves up only once it runs in our demonstration and has been checked.

### 3.2 Home

*Order:* above the fold, only the question, the one-line promise and one example (Lakeside's diesel contrast). Below the fold, short headed blocks: where the money goes, who decides, the proof, today's value, the four questions; then the reassurance, just before the call to action. The renderer checks this order (§5).

> Which of your sites earn, which leak, and where should this month's budget and crews go?

> <!--tag:coming--> See where the money went, choose where it goes next, and know whether it followed. Every figure shows how it's known.

> <!--tag:today--><!--tag:demo--> Lakeside Power, October. Kisiwa burned the most diesel, 904<!--fig:sites.lakeside-power/Kisiwa.actual.nodes.diesel_l--> litres, and has nothing to fix on fuel: all of its generator running was needed. Kobo burned half that, and 25<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> litres, as October's records classify them, went on running the generator while its solar and battery could have carried the load.

<!--fold-->

> <!--tag:coming--><!--tag:demo-emulated--> **Where the money goes** · A budget of 5,000<!--rec:tenants[lakeside-power].portfolio_constraints.budget_usd_nov_dec--> for November and December; 3<!--fig:plans.lakeside-power.default.crew_visits_limit--> crew visits in November. Kisiwa's failed backup generator is repaired: evening hours without backup fall from 125<!--fig:options.KIS-NOACT.protect.obligation_hours_without_backup--> to 15<!--fig:options.KIS-REPAIR.protect.obligation_hours_without_backup-->. Kobo's two generator settings pass the operating checks in a replay, but their effect on fuel and money is not available yet: that needs a replay of Kobo's own October. Mto claims its inverter under warranty and connects a new business customer. Spend: 3,660<!--fig:plans.lakeside-power.default.spend--> of 5,000<!--rec:tenants[lakeside-power].portfolio_constraints.budget_usd_nov_dec-->.

> <!--tag:coming--> **Your people decide** · The person accountable chooses: a site manager, your finance lead, or your executive for capital. Your executive approves the plan, or sends it back.

> <!--tag:coming--> **Proof, site by site** · Did the change happen? Did the money follow in your records? Did the change cause it? Three answers, kept apart.

> <!--tag:today--> **Every litre accounted** · Know which generator running your solar and battery could have carried, and how much fuel your generators cannot explain. Then see whether your change worked.

> **Four questions, one view** · Grow revenue: are you selling all your assets can deliver? Optimize cost and efficiency: what does each litre, kWh and crew visit cost, and is what you billed collected? Protect asset and capital: are service promises, equipment and warranty rights kept? Assure performance and returns: is every figure, choice and result proven?

> **You stay in control** · The product proposes. Your people decide and act. It sends no command to your equipment.

> Book a conversation. In an hour, see what the product does today on a demo operator in your sector, then talk through what a deep-dive on your sites would need.

### 3.3 Mini-grids

> Which sites lost money last month, and why: fuel, billing, collections or losses?

> <!--tag:coming--><!--tag:demo-emulated--> Kobo sold more power than its target in October and still came in −120.50<!--figx:{sites.lakeside-power/Kobo.plan.nodes.contribution}-{sites.lakeside-power/Kobo.actual.nodes.contribution}--> below its contribution target. Fuel took it all: 25<!--fig:sites.lakeside-power/Kobo.actual.nodes.candidate_l--> litres of generator running the solar and battery could have carried, as October's records classify it, and 120<!--fig:sites.lakeside-power/Kobo.actual.nodes.unexplained_l--> litres no generator explains.

> <!--tag:coming--><!--tag:demo--> A setting is judged by the checks the site lives by, and the rest is shown beside it. A lower battery reserve at Kobo passes the operating checks in a replay: energy served, reserve kept, starts within the maker's limit, a regular full charge. Its dawn battery charge falls below the site's margin on 11<!--fig:options.KOB-RESERVE.information.dawn_days_below--> of 61<!--rec:replay_studies.K8.days--> replayed days, and that is stated beside it, never hidden.

> <!--tag:today--> Know, interval by interval, which generator running was needed and which your solar and battery could have carried, and night by night, how much fuel your generators cannot explain.

> <!--tag:coming--> Every site's gap to target, split cause by cause. Then options for each issue, valued against doing nothing, net of their cost.

> <!--tag:coming--> Demand counted as demand only when a customer stands behind it. Spare capacity is shown as capacity.

### 3.4 Cold rooms

> Is this room losing money because it is empty, or because it is inefficient?

> <!--tag:coming--><!--tag:demo-emulated--> The room with the highest energy cost per crate-day has nothing wrong with its equipment: only 4,340<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.occupied_total_crate_days--> of its 12,400<!--fig:sites.harvest-cold/Room A · Mwea.actual.nodes.capacity_crate_days--> crate-days were filled. The room that looks efficient draws 970<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.excess_kwh--> kWh a month more than its occupancy explains, and repairing it is the recommended option.

> <!--tag:today--> Know, room by room, when temperature left its limit and whether the backup started.

> <!--tag:coming--> Return per room, with occupancy kept apart from efficiency, and repair or replace valued against doing nothing.

> <!--tag:coming--> Stock at risk shown in batches and minutes above the limit. Coverage is decided by the supplier or insurer.

### 3.5 EV depots

> Can you meet every departure for less, with the chargers you already have?

> <!--tag:coming--><!--tag:demo--> The cheapest charging schedule would miss 93<!--fig:options.EMB-CHEAPEST.protect.departures_missed--> departures in the month. It is cheaper only because it buys less energy, so it is ruled out. The schedule recommended instead supplies the 2,800<!--fig:options.EMB-DEADLINE.bound.supplied_kwh_night--> kWh a night the buses need, so no bus is short of charge. The timing of each bus's departure is not available yet: it needs a replay of the charging schedule.

> <!--tag:coming--><!--tag:demo--> Another depot can take 6<!--fig:options.RUI-ABSORB6.params.added_buses--> more buses on the chargers it already has, with no departure missed.

> <!--tag:today--> Know, depot by depot, every charging session, the energy it took and which chargers were out of service.

> <!--tag:coming--> Cost per departure met, the schedule that meets every departure for the least cost, and how many more buses your chargers can carry.

### 3.6 How it works

> Five steps, one loop, from the reading to the proof.

> <!--tag:coming--> **See** · Every figure labelled with how it is known: recorded, emulated, measured, calculated, estimated, quoted or modelled.

> <!--tag:coming--> **Decide** · Decisions is where the options wait: options prepared for every issue, one recommended, each beside doing nothing. The person accountable chooses, or chooses nothing: your site and operations managers, your finance lead for billing and claims, your executive for capital.

> <!--tag:coming--> **Act** · The plan holds the approved set of changes. Your team creates the actions, each with an owner and a due date. Spend above the limit your executive sets waits for their approval.

> <!--tag:coming--> **Track** · Every action followed to done, and anything overdue flagged.

> <!--tag:today--> **Proof on mini-grids** · A setting change is already judged against a frozen baseline, and nothing counts as a result before that judgement.

> <!--tag:coming--> **Prove** · Results is where it shows. After every change, three answers: did it happen, did the money follow in your records, and did the change cause it. A result is claimed only after all three.

> <!--tag:coming--> **Waiting for you** · One inbox at the top of every page holds what needs you: a decision to make, an action due, the approval of the plan.

> The product proposes; your people decide and act. It sends no command to your equipment.

### 3.7 The deep-dive and the pilot

The five stages, named as in `commercial-plan.md` (D1): **Initial call → Deep-dive with process owners → Integration pack and pilot timeline → Pilot and monitoring → SaaS**. One line of copy per stage.

> An initial call: we show you what the product does today on a demo operator in your sector, then check four things together: data privacy, your processes, the exports you hold, and who signs.

> A deep-dive with your process owners: your finance, operations and data people map the files you already export, one to four months of records, so your own figures can be read.

> An integration pack and pilot timeline: which sources come first, the pilot's sites, dates and success criteria, and who in your team holds each role.

> Pilot and monitoring: a pilot of about three months on your own sites, with a monthly review and the first change judged on your records.

> SaaS: a subscription, once the pilot has shown you what it is worth.

> The deep-dive and the integration pack take about three to ten weeks from the deep-dive's start to the pilot, depending on how complete your records are.

> The pilot has a fee, agreed after we have talked. We do not publish prices.

> Talk to us about a deep-dive.

### 3.8 How we handle evidence

> Every figure shows how it's known.

> The Demo data tag marks an illustration on a demonstration operator, never a customer result. Emulated means the figure comes from stand-in billing, budget or contract records, used until your own files replace them.

> Figures of different kinds are never added together. A total is never stronger than its weakest part.

> Unknown is never shown as zero. Where a record has no source, the screen says "not available yet" and names it.

> A total says which sites it covers, and a site with a missing record is named, not left out quietly.

> The same litre never carries money twice.

> We do not promise savings; we show how they would be proven.

> <!--tag:coming--> Every option shown beside doing nothing, so no change is called a gain until it beats doing nothing.

> Coverage is decided by the supplier or insurer.

### 3.9 Book a conversation

> Tell us your sector, how many sites you run, and the money question you most want answered.

> We reply to agree a time. The call is an hour: what the product does today on a demo operator in your sector, then your questions.

### 3.10 Operations

> What did your failures cost, which ones keep coming back, and who pays for the repair?

> <!--tag:today--> Know every incident and maintenance request, from raised to closed, with its asset, and which scheduled maintenance is due or overdue.

> <!--tag:coming--> Each incident with the time the asset was out of service and what it cost, counted once. The same failure on the same asset, again, is marked as a repeat and opens a decision.

> <!--tag:coming--> Maintenance weighed as a choice: scheduled visits against breakdowns, each with who pays, the fee, an invoice or cover.

> <!--tag:coming--> Warranties, insurance and service contracts shown beside each asset, with the notice deadline, so a repair decision starts from who pays. Coverage is decided by the supplier or insurer.

> Where a site has no incident or maintenance record, the page says "not available yet" for that site, and a total names the sites it covers.

## 4. Stage gates tied to the delivery steps
<!--derives: §2.9; Figure 10; D1; D14; D12-->

*Serves the objective:* the site grows exactly as the product does, so an executive never meets a claim the demo cannot back.

### 4.1 The stages a claim moves through

**Coming** → **available to see in a walkthrough, on a demonstration operator** (its delivery step merged after a fresh review and live in the refreshed demo) → **available in the deep-dive** (a real file of that record type passes the contract test under a signed data agreement, D14) → **shown as a result** (a money verdict on field records, with the operator's written consent). Stage words only, no dates. Money stays out of trigger copy, because on the demonstration world it is read from emulated records.

### 4.2 The triggers

The renderer reads this table. While a row says "not met", its gated phrase may not appear in §2–§3. "Available to see in a walkthrough" may not appear until one of T4–T11 is met. Each row's prepared copy must carry its gated phrase, pass the lint and hold no figure. To record a trigger, change "not met" to "met: " with the evidence, then move the prepared copy into §2.2 and the pages. T13 and T14 are computed from `commercial-plan.md` §5.2 and are never recorded by hand.

| # | Trigger (design step) | State | Gated phrase | Copy the site may then use | Checked by |
|---|---|---|---|---|---|
| T1 | The owner approves the mock-up for client use | not met | "the full loop on a demo operator" | "We will show you the full loop on a demo operator in your sector, then what runs today." | coordinator |
| T2 | The offer is ready to send: C2, C12 and C13 answered | met: the owner answered C2, C12 and C13 on 19 Nov (`.agent/owner-pack-questions-defaults-2026-11-19.md`); the call to action is in §3.7 | – | the deep-dive page's call to action becomes "Talk to us about a deep-dive" | coordinator |
| T3 | Step 1: the period's cost figure corrected (CH5) | not met | – | none: a correction, not a claim | Architect |
| T4 | Step 3B: outcomes built from their factors, on today's operational records (B1, CH1) | not met | "outcomes broken into what drives them" | "Available to see in a walkthrough, on a demonstration operator: each site's outcomes broken into what drives them, with what is recorded, what is emulated and what is missing." | Architect |
| T5 | Step 3C: the recorded person (CH2) | not met | "who decided and who approved, on record" | "Available to see in a walkthrough, on a demonstration operator: each action with who decided and who approved, on record, with its owner and due date." | Architect |
| T6 | Steps 4 and 5: money leaves joined, targets and the bridge (B2, B3) | not met | "result against target, built up cause by cause, on a demonstration operator" | "Available to see in a walkthrough: each site's result against target, built up cause by cause, on a demonstration operator, from emulated billing and budget records." | Architect |
| T7 | Step 6: decisions and options (CH3) | not met | "decisions valued against doing nothing, on a demonstration operator" | "Available to see in a walkthrough: decisions valued against doing nothing, on a demonstration operator, with the options ruled out and why." | Architect |
| T8 | Step 7: the plan and the Portfolio (P, CH5) | not met | "changes across your sites in one plan, approved by your executive, on a demonstration operator" | "Available to see in a walkthrough: the changes across your sites in one plan, approved by your executive, on a demonstration operator, within budget and crews." | Architect |
| T9 | Step 8: the three verdicts (CH4) | not met | "proof after a change, on a demonstration operator" | "Available to see in a walkthrough: proof after a change, on a demonstration operator, with did it happen, did the money follow and was it the cause answered separately." | Architect |
| T10 | Step 9: contract rights | not met | "contract rights inside the repair decision, on a demonstration operator" | "Available to see in a walkthrough: contract rights inside the repair decision, on a demonstration operator, with the deadline." | Architect |
| T11 | Step 9: the second vertical, cold first | not met | "cold rooms read through what drives them, on a demonstration operator" | "Available to see in a walkthrough: cold rooms read through what drives them, on a demonstration operator, occupancy kept apart from efficiency." | Architect |
| T12 | A real file of a record type passes the contract test in a deep-dive (D14) | not met | "available in the deep-dive" | "Available in the deep-dive: your billing and budget read from your files." (name only the record types that passed) | Architect |
| T13 | The deep-dive and pack fit three to ten weeks in every owner-time case within the owner's decisions (computed) | met: computed from `commercial-plan.md` §5.2 over the two cases within C14 and C15 (3.1 to 9.9 weeks); the copy is in §3.7 | "about three to ten weeks from the deep-dive's start to the pilot" | "The deep-dive and the integration pack take about three to ten weeks from the deep-dive's start to the pilot, depending on how complete your records are." | renderer |
| T14 | The first view comes at most six weeks into the deep-dive in every case within the owner's decisions, and T6 is met (computed) | not met | "within a few weeks of receiving your files" | "Your target against actual, in the product, within a few weeks of receiving your files." | renderer |
| T15 | A first change proved in money on field records, with the operator's written consent | not met | – | a case story, only in the operator's words | owner |

### 4.3 Why T13 is met and T14 is not, yet

The owner decided C14 (up to eight peak days a month) and C15 (two owner-days a month kept for the product) on 19 Nov. In `commercial-plan.md` §5.2 the two cases within those decisions give a deep-dive and pack of 3.1 to 9.9 weeks, so T13 holds and its copy is in §3.7. The four-day reserve rows are a sensitivity the owner did not choose, and the renderer leaves them out. The first view comes at most 4.3 weeks into the deep-dive in both cases, but T14 also needs the money leaves, targets and the bridge live in the demo (T6), so it is not met yet.

## 5. Honesty rules for copy, and what the lint enforces
<!--derives: Rules; Words; D6; D14; Decisions-->

*Serves the objective:* credibility is the differentiator (design Introduction); one overclaim on the site costs the trust every money figure needs.

**The rules** (the design's figure rules, in public form):
1. Every figure says how it is known. Every demo illustration carries a badge tag: "Demo data", or "Demo data · Emulated" when a figure comes from the demonstration world's commercial records (D14; WC6). What the badge means, a demonstration operator and never a customer result, is said once, on the evidence page (§3.8), not repeated in each line. A line that shows a coming construct also carries the Coming tag. Tags are markers that render as corner tags (§3, "How tags render").
2. No savings, in any phrasing; no proof or customer claims; no competitor or product names; no superlatives; and no line that names or argues against monitoring tools or competitors (WC7). The unexpected demo result makes the point.
3. A replay-based value is modelled on simulated data, with its source, or reads "not available yet" where the replay has not run (D6; 0K4m, 22 Nov: one figure per quantity). It never appears on the site.
4. No price, and only the approved durations, each gated where §4 says.
5. People decide. The site never claims that the product makes the operator's choices or approvals, or acts on its own.
6. "Plan" means only the executive-approved set of changes (OD-6). Performance is against a target.
7. A coming construct is never called available now.
8. No legal or insurance conclusion: "Coverage is decided by the supplier or insurer."
9. No internal words: no Finding, leaf, registry, lane, slice, evaluator or mock-up.

**What the lint enforces.** `render_website_content_html.py` checks every quoted block in §2 and §3 against rules 1–9, the stage gates of §4.2 and the walkthrough wording before T1. It imports the design's retired terms and the naming lint from `check_alignment.py`, so the site and the design pack can never drift apart. It refuses to render if any of the planted violations in `website-copy-lint-fixtures.txt` passes; the 19 Nov additions plant `AssetEcon decides for you`, `See actual against plan`, a coming construct called `Running today`, a legal conclusion and each gated phrase. The copy pass of 19 Nov adds two planted sets, each of which must fail for its own rule, not by accident: `[WC7]` lines that argue against monitoring tools or competitors (the stage name "Pilot and monitoring" must still pass), `[TAG]` lines that break the tag rules, and `[M8]` lines that state a coming construct in a block with no Coming tag (whole-pack review H, M8: untagged blocks are now checked too; a question may name a coming construct). The M8 sweep of 19 Nov found 9 untagged blocks stating coming constructs and 1 Today line not limited to mini-grids; all 10 are fixed. The renderer also breaks the Home first fold five ways and must refuse each one.

**What still needs a reader.** Tone; whether a line overstates by implication; whether a line argues against another tool by implication, beyond what the WC7 patterns catch; and whether each "Today" line still matches design Part 1 after a release.

## 6. Decisions for the owner
<!--derives: D1; D2; D6; D12; D14; owner: .agent/owner-pack-questions-defaults-2026-11-19.md-->

*Serves the objective:* these settle what the site may say and when it may say more.

| # | Decision | Context and example | Default |
|---|---|---|---|
| **WC1** | Publish the "Coming" list now, or only "Running today" | A visitor sees "Coming: options valued against doing nothing" before the demo can show it | Publish it, labelled "Coming", in delivery order, with no figure and no date |
| **WC2** | One demo illustration per vertical page | The Kobo figures are Emulated and the reserve figure rests on a replay | Keep them, each with the badge of §5 rule 1; the Kobo stop-threshold value and every other replay-based money value stay off the site (rule 3). The replay counts "4 of 61 replayed days" and "31 of 31 replayed nights" stay, each with the Demo data badge (owner, 19 Nov: "defaults for the three"). The 19 Nov copy pass adds a second, unexpected result where the demo has one (EV: buses absorbed on existing chargers), and shows Kobo's litres, not their money, because one money split sits within the lint's design-value tolerance. 22 Nov (0K4m, D-0K4.33, D-0K4.36, D-0K4.38): the reserve change is admitted on the replay, so its dawn count reads as information beside it, not as a reason it is ruled out; Embakasi's "31 of 31 replayed nights" goes for the structure's energy check, per-bus timing Not available yet (the Embakasi schedule replay, not run); Kobo's 330 L reads as the simulated world records it (dispatch-3.2; dispatch-3.3 re-classifies it in 0K4f) |
| **WC3** | The deep-dive page before T2 | Settled: T2 is met, because the owner answered C2, C12 and C13 on 19 Nov | The deep-dive page now ends "Talk to us about a deep-dive"; every other page keeps "Book a conversation" |
| **WC5** | Does the site state the decided terms: no fee for the deep-dive (C12), or the pilot fee's credit (C2)? | The terms are decided, but D2 discloses price terms after the client conversation, and C12 offers the deep-dive only after the alignment checks pass | No. The site says the pilot has a fee agreed after we have talked; the terms are given in the conversation. The lint keeps refusing "free deep-dive" and "credited" |
| **WC6** | The badge: one form, or two | The owner asked for one short badge on every illustration. D14 requires a figure from emulated commercial records to say Emulated, and rule 7 requires a coming construct to be marked | Two forms of one badge: "Demo data" on operational figures, "Demo data · Emulated" on figures from emulated billing, budget or contract records, each beside the Coming tag where the line shows a coming construct. **Accepted by the owner, 19 Nov** ("defaults for the three"); rendered as corner tags (§3) |
| **WC7** | Should the lint refuse copy that argues against another tool? | The 18 Nov core message named monitoring as the foil. The owner's copy-pass terms keep the lint unchanged, so a reader checks it today (§5) | Yes. **Accepted by the owner, 19 Nov** ("defaults for the three") and now in the lint (`ARGUE` in the renderer), with its own `[WC7]` planted lines, each proved to fail for this rule. The stage name "Pilot and monitoring" is proved to pass |
| **WC4** | Who records a trigger as met | A merged step is not yet live in the refreshed demo | The checker in §4.2 records it with the evidence; the owner sees each change before publication |

**Pushback, with reasons.** The 18 Nov deck gave dated "Coming" increments. I recommend stage words only: the delivery dates belong to `delivery-plan.md` and `two-week-build-plan.md`, which change at each sitting, and a public date that slips costs more trust than it earns.
