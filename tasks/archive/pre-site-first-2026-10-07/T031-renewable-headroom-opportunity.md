# T031 - Recurring renewable headroom opportunity

Status: planned
USER_REVIEW_REQUIRED: true
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).

Map: F, evidence-backed opportunity before load-addition comparison.
Depends on: T026/T027 evidence and envelope path (AC2, AC3), A's
curtailment/dispatch physics (AC1, AC3), T028's Finding/evidence/claim
structure and capability declaration (AC7), T027 Site Overview and profile
(AC7), T029 price context (Proof's price-invariance check only), T034A
Portfolio and seed, and the Lab cockpit's PV/load curves. Not T030: the
Planner's dependency check found no T030 artifact consumed.
Delivery order: after T034A; next T032 completes F. Opportunity runs before
fuel at a cost of two slices (T031, T032) ahead of T030 (`tasks/README.md`).
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
11. The headroom analytic joins the capability declaration
    (`D-2026-10-02-presentation-profile-and-capability-declaration`), which
    gives it its Site > Evidence capability row, Performance > Renewable and
    the Renewable Overview card's assessment slot. Opportunities are a lens on
    Findings, not a new class (`D-2026-10-02-grammar-ownership-test`).
12. Desta joins the Portfolio: Desta's reproducible recipe and seed
    (T036 AC1's Desta recipe, pulled forward) under
    `D-2026-10-02-demo-point-seed-rule`, its own Site through normal
    ingestion, extending the point-3 seed command. Portfolio's opportunity
    lens now renders (T034A AC8), and the opportunity Finding stays a
    separate consequence type, scenario-labelled (T034A AC5). The priority
    rule gains a new version weighting opportunity, shown on the page
    (T034A AC4).

## Proof

Compare repeated sunny low-demand windows with:
a constrained battery/reserve case, a critical-service shortage,
a low-irradiance interval and a missing-capability interval.
Assert which windows qualify, their evidence references and why others do not.

Use an independently calculated simple headroom/energy case and verify that
recurrence requires more than a single fortunate sample.
Change price/tariff and show the physical opportunity remains unchanged.
Reuse the cockpit's existing PV/load curves to inspect the Lab recipe. If
criterion 2 adds a reported signal, apply README's L2 history/view/reload
check; otherwise record that this analytic adds no new cockpit data.

Run relevant simulator/host and analytic/UI tests, shared checks and
`node tools/layout-evidence.mjs` on populated and evidence-limited Renewable
views and on Portfolio with the opportunity lens. Rail unchanged (OPERATE:
Portfolio, Sites; INTELLIGENCE: Findings; WORK: Actions); Site tabs unchanged
at seven, with Performance gaining its Renewable subtab.

*UI check (recommendation 5.1 step 8):* on the seed with Lab off, Portfolio
shows Desta with its opportunity Finding under the opportunity lens; open it
to Desta > Performance > Renewable and the Finding's evidence and limits.

## Scope limits

No load-addition artifact or paired runs; T029A owns the immutable artifact
mechanism and T032 adds the load-addition kind and the comparison.
No demand forecast, market viability score or cold-chain domain model.
Financial upside remains scenario-based when T032 adds a tariff comparison.

## Review

The owner can identify a recurring window and explain what capacity evidence
supports it and which constraints could invalidate it.
Review outcome: pending.
