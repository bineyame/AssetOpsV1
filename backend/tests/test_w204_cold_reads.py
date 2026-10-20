"""W2-04 commit 3: the five cold Site reads over registered W2-02 replays, W2-03 assessment and W2-04 money.

`.agent/W2-04-build-spec.md` "Five API reads", "Selection, projection and capability", the commit-3 Architect
ruling on source contact and the dry-read table. Each replay test runs the W2-02 chain, the W2-03 cold worker and
the W2-04 cold consequence worker in the private `*_test` database, then reads through the real router with the
real `ColdReadService` and consequence store. No accepted, assessment, Finding or consequence row is inserted by
hand; only `gateway_diagnostic` rows are added where a test needs a selected source-specific diagnostic. Replay
tests need `ASSETOPS_TEST_DATABASE_URL` and are skipped (never passed) without it; the pure tests always run.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.analytics import cold_site_reads as csr
from assetops_backend.analytics.cold_reads import ColdReadUnavailable, encode_cursor
from assetops_backend.cold_site_api import build_cold_site_router
from assetops_backend.financials.cold_consequence import SCREEN_WORDING

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
needs_db = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, rows, run
    from test_w204_cold_consequence import drain

    from assetops_backend.analytics.adapters.postgres_assessment_store import ColdReadService
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.evidence.public_provenance import basis_sha256, cold_consequence_row_selection
    from assetops_backend.cold_assessment_api import build_cold_assessment_router
    from assetops_backend.financials.composition import build_cold_consequence_store

CODE = "COLD-READ"
W = "from=2026-10-06T19:00:00Z&to=2026-10-06T20:05:00Z"
TO = datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc)
EMPTY = "from=2026-10-05T19:00:00Z&to=2026-10-05T20:05:00Z"
ROUTES = ("overview", "evidence", "evidence/analysis", "financials", "financial-assumptions")
# W3-01 Run 3 q3: the three literal provenance siblings; each non-null block is the six-key DTO + `detail`.
ENVELOPE = {"site_id", "window", "currentness", "source_provenance", "selected_source_provenance",
            "pending_source_provenance", "limitations"}
DTO = {"classification", "state", "source_ids", "evidence_ids", "basis_sha256", "reasons", "detail"}
RAW_CODES = tuple(SCREEN_WORDING)
EXCURSION_ATTENTION = ["COLD_START_FAILURE", "COLD_TRANSFER_UNKNOWN"]  # the excursion replay's chain


def _registry(site_id, tenant_id, site_type="COLDCHAIN"):
    site = SimpleNamespace(id=site_id, site_type=site_type)
    return SimpleNamespace(imported=lambda code: site if code == CODE else None,
                           tenant=lambda: SimpleNamespace(id=tenant_id))


def client(built, *, site_type="COLDCHAIN", tenant=None, access=None, disclosure=None, url=None) -> TestClient:
    registry = _registry(built.site_id, tenant or built.tenant_id, site_type)
    kw = {k: v for k, v in (("access", access), ("disclosure", disclosure)) if v is not None}
    reads = ColdReadService(url or URL, link_rows=build_link_rows_reader())
    app = FastAPI()
    app.include_router(build_cold_assessment_router(registry, reads, **kw))
    app.include_router(build_cold_site_router(
        registry, csr.ColdSiteReadService(reads, build_cold_consequence_store(url or URL)), **kw))
    return TestClient(app)


def get(c: TestClient, path: str, status: int = 200) -> dict:
    response = c.get(path if path.startswith("/api/") else f"/api/sites/{CODE}/cold/{path}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, path: str, status: int) -> str:
    body = get(c, path, status)
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def no_raw_code(body: dict) -> None:
    """A display field never carries a raw stored money code (codes ruling)."""
    blob = json.dumps(body)
    assert not [code for code in RAW_CODES if f'"{code}' in blob or f" {code}" in blob], blob


# --- pure: source contact (commit-3 Architect ruling) --------------------------------------------------------


SOURCE = uuid4()


def diag(contact="absent", *, offset=0, cadence=60):
    contacts = {} if contact == "absent" else {str(SOURCE).upper(): contact}
    return {"contacts": contacts, "clock_offset_ms": offset, "cadence_seconds": cadence,
            "received_at": TO - timedelta(minutes=1)}


@pytest.mark.parametrize("diagnostic,expected", [
    (None, ("UNKNOWN", None, csr.CONTACT_NO_DIAGNOSTIC)),
    (diag(), ("UNKNOWN", None, csr.CONTACT_NOT_REPORTED)),
    (diag(None), ("NEVER", None, None)),
    (diag("2026-10-06T20:03:00Z"), ("RECENT", "2026-10-06T20:03:00.000000Z", None)),
    (diag("2026-10-06T20:03:00Z", cadence=60), ("RECENT", "2026-10-06T20:03:00.000000Z", None)),  # equality (2 x 60 s)
    (diag("2026-10-06T20:02:59Z", cadence=60), ("STALE", "2026-10-06T20:02:59.000000Z", None)),
    (diag("2026-10-06T20:03:00Z", offset=None), ("UNKNOWN", None, csr.CONTACT_CLOCK)),  # offset not measured
    (diag("2026-10-06T20:03:00Z", offset=60_000), ("UNKNOWN", None, csr.CONTACT_CLOCK)),  # untrusted clock
    (diag("2026-10-06T20:03:00Z", cadence=None), ("UNKNOWN", None, csr.CONTACT_NO_CADENCE)),
    (diag("2026-10-06T20:03:00Z", cadence=0), ("UNKNOWN", None, csr.CONTACT_NO_CADENCE)),
    (diag("2026-10-06T20:05:01Z"), ("UNKNOWN", None, csr.CONTACT_AFTER_WINDOW)),
    (diag("not-a-time"), ("UNKNOWN", None, csr.CONTACT_CLOCK)),
])
def test_source_contact_ruling(diagnostic, expected) -> None:
    assert csr.source_contact(diagnostic, SOURCE, TO) == expected


def test_run5_exact_copy() -> None:
    """Run-5 rulings: contact limitations (verdict 5), Q-R1/Q-R2/Q-R3/Q-R4/Q-R7 sentences, verbatim."""
    assert (csr.CONTACT_NO_DIAGNOSTIC, csr.CONTACT_NOT_REPORTED, csr.CONTACT_NO_CADENCE, csr.CONTACT_CLOCK,
            csr.CONTACT_AFTER_WINDOW) == (
        "No gateway diagnostic was available by the window end and evidence cutoff.",
        "The selected gateway diagnostic has no contact time for this source.",
        "The gateway's reporting interval is not declared, so source contact cannot be called recent.",
        "The gateway time cannot be verified, so the reported contact time is uncertain.",
        "The reported source contact happened after this window ended.")
    assert list(csr.ATTENTION) == ["COLD_RECOMPUTE_PENDING", "COLD_PROBE_GAP", "COLD_START_FAILURE",
                                   "COLD_TRANSFER_UNKNOWN", "COLD_POLICY_MISSING"]
    assert csr.ATTENTION["COLD_START_FAILURE"] == "Automatic generator start failed in the accepted record"
    assert csr.OBJECTIVE_TEXT.format(low="2", high="4") == \
        "Keep the chamber between 2\u20134\u00b0C through power, cooling and operating disturbances."
    assert csr.NOT_INCLUDED_TEXT["SOURCE_GATE_WITHHELD"] == SCREEN_WORDING["SOURCE_GATE_WITHHELD"]
    assert set(csr.COOLING_TEXT) == {"SUPPORTED", "LIMITED", "UNAVAILABLE", "CONTRADICTORY"}
    assert set(csr.REQUIREMENTS) == {"cold-excursion/1", "cold-start-response/1"}


# --- pure: refusal order and parsing (no database) -----------------------------------------------------------


class _Fake:
    def __getattr__(self, name):
        return lambda *a, **k: {"route": name, "args": [str(x) for x in a[3:]]}


def fake_client(*, access=None, disclosure=None, site_type="COLDCHAIN", reads=_Fake()) -> TestClient:
    kw = {k: v for k, v in (("access", access), ("disclosure", disclosure)) if v is not None}
    app = FastAPI()
    app.include_router(build_cold_site_router(_registry(uuid4(), uuid4(), site_type), reads, **kw))
    return TestClient(app)


def test_refusal_codes_without_database() -> None:
    c = fake_client()
    for route in ROUTES:
        assert get(c, f"{route}?{W}")["route"] in ("overview", "evidence", "analysis", "financials", "assumptions")
    assert error(fake_client(access=lambda r, code: 401), f"overview?{W}", 401) == "UNAUTHENTICATED"
    assert error(fake_client(access=lambda r, code: 403), f"evidence?{W}", 403) == "SITE_SCOPE_FORBIDDEN"
    assert error(c, f"overview?{W}&cursor=x", 422) == "COLD_PARAMETER_UNKNOWN"  # cursor is Analysis-only
    assert error(c, "overview?from=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "overview?from=2026-10-06T20:00:00Z&to=2026-10-06T19:00:00Z", 422) == "COLD_WINDOW_INVALID"
    assert error(c, "financials?from=2026-09-01T00:00:00Z&to=2026-10-06T00:00:00Z", 422) == "COLD_WINDOW_TOO_LONG"
    assert error(c, f"overview?{W}&known_at=2026-10-06T20:05:00", 422) == "COLD_TIME_INVALID"  # no zone
    assert error(c, f"overview?{W}&known_at=2026-10-06T23:05:00%2B03:00", 422) == "COLD_TIME_INVALID"
    assert error(c, f"overview?{W}&known_at=2026-10-06T20:05:00.1234567Z", 422) == "COLD_TIME_INVALID"  # Q3
    assert get(c, f"overview?{W}&known_at=2026-10-06T20:05:00.123456Z")["route"] == "overview"
    for bad in ("0", "201", "x"):
        assert error(c, f"evidence/analysis?{W}&limit={bad}", 422) == "COLD_LIMIT_INVALID"
    assert error(fake_client(site_type="MINIGRID"), f"overview?{W}", 404) == "SITE_NOT_FOUND"
    assert error(c, "/api/sites/OTHER/cold/overview", 404) == "SITE_NOT_FOUND"
    assert error(fake_client(reads=None), f"overview?{W}", 503) == "COLD_READ_UNAVAILABLE"

    class _Down:
        def __getattr__(self, name):
            def fail(*a, **k):
                raise ColdReadUnavailable("store down")
            return fail
    for route in ROUTES:
        assert error(fake_client(reads=_Down()), f"{route}?{W}", 503) == "COLD_READ_UNAVAILABLE"
    assert error(fake_client(disclosure=lambda code, t, s: False), f"financials?{W}", 403) == \
        "COLD_SOURCE_DISCLOSURE_FORBIDDEN"


# --- replays -------------------------------------------------------------------------------------------------


def follow(c: TestClient, href: str) -> dict:
    assert "from=" in href and "to=" in href and "known_at=" in href, href
    return get(c, href)


def add_diagnostic(built, gateway_id, sequence: int, received_at, contacts: dict, offset=0) -> None:
    with built.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO gateway_diagnostic (id, tenant_id, site_id, gateway_id, sequence_epoch, diagnostic_sequence, "
            "observed_at, received_at, last_device_contact_by_source, queue_count, oldest_queue_age_seconds, "
            "disk_pressure, clock_offset_ms, mapping_error_count, payload_sha256, diagnostic_text) VALUES "
            "(:id, :t, :s, :g, 'w204-test', :n, :at, :at, CAST(:c AS jsonb), 0, NULL, 'OK', :o, 0, :sha, '{}')"),
            {"id": uuid4(), "t": built.tenant_id, "s": built.site_id, "g": gateway_id, "n": sequence,
             "at": received_at, "c": json.dumps(contacts), "o": offset, "sha": f"{sequence:064x}"})


@needs_db
def test_excursion_five_reads(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    drain(built)
    c = client(built)
    bodies = {route: get(c, f"{route}?{W}") for route in ROUTES}
    for route, body in bodies.items():
        assert ENVELOPE <= set(body), route
        assert body["currentness"]["state"] == "CURRENT", (route, body["currentness"])
        assert body["source_provenance"]["classification"] == "REGISTERED_SIMULATION"
        assert set(body["source_provenance"]) == DTO and body["pending_source_provenance"] is None
        no_raw_code(body)
    known = bodies["overview"]["window"]["known_at"]

    ov = bodies["overview"]
    assert ov["status"]["state"] == "OBSERVED_EXCURSION" and ov["status"]["as_of"]
    assert (ov["objective"]["policy_low_deg_c"], ov["objective"]["policy_high_deg_c"]) == ("2", "4")
    assert ov["objective"]["room_asset_id"] and ov["objective"]["limitation"] is None
    summary = ov["temperature_summary"]
    assert summary["coverage"]["known_points"] == 13 and summary["episode_count"] == 1 and summary["latest_deg_c"]
    assert ov["backup_summary"]["attempts"] == 1 and ov["backup_summary"]["latest_chain_id"]
    steps = [x["step"] for x in ov["causal_strip"]]
    assert steps and steps == sorted(steps, key=("GRID", "START_REQUEST", "START_RESULT", "GENERATOR", "TRANSFER",
                                                 "BUS", "COMPRESSOR", "PROBE").index)
    assert ov["findings"]["count"] == len({i["finding_id"] for i in ov["findings"]["items"]}) >= 1
    for item in ov["findings"]["items"]:
        assert follow(c, item["link"])["finding_id"] == item["finding_id"]  # exact Finding, selection preserved
    money = ov["consequence_summary"]
    assert money["state"] == "UNPRICED" and money["quantity"] == {"low": "19", "high": None, "unit": "degC_min"}
    assert money["amount"] == {"low": None, "high": None, "currency": None}
    assert money["overlap_group"].startswith("cold:")
    assert SCREEN_WORDING["COLD_VALUATION_NOT_APPROVED"] in money["limitation"]
    assert SCREEN_WORDING["OPEN_EPISODE_UPPER_UNKNOWN"] in money["limitation"]
    for name, href in ov["links"].items():
        assert follow(c, href)["window"]["known_at"] == known, name
    assert ov["objective"]["text"] == csr.OBJECTIVE_TEXT.format(low="2", high="4")
    assert [x["code"] for x in ov["needs_attention"]] == EXCURSION_ATTENTION
    for item in ov["needs_attention"]:
        assert set(item) == {"code", "text", "link", "as_of", "limitation"}
        assert item["text"] == csr.ATTENTION[item["code"]] and item["as_of"]
        assert item["link"] is None or follow(c, item["link"])  # never an Action URL
    assert ov["cooling"]["state"] in csr.COOLING_TEXT and ov["cooling"]["text"] == \
        csr.COOLING_TEXT[ov["cooling"]["state"]]
    assert ov["maintenance"] == {"state": "NOT_RECORDED", "text": csr.MAINTENANCE_TEXT, "record_id": None,
                                 "link": None, "as_of": known, "limitation": csr.MAINTENANCE_LIMITATION}

    ev = bodies["evidence"]
    assert [x["claim"] for x in ev["capabilities"]] == list(csr.CAPABILITIES)
    caps = {x["claim"]: x for x in ev["capabilities"]}
    assert caps["TEMPERATURE_POINT"]["state"] == "SUPPORTED" and caps["TEMPERATURE_POINT"]["missing_roles"] == []
    assert caps["EXCURSION_BOUNDS"]["state"] == "SUPPORTED"
    assert caps["EXCURSION_BOUNDS"]["coverage"] == {"known_points": 13, "expected_points": 13, "ratio": "1"}
    assert all(x["state"] in ("SUPPORTED", "LIMITED", "UNAVAILABLE", "CONTRADICTORY") and x["as_of"]
               for x in ev["capabilities"])
    sources = ev["sources"]
    assert sources and all(s["contact"] == "UNKNOWN" and s["limitation"] == csr.CONTACT_NO_DIAGNOSTIC
                           and s["contact_at"] is None for s in sources)  # no gateway diagnostic: never NEVER
    probe = next(s for s in sources if s["role"] == "chamber_temperature")
    assert probe["accepted_count"] == 13 and probe["fact_age"] == 300  # 20:05 - last probe 20:00
    assert probe["last_accepted_at"] == "2026-10-06T20:00:00.000000Z"
    assert probe["quality"] == {"good_count": 13, "other_count": 0}
    assert all(s["quality"]["good_count"] + s["quality"]["other_count"] == s["accepted_count"] for s in sources)
    roles = [s["role"] for s in sources]
    assert roles == sorted(roles, key=lambda r: csr.ROLE_ORDER.get(r, len(csr.ROLE_ORDER)))
    links = dict(ev["links"])
    assert links.pop("foundation") == f"/api/sites/{CODE}/cold/foundation?at=2026-10-06T20%3A05%3A00.000000Z"  # Q-R6
    for name, href in links.items():
        assert follow(c, href)["window"]["known_at"] == known, name

    # Source contact from the latest diagnostic received by min(known_at, to); later receipts are ignored.
    [gateway_id] = [r["gateway_id"] for r in rows(
        built, "SELECT DISTINCT gateway_id FROM signal_binding_revision WHERE site_id = :s "
               "AND source_id = :p", p=UUID(probe["id"]))]
    add_diagnostic(built, gateway_id, 1, TO - timedelta(minutes=2), {probe["id"]: "2026-10-06T20:04:00Z"})
    add_diagnostic(built, gateway_id, 2, TO + timedelta(minutes=1), {probe["id"]: None})  # after `to`: ignored
    contacts = {(s["id"], s["role"]): s for s in get(c, f"evidence?{W}")["sources"]}
    assert contacts[(probe["id"], "chamber_temperature")]["contact"] == "RECENT"
    assert contacts[(probe["id"], "chamber_temperature")]["contact_at"] == "2026-10-06T20:04:00.000000Z"  # Q-R8
    others = [s for (sid, _), s in contacts.items() if sid != probe["id"]]
    assert all(s["contact"] == "UNKNOWN" for s in others)  # another source's key absent or no diagnostic
    add_diagnostic(built, gateway_id, 3, TO - timedelta(minutes=1), {probe["id"]: None})
    assert {(s["contact"], s["contact_at"]) for s in get(c, f"evidence?{W}")["sources"]
            if s["id"] == probe["id"]} == {("NEVER", None)}

    an = bodies["evidence/analysis"]
    expected = sorted(an["source_provenance"]["evidence_ids"])
    seen, cursor = [], None
    while True:
        page = get(c, f"evidence/analysis?{W}&limit=7" + (f"&cursor={cursor}" if cursor else ""))
        seen += page["accepted_records"]["items"]
        # Run-7 paging ruling: every page names the full selected accepted count, not its own length.
        assert page["accepted_records"]["total_count"] == len(expected)
        cursor = page["accepted_records"]["next_cursor"]
        if cursor is None:
            break
    assert len(expected) > 7  # the count differs from a page length, so the assertion above is not vacuous
    assert sorted(x["evidence_id"] for x in seen) == expected
    assert [(x["source_time"], x["evidence_id"]) for x in seen] == sorted((x["source_time"], x["evidence_id"])
                                                                          for x in seen)
    assert all(x["record_target_state"] == "UNAVAILABLE" and x["link"] is None
               and x["limitation"] == csr.RECORD_TARGET_UNAVAILABLE for x in seen)
    probes = [x for x in seen if x["role"] == "chamber_temperature"]
    assert probes and all(x["value_display"] is not None and x["unit"] == "degC" for x in probes)
    assert {r["rule_id"] for r in an["claim_rules"]} == {"cold-excursion/1", "cold-start-response/1"}
    assert all(r["requirement"] == csr.REQUIREMENTS[r["rule_id"]] for r in an["claim_rules"])  # Q-R7
    first = get(c, f"evidence/analysis?{W}&limit=1")["accepted_records"]["next_cursor"]
    moved = encode_cursor(datetime(2026, 10, 6, 19, tzinfo=timezone.utc), uuid4(), "0" * 64)
    assert first and error(c, f"evidence/analysis?{W}&cursor={moved}", 409) == "COLD_CURSOR_BASIS_CHANGED"
    assert error(c, f"evidence/analysis?{W}&cursor=@@", 422) == "COLD_CURSOR_INVALID"

    fin = bodies["financials"]
    [row] = fin["consequences"]
    assert (row["kind"], row["state"], row["quantity_unit"]) == ("PRODUCT_EXPOSURE", "UNPRICED", "degC_min")
    assert row["quantity_bounds"] == {"low": "19", "high": None} and row["currency"] is None
    assert row["amount_bounds"] == {"low": None, "high": None}
    assert row["reason"] == SCREEN_WORDING["COLD_VALUATION_NOT_APPROVED"]
    assert row["limitation"] == SCREEN_WORDING["OPEN_EPISODE_UPPER_UNKNOWN"]
    assert [x["code"] for x in fin["not_included"]] == list(csr.NOT_INCLUDED)
    assert all(x["text"] == csr.NOT_INCLUDED_TEXT[x["code"]] for x in fin["not_included"])  # Q-R4
    basis = row["exact_basis"]  # Q-R5: an object from the selected immutable consequence
    assert set(basis) == {"finding_revision_id", "episode_revision_id", "assessment_revision_id", "evidence_ids",
                          "source_gate_sha256", "assumption_revision_ids", "consequence_basis_sha256"}
    assert basis["evidence_ids"] and basis["evidence_ids"] == sorted(set(basis["evidence_ids"]))
    assert basis["assumption_revision_ids"] == []
    assert all(len(basis[k]) == 64 and basis[k] == basis[k].lower()
               for k in ("source_gate_sha256", "consequence_basis_sha256"))
    assert basis["finding_revision_id"] in {i["revision_id"] for i in ov["findings"]["items"]}
    assert set(basis["evidence_ids"]) <= set(an["source_provenance"]["evidence_ids"])
    # W3-01 Run 3 q3: the consequence row's own block cites its stored evidence plus the pinned Finding citations and
    # selects `{consequence, Finding, episode, assessment}`; it differs from the envelope and the Finding row.
    with built.engine.connect() as conn:
        pinned = {str(x).lower() for x in conn.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE site_id = :s AND finding_revision_id = :r"),
            {"s": built.site_id, "r": basis["finding_revision_id"]}).scalars()}
    cited = sorted(set(basis["evidence_ids"]) | pinned)
    block = row["source_provenance"]
    assert set(block) == DTO and block["evidence_ids"] == cited
    assert block["basis_sha256"] == basis_sha256(built.tenant_id, built.site_id, cold_consequence_row_selection(
        row["id"], basis["finding_revision_id"], basis["episode_revision_id"], basis["assessment_revision_id"]), cited)
    assert block["basis_sha256"] != fin["source_provenance"]["basis_sha256"]
    finding_rows = [i for i in get(c, f"findings?{W}")["items"] if i["revision_id"] == basis["finding_revision_id"]]
    assert finding_rows and all(set(i["source_provenance"]) == DTO for i in finding_rows)
    assert all(i["source_provenance"]["basis_sha256"] not in (block["basis_sha256"],
                                                              ov["source_provenance"]["basis_sha256"])
               for i in finding_rows)
    for name, href in fin["links"].items():
        assert follow(c, href)["window"]["known_at"] == known, name

    asm = bodies["financial-assumptions"]
    assert asm["items"] == [] and asm["missing_keys"] == ["cold_stock_quantity", "cold_stock_unit_value",
                                                           "cold_exposure_rule"]
    assert (asm["publication_state"], asm["currency_state"]) == ("NOT_SUPPORTED_IN_W2", "UNDECLARED")

    # Refusals over a real Site: a cutoff after the committed watermark, disclosure, tenant and store failure.
    future = (datetime.fromisoformat(known.replace("Z", "+00:00")) + timedelta(seconds=1)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ")
    for route in ROUTES:
        assert error(c, f"{route}?{W}&known_at={future}", 422) == "COLD_TIME_INVALID"
    assert error(client(built, disclosure=lambda code, t, s: False), f"evidence?{W}", 403) == \
        "COLD_SOURCE_DISCLOSURE_FORBIDDEN"
    foreign = client(built, tenant=uuid4())
    assert get(foreign, f"overview?{W}")["currentness"]["state"] == "UNKNOWN"
    assert get(foreign, f"financials?{W}")["consequences"] == []
    down = client(built, url="postgresql+psycopg://nobody:x@127.0.0.1:1/none?connect_timeout=2")
    assert error(down, f"overview?{W}", 503) == "COLD_READ_UNAVAILABLE"  # never a blank 200


@needs_db
def test_late_reading_pending_then_historical(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    drain(built)
    c = client(built)
    before = get(c, f"financials?{W}")
    [first] = before["consequences"]
    assert first["state"] == "UNPRICED" and before["currentness"]["state"] == "CURRENT"
    cutoff = before["window"]["known_at"]
    built.advance_late()
    pending = get(c, f"overview?{W}")
    assert pending["currentness"]["state"] == "PENDING_RECOMPUTE"
    assert pending["consequence_summary"]["state"] == "WITHHELD"
    assert pending["consequence_summary"]["limitation"].startswith(csr.PENDING_COPY)
    head = pending["needs_attention"][0]  # Q-R1: pending ranks first, at the cutoff
    assert (head["code"], head["text"], head["as_of"]) == ("COLD_RECOMPUTE_PENDING", csr.PENDING_COPY,
                                                           pending["window"]["known_at"])
    run(built)  # a new assessment and Finding revision; the money work is still queued
    queued = get(c, f"financials?{W}")
    assert queued["currentness"]["state"] == "CURRENT"
    assert [x["state"] for x in queued["consequences"]] in ([], ["WITHHELD"])
    assert all(x["reason"] == csr.PENDING_COPY for x in queued["consequences"])
    drain(built)
    after = get(c, f"financials?{W}")
    [new] = after["consequences"]
    assert new["state"] == "UNPRICED" and new["id"] != first["id"]
    assert get(c, f"overview?{W}")["temperature_summary"]["coverage"]["known_points"] == 13
    historical = get(c, f"financials?{W}&known_at={cutoff}")
    assert historical["currentness"]["state"] == "HISTORICAL"
    assert [x["id"] for x in historical["consequences"]] == [first["id"]]  # the exact old head, no newer mix
    old = get(c, f"overview?{W}&known_at={cutoff}")
    assert old["temperature_summary"]["coverage"]["known_points"] == 12
    assert old["window"]["known_at"] == cutoff and cutoff in old["links"]["financials"].replace("%3A", ":")


@needs_db
def test_missing_probe_and_empty_window(chain) -> None:  # noqa: F811
    built = opened("missing-probe", chain)
    run(built)
    drain(built)
    c = client(built)
    ov = get(c, f"overview?{W}")
    assert ov["temperature_summary"]["coverage"]["known_points"] == 7
    assert ov["backup_summary"]["observed_failure"] == 1
    assert ov["consequence_summary"]["state"] == "UNKNOWN"
    assert ov["consequence_summary"]["quantity"] == {"low": None, "high": None, "unit": None}
    codes = [x["code"] for x in ov["needs_attention"]]
    assert "COLD_PROBE_GAP" in codes and "COLD_START_FAILURE" in codes and "COLD_RECOMPUTE_PENDING" not in codes
    assert codes == [k for k in csr.ATTENTION if k in codes]  # ruled order
    caps = {x["claim"]: x for x in get(c, f"evidence?{W}")["capabilities"]}
    assert caps["EXCURSION_BOUNDS"]["state"] == "LIMITED"  # coverage 7/13 < 0.8
    assert caps["PRODUCT_EXPOSURE"]["state"] != "SUPPORTED"
    assert get(c, f"financials?{W}")["consequences"] == []
    # A valid window with no selected assessment: 200 UNKNOWN with empty arrays on every read.
    bodies = {route: get(c, f"{route}?{EMPTY}") for route in ROUTES}
    for route, body in bodies.items():
        assert body["currentness"]["state"] == "UNKNOWN" and body["limitations"], route
    assert bodies["overview"]["causal_strip"] == [] and bodies["overview"]["findings"]["items"] == []
    assert bodies["overview"]["status"]["state"] == "UNKNOWN"
    assert bodies["overview"]["needs_attention"] == []  # never a generic invented row
    assert bodies["overview"]["objective"]["text"] == csr.OBJECTIVE_ABSENT
    assert (bodies["overview"]["cooling"]["state"], bodies["overview"]["cooling"]["text"]) == (
        "UNAVAILABLE", csr.COOLING_TEXT["UNAVAILABLE"])
    assert bodies["overview"]["maintenance"]["state"] == "NOT_RECORDED"
    assert bodies["overview"]["consequence_summary"]["state"] == "UNKNOWN"
    assert (bodies["evidence"]["capabilities"], bodies["evidence"]["sources"]) == ([], [])
    assert bodies["evidence/analysis"]["accepted_records"] == {"items": [], "next_cursor": None, "total_count": 0}
    assert bodies["evidence/analysis"]["claim_rules"] == []
    assert (bodies["financials"]["consequences"], bodies["financials"]["not_included"]) == ([], [])
    assert bodies["financial-assumptions"]["items"] == []


class _CapReads:
    """Accepted records exist for every role, but the selected W2-03 results count only qualifying points."""

    @staticmethod
    def accepted_on(c, t, s, ids, *a):
        return [{"role": r} for r in ("chamber_temperature", "compressor_state", "backup_start_event")]

    @staticmethod
    def basis_revisions_on(c, t, s, revision_id):
        return {"created_at": TO, "foundations": [], "bindings": []}


def _cap_states(exc_result: dict, chains: list) -> dict:
    sel = {csr.EXC: SimpleNamespace(revision_id=uuid4(), evidence_ids=[uuid4()], result=exc_result),
           csr.START: SimpleNamespace(revision_id=uuid4(), evidence_ids=[], result={"chains": chains})}
    snap = {"t": uuid4(), "s": uuid4(), "known": TO, "selected": sel}
    return {x["claim"]: x for x in csr.ColdSiteReadService(_CapReads(), None)._capabilities(None, snap)}


def test_capability_needs_qualifying_points() -> None:
    """Run-5 verdict 1: accepted but unqualified probe records (clock unattested or uncalibrated, so W2-03 counts
    zero qualifying points) never make a temperature claim SUPPORTED from a raw record count."""
    policy = {"policy_low": "2", "policy_high": "4"}
    unqualified = _cap_states({"known_points": 0, "expected_points": 13, "coverage": "0", "policy": policy,
                               "gaps": [], "excursions": []}, [])
    assert unqualified["TEMPERATURE_POINT"]["state"] == "UNAVAILABLE"
    assert unqualified["EXCURSION_BOUNDS"]["state"] == "UNAVAILABLE"
    assert unqualified["COOLING_RESPONSE"]["state"] == "LIMITED"  # compressor state alone: a narrower claim
    assert unqualified["PRODUCT_EXPOSURE"]["state"] == "UNAVAILABLE"
    for claim in ("BACKUP_START_RESULT", "TRANSFER_POSITION"):
        assert unqualified[claim]["coverage"] == {"known_points": None, "expected_points": None, "ratio": None}
    # An excursion without proved thermal bounds is LIMITED, never SUPPORTED, product exposure.
    unbounded = _cap_states({"known_points": 7, "expected_points": 13, "coverage": "0.54", "policy": policy,
                             "gaps": [], "excursions": [{"exposure_finding": True, "claim_level": "OBSERVED"}]}, [])
    assert unbounded["TEMPERATURE_POINT"]["state"] == "SUPPORTED"
    assert unbounded["PRODUCT_EXPOSURE"]["state"] == "LIMITED"
