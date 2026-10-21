"""W4-03 unit 2b: persisted mini scenarios over Postgres (`.agent/W4-03-build-spec.md` closure 1 Q1-Q3/Q12-Q16,
closure 2 Q1, closure 4 B2/S5/S9/S10/S15/S20/N6/N8, u2 narrative, u2b readings).

The MG-W402-001 authored cases are accepted in process and selected by the W4-02 worker's `reconcile`, as in
`test_w402_reads_postgres.py`. Scenario commands go through `create_app` with the two explicit W4-03 injections; the
list is read from a fresh app (a fresh request). Router-only refusal vectors use a stub registry.
"""

from __future__ import annotations

import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_w402_authored_v4_postgres import cases, ingestion, principal, snapshot
    from test_w402_reads_postgres import CODE, DAYS, ZONE, _ingest, _midnight, _read, _reconcile, _setup

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal, DecisionRefused
    from assetops_backend.mini_decisions.scenarios import ScenarioService, decode_cursor, encode_cursor, parse_list
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions_api import build_mini_decisions_router
    from assetops_backend.mini_depth import projection
    from assetops_backend.mini_depth.inputs import load_hour_inputs, local_noon
    from assetops_backend.mini_depth.read import MiniDepthRead, renewable_revisions
    from assetops_backend.mini_depth.store import PostgresMiniDepthStore

PRINCIPAL_ID = "service:w403-fixture"
ATTESTATION = "service=w403-fixture;job=positive-decisions;rule=w403/1"
ROUTE = f"/api/sites/{CODE}/financials/scenarios"
WRITE_KEYS = {"schema_version", "id", "code", "revision_id", "revision_no", "supersedes_revision_id", "recorded_at"}
ROW_KEYS = {"id", "code", "revision_id", "name", "kind", "narrative", "authored_at", "actor_id", "assumptions",
            "pinned_mini_revision_ids", "scenario_state", "calculation_state", "energy_kwh", "gross_sales",
            "limitations", "url"}


def actor(**overrides):
    return {"kind": "SERVICE", "id": PRINCIPAL_ID, "attestation": ATTESTATION, **overrides}


def principal_for(t, s) -> DecisionPrincipal:
    return DecisionPrincipal("SERVICE", PRINCIPAL_ID, t, s, GRANT_PREFIX + PRINCIPAL_ID)


def load_command(key, pins, narrative="Illustrative productive-load trial.", **extra):
    body = {"schema_version": "mini-scenario-command-1", "idempotency_key": key, "actor": actor(),
            "name": "Grain mill one-hour trial", "kind": "PRODUCTIVE_LOAD",
            "assumptions": [{"key": "proposed_kw", "value": "0.001", "unit": "kW", "source": "Authored trial"},
                            {"key": "duration_hours", "value": "1", "unit": "h", "source": "Authored trial"},
                            {"key": "tariff_per_kwh", "value": "0.25", "unit": "USD/kWh", "source": "Authored"}],
            "pinned_selection": pins, "narrative": narrative}
    body.update(extra)
    return body


def tariff_command(key, narrative="Tariff only.", **extra):
    return {**load_command(key, [], narrative), "kind": "TARIFF_ONLY",
            "assumptions": [{"key": "tariff_per_kwh", "value": "0.3", "unit": "USD/kWh", "source": "Authored"}],
            **extra}


def selected_pins(engine, t, s, days=DAYS):
    body = _read(engine, t, s, "renewable", _midnight(days[0]), _midnight(days[-1] + timedelta(days=1)))
    return [{"local_day": w["local_day"], "selection_seq": w["selection_id"],
             "mini_revision_id": w["assessment_revision_id"]} for w in body["currentness"]["windows"]]


def mg(store, engine):
    installed, t, s = _setup(store, engine)
    _ingest(engine, installed)
    _reconcile(engine, DAYS)
    return t, s


def mg_published(store, engine, tmp_path, capsys):
    """The W4-02 L3 path: each positive authored batch is registered and published before ingest, so the selected
    renewable days classify `AUTHORED_DEMONSTRATION` (a positive provenance baseline)."""
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.composition import build_authored_fixture_specs
    from assetops_backend.publish_source import main as publish_source_main

    installed, t, s = _setup(store, engine)
    doc, sha = snapshot(engine, installed.binding_set.id)
    spec, service, specs = cases.load_spec(), ingestion(), build_authored_fixture_specs()
    for i, b in enumerate(cases.build_batches(spec, doc, sha, "positive")):
        path = tmp_path / f"batch-{i}.json"
        path.write_text(b.body, encoding="utf-8")
        args = ["--site", CODE, "--fixture-id", "assetops.w4-mini-depth-cases", "--fixture-version", "1",
                "--batch-file", str(path)]
        assert publish_source_main(args, ledger=PostgresEvidenceLedger(URL), specs=specs) == 0
        capsys.readouterr()
        service.submit(principal(doc), b.body.encode("utf-8"))
    _reconcile(engine, DAYS)
    return t, s


def client(monkeypatch, t, s, *, injected=True) -> TestClient:
    from assetops_backend import main

    monkeypatch.setenv("DATABASE_URL", URL)
    if not injected:
        return TestClient(main.create_app())
    return TestClient(main.create_app(
        mini_decision_command_access=lambda request, code: None,
        mini_decision_principal=lambda request, code: principal_for(t, s) if code == CODE else None))


def revision_count(engine) -> int:
    with engine.connect() as c:
        return c.execute(text("SELECT count(*) FROM mini_scenario_revision")).scalar_one()


def reselect_limited(engine, t, s, day) -> None:
    """A later W4-02 selection of `day` with a new (LIMITED) revision: an earlier pin is no longer the head."""
    mini = PostgresMiniDepthStore(engine)
    with mini.snapshot() as c:
        inputs = load_hour_inputs(c, t, s, local_noon(day, ZONE), mini.clock(c))
        revision = projection.project("renewable", inputs)
        result = dict(revision.result)
        result["hour"] = {**result["hour"], "decision": "LIMITED", "opportunity_kwh": None}
        result["rows"] = [{**r, "decision": "LIMITED", "constraints": ["COVERAGE_GAP"], "opportunity_kwh": None}
                          for r in result["rows"]]
        mini.append_selection(replace(revision, result=result), job_id=None, backfill=True, connection=c)


def db_now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def test_create_correct_retry_and_fresh_persisted_read(store, engine, monkeypatch) -> None:  # noqa: F811
    t, s = mg(store, engine)
    pins = selected_pins(engine, t, s)
    api = client(monkeypatch, t, s)

    created = api.post(ROUTE, json=load_command("w403-create-001", pins, "First authored narrative."))
    assert created.status_code == 201, created.text
    first = created.json()
    assert set(first) == WRITE_KEYS and first["schema_version"] == "mini-scenario-write-1"
    assert first["revision_no"] == 1 and first["supersedes_revision_id"] is None
    assert first["code"].startswith("SCN-") and len(first["code"]) >= 10
    assert first["recorded_at"].endswith("Z") and len(first["recorded_at"]) == 27

    # Identical authorized retry: the exact original body with 200 and no new row.
    retry = api.post(ROUTE, json=load_command("w403-create-001", pins, "First authored narrative."))
    assert (retry.status_code, retry.json()) == (200, first)
    # Same key, changed narrative: 409 and no new revision.
    count = revision_count(engine)
    changed = api.post(ROUTE, json=load_command("w403-create-001", pins, "A different narrative."))
    assert changed.status_code == 409 and changed.json()["detail"]["code"] == "DECISION_DUPLICATE_KEY"
    assert set(changed.json()["detail"]) == {"code", "message"}
    assert revision_count(engine) == count
    between = db_now(engine)

    correction = load_command("w403-correct-001", pins, "Corrected authored narrative.",
                              supersedes_revision_id=first["revision_id"],
                              correction_reason="Correct the narrative.")
    corrected = api.post(f"{ROUTE}/{first['id']}/revisions", json=correction)
    assert corrected.status_code == 201, corrected.text
    second = corrected.json()
    assert (second["id"], second["code"], second["revision_no"], second["supersedes_revision_id"]) == (
        first["id"], first["code"], 2, first["revision_id"])
    again = api.post(f"{ROUTE}/{first['id']}/revisions", json=correction)
    assert (again.status_code, again.json()) == (200, second)
    count = revision_count(engine)
    dup = api.post(f"{ROUTE}/{first['id']}/revisions", json={**correction, "narrative": "Changed again."})
    assert dup.status_code == 409 and dup.json()["detail"]["code"] == "DECISION_DUPLICATE_KEY"
    stale = api.post(f"{ROUTE}/{first['id']}/revisions", json={**correction, "idempotency_key": "w403-correct-002"})
    assert stale.status_code == 409 and stale.json()["detail"]["code"] == "DECISION_CORRECTION_CONFLICT"
    foreign_root = api.post(f"{ROUTE}/{uuid4()}/revisions", json={**correction, "idempotency_key": "w403-x-0001"})
    assert foreign_root.status_code == 404 and foreign_root.json()["detail"]["code"] == "DECISION_NOT_FOUND"
    foreign_pred = api.post(f"{ROUTE}/{first['id']}/revisions",
                            json={**correction, "idempotency_key": "w403-x-0002", "supersedes_revision_id": str(uuid4())})
    assert foreign_pred.status_code == 422 and foreign_pred.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"
    assert revision_count(engine) == count

    # A fresh app and request: the persisted head and narrative; the historical cutoff returns revision 1's.
    fresh = client(monkeypatch, t, s, injected=False)
    listed = fresh.get(ROUTE)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["schema_version"] == "mini-scenarios-1" and body["status"] == "UNKNOWN"
    assert body["window"]["from"] == "1970-01-01T00:00:00.000000Z" and body["total_count"] == 1
    assert body["selection_token"].startswith("sha256:") and body["next_cursor"] is None
    row = body["rows"][0]
    assert set(row) == ROW_KEYS
    assert (row["id"], row["revision_id"], row["narrative"]) == (
        first["id"], second["revision_id"], "Corrected authored narrative.")
    assert row["scenario_state"] == "DEFINED" and row["url"] is None and row["actor_id"] == PRINCIPAL_ID
    assert row["pinned_mini_revision_ids"] == sorted(p["mini_revision_id"] for p in pins)
    selected = body["selected_source_provenance"]
    assert selected is not None and selected["evidence_ids"]
    if selected["classification"] in ("UNKNOWN", "MIXED"):
        assert row["calculation_state"] == "WITHHELD" and row["energy_kwh"] is None
    else:
        assert row["calculation_state"] in ("GROSS_SCENARIO", "WITHHELD")
    historic = fresh.get(ROUTE, params={"known_at": between.astimezone(timezone.utc).isoformat()})
    old = historic.json()["rows"][0]
    assert (old["revision_id"], old["narrative"], old["scenario_state"]) == (
        first["revision_id"], "First authored narrative.", "HISTORICAL")
    # The default composition refuses every write.
    refused = fresh.post(ROUTE, json=load_command("w403-create-009", pins))
    assert refused.status_code == 403 and refused.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"


def test_pin_scope_basis_and_shape_vectors(store, engine, monkeypatch) -> None:  # noqa: F811
    t, s = mg(store, engine)
    pins = selected_pins(engine, t, s)
    api = client(monkeypatch, t, s)

    def code(body):
        response = api.post(ROUTE, json=body)
        return response.status_code, (response.json().get("detail") or {}).get("code")

    assert code(tariff_command("w403-pins-000"))[0] == 201  # zero pins
    assert code(load_command("w403-pins-005", pins))[0] == 201  # five valid pins
    with engine.connect() as c:
        other = c.execute(text("SELECT id::text FROM mini_depth_revision WHERE tenant_id = :t AND site_id = :s "
                               "AND domain <> 'renewable' LIMIT 1"), {"t": t, "s": s}).scalar()
    foreign = [{**pins[0], "mini_revision_id": str(uuid4())}]
    assert code(load_command("w403-pins-f01", foreign)) == (422, "DECISION_LINK_SCOPE_INVALID")
    if other is not None:
        assert code(load_command("w403-pins-f02", [{**pins[0], "mini_revision_id": other}])) == (
            422, "DECISION_LINK_SCOPE_INVALID")
    assert code(load_command("w403-pins-s01", [{**pins[0], "selection_seq": pins[0]["selection_seq"] + 1000}])) == (
        409, "DECISION_BASIS_CHANGED")
    reselect_limited(engine, t, s, DAYS[0])
    assert code(load_command("w403-pins-s02", pins[:1])) == (409, "DECISION_BASIS_CHANGED")  # same-Site non-head
    six = pins + [{"local_day": "2026-10-11", "selection_seq": 1, "mini_revision_id": str(uuid4())}]
    for key, bad in (("w403-pins-d01", [pins[1], pins[1]]), ("w403-pins-d02", [pins[1], pins[3]]),
                     ("w403-pins-d03", six), ("w403-pins-d04", [{**pins[1], "selection_seq": True}]),
                     ("w403-pins-d05", [{**pins[1], "local_day": "2026-10-7"}]),
                     ("w403-pins-d06", [{**pins[1], "extra": 1}])):
        assert code(load_command(key, bad)) == (422, "DECISION_INPUT_INVALID"), key
    # Closure 1 Q1-Q3 / N8 refusal vectors (shape, USER, attestation, client basis, unknown key, schema).
    assert code({**tariff_command("w403-act-001"), "actor": actor(kind="USER")}) == (403, "DECISION_USER_AUTH_REQUIRED")
    assert code({**tariff_command("w403-act-002"), "actor": actor(attestation="service=other;job=j;rule=r")}) == (
        422, "DECISION_ATTESTATION_INVALID")
    assert code({**tariff_command("w403-act-003"), "actor": actor(authorization_basis=None)}) == (
        422, "DECISION_INPUT_INVALID")
    assert code({**tariff_command("w403-act-004"), "tenant_id": str(t)}) == (422, "DECISION_INPUT_INVALID")
    assert code({**tariff_command("w403-act-005"), "schema_version": "x"}) == (422, "DECISION_INPUT_INVALID")
    for narrative in (None, "   ", "x" * 2001):
        assert code(tariff_command("w403-nar-001", narrative=narrative)) == (422, "DECISION_INPUT_INVALID")
    assert code(tariff_command("w403-nar-002", narrative="  " + "y" * 2000 + "  "))[0] == 201


def test_rows_pages_provenance_and_gate(store, engine, tmp_path, capsys) -> None:  # noqa: F811
    t, s = mg_published(store, engine, tmp_path, capsys)
    pins = selected_pins(engine, t, s)
    decisions = {r["day"]: r["decision"]
                 for r in _read(engine, t, s, "renewable", _midnight(DAYS[0]), _midnight(DAYS[-1] + timedelta(days=1)))
                 ["rows"]}
    eligible = [i for i, p in enumerate(pins) if decisions[p["local_day"]] == "ELIGIBLE"]
    assert len(eligible) >= 4 and eligible[-4:] == list(range(eligible[-4], eligible[-4] + 4)), decisions
    pins_a, pins_b = pins[eligible[-4]:eligible[-4] + 2], pins[eligible[-4] + 2:eligible[-4] + 4]
    dropped: set[str] = set()

    def link_rows(c, tenant_id, site_id, ids):
        return link_rows_on(c, tenant_id, site_id, [i for i in ids if str(i).lower() not in dropped])

    service = ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows))
    who = principal_for(t, s)
    status_a, a = service.create(t, s, who, load_command("w403-page-a01", pins_a, "Two eligible days."))
    status_b, b = service.create(t, s, who, load_command("w403-page-b01", pins_b, "Two later eligible days."))
    status_c, c_ = service.create(t, s, who, tariff_command("w403-page-c01"))
    assert (status_a, status_b, status_c) == (201, 201, 201)

    def page(**q):
        return service.list(t, s, parse_list(q.get("from"), q.get("to"), q.get("limit"),
                                             [q["known_at"]] if "known_at" in q else [], q.get("cursor")), "basis")

    first = page(limit="1")
    second = page(limit="1", cursor=first["next_cursor"])
    third = page(limit="1", cursor=second["next_cursor"])
    rows = first["rows"] + second["rows"] + third["rows"]
    assert first["total_count"] == 3 and third["next_cursor"] is None
    assert [r["id"] for r in rows] == [c_["id"], b["id"], a["id"]]  # (recorded_at DESC, id ASC)
    # The envelope's provenance is the union over all eligible rows, identical on every page.
    assert first["selected_source_provenance"] == second["selected_source_provenance"] ==         third["selected_source_provenance"]
    assert first["selected_source_provenance"]["classification"] == "AUTHORED_DEMONSTRATION"
    assert first["selection_token"] == second["selection_token"] == third["selection_token"]
    with engine.connect() as conn:
        def evidence(of):
            return {str(i) for i in conn.execute(text(
                "SELECT evidence_id FROM mini_depth_revision_evidence WHERE revision_id = ANY(CAST(:ids AS uuid[]))"),
                {"ids": [p["mini_revision_id"] for p in of]}).scalars()}
        a_ids, b_ids = evidence(pins_a), evidence(pins_b)
    assert set(first["selected_source_provenance"]["evidence_ids"]) == a_ids | b_ids
    unpinned = rows[0]
    assert (unpinned["calculation_state"], unpinned["pinned_mini_revision_ids"]) == ("NO_CALCULATION", [])
    assert unpinned["limitations"] == [{"code": "NOT_PRODUCTIVE_LOAD", "evidence_ids": []}]
    # u2c PR-4.4: exact decimal strings on the wire.
    computed = {"calculation_state": "GROSS_SCENARIO", "energy_kwh": "0.001",
                "gross_sales": {"amount": "0.00025", "currency": "USD", "basis": "SCENARIO"}, "limitations": []}
    baseline = {r["id"]: r for r in page()["rows"]}
    for row in (baseline[a["id"]], baseline[b["id"]]):
        assert {k: row[k] for k in computed} == computed and row["scenario_state"] == "DEFINED"

    # Drop B's own accepted IDs from the resolver: B's provenance is not positive and only B is withheld.
    assert b_ids - a_ids
    dropped.update(b_ids - a_ids)
    gated = {r["id"]: r for r in page()["rows"]}
    assert gated[b["id"]]["calculation_state"] == "WITHHELD" and gated[b["id"]]["energy_kwh"] is None
    assert [x["code"] for x in gated[b["id"]]["limitations"]] in (["SOURCE_CLASS_UNKNOWN"], ["SOURCE_CLASS_MIXED"])
    assert gated[a["id"]] == baseline[a["id"]]
    dropped.clear()

    # Stale current pin: a later W4-02 selection replaces A's first day. Current read: DEFINED, withheld; the
    # cutoff before the change: HISTORICAL with the stored arithmetic.
    before = db_now(engine)
    reselect_limited(engine, t, s, DAYS[eligible[-4]])
    current = {r["id"]: r for r in page()["rows"]}
    assert current[a["id"]]["scenario_state"] == "DEFINED" and current[a["id"]]["calculation_state"] == "WITHHELD"
    assert current[a["id"]]["energy_kwh"] is None and current[a["id"]]["gross_sales"] is None
    assert [x["code"] for x in current[a["id"]]["limitations"]] == ["SELECTION_CHANGED"]
    assert current[b["id"]] == baseline[b["id"]]
    past = {r["id"]: r for r in page(known_at=before.isoformat())["rows"]}[a["id"]]
    assert past["scenario_state"] == "HISTORICAL" and {k: past[k] for k in computed} == computed
    # The cursor's fixed cutoff keeps its token (the reselection is after it); a different selected set refuses.
    assert page(limit="1", cursor=first["next_cursor"])["rows"] == second["rows"]
    tampered = decode_cursor(first["next_cursor"])
    tampered["selection_token"] = "sha256:" + "0" * 64
    with pytest.raises(DecisionRefused) as changed:
        page(limit="1", cursor=encode_cursor(tampered))
    assert changed.value.code == "DECISION_BASIS_CHANGED"
    for q, expected in (({"cursor": "not-base64!"}, "INVALID_CURSOR"), ({"limit": "0"}, "INVALID_LIMIT"),
                        ({"limit": "101"}, "INVALID_LIMIT"), ({"from": "2026-10-01T00:00:00Z"}, "INVALID_WINDOW"),
                        ({"known_at": "2999-01-01T00:00:00Z"}, "INVALID_KNOWN_AT")):
        with pytest.raises(DecisionRefused) as refused:
            page(**q)
        assert refused.value.code == expected, q
    # Creation-time window membership (S15): a window before every root is empty.
    assert page(**{"from": "2000-01-01T00:00:00Z", "to": "2000-01-02T00:00:00Z"})["total_count"] == 0


class _Registry:
    def __init__(self, site_type="MINIGRID", down=False):
        self._site = SimpleNamespace(id=uuid4(), site_code=CODE, site_type=site_type)
        self._down = down

    def tenant(self):
        if self._down:
            from assetops_backend.sites.ports import SiteStoreUnavailable
            raise SiteStoreUnavailable("down")
        return SimpleNamespace(id=uuid4())

    def imported(self, code):
        return self._site if code == CODE else None


def _router_client(registry, scenarios=None, **kw) -> TestClient:
    app = FastAPI()
    app.include_router(build_mini_decisions_router(scenarios, registry, **kw))
    return TestClient(app)


def test_router_refusal_order_without_database() -> None:
    body = tariff_command("w403-route-01")
    plain = _router_client(_Registry())
    missing = plain.get("/api/sites/NOPE-1/financials/scenarios")
    assert missing.status_code == 404 and missing.json()["detail"] == {
        "code": "SITE_NOT_FOUND", "message": "No imported Site 'NOPE-1' in this tenant.", "rows": None,
        "total_count": None}
    assert plain.post("/api/sites/NOPE-1/financials/scenarios", json=body).json()["detail"]["code"] == "SITE_NOT_FOUND"
    assert plain.post(ROUTE, json=body).json()["detail"] == {
        "code": "DECISION_WRITE_FORBIDDEN", "message": "This actor cannot change decisions at this Site."}
    forbidden = _router_client(_Registry(), access=lambda r, c: 403)
    assert forbidden.get(ROUTE).status_code == 403
    assert forbidden.get(ROUTE).json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
    anonymous = _router_client(_Registry(), access=lambda r, c: 401)
    assert anonymous.post(ROUTE, json=body).json()["detail"]["code"] == "UNAUTHENTICATED"
    granted = _router_client(_Registry(), command_access=lambda r, c: None)
    unavailable = granted.post(ROUTE, json=body)
    assert unavailable.status_code == 503 and unavailable.json()["detail"]["code"] == "DECISION_STORE_UNAVAILABLE"
    assert granted.get(ROUTE).status_code == 503
    outage = _router_client(_Registry(down=True))
    assert outage.get(ROUTE).status_code == 503
    cold = _router_client(_Registry(site_type="COLD_ROOM"))
    envelope = cold.get(ROUTE).json()
    assert envelope["status"] == "UNKNOWN" and envelope["rows"] == [] and envelope["limitations"] == [
        {"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}]


def test_principal_scope_is_checked_before_the_body() -> None:
    registry = _Registry()
    site = registry.imported(CODE)
    tenant = uuid4()
    registry.tenant = lambda: SimpleNamespace(id=tenant)  # type: ignore[method-assign]
    service = ScenarioService(None, None)  # type: ignore[arg-type]  never reached: admission refuses first
    for who in (None, DecisionPrincipal("SERVICE", PRINCIPAL_ID, tenant, uuid4(), GRANT_PREFIX + PRINCIPAL_ID),
                DecisionPrincipal("SERVICE", PRINCIPAL_ID, tenant, site.id, "SITE_WORK_WRITE:" + PRINCIPAL_ID),
                DecisionPrincipal("USER", PRINCIPAL_ID, tenant, site.id, GRANT_PREFIX + PRINCIPAL_ID)):
        api = _router_client(registry, service, command_access=lambda r, c: None,
                             principal=lambda r, c, who=who: who)
        response = api.post(ROUTE, content=b"not json")
        assert response.status_code == 403 and response.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"


# --- u2c (PR-4.1-4.5, corrected 2b anchor, closure 4 S9 owned by this unit-2b fix) ------------------------------

UNSUPPORTED = {
    "schema_version": "mini-scenarios-1", "window": {"from": None, "to": None, "known_at": None}, "status": "UNKNOWN",
    "currentness": {"state": "UNKNOWN", "job_state": "NONE"},
    "source_provenance": {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [], "evidence_ids": [],
                          "basis_sha256": None,
                          "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]},
    "selected_source_provenance": None, "pending_source_provenance": None, "total_count": 0, "rows": [],
    "next_cursor": None, "selection_token": None, "limitations": [{"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}]}


def test_u2c_non_minigrid_get_and_post() -> None:
    body = tariff_command("w403-cold-01")
    fix = {**tariff_command("w403-cold-02"), "supersedes_revision_id": str(uuid4()), "correction_reason": "Fix."}
    corr = f"{ROUTE}/{uuid4()}/revisions"
    # PR-4.1: 200 with the full unsupported envelope even with no decision store.
    no_store = _router_client(_Registry(site_type="COLD_ROOM"), None, command_access=lambda r, c: None)
    got = no_store.get(ROUTE)
    assert got.status_code == 200 and got.json() == UNSUPPORTED
    # PR-4.2: grant, then store availability, then the Site type; all before principal or body.
    for path, payload in ((ROUTE, body), (corr, fix)):
        assert no_store.post(path, json=payload).json()["detail"]["code"] == "DECISION_STORE_UNAVAILABLE"
        denied = _router_client(_Registry(site_type="COLD_ROOM"), ScenarioService(None, None))  # type: ignore[arg-type]
        refused = denied.post(path, json=payload)
        assert refused.status_code == 403 and refused.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"
        granted = _router_client(_Registry(site_type="COLD_ROOM"), ScenarioService(None, None),  # type: ignore[arg-type]
                                 command_access=lambda r, c: None, principal=lambda r, c: None)
        for out in (granted.post(path, json=payload), granted.post(path, content=b"not json")):
            assert out.status_code == 422 and out.json()["detail"]["code"] == "DECISION_LINK_SCOPE_INVALID"


class _Reader:
    def __init__(self, classification="AUTHORED_DEMONSTRATION"):
        self.classification = classification

    def provenance_blocks(self, c, **kw):
        return {"selected_source_provenance": {"classification": self.classification}}


def test_u2c_row_gate_order_absent_head_and_decimal_strings() -> None:
    """PR-4.3/4.4 at the row: stored reason first, absent head is SELECTION_CHANGED, same revision under a new seq is
    harmless, deduplicated first-seen codes, and the stored arithmetic as exact decimal strings."""
    rev = str(uuid4())
    pins = [{"local_day": "2026-10-06", "selection_seq": 1, "mini_revision_id": rev},
            {"local_day": "2026-10-07", "selection_seq": 2, "mini_revision_id": str(uuid4())}]
    head = {"id": uuid4(), "public_no": 1, "revision_id": uuid4(), "name": "n", "kind": "PRODUCTIVE_LOAD",
            "narrative": "x", "recorded_at": datetime(2026, 10, 20, tzinfo=timezone.utc), "actor_id": PRINCIPAL_ID,
            "assumptions": [], "pinned_mini_revision_ids": sorted(p["mini_revision_id"] for p in pins),
            "pinned_selection_hours": pins,
            "calculation": {"state": "GROSS_SCENARIO", "energy_kwh": "0.0010", "reason": None,
                            "gross_sales": {"amount": "0.000250", "currency": "USD"}}}
    revisions = {p["mini_revision_id"]: {"evidence_ids": []} for p in pins}
    service = ScenarioService(None, _Reader())  # type: ignore[arg-type]
    same = {"2026-10-06": {"mini_revision_id": rev, "selection_seq": 9, "state": "CURRENT"},
            "2026-10-07": {"mini_revision_id": pins[1]["mini_revision_id"], "selection_seq": 2, "state": "CURRENT"}}
    row = service._row(None, uuid4(), uuid4(), head, same, revisions, False)
    assert (row["calculation_state"], row["energy_kwh"], row["gross_sales"]["amount"], row["limitations"]) == (
        "GROSS_SCENARIO", "0.001", "0.00025", [])
    assert isinstance(row["energy_kwh"], str) and isinstance(row["gross_sales"]["amount"], str)
    absent = {"2026-10-06": {"mini_revision_id": None, "selection_seq": None, "state": "UNKNOWN"},
              "2026-10-07": {**same["2026-10-07"], "state": "PENDING_RECOMPUTE"}}
    gated = service._row(None, uuid4(), uuid4(), head, absent, revisions, False)
    assert [x["code"] for x in gated["limitations"]] == ["SELECTION_CHANGED", "RECOMPUTE_PENDING"]
    assert (gated["calculation_state"], gated["energy_kwh"], gated["gross_sales"]) == ("WITHHELD", None, None)
    assert head["calculation"]["energy_kwh"] == "0.0010"  # the stored calculation is untouched
    reasoned = {**head, "calculation": {"state": "WITHHELD", "energy_kwh": None, "gross_sales": None,
                                         "reason": "HEADROOM_BELOW_LOAD"}}
    stale = {day: {**v, "state": "STALE_SOURCE"} for day, v in same.items()}
    mixed = ScenarioService(None, _Reader("MIXED"))  # type: ignore[arg-type]
    out = mixed._row(None, uuid4(), uuid4(), reasoned, stale, revisions, True)
    assert [x["code"] for x in out["limitations"]] == ["HEADROOM_BELOW_LOAD", "SOURCE_STALE", "SOURCE_CLASS_MIXED"]
    assert out["scenario_state"] == "HISTORICAL" and out["energy_kwh"] is None


def _w402(engine, t, s, days, known):
    return _read(engine, t, s, "renewable", _midnight(days[0]), _midnight(days[-1] + timedelta(days=1)),
                 known_at=known)


def test_u2c_currentness_reselection_and_s9_parity(store, engine, tmp_path, capsys) -> None:  # noqa: F811
    t, s = mg_published(store, engine, tmp_path, capsys)
    pins = selected_pins(engine, t, s)
    decisions = {r["day"]: r["decision"] for r in _w402(engine, t, s, DAYS, None)["rows"]}
    eligible = [i for i, p in enumerate(pins) if decisions[p["local_day"]] == "ELIGIBLE"]
    start = next(i for i in eligible if i + 1 in eligible)
    pins_a = pins[start:start + 2]
    days_a = [DAYS[start], DAYS[start + 1]]
    service = ScenarioService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on))
    who = principal_for(t, s)

    def page(**q):
        return service.list(t, s, parse_list(q.get("from"), q.get("to"), q.get("limit"),
                                             [q["known_at"]] if "known_at" in q else [], q.get("cursor")), "basis")

    # PR-4.5: an empty list and an unpinned row assert no current physical basis.
    empty = page()
    assert empty["total_count"] == 0 and empty["currentness"] == {"state": "UNKNOWN", "job_state": "NONE"}
    assert service.create(t, s, who, load_command("w403-u2c-a01", pins_a, "Pinned."))[0] == 201
    k_pinned = db_now(engine)
    assert service.create(t, s, who, tariff_command("w403-u2c-b01"))[0] == 201
    k_both = db_now(engine)
    window = {"from": k_pinned.isoformat(), "to": (k_both + timedelta(seconds=1)).isoformat()}
    only_unpinned = page(**window)
    assert only_unpinned["total_count"] == 1
    assert only_unpinned["currentness"] == {"state": "UNKNOWN", "job_state": "NONE"}
    assert only_unpinned["rows"][0]["scenario_state"] == "DEFINED"
    past_unpinned = page(**window, known_at=k_both.isoformat())
    assert past_unpinned["currentness"] == {"state": "HISTORICAL", "job_state": "NONE"}
    assert past_unpinned["rows"][0]["scenario_state"] == "HISTORICAL"
    # Pagination: page one holds only the unpinned row; the off-page pins still set envelope currentness.
    first = page(limit="1")
    assert first["rows"][0]["pinned_mini_revision_ids"] == [] and first["currentness"]["state"] == "CURRENT"
    assert page(limit="1", cursor=first["next_cursor"])["currentness"] == first["currentness"]

    def parity(known, expected=None):
        """S9: the W4-02 read and the W4-03 list at one explicit cutoff agree on head, currentness and blocks."""
        w4 = _w402(engine, t, s, days_a, known)
        mine = page(known_at=known.isoformat())
        heads = [w["assessment_revision_id"] for w in w4["currentness"]["windows"]]
        assert heads == [p["mini_revision_id"] for p in (expected or pins_a)]
        for key in ("state", "job_state"):
            assert mine["currentness"][key] == w4["currentness"][key], key
        # S20: the scenario's selected block is its exact pins' union, so it equals W4-02's only while they are heads.
        for key in ("selected_source_provenance", "pending_source_provenance", "source_provenance"):
            if expected is None or key == "pending_source_provenance":
                assert mine[key] == w4[key], key
        return w4, next(r for r in mine["rows"] if r["pinned_mini_revision_ids"])

    _, row = parity(db_now(engine))
    assert row["calculation_state"] == "GROSS_SCENARIO" and row["energy_kwh"] == "0.001"
    # Harmless same-revision reselection (closure 4 S5): a new seq, no code, arithmetic kept.
    mini = PostgresMiniDepthStore(engine)
    with mini.snapshot() as c:
        cutoff = renewable_revisions(c, t, s, [pins_a[0]["mini_revision_id"]])[pins_a[0]["mini_revision_id"]][
            "knowledge_cutoff"]  # the same inputs at the same cutoff: the stored revision is reused
        inputs = load_hour_inputs(c, t, s, local_noon(days_a[0], ZONE), cutoff)
        mini.append_selection(projection.project("renewable", inputs), job_id=None, backfill=True, connection=c)
    after = selected_pins(engine, t, s, days_a)
    assert after[0]["mini_revision_id"] == pins_a[0]["mini_revision_id"]
    assert after[0]["selection_seq"] != pins_a[0]["selection_seq"]
    _, row = parity(db_now(engine))
    assert row["limitations"] == [] and row["calculation_state"] == "GROSS_SCENARIO"
    k_clean = db_now(engine)

    # Pending newer evidence: a live renewable job on the first pinned day.
    noon = local_noon(days_a[0], ZONE)
    with engine.begin() as c:
        c.execute(text("SELECT mini_enqueue_hour(:t, :s, 'mini_renewable', :lo, :hi, NULL, clock_timestamp())"),
                  {"t": t, "s": s, "lo": noon.start, "hi": noon.end})
    w4, row = parity(db_now(engine))
    assert w4["currentness"]["state"] == "PENDING_RECOMPUTE" and w4["pending_source_provenance"] is not None
    assert "RECOMPUTE_PENDING" in [x["code"] for x in w4["limitations"]]
    assert [x["code"] for x in row["limitations"]] == ["RECOMPUTE_PENDING"]
    assert (row["calculation_state"], row["energy_kwh"], row["gross_sales"]) == ("WITHHELD", None, None)
    # Historical replay at the earlier cutoff: that cutoff's heads and jobs, the stored arithmetic.
    _, replay = parity(k_clean)
    assert replay["scenario_state"] == "HISTORICAL" and replay["energy_kwh"] == "0.001"
    assert replay["limitations"] == []
    _reconcile(engine, days_a[:1])  # the job is done; day one now has a new selected revision
    moved = selected_pins(engine, t, s, days_a)
    assert moved[0]["mini_revision_id"] != pins_a[0]["mini_revision_id"] and moved[1] == pins_a[1]

    # Stale digest: an ambiguous covering Foundation (test-only replica edit, no job) makes the heads STALE_SOURCE.
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in ("CREATE TEMP TABLE f_copy ON COMMIT DROP AS SELECT * FROM foundation_revision "
                    "WHERE site_id = :s AND superseded_at IS NULL",
                    "UPDATE f_copy SET id = gen_random_uuid(), version = version + 1000, "
                    "recorded_at = clock_timestamp(), superseded_at = '2999-01-01Z', origin = 'PUBLISH'",
                    "INSERT INTO foundation_revision SELECT * FROM f_copy"):
            c.execute(text(sql), {"s": s})
    w4, row = parity(db_now(engine), moved)
    assert w4["currentness"]["state"] == "STALE_SOURCE"
    assert "SOURCE_STALE" in [x["code"] for x in w4["limitations"]]
    assert [x["code"] for x in row["limitations"]] == ["SELECTION_CHANGED", "SOURCE_STALE"]
    assert row["calculation_state"] == "WITHHELD"


def test_u2c_fractional_row_bound_is_the_basis(store, engine) -> None:  # noqa: F811
    """Corrected 2b anchor: the basis bound is `result.rows[0].opportunity_kwh` of the selected stored revision."""
    t, s = mg(store, engine)
    day = DAYS[1]
    mini = PostgresMiniDepthStore(engine)
    with mini.snapshot() as c:
        inputs = load_hour_inputs(c, t, s, local_noon(day, ZONE), mini.clock(c))
        revision = projection.project("renewable", inputs)
        result = dict(revision.result)
        result["hour"] = {**{k: v for k, v in result["hour"].items() if k != "opportunity_kwh"},
                          "decision": "ELIGIBLE"}
        result["rows"] = [{**result["rows"][0], "decision": "ELIGIBLE",
                           "opportunity_kwh": {"low": 0.0125, "high": 0.375}}]
        mini.append_selection(replace(revision, result=result), job_id=None, backfill=True, connection=c)
    reader = MiniDepthRead(engine, link_rows_on)
    with engine.connect() as c:
        basis = reader.read_selected_renewable_basis(c, tenant_id=t, site_id=s, days=[day], known=db_now(engine),
                                                     historical=False)
    assert basis["days"][0]["opportunity_kwh"] == {"low": 0.0125, "high": 0.375}
    pin = selected_pins(engine, t, s, [day])
    service = ScenarioService(PostgresMiniDecisionStore(engine), reader)
    who = principal_for(t, s)

    def stored(key, kw):
        cmd = load_command(key, pin)
        cmd["assumptions"][0]["value"] = kw
        assert service.create(t, s, who, cmd)[0] == 201
        with engine.connect() as c:
            return c.execute(text("SELECT calculation FROM mini_scenario_revision WHERE idempotency_key = :k"),
                             {"k": key}).scalar_one()

    fits = stored("w403-frac-001", "0.0125")
    assert fits["state"] == "GROSS_SCENARIO" and fits["energy_kwh"] == "0.0125"
    assert stored("w403-frac-002", "0.0126")["reason"] == "HEADROOM_BELOW_LOAD"
