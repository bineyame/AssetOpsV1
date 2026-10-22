# W6-01 Global work cases — build contract

Architect, 2026-10-22. Applies to [W6-01a–e](../tasks/W6-01-global-work-cases.md) in order. Each unit card below is the current contract for its builder. This is a planning contract pending independent readiness review and the browser measurements listed in §4; it is not owner acceptance or an implementation dispatch.

## 1. Frozen model and wire

Merged authority: `backend/assetops_backend/work/{model.py,site_index.py,detail.py,service.py}`, `work_api.py`, migration `0027_w4_work_cases`, `estate/{scope.py,index.py,portfolio.py}`, `estate_api.py`, and `sites_api.py:212`. One read-only REPEATABLE READ snapshot selects all authorized imported Sites. No Site HTTP fan-out, new DDL, client tenant, invented mock ID, accepted equipment reading, work verification, warranty or due evaluator. `0036` stays unused; merged Alembic head is `0030_w4_mini_decisions`.

**Identity and time.** Frontend `siteId`, API `{site_code}`, and every Site href use the stored **Site code** (`sites_api.py:212`), never Site UUID. UUID is internal scope/FK identity. Case root `(tenant_id,site_id,work_case.id)` retains stored INC/WR code; plan/operational root `(tenant_id,site_id,canonical_plan_id/canonical_record_id)` retains the root PM/REC code. Case revision is the last `(recorded_at,id)` at cutoff, matching `work/detail.py` and `work/site_index.py`; event and record order is `(recorded_at,id)`. For cases, membership uses root `occurred_at` (incident) or root `created_at` (request), even when a later revision crosses the window. Global incident rows sort by `(root occurred_at desc, site_code_key asc, site_id asc, case_id asc)`; global maintenance rows sort by `(root created_at desc, site_code_key asc, site_id asc, case_id asc)`. Compare the complete tuple in that order for cursor continuation; UUID tiebreaks use lowercase canonical strings. For plans and operational records, membership uses **root `occurred_at`**, head selected at cutoff; display/sort by selected head `(recorded_at desc,site_code_key asc,site_id asc,canonical_root_id asc)`. Thus a correction does not move a root between windows. `occurred_at` in an operational row is the selected head's occurrence and is the `When` display; root occurrence is a separate field. Root and head timestamps must be at/before `known_at`. Global list and outer detail wire instants are whole UTC seconds with `Z`; nested `work_detail` retains merged W4's six fractional digits and `Z` for every instant. New `history.revisions[].occurred_at`, `history.revisions[].recorded_at`, `history.operational_records[].occurred_at` and `history.operational_records[].recorded_at` use six fractional digits and `Z` as well; `selected.known_at` uses whole seconds. Cursor/token canonical instants retain six digits. Decimal quantities are strings.

**Parser, access and status.** Global list routes are `GET /api/work/incidents`, `/maintenance`, `/preventive`, `/operational-records`. Authenticate first (401), then the W3 `estate/scope.py:parse_request` window/known/limit discipline adapted to four work kinds: exactly one `from` and `to`, UTC midnight, `[from,to)` 1–31 days; optional single UTC `known_at` no later than DB read time; `limit` 1–100, default 50; optional `cursor`. `kind` only on operational records, one of `all|OPERATOR_LOG|MANUAL_READING|SHIFT_NOTE|SITE_VISIT`, default `all`. Unknown/repeated non-window keys are `INVALID_CURSOR`; bad/missing window keys are `INVALID_WINDOW`. **Server requires the window**; UI initially sends the last seven complete UTC days ending at today's 00:00 UTC and never claims the server defaulted it. Every global page reads single `from`, `to` and optional `known_at` (A2Q10: plus optional `cursor`, and `kind` on E2 only; other keys ignored, never forwarded) from `location.search`, validates them by the same UTC rules, populates the controls, and sends them unchanged on first read, reload, pagination and Site fallback links; invalid page query shows the `INVALID_WINDOW`/`INVALID_KNOWN_AT` refusal without fetching. Only when both `from` and `to` are absent does the UI use the seven-day initial window; one missing bound is `INVALID_WINDOW`. A denied Site is silently excluded, exactly as W3 estate roots do; global lists have no 403/404. Scope includes `tenant_id` (UUID or null for unavailable tenant), counts, and W3 `access_basis`. If zero Sites are authorized, status is `EMPTY_SCOPE` even with an earlier explicit `known_at`; otherwise earlier explicit cutoff is `HISTORICAL`. `PARTIAL` is reserved for a future per-Site independent read model and is **not produced** by this single-snapshot implementation. Current status is `CURRENT`; store failure is 503. `coverage.state` is `COMPLETE|EMPTY_SCOPE`, `reason` null or `NO_ACCESSIBLE_SITES`, and `sites` is an array of `{site_code,site_id,state:'COVERED'}`. A successful complete zero has `total_count:0`; no null-to-zero coercion. Cursor snapshots pin page-one cutoff and full selected set. Use the W3-03 Portfolio HMAC pattern (`estate/scope.py:299–341`) with a dedicated required `ASSETOPS_WORK_CURSOR_KEY_HEX` (64 hex chars, no default): bad key => 503, bad MAC/shape => 422, changed scope/selection => 409. Set it in test and capture server environments before the first read; A1 documents local generation beside the estate key in `backend/README-db.md`, never prints/logs it, and tests missing/malformed key. Bind route, kind filter, window, cutoff, authorized Site IDs, access basis, full selected root/head/revision/event/link lineage IDs and last sort tuple. Do not reuse W4's unsigned cursor.

**Envelope and row DTO table.** Every successful root returns `schema_version:'global-work-index-1'`, `scope:{tenant_id,authorized_site_count,covered_site_count,access_basis}`, `window:{from,to,bounds:'[from, to)'}`, `known_at`, `status`, `coverage`, `total_count`, `state_counts` (A2Q1: incidents `{OPEN,IN_PROGRESS,CLOSED}`, maintenance `{OPEN,IN_PROGRESS,COMPLETED,CANCELLED}`, full selected set before paging; preventive and operational-records `null`), `rows`, `next_cursor`, `selection_token`. Keys are always present. `next_cursor` is string or null. The following are exhaustive row keys; IDs are UUID strings, nullable fields are explicitly null, links are arrays (possibly empty), and `href` may be null. `source_provenance` is the existing W4 provenance DTO from `provenance_dto`, not a new enum. Case rows reuse `case_basis` (`work/service.py:41-67`). For preventive and operational rows, call `provenance_dto` with selected IDs `[head_id]` and cited accepted-evidence IDs `[]`. Sort and lowercase UUID strings. A correction replaces the selected head ID. The digest follows `evidence/public_provenance.py:63-70`; `sha256:example` below is illustrative, never a stored digest.

| Root | Exact row fields and types |
| --- | --- |
| incidents | `site_code:string, site_name:string, site_id:string, site_code_key:string, case_id:string, code:string, kind:'INCIDENT', revision_id:string, title:string, narrative:string, occurred_at:string, created_at:string, recorded_at:string, state:'OPEN'|'IN_PROGRESS'|'CLOSED', owner:string|null, asset_id:string|null, asset_label:string|null, incident_id:string|null, linked_request_codes:string[], finding_links:Link[], action_links:Link[], source_provenance:object, links:{site:Link,site_incidents:Link}`. Owner is latest selected `ASSIGN.payload.assignee`, never the event actor. Request codes come only from scoped stored request rows whose `incident_id` equals this case ID. |
| maintenance | `site_code:string, site_name:string, site_id:string, site_code_key:string, case_id:string, code:string, kind:'MAINTENANCE_REQUEST', revision_id:string, title:string, narrative:string, occurred_at:string, created_at:string, recorded_at:string, state:'OPEN'|'IN_PROGRESS'|'COMPLETED'|'CANCELLED', owner:string|null, asset_id:string|null, asset_label:string|null, incident_id:string|null, record_id:string|null, activity:string|null, outcome_note:string|null, finding_links:Link[], action_links:Link[], source_provenance:object, links:{site:Link,site_maintenance:Link,detail:Link|null}`. Detail href appears only after C2. |
| preventive | `site_code:string, site_name:string, site_id:string, site_code_key:string, canonical_plan_id:string, root_id:string, head_id:string, code:string, title:string, trigger_kind:'CALENDAR'|'RUN_HOURS', next_due_at:string|null, next_due_hours:string|null, state:'DRAFT', asset_id:string|null, asset_label:string|null, root_occurred_at:string, occurred_at:string, recorded_at:string, supersedes_plan_id:string|null, correction_reason:string|null, source_provenance:object, links:{site:Link}`. `root_id` equals `canonical_plan_id`; root code is read from the root row. |
| operational-records | `site_code:string, site_name:string, site_id:string, site_code_key:string, canonical_record_id:string, root_id:string, head_id:string, code:string, kind:'OPERATOR_LOG'|'MANUAL_READING'|'SHIFT_NOTE'|'SITE_VISIT', body:string, root_occurred_at:string, occurred_at:string, recorded_at:string, period_end:string|null, actor_kind:string, actor_id:string, quantity:string|null, unit:string|null, source_document_sha256:string|null, case_id:string|null, case_kind:'INCIDENT'|'MAINTENANCE_REQUEST'|null, case_code:string|null, state:'SUBMITTED', supersedes_record_id:string|null, correction_reason:string|null, source_provenance:object, links:{site:Link,case:Link|null}`. `case` points to request detail only for MAINTENANCE_REQUEST after C2; INCIDENT points to the Site incidents window. |

`Link` is `{label:string,href:string|null}`; backend constructs hrefs from stored Site code and exact selected IDs as in W3/W4, then frontend renders null href as plain text. Finding href requires W4 lineage true; Action href requires exact selected event; no link to Asset: the existing `SITE_ASSET_ROUTE_PATH` is mounted as a battery Health frame, not general Asset detail. Case row incident/Site fallbacks use the same `[from,to)` and `known_at` query as the global page, URL encoded through `siteWorkIncidentsHref`/`siteWorkMaintenanceHref`; request detail uses `/maintenance/requests/{case_id}?site_id={site_code}&known_at={known_at}`. Case Source in the overview uses a real exact Finding link or plain Incident code with `Open Site incidents` href for the same window. No dead anchors.

**Site Work strip manage links (A2/B2).** In `frontend/src/sites/siteWorkCases.tsx`, add `globalWorkManageHref(kind: WorkKind, scope: WorkScope, selectedKnownAt?: string | null): string`. It returns `/incidents` for `kind='incidents'` or `/maintenance` for `kind='maintenance'`, followed by `?from={encodeURIComponent(scope.from)}&to={encodeURIComponent(scope.to)}` and `&known_at={encodeURIComponent(scope.knownAt ?? selectedKnownAt)}` when that cutoff exists. Pass `result.status === 'loaded' ? result.value.known_at : null` as `selectedKnownAt`; an explicit `scope.knownAt` wins. For example, `from=2026-10-15T00:00:00Z`, `to=2026-10-22T00:00:00Z`, and selected `known_at=2026-10-22T12:00:00Z` yield `/incidents?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z` and `/maintenance?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z`. Omit `known_at` only when neither source provides it; never carry the Site cursor or limit. Do not add `site_id` or `site` to these global URLs: the global parser permits only its declared keys and the destination lists all authorized Sites. The Site source remains clear in the strip's `Scoped to {site}` text; the global page must not imply a Site filter. Keep the other strip's unavailable text until its global route exists.

Literal successful envelope example for each root uses this exact outer shape (substitute the row from the four examples below); this example is a **pure contract example**, not a claimed stored row:

```json
{"schema_version":"global-work-index-1","scope":{"tenant_id":"00000000-0000-0000-0000-000000000001","authorized_site_count":1,"covered_site_count":1,"access_basis":"sha256:example"},"window":{"from":"2026-10-15T00:00:00Z","to":"2026-10-22T00:00:00Z","bounds":"[from, to)"},"known_at":"2026-10-22T12:00:00Z","status":"CURRENT","coverage":{"state":"COMPLETE","reason":null,"sites":[{"site_code":"KOBO-001","site_id":"00000000-0000-0000-0000-000000000002","state":"COVERED"}]},"total_count":1,"rows":["<one exact row below>"],"next_cursor":null,"selection_token":"sha256:example"}
```

The row strings below are literal JSON objects to replace the explanatory `rows` string; `sha256:example` is deliberately non-executable example syntax, not a seeded selection token.

```json
{"site_code":"KOBO-001","site_name":"Kobo","site_id":"00000000-0000-0000-0000-000000000002","site_code_key":"kobo-001","case_id":"00000000-0000-0000-0000-000000000003","code":"INC-000001","kind":"INCIDENT","revision_id":"00000000-0000-0000-0000-000000000004","title":"Generator stopped","narrative":"Operator reported a stop.","occurred_at":"2026-10-20T09:00:00Z","created_at":"2026-10-20T09:01:00Z","recorded_at":"2026-10-20T09:01:00Z","state":"OPEN","owner":null,"asset_id":null,"asset_label":null,"incident_id":null,"linked_request_codes":[],"finding_links":[],"action_links":[],"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:example","reasons":[]},"links":{"site":{"label":"Kobo","href":"/sites/KOBO-001"},"site_incidents":{"label":"Site incidents","href":"/sites/KOBO-001/work/incidents?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z"}}}
{"site_code":"KOBO-001","site_name":"Kobo","site_id":"00000000-0000-0000-0000-000000000002","site_code_key":"kobo-001","case_id":"00000000-0000-0000-0000-000000000005","code":"WR-000002","kind":"MAINTENANCE_REQUEST","revision_id":"00000000-0000-0000-0000-000000000006","title":"Inspect starter","narrative":"Inspection requested.","occurred_at":"2026-10-20T10:00:00Z","created_at":"2026-10-20T10:01:00Z","recorded_at":"2026-10-20T10:01:00Z","state":"OPEN","owner":null,"asset_id":null,"asset_label":null,"incident_id":null,"record_id":null,"activity":null,"outcome_note":null,"finding_links":[],"action_links":[],"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:example","reasons":[]},"links":{"site":{"label":"Kobo","href":"/sites/KOBO-001"},"site_maintenance":{"label":"Site maintenance","href":"/sites/KOBO-001/work/maintenance?from=2026-10-15T00%3A00%3A00Z&to=2026-10-22T00%3A00%3A00Z&known_at=2026-10-22T12%3A00%3A00Z"},"detail":null}}
{"site_code":"KOBO-001","site_name":"Kobo","site_id":"00000000-0000-0000-0000-000000000002","site_code_key":"kobo-001","canonical_plan_id":"00000000-0000-0000-0000-000000000007","root_id":"00000000-0000-0000-0000-000000000007","head_id":"00000000-0000-0000-0000-000000000007","code":"PM-000003","title":"Inspect filters","trigger_kind":"CALENDAR","next_due_at":"2026-10-29T00:00:00Z","next_due_hours":null,"state":"DRAFT","asset_id":null,"asset_label":null,"root_occurred_at":"2026-10-20T11:00:00Z","occurred_at":"2026-10-20T11:00:00Z","recorded_at":"2026-10-20T11:01:00Z","supersedes_plan_id":null,"correction_reason":null,"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:example","reasons":[]},"links":{"site":{"label":"Kobo","href":"/sites/KOBO-001"}}}
{"site_code":"KOBO-001","site_name":"Kobo","site_id":"00000000-0000-0000-0000-000000000002","site_code_key":"kobo-001","canonical_record_id":"00000000-0000-0000-0000-000000000008","root_id":"00000000-0000-0000-0000-000000000008","head_id":"00000000-0000-0000-0000-000000000008","code":"REC-000004","kind":"OPERATOR_LOG","body":"Operator checked the panel.","root_occurred_at":"2026-10-20T12:00:00Z","occurred_at":"2026-10-20T12:00:00Z","recorded_at":"2026-10-20T12:01:00Z","period_end":null,"actor_kind":"SERVICE","actor_id":"service:w401-fixture","quantity":null,"unit":null,"source_document_sha256":null,"case_id":null,"case_kind":null,"case_code":null,"state":"SUBMITTED","supersedes_record_id":null,"correction_reason":null,"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:example","reasons":[]},"links":{"site":{"label":"Kobo","href":"/sites/KOBO-001"},"case":null}}
```

**Detail DTO.** C1 adds the new `GET /api/work/requests/{case_id}?site_id={site_code}&known_at={UTC}` route; the merged W4 route is `GET /api/sites/{site_code}/work/cases/{case_id}` (`work_api.py:174`). The page is `/maintenance/requests/{case_id}`. Detail response keeps the existing `work-case-detail-1` body unchanged as nested `work_detail` (including its own `schema_version`, `site_code`, `case`, `selected_revision`, `finding_links`, `action_links`, `cited_accepted_evidence_ids`, `events`, `records`, `source_provenance`, `coverage`). Outer body is `{schema_version:'global-work-detail-1',selected:{site_code,site_id,case_id,case_code,case_kind,known_at},work_detail,history:{revisions:[...],operational_records:[...]},links:{site:Link,overview:Link,record:Link,history:Link}}`. `history.revisions` contains selected correction rows `{id,revision_no,supersedes_revision_id,title,reason,occurred_at,recorded_at,actor_kind,actor_id}` ordered `(recorded_at,id)`; existing `work_detail.events` and `work_detail.records` are the only event and maintenance-record arrays. `history.operational_records` selects scoped `operational_record.case_id` roots/heads at cutoff with `{canonical_record_id,head_id,code,kind,body,root_occurred_at,occurred_at,recorded_at}` (CL3-3). Outer `links` also carries `source_incident: Link|null` (CL3-5). An unknown or unauthorized exact Site uses existing `SITE_NOT_FOUND` 404 / `SITE_SCOPE_FORBIDDEN` 403 from `work_api.py`; an unknown case uses `WORK_CASE_NOT_FOUND` 404. Site detail parity uses one extracted selector inside each route's own snapshot and preserves the Site wire.

Literal detail example, with illustrative IDs/codes and an empty linked history (not a claim of persisted data):

```json
{"schema_version":"global-work-detail-1","selected":{"site_code":"KOBO-001","site_id":"00000000-0000-0000-0000-000000000002","case_id":"00000000-0000-0000-0000-000000000005","case_code":"WR-000002","case_kind":"MAINTENANCE_REQUEST","known_at":"2026-10-22T12:00:00Z"},"work_detail":{"schema_version":"work-case-detail-1","site_code":"KOBO-001","case":{"id":"00000000-0000-0000-0000-000000000005","code":"WR-000002","kind":"MAINTENANCE_REQUEST","asset_id":null,"occurred_at":"2026-10-20T10:00:00.000000Z","created_at":"2026-10-20T10:01:00.000000Z","state":"OPEN","incident_id":null},"selected_revision":{"id":"00000000-0000-0000-0000-000000000006","revision_no":1,"supersedes_revision_id":null,"title":"Inspect starter","narrative":"Inspection requested.","reason":null,"recorded_at":"2026-10-20T10:01:00.000000Z","actor_kind":"SERVICE","actor_id":"service:w401-fixture","occurred_at":"2026-10-20T10:00:00.000000Z"},"finding_links":[],"action_links":[],"cited_accepted_evidence_ids":[],"events":[{"id":"00000000-0000-0000-0000-000000000009","kind":"CREATED","payload":{},"occurred_at":"2026-10-20T10:00:00.000000Z","recorded_at":"2026-10-20T10:01:00.000000Z","actor_kind":"SERVICE","actor_id":"service:w401-fixture"}],"records":[],"source_provenance":{"classification":"UNKNOWN","state":"UNKNOWN","source_ids":[],"evidence_ids":[],"basis_sha256":"sha256:example","reasons":[]},"coverage":{"state":"COMPLETE","reason":null}},"history":{"revisions":[{"id":"00000000-0000-0000-0000-000000000006","revision_no":1,"supersedes_revision_id":null,"title":"Inspect starter","reason":null,"occurred_at":"2026-10-20T10:00:00.000000Z","recorded_at":"2026-10-20T10:01:00.000000Z","actor_kind":"SERVICE","actor_id":"service:w401-fixture"}],"operational_records":[]},"links":{"site":{"label":"Kobo","href":"/sites/KOBO-001"},"overview":{"label":"Overview","href":"/maintenance/requests/00000000-0000-0000-0000-000000000005?site_id=KOBO-001"},"record":{"label":"Maintenance record","href":"/maintenance/requests/00000000-0000-0000-0000-000000000005/record?site_id=KOBO-001"},"history":{"label":"History","href":"/maintenance/requests/00000000-0000-0000-0000-000000000005/history?site_id=KOBO-001"}}}
```

**Refusal/status table.** All refusal bodies are `detail:{code,message}`; list refusals additionally carry `rows:null,total_count:null`. Global list `UNAUTHENTICATED` 401 uses W3 `estate/scope.py` message and Bearer header; new global detail uses merged W4 `work_api.py:74` message and Bearer header. `INVALID_WINDOW` 422 uses W3 parser message; `INVALID_KNOWN_AT` 422, `INVALID_LIMIT` 422, `INVALID_CURSOR` 422 use W3 literals for global roots. `WORK_BASIS_CHANGED` 409 uses existing W4 message `The work list changed; request page one without a cursor.` `WORK_STORE_UNAVAILABLE` 503 uses existing W4 message `Work records could not be read or saved.` Detail only: `SITE_SCOPE_FORBIDDEN` 403 `No access to Site '{code}'.`, `SITE_NOT_FOUND` 404 `No imported Site '{code}' in this tenant.`, `WORK_CASE_NOT_FOUND` 404 `No work case with this ID at this site.`, `INVALID_KNOWN_AT` 422, `WORK_STORE_UNAVAILABLE` 503. A missing CREATED event is a 503 consistency failure. No global list 403/404. UI copy is separately specified below.

| Route | HTTP / code | Exact `message` |
| --- | --- | --- |
| Global lists | 401 `UNAUTHENTICATED` | `Sign in to read estate records.` |
| New global detail | 401 `UNAUTHENTICATED` | `Sign in to read work.` |
| Global lists | 422 `INVALID_WINDOW` | `from and to must be UTC instants in order, at most 31 days apart.` |
| Global lists | 422 `INVALID_KNOWN_AT` | `known_at must be UTC and no later than the read time.` |
| Global lists | 422 `INVALID_LIMIT` | `limit must be an integer from 1 to 100.` |
| Global lists | 422 `INVALID_CURSOR` | `The cursor is not an estate cursor.` (W3 parser literal, including bad `kind`; adapter retains it) |
| Global lists | 409 `WORK_BASIS_CHANGED` | `The work list changed; request page one without a cursor.` |
| All | 503 `WORK_STORE_UNAVAILABLE` | `Work records could not be read or saved.` |
| Detail only | 403 `SITE_SCOPE_FORBIDDEN` | `No access to Site '{code}'.` |
| Detail only | 404 `SITE_NOT_FOUND` | `No imported Site '{code}' in this tenant.` |
| Detail only | 404 `WORK_CASE_NOT_FOUND` | `No work case with this ID at this site.` |
| Detail only | 422 `INVALID_KNOWN_AT` | `'known_at' must be one UTC instant no later than the read time.` (existing W4 detail literal) |

## 2. Literal display and bounds

The v6.9 screen manifest/index and `screens.js` fix slots, hierarchy and labels. New work-specific provenance disclosure literals: AUTHORED_DEMONSTRATION `Prepared example data` / `These authored work records were prepared for an example. They are not physical equipment readings.`; REGISTERED_SIMULATION `Generated test data` / `These authored work records came from a registered simulation. They are not physical equipment readings.`; MIXED `Sources do not agree` / `The selected links do not establish one work source. No work outcome is verified.`; UNKNOWN `Source unverified` / `The origin of this authored work record is not established. No work outcome is verified.` Do not reuse the cost-oriented `SOURCE_WORDS` disclosure.

Shared controls `From (UTC)`, `To (UTC, exclusive)`, `Show records`, `Reload`, `Previous`, `Next`. The page query contract in section 1 applies to all four global pages; captures set `from` and `to` explicitly so the fixture window does not depend on capture date. UI sends `limit=5` for every root; API default 50. Display UTC dates `22 Oct 2026, 12:00 UTC` using `en-GB` and explicit `UTC`, no local-zone conversion. Normal label `As known at {formatted known_at}`; explicit old cutoff `Historical as of {formatted known_at}`. Empty scope `No accessible Sites.`; complete zero per root `No incident cases in this window.`, `No work requests in this window.`, `No draft plans in this window.`, `No operational records in this window.` followed by `Change the UTC window or open a Site record.` Read failure `Work records could not be read. Reload.`; cursor change `The list changed. Reload the first page.`; detail 403 `No access to this Site.`; detail 404 `No work case with this ID at this site.` `PARTIAL` is never a live state; a pure snapshot may show `Some Sites could not be read. Counts are unavailable.` with `total_count:null`. A failed store is never rendered as zero.

Every page h1/h2, code, actor, reason, notice and table cell uses `min-width:0; overflow-wrap:anywhere`; table stays within a panel-local horizontal scroll area at 390, with visible `Scroll table horizontally` affordance. A 200-character unbroken title wraps; no silent truncation. Narrative and 4000-character table text show a three-line preview (`line-clamp:3`) and a named `<details><summary>Full {title|narrative|activity|event|record} text</summary>…</details>` with the full escaped value. Expanded disclosure may grow the page and is exempt from collapsed caps. UUID/128-character actor cells wrap, never widen the document. Panel `max-height` caps below apply to collapsed state; overflowing table body scrolls vertically within the panel, with headers visible. Caps are design limits checked against `.agent/W6-01-mock-measure-2.md` on the mock with injected stress data, **not browser-verified implementation results**. Wrap each table-cell value in a block carrying the three-line clamp; `line-clamp` on `td` itself does not clamp. Caps exclude expanded `<details>` content.

| Screen / slot | cap 1440 px | cap 390 px | Exact binding / copy |
| --- | ---: | ---: | --- |
| incidents cards | 150 | 310 | `Open incidents` OPEN+IN_PROGRESS; `High severity` / `Awaiting evidence` / `Closed verified` = `Not assessed` with `Severity is not recorded on work cases` / `No case evidence review state` / `Closed does not verify an outcome`. |
| incidents `Incident cases` | 600 | 690 | Columns `Incident, Site, Start, Severity, State, Owner, Findings / work`; 5 rows/page; `Not recorded` severity; owner latest selected ASSIGN payload assignee or `Not assigned`; linked IDs only if scoped. Footer slot replaces mock states footer with `An incident connects authored events and linked records; a gap alone does not create a case.` |
| incidents `Case boundaries` | 140 | 180 | `A closed case records a workflow step. Cause and outcome need their own evidence.` |
| maintenance cards | 180 | 340 | `Open work` OPEN+IN_PROGRESS; others `Not assessed` with `No frozen work verification plan` / `Open Preventive to inspect authored due facts` / `No repeat-finding assessment`. Before B3 the Preventive card is plain text `Preventive plans open in a later unit.` without the unavailable phrase; only the Preventive tab uses `UnavailableTab`, so B2 adds exactly one `$expectedTabs` multiset entry. |
| maintenance `Corrective work requests` | 610 | 690 | Columns `Work request, Asset / site, Owner, State, Verification, Warranty`; `Not established` verification; `Not recorded` warranty. Before C2 row links to exact-window Site maintenance; after C2 to exact request. Footer `Completed work is activity evidence only; outcome is verified separately.` |
| maintenance notice | 90 | 140 | Replace mock lifecycle notice: `A work request records activity. Completion does not verify an equipment outcome.` |
| preventive status strip | 70 | 130 | `Draft plans · due facts are authored, not automatically scheduled`. |
| preventive cards | 150 | 310 | `Plan records` full selected count; `Overdue`, `Due in 14 days` = `Not assessed`; `Feeds evidence` = `Not established`; `Draft plans have no active due evaluator.` |
| preventive `Preventive plan` | 600 | 690 | Columns `Plan item, Asset / site, Trigger, Last done, Next due, State, What it proves`; `Calendar`/`Running hours`, `Not linked`, due date/hours/`Not set`, `Draft`, `Nothing verified by this plan`. Footer `A draft plan is an authored intention. A performed record and later evidence are separate.` |
| preventive notice | 90 | 140 | Replace mock PM-0455 incident story: `No incident link is established by a draft plan.` |
| request header (h1/subtitle plus `mheader`) / tabs | 380 / 90 | 860 / 150 | Stored title and `{WR code} · {Site name} · corrective`; Owner = latest ASSIGN payload assignee or `Not assigned`; `Due / SLA: Not set`; State + `· outcome not established`; Source exact Finding or plain Incident; `Success criterion: Not recorded`. The `mheader` alone is capped at 150 / 400; Owner and Source use a two-line preview with `<details><summary>Full owner text</summary>` or `<details><summary>Full source text</summary>` for the complete escaped value. Stored h1 title wraps through 200 characters without truncation; 380 / 860 follows measured 363 / 844. Tabs obey per-unit rules below. |
| overview `Work done` / `Lifecycle` | 430 / 350 | 510 / 300 | Selected narrative and latest performed activity or `No maintenance activity recorded`; `Warranty not recorded`; lifecycle `Open → In progress → Completed`, or `Cancelled · work stopped` for CANCELLED. Footer `Completed is not Verified. No work-case outcome evaluator is available.` |
| record `Maintenance record · activity` | 650 | 780 | Selected correction heads only: walk each `supersedes_record_id` chain, show latest at cutoff; superseded entries in `<details><summary>Earlier record versions</summary>…</details>`. Activity row `Recorded` / `Authored maintenance record`; outcome note row `Unverified` / `Authored note`. Empty `No maintenance activity recorded`. Footer `What was recorded on site; no outcome verification follows from this entry.` |
| record notice | 100 | 150 | If linked via `operational_record.case_id`, list exact REC codes as authored links to `/operational-records` filtered window; otherwise `No linked Operational record.` Relation exists in `0027`. |
| history `History` | 600 | 690 | Five rows/page, `(recorded_at,id)` ascending; Event labels `CREATED: Created`, `ASSIGN: Assigned`, `COMPLETE: Completed`, `COMMENT: Commented`, `CLOSE: Closed`, `REOPEN: Reopened`, `CANCEL: Cancelled`, revision successor `Correction`; By = stored actor ID. Time is recorded UTC; `<details><summary>Occurrence time</summary>Occurred {formatted occurred_at}</details>`. Missing CREATED => 503. |
| oprecords cards | 150 | 330 | `Records in window` follows active `kind` filter; `Feeding evidence: Not established`; `In review: No review workflow`; `Requested, not yet done: Not recorded`. Subcopy `Authored records only`; `No accepted-evidence publication link`; `All stored records are Submitted`; `Requests are not OperationalRecord rows`. |
| oprecords kind chips | 40 | 80 | Fixed five labels above; wrap inside the chip row without document overflow. |
| oprecords `Operational records` | 650 | 780 | Five rows/page; chips `All, Operator log, Manual reading, Shift note, Site visit` map to `kind=all|OPERATOR_LOG|MANUAL_READING|SHIFT_NOTE|SITE_VISIT`; filtered `total_count` and card agree. Columns `Record, Type, Site, When, By, What it says, Feeds, State`; `Submitted` only. For INC case `Feeds` links Site incidents window. Footer `Authored records and the cases they name; evidence acceptance is separate.` |
| oprecords `Record a manual reading` / `How records are used` | 180 / 330 | 230 / 300 | No browser write. Replace form with `Recording requires an authorized work service.` and `Manual readings cannot be submitted from this page.` Remove mock `Fills REC-307 when submitted`. Explanation `People can author records. They remain separate from accepted equipment readings and do not fill missing evidence.` |

New UI elements absent from the mock (shared control bar, pager, `As known at` line, empty/refusal/cursor-changed blocks, collapsed disclosures and `Scroll table horizontally` affordance) receive a provisional cap of 180 / 300 px per element at 1440 / 390, except the status line at 70 / 130. A2 first capture measures and records each element at both widths; if any exceeds its cap, adjust layout/copy and amend the cap with the measured result before A2 review. Later units repeat for newly mounted elements.

## 3. Unit cards and ownership

One builder run and 1–3 commits per unit. Each page unit has two sequential dispatches within that run: Lane B page/domain files, then Lane A integration on the same branch. Every unit below touches a shared route, guard or API and gets independent per-unit review before its successor. Captures belong to its page unit. All backend tests use a private `*_test` DB and clean up; all new byte-pinned fixtures need `.gitattributes` `eol=lf`. One full suite per slice after focused tests. File lists are exhaustive; an unlisted edit requires an Architect amendment before building.

| Unit | Literal owned files, behavior and producer | Focused test names / captures |
| --- | --- | --- |
| **A1** | Lane B `backend/assetops_backend/work/global_index.py`, `work/adapters/postgres_global_read.py`, `global_work_api.py`, `backend/tests/test_w601a_global_incidents.py`, `tools/w601_seed.py`; Lane A `backend/README-db.md`, `backend/assetops_backend/main.py`, `backend/assetops_backend/work/composition.py`, `tools/checks/configuration-persistence.ps1` (A1Q, §3.1 G1–G3: one `$pgReaders` line, `build_global_work_read` / `build_global_work_index_service`, the `main.py` mount). Build `/api/work/incidents`, HMAC cursor, scope/refusals/row DTO from §1 with the §3.1 Q3–Q9 rulings. Seed helper calls real W4 service against private DB, never browser-supplied SERVICE actor. | `test_w601a_global_incidents.py`: missing/malformed cursor key, authorized/denied Site, two tenants, complete zero, same-time UUID tie, selected revision/ASSIGN, historical, cursor MAC and changed selection, 401/409/422/503; no list 403/404; §3.1 tests `test_missing_lineage_matches_site_row`, `test_continuation_status_follows_page_one`, `test_page_two_known_at_wire_second`, `test_candidates_imported_before_to`, `test_linked_request_codes_order`, `test_site_incidents_link_carries_response_known_at`, `test_read_clock_override_pins_read_at`. `tools/check-all.ps1` after Lane A. A1Q2: R1 seed imports per amended G6(c); `empty_scope` is an access-callback fixture (R4); no `linked` fixture (R2, moved to B1). **Reopened by A2Q1:** `state_counts` in `work/global_index.py` and `test_state_counts_cover_full_selection`; independent review before A2. |
| **A2** | Lane B `frontend/src/work/{GlobalIncidents.tsx,globalWorkClient.ts,globalWork.css,__tests__/globalIncidents.test.tsx}`. Lane A atomically `frontend/src/App.tsx`, `frontend/src/shell/OperatorShellLayout.tsx`, `frontend/src/sites/siteWorkCases.tsx`, `frontend/src/sites/__tests__/siteWorkCases.test.tsx`, `frontend/src/shell/__tests__/{operatorRailInventory.test.tsx,operatorRouteFrames.test.tsx,w301EstateShellRoutes.test.tsx}`, `frontend/src/estate/__tests__/estatePortfolioRoutes.test.tsx`, `tools/checks/{navigation-truthfulness.ps1,navigation-rail-fixtures.ps1,missing-claim-scan.mjs}`, `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F1–F5 rail, fixture, route-constant and ledger literals). Route `/incidents`; remove Incidents unavailable fixture. In the Site Work incident strip replace `Manage in Incidents · Not available yet` with linked `Manage in Incidents`. Set `WORK_CONTEXT_NOTICE` to `Case history is stored with this site. Incidents can be managed globally. Global Maintenance and the create flow are not available yet.` Update the `WORK_CONTEXT_NOTICE` exact exemption in `tools/checks/missing-claim-scan.mjs`. Keep `WORK_MANAGE_UNAVAILABLE_STATUS = "Not available yet"` in `frontend/src/sites/siteWorkCases.tsx` and its exact exemption in `tools/checks/missing-claim-scan.mjs`: the Maintenance strip still uses both until B2. Pin the Incidents link href, the remaining Maintenance unavailable text, and the notice in `frontend/src/sites/__tests__/siteWorkCases.test.tsx`. | `globalIncidents.test.tsx`, `siteWorkCases.test.tsx`; captures positive/zero/historical/refused/cursor-changed at 1440/390, 5 rows, title200/actor128/UUID/reason; no linked or empty-scope capture, `No accessible Sites.` is a typed-response test only (A1Q2 R2/R4). A2Q (section 3.1): Lane B also owns `tools/w601_seed.py` for the additive `stress` fixture (A2Q2); cards from `state_counts` and render rule (A2Q1); capture clock `2026-10-21T12:00:00Z`, window `2026-10-14..2026-10-21` (A2Q3); source line (A2Q4); URL-only cutoff (A2Q5); refusal copy table (A2Q6); footer in Panel `description` (A2Q7); cell literals (A2Q8); registry reason substring edit on `incidents:1,2` (A2Q9); cursor URL plus `globalWorkTrail`, hidden-not-disabled pager, `Showing {a}–{b} of {N}` (A2Q10). `tools/check-all.ps1`, registry checker. CL3-1 loading `Loading the incidents across the estate.`. |
| **B1** | Lane B `work/global_index.py`, `work/adapters/postgres_global_read.py`, `global_work_api.py`, `backend/tests/test_w601b_global_maintenance.py`, `tools/w601_seed.py`. No guard, composition or `main.py` edit (A1Q G4: the routes extend A1's `build_global_work_router` and `GlobalWorkIndexService.read`; the reader is already in `$pgReaders`). Routes `/api/work/maintenance`, `/api/work/preventive`; W4 `post_plan`, correction, request/record/COMPLETE. No DDL or due evaluator. | `test_w601b_global_maintenance.py`: root-window/head crossing, DRAFT, owner payload, scoped links, cursor/refusal; A1Q2 R2 `--fixture linked` in `tools/w601_seed.py` and `test_linked_finding_and_action_hrefs`; R3 basis rule for new row fields; A2Q X1 maintenance `state_counts` + `test_state_counts_cover_full_selection`; X2 `stress` extension (request, record, correction, plan); X9 `detail` fixture events `CREATED, ASSIGN, COMMENT, COMPLETE, REOPEN`, a correction, and a second request with `CANCEL`. CL3-4 `historical` fixture plan + correction (`Due date corrected after review`) and `test_plan_correction_historical_head`. |
| **B2** | Lane B `frontend/src/work/{GlobalMaintenance.tsx,globalWorkClient.ts,globalWork.css,__tests__/globalMaintenance.test.tsx}`. Lane A `frontend/src/App.tsx`, `frontend/src/shell/OperatorShellLayout.tsx`, `frontend/src/shell/__tests__/{operatorRailInventory.test.tsx,operatorRouteFrames.test.tsx,w301EstateShellRoutes.test.tsx}`, `frontend/src/estate/__tests__/estatePortfolioRoutes.test.tsx`, `frontend/src/sites/siteWorkCases.tsx`, `frontend/src/sites/__tests__/siteWorkCases.test.tsx`, `tools/checks/{navigation-truthfulness.ps1,navigation-rail-fixtures.ps1,missing-claim-scan.mjs}`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F1–F5; the Preventive tab literal is F4). Route `/maintenance`; in Site Work maintenance strip replace `Manage in Maintenance · Not available yet` with linked `Manage in Maintenance`. Set `WORK_CONTEXT_NOTICE` to `Case history is stored with this site. Incidents and Maintenance can be managed globally. The create flow is not available yet.` Update the `WORK_CONTEXT_NOTICE` exact exemption in `tools/checks/missing-claim-scan.mjs`; now that both strips link to live routes, remove `WORK_MANAGE_UNAVAILABLE_STATUS` from `frontend/src/sites/siteWorkCases.tsx` and remove its exact exemption from `tools/checks/missing-claim-scan.mjs`. Pin both link hrefs, the absence of the unavailable strip text, and the notice in `frontend/src/sites/__tests__/siteWorkCases.test.tsx`. Before B3 the Preventive scheduled tab is one `UnavailableTab` with one `$expectedTabs` entry; its card uses the plain text in section 2, no second unavailable entry. `UnavailableEntry.tsx` exports `UnavailableTab` and `UnavailableChip`, not a card. | `globalMaintenance.test.tsx`, `siteWorkCases.test.tsx`, guard fixtures; positive/zero/historical/refused/long actor captures at both widths, plus `maintenance-linked` from B1's `linked` fixture (A1Q2 R2). A2Q X1/X3–X8: `Open work` from `state_counts`, A2Q3 clock, A2Q6 copy, footer as Panel `description`, `maintenance:1` reason edit, A2Q10 pager, X8 cell literals; long actor from B1 `stress`. CL3-1 loading `Loading the work requests across the estate.`; CL3-2 card label `Preventive due in 30 days`, value `Not assessed`, plain note until B3. |
| **B3** | Lane B `frontend/src/work/{GlobalPreventive.tsx,globalWorkClient.ts,globalWork.css,__tests__/globalPreventive.test.tsx}`. Lane A `frontend/src/App.tsx`, `tools/checks/navigation-truthfulness.ps1`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F3–F5). Route `/maintenance/preventive`; promote B2 tab and card atomically, remove the tab single `$expectedTabs` entry. | `globalPreventive.test.tsx`; DRAFT/corrected historical/zero/503/long PM captures at both widths; guard. A2Q X1–X8: `Plan records`=`total_count`, long PM from B1 `stress`, A2Q3 clock, A2Q6 copy, footer as Panel `description`, `maintenance-preventive:1` reason edit, A2Q10 pager, X8 cells. CL3: Lane A also `frontend/src/work/GlobalMaintenance.tsx`, `frontend/src/work/__tests__/globalMaintenance.test.tsx` (CL3-2 card link `Open Preventive to inspect authored due facts` to `/maintenance/preventive?from=&to=[&known_at=]`, live tab, `preventive_card_and_tab_link_after_b3`); loading `Loading the preventive plans across the estate.`; producer CL3-4; no `missing-claim-scan.mjs` or `operatorRouteFrames.test.tsx` edit (CL3-7). |
| **C1** | Lane B `backend/assetops_backend/work/{global_detail.py,detail.py,adapters/postgres_global_read.py}`, `backend/assetops_backend/global_work_api.py`, `backend/tests/test_w601c_request_detail.py`; Lane A `backend/assetops_backend/work/composition.py`, `backend/assetops_backend/main.py` (A1Q G5: `build_global_work_detail_service`, router kwargs `details=` and `scope=`). Extract selector into shared `select_case_detail(rx,tenant_id,site_id,site_code,case_id,known_at)`; Site and global routes use it in their own snapshots. API `/api/work/requests/{case_id}?site_id={site_code}&known_at=` checks exact Site scope before case. | `test_w601c_request_detail.py`: Site parity, corrected ordering, case_id-linked operational rows, wrong Site/tenant, missing CREATED 503; A2Q X4 `test_missing_site_id_or_bad_case_id_is_404`. CL3: Lane B also `tools/w601_seed.py` (CL3-3 case-linked OPERATOR_LOG on the first `detail` request); wire `history.operational_records[].root_occurred_at`, `links.source_incident`; tests `test_case_linked_operational_record_root_time`, `test_source_incident_link`. |
| **C2** | Lane B `frontend/src/work/{WorkRequestOverview.tsx,workRequestShared.tsx,globalWorkClient.ts,globalWork.css,__tests__/workRequestOverview.test.tsx}`. Lane A `frontend/src/App.tsx`, `tools/checks/navigation-truthfulness.ps1`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F3–F5). Route `/maintenance/requests/{case_id}` with `site_id={site_code}` query. Tabs Overview exact; Maintenance record, History, Verification via `UnavailableEntry` `Not available yet`, each in `$expectedTabs`. No disabled tab or unbuilt href. | `workRequestOverview.test.tsx`; positive/historical/403/404/long narrative captures at both widths; guard. A2Q X2–X6: long narrative and UUID header from B1 `stress`, A2Q3 clock, A2Q6 401/422/503 copy and no-fetch 404 without `site_id`, footers as Panel `description`, `wr-overview:1,2` reason edit. CL3: loading `Loading the work request.`; header/Work done field map CL3-5; no `missing-claim-scan.mjs` or `operatorRouteFrames.test.tsx` edit (CL3-7). |
| **C3** | Lane B `frontend/src/work/{WorkRequestRecord.tsx,workRequestShared.tsx,globalWork.css,__tests__/workRequestRecord.test.tsx}`. Lane A `frontend/src/App.tsx`, `tools/checks/navigation-truthfulness.ps1`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F3–F5). Route `/maintenance/requests/{case_id}/record`; promote Record tab and remove its `$expectedTabs` entry. | `workRequestRecord.test.tsx`: selected correction head, superseded disclosure, linked REC, empty, 4000-char activity; captures at both widths. A2Q X2–X7: activity from B1 `stress`, A2Q3 clock, A2Q6 copy, footer as Panel `description`, `wr-record:1` reason edit, no pager. CL3: loading `Loading the work request.`; linked REC from C1 `detail` producer, empty from the `CANCEL` request, REC href CL3-3 and `linked_rec_filtered_window_href`; no scan or route-frame test edit (CL3-7). |
| **C4** | Lane B `frontend/src/work/{WorkRequestHistory.tsx,workRequestShared.tsx,globalWork.css,__tests__/workRequestHistory.test.tsx}`. Lane A `frontend/src/App.tsx`, `tools/checks/navigation-truthfulness.ps1`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F3–F5). Route `/maintenance/requests/{case_id}/history`; promote History tab and remove its `$expectedTabs` entry. Verification remains `UnavailableEntry`. | `workRequestHistory.test.tsx`: all seven labels (`history_labels_all_seven`, typed DTO; X9), same-time order, occurrence disclosure, historical/refused; captures at both widths from B1 `detail` and `stress` (reason row). A2Q X3/X4/X6/X7: A2Q3 clock, A2Q6 copy, `wr-history:1` reason edit, client-side five-row pager with `Showing` line. CL3: loading `Loading the work request.`; no scan or route-frame test edit (CL3-7). |
| **E1** | Lane B `backend/assetops_backend/work/{operational_index.py,global_index.py,adapters/postgres_global_read.py}`, `backend/assetops_backend/global_work_api.py`, `backend/tests/test_w601e_operational_index.py`, `tools/w601_seed.py`. No guard, composition or `main.py` edit (A1Q G4: `GlobalWorkIndexService.read` in `global_index.py` dispatches kind `operational-records` to `operational_index.select_operational`). `/api/work/operational-records?kind=...`; full lineage, filter before `total_count`/cursor. Existing POST is untouched. | `test_w601e_operational_index.py`: four kinds, correction root/head, case_id, scope, 31-day window, HMAC/filter/count, 503; `state_counts:null`; A2Q X2 `stress` OPERATOR_LOG 4000-char body. |
| **E2** | Lane B `frontend/src/work/{OperationalRecords.tsx,globalWorkClient.ts,globalWork.css,__tests__/operationalRecords.test.tsx}`. Lane A `frontend/src/App.tsx`, `frontend/src/shell/OperatorShellLayout.tsx`, `frontend/src/shell/__tests__/{operatorRailInventory.test.tsx,operatorRouteFrames.test.tsx,w301EstateShellRoutes.test.tsx}`, `frontend/src/estate/__tests__/estatePortfolioRoutes.test.tsx`, `tools/checks/{navigation-truthfulness.ps1,navigation-rail-fixtures.ps1}`, registry JSON, `frontend/src/shell/operatorSiteRoutes.ts`, `frontend/docs/architecture/v69-screen-ledger.json` (A1Q, §3.1 F1–F5). Route `/operational-records`; read-only gap in §2, no write capture. | `operationalRecords.test.tsx`; positive/zero/filtered/historical/read-503/long body captures at both widths; guard. A2Q X1–X8: `Records in window`=`total_count`, long body from E1 `stress`, A2Q3 clock, A2Q6 copy, footer as Panel `description`, `oprecords:1,3` reason edit, A2Q10 pager reset on kind chip, X8 cells. CL3: loading `Loading the operational records across the estate.`; invalid `kind` and filtered-zero literals CL3-6 with `kind_invalid_and_filtered_zero`; no `missing-claim-scan.mjs` edit; `operatorRouteFrames.test.tsx` already listed for the rail (CL3-7). |

### 3.1 A1Q amendment: A1 builder rulings and guard/composition ownership

*Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.* Source questions: `.agent/W6-01a-phase-handoff.md` Q1–Q9. Every guard literal below was checked against `tools/checks/*` on `plan/W6-01-a1q` (base `25814281`). The unit cards above name these files; this subsection gives the literal edits. Nothing here changes the §1 wire, the §2 copy or any W4 identity.

**G1 (Q1). Reader registration.** A1 Lane A replaces `tools/checks/configuration-persistence.ps1` lines 832–836 with exactly:

```powershell
    # W4-01 Run 3 ruling 7: the work read adapter is a named reader (no write; the work store stays the sole writer).
    $pgReaders = @("$backendRoot/estate/adapters/postgres_estate_read.py", "$backendRoot/estate/adapters/postgres_evidence_money_read.py",
        "$backendRoot/work/adapters/postgres_work_read.py",
        # W6-01a A1Q G1: the read-only global work reader; the SQL-write refusal still applies to it.
        "$backendRoot/work/adapters/postgres_global_read.py",
        # W4-02 unit 5 (closure 1 Q25): the read-only mini-depth reader; the SQL-write refusal still applies to it.
        "$backendRoot/mini_depth/read.py")
```

No other line of that guard changes. The global reader is not a writer: it issues only `SET TRANSACTION READ ONLY` and `SELECT`, and rule 8 still refuses any extracted write in it. No new guard self-test is added (the W4 `postgres_work_read.py` entry is the precedent); `tools/check-all.ps1` must pass all 11 guards after Lane A.

**G2 (Q2). Adapter, service and composition.** Only `work/composition.py` may import a work adapter (rule 1, `configuration-persistence.ps1:167-177` domain entry, `:193-252` check). The A1 shapes are:

- `work/adapters/postgres_global_read.py`: `class PostgresGlobalWorkRead` with `__init__(self, database_url: str | None, *, link_rows: Callable[[Connection, UUID, UUID, list[str]], list[Any]] | None = None, ports: LinkReadPorts | None = None, statement_timeout_ms: int = 30_000, test_read_clock_override: Callable[[], datetime] | None = None)`, `snapshot(self, work: Callable[[GlobalReadTx], Any]) -> Any` and `dispose(self) -> None`. `snapshot` opens one connection with `isolation_level="REPEATABLE READ"`, runs `SET TRANSACTION READ ONLY`, fixes `read_at` (Q6) and maps `OperationalError`/`DBAPIError` to `WorkStoreUnavailable` exactly as `PostgresWorkRead.snapshot` (`postgres_work_read.py:287-300`). `class GlobalReadTx` exposes `read_at`, `imported_sites(tenant_id, to)` (Q5), `site(tenant_id, site_id, site_code) -> _ReadTx` and `linked_request_codes(tenant_id, site_id, case_id, known_at)` (Q7). `site(...)` returns the merged W4 `_ReadTx(c, tenant_id, site_id, site_code, read_at, link_rows, ports)` on the same connection, imported from the sibling adapter `work/adapters/postgres_work_read.py` (rule 1 admits a sibling adapter import). Every per-Site W4 read (`eligible_cases`, `revisions`, `events`, `records`, `revision_links`, `link_selections`, `lineage_evidence`, `link_rows`, `action_window`) is reused through it, never copied. The module imports no `estate/adapters` module: rule 1 refuses a cross-domain adapter import, so the Q5 SQL is copied.
- `work/global_index.py`: `class GlobalWorkIndexService` with `__init__(self, reads: Any)` and `read(self, tenant_id: UUID | None, kind: str, request: GlobalWorkRequest, admit: Callable[[str], bool]) -> dict[str, Any]`. A1 accepts kind `incidents` only; B1 adds `maintenance` and `preventive`; E1 adds `operational-records`. It reads `ASSETOPS_WORK_CURSOR_KEY_HEX` through `os.environ` and reuses `estate.scope.{access_basis,wire_time,token_time,encode_cursor}`, which are not adapters.
- `global_work_api.py`: `def build_global_work_router(service: GlobalWorkIndexService | None, tenant: Callable[[], UUID | None], *, authenticate: Authenticate = development_authenticate, access: Access = development_access, unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter`, with `Authenticate`/`development_authenticate` imported from `assetops_backend.estate_api` and `Access`/`development_access` from `assetops_backend.finding_api`. `service is None` answers 503 `WORK_STORE_UNAVAILABLE` with `rows:null,total_count:null`, never an empty list. `admit(code)` is `access(request, code) is None`, as in `estate_api.py`.
- `work/composition.py` (append, and add both names to `__all__`):

```python
def build_global_work_read(database_url: str | None) -> PostgresGlobalWorkRead:
    """W6-01a: the cross-Site read over the W4 per-Site selection reads, on one snapshot connection."""
    return PostgresGlobalWorkRead(database_url, link_rows=build_link_rows_reader(), ports=_link_read_ports())


def build_global_work_index_service(database_url: str | None) -> GlobalWorkIndexService | None:
    """W6-01a: None without a product database; the router answers 503, never an empty list."""
    return None if not database_url else GlobalWorkIndexService(build_global_work_read(database_url))
```

with `from assetops_backend.work.adapters.postgres_global_read import PostgresGlobalWorkRead` and `from assetops_backend.work.global_index import GlobalWorkIndexService` at the top.
- `main.py`: extend the `work.composition` import (lines 76–77) with `build_global_work_index_service`, add `from assetops_backend.global_work_api import build_global_work_router`, and directly after the W4 `app.include_router(build_work_router(...))` call add:

```python
    # W6-01a (Lane A): the read-only global work roots `/api/work/{incidents,...}`; tenant from the server registry
    # only, per-Site admission through the Finding-route access seam; typed 503 without a database or cursor key.
    app.include_router(build_global_work_router(
        build_global_work_index_service(database_url()), registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
```

**G3. A1 key documentation.** `backend/README-db.md` gains, directly after the estate Portfolio key lines (40–44), the same block for `ASSETOPS_WORK_CURSOR_KEY_HEX`: the POSIX `export ASSETOPS_WORK_CURSOR_KEY_HEX="$(python -c 'import secrets; print(secrets.token_hex(32))')"` line and the commented PowerShell `$env:` line. The existing do-not-print rule covers it.

**G4. B1 and E1 add no wiring.** B1 and E1 add routes inside `build_global_work_router` and kinds inside `GlobalWorkIndexService.read`, and add SQL only in `work/adapters/postgres_global_read.py`, which G1 already registers. E1 keeps its selection in `work/operational_index.py` as `select_operational(rx, tenant_id, sites, request, known_at)`, and `global_index.py` dispatches kind `operational-records` to it (E1 owns `global_index.py` for that one dispatch). Neither unit edits `configuration-persistence.ps1`, `work/composition.py` or `main.py`.

**G5. C1 wiring.** C1 Lane A appends to `work/composition.py`:

```python
def build_global_work_detail_service(database_url: str | None) -> GlobalWorkDetailService | None:
    """W6-01c: the exact request detail on the global read; None without a product database (503)."""
    return None if not database_url else GlobalWorkDetailService(build_global_work_read(database_url))
```

with `from assetops_backend.work.global_detail import GlobalWorkDetailService`, and adds it to `__all__`. `build_global_work_router` gains `details: GlobalWorkDetailService | None = None, scope: Scope | None = None` (`Scope` from `finding_api`). The detail route resolves its Site exactly like `work_api.read_scope` (`work_api.py:71-84`): `access(request, site_code)` gives 401 `Sign in to read work.` or 403 `SITE_SCOPE_FORBIDDEN`, then `scope(site_code)` gives 503 or 404 `SITE_NOT_FOUND`. If `details is None or scope is None`, the route answers 503 `WORK_STORE_UNAVAILABLE`. In `main.py` the A1 call becomes `build_global_work_router(build_global_work_index_service(database_url()), registry_tenant(registry), access=development_access, unavailable=(SiteStoreUnavailable,), details=build_global_work_detail_service(database_url()), scope=registry.ledger_scope)`.

**G6. Backend guard literals every backend unit obeys.** (a) `work` is a `$domains` entry (`configuration-persistence.ps1:170-177`), so `work/global_index.py`, `work/global_detail.py`, `work/operational_index.py` and `work/detail.py` hold no `sqlalchemy`, `psycopg`, `alembic`, `yaml`, `pathlib` or `sqlite3` import and no text matching `open\(` in any letter case (rule 2, `:254-305`). The pattern has no word boundary, so identifiers such as `is_open(` or `reopen(` also fail. (b) `global_work_api.py` is scanned as an HTTP module (`:1533-1550`) and must contain none of `register_publication`, `register_authored`, `register_run`, `authored_record`, `simulation_records`, `publish_source`, `evidence_publication`, `batch_publication_link`, `run_attestation`, `evidence.publication`, `runs.source_publication`. (c) `tools/w601_seed.py`: superseded by A1Q2 R1 below.

**Q3. Row provenance.** Yes. Each case row's `source_provenance` is computed exactly as the Site row (`work/site_index.py:220-237`): `selections = rx.link_selections(revision_id, from, to, known_at)` with the global window; `selected, cited = case_basis(rx, links, revision_id, event_ids, record_id)`, where `record_id` is the last `rx.records(case_id, known_at)` row or null; `dto = provenance_dto(rx, tenant_id, site_id, cited, selected)`; and `dto = missing_lineage(dto)` iff `not all(s["lineage"] for s in selections)`. Test `test_missing_lineage_matches_site_row` seeds one case with a link whose lineage is absent and asserts the global row DTO equals the W4 Site list row DTO for the same window and `known_at`.

**Q4. Status and cutoff on continuation pages.** Page one: `status` is `EMPTY_SCOPE` when zero Sites are authorized; otherwise `HISTORICAL` iff the request carries `known_at` and `known_at < read_at`; otherwise `CURRENT`. The cursor payload gains `page_one_mode: 'current'|'historical'` (bound by the MAC), and every continuation page returns that mode's status (`EMPTY_SCOPE` cannot continue). Neither the W4 explicit-only label nor the estate `k < read_at` label is reused for continuations. The page-two cutoff follows the estate wire-second rule (`estate/index.py:150-158`). The effective `k` is the cursor's six-digit cutoff. An explicit page-two `known_at` must equal it exactly, or have `microsecond == 0` and equal it truncated to the second; otherwise the response is 409 `WORK_BASIS_CHANGED`. A cursor cutoff later than `read_at` is also 409. Response `known_at` is `wire_time(k)` (whole seconds, truncated). Tests: `test_continuation_status_follows_page_one` checks that a current page one followed by a page two that omits `known_at` stays `CURRENT`, and a historical page one followed by the same stays `HISTORICAL`. `test_page_two_known_at_wire_second` checks that the whole-second copy is admitted and another instant gets 409.

**Q5. Authorized-Site candidates.** Yes, verbatim estate predicate and order, copied into `GlobalReadTx.imported_sites`: `SELECT s.id, s.site_code, s.name, s.site_type, s.site_code_key FROM site s WHERE s.tenant_id = :t AND EXISTS (SELECT 1 FROM site_import i WHERE i.tenant_id = s.tenant_id AND i.site_id = s.id AND i.imported_at < :to) ORDER BY s.site_code_key, s.id`, `:to` being the window `to`. There is no `known_at` predicate, which keeps W3 parity. Inactive imported Sites are included. A null tenant gives zero candidates. Each candidate is admitted by `admit(site_code)`, and only admitted IDs enter `access_basis`, counts, rows and the cursor. Test `test_candidates_imported_before_to`.

**Q6. Read time.** Use the W4 form: `read_at = c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(timezone.utc)`, read once per snapshot. `test_read_clock_override`, when set, is called once instead and asserted UTC. Only the constructor kwarg supplies it: no request, environment variable or `main.py` path sets it. The pinned pytest reads (`12:00:02Z` current, `12:00:00Z` historical) construct `PostgresGlobalWorkRead(..., test_read_clock_override=...)` directly. Test `test_read_clock_override_pins_read_at`.

**Q7. Link labels and request-code order.** Build each Link with the merged helpers and keep only `label` and `href`. `finding_links[i]` is `{label, href}` of `site_index._finding_link(site_code, link, lineage)`, which gives label `Finding {finding_id[:8]}` and an href only when that link's selection lineage is true. `action_links[i]` is `{label, href}` of `site_index._action_link(site_code, link, selection)`, with label `Action {action_id[:8]}`. `global_index.py` imports the two private helpers and does not edit `site_index.py`. Order: findings by `(finding_id, finding_revision_id)` ascending, actions by `(action_id, action_event_id)` ascending (`site_index.py:238-239`). `linked_request_codes` comes from `SELECT c.public_code FROM maintenance_work_request r JOIN work_case c ON c.tenant_id = r.tenant_id AND c.site_id = r.site_id AND c.id = r.id WHERE r.tenant_id = :t AND r.site_id = :s AND r.incident_id = :i AND c.kind = 'MAINTENANCE_REQUEST' AND c.created_at <= :k AND EXISTS (SELECT 1 FROM work_case_revision v WHERE v.tenant_id = c.tenant_id AND v.site_id = c.site_id AND v.case_id = c.id AND v.recorded_at <= :k) ORDER BY c.created_at, c.id`. It has no window filter. Test `test_linked_request_codes_order`.

**Q8. Site fallback cutoff.** Always the response `known_at`. `links.site_incidents.href` (and B1's `links.site_maintenance.href`) carries `from`, `to` and the response `known_at` string, URL-encoded through the §1 helpers, on every page and whether or not the request supplied `known_at`. Test `test_site_incidents_link_carries_response_known_at`.

**Q9. Fixture principal.** `service:w401-fixture`, which is `work_api.W401_FIXTURE_SERVICE_PRINCIPAL_ID` (`work_api.py:39`), injected server-side by `tools/w601_seed.py`. The §1 operational-row and detail examples now print `service:w401-fixture`. No `service:w601-fixture` principal exists.

**F1. Rail (A2, B2, E2).** In `frontend/src/shell/OperatorShellLayout.tsx` each unit replaces its one inventory line, and in `tools/checks/navigation-truthfulness.ps1` its one `$expected` entry (lines 550–552):

- A2: `{ kind: "live", to: "/incidents", label: "Incidents", end: false, group: "WORK", icon: "incident" },` and `"live|Incidents|WORK|/incidents",`
- B2: `{ kind: "live", to: "/maintenance", label: "Maintenance", end: false, group: "WORK", icon: "work" },` and `"live|Maintenance|WORK|/maintenance",`
- E2: `{ kind: "live", to: "/operational-records", label: "Operational records", end: false, group: "WORK", icon: "log" },` and `"live|Operational records|WORK|/operational-records",`

**F2. Rail fixtures (A2, B2, E2), `tools/checks/navigation-rail-fixtures.ps1`.** A2 deletes the case `"W3-01: Incidents promoted to live"`, whose anchor `kind: "unavailable", label: "Incidents"` no longer exists (`Edit-Lines` would throw). It adds the following after the W3-02 Financials cases:

```powershell
            @{ Name = "W6-01a: Incidents live root points at a missing route"; Expect = "points at '/incidentz'";
               Rail = (Edit-Lines $rail 'to: "/incidents"' 'to: "/incidentz"') },
            @{ Name = "W6-01a: Incidents route removed (only the catch-all would serve it)"; Expect = "points at '/incidents'";
               App = (Remove-Line $app 'path=\{INCIDENTS_PATH\}') },
            @{ Name = "W6-01a: Incidents demoted back to unavailable"; Expect = "the W1 rail is exactly";
               Rail = (Edit-Lines $rail 'kind: "live", to: "/incidents", label: "Incidents", end: false' 'kind: "unavailable", label: "Incidents"') },
```

B2 adds the same three cases with `W6-01b`, `Maintenance`, `/maintenance`, `/maintenancz` and `MAINTENANCE_PATH`. E2 adds them with `W6-01e`, `Operational records`, `/operational-records`, `/operational-recordz` and `OPERATIONAL_RECORDS_PATH`. The existing `"label typo"` case keeps its anchor.

**F3. Route constants.** The rail guard resolves `path={CONST}` only through plain `export const NAME = "...";` lines in `frontend/src/shell/*.ts(x)` (`navigation-truthfulness.ps1:530-535`, `:666-672`). Each page unit adds one line to `frontend/src/shell/operatorSiteRoutes.ts` after `PORTFOLIO_ROOT_PATH`. It registers `<Route path={CONST} element={...} />` inside the `<Route element={<OperatorShellLayout />}>` block of `App.tsx`, before the `path="*"` catch-all:

| Unit | Constant |
| --- | --- |
| A2 | `export const INCIDENTS_PATH = "/incidents";` |
| B2 | `export const MAINTENANCE_PATH = "/maintenance";` |
| B3 | `export const MAINTENANCE_PREVENTIVE_PATH = "/maintenance/preventive";` |
| C2 | `export const WORK_REQUEST_ROUTE_PATH = "/maintenance/requests/:caseId";` |
| C3 | `export const WORK_REQUEST_RECORD_ROUTE_PATH = "/maintenance/requests/:caseId/record";` |
| C4 | `export const WORK_REQUEST_HISTORY_ROUTE_PATH = "/maintenance/requests/:caseId/history";` |
| E2 | `export const OPERATIONAL_RECORDS_PATH = "/operational-records";` |

`frontend/src/sites/siteWorkCases.tsx` keeps the literal `/incidents` and `/maintenance` strings of §1 and imports nothing from `shell/`, because the Site substrate is a leaf (`site-substrate.ps1:113-121`).

**F4. In-page unavailable multiset, `$expectedTabs` (`navigation-truthfulness.ps1:752-753`).** B2 renders `<UnavailableTab label="Preventive &middot; scheduled" />` and appends `"Preventive &middot; scheduled"` to `$expectedTabs`. The mock `MAINT_GTABS` label is `Preventive · scheduled`. It is written as the HTML entity because the guard reads files in the host code page, so both sides compare ASCII. `globalMaintenance.test.tsx` asserts the rendered text `Preventive · scheduled`. B3 removes that entry and the element. C2 renders `<UnavailableTab label="Maintenance record" />`, `<UnavailableTab label="Verification" />` and `<UnavailableTab label="History" />` in mock `WR_TABS` order (Overview, Maintenance record, Verification, History) and appends `"Maintenance record", "Verification", "History"`. C3 removes `"Maintenance record"` and C4 removes `"History"`. `"Verification"` stays. No unit edits the in-page fixtures: `navigation-rail-fixtures.ps1:125-200` anchors only on `SiteAnalyticsFrames.tsx` and `EvSiteViews.tsx`.

**F5. Screen ledger, `frontend/docs/architecture/v69-screen-ledger.json`.** This follows the W4-01 commit 5 precedent. The unit that mounts a screen's route edits that screen's row in the same Lane A commit, setting these fields:

- `coverage`: `"bounded"`.
- `task`: the unit's slice (`W6-01a` incidents, `W6-01b` maintenance and maintenance-preventive, `W6-01c` wr-overview and wr-record, `W6-01d` wr-history, `W6-01e` oprecords).
- `follow_on`: `null`.
- `promotion_dependencies.to_candidate`: `null`.
- `data_owner`: `"W6-01 global work read (GlobalWorkIndexService / GlobalWorkDetailService)"`.
- `to_real.remaining_work`: `"Independent {slice} review accepting the exact slice, the owner fidelity tier decision and the post-W6 owner walkthrough."`, with `{slice}` the same task ID.

It keeps `registry_dependencies`, `product_destination`, `proposed_fidelity_tier`, `tier_approval`, `to_real.unresolved_panels` and `to_real.acceptance` byte-identical. The remaining three fields are:

| Screen (unit) | `supported_claim` | `interaction` | `unknown_or_empty` |
| --- | --- | --- | --- |
| `incidents` (A2) | `Incident work cases across every authorized imported Site for the selected UTC window, read from stored records in one snapshot with an exact count, the selected revision, latest assignee, scoped request codes, pinned Finding and Action links and a source label; outcomes stay unverified.` | `Open Incidents, choose a UTC window and page through the list; a row opens its Site incidents window or a pinned Finding or Action.` | `No incident case in the window is an exact zero; no accessible Sites, a refused or unreadable read and a changed list are stated and never shown as zero; severity is Not recorded; no mock case is product evidence.` |
| `maintenance` (B2) | `Corrective work requests across every authorized imported Site for the selected UTC window, with the selected revision, latest assignee, latest authored maintenance activity and a source label; verification is Not established and warranty Not recorded.` | `Open Maintenance, choose a UTC window and page through the list; a row opens its Site maintenance window, or the exact request once W6-01c is live.` | `No work request in the window is an exact zero; no accessible Sites, a refused or unreadable read and a changed list are stated and never shown as zero; completion is activity only; no mock request is product evidence.` |
| `maintenance-preventive` (B3) | `Draft preventive plans across every authorized imported Site whose root occurred in the selected UTC window, each at its selected correction head with authored trigger and due facts; no plan is an active schedule.` | `Open Maintenance > Preventive, choose a UTC window and page through the plans; a row opens its Site.` | `No draft plan in the window is an exact zero; Overdue and Due in 14 days are Not assessed because no due evaluator exists; refused or unreadable reads are stated and never shown as zero.` |
| `wr-overview` (C2) | `One work request at one cutoff, read from the stored case detail by Site code: selected revision, state, latest assignee, latest authored activity and the exact Finding or Incident source; Completed is not Verified.` | `Open a work request from Maintenance; the Site, the cutoff and the Overview, Maintenance record and History tabs keep the same request and cutoff.` | `No maintenance activity recorded, Not assigned, Due / SLA Not set and Success criterion Not recorded are stated; a wrong Site is No access or Not found, never an empty request.` |
| `wr-record` (C3) | `The request's authored maintenance records at the cutoff, each at its latest correction head with earlier versions disclosed, and the operational records that name the case.` | `Open the Maintenance record tab of a work request; earlier record versions expand in place and a linked operational record opens the Operational records window.` | `No maintenance activity recorded and No linked Operational record. are stated; an outcome note is an unverified authored note.` |
| `wr-history` (C4) | `The request's authored events and correction revisions at the cutoff in recorded order, with the stored actor and occurrence time.` | `Open the History tab of a work request and page through events five at a time; each row's occurrence time expands in place.` | `A request without its Created event is a read failure, not an empty history; no event verifies an equipment outcome.` |
| `oprecords` (E2) | `Authored operational records across every authorized imported Site whose root occurred in the selected UTC window, each at its selected correction head and filtered by kind with an exact filtered count; all are Submitted and none is accepted evidence.` | `Open Operational records, choose a window and kind chip and page through the list; a row opens its Site or the case it names.` | `No operational record in the window is an exact zero; manual readings cannot be submitted from this page; Feeding evidence is Not established; refused or unreadable reads are stated and never shown as zero.` |

A2 also replaces, in the `sitework-incidents` row's `to_real.remaining_work`, the substring `the missing global Work page and create flow` with `the missing create flow`. B2 does the same in the `sitework-maintenance` row. Every other row stays byte-identical, including the stored bytes of `maintenance-preventive.product_destination`. Run `python frontend/docs/architecture/check_v69_ledger.py` and `node frontend/docs/architecture/check_v69_dependency_registry.cjs` after each edit.

**F6. Frontend guard literals every page unit obeys.**

- Every table renders through `DataTable` from `frontend/src/ui/DataTable.tsx`. A bare `<table` elsewhere fails `shell-overflow.ps1` rule 4 (`:280-307`). The three-line clamp blocks sit inside its cells.
- There is no `<svg` in `frontend/src/work/` (rule 5), so `Scroll table horizontally` is text.
- No type, interface or function in `frontend/src/work/` matches `site-substrate.ps1:35-43`; for example, `interface SiteWorkRow` and `function SiteList` are not allowed.
- New copy uses none of the `missing-claim-scan.mjs` `PATTERNS` phrases, except inside `UnavailableTab` and the two `siteWorkCases.tsx` exemptions that A2 and B2 manage.

**A1Q2. Rulings on the A1 build readings R1–R4** (`.agent/W6-01a-phase-handoff.md`, Run entry; A1 at `task/W6-01a-global-incidents` `c5e45a67`). *Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.* **No A1 code change is required.**

- **R1 is confirmed, and G6(c) is amended to match.** §4 needs the ordered write clock, and `build_work_service` cannot take one. `tools/w601_seed.py` therefore builds `WorkService(PostgresWorkStore(url, link_rows=build_link_rows_reader(), test_db_clock_override=clock))` directly. G6(c) now reads:

  > `tools/w601_seed.py` is outside every backend scan root. It may import `work.service.WorkService`, `work.adapters.postgres_work_store.PostgresWorkStore` (only to pass the constructor-only `test_db_clock_override`), `evidence.composition.build_link_rows_reader`, `sites.adapters.postgres_foundation_store.PostgresFoundationStore`, `sites.adapters.import_files.read_import_source`, `sites.foundation_service.import_site` and `work_api.W401_FIXTURE_SERVICE_PRINCIPAL_ID`. These follow the `tools/s601b_action_walkthrough.py` precedent.
  >
  > No module under `backend/assetops_backend/` may pass `test_db_clock_override`.

  B1 and E1 extend the tool under the same rule.
- **R2 is confirmed as a deferral, and B1 owns the deferred work.** A1 and A2 need no `linked` fixture, and A2 adds no linked capture. B1 adds `--fixture linked` to `tools/w601_seed.py`:
  - **Producer.** It creates real Finding and Action rows with the merged producers that the A1 parity test uses: `CaseRunner(PostgresFoundationStore(url), engine)` from `test_s4_finding_store_postgres`, `run_case(runner, CASES["F01"])` from `test_s6_action_store_postgres`, and `public_finding(runner)` from `test_w401_work_service_postgres`. This is the same import pattern as `tools/s601b_action_walkthrough.py:63-70`.
  - **Rows.** It writes one incident and one maintenance request pinned to that exact Finding revision, and one request pinned to its selected Action event.
  - **Clock and window.** It runs with `--clock 2026-10-08T12:00:00Z`. Its capture and test window is `from=2026-10-01T00:00:00Z&to=2026-10-08T00:00:00Z`, which contains the F01 anchor day 2026-10-06.
  - **Test.** `test_w601b_global_maintenance.py::test_linked_finding_and_action_hrefs` asserts a lineage-true `Finding {id[:8]}` href and `Action {id[:8]}` href on both `/api/work/incidents` and `/api/work/maintenance` rows. The hrefs must be identical to the W4 Site list hrefs.
  - **Capture.** B2 adds the persisted capture `maintenance-linked` at 1440/390 from this fixture.
  - **No pure snapshot.** §4's labelled pure typed snapshot no longer applies to W6-01, because a real producer exists.
- **R3 is confirmed.** The global `selection_token` binds, per row:
  - `site_id`, `case_id` and `revision_id`;
  - the selected event IDs and the selected record ID;
  - the Finding revision IDs and Action event IDs;
  - `link_lineage` as `[kind, id, selected_id, lineage]`;
  - the cited accepted IDs and `linked_request_codes`.

  It does not bind W4's cold/EV `link_fence` states or `selection_token`s. That is correct, because no global row field reads them: Link hrefs depend only on lineage and immutable root IDs, and status comes from Q4.

  Standing rule for B1 and E1: any new row field derived from a stored value adds that value to the row `basis`. A field derived from a fence state must also add the fence; none is planned.
- **R4 is confirmed.** `empty_scope` seeds the same rows as `incidents`. `EMPTY_SCOPE` exists only when the read's access callback denies every Site (pytest `test_complete_zero_and_empty_scope`); that matches §4. The fixture is never presented as persisted empty data, and no capture of it is required. A2 proves `No accessible Sites.` in `globalIncidents.test.tsx` with a typed `EMPTY_SCOPE` response only.

**A2Q. Rulings on the A2 builder questions A2Q1–A2Q10, and the third-round readiness pass** (`.agent/W6-01a-phase-handoff.md`, "Run (A2 build)", commit `7b1ac89b`). *Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.* This is the third ruling round on W6-01a, so the ROLE_CONFIG readiness gate requires a fresh dry-read of every remaining UI card; its closures are X1–X9 below.

**A1 reopens for one change (A2Q1).** A2 builds only after the change below is independently reviewed.

*A1 change.* `work/global_index.py` adds the envelope key `state_counts`, which is always present on a 200 response. For incidents it is exactly `{"OPEN":int,"IN_PROGRESS":int,"CLOSED":int}`. B1 gives maintenance exactly `{"OPEN":int,"IN_PROGRESS":int,"COMPLETED":int,"CANCELLED":int}`. Preventive and operational records return `state_counts:null`.

*Computation.* Each count is taken over the full selected row set before paging and the cursor filter: `sum(1 for r in rows if r["wire"]["state"] == S)`. This is not an SQL predicate, because `state` is `m.reduce_state(kind, events at K)` over the selected events. The token needs no change, because those event IDs are already bound in `basis`. The counts sum to `total_count`. EMPTY_SCOPE gives every count 0. Refusal bodies are unchanged.

*Test.* `test_w601a_global_incidents.py::test_state_counts_cover_full_selection` seeds six incidents in the window: four OPEN, one IN_PROGRESS (ASSIGN) and one CLOSED (CLOSE). It reads with `limit=5` and asserts `{"OPEN":4,"IN_PROGRESS":1,"CLOSED":1}` on both page one and page two, and all zeros on EMPTY_SCOPE.

*Contract and A1 card.* The §1 envelope key list and the A1 card include `state_counts`. A1 Lane B files: `work/global_index.py` and the test file.

**A2Q1. UI cards.** All four cards render only on a 200 response whose `status` is `CURRENT` or `HISTORICAL`, including a complete zero (value `0`). On `EMPTY_SCOPE`, a refusal, a read failure or a cursor change, the card row is not rendered, and the state block (§2 copy) stands in its place above the table panel.

| Card | Value | Note line |
| --- | --- | --- |
| `Open incidents` | `state_counts.OPEN + state_counts.IN_PROGRESS` | `Open or in progress in this window` |
| `High severity` | §2 | §2 |
| `Awaiting evidence` | §2 | §2 |
| `Closed verified` | §2 | §2 |

The mock's `INC-203` note is not reproduced.

**A2Q2. Stress producer.** A2 Lane B gains `tools/w601_seed.py` for one additive fixture `stress`, which is added to `FIXTURES`. It imports the same Sites, then:

1. In tenant one, Site `KOBO-001`, it writes six incidents at the `incidents` occurrence time.
2. Incident 1 gets title `("Backupgeneratorautomaticstartfailure" * 6)[:200]` (200 characters, unbroken). Incidents 2–6 get `Stress incident 2` … `Stress incident 6`.
3. Incident 1 is assigned to `("Fieldmaintenancesupervisorteam" * 5)[:128]` (128 characters, unbroken). That value shows in the Owner cell.

The six rows give the five-row page plus a Next page. In A2, `actor128` means the Owner (assignee) cell. A2 has no UUID or reason cell, so those stress items move to C2 and C4 (X2). Narrative stress is not in the Incidents table.

**A2Q3. Capture clock.** UI captures for every W6-01 page unit use `--clock 2026-10-21T12:00:00Z` and the window `from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z`. This keeps every stored instant before any real capture time on or after 2026-10-21T12:00:03Z.

- **Historical captures** pass `known_at=2026-10-21T12:00:00Z`.
- **`cursor_change`:** read page one first, then run `--append`, which writes at `2026-10-21T12:00:02Z`. That instant is before the page-one cutoff, so the reused cursor is 409.
- **Pytest** keeps `2026-10-22T12:00:00Z` with the constructor read-clock override.
- **B1's `linked`** keeps its A1Q2 clock.

The §4 clock paragraph is amended to match.

**A2Q4. Source label.** The Incident cell's second line is `<details><summary>{label}</summary>{explanation}</details>`, using the §2 work provenance pair chosen by `source_provenance.classification`. The `classification` values are `AUTHORED_DEMONSTRATION`, `REGISTERED_SIMULATION`, `MIXED` and `UNKNOWN`. The same rule applies to the first cell of the B2 (`Work request`), B3 (`Plan item`) and E2 (`Record`) tables.

**A2Q5. Cutoff control.** There is no cutoff input. A cutoff arrives only through the page URL's `known_at`, for example from a Site Work manage link, and shows in the §2 `As known at` / `Historical as of` line. `Reload` re-reads with the same query. The F5 ledger `interaction` strings are amended to drop "or cutoff".

**A2Q6. Refusal UI copy** for all four global list pages. The C2–C4 detail pages use the same 401, `INVALID_KNOWN_AT` and 503 rows, plus the §2 403/404 copy.

| Code | UI sentence | Action |
| --- | --- | --- |
| `UNAUTHENTICATED` | `Sign in to see work records.` | none |
| `INVALID_WINDOW` | `Choose a valid date range of at most 31 days.` | none |
| `INVALID_KNOWN_AT` | `Choose a valid cutoff time.` | none |
| `INVALID_LIMIT` | `Choose a page size from 1 to 100.` | none |
| `INVALID_CURSOR` | `The list changed. Reload the first page.` | `Reload the first page` link: same `from`, `to`, `known_at`, no `cursor` |
| `WORK_BASIS_CHANGED` | `The list changed. Reload the first page.` | same as `INVALID_CURSOR` |
| `WORK_STORE_UNAVAILABLE`, network failure, malformed 200 | `Work records could not be read. Reload.` | none |

An invalid page query is not fetched: it renders the `INVALID_WINDOW` or `INVALID_KNOWN_AT` sentence. None of these sentences matches a `missing-claim-scan.mjs` pattern.

**A2Q7. Footer placement.** Every §2 "Footer" literal renders as the Panel `description` (the mock `panel(title, body, sub)` sub-line under the heading). This applies to A2 `Incident cases`, B2 `Corrective work requests`, B3 `Preventive plan`, C2 `Work done` / `Lifecycle`, C3 `Maintenance record · activity` and E2 `Operational records`. Nothing renders below the table.

**A2Q8. Incidents cell literals.**

| Column | Content |
| --- | --- |
| Incident | Link text `{code} · {title}` to `links.site_incidents.href`. Uses the three-line clamp block and `<details><summary>Full title text</summary>{title}</details>`, then the A2Q4 source line. |
| Site | `links.site` (label and href). |
| Start | The §2 date format of `occurred_at` (`20 Oct 2026, 09:00 UTC`). |
| Severity | Plain text `Not recorded`. |
| State | Chip with `Open` / `In progress` / `Closed`. Tone is `stateTone("incidents", state)`, imported from `frontend/src/sites/siteWorkCases.tsx`; the label map is copied, because `STATE_LABEL` is not exported. |
| Owner | `owner`, or `Not assigned`. |
| Findings / work | Finding links, then Action links, joined ` · `. If `linked_request_codes` is non-empty, add ` / ` and the codes as plain text joined ` · `. When all three are empty: `None linked`. |

**A2Q9. Registry.** A2 edits only the reasons of `incidents:1` and `incidents:2` in `v69-dependency-registry-pilot.json`, replacing `awaits build and independent review` with `is built and awaits independent review`. `status` stays `gap`, and the nodes `I-w601a-read`/`I-w601a-ui` stay `open`. Each later page unit makes the same substring edit to its own rows (X6).

**A2Q10. Paging.** The page URL may carry one `cursor`, which is passed unchanged to the API. Earlier cursors ride in history state as `globalWorkTrail` (an array of `string|null`), following the W4 `workTrail` pattern (`SiteAnalyticsFrames.tsx:1601-1622`), so Previous survives a reload. `Previous` is hidden on page one and `Next` is hidden when `next_cursor` is null; a hidden control renders nothing and is never disabled. Changing the window, Reload or a kind chip clears both the cursor and the trail.

Above the pager, show `Showing {a}–{b} of {total_count}`, where `a = trail.length × 5 + 1` and `b = a + rows.length − 1`. It appears only when `total_count > 0` on CURRENT or HISTORICAL. Its provisional cap is 70/130.

The §1 page-query contract is amended: the page reads `from`, `to`, optional `known_at`, optional `cursor` and, on E2 only, `kind`. Other keys are ignored and never forwarded.

**Readiness pass, other UI units (X1–X9 closed in their cards):**

- **X1 (B1/B2 counts).** B1 adds the maintenance `state_counts` (A2Q1 shape) with the test `test_w601b_global_maintenance.py::test_state_counts_cover_full_selection`. B2 card `Open work` = `state_counts.OPEN + state_counts.IN_PROGRESS`, note `Open or in progress in this window`. B3 `Plan records` and E2 `Records in window` use `total_count`, which is already the full filtered set. Every page uses the A2Q1 card-render rule.
- **X2 (stress producers, B1 owns).** B1 extends `--fixture stress` with:
  - one maintenance request titled `("Startermotorandcontrolpanelinspection" * 6)[:200]`, assigned the A2Q2 128-character owner;
  - narrative `("Inspection narrative " * 200)[:4000]`;
  - one performed record with activity `("Replaced starter relay and tested " * 120)[:4000]` and outcome note `Authored note`;
  - one correction with reason `("Corrected the inspection scope " * 20)[:500]`;
  - one plan titled `("Quarterlyfilterandbeltinspection" * 7)[:200]`.

  E1 extends it with one `OPERATOR_LOG` record whose body is `("Operator checked the panel and logged readings " * 90)[:4000]`. The UUID stress is the 36-character request `case_id` in the C2 `selected` header and the C4 `By` cell's `service:w401-fixture`. The reason stress is the C4 `Correction` row. Captures B2 long actor, B3 long PM, C2 long narrative, C3 4000-character activity and E2 long body all read this fixture.
- **X3 (clocks).** B2, B3, C2–C4 and E2 captures use the A2Q3 clock and window. C2–C4 detail URLs carry `known_at=2026-10-21T12:00:00Z` only for historical captures.
- **X4 (copy).** B2, B3 and E2 use the A2Q6 table. C2–C4 use its 401, `INVALID_KNOWN_AT` and 503 rows plus the §2 403/404.

  C1 rules a missing, empty or repeated `site_id`, or a non-UUID `case_id`, as 404 `WORK_CASE_NOT_FOUND` `No work case with this ID at this site.`. No new code is added. The C2–C4 pages show that §2 404 sentence without fetching when `site_id` is absent. Test: `test_w601c_request_detail.py::test_missing_site_id_or_bad_case_id_is_404`.

  Table empty cells are `None linked` (Findings/work and Feeds), `No asset recorded` (Asset / site) and `Not set` (Next due).
- **X5 (footers).** A2Q7 applies to B2, B3, C2, C3 and E2.
- **X6 (registry and ledger).** Each page unit applies the A2Q9 substring edit to its own `v69-dependency-registry-pilot.json` rows:
  - B2: `maintenance:1`;
  - B3: `maintenance-preventive:1`;
  - C2: `wr-overview:1`, `wr-overview:2`;
  - C3: `wr-record:1`;
  - C4: `wr-history:1`;
  - E2: `oprecords:1`, `oprecords:3` (`oprecords:2` is unchanged).

  The F5 ledger `interaction` literals lose "or cutoff" (A2Q5). No backend unit edits either JSON.
- **X7 (paging).** B2, B3 and E2 use A2Q10, and an E2 kind chip resets the trail. C4 History pages client-side over the merged `work_detail.events` and `history.revisions`, ordered `(recorded_at, id)` ascending: five rows a page, Previous/Next in component state, and the same `Showing` line. C3's record panel has no pager and uses the §2 vertical scroll.
- **X8 (cell literals).**

  | Unit | Column | Content |
  | --- | --- | --- |
  | B2 | Work request | `{code} · {title}`, linked to `links.site_maintenance.href` before C2 and to `links.detail.href` after |
  | B2 | Asset / site | `asset_label` or `No asset recorded`, then the `links.site` link |
  | B2 | Owner | `owner`, or `Not assigned` |
  | B2 | State | `Open` / `In progress` / `Completed` / `Cancelled`, tone `stateTone("maintenance", state)` |
  | B3 | Plan item | `{code} · {title}` as plain text |
  | B3 | Asset / site | As B2 |
  | B3 | Trigger | `Calendar` / `Running hours` |
  | B3 | Next due | The §2 date of `next_due_at`, or `{next_due_hours} running hours`, or `Not set` |
  | E2 | Record | `{code}` |
  | E2 | Type | The chip label |
  | E2 | Site | `links.site` |
  | E2 | When | The §2 date of `occurred_at` |
  | E2 | By | `actor_id` |
  | E2 | What it says | The clamp block plus `<details><summary>Full record text</summary>` |
  | E2 | Feeds | `links.case` (label `case_code`), or `None linked` |
- **X9 (C4 labels).** A request can never carry `CLOSE`, because W4 `TRANSITIONS` has no request CLOSE. `workRequestHistory.test.tsx::history_labels_all_seven` therefore proves all seven labels with a typed DTO. The persisted capture proves `CREATED`, `ASSIGN`, `COMMENT`, `COMPLETE`, `REOPEN` and `Correction` from B1's `detail` fixture, and `CANCEL` from a second request in the same fixture. B1's `detail` fixture writes exactly those events.

**CL3. Closure of the seven open gaps from the Sonnet check.** *Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.* Every new sentence below, and every A2Q sentence, was run against the real `PATTERNS` in `tools/checks/missing-claim-scan.mjs`, and none matched (52 strings checked).

- **CL3-1. Loading copy.** The precedent is the estate roots: `<p className="estate-loading">Loading the … across the estate.</p>` in `findingIndex.tsx:325` and `actionIndex.tsx:193`, and W4's `Loading the site's work records.` in `siteWorkCases.tsx:736`.

  While the read is in flight, each page renders a single `<p data-global-work-loading>` in place of the cards and table body. Headings, the control bar and the tab row stay visible.

  | Unit | Loading sentence |
  | --- | --- |
  | A2 | `Loading the incidents across the estate.` |
  | B2 | `Loading the work requests across the estate.` |
  | B3 | `Loading the preventive plans across the estate.` |
  | E2 | `Loading the operational records across the estate.` |
  | C2, C3, C4 | `Loading the work request.` |

  Each page test asserts its sentence before the client resolves.
- **CL3-2. B3 Preventive card.** The B2 card is the mock's third maintenance card. Its label is `Preventive due in 30 days`, its value is `Not assessed`, and before B3 its note is the plain text `Preventive plans open in a later unit.`.

  B3 replaces that note with the link `Open Preventive to inspect authored due facts`. Its href is `/maintenance/preventive?from={from}&to={to}`, plus `&known_at={known_at}` when the page URL has one. It never carries `cursor`.

  In the same commit, B3 also makes the B2 tab `Preventive · scheduled` a live link to that same href, and removes the `UnavailableTab` and its `$expectedTabs` entry.

  B3's Lane A list gains `frontend/src/work/GlobalMaintenance.tsx` and `frontend/src/work/__tests__/globalMaintenance.test.tsx`. Test: `globalMaintenance.test.tsx::preventive_card_and_tab_link_after_b3`.
- **CL3-3. C3 linked REC.** C1 owns the producer and its Lane B list gains `tools/w601_seed.py`.

  The `detail` fixture (B1) writes two requests. C1 adds one `post_operational_record` on the first request at the next write-clock instant, with body:

  ```
  {"kind":"OPERATOR_LOG","body":"Checked the starter after the inspection.","occurred_at":<--clock minus 2 days>,"period_end":null,"unit":null,"quantity":null,"source_document_sha256":null,"case_id":<first request id>,"actor":ACTOR,"idempotency_key":<writer key>}
  ```

  The empty capture `No linked Operational record.` uses the second (`CANCEL`) request of the same fixture, which has no operational record.

  C1 adds `root_occurred_at` (six digits, `Z`) to each `history.operational_records[]` item.

  Each REC renders as link text `{code}` with href `/operational-records?from={D}&to={D+1 day}&known_at={selected.known_at}&kind={kind}`. `D` is the UTC midnight of that item's `root_occurred_at`, and every value is URL-encoded.

  Tests: `test_w601c_request_detail.py::test_case_linked_operational_record_root_time` and `workRequestRecord.test.tsx::linked_rec_filtered_window_href`.
- **CL3-4. B3 corrected historical producer.** B1 owns it and extends `--fixture historical`:
  1. At the base write clock, a DRAFT plan `{"title":"Inspect filters","trigger_kind":"CALENDAR","next_due_at":<--clock plus 7 days>,"next_due_hours":null,"asset_id":null,"occurred_at":<--clock minus 2 days 1 hour>}`.
  2. At `--clock + 1s`, its correction `{"supersedes_plan_id":<root id>,"canonical_plan_id":<root id>,"correction_reason":"Due date corrected after review","title":"Inspect filters","next_due_at":<--clock plus 14 days>, … unchanged keys}`. Its occurrence is `--clock` minus 1 day.

  A capture with `known_at=--clock` shows the original head, and a current capture shows the correction. Test: `test_w601b_global_maintenance.py::test_plan_correction_historical_head`.
- **CL3-5. C2 field map.** C1 adds `links.source_incident: Link|null`. It is non-null only when `work_detail.case.incident_id` is set: label `Incident {incident public_code}`, href `/sites/{site_code}/work/incidents?from={D}&to={D+1 day}&known_at={selected.known_at}`, where `D` is the UTC midnight of the incident root `occurred_at`. C1 test: `test_w601c_request_detail.py::test_source_incident_link`. The C2 header and Work done slots map to fields as follows:

  | Slot | Source |
  | --- | --- |
  | h1 | `work_detail.selected_revision.title` |
  | Subtitle | `{selected.case_code} · {links.site.label} · corrective` |
  | Owner | `payload.assignee` of the last `work_detail.events` item with `kind == "ASSIGN"` by `(recorded_at, id)`, else `Not assigned` |
  | Due / SLA | Literal `Not set` |
  | State | Label of `work_detail.case.state` + ` · outcome not established` |
  | Source | `work_detail.finding_links` items with a non-null `href`, rendered as links joined ` · `; else the plain text `links.source_incident.label` followed by the link `Open Site incidents` (href `links.source_incident.href`); else `Not recorded` |
  | Success criterion | Literal `Not recorded` |
  | Work done: narrative | `work_detail.selected_revision.narrative` |
  | Work done: latest performed activity | `activity` of the `work_detail.records` head (the item no other item supersedes) with the greatest `(recorded_at, id)`, else `No maintenance activity recorded` |
  | Warranty | Literal `Warranty not recorded` (no wire field) |
  | Lifecycle | `work_detail.case.state` (§2) |
- **CL3-6. E2 `kind`.** If the page URL has `kind` absent, it means `all`. If `kind` is anything other than `all|OPERATOR_LOG|MANUAL_READING|SHIFT_NOTE|SITE_VISIT`, or is repeated, the page does not fetch. It renders `Choose a supported record type.` with the five chips live, and the `All` chip href drops `kind`.

  Kind-filtered zero (200, `total_count:0`, kind ≠ `all`) shows one sentence followed by `Change the UTC window or open a Site record.`:

  | Kind | Zero sentence |
  | --- | --- |
  | `OPERATOR_LOG` | `No operator log records in this window.` |
  | `MANUAL_READING` | `No manual reading records in this window.` |
  | `SHIFT_NOTE` | `No shift note records in this window.` |
  | `SITE_VISIT` | `No site visit records in this window.` |

  `kind=all` keeps the §2 `No operational records in this window.`. Test: `operationalRecords.test.tsx::kind_invalid_and_filtered_zero`.
- **CL3-7. Scan and route-frame edits.**
  - `missing-claim-scan.mjs`: B3, C2, C3, C4 and E2 make no edit, because none of their sentences matches a pattern. The C2–C4 `Not available yet` tabs render only through `UnavailableTab`, whose component const is already exempt. Only A2 and B2 edit the scan, for the `siteWorkCases.tsx` exemptions.
  - `operatorRouteFrames.test.tsx` pins only rail roots (lines 223–228 and 269–271), so it changes only in rail units. A2, B2 and E2 already list it, with the F1 rail change. B3, C2, C3 and C4 make no edit.

  The cards state both.

**A1 is untouched. The A2 card gains only the CL3-1 loading sentence.**

**Residual, not ruled (for the Codex retrospective).** `frontend/src/estate/EstateEvidence.tsx:46` renders the inert mock examples `Operational records · Not available yet` and `Preventive plan · Not available yet`. Both become stale once E2 and B3 are live. This is not a guard or composition gap, and no W6 unit owns that file, so no builder touches it.

## 4. Producers, registry and readiness

**Fixture command and clocks.** `python tools/w601_seed.py --db assetops_w601_<unit>_test --fixture {incidents|maintenance|preventive|detail|operational|zero|empty_scope|linked|historical|cursor_change} --clock 2026-10-22T12:00:00Z` is the prescribed producer CLI, owned by A1 and extended B1/E1. The helper uses W4 `WorkService` with injected `W401_FIXTURE_SERVICE_PRINCIPAL_ID` in the server/test composition, imported two-tenant/two-Site rows and explicit grants; it never sends that actor from browser JS. Each invocation has one frozen **fixture read clock** and an ordered write-clock callable returning `11:59:00Z`, `11:59:01Z`, … for base commands and `12:00:01Z`, `12:00:02Z` for historical successor/late append, with exact occurrence offsets from `--clock`: incident root minus 2 days 3 hours, request root minus 2 days 2 hours, plan root minus 2 days 1 hour, operational root minus 2 days; any correction keeps its root membership occurrence and uses an occurrence one day before `--clock`. All are within W4's 30-day bound. Set `from=2026-10-15T00:00:00Z&to=2026-10-22T00:00:00Z` for the prescribed clock in every positive/zero/historical capture URL; equivalent midnight bounds move with another `--clock`. A2Q3 supersedes this for UI captures: every W6-01 page-unit capture uses `--clock 2026-10-21T12:00:00Z` and `from=2026-10-14T00:00:00Z&to=2026-10-21T00:00:00Z` (historical `known_at=2026-10-21T12:00:00Z`); pytest keeps `2026-10-22T12:00:00Z` with the read-clock override; B1 `linked` keeps its A1Q2 clock. Historical pytest read pins `known_at=12:00:00Z` after the later writes; current pytest read pins `12:00:02Z`. Captures use real DB time, label the returned `known_at`, and must omit an old explicit cutoff unless showing `HISTORICAL`. Capture seed commands print stored IDs/codes from real DB rows; no screenshot uses mock IDs. `linked` first creates real in-scope Finding/Action IDs via the merged producers and passes those exact IDs to W4 commands; if that creation is unavailable, linked positive is a pure typed snapshot and must be labelled that way. `empty_scope` injects a principal access callback denying all Sites. `PARTIAL` is a pure typed response only, never a persisted/API capture. 503 uses unavailable store composition; 401 uses authenticate callback; detail 403/404 use exact Site access/missing Site. `cursor_change` fetches page one then appends a selected row at `12:00:02Z` and reuses cursor. Pure snapshots cover the unreached verified, accepted, severity, warranty and due-evaluator states only as honest gaps; no fake persisted claim.

**Capture artifacts and ownership.** A1 owns `tools/w601_seed.py` and `.agent/W6-01a-review-packet.md`; A2 owns `.agent/W6-01-evidence/A2/{capture.mjs,manifest.json,screenshots}` and contributes its exact revision/captures to that packet. B1 owns `.agent/W6-01b-review-packet.md`; B2 and B3 own `.agent/W6-01-evidence/B2/` and `/B3/` respectively, each with `capture.mjs`, `manifest.json` and screenshots, and contribute to that packet. C1 owns `.agent/W6-01c-review-packet.md`; C2/C3 own corresponding `.agent/W6-01-evidence/C2/` and `/C3/` capture files and contribute to that packet. C4 owns `.agent/W6-01-evidence/C4/{capture.mjs,manifest.json,screenshots}` and `.agent/W6-01d-review-packet.md`. E1 owns `.agent/W6-01e-review-packet.md`; E2 owns `.agent/W6-01-evidence/E2/{capture.mjs,manifest.json,screenshots}` and contributes to that packet. Every manifest records route/query, width, fixture command and stored IDs, response status/known_at, measured cap heights and document/table widths. These paths extend the exhaustive unit lists above; no capture is passed off as persisted evidence without its manifest.

**Registry paths.** In `frontend/docs/architecture/v69-dependency-registry-pilot.json`, `P-work-cases` retains `pending owner` and records the Architect recommendation `Real with honest gaps`, priority `W6`, core panels `incidents:1,incidents:2,maintenance:1,maintenance-preventive:1,wr-overview:1,wr-overview:2,wr-record:1,wr-history:1` as **not owner accepted**. `oprecords` is governed by still-pending `P-work-area`; Architect recommends the same tier for this W6 scope without claiming an owner choice. Building may proceed under this Architect recommendation after the independent readiness gate, while merge/panel promotion remains conditional on the owner walkthrough and explicit owner acceptance; pending-owner status is not silently promoted. Implementation nodes `I-w601a-read/ui`, `I-w601b-read/corrective-ui/preventive-ui`, `I-w601c-detail/overview-ui/record-ui`, `I-w601d-history-ui`, `I-w601e-read/ui` are `open` with literal predecessors in registry JSON. Existing `incidents:1,2` point to A read/UI and `D-work-records`; `maintenance:1` points to B read/corrective UI/data. New rows `maintenance-preventive:1`, `wr-overview:1,2`, `wr-record:1`, `wr-history:1`, `oprecords:1,2,3` point respectively to their B/C/D/E read/UI pair plus `D-work-records`; `v69-screen-ledger.json` carries the same ordered node lists. All remain `gap` until independent implementation review; a registry path is a dependency declaration, not proof of build. Lane A promotes only reviewed rows atomically with their actual route. Run `node frontend/docs/architecture/check_v69_dependency_registry.cjs` after edits.

**Measurement status.** `.agent/W6-01-mock-measure-2.md` records successful 1440/390 mock captures: all seven screens have no document overflow with the section 2 wrap/clamp rules, table panels fit their stated caps, request header measures 363/844 with a 200-character title, `mheader` measures 137/394 with realistic Owner/Source stress, and real-label chips measure 31/70. These are mock measurements; implementation must prove the actual markup, especially cell child blocks and disclosures. A2 first capture measures new controls, pager, status, empty/refusal/cursor blocks, collapsed disclosures, horizontal-scroll affordance, row heights, all capped panels and document/table widths; subsequent page units repeat relevant measurements and expanded full-text cases. Record results in the owned evidence manifests before each unit review.


**Gate.** The prior unchanged-tree registry check (251 nodes, 43 linked pilot panels) and `tools/check-all.ps1` (11 guards) did not test W6 literals. On this edited planning tree, the registry checker passes: **262 nodes, 51 linked pilot panels**; `tools/check-all.ps1` passes **all 11 guards**. These checks validate registry/guard consistency, not implementation or browser behavior. The owner W5/W6 readiness rule still requires an independent fresh dry-read against merged main and Sonnet confirmation that every copy, wire field, route, producer, capture and cap is closed. No A1 dispatch until fresh independent readiness review confirms these literals and the completed mock measurement. At implementation, every unit runs named focused tests/guards on its exact revision; one full backend suite per slice, serialized; builders stop servers/browsers and drop private DBs. The owner later reviews the visual result.

## Readiness closure

| Review item | Closing artifact location |
| --- | --- |
| 1 | §1 Identity and time, Links; C1/C2 cards |
| 2 | §1 Parser, access and status; Refusal/status table; A1 card |
| 3 | §1 Envelope and row DTO table; Detail DTO |
| 4 | §1 Identity and time; B1/E1 cards |
| 5 | §1 DTO owner rule; §2 header and table |
| 6 | §4 Fixture command and clocks |
| 7 | §4 Fixture command and clocks; A1/B1/E1 cards |
| 8 | §2 shared controls and cap table |
| 9 | §4 Registry paths; registry JSON |
| 10 | §3 A2/B2/E2 owned files |
| 11 | §3 B2/B3/C2/C3/C4 cards; §2 header tabs |
| 12 | §2 oprecords read-only slot; E2 card |
| 13 | §1 Detail DTO; §2 record notice |
| 14 | §1 Links |
| 15 | §2 provenance literals |
| 16 | §1 Identity and time; C1 card |
| 17 | §1 Parser, access and status |
| 18 | §1 Identity and time |
| 19 | §1 Refusal/status table; §2 UI refusal copy |
| 20 | §3 unit review rule; §4 producer CLI |
| 21 | §3 unit dispatch rule |
| 22 | §1 Links and Detail DTO; C2 route |
| 23 | §2 incidents footer slot |
| 24 | §1 Links; A2/B2 cards |
| 25 | §2 shared controls and status copy |
| 26 | §2 maintenance notice |
| 27 | §2 preventive notice |
| 28 | §1 plan membership; §2 preventive binding |
| 29 | §2 overview lifecycle |
| 30 | §1 Links; §2 overview Source |
| 31 | §2 record correction selection |
| 32 | §2 history labels and occurrence disclosure |
| 33 | §1 operational `kind`; §2 oprecords cards |
| 34 | §2 oprecords footer and read-only gap; §1 Links |
| 35 | §2 long-title/anywhere rule; §4 measurements |
| 36 | §2 table/text disclosure and cap table; §4 measurements |
| OI-1 | section 1 Identity and time: root-time order and complete cursor tuple |
| OI-2 | section 3 A2/B2 copy, `siteWorkCases.tsx`, `siteWorkCases.test.tsx`, missing-claim exemption |
| OI-3 | section 1 time rule and literal detail JSON |
| OI-4 | section 2 Preventive card; section 3 B2/B3 one-tab multiset |
| OI-5 | section 2 request header/mheader caps and disclosure; mock measure 2 |
| OI-6 | section 1 page query; section 4 occurrence offsets and capture window |
| OI-7 | section 1 empty-scope precedence, provenance selected IDs, cursor key; A1 README/test |
| OI-8 | section 1 new detail route and route-specific 401 literals |
| OI-9 | section 4 capture artifacts, packets and conditional owner merge |
| OI-10 | section 2 chip/new-control caps; section 4 first capture measurement |
| OI-11 | section 1 Site Work strip manage-link helper and literal URLs; section 3 A2/B2 shared status/exemption sequence and tests |
| OI-11 time examples | section 1 request/plan/operational row and nested detail examples agree with section 4 offsets from the frozen fixture clock |
| A1Q-1 (Q1) | section 3.1 G1: one `$pgReaders` line in `configuration-persistence.ps1`; A1 Lane A list |
| A1Q-2 (Q2) | section 3.1 G2: adapter/service/router shapes, `work/composition.py` builders, `main.py` mount; A1 Lane A list |
| A1Q-3 (Q3) | section 3.1 Q3: W4 `case_basis`/`provenance_dto`/`missing_lineage` parity; `test_missing_lineage_matches_site_row` |
| A1Q-4 (Q4) | section 3.1 Q4: page-one status rule, cursor `page_one_mode`, estate wire-second page-two cutoff; two tests |
| A1Q-5 (Q5) | section 3.1 Q5: estate `imported_at < :to` candidate SQL copied, no `known_at` predicate; `test_candidates_imported_before_to` |
| A1Q-6 (Q6) | section 3.1 Q6: W4 `clock_timestamp()` read time and constructor-only `test_read_clock_override` |
| A1Q-7 (Q7) | section 3.1 Q7: W4 `_finding_link`/`_action_link` labels projected to `{label,href}`, W4 order, request-code SQL and order |
| A1Q-8 (Q8) | section 3.1 Q8: fallback links always carry the response `known_at` |
| A1Q-9 (Q9) | section 3.1 Q9 and section 1 examples: `service:w401-fixture` |
| A1Q-G (guard/composition sweep, backend) | section 3.1 G3-G6; B1/E1 no wiring, C1 composition and `main.py`; card lists A1, B1, C1, E1 |
| A1Q-F (guard/composition sweep, frontend) | section 3.1 F1-F6; card lists A2, B2, B3, C2, C3, C4, E2 (`operatorSiteRoutes.ts`, `v69-screen-ledger.json`) |
| A1Q-W5 | `.agent/W6-01-a1q-w5-sweep.md` (W5-01/W5-03 amendments for their own Architect; W5 files not edited here) |
| A1Q2-R1 | section 3.1 G6(c) superseded and A1Q2 R1: seed imports `PostgresWorkStore` for `test_db_clock_override`; A1 card |
| A1Q2-R2 | section 3.1 A1Q2 R2: `linked` fixture, test and `maintenance-linked` capture owned by B1/B2; A1, A2, B1, B2 cards |
| A1Q2-R3 | section 3.1 A1Q2 R3: token basis confirmed; new-field basis rule for B1/E1; B1 card |
| A1Q2-R4 | section 3.1 A1Q2 R4: `empty_scope` access-callback only, typed-response UI test; A1, A2 cards |
| A2Q1 (blocking) | section 3.1 A2Q1 and section 1 envelope: `state_counts`, A1 reopened, `test_state_counts_cover_full_selection`; card render rule |
| A2Q2 (blocking) | section 3.1 A2Q2: A2 owns additive `stress` fixture in `tools/w601_seed.py`; Owner cell is actor128 |
| A2Q3 (blocking) | section 3.1 A2Q3 and section 4: capture clock `2026-10-21T12:00:00Z`, window `2026-10-14..2026-10-21` |
| A2Q4-A2Q10 | section 3.1 A2Q4-A2Q10: source line, URL-only cutoff, refusal copy, footer slot, cell literals, registry reason edit, pager |
| A2Q-X1..X9 (readiness pass) | section 3.1 X1-X9; cards B1, B2, B3, C1, C2, C3, C4, E1, E2 |
| CL3-1 | section 3.1 CL3-1: loading sentences per unit (estate/W4 precedent); A2, B2, B3, C2, C3, C4, E2 cards |
| CL3-2 | section 3.1 CL3-2: Preventive card label/value/note, post-B3 link and href; B3 file list gains GlobalMaintenance files |
| CL3-3 | section 3.1 CL3-3 and section 1 detail DTO: C1 producer in `tools/w601_seed.py`, empty producer, REC href, `root_occurred_at` |
| CL3-4 | section 3.1 CL3-4: B1 `historical` plan correction producer and test |
| CL3-5 | section 3.1 CL3-5 and section 1: C2 slot-to-field map, `links.source_incident` |
| CL3-6 | section 3.1 CL3-6: E2 invalid `kind` and kind-filtered zero literals |
| CL3-7 | section 3.1 CL3-7: scan and `operatorRouteFrames.test.tsx` edits per unit (none beyond A2/B2/E2 rail) |
