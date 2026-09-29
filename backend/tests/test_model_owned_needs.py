"""T024, Option C: what a model needs from the Foundation, frozen with provenance.

`D-2026-09-29-t024-option-c-and-reserve-override`. The daytime mini-grid
profile declares the Foundation values its laws need and the Site Controls its
controller reads; run setup resolves each against the Site valid at run start
and freezes it in the run's deterministic identity, and the run document
carries it through the store and back. Every Draft here is built by the real
setup service from a Site created from the shipped Kobo template and the
shipped Kobo scenario.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RunConfigurationInvalid
from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL,
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_backend.runs.provenance import frozen_inputs
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.service import SiteCreationService
from assetops_backend.sites.site_parsing import (
    CreateSiteRequest,
    parse_site_document,
    render_site_document,
)

from run_fixtures import FakeRuns, FakeScenarios, FakeSites

ROOT = Path(__file__).resolve().parents[2]


def kobo_site(edit=None):
    template = parse_site_template(
        yaml.safe_load(
            (ROOT / "config" / "site-templates" / "kobo-mini-grid-60kw.yaml").read_text(
                encoding="utf-8"
            )
        ),
        source="the Kobo template",
    )
    created: list[Any] = []

    class Recording:
        def create_site(self, record):
            created.append(record)
            return record

    class Catalog:
        def list_templates(self) -> tuple:
            return (template,)

        def get_template(self, template_id: str):
            return template

    SiteCreationService(Recording(), Catalog()).create_site_from_template(
        CreateSiteRequest(
            template_id="kobo-mini-grid-60kw",
            site_id="KOBO-001",
            display_name="Kobo mini-grid",
            country="Ethiopia",
            locality="Kobo",
            timezone="Africa/Addis_Ababa",
        )
    )
    site = created[0]
    if edit is None:
        return site
    document = copy.deepcopy(render_site_document(site))
    edit(document)
    return parse_site_document(document, source="an edited Kobo site")


def kobo_run(*, site_edit=None, model=DAYTIME_MINI_GRID_MODEL) -> SimulationRun:
    definition = parse_scenario_document(
        yaml.safe_load(
            (ROOT / "config" / "scenarios" / "kobo-daytime.yaml").read_text(
                encoding="utf-8"
            )
        ),
        source="kobo-daytime",
        origin="SHIPPED",
    )
    site = kobo_site(site_edit)
    service = RunSetupService(
        FakeRuns(),
        FakeSites((site,)),
        FakeScenarios((definition,)),
        model_profiles=(MINIMAL_FUEL_TANK_MODEL, DAYTIME_MINI_GRID_MODEL),
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: "2026-09-29T09:00:00Z",
    )
    return service.create_draft_run(
        {
            "site_id": "KOBO-001",
            "foundation_version": site.foundation.version,
            "scenario_id": "kobo-daytime",
            "scenario_version": 1,
            "interval": {
                "start_time": "2026-09-22T03:00:00Z",
                "end_time": "2026-09-22T15:00:00Z",
            },
            "timestep_minutes": 15,
            "seed": 7,
            "model_profile": {
                "profile_id": model.model_profile_id,
                "profile_version": model.model_profile_version,
            },
            "publication_profile": {
                "profile_id": LAB_PUBLICATION_PROFILE.publication_profile_id,
                "profile_version": LAB_PUBLICATION_PROFILE.publication_profile_version,
            },
            "run_inputs": [],
        }
    )


class TestTheNeedsAreFrozenWithProvenance:
    def test_every_need_is_frozen_at_its_component_with_who_declared_and_answered(
        self,
    ) -> None:
        run = kobo_run()
        assert run.execution_status == "READY", run.blocking_reasons
        needs = {
            item.addressed_key: item for item in run.deterministic_identity.model_needs
        }
        assert set(needs) == {
            "pv-rated-power@pv-array",
            "inverter-ac-limit@pv-inverter",
            "battery-energy-capacity@battery",
            "pcs-charge-limit@battery-pcs",
            "pcs-discharge-limit@battery-pcs",
            "pcs-conversion-efficiency@battery-pcs",
            "battery-reserve-state-of-charge@battery",
        }
        capacity = needs["battery-energy-capacity@battery"]
        assert capacity.value == 200.0
        assert capacity.unit == "kWh"
        assert capacity.declared_by == "model profile daytime-mini-grid version 1"
        assert capacity.answered_by == "SITE_FOUNDATION"
        assert capacity.foundation_version == 1
        assert capacity.foundation_valid_from
        assert (capacity.property_source, capacity.property_source_version) == (
            "TEMPLATE",
            1,
        )
        assert needs["battery-reserve-state-of-charge@battery"].value == 30.0

    def test_the_effective_site_controls_are_frozen_in_order(self) -> None:
        run = kobo_run()
        controls = {
            item.control_key: item for item in run.deterministic_identity.site_controls
        }
        assert controls["source-priority"].members == (
            "pv-array",
            "battery",
            "generator",
        )
        assert controls["critical-load-priority"].members == (
            "load-clinic",
            "load-res",
            "load-mill",
        )
        assert controls["source-priority"].source == "TEMPLATE"

    def test_a_site_answer_names_the_site_as_its_source(self) -> None:
        def site_value(document):
            for item in document["foundation"]["components"]:
                if item["component_id"] == "battery-pcs":
                    for prop in item["properties"]:
                        if prop["property_key"] == "pcs-discharge-limit":
                            prop["value"] = 22
                            prop["source"] = "SITE"

        run = kobo_run(site_edit=site_value)
        need = next(
            item
            for item in run.deterministic_identity.model_needs
            if item.addressed_key == "pcs-discharge-limit@battery-pcs"
        )
        assert (need.value, need.property_source) == (22.0, "SITE")

    def test_the_fuel_profile_freezes_no_need_and_no_control(self) -> None:
        run = kobo_run(model=MINIMAL_FUEL_TANK_MODEL)
        assert run.deterministic_identity.model_needs == ()
        assert run.deterministic_identity.site_controls == ()


class TestTheProvenanceRowsAreOnTheDraft:
    def test_each_need_and_control_is_a_row_with_its_provenance(self) -> None:
        run = kobo_run()
        rows = frozen_inputs(run.deterministic_identity, run.blocking_reasons)
        need_rows = [row for row in rows if row.identity_field == "model_needs"]
        control_rows = [row for row in rows if row.identity_field == "site_controls"]
        assert len(need_rows) == 7
        capacity = next(
            row
            for row in need_rows
            if "battery-energy-capacity@battery" in row.field
        )
        assert capacity.value == "200 kWh"
        assert "needed by model profile daytime-mini-grid version 1" in (
            capacity.answered_by_detail
        )
        assert "declared TEMPLATE version 1" in capacity.answered_by_detail
        priority = next(
            row for row in control_rows if row.field == "Site control critical-load-priority"
        )
        assert priority.value == "load-clinic > load-res > load-mill"


class TestTheRunDocumentCarriesThem:
    def test_the_needs_and_controls_round_trip_through_the_run_document(
        self,
    ) -> None:
        run = kobo_run()
        reread = parse_run_document(render_run_document(run), source="a round trip")
        assert reread.deterministic_identity.model_needs == (
            run.deterministic_identity.model_needs
        )
        assert reread.deterministic_identity.site_controls == (
            run.deterministic_identity.site_controls
        )

    @pytest.mark.parametrize("key", ["model_needs", "site_controls"])
    def test_a_version_nine_record_omitting_them_is_refused(self, key: str) -> None:
        document = render_run_document(kobo_run())
        del document["deterministic_identity"][key]
        with pytest.raises(RunConfigurationInvalid) as raised:
            parse_run_document(document, source="a hand-edited run")
        assert key in str(raised.value)

    def test_a_version_eight_record_without_them_reads_back_empty(self) -> None:
        document = render_run_document(kobo_run())
        del document["deterministic_identity"]["model_needs"]
        del document["deterministic_identity"]["site_controls"]
        document["deterministic_identity"]["profiles"]["execution_contract_version"] = 8
        reread = parse_run_document(document, source="an earlier run")
        assert reread.deterministic_identity.model_needs == ()
        assert reread.deterministic_identity.site_controls == ()

    def test_an_answer_without_its_source_is_refused(self) -> None:
        document = render_run_document(kobo_run())
        document["deterministic_identity"]["model_needs"][0]["property_source"] = None
        with pytest.raises(RunConfigurationInvalid):
            parse_run_document(document, source="a hand-edited run")


class TestSiteControlsAreValidatedAtTheFoundation:
    @pytest.mark.parametrize(
        "members, fragment",
        [
            (["load-clinic", "load-res"], "leaves out"),
            (["load-clinic", "load-res", "load-mill", "load-res"], "Duplicate"),
            (["load-clinic", "load-res", "battery"], "orders components of type"),
            (["load-clinic", "load-res", "ghost"], "does not declare"),
        ],
    )
    def test_a_priority_list_names_every_component_of_its_kind_once(
        self, members, fragment
    ) -> None:
        from assetops_backend.sites.ports import SiteConfigurationInvalid

        def edit(document):
            for control in document["foundation"]["site_controls"]:
                if control["control_key"] == "critical-load-priority":
                    control["members"] = members

        with pytest.raises(SiteConfigurationInvalid) as raised:
            kobo_site(edit)
        assert fragment in str(raised.value)

    def test_an_unknown_control_key_is_refused(self) -> None:
        from assetops_backend.sites.ports import SiteConfigurationInvalid

        def edit(document):
            document["foundation"]["site_controls"][0]["control_key"] = "auto-mode"

        with pytest.raises(SiteConfigurationInvalid):
            kobo_site(edit)
