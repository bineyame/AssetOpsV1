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
- **X3 (clocks).** B2, B3 and E2 list captures use the A2Q3 clock/window. B1 `detail` and `stress` request captures for C2–C4 use `--clock 2026-10-20T12:00:00Z`. The meaningful C2–C4 historical request pin is `known_at=2026-10-20T11:59:04Z` on the first `detail` request: COMPLETE is selected, later REOPEN and Correction are absent. The earlier `2026-10-21T12:00:00Z` detail pin and `2026-10-20T12:00:01Z` `detail-history` option are superseded; neither shows the prescribed older selected rows.
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
- **X7 (paging).** B2, B3 and E2 use A2Q10, and an E2 kind chip resets the trail. C4's local pager follows the C4 pre-flight ruling: five authored rows/page after removing revision 1, exact string order, and an in-panel `Showing` line. C3's record panel has no pager and uses the §2 vertical scroll.
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

**A2Q11 and R5–R8. Rail pins outside the card, and the A2 readings** (`.agent/W6-01a-phase-handoff.md`, A2 rebuild Run, `0a96d21e`). *Produced by Claude Architect under the 2026-10-22 Codex-reset exception; Codex to review retrospectively.*

**A2Q11.** Six frontend test files pin the operator rail's live links, and CL3-7 missed them. Each rail unit (A2, B2, E2) owns all six, in Lane A, and edits only the pinned rail literals below, in rail order. Each list replaces the previous unit's list.

The six files:

- `frontend/src/shell/__tests__/operatorSiteTabs.test.tsx`
- `frontend/src/shell/__tests__/simulatorLabWorkspaceEntryPoint.test.tsx`
- `frontend/src/shell/__tests__/siteDetailRoute.test.tsx`
- `frontend/src/shell/__tests__/siteFoundationRoute.test.tsx`
- `frontend/src/shell/__tests__/sitesIndexRoute.test.tsx`
- `frontend/src/ui/__tests__/sharedVisualVocabulary.test.tsx`

Where each literal lives:

| Literal | Location |
| --- | --- |
| Labels | `operatorSiteTabs.test.tsx:387` (inline). The `OPERATOR_NAVIGATION_LABELS` const in `simulatorLabWorkspaceEntryPoint.test.tsx:50`, `siteDetailRoute.test.tsx:104` and `siteFoundationRoute.test.tsx:133`. The const used at `sitesIndexRoute.test.tsx:299` and `:381`. |
| Hrefs | `siteDetailRoute.test.tsx:446`, `siteFoundationRoute.test.tsx:469`, and `sharedVisualVocabulary.test.tsx:150` (written there with `SITES_PATH` for `/sites`) |
| Icons | `sharedVisualVocabulary.test.tsx:207` |
| Admitted | `ADMITTED_SINCE_T004` in `siteFoundationRoute.test.tsx:127` |

| Unit | Labels | Hrefs | Icon pairs | `ADMITTED_SINCE_T004` |
| --- | --- | --- | --- | --- |
| A2 | `["Portfolio", "Sites", "Findings", "Actions", "Incidents", "Evidence", "Financials"]` | `["/portfolio", "/sites", "/findings", "/actions", "/incidents", "/evidence", "/financials"]` | `[["Portfolio", "grid"], ["Sites", "site"], ["Findings", "finding"], ["Actions", "action"], ["Incidents", "incident"], ["Evidence", "evidence"], ["Financials", "money"]]` | `["Findings", "Actions", "Evidence", "Financials", "Portfolio", "Incidents"]` |
| B2 | A2 list with `"Maintenance"` after `"Incidents"` | A2 list with `"/maintenance"` after `"/incidents"` | A2 pairs with `["Maintenance", "work"]` after Incidents | A2 list plus `"Maintenance"` |
| E2 | B2 list with `"Operational records"` after `"Maintenance"` | B2 list with `"/operational-records"` after `"/maintenance"` | B2 pairs with `["Operational records", "log"]` after Maintenance | B2 list plus `"Operational records"` |

Other rules for these edits:

- `T004_OPERATOR_NAVIGATION_LABELS` stays unchanged, because it is history. The test at `siteFoundationRoute.test.tsx:455` keeps its name and logic; appending to `ADMITTED_SINCE_T004` is its documented way to admit a reviewed root.
- At `siteDetailRoute.test.tsx:446` and `siteFoundationRoute.test.tsx:469`, the per-href render loop must still pass for the new root. Each new page renders its own `h1` (`Incidents`, `Maintenance` or `Operational records`), and its refusal state renders when no API is available.
- A comment `// W6-01{a|b|e}: {label} rail root is live.` goes above each edited literal.
- No other line changes. `tools/checks` stays untouched.
- Done when the full `src/shell src/estate src/sites src/work src/ui` vitest run passes with 0 failures.

**R5 (confirmed).** `Show records` sends the edited `from` and `to` and keeps any URL `known_at` unchanged. It clears `cursor` and `globalWorkTrail`. `Reload` re-reads page one of the same `from`/`to`/`known_at`.

**R6 (confirmed).** The control bar, status line and `Showing` line sit in the shared `.site-date-bar` slot. The refusal, invalid-query, cursor-changed and empty-scope blocks carry `data-page-refusal`, so `expectV69Panels("incidents")` passes without editing `frontend/src/test/panelStructure.ts`. B2, B3, E2 and C2–C4 use the same slot and attribute.

**R7 (confirmed).** `frontend/src/test/settled.ts` is not edited. Each W6 page test waits with `await waitFor(() => expect(container.querySelector("[data-global-work-loading]")).toBeNull())` after `settledScreen()`. B2, B3, E2 and C2–C4 do the same.

**R8 (confirmed).** The double fetch comes from React StrictMode in the Vite dev server only, and needs no dedupe code. Capture manifests record one response per page read. Each manifest notes `dev server StrictMode issues each read twice; the built app issues one`, and every assertion uses the response the page rendered.

**Residual, not ruled (for the Codex retrospective).** `frontend/src/estate/EstateEvidence.tsx:46` renders the inert mock examples `Operational records · Not available yet` and `Preventive plan · Not available yet`. Both become stale once E2 and B3 are live. This is not a guard or composition gap, and no W6 unit owns that file, so no builder touches it.

