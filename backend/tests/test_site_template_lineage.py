"""T025f: a Site's template lineage against the current shipped template.

Computed on read, never stored, and gated with the template catalog. Every
fixture here is in-process: no test reads or writes a Site store on disk.
"""

from __future__ import annotations

import dataclasses
from typing import Sequence

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.sites.lineage import assess_template_lineage
from assetops_backend.sites.models import SiteRecord, SiteTemplate, SiteTemplateProvenance
from assetops_backend.sites.ports import SiteStoreUnavailable, SiteTemplateStoreUnavailable
from test_site_parsing import valid_site_document
from test_site_repository import FakeSiteRepository, FakeTemplateCatalog, site
from test_site_template_parsing import parse as parse_template
from test_site_template_parsing import valid_document as valid_template_document

LINEAGE_PATH = "/api/simulator-lab/site-template-lineage"
ENABLED = FeatureFlags(simulator_lab_enabled=True)
DISABLED = FeatureFlags(simulator_lab_enabled=False)


def template(template_id: str = "kobo-mini-grid-60kw", version: int = 2) -> SiteTemplate:
    return dataclasses.replace(
        parse_template(valid_template_document()),
        template_id=template_id,
        template_version=version,
    )


def provenance(template_id: str, version: int) -> SiteTemplateProvenance:
    return SiteTemplateProvenance(template_id=template_id, template_version=version)


def site_from(site_id: str, template_id: str | None, version: int = 1) -> SiteRecord:
    document = valid_site_document()
    document["site_id"] = site_id
    document["template"] = (
        None
        if template_id is None
        else {"template_id": template_id, "template_version": version}
    )
    return site(**document)


class TestAssessment:
    SHIPPED = (template("kobo-mini-grid-60kw", 2), template("other", 1))

    def test_a_site_recorded_at_an_earlier_version_is_behind(self) -> None:
        lineage = assess_template_lineage(
            provenance("kobo-mini-grid-60kw", 1), self.SHIPPED
        )
        assert (lineage.state, lineage.current_template_version) == ("BEHIND", 2)

    def test_a_site_recorded_at_the_shipped_version_is_current(self) -> None:
        lineage = assess_template_lineage(
            provenance("kobo-mini-grid-60kw", 2), self.SHIPPED
        )
        assert (lineage.state, lineage.current_template_version) == ("CURRENT", 2)

    def test_a_site_from_no_template_says_so(self) -> None:
        lineage = assess_template_lineage(None, self.SHIPPED)
        assert (lineage.state, lineage.current_template_version) == (
            "NO_TEMPLATE",
            None,
        )

    def test_a_template_no_longer_shipped_is_not_current(self) -> None:
        lineage = assess_template_lineage(provenance("retired", 1), self.SHIPPED)
        assert (lineage.state, lineage.current_template_version) == (
            "NOT_SHIPPED",
            None,
        )

    def test_a_version_above_the_shipped_one_is_not_current(self) -> None:
        lineage = assess_template_lineage(
            provenance("kobo-mini-grid-60kw", 3), self.SHIPPED
        )
        assert (lineage.state, lineage.current_template_version) == (
            "UNRECOGNISED_VERSION",
            2,
        )


class ReadOnlyRepository(FakeSiteRepository):
    def create_site(self, record: SiteRecord) -> SiteRecord:
        raise AssertionError("a lineage read wrote a Site")


class UnavailableSites:
    def list_sites(self) -> Sequence[SiteRecord]:
        raise SiteStoreUnavailable("store is unreachable")

    def get_site(self, site_id: str) -> SiteRecord:
        raise SiteStoreUnavailable("store is unreachable")

    def create_site(self, record: SiteRecord) -> SiteRecord:
        raise AssertionError("a lineage read wrote a Site")


class UnavailableCatalog:
    def list_templates(self) -> Sequence[SiteTemplate]:
        raise SiteTemplateStoreUnavailable("catalog is unreachable")

    def get_template(self, template_id: str) -> SiteTemplate:
        raise SiteTemplateStoreUnavailable("catalog is unreachable")


@pytest.fixture
def records() -> list[SiteRecord]:
    return [
        site_from("KOBO-OLD", "kobo-mini-grid-60kw", 1),
        site_from("KOBO-NEW", "kobo-mini-grid-60kw", 2),
        site_from("PLAIN", None),
        site_from("RETIRED", "retired-archetype", 4),
    ]


class TestTheGatedRoute:
    def test_each_site_states_its_lineage_against_the_shipped_catalog(
        self, records: list[SiteRecord]
    ) -> None:
        before = list(records)
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeTemplateCatalog([template()]),
                site_repository=ReadOnlyRepository(records),
            )
        )

        response = client.get(LINEAGE_PATH)

        assert response.status_code == 200
        by_site = {entry["site_id"]: entry for entry in response.json()["sites"]}
        assert by_site["KOBO-OLD"] == {
            "site_id": "KOBO-OLD",
            "template": {"template_id": "kobo-mini-grid-60kw", "template_version": 1},
            "state": "BEHIND",
            "current_template_version": 2,
        }
        assert by_site["KOBO-NEW"]["state"] == "CURRENT"
        assert by_site["PLAIN"] == {
            "site_id": "PLAIN",
            "template": None,
            "state": "NO_TEMPLATE",
            "current_template_version": None,
        }
        assert by_site["RETIRED"]["state"] == "NOT_SHIPPED"
        # Computed on read: the recorded lineage is exactly what was stored.
        assert records == before
        assert [r.template for r in records] == [r.template for r in before]

    def test_the_operator_site_read_carries_no_lineage_field(
        self, records: list[SiteRecord]
    ) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeTemplateCatalog([template()]),
                site_repository=ReadOnlyRepository(records),
            )
        )
        body = client.get("/api/sites/KOBO-OLD").json()
        assert body["template"] == {
            "template_id": "kobo-mini-grid-60kw",
            "template_version": 1,
        }
        assert "state" not in body
        assert "current_template_version" not in body

    def test_an_unreadable_catalog_is_unavailable_not_current(
        self, records: list[SiteRecord]
    ) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=UnavailableCatalog(),
                site_repository=ReadOnlyRepository(records),
            )
        )
        assert client.get(LINEAGE_PATH).status_code == 503

    def test_an_unreadable_site_store_is_unavailable(self) -> None:
        client = TestClient(
            create_app(
                ENABLED,
                site_template_catalog=FakeTemplateCatalog([template()]),
                site_repository=UnavailableSites(),
            )
        )
        assert client.get(LINEAGE_PATH).status_code == 503

    def test_the_route_is_not_served_when_the_gate_is_closed(
        self, records: list[SiteRecord]
    ) -> None:
        client = TestClient(
            create_app(DISABLED, site_repository=ReadOnlyRepository(records))
        )
        assert client.get(LINEAGE_PATH).status_code == 404
