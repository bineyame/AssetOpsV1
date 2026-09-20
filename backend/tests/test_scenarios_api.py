"""The gated scenario catalog and detail API.

Four things are proved here:

- the catalog and the detail route serve records, with every field coming from
  a scenario document rather than from this module or from the route;
- the target-site resolution states are all four reachable, and each is a
  different fact: a resolvable target enables `Open target Site`, an
  unresolvable one produces a control state with an accessible reason, and an
  unreadable Site store is neither of those;
- private test-oracle expectations are separated by the payload builders, not
  by a caller's discretion;
- nothing on either payload is an assessment, a health result, a confidence, a
  severity, a Finding, or any other product conclusion.

Ports are faked in memory. No test here touches a configuration root except the
one that reads the shipped definition through the real composition, which is
the point of that test.
"""

from __future__ import annotations

import json
from typing import Sequence

import pytest
from fastapi.testclient import TestClient
from scenario_fixtures import scenario_document

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import (
    ScenarioIdentityConflict,
    ScenarioNotFound,
    ScenarioStoreUnavailable,
)
from assetops_backend.simulator_lab_api import (
    scenario_private_expectations,
    scenario_public_detail,
    scenario_public_summary,
)
from assetops_backend.sites.models import (
    SiteFoundation,
    SiteLocation,
    SiteRecord,
    SiteSource,
)
from assetops_backend.sites.ports import (
    SiteIdentityConflict,
    SiteNotFound,
    SiteStoreUnavailable,
)

ENABLED = FeatureFlags(simulator_lab_enabled=True)
DISABLED = FeatureFlags(simulator_lab_enabled=False)

SCENARIOS_PATH = "/api/simulator-lab/scenarios"

#: A string that appears only inside a private expectation. If it turns up in a
#: public payload, something read the private field.
PRIVATE_SENTINEL = "oracle-only-marker-9e3a"


def scenario(**overrides: object) -> ScenarioDefinition:
    document = scenario_document()
    document.update(overrides)
    return parse_scenario_document(document, source="a test", origin="SHIPPED")


def scenario_with_sentinel() -> ScenarioDefinition:
    document = scenario_document()
    document["private_expectations"][0]["statement"] = (
        f"A later analysis must reach {PRIVATE_SENTINEL} for this to pass."
    )
    return parse_scenario_document(document, source="a test", origin="SHIPPED")


class FakeScenarios:
    """An in-memory `ScenarioDefinitionRepository`.

    It imports nothing from `adapters/`, which is the practical test of whether
    the port is a seam or a naming convention.
    """

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


class FakeSites:
    """An in-memory `SiteRepository`, enough for target resolution."""

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
        raise AssertionError("no scenario route may write a site")


def site(site_id: str = "MG-900") -> SiteRecord:
    return SiteRecord(
        site_id=site_id,
        display_name="Configured mini-grid",
        site_type="MINIGRID",
        location=SiteLocation(country="Uganda", locality="Kalangala"),
        timezone="Africa/Kampala",
        lifecycle_status="PLANNED",
        origin="USER",
        source=SiteSource(mode="SIMULATED"),
        template=None,
        foundation=SiteFoundation(
            version=1,
            valid_from="2026-01-01T00:00:00Z",
            summary="A configured mini-grid.",
            components=(),
        ),
    )


def client(
    *,
    scenarios: FakeScenarios | None = None,
    sites: FakeSites | None = None,
    flags: FeatureFlags = ENABLED,
) -> TestClient:
    return TestClient(
        create_app(
            flags,
            site_template_catalog=_NoTemplates(),
            site_repository=sites or FakeSites((site(),)),
            scenario_repository=scenarios or FakeScenarios((scenario(),)),
        )
    )


class _NoTemplates:
    def list_templates(self) -> Sequence[object]:
        return ()

    def get_template(self, template_id: str) -> object:  # pragma: no cover
        raise AssertionError("no scenario route reads a template")


class TestTheGate:
    def test_no_scenario_path_is_served_when_the_gate_is_closed(self) -> None:
        closed = TestClient(
            create_app(DISABLED, site_repository=FakeSites((site(),)))
        )

        assert closed.get(SCENARIOS_PATH).status_code == 404
        assert closed.get(f"{SCENARIOS_PATH}/example-scenario").status_code == 404

    def test_a_closed_gate_never_reads_the_scenario_store(self) -> None:
        """The gate decides whether a surface is served, not what a store
        answers. A closed build must not touch the store to find that out."""

        class Exploding:
            def list_scenarios(self) -> Sequence[ScenarioDefinition]:
                raise AssertionError("the closed gate read the scenario store")

            def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
                raise AssertionError("the closed gate read the scenario store")

        closed = TestClient(
            create_app(
                DISABLED,
                site_repository=FakeSites((site(),)),
                scenario_repository=Exploding(),
            )
        )

        assert closed.get(SCENARIOS_PATH).status_code == 404


class TestTheCatalog:
    def test_the_catalog_serves_the_record(self) -> None:
        body = client().get(SCENARIOS_PATH).json()

        assert len(body["scenarios"]) == 1
        row = body["scenarios"][0]
        assert row["scenario_id"] == "example-scenario"
        assert row["display_name"] == "Example scenario"
        assert row["version"]["scenario_version"] == 2
        assert row["target_site"]["site_id"] == "MG-900"

    def test_the_catalog_carries_no_private_expectation(self) -> None:
        body = client(
            scenarios=FakeScenarios((scenario_with_sentinel(),))
        ).get(SCENARIOS_PATH)

        assert PRIVATE_SENTINEL not in body.text
        assert "private_expectations" not in body.text

    def test_the_catalog_carries_no_timeline(self) -> None:
        """A catalog row says which scenarios are saved. Reading one is the
        detail route's job, and a listing that carried the whole timeline
        would make the two routes two answers to the same question."""
        row = client().get(SCENARIOS_PATH).json()["scenarios"][0]

        assert "timeline" not in row
        assert "public_parameters" not in row

    @pytest.mark.parametrize(
        "failure",
        [
            ScenarioStoreUnavailable("unreadable"),
            ScenarioIdentityConflict("two documents, one identity"),
        ],
    )
    def test_an_unreadable_or_conflicting_store_is_stated(
        self, failure: Exception
    ) -> None:
        """Never degraded into "no scenarios are saved"."""
        response = client(scenarios=FakeScenarios(failure=failure)).get(
            SCENARIOS_PATH
        )

        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "SCENARIO_STORE_UNAVAILABLE"

    def test_an_empty_catalog_is_a_real_answer(self) -> None:
        response = client(scenarios=FakeScenarios(())).get(SCENARIOS_PATH)

        assert response.status_code == 200
        assert response.json() == {"scenarios": []}


class TestTheDetailRoute:
    def test_the_detail_route_serves_the_timeline_in_authored_order(self) -> None:
        body = client().get(f"{SCENARIOS_PATH}/example-scenario").json()
        timeline = body["scenario"]["timeline"]

        assert [entry["event_id"] for entry in timeline] == [
            "first-entry",
            "second-entry",
            "third-entry",
        ]
        assert [entry["sequence"] for entry in timeline] == [1, 2, 3]
        assert [entry["offset_minutes"] for entry in timeline] == [0, 120, 240]
        assert [entry["entry_kind"] for entry in timeline] == [
            "EVENT",
            "INTERVENTION",
            "EVIDENCE_CONDITION",
        ]
        assert [entry["category"] for entry in timeline] == [
            "LOAD",
            "MAINTENANCE",
            "DATA_QUALITY",
        ]
        assert timeline[0]["parameters"][0] == {
            "parameter_id": "peak-demand",
            "display_name": "Peak demand",
            "value": 64.0,
            "unit": "kW",
        }

    def test_identity_is_matched_without_regard_to_case(self) -> None:
        response = client().get(f"{SCENARIOS_PATH}/Example-Scenario")

        assert response.status_code == 200
        assert response.json()["scenario"]["scenario_id"] == "example-scenario"

    def test_an_unknown_scenario_is_not_found(self) -> None:
        response = client().get(f"{SCENARIOS_PATH}/no-such-scenario")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SCENARIO_NOT_FOUND"

    def test_a_malformed_identity_is_not_found_rather_than_unavailable(
        self,
    ) -> None:
        """A malformed identity and an unreadable store must not arrive as the
        same answer: no scenario could ever carry the first."""
        response = client().get(f"{SCENARIOS_PATH}/not a scenario id")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SCENARIO_NOT_FOUND"


class TestTargetSiteResolution:
    def test_a_resolvable_target_resolves(self) -> None:
        body = client(sites=FakeSites((site("MG-900"),))).get(
            f"{SCENARIOS_PATH}/example-scenario"
        ).json()

        resolution = body["target_resolution"]
        assert resolution["state"] == "RESOLVED"
        assert resolution["site_id"] == "MG-900"
        assert resolution["display_name"] == "Configured mini-grid"
        assert resolution["reason"]

    def test_the_stored_spelling_of_the_site_comes_back(self) -> None:
        """A link is built from what is configured, not from what the scenario
        document happened to capitalise."""
        body = client(sites=FakeSites((site("mg-900"),))).get(
            f"{SCENARIOS_PATH}/example-scenario"
        ).json()

        assert body["scenario"]["target_site"]["site_id"] == "MG-900"
        assert body["target_resolution"]["site_id"] == "mg-900"

    def test_an_unconfigured_target_is_a_screen_state_not_a_failure(self) -> None:
        response = client(sites=FakeSites(())).get(
            f"{SCENARIOS_PATH}/example-scenario"
        )

        assert response.status_code == 200
        resolution = response.json()["target_resolution"]
        assert resolution["state"] == "NOT_CONFIGURED"
        assert resolution["site_id"] is None
        assert "MG-900" in resolution["reason"]

    def test_the_scenario_still_reads_when_its_target_is_missing(self) -> None:
        """The whole point of the parser/service split.

        If resolution happened in the parser, removing a Site would make a
        scenario document unreadable and take the catalog with it.
        """
        body = client(sites=FakeSites(())).get(
            f"{SCENARIOS_PATH}/example-scenario"
        ).json()

        assert len(body["scenario"]["timeline"]) == 3

    @pytest.mark.parametrize(
        "failure",
        [
            SiteStoreUnavailable("unreadable"),
            SiteIdentityConflict("two documents, one identity"),
        ],
    )
    def test_an_unreadable_site_store_is_unknown_not_absent(
        self, failure: Exception
    ) -> None:
        """"We could not look" and "it is not there" are different facts."""
        body = client(sites=FakeSites(failure=failure)).get(
            f"{SCENARIOS_PATH}/example-scenario"
        ).json()

        resolution = body["target_resolution"]
        assert resolution["state"] == "UNAVAILABLE"
        assert resolution["site_id"] is None
        assert "unknown" in resolution["reason"]

    def test_a_template_derived_target_has_no_site_to_resolve(self) -> None:
        derived = scenario(
            target_site={
                "policy": "TEMPLATE_DERIVED",
                "site_id": None,
                "template_id": "hybrid-mini-grid-100kw",
                "requirement": "A site built from the hybrid archetype.",
            }
        )

        body = client(scenarios=FakeScenarios((derived,))).get(
            f"{SCENARIOS_PATH}/example-scenario"
        ).json()

        resolution = body["target_resolution"]
        assert resolution["state"] == "NOT_APPLICABLE"
        assert resolution["site_id"] is None
        assert resolution["reason"]

    def test_every_unresolved_state_carries_a_reason(self) -> None:
        """A control that is unavailable without a visible reason is a dead
        end, so the reason is part of the payload rather than a UI string."""
        for sites in (
            FakeSites(()),
            FakeSites(failure=SiteStoreUnavailable("unreadable")),
        ):
            resolution = (
                client(sites=sites)
                .get(f"{SCENARIOS_PATH}/example-scenario")
                .json()["target_resolution"]
            )
            assert resolution["state"] != "RESOLVED"
            assert len(resolution["reason"]) > 0

    def test_no_scenario_route_writes_a_site(self) -> None:
        """`FakeSites.create_site` raises. Reaching the detail route at all
        proves no scenario read path creates, renames, clones, or promotes."""
        assert (
            client().get(f"{SCENARIOS_PATH}/example-scenario").status_code == 200
        )


class TestThePublicPrivateBoundary:
    def test_the_public_payloads_never_read_the_private_field(self) -> None:
        """The sentinel is in the record and in the private payload, so this
        assertion cannot pass because the sentinel was never there."""
        record = scenario_with_sentinel()

        public = json.dumps(
            [scenario_public_summary(record), scenario_public_detail(record)]
        )
        private = json.dumps(scenario_private_expectations(record))

        assert PRIVATE_SENTINEL not in public
        assert PRIVATE_SENTINEL in private

    def test_the_separation_is_in_the_record_not_in_the_rendering(self) -> None:
        """Two parsed fields, not one field with a visibility flag.

        A flag would put the boundary in whoever renders the record, which is
        exactly the presentation-only split the decision refuses.
        """
        record = scenario_with_sentinel()

        assert record.public_parameters
        assert record.private_expectations
        assert not hasattr(record.private_expectations[0], "public")
        assert not hasattr(record.public_parameters[0], "private")

    def test_the_detail_route_carries_the_expectations_in_their_own_section(
        self,
    ) -> None:
        body = client(
            scenarios=FakeScenarios((scenario_with_sentinel(),))
        ).get(f"{SCENARIOS_PATH}/example-scenario").json()

        assert PRIVATE_SENTINEL in json.dumps(body["private_expectations"])
        assert PRIVATE_SENTINEL not in json.dumps(body["scenario"])
        assert body["private_expectations"][0]["oracle_kind"] == "DETECTION"

    def test_no_operator_payload_has_a_field_an_expectation_could_occupy(
        self,
    ) -> None:
        """Operator surfaces are ungated and are never given the private half.

        Asserted over the served operator payload rather than over the scenario
        module, because the claim is about what an operator receives.
        """
        operator = TestClient(
            create_app(ENABLED, site_repository=FakeSites((site(),)))
        )

        index = operator.get("/api/sites")
        detail = operator.get("/api/sites/MG-900")

        for response in (index, detail):
            assert response.status_code == 200
            assert "expectation" not in response.text
            assert "oracle" not in response.text
            assert "scenario" not in response.text


class TestNoProductConclusion:
    """A scenario says what the simulated world is intended to do.

    It does not report that AssetOps observed anything, so no payload here may
    carry an assessment, a source-health result, a confidence, a severity, an
    incident, an action, a verification outcome, or a Finding.
    """

    BANNED = (
        "finding",
        "assessment",
        "severity",
        "confidence",
        "health",
        "incident",
        "verification",
        "commit",
        "ingest",
        "replay",
        "evidence_status",
        "anomaly",
        "alert",
    )

    def test_the_catalog_states_no_conclusion(self) -> None:
        text = client().get(SCENARIOS_PATH).text.casefold()

        for word in self.BANNED:
            assert word not in text

    def test_the_detail_payload_states_no_conclusion(self) -> None:
        text = (
            client().get(f"{SCENARIOS_PATH}/example-scenario").text.casefold()
        )

        for word in self.BANNED:
            assert word not in text

    def test_the_payload_carries_no_run_field(self) -> None:
        """No run exists, so nothing here may carry one's identity, clock,
        seed, status, or result."""
        body = client().get(f"{SCENARIOS_PATH}/example-scenario").json()

        assert "run_id" not in json.dumps(body)
        for key in ("seed", "start_time", "timestep_seconds", "status"):
            assert key not in body["scenario"]
            assert all(key not in entry for entry in body["scenario"]["timeline"])


class TestTheShippedDefinitionThroughTheRealComposition:
    def test_the_fuel_loss_event_is_served_from_the_real_scenario_source(
        self,
    ) -> None:
        """No fake anywhere in this one. It is the claim the slice is for:
        the catalog renders the shipped Fuel Loss Event from the real store."""
        served = TestClient(
            create_app(ENABLED, site_repository=FakeSites((site("MG-001"),)))
        )

        listed = served.get(SCENARIOS_PATH).json()["scenarios"]
        assert any(row["scenario_id"] == "fuel-loss-event" for row in listed)

        body = served.get(f"{SCENARIOS_PATH}/fuel-loss-event").json()
        assert body["scenario"]["display_name"] == "Fuel Loss Event"
        assert body["target_resolution"]["state"] == "RESOLVED"
        assert len(body["scenario"]["timeline"]) == 8
        assert len(body["private_expectations"]) == 4

    def test_the_shipped_timeline_exercises_the_whole_proposed_taxonomy(
        self,
    ) -> None:
        """The proposal is reviewable only if the screen can show it.

        A taxonomy with three categories on screen and seven in the code would
        ask the user to accept four values they never saw.
        """
        from assetops_backend.scenarios.models import (
            EVENT_CATEGORIES,
            TIMELINE_ENTRY_KINDS,
        )

        served = TestClient(
            create_app(ENABLED, site_repository=FakeSites((site("MG-001"),)))
        )
        timeline = served.get(f"{SCENARIOS_PATH}/fuel-loss-event").json()[
            "scenario"
        ]["timeline"]

        assert {entry["category"] for entry in timeline} == EVENT_CATEGORIES
        assert {entry["entry_kind"] for entry in timeline} == TIMELINE_ENTRY_KINDS
