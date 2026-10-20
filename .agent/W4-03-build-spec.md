# W4-03 Architect build contract — mini-grid decisions and work connection

Decision `D-2026-10-20-w4-03-buildspec`; 2026-10-20. Authority: `tasks/W4-03-mini-decisions-work.md`, `D-2026-10-20-post-w2-sequence`, v69 `screens.js`/manifest/rendered-panels and `.agent/W4-03-mock-measurements.md`. This is a proposed contract for independent implementer dry-read and owner wave-start scope/core-panel review. It does not assert W4-01, W3-01 or W4-02 is implemented: on the inspected branch their specs are frozen inputs, while merged code currently ends at `0026_w2_ev_money`. Before builder activation, check the actual merged symbols/columns, `0029` head and reviewed W3 estate adapter; amend this contract if they differ. Never silently implement around a mismatch.

## Verified seam ledger and ownership

| Seam | Verified fact and W4-03 treatment |
| --- | --- |
| `backend/migrations/versions/0009_finding_store.py:FINDING` | `finding` requires `anchor_assessment_revision_id`; `finding_revision` requires `assessment_revision_id`, `analytic_run_id`, `candidate_minutes`, `necessary_minutes`, `indeterminate_minutes`. These are dispatch-shaped and non-null. A renewable opportunity **cannot** be inserted with fabricated dispatch IDs/minutes. `window_assessment_revision_id` is nullable; do not use it as an opportunity pin. New typed opportunity tables and union adapters below own this gap. |
| `analytics/finding_index.py:FindingIndexService`, `analytics/adapters/postgres_assessment_store.py:PostgresAssessmentStore.findings/finding` | W1 Site index and Finding detail select W1 revisions; add a typed `mini_opportunity` arm to the Site/estate Opportunity lens, preserving W1 Cost/Risks behavior and IDs. Do not change W1 dispatch matching or consequence worker. A legacy Finding URL must not be made to decode an opportunity UUID. |
| `frontend/src/sites/FindingDetail.tsx`, `assessmentAnalysis.tsx`, `shell/SiteAnalyticsFrames.tsx`, `shell/operatorSiteRoutes.ts` | W1 Alternatives tab and analysis copy already exist; W4 supplies a persisted selected Alternative table on that tab. W1 `SiteWorkIncidents`/`SiteWorkMaintenance` are W4-01 planned thin lists; deepen their row presentation without changing their canonical read/count. Shell route changes are Lane A owned. |
| `backend/migrations/versions/0011_financial_consequences.py`, `financials/` and W2 money | W1 consequence revision is a separate observed-basis money model; scenario prices and gross sales do not append there. The W4-02 physical headroom revision is never monetary. Existing financial Overview remains unchanged. |
| `.agent/W4-01-build-spec.md` closure; `work/site_index.py`, `work/adapters/postgres_work_read.py` planned | Case IDs, event chronology `(recorded_at,id)`, correction, frozen transitions, Site index window/cutoff/count/cursor and `url:null` are binding. W4-03 must consume them after merge. `maintenance_record.outcome_note` is nullable and `outcome=UNVERIFIED` remains true after COMPLETE; `operational_record` is SUBMITTED and cannot certify telemetry. No new W4-01 columns or automatic Incident/Request creation. |
| `.agent/W4-02-build-spec.md` closure 1–3; `mini_depth/read.py`, `mini_depth_revision`, `mini_depth_selection` planned | One persisted Site-local hour per domain; renewable 1–5 distinct consecutive local days composed from selected noon hours. `mini_depth_selection` has `seq`, `selected_at` and nullable `job_id`; no `known_at` column. Exact head selects greatest `(selected_at,seq)` with selection and revision cutoff <= request cutoff. `cards.used_kw` is a range; opportunity_kwh belongs to complete eligible day only. Its status/currentness, conflicting/pending/changed-watermark gates apply before W4-03 claims. W4-02 does **not** supply demand, tariff, delivery completeness or general backup readiness. |
| `.agent/W3-01-build-spec.md` q1–q4; `evidence/public_provenance.py` planned | Public set DTO is `{classification,source_ids,evidence_ids,basis_sha256,reasons}` plus optional `detail`; classes are AUTHORED_DEMONSTRATION, REGISTERED_SIMULATION, MIXED, UNKNOWN. Resolve full exact selected accepted-ID set on the caller's tenant/Site repeatable snapshot; pending and selected blocks stay distinct. A selected opportunity row uses its own selected mini revision IDs and cited IDs, never the page or scenario. |
| `finding_api.py:Access,Scope,development_access` and W4-01 errors | Reuse tenant/Site bearer scope and `UNAUTHENTICATED`, `SITE_SCOPE_FORBIDDEN`, `SITE_NOT_FOUND` codes. Foreign IDs are 404. Store failure is 503. Do not expose a valid record across a Site boundary. |

Lane A owns `0030`, domain modules, router mount, shared Site/estate route integration, shell, dependency registry and navigation guard. W3-01's estate adapter is consumed after merge; any change to its shared contract is a reviewed versioned amendment, not an ad hoc W4 edit. The W4-01 case contract is frozen. W4-03's own `mini_decisions/` owns all new writes. No use of Lab scenario catalog (`/simulator-lab/scenarios`) as the Site financial scenario store.

## Domain decisions, basis and precedence

**Scenario.** A USER-authored what-if has an immutable root and append-only revisions. Input is a labelled `STOP_SOC`, `PRODUCTIVE_LOAD`, `TARIFF_ONLY` or `OTHER` proposal, with typed quantities/units, narrative, assumption source, actor, DB recorded time and optional pinned W4-02 renewable selection set. The authored value is not accepted evidence. A calculation is allowed only for `PRODUCTIVE_LOAD` when `proposed_kw > 0`, `duration_hours > 0`, `eligible_days > 0`, each selected eligible noon hour has supported lower headroom >= proposed kW and complete guardrails, and an explicitly authored positive tariff with currency/unit is present. Then per-window scenario energy is `proposed_kw × duration_hours` (duration <= 1 h inside that noon hour), and gross scenario sales is energy × tariff; use decimal arithmetic, no collection or net-benefit claim. A `TARIFF_ONLY` revision can present its assumption but has no energy or gross output. Stop-setting scenarios do not infer generator savings. Null rather than zero represents any missing input. Scenario revisions have `supersedes_revision_id`; only the latest version as of `known_at` appears on the current page, earlier versions remain inspectable and labelled historical. A correction requires reason and exact predecessor; it does not alter measured results.

**Alternative.** A versioned authored explanation is attached to one exact W1 dispatch Finding revision and cites accepted IDs or an explicit missing-evidence reason. Allowed dispositions are `PLAUSIBLE`, `CANNOT_EXCLUDE`, `INDETERMINATE`, `RULED_OUT`; `RULED_OUT` requires positive cited counterevidence plus a recorded reasoning statement and an exact same-window Finding basis. No absent record can rule out a transient, override, reserve requirement or PCS failure. The table read pins the requested Finding revision; when a later Finding revision is selected, old alternatives remain history, and their current display is `Needs review for this revision` until explicitly carried forward by a new alternative revision. Alternative text is authored interpretation, not a modification of dispatch `claim` or W1 money.

**Opportunity.** A separate `mini_opportunity` root identifies one Site and a contiguous 1–5 local-day study; `mini_opportunity_revision` pins the exact sorted `(local_day,mini_depth_selection.seq,mini_depth_revision.id)` set and full accepted-ID union. Positive status requires five distinct completely assessed days in this slice's positive fixture, at least one ELIGIBLE day, supported physical headroom on every counted day, W4-02 CURRENT basis at the request cutoff and provenance class neither MIXED nor UNKNOWN. Do not imply that all five days are eligible. `eligible_days/assessed_days` comes from the five W4-02 day rows, not a row page or a five-day aggregate. If selection changes after late evidence, append a new immutable revision and selection; preserve the old one. No automatic Action, case or financial consequence is created. The optional scenario ID is a linked, labelled what-if only; it cannot upgrade the opportunity's observed status. Opportunity identity key is `(tenant,site,first local day,last local day,model version)` with one root per study, not mock `F-109`; public code `OPP-000001` is allocated tenant-wide. Keep the mock's green Opportunity chip only for SUPPORTED; otherwise amber Evidence limited or grey Not assessed. Confidence is always `Not assessed` until a reviewed confidence rule exists; never use mock Medium.

**Work connection.** Show W4-01 canonical case rows and exact `finding_links`/`action_links`; add a read-only `decision_context` from pinned opportunity or scenario only when an explicit same-site ID link is recorded by a W4-03 association command. An opportunity does not imply an Incident, and a scenario does not imply work performed. An authored maintenance activity is `Completed · outcome unverified` until W1 verification evidence independently reaches its reviewed outcome. `url:null` stays noninteractive until W6-01 publishes a reviewed case detail page. W4-03 does not add links to W4-01 tables or alter its APIs; its association table below is separate.

Total display precedence, first match: failed store/resolver => HTTP 503; unauthorized/unknown Site => 403/404; invalid selection/input => 422; no selected revision => UNKNOWN/empty; changed W4-02 basis or overlapping pending/leased/failed job => PENDING_RECOMPUTE or STALE_SOURCE; explicit past cutoff => HISTORICAL; MIXED/UNKNOWN provenance or incomplete/conflicting required evidence => LIMITED; supported physical rule => SUPPORTED; otherwise UNKNOWN. An authored scenario keeps `scenario_state=DEFINED` even if its pinned physical basis becomes stale, but `calculation_state=WITHHELD`. A case count is an authored count even if linked evidence is pending; do not relabel it as an evidence count.

| Inputs at selected cutoff | Physical label | Scenario money label | Opportunity / work effect |
| --- | --- | --- | --- |
| No W4-02 selected noon hour | Not assessed | No calculation | No opportunity revision; cases still list. |
| One or more missing/conflicting days | Evidence limited | Withheld | No positive eligible-day claim; show day gaps and prior revision as historical. |
| Five complete days, zero eligible | No eligible headroom | Withheld | No positive opportunity; empty Opportunity lens. |
| Five complete days, >=1 eligible, no authored load | Supported headroom | No load scenario | Opportunity may be SUPPORTED; proposed load and sales are Unknown. |
| Supported headroom, load but no tariff | Supported headroom | Energy scenario only; gross Unknown | Never show a currency amount. |
| Supported headroom, load and tariff | Supported headroom | Gross sales scenario, before costs | Demand/collections remain unverified; no observed money change. |
| Any row with pending job/new basis | Reassessment pending | Withheld | Prior exact revision remains historical; no current positive badge. |
| Case COMPLETE with no later outcome proof | Case state COMPLETED | Independent | Maintenance outcome Unverified; never Verified. |

## API, exact wire, ordering and errors

Use one read-only REPEATABLE READ transaction and DB snapshot `read_time`; omitted `known_at` is that time, explicit past cutoff is HISTORICAL, future is 422 `INVALID_KNOWN_AT`. UTC `from`/`to` are half-open; serialize six-digit `Z`, accept offsets after normalization. `/api/sites/{site_code}/financials/scenarios?from=...&to=...&known_at=...`, `POST /api/sites/{site_code}/financials/scenarios`, `POST /api/sites/{site_code}/financials/scenarios/{id}/revisions`, `GET /api/sites/{site_code}/findings/{finding_id}/alternatives?revision_id=...&known_at=...`, `POST .../alternatives`, `GET /api/sites/{site_code}/opportunities?from=...&to=...&known_at=...`, `GET /api/sites/{site_code}/opportunities/{id}?known_at=...`, and `POST /api/sites/{site_code}/work/decision-links`. The Opportunity producer is worker/reconcile owned; there is no public POST to assert physical support. Site frontend routes: `/sites/:siteId/financials/scenarios`, `/sites/:siteId/findings/:findingId/alternatives`, `/sites/:siteId/opportunities/:opportunityId`; backend resolves tenant-unique Site **code**, frontend uses Site UUID. Do not substitute either token. The W3 estate Opportunities lens links to the typed opportunity route and keeps its existing W1 routes for W1 Findings.

Writes require USER actor ID, `SITE_DECISION_WRITE`, attestation, 8–128 character idempotency key, DB time and bounded UTF-8 text; SERVICE may write only a named rule/job/version for opportunity projection. All POSTs lock root/head and compare canonical sorted-key JSON SHA-256; exact retry returns prior IDs with 200, differing body 409 `DECISION_DUPLICATE_KEY`. A stale predecessor returns 409 `DECISION_BASIS_CHANGED`. A case association verifies the W4-01 case and decision identity on the same Site but never mutates either root. Scenario create/correction response is 201 with `id,revision_id,revision_no,recorded_at`; correction includes `supersedes_revision_id`. All list reads return full count before page (limit 50, max 100), then rows sorted: scenarios `(recorded_at DESC,id ASC)`; alternatives `(rank ASC,created_at ASC,id ASC)` with rank policy/uncertainty/capability; opportunities `(first_day DESC,id ASC)`; work keeps W4-01 `(occurred_at DESC,id ASC)`. Cursor is URL-safe base64 canonical JSON `v,tenant_id,site_id,from,to,known_at,selection_token,after`; malformed 422 `INVALID_CURSOR`, changed selected set 409 `DECISION_BASIS_CHANGED`. No offset paging.

```json
{"schema_version":"mini-decisions-1","site":{"id":"<site-uuid>","code":"KOBO-001","timezone":"Africa/Nairobi"},"window":{"from":"2026-10-06T09:00:00.000000Z","to":"2026-10-10T10:00:00.000000Z","known_at":"<cutoff>","bounds":"[from,to)"},"status":"SUPPORTED","currentness":{"state":"CURRENT","selected_at":"<db-time>","selection_seq":1},"source_provenance":{"classification":"REGISTERED_SIMULATION","source_ids":["<source-uuid>"],"evidence_ids":["<accepted-uuid>"],"basis_sha256":"sha256:<64-hex>","reasons":[]},"selected_source_provenance":{},"pending_source_provenance":null,"opportunity":{"id":"<opportunity-uuid>","code":"OPP-000001","revision_id":"<revision-uuid>","study_days":5,"eligible_days":3,"assessed_days":5,"headroom_kw":{"low":18,"high":20},"proposed_load_kw":null,"gross_sales_scenario":null,"demand_state":"UNVERIFIED","collection_state":"UNVERIFIED","scenario_id":null,"day_rows":[{"local_day":"2026-10-06","selection_seq":1,"mini_revision_id":"<mini-uuid>","decision":"ELIGIBLE","opportunity_kwh":{"low":18,"high":20},"evidence_ids":["<accepted-uuid>"]}]},"links":{"renewable":"/sites/<site-uuid>/performance/renewable?from=...","site_work":null,"scenario":null},"limitations":[]}
```

Numbers above illustrate wire **shape only** and are not fixture or default values. In actual reads, `selected_source_provenance` is the full selected six-key DTO, `pending_source_provenance` is null or its full pending DTO, and top-level `source_provenance` aliases pending first, selected second, empty UNKNOWN last. If a selected opportunity row is shown while a newer job is pending, its row provenance remains selected and its status is HISTORICAL/PENDING; never relabel its citations as pending. `day_rows` is all study days, not the current page. Scenario row shape is `{id,revision_id,name,kind,authored_at,actor_id,assumptions:[{key,value,unit,source}],pinned_mini_revision_ids:[],calculation_state,energy_kwh:null|number,gross_sales:{amount,currency,basis:"SCENARIO"}|null,limitations:[],url}`. Alternative row is `{id,revision_id,finding_revision_id,explanation,evidence_summary,cited_accepted_evidence_ids,missing_evidence_reason,disposition,reason,review_state}`. Work `decision_context` is `{kind,id,label,url|null}` or null. Absent scalar is JSON null; no empty string or zero sentinel.

| HTTP | Code | Message / screen copy |
| --- | --- | --- |
| 401 | `UNAUTHENTICATED` | `Sign in to read decisions.` / `Sign in to see this page.` |
| 403 | `SITE_SCOPE_FORBIDDEN` | `No access to Site '{code}'.` / `You do not have access to this site.` |
| 403 | `DECISION_WRITE_FORBIDDEN` | `This actor cannot change decisions at this Site.` / `You cannot change this decision.` |
| 404 | `SITE_NOT_FOUND` | `No imported Site '{code}' in this tenant.` / `This site was not found.` |
| 404 | `DECISION_NOT_FOUND` | `No decision with this ID at this Site.` / `This decision was not found at this site.` |
| 404 | `WORK_CASE_NOT_FOUND` | Reuse W4-01 exact response/copy. |
| 409 | `DECISION_BASIS_CHANGED` | `The selected basis changed; reload the first page.` / `The evidence changed. Reload this page.` |
| 409 | `DECISION_DUPLICATE_KEY` | `This key was used for different decision content.` / `This change conflicts with an earlier submission.` |
| 422 | `DECISION_INPUT_INVALID` | `A required decision field or unit is invalid.` / `Check the declared assumptions and try again.` |
| 422 | `INVALID_WINDOW`, `INVALID_KNOWN_AT`, `INVALID_CURSOR` | Respectively `Select a valid Site-local window.`, `Select a time no later than now.`, `Reload the first page.` |
| 503 | `DECISION_STORE_UNAVAILABLE` | `Decision records could not be read or saved.` / `Decisions are unavailable right now. Try again.` |

Error JSON is `{"detail":{"code":"...","message":"...","rows":null,"total_count":null}}` for list requests, with the two list keys omitted for detail/write. 403/404/503 render a full state with no cached positive badge or link. A 200 empty result is reserved for a successful query with no records. Scope check precedes input parsing and record lookup. W4-01 list errors retain their frozen `WORK_*` codes; W4-03 UI does not remap them.

## Migration `0030_w4_mini_decisions`

Parent is exactly `0029_w4_mini_depth` after merge. No `known_at` or `finding` schema modification. Use existing `ledger_append_only()` triggers. All UUIDs lowercase in wire; DB UUID is authoritative. The following is the required table/constraint/index shape; standard `site(tenant_id,id)` and scoped W4-02 revision/evidence FKs must resolve on merged base. The writer verifies each JSON selection tuple against the actual selected row in one transaction; JSON is an immutable snapshot, not a substitute for this check.

```sql
CREATE SEQUENCE mini_decision_public_no_seq;
CREATE TABLE mini_scenario (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL DEFAULT nextval('mini_decision_public_no_seq'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 UNIQUE (tenant_id,site_id,id), UNIQUE (tenant_id,public_no)
);
CREATE TABLE mini_scenario_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL, scenario_id uuid NOT NULL,
 revision_no integer NOT NULL CHECK (revision_no>0), supersedes_revision_id uuid NULL,
 name text NOT NULL CHECK (length(btrim(name)) BETWEEN 1 AND 160),
 kind text NOT NULL CHECK (kind IN ('STOP_SOC','PRODUCTIVE_LOAD','TARIFF_ONLY','OTHER')),
 assumptions jsonb NOT NULL, pinned_mini_revision_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
 calculation jsonb NOT NULL, correction_reason text NULL,
 actor_id text NOT NULL, authorization_basis text NOT NULL, attestation text NOT NULL,
 idempotency_key text NOT NULL, payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id,scenario_id) REFERENCES mini_scenario(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,supersedes_revision_id) REFERENCES mini_scenario_revision(tenant_id,site_id,id),
 UNIQUE (tenant_id,site_id,id), UNIQUE (scenario_id,revision_no),
 UNIQUE (scenario_id,supersedes_revision_id), UNIQUE (scenario_id,idempotency_key),
 CHECK ((revision_no=1 AND supersedes_revision_id IS NULL AND correction_reason IS NULL)
     OR (revision_no>1 AND supersedes_revision_id IS NOT NULL AND length(btrim(correction_reason))>0))
);
CREATE INDEX mini_scenario_site_order ON mini_scenario_revision(tenant_id,site_id,recorded_at DESC,id);
CREATE TABLE mini_alternative_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 finding_id uuid NOT NULL, finding_revision_id uuid NOT NULL,
 alternative_key text NOT NULL, version_no integer NOT NULL CHECK (version_no>0),
 supersedes_revision_id uuid NULL, rank smallint NOT NULL CHECK (rank BETWEEN 1 AND 3),
 explanation text NOT NULL, evidence_summary text NOT NULL,
 missing_evidence_reason text NULL, disposition text NOT NULL
   CHECK (disposition IN ('PLAUSIBLE','CANNOT_EXCLUDE','INDETERMINATE','RULED_OUT')),
 reason text NOT NULL, actor_id text NOT NULL, authorization_basis text NOT NULL,
 attestation text NOT NULL, idempotency_key text NOT NULL,
 payload_sha256 text NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id,finding_id) REFERENCES finding(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,finding_revision_id) REFERENCES finding_revision(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,supersedes_revision_id) REFERENCES mini_alternative_revision(tenant_id,site_id,id),
 UNIQUE (tenant_id,site_id,id), UNIQUE (finding_id,alternative_key,version_no),
 UNIQUE (supersedes_revision_id), UNIQUE (finding_id,idempotency_key)
);
CREATE INDEX mini_alternative_selected ON mini_alternative_revision(tenant_id,site_id,finding_revision_id,rank,created_at,id);
CREATE TABLE mini_alternative_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, alternative_revision_id uuid NOT NULL,
 evidence_id uuid NOT NULL, PRIMARY KEY (alternative_revision_id,evidence_id),
 FOREIGN KEY (tenant_id,site_id,alternative_revision_id) REFERENCES mini_alternative_revision(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,evidence_id) REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE mini_opportunity (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 public_no bigint NOT NULL DEFAULT nextval('mini_decision_public_no_seq'),
 first_day date NOT NULL, last_day date NOT NULL, model_version text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id) REFERENCES site(tenant_id,id),
 UNIQUE (tenant_id,site_id,id), UNIQUE (tenant_id,public_no),
 UNIQUE (tenant_id,site_id,first_day,last_day,model_version),
 CHECK (last_day>=first_day AND last_day-first_day BETWEEN 0 AND 4)
);
CREATE TABLE mini_opportunity_revision (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 opportunity_id uuid NOT NULL, revision_no integer NOT NULL CHECK (revision_no>0),
 selected_hours jsonb NOT NULL, result jsonb NOT NULL,
 input_sha256 text NOT NULL CHECK (input_sha256 ~ '^sha256:[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id,opportunity_id) REFERENCES mini_opportunity(tenant_id,site_id,id),
 UNIQUE (tenant_id,site_id,id), UNIQUE (opportunity_id,revision_no),
 UNIQUE (opportunity_id,input_sha256)
);
CREATE TABLE mini_opportunity_evidence (
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, opportunity_revision_id uuid NOT NULL,
 evidence_id uuid NOT NULL, PRIMARY KEY (opportunity_revision_id,evidence_id),
 FOREIGN KEY (tenant_id,site_id,opportunity_revision_id) REFERENCES mini_opportunity_revision(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,evidence_id) REFERENCES accepted_evidence(tenant_id,site_id,id)
);
CREATE TABLE mini_opportunity_selection (
 seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 tenant_id uuid NOT NULL, site_id uuid NOT NULL, opportunity_id uuid NOT NULL,
 revision_id uuid NOT NULL, selected_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id,opportunity_id) REFERENCES mini_opportunity(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,revision_id) REFERENCES mini_opportunity_revision(tenant_id,site_id,id)
);
CREATE INDEX mini_opportunity_head ON mini_opportunity_selection(tenant_id,site_id,opportunity_id,selected_at DESC,seq DESC);
CREATE TABLE mini_decision_work_link (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, site_id uuid NOT NULL,
 case_id uuid NOT NULL, scenario_id uuid NULL, opportunity_id uuid NULL,
 actor_id text NOT NULL, attestation text NOT NULL, created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (tenant_id,site_id,case_id) REFERENCES work_case(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,scenario_id) REFERENCES mini_scenario(tenant_id,site_id,id),
 FOREIGN KEY (tenant_id,site_id,opportunity_id) REFERENCES mini_opportunity(tenant_id,site_id,id),
 CHECK ((scenario_id IS NULL) <> (opportunity_id IS NULL)),
 UNIQUE (case_id,scenario_id), UNIQUE (case_id,opportunity_id)
);
CREATE INDEX mini_decision_work_case ON mini_decision_work_link(tenant_id,site_id,case_id,created_at,id);
```

Add `BEFORE UPDATE OR DELETE` append-only triggers on all nine tables (including junction and selection tables); no cascade. Service verifies `finding_revision.finding_id=finding_id`, scenario/opportunity selected-revision/site equality, exact accepted-ID scope, and a `RULED_OUT` citation on its transaction. SQL checks alone do not establish these relationships. The opportunity writer verifies all five `mini_depth_selection` rows are renewable noon hours and their linked revision domain/window/Site match; ordered `selected_hours` stores exact `seq`, revision UUID, local day and selection time. Scenario assumptions JSON accepts only closed keys and finite decimal strings; require `unit` and `currency` when applicable, no arbitrary expression language. `mini_decision_public_no_seq` gaps on rollback are allowed. **Downgrade:** lock all nine tables ACCESS EXCLUSIVE in child-to-parent order; if any row exists raise `Downgrade of 0030_w4_mini_decisions refused: decision history exists`; otherwise drop triggers, four explicit indexes, child tables then roots, sequence. Do not cascade or touch `0029`, W1 finding/consequence or W4 work. Catalog tests assert exact delta and one Alembic head. The migration file is created only during implementation, not by this planning task.

## Mock panel, cell and copy ledger

The shell supplies authorized Site name/code/timezone, Site-local window and breadcrumb; no mock organisation name, F-code, time or footer `Illustrative mockup data` becomes product fact. Preserve the mock panel order and shared v69 visual primitives. Every destination below needs an exact reviewed route; if null, use a noninteractive `Unavailable` control with no `href`, click handler or focus target. Chips: green only SUPPORTED/ELIGIBLE, amber LIMITED/PENDING/UNVERIFIED, blue authored/HISTORICAL, grey UNKNOWN/unavailable, red only contradictory/failed. No confidence popover until a reviewed rule exists.

| Screen / mock element | Exact field or gap, literal copy and destination |
| --- | --- |
| `scenarios` shell; Financials subtabs | Site/window from Foundation and route. `Overview` and `Assumptions` retain W1 routes; `Scenarios` is selected. Subtitle `Financials · scenarios` (remove `placeholder` only after live read). No cold/EV Scenarios promotion. |
| Financial scenarios panel empty block | 200 empty `rows=[]` => heading `No scenario defined yet`; body `A scenario compares a declared what-if with the measured case. None has been defined for this site.`; foot `No authored what-if at this site and cutoff.` Store 503 uses refusal copy, never empty. |
| Financial scenarios populated rows | Columns `Scenario` ← name/kind/public number, `Declared change` ← typed assumptions and unit, `Physical basis` ← pinned mini revision IDs or `No measured basis pinned`, `Illustrative result` ← energy/gross scenario or `Cannot calculate from the selected evidence`, `State` ← DEFINED/HISTORICAL with calculation state. Empty list has no invented row. `Open scenario` links only to an implemented detail drawer on exact ID; otherwise `Scenario detail unavailable`. |
| Scenarios notice | Exact `Scenarios never change measured results or the consequence lines on Overview. They are labelled what-ifs, kept separate from evidence.` Always shown. `Create scenario` appears only when reviewed POST UI exists and principal has write authority; otherwise labelled `Scenario creation unavailable`. |
| `alternatives` breadcrumb/title/tabs | W1 exact Finding ID/title/Site, selected `revision_id`; `Open site` resolves authorized Site Overview. W1 Overview/Analysis/Evidence/Recommendation/History retain their reviewed routes; unavailable occurrences stay unavailable. |
| Alternatives table `Explanation` | `alternative.explanation`, limited to author-approved text from persisted revision. For no authored alternatives: `No alternatives recorded for this Finding revision.` Do not copy mock stop-threshold values. |
| `Evidence` | Render each exact cited accepted ID through the shared provenance drawer and `evidence_summary`; if none, show `No accepted record supports or excludes this explanation.` Missing-record text remains an authored question, not a negative observation. |
| `Disposition` | PLAUSIBLE → `Plausible policy explanation`; CANNOT_EXCLUDE → `Cannot exclude`; INDETERMINATE → `Indeterminate`; RULED_OUT → `Ruled out by cited evidence`. If a later Finding revision is selected without a matching new Alternative revision: `Needs review for this revision`. Same-time alternative rows sort rank, created_at, UUID. |
| Alternatives notice | Exact `Candidate runtime is not proof that stopping the generator would have preserved service.` Always shown. The W1 `Other possible explanations (Alternatives)` CTA reaches this route with pinned Finding revision only after loaded; 503 shows `Alternatives unavailable`. |
| `opportunity-finding` status bar | Public `OPP-* · Opportunity` from new typed identity; physical SUPPORTED/limited badge and `Confidence: Not assessed`; secondary `Recommendation · demand unverified` only when supported headroom and demand absent, else `Decision pending · evidence limited`. No `F-109`, mock Medium or implied accepted recommendation. |
| Four cards | `Usable headroom` ← selected W4-02 supported low/high kW (else `Unknown`), note `After the selected retained margin`; `Eligible days` ← `eligible_days / assessed_days` only for five individually assessed days (else `Not established`); `Proposed load` ← authored scenario kW × h (else `No load proposed`); `Gross sales scenario` ← authored gross amount/currency (else `Not calculated`), note `Illustrative, before costs; collections unverified`. |
| Bounded opportunity | Sentence template `Renewable capacity appears available for a one-hour productive load in {eligible_days} adequately observed windows.` only when actual proposal fits each counted hour; without proposal: `Measured renewable headroom is available in {eligible_days} of {assessed_days} assessed windows; no added load has been validated.` Limited: `The selected evidence does not establish a recurring productive-use opportunity.` Always follow with `Electrical feasibility does not establish customer demand, collections or a realised financial benefit.` `Inspect opportunity evidence` opens exact selected evidence IDs in drawer; empty IDs → `No selected opportunity evidence`. |
| Next decision | With supported headroom: `Validate local demand, schedule any proposed load, and check critical service and storage guardrails before a trial.` Otherwise `Complete the missing renewable and service evidence before a load decision.` `Open renewable evaluation` links to the exact five-day W4-02 selected window/cutoff, including all dates; a missing/503 read yields `Renewable evaluation unavailable`. |
| Consequence basis | `Technical quantity` ← low/high physical kW or `Unknown`; `Scenario energy` ← authored kWh per eligible window or `No load scenario`; `Tariff` ← authored value/currency/unit or `No tariff declared`; `Gross sales` ← scenario output or `Not calculated`; `Managed Action` ← exact linked W1 Action ID/event if separately accepted, otherwise `Not yet accepted`. Never show a W1 consequence amount here. |
| `sitework-incidents` status/table | W4-01 `total_count`, `status`, rows. `Scoped to {Site} · {n} incidents`; if store 503, `Incident count unavailable`. Preserve columns `Case`=code with detail URL only when reviewed, `Window`=occurred_at/site local, `What happened`=latest title/narrative, `Linked findings`=exact W4-01 Finding links plus W4-03 typed opportunity context only when explicit association exists, `State`=W4-01 reducer. No rows: `No incidents at this site`; null URL: `Record page unavailable`. |
| `sitework-maintenance` status/table | W4-01 `total_count`, rows. `Scoped to {Site} · {n} maintenance`; 503 `Maintenance count unavailable`. `Work request`=code, `Asset`=scoped asset_label or `No asset linked`, `Activity`=latest MaintenanceRecord activity or `No activity recorded`, `Outcome`=`Unverified` for COMPLETE without separate proof, `Next evidence`=declared reviewed criterion or `No outcome evidence specified`. No rows: `No maintenance work at this site`; null detail URL: `Record page unavailable`. |
| Site Work tabs, manage CTAs, notice | Actions retains W1 count; Incidents/Maintenance counts from W4-01 full count, never page length. `Manage in Incidents`/`Manage in Maintenance` remain `Unavailable` until W6-01 reviewed roots exist. Both notices: `Opening a record moves you to its own area; the breadcrumb keeps this site in context.` Only show as navigation guidance if a real record destination exists; otherwise `Record detail is not available yet; this list keeps the site context.` |

The Site Work delta is additive to W4-01's thin lists: W4-01 owns count, row and empty mechanics. W4-03 supplies only decision context, strengthened gap copy and tested noninteractive destinations. It must not replace W4-01 list source with a join that drops unlinked cases or shrinks full counts.

### Supersession index for visible text

| Earlier source text | W4-03 treatment |
| --- | --- |
| v69 `scenarios` subtitle `(placeholder)` and `Placeholder · to be designed with the owner` | Superseded only on the implemented mini Site route by the live read and the exact empty/populated copy above; cold/EV placeholders remain untouched. |
| v69 Opportunity `F-109`, `Confidence: Medium`, 18–20 kW, 3/5, 10 kW × 1 h, $0.25/kWh, $2.50 | Illustrative only. Typed `OPP-*`, `Not assessed` confidence and selected W4-02 plus authored scenario fields replace them. The fixture may use the proposed load/tariff as *authored test input*, never as production seed. |
| v69 Alternatives `Configuration v7`, 14:50 capability absence and three dispositions | Superseded by pinned Finding revision, exact accepted IDs and authored current alternative revisions. W1 dispatch claim remains intact. |
| W4-02 `No productive-use scenario has been assessed.` and `Opportunity decision unavailable` | W4-02 physical headroom and evidence drawer remain. When the reviewed W4-03 scenario/detail route is live, replace only the unavailable decision destination with its exact ID link; absent scenario still displays the W4-02 missing statement. |
| W4-01 Site Work `url:null` and `Manage in ...` unavailable | Still binding until W6-01 detail/global roots are reviewed; W4-03 decision context does not promote these links. |

No text in an immutable stored revision is edited for a new selection. Historical alternatives/scenarios/opportunity revisions remain addressable with a `Historical basis` label and their own exact citations; the UI uses the newly selected text only for the current row.

## Layout and copy verification

Use only `.agent/W4-03-mock-measurements.md`, not a new browser measurement for this spec. Per piece cap = mock + max(24 px, 10%), rounded up. Whole page may grow with real rows but each named piece must stay within its cap, using bounded inner scrolling for a long table; page scroll width <= supplied 1425 px at 1440 and <=390 px at 390. All named panels are 1161 px wide at 1440, 360 px at 390. Narrow Alternatives columns are mock 115/104/101 px and row heights 62/97/62; table may scroll internally with first column visible. Opportunity desktop cards are four 281 px children; narrow is two columns with 174 px children. Next decision/Consequence basis desktop widths are 735/408 px, narrow 360 px stacked.

| Screen | 1440 max heights in rendered order | 390 max heights in rendered order |
| --- | --- | --- |
| scenarios | Financial scenarios 348; notice 66 | Financial scenarios 391; notice 102 |
| alternatives | Alternatives table panel 268; notice 66 | Alternatives panel 365; notice 84 |
| opportunity-finding | status 69; cards 137; Bounded opportunity 232; Next decision 295; Consequence basis 295 | status 96; cards 273; Bounded opportunity 339; Next decision 217; Consequence basis 295 |
| sitework-incidents | status 61; panel 348; notice 66 | status 115; panel 370; notice 102 |
| sitework-maintenance | status 61; panel 326; notice 66 | status 115; panel 348; notice 102 |

Use the v69 tabs, breadcrumbs and header hierarchy from `screens.js`. For 390 widths, scroll only inside the data grid, wrap notice/body copy, and never clip status chips or create page-level horizontal scroll. Screenshot comparison includes populated, empty and pending/limited variants; record app/mock heights and widths in the review packet, with any over-budget piece as a defect.

## Fixture and one-run commit proof

Fixture `backend/tests/fixtures/w4/w403-mini-decisions.json`, schema `w403-mini-decisions/1`, UTF-8 sorted keys/final LF, records commands and expected semantic outcomes, not resolved UUIDs. Resolve KOBO-001/Foundation/bindings/asset IDs from public reads after W4-02 merges. Positive replay uses W4-02 registered KOBO publication v5 for Nairobi 2026-10-06 through 10, five separate accepted noon hours. Author a 10 kW × 1 h proposed load and $0.25/kWh tariff **as a labelled test scenario only** after actual selected headroom is confirmed; expected $2.50 is asserted only if the fixture's selected lower headroom supports that load, never seeded into product data. A second branch omits tariff/demand and one critical-service source; a third accepts late contradictory evidence after the first selection. Create one W4-01 Incident and one MaintenanceRequest through frozen public case APIs and explicitly associate a decision; a second case remains unlinked to prove count preservation. No private Lab world-state read, static mock F/INC/WR code, direct accepted-evidence insertion or fake `assessment_revision`.

| Commit / one builder run | Output and named focused tests |
| --- | --- |
| 1 — migration/store | `0030`, scoped FKs, append-only, downgrade. `backend/tests/test_w403_migration_postgres.py::{test_0030_single_head_catalog_and_empty_downgrade,test_0030_downgrade_refuses_any_history,test_cross_site_fk_and_immutable_history}`; `backend/tests/test_w403_decision_store_postgres.py::{test_scenario_revision_idempotency_and_correction,test_alternative_revision_exact_finding_and_citations,test_opportunity_selection_matches_five_noon_hours}`. |
| 2 — rule/API | Scenario math/refusals, alternative disposition and full selected provenance. `backend/tests/test_w403_rules.py::{test_scenario_energy_and_gross_are_labelled,test_missing_tariff_demand_and_conflict_withhold,test_alternative_total_disposition_precedence}`; `backend/tests/test_w403_api_postgres.py::{test_scope_403_404_and_store_503,test_invalid_window_cutoff_cursor_and_changed_basis,test_selected_pending_row_provenance_and_full_count}`. |
| 3 — opportunity/index | Worker/reconcile revision selection, late evidence, typed Site/estate union. `backend/tests/test_w403_opportunity_postgres.py::{test_five_distinct_days_eligible_denominator_and_reload,test_late_accepted_row_appends_revision_and_history,test_no_head_and_pending_withhold_current_badge,test_site_and_estate_opportunity_lens_exact_route}`; retain W1 FindingIndex Cost/Risks and W3 estate pagination tests. |
| 4 — three pages | Scenarios, W1 Alternatives delta, opportunity detail, exact CTAs and budget. `frontend/src/sites/__tests__/miniDecisions.test.tsx::{scenario_empty_populated_and_refused,alternative_cells_and_revision_state,opportunity_supported_limited_pending_and_null_money,exact_routes_no_dead_cta,narrow_mock_panel_budgets}`. |
| 5 — Work/closeout | W4-01 list delta, explicit context, no count loss, guard/registry/nav fixtures. `backend/tests/test_w403_work_links_postgres.py::{test_same_site_explicit_link_only,test_unlinked_cases_keep_full_count_and_unverified_outcome}`; `frontend/src/sites/__tests__/siteWorkCases.test.tsx::{decision_context_and_unlinked_case,unverified_maintenance_and_unavailable_destinations}`. Replay positive/missing/late on private `*_test` DB, capture 1440/390, one same-revision full backend Postgres suite, frontend suite, `tools/check-all.ps1`, rule-8/dependency/SQLAlchemy/navigation/registry checks and Alembic single-head/downgrade. Record actual collected counts; do not guess. |

Builder must update rule-8 writer allowlist for the exact `mini_decisions` adapter, denied writer probes, dependency-direction/SQLAlchemy import allowlists, hard-coded upgraded HEAD tests and the v69 unavailable-tab **multiset** atomically with positive/negative navigation fixtures. Promote only the mini `scenarios`, one `alternatives` occurrence, one `opportunity-finding` route and the already-reviewed mini Site Work occurrences; cold/EV variants and global W6 work roots stay unavailable. Review packet cites exact revision/evidence IDs, source class, panel measurements and fixture paths. Independent spec dry-read precedes commit 1; independent slice review and owner walkthrough precede merge.
