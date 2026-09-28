"""Frozen Drafts built the way the product builds them.

Every run these tests execute was created by `RunSetupService` from a Site
instantiated by `SiteCreationService` and a definition read by the real scenario
parser. None was written as a run record and none was read out of `var/runs`.

**Neither of those is a convenience.** A fixture run record can be given any
shape, so a kernel tested against one is tested against the shape its author
expected rather than against what run setup actually freezes. And the backlog
instructs this slice to regenerate rather than execute any Draft frozen before
it: `refuse_incompatible_execution` is an equality test on an integer, version 5
carried several amendments while unpublished on the T020B branch, and twenty-odd
local Drafts are at version 5 with no way to tell them apart. Building a Draft
in-process is what makes the version guard's `5` mean this build's five.

The in-memory repositories here are the same shape as the backend suite's. They
are written again rather than imported because `host/tests` is a separate test
root and reaching into another root's private fixtures would couple two suites
that have no reason to move together.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.ports import RunNotFound
from assetops_backend.runs.profiles import (
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.models import ScenarioDefinition
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.scenarios.ports import ScenarioNotFound
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.parsing import parse_site_template
from assetops_backend.sites.ports import SiteNotFound
from assetops_backend.sites.service import SiteCreationService
from assetops_backend.sites.site_parsing import CreateSiteRequest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SHIPPED_FUEL_LOSS_EVENT = (
    REPOSITORY_ROOT / "config" / "scenarios" / "fuel-loss-event.yaml"
)
HYBRID_TEMPLATE = (
    REPOSITORY_ROOT
    / "config"
    / "site-templates"
    / "hybrid-mini-grid-100kw.yaml"
)
TWIN_TANK_TEMPLATE = (
    REPOSITORY_ROOT
    / "config"
    / "site-templates"
    / "twin-tank-mini-grid-150kw.yaml"
)


class FakeRuns:
    def __init__(self) -> None:
        self.written: list[SimulationRun] = []

    def create_run(self, record: SimulationRun) -> SimulationRun:
        self.written.append(record)
        return record

    def get_run(self, run_id: str) -> SimulationRun:
        for record in self.written:
            if record.run_id == run_id:
                return record
        raise RunNotFound(run_id)

    def list_runs(self) -> Sequence[SimulationRun]:
        return tuple(self.written)


class FakeSites:
    def __init__(self, records: Sequence[SiteRecord] = ()) -> None:
        self._records = tuple(records)

    def list_sites(self) -> Sequence[SiteRecord]:
        return self._records

    def get_site(self, site_id: str) -> SiteRecord:
        for record in self._records:
            if record.site_id.casefold() == site_id.casefold():
                return record
        raise SiteNotFound(site_id)

    def create_site(self, record: SiteRecord) -> SiteRecord:
        raise AssertionError("no run route may write a site")


class FakeScenarios:
    def __init__(self, records: Sequence[ScenarioDefinition] = ()) -> None:
        self._records = tuple(records)

    def list_scenarios(self) -> Sequence[ScenarioDefinition]:
        return self._records

    def get_scenario(self, scenario_id: str) -> ScenarioDefinition:
        for record in self._records:
            if record.scenario_id.casefold() == scenario_id.casefold():
                return record
        raise ScenarioNotFound(scenario_id)


def shipped_document() -> dict[str, Any]:
    """The shipped Fuel Loss Event, as a mutable mapping.

    Returned as a document rather than a parsed definition so a test can change
    one number and re-parse, which is how the causal mutations are made: a
    mutation that edited a parsed record could produce a record the parser would
    never have accepted.
    """
    return yaml.safe_load(SHIPPED_FUEL_LOSS_EVENT.read_text(encoding="utf-8"))


def scenario(document: dict[str, Any] | None = None) -> ScenarioDefinition:
    return parse_scenario_document(
        document if document is not None else shipped_document(),
        source="the shipped definition",
        origin="SHIPPED",
    )


def site_from_template(
    template_path: Path,
    *,
    site_id: str,
    display_name: str = "Kalangala mini-grid",
    timezone: str = "Africa/Kampala",
) -> SiteRecord:
    """A Site instantiated through the product's own create path.

    Not written as a record: templates copy, and what a run freezes has to be
    what that copy produced, including the typed component properties a model
    profile's binding aims at.
    """
    template = parse_site_template(
        yaml.safe_load(template_path.read_text(encoding="utf-8")),
        source=str(template_path.name),
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
            template_id=template.template_id,
            site_id=site_id,
            display_name=display_name,
            country="Uganda",
            locality="Kalangala",
            timezone=timezone,
        )
    )
    return created[0]


def draft(
    *,
    definition: ScenarioDefinition | None = None,
    site: SiteRecord | None = None,
    start_time: str = "2026-09-21T00:00:00Z",
    end_time: str = "2026-09-22T17:00:00Z",
    timestep_minutes: int = 15,
    seed: int = 20260927,
    run_inputs: Sequence[dict[str, Any]] = (),
) -> SimulationRun:
    """One Draft, frozen by the real run setup service.

    The Site defaults to a fresh MG-001 instantiated from the shipped hybrid
    template, which is the Site the shipped definition declares it targets. The
    MG-001 in `var/sites` is untouched: this one lives in memory for the length
    of one test.
    """
    document = definition if definition is not None else scenario()
    target = (
        site
        if site is not None
        else site_from_template(
            HYBRID_TEMPLATE, site_id=document.target_site.site_id or "MG-001"
        )
    )
    setup = RunSetupService(
        FakeRuns(),
        FakeSites((target,)),
        FakeScenarios((document,)),
        model_profiles=(MINIMAL_FUEL_TANK_MODEL,),
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: "2026-09-27T09:00:00Z",
    )
    return setup.create_draft_run(
        {
            "site_id": target.site_id,
            "foundation_version": target.foundation.version,
            "scenario_id": document.scenario_id,
            "scenario_version": document.version.scenario_version,
            "interval": {"start_time": start_time, "end_time": end_time},
            "timestep_minutes": timestep_minutes,
            "seed": seed,
            "model_profile": {
                "profile_id": "minimal-fuel-tank",
                "profile_version": MINIMAL_FUEL_TANK_MODEL.model_profile_version,
            },
            "publication_profile": {
                "profile_id": "simulator-lab-publication",
                "profile_version": LAB_PUBLICATION_PROFILE.publication_profile_version,
            },
            "run_inputs": list(run_inputs),
        }
    )
