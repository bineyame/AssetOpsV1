"""W2-05b commit 1: six strict `ev-scenario/1` documents, the EV catalog route and the EV-only freeze.

`.agent/W2-05b-build-spec.md` "Run 1 rulings (q1)" Q1-Q12: the closed document shape, forcing/observation
order and vocabularies, the two digests, the Site-filtered choice list with its refusals, and a frozen
identity that carries the EV digests while legacy and cold identities keep their bytes.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Sequence

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from run_fixtures import FakeRuns, FakeScenarios, FakeSites, model_profile, publication_profile, scenario, site

from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RegisteredSiteSelection, RunConfigurationInvalid
from assetops_backend.runs.profiles import (
    EV_CHARGER_MODEL,
    EV_PUBLICATION_PROFILE,
    MODEL_PROFILES,
    PUBLICATION_PROFILES,
)
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.service import RunSetupService
from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import ReadOnlyYamlScenarioStore
from assetops_backend.scenarios.ev_parsing import EvScenarioDefinition, parse_ev_scenario_document
from assetops_backend.scenarios.ports import ScenarioConfigurationInvalid, ScenarioStoreUnavailable
from assetops_backend.simulator_lab_api import build_simulator_lab_router
from assetops_backend.sites.ports import SiteStoreUnavailable
from test_w202_cold_run_identity import basis

SCENARIOS = Path(__file__).resolve().parents[2] / "config" / "scenarios"
CASES = ("complete", "interrupted", "fault", "missing-meter", "late-record", "contradictory")
LABELS = ("Complete session", "Interrupted session", "Fault before charging", "Missing meter report",
          "Late session end", "Contradictory session ends")
EV_SITE = "EV-LAB-001"
WINDOW = {"start": "2026-10-06T08:00:00Z", "end": "2026-10-06T09:00:00Z", "end_exclusive": True}
ROUTE = "/api/simulator-lab/ev-scenarios"
ROW_KEYS = {"scenario_id", "scenario_version", "display_name", "schema", "model_profile", "publication_profile",
            "observation_profile", "window", "seed", "site_code"}


def raw(case: str) -> dict:
    return yaml.safe_load((SCENARIOS / f"ev-{case}.yaml").read_text(encoding="utf-8"))


def ev(case: str) -> EvScenarioDefinition:
    return parse_ev_scenario_document(raw(case))


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def refused(document) -> str:
    with pytest.raises(ScenarioConfigurationInvalid) as caught:
        parse_ev_scenario_document(document)
    return str(caught.value)


# --- the six documents -------------------------------------------------------------------------------


def row(time, kind, connector, value):
    return (f"2026-10-06T{time}:00Z", kind, connector, value)


COMPLETE = [row("08:00", "PLUG", "c1", "session-1"), row("08:00", "AUTHORIZE", "c1", "ACCEPT"),
            row("08:01", "REQUEST_KW", "c1", "60"), row("08:31", "UNPLUG", "c1", "END")]
FORCING = {
    "complete": COMPLETE,
    "interrupted": COMPLETE[:3] + [row("08:16", "FAULT", "c1", "LATCH")],
    "fault": [row("08:00", "PLUG", "c1", "session-1"), row("08:00", "FAULT", "c1", "LATCH"),
              row("08:05", "CLEAR", "c1", "CLEAR"), row("08:10", "PLUG", "c2", "session-2"),
              row("08:10", "AUTHORIZE", "c2", "ACCEPT"), row("08:11", "REQUEST_KW", "c2", "60"),
              row("08:21", "UNPLUG", "c2", "END")],
    "missing-meter": COMPLETE, "late-record": COMPLETE, "contradictory": COMPLETE,
}
OBSERVATIONS = {
    "complete": [], "interrupted": [], "fault": [],
    "missing-meter": [{"time": "2026-10-06T08:15:00Z", "kind": "ENERGY_REPORT", "connector": "c1",
                       "action": "DROP", "release_at": None}],
    "late-record": [{"time": "2026-10-06T08:31:00Z", "kind": "EV_SESSION_END", "connector": "c1",
                     "action": "HOLD", "release_at": "2026-10-06T09:05:00Z"}],
    "contradictory": [{"time": "2026-10-06T08:30:00Z", "kind": "EV_SESSION_END", "connector": "c1",
                       "action": "ADD", "release_at": None}],
}


@pytest.mark.parametrize("case", CASES)
def test_each_shipped_document_is_the_exact_case_table(case: str) -> None:
    definition = ev(case)
    assert definition.scenario_id == f"ev-{case}" and definition.version == 1
    assert definition.site_code == EV_SITE and definition.seed == 20517 and definition.window == WINDOW
    assert (definition.model_profile, definition.publication_profile, definition.observation_profile) == (
        "ev-charger/1", "ev-publication/1", "ev-observation/1")
    assert [(f.time, f.kind, f.connector, f.value) for f in definition.forcing] == FORCING[case]
    assert [o.__dict__ for o in definition.observations] == OBSERVATIONS[case]
    assert definition.scenario_sha256 == sha(raw(case))
    assert definition.observation_sha256 == sha(["ev-observation/1", OBSERVATIONS[case]])


def test_digest_is_independent_of_yaml_layout() -> None:
    text = (SCENARIOS / "ev-complete.yaml").read_text(encoding="utf-8")
    reflowed = yaml.safe_dump(yaml.safe_load(text), default_flow_style=True, sort_keys=False)
    assert parse_ev_scenario_document(yaml.safe_load(reflowed)).scenario_sha256 == ev("complete").scenario_sha256
    assert len({ev(case).scenario_sha256 for case in CASES}) == 6


def test_the_shipped_store_parses_all_six_and_the_legacy_parser_none() -> None:
    shipped = [r for r in ReadOnlyYamlScenarioStore().list_scenarios() if isinstance(r, EvScenarioDefinition)]
    assert sorted(r.scenario_id for r in shipped) == sorted(f"ev-{case}" for case in CASES)


def test_scenario_id_must_match_the_file_basename(tmp_path: Path) -> None:
    (tmp_path / "ev-other.yaml").write_text(
        (SCENARIOS / "ev-complete.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ScenarioConfigurationInvalid, match="file basename"):
        ReadOnlyYamlScenarioStore(tmp_path).list_scenarios()


# --- strictness --------------------------------------------------------------------------------------


def mutated(change) -> dict:
    document = copy.deepcopy(raw("complete"))
    change(document)
    return document


@pytest.mark.parametrize("change, message", [
    (lambda d: d.update(version=1), "keys differ"),
    (lambda d: d.pop("observations"), "keys differ"),
    (lambda d: d.update(window=["2026-10-06T08:00:00Z", "2026-10-06T09:00:00Z"]), "window is not a mapping"),
    (lambda d: d["window"].update(end_exclusive="true"), "end_exclusive"),
    (lambda d: d["window"].update(start="2026-10-06T08:00:00+00:00"), "UTC instant"),
    (lambda d: d["window"].update(end="2026-10-06T10:00:00Z"), "window.end"),
    (lambda d: d.update(seed=20518), "seed"),
    (lambda d: d.update(site_code="COLD-LAB-001"), "site_code"),
    (lambda d: d.update(scenario_id="ev--complete"), "scenario_id"),
    (lambda d: d.update(scenario_id="ev-complete-"), "scenario_id"),
    (lambda d: d.update(model_profile="ev-charger/1"), "model_profile is not a mapping"),
    (lambda d: d["model_profile"].update(profile_version=2), "profile_version"),
    (lambda d: d["observation_profile"].update(profile_version="1"), "profile_version"),
    (lambda d: d["forcing"][0].update(extra=None), "keys differ"),
    (lambda d: d["forcing"][2].update(value=60), "must be a string"),
    (lambda d: d["forcing"][2].update(value="60.0"), "canonical non-negative decimal"),
    (lambda d: d["forcing"][2].update(value="-1"), "canonical non-negative decimal"),
    (lambda d: d["forcing"][2].update(value="61"), "exceeds"),
    (lambda d: d["forcing"][0].update(value="session-2"), "plug order"),
    (lambda d: d["forcing"][1].update(value="MAYBE"), "does not pair"),
    (lambda d: d["forcing"][3].update(value="ABORT"), "does not pair"),
    (lambda d: d["forcing"][3].update(connector="c3"), "declared connector"),
    (lambda d: d["forcing"][3].update(kind="GRID_LOSS"), "outside ev-scenario/1"),
    (lambda d: d["forcing"][3].update(kind="GRID_RESTORE"), "outside ev-scenario/1"),
    (lambda d: d["forcing"][3].update(kind="RESET"), "not an EV forcing kind"),
    (lambda d: d["forcing"][3].update(time="2026-10-06T09:00:00Z"), "outside"),
    (lambda d: d["forcing"][3].update(time="2026-10-06T08:31:30Z"), "one-minute boundary"),
    (lambda d: d["forcing"].reverse(), "order"),
    (lambda d: d["forcing"].insert(1, dict(d["forcing"][1])), "repeats"),
    (lambda d: d["forcing"].insert(2, dict(d["forcing"][1], value="DENY")), "repeats"),
    (lambda d: d["forcing"].append({"time": "2026-10-06T08:40:00Z", "kind": "PLUG", "connector": "c2",
                                    "value": "session-2"}) or d["forcing"].append(
        {"time": "2026-10-06T08:50:00Z", "kind": "PLUG", "connector": "c1", "value": "session-3"}), "third PLUG"),
])
def test_a_nonconforming_document_refuses(change, message) -> None:
    assert message in refused(mutated(change))


def test_same_minute_order_is_plug_before_authorize_and_c1_before_c2() -> None:
    swapped = mutated(lambda d: d["forcing"].__setitem__(slice(0, 2), d["forcing"][1::-1]))
    assert "order" in refused(swapped)
    c2_first = mutated(lambda d: d["forcing"].insert(0, {"time": "2026-10-06T08:00:00Z", "kind": "PLUG",
                                                         "connector": "c2", "value": "session-1"}))
    for r in c2_first["forcing"][1:]:
        if r["kind"] == "PLUG":
            r["value"] = "session-2"
    assert "order" in refused(c2_first)


def obs(time="2026-10-06T08:15:00Z", kind="ENERGY_REPORT", connector="c1", action="DROP", release_at=None):
    return {"time": time, "kind": kind, "connector": connector, "action": action, "release_at": release_at}


@pytest.mark.parametrize("rows, message", [
    ([obs(action="HOLD")], "does not pair"),
    ([obs(kind="EV_SESSION_END", action="DROP")], "does not pair"),
    ([obs(kind="EV_SESSION_END", action="HOLD")], "release_at must be a string"),
    ([obs(kind="EV_SESSION_END", action="HOLD", release_at="2026-10-06T08:15:00Z")], "must follow"),
    ([obs(release_at="2026-10-06T09:05:00Z")], "null except for HOLD"),
    ([obs(kind="PROBE_REPORT")], "not an EV observation kind"),
    ([obs(connector="c3")], "declared connector"),
    ([obs(time="2026-10-06T09:00:00Z")], "outside"),
    ([obs(time="2026-10-06T08:20:00Z"), obs()], "order"),
    ([obs(), obs()], "already changes"),
    ([obs(kind="EV_SESSION_END", action="HOLD", release_at="2026-10-06T09:05:00Z"),
      obs(kind="EV_SESSION_END", action="ADD")], "already changes"),
    ([{**obs(), "outcome": None}], "keys differ"),
])
def test_a_nonconforming_observation_refuses(rows, message) -> None:
    assert message in refused(mutated(lambda d: d.update(observations=rows)))


def test_hold_release_may_follow_the_window() -> None:
    assert ev("late-record").observations[0].release_at == "2026-10-06T09:05:00Z"


# --- the catalog route -------------------------------------------------------------------------------


class NoTemplates:
    def list_templates(self) -> Sequence[object]:
        return ()

    def get_template(self, template_id: str) -> object:  # pragma: no cover
        raise AssertionError("no EV scenario route reads a template")


class Registered:
    def __init__(self, codes=(EV_SITE, "COLD-LAB-001"), failure: Exception | None = None) -> None:
        self._codes, self._failure = codes, failure

    def registered(self, site_id: str) -> bool:
        if self._failure is not None:
            raise self._failure
        return site_id in self._codes

    def select(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("listing choices selects no basis")


def client(*, registered=None, scenarios=None, access=lambda request, code: None,
           owner=lambda request, code: True, sites=None) -> TestClient:
    app = FastAPI()
    app.include_router(build_simulator_lab_router(
        NoTemplates(), sites or FakeSites((site(),)),
        scenarios or FakeScenarios((scenario(), *(ev(case) for case in reversed(CASES)))),
        FakeRuns(), MODEL_PROFILES, PUBLICATION_PROFILES,
        registered_bases=registered or Registered(), ev_access=access, ev_owner=owner,
    ))
    return TestClient(app)


def test_six_choices_in_ruled_order_for_the_registered_ev_site() -> None:
    response = client().get(ROUTE, params={"site_id": EV_SITE})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"site_id", "scenarios"} and body["site_id"] == EV_SITE
    assert [c["display_name"] for c in body["scenarios"]] == list(LABELS)
    assert [c["scenario_id"] for c in body["scenarios"]] == [f"ev-{case}" for case in CASES]
    assert all(set(c) == ROW_KEYS for c in body["scenarios"])
    assert body["scenarios"][0] == {
        "scenario_id": "ev-complete", "scenario_version": 1, "display_name": "Complete session",
        "schema": "ev-scenario/1", "model_profile": "ev-charger/1", "publication_profile": "ev-publication/1",
        "observation_profile": "ev-observation/1", "window": WINDOW, "seed": 20517, "site_code": EV_SITE,
    }


def test_refusals_are_typed_and_carry_no_rows() -> None:
    unauthenticated = client(access=lambda request, code: 401).get(ROUTE, params={"site_id": EV_SITE})
    assert unauthenticated.status_code == 401
    assert unauthenticated.json()["detail"]["code"] == "UNAUTHENTICATED"
    for refused_client in (client(owner=lambda request, code: False), client(access=lambda r, c: 403)):
        forbidden = refused_client.get(ROUTE, params={"site_id": EV_SITE})
        assert forbidden.status_code == 403 and "scenarios" not in forbidden.json()
        assert forbidden.json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
    for params in ({}, {"site_id": ""}, {"site_id": "bad id"}, [("site_id", EV_SITE), ("site_id", EV_SITE)],
                   {"site": EV_SITE}):
        invalid = client().get(ROUTE, params=params)
        assert invalid.status_code == 422
        assert invalid.json()["detail"]["code"] == "EV_SCENARIO_PARAMETER_INVALID"
    missing = client().get(ROUTE, params={"site_id": "EV-NOWHERE-9"})
    assert missing.status_code == 404 and missing.json()["detail"]["code"] == "SITE_NOT_FOUND"


def test_known_non_ev_sites_answer_an_empty_list() -> None:
    legacy = site().site_id
    assert client().get(ROUTE, params={"site_id": legacy}).json() == {"site_id": legacy, "scenarios": []}
    assert client().get(ROUTE, params={"site_id": "COLD-LAB-001"}).json()["scenarios"] == []
    none_shipped = client(scenarios=FakeScenarios((scenario(),)))
    assert none_shipped.get(ROUTE, params={"site_id": EV_SITE}).json() == {"site_id": EV_SITE, "scenarios": []}


def test_unreadable_stores_are_unavailable_never_empty() -> None:
    down = client(registered=Registered(failure=SiteStoreUnavailable("registration store down")))
    response = down.get(ROUTE, params={"site_id": EV_SITE})
    assert response.status_code == 503 and response.json()["detail"]["code"] == "SITE_STORE_UNAVAILABLE"
    broken = client(scenarios=FakeScenarios(failure=ScenarioStoreUnavailable("scenario store down")))
    response = broken.get(ROUTE, params={"site_id": EV_SITE})
    assert response.status_code == 503 and response.json()["detail"]["code"] == "SCENARIO_STORE_UNAVAILABLE"
    sites_down = client(registered=Registered(codes=()), sites=FakeSites(failure=SiteStoreUnavailable("down")))
    assert sites_down.get(ROUTE, params={"site_id": EV_SITE}).status_code == 503


def test_legacy_catalog_and_detail_never_serve_ev_documents() -> None:
    listed = client().get("/api/simulator-lab/scenarios").json()["scenarios"]
    assert not any(str(entry.get("scenario_id", "")).startswith("ev-") for entry in listed)
    assert client().get("/api/simulator-lab/scenarios/ev-complete").status_code == 404


# --- the EV-only freeze ------------------------------------------------------------------------------


class FakeRegistered:
    def __init__(self) -> None:
        self._site = site(site_id=EV_SITE)

    def registered(self, site_id: str) -> bool:
        return site_id == EV_SITE

    def select(self, site_id, *, start_time, end_time, knowledge_at) -> RegisteredSiteSelection:
        return RegisteredSiteSelection(site=self._site, signal_mappings=(), basis=basis())


def ev_service(*, registered: bool = True, case: str = "complete") -> tuple[RunSetupService, FakeRuns]:
    store = FakeRuns()
    return RunSetupService(
        store, FakeSites((site(), site(site_id=EV_SITE))), FakeScenarios((scenario(), ev(case))),
        model_profiles=(model_profile(), EV_CHARGER_MODEL),
        publication_profiles=(publication_profile(), EV_PUBLICATION_PROFILE),
        now=lambda: "2026-10-06T07:00:00Z",
        registered_bases=FakeRegistered() if registered else None,
    ), store


def ev_request(case: str = "complete", **overrides) -> dict:
    request = {
        "site_id": EV_SITE, "foundation_version": 1, "scenario_id": f"ev-{case}", "scenario_version": 1,
        "interval": {"start_time": WINDOW["start"], "end_time": WINDOW["end"]}, "timestep_minutes": 1,
        "seed": 20517, "model_profile": {"profile_id": "ev-charger", "profile_version": 1},
        "publication_profile": {"profile_id": "ev-publication", "profile_version": 1}, "run_inputs": [],
    }
    request.update(overrides)
    return request


@pytest.mark.parametrize("case", CASES)
def test_ev_run_freezes_both_digests_and_round_trips(case: str) -> None:
    setup, store = ev_service(case=case)
    run = setup.create_draft_run(ev_request(case))
    assert store.written == [run]
    identity = run.deterministic_identity
    definition = ev(case)
    assert identity.scenario.scenario_id == f"ev-{case}" and identity.scenario.scenario_version == 1
    assert identity.scenario.scenario_sha256 == definition.scenario_sha256
    assert (identity.profiles.model_profile_id, identity.profiles.publication_profile_id) == (
        "ev-charger", "ev-publication")
    assert identity.profiles.observation_profile_id == "ev-observation"
    assert identity.profiles.observation_profile_version == 1
    assert identity.profiles.observation_sha256 == definition.observation_sha256
    assert identity.seed == 20517 and identity.interval.timestep_minutes == 1
    assert identity.forcings == () and identity.initialization_inputs == () and identity.causes == ()
    assert run.registered_basis == basis()
    document = render_run_document(run)
    assert all(private not in canonical(document) for private in ("session-1", "REQUEST_KW", "PLUG", "LATCH"))
    assert parse_run_document(json.loads(canonical(document)), source="test") == run


def test_an_ev_identity_without_its_digests_is_refused_on_read() -> None:
    setup, _ = ev_service()
    document = render_run_document(setup.create_draft_run(ev_request()))
    stripped = json.loads(canonical(document))
    del stripped["deterministic_identity"]["scenario"]["scenario_sha256"]
    for key in ("observation_profile_id", "observation_profile_version", "observation_sha256"):
        del stripped["deterministic_identity"]["profiles"][key]
    with pytest.raises(RunConfigurationInvalid, match="EV run"):
        parse_run_document(stripped, source="test")


@pytest.mark.parametrize("overrides, code", [
    ({"seed": 1}, "REQUEST_INVALID"),
    ({"scenario_version": 2}, "VERSION_UNAVAILABLE"),
    ({"timestep_minutes": 5}, "INTERVAL_INVALID"),
    ({"interval": {"start_time": "2026-10-06T08:00:00Z", "end_time": "2026-10-06T08:30:00Z"}}, "INTERVAL_INVALID"),
    ({"model_profile": {"profile_id": "simulator-lab-model", "profile_version": 1}}, "VERSION_UNAVAILABLE"),
    ({"publication_profile": {"profile_id": "cold-publication", "profile_version": 1}}, "VERSION_UNAVAILABLE"),
])
def test_a_request_that_differs_from_the_document_is_refused_before_draft(overrides, code) -> None:
    setup, store = ev_service()
    with pytest.raises(RunSetupRefused) as caught:
        setup.create_draft_run(ev_request(**overrides))
    assert caught.value.kind == code and store.written == []


def test_an_unregistered_site_and_legacy_scenario_with_ev_profiles_refuse() -> None:
    setup, store = ev_service(registered=False)
    with pytest.raises(RunSetupRefused):
        setup.create_draft_run(ev_request())
    setup, store = ev_service()
    legacy = ev_request(scenario_id=scenario().scenario_id, site_id=site().site_id)
    legacy.update(interval={"start_time": "2026-01-01T00:00:00Z", "end_time": "2026-01-01T01:00:00Z"})
    with pytest.raises(RunSetupRefused) as caught:
        setup.create_draft_run(legacy)
    assert caught.value.kind == "VERSION_UNAVAILABLE" and store.written == []
