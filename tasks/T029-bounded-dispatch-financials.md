# T029 - Bounded dispatch consequence from versioned assumptions

Status: planned
USER_REVIEW_REQUIRED: true

Map: D.
Depends on: T028.
Next: T030.
Branch: task/T029-bounded-dispatch-financials
Sizing: thin product composition over C's quantities.

## Outcome

Finding Detail, Site Financials and a compact Overview value show the bounded
fuel and maintenance consequence of candidate runtime.
Inspect technical quantity, price/accrual assumptions, basis and confidence
separately. Change price and watch money change without changing physics.

This translates the first useful Finding before fuel and portfolio breadth.

## Read for detail

- v4 section 22.
- Roadmap sections 3.3, 7/D and 12.1.
- .ai/ARCHITECTURE.md: Configuration Persistence. BusinessContext is persisted
  configuration and obeys its port, store separation and strict-parser rules.
- Shared checks and exclusions: tasks/README.md.

## Acceptance criteria

1. Persist versioned BusinessContext with currency, effective time, provenance,
   fuel price and generator maintenance accrual assumption.
   Keep assumptions separate from physical Foundation ratings.
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
9. Site Overview, Finding and Financials present the same consequence model
   with links to evidence and assumptions.
10. Internally use the roadmap's small versioned default assumption set with
    clearly labelled scenario values. Obtain the user's chosen client-facing
    assumptions before external exposure; do not invent approval.

## Proof

Use a hand-calculated fuel range with two prices and a separate runtime accrual.
Assert the monetary results and unchanged technical assessment.
Exercise missing price, mixed currency/unit refusal, effective-version change,
repeat aggregation and any displayed extrapolation.

Run relevant backend/frontend tests, shared repository checks and layout
evidence for Financials and the new Overview/Finding value.
Show the owner the same Finding before and after a price change.

## Scope limits

No financial planning suite, cash-flow model or generalized tariff engine.
Tariff scenario revenue for productive load belongs to T032.
Battery replacement exposure belongs to T033.
Do not label candidate consequence as realized savings.

## Review

The owner approves the financial assumption basis and client-facing bounds.
Roadmap 12.1 is a user decision at external exposure, not a blocker on building
the internal versioned example.
Review outcome: pending.
