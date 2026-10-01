"""T025g phase 1: the run is the only join of a scenario and a site.

`D-2026-10-01-run-binds-scenario-to-site`. Proved here and in
`test_run_setup.py`:

- AC1/AC10: a scenario need not name a site; a well-formed legacy
  `target_site` still parses, so documents shaped like the owner's
  `var/scenarios` copies keep the catalog alive. Those copies are never read:
  the shape is reproduced from the shipped documents they were copied from.
- AC2/AC6a: run setup binds the site the user picks (`test_run_setup.py`).
- AC3: the Site's template lineage is frozen on the run's site binding as
  provenance. A run stored before this slice reads back "not recorded" and
  re-renders exactly as it was stored.
"""

from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
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

from assetops_backend.runs.models import FrozenTemplateLineage
from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.adapters.composite_scenario_repository import (
    CompositeScenarioRepository,
)
from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import (
    ReadOnlyYamlScenarioStore,
)
from assetops_backend.scenarios.adapters.yaml_user_scenario_store import (
    UserYamlScenarioStore,
)
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid
from assetops_backend.sites.models import SiteTemplateProvenance

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_SCENARIOS = REPOSITORY_ROOT / "config" / "scenarios"


def parse(document: dict, *, origin: str = "SHIPPED"):
    return parse_scenario_document(document, source="a test", origin=origin)


def draft(*, sites: FakeSites, **request):
    setup = RunSetupService(
        FakeRuns(),
        sites,
        FakeScenarios((scenario(),)),
        model_profiles=(model_profile(),),
        publication_profiles=(publication_profile(),),
        now=lambda: "2026-09-21T09:00:00Z",
    )
    return setup.create_draft_run(setup_request(**request))


# --- AC1: the parser ---------------------------------------------------------


class TestTheParser:
    def test_a_document_without_target_site_parses(self) -> None:
        document = scenario_document()
        del document["target_site"]

        record = parse(document)

        assert record.target_site is None
        assert record.site_contract is None

    def test_a_well_formed_legacy_target_site_is_carried(self) -> None:
        record = parse(scenario_document())

        assert record.target_site is not None
        assert record.target_site.policy == "DECLARED_SITE"
        assert record.target_site.site_id == "MG-900"

    def test_a_null_target_site_is_malformed_not_absent(self) -> None:
        """Absent is accepted; present-and-null is a broken declaration."""
        document = scenario_document()
        document["target_site"] = None

        with pytest.raises(ScenarioConfigurationInvalid, match="target_site"):
            parse(document)

    def test_a_site_contract_description_is_accepted(self) -> None:
        document = scenario_document()
        del document["target_site"]
        document["site_contract"] = {
            "description": "A mini-grid with a generator and a status signal."
        }

        record = parse(document)

        assert record.site_contract is not None
        assert record.site_contract.description == (
            "A mini-grid with a generator and a status signal."
        )

    def test_an_empty_site_contract_has_no_description(self) -> None:
        document = scenario_document()
        document["site_contract"] = {}

        contract = parse(document).site_contract
        assert contract is not None
        assert contract.description is None

    @pytest.mark.parametrize(
        "contract",
        [
            pytest.param("prose", id="not-an-object"),
            pytest.param(None, id="null"),
            pytest.param({"description": ""}, id="empty-description"),
            pytest.param({"description": 7}, id="description-not-text"),
            pytest.param({"description": "x" * 601}, id="description-too-long"),
            # No template hint and no site may ride in the contract block.
            pytest.param(
                {"template_id": "kobo-mini-grid-60kw"}, id="template-hint"
            ),
            pytest.param({"site_id": "KOBO-001"}, id="site-id"),
        ],
    )
    def test_a_malformed_site_contract_is_refused(self, contract) -> None:
        document = scenario_document()
        document["site_contract"] = contract

        with pytest.raises(ScenarioConfigurationInvalid, match="site_contract"):
            parse(document)

    @pytest.mark.parametrize("key", ["template_id", "template", "archetype"])
    def test_no_template_hint_is_accepted_at_the_top_level(self, key) -> None:
        document = scenario_document()
        document[key] = "kobo-mini-grid-60kw"

        with pytest.raises(ScenarioConfigurationInvalid, match=key):
            parse(document)


# --- AC10: the catalog stays alive -------------------------------------------


def owner_shaped_copy(path: Path) -> dict:
    """A shipped document copied the way the owner copied one into `var/`.

    The owner's workaround (`D-2026-10-01-run-binds-scenario-to-site`,
    Trigger) was a copy of a shipped scenario under a new identity naming a
    different site through the legacy `DECLARED_SITE` declaration.
    """
    document = copy.deepcopy(yaml.safe_load(path.read_text(encoding="utf-8")))
    document["scenario_id"] = f"{document['scenario_id']}-copy"
    assert document["target_site"]["policy"] == "DECLARED_SITE"
    document["target_site"]["site_id"] = "GONDAR-01"
    return document


SHIPPED_DOCUMENTS = sorted(SHIPPED_SCENARIOS.glob("*.yaml"))


def test_the_shipped_documents_were_found() -> None:
    assert len(SHIPPED_DOCUMENTS) >= 7, "nothing to copy, so AC10 proves nothing"


@pytest.mark.parametrize(
    "path", SHIPPED_DOCUMENTS, ids=[path.stem for path in SHIPPED_DOCUMENTS]
)
def test_an_owner_shaped_copy_still_parses(path: Path) -> None:
    record = parse(owner_shaped_copy(path), origin="USER")

    assert record.target_site is not None
    assert record.target_site.site_id == "GONDAR-01"


def test_the_catalog_lists_every_owner_shaped_copy(tmp_path: Path) -> None:
    """One malformed document fails the whole catalog, so the list is the proof."""
    user = tmp_path / "user"
    user.mkdir()
    for path in SHIPPED_DOCUMENTS:
        (user / path.name).write_text(
            yaml.safe_dump(owner_shaped_copy(path), sort_keys=False),
            encoding="utf-8",
        )

    repository = CompositeScenarioRepository(
        shipped=ReadOnlyYamlScenarioStore(SHIPPED_SCENARIOS),
        user=UserYamlScenarioStore(user),
    )
    listed = {record.scenario_id for record in repository.list_scenarios()}

    for path in SHIPPED_DOCUMENTS:
        original = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert original["scenario_id"] in listed
        assert f"{original['scenario_id']}-copy" in listed


# --- AC3: template lineage frozen as run provenance --------------------------


KOBO_LINEAGE = SiteTemplateProvenance(
    template_id="kobo-mini-grid-60kw", template_version=2
)


class TestTemplateLineage:
    def test_a_site_built_from_a_template_freezes_its_lineage(self) -> None:
        record = draft(sites=FakeSites((site(template=KOBO_LINEAGE),)))

        assert record.deterministic_identity.site.template_lineage == (
            FrozenTemplateLineage(
                template_id="kobo-mini-grid-60kw", template_version=2
            )
        )

    def test_a_site_with_no_template_freezes_an_explicit_null(self) -> None:
        record = draft(sites=FakeSites((site(),)))

        assert record.deterministic_identity.site.template_lineage == (
            FrozenTemplateLineage(template_id=None, template_version=None)
        )

    @pytest.mark.parametrize(
        "template", [KOBO_LINEAGE, None], ids=["template", "no-template"]
    )
    def test_lineage_round_trips_through_the_stored_document(
        self, template
    ) -> None:
        record = draft(sites=FakeSites((site(template=template),)))
        document = render_run_document(record)

        assert "template_lineage" in document["deterministic_identity"]["site"]
        reloaded = parse_run_document(document, source="a test")
        assert reloaded == record

    def test_a_run_stored_before_lineage_reads_not_recorded(self) -> None:
        record = draft(sites=FakeSites((site(template=KOBO_LINEAGE),)))
        document = render_run_document(record)
        del document["deterministic_identity"]["site"]["template_lineage"]

        reloaded = parse_run_document(document, source="an earlier run")

        assert reloaded.deterministic_identity.site.template_lineage is None
        # Re-rendered exactly as it was stored: nothing is inferred or added.
        assert render_run_document(reloaded) == document

    @pytest.mark.parametrize(
        "lineage",
        [
            pytest.param(None, id="null"),
            pytest.param({"template_id": "kobo-mini-grid-60kw"}, id="half"),
            pytest.param(
                {"template_id": "kobo-mini-grid-60kw", "template_version": None},
                id="id-without-version",
            ),
            pytest.param(
                {"template_id": None, "template_version": 2},
                id="version-without-id",
            ),
            pytest.param(
                {
                    "template_id": "kobo-mini-grid-60kw",
                    "template_version": 2,
                    "site_id": "KOBO-001",
                },
                id="extra-key",
            ),
            pytest.param(
                {"template_id": "kobo-mini-grid-60kw", "template_version": "2"},
                id="version-not-whole",
            ),
        ],
    )
    def test_a_malformed_stored_lineage_is_refused(self, lineage) -> None:
        record = draft(sites=FakeSites((site(),)))
        document = render_run_document(record)
        document["deterministic_identity"]["site"]["template_lineage"] = lineage

        with pytest.raises(RunConfigurationInvalid, match="template_lineage"):
            parse_run_document(document, source="a test")

    def test_lineage_is_not_a_frozen_input(self) -> None:
        """The guardrail, setup-summary half: provenance, not a frozen input.

        The world-inputs and `frozen_inputs_identity` half is proved in
        `host/tests/test_t025g_lineage.py` and by the contract-9 gate
        reproducing unchanged.
        """
        record = draft(sites=FakeSites((site(template=KOBO_LINEAGE),)))
        identity = record.deterministic_identity
        without = replace(
            identity, site=replace(identity.site, template_lineage=None)
        )

        assert frozen_inputs(identity) == frozen_inputs(without)


# --- Phase-1 transitional: the detail read model survives a document without
# --- a site. Both the resolution and this payload retire in phase 2 (AC8).


def test_the_detail_service_resolves_nothing_for_a_document_without_a_site() -> None:
    from assetops_backend.scenarios.service import ScenarioDetailService
    from assetops_backend.simulator_lab_api import scenario_public_summary

    document = scenario_document()
    del document["target_site"]
    unnamed = parse(document)
    detail = ScenarioDetailService(FakeScenarios((unnamed,)), FakeSites((site(),)))

    assert detail.resolve_target_site(unnamed).state == "NOT_APPLICABLE"
    assert {
        item.state for item in detail.resolve_observation_sources(unnamed)
    } <= {"NOT_CONFIGURED", "NOT_APPLICABLE"}
    assert scenario_public_summary(unnamed)["target_site"] is None
