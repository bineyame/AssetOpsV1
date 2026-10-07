# S4-02 — Bounded Financials and assumptions

Status: outline; refine after preceding task review, before activation
USER_REVIEW_REQUIRED: true
Milestone: S4 Finding + Financials
Depends on: S4-01
Branch: task/S4-02-bounded-financials
Planner: Codex, 2026-10-07

## Visible outcome

Site financials/assumptions show technical quantity, price/maintenance basis and bounded amount for one Finding.

## Persisted object and read contract

Versioned FinancialAssumptionRevision and FinancialConsequenceRevision plus Site Financials read/write API. Apply `A-actor-identity` to `financial_assumption_revision.author_id`; persist the authenticated/system author under that contract, never a client-asserted ID.

## Demo acceptance

Change fuel price and see a new consequence revision while Finding claim/quantity stay fixed; inspect range and currency.

## Missing/conflicting evidence

No price yields unpriced amount, never zero; incompatible bases do not silently sum.

## Evidence lineage

Consequence resolves assumption version, FindingRevision, AssessmentRevision and accepted SourceEnvelope IDs.

## Review and refinement

Reviewer opens the selected-window surface and read API, verifies storage/reload and the state above, and follows lineage. Apply shared gates in the current task queue. Before implementation, refine exact fixture, wire/API fields, migration seam and focused checks using the reviewed predecessor and accepted architecture/technical design. This outline is not permission to change those contracts.

## Defer

Portfolio rollup and speculative valuations.
