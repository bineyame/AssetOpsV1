# S4-03 handoff

Task: `tasks/S4-03-finding-evidence-history.md` (binding). Branch `task/S4-03-finding-evidence-history`.
Plan review carries: `.agent/S4-03-plan-review.md` (C1 registry "knowledge cutoff" rewording and C2 ledger task fields are closeout/coordinator items, untouched here).

## Phase 1 - `I-finding-evidence-read` + `I-finding-history-read` (backend only)

Implementer: Claude, 2026-10-13. No UI, no new Finding writer, no `knowledge_at` replay, no registry/ledger edits.

### What landed

- Commit `6ac76f3` - two child routes of the canonical Finding root, read-only store queries, service methods, tests.
- Route choice: **child routes under the same root** (not more query params on the root GET), so the root body stays the S4-01 contract and each child pages its own set. Both reuse the root's `open_scope`, `source_gate`, `closed` and `served` exactly.
- The root read was refactored only to share `_choose`, `_relations`, `_root` (no response change; S4-01 tests pass).

### API shapes

`GET /api/sites/{site_code}/findings/{finding_id}/evidence?revision_id=&offset=0&limit=200` (limit 1..500)

- `selection`: `revision_id`, `revision_no`, `selected_by` (`LATEST_RECORDED` | `EXACT_REVISION_ID`), `latest_revision_id`, `is_latest`, `replay` (no knowledge_at statement).
- `revision`: the S4-01 summary fields plus `claim_level`, `minutes{candidate,necessary,indeterminate}`, `analytic_run_id`, `window_assessment_revision_id`, `cited_evidence_sha256`, `input_evidence_sha256`, `limitations`.
- `counts`: `cited_total`, `cited_resolved`, `cited_unresolved`, `cited_with_broken_lineage`, `input_distinct_total` (distinct `analytic_run_evidence` over the revision's cited runs), `input_by_run[{analytic_run_id,input_evidence_count,input_sha256}]`, `statement` (cited vs input).
- `lineage`: `status` (`COMPLETE` | `BROKEN`, over the **whole** cited set, not the page), `cited_set_digest{status: VERIFIED|MISMATCH|NOT_VERIFIED, recorded, recomputed}`, `set_breaks[]` (`CITED_SET_DIGEST`, `ANALYTIC_RUN`), `broken_records[{evidence_id, links[]}]`, `statement`, `words` (plain sentence per link name).
  Link names: `ACCEPTED_EVIDENCE`, `BATCH`, `ACCEPTANCE_DISPOSITION`, `ENVELOPE`, `ENVELOPE_DIGEST`, `FOUNDATION_REVISION`, `BINDING_SET_REVISION`, `BINDING_REVISION`, `ASSESSMENT_CITATION`, `RUN_INPUT`, `ANALYTIC_RUN`, `CITED_SET_DIGEST`.
- `assessments[]`: `assessment_revision_id`, `scope` (WINDOW/INTERVAL), `is_primary`, `assessment_key`, `assessment_revision_no`, `claim_level`, `window{start,end}`, `model_version`, `analytic_run_id`, `run_resolved`, `cohort{status,sha256}`, `basis{foundation_revision_ids, binding_set_revision_ids, configuration_sha256, control_basis}`, `cited_records`.
- `records[]` (page; order `source_time, evidence_id`): `evidence_id`, `resolved`, `lineage_status` (RESOLVED/BROKEN), `broken_links[]`, `role`, `value`, `unit`, `quality`, `unavailable_reason`, `source_time`, `interval{start,end}`, `published_at`, `received_at`, `accepted_at`, `disposition`, `source{gateway_id, source_id, sequence_epoch, sequence, device_id, signal_id, asset_id, source_mode}`, `batch{batch_id, external_batch_id, resolved}`, `message_id`, `envelope{sha256, digest_verified}`, `accepted_as{foundation_revision_id, foundation_version, foundation_resolved, binding_set_revision_id, binding_set_version, binding_set_resolved, binding_revision_id, binding_resolved, conversion_kind, configuration_outdated}`, `used_by{assessment_revision_ids, run_ids}`. An unresolved accepted row returns only `evidence_id`, `resolved:false`, `broken_links`, `withheld`.
- `page`: `offset`, `limit`, `total`, `returned`, `next_offset` (null on the last page), `order`.
- `provenance`: `statement`, `cited_evidence_by_source[]`, `case_annotations` (only when `ASSETOPS_FINDING_CASES_MANIFEST` is configured; the only source of F-case/gateway-sealed labels).
- `currentness`: null when the source is open; `{state: SOURCE_CLOSED}` for a pinned read while closed.
- `links`: `canonical`, `selected_revision`, `evidence`, `history` (frontend shapes `/sites/{code}/findings/{id}/evidence|history?revision_id=` - the C5 shape for phases 2/3), `api_finding`, `api_evidence`, `api_history`, `performance{status,note}`, `records{evidence_id: /api/sites/{code}/evidence/records/{evidence_id}}` (resolved records on this page only; exact evidence ID, never message ID - avoids 409 RECORD_AMBIGUOUS), `assessment_revisions{id: /api/sites/{code}/performance/dispatch/revisions/{id}}` (empty while closed), `api_next_page`.
- Also `site_code`, `access_basis`, `source_gate`, `audit_only` (non-null when the gate is closed), `finding`, `unavailable`.

`GET /api/sites/{site_code}/findings/{finding_id}/history?revision_id=&after_revision_no=0&limit=200` (limit 1..500)

- `selection`: as above plus `selected_note` (latest at read time vs pinned) and `latest_revision_no`. Omitted `revision_id` selects the latest at read time.
- `revisions[]`: S4-01 `_summary` fields (`id`, `revision_no`, `recorded_at`, `transition`, `lifecycle`, `claim_level`, `support_changed`, `model_version`, `matcher_version`, `episode`, `candidate_minutes`, `basis_sha256`, `support_sha256`, `primary_assessment_revision_id`, `window_/interval_assessment_revision_ids`, `prior_window_/prior_interval_assessment_revision_ids`, `foundation_revision_ids`, `binding_set_revision_ids`, `cited_evidence_count`) plus `minutes{candidate,necessary,indeterminate}`, `previous_revision_id`, `is_selected`, `is_latest`, `cited_evidence{count,resolved,lineage}`, `times{recorded_at, analytic_completed_at, source_time{first,last}, received_at, accepted_at}`.
- `page`: `after_revision_no`, `limit`, `total`, `returned`, `next_after_revision_no`. `earlier_versions`: `NONE` | `PRESENT`. `revision_groups` (all revisions; BASIS_REFRESHED grouping hint, IDs kept). `state{lifecycle, latest_transition}`, `relations` (same as root), `time_kinds`, `statement`, `unavailable{recommendation}`.
- `links`: as above plus `revisions{id: {finding, evidence, api_evidence}}` for the page, `api_next_page`.

Refusals (both routes): 401 `UNAUTHENTICATED`, 403 `SITE_SCOPE_FORBIDDEN` (access seam), 404 unknown Site / unknown or cross-Site root / revision of another Finding, 422 malformed UUID, 409 `PERFORMANCE_CUTOVER_CLOSED` for an unpinned read while closed, 503 `FINDING_STORE_UNAVAILABLE` for store/lineage failure or no database. A broken lineage join is a 200 `lineage.status = BROKEN` with named links, never 503 and never an empty bundle.

### Anchors

- `backend/assetops_backend/finding_api.py:142-209` (child routes; `child_links` :147, `audit_only` :157, evidence :164, history :188).
- `backend/assetops_backend/analytics/finding_read.py:59-196` (constants, `_choose`, `_relations`, `_root`, `_record_breaks` :120, `_record` :143); `evidence()` :448, `history()` :552.
- `backend/assetops_backend/analytics/adapters/postgres_finding_store.py:306-395` (`revision_evidence` :308 - LEFT joins, envelope digest recomputed in SQL with `sha256(convert_to(text,'UTF8'))`; `revision_times` :373).
- Frontend phase 2/3 start points (untouched): `frontend/src/sites/findingClient.ts`, `SiteFinding.tsx`, `frontend/src/shell/operatorSiteRoutes.ts:158-170` (legacy tabs not repurposed). The root's `unavailable.evidence_tab/history_tab` strings (`finding_read.py:49-50`) still say S4-03; phase 2/3 should retire them when the child views land.

### Fixtures and how to regenerate

- Tests run the committed `backend/conversions/s4-finding-cases-v1.json` through the S4-01 `CaseRunner` (ingestion, S3 worker, matcher); no Finding rows are inserted. Set `ASSETOPS_TEST_DATABASE_URL` to a private `*_test` database (I used `assetops_s403_test`, now dropped).
- F01-gateway (ordinary gateway-sealed path) is environment-bound: compared on a private `pg_dump` copy of `assetops_s4cases` against the run artifact `%LOCALAPPDATA%/AssetOps/s4-finding-cases/s4-finding-cases-{run,manifest}.json` (produced 2026-10-12). Regenerate with `tools/s4_finding_cases.py run --work <scratch>` per `.agent/S4-01-phase-1-fix-handoff.md`.
- Result on that copy (11 Findings, 30 revisions, every revision read in 40-record pages): every cited set equals `finding_revision_evidence`, every lineage COMPLETE, every cited digest VERIFIED, record-route envelope SHA matches; 0 mismatches. F01-gateway Finding `624f2558...` r1: 102 cited of 263 run inputs, all labelled F01-gateway, epoch `s4-gateway-epoch-1`; fixture cases use `s4-fixture-epoch-1`. Every row's `source_mode` is `SIMULATED` (the gateway's registered mode), so "ordinary gateway-sealed vs fault fixture" is distinguishable only via epoch and the case manifest annotation - not from a central column (S4-01 `PROVENANCE_STATEMENT`).
- F04 `d176a8f0` r1 42 cited / r2 78 cited (late IDs only on r2); F05 `c727093a` OPENED, UNCONFIRMED, NO_LONGER_SUPPORTED; F06 merge/split chains readable on old and canonical IDs; F08 has no Finding (window state NOT_DETERMINABLE).

### Tests added

- `backend/tests/test_s4_finding_evidence_history_postgres.py`: all cases; every revision's Evidence walked in 7-record pages and every History in 2-row pages, compared field by field with `accepted_evidence`, `ingestion_disposition`, `analytic_run_evidence`, `finding_revision*`; F04 append pinning; F05; F06; F08 retry adds no revision; cross-Site (second Site code with another Site ID) and foreign-revision 404s; closed-gate 409 and pinned audit reads. Second test corrupts its own test DB (replica mode) to delete one cited accepted row and tamper one envelope: named `ACCEPTED_EVIDENCE` / `ENVELOPE_DIGEST`, totals unchanged, digest NOT_VERIFIED, no record link for the missing row, History row `lineage: BROKEN`.
- `backend/tests/test_s4_finding_evidence_history_api.py` (no DB): 205-version page boundary (200 + 5, cursor 200, groups keep all IDs, pinned old revision selected, latest marked separately), one-revision `NONE`, 401/403/404/409/503 matrix including lineage-read failure as 503. The 205 revisions are a test-only in-memory store: the ordinary path would need 205 distinct S3 selections of one window, and the Postgres store returns a Finding's full ordered list so the paging under test is the service's own (also exercised over real rows in small pages).
- Non-vacuity: committed first, then (1) disabled the envelope digest check -> the broken-join test failed (`{...ACCEPTED_EVIDENCE} == {...ENVELOPE_DIGEST}` mismatch); (2) changed the store's accepted join to INNER -> failed `assert (65 == 66)`; both reverted with `git checkout --`.

### Checks run (actual results)

- Targeted: `test_s4_finding_evidence_history_postgres.py`, `test_s4_finding_read_postgres.py`, `test_s4_finding_store_postgres.py`: 11 passed (203 s). `test_s4_finding_evidence_history_api.py` + `test_s4_finding_api.py`: 22 passed.
- Full backend pytest: see the Phase 1 results line below.
- `tools/check-all.ps1`: 8 of 9 PASS. **FAIL: Delivery checker fixtures** - `test_delivery_next_work.cjs:358` asserts `S4-03` packet status `not_started`, actual `active`. Caused by the activation commit `2bb4f87` (`Status: active`), not by this phase (no task/registry/fixture file changed here). Left for the coordinator/Planner: the fixture's "real packets are not_started" expectation needs S4-03 removed or updated; I did not loosen it.

### Open risks / deviations

- Lineage checks run over the whole cited set per request (one LEFT-joined query, plus citation/input lookups); bounded by one revision's cited set (max 114 in the fixture). Not paged in SQL; offsets are stable because the set is immutable.
- `control_basis` is stated as "recorded only inside the run's configuration digest": no separate control revision ID exists in storage.
- History without `revision_id` while the gate is closed is 409 (fail-closed, same as the root); pinned is audit material.
- The S2 record link is offered while the Performance gate is closed (the Evidence inspector is not behind that gate); Dispatch links are withheld.
- `ASSESSMENT_CITATION` assumes every cited record is listed in some cited assessment's `evidence_ids`; true for all 30 fixture revisions.
- No Architect question raised.

### Next

Phase 2 (`I-finding-evidence-ui`): build the Evidence child view on `/sites/{code}/findings/{id}/evidence?revision_id=` over this API; page with `next_offset`; render `lineage.broken_records`/`set_breaks` with `lineage.words`; record links from `links.records`, Dispatch from `links.assessment_revisions`. Respect AC4 (`<MissingClaim>` for absent capabilities; mock ActionEvent/recommendation omitted by default and listed for G-04).
