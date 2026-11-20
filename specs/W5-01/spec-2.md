## C4 — authored cold scenario store (W5-01b; per-unit review)

Allowed authored what-if contract `cold-scenario-authored/1`: the only `kind` is `STOCK_VALUE_CONTEXT`; the only assumption object is `{stock_quantity,stock_unit,unit_value,currency}` with quantity and value decimal strings greater than zero and at most 8 fractional digits, `stock_unit` a nonempty 1–32 character label, and `currency` a three-letter uppercase ISO 4217 code. The baseline is the selected observed W2 cold window and its accepted IDs, **not** a matched counterfactual; there is no calculated amount, spoilage rule, comparison delta or outcome. Scenario scope is exactly one authorized Site and selected half-open UTC period of at most 31 days; cross-Site scenarios and currency conversion are refused as `COLD_SCENARIO_INVALID`. Formula version is `AUTHORED_ONLY/1` and must be stored. This deliberately implements a reviewable authored scenario list without claiming a financial translation that the selected evidence cannot support.

Read C4, shared contract, merged `mini_decisions/scenarios.py` command/actor pattern. Files: **Lane A only** `backend/migrations/versions/0032_w5_cold_scenarios.py`, new `backend/assetops_backend/cold_scenarios/{rules,store,service}.py`, `cold_scenarios_api.py`, `backend/tests/test_w501_cold_scenarios_postgres.py`; shared `backend/assetops_backend/main.py`, `backend/assetops_backend/analytics/cold_depth.py` (adds `basis_on` only), `tools/checks/configuration-persistence.ps1` and `tools/writer_guard_probes.py` (rule-8 writer policy below). Migration creates scoped `cold_scenario` (tenant/site/id, public_no, actor, created_at) and append-only `cold_scenario_revision` (id, scenario, revision_no, prior, recorded_at, actor, idempotency_key, name max 160, assumptions JSON, authored basis JSON, basis_sha256, correction reason). Composite Site FK, unique `(scenario_id,revision_no)` and `(scenario_id,idempotency_key)`; never rewrite a revision. Authored basis includes half-open window, exact selected W2 assessment revision IDs, accepted evidence IDs, Foundation revision ID, cutoff and source class. No observed-outcome column, enum, field or status. Correction appends. Same key/body returns same ID; same key/different body is 409 `COLD_SCENARIO_IDEMPOTENCY_CONFLICT`; stale predecessor 409 `COLD_SCENARIO_REVISION_CONFLICT`; invalid input 422 `COLD_SCENARIO_INVALID`; existing cold access/503 codes apply. Ordinary viewer has `GET /api/sites/{site_code}/cold/financials/scenarios?from=&to=&known_at=&scenario_at=&limit=&cursor=`; POST same path and `POST .../{scenario_id}/revisions` require existing decision principal/actor policy. List DTO `cold-scenarios-1` has window/watermark, scenario_at, selection, items, next_cursor; row fields `id`, `revision_id`, `name`, `assumptions`, `authored_basis`, `recorded_at`, `scenario_state` (`DEFINED` or read-only `HISTORICAL`) and exact source IDs. No observed outcome field. Default 50/max 100; cursor binds tenant/Site/window/evidence cutoff/scenario_at/watermark/last `(recorded_at,id)`; invalid 422 `COLD_SCENARIO_CURSOR_INVALID`, changed basis 409 `COLD_SCENARIO_CURSOR_BASIS_CHANGED`. Watermarked empty means no authored row in scope, not failed read. Tests prove migration/downgrade/sole head, auth, replay, foreign IDs, cutoff, cursor, store failure and no revenue/spoilage/savings claim. Persisted positive producer is this new POST exercised by `test_w501_cold_scenarios_postgres.py` with exact C1 selected IDs; it must exist and pass at C4 review before C5 captures. Use the C1 returned evidence watermark for basis selection, and DB `clock_timestamp()` for authored `recorded_at`/default `scenario_at`. The new POST producer saves `scenario_at` after first write, then appends correction at a later DB instant; historical list passes saved `scenario_at`. The clocks remain distinct response fields. Never compare a 2026 evidence event timestamp to a present-day authored row. Review C4 before C5.

**C4 exact persisted schema and wire contract.** Migration `0032_w5_cold_scenarios` first creates `cold_scenario_public_no_seq`, then `cold_scenario`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `public_no bigint NOT NULL DEFAULT nextval('cold_scenario_public_no_seq')`, `create_key text NOT NULL`, `create_payload_sha256 text NOT NULL`, `create_actor_id text NOT NULL`, `created_at timestamptz NOT NULL DEFAULT clock_timestamp()`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`; named constraints `cold_scenario_scope_uk UNIQUE(tenant_id,site_id,id)`, `cold_scenario_public_uk UNIQUE(tenant_id,public_no)`, `cold_scenario_create_key_uk UNIQUE(tenant_id,site_id,create_key)`, and named `cold_scenario_site_fk` on `(tenant_id,site_id)` to `site(tenant_id,id)`. Root checks `cold_scenario_create_key_check` length 8..128, `cold_scenario_create_payload_sha256_check` 64 lowercase hex, `cold_scenario_create_actor_id_check` trimmed length 1..128. `cold_scenario_revision`: `id uuid PK`, `tenant_id uuid NOT NULL`, `site_id uuid NOT NULL`, `scenario_id uuid NOT NULL`, `revision_no integer NOT NULL`, `supersedes_revision_id uuid NULL`, `name text NOT NULL`, `kind text NOT NULL`, `assumptions jsonb NOT NULL`, `authored_basis jsonb NOT NULL`, `basis_sha256 text NOT NULL`, `formula_version text NOT NULL`, `correction_reason text NULL`, `actor_kind text NOT NULL`, `actor_id text NOT NULL`, `authorization_basis text NOT NULL`, `attestation text NOT NULL`, `idempotency_key text NOT NULL`, `payload_sha256 text NOT NULL`, `recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()`. Checks: `cold_scenario_revision_revision_no_check` (>0), `cold_scenario_revision_name_check` (trimmed length 1..160), `cold_scenario_revision_kind_check` (`STOCK_VALUE_CONTEXT`), `cold_scenario_revision_formula_check` (`AUTHORED_ONLY/1`), `cold_scenario_revision_chain_check` (revision 1 has null prior/reason; later revision has nonnull prior and trimmed reason length 1..2000), `cold_scenario_revision_basis_sha256_check` and `cold_scenario_revision_payload_sha256_check` (each 64 lowercase hexadecimal characters), `cold_scenario_revision_idempotency_key_check` (length 8..128), `cold_scenario_revision_actor_check` (nonempty actor kind/id/authorization basis/attestation). Named FKs `cold_scenario_revision_scenario_fk` `(tenant_id,site_id,scenario_id)` to scoped root, `cold_scenario_revision_previous_fk` `(tenant_id,site_id,supersedes_revision_id)` to scoped revision; named unique `cold_scenario_revision_scope_uk(tenant_id,site_id,id)`, `cold_scenario_revision_no_uk(scenario_id,revision_no)`, `cold_scenario_revision_previous_uk(scenario_id,supersedes_revision_id)`, `cold_scenario_revision_key_uk(scenario_id,idempotency_key)`. Index `cold_scenario_site_order(tenant_id,site_id,recorded_at DESC,id)`. Downgrade removes index, revision, root, then sequence. Basis JSON is server-resolved inside the write snapshot; client cannot choose IDs or cutoff. **Basis source read (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** C4 adds the public method `ColdDepthReadService.basis_on(c, t, s, code, lo, hi, known_at) -> dict` to `backend/assetops_backend/analytics/cold_depth.py`, a shared file added to the C4 file list. It composes only C1 pieces on the caller's connection `c`: `_selected` (including the 422 future `known_at` check), `_head`, and `ColdReadService.foundation_on(c, snap)`. It returns `{"window": head["window"], "selection": head["selection"], "authored_basis": {"from": window.from, "to": window.to, "cutoff": window.known_at, "assessment_revision_ids": selection.assessment_revision_ids, "accepted_evidence_ids": selection.accepted_evidence_ids, "foundation_revision_id": foundation["revision_id"] or null, "source_provenance": selection.source_provenance}}`. `cold_scenarios/store.py` calls it with its own write-transaction connection for POST, and with its read connection for the GET list's `window` and `selection`. POST returns 422 `COLD_SCENARIO_INVALID` when `assessment_revision_ids` is `[]` or `foundation_revision_id` is null. Test: `test_w501_cold_scenarios_postgres.py::test_command_schema_refusals_and_replay` asserts that the stored `authored_basis` equals `basis_on` on the backup-failed replay window.

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

**C4 guard and composition ownership (A1Q W5S-3/W5S-4/W5S-9; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively).** `cold_scenarios/store.py` is a new product database writer. Without the policy below, rule 8 fails with "Database driver imported outside" and "A second product database writer". `cold_scenarios_api.py` contains none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication` (`authored_basis` is allowed; `configuration-persistence.ps1` HTTP scan, A1Q W5S-9).

**C4 rule-8 writer policy (literal).**

1. **Writer and tables.** In `tools/checks/configuration-persistence.ps1`, after line 823 (`foreach ($table in $decisionTables) { $decisionInsertsSeen[$table] = 0 }`), insert:

   ```powershell
   # W5-01b C4 (migration 0032): the authored cold scenario store is the sole runtime writer of the two 0032 tables,
   # INSERT-only (no UPDATE, DELETE, upsert, TRUNCATE, MERGE, COPY or DDL), and it writes no other table. Each table
   # keeps at least one owner INSERT in the store (anti-vacuity below).
   $coldScenarioWriter = "$backendRoot/cold_scenarios/store.py"
   $coldScenarioTables = @('cold_scenario', 'cold_scenario_revision')
   $coldScenarioInsertsSeen = @{}
   foreach ($table in $coldScenarioTables) { $coldScenarioInsertsSeen[$table] = 0 }
   ```

2. **Writer tallies.** Append `$coldScenarioWriter` as the last element of `$pgWriters`. Append `; $coldScenarioWriter = 0` inside the `$pgWritesSeen` literal and `; $coldScenarioWriter = $false` inside the `$pgDriverSeen` literal.

3. **Forbidden-line check.** After the mini-decision forbidden-line block (`:938-941`), insert:

   ```powershell
               if ($module.Path -eq $coldScenarioWriter -and $line -match $actionForbidden) {
                   $failures.Add("The cold scenario store never updates, deletes, truncates, upserts or runs DDL; " +
                       "$($module.Path):${lineNumber}: $($line.Trim()).") | Out-Null
               }
   ```

4. **Statement check.** After the mini-decision statement block (`:1080-1095`), insert:

   ```powershell
                   if ($module.Path -eq $coldScenarioWriter -and -not (
                           $line -match '(?i)\bINSERT\s+INTO\s+([a-z_]+)\s*\(' -and $coldScenarioTables -contains $Matches[1].ToLowerInvariant())) {
                       $failures.Add(("The cold scenario store only inserts into $($coldScenarioTables -join ', ') " +
                           "(append-only); $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                   }
                   if ($null -ne $target -and $coldScenarioTables -contains $target) {
                       if ($module.Path -ne $coldScenarioWriter) {
                           $failures.Add(("Only $coldScenarioWriter writes cold scenario table '$target'; " +
                               "$($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                       } elseif ($line -notmatch '(?i)^INSERT\s+INTO\b' -or $line -match '(?i)\bON\s+CONFLICT\b') {
                           $failures.Add(("Cold scenario table '$target' is insert-only: no UPDATE, DELETE, TRUNCATE, " +
                               "MERGE, COPY or upsert from any module; $($module.Path):${lineNumber}: $($line.Trim()).")) | Out-Null
                       } else {
                           $coldScenarioInsertsSeen[$target]++
                       }
                   }
   ```

5. **Anti-vacuity.** After the mini-decision anti-vacuity loop (`:1315-1320`), insert:

   ```powershell
       foreach ($table in $coldScenarioTables) {
           if ($extractorRan -and $coldScenarioInsertsSeen[$table] -lt 1) {
               $failures.Add(("Rule 8 found no INSERT INTO $table in $coldScenarioWriter, so the cold scenario insert-only " +
                   "check is vacuous. Update the check, do not delete it.")) | Out-Null
           }
       }
   ```

6. **Probe names.** After the mini-decision probe names (`:1486-1491`), insert:

   ```powershell
       # W5-01b C4: the cold scenario writer policy fails closed the same way.
       foreach ($table in $coldScenarioTables) {
           $workProbeNames += @("controls cold-scenario $table insert", "cold-scenario $table foreign insert",
               "cold-scenario $table update", "cold-scenario $table delete", "cold-scenario $table upsert",
               "cold-scenario $table owner insert unseen")
       }
       $workProbeNames += @('cold-scenario truncate')
   ```

7. **Probe corpus.** In `tools/writer_guard_probes.py`:

   - after `DECISION = f"{B}/mini_decisions/store.py"`, add `COLD_SCENARIO = f"{B}/cold_scenarios/store.py"`;
   - add one docstring `Sets:` bullet: ``- `cold-scenario <table> ...`: W5-01b C4 (migration 0032) two cold scenario tables, the same family as `decision`, owned by `cold_scenarios/store.py`; `cold-scenario truncate`; `controls cold-scenario <table> insert` must pass.``;
   - after the `decision truncate` entry, add the block below.

   The guard searches for each literal `("<name>"`, so every name is written out, never formatted.

   ```python
   # W5-01b C4 (migration 0032): the cold scenario store alone INSERTs both cold scenario tables, which no module
   # updates, deletes, upserts, truncates, merges or copies; each table keeps at least one owner INSERT.

   def _cold_scenario_only(table: str) -> str:
       return f"Cold scenario table '{table}' is insert-only"


   def _cold_scenario_unseen(table: str) -> tuple:
       return (COLD_SCENARIO, ("replace", f'"INSERT INTO {table} (', f'"SELECT * FROM {table} WHERE ('),
               f"Rule 8 found no INSERT INTO {table} in ")


   NEGATIVE += [
       ("cold-scenario cold_scenario foreign insert", FINDING, _work_foreign("cold_scenario"), "writes cold scenario table 'cold_scenario'"),
       ("cold-scenario cold_scenario update", COLD_SCENARIO, split("cold_scenario", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario delete", COLD_SCENARIO, _work_delete("cold_scenario"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario upsert", COLD_SCENARIO, _work_upsert("cold_scenario"), _cold_scenario_only("cold_scenario")),
       ("cold-scenario cold_scenario owner insert unseen", *_cold_scenario_unseen("cold_scenario")),
       ("cold-scenario cold_scenario_revision foreign insert", FINDING, _work_foreign("cold_scenario_revision"), "writes cold scenario table 'cold_scenario_revision'"),
       ("cold-scenario cold_scenario_revision update", COLD_SCENARIO, split("cold_scenario_revision", "site_id = :s WHERE tenant_id = :i"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision delete", COLD_SCENARIO, _work_delete("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision upsert", COLD_SCENARIO, _work_upsert("cold_scenario_revision"), _cold_scenario_only("cold_scenario_revision")),
       ("cold-scenario cold_scenario_revision owner insert unseen", *_cold_scenario_unseen("cold_scenario_revision")),
       ("cold-scenario truncate", COLD_SCENARIO, '_OPS02 = "TRUNCATE cold_scenario"\n',
        "The cold scenario store never updates, deletes, truncates, upserts or runs DDL"),
   ]
   WRITER_CONTROLS += [
       ("controls cold-scenario cold_scenario insert", COLD_SCENARIO, _work_control("cold_scenario")),
       ("controls cold-scenario cold_scenario_revision insert", COLD_SCENARIO, _work_control("cold_scenario_revision")),
   ]
   ```

8. **Store style.** Every store INSERT is one string literal beginning `"INSERT INTO <table> (`, so the owner-insert-unseen probe can find it. The store has no `ON CONFLICT` anywhere: the `$actionForbidden` line check refuses it, so idempotent replay is a SELECT followed by a caught unique violation, as in `mini_decisions/store.py`.

9. **Checks.** C4 runs `tools/check-all.ps1` and `python tools/writer_guard_probes.py --seam` on the names starting `cold-scenario` and `controls cold-scenario`, on a clean committed tree.

Lane A wiring in `main.py`:

- add `from assetops_backend.cold_scenarios.service import ColdScenarioService`, `from assetops_backend.cold_scenarios.store import PostgresColdScenarioStore` and `from assetops_backend.cold_scenarios_api import build_cold_scenarios_router`;
- after the C1 mount, add:

  ```python
      # W5-01b C4: authored cold scenarios. Writes need the two explicit decision injections; reads use the cold gate.
      cold_scenario_store = PostgresColdScenarioStore.from_url(database_url()) if cold_reads is not None else None
      if cold_scenario_store is not None:
          app.router.on_shutdown.append(cold_scenario_store.dispose)
      app.include_router(build_cold_scenarios_router(
          registry, None if cold_scenario_store is None else ColdScenarioService(cold_scenario_store, cold_reads),
          command_access=mini_decision_command_access, principal=mini_decision_principal))
  ```

`cold_scenarios` is a top-level package like `mini_decisions`, not a `$domains` entry and not an adapter layer, so `main.py` may import its store directly.

**Reconciliation with C1q (C4 basis source).**
- `ColdScenarioService(cold_scenario_store, cold_reads)` builds `ColdDepthReadService(cold_reads)`.
- It resolves the basis by calling `basis_on(c, ...)` with the `Connection` that `cold_scenario_store.transaction()` yields (the `PostgresMiniDecisionStore.transaction` pattern), inside the same transaction as the INSERTs.
- The store imports no `analytics` module and holds only its own INSERT and SELECT SQL.

## C5 — cold Scenarios, navigation and W2-F L1 (per-unit review)

Read C5, mock caps, C4 DTO, literal ledger. Files: new `frontend/src/sites/ColdScenarios.tsx`, `frontend/src/sites/coldScenariosClient.ts`, `frontend/src/sites/__tests__/coldScenarios.test.tsx`; shared **Lane A only** `frontend/src/App.tsx`, `frontend/src/shell/SiteAnalyticsFrames.tsx`, `operatorSiteRoutes.ts`, `frontend/src/sites/ColdAssessmentViews.tsx`, `frontend/src/sites/__tests__/coldRoutes.test.tsx`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/docs/architecture/v69-screen-ledger.json`, `tools/checks/navigation-truthfulness.ps1`, `tools/checks/navigation-rail-fixtures.ps1`. Page: heading `Scenarios`; panel `Financial scenarios`; empty title `No scenario defined yet`; body `A scenario needs declared assumptions and an authored basis. None has been defined for this site and window.`; notice `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` One-row labels `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, pill `Defined` or `Historical`; `Review assumptions →` expands exact basis locally. Pending notice `Underlying evidence is being reassessed; the authored scenario remains separate.` Refusal `Cold scenarios unavailable`, exact server message and `Retry`. No observed-outcome status/label and no ordinary-viewer create control. In `SiteAnalyticsFrames.FinancialsSections`, render the live cold Scenarios tab when `site_type === COLDCHAIN`; retain `<UnavailableTab label="Scenarios" />` for every other non-mini-grid Site. Replace the cold-only `Scenarios are read for mini-grid sites only.` branch with `ColdScenarios` at `/sites/{site_code}/financials/scenarios`. `siteFinancialScenariosHref` must accept/preserve `from,to,known_at,scenario_at` for cold. `$expectedTabs` retains two `Scenarios`; re-anchor the positive and negative `navigation-rail-fixtures.ps1` checks to both the live cold branch and retained fallback. Registry `(cold-scenarios,1) Financial scenarios` maps C4 list/empty; no observed-outcome technical node is resolved.

**C5 registry row.** C5 alone adds `I-W5-cold-scenario-read` and `I-W5-cold-scenario-ui` nodes (`kind:implementation`, `area:cold-chain`, `status:open`, task W5-01b). The summary panel row is `screen_id:cold-scenarios`, `panel_index:1`, `title:Financial scenarios`, `area:cold-chain`, `requires:[I-W5-cold-scenario-read,I-W5-cold-scenario-ui]`, `status:gap`, `reason:Authored stock-value context is listed without observed loss or an outcome claim.` Test `coldScenarios.test.tsx::authored_pending_historical_basis` verifies the UI and registry guard checks this row.

Fix W2-F L1 in refused cold Finding branch: `StatusBar label="Finding state"` with `Unknown` / `Confidence: Unknown` directly above `PageRefusal`; assert in `coldRoutes.test.tsx::w2f_finding_strip_confidence`. Captures at 1440/390, owned here: `cold-scenarios-empty` (C4 GET before POST), `cold-scenarios-authored` (C4 POST), `cold-scenarios-historical` (C4 correction fixture and saved pre-correction `scenario_at`), `cold-scenarios-pending` (C1 late-reading fixture plus authored row), `cold-scenarios-refused` (C4 GET with `from` later than `to`: 422 `COLD_WINDOW_INVALID`, shared capture method), `cold-finding-refused-unknown` (merged W2-F refusal test). Clocks are C4's returned watermarks; historical uses the saved pre-correction `scenario_at` and/or before-late evidence `known_at`. Expand basis in a capped 390px internal scroller (max 560px panel for one row, separate disclosure cap 360px); long UUIDs break at character boundaries and exact full values remain available. Run the W1 vocabulary scan; wrap raw source IDs with `data-vocabulary-exempt="source-reference"`. Do not run T028 vocabulary over this intentionally named `Scenarios` page. Run `tools/check-all.ps1`, focused tests, mock/app cap pairs, one W5-01b real-Postgres suite, final independent review and merge before W5-02.

**C5 readiness pass 3 (Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldScenarios.test.tsx::states_loading_and_refusal`).**

**C5 scenario row, page and client (closure 2; Claude Architect, 2026-10-22 Codex-reset exception; Codex to review retrospectively; test `coldScenarios.test.tsx::row_disclosure_and_client`).**
- **Page frame.** Breadcrumb `Sites › {Site name} › Financials › Scenarios`; heading `Scenarios`. The description is the existing `SITE_SCREEN_DESCRIPTIONS.scenarios` (`Financials · scenarios`), so `V69Layout.tsx` is not edited.
- **Item table.** Items render in one `DataTable` inside `Financial scenarios`, with columns `Authored scenario`, `Assumptions`, `Basis`, `Defined at`, `State` and one row per `items[]` entry in DTO order.
  - `Authored scenario`: `name`, then on a second line `code` and `revision {revision_no}`, the code inside `data-vocabulary-exempt="source-reference"`.
  - `Assumptions`: `{stock_quantity} {stock_unit} at {unit_value} {currency} per {stock_unit}`. Decimal strings are printed verbatim.
  - `Basis`: `Selected evidence through {cutoff}`, with `cutoff` formatted `YYYY-MM-DD HH:MM UTC`, then a `<button type="button" aria-expanded>` labelled `Review assumptions →`.
  - `Defined at`: `recorded_at` as `YYYY-MM-DD HH:MM UTC`.
  - `State`: a neutral `Badge` whose text comes from `scenario_state`: `DEFINED` → `Defined`, `HISTORICAL` → `Historical`.
- **`Review assumptions →` expansion.** A full-width row directly below its item, scrolled internally at 390 (360px cap). It is a `<dl>` with these terms in order, every ID in a `data-vocabulary-exempt="source-reference"` span with character breaks and one ID per line:
  - `Kind` → `STOCK_VALUE_CONTEXT`
  - `Assumptions` → each key and value, one per line: stock_quantity,stock_unit,unit_value,currency
  - `Window` → `authored_basis.from` – `authored_basis.to` (ISO, verbatim)
  - `Evidence cutoff` → `authored_basis.cutoff`
  - `Assessment revisions` → `authored_basis.assessment_revision_ids`
  - `Accepted evidence` → `{n} records`, then each `authored_basis.accepted_evidence_ids` entry
  - `Foundation revision` → `authored_basis.foundation_revision_id`
  - `Source classification` → `authored_basis.source_provenance.classification`
  - `Revision` → `revision_id`
  A null ID prints `None`.
- **Client.** `frontend/src/sites/coldScenariosClient.ts` validation; any violation is the unavailable state.
  - Top level: exact keys `schema_version` (`"cold-scenarios-1"`), `site_id`, `window` (exact `from,to,known_at,committed_watermark`), `scenario_at`, `selection` (exact `state,assessment_revision_ids,accepted_evidence_ids,source_provenance`), `items`, `next_cursor` (string or null).
  - Item: exact keys `id`, `code` (matches `^CSCN-\d{6,}$`), `revision_id`, `revision_no` (integer ≥ 1), `name` (string of 1–160 characters), `kind` (`"STOCK_VALUE_CONTEXT"`), `assumptions` (exact keys `stock_quantity,stock_unit,unit_value,currency`, all strings, `currency` matching `^[A-Z]{3}$`), `authored_basis` (exact keys `from,to,cutoff,assessment_revision_ids,accepted_evidence_ids,foundation_revision_id,source_provenance`), `recorded_at` (string), `scenario_state` (`DEFINED` or `HISTORICAL`).
  - `selection.state` is one of the five STATES.
- **Refusal heading.** `Cold scenarios unavailable`.
- **Currentness.** `selection.state` from the C4 list drives an amber `Notice` above the `Financial scenarios` panel:
  - `PENDING_RECOMPUTE` → `Underlying evidence is being reassessed; the authored scenario remains separate.`
  - `HISTORICAL` → `Read at an earlier evidence cutoff; newer committed evidence exists.`
  - `STALE_SOURCE` → `The selected source is stale for this window.`
  - `UNKNOWN` → `No selected cold assessment covers this window yet.`
  - `CURRENT` → no notice.
  The row pill stays `Defined` or `Historical` from `scenario_state`.
- **Copy.** Loading, unavailable and refusal copy follow the shared capture-method section.
- **Captures.** Producers follow the shared method, with `cold-scenarios-pending` using the late-reading sequence (`advance_late()` without running the worker, after one authored POST).
- **Depends on.** C4 merged review and C1 (selection).


