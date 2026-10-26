# AssetOps — Final Commercial Assessment Clarifications

The current `commercial-capability-readiness.md` is accepted as the commercial architecture and capability baseline, subject to the targeted clarifications below.

Do not reopen the product thesis, commercial outcome rankings, capability catalogue, or overall demo coverage. These are settled planning foundations.

## 1. Clarify engineering effort for agent-assisted development

The existing Small/Medium/Large estimates appear based on conventional engineering delivery timelines.

Implementation will be performed substantially by coding agents, with architect oversight and human review.

Reassess effort accordingly, distinguishing:

- Coding and implementation effort using the existing repository and coding agents
- Architecture/design uncertainty
- Integration and regression-test complexity
- End-to-end database/browser validation
- External device or customer-data dependencies
- Human review and acceptance requirements

Do not mechanically convert weeks into hours or assume agent-generated code is automatically complete.

Use repository-specific implementation seams, existing services and tests to identify which improvements could realistically be delivered within a focused five-working-day sprint.

Distinguish effort from confidence and risk. A capability that can be coded quickly may still require substantial validation.

The objective is a realistic **agent-assisted execution estimate**, not a conservative human staffing estimate or an optimistic one-shot generation assumption.

## 2. Tighten three commercial economic models

### A. Mini-grid: physical energy, billing and collections

Do not conflate eligible headroom, customer demand, delivered energy, billed energy and collected revenue.

A more defensible expected contribution model is:

**Expected contribution = Expected collected revenue − Incremental generation/delivery cost − Enablement cost − Other incremental operating costs**

For a simplified volumetric tariff scenario:

**Expected contribution = E_delivered × tariff × assumed collection fraction − E_delivered × marginal cost/kWh − enablement and other incremental costs**

Use appropriate tariff, billing and collection assumptions. If collection is unavailable, declare the assumption and show sensitivity.

Energy supply costs accrue even when customers do not pay.

Keep commercial opportunity, observed delivery and actual collection as separate evidence states.

### B. EV: feasible operational decisions, not merely energy shortfalls

A charging shortfall does not independently establish lost service or commercial loss.

For the bounded bus charging decision, verify:

- Initial usable energy and required departure reserve
- Available charging time and effective charging power
- Connector/session occupancy
- Shared depot power constraints
- Relevant charging efficiency and taper assumptions
- Applicable tariff and alternative costs
- Impact of reallocating charging capacity on other vehicles

Compare feasible alternatives rather than merely reporting an unmet energy target.

A small constrained decision model is sufficient; no fleet-scale optimizer is required.

The modeled outcome should explain why one charging decision is operationally and commercially preferable under declared assumptions.

### C. Cold chain: review exposure versus financial loss

Distinguish three concepts:

1. **Inventory requiring review:** Declared value of lots satisfying a documented location, product and exposure rule.
2. **Modeled financial exposure:** A monetary consequence supported by a separately justified quality/rejection/economic model.
3. **Verified inventory loss:** Established through independent quality and commercial records.

The initial demo can compellingly establish which lots require review and their declared value.

Do not label the full inventory value as expected loss, imply a damage probability from room-air temperature, or claim avoided spoilage.

Preserve uncertainty about product-core temperature, quality outcome and actual financial loss.

## 3. Distinguish portfolio triage, commercial comparison and resource allocation

These are related but separate decisions.

**Portfolio triage**

Which sites, risks and opportunities need management attention now?

Use urgency, recurrence, operational severity, data confidence, unknowns and actionability.

**Commercial opportunity comparison**

Which opportunities appear economically attractive under compatible assumptions?

Use qualified value, time window, beneficiary, intervention cost, feasibility, evidence confidence and uncertainty.

**Portfolio resource/capital allocation**

How should constrained budgets, technicians, maintenance windows or capital be distributed among competing interventions?

This requires resource constraints, dependencies and more sophisticated decision logic.

For the initial AssetOps demo, prioritize **commercially informed triage and bounded opportunity comparison**.

Do not imply that the platform already performs optimal capital or resource allocation.

Avoid a universal priority score when commercial values or risk measures are not comparable.

Present the reason for the proposed investigation or placement explicitly, and treat missing evidence as a need for investigation rather than low priority.

## 4. Explicitly prevent double-counting commercial opportunities

Add an acceptance criterion for any portfolio-level aggregate financial estimate.

Commercial opportunities may overlap. For example:

- Productive-use demand growth can increase generation costs.
- Improved dispatch can affect fuel cost and energy availability simultaneously.
- Service-reliability improvements may overlap with modeled revenue protection.
- Multiple findings may describe the same underlying commercial exposure.

Do not sum gross opportunities or individually modeled benefits merely because they share a currency.

Before aggregation, establish:

- Common beneficiary
- Compatible time window and assumptions
- Mutually exclusive or independently attributable value
- Baseline and counterfactual consistency
- Treatment of overlapping effects and incremental costs

Where independence cannot be established, present opportunities separately, identify possible overlap, or show a qualified combined scenario.

**Acceptance rule: AssetOps must never display an aggregate financial opportunity that double-counts the same underlying benefit.**

This applies to both simulated executive dashboards and future field-value reporting.

## 5. Strengthen the commercial interpretation of the deep walkthrough

The existing mini-grid generator-support intervention is a good choice for demonstrating integrated system depth.

However, do not allow it to become primarily a technical demonstration of:

Finding → Action → Technical verification.

Frame the walkthrough around the commercial operating problem and its consequences.

The preferred sequence is:

**Commercially relevant operating issue → Source-backed drivers and history → Feasible intervention → Recorded action → Independent technical verification → Qualified commercial reassessment**

Evaluate whether the existing fuel-cost model can be reapplied to comparable accepted before/after observations using:

- The same economic model and price basis
- Compatible physical measurement boundaries
- Equivalent service/reserve obligations
- Comparable operational conditions
- Explicit intervention cost and assumptions
- Source-coherent baseline and later windows

If feasible, present the resulting difference as a **post-intervention modeled commercial improvement**, not verified realized savings.

If the relevant observations cannot support a defensible comparison, display an inconclusive or unavailable financial result with the reason.

A passing reserve-verification criterion must not automatically imply lower diesel consumption or reduced financial cost.

The objective is to demonstrate that operational intelligence, intervention and verification serve a commercial decision—not merely that the Action lifecycle functions correctly.

This deeper walkthrough complements broader commercial outcome coverage; it does not replace the mini-grid productive-use opportunity, EV economics or cold-chain commercial outcomes.

## 6. Preserve the agreed product direction

The strategic goal is already established:

**AssetOps helps infrastructure operators systematically improve commercial and operational performance through integrated data, explainable intelligence, actionable decisions, historical accountability and independently verifiable evidence.**

There is no need to revisit whether AssetOps should be a reporting product or a performance-improvement system.

The architectural task is to ensure that selected capabilities and demonstrations progressively realize this established goal, without claiming capabilities or financial results that have not been substantiated.

## 7. Expected output

Make only the necessary targeted clarifications to `commercial-capability-readiness.md`, or provide a concise addendum if that avoids unnecessary document churn.

Preserve implementation evidence and existing architectural judgments.

Do not create new feature families, revise the full roadmap, implement code, or produce the five-day plan yet.

Conclude with any implications these clarifications have for demo-scope selection and agent-assisted execution estimates.

Stop after the updated commercial assessment for owner review.
