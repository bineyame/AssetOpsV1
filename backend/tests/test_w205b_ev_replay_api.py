"""W2-05b EV replay route and service over fakes (no database).

Mirrors `test_w202_cold_replay_api.py` for `GET /api/sites/{site_code}/ev/replay` (build spec commit 5, q4 "Final
commit 4-5" items 2-3). The registered Postgres proofs live in `test_w205b_ev_replay_postgres.py`; this file pins
the refusal ladder, the eight-field shape, the digest rule and the N1 `create_app` composition.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from run_fixtures import FakeRuns
from test_w205b_ev_scenarios import EV_SITE, composed, ev_request, ev_service

from assetops_backend.cold_replay_api import development_owner, no_owner_principal
from assetops_backend.evidence.ledger import LedgerUnavailable
from assetops_backend.ev_replay import EvReplayService
from assetops_backend.ev_replay_api import EV_REPLAY_ROUTE, build_ev_replay_router
from assetops_backend.finding_api import development_access
from assetops_backend.runs.ports import RunStoreUnavailable
from assetops_contracts.ingestion_batch_v2 import seal_batch_v2
from assetops_contracts.source_envelope import canonical_json
from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

TENANT = UUID("00000000-0000-4000-8000-0000000000a1")
SITE = UUID("00000000-0000-4000-8000-0000000000b1")
PUB_1 = "00000000-0000-4000-8000-000000000001"
PUB_2 = "00000000-0000-4000-8000-000000000002"
EV_1 = "00000000-0000-4000-8000-0000000000e1"
SHA = hashlib.sha256(b"snapshot").hexdigest()
URL = "/api/sites/EV-LAB-001/ev/replay"


def envelope(seq: int) -> str:
    return canonical_envelope_v3_text(SourceEnvelopeV3(
        message_id=v3_message_id(site_id="EV-LAB-001", gateway_id="gw", source_id="src", sequence_epoch="e",
                                 sequence=seq),
        sequence_epoch="e", sequence=seq, site_id="EV-LAB-001", gateway_id="gw", source_id="src",
        device_id="probe", signal_id="chamber_temperature", binding_set_id="bs", binding_version=1,
        source_time=f"2026-10-06T19:0{seq}:00Z", published_at=f"2026-10-06T19:0{seq}:00Z", interval_start=None,
        interval_end=None, family="MEASUREMENT", measurement="STATE_AT_INSTANT", value="3.5", unit="degC",
        quality="GOOD", unavailable_reason=None))


def batch(count: int):
    return seal_batch_v2(site_id="EV-LAB-001", gateway_id="gw", source_id="src", source_mode="SIMULATED",
                         foundation_version=1, foundation_valid_from="2026-10-01T00:00:00Z", binding_set_id="bs",
                         binding_version=1, snapshot_sha256=SHA, envelope_texts=[envelope(i + 1) for i in range(count)])


def publication(pub_id: str, sealed=None, **over) -> dict:
    if sealed is None:
        row = {"publication_id": pub_id, "p_tenant": str(TENANT), "p_site": str(SITE), "p_ext": "pending",
               "p_sha": "0" * 64, "l_batch": None, "b_id": None, "b_tenant": None, "b_site": None, "b_ext": None,
               "b_sha": None, "b_status": None, "b_total": None, "b_text": None}
    else:
        parsed, text = sealed
        row = {"publication_id": pub_id, "p_tenant": str(TENANT), "p_site": str(SITE), "p_ext": parsed.batch_id,
               "p_sha": parsed.payload_sha256, "l_batch": "batch-" + pub_id, "b_id": "batch-" + pub_id,
               "b_tenant": str(TENANT), "b_site": str(SITE), "b_ext": parsed.batch_id,
               "b_sha": parsed.payload_sha256, "b_status": "COMPLETED", "b_total": len(parsed.envelopes),
               "b_text": text}
    row.update(over)
    return row


class FakeReader:
    def __init__(self, publications=(), dispositions=(), *, failure=None, referenced=False) -> None:
        self.rows = {"publications": list(publications), "dispositions": list(dispositions)}
        self.failure = failure
        self.referenced = referenced

    def ev_replay_rows(self, tenant_id, site_id, run_id):
        if self.failure:
            raise self.failure
        return self.rows

    def ev_replay_run_referenced(self, tenant_id, site_id, run_id):
        return self.referenced


def ev_run(**basis_over):
    setup, store = ev_service()
    run = setup.create_draft_run(ev_request())
    assert run.execution_status == "READY", run.blocking_reasons
    basis = replace(run.registered_basis, **{"tenant_id": str(TENANT), "site_record_id": str(SITE), **basis_over})
    run = replace(run, registered_basis=basis)
    store.written[:] = [run]
    return run, store


def client(reader=None, runs=None, *, access=development_access, owner=development_owner, scope=None,
           service=True) -> TestClient:
    app = FastAPI()
    svc = EvReplayService(reader or FakeReader(), runs or FakeRuns()) if service else None
    app.include_router(build_ev_replay_router(
        svc, scope or (lambda code: ("EV-LAB-001", TENANT, SITE) if code.upper() == "EV-LAB-001" else None),
        access=access, owner=owner))
    return TestClient(app)


def test_route_shape_and_digest_from_dispositions() -> None:
    run, store = ev_run()
    sealed = batch(3)
    dispositions = [
        {"batch_id": "batch-" + PUB_1, "ordinal": 0, "decision": "ACCEPTED", "accepted_evidence_id": EV_1},
        {"batch_id": "batch-" + PUB_1, "ordinal": 1, "decision": "DUPLICATE", "accepted_evidence_id": EV_1},
        {"batch_id": "batch-" + PUB_1, "ordinal": 2, "decision": "CONFLICT", "accepted_evidence_id": None},
    ]
    reader = FakeReader([publication(PUB_1, sealed), publication(PUB_2)], dispositions)
    body = client(reader, store).get(URL, params={"run_id": run.run_id}).json()
    assert list(body) == ["publication_id", "publication_ids", "run_profile", "scenario_digest", "batch_ids",
                          "receipts", "accepted_record_ids", "public_digest"]
    assert body["publication_id"] == PUB_2 and body["publication_ids"] == [PUB_1, PUB_2]
    assert body["run_profile"] == {
        "model_profile": {"profile_id": "ev-charger", "profile_version": 1},
        "publication_profile": {"profile_id": "ev-publication", "profile_version": 1},
        "observation_profile": {"profile_id": "ev-observation", "profile_version": 1}}
    assert body["scenario_digest"] == run.deterministic_identity.scenario.scenario_sha256
    ext = sealed[0].batch_id
    assert body["batch_ids"] == [ext]
    assert body["receipts"] == [{"batch_id": ext, "accepted": 1, "duplicate": 1, "rejected": 0, "conflict": 1}]
    assert body["accepted_record_ids"] == [EV_1]
    digest_input = [[ext, i, hashlib.sha256(sealed[0].envelopes[i].encode()).hexdigest(), d, e]
                    for i, (d, e) in enumerate([("ACCEPTED", EV_1), ("DUPLICATE", EV_1), ("CONFLICT", None)])]
    assert body["public_digest"] == hashlib.sha256(canonical_json(digest_input).encode()).hexdigest()


def test_a_run_with_no_publications_is_empty_with_the_digest_of_an_empty_array() -> None:
    run, store = ev_run()
    body = client(FakeReader(), store).get(URL, params={"run_id": run.run_id}).json()
    assert body["publication_id"] is None and body["publication_ids"] == [] and body["batch_ids"] == []
    assert body["receipts"] == [] and body["accepted_record_ids"] == []
    assert body["public_digest"] == hashlib.sha256(b"[]").hexdigest()


@pytest.mark.parametrize("params", [{}, {"run_id": ""}, {"run_id": "a", "x": "1"}, {"other": "a"}, "run_id=a&run_id=b",
                                    {"run_id": "run-NOTHEX"}, {"run_id": "run-" + "0" * 31}])
def test_parameters_must_be_exactly_one_run_id(params) -> None:
    run, store = ev_run()
    response = client(FakeReader(), store).get(URL + ("?" + params if isinstance(params, str) else ""),
                                               params=None if isinstance(params, str) else params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EV_REPLAY_PARAMETER_INVALID"


def test_access_ladder() -> None:
    run, store = ev_run()
    q = {"run_id": run.run_id}
    assert client(runs=store, access=lambda r, s: 401).get(URL, params=q).status_code == 401
    forbidden = client(runs=store, access=lambda r, s: 403).get(URL, params=q)
    assert forbidden.status_code == 403 and forbidden.json()["error"]["code"] == "SITE_SCOPE_FORBIDDEN"
    # Production composition: the development access admits, but no owner principal exists -> 403.
    assert client(runs=store, owner=no_owner_principal).get(URL, params=q).status_code == 403
    missing_site = client(runs=store).get("/api/sites/OTHER-1/ev/replay", params=q)
    assert missing_site.status_code == 404 and missing_site.json()["error"]["code"] == "SITE_NOT_FOUND"
    missing_run = client(runs=store).get(URL, params={"run_id": "run-" + "0" * 32})
    assert missing_run.status_code == 404 and missing_run.json()["error"]["code"] == "RUN_NOT_FOUND"


@pytest.mark.parametrize("over", [{"tenant_id": "00000000-0000-4000-8000-0000000000ff"},
                                  {"site_record_id": "00000000-0000-4000-8000-0000000000ff"}])
def test_another_tenant_or_site_run_is_not_found(over) -> None:
    run, store = ev_run(**over)
    response = client(FakeReader(), store).get(URL, params={"run_id": run.run_id})
    assert response.status_code == 404 and response.json()["error"]["code"] == "RUN_NOT_FOUND"


def test_unavailable_cases_answer_503() -> None:
    run, store = ev_run()
    q = {"run_id": run.run_id}
    sealed = batch(2)
    one = [{"batch_id": "batch-" + PUB_1, "ordinal": 0, "decision": "ACCEPTED", "accepted_evidence_id": EV_1}]
    cases = [
        FakeReader(failure=LedgerUnavailable("down")),
        FakeReader([publication(PUB_1, sealed)], one),  # incomplete dispositions
        FakeReader([publication(PUB_1, sealed, b_status="IN_PROGRESS")], one),
        FakeReader([publication(PUB_1, sealed, b_text="{}")], one),
        FakeReader([publication(PUB_1, sealed, b_site=str(TENANT))], one),
        FakeReader([publication(PUB_1, sealed, b_id=None)], one),
    ]
    for reader in cases:
        response = client(reader, store).get(URL, params=q)
        assert response.status_code == 503 and response.json()["error"]["code"] == "EV_REPLAY_UNAVAILABLE"
    assert client(FakeReader(), FakeRuns(failure=RunStoreUnavailable("x"))).get(URL, params=q).status_code == 503
    assert client(FakeReader(referenced=True), FakeRuns()).get(URL, params=q).status_code == 503
    assert client(service=False).get(URL, params=q).status_code == 503


def test_a_non_ev_run_is_not_found() -> None:
    run, store = ev_run()
    profiles = replace(run.deterministic_identity.profiles, model_profile_id="other-model")
    store.written[:] = [replace(run, deterministic_identity=replace(run.deterministic_identity, profiles=profiles))]
    assert client(FakeReader(), store).get(URL, params={"run_id": run.run_id}).status_code == 404


def test_route_constant() -> None:
    assert EV_REPLAY_ROUTE == "/api/sites/{site_code}/ev/replay"


def test_composed_reader_exposes_only_the_two_select_reads() -> None:
    # W2-05b, as W2-02 review L5: the composed reader is narrowed; no ledger writer is reachable through it.
    from assetops_backend.evidence.composition import build_ev_replay_reader

    reader = build_ev_replay_reader("postgresql+psycopg://unused@127.0.0.1:1/never_test")
    public = {name for name in dir(reader) if not name.startswith("_")}
    assert public == {"ev_replay_rows", "ev_replay_run_referenced"}


def test_a_repeated_valid_run_id_is_refused() -> None:
    run, store = ev_run()
    repeated = client(FakeReader(), store).get(URL + f"?run_id={run.run_id}&run_id={run.run_id}")
    assert repeated.status_code == 422


# --- N1: `create_app` passes its injected `ev_access`/`ev_owner` to the EV replay router -----------------------

RUN = "run-" + "0" * 32
EV_URL = f"/api/sites/{EV_SITE}/ev/replay"


def test_the_default_composition_refuses_the_ev_replay_without_an_owner_principal() -> None:
    response = composed().get(EV_URL, params={"run_id": RUN})
    assert response.status_code == 403 and response.json()["error"]["code"] == "SITE_SCOPE_FORBIDDEN"


def test_an_injected_site_scoped_owner_passes_the_gate_only_for_its_site() -> None:
    owner = composed(ev_access=lambda request, code: None, ev_owner=lambda request, code: code == EV_SITE)
    # Past 401/403/422 for its Site: no ledger is configured in this composition, so the next step is 503.
    passed = owner.get(EV_URL, params={"run_id": RUN})
    assert passed.status_code == 503 and passed.json()["error"]["code"] == "EV_REPLAY_UNAVAILABLE"
    for other in ("MG-001", "COLD-LAB-001"):
        wrong_site = owner.get(f"/api/sites/{other}/ev/replay", params={"run_id": RUN})
        assert wrong_site.status_code == 403 and wrong_site.json()["error"]["code"] == "SITE_SCOPE_FORBIDDEN"
    unauthenticated = composed(ev_access=lambda request, code: 401, ev_owner=lambda request, code: True)
    response = unauthenticated.get(EV_URL, params={"run_id": RUN})
    assert response.status_code == 401 and response.json()["error"]["code"] == "UNAUTHENTICATED"
