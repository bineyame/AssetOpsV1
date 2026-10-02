# T029 - Bounded dispatch consequence from versioned assumptions

Status: planned
USER_REVIEW_REQUIRED: true

Map: D; completes demo point 2 (expert / early prospect) with T028.
Depends on: T028.
Delivery order: after T028; next T029B, then T029A and T034.
Branch: task/T029-bounded-dispatch-financials
Sizing: first UI write path for persisted assumptions; thin product
composition over C's quantities (220-line ceiling).
Planner: Claude under the Codex-reset exception (`.ai/ROLE_CONFIG.md`).
Amended 2026-10-02 under `D-2026-10-02-demo-led-recommendation`
(`.ai/ARCHITECT_DEMO_RECOMMENDATION.md` 6.2 "T029", 2.4, 2.5, section 3
"Financial Consequence", 5.2).

## Outcome

Finding Detail, Site > Financials and a compact Overview value line show the
bounded fuel and maintenance consequence of candidate runtime.
Inspect technical quantity, price/accrual assumptions, basis and confidence
separately. On Site > Financials > Assumptions, change the price in the UI and
watch money change without changing physics: that is the point-2 demo moment.

This translates the first useful Finding before fuel and portfolio breadth.

T028 and T029 together are showable to a domain expert or early prospect. After
that conversation the Planner reassesses the remaining queue against what was
actually said, rather than treating T029B-T036 as immutable.

## Read for detail

- v4 section 22.
- Roadmap sections 3.3, 7/D and 12.1.
- Recommendation section 3 "Financial Consequence" (hierarchy and demo moment)
  and 5.2 row 2 (the point-2 journey).
- `.ai/ARCHITECTURE.md` Configuration Persistence: BusinessContext is persisted
  configuration and obeys its port, store separation, strict-parser and atomic
  write rules, including for UI edits.
- `D-2026-10-02-rendered-tabs-per-capability` (Site tabs at T029),
  `D-2026-10-02-demo-point-seed-rule` (the seed below).
- Shared checks and exclusions: tasks/README.md.

## Deliver

- **Site > Financials becomes a destination** with subtabs
  `Overview | Assumptions` (Drivers and Scenarios are later and not rendered).
  Overview: consequence lines by non-overlapping category (fuel, maintenance),
  each with technical quantity, assumptions in use, money range with a window
  or extrapolation label, and a link to the source Finding. Assumptions: the
  site's current BusinessContext version, its history, and an edit form.
  Financial pages carry no assessment status (v6.9 8.36).
- **Rendered at the end of T029.** Rail unchanged from T028 (OPERATE: Sites;
  INTELLIGENCE: Findings; the T002 `Operator home` item was removed in T027
  phase 1). Site tabs, six, canonical order: `Overview | Foundation |
  Performance | Findings | Financials | Evidence`. The tab is enabled by
  filtering the one inventory in `frontend/src/shell/operatorSiteTabs.tsx`,
  not by a per-milestone list.
- **BusinessContext is site-scoped.** No global Financials page or rail item.
  Revisit trigger, recorded here as recommendation 2.5 asks: **"shared or
  portfolio assumption sets"** - if BusinessContext becomes portfolio-shared
  with its own versions, the global Financials question reopens.
- **The point-2 seed** (AC14), owned here per `D-2026-10-02-demo-point-seed-rule`.

## Acceptance criteria

1. Persist versioned, site-scoped BusinessContext with currency, effective
   time, provenance (including the editing actor), fuel price and generator
   maintenance accrual assumption. Keep assumptions separate from physical
   Foundation ratings.
2. Resolve the assumption version appropriate to the assessed period and retain
   the technical assessment/version on each consequence.
3. Display the technical runtime/fuel range independently of the monetary range,
   including measured/modelled/scenario basis and uncertainty.
4. Maintenance consequence names its runtime/start/service accrual basis.
   An unavailable input yields unavailable consequence, not zero cost.
5. Changing fuel price changes money only; the accepted evidence, physical
   trajectory, technical quantity, classification and technical confidence stay.
6. Changing an assumption creates a traceable new economic interpretation;
   prior consequence/assumption pairs remain inspectable.
7. Show the selected window. Extrapolated daily/monthly values state the source
   window, recurrence assumption and basis instead of implying measurement.
8. Prevent double-counting the same runtime/fuel basis across Finding and Site
   totals. Fuel and maintenance bases remain separately inspectable.
9. Site Overview's value line, the Finding's consequence panel and Site >
   Financials read the same consequence model, with links to evidence and
   assumptions.
10. Internally use the roadmap's small versioned default assumption set with
    clearly labelled scenario values. Obtain the user's chosen client-facing
    assumptions before external exposure; do not invent approval.
11. Site > Financials renders `Overview | Assumptions` as real destinations;
    Site tabs render six in canonical order, and nothing is labelled in place.
12. Assumptions are editable in the UI. Saving an edit creates a new
    BusinessContext version through the strict parser and an atomic write
    (AC1, AC6); it never overwrites a prior version. Before saving, the form
    states the effective time the edit applies from and which assessed windows
    it therefore reprices. Invalid input (missing price, mixed currency or
    unit, malformed effective time) is refused with a reason and leaves the
    store unchanged.
13. BusinessContext belongs to one site; another site's consequence never
    resolves it. No global Financials route or rail item exists.
14. **Point-2 seed.** One Kobo site on template `kobo-mini-grid-60kw` v3 (no
    template-version drift), with a healthy reference window and a
    prolonged-runtime window (T028's recipes) committed through normal
    ingestion, and the default assumption set. Idempotent: running it twice
    does not double-ingest records, duplicate the site or duplicate Findings.
    Verified with the Lab gate off. Rehearsed by walking the point-2 journey:
    Sites -> Kobo Overview -> Performance > Dispatch -> Finding -> claim
    drawer -> Site > Financials, change the price.

## Proof

Use a hand-calculated fuel range with two prices and a separate runtime accrual.
Assert the monetary results and unchanged technical assessment.
Exercise missing price, mixed currency/unit refusal, effective-version change,
repeat aggregation, a UI edit that creates a version, a refused edit that
writes nothing, and any displayed extrapolation.

Run relevant backend/frontend tests, shared repository checks and
`node tools/layout-evidence.mjs` covering Financials Overview and Assumptions
(including the edit form) and the new Overview/Finding value.
Run the seed twice and show the counts unchanged. Document the seed command in
the review packet.

The cockpit may help review the Lab recipe, but money and technical quantity
consume accepted evidence and versioned assumptions only. This slice adds no
private runtime fact or required Lab chart.

*UI check:* on the seeded site, with the Lab gate off, the owner walks the full
point-2 journey above, edits the fuel price on Assumptions, and sees the same
Finding's money change while its runtime/fuel quantity, classification and
confidence do not; the prior version stays inspectable.

## Scope limits

No financial planning suite, cash-flow model or generalized tariff engine.
No global Financials page and no portfolio-shared assumption set (see the
revisit trigger above).
Tariff scenario revenue for productive load belongs to T032.
Battery replacement exposure belongs to T033.
Sites assessment columns and Sites-as-landing belong to T029B.
Do not label candidate consequence as realized savings.

## Review

The owner approves the financial assumption basis and client-facing bounds.
Roadmap 12.1 is a user decision at external exposure, not a blocker on building
the internal versioned example.
Review outcome: pending.
