"""Service boundary over the scenario port.

Each service receives its ports by injection and never learns where anything is
stored. A fake in-memory repository satisfies them with no import from
`adapters/`, which is the practical test of whether a port is a real seam or a
naming convention.

Neither service catches `yaml.YAMLError`, `OSError`, or any other
store-specific exception. If one reaches here, the adapter failed to translate
it and the seam has leaked; that is a seam failure to fix in the adapter, not a
defensive `except` to add here.

The scenario domain resolves no site (T025g,
`D-2026-10-01-run-binds-scenario-to-site`). A scenario version states what it
needs of a site; run setup is the only component that holds a scenario and a
site together. Neither service here holds a Site port, and
`test_run_binds_scenario_to_site.py` fails if one is added back.
"""

from __future__ import annotations

from assetops_backend.scenarios.models import (
    ScenarioAddressNeed,
    ScenarioDefinition,
    ScenarioParameter,
    ScenarioSiteNeeds,
)
from assetops_backend.scenarios.ports import AnyScenarioDefinition, ScenarioDefinitionRepository
from assetops_backend.state_refs import StateRef


class ScenarioCatalogService:
    """Read-only scenario catalog use cases.

    Ordering is fixed here so the catalog does not depend on directory
    iteration order in whichever adapter is composed.
    """

    def __init__(self, repository: ScenarioDefinitionRepository) -> None:
        self._repository = repository

    def list_scenarios(self) -> tuple[AnyScenarioDefinition, ...]:
        """Return every saved scenario (legacy or `cold-scenario/1`), ordered by scenario identity."""
        return tuple(
            sorted(
                self._repository.list_scenarios(),
                key=lambda scenario: scenario.scenario_id,
            )
        )

    def get_scenario(self, scenario_id: str) -> AnyScenarioDefinition:
        """Return one scenario by its identity.

        Raises:
            ScenarioNotFound: no such `scenario_id`.
        """
        return self._repository.get_scenario(scenario_id)


class ScenarioDetailService:
    """One scenario, plus what it needs of whichever site a run binds it to.

    This service creates, renames, clones, and promotes nothing, and it reads
    no site. What it adds to the record is derived from the document alone.
    """

    def __init__(self, repository: ScenarioDefinitionRepository) -> None:
        self._repository = repository

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        """Return one scenario by its identity.

        Raises:
            ScenarioNotFound: no such `scenario_id`.
        """
        return self._repository.get_scenario(scenario_id)


def scenario_site_needs(scenario: ScenarioDefinition) -> ScenarioSiteNeeds:
    """The addresses and device sources a scenario version names.

    Every address an entry, an entry parameter, a public parameter or a
    parameter bound names, once, with the execution roles it is named in.
    Device observation sources are listed as declared. Nothing here is checked
    against a site: an address a site does not declare is run setup's blocking
    reason, never a detail-screen state.
    """
    roles: dict[str, set[str]] = {}
    refs: dict[str, StateRef] = {}

    def note(ref: StateRef | None, role: str | None) -> None:
        if ref is None:
            return
        key = ref.addressed_key
        refs.setdefault(key, ref)
        bucket = roles.setdefault(key, set())
        if role is not None:
            bucket.add(role)

    def note_parameter(parameter: ScenarioParameter) -> None:
        note(parameter.state_ref, parameter.execution_role)
        if parameter.bounds is not None:
            note(parameter.bounds.state_ref, None)

    for entry in scenario.timeline:
        note(entry.state_ref, entry.execution_role)
        for parameter in entry.parameters:
            note_parameter(parameter)
    for parameter in scenario.public_parameters:
        note_parameter(parameter)

    addresses = tuple(
        ScenarioAddressNeed(
            address=key,
            scope=refs[key].scope,
            component_id=refs[key].component_id,
            state_key=refs[key].state_key,
            execution_roles=tuple(sorted(roles[key])),
        )
        for key in sorted(refs)
    )
    return ScenarioSiteNeeds(
        addresses=addresses,
        device_sources=tuple(
            source
            for source in scenario.observation_sources
            if source.device_id is not None
        ),
    )
