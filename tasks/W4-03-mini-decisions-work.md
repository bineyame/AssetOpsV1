# W4-03 — Mini-grid decisions and work connection

Status: planned; spec-review closure recorded, owner wave-start gate pending. Lane A, step 2; size L in reviewable units. Branch `task/W4-03-mini-decisions-work` after independently reviewed and merged W4-01, W3-01 and W4-02. Migration `0030` follows `0029_w4_mini_depth`; `0028` remains unused. USER_REVIEW_REQUIRED: true at the W4 owner checkpoint. This packet and [Architect build spec](../.agent/W4-03-build-spec.md) are planning contracts, not implementation authorization. The owner wave-start scope/core-panel gate precedes build.

## Boundary and dependencies

`D-2026-10-20-post-w2-sequence` assigns `scenarios`, `alternatives`, `opportunity-finding`, and deeper `sitework-incidents`/`sitework-maintenance`. Consume W4-02's individually selected Site-local noon hours and exact accepted evidence, W4-01's frozen authored case API and index, W3-01's public provenance DTO, and W1 Finding/Action identities. W4-03 owns the scenario/alternative/opportunity decision records and `0030`; it does not redefine W4-01 case states, treat a case as an Action, or turn a scenario into observed money. The v69 mock and its manifest fix layout and content positions, while actual values require selected public evidence or authored, labelled assumptions.

The W1 `finding`/`finding_revision` schema is dispatch-shaped (mandatory assessment/run and candidate-minute columns). Do not insert an opportunity by fabricating those fields. The build spec gives an independent opportunity identity and its own scoped Site read/detail. The Site Findings Opportunity chip and W3-01 estate Finding-row Opportunity lens remain unavailable/empty with honest copy; adding opportunity rows there requires a later versioned W3-01 amendment. The canonical Site Finding's Alternatives tab is currently unavailable; this slice promotes that exact child route and keeps the legacy analytic alternatives list separate.

## Observable exit

- A Site Financials Scenarios page shows an honest empty state and a persisted, authored mini-grid what-if after reload. Assumptions, output and optional tariff remain labelled **scenario**. No scenario writes W1/W2 consequence or measured read tables.
- The generator Finding Alternatives tab lists exact reviewed explanations and their accepted-evidence or missing-evidence basis, with a bounded disposition. It never treats absent high-frequency or override evidence as proof of absence.
- A new mini-grid Opportunity detail is backed by W4-02's five distinct selected local-day hours, with physical headroom, eligible-day denominator, accepted IDs, an optional explicitly linked authored load/tariff scenario and explicit demand/collection gaps. The exact five-day Renewable evaluation links to it; Site/estate Finding lenses do not gain opportunity rows. Late evidence creates a new revision, preserving history. If W4-02 cannot produce its authored positive replay, preserve LIMITED/UNKNOWN and record the positive claim as unproved.
- The two Site Work lists retain W4-01 canonical IDs/counts and show exact linked opportunity/dispatch Finding and work context where present; missing links and unverified maintenance outcomes stay visible. No mock `F-109`, `INC-203` or `WR-019` is seeded as product history.
- API refusal, migration/downgrade, 1440/390 layout, positive/missing/late fixtures and named proof follow the build spec. A successful UI reload and app-vs-mock capture at both widths are part of closeout.

## Reviewable commits

1. `0030` schema, immutable identities, exact-link tests and catalog proof.
2. Scenario rules and scoped write/read API.
3. Alternatives API and exact canonical Finding revision.
4. Opportunity enqueue, worker and projection.
5. Opportunity read, history, currentness and provenance.
6. Scenarios and canonical Alternatives pages.
7. Opportunity page and exact five-day Renewable CTA.
8. Work decision-context overlay and frozen W4-01 Site-list presentation.
9. Authored fixture replay, navigation/registry/guard update, captures and one same-revision backend suite.

Each commit has the tests named in the build spec and one builder handoff. Only Lane A edits shared router, shell, guard, registry and navigation files. Run focused proof per commit; run `tools/check-all.ps1`, dependency/rule-8/navigation/registry checks and one full real-Postgres backend suite at closeout. Use private `*_test` databases, ordinary ingestion and public Site/work APIs; never query simulator private truth to make a public claim. Independent slice review precedes the owner checkpoint.
