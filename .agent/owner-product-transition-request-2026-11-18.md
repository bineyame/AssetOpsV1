# Owner request 2026-11-18 (verbatim): product transition document

## The request

> let the architect prepare a well illustrted document to map out the product transition in a similar way that you did but with a section on the technical details needed to get there as well as overall product roadmap, let it be put on the same layer4 folder.

"in a similar way that you did" refers to the coordinator's two answers below, given in chat just before the request. They are reproduced verbatim as the reference for shape and reasoning. They are the coordinator's own analysis, not the owner's; the Architect should verify every factual claim in them against the code and the pack and correct anything wrong.

## Owner's statement of the demo objective (same day, verbatim)

> the primary objective of the demo is to convert minigrid, ev and colchain operator executives and decision makers to adopt the product with real value that is not offered by monitoring tools they probably have and competitors in africa

## Owner question 1 (verbatim)

> what is the fundamtental difference between the current one and layer 4 from a product point of view

### Coordinator's answer (verbatim)

**In short:** today's product starts from signals and tells an operator what looks wrong and roughly what it might be worth. Layer 4 starts from how each outcome is made up, and tells them where their money stands, what to do about it, and whether it worked.

| | Today's product | Layer 4 |
|---|---|---|
| **Starting point** | Telemetry and records produce findings, such as "generator running while solar could carry the load" | Each outcome (contribution, cost to serve, service obligations) is declared as a structure of factors: litres, kWh billed, crate-days, peak kW |
| **How performance is read** | Findings are tagged to outcomes; the Portfolio cards summarise them | Plan against actual is built up factor by factor, so the 562 shortfall breaks down into 412.50 + 37.50 + 150 − 38 |
| **What a value means** | Mostly gross exposure: the upper bound if everything flagged were avoidable | The change an action makes, valued against doing nothing, net of its own cost and declared risks |
| **Choices** | One recommended action per finding | Several options per decision (including no action), compared, with rejected options shown and why |
| **Trade-offs** | Mostly displayed rather than enforced: a conflicting outcome is shown but doesn't stop an action | Service rules and warranty rights are part of the evaluation. An option that breaks dawn battery charge or loses warranty cover is excluded or penalised |
| **Across sites** | Findings are listed and summed per site | One plan across the portfolio within budget, crews and dependencies. The plan changes when the conditions change, as in the letter-of-intent switch |
| **Money sources** | Operational data (telemetry, fuel) | Operational data plus commercial and financial data: billing, collections, tariffs, contracts, warranties, quotes |
| **Proof** | Verification of the specific finding | Three verdicts: the operational change happened, the money followed, and it was caused by the action (untreated sites used for comparison) |
| **Honesty of figures** | Some labelling of where figures come from | Every figure labelled recorded, calculated, assumed or modelled, and figures from different evidence types never added together |

What this means for the buyer: today, an advanced monitoring and diagnostics tool with economic hints, overlapping with what operators and competitors already have, plus a layer of findings. Layer 4: an economic decision system for the operator's management, answering "where is our money going, what is worth doing within our budget and crews, and did it pay off". Monitoring becomes one of its inputs rather than the product.

What it costs to get there: today's observation work (telemetry ingestion and findings such as generator support) carries over, roughly two-thirds done for mini-grid. Most of the rest is new: the factor structures; commercial data integration; options and plan search; rights; the three-way proof. That is a months-long gap.

## Owner question 2 (verbatim)

> is going with the current product looking for pilot better or bulding layer 4 or someting in between with layer 4 as destination? describe your recommendation in detail

### Coordinator's answer (verbatim, abridged only by removing the closing question)

**Recommendation: the in-between path. Pilot now, with Layer 4 as the destination: sell the decision loop, deliver it narrowly at first, and build it using the pilots' data.**

Neither extreme works:
- Piloting with the current product as it is puts you in the monitoring category. The demo audience already has monitoring; pilots on those terms mostly teach whether you can match a dashboard.
- Building Layer 4 first, then piloting, means months of building without real data. Layer 4 can't be finished without that data: replay figures stay design values until run on real generator, battery and fuel series; commercial data (billing, collections, contracts) looks different at every operator; which options matter to operators is a guess until you've sat with one.

The in-between path fixes the main weakness in the pack's own delivery order (main document §9), which puts pilot onboarding last (slice 9). Move it to the start and run it alongside the build, because slices 0 (calibration) and 2 (commercial data) need a real operator's data to be done properly.

1. Lead with one vertical: mini-grid. It is the most built today (observation about two-thirds done; generator support detection exists), has the most evidence and the clearest money story (Kobo). The primitives are general, so EV and cold chain reuse them later. For EV and cold-chain prospects, the demo still shows their stories; the offer to them is a data assessment, which qualifies them and collects their data shapes.

2. The pilot offer: 2–3 mini-grid operators, mixed sizes and data maturity; three months, ideally paid with a low fee or free with a conversion clause. They give: generator and battery interval data; fuel dips and deliveries; billing and collections exports; the plan or budget; open repairs and quotes (the pack's exposed gaps become the onboarding checklist). They get a monthly economic review; early on, product plus analyst, the analyst filling gaps with the evaluator prototype, openly. Success criteria: find avoidable cost they didn't know about; run at least one supervised trial; verify the result.

3. Build order, each step shippable and visible to the pilot:

| Step | What the pilot sees | Maps to pack slices |
|---|---|---|
| A. Stop misleading | Today's figures relabelled honestly; per-site money and reasons the system already computes are shown | 1 |
| B. Plan against actual through factors | Their own "562 table": contribution against plan, split into fuel (necessary, avoidable, unexplained), billing and collections, computed from their data | 2 + 3, mini-grid only |
| C. Calibration on their data | The generator replay run on their own series, so savings become measured, not design values | 0 (spike K) |
| D. Options against doing nothing | Their real decisions valued and compared, with reasons for rejected ones | 4 |
| E. Proof | First trial verified before and after, with an untreated comparison site | 7, simplified |
| F. Plan within budget and crews | One plan across their sites | 5 |
| G. Rights and warranties, full Portfolio restructure, then cold chain and EV | Later, once the core is proven on real data | 5 (UI), 6, 8 |

Step B is the single most important: the cheapest piece that clearly beats monitoring. If B, C and E work for one operator, you have a case study that sells the rest.

Not to do: don't sell the current product as it is; don't promise all three verticals in the first pilots; don't quote replay savings as real until step C has run on the pilot's data; don't keep polishing the design pack.

Risks: analyst work doesn't scale (cap pilots, automate each manual step next); data is messy or missing (start with file imports; a pilot that can't supply billing or fuel data qualifies itself out); the money story is smaller than expected on real data (decide after step B with the first operator); effort: A and B roughly weeks, D–F a few months for mini-grid, rest follows — rough, needs a planning pass.

## Owner follow-ups after the first review (verbatim)

Owner question:

> are these time estaimtes for agentic deveopment or human dev?

The coordinator answered: agentic, at this repo's pace (observed 1–3 days per specified slice; the document assumes 1–2 weeks per reviewed change with two lanes, so heavily padded); the real limits are owner review time, rework from getting the design wrong (the Layer 4 pack took 13 revisions), and pilot calendar time; a human team would likely be several times slower (a judgement, not a measurement). The coordinator proposed that the document state this plainly.

The coordinator then proposed a fix round on the review findings (REVIEW.md "## Review of product transition and roadmap (0dd950ffd)", M1–M3, L1–L7) plus that effort clarification. The owner replied:

> yes, include that in the fix round along with workflow change to avoid rework and cutback on time

### Reference: owner-approved working rules from the Layer 4 pack (2026-11-17)

These were approved by the owner after the 13 revisions (twelfth message in `.agent/owner-layer4-direction-feedback-2026-11-17.md`, plus the coordinator's briefing rules the owner approved):
- Write the complete structure specification before any figure; figures are outputs, never targets.
- Checks independent of what they check: no shared logic, lists or hard-coded expected figures.
- Fix rounds address classes of problem, not lists of instances; keep a register of everything not derived.
- Keep agent scope small enough to hold; narrow helpers checked against the specification.
- If two review rounds in a row expect to be the last and still find new instances of the same class, stop and take the pattern to the owner.

Root cause the coordinator gave the owner for the rework: the Architect wrote the demo story first and fitted the structure to it; typed rules kept figures in place and reviews found them one at a time.

A separate, concurrent assessment covers repo declutter and agent context efficiency (`.agent/owner-repo-declutter-request-2026-11-18.md`); its recommendation file is `.agent/repo-declutter-recommendation-2026-11-18.md` once written. The workflow section here should focus on the development process (how work is specified, built, reviewed and approved) and may point to that assessment for repo organisation and context, without duplicating it.

## Owner instruction on the coordinator's three pitch points (verbatim)

After rev 2's re-review (REVIEW.md "## Re-review of product transition and roadmap rev 2 (21c329aeb)", ACCEPT WITH NOTES, L-A..L-E), the coordinator proposed a last small pass on the five Low findings plus its three pitch points. The owner replied:

> let the architect consider the three point and incldued them on merit or say why not

The coordinator's three points, as given to the owner (coordinator's analysis, not the owner's):

1. **Keep the live product in the demo.** Executives will ask "what's real today?" Show the live monitoring and findings as the foundation, then the decision layer as what's being built with design partners. A demo that is only a mock-up invites the question and loses trust when it's answered. (The document's current demo is mostly the Layer 4 mock-up; the live product appears only after its misleading figures are fixed.)
2. **Frame the pitch as a design-partner offer.** Turn the gap between today's product and Layer 4 into a reason to join early.
3. **Let early conversations run in parallel with Phase 0.** Pitch to friendly prospects while the diagnostic kit is prepared; don't sign a diagnostic until the kit and the data agreement exist.

The coordinator also said the Architect's paid-diagnostic close with a qualification gate is better than the coordinator's original pilot offer.
