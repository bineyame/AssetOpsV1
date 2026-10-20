# W2-07 phase handoff (run 1, 2026-10-20)

Branch `task/W2-07-ev-site-evidence-money`, worktree `AssetOpsV1-review5`. Private DB `w207a_test` (dropped at end of
run). Stopped after spec commit 1: commit 2 is blocked on pending ruling R2 (`.agent/W2-07-pending-rulings.md`).

## Landed (commit 1)

- `backend/migrations/versions/0026_w2_ev_money.py`: the spec's literal 0026 body (key/unit CHECK widening, EV-only
  positive CHECK, five scoped append-only tables, tariff key trigger, trigger-only work via `ev_consequence_enqueue`
  with `ON CONFLICT (tenant_id,site_id,window_start,window_end,dirty_basis_sha256) DO NOTHING`, backfill, guarded
  downgrade) plus a leading catalog assertion that the two 0010 CHECK names exist.
- `financials/assumptions.py`: `ASSUMPTION_KEYS` gains `ev_gross_tariff_per_kwh`; `EV_TARIFF_KEY`, `UNITS`,
  `unit_for`, EV-only `VALUE_NOT_POSITIVE` and active-ISO-4217 `CURRENCY_NOT_ISO` (R4). Diesel digest/unit unchanged.
  `postgres_assumption_store.py` and `assumption_read.py` use `UNITS[key]`.
- Rule 8 (`tools/checks/configuration-persistence.ps1`): `$evConsequenceTables` (revision, session, evidence,
  work_attempt) in `$consequenceTables`, insert-only per table, `ev_consequence_work` runtime-forbidden, 0026
  migration-text arbiter check, required EV probe names. Probes in `tools/writer_guard_probes.py`
  (literal `ev ...` negatives and `controls ev ...`; rule 8 matches names textually).
- Tests: `backend/tests/test_w207_ev_money_postgres.py` (named proofs `test_0026_follows_installed_0025_and_
  preserves_diesel`, `test_0026_trigger_only_work_and_exact_conflict_constraint`, plus
  `test_0026_scoped_constraints_state_arithmetic_and_append_only`). Head literals moved to `0026_w2_ev_money` in 11
  existing test files (head assertions only).

## Evidence (commit 1, `601456bc` + `a471f3f4`)

- `test_w207_ev_money_postgres.py` 3 passed. Adjacent: 14 head/assumption/migration files 214 passed + 1 fixed
  (`test_w204_cold_migration.py` snapshot now expects the 0010 diesel-only checks below 0026: `below_0026`), then
  `test_w204_cold_migration.py` + `test_w206_ev_store_postgres.py` + `test_w206_ev_reads_postgres.py` 44 passed.
- Rule-8 EV probes (`tools/writer_guard_probes.py --seam`, 33 EV names): 28 CAUGHT, 5 ALLOWED, tree restored.
- `tools/check-all.ps1`: all 10 guards passed. Full backend/host suites not run (by brief).

## Commit 2 anchors (after R2/R5/R6 rulings)

- Pure module (new) `financials/ev_money.py`: price state table from "Commits 2-3" + reconciliation table; SHA row
  forms from "Use exact SHA row forms" (canonicalization = W2-06 rule, `analytics/ev.py` helpers such as `ev.plain`).
- Store: add `ev_unit`/`ev_record_failure`/`ev_pending_work`/`ev_claim_site` to
  `financials/adapters/postgres_consequence_store.py`, mirroring the cold pattern at `:513-659` and `ColdUnit`
  `:666-823` (advisory work lock, REPEATABLE READ, check basis before `revision_no`, attempt insert like
  `_cold_attempt`; no `consequence_revision_ids` column on the EV attempt table). Runner mirrors
  `financials/cold_recompute.py` (`retry_due_at` from `financials/recompute.py`).
- Enable the "inserts seen" vacuity check for `$evConsequenceTables` in rule 8 (cold precedent
  `configuration-persistence.ps1` `coldConsequenceInsertsSeen`) and add `ev ... owner insert unseen` probes.
- Inputs: exact selected `ev-session/1` assessment with both bounds equal (reconciliation "Commits 2-3"); reuse
  `EvReadService` caller-connection reads (`analytics/ev_reads.py`), S4-05 link rows as `ColdUnit.basis` does.
- Replay fixtures: `test_w205b_ev_replay_postgres.py:chain`, `test_w206_ev_store_postgres.py:run_worker`; the
  chain test recreates the module DB, so keep chain tests after `site` tests in a module.

## Open risks

- R2 decides whether any replay case can be ESTIMATED. R1: source-gate trigger is inert for ordinary batches.
- Rule-8 probes run against a committed tree only (`tools/writer_guard_probes.py` refuses a dirty `backend/`).

## Run 2 (2026-10-20): stopped on pending ruling R7

- Landed `7cbe440c`: q1 R3 (`TestMigration0026::test_r3_store_publishes_ev_tariff_and_public_post_stays_401`:
  store publish under SYSTEM_PUBLISHER/SYSTEM_FIXTURE returns ID/`recorded_at`; unauthenticated POST 401, no new
  revision) and q1 R4 (`test_r4_ev_currency_and_value_validation_is_ev_only`: KES ok, ABC/0/-1 EV refused, diesel
  ABC/0 still valid). No product code changed (R4 validation was already in commit 1). Both tests pass.
- R1 not applied: its premise fails (`.agent/W2-07-pending-rulings.md` R7, with empirical failing trial). Commits
  2-3 not started. Resume: apply the R7 ruling to 0026 + the trigger test, then build commit 2 from the anchors above.
- Private DB `w207b_test` dropped at end of run.

## Run 3 (2026-10-20): q2 R7 landed; stopped at context budget before commit 2

- Landed `69ea6aee` (q2 R7): `0026_w2_ev_money.py` `ev_consequence_on_accepted()` replaced by the literal R7 body
  (immediate link trigger and its body unchanged). `test_0026_trigger_only_work_and_exact_conflict_constraint`
  splits the late delivery by wrapping `PostgresEvidenceLedger.decide_chunk` (monkeypatch; first call per batch
  snapshots work + link count), then asserts the R7 literal set: pre-decide work == after_run, link==1, gate
  disjoint; post == after_run | late ACCEPTED_EV | gate; one row per gate hash; double re-enqueue unchanged.
- Linked non-EV batch: the registered late phase delivers exactly one (EV) batch, so the test uses the first
  upload's committed linked batches with zero qualifying EV rows (work stayed empty across that upload); asserts
  link==1 and their SOURCE_GATE hashes disjoint from final work. No later linked non-EV batch is reachable through
  the registered fixture without a new publication path (noted, not decided).
- Unlinked EV acceptance: helper `unpublished_ev_upload` re-seals one late EV envelope (new sequence/message_id and
  event_id or value) as an unpublished upload via `BatchIngestionService` + the same ledger; runs last (after
  backfill) because it makes the Site source MIXED; asserts ACCEPTED_EV only, no SOURCE_GATE, no link.
- Non-vacuity: removing the R7 `IF EXISTS ... SOURCE_GATE` block fails the test (missing gate rows); reverted.
- Resume: spec commit 2 from the "Commit 2 anchors" above plus q1 R2/R5/R6 and the reconciliation's
  "Commits 2-3" (exact-bounds selection). Commit 3 after. Private DB `w207c_test` dropped at end of run.
- Evidence (`69ea6aee`): `test_w207_ev_money_postgres.py` 5 passed; adjacent `test_w206_ev_store_postgres.py` +
  `test_w205b_ev_replay_postgres.py` + `test_w204_cold_migration.py` 37 passed (12m13s); `tools/check-all.ps1`
  all 10 guards passed. Full backend/host suites not run (by brief).

## Run 4 (2026-10-20): stopped on pending ruling R8 before commit 2 code

- No product code changed. Commit 2 is blocked on `.agent/W2-07-pending-rulings.md` R8: a stored
  `WITHHELD/PENDING_RECOMPUTE` revision strands the window (no re-enqueue after an idempotent W2-06 job; literal basis
  SHA collides with the later settled derivation). C1-C5 there are the implementer's readings for the same commit.
- Commit 2 build plan (unchanged by R8 except the pending branch): `financials/ev_money.py` pure (R5 precedence incl.
  read-only HISTORICAL/STALE rows, R6 composition, per-interval tariff coverage -> TARIFF_MISSING/PRICE_GAP, SHA forms
  build spec `:77` with `fuel_cost.canonical_json`); store `ev_unit` (REPEATABLE READ + `pg_advisory_xact_lock(
  hashtextextended('ev_consequence:'||work_id,0))`, reuse `EvReadService._snapshot(c,t,s,code,ws,we,None)` at
  `postgres_assessment_store.py:2102` for exact selection/pending, sessions from `result.session_revision_ids`,
  SUPPORT `ev_meter_interval` rows + `accepted_evidence.envelope_sha256`, current assignments `recorded_to IS NULL`
  joined to revision value/currency/unit/recorded_at), `ev_record_failure`, `ev_pending_work` (order `created_at,id`;
  EV work column is `created_at`, not `enqueued_at`), `ev_claim_site`; attempt/revision times via `clock_timestamp()`
  in SQL (0026 has no defaults on `started_at/finished_at/recorded_at`). Runner `financials/ev_recompute.py`
  mirroring `cold_recompute.py`. Rule 8 `evConsequenceInsertsSeen` + `ev ... owner insert unseen` probes.
- Tests: chain fixture recreates the DB per case (~20 s each); six-case vector test parametrized after the `site`
  tests. Tariff fixture valid `[2026-10-06T08:00Z,09:00Z)`, `0.27775 KES`, idempotency `w207-golden-tariff-1`.
- Commit 3 anchors (selected reads): `EvReadService` (`postgres_assessment_store.py:2075`; `_read` `:2092`,
  `_snapshot` `:2102`, `_envelope` `:2184`, `_status` `:2223`, `_page` `:2320`), pure helpers
  `analytics/ev_reads.py` (cursor `encode_cursor/decode_cursor/check_cursor`, notes), W2-06 router for error
  mapping; build-spec "Commits 2–3" reconciliation (`:487-530`) and "Commits 3–5" (`:531-549`) for shapes/codes.
- No private DB was created this run.

## Run 5 (2026-10-20): spec commit 2 landed (q1 R2/R5/R6, q2, q3 R8 + C1-C5)

- Landed `94c1a2f2` + `4f34e3e2` + `1ce20550` (snapshot injection fix; line numbers below shift by ~+5 in the store). Pure `financials/ev_money.py` (`derive` :200, `conflicts` :162, `select_tariff`
  :184, line-77 forms `technical_rows` :126 / `technical_input_sha256` :144 / `consequence_basis_sha256` :149 /
  `overlap_group` :156). Store `postgres_consequence_store.py`: `ev_unit` :659, `ev_record_failure` :669,
  `ev_pending_work` :685 (`created_at,id`), `ev_claim_site` :702, `ev_rows` :727, `_ev_attempt` :924, `EvUnit` :937
  (`pending` :956 = R8 literal predicate; `basis` :964 calls the injected `ev_snapshot` =
  `analytics.composition.build_ev_selected_snapshot` (`EvReadService._snapshot(c,t,s,"",lo,hi,None)`; rule 8 bans
  a direct analytics-adapter import);
  `append` :1009 window lock, basis replay before `revision_no`). Runner `financials/ev_recompute.py`
  (`EvConsequenceWorker`); composition `build_ev_consequence_store/_worker`. Rule 8 `evConsequenceInsertsSeen` +
  four `ev <table> owner insert unseen` probes (required by name).
- Readings applied (not new rulings): line-77 `source_class` = selected stored `result.source_provenance.class`,
  `source_gate` = C5 classified class; tariff fields enter the basis only when ESTIMATED; links (session/evidence)
  only for ESTIMATED (C2 "priced"); WITHHELD/INCOMPLETE quantity null; UNPRICED tariff rows keep eligible kWh.
  Contradiction = CONTRADICTORY session, EXCLUDED `METER_OVERLAP`, one evidence ID under two sessions, or
  overlapping SUPPORT intervals on one connector. No exact selection / no session -> empty SUCCEEDED attempt.
- The replay's selected EV window is `[08:00, 09:05)` (not 09:00); tests read it via `ev_window` (:658). The golden
  tariff `[08:00, 09:00)` covers every eligible interval. R8 test inserts/UPDATEs a `recompute_job` row directly and
  calls `ev_consequence_enqueue` for the no-basis-change dirtiness event (existing test precedent).
- Commit 3 anchors: reads in `EvReadService` (`postgres_assessment_store.py:2075`, `_read` :2092, `_snapshot` :2102,
  `_envelope` :2184, `_sessions` :2236) unchanged by commit 2. Current consequence for a read: recompute the basis
  with `EvUnit.basis` logic + `ev_money.derive` on the read connection (both SELECT-only/pure) and select the stored
  revision whose `basis_sha256` matches; none -> STALE_BASIS read guard. Do not use "highest revision_no": a basis
  replay (R8) may make an older revision current again. Pending/historical mask via `_snapshot` state.
  Extend `test_pending_retry_settles_without_new_assessment_revision` (:787) with the five-read null current
  amount + pending copy (deferred: the reads do not exist in commit 2).
- Evidence (`1ce20550`): `test_w207_ev_money.py` 2 passed; `test_w207_ev_money_postgres.py` 12 passed (six vectors
  exact + R8 regression); adjacent run on `4f34e3e2` (w207 x2, w206 store, w205b replay, w204 cold migration/worker,
  s4 consequence store/recompute) 81 passed in 17m37s; after the fix w207 x2 + w204 cold worker 18 passed;
  `tools/check-all.ps1` all 10 guards passed; probes `ev <4 tables> owner insert unseen` CAUGHT, control ALLOWED.
  Full suites not run (by brief). Private DB `w207e_test` dropped.

## Run 6 (2026-10-20): spec commit 3 landed (five reads, q4 selector)

- Landed `7fb66e17`. API `backend/assetops_backend/ev_site_api.py::build_ev_site_router` (mounted in `main.py`
  after the W2-06 router) reuses `ev_assessment_api.ev_gate` (W2-06 gate/refusals/messages, refactored out of
  `build_ev_assessment_router`, behaviour unchanged). Routes `GET /api/sites/{code}/ev/overview|evidence|
  evidence/analysis|financials|financial-assumptions`; Analysis/Financials take `cursor,limit` (default 50, 1..200).
- Composition `backend/assetops_backend/ev_site_reads.py::EvSiteReads` (pure; `_select` = the q4 shared selector,
  `_consequence` = stored row or read guard, `MONEY_COPY` = R5/R6 copy, `CLAIMS` order, `NEXT_EVIDENCE`,
  `SOURCE_UNVERIFIED_NOTE`). Built by `financials/composition.py::build_ev_site_read_service`.
- Adapter seams: `EvReadService.within/open_on/status_on/sessions_on/findings_on/page_on/foundation_on/assets_on/
  accepted_on` (`postgres_assessment_store.py`, after `_page`); `page_on` puts `route|basis` in the canonical cursor.
  Consequence store: module `ev_money_basis_on` (now also behind `EvUnit.basis`) and SELECT-only `EvMoneyReads`
  (`select_on` = q4 literal SQL, `history_on`, `tariff_on`, links via FK; `tariff_recorded_at` from the stored FK).
- Wire additions beyond the closure field lists (UI may rely on them): consequence `revision_no,tariff_recorded_at,
  limitation`; summary `reason`; Financials `history[]` (each `label:"Historical scenario"`); Analysis `total_count,
  excluded_records`, item `session_id,note`; Assumptions `tariff_revision_count,publication_note` (R2 sentence,
  `YYYY-MM-DD HH:MM UTC`), `consequence_tariff`; overview finding items `start/fault/abort_evidence_id`.
  PENDING/HISTORICAL with stored history -> consequence is a `WITHHELD/{PENDING_RECOMPUTE|HISTORICAL_CURRENT_CLAIM}`
  guard with null `revision_id/amount/currency`; without history -> `null`. UNKNOWN -> `null`.
- Readings (not rulings) to confirm at review: `objective.configured_service_window` is `null` (weekly schedule not
  resolved into the window); source `contact.state` is always `UNKNOWN` (no source-specific diagnostic wired);
  capability coverage seconds use selected session spans/Site-import intervals; the complete replay has accepted
  Site import intervals (`observed_peak_kw="60"`, `CONTEXT_ONLY`) and 223 accepted Analysis rows, so the closure's
  "no Site import" illustration does not hold. `links` are UI paths `/sites/{code}/ev`, `/ev/evidence`,
  `/ev/evidence/analysis`, `/ev/financials`, `/ev/financial-assumptions` with `?from&to&known_at` - commits 4-5 must
  serve exactly these; `finding` link stays null; Analysis item links all null, `record_target_state="UNAVAILABLE"`.
- Commits 4-5 anchors (UI): W2-06 frames `frontend/src/sites/EvAssessmentViews.tsx` (EvSessionsFrame/EvFindingFrame)
  wired in `frontend/src/shell/SiteAnalyticsFrames.tsx:36,175,502`; client `frontend/src/sites/evAssessmentClient.ts`
  (`createEvAssessmentClient` :204; add the five reads there or a sibling `evSiteClient.ts`). Cold precedent:
  `frontend/src/sites/coldSiteViews.tsx` (`ColdSiteFrame` :394, `eatTime` :168, `coldUiHref` :185) routed by
  `frontend/src/shell/coldSiteRoutes.tsx::coldSiteScreen` from `SiteAnalyticsFrames.tsx:715`. Mock screens
  `ev-health`(overview) / `ev-evidence` / `ev-evidence-analysis` / `ev-financials` / `ev-assumptions` in
  `frontend/mockups/v69/screen-manifest.json:1114-1186`. Guard `tools/checks/navigation-truthfulness.ps1`
  (`Get-InPageUnavailableEntryFailures`, +0 multiset). Tests: `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx`.
- Evidence (`7fb66e17`): `test_w207_ev_site_reads_postgres.py` 10 passed (envelope/selection incl. selector,
  stale guard, pending and literal empty prefix; 409 cursor + refusals; SOURCE_UNVERIFIED paging; Finding IDs; six
  replays + late terminal past an exact [08:00,08:30) end). Extended `test_pending_retry_settles_without_new_assessment_
  revision` (five-read pending mask, same revision restored, lower matching beats higher unmatched). Adjacent run
  (w207 pure + money pg + site reads, w206 reads + store) 57 passed in 21m37s. `tools/check-all.ps1` all 10 guards
  passed. Full suites not run (by brief). Private DB `w207f_test` dropped.

## Run 7 (2026-10-20): q5 commit-3 wire corrections landed; stopped at context budget before commits 4-5

- Landed `50c31605` (brief step 1). `ev_site_reads.py`: pure `service_windows`/`objective_windows` (q5 R1),
  `_contacts` (R2), `_union/_intersect/_measure/_coverage`, `_claim_coverage`, `_spans`, `_session_coverage` (R3);
  Analysis items add `interval_start/interval_end`; `note` only when `use=EXCLUDED` and `reason=SOURCE_UNVERIFIED`.
  Adapter (`postgres_assessment_store.py`, after `EvReadService.accepted_on`): `source_bindings_on` (selected run's
  `binding_set_revision_ids` matched as binding or binding-set revision IDs, else effective at cutoff; registered
  gateways only) and `source_contacts_on` (delegates to `ColdReadService.source_contacts_on`).
- Tests (`test_w207_ev_site_reads_postgres.py`): the five q5-named tests added; file 15 passed in 5m44s on `w207g_test`.
- Readings (not rulings), for the packet / review:
  1. `objective.service_schedule_declared` (bool) added so a declared schedule with no selected overlap is not
     "missing configuration"; `configured_service_windows` is always the list (one element when single). UI derives
     `Service window not declared` (declared=false) and `Configured service hours vary by connector` (len>1).
  2. `contact` keys: `state, checked_at, last_seen_at, age_seconds, diagnostic_id, diagnostic_received_at,
     cadence_seconds`. A connector slot binds three sources (one per role) on one gateway, so it aggregates:
     identical states -> that state, differing -> `MIXED`. SITE_METER uses only its `ev_site_import` binding. In the
     complete replay `known_at` (09:00) < `to` (09:05), so `checked_at` = known_at.
  3. Coverage adds `unit` (`WINDOW_SECONDS|SESSION_SECONDS|null`). Session claims are null when any selected
     session lacks a proved span; SESSION_OUTCOME known=expected=summed proved spans. `SUPPORTED` is demoted to
     `LIMITED` unless `ratio=="1"`. The null-coverage sentence is appended to a claim's own limitation
     (e.g. `Gross scenario only. Coverage duration cannot be calculated from the selected records.`).
  4. Source `limitation` `No source-specific contact diagnostic.` only when contact is UNKNOWN and facts exist.
- Resume at brief step 2 (spec commits 4-5, five EV UI routes) from the Run 6 "Commits 4-5 anchors (UI)" bullet,
  q5 "Commits 4–5 implementer dry-read", closure section 4 (spec lines 438-462) and the commits 4-5 copy ledger
  (spec lines 91-127). The wire is now the corrected q5 contract. Then step 3 (focused, check-all, full backend,
  host; copy `var/sites/mg-001.yaml` from plan2 if missing) and step 4 (packet). `w207g_test` was dropped.

## Run 8 (2026-10-20): main merged (q6), q6 backend landed; stopped at context budget before commits 4-5 UI

- Merged main (q6 rulings, spec "Run 7 rulings (q6)" at `.agent/W2-07-build-spec.md:716`). Landed `cfd299f8`:
  `ev_site_reads.py` `enabled_connectors()` (components `EV_CONNECTOR` with `ev-connector-enabled=ENABLED`);
  `service_windows` only resolves enabled connectors; `objective_windows` common = one occurrence covering
  **every** enabled connector (scheduled or not), `declared` = an enabled connector has weekly entries.
  Contact (`_contacts.contact`) now returns `by_source` (one per bound source, sorted by `source_id`, keys
  `source_id,state,last_seen_at,age_seconds,diagnostic_id,diagnostic_received_at,cadence_seconds`); one-source
  slot copies its details up; multi-source slot -> agreed state or `MIXED`, top-level details null. Coverage code
  already matched q6 R3; tests extended. `test_objective_resolves...`, `test_source_contact_uses...`,
  `test_claim_coverage_uses...` 3 passed (62.8s, `w207h_test`, dropped). q6 frontend tests are still owed in
  `evSiteMoneyRoutes.test.tsx` (`all_five_routes...` three objective labels; `ev_evidence_tabs_and_record_limit`
  Mixed chip/`Source contacts differ`/footer `Contact checked at {checked_at} UTC`/null + both coverage units;
  `financial_tabs_and_price_gate` `Metered with complete coverage` only on gross claim `ratio:"1"`).
- Nothing of commits 4-5 is written yet. Survey results so the next run need not re-read:
  - Routes are NEW paths `/sites/:siteId/ev`, `/ev/evidence`, `/ev/evidence/analysis`, `/ev/financials`,
    `/ev/financial-assumptions` (add `*_ROUTE_PATH` + Href helpers in `frontend/src/shell/operatorSiteRoutes.ts`
    near :107-:200; mount in `frontend/src/App.tsx` route list near :289-:333 passing `evAssessment`).
    API reads `/api/sites/{code}/ev/overview|evidence|evidence/analysis|financials|financial-assumptions` with
    `coldWindowSearch(window)` (+`cursor`/`limit` for analysis/financials); add to
    `frontend/src/sites/evAssessmentClient.ts` (`read()` :174 returns `ColdRead`, shapes :162) or a sibling client.
  - Reuse from `frontend/src/sites/EvAssessmentViews.tsx`: `evRefusalText` :78 (exact refusal copy already),
    `useRead` :100, `windowKey` :117, `ShortId`, `Gap` :132, `ProvenanceBadge` :157, `ToneBadge` :202
    (`ev-chip ev-tone--{green|amber|red}`), frame skeleton `EvSessionsFrame` :532 (Breadcrumbs, SitePageHeader,
    tabs, `site-tabs site-subtabs` nav, StatusBar, MetricCards, Panel, `panel-pair ev-pair`). Export the helpers.
    Unsupported in-panel controls: `UnavailableInline`/`UnavailableLinkEntry` (no `UnavailableTab`: +0 multiset).
  - Wire nested shapes (`backend/assetops_backend/ev_site_reads.py`): capabilities `claim,state,required_roles,
    missing_roles,coverage{known_seconds,expected_seconds,ratio,unit},accepted_evidence_ids,as_of,limitation`
    (seven claims in `CLAIMS` :49 order); sources `slot(CONNECTOR_1|CONNECTOR_2|SITE_METER|BILLING),asset_id,
    display_name,contact{...,by_source},quality{state GOOD|DEGRADED|NO_FACT,accepted_count},roles,as_of,limitation`
    (DEGRADED -> `Limited`); next_evidence `code,text,why,link`; needs_attention `code(PENDING|FAULT_ABORT|
    INCOMPLETE_SESSION|METER_OR_SOURCE_GAP|TARIFF_MISSING),text,link`; energy `supported_kwh,complete_kwh,
    partial_kwh,unknown_seconds`; site_power `observed_peak_kw,configured_limit_kw,coverage,claim_limit`;
    analysis items per q5 §5 with `record_kind` verbatim and `KIND_TEXT` value_display for events; tariff
    `revision_id,value,currency,unit,basis,valid_from,valid_to,recorded_at`; `billing_state` always `NO_RECORD`.
  - Mock panel titles: `v69-rendered-panels.json` has `ev-evidence`, `ev-evidence-analysis`, `ev-financials`,
    `ev-assumptions`; the EV Overview id in the JSON is `ev-health` with ONE panel `Condition and evidence` --
    that disagrees with q5's five-title EV Overview array. Check the manifest (`screen-manifest.json:1114-1186`)
    for which mock screen is `/ev` before using `expectV69Panels`; if no JSON entry has the five titles, that is a
    pending ruling (the helper reads the JSON, so asserting q5's array needs a JSON entry or approved title map).
- UI-copy dependence on the three q6 fields (keep isolated): objective line (service_schedule_declared /
  configured_service_window(s)); Contact chip + `Source details` + footer (contact.state/by_source/checked_at);
  Site power card, capability What-can-say/coverage text, claim details, Financials Confidence (coverage.unit/ratio).
- Readings made this run: "enabled connector" = Foundation component property `ev-connector-enabled=ENABLED`
  (same as `sites/ev_foundation.py:522`); a schedule on a disabled connector is not "declared".
- Resume: commits 4-5 UI per spec :91-127, closure §4 :438-462, q5 dry-read, q6; then final verification
  (focused, check-all, full backend, host) and the packet.

## Run 9 (2026-10-20): in progress - commits 4-5 UI
- Panel JSON keys confirmed: `ev`, `ev-evidence`, `ev-evidence-analysis`, `ev-financials`, `ev-assumptions` (q5 titles).
- Plan: new `frontend/src/sites/evSiteClient.ts` (five reads), `frontend/src/sites/EvSiteViews.tsx` (one frame, five
  views, modelled on `coldSiteViews.tsx::ColdSiteFrame`), `frontend/src/sites/w2-ev-site.css`, routes in
  `operatorSiteRoutes.ts` + `App.tsx`, tests `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx`.
- Run 9 landed UI (`frontend/src/sites/{evSiteClient.ts,EvSiteViews.tsx,w2-ev-site.css}`, `shell/evSiteRoutes.tsx`,
  routes in `operatorSiteRoutes.ts`/`App.tsx`) and 5 passing tests in `evSiteMoneyRoutes.test.tsx`. Next: captures
  (reuse `.agent/W2-06-evidence/{seed.py,capture.mjs}` into `.agent/W2-07-evidence/`), height table, full frontend
  suite/build, then final verification and packet.
