# Owner request 2026-11-19 (verbatim): design doc thoroughly checked and regenerated

Context: the owner was reading `product-transition-and-roadmap.md` §1.1 (Layer 4 pack, branch `task/product-direction-layer4-design`, head 110f6957d).

## Owner's question

> does the new layer4 design assume that it takes action on its own? i don't see its proision for users to act on the bases of context given to them, then tracked as is the case in the current product. it also says findings are conditions on factory keys, but findings are results of condition evaluation as living artifact(output). I am looking at section 1.1 of the transtion and roadmap document and i need clarity

## Owner's direction (after the coordinator's reply)

> this is not just a fix, i see it as a gap in the understanding  of the way the current product mechanics works, and what it lacks. Desciplined factor connection to outcome, value chain and performance to target, financial and operational integrations are clear boosters to an otherwise solid core in the current product and i feel that is not well recognizes. I want the design doc to be throughly checked and regenerated

## Owner's addition (later the same day, on changes to the core)

> i am not agaisnt change of the core but it needs to be for merit and intentional clearly exposing the issue against the objective we are trying to achive

## Owner's addition (on size and form)

> also, i don't need a large doc, i want very intentional, clearly explained , well illustrated document that addressess the core topics well

## Owner's addition (on diagrams)

> also let the architect add sequence and usecase diagrams , process flows..etc for clarity with mingrid for demonstration

## Owner's addition (diagram focus)

> the diagrams should focus on only aspects that pertain to the chanes to the current product

## Owner's direction on the document structure (after Phase A, commit d372c3682)

> I want the document to be structured as follows 1- current overall architecture and business value it delivers , mecahnics it uses to deliver it  2- proposed architecture and changes that deliver even better value on top  of the existing one: focus on what the new constructs bring and they fit :e.g  factor(factor leaf..) he;p descipline connection of drivers to outcomes and commercial and operational integration address the data gap for perfromance to taget feature...etc all grounded on the differtiation we want the product to bring and convert client. Pay attention to workflow as well that involves the user. We also need to have broader view of the business in the analysis and design, not just focus on isolated slice.

## Owner's answers to Q-A1 to Q-A3

> 1-a finding should have impact on the bottomline or is a risk or an opportunity - which means it needs to be acted on and the user likely reate one more action against it 2-yes lets have a few sensible roles 3-is plan different from action ? let teh archtiect explain who owns it and why it is necessary

## Owner's answers to the three open questions (plan vs Action, spend threshold, deviation tolerance)

> 1.i believe a plan is  a legitmate new construct and need to be added as such and integrated with the existing constructs. e.g an action be raised against a plan or a finding. push back if i got this wrong 2.this should be configurable and a matter of site/portfolio setting 3. yes configurable tolerance should dictate this

## Coordinator's refinement on the plan (owner approved passing it to the Architect: "yes, pass the refinement to the architect")

Coordinator's text, as given to the owner:
- An Action's **origin** is either a Finding (reactive: something observed) or a plan item (proactive work no Finding triggered: scheduled maintenance, a budgeted battery replacement, a new customer connection, an expansion).
- Separately, an Action has a **plan membership** (what it is funded and scheduled under): an Action raised against a Finding that spends shared budget or crew time also joins the period's plan, so the executive approves it with everything else.
- Rule: one origin per Action, plus at most one plan membership, so the same work is never counted twice.

## Owner's addition to the standing document brief

> one more things, i want overall objective to be considerd, not narrow slice that is detacehd

## Owner's answers on rev 16.2 open points

> Q-B1 yes, agree with the architect's pushbacks
