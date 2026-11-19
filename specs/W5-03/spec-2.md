## Unit E5 — authored EV scenario store, W5-03b; per-unit review

Allowed authored what-if contract `ev-scenario-authored/1`: the only `kind` is `GROSS_TARIFF_CONTEXT`; the assumption object is exactly `{tariff_per_kwh,currency}` with positive decimal string at most 8 fractional digits and uppercase three-letter ISO 4217 currency. The baseline is the selected W2-07 `ev_session_revision` rows for which `ev_reads.energy_complete(state,supported_kwh,unknown_meter_seconds) is True`, with their exact accepted meter evidence IDs. Persist those session revision IDs and the selected `ev_consequence_revision.id`/tariff revision ID only when a priced consequence exists; no metered-energy table exists. A zero-row complete-meter selection refuses `EV_SCENARIO_INVALID`. There is no computed money amount, collected revenue, lost sales, comparison delta or observed outcome in this contract. Formula version is `AUTHORED_ONLY/1`; scope is one authorized EV Site and one selected half-open UTC period at most 31 days. Cross-Site, currency conversion and a scenario with no exact selected complete `ev_session_revision` are refused as `EV_SCENARIO_INVALID`. This keeps the Scenario tab an authored-basis list while W2-07 continues to own measured energy and eligible gross tariff consequence.

Read: E5, selected contract, merged W4-03 `mini_decisions/scenarios.py` command/actor pattern. Files: **Lane A only** `backend/migrations/versions/0034_w5_ev_scenarios.py`, new `backend/assetops_backend/ev_scenarios/{rules,store,service}.py`, `ev_scenarios_api.py`, `backend/tests/test_w503_ev_scenarios_postgres.py`; shared `backend/assetops_backend/main.py`, `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` (A1Q W5S-7). Migration creates scoped `ev_scenario` and append-only `ev_scenario_revision` with the identity/actor/idempotency/prior/correction/check/composite-Site-FK shape of W5-01 C4. It carries `basis_sha256`, selected session/assessment/accepted evidence/Foundation/tariff revision IDs and assumptions. There is no observed-outcome column, field, enum or status. Unique `(scenario_id,revision_no)` and `(scenario_id,idempotency_key)`; correction appends only. Existing decision principal protects `POST /api/sites/{code}/ev/financials/scenarios` and `POST .../{scenario_id}/revisions`; ordinary viewers have `GET ...?from=&to=&known_at=&scenario_at=&limit=&cursor=`. DTO `ev-scenarios-1`: watermarked scoped list with separate `scenario_at`, immutable revision IDs, `DEFINED` or read-only `HISTORICAL`; default 50/max 100, cursor binds Site/window/evidence cutoff/scenario_at/watermark/last `(recorded_at,id)`. New typed codes: `EV_SCENARIO_INVALID` 422, `EV_SCENARIO_CURSOR_INVALID` 422, `EV_SCENARIO_CURSOR_BASIS_CHANGED` 409, `EV_SCENARIO_IDEMPOTENCY_CONFLICT` 409, `EV_SCENARIO_REVISION_CONFLICT` 409; existing EV access/unavailable codes remain. No default row, inferred tariff, collections, lost revenue, verified outcome or mutable measured consequence. Test migration upgrade/downgrade/sole head after exact `0033_w5_cold_work`, actor scope, idempotency, foreign ID, cutoff/cursor, empty/failed and a real persisted POST. The positive producer for E6 is this POST proved by `test_w503_ev_scenarios_postgres.py` with E1's exact selected IDs; it must pass review before E6. The EV selection uses the E1 09:00/09:05 decision watermark; server scenario `recorded_at` and default `scenario_at` are DB wall time. Save `scenario_at` after first POST, append correction later, and pass saved `scenario_at` to read the prior authored revision. Do not use 16:05/16:07 as a selected evidence cutoff. Independent review gates E6.

**E5 exact persisted schema and wire contract.** Migration `0034_w5_ev_scenarios` first creates `ev_scenario_public_no_seq`, then `ev_scenario` with `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `public_no bigint NOT NULL DEFAULT nextval('ev_scenario_public_no_seq')`, `create_key text NOT NULL`, `create_payload_sha256 text NOT NULL`, `create_actor_id text NOT NULL`, `created_at timestamptz NOT NULL DEFAULT clock_timestamp()`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`; named `ev_scenario_scope_uk(tenant_id,site_id,id)`, `ev_scenario_public_no_uk(tenant_id,public_no)`, `ev_scenario_create_key_uk(tenant_id,site_id,create_key)` and `ev_scenario_site_fk(tenant_id,site_id)` to `site(tenant_id,id)`. Root checks `ev_scenario_create_key_check` length 8..128, `ev_scenario_create_payload_sha256_check` 64 lowercase hex, `ev_scenario_create_actor_id_check` trimmed length 1..128. `ev_scenario_revision` columns: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `scenario_id uuid NOT NULL`, `revision_no integer NOT NULL`, `supersedes_revision_id uuid NULL`, `name text NOT NULL`, `kind text NOT NULL`, `assumptions jsonb NOT NULL`, `authored_basis jsonb NOT NULL`, `basis_sha256 text NOT NULL`, `formula_version text NOT NULL`, `correction_reason text NULL`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`, `authorization_basis text NOT NULL`, `attestation text NOT NULL`, `idempotency_key text NOT NULL`, `payload_sha256 text NOT NULL`, `recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()`. Named checks `ev_scenario_revision_revision_no_check` (>0), `ev_scenario_revision_name_check` (trimmed 1..160), `ev_scenario_revision_kind_check` (`GROSS_TARIFF_CONTEXT`), `ev_scenario_revision_formula_check` (`AUTHORED_ONLY/1`), `ev_scenario_revision_chain_check` (same first/later rule C4), `ev_scenario_revision_basis_sha256_check` and `ev_scenario_revision_payload_sha256_check` (each 64 lowercase hex), `ev_scenario_revision_idempotency_key_check` (length 8..128), `ev_scenario_revision_actor_check` (nonempty actor kind/id/authorization basis/attestation). Named composite scoped FKs are `ev_scenario_revision_scenario_fk(tenant_id,site_id,scenario_id)` and `ev_scenario_revision_previous_fk(tenant_id,site_id,supersedes_revision_id)`; unique constraints are `ev_scenario_revision_scope_uk(tenant_id,site_id,id)`, `ev_scenario_revision_no_uk(scenario_id,revision_no)`, `ev_scenario_revision_previous_uk(scenario_id,supersedes_revision_id)`, `ev_scenario_revision_key_uk(scenario_id,idempotency_key)`. Index `ev_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`. Downgrade removes index, revision, root, then sequence. `0033_w5_cold_work` is a W5-02 naming obligation; W5-02's task must adopt that exact ID before E5 migration runs.

POST root and correction take gate query `from,to,known_at`; `from,to` are required, paired strict UTC and at most 31 days. Optional `known_at` selects evidence within the write snapshot. Unknown/repeated query keys use `EV_PARAMETER_UNKNOWN` 422. No body pin can override selected Site or window. Server-resolved `authored_basis` JSON has closed keys `{from,to,cutoff,assessment_revision_id,session_revision_ids,accepted_evidence_ids,foundation_revision_id,consequence_revision_id,tariff_revision_id,source_provenance}`; last two IDs are nullable, and all selected UUID lists are sorted/deduplicated. SQL checks require assumptions/basis to be JSON objects; exact key grammar and selected-ID membership are service rules. Root `create_payload_sha256` hashes canonical command and query/window for same-key replay.

**Metered-energy baseline table (test `test_w503_ev_scenarios_postgres.py::test_complete_session_baseline`).**

| Stored basis field | Exact merged source | Refusal / null rule |
| --- | --- | --- |
| `session_revision_ids` | selected `ev_session_revision.id` where `ev_reads.energy_complete(state,supported_kwh,unknown_meter_seconds) is True` | empty → 422 `EV_SCENARIO_INVALID`; never use an incomplete meter row |
| `accepted_evidence_ids` | accepted meter evidence IDs cited by those selected session revisions | empty/foreign → 422 `EV_SCENARIO_INVALID` |
| `assessment_revision_id` | selected W2-06 EV assessment revision | absent → 422 `EV_SCENARIO_INVALID` |
| `foundation_revision_id` | effective selected EV Foundation | absent/foreign → 422 `EV_SCENARIO_INVALID` |
| `consequence_revision_id`, `tariff_revision_id` | selected W2-07 `ev_consequence_revision` and its cited tariff revision if eligible | nullable; no priced consequence is invented |
| `cutoff` | selected snapshot's returned `known`/`committed_watermark` (09:00/09:05 only in the fixed E1 fixture) | later than current watermark → 422 `EV_TIME_INVALID` |

**E5 review ruling on the baseline (2026-10-23, controlling the earlier currency-conversion sentence and the table's “foreign” wording).** An eligible current priced consequence has a selected tariff currency. An authored currency different from it is refused; with null priced IDs, any syntactically valid authored currency is permitted and the money IDs stay null. No amount or conversion is calculated. A meter ID is foreign if it is missing from either the window's accepted set at the cutoff or the selected assessment head's cited `evidence_ids`; compare normalized UUIDs and refuse the complete command rather than shrinking the stored list. A Foundation is valid only if its resolved revision is present in the selected head's nonempty `foundation_ids`.

POST root closed body `{schema_version:"ev-scenario-command-1",idempotency_key:string,actor:{kind:"SERVICE",id:string,attestation:string},name:string,kind:"GROSS_TARIFF_CONTEXT",assumptions:{tariff_per_kwh:string,currency:string}}`; correction adds `supersedes_revision_id` UUID and `correction_reason` 1..2000. Server resolves exact complete `ev_session_revision` rows and selected IDs within the write snapshot. No client pin/basis field. Missing/non-SERVICE principal or wrong scope/grant → 403 `DECISION_WRITE_FORBIDDEN`; USER actor → 403 `DECISION_USER_AUTH_REQUIRED`; bad attestation → 422 `DECISION_ATTESTATION_INVALID` (merged `mini_decisions/model.py:34`); missing exact complete sessions or invalid assumptions/basis → 422 `EV_SCENARIO_INVALID`; same key/different body → 409 `EV_SCENARIO_IDEMPOTENCY_CONFLICT`; stale prior → 409 `EV_SCENARIO_REVISION_CONFLICT`; store unavailable → 503 `DECISION_STORE_UNAVAILABLE` or `EV_READ_UNAVAILABLE`; read gate retains `UNAUTHENTICATED`, `SITE_SCOPE_FORBIDDEN`, `SITE_NOT_FOUND`, `EV_SOURCE_DISCLOSURE_FORBIDDEN`. New write returns 201 `{schema_version:"ev-scenario-write-1",id,code:"ESCN-000001",revision_id,revision_no}`; exact replay returns 200 same body. Public number uses global `ev_scenario_public_no_seq`, `ESCN-` plus six minimum zero-padded decimal digits.

| E5 refusal | HTTP | Trigger |
| --- | ---: | --- |
| `UNAUTHENTICATED` | 401 | Missing authenticated request |
| `SITE_SCOPE_FORBIDDEN`, `EV_SOURCE_DISCLOSURE_FORBIDDEN` | 403 | Site or source disclosure denied |
| `DECISION_WRITE_FORBIDDEN`, `DECISION_USER_AUTH_REQUIRED` | 403 | Service principal or actor rejected |
| `DECISION_ATTESTATION_INVALID` | 422 | Malformed service attestation |
| `SITE_NOT_FOUND` | 404 | No authorized EV Site |
| `DECISION_NOT_FOUND` — `No decision with this ID at this Site.` | 404 | Correction root ID is malformed, unknown or foreign to this Site |
| `EV_PARAMETER_UNKNOWN`, `EV_TIME_INVALID`, `EV_WINDOW_INVALID`, `EV_WINDOW_TOO_LONG`, `EV_SCENARIO_CURSOR_INVALID` | 422 | Query, time, window or cursor invalid |
| `EV_LIMIT_INVALID` — `'limit' must be 1 to 100.` | 422 | Explicit list limit is malformed, non-ASCII, zero or above 100 |
| `EV_SCENARIO_INVALID` — `The EV scenario request or selected basis is invalid.` | 422 | Invalid body/basis, absent or foreign Foundation, missing complete sessions, empty meter set, or meter ID outside either selected citation or accepted evidence |
| `EV_SCENARIO_INVALID` — `The authored currency must match the selected priced tariff currency.` | 422 | Priced consequence and tariff selected, but authored currency differs; same-currency and unpriced commands do not refuse |
| `DECISION_LINK_SCOPE_INVALID` — `A cited or linked ID is outside this Site or basis.` | 422 | Syntactically valid correction predecessor ID is outside the scoped root; malformed predecessor UUID uses `EV_SCENARIO_INVALID` |
| `EV_SCENARIO_CURSOR_BASIS_CHANGED`, `EV_SCENARIO_IDEMPOTENCY_CONFLICT`, `EV_SCENARIO_REVISION_CONFLICT` | 409 | Changed selection, replay body or predecessor |
| `EV_READ_UNAVAILABLE` | 503 | Selected read unavailable |
| `DECISION_STORE_UNAVAILABLE` — `Decision records could not be read or saved.` | 503 | Authored store unavailable, malformed stored root/candidate basis, or a second serialization/unique race after one retry; never return a partial list or write |

The non-refusal side of A1/A4 is also fixed: `scenario_money_on(c,snap)` selects the eligible **current** W2-07 priced head on the same E5 write connection, and the migration index remains `(tenant_id,site_id,recorded_at DESC,id)` while list/cursor order is `(recorded_at DESC,id DESC)`. The evidence watermark is not a DB recorded-time cutoff. Tests pin eligible and null money IDs, the index definition and equal-time pagination. E5 correction tests pin the exact root/predecessor codes above and zero writes on refusal. `test_complete_session_baseline` pins absent/foreign Foundation and both forms of foreign meter evidence with zero writes. The list tests pin malformed persisted root/candidate 503, a 51-root default page of 50 then one, and the one-retry/two-race store behavior. These additions are required before E5 review acceptance; see `.agent/W5-03b-e5-rulings.md`.

GET list `ev-scenarios-1` is `{schema_version,site_id,window:{from,to,known_at,committed_watermark},scenario_at,selection:{state,assessment_revision_id,session_revision_ids,accepted_evidence_ids,source_provenance},items:[{id,code,revision_id,revision_no,name,kind,assumptions,authored_basis,recorded_at,scenario_state}],next_cursor}`. Pending comes from the selected W2 EV assessment `selection.state`; historical follows the EV precedence of `ev_reads.currentness_state`. Revision 1 `authored_basis.from,to` fixes each root window. A correction resolves its query `from,to` and must equal revision 1 exactly; mismatch returns 422 `EV_SCENARIO_INVALID` before append. Test same-window correction and cross-window refusal. Include only roots whose revision 1 `authored_basis.from,to` equals requested period; choose latest revision where `recorded_at <= scenario_at` and `authored_basis.cutoff <= window.known_at`. `scenario_state=HISTORICAL` iff superseded at current authored DB time or caller `scenario_at` precedes the latest stored revision or `known_at` precedes the current evidence watermark; else `DEFINED`. If `scenario_at` is omitted, resolve DB `clock_timestamp()` in the read snapshot; explicit UTC `scenario_at` after DB now refuses 422 `EV_TIME_INVALID`. The 09:00/09:05 evidence clock is independent of DB authored time; current authored rows remain visible even when the selected evidence watermark is 09:00. Cursor binds Site/window/evidence cutoff/scenario_at/watermark/last row and returns 422 invalid or 409 changed basis. Tests `test_w503_ev_scenarios_postgres.py::test_command_refusals_and_replay`, `::test_pending_historical_list_and_cursor`, `::test_schema_constraints`.

**E5 guard and composition ownership (A1Q W5S-7/W5S-8/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** `ev_scenarios/store.py` is a new product database writer. Apply the rule-8 policy text from W5-01 C4 "C4 guard and composition ownership" (`.agent/W5-01-build-spec.md`, steps 1–9) to `configuration-persistence.ps1` and `writer_guard_probes.py`, with exactly these substitutions:

| W5-01 C4 text | E5 text |
| --- | --- |
| `W5-01b C4 (migration 0032)` | `W5-03b E5 (migration 0034)` |
| `$coldScenarioWriter` | `$evScenarioWriter` |
| `$coldScenarioTables` | `$evScenarioTables` |
| `$coldScenarioInsertsSeen` | `$evScenarioInsertsSeen` |
| `cold_scenarios/store.py` | `ev_scenarios/store.py` |
| `'cold_scenario', 'cold_scenario_revision'` | `'ev_scenario', 'ev_scenario_revision'` |
| message words `cold scenario` / `Cold scenario` | `EV scenario` / `EV scenario` |
| probe prefix `cold-scenario` | `ev-scenario` |
| `COLD_SCENARIO` | `EV_SCENARIO` |
| `_cold_scenario_only` / `_cold_scenario_unseen` | `_ev_scenario_only` / `_ev_scenario_unseen` |
| truncate probe `"TRUNCATE cold_scenario"` | `"TRUNCATE ev_scenario"` |

Insert every E5 block directly after the corresponding C4 block. If W5-01b has not merged when E5 runs, insert after the mini-decision block instead. `ev_scenarios_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

Lane A wiring in `main.py`: add the imports `EvScenarioService`, `PostgresEvScenarioStore` and `build_ev_scenarios_router`, and after the E1b mount add:

```python
    # W5-03b E5: authored EV scenarios. Writes need the two explicit decision injections; reads use the EV gate.
    ev_scenario_store = PostgresEvScenarioStore.from_url(database_url()) if ev_reads is not None else None
    if ev_scenario_store is not None:
        app.router.on_shutdown.append(ev_scenario_store.dispose)
    app.include_router(build_ev_scenarios_router(
        registry, None if ev_scenario_store is None else EvScenarioService(ev_scenario_store, ev_reads),
        command_access=mini_decision_command_access, principal=mini_decision_principal))
```

The service resolves eligible `ev_consequence_revision` and tariff IDs through the new public caller-connection `EvSiteReads` method inside the store's write snapshot. That method reuses W2-07 selection and guard policy; the E5 store does not duplicate the money predicate or import a `financials` adapter. Add `backend/assetops_backend/ev_site_reads.py` and `backend/assetops_backend/analytics/adapters/postgres_assessment_store.py` to E5 Lane A ownership, together with the 18 sole-head tests in the pre-flight section below.

## Unit E6 — EV Scenarios page and W5-03b close; per-unit review

**Build-time correction, controlling earlier E6 text (rulings 18, 20).** `App.tsx` injects the authored-list `evScenarioList?: EvScenariosClient` into `SiteEvFrame`/`EvSiteFrame` as `evScenarios`/`scenarios`. The existing `evScenarios?: EvScenarioChoiceClient` remains the Lab run-setup choice prop. In the expanded `Accepted evidence` row, count `authored_basis.accepted_evidence_ids`: `n=1` displays exactly `1 record`; every other count displays `{n} records`. Assert both branches in `evScenarios.test.tsx`. The mock's sole `Financial scenarios` panel and empty illustration remain the E6 screen reference (`index.html:859–862`); R27 covers populated authored rows.

Read: E6, measurement table, E5 DTO and literal page copy below. Files: new `frontend/src/sites/EvScenarios.tsx`, `frontend/src/sites/evScenarios.css`, `frontend/src/sites/evScenariosClient.ts`, `frontend/src/sites/__tests__/evScenarios.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/sites/EvSiteViews.tsx`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `frontend/src/shell/evSiteRoutes.tsx`, `frontend/src/sites/__tests__/evSiteMoneyRoutes.test.tsx`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Replace the EV `<UnavailableTab label="Scenarios" />` in `EvSiteViews.tsx` after `/sites/{site_code}/ev/financials/scenarios` is live; leave the shared non-EV fallback without editing `SiteAnalyticsFrames.tsx`. Preserve `from,to,known_at` throughout Financials and `scenario_at` on the Scenarios entry only. Registry `(ev-scenarios,1) Financial scenarios` maps E5 authored list/empty; add no observed-outcome technical node. Captures are in E6, the page-owning unit.

Page literals: h1 is the selected Site name; subtitle `Financials · scenarios (placeholder)`; panel `Financial scenarios` with icon/meta `Placeholder · to be designed with the owner`; empty title `No scenario defined yet`; body `A scenario compares a declared what-if with the measured case, for example a different stop setting, stock value or tariff. None has been defined for this site.`; blue notice `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` Persisted rows replace only the empty block (R27 D2). Row labels are `Authored scenario`, `Assumptions`, `Basis`, `Defined at`; `Defined` or `Historical`; `Review assumptions →` expands the stored basis. Pending notice `Underlying evidence is being reassessed; the authored scenario remains separate.` Refusal heading `EV scenarios unavailable`, exact server error and `Retry`. No create control for ordinary viewer.

**E6 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evScenarios.test.tsx::routes_states_loading`).**

**E6 scenario row, page and client (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `evScenarios.test.tsx::row_disclosure_and_client`).**
- **Page frame.** Breadcrumb `Sites › {Site name} › Financials › Scenarios`; h1 `{Site name}`. Use a screen-scoped description override `Financials · scenarios (placeholder)` without changing shared `SITE_SCREEN_DESCRIPTIONS.scenarios` or `V69Layout.tsx`.
- **Item table.** Items render in one `DataTable` inside `Financial scenarios`, with columns `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, `State` and one row per `items[]` entry in DTO order.
  - `Authored scenario`: `name`, then on a second line `code` and `revision {revision_no}`, the code inside `data-vocabulary-exempt="source-reference"`.
  - `Assumptions`: `{tariff_per_kwh} {currency}/kWh gross tariff`. Decimal strings are printed verbatim.
  - `Basis`: `Selected evidence through {cutoff}`, with `cutoff` formatted `YYYY-MM-DD HH:MM UTC`, then a `<button type="button" aria-expanded>` labelled `Review assumptions →`.
  - `Defined at`: `recorded_at` as `YYYY-MM-DD HH:MM UTC`.
  - `State`: a neutral `Badge` whose text comes from `scenario_state`: `DEFINED` → `Defined`, `HISTORICAL` → `Historical`.
- **`Review assumptions →` expansion.** A full-width row directly below its item, scrolled internally at 390 (360px cap). It is a `<dl>` with these terms in order, every ID in a `data-vocabulary-exempt="source-reference"` span with character breaks and one ID per line:
  - `Kind` → `GROSS_TARIFF_CONTEXT`
  - `Assumptions` → each key and value, one per line: tariff_per_kwh,currency
  - `Window` → `authored_basis.from` – `authored_basis.to` (ISO, verbatim)
  - `Evidence cutoff` → `authored_basis.cutoff`
  - `Assessment revision` → `authored_basis.assessment_revision_id`
  - `Session revisions` → `authored_basis.session_revision_ids`
  - `Accepted evidence` → `1 record` for `n=1`, otherwise `{n} records`, then each `authored_basis.accepted_evidence_ids` entry; `n` is that ID array's length. Assert singular and plural in `evScenarios.test.tsx`.
  - `Foundation revision` → `authored_basis.foundation_revision_id`
  - `Consequence revision` → `authored_basis.consequence_revision_id`
  - `Tariff revision` → `authored_basis.tariff_revision_id`
  - `Source classification` → `authored_basis.source_provenance.classification`
  - `Revision` → `revision_id`
  A null ID prints `None`.
- **Client.** `frontend/src/sites/evScenariosClient.ts` validation; any violation is the unavailable state.
  - Top level: exact keys `schema_version` (`"ev-scenarios-1"`), `site_id`, `window` (exact `from,to,known_at,committed_watermark`), `scenario_at`, `selection` (exact `state,assessment_revision_id,session_revision_ids,accepted_evidence_ids,source_provenance`), `items`, `next_cursor` (string or null).
  - Item: exact keys `id`, `code` (matches `^ESCN-\d{6,}$`), `revision_id`, `revision_no` (integer ≥ 1), `name` (string of 1–160 characters), `kind` (`"GROSS_TARIFF_CONTEXT"`), `assumptions` (exact keys `tariff_per_kwh,currency`, all strings, `currency` matching `^[A-Z]{3}$`), `authored_basis` (exact keys `from,to,cutoff,assessment_revision_id,session_revision_ids,accepted_evidence_ids,foundation_revision_id,consequence_revision_id,tariff_revision_id,source_provenance`), `recorded_at` (string), `scenario_state` (`DEFINED` or `HISTORICAL`).
  - `selection.state` is one of the five STATES.
- **Refusal heading.** `EV scenarios unavailable`.
- **Routes.** `operatorSiteRoutes.ts`: `SITE_EV_SUFFIX` gains `scenarios: "/financials/scenarios"`.
  - `EvSiteViews.tsx`: `EvSiteRoutes` gains `scenarios: string`; `EvSiteView` gains `"scenarios"`. The Financials subtab list replaces `<UnavailableTab label="Scenarios" />` with a live `["scenarios", "Scenarios", sel(routes.scenarios, window)]` entry, carrying `scenario_at` when present.
  - `shell/evSiteRoutes.tsx`: add `scenarios: siteEvHref(siteId, "scenarios"),` and `CURRENT_TAB.scenarios = "Financials"`.
- **Currentness.** The EV ledger state sentences apply, except `PENDING_RECOMPUTE`, which keeps the E6 pending notice.
- **Copy.** Loading, unavailable and refusal follow the shared section.
- **Captures.** `ev-scenarios-refused` is the shared 422 `from>to` refusal.
- **Depends on.** E5 merged review.

E6 adds registry node `I-W5-ev-scenario-read` and `I-W5-ev-scenario-ui` (`kind:implementation`, `area:ev`, `status:open`, task W5-03b) and summary row `screen_id:ev-scenarios`, `panel_index:1`, `title:Financial scenarios`, `area:ev`, `requires:[I-W5-ev-scenario-read,I-W5-ev-scenario-ui]`, `status:gap`, `reason:Authored tariff context is listed separately from selected metered energy and any observed outcome.` Exact basis disclosure is internally scrolled at 390; the one-row panel cap does not cap unlimited expanded text. Test `evScenarios.test.tsx::basis_disclosure_and_pending_historical`.

Captures: `ev-scenarios-empty` (GET before POST), `ev-scenarios-authored` (new POST), `ev-scenarios-historical` (correction and saved pre-correction `scenario_at`), `ev-scenarios-pending` (late-record builder with authored row), `ev-scenarios-refused` (gate), at 1440/390. Positive producer is the new persisted command path proved by `test_w503_ev_scenarios_postgres.py`; its seed uses E1's exact selected EV IDs. Use the E1 09:00/09:05 evidence watermark and the saved pre-correction `scenario_at`; no 16:05 pin. Expanded basis has a 360px internal scroller, exact full IDs with character breaks, and its own 390 capture. Run the W1 vocabulary scan, exempt raw IDs using `data-vocabulary-exempt="source-reference"`; do not apply T028 vocabulary to a page whose title is `Scenarios`. UI tests assert empty, authored, historical, pending and refused copy, exact basis disclosure, no invented outcome and no dead links. Run focused tests, `tools/check-all.ps1`, one W5-03b full real-Postgres suite, 1440/390 caps, independent review/merge before W5-04.

### Executable registry and ledger amendment

Apply these exact JSON objects to the registry in the named unit only. Insert each node once; append each panel once. For the four EV screens, set `registry_dependencies.product_node_id` to `P-ev-area` and `registry_dependencies.node_ids` to the ordered unique concatenation of that screen’s panel `requires` arrays. E3 owns availability and energy ledger edits; E4 owns ev-health; E6 owns ev-scenarios. Status remains `gap` and nodes remain `open` until independent review.

**E3 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-depth-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-03a",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-ev-depth-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections",
      "I-W5-ev-depth-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03a",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps, 1440/390 captures and preserved gateway panel where applicable."
  }
]
```

**E3 — panel rows**

```json
[
  {
    "screen_id": "availability",
    "panel_index": 1,
    "title": "Connector states over the service schedule",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Selected connector states cover only cadence-bounded scheduled spans; gaps remain Unknown."
  },
  {
    "screen_id": "availability",
    "panel_index": 2,
    "title": "Full-schedule availability bound",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Bounds require a selected schedule and accepted state coverage; missing status remains Unknown."
  },
  {
    "screen_id": "availability",
    "panel_index": 3,
    "title": "Most useful next evidence",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "The selected status gap identifies needed source history, not physical availability."
  },
  {
    "screen_id": "energy",
    "panel_index": 1,
    "title": "Import power and configured limit",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Accepted import samples and configuration do not establish a causal site-power limit."
  },
  {
    "screen_id": "energy",
    "panel_index": 2,
    "title": "What can be concluded",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Requested and allocated power evidence is absent; limit causation remains Unknown."
  },
  {
    "screen_id": "energy",
    "panel_index": 3,
    "title": "Technical-to-financial bridge",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-depth-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Gross tariff consequence is bounded; billing settlement and lost sales are unsupported."
  }
]
```

E3 ledger `availability`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-depth-ui", "D-ev-domain"]}.

E3 ledger `energy`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-depth-ui", "D-ev-domain"]}.

**E4 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-health-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps and 1440/390 captures."
  }
]
```

**E4 — panel rows**

```json
[
  {
    "screen_id": "ev-health",
    "panel_index": 1,
    "title": "Condition and evidence",
    "area": "ev",
    "requires": [
      "I-W5-ev-depth-read",
      "I-W5-ev-health-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Selected faults warrant investigation but do not diagnose charger condition."
  }
]
```

E4 ledger `ev-health`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-depth-read", "I-W5-ev-health-ui", "D-ev-domain"]}.

**E6 — registry nodes**

```json
[
  {
    "id": "I-W5-ev-scenario-read",
    "kind": "implementation",
    "layer": "projection",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections"
    ],
    "effort": "M",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed selected read with exact evidence lineage and bounded unknown states."
  },
  {
    "id": "I-W5-ev-scenario-ui",
    "kind": "implementation",
    "layer": "ui",
    "area": "ev",
    "owner": "Implementer / Reviewer",
    "status": "open",
    "requires": [
      "A-ev-site-projections",
      "I-W5-ev-scenario-read"
    ],
    "effort": "S",
    "evidence": null,
    "task": "W5-03b",
    "acceptance_target": "Reviewed v6.9 route with selected read, honest gaps and 1440/390 captures."
  }
]
```

**E6 — panel rows**

```json
[
  {
    "screen_id": "ev-scenarios",
    "panel_index": 1,
    "title": "Financial scenarios",
    "area": "ev",
    "requires": [
      "I-W5-ev-scenario-read",
      "I-W5-ev-scenario-ui",
      "D-ev-domain"
    ],
    "status": "gap",
    "reason": "Authored tariff context is listed separately from selected metered energy and any observed outcome."
  }
]
```

E6 ledger `ev-scenarios`: `registry_dependencies` = {"product_node_id": "P-ev-area", "node_ids": ["I-W5-ev-scenario-read", "I-W5-ev-scenario-ui", "D-ev-domain"]}.

