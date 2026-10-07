# T030 - Fuel reconciliation with imperfect operational records

Status: planned
USER_REVIEW_REQUIRED: true
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

Map: E.
Depends on: T027-T029, T034A Portfolio and seed, and the existing Fuel Loss
causal world.
Delivery order: after T032; next T035. Opportunity (T031, T032) runs first
under `D-2026-10-02-demo-led-recommendation`; the Planner's dependency check
found no T030 artifact consumed by T031/T032 (`tasks/README.md`). Point-2
feedback may reorder the breadth slices again.
Branch: task/T030-fuel-records-and-reconciliation
Sizing: operational-record evidence and fuel analytic.

## Outcome

Performance/Fuel explains a FuelBalanceWindow from opening level, recorded
delivery, expected generator use and closing evidence, with residual and
uncertainty. Follow its Finding to evidence and bounded consequence.

The same physical delivery can have a correct, delayed, absent or contradictory
record. Product claims respond to evidence quality; private fuel removal
remains an unexplained residual rather than an accusation.

## Read for detail

- v4 sections 11-12 and 17.
- Roadmap sections 3.4, 7/E and 4.
- FEATURE_MAP: fuel-model expectation basis and uncertainty.
- Shared checks and exclusions: tasks/README.md.

## Deliver and acceptance

1. Model a physical fuel delivery/movement independently from the operational
   delivery record. Author record conditions without changing the physical event.
2. Extend T026's operational-record family with delivery and operator-hand-dip
   records: identity, units, occurrence/effective time, source provenance and
   publication/receipt semantics through normal ingestion. Reuse that family's
   contract rather than defining a second one.
3. Demonstrate present, delayed, missing, partial and contradictory records.
   Preserve what was reported; conflicts remain inspectable.
4. Reconstruct FuelBalanceWindow only from accepted opening/closing tank
   evidence, delivery records and consumption evidence/model.
5. Define and display the residual sign convention and units consistently
   across calculation, chart, Finding and evidence explanation.
6. State whether expected consumption is measured or modelled and identify
   its inputs, model version and uncertainty. A model output is not a meter.
7. Resolve the carried fuel-model expectation-basis decision in the implemented
   analytic: retain separate sensor, delivery, consumption and timing uncertainty
   contributions and a reproducible combined bound.
8. Judge material residual against that bound and evidence coverage.
   Missing opening/closing or consumption support limits or prevents the claim.
9. A delayed delivery record can revise the assessed window after acceptance;
   original evidence and assessment history remain available.
10. Private unrecorded removal may produce unexplained movement, but private
    event identity/cause cannot enter the Finding, evidence or financial label.
11. Conflicting hand dip and sensor evidence expose disagreement; no automatic
    choice of whichever reading best matches private truth is allowed.
12. Reuse the canonical Finding/Evidence presentation and BusinessContext.
    Consequence remains a bounded residual interpretation, not theft valuation.
13. Avoid double-counting modelled generator use as both dispatch consequence
    and missing fuel loss when composing Site Financials.
14. The authored Fuel Loss numerical expectations corrected in T021 remain
    private regression checks; the product derives its balance independently.
15. Performance/Fuel shows terms, window, residual, uncertainty, completeness,
    provenance links and the effect of a late/corrected record.
16. Same accepted evidence and analytic version reproduce the balance.
    Gate off and removal of private runtime data leave it intact.
17. After reload, show new physical fuel causes in the gated private timeline;
    show delivery and hand-dip records in the separate source-record inspector
    with occurrence, publication and effective times. A missing record is not
    an absent physical delivery, and the timeline makes no theft inference.
18. The source-record inspector in AC17 extends T027's Site > Evidence record
    inspector rather than adding a second one (recommendation section 3
    Evidence).
19. The fuel-balance analytic joins the capability declaration
    (`D-2026-10-02-presentation-profile-and-capability-declaration`), giving
    it its Site > Evidence capability row, Performance > Fuel and the Fuel
    Overview card's assessment slot.
20. Genda joins the Portfolio: Genda's reproducible recipe and seed (T036
    AC1's Genda recipe, pulled forward) under
    `D-2026-10-02-demo-point-seed-rule`, its own Site through normal
    ingestion, extending the point-3 seed command. Its consequence stays a
    separate type from Kobo's dispatch consequence (T034A AC5).

## Proof

Use a hand-derived balance with known opening, delivery, use and closing terms.
Then vary records while holding physical movement fixed.

| Mutation | Required product result |
| --- | --- |
| Omit physical removal | Changed observed residual through new telemetry |
| Keep delivery, omit its record | Reduced claim capability, world unchanged |
| Release delivery record late | Revision with original provenance |
| Partial/contradictory delivery | Explicit uncertainty/conflict |
| Hand dip disagrees with sensor | Both references and bounded interpretation |
| Expected consumption model changes | Versioned quantity/bound change |
| Missing closing reading | No precise residual fabricated |
| Private cause removed after Commit | Same assessment |
| Price changes | Same physical balance and uncertainty |

Include an acceptance fixture where residual is inside uncertainty and one
where it is materially outside. Neither fixture can assert theft.
Run simulator/host operational-record tests, ingestion/analytic/frontend tests,
shared checks and `node tools/layout-evidence.mjs` on Fuel, Finding and
Portfolio. Rail unchanged; Site tabs unchanged at seven, with Performance
gaining its Fuel subtab.

*UI check (recommendation 5.1 step 10, optional in the journey):* on the seed
with Lab off, Portfolio shows Genda's fuel Finding; open Genda > Performance >
Fuel and the late record's revision with its original provenance.

## Scope limits

No fuel inventory ERP, supplier workflow, theft detection or billing system.
Generic maintenance records and work planning are not prerequisites.
This is the existing Fuel Loss story's first product Finding, after dispatch.

## Review

The owner inspects the same movement with different record quality and reviews
the consumption expectation basis and uncertainty.
Review outcome: pending.
