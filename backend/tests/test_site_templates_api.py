"""API tests for the gated Site Templates surface.

Two things are being proved. That the served template surface is a template
surface: template identity, no Site identity, no operational values, and no
write route. And that it is genuinely gated: with the flag off the paths are
not served at all, which the gate tests assert structurally and these assert by
request.

The catalog is injected as a port, so these tests exercise the API over a fake
in-memory catalog rather than over the shipped configuration root.
"""

from __future__ import annotations

from typing import Sequence

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.sites.models import SiteTemplate
from assetops_backend.sites.ports import (
    SiteTemplateNotFound,
    SiteTemplateStoreUnavailable,
)
from test_site_template_parsing import parse, valid_document

DISABLED = FeatureFlags(simulator_lab_enabled=False)
ENABLED = FeatureFlags(simulator_lab_enabled=True)

TEMPLATES_PATH = "/api/simulator-lab/site-templates"


class FakeCatalog:
    def __init__(self, templates: Sequence[SiteTemplate]) -> None:
        self._templates = tuple(templates)

    def list_templates(self) -> Sequence[SiteTemplate]:
        return self._templates

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template
        raise SiteTemplateNotFound(f"No template {template_id!r}")


class UnavailableCatalog:
    def list_templates(self) -> Sequence[SiteTemplate]:
        raise SiteTemplateStoreUnavailable("catalog is unreachable")

    def get_template(self, template_id: str) -> SiteTemplate:
        raise SiteTemplateStoreUnavailable("catalog is unreachable")


class EmptySiteRepository:
    """No Site exists in these tests, and none may be written by them."""

    def list_sites(self) -> Sequence[object]:
        return ()

    def get_site(self, site_id: str) -> object:
        raise AssertionError("a template test resolved a Site")

    def create_site(self, record: object) -> object:
        raise AssertionError("a template test wrote a Site")


@pytest.fixture
def client() -> TestClient:
    template = parse(valid_document())
    return TestClient(
        create_app(
            ENABLED,
            site_template_catalog=FakeCatalog([template]),
            site_repository=EmptySiteRepository(),
        )
    )


class TestTemplateListing:
    def test_the_listing_names_template_identity_and_version(
        self, client: TestClient
    ) -> None:
        response = client.get(TEMPLATES_PATH)

        assert response.status_code == 200
        assert response.json() == {
            "templates": [
                {
                    "template_id": "test-archetype",
                    "template_version": 2,
                    "display_name": "Test Archetype",
                    "site_type": "MINIGRID",
                    "summary": "A template used by tests only.",
                }
            ]
        }

    def test_the_listing_exposes_no_site_or_operational_field(
        self, client: TestClient
    ) -> None:
        body = client.get(TEMPLATES_PATH).text

        for field in (
            "site_id",
            "lifecycle_status",
            "timezone",
            "location",
            "source_mode",
            "last_data",
            "health",
            "evidence",
        ):
            assert field not in body


class TestTemplateDetail:
    def test_the_detail_renders_the_foundation_the_template_would_produce(
        self, client: TestClient
    ) -> None:
        response = client.get(f"{TEMPLATES_PATH}/test-archetype")

        assert response.status_code == 200
        body = response.json()
        assert body["template_id"] == "test-archetype"
        assert body["template_version"] == 2
        assert body["components"] == [
            {
                "component_id": "pv-array",
                "component_type": "PV_ARRAY",
                "display_name": "PV array",
                "rating": {"value": 100.0, "unit": "kW"},
            },
            {
                "component_id": "site-meter",
                "component_type": "METER",
                "display_name": "Site meter",
                "rating": None,
            },
        ]

    def test_an_unknown_template_id_is_not_found(self, client: TestClient) -> None:
        response = client.get(f"{TEMPLATES_PATH}/absent-archetype")

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "template_id", ["..", "%2e%2e", "MG-001", "Test-Archetype"]
    )
    def test_a_traversal_or_site_shaped_id_is_not_found(
        self, client: TestClient, template_id: str
    ) -> None:
        assert client.get(f"{TEMPLATES_PATH}/{template_id}").status_code == 404


class TestStoreFailuresAreStatedNotFaked:
    def test_an_unreachable_catalog_is_reported_as_unavailable(self) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=UnavailableCatalog(),
                site_repository=EmptySiteRepository(),
            )
        )

        assert client.get(TEMPLATES_PATH).status_code == 503
        assert client.get(f"{TEMPLATES_PATH}/test-archetype").status_code == 503


class TestNoWriteRouteExists:
    @pytest.mark.parametrize("path", [TEMPLATES_PATH, f"{TEMPLATES_PATH}/test-archetype"])
    def test_no_write_verb_is_accepted_on_a_template_path(
        self, client: TestClient, path: str
    ) -> None:
        for request in (client.post, client.put, client.patch, client.delete):
            assert request(path).status_code == 405, f"{path} accepted a write verb"

    def test_no_create_instantiate_or_import_route_hangs_off_a_template_path(
        self, client: TestClient
    ) -> None:
        """Nothing is created by addressing a template.

        T006 adds a create route, so this no longer asserts that no create
        route exists anywhere. It asserts the thing that stayed true: a
        template is never the subject of a write. Creation is addressed as a
        Site under the Lab prefix, is covered by `test_sites_api.py`, and
        never writes to the template catalog.
        """
        for path in (
            f"{TEMPLATES_PATH}/test-archetype/instantiate",
            f"{TEMPLATES_PATH}/test-archetype/create-site",
            f"{TEMPLATES_PATH}/import",
            f"{TEMPLATES_PATH}/test-archetype/sites",
        ):
            # 404 where no route matches, 405 where the path spells a
            # template_id that no template has. Either way nothing is created.
            assert client.post(path).status_code in (404, 405), f"{path} exists"
            assert client.get(path).status_code == 404, f"{path} exists"

    def test_the_operator_sites_api_accepts_no_write_verb(
        self, client: TestClient
    ) -> None:
        """The Sites index is a read surface; creation is gated and elsewhere."""
        for request in (client.post, client.put, client.patch, client.delete):
            assert request("/api/sites").status_code in (404, 405)

    def test_the_openapi_description_advertises_read_operations_only(
        self, client: TestClient
    ) -> None:
        schema = client.get("/openapi.json").json()
        template_paths = {
            path: set(operations)
            for path, operations in schema["paths"].items()
            if "site-template" in path
        }

        assert template_paths
        for operations in template_paths.values():
            assert operations == {"get"}


class TestTemplateSurfaceIsGated:
    @pytest.mark.parametrize(
        "path",
        [TEMPLATES_PATH, f"{TEMPLATES_PATH}/test-archetype", f"{TEMPLATES_PATH}/"],
    )
    def test_the_template_paths_are_not_served_when_the_gate_is_closed(
        self, path: str
    ) -> None:
        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=FakeCatalog([]),
                site_repository=EmptySiteRepository(),
            )
        )

        assert client.get(path).status_code == 404

    def test_a_closed_gate_never_reads_the_catalog(self) -> None:
        """The gate removes the surface; it must not need the store to do so."""

        class ExplodingCatalog:
            def list_templates(self) -> Sequence[SiteTemplate]:
                raise AssertionError("the catalog was read behind a closed gate")

            def get_template(self, template_id: str) -> SiteTemplate:
                raise AssertionError("the catalog was read behind a closed gate")

        client = TestClient(
            create_app(
                DISABLED,
                site_template_catalog=ExplodingCatalog(),
                site_repository=EmptySiteRepository(),
            )
        )

        assert client.get(TEMPLATES_PATH).status_code == 404
        assert client.get("/api/health").status_code == 200
