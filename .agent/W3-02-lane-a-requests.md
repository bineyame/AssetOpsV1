# W3-02 Lane A requests (from Lane B)

## Commit 1 - mount the Evidence router (closure 4 B6 row `1`)

Lane B added `estate/evidence_money.py` (`EstateEvidenceService`), `estate/adapters/postgres_evidence_money_read.py` (`PostgresEvidenceMoneyRead`) and `estate_evidence_money_api.py` (`build_estate_evidence_money_router`). The guard allows only `estate/composition.py` to import the estate adapter, so the builder must live there. Exact diffs:

`backend/assetops_backend/estate/composition.py` - add after `build_estate_index_service`:

```python
def build_estate_evidence_service(database_url: str | None) -> Any:
    """W3-02: None without a product database (the router answers 503, never an empty estate)."""
    if not database_url:
        return None
    from assetops_backend.analytics.claim_limit_read import ClaimLimitReadService, ClaimLimitRefusal
    from assetops_backend.estate.adapters.postgres_evidence_money_read import PostgresEvidenceMoneyRead
    from assetops_backend.estate.evidence_money import EstateEvidenceService

    base = build_estate_read(database_url)
    keys = ("findings", "assessments", "actions", "consequences", "eligibility", "cold", "ev", "provenance_reads",
            "inconsistent", "unavailable", "cold_site", "ev_site", "ev_money")
    return EstateEvidenceService(PostgresEvidenceMoneyRead(
        database_url, claim_limits=ClaimLimitReadService(base.assessments), claim_limit_refused=(ClaimLimitRefusal,),
        **{k: getattr(base, k) for k in keys}))
```

The test stand-in `evidence_read` in `backend/tests/test_w302_evidence_scope_snapshot_postgres.py` builds the same object. After the mount, it may call this builder instead.

`backend/assetops_backend/main.py` - imports and mount, after the W3-01 estate router (around `main.py:467`):

```python
from assetops_backend.estate.composition import build_estate_evidence_service  # with the existing estate import
from assetops_backend.estate_evidence_money_api import build_estate_evidence_money_router
...
    # W3-02 commit 1: the read-only estate Evidence root `/api/estate/evidence` (same tenant/access seams).
    app.include_router(build_estate_evidence_money_router(
        build_estate_evidence_service(database_url()), registry_tenant(registry),
        access=development_access, unavailable=(SiteStoreUnavailable,)))
```

No shell, registry or guard change is needed for commit 1. Please run the W3-01 estate API tests and the three `test_w302_evidence_*` files after the mount.

## Open questions for Lane A facades
See `.agent/W3-02-pending-rulings.md` c1-q1 (EV `historical_label` condition) and c1-q2 (`unknown_meter` not exposed by `EvSiteReads.capabilities_on`).

## Commit 2 - Evidence shell route, rail, registry and captures (closure 4 B6 row `2`)

Lane B landed `frontend/src/estate/EstateEvidence.tsx` (`EstateEvidencePage`, `ESTATE_EVIDENCE_PATH = "/evidence"`),
`estateEvidenceMoneyClient.ts` (`EstateEvidenceMoneyClient`, `createEstateEvidenceMoneyClient`), `estateEvidence.css`
and `estate/__tests__/estateEvidence.test.tsx` (6 tests). The page renders its own `PageHeader`; the frame owns `<main>`.

1. `frontend/src/shell/EstateRootFrames.tsx` - add:
```tsx
import { EstateEvidencePage } from "../estate/EstateEvidence";
import type { EstateEvidenceMoneyClient } from "../estate/estateEvidenceMoneyClient";

export function EstateEvidenceFrame({ client }: { client: EstateEvidenceMoneyClient }) {
  return (
    <main aria-label="Evidence">
      <EstateEvidencePage client={client} />
    </main>
  );
}
```
2. `frontend/src/App.tsx` - closure 4: a new optional prop, the W3-01 `estateIndex` unchanged:
   import `createEstateEvidenceMoneyClient, type EstateEvidenceMoneyClient` and `ESTATE_EVIDENCE_PATH`;
   `const defaultEstateEvidenceMoney = createEstateEvidenceMoneyClient();` beside `defaultEstateIndex` (App.tsx:124);
   prop `/** W3-02: the read-only estate Evidence (and, at commit 4, Financials) roots. */ estateEvidenceMoney?: EstateEvidenceMoneyClient;`
   after `estateIndex` (App.tsx:210), defaulted like it (App.tsx:236); route after the Actions root (App.tsx:404):
   `<Route path={ESTATE_EVIDENCE_PATH} element={<EstateEvidenceFrame client={estateEvidenceMoney} />} />`.
   Check no existing `/evidence` route shadows it (`operatorSiteRoutes.ts:217` is a Site-relative suffix only).
3. `frontend/src/shell/OperatorShellLayout.tsx:59` - the rail `Evidence` root becomes live:
   `{ kind: "live", to: "/evidence", label: "Evidence", end: false, group: "ASSURANCE", icon: "evidence" }`, plus the
   navigation-rail fixtures/truthfulness inventory that pins the unavailable roots (`tools/checks/navigation-*`).
4. Eyebrow: the mock eyebrow `Evidence` has no `PageHeader` slot (no page uses one); if the shell breadcrumb carries
   root crumbs, it should read `Evidence`. Lane B rendered no extra pre-panel element (the panel guard forbids one).
5. Registry/checker: `I-estate-evidence-root`, screen title `Portfolio evidence`, reviewed paths
   `globalevidence:1` = `Capability coverage across sites`, `globalevidence:2` = `Recurring evidence gaps` (closure 5
   S13); delivered only after this phase's independent review. Cards and notice stay inside those paths.
6. Worksheet: correct `.agent/W3-02-mock-measurements.md` to closure 4's ceiling maxima (Aggregation 390 = 187).
7. Captures (closure 1 "Mock copy, navigation and measured layout"): `node tools/layout-evidence.mjs` / CDP at
   1440 and 390 on the mounted `/evidence` with a three-Site stocked estate; record cards/coverage/gaps/notice rects and
   coverage/gaps table client/scroll width, document scroll width = client width. Maxima 1440/390: cards 137/291,
   coverage 314/468, gaps 316/703, notice 66/102. Lane B bounded the tables with internal scroll in
   `estateEvidence.css` (coverage scroll region max-height 200/300 px, gaps 180/420 px, min-width 520/330 px); if a
   capture exceeds a maximum, return the numbers to Lane B rather than editing the page CSS.
8. After mounting, run `src/estate/__tests__/estateEvidence.test.tsx`, the W3-01 `estateRoots.test.tsx`, the shell
   route/rail tests, tsc and `tools/check-all.ps1`.

## Commit 3 (Lane B -> Lane A mount)
`GET /api/estate/financials` is a second route on the already-mounted `build_estate_evidence_money_router`
(`backend/assetops_backend/estate_evidence_money_api.py`); its service is the mounted
`build_estate_evidence_service(...)` (`EstateEvidenceService.financials`, delegating to `estate/financials.py`).
So `main.py` needs **no change**; Lane A only verifies the mount: `create_app()` serves `/api/estate/financials`
(no-DB 503 body `{code:ESTATE_STORE_UNAVAILABLE,...,rows:null,total_count:null,groups:null,exclusions:null,diagnostics:null}`)
and adds a mount test beside `test_w302_evidence_composition_mount_no_db_503`. No guard change: the new domain
module `estate/financials.py` imports no driver; the adapter additions stay in `estate/adapters/postgres_evidence_money_read.py`
(`$pgReaders`). Commit 3 is held at closure 2 N3 (c3-q1) - review only after the ruling.

## Commit 4 - Financials shell route, rail, registry and captures (closure 4 B6 row `4`)

Lane B landed `frontend/src/estate/EstateFinancials.tsx` (`EstateFinancialsPage`, `ESTATE_FINANCIALS_PATH = "/financials"`),
`estateFinancialsWords.ts`, `estateFinancials.css` (the page also imports `estateEvidence.css` for the shared tones),
and in `estateEvidenceMoneyClient.ts` a separate `EstateFinancialsClient` / `createEstateFinancialsClient()`
(`GET /api/estate/financials`). `EstateEvidenceMoneyClient` is unchanged, so the commit-2 fakes need no edit.
Tests: `src/estate/__tests__/estateFinancials.test.tsx` (6). `src/test/settled.ts` LOADING gained
`financials across the estate` (the page's `Loading financials across the estate.`).

1. `frontend/src/shell/EstateRootFrames.tsx` - add:
```tsx
import { EstateFinancialsPage } from "../estate/EstateFinancials";
import type { EstateFinancialsClient } from "../estate/estateEvidenceMoneyClient";

/** W3-02 commit 4: the estate Financials root. */
export function EstateFinancialsFrame({ client }: { client: EstateFinancialsClient }) {
  return (
    <main aria-label="Financials">
      <EstateFinancialsPage client={client} />
    </main>
  );
}
```
2. `frontend/src/App.tsx` - a new optional prop beside `estateEvidenceMoney` (App.tsx:222), defaulted like it (App.tsx:250):
   `const defaultEstateFinancials = createEstateFinancialsClient();` beside `defaultEstateEvidenceMoney` (App.tsx:132);
   `/** W3-02 commit 4: the read-only estate Financials root. */ estateFinancials?: EstateFinancialsClient;`;
   route after the Evidence root (App.tsx:422): `<Route path={ESTATE_FINANCIALS_PATH} element={<EstateFinancialsFrame client={estateFinancials} />} />`.
   Check no existing `/financials` route shadows it (Site financial routes are Site-relative suffixes).
3. Rail: the `Financials` estate root becomes live (`OperatorShellLayout.tsx`, same shape as the Evidence entry,
   `to: "/financials"`, `end: false`), plus the navigation-rail fixtures/truthfulness inventory under `tools/checks/navigation-*`.
4. Registry/checker: `I-estate-money-root`, screen title `Portfolio financials`, reviewed paths
   `globalfinancials:1` = `Consequence register`, `globalfinancials:2` = `Aggregation rule` (closure 5 S13); delivered
   only after the commit-4 independent review. Status bar and notice stay inside those paths. Ledger
   `frontend/docs/architecture/v69-screen-ledger.json` `globalfinancials` `data_owner`, as c2 L3 did for Evidence:
   `Estate Financials read — GET /api/estate/financials (backend/assetops_backend/estate/financials.py)` (needs Architect
   confirmation of the literal; Lane B did not edit the ledger).
5. Captures (closure 1 "Mock copy, navigation and measured layout"; closure 4 maxima 1440/390: status 68/95, register
   293/448, notice 66/102, Aggregation 123/187) on the mounted `/financials` with a three-Site stocked estate and a
   partial variant, into `.agent/W3-02-evidence/` like commit 2: status/register/notice/Aggregation rects, register
   table client/scroll width, document scroll width = client width. Lane B bounds: register scroll region max-height
   176/300 px, min-width 500 px; grouping results list max-height 56/96 px. The Aggregation 123 px 1440 maximum is tight
   once result chips render; if a capture exceeds a maximum, return the numbers to Lane B rather than editing page CSS.
   After the captures land, Lane B adds `meetsMeasuredNarrowLayoutWithoutDocumentOverflow` to
   `estateFinancials.test.tsx` reading them (as `estateEvidence.test.tsx:610`).
6. After mounting, run `src/estate/__tests__/estateFinancials.test.tsx`, `estateEvidence.test.tsx`, the W3-01
   `estateRoots.test.tsx`, the shell route/rail tests, tsc and `tools/check-all.ps1`.

Also open for commit 4 (Lane B backend, not in this run): closure 5 B5's Financials route-read tests (follow generated
cold/EV `links.bridge`/`links.evidence` through the W2 Site reads, exact window/cutoff, no 422, base-route fallback),
and the one same-revision full real-Postgres suite.
