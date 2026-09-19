"""The Site Foundation fetch seam, generated from real responses.

This module is one half of a contract. It drives the real application through
`create_app`, captures exactly what each endpoint returns, and compares the
result to a checked-in fixture that the frontend's own tests read back. Neither
side imports the other; the fixture is the only crossing.

Why it exists. Backend API tests prove what the backend sends. Frontend UI
tests, which inject fakes, prove what a screen does with a body someone wrote
by hand. Between T006 and T009 nothing proved those two agreed, and a drift
there is invisible until a screen shows an empty list for an unreadable store,
or a generic failure instead of the backend's own refusal copy.

The anti-rot rule is the load-bearing part. A fixture nobody regenerates looks
like coverage while proving nothing, so a normal test run FAILS when the
captured responses differ from the checked-in file. Updating the file without
this generator agreeing is not a passing state. Regenerate deliberately:

    ASSETOPS_UPDATE_CONTRACT_FIXTURE=1 python -m pytest \\
        backend/tests/test_fetch_seam_contract.py

and read the diff before committing it: a change here is a change to what every
Site screen can render.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Sequence

import pytest
from fastapi.testclient import TestClient

from assetops_backend.config import FeatureFlags
from assetops_backend.main import create_app
from assetops_backend.sites.models import SiteRecord, SiteTemplate
from assetops_backend.sites.ports import (
    SiteStoreUnavailable,
    SiteTemplateStoreUnavailable,
)
from assetops_backend.sites.site_parsing import parse_site_document
from test_site_parsing import (
    valid_create_request,
    valid_site_document,
    without_foundation_content,
)
from test_site_repository import FakeSiteRepository, site
from test_site_template_parsing import parse as parse_template
from test_site_template_parsing import valid_document as valid_template_document

DISABLED = FeatureFlags(simulator_lab_enabled=False)
ENABLED = FeatureFlags(simulator_lab_enabled=True)

SITES_PATH = "/api/sites"
SITE_DETAIL_PATH = "/api/sites/MG-002"
LAB_STATUS_PATH = "/api/simulator-lab/status"
TEMPLATES_PATH = "/api/simulator-lab/site-templates"
CREATE_SITE_PATH = "/api/simulator-lab/sites"

TEMPLATE = parse_template(valid_template_document())

# Derived, never spelled twice. An earlier draft hard-coded a template ID the
# fake catalog does not hold, and every create and template-detail case came
# back 404 - a fixture that would have taught the frontend tests the wrong
# contract while looking populated.
TEMPLATE_DETAIL_PATH = f"{TEMPLATES_PATH}/{TEMPLATE.template_id}"


def _create_request(**overrides: Any) -> dict[str, Any]:
    """A create body aimed at the template the catalog actually holds."""
    request = valid_create_request()
    request["template_id"] = TEMPLATE.template_id
    request.update(overrides)
    return request


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPOSITORY_ROOT / "contract-fixtures" / "site-foundation-fetch-seam.json"

REGENERATE_ENV = "ASSETOPS_UPDATE_CONTRACT_FIXTURE"
REGENERATE_COMMAND = (
    f"{REGENERATE_ENV}=1 python -m pytest backend/tests/test_fetch_seam_contract.py"
)


class _Catalog:
    """A shipped catalog holding whatever the case needs, including nothing."""

    def __init__(self, templates: Sequence[SiteTemplate] = (TEMPLATE,)) -> None:
        self._templates = tuple(templates)

    def list_templates(self) -> Sequence[SiteTemplate]:
        return self._templates

    def get_template(self, template_id: str) -> SiteTemplate:
        for template in self._templates:
            if template.template_id == template_id:
                return template

        from assetops_backend.sites.ports import SiteTemplateNotFound

        raise SiteTemplateNotFound(
            f"No shipped site template with template ID {template_id!r} exists."
        )


class _UnavailableCatalog:
    def list_templates(self) -> Sequence[SiteTemplate]:
        raise SiteTemplateStoreUnavailable("the shipped template catalog is unreadable")

    def get_template(self, template_id: str) -> SiteTemplate:
        raise SiteTemplateStoreUnavailable("the shipped template catalog is unreadable")


class _UnavailableRepository:
    def list_sites(self) -> Sequence[SiteRecord]:
        raise SiteStoreUnavailable("the site store is unreachable")

    def get_site(self, site_id: str) -> SiteRecord:
        raise SiteStoreUnavailable("the site store is unreachable")

    def create_site(self, record: SiteRecord) -> SiteRecord:
        raise SiteStoreUnavailable("the site store is unreachable")


def _client(
    flags: FeatureFlags,
    *,
    catalog: Any = None,
    repository: Any = None,
) -> TestClient:
    return TestClient(
        create_app(
            flags,
            site_template_catalog=_Catalog() if catalog is None else catalog,
            site_repository=FakeSiteRepository() if repository is None else repository,
        )
    )


def _capture(
    client: TestClient,
    method: str,
    path: str,
    *,
    body: Any = None,
    description: str,
) -> dict[str, Any]:
    """One request and its real response, in the shape the fixture records."""
    response = client.request(method, path, json=body)

    try:
        parsed: Any = response.json()
    except ValueError:
        parsed = None

    request: dict[str, Any] = {"method": method, "path": path}
    if body is not None:
        request["body"] = body

    return {
        "description": description,
        "request": request,
        "response": {"status": response.status_code, "body": parsed},
    }


def _generate() -> dict[str, Any]:
    """Every case in the seam, captured from the real application."""
    cases: dict[str, Any] = {}

    with _client(ENABLED, repository=FakeSiteRepository([site()])) as loaded:
        cases["sites_list_loaded"] = _capture(
            loaded,
            "GET",
            SITES_PATH,
            description="One configured Site. The operator index is ungated.",
        )
        cases["site_detail_loaded"] = _capture(
            loaded,
            "GET",
            SITE_DETAIL_PATH,
            description=(
                "One Site with its Foundation, carrying both a component with a "
                "declared rating and one whose rating is null."
            ),
        )
        cases["site_detail_not_found"] = _capture(
            loaded,
            "GET",
            "/api/sites/MG-404",
            description=(
                "An unknown Site is not-found, never an empty Site. Distinct "
                "from an unreadable store."
            ),
        )
        cases["simulator_lab_status_enabled"] = _capture(
            loaded,
            "GET",
            LAB_STATUS_PATH,
            description=(
                "The gate sentinel. No Site Foundation client calls it; it is "
                "captured so the closed-gate 404 below means something."
            ),
        )
        cases["template_list_loaded"] = _capture(
            loaded,
            "GET",
            TEMPLATES_PATH,
            description="The shipped template catalog.",
        )
        cases["template_detail_loaded"] = _capture(
            loaded,
            "GET",
            TEMPLATE_DETAIL_PATH,
            description="The Foundation content one shipped template would produce.",
        )
        cases["template_detail_not_found"] = _capture(
            loaded,
            "GET",
            f"{TEMPLATES_PATH}/no-such-template",
            description="An unknown template identity.",
        )

    # A Foundation that declares no topology, no device, no mapping and no
    # control assumption. Captured as its own case because `null` and an empty
    # list are the distinction the expanded schema exists to keep: a screen
    # reading this body must state the absence in words, not render an empty
    # device table that would say this Site has none.
    declares_none = parse_site_document(
        without_foundation_content(valid_site_document()), source="fixture"
    )
    with _client(ENABLED, repository=FakeSiteRepository([declares_none])) as bare:
        cases["site_detail_declares_no_foundation_content"] = _capture(
            bare,
            "GET",
            SITE_DETAIL_PATH,
            description=(
                "A Site whose Foundation declares no topology, devices, "
                "mappings or control assumptions. Each is null, never an "
                "empty list."
            ),
        )

    with _client(ENABLED) as empty:
        cases["sites_list_empty"] = _capture(
            empty,
            "GET",
            SITES_PATH,
            description=(
                "First run. An empty list is a real answer and must never be "
                "read as an unreadable store."
            ),
        )
        cases["create_site_created"] = _capture(
            empty,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(),
            description=(
                "A created Site, returned as the same Site summary shape the "
                "operator index accepts."
            ),
        )

    with _client(ENABLED) as invalid:
        cases["create_site_invalid_request"] = _capture(
            invalid,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(site_id="not a valid id"),
            description=(
                "A malformed identity. The refusal is product copy the screen "
                "renders verbatim, not a validation dump."
            ),
        )

    with _client(ENABLED, repository=FakeSiteRepository([site()])) as conflict:
        cases["create_site_duplicate_identity"] = _capture(
            conflict,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(),
            description=(
                "A Site ID already in use. T006 settled this copy as renderable "
                "product copy."
            ),
        )

    with _client(ENABLED) as unknown_template:
        cases["create_site_template_not_found"] = _capture(
            unknown_template,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(template_id="no-such-template"),
            description="A template identity the shipped catalog does not hold.",
        )

    with _client(ENABLED, repository=_UnavailableRepository()) as unreadable:
        cases["sites_list_store_unavailable"] = _capture(
            unreadable,
            "GET",
            SITES_PATH,
            description=(
                "The store could not be read. A different fact from an empty "
                "index, and the index must not claim the second."
            ),
        )
        cases["site_detail_store_unavailable"] = _capture(
            unreadable,
            "GET",
            SITE_DETAIL_PATH,
            description=(
                "The store could not be read. A different fact from a Site that "
                "is not configured."
            ),
        )
        cases["create_site_store_unavailable"] = _capture(
            unreadable,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(),
            description="Nothing was written, and the refusal says so.",
        )

    with _client(ENABLED, catalog=_Catalog(())) as empty_catalog:
        cases["template_list_empty"] = _capture(
            empty_catalog,
            "GET",
            TEMPLATES_PATH,
            description=(
                "This build ships no templates. A real answer, not an "
                "unreadable catalog."
            ),
        )

    with _client(ENABLED, catalog=_UnavailableCatalog()) as unreadable_catalog:
        cases["template_list_catalog_unavailable"] = _capture(
            unreadable_catalog,
            "GET",
            TEMPLATES_PATH,
            description=(
                "The catalog could not be read. Must not degrade into an empty "
                "catalog."
            ),
        )
        cases["template_detail_catalog_unavailable"] = _capture(
            unreadable_catalog,
            "GET",
            TEMPLATE_DETAIL_PATH,
            description="The catalog could not be read.",
        )

    # The closed gate. Lab surfaces are unserved; operator Site reads are not
    # touched by the gate and answer exactly as they do with it open.
    with _client(DISABLED, repository=FakeSiteRepository([site()])) as closed:
        cases["gate_closed_status"] = _capture(
            closed,
            "GET",
            LAB_STATUS_PATH,
            description="Unserved, not a disabled-looking body.",
        )
        cases["gate_closed_template_list"] = _capture(
            closed,
            "GET",
            TEMPLATES_PATH,
            description="Unserved. The route is not registered at all.",
        )
        cases["gate_closed_template_detail"] = _capture(
            closed,
            "GET",
            TEMPLATE_DETAIL_PATH,
            description="Unserved.",
        )
        cases["gate_closed_create_site"] = _capture(
            closed,
            "POST",
            CREATE_SITE_PATH,
            body=_create_request(),
            description="Unserved. Nothing can be created through a closed gate.",
        )
        cases["gate_closed_sites_list"] = _capture(
            closed,
            "GET",
            SITES_PATH,
            description=(
                "Ungated. The gate covers Lab surfaces and execution, never "
                "Site objects or stores."
            ),
        )
        cases["gate_closed_site_detail"] = _capture(
            closed,
            "GET",
            SITE_DETAIL_PATH,
            description="Ungated, and identical to the open-gate response.",
        )

    return {
        "generated_by": "backend/tests/test_fetch_seam_contract.py",
        "regenerate_with": REGENERATE_COMMAND,
        "purpose": (
            "The Site Foundation frontend/backend fetch seam. The backend "
            "generates these from real responses; the frontend's client tests "
            "read them back. Neither side imports the other."
        ),
        "cases": cases,
    }


@pytest.fixture(scope="module")
def cases() -> dict[str, Any]:
    """The captured cases, generated once for the guards below."""
    return _generate()["cases"]


def _serialize(fixture: dict[str, Any]) -> str:
    return json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


class TestFetchSeamFixture:
    """The fixture is generated here and must match what is checked in."""

    def test_the_checked_in_fixture_matches_what_the_backend_sends(self) -> None:
        generated = _serialize(_generate())

        if os.environ.get(REGENERATE_ENV) == "1":
            FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
            FIXTURE_PATH.write_text(generated, encoding="utf-8")
            pytest.skip(
                f"Regenerated {FIXTURE_PATH.name}. Read the diff before "
                "committing it: a change here changes what every Site screen "
                "can render."
            )

        assert FIXTURE_PATH.is_file(), (
            f"The fetch seam fixture is missing at {FIXTURE_PATH}. "
            f"Generate it with: {REGENERATE_COMMAND}"
        )

        checked_in = FIXTURE_PATH.read_text(encoding="utf-8")

        assert checked_in == generated, (
            "The checked-in fetch seam fixture no longer matches what the "
            "backend sends, so the frontend client tests are asserting against "
            "a response shape that no longer exists. This is the point of the "
            "fixture: it cannot rot silently. If the change is intended, "
            f"regenerate with: {REGENERATE_COMMAND}"
        )


class TestTheSeamItselfHoldsItsDistinctions:
    """Guards on the captured responses, so a regeneration cannot quietly
    erase a distinction the screens depend on.

    Without these, regenerating the fixture after a backend change would make
    the frontend tests agree with the new shape and nobody would notice that a
    product rule had moved.
    """

    def test_an_empty_index_is_not_an_unreadable_store(
        self, cases: dict[str, Any]
    ) -> None:
        empty = cases["sites_list_empty"]["response"]
        unreadable = cases["sites_list_store_unavailable"]["response"]

        assert empty["status"] == 200
        assert empty["body"] == {"sites": []}
        assert unreadable["status"] == 503

    def test_an_unknown_site_is_not_an_unreadable_store(
        self, cases: dict[str, Any]
    ) -> None:
        assert cases["site_detail_not_found"]["response"]["status"] == 404
        assert cases["site_detail_store_unavailable"]["response"]["status"] == 503

    def test_every_create_refusal_carries_renderable_copy(
        self, cases: dict[str, Any]
    ) -> None:
        # The create client reads `detail.message`. A refusal whose detail is a
        # bare string would reach a screen as a generic failure instead of the
        # backend's own words.
        for name in (
            "create_site_invalid_request",
            "create_site_duplicate_identity",
            "create_site_template_not_found",
            "create_site_store_unavailable",
        ):
            detail = cases[name]["response"]["body"]["detail"]
            assert isinstance(detail, dict), f"{name} lost its refusal envelope"
            assert isinstance(detail.get("message"), str) and detail["message"], (
                f"{name} has no renderable message"
            )

    def test_a_closed_gate_serves_no_lab_surface(self, cases: dict[str, Any]) -> None:
        for name in (
            "gate_closed_status",
            "gate_closed_template_list",
            "gate_closed_template_detail",
            "gate_closed_create_site",
        ):
            assert cases[name]["response"]["status"] == 404, f"{name} is still served"

    def test_a_closed_gate_does_not_reach_site_reads(
        self, cases: dict[str, Any]
    ) -> None:
        assert (
            cases["gate_closed_sites_list"]["response"]
            == cases["sites_list_loaded"]["response"]
        )
        assert (
            cases["gate_closed_site_detail"]["response"]
            == cases["site_detail_loaded"]["response"]
        )

    def test_a_declared_foundation_is_distinguishable_from_one_that_declares_none(
        self, cases: dict[str, Any]
    ) -> None:
        """The distinction the expanded Foundation is built around.

        A frontend reading these two bodies has to be able to tell "this Site
        declares no devices" from "this Site declares these devices". If the
        empty case ever came back as `[]`, a screen could render an empty
        device table and state something about the site that its configuration
        document never said.
        """
        declared = cases["site_detail_loaded"]["response"]["body"]["foundation"]
        none = cases["site_detail_declares_no_foundation_content"]["response"][
            "body"
        ]["foundation"]

        for field in (
            "topology",
            "devices",
            "signal_mappings",
            "control_assumptions",
        ):
            assert none[field] is None, f"{field} came back as something other than null"
            assert declared[field] is not None, f"{field} carries no declared content"

    def test_a_declared_device_carries_no_runtime_or_evidence_value(
        self, cases: dict[str, Any]
    ) -> None:
        """Devices reach the wire as configured assets awaiting runtime."""
        foundation = cases["site_detail_loaded"]["response"]["body"]["foundation"]

        assert foundation["devices"], "the device guard must not be vacuous"
        for device in foundation["devices"]:
            for signal in device["signals"]:
                assert set(signal) == {"signal_id", "display_name", "unit"}

    def test_a_template_never_acquires_site_identity(
        self, cases: dict[str, Any]
    ) -> None:
        detail = cases["template_detail_loaded"]["response"]["body"]

        for field in (
            "site_id",
            "lifecycle_status",
            "location",
            "timezone",
            "source",
            "origin",
        ):
            assert field not in detail, f"a template acquired {field}"

    def test_no_response_carries_evidence_or_simulator_truth(
        self, cases: dict[str, Any]
    ) -> None:
        banned = (
            "evidence",
            "source_health",
            "last_analysed",
            "assessment",
            "findings",
            "analytics",
            "replay",
            "truth",
        )
        serialized = json.dumps(cases)

        for field in banned:
            assert f'"{field}"' not in serialized, f"a response carries {field}"
