"""W2-02 commit (2): the cold-only freeze and its run-identity round trip.

`D-2026-10-17-w2-02-buildspec` "Scenario and observation documents" and "Lab choice and run-request
closure": a cold document freezes only for its registered Site with the exact request it fixes, the four
cold identity keys render only for a cold run (omit, never null, for every older run) and round-trip, and
a malformed digest is refused on read.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
import yaml
from run_fixtures import FakeRuns, FakeScenarios, FakeSites, model_profile, publication_profile, scenario, site

from assetops_backend.runs.models import RegisteredBasis
from assetops_backend.runs.parsing import parse_run_document, render_run_document
from assetops_backend.runs.ports import RegisteredSiteSelection, RunConfigurationInvalid
from assetops_backend.runs.profiles import COLD_PUBLICATION_PROFILE, COLD_THERMAL_MODEL
from assetops_backend.runs.refusals import RunSetupRefused
from assetops_backend.runs.service import RunSetupService
from assetops_backend.runs.source_publication import run_identity_sha256
from assetops_backend.scenarios.cold_parsing import parse_cold_scenario_document

SCENARIOS = Path(__file__).resolve().parents[2] / "config" / "scenarios"
COLD_SITE = "COLD-LAB-001"
SNAPSHOT = '{"bindings":[]}'


def cold_definition(case: str = "normal"):
    document = yaml.safe_load((SCENARIOS / f"cold-{case}.yaml").read_text(encoding="utf-8"))
    return parse_cold_scenario_document(document)


def basis() -> RegisteredBasis:
    return RegisteredBasis(
        tenant_id="tenant-1", site_record_id="site-record-1", foundation_revision_id="foundation-rev-1",
        foundation_version=1, foundation_valid_from="2026-10-01T00:00:00Z", foundation_valid_to=None,
        foundation_content_sha256="c" * 64, binding_set_id="binding-set-1",
        binding_set_revision_id="binding-rev-v4", binding_set_version=2,
        binding_valid_from="2026-10-01T00:01:00Z", binding_valid_to=None, snapshot_schema="snapshot/1",
        snapshot_sha256=hashlib.sha256(SNAPSHOT.encode("utf-8")).hexdigest(), snapshot_canonical=SNAPSHOT,
        source_start="2026-10-06T19:00:00Z", knowledge_at="2026-10-06T19:00:00Z",
        site_display_name="Cold replay lab", selection="CURRENT",
    )


class FakeRegistered:
    def __init__(self, site_id: str = COLD_SITE) -> None:
        self._site = site(site_id=site_id)

    def registered(self, site_id: str) -> bool:
        return site_id == self._site.site_id

    def select(self, site_id, *, start_time, end_time, knowledge_at) -> RegisteredSiteSelection:
        return RegisteredSiteSelection(site=self._site, signal_mappings=(), basis=basis())


def cold_service(*, registered=True, case: str = "normal") -> tuple[RunSetupService, FakeRuns]:
    store = FakeRuns()
    return (
        RunSetupService(
            store,
            FakeSites((site(), site(site_id=COLD_SITE))),
            FakeScenarios((scenario(), cold_definition(case))),
            model_profiles=(model_profile(), COLD_THERMAL_MODEL),
            publication_profiles=(publication_profile(), COLD_PUBLICATION_PROFILE),
            now=lambda: "2026-10-06T18:00:00Z",
            registered_bases=FakeRegistered() if registered else None,
        ),
        store,
    )


def cold_request(case: str = "normal", **overrides) -> dict:
    request = {
        "site_id": COLD_SITE,
        "foundation_version": 1,
        "scenario_id": f"cold-{case}",
        "scenario_version": 1,
        "interval": {"start_time": "2026-10-06T19:00:00Z", "end_time": "2026-10-06T20:00:00Z"},
        "timestep_minutes": 1,
        "seed": 20417,
        "model_profile": {"profile_id": "cold-thermal", "profile_version": 1},
        "publication_profile": {"profile_id": "cold-publication", "profile_version": 1},
        "run_inputs": [],
    }
    request.update(overrides)
    return request


def expected_observation_sha256(observations: list) -> str:
    text = json.dumps({"observation_profile": "cold-observation/1", "observations": observations},
                      sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


COLD_KEYS_SCENARIO = ("scenario_sha256",)
COLD_KEYS_PROFILES = ("observation_profile_id", "observation_profile_version", "observation_sha256")


def test_cold_run_freezes_digests_and_round_trips() -> None:
    setup, store = cold_service()
    run = setup.create_draft_run(cold_request())
    assert run.execution_status == "READY" and store.written == [run]
    identity = run.deterministic_identity
    definition = cold_definition()
    assert identity.scenario.scenario_sha256 == definition.scenario_sha256
    assert identity.profiles.observation_profile_id == "cold-observation"
    assert identity.profiles.observation_profile_version == 1
    assert identity.profiles.observation_sha256 == expected_observation_sha256([])
    assert run.registered_basis == basis()
    assert identity.forcings == () and identity.initialization_inputs == ()

    document = render_run_document(run)
    rendered = document["deterministic_identity"]
    assert rendered["scenario"]["scenario_sha256"] == definition.scenario_sha256
    assert all(key in rendered["profiles"] for key in COLD_KEYS_PROFILES)
    again = parse_run_document(json.loads(json.dumps(document)), source="test")
    assert again == run
    assert run_identity_sha256(again) == run_identity_sha256(run)


def test_observation_digest_covers_rows_in_order() -> None:
    setup, _ = cold_service(case="missing-probe")
    run = setup.create_draft_run(cold_request("missing-probe"))
    rows = [
        {"at": f"2026-10-06T19:{m}:00Z", "kind": "PROBE_REPORT", "device_id": "probe-1", "action": "DROP",
         "outcome": None, "release_at": None}
        for m in ("15", "20", "25", "30", "35", "40")
    ]
    assert run.deterministic_identity.profiles.observation_sha256 == expected_observation_sha256(rows)
    normal, _ = cold_service()
    other = normal.create_draft_run(cold_request())
    assert run_identity_sha256(replace(other, run_id=run.run_id, created_at=run.created_at)) != (
        run_identity_sha256(run)
    )


def test_legacy_run_omits_the_cold_keys() -> None:
    setup, _ = cold_service()
    from run_fixtures import setup_request

    run = setup.create_draft_run(setup_request())
    rendered = render_run_document(run)["deterministic_identity"]
    assert not any(key in rendered["scenario"] for key in COLD_KEYS_SCENARIO)
    assert not any(key in rendered["profiles"] for key in COLD_KEYS_PROFILES)
    assert parse_run_document(render_run_document(run), source="test") == run


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d["scenario"].__setitem__("scenario_sha256", "A" * 64),
        lambda d: d["profiles"].__setitem__("observation_sha256", "a" * 63),
        lambda d: d["profiles"].pop("observation_profile_id"),
        lambda d: d["scenario"].pop("scenario_sha256"),
        lambda d: d["profiles"].__setitem__("observation_sha256", None),
    ],
)
def test_a_bad_cold_digest_is_refused_on_read(mutate) -> None:
    setup, _ = cold_service()
    document = json.loads(json.dumps(render_run_document(setup.create_draft_run(cold_request()))))
    mutate(document["deterministic_identity"])
    with pytest.raises(RunConfigurationInvalid):
        parse_run_document(document, source="test")


@pytest.mark.parametrize(
    ("overrides", "kind"),
    [
        ({"seed": 1}, "REQUEST_INVALID"),
        ({"timestep_minutes": 5}, "INTERVAL_INVALID"),
        ({"interval": {"start_time": "2026-10-06T19:00:00Z", "end_time": "2026-10-06T19:30:00Z"}},
         "INTERVAL_INVALID"),
        ({"scenario_version": 2}, "VERSION_UNAVAILABLE"),
        ({"model_profile": {"profile_id": "example-model", "profile_version": 1}}, "VERSION_UNAVAILABLE"),
        ({"publication_profile": {"profile_id": "example-publication", "profile_version": 1}},
         "VERSION_UNAVAILABLE"),
    ],
)
def test_a_request_that_differs_from_the_document_is_refused_before_draft(overrides, kind) -> None:
    setup, store = cold_service()
    with pytest.raises(RunSetupRefused) as raised:
        setup.create_draft_run(cold_request(**overrides))
    assert raised.value.kind == kind
    assert store.written == []


def test_a_cold_document_never_freezes_against_a_legacy_or_other_site() -> None:
    setup, store = cold_service(registered=False)
    with pytest.raises(RunSetupRefused) as raised:
        setup.create_draft_run(cold_request())
    assert raised.value.kind == "VERSION_UNAVAILABLE" and store.written == []
    setup, store = cold_service()
    with pytest.raises(RunSetupRefused):
        setup.create_draft_run(cold_request(site_id="MG-900"))
    assert store.written == []


@pytest.mark.parametrize(
    ("model_id", "publication_id"),
    [("cold-thermal", "cold-publication"), ("cold-thermal", "example-publication"),
     ("example-model", "cold-publication")],
)
def test_a_cold_profile_with_a_legacy_scenario_is_refused_before_draft(model_id, publication_id) -> None:
    from run_fixtures import setup_request

    setup, store = cold_service()
    request = setup_request()
    request["model_profile"] = {"profile_id": model_id, "profile_version": 1}
    request["publication_profile"] = {**request["publication_profile"], "profile_id": publication_id,
                                      "profile_version": 1}
    with pytest.raises(RunSetupRefused) as raised:
        setup.create_draft_run(request)
    assert raised.value.kind == "VERSION_UNAVAILABLE"
    assert "Cold-chain profiles run only from a cold-scenario/1 document" in str(raised.value)
    assert store.written == []


def test_legacy_run_identity_golden_vector_unchanged() -> None:
    """Pinned from `main` before W2-02: the cold keys change no older run's identity bytes."""
    from run_fixtures import setup_request

    setup, _ = cold_service()
    run = replace(setup.create_draft_run(setup_request()), run_id="11111111-1111-4111-8111-111111111111",
                  created_at="2026-09-21T09:00:00Z")
    assert run_identity_sha256(run) == "0db30ea953d46f282010a1f3b5dd3a61294543b5ce67df63a461be99dddd0bd5"
