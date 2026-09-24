# Queue Review Feedback — Verbatim

User feedback on the recreated task queue, 2026-09-24, after the Architect
review merged at `c625308`. Reproduced exactly as given, with no summary,
reordering or interpretation. Tasks and planning documents that respond to it
should cite this file rather than restate it.

---

here is my feedback on the plan the architect came up with which i need it to address: Overall, the plan is substantially aligned with the outcome we defined, and it has improved in an important way: most tasks now terminate in something observable rather than merely in architectural infrastructure. The queue explicitly identifies T027 as the internal architecture demo, T028 as the domain-expert feedback checkpoint, and T036 as the complete portfolio/client walkthrough.

I would still change the sequencing in a few places because the plan remains somewhat biased toward proving infrastructure thoroughly before exposing product value. The biggest opportunities are to thin T026, bring verification forward, and stop treating T036 as the first meaningful client-facing milestone.

Alignment against our three principles
Principle    Assessment    Comment
Build toward clear demonstrable slices    Strong    T024, T025, T027, T028 onward have explicit observable outcomes rather than abstract framework completion.
Demo speed over pedantic purity    Mixed-good    Much improved, but T021A and parts of T026 are still architecture-semantic work sitting directly in the critical path.
High-level but concrete    Strong    Tasks generally specify causal/product outcome and acceptance behavior without prescribing every implementation detail. Some acceptance lists are still longer than necessary.

The structure from T024 → T025 → T026 → T027 → T028 is particularly coherent. T024 builds the smallest useful electrical world with three separately addressed loads, PV, battery, service and curtailment. T025 then makes that a credible hybrid mini-grid by adding generator behavior and policy while explicitly refusing to script a Finding. T027 then crosses the actual product boundary and produces a persistent Site Overview from normal ingestion. Finally, T028 creates the first genuinely useful AssetOps product interaction—Site → Dispatch → Finding → Evidence—and explicitly labels itself the earliest domain-expert feedback point.

That is exactly the direction we wanted.

Where I would change the plan
1. T026 is carrying too much work before the first product Finding

T026 currently combines two different concerns:

A. evidence needed for the dispatch Finding

PV capability
BMS SOC / capability
generator
load
policy
operator-commanded records

and:

B. gateway realism

outage
buffering
recovery
retry
duplicates
out-of-order delivery
buffer exhaustion
noise/bias/gaps

A is directly required for T028. B mostly is not.

Gateway recovery is a useful proof of architecture, but it is not what makes a former mini-grid operator say:

“This Finding could help me.”

For demo speed, I would narrow T026's mandatory outcome to:

healthy + prolonged runtime
        ↓
PV/BMS/generator/load/policy evidence
        ↓
canonical envelopes
        ↓
enough imperfect evidence for T028

Keep one simple gap/delay case to prove evidence limitations.

Move full outage/buffering/retry/out-of-order/buffer-exhaustion behavior into a later hardening task unless it is almost free because the mechanism already exists.

This is the most obvious place where the plan can better embody:

product demonstration before infrastructure completeness.

2. Do not let T021A become a philosophical checkpoint

T021A is small and correctly placed after T021; it removes an execution_requirement claim from reported observations and explicitly says the kernel does not depend on it.

I would keep it in the queue only because it is cheap now and potentially expensive after traces freeze, not because it represents meaningful product progress.

Its execution rule should effectively be:

time-box it; implement the narrow parser closure; no architectural discussion.

If it unexpectedly grows, I would move it out of the critical path rather than let it delay T022.

This is precisely the kind of work your new principle is aimed at controlling.

3. T023 is justified, but don't polish its inspector

T023 is an infrastructure slice, but it protects one of the few boundaries we explicitly decided must be correct:

canonical SourceEnvelope is the sole future product crossing.

It creates persisted source envelopes that can be inspected without live world objects, and explicitly does not yet perform ingestion.

I would retain T023.

But its Lab inspector should remain extremely utilitarian. The value is:

I can inspect exactly what is about to cross the boundary.

Not:

we now have a polished source-envelope debugging application.
The bigger sequencing question: verification is too late

This is the most important product-level adjustment I would make.

Current sequence is:

T028  first Finding
T029  money
T030  fuel reconciliation
T031  renewable headroom
T032  productive-load paired comparison
T033  battery lifecycle
T034  intervention verification

The logic is internally consistent.

But from a product-positioning perspective, Finding → action → verification is more fundamental than battery lifecycle and arguably more differentiating than the third or fourth analytic.

T034 is very strong. It says work completion does not resolve the Finding; post-action evidence must demonstrate the target and guardrails. That is one of AssetOps's strongest product ideas.

I would therefore aim for this product progression:

1. detect
2. explain
3. monetize
4. intervene
5. verify
6. add analytic breadth

rather than:

1. detect
2. explain
3. monetize
4. fuel story
5. opportunity story
6. lifecycle story
7. finally verify

The architectural complication is that T034 currently depends on T032's immutable intervention mechanism and T033's battery-stress guardrail.

I would question the T033 dependency.

For the first verification story, these guardrails are already meaningful:

candidate generator runtime
battery reserve breaches
critical-load service
unserved energy

Battery stress can be added later as a richer guardrail.

So I recommend:

T032 intervention machinery
        ↓
T034 verification
        ↓
T033 richer lifecycle/stress

or, even better, extract the minimal immutable policy-intervention mechanism needed by T034 so verification can happen shortly after T029.

That would materially strengthen the demo path.

T030 and T031 are very well aligned

I would not significantly change these.

T030 is a good second analytical story because it tests an important AssetOps behavior that dispatch alone does not: combining physical evidence and operational records without overclaiming cause. It explicitly keeps private removal out of the product conclusion and treats it only as unexplained residual.

T031 is also particularly strong because it prevents AssetOps from becoming a pure loss-detection product. It finds recurring physical renewable headroom while explicitly refusing to equate that with market demand or commercial viability.

Those are both product-relevant, not architecture for architecture's sake.

T032 is sound, but potentially over-engineered for the first comparison

T032 is technically excellent. It freezes the load addition, compares effective frozen inputs at field/path level, isolates comparison history from ordinary site history, and sends both worlds through normal ingestion.

This is architecturally strong.

But there is a risk that the comparison machinery becomes a project in itself.

For the demo, the visible requirement is simpler:

same site
same window
same forcing
same initial conditions
same policy

only difference:
+12 kW productive load

Then show:

baseline        intervention
PV use
curtailment
diesel
energy served
scenario revenue

The rigorous frozen-input comparison should remain underneath, but I would tell the implementer:

implement exactly enough comparison machinery to prove this one load-addition scenario; do not build a generalized experimentation platform.

That is consistent with the task's stated scope, but worth reinforcing.

T033 is valuable, but it is the easiest major story to defer

T033 is carefully scoped: it avoids turning stress into measured SoH or precise remaining life, keeps unknown historical stress unknown, and separates replacement exposure from operational loss.

So I like the design.

But in terms of speed to a compelling client demo, this is less essential than:

Dispatch Finding,
financial consequence,
productive-use opportunity,
intervention verification.

If schedule pressure appears, T033 should be the first major story to move behind early client feedback.

That would not weaken the core proposition.

T036 is a good full demo, but it should not be called the first credible client milestone

T036 itself is well conceived. The six sites each have independent histories, Findings are normally computed rather than scripted, financial categories remain separate, and Lab truth comparison appears only at the end.

But I would change the planning language around it.

The queue currently calls T036:

credible client-demo checkpoint.

That is too conservative given our intent.

There should be three explicit commercial-feedback points:

T027
INTERNAL ARCHITECTURE DEMO

T028 / T029
DOMAIN-EXPERT + EARLY PROSPECT DEMO
one site, one strong Finding, evidence, money

T034-ish
STRONG PRODUCT DEMO
Finding -> action -> verification

T036
FULL PORTFOLIO / POLISHED CLIENT DEMO

A former mini-grid colleague does not require Meki, Kobo, Genda, Bahir, Desta and Arsi before they can give valuable feedback.

The README correctly says feedback should be sought at T028 before the portfolio exists. I would make that philosophy more prominent throughout the plan.

One missing artifact

The queue includes:

T035 — Bahir start failure and bounded service assessment

but the detailed T035 task was not among the attached files.

So I cannot assess whether its specific scope is appropriately lean.

Conceptually it fits the final portfolio because it supplies the reliability/service story that the other sites do not. But before implementing it, I would review it using the same standard:

Can we create one credible outage → backup response → unserved-energy chain without building a generalized incident-management subsystem?

My preferred adjusted delivery path

I would preserve almost all of the work plan, but conceptually optimize it toward this sequence:

T020A / A1 / B
      foundational contracts, aggressively time-boxed

T021
      causal proof

T021A
      cheap parser closure only

T022
      FIRST VISIBLE SIMULATOR

T023
      canonical boundary

T024 + T025
      CREDIBLE PHYSICAL MINI-GRID

T026-lite
      only dispatch-critical evidence + basic imperfection

T027
      FIRST REAL ASSETOPS SITE

T028
      FIRST VALUABLE PRODUCT
      >>> TALK TO MINI-GRID CONTACT HERE <<<

T029
      ECONOMIC RELEVANCE

then prioritize:
      intervention machinery + T034 verification

before necessarily completing:
      T030 / T031 / T032 / T033 breadth

then:
      fuel
      opportunity
      lifecycle
      reliability
      portfolio polish

I would not insist on exactly that ordering if dependencies make it artificially expensive. The important principle is that after T028/T029, the Planner should reassess the queue based on what the domain expert says rather than treating T030→T036 as immutable.

Bottom line

The plan is good and substantially aligned. It clearly reflects the demo roadmap rather than the earlier tendency toward architecture-first implementation.

The three changes I would make are:

Thin T026 to dispatch-essential evidence; defer full gateway-failure realism.
Bring intervention verification earlier, and do not require battery-stress work before the first verification story.
Treat T028/T029 as a legitimate external-feedback/client-learning milestone, with T036 representing the complete polished portfolio demo—not the point at which customer conversations may begin.

Those changes would make the plan better match the principle you stated: real visible product progress first, architectural rigor where it materially protects credibility, and everything else only when the demo or real user feedback earns the complexity.

---

# Round Two — Verbatim

User feedback on the resequenced queue, 2026-09-24, after the Architect
revision at `2970d74`. Same treatment: reproduced exactly, no summary.
Two changes requested, one area flagged to watch without changing.

---
The revisions are materially better aligned with the outcome and with the three principles you set. The plan now feels much more like a product-delivery plan constrained by architecture, rather than an architecture programme that eventually produces a product.

The biggest improvement is that the queue now has explicit progressive demo checkpoints rather than one distant finish line: T027 is the internal architecture demo, T028/T029 is the domain-expert/early-prospect demo, T034 is the strong product demo, and T036 is the polished portfolio demo. That is exactly the framing we wanted.

What changed particularly well

T021A is now correctly treated as cheap contract hygiene rather than product progress. The new execution rule says to implement the narrow parser closure, avoid architectural/vocabulary discussion, and move it out of the critical path if it grows. That is a very good embodiment of “demo delivery speed over pedantic purity.”

T023 also improved in exactly the right way. The canonical source-envelope boundary remains protected, but the inspector is explicitly described as utilitarian and not worth polishing at the expense of the first Finding. That is the right distinction between important boundary and unimportant presentation sophistication.

The T026 change is probably the strongest correction. It now carries only the dispatch evidence the first Finding actually needs—PV/BMS/generator/load/policy evidence, one gap and one delayed publication—and explicitly refuses to re-expand into gateway recovery, buffering, retry, duplicate and noise realism. That directly removes unnecessary work from the path to T028.

The milestone at T028/T029 is now framed correctly. T028 says it is the first valuable Finding and T028+T029 is a legitimate early external demo rather than a rehearsal. T029 then explicitly says the Planner should reassess the rest of the queue after that conversation instead of treating later work as immutable. This is important: real operator feedback now becomes an input to planning before the product is “finished.”

Extracting T029A from T032 was also the right architectural/product trade. The immutable intervention mechanism is now available immediately after the first monetized Finding, without requiring productive-use analytics and a generalized paired-comparison mechanism first. T029A is deliberately restricted to one POLICY_CHANGE mechanism and a utilitarian Lab interaction.

That enables the biggest improvement to the sequence: T034 now comes immediately after T029A and closes the shortest strong AssetOps product story:

detect
→ explain
→ monetize
→ intervene
→ verify

The task explicitly says it no longer depends on fuel reconciliation, productive-use or lifecycle breadth, and battery stress is no longer a prerequisite guardrail. That is exactly the product priority I was hoping the replan would adopt.

T032 is also substantially better scoped. It says, in effect: build one exact comparison—same site, same window, same forcing, same initial conditions, same policy, plus one added productive load—and implement only enough rigorous comparison machinery to make that scenario trustworthy. It explicitly warns against building a generalized experimentation platform.

And T033 now has the right status: useful, valuable, but explicitly the first major story to defer under schedule pressure. That is consistent with the product priorities.

T035 is now well scoped

The new T035 fills the missing reliability story cleanly. Its leanness rule is strong:

one outage → backup response → unserved-energy chain, without building a generalized incident-management subsystem.

The task also correctly reuses T034's critical-service/unserved-energy basis instead of creating another measurement model.

I would keep that.

Two things I would still change

The first is T026A should not be a hard prerequisite for T036.

T026A is now correctly described as deferred hardening and explicitly “not a gate on C, D or H.” It covers outage buffering, retry, duplicates, out-of-order release, buffer exhaustion and noisy signals.

But T036 currently declares:

Depends on T027–T035, T026A, and completed A.

I don't think that dependency follows from the product goal.

The polished portfolio demo needs:

healthy site
dispatch loss
fuel
productive-use opportunity
battery trajectory
reliability
verification

It does not need a full gateway outage/recovery demonstration.

Even T036's own acceptance criteria do not fundamentally depend on T026A. The Lab proof can demonstrate truth isolation and a claim-limited evidence case using the ordinary gap/delay mechanisms already delivered by T026.

So I would change:

T035
→ T026A
→ T036

to something more like:

T035
→ T036

T026A = optional hardening
before or after T036 depending on feedback/time

or make T026A conditional:

required before T036 only if the final client demo deliberately includes gateway-outage recovery as a proof story.

Otherwise a deferred architecture-hardening item has quietly become a gate on the polished product demo.

That would undermine the principle we just established.

The second change is smaller: T033 and T035 should remain reorderable.

Current order is:

T032
T033 battery lifecycle
T035 reliability
T026A
T036

The plan correctly says T033 is the first major story to defer under schedule pressure.

For many mini-grid operators, I suspect the Bahir story:

generator requested
→ start failure
→ insufficient supply
→ critical load affected
→ unserved energy

may be more immediately operationally compelling than battery replacement exposure.

So I would avoid freezing:

T033 must precede T035

as a strategic sequence.

After T028/T029 feedback, you may find the operator says:

“Backup failures and unserved customers are much more important to me than battery degradation.”

Then the appropriate sequence is:

T034
→ T035
→ T030/T031...

and T033 moves later.

The README already gives you permission to do this by saying later tasks should be reassessed after T028/T029. I would make T033/T035 ordering explicitly flexible rather than merely relying on that general statement.

One area to watch, but I would not change yet

T027 still has a fairly substantial acceptance surface for the first Commit/ingestion path: durable manifests, resumable release, conflict semantics, overlapping-record behavior, persistence of rejected records, timestamp distinctions, and evidence inspection.

Unlike T026A, most of this sits on a protected seam. I would therefore not strip it aggressively.

But I would tell the implementer:

Do the minimum robust implementation necessary to prove source-envelope → normal ingestion → persistent Site Overview. Do not turn T027 into a generalized ingestion reliability project.

For example, resumability can be simple and correct rather than production-scale.

So I see T027 as an area to watch for scope growth rather than something currently misplanned.

The revised queue now has the right shape

Conceptually, it has become:

FOUNDATION
T020A / A1 / B / T021 / T021A

        ↓

VISIBLE SIMULATOR
T022

        ↓

REAL SOURCE BOUNDARY
T023

        ↓

CREDIBLE MINI-GRID WORLD
T024 / T025

        ↓

JUST ENOUGH EVIDENCE
T026

        ↓

REAL ASSETOPS SITE
T027
        ★ INTERNAL DEMO

        ↓

FIRST PRODUCT VALUE
T028
        ★ DOMAIN EXPERT

        ↓

BUSINESS RELEVANCE
T029
        ★ EARLY PROSPECT DEMO

        ↓

INTERVENTION MECHANISM
T029A

        ↓

CLOSED LOOP
T034
        ★ STRONG PRODUCT DEMO

        ↓

BREADTH, GUIDED BY FEEDBACK
T030 fuel
T031 headroom
T032 productive-use what-if
T033 lifecycle OR defer
T035 reliability

        ↓

PORTFOLIO
T036
        ★ POLISHED CLIENT DEMO

        ↓ / parallel

T026A
gateway hardening if/when justified

That is much closer to how I would actually build AssetOps.

My overall comment

I would now be comfortable starting implementation from this plan, subject to the one meaningful change:

remove T026A as an unconditional prerequisite of T036.

Everything else is either well aligned or appropriately flexible.

More importantly, the plan has now internalized the principle that I think matters most for this stage:

architecture exists to make each increasingly valuable product demonstration credible; the project does not have to finish the architecture before it starts learning from users.

That is a substantial improvement over the earlier queue.
