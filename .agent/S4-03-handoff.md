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
- `revisions[]`: S4-01 `_summary` fields (`id`, `revision_no`, `recorded_at`, `transition`, `lifecycle`, `claim_level`, `support_changed`, `model_version`, `matcher_version`, `episode`, `candidate_minutes`, `basis_sha256`, `support_sha256`, `primary_assessment_revision_id`, `window_/interval_assessment_revision_ids`, `prior_window_/prior_interval_assessment_revision_ids`, `foundation_revision_ids`, `binding_set_revision_ids`, `cited_evidence_count`) plus `minutes{candidate,necessary,indeterminate}`, `previous_revision_id`, `is_selected`, `is_latest`, `cited_evidence{count,resolved,accepted_rows: ALL_RESOLVED|UNRESOLVED_PRESENT,note}` (accepted-row existence only; no lineage verdict in History, full lineage is the Evidence read; review F1), `times{recorded_at, analytic_completed_at, source_time{first,last}, received_at, accepted_at}`.
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

- `backend/tests/test_s4_finding_evidence_history_postgres.py`: all cases; every revision's Evidence walked in 7-record pages and every History in 2-row pages, compared field by field with `accepted_evidence`, `ingestion_disposition`, `analytic_run_evidence`, `finding_revision*`; F04 append pinning; F05; F06; F08 retry adds no revision; cross-Site (second Site code with another Site ID) and foreign-revision 404s; closed-gate 409 and pinned audit reads. Second test corrupts its own test DB (replica mode) to delete one cited accepted row and tamper one envelope: named `ACCEPTED_EVIDENCE` / `ENVELOPE_DIGEST`, totals unchanged, digest NOT_VERIFIED, no record link for the missing row, History row `accepted_rows: UNRESOLVED_PRESENT`; a separate envelope-only tamper test shows Evidence BROKEN/`ENVELOPE_DIGEST` while History stays `ALL_RESOLVED` with no lineage claim.
- `backend/tests/test_s4_finding_evidence_history_api.py` (no DB): 205-version page boundary (200 + 5, cursor 200, groups keep all IDs, pinned old revision selected, latest marked separately), one-revision `NONE`, 401/403/404/409/503 matrix including lineage-read failure as 503. The 205 revisions are a test-only in-memory store: the ordinary path would need 205 distinct S3 selections of one window, and the Postgres store returns a Finding's full ordered list so the paging under test is the service's own (also exercised over real rows in small pages).
- Non-vacuity: committed first, then (1) disabled the envelope digest check -> the broken-join test failed (`{...ACCEPTED_EVIDENCE} == {...ENVELOPE_DIGEST}` mismatch); (2) changed the store's accepted join to INNER -> failed `assert (65 == 66)`; both reverted with `git checkout --`.

### Checks run (actual results)

- Targeted: `test_s4_finding_evidence_history_postgres.py`, `test_s4_finding_read_postgres.py`, `test_s4_finding_store_postgres.py`: 11 passed (203 s). `test_s4_finding_evidence_history_api.py` + `test_s4_finding_api.py`: 22 passed.
- Full backend pytest (private `assetops_s403_test`): `3 failed, 1902 passed, 1 error in 831.78s`. All 4 are in `test_s4_finding_store_postgres.py` and every one is `FATAL: sorry, too many clients already`: another agent's suite held 82 of the server's 100 connections on `assetops_test` at the same time. Rerun of that file alone: `6 passed in 80.99s`. No assertion failure anywhere.
- `tools/check-all.ps1`: first run 8 of 9 PASS; Delivery checker fixtures failed at `test_delivery_next_work.cjs:358` (expected S4-03 `not_started`, actual `active`), caused by activation `2bb4f87`, not this phase. After the coordinator's fixture fix `9b065fb` landed on the branch, rerun on `62f1ce8`: **9 of 9 PASS**.

### Open risks / deviations

- Lineage checks run over the whole cited set per request (one LEFT-joined query, plus citation/input lookups); bounded by one revision's cited set (max 114 in the fixture). Not paged in SQL; offsets are stable because the set is immutable.
- `control_basis` is stated as "recorded only inside the run's configuration digest": no separate control revision ID exists in storage.
- History without `revision_id` while the gate is closed is 409 (fail-closed, same as the root); pinned is audit material.
- The S2 record link is offered while the Performance gate is closed (the Evidence inspector is not behind that gate); Dispatch links are withheld.
- `ASSESSMENT_CITATION` assumes every cited record is listed in some cited assessment's `evidence_ids`; true for all 30 fixture revisions.
- No Architect question raised.

### Next

Phase 2 (`I-finding-evidence-ui`): build the Evidence child view on `/sites/{code}/findings/{id}/evidence?revision_id=` over this API; page with `next_offset`; render `lineage.broken_records`/`set_breaks` with `lineage.words`; record links from `links.records`, Dispatch from `links.assessment_revisions`. Respect AC4 (`<MissingClaim>` for absent capabilities; mock ActionEvent/recommendation omitted by default and listed for G-04).

## Phase 2 - `I-finding-evidence-ui`

Implementer: Claude, 2026-10-13. This phase is UI only, plus one backend placeholder retirement. It adds no new read, no Finding writer and no registry or ledger edit.

### What landed (commits)

- `c4ea8f4`: the Evidence child view, the frame section switch, the client, the legacy-tab resolver, C6 `evidence_tab` retirement and tests.
- `9d6108b`: `.agent/S4-03-questions-1.md` (Q1-Q3, each with its fail-closed default built).
- `bfab6c8`: walkthrough and browser-evidence tool changes (made by the evidence subagent).
- `6dd7823`: a fix for the 390 px overflow (`.site-finding-evidence > * { min-width: 0 }`), plain duration words, and a hardened redirect test.

### Route and child-view structure (phase 3 plugs History in here)

- `frontend/src/shell/operatorSiteRoutes.ts:159-180` defines:
  - `FINDING_CHILD_VIEWS = ["evidence"]` and `FindingChildView`
  - `SITE_FINDING_VIEW_ROUTE_PATH = /sites/:siteId/findings/:findingId/:findingView`
  - `siteFindingViewHref(site, id, view, revisionId?)`
  - `siteEvidenceAcceptedRecordHref(site, evidenceId)`, which builds `/sites/{s}/evidence?view=analysis&record=<accepted id>`. The ledger inspector reads `record` as the exact evidence ID.
- `frontend/src/App.tsx:254`: both the root path and the child path render `SiteFindingFrame`.
- `frontend/src/shell/SiteAnalyticsFrames.tsx:285-395` (`SiteFindingFrame`):
  - It reads `findingView` and `revision_id`.
  - `FINDING_SECTION_LABELS` is at :295.
  - It builds the `FindingSections` links: Finding, then each child view, each keeping `revision_id`.
  - The view switch is at :360. An unknown view name gets a `not_found` panel and no read.
- What phase 3 needs to add:
  - `"history"` in `FINDING_CHILD_VIEWS` and `FINDING_SECTION_LABELS`
  - a branch at the switch
  - `getFindingHistory` on `FindingClient` (`frontend/src/sites/findingClient.ts:418`)
- `FindingSections` and `SiteFindingEvidence` are in `frontend/src/sites/SiteFindingEvidence.tsx` (:43, :107).
- The Evidence view's address state:
  - `revision_id`
  - `offset`: the record page, 50 per page (`EVIDENCE_PAGE_SIZE`)
  - `record`: the selected record (finding-evidence:2)
- Section links keep `revision_id` only.

### Behaviour (by AC)

- **Selection.**
  - An omitted version is labelled latest at read time, with a pin link (`[data-evidence-latest-at-read]`, `[data-evidence-pin]`).
  - An earlier version leads with its non-current notice (`[data-evidence-earlier-version]`).
  - A closed source leads with "Record only" (`[data-evidence-audit-only]`) and withholds Dispatch links.
  - An unknown or foreign version gets a 404 panel and the URL is kept. The latest version is offered as a link only and is never substituted.
- **Counts.**
  - Cited and input totals are shown separately (`[data-evidence-cited-total]`, `[data-evidence-input-total]`).
  - Sources are grouped by gateway, source and epoch. The registered source mode is shown as its exact recorded value.
  - Case-manifest notes appear when present.
- **Lineage.**
  - The positive sentence ("every cited record traces…") appears only when `lineage.status == COMPLETE`.
  - When BROKEN, the view lists `set_breaks` and `broken_records`. An unresolved row shows only the withheld sentence.
  - Link words come from the frontend `LINK_WORDS` map (`SiteFindingEvidence.tsx:69`), falling back to `lineage.words` (Q2: the backend's words use banned product vocabulary).
- **Links.**
  - The record inspector link appears only when `links.records[id]` exists.
  - A Dispatch link appears only when `links.assessment_revisions[id]` exists. An INTERVAL assessment links to `?day=&revision=`, a WINDOW assessment to `?day=`.
- **Legacy tab** (`/findings/{site}/{assessment}/evidence`).
  - `LegacyFindingEvidence` (`SiteFindingEvidence.tsx:690`, wired into `FindingDetail.tsx`) reads `finding-windows/{day}`.
  - With exactly one saved Finding it redirects (replace) to that Finding's Evidence view. With several it offers a choice. With none, or when the read is refused, it says so in plain words.
  - The old per-segment `FindingEvidence` list is removed (Q1).
- **C6.** The `evidence_tab` key is removed from `finding_read.UNAVAILABLE`. Two placeholders remain for phase 3 to retire: `history_tab`, and the S4-01 page's history "Not yet available" text (`SiteFinding.tsx` WhereToLook, baselined).
- **AC4.** No new absent-capability phrase and no `<MissingClaim>` were added. The missing-claim scan is unchanged: 1 tagged, 16 baselined.

### G-04 list (mock content omitted, not rendered)

- Mock `finding-evidence` has no ActionEvent or recommendation element (index.html:715-717), so nothing was omitted for that reason.
- From the mock tab row (index.html:1106), "Alternatives" and "Recommendation" are not rendered in the app's Finding sections. "History" is phase 3.
- The mock `finding-evidence:1` bundle summary rows are illustrative and are not rendered as rows:
  - Generator state/power GEN-001
  - Battery SOC BMS-001, "delayed report received 16:00"
  - PCS capability PCS-001, "14:50 missing"
  - PV/load INV-001/MTR-001

  The app shows the actual cited records instead. It has no device-code summary and no coverage/use column.

### Evidence

- **Tools.**
  - `tools/s4_finding_walkthrough.py` gains:
    - `--db`/`--work` (env `ASSETOPS_S4_WALK_DB`/`_WORK`; protected names are refused)
    - Evidence links
    - `close-gate`/`open-gate`
    - `drop`
  - `tools/s4-finding-evidence.mjs` gains:
    - env `ASSETOPS_S4_WALK_WORK` and `ASSETOPS_CDP_PORT`
    - `ASSETOPS_S4_EVIDENCE_SUITE=all|finding|evidence|closed|broken`
- **Setup for the final run on `6dd7823`.**
  - Private DB `assetops_s403p2_walk`, a template copy of `assetops_s4cases`.
  - API on 8898, Vite on 5398.
  - Output in `%TEMP%\s403p2-evidence-r2\`: PNGs (`-desktop` = 1440, `-narrow` = 390) and `run-all.log`, `run-closed.log`, `run-broken.log`.
  - Afterwards the DB and work folder were dropped and the PIDs stopped.
- **all: 68/68 PASS.**
  - F01-gateway `624f2558`: 102 cited and 263 input, both equal to the API. The first row, `42f8352e`, equals the API.
  - Page 2 (offset 50): 50 rows. The first row, `79b569b0`, equals the API.
  - F04 `d176a8f0` v1, pinned: the earlier-version notice leads and the total is 42 (v2 is 78).
  - Unknown version: refused with 404 and the URL is unchanged.
  - Keyboard: Tab×22 then Enter selects a record (`record=` appears in the URL). Reload keeps the URL and the record. Tab×72 then Enter on Next goes to `offset=50`.
  - The mock `#/finding-evidence` was captured at both widths.
- **closed: 4/4 PASS.** The unpinned read returns 409. Pinned F04 v1 leads with "Record only", has 0 Dispatch links, and its total is 42.
- **broken: 6/6 PASS.** This used a deliberate tamper of the private DB only: one envelope of F03 `3a4affdc` was altered. Lineage is BROKEN, the broken records `[0430330d]` equal the API, and `ENVELOPE_DIGEST` is named.
- **Overflow.** Measured element counts were 48, 85 and 90, all non-empty. Width was 390 vs 390 at 390 px and 1425 vs 1425 at 1440 px. Round 1 had 693 vs 390 at 390 px, which `6dd7823` fixed.
- **Legacy tab not captured.** KOBO-001's legacy endpoints return `AWAITING_EVIDENCE_MIGRATION`, so no assessment ID exists to open. Unit tests cover it.
- **Layout evidence: not run.**
  - `tools/layout-evidence.mjs` creates Lab runs on its default path (lines 716 and 3121).
  - It defaults to site MG-001, which is absent from this store.
  - It never visits `/sites/<site>/findings/<id>/evidence`.

  For this path, the S4 evidence script's overflow measurements above are the layout evidence.

### Checks (actual)

- `siteFindingEvidence.test.tsx`: 21 passed.
- Full frontend vitest: 59 files, 1412 passed.
- `tsc --noEmit`: clean.
- `npm run build`: exit 0, with a chunk-size warning only.
- Backend `test_s4_finding_evidence_history_api.py` + `test_s4_finding_api.py`: 22 passed.
- `tools/check-all.ps1`: all 9 guards passed.
- Non-vacuity proofs, on committed code, each reverted with `git checkout --`:
  - Forcing the COMPLETE branch makes "names broken links… withholds the positive lineage claim" fail.
  - `dispatchable = true` makes "closed source… no Dispatch link" fail.

### Open risks

- Q1-Q3 are still open; their defaults are built.
- The legacy redirect matches by day, not by exact assessment.
- The WINDOW assessment row shows 0 cited records when segments cite only interval revisions. That is accurate data but may read oddly.
- The narrow pinned-record screenshot hits the script's 7000 px height cap. The image is cut off; the page is not clipped.
- Phase 1 carry C1 (`ASSESSMENT_CITATION`) is unchanged.

## Phase 2 fix round (review RETURN; Architect Q1, Q2 overruled, Q3 ratified)

Commits: `bc9a602` (backend words, L4 tool), `3dc9806` (UI, tests, catalogue). Implementer: Claude, 2026-10-13. No server started; no browser evidence rerun (the Evidence view's layout changed by one table and two lines; 1440/390 remains for the owner walkthrough).

- **Q1 + M1.** `LegacyFindingEvidence` (`SiteFindingEvidence.tsx`, end of file) no longer redirects. It reads every UTC day the assessed window touches (`daysTouched`), keeps Findings with `episode_start < window.end && window.start < episode_end` (`overlapsWindow`), and lists them as links under "Findings recorded for this day", worded as a day-level aid. No-result and unreadable states and the records link are kept.
- **Q2.** `finding_read.BROKEN_WORDS`, `LINEAGE_STATEMENT` and the unresolved row's `withheld` now use the plain meanings; codes unchanged. UI: `LinkText` shows `LINK_WORDS` for a known code and "A record link could not be checked" with the code only in `[data-evidence-technical-detail]` for an unknown one; backend prose is never rendered. Parity: `frontend/src/sites/__tests__/findingLinkWordsParity.test.ts` reads `finding_read.py` as text (`src/test/rawSource.d.ts` types the `?raw` import) and requires equal keys and wording; backend `test_broken_lineage_words_are_product_safe_at_source` bans engineering words.
- **M2.** `data-evidence-lifecycle` line from `revision.lifecycle` using `LIFECYCLE_WORDS`. Non-SUPPORTED states lead the panel; SUPPORTED reads after the version lines (so "Record only" still leads on a closed source).
- **M3.** `sourceModeWords` (`findingWords.ts`) gives "Demonstration data" / "Live data"; the exact mode stays in `data-source-mode`. Both exemptions removed; column is "Kind of data".
- **L1** dash for unreadable avoidable time. **L2** "(stored message missing)" for ENVELOPE. **L4** `prepare` writes `.s4-walkthrough-work`; `drop` removes a `--work` folder only if it holds it.
- **M4.** `InputsByMeasurement` (Bundle): Input and Source and Records counted from the page's resolved records' `role` and source, labelled "on this page". Coverage and Use are two `<MissingClaim>` elements: gaps `G-finding-evidence-coverage` and `G-finding-evidence-use` (registry `mock_gaps`, `gapCatalogue.ts`, ledger `finding-evidence.gap_ids`), placements `finding-evidence.bundle.coverage` and `.use`. The scan reports 3 tagged, 16 baselined. Alternatives and Recommendation tabs stay omitted for G-04.

Non-vacuity (mutation, then `git checkout --`): `overlapsWindow` returning true fails the two exclusion tests; hiding the lifecycle line fails the lifecycle test; changing a frontend word fails parity (2 tests); changing a backend word to "envelope" fails the backend test.

Results: vitest 60 files, 1422 passed; tsc 0; build 0; `test_s4_finding_api.py` + `test_s4_finding_evidence_history_api.py` 23 passed; `test_s4_finding_evidence_history_postgres.py` 3 passed on `assetops_test` (run before the commit; no backend code changed after); `tools/check-all.ps1` 9 of 9 pass.

Open: the Postgres test is not rerun after the final commit (only test and doc files changed since). The envelope/row comparison against Postgres owed by the re-reviewer is unchanged. G-04 list gains nothing new.
