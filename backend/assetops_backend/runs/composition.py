"""The single composition module for run storage.

This is the one place in the product allowed to import
`assetops_backend.runs.adapters.*`; `tools/check-architecture.ps1` fails the
build on an adapter import from anywhere else. Every other caller receives the
port by injection and cannot name a storage technology even by accident.

Swapping the store is therefore one new adapter module plus one line here.
"""

from __future__ import annotations

from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_backend.runs.ports import SimulationRunRepository


def build_run_repository() -> SimulationRunRepository:
    """Choose the adapter that persists Draft SimulationRuns.

    One store. Unlike Sites and scenarios there is no shipped half to compose
    with: nothing ships a run, because a run is a record of something this
    installation did.
    """
    return YamlRunStore()
