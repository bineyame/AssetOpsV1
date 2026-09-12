# AssetOps

Operator tooling for distributed energy sites, and a Simulator Lab that behaves
like a real site and publishes through the same ingestion semantics.

Start with `AGENTS.md` and `.ai/START_HERE.md`.

## Layout

| Path | Contents |
| --- | --- |
| `backend/` | FastAPI backend (`assetops_backend`) |
| `frontend/` | React + TypeScript UI (Vite) |
| `simulator/` | Deterministic Python simulator (`assetops_simulator`) |
| `tools/` | Repository guard scripts |
| `.ai/` | Product, architecture, workflow and planning documents |
| `tasks/` | Task definitions; completed tasks move to `tasks/completed/` |
| `Docs/` | Product specification, UI mockups, site line diagrams |

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

`check-architecture.ps1` enforces the stack and module-direction seam: it fails
on UI-to-simulator and simulator-to-product imports. `check-agent-workflow.ps1`
validates the repository's agent-workflow governance files and task metadata.

Neither guard is wired to a CI runner yet; both must be invoked manually.
