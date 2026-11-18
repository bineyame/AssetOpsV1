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

## Round 2 (V1a service / V1b read build, 2026-10-24) - recorded, not decided

### Q6 - Ruling 27 "greatest accepted disposition" vs the merged pin's evidence cutoff
Ruling 27 computes the evidence cutoff as the greatest **accepted** `ingestion_disposition.decided_at <= command_now`
and says this "follows W5-02 cold `_ReadTx._pin`". Merged `_ReadTx._cold_ev`
(`backend/assetops_backend/work/adapters/postgres_work_read.py:281-283`) uses
`SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id=:t AND site_id=:s AND decided_at <= :k` -
no `decision = 'ACCEPTED'` filter, so a later REJECTED disposition moves the cutoff. `EvReadService._snapshot`
(`postgres_assessment_store.py:2681`) uses the same unfiltered `max(decided_at)` as its watermark. Not decided: the
V1 build uses the existing `selected_finding_pin` (unfiltered, shared with cold and W4 links) unchanged. Adding the
filter would change cold/W4 link pins too. Which is binding - the merged unfiltered cutoff (amend ruling 27's word
"accepted"), or an EV-only accepted-filtered cutoff (a second pin implementation)?

### Q7 - EV detail without an intent when the Finding is no longer selected at `known_at`
Ruling 27 pins the historical selection at the intent's `recorded_at`; with no intent there is no immutable cutoff,
so the pin is taken at the read `known_at` (coordinator brief). After any later EV recompute the Action's Finding
revision is no longer the selected head at `known_at`. Built: no intent -> 200 with `status` UNKNOWN, null Finding
href and `missing_lineage` provenance (the cold behaviour); with an intent any missing/mismatched recheck -> 409
`DOMAIN_INTENT_BASIS_CHANGED` (EV message). Confirm, or should the no-intent case pin at the Action's `recorded_at`
or refuse 409?

## Round 3 (V1b producer/walkthrough, 2026-10-24) - recorded, not decided

### Q8 - `ev-fault` has no fault-ended session or EV Finding (pre-flight 20, readiness 31, spec "V1 selection")
`config/scenarios/ev-fault.yaml` is "Fault before charging": FAULT 08:00, CLEAR 08:05, session 08:11-08:21
COMPLETED (`contract-fixtures/w2/ev/fault.json` assertions `outcome: COMPLETED`, `abort_at: null`). EV Findings are
written only for `qualified_fault_abort` sessions (`OBSERVED_ABORT` with a FAULT at the abort,
`analytics/ev.py:616-630`, `analytics/adapters/postgres_finding_store.py:728`). The fault-ended session with a
SUPPORTED Finding is `ev-interrupted` (OBSERVED_ABORT, fault 08:16). The producer keeps `POSITIVE_SCENARIO =
"ev-fault"` as ruled; `select_positive` would refuse it ("expected one SUPPORTED EV Finding on a fault-ended
selected session"). Which scenario is the positive replay?

### Q9 - The registered EV path cannot produce Site `EV-W504-DEPOT-{suffix}` or a shifted window
`scenarios/ev_parsing.py:179-189` pins `site_code` to `EV-LAB-001` (or `EV-LAB-002` for `ev-complete-lab-002`) and
the window to exactly `2026-10-06T08:00Z-09:00Z`; `sites/ev_lab.install_ev_lab` imports the fixed EV-LAB-001
fixture. The run setup, host publication and gateway admission all go through that parser. So the ruled shifted
`[D+08:00,D+09:00)` replay at the generated Site code is refused on merged code (proved DB-free:
`test_replay_is_blocked_on_merged_parser`), and ruling 31 authorizes no product change. Options: (a) a product
change admitting a producer-generated EV Site/window; (b) the producer bypasses the registered run/host/gateway path
and posts shifted envelopes straight to batch ingestion (a design decision, untested, needs gateway credentials and
v4 envelopes); (c) keep EV-LAB-001 at 2026-10-06 (18 days before today, inside W4's 30-day limit, but no longer than
~24 days from now) and drop the generated code/shift.

### Q10 - The registered EV publication runner exists only in test modules
`Chain._gateway` uses `gateway_process.GatewayProcess`, `fake_central.FakeCentral` (gateway/tests), `run_fixtures.
FakeScenarios/FakeSites`, `scenario_cache`, `test_s1_bindings_postgres.Clock`, `pg_harness`, and the ledger's
`test_decision_clock_override`. W5-02's cold walkthrough imported `backend/tests` in its child process; ruling 29
and the brief forbid that here. Even after Q9, a non-test producer needs its own gateway/central harness. Is a
tool-local copy authorized, or may the walkthrough child import those test helpers as the cold precedent did?

### Q11 - WR narrative
W4 requires a case `narrative` (1..4000, `work/service.py:175`); the spec gives the WR only title/activity/
outcome_note. Provisional: `WR_NARRATIVE_PENDING_RULING` = the activity literal, flagged in the manifest.

### Q12 - Short name `Depot`
The Site document and Site read have no short-name field (no `short_name` anywhere in `assetops_backend`). The
producer records `Depot` in the manifest only.
