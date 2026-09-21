"""Storage adapters for SimulationRuns.

Imported only by `assetops_backend.runs.composition`, which
`tools/check-architecture.ps1` enforces. Everything above the composition
module receives the port by injection and cannot name a storage technology
even by accident.
"""
