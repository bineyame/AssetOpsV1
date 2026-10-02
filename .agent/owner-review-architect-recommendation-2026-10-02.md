# Owner review of the Architect demo recommendation (2026-10-02)

Issued by the owner 2026-10-02 against `.ai/ARCHITECT_DEMO_RECOMMENDATION.md`
at commit `a28479f`. Verbatim below (the "ARCHITECT_DEMO_RECOMMENDATION"
markers are citation markers from the owner's paste).

---

I think this is a strong recommendation overall. It has moved from “navigation design” into delivery architecture for the demo, which is what you actually needed. I would accept most of it, but I would not approve it unchanged.
The strongest part is that it now makes every major spine task land on a real canonical product surface, rather than allowing T027–T034 to produce disconnected implementation artifacts. T027 becomes Site Overview + Site Evidence, T028 becomes Dispatch + Finding Detail, T029 becomes Site Financials, and T034 becomes Action + Verification. That is exactly the right direction.    ARCHITECT_DEMO_RECOMMENDATION
I also strongly agree with the proposed demo story change: keep the Kobo story continuous through Finding → money → intervention → verification, then show opportunity/lifecycle breadth afterwards. That is much stronger than interrupting the core causal loop with Desta and Arsi before coming back to verification.    ARCHITECT_DEMO_RECOMMENDATION
The proposed Portfolio-lite after T034 is also a very good idea. It means the final demo’s opening mental model appears early, and every later story enriches the first screen rather than only adding another deep page.    ARCHITECT_DEMO_RECOMMENDATION I would approve that.
Where I would push back is on five things.
1. “Keep v6.9’s grammar exactly” is slightly too rigid
The document says the ten root classes and eight Site tabs are sound and that the recommendation only changes prominence.    ARCHITECT_DEMO_RECOMMENDATION
I think that is a useful default, but not something I would freeze as a principle.
We already found one probable exception: global Financials may not deserve to remain a root at all, because its meaningful content overlaps heavily with Portfolio Value & Operations. The architect itself reaches that conclusion later.    ARCHITECT_DEMO_RECOMMENDATION
So I would rewrite the principle as:
Preserve v6.9’s grammar unless the demo/product reasoning reveals a genuine ownership problem.

That leaves the architecture disciplined without making the canonical document immune to product learning.
2. I like the archetype descriptor, but it currently owns slightly too much
The proposed descriptor contains:
- Overview domains
- Performance subtabs
- Health emphasis
- Finding types
- consequence categories
- evidence capabilities
- verification templates
- vocabulary    ARCHITECT_DEMO_RECOMMENDATION
The first three are clearly presentation/domain-pack concerns.
I am less comfortable with a static UI-oriented descriptor becoming authoritative for things like:
Finding types the archetype may produce
verification templates
evidence capabilities

Those start touching domain behavior and analytic capability, not merely navigation.
I would prefer a boundary closer to:
DomainPresentationProfile
    overview_domains
    performance_views
    health_emphasis
    labels / vocabulary
    consequence presentation

while backend/domain modules remain authoritative about:
what findings actually exist
what evidence an analytic requires
what verification rules exist

The descriptor can reference those capabilities, but shouldn't become the canonical source for them.
Otherwise later you risk:
frontend pack says this Finding exists
backend analytic says something different

The architect partially protects against this by saying analytics remain ordinary backend modules, which is good.    ARCHITECT_DEMO_RECOMMENDATION I would just tighten that seam explicitly.
3. T027 Site > Evidence is good, but don't overstate “capability readiness” yet
I like moving the one-off evidence inspector into a durable canonical Site > Evidence surface. That's an excellent improvement.    ARCHITECT_DEMO_RECOMMENDATION
But there are two different things hiding under “Evidence”:
A. what records have been accepted and their quality/coverage

B. what claims AssetOps can make given those records

At T027, A definitely exists.
B becomes much more meaningful only when T028 introduces the first real analytic and its evidence requirements.
So I would sequence Site Evidence internally as:
T027:
Source records
coverage
timestamps
mapping/config basis

T028+:
Capability readiness
claim ceilings
missing evidence for specific analytic claims

The document currently says Site Evidence shows Full / Limited / None by capability.    ARCHITECT_DEMO_RECOMMENDATION That's good eventually, but I would avoid making T027 pretend it already knows rich claim readiness before a real claim exists.
This is a subtle but important semantic boundary.
4. The post-T034 reorder is directionally good, but I would not approve the exact order yet
The recommendation proposes:
T031 → T032 → T030 → T035 → T033

instead of:
T030 → T031 → T032 → T033 → T035

The rationale is persuasive: productive-use adds growth, while T030 is another loss/accountability story; service is probably more immediately compelling than battery lifecycle.    ARCHITECT_DEMO_RECOMMENDATION
I agree with the priority logic.
But the architect itself notes a real dependency uncertainty: T031 currently declares T030 as a dependency, and no shipped world curtails PV yet.    ARCHITECT_DEMO_RECOMMENDATION
So I would approve:
Priority intent:
Opportunity before fuel if dependency cost is low.
Service before battery unless feedback says otherwise.

but not hard-freeze the exact task order until Planner verifies what T030 actually provides that T031 consumes.
This is one of those places where product priority should drive the replan, but dependency reality still matters.
5. The treatment of empty contextual tabs still feels too canonical-document-driven
The recommendation says contextual tabs can be “labelled in place” before they have content, while global navigation appears only when truthful surfaces exist.    ARCHITECT_DEMO_RECOMMENDATION
That asymmetry worries me.
For example, at T028 the Finding Detail would show:
Overview
Evidence
Alternatives
Recommendation   [not implemented]
History          [not implemented]

because Recommendation and History are “labelled in place” until T034.    ARCHITECT_DEMO_RECOMMENDATION
For an internal architecture view that may be okay.
For a client-facing product, I would rather show:
Overview
Evidence
Alternatives

and let Recommendation/History appear when real.
Likewise, I would avoid eight visible Site tabs with half of them empty merely because v6.9 says there are eight canonical tabs.
The stronger rule should be:
The canonical tab set defines ownership and future placement; the rendered tab set contains only meaningful destinations unless absence itself communicates something useful.

That seems more consistent with the architect's own excellent rule for the root rail: only show truthful destinations.
Where I think the architect is especially right
The Site Overview hierarchy is good. It avoids a generic dashboard and makes the page answer:
“Is this site meeting its operating objective, and what matters now?”

The proposed structure—objective, domain assessments, selected-day physical context, top Findings, then compact consequence—is very aligned with the product.    ARCHITECT_DEMO_RECOMMENDATION
The Finding Detail hierarchy is also excellent:
bounded claim
observed facts
inference
confidence basis
claim ceiling
technical consequence
money
next step

That is much closer to what makes AssetOps distinctive than a generic finding card.    ARCHITECT_DEMO_RECOMMENDATION
The distinction between Completed and Verified is rightly made a visible product concept rather than backend semantics.    ARCHITECT_DEMO_RECOMMENDATION
And I strongly agree with keeping global Financials out of the demo rail while putting economics into Site Financials, Finding consequence, and Portfolio's value column.    ARCHITECT_DEMO_RECOMMENDATION That is cleaner than my earlier tentative root-level Financials structure.
My disposition on its major decisions
I would treat the architect's proposed decisions roughly like this:
Decision    My feedback
D1 filtered grouped root menu    Accept, but don't promise the full v6.9 end-state can never change
D2 Portfolio-lite after T034    Strong accept
D3 Kobo detect→verify uninterrupted    Strong accept
D4 opportunity before fuel; service before battery    Accept as priority intent, dependency-check before exact reorder
D5 static mini-grid archetype descriptor    Accept with narrower authority
D6 Site Evidence at T027    Accept, but T027 = source/coverage; analytic claim readiness matures from T028
D7 Action + Foundation Changes representation    Accept; very coherent
D8 park T025h    Accept


So I think the architect has substantially improved the roadmap.
The biggest thing I would send back is not “redesign this.” It is more focused:
Adopt the sequencing and product-surface recommendations, but loosen unnecessary loyalty to rendered canonical navigation, narrow the domain descriptor's authority, and distinguish source-evidence readiness at T027 from claim-capability readiness that emerges with analytics at T028+.

With those changes, I think this is strong enough to become planning input rather than another round of architecture exploration.
