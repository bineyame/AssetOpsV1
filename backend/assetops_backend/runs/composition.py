"""The single composition module for run storage.

This is the one place in the product allowed to import
`assetops_backend.runs.adapters.*`; `tools/check-architecture.ps1` fails the
build on an adapter import from anywhere else. Every other caller receives the
port by injection and cannot name a storage technology even by accident.

Swapping the store is therefore one new adapter module plus one line here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from assetops_backend.runs.adapters.json_commit_store import JsonCommitStore
from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
from assetops_backend.runs.commit_ports import CommittedArtifactStore
from assetops_backend.runs.adapters.yaml_operational_action_log import YamlOperationalActionLog
from assetops_backend.runs.ports import OperationalActionLogPort, SimulationRunRepository

if TYPE_CHECKING:
    from assetops_backend.runs.replay_series import SeriesReader


def build_run_repository() -> SimulationRunRepository:
    """Choose the adapter that persists Draft SimulationRuns.

    One store. Unlike Sites and scenarios there is no shipped half to compose
    with: nothing ships a run, because a run is a record of something this
    installation did.
    """
    return YamlRunStore()


def build_operational_action_log() -> OperationalActionLogPort:
    """Choose the adapter that reads shipped operational-action logs (DIESEL-1-R3i S5-a)."""
    return YamlOperationalActionLog()


def build_commit_store() -> CommittedArtifactStore:
    """Choose the adapter that files sealed Commit artifacts (T027, D4)."""
    return JsonCommitStore()


def build_series_reader(database_url: str) -> "SeriesReader":
    """The replay series reader (0K3) over the product's evidence query and Foundation store."""
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.runs.replay_series import SeriesReader
    from assetops_backend.sites.composition import build_foundation_store

    return SeriesReader(build_postgres_assessment_store(database_url), build_foundation_store(database_url))
