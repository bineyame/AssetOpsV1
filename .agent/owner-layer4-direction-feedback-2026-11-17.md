# Owner feedback 2026-11-17 (verbatim): Layer 4 design pack direction

Context: on the Layer 4 design pack at Docs/demo-sprint/product-direction-layer4/ (rev 3, commit f5d2b9a4f), based on .agent/AssetEcon_Product_Direction_Layers_1_to_3_and_Claude_Brief_REVISED.md.

Owner, first message:

> I find both the main design document and the mockup narrow stiched ideas than fundamental designs.

Owner, second message (answering the coordinator's three direction questions: whether reuse is a hard constraint, whether the mock-up gets a new structure, and whether the existing pack stays as input):

> The core point about extend and reuse is on the bases of merit for efficency, to the extent it is aligned with where we want to go(thre is assumption that many of the existing things are still relevant but if not they should be mentioned why and a proper new approach taken). Regarding the mockup, the request is not to have a COO, CEO...separate filters and new menu items, but to review the overall current portfolio experience and structure it in a way those requirements are met. I see a narrow focus overall instead of defining fundamental mechanics and derive the specifics accordingly.

Owner, third message (added while the redesign Architect was running):

> integrations needed , new algorithms/modifications, UI strategy need to be mentioned as well

Owner, fourth message. The coordinator had summarised its understanding, beginning with the mechanism step "an outcome falls short of plan → the cause behind it is identified → a lever is selected → ...". The owner replied:

> yes, for the most part. a slight correction: "an outcome falls short of the plan" , more like it is observed by the underlying factors which are stucturally defined- so in that sense you got it backward

Owner, fifth message. The coordinator summarised its understanding of the owner's need in six points (below). The owner replied "yes, that's right", and then:

> you may pass those points you shared to it, as a guide

The six points the owner confirmed:

1. The foundation is the structure the brief already defines. Each outcome is built from underlying operational, commercial and financial factors, with clear units, periods and scope. The product watches those factors. Where an outcome stands, including any shortfall against plan, is read upward through that structure; it is never detected at the top first and explained afterwards. Levers act on the factors, and so do options, actions and verification.
2. The design starts from those mechanics and derives everything else from them: how each kind of asset (mini-grid, cold chain, EV) fills in the shared structure with its own factors, levers and limits; the integrations each factor needs, and why; the new algorithms and the changes to existing ones; the UI strategy; and the restructured Portfolio experience.
3. Today's system is judged on merit against that target. Much of it is probably still relevant. Where a part fits and saves effort, keep or extend it. Where it doesn't, say why and design a proper new approach. The current code must not shape the design.
4. The mock-up rethinks the current Portfolio experience as a whole. Its structure follows the same mechanics, so the CEO, COO, CFO and CCO questions are answered naturally. There are no role switches, extra filters or new menus added on top.
5. The Architect must understand the brief itself. It works from the owner's document and the owner's own words, not from coordinator summaries.
6. Success means one coherent design in which each detail clearly follows from the core, not a set of good but separate ideas held together by examples.

Owner, sixth message (on why the previous version fell short):

> i was not against the re-use, but the re-use itself was narrow, in the sense that it did not establish the core future mechanics, and then decided what to reuse, rebuild or create, and often it focussed on a specific path(e.g kobo or specific minigrid) that overarching logic

Owner, seventh message (on rev 4, while the rev 5 fix round was running):

> one things to note: execute questions should not be stated verbatim, they should just naturally emerge on the way information is organized

Owner, eighth message. The coordinator explained how it understood the seventh message (text below). The owner replied: "yes, pass that to the architect".

The understanding the owner confirmed:

- The screens do not state the executive questions as text: not as titles, labels or subheadings, and not as captions such as "This answers the CFO's question…". The answers come from how the Portfolio is organised: what comes first, how things are grouped, how one view leads to the next, and what each number breaks down into. Each executive finds what they need without being told "this is your question".
- Headings name the business content, not the question. For example, "Contribution by Site, plan against actual" rather than "Why is performance off plan?".
- The structure itself carries the answers. The CFO question emerges when each outcome breaks down through its factors to plan against actual. The COO question emerges when the plan and its constraints sit where action is decided. The CEO question emerges when the overview shows which outcomes are moving and why.
- The questions stay in the design documents as acceptance tests the design must pass. On screen they are invisible.
- The same holds for the mock-up's tab and section names, and for the walkthrough script. The presenter can talk through the executive's concerns, but the product screens do not spell them out.

Owner, ninth message (on rev 8). The coordinator had commented that per-option Protect effects, option values and plan values are hand-written into the demo data, decision by decision, instead of being derived by evaluating the factor structure as the "Evaluate" mechanic says; that the R8-M1 and R8-M2 errors are symptoms of this; and that the checker reconciles those figures but does not derive them. The owner replied:

> make sure the reviewer also checks your points, the structural aspect of mechanics are still very important even in the document illustration

Owner, tenth message (on rev 9). The coordinator offered two options: (A) address the rev 9 review findings R9-M1..M4 and R9-L1..L3 together with the coordinator's points 1, 3 and 4 on rev 9, then a fresh review; or (B) address the R9 findings only and treat deeper-layer evaluation as a delivery slice. The owner chose A:

> A, let the architect address all of them

The coordinator's points the owner authorised passing on:
1. The evaluated structure covers only the money layer (revenue, cost to serve, contribution). The deeper layers declared in main doc §2.1 are not evaluated: the value-chain stages (delivered → metered → billed → collected), the physical sub-structures (e.g. generator running split into necessary and candidate), the Protect measures, the O2 operational-productivity measures, and rights (who bears a cost). Protect effects are computed from restore dates only. The causal step of each option, why it changes a factor by a given amount, lives in these layers, and it is still a hand input.
3. Only six Sites have option base factors (Kobo, Kisiwa, Mto, Mwea, Kirinyaga, Embakasi). Thika, Kasarani and Ruiru decisions are not evaluated through the structure.
4. Rights sit outside the structure. The Mto inverter options have no factor changes, only a one-off cost, so their whole difference is handled outside it.

Owner, eleventh message:

> pass your previous comment to the architectas well about gaps on structure not producing figures concern

The coordinator's comment on rev 9, as given to the owner:

What now meets it:
- Each vertical has declared outcome formulas over named factors. For example, mini-grid contribution is revenue minus cost to serve, with revenue = billed kWh × tariff + productive kWh × productive tariff.
- Options are written as changes to factors, not as results. Kobo's stop-setting option is "diesel −210 L/month, battery throughput +150 kWh", and its value is computed by re-evaluating the structure against doing nothing.
- Plans are found by search under the declared constraints. Budget, one-of choices, dependencies and switches are inputs, and the plans are worked out from them. Sensitivities, such as diesel 20% cheaper, are factor overrides, so they move consistently.
- The same machinery serves all three verticals.

Where it still falls short:
1. The evaluated structure is shallow. It covers only the money layer: revenue, cost and contribution. The design's own structure (§2.1) is much deeper, and none of these layers is evaluated: the value chain from delivered to metered, billed and collected; the physical layers, such as generator running split into necessary and avoidable; the Protect measures; the operational productivity measures; and the rights that decide who bears a cost. The Protect effects are computed only from restore dates, which is date arithmetic rather than structure.
2. The causal step is still entered by hand. Kobo's −210 L, Mto's 1,650 kWh and 68 L, and Kirinyaga's −776 kWh are typed in as inputs. That is exactly where the mechanics' argument lives: why this option changes this factor by this much. Some of these are honestly flagged as replay design values. Others carry no flag, including the welding load's 217.8 L, the Kisiwa battery's −150 L and Kirinyaga replacement's −1,171.5 kWh.
3. Coverage is partial. Options have base factors for only six Sites: all three mini-grid Sites, Mwea and Kirinyaga for cold, and Embakasi for EV. Thika, Kasarani and Ruiru decisions are not evaluated this way, so their figures still come from somewhere else.
4. Contract rights sit outside the structure. The two Mto inverter options have no factor changes, only a one-off cost, so their whole difference is handled outside it.

In short: the illustration now evaluates the top layer of the structure honestly, but the lower layers, where the causal claims are, remain hand-written inputs. That's a sound way to stage the work, but it isn't yet "the structure produces the figures" all the way down.

Owner, twelfth message (during the rev 13 round). The owner asked why the architect kept making the same kind of mistake. The coordinator gave its diagnosis and listed which parts could be passed on as instructions. The owner replied: "yes, send points 1-4 to the architect". The four points:

1. Answers first, structure second. Demo figures are outputs, never targets. If the structure gives a different number, the figure and the story change, not the structure. "No headline figure changed" is not a success criterion. Any rule, key or tag that exists to keep a figure where it was must be removed or listed as a declared input.
2. Fix the class, not the case. The derivation register (the full sweep) is the main deliverable of this round, not an appendix to the fixes.
3. Checks must not share the author's assumptions. The checker must not import or copy the evaluator's logic, must not hard-code expected figures, and must not share lists with the code it checks. Every expected value is recomputed independently from declared inputs.
4. Scope. First write the complete structure specification: factors, layers, rights, limits, horizons and the declared inputs. Then make the data, code and screens conform to it. Use narrowly scoped helpers, each checked against that specification.

Owner, thirteenth message (18 Nov, on the final pack, commit 879fa008f). The owner said "i don't quite understand section 7.1 of layer4-transformation-design doc, please explain it here more clearly", then asked "so for kobo, how does that number 562 and the 330, 37.5, 150 and 120 workout?". The coordinator explained Kobo as below. The owner then replied:

> yes, let the architect rewrite section 7 that way

The coordinator's Kobo explanation the owner referred to ("that way"):

- Start from the inputs the section leaves out: plan 700 L of diesel (all necessary), actual 1,180 L consumed (fuel balance: opening dip 220 + deliveries 1,200 − closing dip 240).
- Split the actual: metered generator energy × consumption rate 0.30 L/kWh = 1,060 L the generator should have used; dispatch classification splits it into necessary 730 L and candidate 330 L; the remaining 1,180 − 1,060 = 120 L is unexplained (above the 2% tolerance, about 24 L, so investigate).
- A plan-against-actual table per factor, priced at 1.25/L: necessary 700 → 730 (+30 L, −37.50); candidate 0 → 330 (−412.50); unexplained 0 → 120 (−150.00); total 700 → 1,180 (−600.00, diesel cost 875 → 1,475).
- Revenue: billed 8,645 vs 8,550 kWh = +95 kWh × 0.40 = +38.00. O&M and staff on plan.
- Sum: −412.50 − 37.50 − 150.00 + 38.00 = −562.00; contribution 1,445 plan → 883 actual.
- State honestly what is derived (money figures, totals), what is recorded (fuel balance), and what is a declared input standing in for a calculation (the 730/330/120 split, labelled "Calculated from records" but typed in the demo).
- Separately, the coordinator had walked 7.1 step by step (Observe → Evaluate → Choose → Prove), splitting Choose into: the plan and its limits; (a) valued in money; (b) protective, not valued in money; downside and sensitivities; listed-beside items; the switch. The coordinator noted the Choose paragraph packs all of this into one ~400-word block.
