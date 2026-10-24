# W5-04a V1a/V1b builder questions (against main f7761b28)

Builder, 2026-10-24. Raised under the dispatch rule "if anything is unclear or contradicts the merged code, stop and
list it". Each question names the ruling, what merged code does, and the options seen. No option is chosen in code
for Q1-Q4; the V1a parts that do not depend on them were built (see `.agent/W5-04a-handoff.md`).

## Q1 - Where the EV "Finding pin" is stored (readiness ruling 10 vs spec basis keys and merged W5-02)

Ruling 10: "store `window_start`, `window_end`, `known_at` (selected cutoff) and exact `finding_revision_id` in the
immutable intent selection/basis already owned by W5-02", taken from "the server-reselected EV `_snapshot` for the
POST's `from,to,known_at`".

Merged code: the closed intent POST body is `{supersedes_id, declared_at, criteria, basis, actor, idempotency_key}`
(`work/domain_action.py:174`) with no `from/to/known_at`; the build spec fixes EV `basis` keys as exactly
`{finding_revision_id, work_case_id, work_record_id, accepted_evidence_ids, session_ids}`. W5-02 stores no window or
cutoff anywhere: the cold pin is recomputed by `_ReadTx._pin` (`postgres_work_read.py:234`) from the Finding
revision's `analytic_run` window, the Site's `ingestion_disposition` cutoff and the selection cutoff
(`command_now` on write, the read `known_at` on detail). The detail read returns `intent.basis` verbatim.

Options: (a) store nothing new - the pin is the pinned revision's run window plus the intent's `recorded_at` as the
selection cutoff, both already immutable; (b) the server appends a stored-only `pin:{window_start,window_end,known_at}`
object to `basis` (the stored basis then differs from the closed body shape and changes the detail wire); (c) add
`from,to,known_at` to the closed POST body (wire change to K1). Which?

## Q2 - Message for a malformed intent/case-link body before the Action is resolved (pre-flight 10, readiness 11)

Merged order (`domain_intent.py:97-142`): closed shape and static bounds 422 run before actor authorization and
before the store transaction resolves the Action (404). For EV the criterion count (3 vs 4) and the `session_ids`
basis key are domain-specific, so they can only be validated after the Action's stored domain is read. Pre-flight 10
gives the neutral `The Action domain is missing or unsupported.` only for a missing/unknown POST `domain`, and says
"never default to cold or EV based on a malformed body".

Question: for an intent body that fails a domain-independent check (missing top-level key, bad `declared_at`,
bad key) before resolution, which literal - the cold one (today's behaviour), the neutral domain literal, or a new
neutral literal? And may the domain-specific criteria/basis checks move inside the transaction after the 404 check
(a 422 for a malformed EV criteria list on an unknown Action ID would then become 404)?

## Q3 - K0 producer route and session-list watermark (readiness ruling 8) do not exist as named

Merged code: there is no `GET /api/sites/{site_code}/ev/scenarios`; the E5 list is
`GET /api/sites/{site_code}/ev/financials/scenarios` (`ev_scenarios_api.py:44`), whose `window` carries
`committed_watermark`. The EV session list `GET .../ev/sessions` (`ev_assessment_api.py:158`) returns
`window:{from,to,known_at}` only - no watermark - so "cross-checking the same selected EV session-list `window`
watermark" has nothing to compare. Confirm: use `/ev/financials/scenarios` `window.committed_watermark` as K0, and
cross-check against the session list's `window.known_at` (or drop the cross-check)?

## Q4 - "the selected accepted set at the same pin" (readiness ruling 6)

Two merged candidates: (a) the selected EV assessment head's `selected.evidence_ids`
(`EvReadService._snapshot`, P:2744), which `selected_provenance_on` filters by; (b) `accepted_on(c, snap)` (P:3128),
accepted evidence of the window at the evidence cutoff. E5's A6 used both (accepted set AND assessment-head
citations). Which is "the selected accepted set" - (b), with (a) not required, or both?

## Q5 - Scope of V1b's producer/walkthrough in this run (information, not a contradiction)

V1b's card includes `tools/w504_ev_work_cases.py` (non-test, W2 manifests and ingestion APIs) and
`tools/w504_ev_work_walkthrough.py` (`prepare|serve|attest|drop`). The cold equivalents are 272 + 895 lines. They
depend on Q3. Confirm they stay in V1b rather than a separate unit.
