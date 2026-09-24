# T031 - Recurring renewable headroom opportunity

Status: planned
USER_REVIEW_REQUIRED: true

Map: F, evidence-backed opportunity before load-addition comparison.
Depends on: T027-T030 and A's curtailment/dispatch model.
Delivery order: after T030; next T032 completes F.
Branch: task/T031-renewable-headroom-opportunity
Sizing: bounded opportunity analytic and product composition.

## Outcome

Renewable/Productive-use identifies recurring headroom windows under observed
demand, reserve, storage and service constraints. An opportunity Finding links
the estimate, evidence coverage and limits.

This supplies a concrete opportunity before adding intervention machinery.
It establishes electrical capacity, not local market demand.

## Read for detail

- Roadmap sections 3.5, 4 and 7/F.
- v4 sections 11, 17 and 22.
- Shared checks and exclusions: tasks/README.md.

## Acceptance criteria

1. A healthy underutilized recipe produces repeated daytime curtailment through
   physics and publishes the evidence required to assess it.
2. Extend the normal observation/envelope path if accepted evidence lacks
   capability/curtailment inputs. Product analytics cannot use private flows.
3. Estimate recurring headroom from accepted demand, PV capability, storage/
   reserve limits, generator operation and service evidence for named windows.
4. Present capacity and duration/energy with units, recurrence basis, coverage
   and uncertainty. Name the number of observed eligible windows.
5. Storage needs, reserve protection and critical service can reduce or remove
   an otherwise attractive headroom window.
6. Missing capability/service evidence limits the opportunity rather than
   being replaced by an ideal PV curve or private simulator state.
7. Opportunity Finding reuses C's evidence/claim structure and links from the
   Renewable screen and Site Overview.
8. Explicitly separate physical headroom from demand, sales and commercial
   viability. A configured operating case is visibly scenario/modelled.
9. Repeated analysis is deterministic/versioned and avoids duplicate Findings.
10. T032's evaluation entry appears only when that workflow is implemented;
    this task does not ship a placeholder action.

## Proof

Compare repeated sunny low-demand windows with:
a constrained battery/reserve case, a critical-service shortage,
a low-irradiance interval and a missing-capability interval.
Assert which windows qualify, their evidence references and why others do not.

Use an independently calculated simple headroom/energy case and verify that
recurrence requires more than a single fortunate sample.
Change price/tariff and show the physical opportunity remains unchanged.

Run relevant simulator/host and analytic/UI tests, shared checks and layout
evidence on populated and evidence-limited Renewable views.

## Scope limits

No immutable interventions or paired runs yet; T032 owns them together.
No demand forecast, market viability score or cold-chain domain model.
Financial upside remains scenario-based when T032 adds a tariff comparison.

## Review

The owner can identify a recurring window and explain what capacity evidence
supports it and which constraints could invalidate it.
Review outcome: pending.
