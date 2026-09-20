"""The `ScenarioDefinitionRepository` over both scenario stores.

Shipped scenarios and user-authored scenarios share one globally unique
`scenario_id` space. This adapter merges the two stores into that one space,
and the way it merges them is the point: there is no overlay and no precedence.
The same `scenario_id` present in both stores is refused loudly at load rather
than resolving to either document, because an identity that resolves to
different content depending on store state cannot anchor the version a future
run freezes.

Origin is not encoded into identity. A user `scenario_id` is not prefixed and
nothing here can tell which store a scenario came from by reading its identity;
that is what the `origin` field on the record is for, and the store sets it.

There is no write path to delegate to, in either store. That is what makes
"T017 cannot create a scenario" structural rather than a convention.
"""

from __future__ import annotations

from typing import Protocol, Sequence

from assetops_backend.scenarios.identity import (
    scenario_id_key,
    validate_scenario_id,
)
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_backend.scenarios.ports import (
    ScenarioIdentityConflict,
    ScenarioNotFound,
)


class ReadableScenarioStore(Protocol):
    """One half of the identity space. Adapter-internal, never a domain port."""

    @property
    def store_name(self) -> str: ...

    def list_scenarios(self) -> Sequence[ScenarioDefinition]: ...


class CompositeScenarioRepository:
    """A `ScenarioDefinitionRepository` backed by the shipped and user stores."""

    def __init__(
        self, shipped: ReadableScenarioStore, user: ReadableScenarioStore
    ) -> None:
        self._shipped = shipped
        self._user = user

    def list_scenarios(self) -> tuple[ScenarioDefinition, ...]:
        by_identity: dict[str, tuple[str, ScenarioDefinition]] = {}

        for store in (self._shipped, self._user):
            for record in store.list_scenarios():
                key = scenario_id_key(record.scenario_id)
                previous = by_identity.get(key)
                if previous is not None:
                    previous_store, previous_record = previous
                    raise ScenarioIdentityConflict(
                        f"Scenario ID {record.scenario_id!r} is declared in "
                        f"the {previous_store} store as "
                        f"{previous_record.scenario_id!r} and in the "
                        f"{store.store_name} store. Scenario identity is "
                        "globally unique across both stores and is compared "
                        "without regard to case; there is no precedence "
                        "between them, so neither document is used."
                    )
                by_identity[key] = (store.store_name, record)

        return tuple(
            record
            for _, record in sorted(
                by_identity.values(), key=lambda entry: entry[1].scenario_id
            )
        )

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        validate_scenario_id(scenario_id)
        key = scenario_id_key(scenario_id)

        for record in self.list_scenarios():
            if scenario_id_key(record.scenario_id) == key:
                return record

        raise ScenarioNotFound(
            f"No scenario with scenario ID {scenario_id!r} is saved."
        )
