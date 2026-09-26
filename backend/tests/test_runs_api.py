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
    END_TIME,
    START_TIME,
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
from assetops_backend.runs.ports import RunStoreUnavailable
from assetops_backend.sites.models import SiteRecord
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
        # The publication profile supplies a cadence, and until T020 this row
        # said the model profile answered it.
        assert (
            rows["Cadence for example-device-reading"]["answered_by"]
            == "PUBLICATION_PROFILE"
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


class TestTheInventory:
    """Which Drafts exist, and nothing about what they have done."""

    def _three_runs(self) -> tuple[TestClient, FakeRuns]:
        served, store = client()
        for _ in range(3):
            assert served.post(RUNS_PATH, json=setup_request()).status_code == 201
        return served, store

    def test_it_lists_the_persisted_drafts(self) -> None:
        served, store = self._three_runs()

        body = served.get(RUNS_PATH).json()

        assert len(body["runs"]) == 3
        assert {row["run_id"] for row in body["runs"]} == {
            record.run_id for record in store.written
        }

    def test_each_row_is_backed_by_the_record(self) -> None:
        served, store = client()
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        row = served.get(RUNS_PATH).json()["runs"][0]

        assert row["run_id"] == created["run_id"]
        assert row["site_id"] == "MG-900"
        assert row["scenario_id"] == "example-scenario"
        assert row["scenario_version"] == 2
        assert row["foundation_version"] == 1
        assert row["lifecycle_status"] == "DRAFT"
        assert row["execution_status"] == "READY"
        assert row["interval"]["start_time"] == START_TIME
        assert row["interval"]["end_time"] == END_TIME
        assert row["blocking_reason_count"] == 0

    def test_a_row_claims_nothing_about_what_a_run_has_done(self) -> None:
        """An inventory of runs invites columns nothing can fill.

        A zero is a measurement, so a progress or an evidence column would be
        a claim rather than an empty space.
        """
        served, _ = client()
        served.post(RUNS_PATH, json=setup_request())

        row = served.get(RUNS_PATH).json()["runs"][0]

        for absent in (
            "progress",
            "elapsed",
            "state",
            "health",
            "source_health",
            "evidence",
            "observations",
            "committed",
            "findings",
        ):
            assert absent not in row, absent

    def test_the_order_is_newest_first_and_total(self) -> None:
        """Two runs made in the same second do not swap between reads."""
        store = FakeRuns()
        served, _ = client(runs=store)
        for _ in range(3):
            served.post(RUNS_PATH, json=setup_request())

        first = [row["run_id"] for row in served.get(RUNS_PATH).json()["runs"]]
        second = [row["run_id"] for row in served.get(RUNS_PATH).json()["runs"]]

        assert first == second
        # The fixture clock is fixed, so identity is what breaks the tie.
        assert first == sorted(first, reverse=True)

    def test_an_unreadable_store_is_not_an_empty_inventory(self) -> None:
        """"The store could not be read" and "no runs are saved" are two
        facts, and an inventory must not state the second for the first."""
        served, _ = client(
            runs=FakeRuns(failure=RunStoreUnavailable("unreadable"))
        )

        response = served.get(RUNS_PATH)

        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "RUN_STORE_UNAVAILABLE"


class TestOneRunByIdentity:
    def test_it_returns_that_run(self) -> None:
        served, _ = client()
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        body = served.get(f"{RUNS_PATH}/{created['run_id']}").json()

        assert body["run"]["run_id"] == created["run_id"]
        assert body["run"]["deterministic_identity"] == (
            created["deterministic_identity"]
        )
        assert body["run"]["frozen_inputs"] == created["frozen_inputs"]

    def test_an_unknown_run_is_never_another_run(self) -> None:
        """A fallback would put one run's frozen identity under another
        run's name, which is the worst thing this route could do."""
        served, _ = client()
        served.post(RUNS_PATH, json=setup_request())

        response = served.get(f"{RUNS_PATH}/run-{'0' * 32}")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "RUN_NOT_FOUND"
        assert "run" not in response.json()

    def test_a_malformed_identity_is_not_found_rather_than_a_store_error(
        self,
    ) -> None:
        """No run could ever carry it, so it is answered as not found - and
        it is answered without reading the store."""
        served, _ = client(
            runs=FakeRuns(failure=RunStoreUnavailable("never reached"))
        )

        response = served.get(f"{RUNS_PATH}/not-a-run-identity")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "RUN_NOT_FOUND"

    def test_no_private_scenario_expectation_reaches_a_run(self) -> None:
        """A run freezes identities and versions, not scenario content.

        There is no field a private expectation could arrive in, which is
        what makes this true rather than a filter somebody remembered.
        """
        served, _ = client()
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        body = served.get(f"{RUNS_PATH}/{created['run_id']}")

        assert "private_expectations" not in body.text
        assert "oracle" not in body.text.lower()


class TestWhatReadyDoesNotAssert:
    """The disclosure travels with the status, not with a screen."""

    def test_a_ready_run_carries_it_in_the_payload(self) -> None:
        served, _ = client()
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        assert created["execution_status"] == "READY"
        disclosure = created["readiness_disclosure"]
        assert disclosure
        assert "does not mean the model can" in disclosure
        assert "no causal runtime exists" in disclosure

    def test_it_survives_the_store_rather_than_being_added_by_one_route(
        self,
    ) -> None:
        """Read back, a run that was never written with a disclosure has
        one: it is a property of the status, computed on the way out, so
        every Draft written before this slice gets it too."""
        served, _ = client()
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        read_back = served.get(f"{RUNS_PATH}/{created['run_id']}").json()["run"]
        row_count = len(served.get(RUNS_PATH).json()["runs"])

        assert read_back["readiness_disclosure"] == (
            created["readiness_disclosure"]
        )
        assert row_count == 1

    def test_it_names_the_condition_rather_than_a_slice(self) -> None:
        """`D-2026-09-22-expiry-follows-the-condition`: the slice that closes
        the condition has to be able to recognise what to retire, and a slice
        number in the text is a guess about when."""
        served, _ = client()
        disclosure = served.post(RUNS_PATH, json=setup_request()).json()[
            "run"
        ]["readiness_disclosure"]

        assert "conformance test" in disclosure
        assert "kernel" in disclosure
        for slice_number in ("T021", "T022", "T020"):
            assert slice_number not in disclosure

    def test_a_blocked_run_makes_no_equivalent_claim(self) -> None:
        """`BLOCKED` says a run may not execute, which needs no disclaimer
        about execution."""
        served, _ = client(
            publication=publication_profile(cadence_minutes=None)
        )
        created = served.post(RUNS_PATH, json=setup_request()).json()["run"]

        assert created["execution_status"] == "BLOCKED"
        assert created["readiness_disclosure"] is None


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
    that is `BLOCKED`, with the reasons named.

    T020A adds a second group of reasons to it, and they are the template-copy
    consequence made visible. `MG-001` was created from template version 1 and
    a template does not migrate a Site that already exists, so its components
    carry ratings and no typed properties. The shipped scenario now declares
    two Foundation-owned values, the profile binds each to a named property,
    and this Foundation declares neither - so the Draft blocks with the
    property named, and is persisted and inspectable rather than refused
    (`D-2026-09-22-foundation-property-absent-blocks`).
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

        # Two groups of reasons, and they are two different facts about the
        # selected profile. Three states it does not model, and two initial
        # values it could not locate in this Site's Foundation.
        by_kind: dict[str, set[str]] = {}
        for reason in record.blocking_reasons:
            by_kind.setdefault(reason.kind, set()).add(reason.subject)

        # Every subject is an ADDRESS, and the earlier draft of this test
        # said otherwise. It claimed that an unmodelled state is one fact
        # however many assets carry it, so its subject could stay the
        # semantic key - which an independent review disproved: keyed on the
        # key, two required declarations about two different tanks
        # deduplicate into one row, and the second declaration is gone. The
        # profile is still ASKED about the semantic key; what it reports is
        # addressed.
        assert by_kind == {
            "STATE_NOT_SUPPORTED": {
                "site:site-load-demand",
                "site:plane-of-array-irradiance",
                "fuel-level-reporting-availability@fuel-tank",
            },
            "INITIAL_VALUE_NOT_RESOLVED": {
                "fuel-tank-capacity@fuel-tank",
                "generator-specific-fuel-consumption@generator",
            },
        }

        # The unresolved reasons name the property that is missing AND the
        # component it is missing from, which is what makes a blocked Draft
        # more useful than a refusal: there is something to read that says
        # what to declare and where.
        #
        # Asserted as phrases rather than as the two identifiers, and the
        # difference is not cosmetic. `fuel-tank-capacity` contains both
        # `fuel-tank` and `tank-capacity` as substrings, so checking for those
        # names passed against an explanation that carried only the state key:
        # an independent review replaced every unresolved explanation with
        # `No answer for <state_key>.` and this test still went green. It
        # proved the reason set and the absence, not that a reader is told
        # what to do.
        unresolved = {
            reason.subject: reason.statement
            for reason in record.blocking_reasons
            if reason.kind == "INITIAL_VALUE_NOT_RESOLVED"
        }
        assert (
            "tank-capacity property of component fuel-tank,"
            in unresolved["fuel-tank-capacity@fuel-tank"]
        )
        assert (
            "specific-fuel-consumption property of component generator,"
            in unresolved["generator-specific-fuel-consumption@generator"]
        )
        for statement in unresolved.values():
            # What is wrong, and the two repairs that would fix it.
            assert "declares no such property on it" in statement
            assert "another component" in statement

        # And it froze everything anyway, which is what makes it inspectable.
        assert record.deterministic_identity.site.site_id == "MG-001"
        frozen = {
            item.addressed_key: item
            for item in record.deterministic_identity.initialization_inputs
        }
        assert set(frozen) == {
            "fuel-tank-capacity@fuel-tank",
            "fuel-tank-volume@fuel-tank",
            "generator-specific-fuel-consumption@generator",
        }

        # Every absent value has a blocking reason naming the same state, and
        # the value and its canonical form are absent together. Both are
        # invariants `SimulationRun` enforces; asserted here because this is
        # the first shipped document that exercises them.
        for address in (
            "fuel-tank-capacity@fuel-tank",
            "generator-specific-fuel-consumption@generator",
        ):
            assert frozen[address].value is None, address
            assert frozen[address].canonical_value is None, address
        assert frozen["fuel-tank-volume@fuel-tank"].value == 430.0
        assert frozen["fuel-tank-volume@fuel-tank"].canonical_value == 430.0

        # MG-001 itself is untouched by the template that moved to version 2.
        assert mg_001.template is not None
        assert mg_001.template.template_version == 1
        assert mg_001.foundation.version == 1
        assert all(
            component.properties is None
            for component in mg_001.foundation.components
        )

    def test_a_site_created_from_the_updated_template_resolves_both_values(
        self,
    ) -> None:
        """The same scenario, the same profile, a Site with the properties.

        This is the slice end to end. A Site instantiated from the shipped
        template through the product's own create path declares the two typed
        properties; the profile's bindings name them; and the Draft freezes
        500 L and 0.311 L/kWh with the Foundation named as the answerer.

        It also fixes the number this suite would otherwise have lost.
        Nothing asserted that the shipped tank holds 500 L once
        `tank-capacity` stopped stating it in the scenario document
        (`D-2026-09-22-capacity-bound-source`), and this is where the 500
        lives now: in a frozen run, resolved from a site.
        """
        store = FakeRuns()
        record = self._draft_from_the_updated_template(store)

        frozen = {
            item.state_key: item
            for item in record.deterministic_identity.initialization_inputs
        }

        assert frozen["fuel-tank-capacity"].value == 500.0
        assert frozen["fuel-tank-capacity"].unit == "L"
        assert frozen["fuel-tank-capacity"].answered_by == "SITE_FOUNDATION"
        # The whole phrase, for the reason the blocking statements above use
        # one: a state key that shares words with the component and the
        # property it names cannot be what satisfies an assertion about them.
        assert (
            "component fuel-tank property tank-capacity"
            in frozen["fuel-tank-capacity"].answered_by_detail
        )

        coefficient = frozen["generator-specific-fuel-consumption"]
        assert coefficient.value == 0.311
        assert coefficient.unit == "L/kWh"
        assert coefficient.answered_by == "SITE_FOUNDATION"
        assert (
            "component generator property specific-fuel-consumption"
            in coefficient.answered_by_detail
        )

        # No reason is left about either of them: the absent-value case above
        # and this one are the same code path with a different Foundation.
        assert not [
            reason
            for reason in record.blocking_reasons
            if reason.kind == "INITIAL_VALUE_NOT_RESOLVED"
        ]
        assert store.written == [record]

    def _draft_from_the_updated_template(self, store):
        """One Draft, for a Site instantiated from the shipped template v2."""
        from pathlib import Path

        import yaml

        from assetops_backend.runs.profiles import (
            LAB_PUBLICATION_PROFILE,
            MINIMAL_FUEL_TANK_MODEL,
        )
        from assetops_backend.runs.service import RunSetupService
        from assetops_backend.sites.parsing import parse_site_template
        from assetops_backend.sites.service import SiteCreationService
        from assetops_backend.sites.site_parsing import CreateSiteRequest

        repo_root = Path(__file__).resolve().parents[2]
        shipped_scenario = parse_scenario_document(
            yaml.safe_load(
                (
                    repo_root / "config" / "scenarios" / "fuel-loss-event.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped definition",
            origin="SHIPPED",
        )
        template = parse_site_template(
            yaml.safe_load(
                (
                    repo_root
                    / "config"
                    / "site-templates"
                    / "hybrid-mini-grid-100kw.yaml"
                ).read_text(encoding="utf-8")
            ),
            source="the shipped template",
        )

        created: list[SiteRecord] = []

        class Recording:
            def create_site(self, record: SiteRecord) -> SiteRecord:
                created.append(record)
                return record

        class Catalog:
            def list_templates(self) -> tuple:
                return (template,)

            def get_template(self, template_id: str):
                return template

        # The scenario declares that it targets MG-001, and a run is not the
        # place to retarget a scenario - so the new fixture carries that
        # identity here. It is an in-memory Site built from the updated
        # template, not the MG-001 in `var/`, which the test above reads
        # unchanged.
        SiteCreationService(Recording(), Catalog()).create_site_from_template(
            CreateSiteRequest(
                template_id="hybrid-mini-grid-100kw",
                site_id="MG-001",
                display_name="Kalangala mini-grid",
                country="Uganda",
                locality="Kalangala",
                timezone="Africa/Kampala",
            )
        )
        instantiated = created[0]

        return RunSetupService(
            store,
            FakeSites((instantiated,)),
            FakeScenarios((shipped_scenario,)),
            model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
            publication_profiles=(LAB_PUBLICATION_PROFILE,),
            now=lambda: "2026-09-21T09:00:00Z",
        ).create_draft_run(
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

    def test_only_the_changed_property_changes_its_own_frozen_answer(
        self,
    ) -> None:
        """The whole frozen set, not one scalar.

        The packet backed this criterion with a test comparing a single
        capacity value and a structural argument about dispatch. An
        independent review pointed out that a metamorphic comparison of the
        whole set is what the criterion asks for, and ran one; this keeps
        that coverage in the suite rather than in a review that has finished.

        Two changes, one at a time, against the shipped scenario and a Site
        built from the shipped template. Changing the generator's coefficient
        must move exactly one frozen row. Changing what the scenario
        dispatches must move none of them, because an output the story forces
        is not something a machine's physical property follows.
        """
        baseline = self._frozen_answers()

        by_coefficient = self._frozen_answers(coefficient=0.42)
        moved = {
            key
            for key in baseline
            if baseline[key] != by_coefficient.get(key)
        }
        assert moved == {"generator-specific-fuel-consumption"}
        assert (
            by_coefficient["generator-specific-fuel-consumption"].value == 0.42
        )

        # And nothing drifted between two runs of the unchanged pair, so the
        # comparison above is about the edit and not about run-to-run noise.
        assert self._frozen_answers() == baseline

        by_dispatch = self._frozen_answers(dispatched_output=30)
        assert by_dispatch == baseline

    def _frozen_answers(
        self,
        *,
        coefficient: float | None = None,
        dispatched_output: float | None = None,
    ) -> dict:
        """The frozen initial values, for one edit to the site or the story.

        Both documents are copied in memory. The local `var/` fixtures are
        read and never written.
        """
        import copy
        from pathlib import Path

        import yaml

        from assetops_backend.runs.profiles import (
            LAB_PUBLICATION_PROFILE,
            MINIMAL_FUEL_TANK_MODEL,
        )
        from assetops_backend.runs.service import RunSetupService
        from assetops_backend.sites.parsing import parse_site_template
        from assetops_backend.sites.service import SiteCreationService
        from assetops_backend.sites.site_parsing import CreateSiteRequest

        repo_root = Path(__file__).resolve().parents[2]
        template_document = yaml.safe_load(
            (
                repo_root
                / "config"
                / "site-templates"
                / "hybrid-mini-grid-100kw.yaml"
            ).read_text(encoding="utf-8")
        )
        scenario_document = yaml.safe_load(
            (
                repo_root / "config" / "scenarios" / "fuel-loss-event.yaml"
            ).read_text(encoding="utf-8")
        )

        if coefficient is not None:
            template_document = copy.deepcopy(template_document)
            for component in template_document["foundation"]["components"]:
                for item in component.get("properties") or ():
                    if item["property_key"] == "specific-fuel-consumption":
                        item["value"] = coefficient

        if dispatched_output is not None:
            scenario_document = copy.deepcopy(scenario_document)
            for entry in scenario_document["timeline"]:
                for parameter in entry.get("parameters") or ():
                    if parameter["parameter_id"] == "dispatched-output":
                        parameter["value"] = dispatched_output

        template = parse_site_template(
            template_document, source="the shipped template"
        )
        created: list[SiteRecord] = []

        class Recording:
            def create_site(self, record: SiteRecord) -> SiteRecord:
                created.append(record)
                return record

        class Catalog:
            def list_templates(self) -> tuple:
                return (template,)

            def get_template(self, template_id: str):
                return template

        SiteCreationService(Recording(), Catalog()).create_site_from_template(
            CreateSiteRequest(
                template_id="hybrid-mini-grid-100kw",
                site_id="MG-001",
                display_name="Kalangala mini-grid",
                country="Uganda",
                locality="Kalangala",
                timezone="Africa/Kampala",
            )
        )

        record = RunSetupService(
            FakeRuns(),
            FakeSites((created[0],)),
            FakeScenarios(
                (
                    parse_scenario_document(
                        scenario_document,
                        source="the shipped definition",
                        origin="SHIPPED",
                    ),
                )
            ),
            model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
            publication_profiles=(LAB_PUBLICATION_PROFILE,),
            now=lambda: "2026-09-21T09:00:00Z",
        ).create_draft_run(
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

        return {
            item.state_key: item
            for item in record.deterministic_identity.initialization_inputs
        }

    def test_the_frozen_answers_survive_a_round_trip(self, tmp_path) -> None:
        """A reload agrees with what was frozen, values, units and absence.

        The store is the real YAML adapter rather than a fake, because the
        claim is that the answers persist rather than that a record holds
        them in memory.
        """
        from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore

        store = YamlRunStore(tmp_path)
        record = self._draft_from_the_updated_template(store)

        reloaded = store.get_run(record.run_id)

        assert (
            reloaded.deterministic_identity.initialization_inputs
            == record.deterministic_identity.initialization_inputs
        )
        frozen = {
            item.state_key: item
            for item in reloaded.deterministic_identity.initialization_inputs
        }
        assert frozen["fuel-tank-capacity"].value == 500.0
        assert frozen["generator-specific-fuel-consumption"].value == 0.311
        assert (
            frozen["generator-specific-fuel-consumption"].answered_by
            == "SITE_FOUNDATION"
        )
        assert (
            reloaded.deterministic_identity.profiles.execution_contract_version
            == record.deterministic_identity.profiles.execution_contract_version
        )
