# W4-03 — Mini-grid decisions and work connection

Status: planned; build spec pending. Lane A, step 2; size L in one-run commits. Branch `task/W4-03-mini-decisions-work` after independently reviewed and merged W4-01, W3-01 and W4-02. Migration `0030` follows `0029_w4_mini_depth`; `0028` remains unused. USER_REVIEW_REQUIRED: true at the W4 owner checkpoint. This packet and [Architect build spec](../.agent/W4-03-build-spec.md) are planning contracts, not implementation authorization. Independent spec review and the owner wave-start scope/core-panel gate precede build.

## Boundary and dependencies

`D-2026-10-20-post-w2-sequence` assigns `scenarios`, `alternatives`, `opportunity-finding`, and deeper `sitework-incidents`/`sitework-maintenance`. Consume W4-02's individually selected Site-local noon hours and exact accepted evidence, W4-01's frozen authored case API and index, W3-01's public provenance DTO and estate Opportunity lens, and W1 Finding/Action identities. W4-03 owns the scenario/alternative/opportunity decision records and `0030`; it does not redefine W4-01 case states, treat a case as an Action, or turn a scenario into observed money. The v69 mock and its manifest fix layout and content positions, while actual values require selected public evidence or authored, labelled assumptions.

The W1 `finding`/`finding_revision` schema is dispatch-shaped (mandatory assessment/run and candidate-minute columns). Do not insert an opportunity by fabricating those fields. The build spec gives an independent opportunity identity and a typed union integration for Site and estate indexes. W3-01's Opportunities lens remains honestly empty until that integration is reviewed and merged. Existing W1 Alternatives is already a visible Finding tab; this slice supplies an exact persisted explanation/disposition read without changing its dispatch conclusion.

## Observable exit

- A Site Financials Scenarios page shows an honest empty state and a persisted, authored mini-grid what-if after reload. Assumptions, output and optional tariff remain labelled **scenario**. No scenario writes W1/W2 consequence or measured read tables.
- The generator Finding Alternatives tab lists exact reviewed explanations and their accepted-evidence or missing-evidence basis, with a bounded disposition. It never treats absent high-frequency or override evidence as proof of absence.
- A new mini-grid Opportunity detail is backed by W4-02's five distinct selected local-day hours, with physical headroom, eligible-day denominator, accepted IDs, an optional authored load/tariff scenario and explicit demand/collection gaps. It appears in the typed Site/estate Opportunity lens only when selected and supported. Late evidence creates a new revision, preserving history.
- The two Site Work lists retain W4-01 canonical IDs/counts and show exact linked opportunity/dispatch Finding and work context where present; missing links and unverified maintenance outcomes stay visible. No mock `F-109`, `INC-203` or `WR-019` is seeded as product history.
- API refusal, migration/downgrade, 1440/390 layout, positive/missing/late fixtures and named proof follow the build spec. A successful UI reload and app-vs-mock capture at both widths are part of closeout.

## Reviewable commits

1. `0030` schema, immutable scenario/alternative/opportunity identities and exact-link tests.
2. Scoped writer/read APIs, total status and refusal tables, selected-window and provenance proof.
3. Opportunity projector, late selection and typed Site/estate index integration.
4. Scenarios, Alternatives and Opportunity pages, with every mock cell and CTA mapped.
5. Site Work delta, navigation/registry/guard update, fixture replay, captures and one same-revision backend suite.

Each commit has the tests named in the build spec and one builder handoff. Only Lane A edits shared router, shell, guard, registry and navigation files. Run focused proof per commit; run `tools/check-all.ps1`, dependency/rule-8/navigation/registry checks and one full real-Postgres backend suite at closeout. Use private `*_test` databases, ordinary ingestion and public Site/work APIs; never query simulator private truth to make a public claim. Independent slice review precedes the owner checkpoint.
