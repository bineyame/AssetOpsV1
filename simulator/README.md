# Simulator Root

Python deterministic simulator root for the AssetOps modular monolith.

T001 establishes this root only. Simulator execution is unavailable: there is no
world state, no run execution, no private truth, and no staged or released
output.

Dependency direction: the simulator must not import from or write into the
product backend root (`backend/assetops_backend`). The frontend must not import
simulator modules. `tools/check-architecture.ps1` guards both directions.
