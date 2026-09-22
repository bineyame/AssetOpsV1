"""The gated run setup API: the two outcomes, over HTTP.

The route exists to keep one distinction visible to a client, and these tests
are that distinction: a refusal is a 422 that allocated no `run_id` and wrote
nothing, and a created Draft is a 201 that is persisted whether it is `READY`
or `BLOCKED`. A client that could not tell the two apart would have to guess
whether there is anything to go and look at.

Ports are faked in memory, so nothing here touches a configuration root or
writes to disk. The gate itself is proved in `test_simulator_lab_gate.py`.
"""

from __future__ import annotations

from typing import Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from run_fixtures import (
    FakeRuns,
    FakeScenarios,
    FakeSites,
    model_profile,
    publication_profile,
    scenario,
    setup_request,
    site,
)
from scenario_fixtures import scenario_document

from assetops_backend.main import health_router
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.simulator_lab_api import build_simulator_lab_router
from assetops_backend.sites.ports import SiteStoreUnavailable
from assetops_backend.sites_api import build_sites_router

RUNS_PATH = "/api/simulator-lab/runs"
RUN_PROFILES_PATH = "/api/simulator-lab/run-profiles"


class _NoTemplates:
    def list_templates(self) -> Sequence[object]:
        return ()

    def get_template(self, template_id: str) -> object:  # pragma: no cover
        raise AssertionError("no run route reads a template")


def client(
    *,
    runs: FakeRuns | None = None,
    sites: FakeSites | None = None,
    scenarios: FakeScenarios | None = None,
    model=None,
    publication=None,
) -> tuple[TestClient, FakeRuns]:
    """An app serving the gated router, with the fixtures' profiles.

    The router is built directly rather than through `create_app` for one
    reason: `create_app` composes the SHIPPED profiles, which is right for
    the product and wrong for a test about the route. The shipped model
    cannot execute the example scenario, so every response would be
    `BLOCKED` and `READY` would be untestable here. That the gate composes
    the shipped profiles at all is proved in `test_simulator_lab_gate.py`,
    and the shipped combination has a test of its own at the bottom of this
    file.
    """
    store = FakeRuns() if runs is None else runs
    site_repository = sites or FakeSites((site(),))

    app = FastAPI(title="AssetOps", version="0.0.0")
    app.include_router(health_router)
    app.include_router(build_sites_router(site_repository))
    app.include_router(
        build_simulator_lab_router(
            _NoTemplates(),
            site_repository,
            scenarios or FakeScenarios((scenario(),)),
            store,
            (model or model_profile(),),
            (publication or publication_profile(),),
        )
    )
    return TestClient(app), store


class TestTheProfilesRoute:
    def test_it_serves_what_a_profile_models_and_resolves(self) -> None:
        served, _ = client()
        body = served.get(RUN_PROFILES_PATH).json()

        model = body["model_profiles"][0]
        assert model["model_profile_id"] == "example-model"
        assert {
            state["state_key"] for state in model["supported_states"]
        } == {"example-stored-volume", "example-demand"}

        publication = body["publication_profiles"][0]
        assert publication["device_signal_cadence_minutes"] == 15
        assert publication["simulator_source_id"] == "example-simulator-source"
        assert publication["gateway_id"] == "example-gateway"

    def test_an_undeclared_value_is_null_rather_than_absent(self) -> None:
        served, _ = client(publication=publication_profile(gateway_id=None))
        body = served.get(RUN_PROFILES_PATH).json()

        assert body["publication_profiles"][0]["gateway_id"] is None


class TestACreatedDraft:
    def test_a_ready_draft_is_created_and_persisted(self) -> None:
        served, store = client()

        response = served.post(RUNS_PATH, json=setup_request())

        assert response.status_code == 201
        run = response.json()["run"]
        assert run["execution_status"] == "READY"
        assert run["lifecycle_status"] == "DRAFT"
        assert run["blocking_reasons"] == []
        assert [record.run_id for record in store.written] == [run["run_id"]]

    def test_a_blocked_draft_is_created_and_persisted_with_its_reasons(
        self,
    ) -> None:
        served, store = client(
            publication=publication_profile(cadence_minutes=None)
        )

        response = served.post(RUNS_PATH, json=setup_request())

        assert response.status_code == 201
        run = response.json()["run"]
        assert run["execution_status"] == "BLOCKED"
        assert [reason["kind"] for reason in run["blocking_reasons"]] == [
            "CADENCE_NOT_RESOLVED"
        ]
        assert len(store.written) == 1

    def test_the_summary_carries_the_frozen_inputs_and_their_answerers(
        self,
    ) -> None:
        served, _ = client()
        run = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        rows = {row["field"]: row for row in run["frozen_inputs"]}

        assert rows["Site"]["answered_by"] == "SITE_FOUNDATION"
        assert rows["Scenario version"]["answered_by"] == "SCENARIO"
        assert rows["Seed"]["answered_by"] == "RUN_INPUT"
        assert rows["Seed"]["value"] == "4242"
        assert (
            rows["Cadence for example-device-reading"]["answered_by"]
            == "MODEL_PROFILE"
        )
        for row in run["frozen_inputs"]:
            assert row["answered_by_detail"]

    def test_the_summary_claims_no_execution_and_no_evidence(self) -> None:
        """There is no field these could arrive in, which is the point."""
        served, _ = client()
        run = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        for absent in (
            "progress",
            "elapsed",
            "state",
            "trace",
            "staged",
            "committed",
            "commit_eligibility",
            "evidence",
            "findings",
        ):
            assert absent not in run, absent

    def test_the_intervention_history_is_served_empty(self) -> None:
        served, _ = client()
        run = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        assert (
            run["deterministic_identity"]["intervention_history"] == []
        )


class TestARefusal:
    def test_a_refusal_says_no_run_was_created(self) -> None:
        served, store = client()

        response = served.post(RUNS_PATH, json=setup_request(seed=-1))

        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["code"] == "RUN_REQUEST_INVALID"
        assert detail["refusal_kind"] == "REQUEST_INVALID"
        assert detail["run_created"] is False
        assert detail["message"]
        assert store.written == []

    def test_each_refusal_kind_arrives_as_its_own_code(self) -> None:
        """Different facts, different codes. A client that had to read the
        message to tell a malformed interval from an unconfigured site would
        be parsing product copy."""
        served, store = client(sites=FakeSites(()))
        unconfigured = served.post(RUNS_PATH, json=setup_request())

        served_two, store_two = client()
        malformed = served_two.post(
            RUNS_PATH,
            json=setup_request(
                interval={
                    "start_time": "2026-09-21T05:00:00Z",
                    "end_time": "2026-09-21T00:00:00Z",
                }
            ),
        )

        assert unconfigured.json()["detail"]["code"] == "RUN_VERSION_UNAVAILABLE"
        assert malformed.json()["detail"]["code"] == "RUN_INTERVAL_INVALID"
        assert store.written == []
        assert store_two.written == []

    def test_an_unreal_time_zone_is_refused_over_http(self) -> None:
        served, store = client(
            sites=FakeSites((site(timezone="Africa/Atlantis"),))
        )

        response = served.post(RUNS_PATH, json=setup_request())

        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "RUN_TIMEZONE_NOT_IANA"
        assert store.written == []

    def test_an_unreachable_site_store_is_a_store_failure_not_a_refusal(
        self,
    ) -> None:
        """"We could not look" is not "your request was wrong"."""
        served, store = client(
            sites=FakeSites(failure=SiteStoreUnavailable("unreadable"))
        )

        response = served.post(RUNS_PATH, json=setup_request())

        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "SITE_STORE_UNAVAILABLE"
        assert store.written == []


class TestTheShippedFuelLossEventCannotReachReady:
    """The accepted residual, as a run setup outcome.

    `D-2026-09-21-scenario-execution-contract` accepted that the declared
    causes do not reach either reading and said what run setup does about it
    until one of the three ways out is chosen. This is that, end to end: the
    shipped scenario against the shipped model profile is a persisted Draft
    that is `BLOCKED`, with the unreached readings named among the reasons.
    """

    def test_the_shipped_scenario_blocks_on_its_unreached_readings(
        self,
    ) -> None:
        from pathlib import Path

        import yaml

        from assetops_backend.runs.profiles import (
            LAB_PUBLICATION_PROFILE,
            MINIMAL_FUEL_TANK_MODEL,
        )
        from assetops_backend.runs.service import RunSetupService
        from assetops_backend.sites.site_parsing import parse_site_document

        repo_root = Path(__file__).resolve().parents[2]
        shipped = parse_scenario_document(
            yaml.safe_load(
                (
                    repo_root / "config" / "scenarios" / "fuel-loss-event.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped definition",
            origin="SHIPPED",
        )
        mg_001 = parse_site_document(
            yaml.safe_load(
                (repo_root / "var" / "sites" / "mg-001.yaml").read_text(
                    encoding="utf-8"
                )
            ),
            source="a fixture site",
        )

        store = FakeRuns()
        setup = RunSetupService(
            store,
            FakeSites((mg_001,)),
            FakeScenarios((shipped,)),
            model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
            publication_profiles=(LAB_PUBLICATION_PROFILE,),
            now=lambda: "2026-09-21T09:00:00Z",
        )

        record = setup.create_draft_run(
            {
                "site_id": "MG-001",
                "foundation_version": 1,
                "scenario_id": "fuel-loss-event",
                "scenario_version": 1,
                "interval": {
                    "start_time": "2026-09-21T00:00:00Z",
                    "end_time": "2026-09-22T17:00:00Z",
                },
                "timestep_minutes": 15,
                "seed": 20260921,
                "model_profile": {
                    "profile_id": "minimal-fuel-tank",
                    "profile_version": 1,
                },
                "publication_profile": {
                    "profile_id": "simulator-lab-publication",
                    "profile_version": 1,
                },
                "run_inputs": [],
            }
        )

        assert record.execution_status == "BLOCKED"
        assert store.written == [record]

        # Three reasons and all three are the same kind: states the first
        # model profile does not model. Named, so that widening the profile
        # is visible here rather than silent.
        #
        # It was five before Amendment 1's proposal (e), and the other two
        # were the readings the scenario's declared causes do not reach. Run
        # setup has no kernel, so it never had standing to judge that; the
        # outcome is unchanged and the reasons are sounder.
        assert {reason.kind for reason in record.blocking_reasons} == {
            "STATE_NOT_SUPPORTED"
        }
        assert {reason.subject for reason in record.blocking_reasons} == {
            "site-load-demand",
            "plane-of-array-irradiance",
            "fuel-level-reporting-availability",
        }

        # And it froze everything anyway, which is what makes it inspectable.
        assert record.deterministic_identity.site.site_id == "MG-001"
        assert [
            item.state_key
            for item in record.deterministic_identity.initialization_inputs
        ] == ["fuel-tank-capacity", "fuel-tank-volume"]
