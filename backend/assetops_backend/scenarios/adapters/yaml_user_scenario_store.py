"""YAML adapter over the user-authored scenario store.

`USER_SCENARIO_STORE_ROOT` is declared here and nowhere else. One owned
location for the writable root is what keeps "outside the shipped configuration
roots" checkable, and `tools/check-architecture.ps1` fails the build if a
second module declares it.

The root is where later scenario authoring will persist what a user writes, and
it exists now because identity has to be disjoint from the beginning: a
`scenario_id` that was unique only among shipped definitions would stop being
unique the first time somebody authored one, and by then a run would have
frozen a version against it.

T017 ships no scenario creation flow, so this adapter reads and nothing more.
There is no create, update, rename, or delete method here, which means the
product cannot write a scenario at all today - not by convention, but because
there is no code that could. The slice that adds authoring adds the write path,
its atomicity, and the guard exemption together.
"""

from __future__ import annotations

from pathlib import Path

from assetops_backend.scenarios.adapters.yaml_scenario_documents import (
    read_scenario_records,
)
from assetops_backend.scenarios.models import ScenarioDefinition

REPO_ROOT = Path(__file__).resolve().parents[4]

#: The user-authored scenario store. It lives outside every shipped
#: configuration root and outside version control: `.gitignore` covers `var/`,
#: and `tools/check-architecture.ps1` checks that it does.
USER_SCENARIO_STORE_ROOT = REPO_ROOT / "var" / "scenarios"

STORE_NAME = "user"

#: Provenance the store supplies, because the document must not be able to
#: claim it.
ORIGIN = "USER"


class UserYamlScenarioStore:
    """The user-authored half of the scenario identity space."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = USER_SCENARIO_STORE_ROOT if root is None else root

    @property
    def store_name(self) -> str:
        return STORE_NAME

    def list_scenarios(self) -> tuple[ScenarioDefinition, ...]:
        return read_scenario_records(
            self._root, store_name=STORE_NAME, origin=ORIGIN
        )
