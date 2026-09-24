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
