# AssetOps

Operator tooling for distributed energy sites, and a Simulator Lab that behaves
like a real site and publishes through the same ingestion semantics.

Start with `AGENTS.md` and `.ai/START_HERE.md`.

## Layout

| Path | Contents |
| --- | --- |
| `config/` | Runtime configuration shared by backend and frontend |
| `config/site-templates/` | Shipped, read-only site configuration templates |
| `config/sites/` | Shipped, read-only site store. Ships empty: M1 ships zero sites |
| `var/` | Writable store for user-authored configuration. Gitignored, created at runtime |
| `backend/` | FastAPI backend (`assetops_backend`) |
| `frontend/` | React + TypeScript UI (Vite) |
| `simulator/` | Deterministic Python simulator (`assetops_simulator`) |
| `tools/` | Repository guard scripts |
| `.ai/` | Product, architecture, workflow and planning documents |
| `tasks/` | Task definitions; completed tasks move to `tasks/completed/` |
| `Docs/` | Product specification, UI mockups, site line diagrams |

## Configuration

`config/app-config.json` is the single source of truth for feature flags. The
backend reads it at startup and the frontend imports the same file, so one edit
moves both serving boundaries.

```json
{
  "simulator_lab": {
    "enabled": false
  }
}
```

`simulator_lab.enabled` gates simulator surfaces and execution only. Operator
routes, and later Site history, provenance, accepted evidence, analytics and
Replay, are unaffected by it in both states.

- `false` (the shipped default): the Simulator Lab route is not registered in
  the UI, the `/api/simulator-lab/*` router is not mounted, and neither the
  workspace chrome nor operator navigation shows any Simulator Lab entry point,
  label, or hint. Direct URLs and API calls are not served.
- `true`: the Simulator Lab shell is reachable, an `Open Simulator Lab` entry
  point appears in the workspace utility chrome,
  `GET /api/simulator-lab/status` reports that the surface is served, the
  Lab's Site Templates catalog is served at
  `GET /api/simulator-lab/site-templates`, and the create-a-site flow is served
  at `/simulator-lab/create-site` with `POST /api/simulator-lab/sites` behind
  it. The Sites index offers a link into that flow. There is still no run
  execution.

The Sites index, one site's page, and the `GET /api/sites` and
`GET /api/sites/{site_id}` routes behind them are operator capabilities and are
never gated. They are served identically in both states, and a site created while the
Lab was enabled stays fully visible when it is disabled, because the gate covers
surfaces and execution and never objects or stores. A gate-off build with an
empty Sites index and no way to add a site is the correct state, not a defect.

Simulator Lab is a separate developer workspace, not an operator screen, so its
entry point lives in workspace-level chrome above the operator shell and never
in operator navigation. Operator navigation lists the same three operator
routes in both flag states, and the Simulator Lab shell renders outside the
operator route layout with no operator chrome.

Parsing is strict: unknown keys and non-boolean flag values are rejected rather
than coerced. Restart the backend and the Vite dev server after editing the
file.

## Shipped site templates

`config/site-templates/` holds the shipped site configuration templates. They
are read-only at runtime and separate from any site store: a template declares
`template_id`, `template_version` and foundation content, and never a
`site_id`, lifecycle status, location, or place-bound timezone. A template is
not a site, and this milestone ships zero sites - every site in the product is
one a user created.

Templates are reached only through the `SiteTemplateCatalog` port in
`backend/assetops_backend/sites/`, whose YAML adapter is imported by the single
composition module. Documents are strictly validated on load: unknown keys,
unsupported values, duplicate identities, oversized documents and
over-cardinality collections are refused rather than normalized.

## Sites

`config/sites/` is the shipped, read-only site store. It ships empty on purpose:
M1 ships zero canonical sites, so first run has a genuinely empty Sites index
and every site in the product is one a user created.

`var/sites/` is the writable store for user-authored site documents. It is
created at runtime, is gitignored, and lives outside every shipped
configuration root. Removing a user-created site is a developer action on this
directory for the whole milestone: the product offers no delete, archive, or
tombstone.

The two stores share one globally unique `site_id` space with no overlay and no
precedence. The same `site_id` in both fails loudly at load rather than
resolving to either document, and creation refuses an identity already present
in either store, compared without regard to case.

A site is created by copying a shipped template: the template's foundation
content is deep-copied into the new site, which records `template_id` and
`template_version` as provenance. A later template change never alters a site
already created from it. `site_id` is immutable, and configuration is fixed at
creation in M1 - there is no edit, save, publish, rename, duplicate, delete, or
version history anywhere in the product.

Configuration origin (`SHIPPED` / `USER`), source mode (`LIVE` / `SIMULATED`),
and lifecycle status are three independent facts. In M1 every user-created site
also has `SIMULATED` source mode, because the Simulator Lab is the only creation
path; they coincide by circumstance and neither is derived from the other.

A site is addressed by `site_id` and by nothing else. `GET /api/sites/{site_id}`
serves one site and the operator route `/sites/:siteId` renders it; a row in the
Sites index is the way in. Lookup compares identity without regard to case, and
both the response and the screen show the stored canonical spelling, so one site
can never present as two. An unknown site is an explicit not-found surface, not
an empty site.

A site's page shows what the product knows: identity, name, type, location,
timezone, lifecycle status, source mode, configuration origin, template
provenance, and the foundation's version and validity start. Integration
readiness, evidence availability and source health are separate concepts with no
truthful source yet, so each is stated as unavailable with its reason rather
than zeroed or given a health value. There is no telemetry, chart, tab bar,
diagram, image panel, or action control of any kind.

Operator navigation does not grow for a site surface and loses the items that
stopped being true. The parameterless `Site details` route and item are gone,
because a Site Details link that names no site is not a destination;
`Site configuration` is still parameterless and is removed by the slice that
gives it an identified replacement.

Site presentation lives in `frontend/src/sites/`: one read model, one view
model, one set of components, composed by the operator shell and later by the
Lab's site view. Nothing there imports shell code, simulator code, or the
feature flag, and nothing there takes a shell, mode, or variant prop.

## Running things

Commands below use invocations that work regardless of the PowerShell execution
policy. If your policy is `Bypass` or `Unrestricted`, `npm test` and
`.\tools\check-architecture.ps1` also work directly; under `Restricted` or
`RemoteSigned` they fail on `npm.ps1` and unsigned `.ps1` files, which is why the
`npm.cmd` and `-ExecutionPolicy Bypass` forms are given here.

Python is not on `PATH` on the current development machine — only a Microsoft
Store alias. The repository-root `.venv` is the working interpreter.

### Backend

```
cd backend
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m uvicorn assetops_backend.main:app --reload
```

Health route: `GET http://127.0.0.1:8000/api/health`

### Frontend

```
cd frontend
npm.cmd install
npm.cmd test
npm.cmd run typecheck
npm.cmd run build
npm.cmd run dev
```

`npm.cmd run dev` proxies `/api` to `http://127.0.0.1:8000`, so run the backend
alongside it. The proxy is dev-server configuration only: the built app and the
backend are served from one origin and request the same paths either way.

### Guards

```
powershell -NoProfile -ExecutionPolicy Bypass -File tools\check-architecture.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools\check-agent-workflow.ps1
```

`check-architecture.ps1` enforces the stack and module-direction,
simulator/product, and simulator feature gate seams: it fails on
UI-to-simulator, simulator-to-product, and product-to-simulator imports, on a
missing or non-boolean `simulator_lab.enabled`, and on a simulator URL declared
outside the gated route modules (`backend/assetops_backend/simulator_lab_api.py`
and `frontend/src/shell/simulatorLabRoutes.tsx`). Everything else must import
the exported path constant, so an entry point cannot be added outside the gate.
It also enforces the configuration persistence and shipped-configuration
seams: imports resolving into `backend/assetops_backend/sites/adapters/` are
permitted only from `backend/assetops_backend/sites/composition.py` or from
inside that package, the yaml, pathlib and sqlite3 modules and direct file
opening are banned inside the sites package above the adapter layer, no module
that resolves a shipped configuration root may hold a write-capable call, the
shipped site store ships empty, configuration is written only by
`backend/assetops_backend/sites/adapters/yaml_user_site_store.py`, and the
writable user store root has exactly one owning declaration and is covered by
`.gitignore`.

Two further checks protect the shared site presentation substrate: site
presentation components, site view-model derivation, site detail components, and
site read-model types resolve in `frontend/src/sites/` only, and that directory
imports no shell code, no simulator code, and no feature flag, and declares no
shell, mode, or variant discriminant. A shell route frame, named `*Frame`, may
compose the substrate; it may not define what a site looks like.

One check protects navigation truthfulness: the parameterless `/site-details`
path appears nowhere in `frontend/src`, and the identified site route must be
present for that absence to mean anything.

Every check carries a non-vacuity assertion that fails if it stops matching real
code.

`check-agent-workflow.ps1` validates the repository's agent-workflow governance
files and task metadata.

Neither guard is wired to a CI runner yet; both must be invoked manually.
