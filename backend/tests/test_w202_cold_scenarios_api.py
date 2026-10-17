"""W2-02: `GET /api/simulator-lab/cold-scenarios?site_id=` (`D-2026-10-17-w2-02-buildspec`, "Lab choice and
run-request closure"). The six cold choices only for the registered `COLD-LAB-001` Site; an empty list for
any other or unregistered Site; an unreadable store is unavailable, never empty; the legacy catalog stays
legacy-only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from run_fixtures import FakeRuns, FakeScenarios, FakeSites, scenario, site

from assetops_backend.runs.profiles import MODEL_PROFILES, PUBLICATION_PROFILES
from assetops_backend.scenarios.cold_parsing import parse_cold_scenario_document
from assetops_backend.scenarios.ports import ScenarioStoreUnavailable
from assetops_backend.simulator_lab_api import build_simulator_lab_router
from assetops_backend.sites.ports import SiteStoreUnavailable

SCENARIOS = Path(__file__).resolve().parents[2] / "config" / "scenarios"
CASES = ("normal", "excursion", "backup-failed", "missing-probe", "late-reading", "contradictory")
ROUTE = "/api/simulator-lab/cold-scenarios"
CHOICE_KEYS = {"scenario_id", "scenario_version", "display_name", "schema", "model_profile",
               "publication_profile", "observation_profile", "start", "end", "seed"}


def cold(case: str):
    return parse_cold_scenario_document(
        yaml.safe_load((SCENARIOS / f"cold-{case}.yaml").read_text(encoding="utf-8"))
    )


class NoTemplates:
    def list_templates(self) -> Sequence[object]:
        return ()

    def get_template(self, template_id: str) -> object:  # pragma: no cover
        raise AssertionError("no cold scenario route reads a template")


class Registered:
    def __init__(self, codes=("COLD-LAB-001",), failure: Exception | None = None) -> None:
        self._codes = codes
        self._failure = failure

    def registered(self, site_id: str) -> bool:
        if self._failure is not None:
            raise self._failure
        return site_id in self._codes

    def select(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("listing choices selects no basis")


def client(*, registered=None, scenarios=None, no_port: bool = False) -> TestClient:
    app = FastAPI()
    app.include_router(
        build_simulator_lab_router(
            NoTemplates(), FakeSites((site(),)),
            scenarios or FakeScenarios((scenario(), *(cold(case) for case in reversed(CASES)))),
            FakeRuns(), MODEL_PROFILES, PUBLICATION_PROFILES,
            registered_bases=None if no_port else (registered or Registered()),
        )
    )
    return TestClient(app)


def test_six_choices_for_the_registered_cold_site() -> None:
    response = client().get(ROUTE, params={"site_id": "COLD-LAB-001"})
    assert response.status_code == 200
    body = response.json()
    assert body["site_id"] == "COLD-LAB-001"
    choices = body["scenarios"]
    assert [c["scenario_id"] for c in choices] == sorted(f"cold-{case}" for case in CASES)
    assert all(set(c) == CHOICE_KEYS for c in choices)
    labels = {c["scenario_id"]: c["display_name"] for c in choices}
    assert labels == {
        "cold-normal": "Normal", "cold-excursion": "Excursion", "cold-backup-failed": "Backup failed",
        "cold-missing-probe": "Missing probe", "cold-late-reading": "Late reading",
        "cold-contradictory": "Contradictory",
    }
    normal = next(c for c in choices if c["scenario_id"] == "cold-normal")
    assert normal == {
        "scenario_id": "cold-normal", "scenario_version": 1, "display_name": "Normal",
        "schema": "cold-scenario/1", "model_profile": "cold-thermal/1",
        "publication_profile": "cold-publication/1", "observation_profile": "cold-observation/1",
        "start": "2026-10-06T19:00:00Z", "end": "2026-10-06T20:00:00Z", "seed": 20417,
    }


def test_empty_for_any_other_or_unregistered_site() -> None:
    assert client().get(ROUTE, params={"site_id": "COLD-001"}).json() == {"site_id": "COLD-001", "scenarios": []}
    assert client().get(ROUTE, params={"site_id": "cold-lab-001"}).json()["scenarios"] == []
    unregistered = client(registered=Registered(codes=()))
    assert unregistered.get(ROUTE, params={"site_id": "COLD-LAB-001"}).json()["scenarios"] == []
    assert client(no_port=True).get(ROUTE, params={"site_id": "COLD-LAB-001"}).json()["scenarios"] == []


def test_an_unreadable_store_is_unavailable_not_empty() -> None:
    down = client(registered=Registered(failure=SiteStoreUnavailable("registration store down")))
    assert down.get(ROUTE, params={"site_id": "COLD-LAB-001"}).status_code == 503
    broken = client(scenarios=FakeScenarios(failure=ScenarioStoreUnavailable("scenario store down")))
    assert broken.get(ROUTE, params={"site_id": "COLD-LAB-001"}).status_code == 503


def test_site_id_is_required() -> None:
    assert client().get(ROUTE).status_code == 422


def test_the_legacy_catalog_stays_legacy_only() -> None:
    served = client()
    ids = [row["scenario_id"] for row in served.get("/api/simulator-lab/scenarios").json()["scenarios"]]
    assert not any(i.startswith("cold-") for i in ids) and ids
    assert served.get("/api/simulator-lab/scenarios/cold-normal").status_code == 404
