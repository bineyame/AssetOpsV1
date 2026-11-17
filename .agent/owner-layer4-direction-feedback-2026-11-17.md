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
