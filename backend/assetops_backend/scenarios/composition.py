"""The single composition module for scenario storage.

This is the one place in the product allowed to import
`assetops_backend.scenarios.adapters.*`; `tools/check-architecture.ps1` fails
the build on an adapter import from anywhere else. Every other caller receives
the port by injection and cannot name a storage technology even by accident.

Swapping the store is therefore one new adapter module plus one line here.
"""

from __future__ import annotations

from assetops_backend.scenarios.adapters.composite_scenario_repository import (
    CompositeScenarioRepository,
)
from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import (
    ReadOnlyYamlScenarioStore,
)
from assetops_backend.scenarios.adapters.yaml_user_scenario_store import (
    UserYamlScenarioStore,
)
from assetops_backend.scenarios.ports import ScenarioDefinitionRepository


def build_scenario_repository() -> ScenarioDefinitionRepository:
    """Choose the adapters that serve ScenarioDefinitions.

    Two stores, one identity space. The shipped store holds tracked read-only
    definitions and ships the Fuel Loss Event; the user store is where later
    authoring will land. The composite refuses an identity that resolves in
    both rather than picking one, so there is no overlay and no precedence to
    reason about anywhere above this line.
    """
    return CompositeScenarioRepository(
        shipped=ReadOnlyYamlScenarioStore(),
        user=UserYamlScenarioStore(),
    )
