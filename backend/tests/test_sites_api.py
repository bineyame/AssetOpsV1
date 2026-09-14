"""API tests for the operator Sites surface and the gated create surface.

Three things are being proved. That the Sites index API is an operator
capability and behaves identically in both gate states. That the create API is
a Simulator Lab surface and is absent when the gate is closed. And that a
refusal is product copy naming what is wrong and what would be acceptable,
rather than a generic failure or a stack trace.

Both ports are injected, so these tests exercise the API over fakes and a
temporary store rather than over the shipped configuration roots.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Sequence

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.sites.adapters.composite_site_repository import (
    CompositeSiteRepository,
)
from assetops_backend.sites.adapters.yaml_shipped_site_store import (
    ReadOnlyYamlSiteStore,
)
from assetops_backend.sites.adapters.yaml_user_site_store import WritableYamlSiteStore
from assetops_backend.sites.models import SiteRecord, SiteTemplate
from assetops_backend.sites.ports import SiteNotFound, SiteStoreUnavailable
from test_site_parsing import valid_create_request, valid_site_document
from test_site_repository import FakeSiteRepository, site, snapshot, write_document
from test_site_template_parsing import parse as parse_template
from test_site_template_parsing import valid_document as valid_template_document

DISABLED = FeatureFlags(simulator_lab_enabled=False)
ENABLED = FeatureFlags(simulator_lab_enabled=True)

SITES_PATH = "/api/sites"
CREATE_SITE_PATH = "/api/simulator-lab/sites"

TEMPLATE = parse_template(valid_template_document())


class FakeCatalog:
    def __init__(self, templates: Sequence[SiteTemplate] = (TEMPLATE,)) -> None:
        self._templates = tuple(templates)

    def list_templates(self) -> Sequence[SiteTemplate]:
        return self._templates

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        from assetops_backend.sites.ports import SiteTemplateNotFound

        raise SiteTemplateNotFound(f"No template {template_id!r}")


class UnavailableRepository:
    def list_sites(self) -> Sequence[SiteRecord]:
        raise SiteStoreUnavailable("the site store is unreachable")

    def get_site(self, site_id: str) -> SiteRecord:
        raise SiteStoreUnavailable("the site store is unreachable")

    def create_site(self, record: SiteRecord) -> SiteRecord:
        raise SiteStoreUnavailable("the site store is unreachable")


def request_body(**overrides: Any) -> dict[str, Any]:
    body = valid_create_request()
    body["template_id"] = TEMPLATE.template_id
    body.update(overrides)
    return body


@pytest.fixture
def store(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def repository(store: Path) -> CompositeSiteRepository:
    return CompositeSiteRepository(
        shipped=ReadOnlyYamlSiteStore(store / "shipped"),
        user=WritableYamlSiteStore(store / "user"),
    )


@pytest.fixture
def client(repository: CompositeSiteRepository) -> Iterator[TestClient]:
    yield TestClient(
        create_app(
            ENABLED, site_template_catalog=FakeCatalog(), site_repository=repository
        )
    )


class TestSitesIndexIsAnOperatorCapability:
    @pytest.mark.parametrize("flags", [DISABLED, ENABLED], ids=["gate-off", "gate-on"])
    def test_the_sites_api_is_served_in_both_gate_states(
        self, repository: CompositeSiteRepository, flags: FeatureFlags
    ) -> None:
        client = TestClient(
            create_app(
                flags, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )

        response = client.get(SITES_PATH)

        assert response.status_code == 200
        assert response.json() == {"sites": []}

    def test_a_site_created_with_the_gate_open_is_visible_with_it_closed(
        self, repository: CompositeSiteRepository
    ) -> None:
        """A Lab-created Site is product history, not simulator execution."""
        open_client = TestClient(
            create_app(
                ENABLED, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )
        assert open_client.post(CREATE_SITE_PATH, json=request_body()).status_code == 201

        closed_client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=repository,
            )
        )

        assert closed_client.get(SITES_PATH).json() == open_client.get(
            SITES_PATH
        ).json()
        assert [
            entry["site_id"] for entry in closed_client.get(SITES_PATH).json()["sites"]
        ] == ["MG-002"]

    def test_the_first_run_index_is_empty_rather_than_populated(
        self, client: TestClient
    ) -> None:
        assert client.get(SITES_PATH).json() == {"sites": []}

    def test_an_unreadable_store_is_stated_rather_than_shown_as_empty(self) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=UnavailableRepository(),
            )
        )

        assert client.get(SITES_PATH).status_code == 503


class TestSitesIndexShape:
    @pytest.fixture
    def populated(self, store: Path) -> TestClient:
        write_document(
            store / "user",
            site(site_id="MG-002", origin="USER", source={"mode": "SIMULATED"}),
        )
        write_document(
            store / "shipped",
            site(
                site_id="CC-001",
                origin="SHIPPED",
                source={"mode": "LIVE"},
                template=None,
            ),
        )
        return TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=CompositeSiteRepository(
                    shipped=ReadOnlyYamlSiteStore(store / "shipped"),
                    user=WritableYamlSiteStore(store / "user"),
                ),
            )
        )

    def test_each_row_carries_identity_configuration_and_provenance(
        self, populated: TestClient
    ) -> None:
        sites = {entry["site_id"]: entry for entry in populated.get(SITES_PATH).json()["sites"]}

        assert set(sites) == {"CC-001", "MG-002"}
        row = sites["MG-002"]
        assert row["display_name"] == "Kalangala Mini-Grid"
        assert row["site_type"] == "MINIGRID"
        assert row["location"] == {"country": "Uganda", "locality": "Kalangala"}
        assert row["lifecycle_status"] == "PLANNED"
        assert row["origin"] == "USER"
        assert row["source"] == {"mode": "SIMULATED"}
        assert row["template"] == {
            "template_id": "hybrid-mini-grid-100kw",
            "template_version": 1,
        }

    def test_origin_and_mode_are_independent_facts_on_the_wire(
        self, populated: TestClient
    ) -> None:
        """Neither may be derived from the other, so the shape carries both."""
        sites = {entry["site_id"]: entry for entry in populated.get(SITES_PATH).json()["sites"]}

        assert (sites["MG-002"]["origin"], sites["MG-002"]["source"]["mode"]) == (
            "USER",
            "SIMULATED",
        )
        assert (sites["CC-001"]["origin"], sites["CC-001"]["source"]["mode"]) == (
            "SHIPPED",
            "LIVE",
        )

    def test_no_lab_flag_and_no_evidence_field_appears_on_the_wire(
        self, populated: TestClient
    ) -> None:
        body = populated.get(SITES_PATH).text

        for field in (
            "created_in_lab",
            "is_simulator_site",
            "last_data",
            "last_analysed",
            "health",
            "evidence",
            "analytics",
            "replay",
            "findings",
        ):
            assert field not in body


class TestCreateSucceeds:
    def test_a_site_is_created_from_a_template(self, client: TestClient) -> None:
        response = client.post(CREATE_SITE_PATH, json=request_body())

        assert response.status_code == 201
        body = response.json()
        assert body["site_id"] == "MG-002"
        assert body["origin"] == "USER"
        assert body["source"] == {"mode": "SIMULATED"}
        assert body["lifecycle_status"] == "PLANNED"
        assert body["template"]["template_id"] == TEMPLATE.template_id

    def test_the_created_site_appears_in_the_operator_index(
        self, client: TestClient
    ) -> None:
        client.post(CREATE_SITE_PATH, json=request_body())

        sites = client.get(SITES_PATH).json()["sites"]

        assert [entry["site_id"] for entry in sites] == ["MG-002"]

    def test_the_created_site_survives_a_restart(
        self, client: TestClient, store: Path
    ) -> None:
        client.post(CREATE_SITE_PATH, json=request_body())

        restarted = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=CompositeSiteRepository(
                    shipped=ReadOnlyYamlSiteStore(store / "shipped"),
                    user=WritableYamlSiteStore(store / "user"),
                ),
            )
        )

        assert [
            entry["site_id"] for entry in restarted.get(SITES_PATH).json()["sites"]
        ] == ["MG-002"]


class TestCreateRefusals:
    def test_a_duplicate_site_id_is_refused_and_nothing_is_written(
        self, client: TestClient, store: Path
    ) -> None:
        client.post(CREATE_SITE_PATH, json=request_body())
        before = snapshot(store / "user")

        response = client.post(
            CREATE_SITE_PATH, json=request_body(display_name="Replacement")
        )

        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "SITE_ID_IN_USE"
        assert snapshot(store / "user") == before

    def test_a_case_variant_duplicate_is_refused(
        self, client: TestClient, store: Path
    ) -> None:
        client.post(CREATE_SITE_PATH, json=request_body(site_id="MG-002"))
        before = snapshot(store / "user")

        response = client.post(CREATE_SITE_PATH, json=request_body(site_id="mg-002"))

        assert response.status_code == 409
        message = response.json()["detail"]["message"]
        assert "mg-002" in message and "MG-002" in message
        assert "without regard to case" in message
        assert snapshot(store / "user") == before

    def test_a_malformed_site_id_is_refused(
        self, client: TestClient, store: Path
    ) -> None:
        response = client.post(CREATE_SITE_PATH, json=request_body(site_id="../MG-002"))

        assert response.status_code == 422
        assert response.json()["detail"]["code"] == "SITE_REQUEST_INVALID"
        assert "letters, digits" in response.json()["detail"]["message"]
        assert snapshot(store / "user") == {}

    def test_a_missing_required_identity_field_is_refused(
        self, client: TestClient, store: Path
    ) -> None:
        body = request_body()
        del body["display_name"]

        response = client.post(CREATE_SITE_PATH, json=body)

        assert response.status_code == 422
        assert "Display name is required" in response.json()["detail"]["message"]
        assert snapshot(store / "user") == {}

    def test_an_unknown_template_is_refused(
        self, client: TestClient, store: Path
    ) -> None:
        response = client.post(
            CREATE_SITE_PATH, json=request_body(template_id="absent-archetype")
        )

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "TEMPLATE_NOT_FOUND"
        assert snapshot(store / "user") == {}

    def test_the_four_refusals_read_differently_and_carry_no_stack_trace(
        self, client: TestClient
    ) -> None:
        client.post(CREATE_SITE_PATH, json=request_body())

        messages = [
            client.post(CREATE_SITE_PATH, json=request_body()).json()["detail"][
                "message"
            ],
            client.post(CREATE_SITE_PATH, json=request_body(site_id="mg-002")).json()[
                "detail"
            ]["message"],
            client.post(CREATE_SITE_PATH, json=request_body(site_id="MG 003")).json()[
                "detail"
            ]["message"],
            client.post(
                CREATE_SITE_PATH,
                json={
                    key: value
                    for key, value in request_body(site_id="MG-003").items()
                    if key != "timezone"
                },
            ).json()["detail"]["message"],
        ]

        assert len(set(messages)) == 4
        for message in messages:
            assert "Traceback" not in message
            assert "assetops_backend" not in message

    def test_an_unknown_request_field_is_refused(self, client: TestClient) -> None:
        """A request cannot choose its own origin, mode, or lifecycle."""
        response = client.post(CREATE_SITE_PATH, json=request_body(origin="SHIPPED"))

        assert response.status_code == 422
        assert "Unknown" in response.json()["detail"]["message"]

    def test_an_unwritable_store_is_stated_rather_than_faked(self) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=UnavailableRepository(),
            )
        )

        response = client.post(CREATE_SITE_PATH, json=request_body())

        assert response.status_code == 503
        assert "Nothing was written" in response.json()["detail"]["message"]


class TestCreateIsGated:
    @pytest.mark.parametrize("path", [CREATE_SITE_PATH, f"{CREATE_SITE_PATH}/"])
    def test_the_create_route_is_not_served_when_the_gate_is_closed(
        self, repository: CompositeSiteRepository, path: str
    ) -> None:
        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=repository,
            )
        )

        assert client.post(path, json=request_body()).status_code == 404

    def test_a_closed_gate_writes_nothing_when_a_create_is_attempted(
        self, repository: CompositeSiteRepository, store: Path
    ) -> None:
        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=repository,
            )
        )

        client.post(CREATE_SITE_PATH, json=request_body())

        assert snapshot(store / "user") == {}
        assert client.get(SITES_PATH).json() == {"sites": []}

    def test_no_create_route_hangs_off_the_operator_sites_path(
        self, client: TestClient
    ) -> None:
        """Creation is a Lab surface, so the operator API cannot reach it."""
        for path in (SITES_PATH, f"{SITES_PATH}/create", f"{SITES_PATH}/MG-002"):
            assert client.post(path, json=request_body()).status_code in (404, 405)


class TestNoUpdateOrDeleteRouteExists:
    @pytest.mark.parametrize("flags", [DISABLED, ENABLED], ids=["gate-off", "gate-on"])
    def test_no_write_verb_is_accepted_on_a_site_path(
        self, repository: CompositeSiteRepository, flags: FeatureFlags
    ) -> None:
        client = TestClient(
            create_app(
                flags, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )

        for path in (SITES_PATH, f"{SITES_PATH}/MG-002", f"{CREATE_SITE_PATH}/MG-002"):
            for request in (client.put, client.patch, client.delete):
                assert request(path).status_code in (404, 405), f"{path} accepted a verb"

    @pytest.mark.parametrize("flags", [DISABLED, ENABLED], ids=["gate-off", "gate-on"])
    def test_the_openapi_description_declares_no_put_patch_or_delete_on_a_site(
        self, repository: CompositeSiteRepository, flags: FeatureFlags
    ) -> None:
        client = TestClient(
            create_app(
                flags, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )
        schema = client.get("/openapi.json").json()

        site_paths = {
            path: set(operations)
            for path, operations in schema["paths"].items()
            if "site" in path
        }

        assert site_paths, "the route inventory must not be vacuous"
        for path, operations in site_paths.items():
            assert operations <= {"get", "post"}, f"{path} declares {operations}"
            assert "put" not in operations
            assert "patch" not in operations
            assert "delete" not in operations

    @pytest.mark.parametrize("flags", [DISABLED, ENABLED], ids=["gate-off", "gate-on"])
    def test_the_only_per_site_route_reads_one_site(
        self, repository: CompositeSiteRepository, flags: FeatureFlags
    ) -> None:
        """T007 adds exactly one per-Site path, and only `GET` on it.

        This replaces T006's "no per-Site route is registered yet". It is not
        a relaxation: the route inventory is still pinned to an exact list,
        the list is one path rather than none, and the verb set on it is
        pinned to `get`.
        """
        client = TestClient(
            create_app(
                flags, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )
        schema = client.get("/openapi.json").json()

        assert [path for path in schema["paths"] if "{site_id}" in path] == [
            f"{SITES_PATH}/{{site_id}}"
        ]
        assert set(schema["paths"][f"{SITES_PATH}/{{site_id}}"]) == {"get"}


class TestSiteDetail:
    """`GET /api/sites/{site_id}`: one Site, addressed by its only identity."""

    @pytest.fixture
    def created(self, client: TestClient) -> TestClient:
        assert client.post(CREATE_SITE_PATH, json=request_body()).status_code == 201
        return client

    def test_a_created_site_resolves_by_its_site_id(
        self, created: TestClient
    ) -> None:
        response = created.get(f"{SITES_PATH}/MG-002")

        assert response.status_code == 200
        body = response.json()
        assert body["site_id"] == "MG-002"
        assert body["display_name"] == "Kalangala Mini-Grid"
        assert body["site_type"] == "MINIGRID"
        assert body["location"] == {"country": "Uganda", "locality": "Kalangala"}
        assert body["timezone"] == "Africa/Kampala"
        assert body["lifecycle_status"] == "PLANNED"
        assert body["origin"] == "USER"
        assert body["source"] == {"mode": "SIMULATED"}
        assert body["template"] == {
            "template_id": TEMPLATE.template_id,
            "template_version": TEMPLATE.template_version,
        }
        assert body["foundation"]["version"] == 1
        assert isinstance(body["foundation"]["valid_from"], str)

    def test_an_unknown_site_id_is_not_found(self, created: TestClient) -> None:
        response = created.get(f"{SITES_PATH}/MG-404")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SITE_NOT_FOUND"
        assert "MG-404" in response.json()["detail"]["message"]

    def test_a_not_found_carries_no_site_shaped_body(
        self, created: TestClient
    ) -> None:
        """Not found is a refusal, never an empty Site."""
        body = created.get(f"{SITES_PATH}/MG-404").json()

        assert "site_id" not in body
        assert "lifecycle_status" not in body
        assert "foundation" not in body

    @pytest.mark.parametrize("requested", ["mg-002", "Mg-002", "MG-002"])
    def test_a_case_variant_resolves_to_the_stored_canonical_identity(
        self, created: TestClient, requested: str
    ) -> None:
        """One Site can never present as two.

        Uniqueness is compared without regard to case at the port, so lookup
        is too: a Site that exists for the purposes of a conflict must not be
        absent for the purposes of a lookup. The response carries the stored
        spelling, not the requested one.
        """
        response = created.get(f"{SITES_PATH}/{requested}")

        assert response.status_code == 200
        assert response.json()["site_id"] == "MG-002"

    def test_a_malformed_site_id_is_not_found_and_says_what_is_acceptable(
        self, created: TestClient
    ) -> None:
        response = created.get(f"{SITES_PATH}/MG 002")

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "SITE_NOT_FOUND"
        assert "letters, digits" in response.json()["detail"]["message"]

    def test_an_unreadable_store_is_stated_rather_than_reported_as_absent(
        self,
    ) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=UnavailableRepository(),
            )
        )

        response = client.get(f"{SITES_PATH}/MG-002")

        assert response.status_code == 503
        assert response.json()["detail"]["code"] == "SITE_STORE_UNAVAILABLE"

    def test_the_detail_shape_carries_no_evidence_derived_field(
        self, created: TestClient
    ) -> None:
        body = created.get(f"{SITES_PATH}/MG-002").text

        for field in (
            "created_in_lab",
            "is_simulator_site",
            "last_data",
            "last_analysed",
            "health",
            "evidence",
            "analytics",
            "replay",
            "findings",
            "readiness",
            "telemetry",
        ):
            assert field not in body

    def test_the_detail_shape_carries_no_foundation_content(
        self, created: TestClient
    ) -> None:
        """Foundation content is the Site Configuration surface's shape."""
        foundation = created.get(f"{SITES_PATH}/MG-002").json()["foundation"]

        assert set(foundation) == {"version", "valid_from"}

    @pytest.mark.parametrize("flags", [DISABLED, ENABLED], ids=["gate-off", "gate-on"])
    def test_the_detail_route_is_never_gated(
        self, repository: CompositeSiteRepository, flags: FeatureFlags
    ) -> None:
        open_client = TestClient(
            create_app(
                ENABLED, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )
        assert open_client.post(CREATE_SITE_PATH, json=request_body()).status_code == 201

        client = TestClient(
            create_app(
                flags, site_template_catalog=FakeCatalog(), site_repository=repository
            )
        )

        assert client.get(f"{SITES_PATH}/MG-002").json() == open_client.get(
            f"{SITES_PATH}/MG-002"
        ).json()

    def test_the_detail_api_is_satisfied_by_a_fake_repository(self) -> None:
        """Handler to service to port: no shortcut to storage."""
        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=FakeSiteRepository([site()]),
            )
        )

        assert client.get(f"{SITES_PATH}/MG-002").json()["site_id"] == "MG-002"

    def test_the_template_id_does_not_address_a_site(
        self, created: TestClient
    ) -> None:
        """Template provenance is not Site identity and never routes."""
        assert (
            created.get(f"{SITES_PATH}/{TEMPLATE.template_id}").status_code == 404
        )

    def test_the_display_name_does_not_address_a_site(
        self, created: TestClient
    ) -> None:
        assert created.get(f"{SITES_PATH}/Kalangala").status_code == 404


class TestTheApiUsesThePort:
    def test_the_sites_api_is_satisfied_by_a_fake_repository(self) -> None:
        """Handler to service to port: no shortcut to storage anywhere."""
        record = site()
        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=FakeSiteRepository([record]),
            )
        )

        assert [
            entry["site_id"] for entry in client.get(SITES_PATH).json()["sites"]
        ] == ["MG-002"]

    def test_the_create_api_is_satisfied_by_a_fake_repository(self) -> None:
        repository = FakeSiteRepository()
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeCatalog(),
                site_repository=repository,
            )
        )

        assert client.post(CREATE_SITE_PATH, json=request_body()).status_code == 201
        assert [record.site_id for record in repository.list_sites()] == ["MG-002"]

    def test_a_not_found_never_leaks_a_storage_exception(self) -> None:
        repository = FakeSiteRepository()

        with pytest.raises(SiteNotFound):
            repository.get_site("MG-404")

        assert valid_site_document()["site_id"] == "MG-002"
