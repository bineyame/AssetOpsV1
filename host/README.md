# Composition leaf

`host/` wires the product and the simulator together and is imported by nothing.
That is v4 section 3.2: `backend/` imports no simulator package, `simulator/`
imports no `assetops_backend` module at all, `host/` may import both, and nothing
imports `host/`. `tools/check-architecture.ps1` holds all four.

- `execution_adapter.py` turns a frozen `SimulationRun` and the versioned
  definition it names into the neutral `FrozenWorldInputs` a kernel executes,
  and returns the private trajectory beside the inputs it was built from.
- `tests/` is the only place a test may compose both sides. The dependency guard
  scans the whole backend tree including `backend/tests`, and a composing test is
  not an exception to it.

Run the suite from this directory:

```powershell
..\.venv\Scripts\python.exe -m pytest
```

It needs `assetops-backend`, `assetops-contracts` and `assetops-simulator`
installed into the workspace virtual environment. From the repository root:

```powershell
.venv\Scripts\python.exe -m pip install -e backend -e contracts -e simulator
```
