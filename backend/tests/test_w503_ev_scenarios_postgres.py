"""W5-03b unit E5: authored EV scenario store, migration `0034_w5_ev_scenarios`, command/list service and API.

`.agent/W5-03-build-spec.md` E5 card, "E5 exact persisted schema and wire contract", "E5 consolidated correction"
(P-E5-1..10) and P-34-2/3. The persisted positive producer is the in-process POST over W2-05b's registered `Chain`
(`ev_depth_cases.py`, window `[2026-10-06T08:00Z, 09:00Z)`), with the E1 selected IDs. Requires
ASSETOPS_TEST_DATABASE_URL for every test except the pure rules tests.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from assetops_backend.ev_scenarios import rules
from assetops_backend.mini_decisions.model import DecisionRefused
from ev_depth_cases import HI, HISTORICAL_KNOWN_AT, LO, QUERY, URL, chain, pending, settled  # noqa: F401

needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_s4_consequence_store_postgres import site  # noqa: F401
    from test_w203_cold_migration_postgres import _replica, head, scalar
    from test_w207_ev_money_postgres import EV_KEY, GOLDEN_FROM, GOLDEN_TO, ev_money_rows, golden_tariff, money, money_head
    from test_w402_migration_postgres import downgrade_config

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService
    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.ev_scenarios.service import EvScenarioService
    from assetops_backend.ev_scenarios.store import PostgresEvScenarioStore
    from assetops_backend.ev_scenarios_api import build_ev_scenarios_router
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication
    from assetops_backend.financials.composition import build_ev_site_read_service
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal
    from assetops_backend.sites.ports import SiteStoreUnavailable

HEAD = "0034_w5_ev_scenarios"
PREVIOUS = "0033_w5_cold_work"
REFUSED = "Downgrade of 0034_w5_ev_scenarios refused: EV scenario history exists"
TABLES = ("ev_scenario_revision", "ev_scenario")
SEQUENCE = "ev_scenario_public_no_seq"
COLUMNS = {
    "ev_scenario": ["id", "tenant_id", "site_id", "public_no", "create_key", "create_payload_sha256",
                    "create_actor_id", "created_at", "actor_kind", "actor_id"],
    "ev_scenario_revision": ["id", "tenant_id", "site_id", "scenario_id", "revision_no", "supersedes_revision_id",
                             "name", "kind", "assumptions", "authored_basis", "basis_sha256", "formula_version",
                             "correction_reason", "actor_kind", "actor_id", "authorization_basis", "attestation",
                             "idempotency_key", "payload_sha256", "recorded_at"],
}
CATALOG = {
    "p": ["ev_scenario_pkey", "ev_scenario_revision_pkey"],
    "u": sorted(["ev_scenario_scope_uk", "ev_scenario_public_no_uk", "ev_scenario_create_key_uk",
                 "ev_scenario_revision_scope_uk", "ev_scenario_revision_no_uk", "ev_scenario_revision_previous_uk",
                 "ev_scenario_revision_key_uk"]),
    "f": sorted(["ev_scenario_site_fk", "ev_scenario_revision_scenario_fk", "ev_scenario_revision_previous_fk"]),
    "c": sorted(["ev_scenario_create_key_check", "ev_scenario_create_payload_sha256_check",
                 "ev_scenario_create_actor_id_check", "ev_scenario_revision_revision_no_check",
                 "ev_scenario_revision_name_check", "ev_scenario_revision_kind_check",
                 "ev_scenario_revision_formula_check", "ev_scenario_revision_chain_check",
                 "ev_scenario_revision_basis_sha256_check", "ev_scenario_revision_payload_sha256_check",
                 "ev_scenario_revision_idempotency_key_check", "ev_scenario_revision_actor_check",
                 "ev_scenario_revision_assumptions_check", "ev_scenario_revision_authored_basis_check"]),
}
FK_TARGETS = {
    "ev_scenario_site_fk": ("site", ["tenant_id", "site_id"]),
    "ev_scenario_revision_scenario_fk": ("ev_scenario", ["tenant_id", "site_id", "scenario_id"]),
    "ev_scenario_revision_previous_fk": ("ev_scenario_revision", ["tenant_id", "site_id", "supersedes_revision_id"]),
}
INDEX = ("CREATE INDEX ev_scenario_site_order ON public.ev_scenario_revision USING btree "
         "(tenant_id, site_id, recorded_at DESC, id)")

CODE = "EV-LAB-001"
ROUTE = f"/api/sites/{CODE}/ev/financials/scenarios"
OTHER_W = "from=2026-10-06T08:00:00Z&to=2026-10-06T08:30:00Z"
EMPTY_W = "from=2026-10-05T08:00:00Z&to=2026-10-05T09:00:00Z"
WATERMARK = "2026-10-06T09:00:00.000000Z"
DOWN = "postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=2"
PRINCIPAL = "service:ev-scenario-seed"
ATTEST = "service=ev-scenario-seed;job=w503b-e5;rule=AUTHORED_ONLY/1"
WRITE_KEYS = ["schema_version", "id", "code", "revision_id", "revision_no"]
LIST_KEYS = ["schema_version", "site_id", "window", "scenario_at", "selection", "items", "next_cursor"]
WINDOW_KEYS = ["from", "to", "known_at", "committed_watermark"]
SELECTION_KEYS = ["state", "assessment_revision_id", "session_revision_ids", "accepted_evidence_ids",
                  "source_provenance"]
ITEM_KEYS = ["id", "code", "revision_id", "revision_no", "name", "kind", "assumptions", "authored_basis",
             "recorded_at", "scenario_state"]
BASIS_KEYS = ["from", "to", "cutoff", "assessment_revision_id", "session_revision_ids", "accepted_evidence_ids",
              "foundation_revision_id", "consequence_revision_id", "tariff_revision_id", "source_provenance"]
CLAIMS = ("revenue", "collect", "lost", "saving", "amount", "outcome", "delta", "observed", "verified")
ASSUMPTIONS = {"tariff_per_kwh": "0.31", "currency": "KES"}


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


# --- pure rules ---------------------------------------------------------------------------------------------


def command_body(key: str, **over) -> dict:
    body = {"schema_version": "ev-scenario-command-1", "idempotency_key": key,
            "actor": {"kind": "SERVICE", "id": PRINCIPAL, "attestation": ATTEST},
            "name": "Gross tariff context", "kind": "GROSS_TARIFF_CONTEXT", "assumptions": dict(ASSUMPTIONS)}
    body.update(over)
    return body


def correction_body(key: str, previous: str, **over) -> dict:
    return command_body(key, supersedes_revision_id=previous, correction_reason="Corrected tariff", **over)


def test_rules_closed_command_and_assumptions() -> None:
    cmd = rules.parse_command(command_body("rules-key-0001", name="  Tariff  "), correction=False)
    assert cmd["name"] == "Tariff" and cmd["assumptions"] == ASSUMPTIONS and cmd["kind"] == "GROSS_TARIFF_CONTEXT"
    assert rules.scenario_code(1) == "ESCN-000001" and rules.scenario_code(1234567) == "ESCN-1234567"
    for value in ("0", "-1", "1e3", ".5", "5.", "01", "0.123456789", 1, None, "NaN"):
        with pytest.raises(DecisionRefused) as error:
            rules.assumptions({"tariff_per_kwh": value, "currency": "KES"})
        assert error.value.code == "EV_SCENARIO_INVALID", value
    assert rules.assumptions({"tariff_per_kwh": "0.12345678", "currency": "USD"})["tariff_per_kwh"] == "0.12345678"
    for currency in ("kes", "KE", "ZZZ", "KESX", None):
        with pytest.raises(DecisionRefused):
            rules.assumptions({"tariff_per_kwh": "1", "currency": currency})
    bad = [command_body("rules-key-0002", extra=1), command_body("rules-key-0003", kind="STOCK_VALUE_CONTEXT"),
           command_body("rules-key-0004", schema_version="cold-scenario-command-1"),
           command_body("rules-key-0005", assumptions={**ASSUMPTIONS, "amount": "9"}),
           command_body("rules-key-0006", authored_basis={}), command_body("short")]
    for body in bad:
        with pytest.raises(DecisionRefused) as error:
            rules.parse_command(body, correction=False)
        assert error.value.code == "EV_SCENARIO_INVALID"
    with pytest.raises(DecisionRefused):
        rules.parse_command(command_body("rules-key-0007"), correction=True)  # no supersedes/reason
    assert set(rules.BASIS_KEYS) == set(BASIS_KEYS)
    assert not any(c in k for k in rules.BASIS_KEYS + rules.ASSUMPTION_KEYS for c in CLAIMS)


# --- schema -------------------------------------------------------------------------------------------------


def catalog(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        tables = sorted(c.execute(text("SELECT relname FROM pg_class WHERE relkind = 'r' AND relname = ANY(:t)"),
                                  {"t": list(TABLES)}).scalars())
        columns = {t: list(c.execute(text(
            "SELECT attname FROM pg_attribute WHERE attrelid = to_regclass(:t) AND attnum > 0 AND NOT attisdropped "
            "ORDER BY attnum"), {"t": t}).scalars()) for t in tables}
        named = {k: sorted(c.execute(text(
            "SELECT conname FROM pg_constraint WHERE contype = :k AND conrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t) AND relkind = 'r')"),
            {"k": k, "t": list(TABLES)}).scalars()) for k in ("p", "u", "f", "c")}
        fks = {r[0]: (r[1], list(r[2])) for r in c.execute(text(
            "SELECT conname, confrelid::regclass::text, (SELECT array_agg(attname ORDER BY array_position(conkey, "
            "attnum)) FROM pg_attribute WHERE attrelid = conrelid AND attnum = ANY(conkey)) FROM pg_constraint "
            "WHERE contype = 'f' AND conname = ANY(:n)"), {"n": list(FK_TARGETS)})}
        index = c.execute(text("SELECT indexdef FROM pg_indexes WHERE indexname = 'ev_scenario_site_order'")).scalar()
        triggers = sorted(tuple(r) for r in c.execute(text(
            "SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger WHERE NOT tgisinternal AND tgrelid IN "
            "(SELECT oid FROM pg_class WHERE relname = ANY(:t))"), {"t": list(TABLES)}))
        sequence = c.execute(text("SELECT count(*) FROM pg_class WHERE relkind = 'S' AND relname = :s"),
                             {"s": SEQUENCE}).scalar_one()
    return {"tables": tables, "columns": columns, "named": named, "fks": fks, "index": index,
            "triggers": triggers, "sequence": sequence}


def expected_catalog() -> dict:
    return {"tables": sorted(TABLES), "columns": COLUMNS, "named": CATALOG, "fks": FK_TARGETS, "index": INDEX,
            "triggers": sorted((f"{t}_immutable", f"CREATE TRIGGER {t}_immutable BEFORE DELETE OR UPDATE ON public.{t} "
                                "FOR EACH ROW EXECUTE FUNCTION ledger_append_only()") for t in TABLES),
            "sequence": 1}


def expected_absent() -> dict:
    return {"tables": [], "columns": {}, "named": {k: [] for k in ("p", "u", "f", "c")}, "fks": {}, "index": None,
            "triggers": [], "sequence": 0}


def _insert_revision(c, tenant_id, site_id, root, *, rid=None, no=1, previous=None, reason=None, kind="GROSS_TARIFF_CONTEXT",
                     formula="AUTHORED_ONLY/1", assumptions="{}", basis="{}", key="idem-key-0001", name="Tariff"):
    c.execute(text(
        "INSERT INTO ev_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, supersedes_revision_id, "
        "name, kind, assumptions, authored_basis, basis_sha256, formula_version, correction_reason, actor_kind, "
        "actor_id, authorization_basis, attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :r, :no, "
        ":p, :name, :kind, CAST(:a AS jsonb), CAST(:b AS jsonb), :h, :f, :why, 'SERVICE', 'svc-1', 'grant', "
        "'attested', :k, :h)"),
        {"id": rid or uuid4(), "t": tenant_id, "s": site_id, "r": root, "no": no, "p": previous, "name": name,
         "kind": kind, "a": assumptions, "b": basis, "h": _sha("x"), "f": formula, "why": reason, "k": key})


@needs_db
def test_schema_constraints(site, engine) -> None:  # noqa: F811
    """Sole head 0034 above exactly 0033; exact 0034 catalog; append-only triggers; named checks; a nonempty
    downgrade is refused and leaves everything; an empty downgrade reaches 0033 without the catalog and re-upgrades."""
    from alembic import command
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [HEAD]
    assert script.get_revision(HEAD).down_revision == PREVIOUS
    assert head(engine) == HEAD and catalog(engine) == expected_catalog()

    with engine.connect() as c:
        tenant_id, site_id = c.execute(text("SELECT tenant_id, id FROM site ORDER BY id LIMIT 1")).one()
    root, rev = uuid4(), uuid4()
    with engine.begin() as c:
        c.execute(text(
            "INSERT INTO ev_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, create_actor_id, "
            "actor_kind, actor_id) VALUES (:id, :t, :s, 'create-key-0001', :h, 'svc-1', 'SERVICE', 'svc-1')"),
            {"id": root, "t": tenant_id, "s": site_id, "h": _sha("create")})
        _insert_revision(c, tenant_id, site_id, root, rid=rev, basis=json.dumps({"from": "2026-10-06T08:00:00Z"}))
    for table, row in (("ev_scenario_revision", rev), ("ev_scenario", root)):
        for sql in (f"UPDATE {table} SET actor_id = 'svc-2' WHERE id = :id", f"DELETE FROM {table} WHERE id = :id"):
            with pytest.raises(DBAPIError):
                with engine.begin() as c:
                    c.execute(text(sql), {"id": row})
    checks = [
        ("ev_scenario_revision_assumptions_check", {"assumptions": "[]", "key": "idem-key-0002"}),
        ("ev_scenario_revision_authored_basis_check", {"basis": "[]", "key": "idem-key-0003"}),
        ("ev_scenario_revision_kind_check", {"kind": "STOCK_VALUE_CONTEXT", "key": "idem-key-0004"}),
        ("ev_scenario_revision_formula_check", {"formula": "AUTHORED/2", "key": "idem-key-0005"}),
        ("ev_scenario_revision_chain_check", {"key": "idem-key-0006", "no": 2}),
        ("ev_scenario_revision_idempotency_key_check", {"key": "short"}),
        ("ev_scenario_revision_name_check", {"name": "  ", "key": "idem-key-0007"}),
        ("ev_scenario_revision_(chain|revision_no)_check", {"no": 0, "key": "idem-key-0008"}),
        ("ev_scenario_revision_no_uk", {"key": "idem-key-0009"}),
        ("ev_scenario_revision_key_uk", {"key": "idem-key-0001", "no": 2, "previous": rev, "reason": "Fix"}),
        ("ev_scenario_revision_previous_fk", {"key": "idem-key-0010", "no": 2, "previous": uuid4(), "reason": "Fix"}),
        ("ev_scenario_revision_scenario_fk", {"key": "idem-key-0011", "root": uuid4()}),
    ]
    for name, over in checks:
        with pytest.raises(DBAPIError, match=name):
            with engine.begin() as c:
                _insert_revision(c, tenant_id, site_id, over.pop("root", root), **over)
    for name, sql in (
            ("ev_scenario_create_key_check", "'short'"),
            ("ev_scenario_create_key_uk", "'create-key-0001'")):
        with pytest.raises(DBAPIError, match=name):
            with engine.begin() as c:
                c.execute(text(
                    "INSERT INTO ev_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
                    f"create_actor_id, actor_kind, actor_id) VALUES (:id, :t, :s, {sql}, :h, 'svc-1', 'SERVICE', "
                    "'svc-1')"), {"id": uuid4(), "t": tenant_id, "s": site_id, "h": _sha("create")})
    with pytest.raises(DBAPIError, match="ev_scenario_site_fk"):
        with engine.begin() as c:
            c.execute(text(
                "INSERT INTO ev_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, create_actor_id, "
                "actor_kind, actor_id) VALUES (:id, :t, :s, 'create-key-0002', :h, 'svc-1', 'SERVICE', 'svc-1')"),
                {"id": uuid4(), "t": tenant_id, "s": uuid4(), "h": _sha("create")})
    assert [scalar(engine, f"SELECT count(*) FROM {t}") for t in TABLES] == [1, 1]

    config = downgrade_config(site, engine)
    try:
        with pytest.raises(DBAPIError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
        assert head(engine) == HEAD and catalog(engine) == expected_catalog()
        assert [scalar(engine, f"SELECT count(*) FROM {t}") for t in TABLES] == [1, 1]
        _replica(engine, f"DELETE FROM ev_scenario_revision WHERE id = '{rev}'",
                 f"DELETE FROM ev_scenario WHERE id = '{root}'")
        engine.dispose()
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS and catalog(engine) == expected_absent()
        engine.dispose()
        command.upgrade(config, "head")
    finally:
        if head(engine) != HEAD:
            engine.dispose()
            command.upgrade(config, "head")
    assert head(engine) == HEAD and catalog(engine) == expected_catalog()
    assert ScriptDirectory.from_config(config).get_heads() == [HEAD]


# --- persisted command, list and router ---------------------------------------------------------------------


def _registry(built, *, site_id=None, site_type="EV_CHARGING", down=False):
    site_ = SimpleNamespace(id=site_id or built.site_id, site_type=site_type)

    def imported(code):
        if down:
            raise SiteStoreUnavailable("The Site store is unavailable.")
        return site_ if code == CODE else None
    return SimpleNamespace(imported=imported, tenant=lambda: SimpleNamespace(id=built.tenant_id))


def scenarios_client(built, *, principal=True, command=None, access=None, disclosure=None, store_url=None,
                     link_rows=True, service=True, site_id=None, site_type="EV_CHARGING", down=False,
                     principal_site=None) -> "TestClient":
    """The in-process E5 producer: the router with an injected `DecisionPrincipal` carrying its own
    `GRANT_PREFIX` grant for the exact tenant/Site (the C4 pattern)."""
    scope = principal_site or site_id or built.site_id
    kw = {"command_access": command or (lambda request, code: None),
          "principal": (lambda request, code: DecisionPrincipal("SERVICE", PRINCIPAL, built.tenant_id, scope,
                                                                GRANT_PREFIX + PRINCIPAL)) if principal
          else (lambda request, code: None)}
    if access is not None:
        kw["access"] = access
    if disclosure is not None:
        kw["disclosure"] = disclosure
    reads = build_ev_read_service(URL) if link_rows else EvReadService(URL)
    svc = (EvScenarioService(PostgresEvScenarioStore.from_url(store_url or URL), reads,
                             build_ev_site_read_service(URL)) if service else None)
    app = FastAPI()
    app.include_router(build_ev_scenarios_router(
        _registry(built, site_id=site_id, site_type=site_type, down=down), svc, **kw))
    return TestClient(app)


def post(c, body, query: str = QUERY, status: int = 201, path: str = "") -> dict:
    response = c.post(f"{ROUTE}{path}?{query}", json=body)
    assert response.status_code == status, response.text
    return response.json()


def listed(c, query: str = QUERY, status: int = 200) -> dict:
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


def refused_post(c, body, status: int, code: str, query: str = QUERY, path: str = "") -> None:
    refusal(c.post(f"{ROUTE}{path}?{query}", json=body), status, code)


def refused_get(c, query: str, status: int, code: str) -> None:
    refusal(c.get(f"{ROUTE}?{query}"), status, code)


LATE_DECIDED = datetime(2026, 10, 6, 9, 5, tzinfo=timezone.utc)


def late_import(built, decided_at: datetime) -> str:
    """Test-only: `ev_depth_cases.add_import`'s accepted `ev_site_import` clone with its ACCEPTED disposition decided at
    `decided_at` (a later committed watermark); its enqueue trigger queues a PENDING recompute job over the window,
    the shape of the registered `late-record` release (whose 09:00 session is not energy complete, so it cannot be
    authored first)."""
    new_id = uuid4()
    with built.engine.begin() as c:
        old = c.execute(text("SELECT id, batch_id FROM accepted_evidence WHERE site_id = :s AND role = 'ev_site_import' "
                             "ORDER BY source_time, id LIMIT 1"), {"s": built.site_id}).one()
        c.execute(text("CREATE TEMP TABLE _w503b_e ON COMMIT DROP AS SELECT * FROM accepted_evidence WHERE id = :i"),
                  {"i": old.id})
        c.execute(text("CREATE TEMP TABLE _w503b_d ON COMMIT DROP AS SELECT * FROM ingestion_disposition "
                       "WHERE accepted_evidence_id = :i AND decision = 'ACCEPTED'"), {"i": old.id})
        ordinal = c.execute(text("SELECT max(ordinal) + 1 FROM ingestion_disposition WHERE batch_id = :b"),
                            {"b": old.batch_id}).scalar_one()
        message = f"w503b-late-{new_id}"
        c.execute(text("UPDATE _w503b_e SET id = :n, ordinal = :o, message_id = :m, sequence = sequence + 2000000"),
                  {"n": new_id, "o": ordinal, "m": message})
        c.execute(text("UPDATE _w503b_d SET ordinal = :o, message_id = :m, accepted_evidence_id = :n, decided_at = :d"),
                  {"o": ordinal, "m": message, "n": new_id, "d": decided_at})
        c.execute(text("INSERT INTO accepted_evidence SELECT * FROM _w503b_e"))
        c.execute(text("INSERT INTO ingestion_disposition SELECT * FROM _w503b_d"))
    return str(new_id).lower()


def _query(work):
    from sqlalchemy import create_engine

    eng = create_engine(URL)
    try:
        with eng.connect() as c:
            return work(c)
    finally:
        eng.dispose()


def counts(built) -> list[int]:
    return _query(lambda c: [c.execute(text(f"SELECT count(*) FROM {t} WHERE site_id = :s"),
                                       {"s": built.site_id}).scalar_one() for t in TABLES])


def stored(built, revision_id: str) -> dict:
    return _query(lambda c: dict(c.execute(text("SELECT * FROM ev_scenario_revision WHERE id = :id"),
                                           {"id": revision_id}).mappings().one()))


def selected(built, known_at=None) -> dict:
    """The E1 selected snapshot, its sessions and its meter evidence, read independently of the E5 path."""
    reads = build_ev_read_service(URL)
    try:
        def work(c):
            snap, body = reads.open_on(c, built.tenant_id, built.site_id, CODE, LO, HI, known_at)
            sessions = reads.sessions_on(c, snap)
            complete = sorted(x["revision_id"] for x in sessions if x["energy_complete"] is True)
            meters = sorted({str(r[0]).lower() for r in c.execute(text(
                "SELECT evidence_id FROM ev_meter_interval WHERE site_id = :s AND evidence_id IS NOT NULL "
                "AND revision_id = ANY(CAST(:ids AS uuid[]))"), {"s": built.site_id, "ids": complete})})
            return {"snap": snap, "body": body, "complete": complete, "meters": meters,
                    "foundation": reads.foundation_revision_on(c, snap),
                    "accepted": {str(r["evidence_id"]).lower() for r in reads.accepted_on(c, snap)},
                    "provenance": reads.selected_provenance_on(c, snap, meters)}
        return reads.within(work)
    finally:
        reads.dispose()


@needs_db
def test_complete_session_baseline(chain) -> None:  # noqa: F811
    """The metered-energy baseline table: the first POST persists exactly the E1 selected complete session revisions,
    their accepted meter evidence, the selected assessment, Foundation, eligible priced consequence and tariff, and
    the returned watermark as cutoff (P-34-2); a stale tariff yields null money IDs; P-34-3 refusal and same IDs."""
    built = settled(chain, "complete")
    tariff = golden_tariff(built)
    assert all(o.succeeded for o in money(built))
    rows = ev_money_rows(built)
    head_row = money_head({"ev_consequence_revision": [
        r for r in rows["ev_consequence_revision"] if (r["window_start"], r["window_end"]) == (LO, HI)]})
    want = selected(built)
    sel = want["snap"]["selected"]
    assert want["complete"] and want["meters"]  # P-E5-7: a real complete metered session exists
    c = scenarios_client(built)
    out = post(c, command_body("base-key-0001"))
    assert list(out) == WRITE_KEYS and out["code"].startswith("ESCN-") and out["revision_no"] == 1
    row = stored(built, out["revision_id"])
    basis = row["authored_basis"]
    assert list(sorted(basis)) == sorted(BASIS_KEYS)
    assert basis == {
        "from": "2026-10-06T08:00:00.000000Z", "to": "2026-10-06T09:00:00.000000Z",
        "cutoff": want["body"]["window"]["known_at"],
        "assessment_revision_id": str(sel["revision_id"]).lower(), "session_revision_ids": want["complete"],
        "accepted_evidence_ids": want["meters"], "foundation_revision_id": want["foundation"]["id"],
        "consequence_revision_id": str(head_row["id"]).lower(), "tariff_revision_id": str(tariff).lower(),
        "source_provenance": want["provenance"]}
    assert basis["cutoff"] == WATERMARK  # the returned watermark, not a literal: the fixture's 09:00
    assert set(want["meters"]) <= set(sel["evidence_ids"]) and want["provenance"]["evidence_ids"] == want["meters"]
    # Ruling A6: every stored meter ID is in the window's accepted set, the head's cited set and the provenance.
    assert basis["accepted_evidence_ids"] == want["meters"] and set(want["meters"]) <= want["accepted"]
    assert set(want["meters"]) <= {str(x).lower() for x in sel["evidence_ids"]}
    assert set(want["meters"]) <= set(basis["source_provenance"]["evidence_ids"])
    assert row["basis_sha256"] == rules.basis_sha256(basis) and row["formula_version"] == "AUTHORED_ONLY/1"
    assert (row["actor_kind"], row["actor_id"], row["attestation"], row["authorization_basis"]) == (
        "SERVICE", PRINCIPAL, ATTEST, GRANT_PREFIX + PRINCIPAL)
    assert row["assumptions"] == ASSUMPTIONS and row["kind"] == "GROSS_TARIFF_CONTEXT"

    page = listed(c)
    assert list(page) == LIST_KEYS and list(page["window"]) == WINDOW_KEYS
    assert list(page["selection"]) == SELECTION_KEYS
    assert page["window"]["committed_watermark"] == WATERMARK and page["selection"]["state"] == "CURRENT"
    assert page["selection"]["assessment_revision_id"] == str(sel["revision_id"]).lower()
    assert page["selection"]["source_provenance"] == want["body"]["selected_source_provenance"]
    assert set(want["meters"]) <= set(page["selection"]["accepted_evidence_ids"])
    assert set(page["selection"]["accepted_evidence_ids"]) <= set(sel["evidence_ids"])
    [item] = page["items"]
    assert list(item) == ITEM_KEYS and item["authored_basis"] == basis and item["scenario_state"] == "DEFINED"
    assert (item["id"], item["code"], item["revision_id"]) == (out["id"], out["code"], out["revision_id"])

    # P-34-3: `known_at` after the returned watermark is 422; a read at the watermark keeps the same session IDs.
    refused_post(c, command_body("base-key-0002"), 422, "EV_TIME_INVALID", f"{QUERY}&known_at=2026-10-06T09:00:01Z")
    refused_get(c, f"{QUERY}&known_at=2026-10-06T09:00:01Z", 422, "EV_TIME_INVALID")
    at = listed(c, f"{QUERY}&known_at={WATERMARK}")
    assert at["selection"]["session_revision_ids"] == page["selection"]["session_revision_ids"]
    assert [i["revision_id"] for i in at["items"]] == [out["revision_id"]]
    assert at["items"][0]["scenario_state"] == "DEFINED"

    # A later tariff correction without money recompute: the W2-07 read guard (WITHHELD) persists no money IDs.
    prices = PostgresAssumptionStore(URL)
    try:
        prices.publish(built.tenant_id, built.site_id, Publication(
            assumption_key=EV_KEY, currency="KES", value=Decimal("0.30000"), basis="AUTHORED_ESTIMATE",
            source_reference="W5-03b E5 stale test", valid_from=GOLDEN_FROM, valid_to=GOLDEN_TO,
            change_kind="CORRECTION", correction_reason="stale basis", expected_prior_revision_id=tariff,
            idempotency_key="w503-e5-stale-1", channel="SYSTEM_FIXTURE", provenance={}), SYSTEM_PUBLISHER)
    finally:
        prices.dispose()
    stale = stored(built, post(c, command_body("base-key-0003"))["revision_id"])["authored_basis"]
    assert (stale["consequence_revision_id"], stale["tariff_revision_id"]) == (None, None)
    assert stale["session_revision_ids"] == want["complete"]
    built.close()


@needs_db
def test_unpriced_selection_and_incomplete_meter(chain) -> None:  # noqa: F811
    """No published tariff: null consequence/tariff IDs. A selection with no complete metered session is 422 and
    writes nothing."""
    built = settled(chain, "fault")
    c = scenarios_client(built)
    basis = stored(built, post(c, command_body("fault-key-0001"))["revision_id"])["authored_basis"]
    assert (basis["consequence_revision_id"], basis["tariff_revision_id"]) == (None, None)
    assert basis["session_revision_ids"] == selected(built)["complete"]
    built.close()

    partial = settled(chain, "missing-meter")
    assert not selected(partial)["complete"]
    c = scenarios_client(partial)
    refused_post(c, command_body("part-key-0001"), 422, "EV_SCENARIO_INVALID")
    assert counts(partial) == [0, 0]
    page = listed(c)
    assert page["items"] == [] and page["selection"]["state"] == "CURRENT"
    partial.close()


@needs_db
def test_command_refusals_and_replay(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    c = scenarios_client(built)
    # Principal, actor and attestation policy: 403/403/422 and nothing written.
    refused_post(scenarios_client(built, principal=False), command_body("pol-key-0001"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, principal_site=uuid4()), command_body("pol-key-0002"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, command=lambda r, code: 403), command_body("pol-key-0003"), 403,
                 "DECISION_WRITE_FORBIDDEN")
    refused_post(scenarios_client(built, command=lambda r, code: 401), command_body("pol-key-0004"), 401,
                 "UNAUTHENTICATED")
    refused_post(c, command_body("pol-key-0005", actor={"kind": "USER", "id": "user:1", "attestation": ATTEST}),
                 403, "DECISION_USER_AUTH_REQUIRED")
    refused_post(c, command_body("pol-key-0006", actor={"kind": "SERVICE", "id": PRINCIPAL, "attestation": "x"}),
                 422, "DECISION_ATTESTATION_INVALID")
    # Body, window and query refusals.
    for body in (command_body("body-key-0001", extra=1), command_body("body-key-0002", kind="STOCK_VALUE_CONTEXT"),
                 command_body("body-key-0003", assumptions={"tariff_per_kwh": "0.1", "currency": "kes"}),
                 command_body("body-key-0004", assumptions={"tariff_per_kwh": "0.123456789", "currency": "KES"}),
                 command_body("body-key-0005", authored_basis={"session_revision_ids": []})):
        refused_post(c, body, 422, "EV_SCENARIO_INVALID")
    refusal(c.post(f"{ROUTE}?{QUERY}", content=b"not json", headers={"content-type": "application/json"}), 422,
            "EV_SCENARIO_INVALID")
    refused_post(c, command_body("win-key-0001"), 422, "EV_WINDOW_INVALID", query="")
    refused_post(c, command_body("win-key-0002"), 422, "EV_WINDOW_INVALID", query="from=2026-10-06T08:00:00Z")
    refused_post(c, command_body("win-key-0003"), 422, "EV_WINDOW_TOO_LONG",
                 query="from=2026-09-01T00:00:00Z&to=2026-10-06T09:00:00Z")
    refused_post(c, command_body("win-key-0004"), 422, "EV_PARAMETER_UNKNOWN", query=f"{QUERY}&scenario_at=x")
    refused_post(c, command_body("win-key-0005"), 422, "EV_PARAMETER_UNKNOWN", query=f"{QUERY}&from=x")
    refused_post(c, command_body("win-key-0006"), 422, "EV_TIME_INVALID",
                 query="from=2026-10-06T08:00:00+03:00&to=2026-10-06T09:00:00Z")
    refused_post(c, command_body("win-key-0007"), 422, "EV_SCENARIO_INVALID", query=EMPTY_W)  # UNKNOWN selection
    assert counts(built) == [0, 0]

    # First write, exact replay (200, same body), same key with a different body (409).
    first = post(c, command_body("main-key-0001"))
    assert post(c, command_body("main-key-0001"), status=200) == first
    assert post(c, command_body("main-key-0001"), query=f"{QUERY}&known_at={WATERMARK}", status=200) == first
    refused_post(c, command_body("main-key-0001", name="Other"), 409, "EV_SCENARIO_IDEMPOTENCY_CONFLICT")
    refused_post(c, command_body("main-key-0001"), 409, "EV_SCENARIO_IDEMPOTENCY_CONFLICT", query=OTHER_W)
    assert counts(built) == [1, 1]  # [revisions, roots]
    # Correction: same window 201 and replay 200; cross-window 422 before append; stale prior 409; foreign 422/404.
    path = f"/{first['id']}/revisions"
    second = post(c, correction_body("corr-key-0001", first["revision_id"]), path=path)
    assert (second["id"], second["code"], second["revision_no"]) == (first["id"], first["code"], 2)
    assert post(c, correction_body("corr-key-0001", first["revision_id"]), path=path, status=200) == second
    refused_post(c, correction_body("corr-key-0001", first["revision_id"], name="Other"), 409,
                 "EV_SCENARIO_IDEMPOTENCY_CONFLICT", path=path)
    refused_post(c, correction_body("corr-key-0002", second["revision_id"]), 422, "EV_SCENARIO_INVALID",
                 query=OTHER_W, path=path)
    refused_post(c, correction_body("corr-key-0003", first["revision_id"]), 409, "EV_SCENARIO_REVISION_CONFLICT",
                 path=path)
    refused_post(c, correction_body("corr-key-0004", str(uuid4())), 422, "DECISION_LINK_SCOPE_INVALID", path=path)
    for body, code, message in (
            (correction_body("corr-key-0008", str(uuid4())), "DECISION_LINK_SCOPE_INVALID",
             "A cited or linked ID is outside this Site or basis."),
            (correction_body("corr-key-0009", "not-a-uuid"), "EV_SCENARIO_INVALID",
             "The EV scenario request or selected basis is invalid.")):  # ruling A3
        response = c.post(f"{ROUTE}{path}?{QUERY}", json=body)
        assert response.status_code == 422 and response.json() == {"error": {"code": code, "message": message}}
    response = c.post(f"{ROUTE}/{uuid4()}/revisions?{QUERY}", json=correction_body("corr-key-0010", str(uuid4())))
    assert response.status_code == 404 and response.json() == {
        "error": {"code": "DECISION_NOT_FOUND", "message": "No decision with this ID at this Site."}}
    refused_post(c, correction_body("corr-key-0005", second["revision_id"]), 404, "DECISION_NOT_FOUND",
                 path=f"/{uuid4()}/revisions")
    refused_post(c, correction_body("corr-key-0006", second["revision_id"]), 404, "DECISION_NOT_FOUND",
                 path="/not-a-uuid/revisions")
    assert counts(built) == [2, 1]  # [revisions, roots]
    row = stored(built, second["revision_id"])
    assert (str(row["supersedes_revision_id"]), row["correction_reason"]) == (first["revision_id"], "Corrected tariff")
    # A second root from another key gets the next public number; the global sequence is never reused.
    third = post(c, command_body("main-key-0002"))
    assert int(third["code"][5:]) > int(first["code"][5:]) and third["id"] != first["id"]
    built.close()


@needs_db
def test_pending_historical_list_and_cursor(chain) -> None:  # noqa: F811
    """Authored DB time and the evidence clock are independent: save `scenario_at` after the first POST, correct
    later, and read the prior revision with the saved `scenario_at`; pending/historical selections refuse writes
    but keep earlier rows; the cursor binds the window, cutoff, `scenario_at`, watermark and limit."""
    built = settled(chain, "complete")
    c = scenarios_client(built)
    first = post(c, command_body("pend-key-0001"))
    saved = listed(c)["scenario_at"]
    second = post(c, correction_body("pend-key-0002", first["revision_id"]), path=f"/{first['id']}/revisions")
    now = listed(c)
    assert [(i["revision_id"], i["scenario_state"]) for i in now["items"]] == [(second["revision_id"], "DEFINED")]
    then = listed(c, f"{QUERY}&scenario_at={saved}")
    assert then["scenario_at"] == saved
    assert [(i["revision_id"], i["scenario_state"]) for i in then["items"]] == [(first["revision_id"], "HISTORICAL")]
    refused_get(c, f"{QUERY}&scenario_at=2099-01-01T00:00:00Z", 422, "EV_TIME_INVALID")
    refused_get(c, f"{QUERY}&scenario_at=2026-10-06T08:00:00+03:00", 422, "EV_TIME_INVALID")
    before = [post(c, command_body(f"page-key-000{n}"))["id"] for n in range(1, 3)]

    # Cursor: three heads, limit 1; page two inherits the clocks; tampered/foreign cursors are refused.
    one = listed(c, f"{QUERY}&limit=1")
    assert len(one["items"]) == 1 and one["next_cursor"]
    seen = [one["items"][0]["id"]]
    cursor = one["next_cursor"]
    while cursor:
        nxt = listed(c, f"{QUERY}&cursor={cursor}")
        assert nxt["scenario_at"] == one["scenario_at"] and len(nxt["items"]) == 1
        seen.append(nxt["items"][0]["id"])
        cursor = nxt["next_cursor"]
    assert sorted(seen) == sorted([first["id"], *before]) and len(set(seen)) == 3
    refused_get(c, f"{QUERY}&cursor={one['next_cursor']}&limit=2", 409, "EV_SCENARIO_CURSOR_BASIS_CHANGED")
    refused_get(c, f"{QUERY}&cursor={one['next_cursor']}&known_at=2026-10-06T08:59:00Z", 409,
                "EV_SCENARIO_CURSOR_BASIS_CHANGED")
    refused_get(c, f"{QUERY}&cursor=not-a-cursor", 422, "EV_SCENARIO_CURSOR_INVALID")
    other = scenarios_client(built, site_id=uuid4())
    refused_get(other, f"{QUERY}&cursor={one['next_cursor']}", 422, "EV_SCENARIO_CURSOR_INVALID")
    for bad in ("0", "101", "x", "²"):
        refused_get(c, f"{QUERY}&limit={bad}", 422, "EV_LIMIT_INVALID")
    assert len(listed(c, f"{QUERY}&limit=100")["items"]) == 3
    assert c.get(f"{ROUTE}?{QUERY}&limit=0").json() == {  # ruling A2
        "error": {"code": "EV_LIMIT_INVALID", "message": "'limit' must be 1 to 100."}}
    assert c.get(f"{ROUTE}?{QUERY}&limit=0").json() == {  # ruling A2
        "error": {"code": "EV_LIMIT_INVALID", "message": "'limit' must be 1 to 100."}}
    empty = listed(c, EMPTY_W)
    assert empty["items"] == [] and empty["selection"]["state"] == "UNKNOWN" and empty["next_cursor"] is None
    assert listed(c, OTHER_W)["items"] == []  # a root is listed only for its revision 1 window

    # A late accepted record decided at 09:05 leaves an unrun recompute job: PENDING refuses writes; earlier rows stay.
    late_import(built, LATE_DECIDED)
    pend = listed(c)
    assert pend["selection"]["state"] == "PENDING_RECOMPUTE" and pend["window"]["committed_watermark"] != WATERMARK
    assert len(pend["items"]) == 3 and all(i["scenario_state"] == "DEFINED" for i in pend["items"])
    refused_post(c, command_body("pend-key-0009"), 422, "EV_SCENARIO_INVALID")
    refused_post(c, correction_body("pend-key-0010", second["revision_id"]), 422, "EV_SCENARIO_INVALID",
                 path=f"/{first['id']}/revisions")
    refused_get(c, f"{QUERY}&cursor={one['next_cursor']}", 409, "EV_SCENARIO_CURSOR_BASIS_CHANGED")
    # An explicit earlier evidence cutoff: HISTORICAL selection; rows authored at that cutoff are historical.
    old = listed(c, f"{QUERY}&known_at={HISTORICAL_KNOWN_AT}")
    assert old["selection"]["state"] == "HISTORICAL" and old["window"]["known_at"] == HISTORICAL_KNOWN_AT
    assert len(old["items"]) == 3 and all(i["scenario_state"] == "HISTORICAL" for i in old["items"])
    refused_post(c, command_body("pend-key-0011"), 422, "EV_SCENARIO_INVALID",
                 query=f"{QUERY}&known_at={HISTORICAL_KNOWN_AT}")
    assert counts(built) == [4, 3]  # [revisions, roots]
    built.close()


@needs_db
def test_selected_provenance_on_sets(chain, monkeypatch) -> None:  # noqa: F811
    """P-E5-3/4: mixed-case, empty, foreign and mixed-class sets through `selected_provenance_on`."""
    from test_w206_ev_store_postgres import MIXED_RUNS, patch_links

    built = settled(chain, "complete")
    reads = build_ev_read_service(URL)
    try:
        def work(c):
            snap, _ = reads.open_on(c, built.tenant_id, built.site_id, CODE, LO, HI, None)
            ids = list(snap["selected"]["evidence_ids"])[:2]
            lower = reads.selected_provenance_on(c, snap, ids)
            upper = reads.selected_provenance_on(c, snap, [x.upper() for x in ids] + ids)
            empty = reads.selected_provenance_on(c, snap, [])
            foreign = reads.selected_provenance_on(c, snap, [str(uuid4()).upper()])
            partly = reads.selected_provenance_on(c, snap, ids + [str(uuid4())])
            return ids, lower, upper, empty, foreign, partly
        ids, lower, upper, empty, foreign, partly = reads.within(work)
    finally:
        reads.dispose()
    assert len(ids) == 2 and lower["evidence_ids"] == sorted(ids) and upper == lower == partly
    assert lower["classification"] != "UNKNOWN"
    assert empty == foreign and empty["classification"] == "UNKNOWN" and empty["evidence_ids"] == []
    patch_links(monkeypatch, MIXED_RUNS[0])
    reads = build_ev_read_service(URL)
    try:
        mixed = reads.within(lambda c: reads.selected_provenance_on(
            c, reads.open_on(c, built.tenant_id, built.site_id, CODE, LO, HI, None)[0], ids))
    finally:
        reads.dispose()
    assert mixed["classification"] == "MIXED" and mixed["evidence_ids"] == sorted(ids)
    built.close()


@needs_db
def test_router_statuses_and_store_failures(chain) -> None:  # noqa: F811
    built = settled(chain, "complete")
    refused_get(scenarios_client(built, access=lambda r, code: 401), QUERY, 401, "UNAUTHENTICATED")
    refused_get(scenarios_client(built, access=lambda r, code: 403), QUERY, 403, "SITE_SCOPE_FORBIDDEN")
    refused_get(scenarios_client(built, disclosure=lambda *a: False), QUERY, 403, "EV_SOURCE_DISCLOSURE_FORBIDDEN")
    refused_get(scenarios_client(built, site_type="COLDCHAIN"), QUERY, 404, "SITE_NOT_FOUND")
    refusal(scenarios_client(built).get(f"/api/sites/OTHER/ev/financials/scenarios?{QUERY}"), 404, "SITE_NOT_FOUND")
    refused_get(scenarios_client(built, down=True), QUERY, 503, "EV_READ_UNAVAILABLE")
    refused_get(scenarios_client(built, service=False), QUERY, 503, "EV_READ_UNAVAILABLE")
    refused_post(scenarios_client(built, service=False), command_body("down-key-0001"), 503, "EV_READ_UNAVAILABLE")
    refused_get(scenarios_client(built, store_url=DOWN), QUERY, 503, "DECISION_STORE_UNAVAILABLE")
    refused_post(scenarios_client(built, store_url=DOWN), command_body("down-key-0002"), 503,
                 "DECISION_STORE_UNAVAILABLE")
    # The selected read runs on the store connection; its provenance reader failing is 503 `EV_READ_UNAVAILABLE`.
    refused_get(scenarios_client(built, link_rows=False), QUERY, 503, "EV_READ_UNAVAILABLE")
    refused_post(scenarios_client(built, link_rows=False), command_body("down-key-0003"), 503, "EV_READ_UNAVAILABLE")
    refused_get(scenarios_client(built), f"{QUERY}&from=2026-10-06T08:00:00Z", 422, "EV_PARAMETER_UNKNOWN")
    refused_get(scenarios_client(built), f"{QUERY}&amount=1", 422, "EV_PARAMETER_UNKNOWN")
    assert counts(built) == [0, 0]
    built.close()


def test_main_mounts_the_scenario_routes() -> None:
    from fastapi.testclient import TestClient as Client

    from assetops_backend.main import create_app

    c = Client(create_app())
    for method, path in (("get", ""), ("post", ""), ("post", f"/{uuid4()}/revisions")):
        body = getattr(c, method)(f"{ROUTE}{path}?{QUERY}").json()
        assert set(body) == {"error"}, (method, path, body)  # the typed wrapper, never the framework 404


# --- E5 fix round (rulings A1-A6, M1, L1-L3) ------------------------------------------------------------------


def _patched_snapshot(monkeypatch, change) -> None:
    """Wrap `EvReadService._snapshot` so `change(selected)` returns the selected head the E5 basis sees."""
    original = EvReadService._snapshot

    def wrapped(self, *args, **kwargs):
        snap = original(self, *args, **kwargs)
        if snap["selected"] is not None:
            snap = {**snap, "selected": change(dict(snap["selected"]))}
        return snap
    monkeypatch.setattr(EvReadService, "_snapshot", wrapped)


def _spied_foundation(monkeypatch) -> list:
    """Record every `foundation_revision_on` result, so a fallback case proves a Foundation was found."""
    original, seen = EvReadService.foundation_revision_on, []

    def spy(self, c, snap):
        found = original(self, c, snap)
        seen.append(found)
        return found
    monkeypatch.setattr(EvReadService, "foundation_revision_on", spy)
    return seen


@needs_db
def test_baseline_foundation_and_foreign_meter_refusals(chain, monkeypatch) -> None:  # noqa: F811
    """M1 and ruling A6: an absent, foreign or uncited Foundation, an accepted meter ID omitted from the selected
    head, and a cited meter ID outside the accepted set are each 422 `EV_SCENARIO_INVALID` with nothing written;
    the unpatched read still writes."""
    built = settled(chain, "complete")
    want = selected(built)
    assert want["meters"] and set(want["meters"]) <= want["accepted"]
    c = scenarios_client(built)
    stranger, other = str(uuid4()), str(uuid4())

    def refuse(key: str) -> None:
        refused_post(c, command_body(key), 422, "EV_SCENARIO_INVALID")
        assert counts(built) == [0, 0]

    with monkeypatch.context() as m:  # (a) no Foundation resolves
        m.setattr(EvReadService, "foundation_revision_on", lambda self, conn, snap: None)
        refuse("found-key-0001")
    with monkeypatch.context() as m:  # (b) a resolved Foundation outside a nonempty cited set
        m.setattr(EvReadService, "foundation_revision_on",
                  lambda self, conn, snap: {"id": stranger, "content": {}, "valid_from": None, "valid_to": None})
        refuse("found-key-0002")
    with monkeypatch.context() as m:  # (c) multi-ID head: the fallback Foundation is outside the cited IDs
        _patched_snapshot(m, lambda head: {**head, "foundation_ids": [stranger, other]})
        found = _spied_foundation(m)
        refuse("found-key-0003")
        # The fallback did resolve a real Foundation; the refusal is its absence from the cited IDs.
        assert found and all(f is not None and f["id"] not in (stranger, other) for f in found)
    with monkeypatch.context() as m:  # (d) a head citing no Foundation cannot validate one by fallback
        _patched_snapshot(m, lambda head: {**head, "foundation_ids": []})
        found = _spied_foundation(m)
        refuse("found-key-0004")
        assert found and all(f is not None and f["id"] == want["foundation"]["id"] for f in found)
    with monkeypatch.context() as m:  # (e) an accepted meter ID omitted from the selected head's evidence
        drop = set(want["meters"][:1])
        _patched_snapshot(m, lambda head: {**head, "evidence_ids": [
            x for x in head["evidence_ids"] if str(x).lower() not in drop]})
        refuse("meter-key-0001")
    with monkeypatch.context() as m:  # (f) a cited meter ID outside the window's accepted set
        m.setattr(EvReadService, "accepted_on", lambda self, conn, snap: [])
        refuse("meter-key-0002")
    first = post(c, command_body("found-key-0005"))  # the unpatched read still writes
    assert counts(built) == [1, 1]
    with monkeypatch.context() as m:  # the correction path refuses the same way and appends nothing
        m.setattr(EvReadService, "accepted_on", lambda self, conn, snap: [])
        refused_post(c, correction_body("meter-key-0003", first["revision_id"]), 422, "EV_SCENARIO_INVALID",
                     path=f"/{first['id']}/revisions")
    assert counts(built) == [1, 1]
    built.close()


@needs_db
def test_currency_must_match_priced_tariff(chain) -> None:  # noqa: F811
    """Ruling A5 (and A1 for the null case): a USD command over a KES priced consequence is refused with nothing
    written; KES succeeds with both money IDs stored; an unpriced selection accepts USD with both IDs null."""
    built = settled(chain, "complete")
    tariff = golden_tariff(built)
    assert all(o.succeeded for o in money(built))
    c = scenarios_client(built)
    usd = {"tariff_per_kwh": "0.31", "currency": "USD"}
    response = c.post(f"{ROUTE}?{QUERY}", json=command_body("cur-key-0001", assumptions=usd))
    assert response.status_code == 422 and response.json() == {"error": {
        "code": "EV_SCENARIO_INVALID",
        "message": "The authored currency must match the selected priced tariff currency."}}
    assert counts(built) == [0, 0]
    made = post(c, command_body("cur-key-0002"))
    basis = stored(built, made["revision_id"])["authored_basis"]
    assert basis["tariff_revision_id"] == str(tariff).lower() and basis["consequence_revision_id"] is not None
    assert "currency" not in basis  # compared on the write connection, never persisted
    response = c.post(f"{ROUTE}/{made['id']}/revisions?{QUERY}", json=correction_body(
        "cur-key-0003", made["revision_id"], assumptions=usd))
    assert response.status_code == 422 and response.json() == {"error": {
        "code": "EV_SCENARIO_INVALID",
        "message": "The authored currency must match the selected priced tariff currency."}}
    assert counts(built) == [1, 1]
    built.close()

    unpriced = settled(chain, "fault")
    out = post(scenarios_client(unpriced), command_body("cur-key-0004", assumptions=usd))
    row = stored(unpriced, out["revision_id"])
    assert row["assumptions"] == usd
    assert (row["authored_basis"]["consequence_revision_id"], row["authored_basis"]["tariff_revision_id"]) == (
        None, None)
    unpriced.close()


def _raw_roots(built, specs: list[tuple[str, dict, datetime]]) -> list[tuple[str, str]]:
    """Test-only roots, each with a revision 1 holding the given basis and `recorded_at`; returns (root, revision)."""
    revision = ("INSERT INTO ev_scenario_revision (id, tenant_id, site_id, scenario_id, revision_no, "
                "supersedes_revision_id, name, kind, assumptions, authored_basis, basis_sha256, formula_version, "
                "correction_reason, actor_kind, actor_id, authorization_basis, attestation, idempotency_key, "
                "payload_sha256, recorded_at) VALUES (:id, :t, :s, :r, 1, NULL, 'Raw', 'GROSS_TARIFF_CONTEXT', "
                "CAST(:a AS jsonb), CAST(:b AS jsonb), :h, 'AUTHORED_ONLY/1', NULL, 'SERVICE', 'svc', 'grant', "
                "'attested', :k, :h, :at)")
    made = []
    with built.engine.begin() as conn:
        for key, body, at in specs:
            root, rev = uuid4(), uuid4()
            conn.execute(text(
                "INSERT INTO ev_scenario (id, tenant_id, site_id, create_key, create_payload_sha256, "
                "create_actor_id, actor_kind, actor_id) VALUES (:id, :t, :s, :k, :h, 'svc', 'SERVICE', 'svc')"),
                {"id": root, "t": built.tenant_id, "s": built.site_id, "k": key, "h": _sha("c" + key)})
            conn.execute(text(revision), {"id": rev, "t": built.tenant_id, "s": built.site_id, "r": root,
                                          "a": json.dumps(ASSUMPTIONS), "b": json.dumps(body),
                                          "h": _sha("b" + key), "k": key, "at": at})
            made.append((str(root), str(rev)))
    return made


@needs_db
def test_equal_recorded_at_pagination_order(chain) -> None:  # noqa: F811
    """Ruling A4: the list order is `(recorded_at DESC, id DESC)` with a matching cursor predicate, so heads that
    share one `recorded_at` page strictly by descending ID with none repeated or skipped."""
    built = settled(chain, "complete")
    c = scenarios_client(built)
    real = post(c, command_body("eq-key-0001"))
    basis = stored(built, real["revision_id"])["authored_basis"]
    tie = datetime(2026, 10, 6, 9, 30, 0, 123456, tzinfo=timezone.utc)
    raw = _raw_roots(built, [(f"eq-raw-000{n}", basis, tie) for n in range(1, 4)])
    want = [real["revision_id"], *sorted((rev for _, rev in raw), reverse=True)]
    got = []
    page = listed(c, f"{QUERY}&limit=1")
    while True:
        assert len(page["items"]) == 1
        got.append(page["items"][0]["revision_id"])
        if not page["next_cursor"]:
            break
        page = listed(c, f"{QUERY}&cursor={page['next_cursor']}")
    assert got == want
    assert [i["revision_id"] for i in listed(c, f"{QUERY}&limit=100")["items"]] == want
    built.close()


@needs_db
def test_malformed_stored_basis_and_root_window_are_503(chain) -> None:  # noqa: F811
    """L1/ruling 8: a candidate whose stored basis lacks the cutoff, and a root whose revision 1 lacks `from` or
    `to`, each make the whole list 503 `DECISION_STORE_UNAVAILABLE` (no partial 200); deleting them restores it."""
    built = settled(chain, "complete")
    c = scenarios_client(built)
    real = post(c, command_body("bad-key-0001"))
    basis = stored(built, real["revision_id"])["authored_basis"]
    early = datetime.now(timezone.utc) - timedelta(minutes=5)
    assert [i["id"] for i in listed(c)["items"]] == [real["id"]]
    for missing in ("cutoff", "to", "from"):
        broken = {k: v for k, v in basis.items() if k != missing}
        [(root, rev)] = _raw_roots(built, [(f"bad-raw-{missing}", broken, early)])
        for query in (QUERY, f"{QUERY}&limit=1"):
            response = c.get(f"{ROUTE}?{query}")
            refusal(response, 503, "DECISION_STORE_UNAVAILABLE")
            assert "items" not in response.json()
            assert response.json()["error"]["message"] == "Decision records could not be read or saved."
        _replica(built.engine, f"DELETE FROM ev_scenario_revision WHERE id = '{rev}'",
                 f"DELETE FROM ev_scenario WHERE id = '{root}'")
        assert [i["id"] for i in listed(c)["items"]] == [real["id"]]
    built.close()


@needs_db
def test_default_page_is_fifty(chain) -> None:  # noqa: F811
    """L2/rulings 2 and 9: 51 roots without `limit` give 50 rows and a cursor, then one row; page two keeps page
    one's clocks, window and selection basis."""
    built = settled(chain, "complete")
    c = scenarios_client(built)
    first = post(c, command_body("page-key-0000"))
    basis = stored(built, first["revision_id"])["authored_basis"]
    base = datetime(2026, 10, 6, 9, 30, tzinfo=timezone.utc)
    _raw_roots(built, [(f"page-raw-{n:04d}", basis, base + timedelta(seconds=n)) for n in range(1, 51)])
    one = listed(c)
    assert len(one["items"]) == 50 and one["next_cursor"]
    two = listed(c, f"{QUERY}&cursor={one['next_cursor']}")
    assert len(two["items"]) == 1 and two["next_cursor"] is None
    assert (two["scenario_at"], two["window"], two["selection"]) == (
        one["scenario_at"], one["window"], one["selection"])
    ids = [i["id"] for i in one["items"]] + [i["id"] for i in two["items"]]
    assert len(set(ids)) == 51
    assert len(listed(c, f"{QUERY}&limit=100")["items"]) == 51
    built.close()


@needs_db
def test_write_race_retries_once_then_503(chain, monkeypatch) -> None:  # noqa: F811
    """L3/ruling 10 (P-E5-6): one `IntegrityError` rolls back and retries once (201 with one root and revision); a
    race that committed the same key answers the retry with exact-key 200; two consecutive races are 503
    `DECISION_STORE_UNAVAILABLE` with nothing committed."""
    from sqlalchemy.exc import IntegrityError

    built = settled(chain, "complete")
    c = scenarios_client(built)
    original_root = PostgresEvScenarioStore.insert_scenario
    original_revision = PostgresEvScenarioStore.insert_scenario_revision
    calls = {"n": 0}

    def race_once(conn, row):  # the insert lands, then fails: the transaction rolls back
        calls["n"] += 1
        original_revision(conn, row)
        if calls["n"] == 1:
            raise IntegrityError("INSERT", {}, Exception("race"))

    with monkeypatch.context() as m:  # one race: rolled back, then a clean 201
        m.setattr(PostgresEvScenarioStore, "insert_scenario_revision", staticmethod(race_once))
        made = post(c, command_body("race-key-0001"))
        assert calls["n"] == 2 and made["revision_no"] == 1
    assert counts(built) == [1, 1]  # [revisions, roots]

    seen = {"n": 0}
    other = scenarios_client(built)

    def raced_root(conn, row):  # a concurrent writer commits the same key first; this insert then collides
        seen["n"] += 1
        if seen["n"] == 1:
            post(other, command_body("race-key-0002"))
        return original_root(conn, row)

    with monkeypatch.context() as m:
        m.setattr(PostgresEvScenarioStore, "insert_scenario", staticmethod(raced_root))
        replay = post(c, command_body("race-key-0002"), status=200)
        assert replay["revision_no"] == 1 and seen["n"] == 2  # outer insert + the racing writer; the retry inserts nothing
    assert counts(built) == [2, 2]

    calls["n"] = 0
    with monkeypatch.context() as m:  # a correction race: one retry, then the appended revision
        m.setattr(PostgresEvScenarioStore, "insert_scenario_revision", staticmethod(race_once))
        second = post(c, correction_body("race-key-0003", made["revision_id"]), path=f"/{made['id']}/revisions")
        assert second["revision_no"] == 2 and calls["n"] == 2
    assert counts(built) == [3, 2]

    def race_always(conn, row):
        original_revision(conn, row)
        raise IntegrityError("INSERT", {}, Exception("race"))

    with monkeypatch.context() as m:  # two consecutive races: 503, nothing committed
        m.setattr(PostgresEvScenarioStore, "insert_scenario_revision", staticmethod(race_always))
        response = c.post(f"{ROUTE}?{QUERY}", json=command_body("race-key-0004"))
        refusal(response, 503, "DECISION_STORE_UNAVAILABLE")
        assert response.json()["error"]["message"] == "Decision records could not be read or saved."
        refusal(c.post(f"{ROUTE}/{made['id']}/revisions?{QUERY}", json=correction_body(
            "race-key-0005", second["revision_id"])), 503, "DECISION_STORE_UNAVAILABLE")
    assert counts(built) == [3, 2]
    built.close()
