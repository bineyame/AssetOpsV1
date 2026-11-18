# S4-03 phase 1 review (fresh Claude Reviewer)

Scope: `2bb4f87..6ac76f3` (backend Evidence and History child reads), plus `9b065fb` (delivery fixture). HEAD at review end is `e9eb2e3`. The commits after `df72b67` change only `.agent/S4-03-handoff.md`.
Judged against: `tasks/S4-03-finding-evidence-history.md` (phase 1 row, read/route contract, ACs), `.agent/S4-03-handoff.md`, `D-2026-10-12-finding-episode-and-revisions`, `D-2026-10-11-s3-phase-2-selection-and-read`, `.ai/WORKFLOW.md` Review Packet.

## Verdict: RETURN (one small fix, no rework of the design)

The read design is sound and I verified it against the code and the writer. There is one misleading claim in the History contract that phase 3 would render as a lineage verdict. It is cheap to fix now and expensive to unwind once the UI binds to it. Everything else is accepted, and the other points are carries.

## Finding (required)

**F1 - History `cited_evidence.lineage` reports COMPLETE when it has checked only accepted-row existence (misleading claim).**
`backend/assetops_backend/analytics/finding_read.py:575`: `"lineage": "COMPLETE" if cited == resolved else "BROKEN"`, where `resolved` is `count(e.id)` from `revision_times` (`postgres_finding_store.py` revision_times, LEFT join to `accepted_evidence` only).
- Evidence (`_record_breaks`, `finding_read.py:120`) defines lineage as batch, disposition, envelope presence and digest, Foundation/binding revisions, assessment citation, run input and the cited-set digest. History uses the same word over a single join.
- Consequence: for a revision whose envelope text was tampered, or whose disposition, batch or basis does not resolve, History says `lineage: COMPLETE` while Evidence for the same revision says `lineage.status: BROKEN`. The broken-join test (`test_s4_finding_evidence_history_postgres.py:274-276`) passes only because it also deletes an accepted row.
- Why it matters: the task requires withholding a positive lineage claim when a link cannot resolve. History is the surface phase 3 shows per row.
- Fix (either is fine):
  - (a) Rename the field to what it measures, e.g. `cited_evidence: {count, resolved, accepted_rows: "ALL_RESOLVED" | "UNRESOLVED_PRESENT"}` with a note that full lineage is on Evidence.
  - (b) Compute the same break set per revision.
  - Add a test for the History row when only the envelope is tampered.

## Verification of the dispatch questions

1. **Evidence membership and lineage are correct.**
   - Membership is `finding_revision_evidence` for the exact selected revision, with tenant and Site scope (`postgres_finding_store.py:~309-346`).
   - All joins are LEFT, so a missing accepted row stays in the set as `ACCEPTED_EVIDENCE`. It is never dropped, and totals are unchanged.
   - The cited-digest recompute matches the writer: `sha256_json([[id, envelope_sha256]...])` in `ORDER BY id` (`postgres_finding_store.py:168-191`). The reader sorts by lowercase UUID string, which gives the same order as Postgres uuid byte order. The check is therefore real.
   - The envelope text digest is recomputed in SQL.
   - Cited count (`cited_total`) and run input count (`input_distinct_total`, `input_by_run`) are separate fields.
   - A lineage-read exception gives 503, not an empty bundle (API test).
2. **History paging: the 205-version in-memory proof is acceptable.**
   - The SQL path does no paging. `finding_detail` returns every revision of the Finding with `ORDER BY r.revision_no` and no LIMIT (`postgres_finding_store.py:242-244`).
   - All paging is in `history()` (`after_revision_no` filter, then slice). The in-memory test exercises exactly that code. The Postgres test walks every fixture Finding in 2-row pages against stored rows.
   - There is no SQL paging defect for the test to hide. The residual cost is that every page loads the full revision list, which is fine at fixture and MVP scale (carry C5).
3. **Refusals match S4-01.**
   - Both routes reuse the root's `open_scope`, `source_gate`, `closed` and `served`.
   - 401, 403, 404 and 503 are tested in the API test. 404 cases covered: unknown Site, unknown root, foreign revision, and cross-Site with the same tenant and a different Site ID (Postgres test). 409 for an unpinned read while closed is tested. A pinned read while closed returns `audit_only` plus `currentness: SOURCE_CLOSED`.
   - 422 comes from FastAPI UUID and Query validation.
   - There is no `knowledge_at` parameter or claim, and `replay` states that none is offered.
   - No Finding writer is added. Reads only.
4. **Listed open risks:**
   - `control_basis` is only in the digest. This is not misleading: `configuration_sha256` does hash controls (`assessment_worker.py:73-79`), and control Foundation revisions are in `foundation_revision_ids`.
   - An unpinned History read returning 409 while the gate is closed is consistent with the root and the packet's fail-closed rule.
   - Offering the S2 record link while the Performance gate is closed is consistent with the packet. The rule withholds live S3 drill-down, and Dispatch links are withheld. The S2 inspector has its own gate.
   - The `ASSESSMENT_CITATION` assumption can only fail toward BROKEN (a false negative), never toward a fabricated positive. It checks `assessment_revision.evidence_ids` rather than the segment-level `result.segments[].evidence_ids` that the writer actually cites (`finding_episode.py:434`). This is a carry (C1), not a defect.

## Carries (not blocking)

- **C1** Check `ASSESSMENT_CITATION` against the cited interval revisions' `result.segments[].evidence_ids` (the writer's own citation source) rather than the revision-level `evidence_ids`, or document the subset relation as an invariant.
- **C2** `9b065fb` loosens the delivery fixture from `not_started` to "any recognised Status" for S4-03, S4-04, S5-02 and S6-03 (`test_delivery_next_work.cjs:359`). This is acceptable because the test's intent is README links and the graph pass. Note that it no longer catches an accidental early activation of the other three.
- **C3** `provenance.case_annotations` calls the private `self.dispatch._annotate` (`finding_read.py`, evidence). It works, but a public seam would be cleaner.
- **C4** The Evidence route loads and lineage-checks the whole cited set on every page request. This is fine at the fixture maximum of 114 records, and the handoff already names it.
- **C5** The History route builds every revision summary on each page. This is fine at MVP scale.
- **C6** The root `unavailable.evidence_tab/history_tab` strings still say S4-03. Phase 2 and 3 should retire them (already noted in the handoff).

## Checks run (actual results)

- **Full backend suite.** Command: `ASSETOPS_TEST_DATABASE_URL=...@127.0.0.1:55432/assetops_test .venv/Scripts/python.exe -m pytest backend -q`.
  - Result: `3 failed, 1901 passed, 21 warnings, 2 errors in 807.15s`.
  - All 5 failures and errors are in `test_s2_gateway_access_postgres.py`, each with `FATAL: sorry, too many clients already`. They overlapped with the builder's concurrent full run on the same database.
  - That file rerun alone: `29 passed, 3 warnings in 47.36s`. The failures are environmental, not defects.
  - The failed gateway tests left temporary credential files under `%TEMP%\pytest-of-assef\pytest-1732\` (test-only, as their messages describe).
- **Targeted S4 tests**: `test_s4_finding_evidence_history_postgres.py`, `test_s4_finding_evidence_history_api.py`, `test_s4_finding_read_postgres.py`, `test_s4_finding_store_postgres.py` and `test_s4_finding_api.py` gave `33 passed, 5 warnings in 223.47s`.
- **`tools/check-all.ps1`**: `All 9 guards passed` (architecture, navigation, workflow, registry, delivery fixtures, mock-gap fixtures, orphan scan with 1 tagged and 16 baselined, scan fixtures, ledger with 110 screens).
- **Not run:**
  - No frontend checks; phase 1 has no frontend change.
  - I did not rerun the handoff's comparison on the private copy of `assetops_s4cases` (F01-gateway environment-bound IDs). I treat that comparison as the builder's claim, not verified here.
  - I did not repeat the non-vacuity mutations.
  - No database other than `assetops_test` was touched.
