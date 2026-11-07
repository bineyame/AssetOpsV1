"""DIESEL-1 K1 (ruling DIESEL-1-R3c §9c.1): Kisiwa Drafts on the registered Site.

`KisiwaRegistered` is the attribute and method surface `tools/probe_kisiwa_fuel.py` `build()`, `execute_day()` and
`readings()` use from the probe's `Registered`, built over a store in which `tools/demo_combined_kisiwa.py`
`register_in` registered KISIWA-001 (Postgres in the parity test). The model is K1a's product mini-grid v7, not the
probe-local copy. Nothing is read from or written to `var/`.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from typing import Any

from assetops_backend.runs.profiles import MINI_GRID_V6_MODEL, MINI_GRID_V7_MODEL
from assetops_simulator.packs import mini_grid

SITE_ID = "KISIWA-001"
RUN1_START = "2026-10-01T12:00:00Z"  # F0r run 1, 15:00 local (UTC+3)
SEED = 20260929
TIMESTEP_MINUTES = 5


def _at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def _iso(moment: datetime) -> str:
    return moment.isoformat().replace("+00:00", "Z")


def _publication_profile():
    from assetops_backend.runs.profiles import REGISTERED_KOBO_PUBLICATION_PROFILE_V5

    return REGISTERED_KOBO_PUBLICATION_PROFILE_V5


class KisiwaRegistered:
    """The registered path over an already registered KISIWA-001: the real `RegisteredLabBasis` over `store`."""

    def __init__(self, store, setup_at: str, actions=None) -> None:
        """`actions` is an `OperationalActionLogPort` handed to run setup (DIESEL-1-R3f); None means no log."""
        from assetops_backend.runs.registered_basis import RegisteredLabBasis
        from assetops_backend.sites.cutover import ImportedSiteRegistry
        from assetops_backend.sites.foundation_service import FoundationService

        self.store = store
        self.setup_at = setup_at
        self.actions = actions
        moment = _at(setup_at)
        self.basis = RegisteredLabBasis(ImportedSiteRegistry(FoundationService(store, "demo", lambda: moment)))
        self.v7_sim = mini_grid.MINI_GRID_V7_MODEL
        self.v7_profile = MINI_GRID_V7_MODEL
        start = _at(RUN1_START)
        selection = self.basis.select(SITE_ID, start_time=RUN1_START, end_time=_iso(start + timedelta(days=1)),
                                      knowledge_at=None)
        self.foundation_version = selection.basis.foundation_version

    def draft(self, document: dict[str, Any], start: str, end: str, model: str = "v7",
              operational_actions: dict | None = None):
        """The probe's `Registered.draft` `RunSetupService` call, on product v7 (or v6).

        `operational_actions` (`{"log_id", "log_version"}`) is added to the request only when given."""
        from assetops_backend.runs.service import RunSetupService
        from assetops_backend.scenarios.parsing import parse_scenario_document
        from fixtures import FakeRuns, FakeScenarios, FakeSites

        profile = _publication_profile()
        chosen = self.v7_profile if model == "v7" else MINI_GRID_V6_MODEL
        definition = parse_scenario_document(copy.deepcopy(document), source="a Kisiwa scenario", origin="SHIPPED")
        setup = RunSetupService(
            FakeRuns(), FakeSites(()), FakeScenarios((definition,)), model_profiles=(chosen,),
            publication_profiles=(profile,), now=lambda: self.setup_at, registered_bases=self.basis,
            operational_actions=self.actions)
        extra = {} if operational_actions is None else {"operational_actions": operational_actions}
        return setup.create_draft_run({**extra,
            "site_id": SITE_ID, "foundation_version": self.foundation_version,
            "scenario_id": definition.scenario_id, "scenario_version": definition.version.scenario_version,
            "interval": {"start_time": start, "end_time": end}, "timestep_minutes": TIMESTEP_MINUTES,
            "seed": SEED,
            "model_profile": {"profile_id": chosen.model_profile_id,
                              "profile_version": chosen.model_profile_version},
            "publication_profile": {"profile_id": profile.publication_profile_id,
                                    "profile_version": profile.publication_profile_version},
            "run_inputs": []})

    def sim(self, model: str):
        return self.v7_sim if model == "v7" else mini_grid.MINI_GRID_V6_MODEL


def draft_day(store, document: dict[str, Any], start: str, end: str, setup_at: str, actions=None,
              operational_actions: dict | None = None):
    """One Kisiwa Draft on product v7 / registered-kobo-publication v5 over the registered Site in `store`."""
    return KisiwaRegistered(store, setup_at, actions).draft(document, start, end, "v7", operational_actions)
