# Website content: what the site says now, what it says is coming, and the rules every line passes

**AssetEcon · go-to-market document for the owner and the site editor · AssetOps Architect (Claude) · 19 Nov 2026 · recreated from the design (rev 16.7)**

**Status.** Recreated from scratch at the owner's order (`.agent/owner-recreate-document-packs-2026-11-19.md`; document #10 in `regeneration/F-pack-recreation-plan.md`). It replaces the copy deck of 18 Nov. The recommendation for the owner's site repository (#11) follows from this document, later and separately.

**How it is built.**
- **Now** is the design's Part 1: today's product, as the code runs it.
- **Coming** is the design's Part 2, in the delivery order of design §2.9 and Figure 10. A coming line moves to "now" only when its trigger in §4 is met.
- **Every line of copy** is a quoted block in §2 and §3. `render_website_content_html.py` lints each one, enforces the stage gates and proves the lint on planted violations (`website-copy-lint-fixtures.txt`) before it renders the page.
- **Commercial facts** (the path, the price policy, durations) come from `commercial-plan.md`, which derives them from the owner's decisions.

## On one page
<!--derives: Introduction; Part 1; Part 2; D1; D12-->

*Serves the objective:* the site must make an operator executive want an initial call, because it promises economic judgement their monitoring tools do not give, and because every claim on it is one we can show.

| Question | Answer |
|---|---|
| Who it is for | CEOs, CFOs and COOs of mini-grid, cold-room and captive-EV operators in Africa; second, their heads of operations and finance |
| The one call to action | Book a conversation: the initial call of the engagement path (D1) |
| What it says is running now | Honest, bounded judgement on Site evidence: what happened and how sure we are, missing fuel, what it might be worth as a labelled range, what to look at first, and whether a change worked, with proof before credit (Part 1) |
| What it says is coming | Their money explained against target, choices valued against doing nothing net of their cost, the Sites' changes in one plan approved by the executive, proof that the money followed, and who decided on record (Part 2, in delivery order) |
| What it never says | Savings, customer claims, competitor names, a price, a duration not on the approved list, or a coming construct as available (§5) |
| What changes it | A trigger in §4, met and checked: a delivery step merged and live in the demo, a real file passing the contract test, or the owner's answer |

## 1. Audience and goal
<!--derives: §2.0; §2.6; D1; D12; WP §1.0-->

*Serves the objective:* an executive books a call only if the site speaks to their money question and earns their trust in the first minute.

| Visitor | What they must come to believe | Where they meet it |
|---|---|---|
| Mini-grid CEO or CFO | "This explains why a month came in below target, Site by Site, and what is worth doing about it within my budget and crews" | Home, Mini-grids |
| Cold-room CEO | "This tells an empty room from an inefficient one before I spend on either" | Cold rooms |
| EV fleet COO | "This meets every departure at the lowest energy cost my chargers allow" | EV depots |
| Head of operations or finance | "Every figure says how it is known, and nothing is claimed before it is proven" | How we handle evidence |
| A financier or board member | "Who decided, who approved and what followed is on record" (coming) | How it works |

**The goal of every page** is one action: book a conversation. The second-best action is to send the export checklist to the person who holds the data.

## 2. Messages: now and coming
<!--derives: Part 1; §1.1; §1.2; §1.4; §1.5; Part 2; §2.9; Figure 10; Rules-->

*Serves the objective:* the message opens with the executive's money question and is honest about what runs now and what is coming.

### 2.1 The core message

> Your monitoring shows what your assets did. AssetEcon is being built to show what that did to your money, what is worth doing about it, and whether it paid off.

> Every figure says how it is known. We do not promise savings; we show how they would be proven.

### 2.2 Now: what the product does today

These lines come from design §1.1, §1.2 and §1.4. Each is something the product does on Site evidence as the code runs it.

> Running today: every reading is kept with where it came from, its unit, its quality and whether it was live or simulated.

> Running today on mini-grids: generator running is classified interval by interval as necessary, as running the solar and battery could have carried, or as not yet determinable.

> Running today on mini-grids: fuel is balanced night by night against what the generator explains, so unexplained fuel is named.

> Running today: what an issue might be worth is shown as a range, labelled as modelled, and never added up across kinds.

> Running today: what to look at first and a next step, and where the rule allows, a recommended setting change.

> Running today: the response is tracked from accepted to applied, and a change is judged after it is made. Nothing counts as a result before that judgement.

> Running today on cold rooms: temperature excursions and backup starts. On EV depots: sessions, energy and charger availability.

> Every site and the portfolio are read in four categories: Grow, Optimize, Protect and Assure. Each names the records still missing.

> Not yet connected: billing, payments, budgets and contracts. Where a record is missing, the screen says so; it is never shown as zero.

### 2.3 Coming: in the order we are building it

These lines follow the delivery order of design §2.9 and Figure 10. None carries a figure. Each says "coming" until its trigger in §4 is met.

> Coming first: your billing, collections, fuel purchases and budget read from the files you already export, each checked before it is used.

> Coming: each outcome built from what drives it, from the litre and the kWh up, so every driver is a quantity, not a sentence.

> Coming: who raised each action, who owns it, when it is due, and who approved the spend, on record.

> Coming: contribution, cost to serve and collections for every site, from your own records, against your targets.

> Coming: the gap to target split cause by cause, so you can say how much of the month each cause took.

> Coming: for each issue, options valued against doing nothing, net of their cost, checked against your service rules, with one recommended and the reason any option is ruled out. Your site and operations managers choose.

> Coming: the changes across your sites combined in one plan within your budget and crews, proposed for your executive to approve or send back.

> Coming: after a change, three answers kept apart: did it happen, did the money follow in your records, and did the change cause it.

> Coming after that: contract rights inside repair decisions, then cold rooms and EV depots on the same core.

### 2.4 Confident, and still a hypothesis

> We believe the value is in joining your operational, commercial and contract records into one economic judgement. The pilot on your sites is how we both find out.

> Some sites may have nothing to save. The comparison against doing nothing says so, before anyone calls it a saving.

## 3. Copy deck by page
<!--derives: Part 1; §2.0; §2.1; §2.2; §2.4; §2.5; §2.6; §2.7; Figure 3; Figure 5; WP §1.1; WP §1.2; WP §1.3; D1; D14-->

*Serves the objective:* each page carries one vertical's money question to the same call to action, with claims a demo can back.

### 3.1 Sitemap

| Page | Its job |
|---|---|
| Home | the money question, today's honest base, what is coming, the call to action |
| Mini-grids · Cold rooms · EV depots | the vertical's question in its own words, with one demo illustration |
| How it works | the loop: see, decide, act, track, prove; who decides at each step |
| The deep-dive and the pilot | the engagement path and what the operator gives and gets |
| Now and coming | the two lists of §2.2 and §2.3, kept in step with §4 |
| How we handle evidence | the figure rules, in plain words |
| Book a conversation | the form and what happens next |

The Now and coming page carries the lines of §2.2 and §2.3 unchanged, introduced by:

> Now: the lines on this page marked "Running today" are what the product does on site evidence today.

> Coming: the lines marked "Coming" are in build, in the order shown. A line moves up only when it runs in our demonstration and has been checked.

### 3.2 Home

> Monitoring tells you what your assets did. We are building the tool that tells you what it did to your money.

> For mini-grid, cold-room and EV depot operators who need to know why a month came in below target, which lever moves it, and what it is worth.

> Today the product already gives honest judgement on your site evidence: what happened, how sure we are, and whether a change worked. Next, it puts your own money on the same footing.

> Book a conversation. We show you what the product does today on a demo operator in your sector, then talk through what a deep-dive on your sites would need.

### 3.3 Mini-grids

> Which sites lost contribution last month, and why: fuel, billing, collections or losses?

> Today: generator running classified as necessary, or as running the solar and battery could have carried, and fuel balanced night by night.

> Coming: your target against actual for each site, split cause by cause. For example, Kobo, October, a demonstration mini-grid: contribution 883<!--fig:sites.lakeside-power/Kobo.actual.nodes.contribution--> against a target of 1,445<!--fig:sites.lakeside-power/Kobo.plan.nodes.contribution-->, a gap built from four causes. Illustration on demo data, Emulated, with simulated telemetry; not a customer result.

> Coming: options for each issue valued against doing nothing. The obvious setting can be the wrong one: in the demonstration, a lower battery reserve is ruled out because it puts dawn battery charge too low on 4<!--fig:options.KOB-RESERVE.params.dawn_days_below_35pct--> of 61 replayed days. Illustration on demo data.

### 3.4 Cold rooms

> Is this room unprofitable because it is empty, or because it is inefficient?

> Today: temperature excursions and backup starts, read room by room.

> Coming: return per room with occupancy kept apart from efficiency, and repair or replace valued against doing nothing. In the demonstration, one room is simply empty, while another draws 970<!--fig:sites.harvest-cold/Room C · Kirinyaga.actual.nodes.excess_kwh--> kWh a month above what its occupancy explains, and its repair is the recommended option. Illustration on demo data, Emulated.

> Spoiled stock and who pays for it are named, never judged. Coverage is decided by the supplier or insurer.

### 3.5 EV depots

> Can you meet every departure for less with the chargers you have?

> Today: charging sessions, energy and charger availability, depot by depot.

> Coming: cost per departure met, and a charging schedule chosen because it meets every departure, not because it is cheapest. In the demonstration, the cheapest schedule would miss 93<!--fig:options.EMB-CHEAPEST.protect.departures_missed--> departures in the month, so it is ruled out. Illustration on demo data.

### 3.6 How it works

> See: every figure says how it is known: recorded, emulated, measured, calculated, estimated, quoted or modelled.

> Decide: the product prepares the options and recommends one. Your site and operations managers choose, or choose nothing.

> Act: your team creates the actions, each with an owner and a due date. Spend above the limit your executive sets waits for their approval.

> Track: every action is followed to done, with overdue shown.

> Prove: after a change, the product judges whether it happened, whether the money followed and whether the change caused it. A result is claimed only after that judgement.

> The product proposes; your people decide and act. It sends no command to your equipment.

### 3.7 The deep-dive and the pilot

The five stages, named as in `commercial-plan.md` (D1): **Initial call → Deep-dive with process owners → Integration pack and pilot timeline → Pilot and monitoring → SaaS**. One line of copy per stage.

> An initial call: we show you what the product does today on a demo operator in your sector, then check four things together: data privacy, your processes, the exports you hold, and who signs.

> A deep-dive with your process owners: your finance, operations and data people map the files you already export, one to four months of records, so your own figures can be read.

> An integration pack and pilot timeline: which sources come first, the pilot's sites, dates and success criteria, and who in your team holds each role.

> Pilot and monitoring: a pilot of about three months on your own sites, with a monthly review and the first change judged on your records.

> SaaS: a subscription, once the pilot has shown you what it is worth.

> The pilot has a fee, agreed after we have talked. We do not publish prices.

### 3.8 How we handle evidence

> Every figure says how it is known.

> Figures of different kinds are never added together. A total is never stronger than its weakest part.

> Unknown is never shown as zero, and a missing record is named.

> The same litre never carries money twice.

> We do not promise savings; we show how they would be proven. Doing nothing is always shown beside every option.

> Coverage is decided by the supplier or insurer.

### 3.9 Book a conversation

> Tell us your sector, how many sites you run, and the question your monitoring cannot answer.

> We reply to agree a time. The call is an hour: what the product does today on a demo operator in your sector, then your questions.

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
| T2 | The offer is ready to send: C2, C12 and C13 answered | not met | – | the deep-dive page's call to action becomes "Talk to us about a deep-dive" | coordinator |
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
| T13 | The deep-dive and pack fit three to ten weeks in every owner-time case still open (computed) | not met | "about three to ten weeks from the deep-dive's start to the pilot" | "The deep-dive and the integration pack take about three to ten weeks from the deep-dive's start to the pilot, depending on how complete your records are." | renderer |
| T14 | The first view comes at most six weeks into the deep-dive in every open case, and T6 is met (computed) | not met | "within a few weeks of receiving your files" | "Your target against actual, in the product, within a few weeks of receiving your files." | renderer |
| T15 | A first change proved in money on field records, with the operator's written consent | not met | – | a case story, only in the operator's words | owner |

### 4.3 Why T13 and T14 are not met today

In `commercial-plan.md` §5.2, the open case with no peak days and a four-day product reserve gives a deep-dive and pack of up to 15.5 weeks and a first view up to 6.8 weeks into the deep-dive. Both stay open until the owner answers C14 and C15. T14 also needs the money leaves, targets and the bridge live in the demo (T6).

## 5. Honesty rules for copy, and what the lint enforces
<!--derives: Rules; Words; D6; D14; Decisions-->

*Serves the objective:* credibility is the differentiator (design Introduction); one overclaim on the site costs the trust every money figure needs.

**The rules** (the design's figure rules, in public form):
1. Every figure says how it is known, and a demo figure carries "Illustration on demo data". A figure from the demonstration world's commercial records also says Emulated (D14).
2. No savings, in any phrasing; no proof or customer claims; no competitor or product names; no superlatives.
3. A replay-based value is a design value until the replay runs on recorded data (D6). It never appears on the site.
4. No price, and only the approved durations, each gated where §4 says.
5. People decide. The site never claims that the product makes the operator's choices or approvals, or acts on its own.
6. "Plan" means only the executive-approved set of changes (OD-6). Performance is against a target.
7. A coming construct is never called available now.
8. No legal or insurance conclusion: "Coverage is decided by the supplier or insurer."
9. No internal words: no Finding, leaf, registry, lane, slice, evaluator or mock-up.

**What the lint enforces.** `render_website_content_html.py` checks every quoted block in §2 and §3 against rules 1–9, the stage gates of §4.2 and the walkthrough wording before T1. It imports the design's retired terms and the naming lint from `check_alignment.py`, so the site and the design pack can never drift apart. It refuses to render if any of the planted violations in `website-copy-lint-fixtures.txt` passes; the 19 Nov additions plant `AssetEcon decides for you`, `See actual against plan`, a coming construct called `Running today`, a legal conclusion and each gated phrase.

**What still needs a reader.** Tone, whether a line overstates by implication, and whether each "Running today" line still matches design Part 1 after a release.

## 6. Decisions for the owner
<!--derives: D1; D2; D6; D12; D14-->

*Serves the objective:* these settle what the site may say and when it may say more.

| # | Decision | Context and example | Default |
|---|---|---|---|
| **WC1** | Publish the "Coming" list now, or only "Running today" | A visitor sees "Coming: options valued against doing nothing" before the demo can show it | Publish it, labelled "Coming", in delivery order, with no figure and no date |
| **WC2** | One demo illustration per vertical page | The Kobo figures are Emulated and the reserve figure rests on a replay | Keep them, each labelled as in §3; the Kobo stop-threshold value stays off the site (rule 3) |
| **WC3** | The deep-dive page before T2 | The offer's terms (C2, C12, C13) are open | Describe the path only; the call to action stays "Book a conversation" |
| **WC4** | Who records a trigger as met | A merged step is not yet live in the refreshed demo | The checker in §4.2 records it with the evidence; the owner sees each change before publication |

**Pushback, with reasons.** The 18 Nov deck gave dated "Coming" increments. I recommend stage words only: the delivery dates belong to `delivery-plan.md` and `two-week-build-plan.md`, which change at each sitting, and a public date that slips costs more trust than it earns.
