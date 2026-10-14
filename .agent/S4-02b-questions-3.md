# S4-02b phase 2b: questions and conservative choices (Implementer, 2026-10-14)

None blocks review. Each has a built, conservative default.

## Q10. Closed-source state name (review M1)
Built: a fifth currentness state `AUDIT_ONLY` (reason `SOURCE_CLOSED`, plus `FINDING_REVISION_SUPERSEDED` when the revision is also old). It takes precedence over HISTORICAL/STALE/CURRENT and never derives. The bridge gives `AUDIT_ONLY` with no amount. Alternative: HISTORICAL with reason `SOURCE_CLOSED`. A separate state keeps "earlier version" and "source not open" distinguishable in the copy.

## Q11. How the demonstration Finding is labelled
Nothing in the evidence records which batch was authored for the demonstration (P01-power is posted with the registered gateway credential, like every S4 case). Built: `backend/assetops_backend/demonstration_label.py` reads the spec `conversions/s4-power-demo-cases-v1.json` and labels a Finding whose window lies wholly inside a declared case day at the declared Site (KOBO-001, 2026-10-23). It is a presentation label only; it changes no number or state. Risk: any later KOBO-001 Finding on 2026-10-23 would also be labelled. Better long-term: record authorship (a batch or source label) at ingestion; a Planner/Architect item, linked to the owner backlog "analysis input data for simulated and real Sites".

## Q12. Consequence versions on Assumptions
The packet says the Assumptions History view "shows exact price revisions and consequence revisions". Consequence revisions are per FindingRevision and there is no Site-wide consequence list read in 2a. Built: Financials › Overview lists every consequence version of the selected Finding version, each linking its exact price version on Assumptions; Assumptions lists price versions only. A Site-level "fuel cost versions that used this price" list needs a new read; deferred (G-05 itemization / later slice).

## Q13. STALE and PENDING copy (2a Q1)
Kept separate: "Out of date: no current cost" and "Not worked out yet". The STALE reason says "a recalculation is queued" only when the read lists pending work (review L4), else "has not been recalculated yet". Owner checkpoint question 4.

## Q14. PRICE_SPANS_WINDOW in the walkthrough
Not staged: it needs a test-scoped correction inside P01's window, which is not a fixture step. It is covered by `test_a_correction_inside_the_window_appends_an_unpriced_revision` (Postgres) and the frontend `UNPRICED / PRICE_SPANS_WINDOW` case. The walkthrough's UNPRICED example is `NO_PRICE` (empty store after recompute).

## Q15. Pinned consequence view keeps the head panel
With `consequence_revision_id`, the page shows the current (head) money panel first and the pinned earlier version in its own panel labelled "kept for the record". Alternative: replace the head panel. Keeping both makes the old/new comparison visible and never lets the old amount stand alone as if current.
