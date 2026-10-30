"""W5-01b unit C4: authored cold scenario store, migration `0032_w5_cold_scenarios`, command/list service and API.

`.agent/W5-01-build-spec.md` C4 card, "C4 exact persisted schema and wire contract" and pre-flight rulings
P-C4-1..23. Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import hashlib
import json
import os
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar
    from test_w402_migration_postgres import downgrade_config


LATEST_HEAD = "0038_out_objectives"  # W5-03b: 0034 and 0033 sit above the 0032 migration under test
COLD_HEAD = "0032_w5_cold_scenarios"
COLD_PREVIOUS = "0030_w4_mini_decisions"
COLD_REFUSED = "Downgrade of 0032_w5_cold_scenarios refused: cold scenario history exists"
COLD_TABLES = ("cold_scenario_revision", "cold_scenario")
COLD_SEQUENCE = "cold_scenario_public_no_seq"
COLD_COLUMNS = {
    "cold_scenario": ["id", "tenant_id", "site_id", "public_no", "create_key", "create_payload_sha256",
                      "create_actor_id", "created_at", "actor_kind", "actor_id"],
    "cold_scenario_revision": ["id", "tenant_id", "site_id", "scenario_id", "revision_no", "supersedes_revision_id",
                               "name", "kind", "assumptions", "authored_basis", "basis_sha256", "formula_version",
                               "correction_reason", "actor_kind", "actor_id", "authorization_basis", "attestation",
                               "idempotency_key", "payload_sha256", "recorded_at"],
}
COLD_CATALOG = {
    "p": ["cold_scenario_pkey", "cold_scenario_revision_pkey"],
    "u": sorted(["cold_scenario_scope_uk", "cold_scenario_public_uk", "cold_scenario_create_key_uk",
                 "cold_scenario_revision_scope_uk", "cold_scenario_revision_no_uk",
                 "cold_scenario_revision_previous_uk", "cold_scenario_revision_key_uk"]),
    "f": sorted(["cold_scenario_site_fk", "cold_scenario_revision_scenario_fk", "cold_scenario_revision_previous_fk"]),
    "c": sorted(["cold_scenario_create_key_check", "cold_scenario_create_payload_sha256_check",
                 "cold_scenario_create_actor_id_check", "cold_scenario_revision_revision_no_check",
                 "cold_scenario_revision_name_check", "cold_scenario_revision_kind_check",
                 "cold_scenario_revision_formula_check", "cold_scenario_revision_chain_check",
                 "cold_scenario_revision_basis_sha256_check", "cold_scenario_revision_payload_sha256_check",
                 "cold_scenario_revision_idempotency_key_check", "cold_scenario_revision_actor_check",
                 "cold_scenario_revision_assumptions_check", "cold_scenario_revision_authored_basis_check"]),
}
COLD_FK_TARGETS = {
    "cold_scenario_site_fk": ("site", ["tenant_id", "site_id"]),
    "cold_scenario_revision_scenario_fk": ("cold_scenario", ["tenant_id", "site_id", "scenario_id"]),
    "cold_scenario_revision_previous_fk": ("cold_scenario_revision", ["tenant_id", "site_id", "supersedes_revision_id"]),
}
COLD_INDEX = ("CREATE INDEX cold_scenario_site_order ON public.cold_scenario_revision USING btree "
              "(tenant_id, site_id, recorded_at DESC, id DESC)")


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def cold_catalog(engine) -> dict:  # noqa: F811
    """Exact 0032 catalog: tables, columns, named constraints, FK targets, index definition, triggers, sequence."""
    with engine.connect() as c:
        tables = sorted(c.execute(text("SELECT relname FROM pg_class WHERE relkind = 'r' AND relname = ANY(:t)"),
                                  {"t": list(COLD_TABLES)}).scalars())
        columns = {t: list(c.execute(text(
            "SELECT attname FROM pg_attribute WHERE attrelid = to_regclass(:t) AND attnum > 0 AND NOT attisdropped "
            "ORDER BY attnum"), {"t": t}).scalars()) for t in tables}
        named = {k: sorted(c.execute(text(
            "SELECT conname FROM pg_constraint WHERE contype = :k AND conrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t) AND relkind = 'r')"),
            {"k": k, "t": list(COLD_TABLES)}).scalars()) for k in ("p", "u", "f", "c")}
        fks = {r[0]: (r[1], list(r[2])) for r in c.execute(text(
            "SELECT conname, confrelid::regclass::text, (SELECT array_agg(attname ORDER BY array_position(conkey, "
            "attnum)) FROM pg_attribute WHERE attrelid = conrelid AND attnum = ANY(conkey)) FROM pg_constraint "
            "WHERE contype = 'f' AND conname = ANY(:n)"), {"n": list(COLD_FK_TARGETS)})}
        index = c.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname = 'cold_scenario_site_order'")).scalar()
        triggers = sorted(tuple(r) for r in c.execute(text(
            "SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t))"), {"t": list(COLD_TABLES)}))
        sequence = c.execute(text("SELECT count(*) FROM pg_class WHERE relkind = 'S' AND relname = :s"),
                             {"s": COLD_SEQUENCE}).scalar_one()
    return {"tables": tables, "columns": columns, "named": named, "fks": fks, "index": index,
            "triggers": triggers, "sequence": sequence}


def expected_cold_catalog() -> dict:
    return {"tables": sorted(COLD_TABLES), "columns": COLD_COLUMNS, "named": COLD_CATALOG, "fks": COLD_FK_TARGETS,
            "index": COLD_INDEX,
            "triggers": sorted((f"{t}_immutable", f"CREATE TRIGGER {t}_immutable BEFORE DELETE OR UPDATE ON public.{t} "
                                "FOR EACH ROW EXECUTE FUNCTION ledger_append_only()") for t in COLD_TABLES),
            "sequence": 1}


def expected_cold_absent() -> dict:
    return {"tables": [], "columns": {}, "named": {k: [] for k in ("p", "u", "f", "c")}, "fks": {}, "index": None,
            "triggers": [], "sequence": 0}


def seed_cold_scenario(engine, tenant_id, site_id) -> tuple:  # noqa: F811
    """One root and its revision 1, written directly (catalog test only; the service is the product writer)."""
    root, rev = uuid4(), uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO cold_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, create_actor_id, "
            "actor_kind, actor_id) VALUES (:id, :t, :s, 'create-key-0001', :h, 'svc-1', 'SERVICE', 'svc-1')"),
            {"id": root, "t": tenant_id, "s": site_id, "h": _sha("create")})
        c.execute(text(
            "INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, name, kind, "
            "assumptions, authored_basis, basis_sha256, formula_version, actor_kind, actor_id, authorization_basis, "
            "attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :r, 1, 'Stock context', "
            "'STOCK_VALUE_CONTEXT', CAST(:a AS jsonb), CAST(:b AS jsonb), :bh, 'AUTHORED_ONLY/1', 'SERVICE', 'svc-1', "
            "'grant', 'attested', 'idem-key-0001', :ph)"),
            {"id": rev, "t": tenant_id, "s": site_id, "r": root,
             "a": json.dumps({"stock_quantity": "10", "stock_unit": "kg", "unit_value": "2.5", "currency": "USD"}),
             "b": json.dumps({"from": "2026-10-01T00:00:00Z"}), "bh": _sha("basis"), "ph": _sha("payload")})
    return root, rev


def test_migration_constraints(site, engine) -> None:  # noqa: F811
    """P-C4-1..6: sole head and exact 0032 catalog; append-only triggers refuse UPDATE/DELETE; JSON-object checks;
    a nonempty downgrade is refused and leaves everything in place; an empty downgrade reaches 0030 without the 0032
    catalog and re-upgrades to the same catalog."""
    from alembic import command
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [LATEST_HEAD]
    assert script.get_revision("0033_w5_cold_work").down_revision == COLD_HEAD
    assert script.get_revision(COLD_HEAD).down_revision == COLD_PREVIOUS
    assert head(engine) == LATEST_HEAD and cold_catalog(engine) == expected_cold_catalog()

    with engine.connect() as c:
        tenant_id, site_id = c.execute(text("SELECT tenant_id, id FROM site ORDER BY id LIMIT 1")).one()
    root, rev = seed_cold_scenario(engine, tenant_id, site_id)
    for table, row in (("cold_scenario_revision", rev), ("cold_scenario", root)):
        for sql in (f"UPDATE {table} SET actor_id = 'svc-2' WHERE id = :id", f"DELETE FROM {table} WHERE id = :id"):
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text(sql), {"id": row})
    for column in ("assumptions", "authored_basis"):
        with pytest.raises(DBAPIError, match=f"cold_scenario_revision_{column}_check"):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, "
                    "supersedes_revision_id, name, kind, assumptions, authored_basis, basis_sha256, formula_version, "
                    "correction_reason, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
                    "payload_sha256) VALUES (:id, :t, :s, :r, 2, :p, 'Stock context', 'STOCK_VALUE_CONTEXT', "
                    f"{'CAST(:j AS jsonb)' if column == 'assumptions' else 'CAST(:o AS jsonb)'}, "
                    f"{'CAST(:j AS jsonb)' if column == 'authored_basis' else 'CAST(:o AS jsonb)'}, :h, "
                    "'AUTHORED_ONLY/1', 'Fix', 'SERVICE', 'svc-1', 'grant', 'attested', 'idem-key-0002', :h)"),
                    {"id": uuid4(), "t": tenant_id, "s": site_id, "r": root, "p": rev, "j": "[]", "o": "{}",
                     "h": _sha("x")})
    assert [scalar(engine, f"SELECT count(*) FROM {t}") for t in COLD_TABLES] == [1, 1]

    config = downgrade_config(site, engine)
    try:
        with pytest.raises(DBAPIError, match=COLD_REFUSED):
            command.downgrade(config, COLD_PREVIOUS)
        assert head(engine) == LATEST_HEAD and cold_catalog(engine) == expected_cold_catalog()
        assert [scalar(engine, f"SELECT count(*) FROM {t}") for t in COLD_TABLES] == [1, 1]
        _replica(engine, f"DELETE FROM cold_scenario_revision WHERE id = '{rev}'",
                 f"DELETE FROM cold_scenario WHERE id = '{root}'")
        engine.dispose()
        command.downgrade(config, COLD_PREVIOUS)
        assert head(engine) == COLD_PREVIOUS and cold_catalog(engine) == expected_cold_absent()
        engine.dispose()
        command.upgrade(config, "head")
    finally:
        if head(engine) != LATEST_HEAD:
            engine.dispose()
            command.upgrade(config, "head")
    assert head(engine) == LATEST_HEAD and cold_catalog(engine) == expected_cold_catalog()
    assert ScriptDirectory.from_config(config).get_heads() == [LATEST_HEAD]


# --- C4 part B: command, list and router (the persisted positive producer is the in-process POST) ---------------

if URL:
    from datetime import datetime, timedelta, timezone
    from types import SimpleNamespace

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, rows, run

    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService
    from assetops_backend.analytics.cold_depth import ColdDepthReadService
    from assetops_backend.cold_scenarios.service import ColdScenarioService
    from assetops_backend.cold_scenarios.store import PostgresColdScenarioStore
    from assetops_backend.cold_scenarios_api import build_cold_scenarios_router
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal
    from assetops_backend.sites.ports import SiteStoreUnavailable
    from assetops_backend.work.model import canonical_json

CODE = "COLD-READ"
LO, HI = "2026-10-06T19:00:00Z", "2026-10-06T20:05:00Z"
W = f"from={LO}&to={HI}"
OTHER_W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:30:00Z"
EMPTY_W = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z"
ROUTE = f"/api/sites/{CODE}/cold/financials/scenarios"
DOWN = "postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=2"
PRINCIPAL = "service:cold-scenario-seed"
ATTEST = "service=cold-scenario-seed;job=w501b-c4;rule=AUTHORED_ONLY/1"
WRITE_KEYS = ["schema_version", "id", "code", "revision_id", "revision_no"]
LIST_KEYS = ["schema_version", "site_id", "window", "scenario_at", "selection", "items", "next_cursor", "total_pages"]
ITEM_KEYS = ["id", "code", "revision_id", "revision_no", "name", "kind", "assumptions", "authored_basis",
             "recorded_at", "scenario_state"]
BASIS_KEYS = ["from", "to", "cutoff", "assessment_revision_ids", "accepted_evidence_ids", "foundation_revision_id",
              "source_provenance"]
CLAIMS = ("revenue", "spoil", "saving", "amount", "loss", "outcome", "delta", "profit", "cost")
ASSUMPTIONS = {"stock_quantity": "1200", "stock_unit": "kg", "unit_value": "3.25", "currency": "USD"}


def _registry(built, *, site_id=None, site_type="COLDCHAIN", down=False):
    site = SimpleNamespace(id=site_id or built.site_id, site_type=site_type)

    def imported(code):
        if down:
            raise SiteStoreUnavailable("The Site store is unavailable.")
        return site if code == CODE else None
    return SimpleNamespace(imported=imported, tenant=lambda: SimpleNamespace(id=built.tenant_id))


def reads(url=None, link_rows=True) -> "ColdReadService":
    return ColdReadService(url or URL, link_rows=build_link_rows_reader() if link_rows else None)


def scenarios_client(built, *, principal=True, command=None, access=None, disclosure=None, store_url=None,
                     reads_url=None, link_rows=True, service=True, site_id=None, site_type="COLDCHAIN",
                     down=False, principal_site=None) -> "TestClient":
    """The in-process C4 producer: the router with an injected `DecisionPrincipal` carrying its own
    `GRANT_PREFIX` grant for the exact tenant/Site (`tools/w403_mini_decisions_walkthrough.py:88` pattern)."""
    scope = principal_site or site_id or built.site_id
    kw = {"command_access": command or (lambda request, code: None),
          "principal": (lambda request, code: DecisionPrincipal("SERVICE", PRINCIPAL, built.tenant_id, scope,
                                                                GRANT_PREFIX + PRINCIPAL)) if principal
          else (lambda request, code: None)}
    if access is not None:
        kw["access"] = access
    if disclosure is not None:
        kw["disclosure"] = disclosure
    svc = (ColdScenarioService(PostgresColdScenarioStore.from_url(store_url or URL),
                               reads(reads_url, link_rows)) if service else None)
    app = FastAPI()
    app.include_router(build_cold_scenarios_router(
        _registry(built, site_id=site_id, site_type=site_type, down=down), svc, **kw))
    return TestClient(app)


def command_body(key: str, **over) -> dict:
    body = {"schema_version": "cold-scenario-command-1", "idempotency_key": key,
            "actor": {"kind": "SERVICE", "id": PRINCIPAL, "attestation": ATTEST},
            "name": "Stock value at risk", "kind": "STOCK_VALUE_CONTEXT", "assumptions": dict(ASSUMPTIONS)}
    body.update(over)
    return body


def correction_body(key: str, previous: str, **over) -> dict:
    return command_body(key, supersedes_revision_id=previous, correction_reason="Corrected stock count", **over)


def post(c, body, query: str = W, status: int = 201, path: str = "") -> dict:
    response = c.post(f"{ROUTE}{path}?{query}", json=body) if not isinstance(body, bytes) else \
        c.post(f"{ROUTE}{path}?{query}", content=body, headers={"content-type": "application/json"})
    assert response.status_code == status, response.text
    return response.json()


def listed(c, query: str = W, status: int = 200) -> dict:
    response = c.get(f"{ROUTE}?{query}" if query else ROUTE)
    assert response.status_code == status, response.text
    return response.json()


def refusal(response, status: int, code: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert list(body) == ["error"] and list(body["error"]) == ["code", "message"], body
    assert body["error"]["code"] == code and body["error"]["message"], body
    if status == 401:
        assert response.headers.get("www-authenticate") == "Bearer"


def refused_post(c, body, status: int, code: str, query: str = W, path: str = "") -> None:
    refusal(c.post(f"{ROUTE}{path}?{query}", json=body), status, code)


def refused_get(c, query: str, status: int, code: str) -> None:
    refusal(c.get(f"{ROUTE}?{query}"), status, code)


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _sha256(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def basis_on(built, query_known=None, lo=LO, hi=HI) -> dict:
    r = reads()
    try:
        return r.within(lambda c: ColdDepthReadService(r).basis_on(
            c, built.tenant_id, built.site_id, CODE, _at(lo), _at(hi), None if query_known is None else _at(query_known)))
    finally:
        r.dispose()


def stored(built, scenario_id: str) -> list[dict]:
    return [dict(r) for r in rows(built, "SELECT r.*, m.create_payload_sha256, m.create_key, m.public_no, "
                                         "m.actor_kind AS root_actor_kind, m.actor_id AS root_actor_id, "
                                         "m.create_actor_id FROM cold_scenario_revision r JOIN cold_scenario m "
                                         "ON m.id = r.scenario_id WHERE r.site_id = :s AND r.scenario_id = :id "
                                         "ORDER BY r.revision_no", id=scenario_id)]


def counts(built) -> list[int]:
    return [rows(built, f"SELECT count(*) AS n FROM {t} WHERE site_id = :s")[0]["n"] for t in COLD_TABLES]


def assert_no_claim(value) -> None:
    """No revenue, spoilage, savings, amount, loss or outcome field anywhere in a C4 body."""
    if isinstance(value, dict):
        for key, item in value.items():
            assert not any(word in key.lower() for word in CLAIMS), key
            assert_no_claim(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_claim(item)


def canonical_command(body: dict) -> dict:
    out = {k: v for k, v in body.items() if k != "idempotency_key"}
    out["name"] = out["name"].strip()
    out["assumptions"] = {**out["assumptions"], "stock_unit": out["assumptions"]["stock_unit"].strip()}
    return out


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_command_schema_refusals_and_replay(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = scenarios_client(built)
    expected = basis_on(built)
    assert expected["selection"]["state"] == "CURRENT" and expected["authored_basis"]["assessment_revision_ids"]

    # The persisted positive producer: exact C1 selected IDs, stored basis equals `basis_on`.
    body = command_body("seed-create-0001", name="  Stock value at risk  ",
                        assumptions={**ASSUMPTIONS, "stock_unit": "  kg  "})
    out = post(c, body)
    assert list(out) == WRITE_KEYS and out["schema_version"] == "cold-scenario-write-1"
    assert out["revision_no"] == 1 and out["code"].startswith("CSCN-") and len(out["code"]) >= 11
    assert out["code"][5:].isdigit()
    [rev] = stored(built, out["id"])
    assert str(rev["id"]) == out["revision_id"] and out["code"] == f"CSCN-{rev['public_no']:06d}"
    assert rev["authored_basis"] == expected["authored_basis"]
    assert set(rev["authored_basis"]) == set(BASIS_KEYS)
    assert rev["authored_basis"]["foundation_revision_id"] == \
        str(built.run.registered_basis.foundation_revision_id).lower()
    assert rev["authored_basis"]["cutoff"] == expected["window"]["committed_watermark"]
    assert (rev["name"], rev["assumptions"]["stock_unit"]) == ("Stock value at risk", "kg")
    assert rev["assumptions"] == {**ASSUMPTIONS, "stock_unit": "kg"}
    assert (rev["kind"], rev["formula_version"], rev["revision_no"]) == ("STOCK_VALUE_CONTEXT", "AUTHORED_ONLY/1", 1)
    assert (rev["supersedes_revision_id"], rev["correction_reason"]) == (None, None)
    assert (rev["actor_kind"], rev["actor_id"], rev["attestation"]) == ("SERVICE", PRINCIPAL, ATTEST)
    assert rev["authorization_basis"] == GRANT_PREFIX + PRINCIPAL
    assert (rev["root_actor_kind"], rev["root_actor_id"], rev["create_actor_id"]) == ("SERVICE", PRINCIPAL, PRINCIPAL)
    # Hashes (P-C4-22): create input `{command, site_id, window:{from,to,cutoff}}`; revision 1 equals it.
    window = {"from": expected["window"]["from"], "to": expected["window"]["to"],
              "cutoff": expected["authored_basis"]["cutoff"]}
    create_sha = _sha256({"command": canonical_command(body), "site_id": str(built.site_id).lower(),
                          "window": window})
    assert rev["create_payload_sha256"] == rev["payload_sha256"] == create_sha
    assert rev["basis_sha256"] == _sha256(rev["authored_basis"])
    assert rev["create_key"] == rev["idempotency_key"] == "seed-create-0001"
    assert_no_claim(out)
    assert_no_claim(rev["authored_basis"])
    columns = [r["column_name"] for r in rows(built, "SELECT column_name FROM information_schema.columns "
                                                     "WHERE table_name = ANY(:t) AND :s IS NOT NULL",
                                              t=list(COLD_TABLES))]
    assert columns and not [k for k in columns if any(w in k for w in CLAIMS)]
    assert counts(built) == [1, 1]

    # Exact replay (omitted or explicit equal cutoff) is 200 with the same body; changed body or cutoff is 409.
    assert post(c, body, status=200) == out
    assert post(c, body, f"{W}&known_at={window['cutoff']}", status=200) == out
    refused_post(c, {**body, "name": "Another name"}, 409, "COLD_SCENARIO_IDEMPOTENCY_CONFLICT")
    earlier = (_at(window["cutoff"]) - timedelta(microseconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    refused_post(c, body, 409, "COLD_SCENARIO_IDEMPOTENCY_CONFLICT", f"{W}&known_at={earlier}")
    refused_post(c, body, 409, "COLD_SCENARIO_IDEMPOTENCY_CONFLICT", OTHER_W)
    assert counts(built) == [1, 1]

    # Closed body, decimal grammar, unit, ISO currency and name: 422 COLD_SCENARIO_INVALID, nothing written.
    bad_bodies = [
        {**command_body("bad-key-0001"), "extra": 1},
        {k: v for k, v in command_body("bad-key-0002").items() if k != "name"},
        command_body("bad-key-0003", schema_version="cold-scenario-command-2"),
        command_body("bad-key-0004", kind="SPOILAGE"),
        command_body("short"),
        command_body("bad-key-0005", name="   "),
        command_body("bad-key-0006", name="n" * 161),
        command_body("bad-key-0007", actor={"kind": "SERVICE", "id": PRINCIPAL, "attestation": ATTEST, "x": 1}),
        command_body("bad-key-0008", assumptions={**ASSUMPTIONS, "spoilage_rate": "0.1"}),
        command_body("bad-key-0009", assumptions={k: v for k, v in ASSUMPTIONS.items() if k != "currency"}),
        command_body("bad-key-0010", supersedes_revision_id=out["revision_id"]),
        [], "text",
    ]
    for value in ("0", "0.0", "-1", "+1", "1e3", ".5", "5.", "01", "1.123456789", "1234567890123456789", "1,5",
                  " 1", 5, None, "NaN", "Infinity"):
        bad_bodies.append(command_body("bad-dec-0001", assumptions={**ASSUMPTIONS, "stock_quantity": value}))
        bad_bodies.append(command_body("bad-dec-0002", assumptions={**ASSUMPTIONS, "unit_value": value}))
    for unit in ("", "   ", "k" * 65, "kg\x07", "\tkg\nx", 3):
        bad_bodies.append(command_body("bad-unit-001", assumptions={**ASSUMPTIONS, "stock_unit": unit}))
    for money in ("usd", "US", "USDD", "ABC", "XYZ", " USD", 840, None):
        bad_bodies.append(command_body("bad-cur-0001", assumptions={**ASSUMPTIONS, "currency": money}))
    for bad in bad_bodies:
        refused_post(c, bad, 422, "COLD_SCENARIO_INVALID")
    refusal(c.post(f"{ROUTE}?{W}", content=b"{not json", headers={"content-type": "application/json"}), 422,
            "COLD_SCENARIO_INVALID")
    assert counts(built) == [1, 1]
    # Boundary decimals and labels are accepted verbatim.
    edge = post(c, command_body("seed-edge-0001", name="n" * 160, assumptions={
        "stock_quantity": "0.00000001", "stock_unit": "u" * 64, "unit_value": "999999999999999999.99999999",
        "currency": "EUR"}))
    assert stored(built, edge["id"])[0]["assumptions"] == {
        "stock_quantity": "0.00000001", "stock_unit": "u" * 64, "unit_value": "999999999999999999.99999999",
        "currency": "EUR"}

    # Principal and actor policy (merged mini-decision admit/authorize), before the body.
    refused_post(scenarios_client(built, principal=False), command_body("pol-key-0001"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, principal_site=uuid4()), command_body("pol-key-0002"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, command=lambda request, code: 403), command_body("pol-key-0003"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, command=lambda request, code: 401), command_body("pol-key-0004"), 401,
                 "UNAUTHENTICATED")
    refused_post(c, command_body("pol-key-0005", actor={"kind": "USER", "id": "user:1", "attestation": "x"}), 403,
                 "DECISION_USER_AUTH_REQUIRED")
    for actor in ({"kind": "SERVICE", "id": PRINCIPAL, "attestation": "signed"},
                  {"kind": "SERVICE", "id": "service:other", "attestation": "service=other;job=j;rule=r"},
                  {"kind": "SERVICE", "id": PRINCIPAL, "attestation": "service=other;job=j;rule=r"}):
        refused_post(c, command_body("pol-key-0006", actor=actor), 422, "DECISION_ATTESTATION_INVALID")
    refused_post(c, command_body("pol-key-0007", actor=None), 422, "COLD_SCENARIO_INVALID")

    # Window and basis: both bounds required; no selected assessment; future cutoff.
    refused_post(c, command_body("win-key-0001"), 422, "COLD_WINDOW_INVALID", "")
    refused_post(c, command_body("win-key-0002"), 422, "COLD_WINDOW_INVALID", f"from={LO}")
    refused_post(c, command_body("win-key-0003"), 422, "COLD_SCENARIO_INVALID", EMPTY_W)
    refused_post(c, command_body("win-key-0004"), 422, "COLD_TIME_INVALID", f"{W}&known_at=2099-01-01T00:00:00Z")
    refused_post(c, command_body("win-key-0005"), 422, "COLD_PARAMETER_UNKNOWN", f"{W}&scenario_at={LO}")
    assert counts(built) == [2, 2]

    # Corrections: same window appends; stale predecessor 409; foreign or unknown IDs; cross-window 422.
    path = f"/{out['id']}/revisions"
    fixed = post(c, correction_body("seed-fix-00001", out["revision_id"],
                                    assumptions={**ASSUMPTIONS, "stock_quantity": "1100"}), path=path)
    assert list(fixed) == WRITE_KEYS and (fixed["id"], fixed["code"], fixed["revision_no"]) == \
        (out["id"], out["code"], 2)
    first, second = stored(built, out["id"])
    assert str(second["supersedes_revision_id"]) == out["revision_id"]
    assert second["correction_reason"] == "Corrected stock count" and second["recorded_at"] > first["recorded_at"]
    assert second["authored_basis"] == expected["authored_basis"]
    fix_window = {"from": window["from"], "to": window["to"], "cutoff": second["authored_basis"]["cutoff"]}
    assert second["payload_sha256"] == _sha256({
        "command": canonical_command(correction_body("x", out["revision_id"],
                                                     assumptions={**ASSUMPTIONS, "stock_quantity": "1100"})),
        "root_id": out["id"], "window": fix_window})
    assert post(c, correction_body("seed-fix-00001", out["revision_id"],
                                   assumptions={**ASSUMPTIONS, "stock_quantity": "1100"}), path=path,
                status=200) == fixed
    refused_post(c, correction_body("seed-fix-00001", out["revision_id"]), 409,
                 "COLD_SCENARIO_IDEMPOTENCY_CONFLICT", path=path)
    refused_post(c, correction_body("seed-fix-00002", out["revision_id"]), 409, "COLD_SCENARIO_REVISION_CONFLICT",
                 path=path)
    refused_post(c, correction_body("seed-fix-00003", str(uuid4())), 422, "DECISION_LINK_SCOPE_INVALID", path=path)
    refused_post(c, correction_body("seed-fix-00004", edge["revision_id"]), 422, "DECISION_LINK_SCOPE_INVALID",
                 path=path)
    refused_post(c, correction_body("seed-fix-00005", fixed["revision_id"]), 422, "COLD_SCENARIO_INVALID",
                 OTHER_W, path=path)
    refused_post(c, correction_body("seed-fix-00006", fixed["revision_id"]), 404, "DECISION_NOT_FOUND",
                 path=f"/{uuid4()}/revisions")
    refused_post(c, correction_body("seed-fix-00007", fixed["revision_id"]), 404, "DECISION_NOT_FOUND",
                 path="/not-a-uuid/revisions")
    refused_post(scenarios_client(built, site_id=uuid4()), correction_body("seed-fix-00008", fixed["revision_id"]),
                 404, "DECISION_NOT_FOUND", path=path)  # a foreign Site's root is not found in this scope
    refused_post(c, {**correction_body("seed-fix-00009", fixed["revision_id"]), "correction_reason": " "}, 422,
                 "COLD_SCENARIO_INVALID", path=path)
    refused_post(c, command_body("seed-fix-00010"), 422, "COLD_SCENARIO_INVALID", path=path)
    assert counts(built) == [3, 2]  # (revisions, roots)


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_pending_historical_list_and_cursor(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    c = scenarios_client(built)
    empty = listed(c)
    assert list(empty) == LIST_KEYS and empty["items"] == [] and empty["next_cursor"] is None
    assert empty["total_pages"] == 0  # Q-C5b-2: no selected rows
    assert empty["schema_version"] == "cold-scenarios-1" and empty["site_id"] == str(built.site_id)
    assert empty["window"]["committed_watermark"] is not None  # watermarked empty: no authored row in scope
    first = post(c, command_body("late-key-0001"))
    page = listed(c)
    w0 = page["window"]["known_at"]
    assert page["selection"]["state"] == "CURRENT" and w0 == page["window"]["committed_watermark"]
    assert page["selection"] == basis_on(built)["selection"]
    [item] = page["items"]
    assert list(item) == ITEM_KEYS and (item["id"], item["revision_id"], item["scenario_state"]) == \
        (first["id"], first["revision_id"], "DEFINED")
    assert item["authored_basis"] == basis_on(built)["authored_basis"] and item["code"] == first["code"]
    assert_no_claim(page)
    saved_at = page["scenario_at"]  # the GET after the first write fixes the authored clock
    assert _at(item["recorded_at"]) <= _at(saved_at)
    assert listed(c, "")["window"]["from"] is not None  # no window: the latest selected window

    built.advance_late()  # new committed evidence, worker not run: the selection is pending
    pending = listed(c)
    assert pending["selection"]["state"] == "PENDING_RECOMPUTE"
    assert pending["window"]["committed_watermark"] > w0
    assert [i["id"] for i in pending["items"]] == [first["id"]]
    # Replay after the evidence advance answers from the stored hash and prior cutoff.
    assert post(c, command_body("late-key-0001"), status=200) == first
    refused_post(c, command_body("late-key-0001"), 409, "COLD_SCENARIO_IDEMPOTENCY_CONFLICT",
                 f"{W}&known_at={pending['window']['committed_watermark']}")
    second = post(c, command_body("late-key-0002", name="Second stock lot"))  # saved with its actual state/cutoff
    [second_rev] = stored(built, second["id"])
    assert second_rev["authored_basis"]["cutoff"] == pending["window"]["committed_watermark"]
    # A later correction at a later DB instant.
    fixed = post(c, correction_body("late-fix-0001", first["revision_id"]), path=f"/{first['id']}/revisions")
    refused_post(c, correction_body("late-fix-0002", fixed["revision_id"]), 422, "COLD_SCENARIO_INVALID", OTHER_W,
                 path=f"/{first['id']}/revisions")
    now = listed(c)
    assert [(i["id"], i["revision_id"], i["scenario_state"]) for i in now["items"]] == [
        (first["id"], fixed["revision_id"], "DEFINED"), (second["id"], second["revision_id"], "DEFINED")]
    # Q-C5b-2: the count is of selected heads only; the superseded revision 1 is never counted.
    assert now["total_pages"] == 1 and listed(c, f"{W}&limit=1")["total_pages"] == 2
    # Historical correction view: the saved authored clock shows revision 1 as HISTORICAL; the later rows are absent.
    then = listed(c, f"{W}&scenario_at={saved_at}")
    assert then["scenario_at"] == saved_at
    assert [(i["id"], i["revision_id"], i["scenario_state"]) for i in then["items"]] == [
        (first["id"], first["revision_id"], "HISTORICAL")]
    # Q-C5b-2: historical revision selection counts revision 1 alone at the saved authored clock.
    assert listed(c, f"{W}&scenario_at={saved_at}&limit=1")["total_pages"] == 1
    # The earlier evidence cutoff: every row is HISTORICAL; rows with a later cutoff are absent.
    old = listed(c, f"{W}&known_at={w0}")
    assert old["selection"]["state"] == "HISTORICAL" and old["window"]["known_at"] == w0
    assert [(i["id"], i["revision_id"], i["scenario_state"]) for i in old["items"]] == [
        (first["id"], first["revision_id"], "HISTORICAL")]
    refused_get(c, f"{W}&scenario_at=2099-01-01T00:00:00Z", 422, "COLD_TIME_INVALID")
    refused_get(c, f"{W}&scenario_at=yesterday", 422, "COLD_TIME_INVALID")
    refused_get(c, f"{W}&known_at=2099-01-01T00:00:00Z", 422, "COLD_TIME_INVALID")

    # Cursor: page one of two binds the selection; new evidence before page two is 409 basis changed.
    one = listed(c, f"{W}&limit=1")
    assert len(one["items"]) == 1 and one["next_cursor"]
    two = listed(c, f"{W}&cursor={one['next_cursor']}")
    assert [i["id"] for i in one["items"] + two["items"]] == [first["id"], second["id"]]
    assert two["next_cursor"] is None and two["scenario_at"] == one["scenario_at"]
    run(built)  # the worker's new assessment changes the selection
    refused_get(c, f"cursor={one['next_cursor']}", 409, "COLD_SCENARIO_CURSOR_BASIS_CHANGED")
    current = listed(c)
    assert current["selection"]["state"] == "CURRENT"
    assert {i["scenario_state"] for i in current["items"]} == {"DEFINED"}


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_list_51_rows_and_cursor_refusals(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = scenarios_client(built)
    made = [post(c, command_body(f"page-key-{n:04d}", name=f"Lot {n}"))["id"] for n in range(51)]
    one = listed(c)
    assert len(one["items"]) == 50 and one["next_cursor"]
    stamps = [(_at(i["recorded_at"]), i["revision_id"]) for i in one["items"]]
    assert stamps == sorted(stamps, reverse=True)
    two = listed(c, f"cursor={one['next_cursor']}")
    assert len(two["items"]) == 1 and two["next_cursor"] is None
    assert (one["total_pages"], two["total_pages"]) == (2, 2)  # Q-C5b-2: ceil(51 / 50) on both pages
    assert (two["window"], two["selection"], two["scenario_at"]) == (one["window"], one["selection"],
                                                                     one["scenario_at"])
    assert sorted(i["id"] for i in one["items"] + two["items"]) == sorted(made)
    assert listed(c, f"{W}&known_at={one['window']['known_at']}&scenario_at={one['scenario_at']}&limit=50"
                     f"&cursor={one['next_cursor']}")["items"] == two["items"]
    # Explicit values that differ from the cursor's bound clocks, window or limit are a changed basis.
    cursor = one["next_cursor"]
    refused_get(c, f"limit=10&cursor={cursor}", 409, "COLD_SCENARIO_CURSOR_BASIS_CHANGED")
    refused_get(c, f"scenario_at={one['items'][0]['recorded_at']}&cursor={cursor}", 409,
                "COLD_SCENARIO_CURSOR_BASIS_CHANGED")
    refused_get(c, f"{OTHER_W}&cursor={cursor}", 409, "COLD_SCENARIO_CURSOR_BASIS_CHANGED")
    earlier = (_at(one["window"]["known_at"]) - timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    refused_get(c, f"known_at={earlier}&cursor={cursor}", 409, "COLD_SCENARIO_CURSOR_BASIS_CHANGED")
    for bad in ("garbage", "e30", cursor[:-4]):
        refused_get(c, f"cursor={bad}", 422, "COLD_SCENARIO_CURSOR_INVALID")
    foreign = scenarios_client(built, site_id=uuid4())
    refusal(foreign.get(f"{ROUTE}?cursor={cursor}"), 422, "COLD_SCENARIO_CURSOR_INVALID")
    for limit in ("0", "101", "x", "-1", "1.5"):
        refused_get(c, f"limit={limit}", 422, "COLD_LIMIT_INVALID")
    hundred = listed(c, "limit=100")
    assert len(hundred["items"]) == 51 and hundred["total_pages"] == 1


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_router_statuses_and_store_failures(chain) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    run(built)
    c = scenarios_client(built)
    body = command_body("route-key-001")
    for client, status, code in (
            (scenarios_client(built, access=lambda request, code: 401), 401, "UNAUTHENTICATED"),
            (scenarios_client(built, access=lambda request, code: 403), 403, "SITE_SCOPE_FORBIDDEN"),
            (scenarios_client(built, disclosure=lambda code, t, s: False), 403, "COLD_SOURCE_DISCLOSURE_FORBIDDEN"),
            (scenarios_client(built, site_type="MINIGRID"), 404, "SITE_NOT_FOUND"),
            (scenarios_client(built, down=True), 503, "COLD_READ_UNAVAILABLE"),
            (scenarios_client(built, service=False), 503, "DECISION_STORE_UNAVAILABLE"),
            (scenarios_client(built, store_url=DOWN), 503, "DECISION_STORE_UNAVAILABLE"),
            (scenarios_client(built, link_rows=False), 503, "COLD_READ_UNAVAILABLE")):
        refusal(client.get(f"{ROUTE}?{W}"), status, code)
        refusal(client.post(f"{ROUTE}?{W}", json=body), status, code)
    refusal(c.get(f"/api/sites/NOPE/cold/financials/scenarios?{W}"), 404, "SITE_NOT_FOUND")
    refusal(c.post(f"/api/sites/NOPE/cold/financials/scenarios?{W}", json=body), 404, "SITE_NOT_FOUND")
    for query, status, code in (
            (f"{W}&page=1", 422, "COLD_PARAMETER_UNKNOWN"),
            (f"{W}&from={LO}", 422, "COLD_PARAMETER_UNKNOWN"),
            (f"{W}&known_at={HI}&known_at={HI}", 422, "COLD_PARAMETER_UNKNOWN"),
            (f"from={LO}", 422, "COLD_WINDOW_INVALID"),
            (f"from={HI}&to={LO}", 422, "COLD_WINDOW_INVALID"),
            ("from=2026-09-01T00:00:00Z&to=2026-10-06T00:00:00Z", 422, "COLD_WINDOW_TOO_LONG"),
            ("from=2026-10-06T19:00:00&to=2026-10-06T20:00:00Z", 422, "COLD_TIME_INVALID"),
            ("from=2026-10-06T19:00:00.1234567Z&to=2026-10-06T20:00:00Z", 422, "COLD_TIME_INVALID"),
            ("from=2026-10-06T19:00:00%2B01:00&to=2026-10-06T20:00:00Z", 422, "COLD_TIME_INVALID")):
        refused_get(c, query, status, code)
        refused_post(c, body, status, code, query)
    refused_get(c, f"{W}&cursor=a&cursor=b", 422, "COLD_PARAMETER_UNKNOWN")
    refusal(c.post(f"{ROUTE}/{uuid4()}/revisions?{W}&limit=1", json=body), 422, "COLD_PARAMETER_UNKNOWN")
    # A store failure in the read leaves no partial write; the malformed persisted basis is 503.
    assert counts(built) == [0, 0]
    made = post(c, body)
    good = stored(built, made["id"])[0]["authored_basis"]
    for n, basis in enumerate(({**good, "cutoff": "not-a-time"}, {**good, "extra": 1})):
        root, rev = uuid4(), uuid4()
        with built.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO cold_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
                "create_actor_id, actor_kind, actor_id) VALUES (:id, :t, :s, :k, :h, 'svc', 'SERVICE', 'svc')"),
                {"id": root, "t": built.tenant_id, "s": built.site_id, "k": f"malformed-{n:04d}", "h": _sha("c")})
            conn.execute(text(
                "INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, name, kind, "
                "assumptions, authored_basis, basis_sha256, formula_version, actor_kind, actor_id, "
                "authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :r, 1, "
                "'Malformed', 'STOCK_VALUE_CONTEXT', CAST(:a AS jsonb), CAST(:b AS jsonb), :h, 'AUTHORED_ONLY/1', "
                "'SERVICE', 'svc', 'basis', 'attested', :k, :h)"),
                {"id": rev, "t": built.tenant_id, "s": built.site_id, "r": root, "a": json.dumps(ASSUMPTIONS),
                 "b": json.dumps(basis), "h": _sha("b"), "k": f"malformed-{n:04d}"})
        refused_get(c, W, 503, "DECISION_STORE_UNAVAILABLE")
        _replica(built.engine, f"DELETE FROM cold_scenario_revision WHERE id = '{rev}'",
                 f"DELETE FROM cold_scenario WHERE id = '{root}'")
    assert [i["id"] for i in listed(c)["items"]] == [made["id"]]


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set")
def test_list_malformed_stored_basis_is_503(chain) -> None:  # noqa: F811
    """Q-C5b item 5: a candidate revision whose stored basis lacks from/to/cutoff is 503, never a partial 200."""
    built = opened("backup-failed", chain)
    run(built)
    c = scenarios_client(built)
    made = post(c, command_body("shape-key-0001"))
    good = stored(built, made["id"])[0]
    basis = good["authored_basis"]
    assert [i["id"] for i in listed(c)["items"]] == [made["id"]]
    revision = ("INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, "
                "supersedes_revision_id, name, kind, assumptions, authored_basis, basis_sha256, formula_version, "
                "correction_reason, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
                "payload_sha256) VALUES (:id, :t, :s, :r, :n, :p, 'Malformed', 'STOCK_VALUE_CONTEXT', "
                "CAST(:a AS jsonb), CAST(:b AS jsonb), :h, 'AUTHORED_ONLY/1', :why, 'SERVICE', 'svc', 'basis', "
                "'attested', :k, :h)")
    # A new root whose revision 1 fixes the window but lacks its cutoff (the cutoff predicate would drop it).
    root, rev = uuid4(), uuid4()
    with built.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO cold_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
            "create_actor_id, actor_kind, actor_id) VALUES (:id, :t, :s, 'shape-0001', :h, 'svc', 'SERVICE', 'svc')"),
            {"id": root, "t": built.tenant_id, "s": built.site_id, "h": _sha("c")})
        conn.execute(text(revision), {
            "id": rev, "t": built.tenant_id, "s": built.site_id, "r": root, "n": 1, "p": None, "why": None,
            "a": json.dumps(ASSUMPTIONS), "b": json.dumps({k: v for k, v in basis.items() if k != "cutoff"}),
            "h": _sha("b"), "k": "shape-0001"})
    for query in (W, f"{W}&limit=1", ""):
        response = c.get(f"{ROUTE}?{query}" if query else ROUTE)
        refusal(response, 503, "DECISION_STORE_UNAVAILABLE")
        assert "items" not in response.json()
    _replica(built.engine, f"DELETE FROM cold_scenario_revision WHERE id = '{rev}'",
             f"DELETE FROM cold_scenario WHERE id = '{root}'")
    assert [i["id"] for i in listed(c)["items"]] == [made["id"]]
    # A later correction of the well-formed root that lacks 'to' is equally malformed history.
    rev2 = uuid4()
    with built.engine.begin() as conn:
        conn.execute(text(revision), {
            "id": rev2, "t": built.tenant_id, "s": built.site_id, "r": good["scenario_id"], "n": 2,
            "p": good["id"], "why": "Corrected stock count", "a": json.dumps(ASSUMPTIONS),
            "b": json.dumps({k: v for k, v in basis.items() if k != "to"}), "h": _sha("b"), "k": "shape-0002"})
    refused_get(c, W, 503, "DECISION_STORE_UNAVAILABLE")
    _replica(built.engine, f"DELETE FROM cold_scenario_revision WHERE id = '{rev2}'")
    assert [i["id"] for i in listed(c)["items"]] == [made["id"]]


def test_list_malformed_root_window_is_503(chain) -> None:  # noqa: F811
    """Q-C5c item 3: a Site root whose revision 1 lacks `from` or `to` has no trustworthy window, so it makes every
    list of that tenant and Site a 503 (never a partial 200); another Site's malformed root does not poison it, and
    an authored clock before the malformed revision still lists the valid root."""
    built = opened("backup-failed", chain)
    run(built)
    c = scenarios_client(built)
    made = post(c, command_body("root-key-0001"))
    basis = stored(built, made["id"])[0]["authored_basis"]
    before = listed(c)
    assert [i["id"] for i in before["items"]] == [made["id"]]
    saved_at = before["scenario_at"]
    # A second Site of the same tenant (test-only row copied from the fixture Site).
    other_site = uuid4()
    code = f"W501-OTHER-{other_site.hex[:8]}"
    with built.engine.connect() as conn:
        cols = [r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'site' ORDER BY ordinal_position"))]
    pick = {"id": f"'{other_site}'", "site_code": f"'{code}'", "site_code_key": f"'{code.lower()}'"}
    _replica(built.engine, f"INSERT INTO site ({', '.join(cols)}) SELECT {', '.join(pick.get(x, x) for x in cols)} "
                           f"FROM site WHERE id = '{built.site_id}'")
    revision = ("INSERT INTO cold_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, "
                "supersedes_revision_id, name, kind, assumptions, authored_basis, basis_sha256, formula_version, "
                "correction_reason, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
                "payload_sha256) VALUES (:id, :t, :s, :r, 1, NULL, 'Malformed', 'STOCK_VALUE_CONTEXT', "
                "CAST(:a AS jsonb), CAST(:b AS jsonb), :h, 'AUTHORED_ONLY/1', NULL, 'SERVICE', 'svc', 'basis', "
                "'attested', :k, :h)")

    def malformed_root(site_id, key: str, missing: str):
        root, rev = uuid4(), uuid4()
        with built.engine.begin() as conn:
            conn.execute(text(
                "INSERT INTO cold_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
                "create_actor_id, actor_kind, actor_id) VALUES (:id, :t, :s, :k, :h, 'svc', 'SERVICE', 'svc')"),
                {"id": root, "t": built.tenant_id, "s": site_id, "k": key, "h": _sha("c")})
            conn.execute(text(revision), {
                "id": rev, "t": built.tenant_id, "s": site_id, "r": root, "a": json.dumps(ASSUMPTIONS),
                "b": json.dumps({k: v for k, v in basis.items() if k != missing}), "h": _sha("b"), "k": key})
        return root, rev

    def remove(root, rev) -> None:
        _replica(built.engine, f"DELETE FROM cold_scenario_revision WHERE id = '{rev}'",
                 f"DELETE FROM cold_scenario WHERE id = '{root}'")

    # Another Site's malformed root (missing 'from') does not poison this Site's list.
    foreign = malformed_root(other_site, "root-0000", "from")
    assert [i["id"] for i in listed(c)["items"]] == [made["id"]]
    assert [i["id"] for i in listed(c, f"{W}&limit=1")["items"]] == [made["id"]]
    for key, missing in (("root-0001", "from"), ("root-0002", "to")):
        root, rev = malformed_root(built.site_id, key, missing)
        for query in (W, f"{W}&limit=1"):
            response = c.get(f"{ROUTE}?{query}")
            refusal(response, 503, "DECISION_STORE_UNAVAILABLE")
            assert "items" not in response.json()
        # The authored clock before the malformed revision still lists the valid root.
        assert [i["id"] for i in listed(c, f"{W}&scenario_at={saved_at}")["items"]] == [made["id"]]
        remove(root, rev)
        assert [i["id"] for i in listed(c)["items"]] == [made["id"]]
    remove(*foreign)
    _replica(built.engine, f"DELETE FROM site WHERE id = '{other_site}'")
