# W5-01 cold depth — build contract

Architect/Planner, 2026-10-22. Packet: [`tasks/W5-01-cold-depth.md`](../tasks/W5-01-cold-depth.md). Authority: `.ai/ROLE_CONFIG.md` readiness gate and all 13 W3/W4 lessons, `.agent/post-W2-sequence.md` W5-01, v6.9 `cooling`, `cold-health`, `cold-scenarios`, merged W2-03/04 selected reads and W4-01 frozen case model. Cards C1–C5 are complete builder instructions. Each card needs this shared section, its own card and at most two linked existing code sections.

Each card is one builder run and one to three commits. Its final commit includes its tests and, for page cards, the named 1440/390 captures; the builder then hands off for the stated review before dependent work.

## Gate, merge and immutable boundaries

**W2 gate satisfied:** W2-F merged as `2df2a3da`; the independent re-audit closed all 14 structural findings. W2-F Low L1 is fixed in C5: the refused cold Finding displays `Finding state` / `Unknown` / `Confidence: Unknown` above `PageRefusal`. Its L2 is capture-manifest provenance and changes no product semantics. W5-01a (C1–C3) is read-only selected depth with two pages and no migration. W5-01b (C4–C5) adds the authored scenario pipeline and one page. It owns `0032_w5_cold_scenarios`, exact `down_revision="0030_w4_mini_decisions"`; W3-03's reserved `0031` is unused. W5-01b merges before W5-02 `0033`. C1 and C4 touch shared read/router/schema; C2/C3/C5 mount shared Site frames, navigation or registry. **Every unit receives per-unit independent review** before its dependent unit. No W4-01 Incident/Maintenance/WorkEvent identity, lifecycle or refusal code changes.

`cold-findings`, `cold-work`, Incident, work verification, cold Recommendation and Action belong to W5-02. A W5-01 cue to an unbuilt W5-02 destination is plain text with no `href`, click handler or tab stop. Existing Temperature, Backup, Evidence, Foundation and Financials routes remain real destinations.

Readiness review ran `tools/check-all.ps1`: all 11 guards passed, including the estate self-test. Builders rerun it after shared navigation or registry changes. C2 replaces one `Cooling` unavailable occurrence. C5 makes the shared `Scenarios` tab live for cold only; the unavailable literal remains for other non-mini-grid Sites, so the navigation multiset count is unchanged. Registry titles come from `v69-rendered-panels.json`.

## Shared selected read and guards

`GET /api/sites/{site_code}/cold/cooling` and `/cold/health` reuse the gate factored by C1 from the nested `cold_site_api.build_cold_site_router.opened`: authenticate and Site-scope before lookup; enforce strict paired half-open UTC `from,to` at most 31 days, optional `known_at`, disclosure, one read-only REPEATABLE READ connection, and committed watermark. `schema_version:"cold-depth-1"`; response fields `site_id`, `window:{from,to,known_at,committed_watermark}`, `selection:{state,assessment_revision_ids,accepted_evidence_ids,source_provenance}`, page payload and `links`. The state is exactly `cold_reads.STATES`: `CURRENT`, `PENDING_RECOMPUTE`, `STALE_SOURCE`, `HISTORICAL`, `UNKNOWN`, with merged cold precedence (pending before historical). Exact accepted IDs are deduplicated cited IDs from the selected W2-03 assessment, episode/Finding and W2-04 read, never a page or cursor subset. Call `ColdReadService.envelope_on(...)["source_provenance"]` for the revision-ID selection; do not pass evidence IDs as revision tokens to `public_provenance`. `evidence/public_provenance.py` classifies the *entire* selected set: empty/broken/foreign is `UNKNOWN`; incompatible classes/runs are `MIXED`. No gateway/run-mode inference and no private Lab truth.

Cooling payload: `recovery_state` (`LIMITED`, `CONTRADICTORY`, `UNKNOWN`), selected accepted compressor/probe points and IDs, `observed_restart_at`, `observed_return_to_policy_at`, nullable `duration_lower_seconds`/`duration_upper_seconds`, `comparison_state` (`CONTEXT_MISSING` for existing W2 producer), and context rows for ambient, continuous power, door, loading and defrost. The W2 selected start chain lacks ordered recovery proof (`cold_site_reads.COOLING_TEXT` and W2-F S2), so all existing W2 replay cases keep duration null and comparison missing even if separate compressor/probe observations exist. Never show mock 36/42 minutes or +17% as measured. Health payload has effective configured `asset_id`, `observation`, `condition_state` (`NEEDS_INVESTIGATION`, `LIMITED`, `UNKNOWN`, `NOT_CONFIGURED`), `limitation`, selected accepted IDs and link. A selected failed generator start permits `NEEDS_INVESTIGATION`, not failed-part diagnosis. Compressor condition is `UNKNOWN`; one accepted probe permits `Limited` sensing coverage, not room-wide condition. Null is distinct from zero and from an empty array. Malformed 200 responses render refusal, not a fabricated empty state.

Existing refusal codes (copied from `cold_site_api`): `UNAUTHENTICATED` 401, `SITE_SCOPE_FORBIDDEN` 403, `COLD_PARAMETER_UNKNOWN`, `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID`, `COLD_WINDOW_TOO_LONG` 422, `SITE_NOT_FOUND` 404, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` 403, `COLD_READ_UNAVAILABLE` 503. These cursorless routes invent no 409. API `links` use `/api/sites/{site_code}/cold/...` and keys `temperature`, `backup`, `evidence`, `health`; UI translates through `coldUiHref`/`operatorSiteRoutes.ts`. The shell Site token is imported `site_code`, never the internal UUID. Exact selected Finding/assessment UUID and revision ID are carried only as record IDs where applicable. Preserve `from,to,known_at`. Current destinations are `/sites/{site_code}/performance/temperature`, `/sites/{site_code}/performance/backup`, `/sites/{site_code}/evidence`, `/sites/{site_code}/health`; missing ID means text, not a link. Mock F-118 and INC-203 are display examples, never database IDs.

### Visible literal ledger

The Site title comes from imported Site data; `GreenHarvest Cold Room` is a fixture value, not page copy. Dynamic UTC timestamps follow the selected window. All strings below are literal; a server refusal adds its exact `{error:{code,message}}` text below the specified heading and a `Retry` link to the same URL.

| Surface | Exact order, copy and destination |
| --- | --- |
| Cooling header/status | `Sites › {Site name} › Performance › Cooling`; heading `Cooling`; `Comparison limited`/`Confidence: Low`/`Observed cooling response is incomplete; ambient, loading and defrost context is missing.` for LIMITED; use C2 state matrix for CONTRADICTORY and UNKNOWN; `Inspect recovery basis →` links to selected Temperature. `Low` describes this comparison, not an assessment enum. |
| Cooling four cards | `Usual time back to 4°C` = `Unknown` / `No matched earlier window`; `This time back to 4°C` = `Not established` / `No ordered compressor-to-policy recovery assessment`; `Difference` = `Unknown` / `A comparison is not supported`; `Comparable?` = `Not yet` / the recovery-state-specific C2 note. If selected policy upper bound differs from 4°C, substitute its configured value; if policy absent use `back to policy` in both labels. |
| Cooling titled panels | `Recovery curves` uses selected accepted points only; if none `No accepted recovery sequence in this window.` `Context normalization` has `Ambient temperature`, `Power availability`, `Door-open duration`, `Loading / batch`, `Defrost`; C1 maps each row to its exact accepted role or always Unknown. The backup-failed door pair is Observed. `Next best evidence` has `Record a comparable recovery` / `Keep load, door, ambient, defrost and cooling-energy records.` (plain text until W5-02), and `Inspect the backup sequence` / `Open Backup →` (live selected Backup). |
| Cooling notice | `These records do not establish cooling degradation or compressor failure. Record loading and door activity and compare a later recovery under similar conditions.` |
| Cold Health | `Sites › {Site name} › Health`; heading `Health`. Cards in order: `Backup generator`, `Cooling plant`, `Temperature sensing` use C3's complete NEEDS_INVESTIGATION/LIMITED/UNKNOWN/NOT_CONFIGURED matrix and state-specific notes. No green physical-condition state. |
| Health panel | `Condition and evidence`; columns `Asset`, `Supported assessment`, `Next evidence`. Effective generator asset: `Automatic start failed` or `No accepted start result` / `Witness an automatic-start test`; compressor: `Condition unknown` / `Record matched loading, door and ambient context`; probe: `Single-point observation` or `No accepted probe` / `Add calibrated spatial coverage`. Asset label/ID from selected Foundation. Existing Backup/Evidence destinations only. |
| Shared state/empty/refusal | `PENDING_RECOMPUTE`: `New evidence is waiting to be assessed. Earlier selected observations are shown, not a current conclusion.` (new W5 literal, intentionally distinct from `cold_reads.PENDING_NOTE`); `HISTORICAL`: `Read at an earlier evidence cutoff; newer committed evidence exists.` (merged `cold_reads.HISTORICAL_NOTE`); `STALE_SOURCE`: `The selected source is stale for this window.`; `UNKNOWN`: `No selected cold assessment covers this window yet.` Cooling empty `No accepted recovery sequence in this window.` Health empty `No condition observation is available for this window.` Refusal heading `Cold depth unavailable`; button `Retry`. Pending/stale/historical never gain a current positive condition label. |

### Measured mock and content caps

`tools/measure-mock-panels.mjs` measured the seven requested mock screens at 1440×1000 and 390×900 on 2026-10-22; Chrome required a temporary `--no-sandbox` launch adjustment. Temporary script was removed. The mock content region is 1161/360px, document/client scroll widths 1425/1425 and 390/390. A second measured pass inserted a 166-character missing-evidence sentence with a 36-character UUID in the first metric note, first panel prose and first notice at both widths. Its actual worst pass is recorded below. Refusal overlays do not exist in the mock and are capped by app captures.

| Screen | Base page 1440/390; base block heights px | Worst page 1440/390; 390 card height | App caps 1440/390 px |
| --- | --- | --- | --- |
| `cooling` | 1312/2124; status 45/99, cards 113/264, recovery 386/235, context 386/398, notice 42/97, next 234/268 | 1361/2188; cards 344 | status ≤85/140; cards ≤180/360; each panel ≤470/500; notice ≤90/150; next ≤300/360; page ≤1600/2350 |
| `cold-health` | 1001/1244; cards 138/314, condition 198/269 | 1001/1323; cards 393 | cards ≤200/430; condition ≤330/430; page ≤1200/1550 |
| `cold-scenarios` | 1001/1125; panel 316/355, notice 42/78 | 1001/1127; no cards | panel ≤430/560 for one row or empty; notice ≤90/135; page ≤1250/1500 |

At 390, cards wrap two columns and the table scrolls within its panel with sticky first column. UUIDs break at character boundaries. 160-character limitations/source descriptions wrap; longer optional narrative may show the first 160 characters with `Read full basis` disclosing the exact full text. Never ellipsize status, missingness, refusal or source classification. Every capture asserts document `scrollWidth <= clientWidth`, each block cap and refusal overlay cap.

## C1 — selected cold depth read (W5-01a; per-unit review)

Read C1, shared contract, merged `analytics/cold_site_reads.py` and `analytics/cold_reads.py`. Files: new `backend/assetops_backend/analytics/cold_depth.py`, `backend/assetops_backend/cold_depth_api.py`, `backend/tests/test_w501_cold_depth_postgres.py`, `backend/tests/test_w501_cold_depth_router.py`; shared **Lane A only** `backend/assetops_backend/main.py`, `backend/assetops_backend/cold_site_api.py` (extract nested `opened` into an importable same-semantics gate). No schema. Compose on `ColdReadService.within` and the W2 selected rows on one connection. Tests prove exact source IDs, first/final cutoff, pending PENDING/LEASED/FAILED job, historical known_at, stale probe, empty, wrong Site, missing selected ID, DB failure and that no W2 case produces a numeric recovery comparison. Existing verified producers: `backend/tests/test_w204_cold_reads.py::test_excursion_five_reads`, `::test_late_reading_pending_then_historical`, `::test_missing_probe_and_empty_window`, `backend/tests/test_w203_cold_reads_postgres.py`, `config/scenarios/cold-backup-failed.yaml`, `backend/tests/fixtures/w2/cold-w203-vectors.json`. Producer command: `pytest backend/tests/test_w204_cold_reads.py::test_late_reading_pending_then_historical backend/tests/test_w202_cold_replay_postgres.py -q` on a private `*_test` DB. Window `[2026-10-06T19:00:00Z,2026-10-06T20:05:00Z)`; current reads omit `known_at` and use the committed DB watermark, whose cold ingestion `decided_at` is wall-clock `clock_timestamp()`/`datetime.now(timezone.utc)` in the merged chain. Save `before["window"]["known_at"]` before `advance_late()`; pass that exact value for the historical read after late advancement. No fixed 2026-10-06 cutoff is valid on a present-day cold replay. The frozen scenario event clock and the wall-clock decision clock are separate facts; pin/read within each fixture by the returned watermark. Review C1 before C2.

**C1 derivation table (test `test_w501_cold_depth_postgres.py::test_cooling_first_steps_and_context`).** `recovery_state` maps W2 `cooling_recovery.state`: `LIMITED` → `LIMITED`, `CONTRADICTORY` → `CONTRADICTORY`, `UNAVAILABLE` or no selected assessment → `UNKNOWN`. `selected_points` is an ordered list of the selected start-chain `COMPRESSOR` and `PROBE` first observed steps only, each `{role,source_time,evidence_ids}`; it is not a recovery curve. `observed_restart_at` is null because the first compressor step cannot prove a restart after the interruption; `observed_return_to_policy_at` is null because the first probe step cannot prove a later return. Both duration fields are null. No unselected `compressor_state` or probe row may fill them. `comparison_state=CONTEXT_MISSING` for W2. Context rows are exactly: `Ambient temperature` = always `Unknown` (optional `ambient_temperature` exists in `cold-roles-1`, but the W2 assessment does not select it); `Power availability` = `Observed` only from an accepted selected `grid_power_event` row, else `Unknown`; `Door-open duration` = `Observed` only from a matched accepted selected `door_event` OPEN/CLOSE pair with positive elapsed time, else `Unknown`; C1 reads event kind and source time for the exact selected accepted `door_event` evidence IDs from the Site-scoped evidence ledger on the same REPEATABLE READ connection (add the read in `analytics/cold_depth.py`); CONTEXT links alone do not prove a pair. `Loading / batch` = always `Unknown` (no loading role); `Defrost` = always `Unknown` (no defrost role). The `cold-backup-failed.yaml` producer has `DOOR_OPEN` 19:10 and `DOOR_CLOSE` 19:11, so its door row is `Observed`, duration 60 seconds; loading/ambient/defrost remain Unknown. A door event does not imply a comparable cooling recovery. C1 includes `backend/tests/test_w501_cold_depth_router.py::test_cold_depth_gate_and_links` for the extracted gate and Site-code API links.

Cold selected response `links` is `{temperature,backup,evidence,health}` with API paths by `site_code`; missing selected record IDs remain null. C1's direct stale-source test may use an accepted but stale diagnostic/probe fixture, while the positive replay may not reach it. Every cold persisted capture uses the returned committed watermark, never a guessed event timestamp.

## C2 — Cooling page (W5-01a; per-unit review)

Read C2, literal ledger, mock caps, C1 DTO. Files: new `frontend/src/sites/ColdDepthClient.ts`, `frontend/src/sites/ColdCooling.tsx`, `frontend/src/sites/__tests__/coldDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/src/sites/coldSiteViews.tsx`, `frontend/src/sites/ColdAssessmentViews.tsx`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace the single unavailable `Cooling` occurrence only after its truthful route `/sites/{site_code}/performance/cooling` is live. C2 creates `ColdDepthClient.ts` with validated cooling and Health reads and both DTO types; C3 may edit this client for Health wiring while preserving cooling validation. Tests assert exact four cards/five context rows, W2 null comparison, no 36/42/+17% measured claim, state/refusal copy and query-preserving links. Captures owned here at 1440/390: `cooling-limited` (C1 backup-failed producer), `cooling-empty` (C1 missing-probe producer), `cooling-pending` and `cooling-historical` (C1 late-reading producer), `cooling-refused` (serve a foreign-Site or disclosure-denied request through the live C1 route; assert the 403 response and rendered refusal, not a fake-client unit test). The window and returned watermark are C1's; save the before-late watermark for historical. Replace `$expectedTabs` one `Cooling` occurrence and re-anchor `navigation-rail-fixtures.ps1` negative case to the live `<ColdCooling`/route branch: deleting that live branch must fail. Breadcrumb intentionally ends `Performance › Cooling`; Temperature and Backup siblings remain at `Performance`. At 390, use actual `Not established`, `Unknown` and the 51-character ordered-recovery note in the two-column cap test; wrap values/notes without ellipsis. Run navigation positive/negative fixtures and review C2 before C3.

**C2 literal state matrix (test `coldDepth.test.tsx::cooling_state_copy`).** `LIMITED`: status `Comparison limited`, confidence `Low`, subtitle `Observed cooling response is incomplete; ambient, loading and defrost context is missing.` `CONTRADICTORY`: status `Comparison contradictory`, confidence `Unknown`, subtitle `Selected cooling observations conflict; no recovery comparison is supported.` `UNKNOWN`: status `Comparison unknown`, confidence `Unknown`, subtitle `No selected cooling assessment establishes a recovery comparison for this window.` The four card labels and values in the shared ledger apply to all three states; the fourth note is `Ambient, loading and defrost records missing` only in LIMITED, `Conflicting selected observations prevent a comparison` in CONTRADICTORY, and `No selected comparison basis` in UNKNOWN. The door row uses C1's observed pair, so no visible string says door context is missing in the backup-failed fixture. `CURRENT` leaves the recovery state label intact; pending/historical/stale show their state notice and suppress a current-positive comparison label. Live 403 refusal is captured through the new route with the same URL on Retry.

## C3 — cold Health and W5-01a close (per-unit review)

Read C3, literal ledger, mock caps, C1 DTO. Files: new `frontend/src/sites/ColdHealthDepth.tsx`, `frontend/src/sites/__tests__/coldHealthDepth.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteHealthFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/sites/ColdDepthClient.ts`, `frontend/src/sites/ColdFoundationViews.tsx`, `frontend/src/sites/__tests__/siteHealthBoundary.test.tsx`, `frontend/src/sites/__tests__/coldSiteViews.test.tsx`; run `frontend/docs/architecture/check_v69_dependency_registry.cjs`. Keep S7 two-clock gateway contact separate from equipment condition. Registry titled panels `(cooling,1) Recovery curves`, `(cooling,2) Context normalization`, `(cooling,3) Next best evidence`, `(cold-health,1) Condition and evidence` map only exact C1 selected read/gap paths; unresolved comparator and physical-condition nodes stay unresolved. Captures at 1440/390: `cold-health-failed-start`, `cold-health-unknown`, `cold-health-pending`, `cold-health-historical`, `cold-health-refused`, using C1 backup-failed/empty/late/refusal producers and clock equal to the C1 response watermark; historical uses the before-late watermark, not a fixed 2026 instant. Tests assert no physical health from gateway contact/configuration. Run `tools/check-all.ps1`, focused tests and one real-Postgres full suite, then review/merge W5-01a.

**C3 Health composition and state copy (test `coldHealthDepth.test.tsx::condition_matrix`).** For COLDCHAIN, `SiteHealthFrames.tsx` renders the v69 condition cards, then `Condition and evidence`, then the bounded condition notice. It retains the shared S7 `Data sources · data quality, not equipment condition` panel below `Condition and evidence` using the existing `SiteHealth.tsx` gateway read and independent server-receipt clock. The live `Health › Data sources →` link in `ColdFoundationViews.tsx:646` targets this panel (add a stable fragment). Cold Evidence source analysis is a different read. Preserve S7 acceptance and update `siteHealthBoundary.test.tsx` and `coldSiteViews.test.tsx` for the composition and link. The 1200/1550px mock page cap measured the condition-only composition. C3 keeps the S7 panel and checks a composed app page cap of 1900/2350px at 1440/390, a gateway panel cap of 700/800px, and no horizontal document overflow in each Health capture; record actual measurements before review. The table deliberately uses v69 column `Supported assessment`; the third probe row is a deliberate W5 addition, measured under the 330/430px cap. Card notes are conditional: backup `NEEDS_INVESTIGATION` → `Failed automatic start observed; part not diagnosed`; backup `UNKNOWN` → `No accepted automatic-start result in this window`; backup `NOT_CONFIGURED` → value `Not configured`, note `No backup generator is declared in the selected Foundation`. Cooling plant `UNKNOWN` → `Comparable recovery and condition evidence absent`; cooling plant `NOT_CONFIGURED` → value `Not configured`, note `No cooling plant is declared in the selected Foundation`. Temperature sensing `LIMITED` (exactly one accepted selected probe) → `One accepted probe does not establish room-wide coverage`; `UNKNOWN` → `No accepted probe observation in this window` when none is selected, or `Multiple selected probes do not establish room-wide condition` when two or more are selected; `NOT_CONFIGURED` → value `Not configured`, note `No temperature probe is declared in the selected Foundation`. No other positive condition value is allowed. Table row observations follow the same state: absent asset → `Not configured`; present without selected observation → `No accepted start result`/`Condition unknown`/`No accepted probe`; selected failed start → `Automatic start failed`; accepted single probe → `Single-point observation`. C1 and C3 also test exactly one versus two accepted selected probes; two remains `UNKNOWN` physical condition. A `NOT_CONFIGURED` state is produced by a test-scoped selected Foundation without that asset and asserted by `test_w501_cold_depth_postgres.py::test_health_not_configured`; no existing cold replay is falsely labelled as that state.

**Registry rows written by C3** in `v69-dependency-registry-pilot.json` (C3 creates only `I-W5-cold-depth-read` and `I-W5-cold-depth-ui`; C5 alone creates the scenario nodes). The following table summarizes the rows; the executable JSON and ledger values below are authoritative. Each panel row has `status` stays `gap` until implementation review accepts the node evidence:

| screen_id, panel_index, title | area | requires | status | reason |
| --- | --- | --- | --- | --- |
| `cooling`, 1, `Recovery curves` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `W5-01a selected first steps do not establish an ordered recovery curve.` |
| `cooling`, 2, `Context normalization` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Ambient is not selected by the W2 cooling assessment; loading and defrost roles are absent, so those context rows show Unknown.` |
| `cooling`, 3, `Next best evidence` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Evidence actions are bounded to existing Backup and Temperature destinations.` |
| `cold-health`, 1, `Condition and evidence` | `cold-chain` | `I-W5-cold-depth-read`, `I-W5-cold-depth-ui` | `gap` | `Selected start and probe observations do not establish physical equipment health.` |

C3 inserts only its depth rows and nodes together; `node` IDs in `requires` must exist before `check-all`. C5 adds its scenario nodes and row in W5-01b.

## C4 — authored cold scenario store (W5-01b; per-unit review)

Allowed authored what-if contract `cold-scenario-authored/1`: the only `kind` is `STOCK_VALUE_CONTEXT`; the only assumption object is `{stock_quantity,stock_unit,unit_value,currency}` with quantity and value decimal strings greater than zero and at most 8 fractional digits, `stock_unit` a nonempty 1–32 character label, and `currency` a three-letter uppercase ISO 4217 code. The baseline is the selected observed W2 cold window and its accepted IDs, **not** a matched counterfactual; there is no calculated amount, spoilage rule, comparison delta or outcome. Scenario scope is exactly one authorized Site and selected half-open UTC period of at most 31 days; cross-Site scenarios and currency conversion are refused as `COLD_SCENARIO_INVALID`. Formula version is `AUTHORED_ONLY/1` and must be stored. This deliberately implements a reviewable authored scenario list without claiming a financial translation that the selected evidence cannot support.

Read C4, shared contract, merged `mini_decisions/scenarios.py` command/actor pattern. Files: **Lane A only** `backend/migrations/versions/0032_w5_cold_scenarios.py`, new `backend/assetops_backend/cold_scenarios/{rules,store,service}.py`, `cold_scenarios_api.py`, `backend/tests/test_w501_cold_scenarios_postgres.py`; shared `backend/assetops_backend/main.py`. Migration creates scoped `cold_scenario` (tenant/site/id, public_no, actor, created_at) and append-only `cold_scenario_revision` (id, scenario, revision_no, prior, recorded_at, actor, idempotency_key, name max 160, assumptions JSON, authored basis JSON, basis_sha256, correction reason). Composite Site FK, unique `(scenario_id,revision_no)` and `(scenario_id,idempotency_key)`; never rewrite a revision. Authored basis includes half-open window, exact selected W2 assessment revision IDs, accepted evidence IDs, Foundation revision ID, cutoff and source class. No observed-outcome column, enum, field or status. Correction appends. Same key/body returns same ID; same key/different body is 409 `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`; stale predecessor 409 `COLD_SCENARIO_REVISION_CONFLICT`; invalid input 422 `COLD_SCENARIO_INVALID`; existing cold access/503 codes apply. Ordinary viewer has `GET /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=&scenario_at=&limit=&cursor=`; POST same path and `POST .../{scenario_id}/revisions` require existing decision principal/actor policy. List DTO `cold-scenarios-1` has window/watermark, scenario_at, selection, items, next_cursor; row fields `id`, `revision_id`, `name`, `assumptions`, `authored_basis`, `recorded_at`, `scenario_state` (`DEFINED` or read-only `HISTORICAL`) and exact source IDs. No observed outcome field. Default 50/max 100; cursor binds tenant/Site/window/evidence cutoff/scenario_at/watermark/last `(recorded_at,id)`; invalid 422 `COLD_SCENARIO_CURSOR_INVALID`, changed basis 409 `COLD_SCENARIO_CURSOR_BASIS_CHANGED`. Watermarked empty means no authored row in scope, not failed read. Tests prove migration/downgrade/sole head, auth, replay, foreign IDs, cutoff, cursor, store failure and no revenue/spoilage/savings claim. Persisted positive producer is this new POST exercised by `test_w501_cold_scenarios_postgres.py` with exact C1 selected IDs; it must exist and pass at C4 review before C5 captures. Use the C1 returned evidence watermark for basis selection, and DB `clock_timestamp()` for authored `recorded_at`/default `scenario_at`. The new POST producer saves `scenario_at` after first write, then appends correction at a later DB instant; historical list passes saved `scenario_at`. The clocks remain distinct response fields. Never compare a 2026 evidence event timestamp to a present-day authored row. Review C4 before C5.

**C4 exact persisted schema and wire contract.** Migration `0032_w5_cold_scenarios` first creates `cold_scenario_public_no_seq`, then `cold_scenario`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `public_no bigint NOT NULL DEFAULT nextval('cold_scenario_public_no_seq')`, `create_key text NOT NULL`, `create_payload_sha256 text NOT NULL`, `create_actor_id text NOT NULL`, `created_at timestamptz NOT NULL DEFAULT clock_timestamp()`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`; named constraints `cold_scenario_scope_uk UNIQUE(tenant_id,site_id,id)`, `cold_scenario_public_uk UNIQUE(tenant_id,public_no)`, `cold_scenario_create_key_uk UNIQUE(tenant_id,site_id,create_key)`, and named `cold_scenario_site_fk` on `(tenant_id,site_id)` to `site(tenant_id,id)`. Root checks `cold_scenario_create_key_check` length 8..128, `cold_scenario_create_payload_sha256_check` 64 lowercase hex, `cold_scenario_create_actor_id_check` trimmed length 1..128. `cold_scenario_revision`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `scenario_id uuid NOT NULL`, `revision_no integer NOT NULL`, `supersedes_revision_id uuid NULL`, `name text NOT NULL`, `kind text NOT NULL`, `assumptions jsonb NOT NULL`, `authored_basis jsonb NOT NULL`, `basis_sha256 text NOT NULL`, `formula_version text NOT NULL`, `correction_reason text NULL`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`, `authorization_basis text NOT NULL`, `attestation text NOT NULL`, `idempotency_key text NOT NULL`, `payload_sha256 text NOT NULL`, `recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()`. Checks: `cold_scenario_revision_revision_no_check` (>0), `cold_scenario_revision_name_check` (trimmed length 1..160), `cold_scenario_revision_kind_check` (`STOCK_VALUE_CONTEXT`), `cold_scenario_revision_formula_check` (`AUTHORED_ONLY/1`), `cold_scenario_revision_chain_check` (revision 1 has null prior/reason; later revision has nonnull prior and trimmed reason length 1..2000), `cold_scenario_revision_basis_sha256_check` and `cold_scenario_revision_payload_sha256_check` (each 64 lowercase hexadecimal characters), `cold_scenario_revision_idempotency_key_check` (length 8..128), `cold_scenario_revision_actor_check` (nonempty actor kind/id/authorization basis/attestation). Named FKs `cold_scenario_revision_scenario_fk` `(tenant_id,site_id,scenario_id)` to scoped root, `cold_scenario_revision_previous_fk` `(tenant_id,site_id,supersedes_revision_id)` to scoped revision; named unique `cold_scenario_revision_scope_uk(tenant_id,site_id,id)`, `cold_scenario_revision_no_uk(scenario_id,revision_no)`, `cold_scenario_revision_previous_uk(scenario_id,supersedes_revision_id)`, `cold_scenario_revision_key_uk(scenario_id,idempotency_key)`. Index `cold_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`. Downgrade removes index, revision, root, then sequence. Basis JSON is server-resolved inside the write snapshot; client cannot choose IDs or cutoff.

POST root and correction both take gate query `from,to,known_at`; `from,to` are required, strict UTC, paired and at most 31 days; optional `known_at` selects the evidence basis within the write snapshot. Unknown/repeated query keys use `COLD_PARAMETER_UNKNOWN` 422. No body field may override the Site or selected window. Server-resolved `authored_basis` JSON has closed keys `{from,to,cutoff,assessment_revision_ids,accepted_evidence_ids,foundation_revision_id,source_provenance}`; UUID arrays are sorted/deduplicated and every ID belongs to this selected Site/window. SQL JSON checks require `jsonb_typeof(assumptions)='object'` and `jsonb_typeof(authored_basis)='object'`; exact keys, decimal grammar, ISO currency and selected-ID membership are service rules. The root stores `create_payload_sha256` of canonical command plus the selected query/window; exact-key replay compares it with the first revision payload hash.

POST root body, closed keys: `{schema_version:"cold-scenario-command-1",idempotency_key:string,actor:{kind:"SERVICE",id:string,attestation:string},name:string,kind:"STOCK_VALUE_CONTEXT",assumptions:{stock_quantity:string,stock_unit:string,unit_value:string,currency:string}}`. Correction POST adds `supersedes_revision_id` UUID and `correction_reason` 1..2000 characters; all other keys identical. Reuse `mini_decisions.scenarios.admit`/`authorize`: missing/non-SERVICE principal or wrong scope/grant → 403 `DECISION_WRITE_FORBIDDEN`; USER actor → 403 `DECISION_USER_AUTH_REQUIRED`; malformed service attestation → 422 `DECISION_ATTESTATION_INVALID` (merged `mini_decisions/model.py:34`). Gate/read failures retain `UNAUTHENTICATED` 401, `SITE_SCOPE_FORBIDDEN` 403, `SITE_NOT_FOUND` 404, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` 403, `COLD_READ_UNAVAILABLE` or `DECISION_STORE_UNAVAILABLE` 503. Invalid body, nonselected/foreign basis, no selected cold assessment, cross-Site/currency conversion → 422 `COLD_SCENARIO_INVALID`; same key/different canonical body → 409 `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`; stale prior → 409 `COLD_SCENARIO_REVISION_CONFLICT`. New root/correction → 201 `{schema_version:"cold-scenario-write-1",id,code:"CSCN-000001",revision_id,revision_no}`; exact replay → 200 same body. Public number uses the global `cold_scenario_public_no_seq` with `CSCN-` plus six minimum zero-padded decimal digits.

| C4 refusal | HTTP | Trigger |
| --- | ---: | --- |
| `UNAUTHENTICATED` | 401 | Missing authenticated request |
| `SITE_SCOPE_FORBIDDEN`, `COLD_SOURCE_DISCLOSURE_FORBIDDEN` | 403 | Site or source disclosure denied |
| `DECISION_WRITE_FORBIDDEN`, `DECISION_USER_AUTH_REQUIRED` | 403 | Service principal or actor rejected |
| `DECISION_ATTESTATION_INVALID` | 422 | Malformed service attestation |
| `SITE_NOT_FOUND` | 404 | No authorized cold Site |
| `COLD_PARAMETER_UNKNOWN`, `COLD_TIME_INVALID`, `COLD_WINDOW_INVALID`, `COLD_WINDOW_TOO_LONG`, `COLD_SCENARIO_INVALID`, `COLD_SCENARIO_CURSOR_INVALID` | 422 | Query, time, body, basis or cursor invalid |
| `COLD_SCENARIO_CURSOR_BASIS_CHANGED`, `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`, `COLD_SCENARIO_REVISION_CONFLICT` | 409 | Changed selection, replay body or predecessor |
| `COLD_READ_UNAVAILABLE`, `DECISION_STORE_UNAVAILABLE` | 503 | Selected read or authored store unavailable |

GET list `cold-scenarios-1`: `{schema_version,site_id,window:{from,to,known_at,committed_watermark},scenario_at,selection:{state,assessment_revision_ids,accepted_evidence_ids,source_provenance},items:[{id,code,revision_id,revision_no,name,kind,assumptions,authored_basis,recorded_at,scenario_state}],next_cursor}`. `selection.state` comes from C1's selected cold read and drives C5 pending notice. Revision 1 `authored_basis.from,to` fixes each root window. A correction resolves its query `from,to` and must equal revision 1 exactly; mismatch returns 422 `COLD_SCENARIO_INVALID` before append. Test same-window correction and cross-window refusal. List only roots whose revision 1 `authored_basis.from,to` equals the requested period; select each latest revision with `recorded_at <= scenario_at` and `authored_basis.cutoff <= window.known_at`. `scenario_state=HISTORICAL` iff the selected revision is superseded at current authored DB time or the caller passed `scenario_at` before the latest stored revision or `known_at` before the current evidence watermark; otherwise `DEFINED`. A revision written after `scenario_at` is absent, never backdated. If `scenario_at` is omitted, resolve it from `clock_timestamp()` within the read snapshot; validate explicit `scenario_at` as UTC and no later than that DB time, returning `COLD_TIME_INVALID` 422 otherwise. Keep the evidence `known_at` independent: it is the selected assessment cutoff, not the authored write clock. Cursor binds the exact selection and last `(recorded_at,id)`; 422 cursor invalid, 409 basis changed. Tests `test_w501_cold_scenarios_postgres.py::test_command_schema_refusals_and_replay`, `::test_pending_historical_list_and_cursor`, `::test_migration_constraints` prove every branch.

## C5 — cold Scenarios, navigation and W2-F L1 (per-unit review)

Read C5, mock caps, C4 DTO, literal ledger. Files: new `frontend/src/sites/ColdScenarios.tsx`, `frontend/src/sites/coldScenariosClient.ts`, `frontend/src/sites/__tests__/coldScenarios.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/src/sites/ColdAssessmentViews.tsx`, `frontend/src/sites/__tests__/coldRoutes.test.tsx`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Page: heading `Scenarios`; panel `Financial scenarios`; empty title `No scenario defined yet`; body `A scenario needs declared assumptions and an authored basis. None has been defined for this site and window.`; notice `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` One-row labels `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, pill `Defined` or `Historical`; `Review assumptions →` expands exact basis locally. Pending notice `Underlying evidence is being reassessed; the authored scenario remains separate.` Refusal `Cold scenarios unavailable`, exact server message and `Retry`. No observed-outcome status/label and no ordinary-viewer create control. In `SiteAnalyticsFrames.FinancialsSections`, render the live cold Scenarios tab when `site_type === COLDCHAIN`; retain `<UnavailableTab label="Scenarios" />` for every other non-mini-grid Site. Replace the cold-only `Scenarios are read for mini-grid sites only.` branch with `ColdScenarios` at `/sites/{site_code}/financials/scenarios`. `siteFinancialScenariosHref` must accept/preserve `from,to,known_at,scenario_at` for cold. `$expectedTabs` retains two `Scenarios`; re-anchor the positive and negative `navigation-rail-fixtures.ps1` checks to both the live cold branch and retained fallback. Registry `(cold-scenarios,1) Financial scenarios` maps C4 list/empty; no observed-outcome technical node is resolved.

**C5 registry row.** C5 alone adds `I-W5-cold-scenario-read` and `I-W5-cold-scenario-ui` nodes (`kind:implementation`, `area:cold-chain`, `status:open`, task W5-01b). The summary panel row is `screen_id:cold-scenarios`, `panel_index:1`, `title:Financial scenarios`, `area:cold-chain`, `requires:[I-W5-cold-scenario-read,I-W5-cold-scenario-ui]`, `status:gap`, `reason:Authored stock-value context is listed without observed loss or an outcome claim.` Test `coldScenarios.test.tsx::authored_pending_historical_basis` verifies the UI and registry guard checks this row.

Fix W2-F L1 in refused cold Finding branch: `StatusBar label="Finding state"` with `Unknown` / `Confidence: Unknown` directly above `PageRefusal`; assert in `coldRoutes.test.tsx::w2f_finding_strip_confidence`. Captures at 1440/390, owned here: `cold-scenarios-empty` (C4 GET before POST), `cold-scenarios-authored` (C4 POST), `cold-scenarios-historical` (C4 correction fixture and saved pre-correction `scenario_at`), `cold-scenarios-pending` (C1 late-reading fixture plus authored row), `cold-scenarios-refused` (C4 access refusal), `cold-finding-refused-unknown` (merged W2-F refusal test). Clocks are C4's returned watermarks; historical uses the saved pre-correction `scenario_at` and/or before-late evidence `known_at`. Expand basis in a capped 390px internal scroller (max 560px panel for one row, separate disclosure cap 360px); long UUIDs break at character boundaries and exact full values remain available. Run the W1 vocabulary scan; wrap raw source IDs with `data-vocabulary-exempt="source-reference"`. Do not run T028 vocabulary over this intentionally named `Scenarios` page. Run `tools/check-all.ps1`, focused tests, mock/app cap pairs, one W5-01b real-Postgres suite, final independent review and merge before W5-02.


### Executable registry and ledger amendment

Apply these exact JSON objects to the registry in the named unit only. Insert each node once; append each panel once. For the three cold screens, set `registry_dependencies.product_node_id` to `P-cold-area` and `registry_dependencies.node_ids` to the ordered unique concatenation of that screen’s panel `requires` arrays. C3 owns cooling and cold-health ledger edits; C5 owns cold-scenarios. Status remains `gap` and nodes remain `open` until independent review.

**C3 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-depth-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-depth-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01a",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C3 — panel rows**

```json
[
  {
    "screen_id": "cooling",
    "panel_index": 1,
    "title": "Recovery curves",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "W5-01a selected first steps do not establish an ordered recovery curve."
  },
  {
    "screen_id": "cooling",
    "panel_index": 2,
    "title": "Context normalization",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Ambient is not selected by the W2 cooling assessment; loading and defrost roles are absent, so those context rows show Unknown."
  },
  {
    "screen_id": "cooling",
    "panel_index": 3,
    "title": "Next best evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Evidence actions are bounded to existing Backup and Temperature destinations."
  },
  {
    "screen_id": "cold-health",
    "panel_index": 1,
    "title": "Condition and evidence",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-depth-read",
      "I-W5-cold-depth-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Selected start and probe observations do not establish physical equipment health."
  }
]
```

C3 ledger `cooling`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

C3 ledger `cold-health`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-depth-read", "I-W5-cold-depth-ui", "D-cold-domain"]}.

**C5 — registry nodes**

```json
[
  {
    "id": "I-W5-cold-scenario-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-cold-scenario-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "cold-chain",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-cold-site-projections",
      "I-W5-cold-scenario-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-01b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**C5 — panel rows**

```json
[
  {
    "screen_id": "cold-scenarios",
    "panel_index": 1,
    "title": "Financial scenarios",
    "area": "cold-chain",
    "requires": [
      "I-W5-cold-scenario-read",
      "I-W5-cold-scenario-ui",
      "D-cold-domain"
    ],
    "status": "gap",
    "reason": "Authored stock-value context is listed without observed loss or an outcome claim."
  }
]
```

C5 ledger `cold-scenarios`: `registry_dependencies` = {"product_node_id": "P-cold-area", "node_ids": ["I-W5-cold-scenario-read", "I-W5-cold-scenario-ui", "D-cold-domain"]}.

## Readiness closure

| Review item | Closing artifact location |
| --- | --- |
| 1 | C1 producer clock |
| 2 | Shared selected read and C1 links |
| 3 | C1/C2 file lists |
| 4 | C3/C5 registry rows |
| 5 | C1 context table |
| 6 | C1 derivation table |
| 7 | Shared selected read provenance |
| 8 | C2 state matrix |
| 9 | C2 breadcrumb rule |
| 10 | C2 live refusal capture |
| 11 | C2 worst-content cap |
| 12 | C2 navigation fixture |
| 13 | C3 condition matrix |
| 14 | C3 Health composition |
| 15 | C3 table deviation |
| 16 | C4 persisted schema |
| 17 | C4 POST and refusals |
| 18 | C4 list and historical predicate |
| 19 | C5 cold Scenarios branch |
| 20 | C5 query preservation |
| 21 | C5 fixture anchors |
| 22 | C5 vocabulary rule |
| 23 | C5 expanded-basis cap |
| 24 | C5 Finding strip test |
| 25 | C4 one-run card |
| 26 | Shared literal ledger |
| 27 | Gate and guards |
| R1 (review 4) | C3/C5 executable node, panel and ledger JSON below; applied together to a scratch registry and the dependency checker passed on 2026-10-22. |
| R2 | C3 keeps the S7 gateway panel and live Foundation link, names tests and composed page caps. |
| R3 | C4 POST and refusal table use merged 422. |
| R4 | C4 revision-1 window rule and cross-window correction refusal. |
| R5 | C1 accepted door-event ledger read and optional ambient-role distinction. |
| R6 | Health enum includes LIMITED; C3 covers zero, one and two selected probes. |
| R7 | C2/C3 client edit ownership and C3/C5 single node creation. |
