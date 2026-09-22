"""Shared fixtures for the run setup tests.

One valid setup request, one configured Site, and one pair of profiles that
can execute the example scenario, which every test starts from and breaks in
exactly one way. That is what makes a refusal test about the rule it names: if
each test built its own request, a test could pass because the request was
malformed in a second way the service happened to reach first - which is the
mistake T017's review found in a deliberate violation and T018 repeated twice.

The Site here is `MG-900`, which is the Site the shared scenario fixture
declares it targets. It configures the device and signal that fixture reports
through, declares a topology, and declares signal mappings, so a test that
wants any of those absent removes exactly one of them.

The shipped Fuel Loss Event and `MG-001` are deliberately NOT used here. Those
belong in the tests that are about the shipped documents, and a fixture that
mirrored them would make every run setup test a test of shipped content.
"""

from __future__ import annotations

from typing import Any, Sequence

from scenario_fixtures import scenario_document

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.ports import RunIdentityConflict, RunNotFound
from assetops_backend.runs.profiles import (
    FoundationBinding,
    ModelProfile,
    PublicationProfile,
    SupportedState,
)
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioNotFound
from assetops_backend.sites.models import (
    DeviceSignal,
    FoundationDevice,
    FoundationTopology,
    Rating,
    SignalMapping,
    SiteComponent,
    SiteFoundation,
    SiteLocation,
    SiteRecord,
    SiteSource,
    TopologyNode,
)
from assetops_backend.sites.ports import SiteNotFound

#: The interval the example scenario fits inside. Its last entry is a point at
#: 240 minutes, and the interval is half-open, so 300 minutes covers it with
#: room and divides by the timestep.
START_TIME = "2026-09-21T00:00:00Z"
END_TIME = "2026-09-21T05:00:00Z"


def scenario(**overrides: Any) -> ScenarioDefinition:
    document = scenario_document()
    document.update(overrides)
    return parse_scenario_document(document, source="a test", origin="SHIPPED")


#: The sentinel for "this test did not say", as distinct from "this test says
#: the foundation declares none". Those are two different fixtures and `None`
#: is the second: a default of `None` made "no topology is refused" pass by
#: building the default topology and never reaching the rule it named.
DEFAULT = object()


def site(
    *,
    site_id: str = "MG-900",
    timezone: str = "Africa/Kampala",
    topology: Any = DEFAULT,
    devices: Any = DEFAULT,
    components: Any = DEFAULT,
    signal_mappings: Any = DEFAULT,
    foundation_version: int = 1,
) -> SiteRecord:
    """The configured Site the example scenario targets."""
    return SiteRecord(
        site_id=site_id,
        display_name="Configured mini-grid",
        site_type="MINIGRID",
        location=SiteLocation(country="Uganda", locality="Kalangala"),
        timezone=timezone,
        lifecycle_status="PLANNED",
        origin="USER",
        source=SiteSource(mode="SIMULATED"),
        template=None,
        foundation=SiteFoundation(
            version=foundation_version,
            valid_from="2026-01-01T00:00:00Z",
            summary="A configured mini-grid.",
            components=(
                default_components() if components is DEFAULT else components
            ),
            topology=default_topology() if topology is DEFAULT else topology,
            devices=default_devices() if devices is DEFAULT else devices,
            signal_mappings=(
                default_mappings()
                if signal_mappings is DEFAULT
                else signal_mappings
            ),
        ),
    )


def default_components() -> tuple[SiteComponent, ...]:
    return (
        SiteComponent(
            component_id="example-store",
            component_type="FUEL_TANK",
            display_name="Stored volume",
            rating=Rating(value=500.0, unit="L"),
        ),
    )


def default_topology() -> FoundationTopology:
    return FoundationTopology(
        nodes=(
            TopologyNode(
                node_id="example-store",
                component_id="example-store",
                node_role="FUEL_STORAGE",
            ),
        ),
        connections=(),
    )


def default_devices() -> tuple[FoundationDevice, ...]:
    return (
        FoundationDevice(
            device_id="example-sensor",
            device_type="SENSOR",
            display_name="Stored level sensor",
            component_id="example-store",
            signals=(
                DeviceSignal(
                    signal_id="example-level",
                    display_name="Stored level",
                    unit="L",
                ),
            ),
        ),
    )


def default_mappings() -> tuple[SignalMapping, ...]:
    return (
        SignalMapping(
            mapping_id="example-store-level",
            device_id="example-sensor",
            signal_id="example-level",
            component_id="example-store",
        ),
    )


def model_profile(
    *,
    profile_id: str = "example-model",
    version: int = 1,
    supported_states: tuple[SupportedState, ...] | None = None,
) -> ModelProfile:
    """A profile that can execute everything the example scenario needs.

    Every test that proves a `BLOCKED` state narrows this rather than widening
    something: a profile that supported nothing would block for reasons the
    test did not mean.
    """
    return ModelProfile(
        model_profile_id=profile_id,
        model_profile_version=version,
        display_name="Example model",
        statement="Models the example scenario's states.",
        supported_states=(
            default_supported_states()
            if supported_states is None
            else supported_states
        ),
    )


def default_supported_states() -> tuple[SupportedState, ...]:
    return (
        SupportedState(
            state_key="example-stored-volume",
            supported_roles=frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}),
            foundation_binding=None,
            statement="The stored volume can be caused and reported.",
        ),
        SupportedState(
            state_key="example-demand",
            supported_roles=frozenset({"FORCING_INPUT"}),
            foundation_binding=None,
            statement="Demand can be forced on the run.",
        ),
    )


def foundation_bound_states() -> tuple[SupportedState, ...]:
    """The same states, with the stored volume bound to a Foundation rating."""
    return (
        SupportedState(
            state_key="example-stored-volume",
            supported_roles=frozenset({"CAUSAL_INPUT", "REPORTED_OBSERVATION"}),
            foundation_binding=FoundationBinding(
                component_type="FUEL_TANK", rating_unit="L"
            ),
            statement="The stored volume is bounded by a declared rating.",
        ),
        SupportedState(
            state_key="example-demand",
            supported_roles=frozenset({"FORCING_INPUT"}),
            foundation_binding=None,
            statement="Demand can be forced on the run.",
        ),
    )


def publication_profile(
    *,
    profile_id: str = "example-publication",
    version: int = 1,
    cadence_minutes: int | None = 15,
    simulator_source_id: str | None = "example-simulator-source",
    gateway_id: str | None = "example-gateway",
) -> PublicationProfile:
    """A profile that resolves all three of the inputs nothing else may."""
    return PublicationProfile(
        publication_profile_id=profile_id,
        publication_profile_version=version,
        display_name="Example publication profile",
        statement="Declares the cadence and the two publication identities.",
        device_signal_cadence_minutes=cadence_minutes,
        simulator_source_id=simulator_source_id,
        gateway_id=gateway_id,
    )


def setup_request(**overrides: Any) -> dict[str, Any]:
    """A valid setup request, fresh each call."""
    request: dict[str, Any] = {
        "site_id": "MG-900",
        "foundation_version": 1,
        "scenario_id": "example-scenario",
        "scenario_version": 2,
        "interval": {"start_time": START_TIME, "end_time": END_TIME},
        "timestep_minutes": 15,
        "seed": 4242,
        "model_profile": {"profile_id": "example-model", "profile_version": 1},
        "publication_profile": {
            "profile_id": "example-publication",
            "profile_version": 1,
        },
        "run_inputs": [],
    }
    request.update(overrides)
    return request


class FakeRuns:
    """An in-memory `SimulationRunRepository`.

    It imports nothing from `adapters/`, which is the practical test of
    whether the port is a seam or a naming convention. It also records every
    write, so a refusal test can assert that nothing was written rather than
    only that an error was raised.
    """

    def __init__(self, *, failure: Exception | None = None) -> None:
        self.written: list[SimulationRun] = []
        self._failure = failure

    def create_run(self, record: SimulationRun) -> SimulationRun:
        if self._failure is not None:
            raise self._failure
        for existing in self.written:
            if existing.run_id == record.run_id:
                raise RunIdentityConflict(record.run_id)
        self.written.append(record)
        return record

    def get_run(self, run_id: str) -> SimulationRun:
        # A store that cannot be reached cannot be read either. The failure
        # applies to every method rather than only to the write, because a
        # fake that fails on one is a fake of a store nothing has.
        if self._failure is not None:
            raise self._failure
        for record in self.written:
            if record.run_id == run_id:
                return record
        raise RunNotFound(run_id)

    def list_runs(self) -> Sequence[SimulationRun]:
        if self._failure is not None:
            raise self._failure
        return tuple(self.written)


class FakeSites:
    """An in-memory `SiteRepository`."""

    def __init__(
        self,
        records: Sequence[SiteRecord] = (),
        *,
        failure: Exception | None = None,
    ) -> None:
        self._records = tuple(records)
        self._failure = failure

    def list_sites(self) -> Sequence[SiteRecord]:
        if self._failure is not None:
            raise self._failure
        return self._records

    def get_site(self, site_id: str) -> SiteRecord:
        if self._failure is not None:
            raise self._failure
        for record in self._records:
            if record.site_id.casefold() == site_id.casefold():
                return record
        raise SiteNotFound(site_id)

    def create_site(self, record: SiteRecord) -> SiteRecord:  # pragma: no cover
        raise AssertionError("no run route may write a site")


class FakeScenarios:
    """An in-memory `ScenarioDefinitionRepository`."""

    def __init__(
        self,
        records: Sequence[ScenarioDefinition] = (),
        *,
        failure: Exception | None = None,
    ) -> None:
        self._records = tuple(records)
        self._failure = failure

    def list_scenarios(self) -> Sequence[ScenarioDefinition]:
        if self._failure is not None:
            raise self._failure
        return self._records

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        if self._failure is not None:
            raise self._failure
        for record in self._records:
            if record.scenario_id.casefold() == scenario_id.casefold():
                return record
        raise ScenarioNotFound(scenario_id)
