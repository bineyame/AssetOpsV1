"""Read-only YAML adapter over the shipped scenario store.

`config/scenarios/` is git-tracked configuration that is read-only at runtime.
This module reads it and does nothing else: it has no write, create, rename,
delete, or temporary-file path, and `tools/check-architecture.ps1` fails the
build if a write-capable call appears in any module that names a shipped
configuration root.

Unlike the shipped Site store, this one does not ship empty. T017 has no
scenario creation flow, so a fresh checkout needs a tracked definition for the
catalog to show, and `config/scenarios/fuel-loss-event.yaml` is it. That is
parallel to the shipped template catalog rather than to the shipped Site store:
the Fuel Loss Event is a directly selectable `ScenarioDefinition`, not an
archetype something is created from, so it is listed as itself.

It is still the other half of one identity space rather than a tier above the
user store. There is no overlay and no precedence between the two.
"""

from __future__ import annotations

from pathlib import Path

from assetops_backend.scenarios.adapters.yaml_scenario_documents import (
    read_scenario_records,
)
from assetops_backend.scenarios.models import ScenarioDefinition

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The shipped, read-only scenario configuration root. Separate from the
#: writable user store and from every Site root: shipped configuration never
#: lives inside a directory anything writes to.
SHIPPED_SCENARIO_ROOT = REPO_ROOT / "config" / "scenarios"

STORE_NAME = "shipped"

#: Provenance the store supplies, because the document must not be able to
#: claim it.
ORIGIN = "SHIPPED"


class ReadOnlyYamlScenarioStore:
    """The shipped half of the scenario identity space.

    Read-only is structural rather than a convention: there is no method here
    that writes, so no caller can write through it and no adapter has a write
    path to implement.
    """

    def __init__(self, root: Path | None = None) -> None:
        self._root = SHIPPED_SCENARIO_ROOT if root is None else root

    @property
    def store_name(self) -> str:
        return STORE_NAME

    def list_scenarios(self) -> tuple[ScenarioDefinition, ...]:
        return read_scenario_records(
            self._root, store_name=STORE_NAME, origin=ORIGIN
        )
