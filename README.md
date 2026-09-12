# AssetOps

Operator tooling for distributed energy sites, and a Simulator Lab that behaves
like a real site and publishes through the same ingestion semantics.

Start with `AGENTS.md` and `.ai/START_HERE.md`.

## Layout

| Path | Contents |
| --- | --- |
| `config/` | Runtime configuration shared by backend and frontend |
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
  the UI, the `/api/simulator-lab/*` router is not mounted, and the operator
  shell shows no Simulator Lab entry point. Direct URLs and API calls are not
  served.
- `true`: the empty Simulator Lab shell is reachable, a Simulator Lab entry
  point appears in operator navigation, and `GET /api/simulator-lab/status`
  reports that the surface is served. There is still no run execution.

Parsing is strict: unknown keys and non-boolean flag values are rejected rather
than coerced. Restart the backend and the Vite dev server after editing the
file.

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
`check-agent-workflow.ps1` validates the repository's agent-workflow governance
files and task metadata.

Neither guard is wired to a CI runner yet; both must be invoked manually.
