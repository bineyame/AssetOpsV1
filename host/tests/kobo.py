"""Kobo daytime Drafts, built the way the product builds them (T024).

A Site from the shipped `kobo-mini-grid-60kw` template, a scenario from the
shipped `kobo-daytime*` documents, and a Draft frozen by the real run setup
service against the `daytime-mini-grid` profile. Nothing is read from or
written to `var/`.

`site_edit` and `document_edit` change one fact before the product parses it,
which is how a variation is made: a mutation of a parsed record could produce
one the parser would never have accepted.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

import yaml

from assetops_backend.runs.models import SimulationRun
from assetops_backend.runs.profiles import (
    DAYTIME_MINI_GRID_MODEL,
    LAB_PUBLICATION_PROFILE,
    MINIMAL_FUEL_TANK_MODEL,
)
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.parsing import parse_scenario_document
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.site_parsing import (
    parse_site_document,
    render_site_document,
)

from fixtures import (
    REPOSITORY_ROOT,
    FakeRuns,
    FakeScenarios,
    FakeSites,
    site_from_template,
)

KOBO_TEMPLATE = (
    REPOSITORY_ROOT / "config" / "site-templates" / "kobo-mini-grid-60kw.yaml"
)
SCENARIOS = REPOSITORY_ROOT / "config" / "scenarios"
KOBO_SITE_ID = "KOBO-001"
START = "2026-09-22T03:00:00Z"  # 06:00 in Africa/Addis_Ababa
END = "2026-09-22T15:00:00Z"
FOUNDATION_VALID_FROM = "2026-09-01T00:00:00Z"  # before START


def kobo_document(name: str = "kobo-daytime") -> dict[str, Any]:
    return yaml.safe_load((SCENARIOS / f"{name}.yaml").read_text(encoding="utf-8"))


def kobo_site(
    site_edit: Callable[[dict[str, Any]], None] | None = None,
) -> SiteRecord:
    site = site_from_template(
        KOBO_TEMPLATE, site_id=KOBO_SITE_ID, timezone="Africa/Addis_Ababa"
    )
    # The template path stamps the Foundation with the wall clock, which is
    # after the September interval these runs cover. A Foundation that begins
    # after the run starts blocks it (T024 fix round), so the fixture's
    # Foundation is made valid from before the run.
    document = copy.deepcopy(render_site_document(site))
    document["foundation"]["valid_from"] = FOUNDATION_VALID_FROM
    if site_edit is not None:
        site_edit(document)
    return parse_site_document(document, source="an edited Kobo site")


def component(document: dict[str, Any], component_id: str) -> dict[str, Any]:
    for item in document["foundation"]["components"]:
        if item["component_id"] == component_id:
            return item
    raise KeyError(component_id)


def set_property(
    document: dict[str, Any], component_id: str, key: str, value: float
) -> None:
    for item in component(document, component_id)["properties"]:
        if item["property_key"] == key:
            item["value"] = value
            item["source"] = "SITE"
            return
    raise KeyError(key)


def remove_property(document: dict[str, Any], component_id: str, key: str) -> None:
    item = component(document, component_id)
    item["properties"] = [
        entry for entry in item["properties"] if entry["property_key"] != key
    ] or None


def kobo_draft(
    name: str = "kobo-daytime",
    *,
    document: dict[str, Any] | None = None,
    document_edit: Callable[[dict[str, Any]], None] | None = None,
    site_edit: Callable[[dict[str, Any]], None] | None = None,
    timestep_minutes: int = 15,
    model_profile: str = "daytime-mini-grid",
    seed: int = 20260929,
    start_time: str = START,
    end_time: str = END,
) -> SimulationRun:
    raw = copy.deepcopy(document if document is not None else kobo_document(name))
    if document_edit is not None:
        document_edit(raw)
    definition = parse_scenario_document(
        raw, source="a Kobo scenario", origin="SHIPPED"
    )
    site = kobo_site(site_edit)
    profiles = (MINIMAL_FUEL_TANK_MODEL, DAYTIME_MINI_GRID_MODEL)
    profile = next(p for p in profiles if p.model_profile_id == model_profile)
    setup = RunSetupService(
        FakeRuns(),
        FakeSites((site,)),
        FakeScenarios((definition,)),
        model_profiles=profiles,
        publication_profiles=(LAB_PUBLICATION_PROFILE,),
        now=lambda: "2026-09-29T09:00:00Z",
    )
    return setup.create_draft_run(
        {
            "site_id": site.site_id,
            "foundation_version": site.foundation.version,
            "scenario_id": definition.scenario_id,
            "scenario_version": definition.version.scenario_version,
            "interval": {"start_time": start_time, "end_time": end_time},
            "timestep_minutes": timestep_minutes,
            "seed": seed,
            "model_profile": {
                "profile_id": profile.model_profile_id,
                "profile_version": profile.model_profile_version,
            },
            "publication_profile": {
                "profile_id": LAB_PUBLICATION_PROFILE.publication_profile_id,
                "profile_version": LAB_PUBLICATION_PROFILE.publication_profile_version,
            },
            "run_inputs": [],
        }
    )


__all__ = [
    "KOBO_SITE_ID",
    "Path",
    "component",
    "kobo_document",
    "kobo_draft",
    "kobo_site",
    "remove_property",
    "set_property",
]
