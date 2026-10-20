# W3-02 — Estate evidence and money basis

Status: planned; build spec pending. Lane B, step 1 after W3-01; size L, four reviewable commits. Branch `task/W3-02-estate-evidence-money-basis` from reviewed merged W3-01 and W4-01. USER_REVIEW_REQUIRED: true, after independent slice review at the W3 owner checkpoint.

## Binding, dependencies and ownership

`D-2026-10-20-post-w2-sequence` and `D-2026-10-20-w3-02-buildspec` control this slice. The Architect contract is `.agent/W3-02-build-spec.md`. Own exact v69 `globalevidence` and `globalfinancials` roots. Consume W3-01 authorized estate scope and shared provenance DTO, plus W1 Site Evidence/consequence and W2 cold/EV selected reads. This slice projects Site-owned facts at one cutoff; it creates neither an estate assessment nor a new Site consequence.

Lane B owns estate domain reads, tests and page components. Lane A exclusively owns `main.py`, migrations, shell/navigation, the dependency registry/checker and `tools/checks/`; integrate shared edits sequentially after both lanes synchronize on main. The read-only contract needs no migration. Reservation `0028` is unused, not silently reassigned; stored projections need a versioned Architect amendment.

## Exit criteria

- Global Evidence shows every authorized Site's selected capabilities, explicit coverage/currentness and exact Site readiness destinations. Recurring gaps come only from typed persisted missing roles; no mock Action is created.
- Global Financials lists exact selected Site consequence revisions, bounded amounts or honest unpriced/withheld values, source and assumption lineage. A total appears only within a complete, comparable, non-overlapping category/currency/period/basis group. No cross-category profit, savings, collections or spoilage is inferred.
- Both roots retain UTC window and `known_at` across reloads. Missing/pending/conflicting Sites remain visible; unknown never becomes zero. Positive, empty, pending, mixed-source, mixed-currency and overlapping-basis variants pass independent review and owner checkpoint.

## Phases

1. Evidence read/API on one repeatable snapshot and full authorized scope; typed gap grouping and exact cited IDs.
2. Evidence screen: three cards, capability table, recurring gaps and boundary notice, with reviewed Lane A route integration.
3. Money read/API: exact W1/cold/EV consequence selection, comparability and exclusion proof, with no writes.
4. Financials screen and closeout: register, aggregation rule, honest totals, 1440/390 captures, tests and independent slice review.

One builder run and handoff covers one commit. The build spec maps each mock element, JSON/refusal, copy, fixture and height budget. Each commit gets focused tests; the slice gets one same-revision real-Postgres full suite, frontend checks and architecture/workflow/rule-8/navigation/registry guards. This packet remains planning status until the independent spec closure is checked and the owner wave-start scope/core-panel gate is recorded.

## Architect spec-review closure (2026-10-20)

The appended `Review closure (2026-10-20)` in `.agent/W3-02-build-spec.md` amends `D-2026-10-20-w3-02-buildspec` and governs where earlier sections differ. Scope now includes a **prerequisite commit 0** owned by Lane A: connection-taking W1 multi-day and historical-cutoff selection, shared estate selection-token/parser and read-only SQL guard integration. The four product phases above become commits 1–4 after that prerequisite. Lane B does not edit existing W1/W2 readers. The cold and EV evidence tables use the Site's four grouped mock-facing capability rows, with full raw claims retained in disclosure. Both roots use W3-01's last-seven-complete-UTC-days default, page limit 50, refusal codes, cursor and coverage shape. Mock cards, panels, columns, notices and inert action slots remain visible with honest unsupported-value copy.

Financial comparability compares normalized assumption **values** and exact windows, while preserving per-Site assumption revision IDs as lineage. A real persisted two-EV-Site positive test is required before claiming a COMPARABLE numeric group; if that producer setup cannot be made through the reviewed public path, the UI keeps the group slot and says `Comparable total unavailable for this selection`, and the issue returns to Architect. Cold unpriced heads and other selected heads stay in the register; there is no fabricated Finding gap row or estate-wide total. Five builder handoffs, the corrected 1440/390 measured budgets, named tests and exact success/error wire vectors are in the build-spec closure. W3-01 and W4-01 must merge first; `0028` remains unused.
