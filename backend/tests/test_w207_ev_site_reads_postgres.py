"""W2-07 commit 3: the five selected EV Site reads over the registered W2-05b replays (`.agent/W2-07-build-spec.md`
"Five selected reads", concrete-artifact closure section 2, the post-W2-06 reconciliation and q1-q4).

The routes go through `build_ev_site_router` with the real `EvSiteReads` (W2-06 `EvReadService` + `EvMoneyReads`),
mounted beside W2-06's `build_ev_assessment_router` so the shared envelope is compared byte for byte. Golden values
are the real persisted IDs, times and hashes, never the illustrative constants of the closure examples.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from test_w205b_ev_replay_postgres import CASES, URL, chain  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w206_ev_reads_postgres import _at, _iso, rebind, unknown_revisions
    from test_w206_ev_store_postgres import LATE_HI, LATE_LO, run_worker, select_exact
    from test_w207_ev_money_postgres import (
        FIVE,
        GOLDEN_FROM,
        GOLDEN_TO,
        PENDING_COPY,
        VECTORS,
        EV_KEY,
        ev_money_rows,
        ev_window,
        five_reads,
        golden_tariff,
        money,
        money_head,
    )

    from assetops_backend.analytics.composition import build_ev_read_service
    from assetops_backend.analytics.ev_reads import encode_cursor
    from assetops_backend.ev_assessment_api import build_ev_assessment_router
    from assetops_backend.ev_site_api import build_ev_site_router
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication
    from assetops_backend.financials.composition import build_ev_site_read_service

CODE = "EV-LAB-001"
ROUTES = {"overview": "overview", "evidence": "evidence", "analysis": "evidence/analysis",
          "financials": "financials", "assumptions": "financial-assumptions"}
ENVELOPE = ("site_id", "window", "currentness", "source_provenance", "limitations")
LINKS = {"self", "evidence", "analysis", "finding", "financials"}
FIELDS = {
    "overview": {"status", "objective", "denominator", "energy", "site_power", "findings", "needs_attention",
                 "consequence_summary", "links"},
    "evidence": {"capabilities", "sources", "next_evidence", "links"},
    "analysis": {"items", "total_count", "excluded_records", "claim_rules", "next_cursor", "links"},
    "financials": {"consequence", "history", "not_included", "next_cursor", "links"},
    "assumptions": {"tariff", "tariff_revision_count", "publication_note", "consequence_tariff", "billing_state",
                    "missing_keys", "links"},
}
CLAIMS = ["SESSION_OUTCOME", "SERVICE_STATE", "DELIVERED_ENERGY", "FAULT_ASSOCIATION", "SITE_POWER_CONTEXT",
          "POWER_CONSTRAINT", "GROSS_TARIFF_SCENARIO"]
NO_SELECTION = "No selected EV session assessment covers this window yet."
SOURCE_UNVERIFIED = "Source or binding unverified for this record."


def client(built, *, site_type="EV_CHARGING", access=None, reads="real") -> TestClient:
    site = SimpleNamespace(id=built.site_id, site_type=site_type)
    registry = SimpleNamespace(imported=lambda code: site if code == CODE else None,
                               tenant=lambda: SimpleNamespace(id=built.tenant_id))
    kw = {} if access is None else {"access": access}
    app = FastAPI()
    app.include_router(build_ev_assessment_router(registry, build_ev_read_service(URL), **kw))
    app.include_router(build_ev_site_router(registry, build_ev_site_read_service(URL) if reads == "real" else reads,
                                            **kw))
    return TestClient(app)


def get(c: TestClient, path: str, status: int = 200) -> dict:
    response = c.get(f"/api/sites/{CODE}/ev/{path}")
    assert response.status_code == status, response.text
    return response.json()


def error(c: TestClient, path: str, status: int) -> str:
    body = get(c, path, status)
    assert set(body) == {"error"} and set(body["error"]) == {"code", "message"}, body
    return body["error"]["code"]


def all_five(c: TestClient, query: str = "") -> dict:
    sep = "?" if query else ""
    return {name: get(c, f"{path}{sep}{query}") for name, path in ROUTES.items()}


def analysis_all(c: TestClient, query: str, limit: int) -> list:
    """Every Analysis page of one selection; the full-window count is independent of the page."""
    items, cursor, total = [], None, None
    while True:
        page = get(c, f"evidence/analysis?{query}&limit={limit}" + (f"&cursor={cursor}" if cursor else ""))
        assert total is None or page["total_count"] == total
        total = page["total_count"]
        items += page["items"]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(items) == total
    return items


def check_shape(reads: dict, w206: dict) -> None:
    """Every route carries W2-06's public envelope verbatim, with its own W2-07 fields alongside."""
    for name, body in reads.items():
        assert set(body) == set(ENVELOPE) | FIELDS[name], (name, sorted(body))
        assert {k: body[k] for k in ENVELOPE} == {k: w206[k] for k in ENVELOPE}, name
        assert set(body["currentness"]) == {"state", "as_of", "limitation"}
        assert set(body["source_provenance"]) == {"classification", "source_ids", "evidence_ids", "basis_sha256",
                                                  "reasons"}
        assert set(body["links"]) == LINKS and body["links"]["finding"] is None
        assert body["currentness"]["state"] != "STALE_SOURCE"


def _settled(chain, case: str = "complete"):  # noqa: F811
    built = chain(case)
    built.start_release_upload()
    run_worker(built)
    return built


def test_five_routes_reuse_w206_envelope_and_exact_selection(chain) -> None:  # noqa: F811
    built = _settled(chain)
    tariff = golden_tariff(built)
    assert all(o.succeeded for o in money(built))
    head = money_head(ev_money_rows(built))
    c = client(built)
    reads = all_five(c)
    w206 = get(c, "sessions")
    check_shape(reads, w206)
    known = reads["overview"]["window"]["known_at"]
    lo, hi = ev_window(built)
    assert (reads["overview"]["window"]["from"], reads["overview"]["window"]["to"]) == (_iso(lo), _iso(hi))
    assert w206["currentness"]["state"] == "CURRENT" and w206["source_provenance"]["reasons"] == []
    assert w206["source_provenance"]["classification"] == "REGISTERED_SIMULATION"

    # Overview: W2-06 full-window denominator/status, energy, one selected consequence.
    o = reads["overview"]
    assert (o["status"], o["denominator"]) == (w206["status"], w206["denominator"])
    assert (o["energy"]["supported_kwh"], o["energy"]["complete_kwh"], o["energy"]["partial_kwh"],
            o["energy"]["unknown_seconds"]) == ("30.000", "30.000", "0.000", 0)
    query = f"from={_iso(lo)}&to={_iso(hi)}&known_at={known}"
    accepted = analysis_all(c, query, 200)
    imports = [x for x in accepted if x["role"] == "site_import"]
    power = o["site_power"]
    assert imports and power["claim_limit"] == "CONTEXT_ONLY"  # the replay records Site import intervals
    assert Decimal(power["observed_peak_kw"]) == max(Decimal(x["value_display"]) for x in imports)
    assert power["coverage"]["expected_seconds"] == int((hi - lo).total_seconds())
    assert 0 < power["coverage"]["known_seconds"] <= power["coverage"]["expected_seconds"]
    summary = o["consequence_summary"]
    assert (summary["state"], summary["quantity_kwh"], summary["amount"], summary["currency"]) == (
        "ESTIMATED", "30.000", "8.33250000", "KES")
    assert summary["overlap_group"] == head["overlap_group"] and summary["limitation"] == (
        "Gross tariff scenario; not cash collected.")
    assert o["links"]["self"] == f"/sites/{CODE}/ev?from={_iso(lo)}&to={_iso(hi)}&known_at={known}"

    # Financials: the stored revision with its stored tariff, links and the two clocks.
    f = reads["financials"]["consequence"]
    assert (f["revision_id"], f["state"], f["reason"], f["amount"], f["tariff_revision_id"], f["tariff_value"]) == (
        str(head["id"]), "ESTIMATED", "ELIGIBLE_COMPLETE_INTERVALS", "8.33250000", str(tariff), "0.27775")
    rows = ev_money_rows(built)
    assert f["evidence_ids"] == sorted(str(r["evidence_id"]) for r in rows["ev_consequence_evidence"]
                                       if r["consequence_revision_id"] == head["id"]) and len(f["evidence_ids"]) == 7
    assert f["session_revision_ids"] == sorted(str(r["session_revision_id"]) for r in rows["ev_consequence_session"]
                                               if r["consequence_revision_id"] == head["id"])
    assert _at(f["tariff_recorded_at"]) > _at(known) and _at(f["recorded_at"]) > _at(f["tariff_recorded_at"])
    assert reads["financials"]["not_included"] == ["lost_sales", "collections", "margin", "repair", "warranty"]
    assert reads["financials"]["history"] == []

    # Assumptions: the current published assignment and the later-publication sentence.
    a = reads["assumptions"]
    assert (a["tariff"]["revision_id"], a["tariff"]["value"], a["tariff"]["currency"], a["tariff"]["basis"]) == (
        str(tariff), "0.27775", "KES", "AUTHORED_ESTIMATE")
    assert (_at(a["tariff"]["valid_from"]), _at(a["tariff"]["valid_to"])) == (GOLDEN_FROM, GOLDEN_TO)
    assert a["publication_note"].startswith("Tariff published ") and a["publication_note"].endswith(" UTC.")
    assert "Evidence through" in a["publication_note"] and a["missing_keys"] == [] and a["billing_state"] == "NO_RECORD"
    assert a["consequence_tariff"]["recorded_at"] == f["tariff_recorded_at"]

    # Evidence and Analysis: seven claim rows in mock order, real accepted IDs, one sorted accepted list.
    e = reads["evidence"]
    assert [x["claim"] for x in e["capabilities"]] == CLAIMS
    delivered = {x["claim"]: x for x in e["capabilities"]}["DELIVERED_ENERGY"]
    assert delivered["state"] == "SUPPORTED" and set(f["evidence_ids"]) <= set(delivered["accepted_evidence_ids"])
    assert [x["slot"] for x in e["sources"]] == ["CONNECTOR_1", "CONNECTOR_2", "SITE_METER", "BILLING"]
    assert all(x["contact"]["state"] == "UNKNOWN" for x in e["sources"]) and len(e["next_evidence"]) <= 3
    an = reads["analysis"]
    keys = [(x["source_time"], x["evidence_id"]) for x in accepted]
    assert keys == sorted(keys) and an["total_count"] == len(accepted) and an["items"] == accepted[:50]
    assert set(f["evidence_ids"]) <= {x["evidence_id"] for x in accepted}
    assert set(w206["source_provenance"]["evidence_ids"]) <= {x["evidence_id"] for x in accepted}
    assert [x["claim"] for x in an["claim_rules"]] == CLAIMS
    assert all(x["record_target_state"] == "UNAVAILABLE" and set(x["links"]) == LINKS for x in accepted)
    assert analysis_all(c, query, 37) == accepted

    # q4 selector: a different-basis higher-numbered stored row never wins; the matching row stays current.
    with built.engine.begin() as cx:
        cx.execute(text(
            "INSERT INTO ev_consequence_revision (id, tenant_id, site_id, finding_revision_id, assessment_revision_id, "
            "revision_no, basis_sha256, technical_input_sha256, formula_version, window_start, window_end, "
            "quantity_kwh, state, reason, source_gate, overlap_group, recorded_at) SELECT :i, tenant_id, site_id, "
            "NULL, assessment_revision_id, revision_no + 1, :b, technical_input_sha256, formula_version, window_start, "
            "window_end, quantity_kwh, 'UNPRICED', 'TARIFF_MISSING', source_gate, overlap_group, clock_timestamp() "
            "FROM ev_consequence_revision WHERE id = :h"), {"i": uuid4(), "b": "e" * 64, "h": head["id"]})
    after = all_five(c)
    assert after["financials"]["consequence"]["revision_id"] == str(head["id"])
    assert [h["label"] for h in after["financials"]["history"]] == ["Historical scenario"]

    # Stale basis: a later tariff correction before money recompute -> read guard, null current amount.
    prices = PostgresAssumptionStore(URL)
    try:
        prices.publish(built.tenant_id, built.site_id, Publication(
            assumption_key=EV_KEY, currency="KES", value=Decimal("0.30000"), basis="AUTHORED_ESTIMATE",
            source_reference="W2-07 site-read stale test", valid_from=GOLDEN_FROM, valid_to=GOLDEN_TO,
            change_kind="CORRECTION", correction_reason="stale basis", expected_prior_revision_id=tariff,
            idempotency_key="w207-site-stale-1", channel="SYSTEM_FIXTURE", provenance={}), SYSTEM_PUBLISHER)
    finally:
        prices.dispose()
    stale = all_five(c)
    guard = stale["financials"]["consequence"]
    assert (guard["state"], guard["reason"], guard["amount"], guard["currency"], guard["revision_id"]) == (
        "WITHHELD", "STALE_BASIS", None, None, None)
    assert guard["limitation"] == "The gross tariff scenario is being refreshed."
    assert stale["overview"]["consequence_summary"]["amount"] is None
    assert len(ev_money_rows(built)["ev_consequence_revision"]) == 2  # the guard is never inserted

    # Pending prefix: an overlapping job masks current money on all five; old rows are history only.
    job = uuid4()
    with built.engine.begin() as cx:
        cx.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
            "available_at, created_at) VALUES (:j, :t, :s, 'ev_charging', :a, :b, 'PENDING', now(), now())"),
            {"j": job, "t": built.tenant_id, "s": built.site_id, "a": lo, "b": hi})
    pending = all_five(c)
    check_shape(pending, get(c, "sessions"))
    assert all(b["currentness"]["state"] == "PENDING_RECOMPUTE" and b["currentness"]["limitation"] == PENDING_COPY
               for b in pending.values())
    assert pending["overview"]["currentness"]["as_of"] == w206["currentness"]["as_of"]
    held = pending["financials"]["consequence"]
    assert (held["reason"], held["amount"], held["currency"]) == ("PENDING_RECOMPUTE", None, None)
    assert (pending["overview"]["consequence_summary"]["amount"],
            pending["overview"]["consequence_summary"]["currency"]) == (None, None)
    assert str(head["id"]) in {h["revision_id"] for h in pending["financials"]["history"]}

    # Literal empty prefix: a valid window with no exact selection.
    empty_q = "from=2026-10-07T08:00:00Z&to=2026-10-07T16:00:00Z"
    empty = all_five(c, empty_q)
    check_shape(empty, get(c, f"sessions?{empty_q}"))
    for body in empty.values():
        assert body["currentness"] == {"state": "UNKNOWN", "as_of": None, "limitation": NO_SELECTION}
        assert body["source_provenance"] == {"classification": None, "source_ids": [], "evidence_ids": [],
                                             "basis_sha256": None, "reasons": []}
        assert body["limitations"] == [NO_SELECTION]
    assert empty["overview"]["status"]["state"] == "UNKNOWN"
    assert all(empty["overview"]["denominator"][k] is None for k in
               ("started", "completed", "observed_abort", "incomplete", "contradictory", "orphan",
                "confirmed_delivery", "fault_aborted"))
    assert empty["overview"]["consequence_summary"]["amount"] is None
    assert empty["overview"]["consequence_summary"]["limitation"] == "No gross tariff scenario assessed."
    assert empty["evidence"]["capabilities"] == [] and empty["evidence"]["next_evidence"] == []
    assert (empty["analysis"]["items"], empty["analysis"]["claim_rules"], empty["analysis"]["next_cursor"]) == (
        [], [], None)
    assert (empty["financials"]["consequence"], empty["financials"]["history"]) == (None, [])
    assert (empty["assumptions"]["tariff"], empty["assumptions"]["missing_keys"]) == (None, [EV_KEY])


def test_only_cursor_basis_change_is_ev_site_409(chain) -> None:  # noqa: F811
    built = _settled(chain)
    c = client(built)
    lo, hi = ev_window(built)
    first = get(c, f"evidence/analysis?limit=1")
    known = first["window"]["known_at"]
    q = f"from={_iso(lo)}&to={_iso(hi)}&known_at={known}"
    cursor = first["next_cursor"]
    assert cursor
    seen = set()
    # The route is inside the canonical cursor: an Analysis cursor is a changed basis on Financials.
    seen.add(error(c, f"financials?{q}&cursor={cursor}", 409))
    basis = first["source_provenance"]["basis_sha256"]
    wrong = encode_cursor(lo, hi, _at(known), f"analysis|{'0' * 64}", lo, UUID(int=0))
    seen.add(error(c, f"evidence/analysis?{q}&cursor={wrong}", 409))
    assert seen == {"EV_CURSOR_BASIS_CHANGED"} and basis
    assert error(c, f"evidence/analysis?{q}&cursor=not-a-cursor", 422) == "EV_CURSOR_INVALID"
    codes = set()
    for path in ROUTES.values():
        codes |= {error(c, f"{path}?from={_iso(lo)}", 422), error(c, f"{path}?from=x&from=y", 422),
                  error(c, f"{path}?bogus=1", 422), error(c, f"{path}?from=2026-10-06T08:00:00+03:00&to=x", 422),
                  error(c, f"{path}?from={_iso(lo)}&to={_iso(lo + timedelta(days=32))}", 422)}
    assert codes == {"EV_WINDOW_INVALID", "EV_PARAMETER_UNKNOWN", "EV_TIME_INVALID", "EV_WINDOW_TOO_LONG"}
    for path in ("evidence/analysis", "financials"):
        assert error(c, f"{path}?limit=0", 422) == "EV_LIMIT_INVALID"
        assert error(c, f"{path}?limit=201", 422) == "EV_LIMIT_INVALID"
    assert error(c, "overview?limit=1", 422) == "EV_PARAMETER_UNKNOWN"
    future = _iso(_at(known) + timedelta(seconds=1))
    assert error(c, f"overview?known_at={future}", 422) == "EV_TIME_INVALID"
    assert {error(client(built, access=lambda r, code: 401), p, 401) for p in ROUTES.values()} == {"UNAUTHENTICATED"}
    assert {error(client(built, access=lambda r, code: 403), p, 403) for p in ROUTES.values()} == {
        "SITE_SCOPE_FORBIDDEN"}
    assert {error(client(built, site_type="COLD_CHAIN"), p, 404) for p in ROUTES.values()} == {"SITE_NOT_FOUND"}
    assert {error(client(built, reads=None), p, 503) for p in ROUTES.values()} == {"EV_READ_UNAVAILABLE"}
    # A missing exact selection is 200 UNKNOWN, never a 409, and no route emits EV_SELECTION_UNSETTLED.
    assert get(c, "overview?from=2026-10-08T08:00:00Z&to=2026-10-08T09:00:00Z")["currentness"]["state"] == "UNKNOWN"


def test_source_unverified_record_survives_analysis_paging(chain, monkeypatch) -> None:  # noqa: F811
    built = chain("complete")
    built.start_release_upload()
    rebind(monkeypatch, lambda r: r.kind == "EV_SESSION_START")
    run_worker(built)
    [_rid, result, _claim, lo, hi] = unknown_revisions(built)[0]
    c = client(built)
    q = f"from={_iso(lo)}&to={_iso(hi)}"
    full = get(c, f"evidence/analysis?{q}")
    excluded = result["excluded_records"]
    assert excluded and full["excluded_records"] == excluded
    known = full["window"]["known_at"]
    accepted = analysis_all(c, f"{q}&known_at={known}", 200)
    ids = {x["evidence_id"] for x in excluded}
    rows = [x for x in accepted if x["evidence_id"] in ids]
    assert {x["evidence_id"] for x in rows} == ids  # the real accepted rows, with their full UUIDs
    assert all((x["use"], x["reason"], x["note"], x["record_kind"]) == (
        "EXCLUDED", "SOURCE_UNVERIFIED", SOURCE_UNVERIFIED, "EV_SESSION_START") for x in rows)
    assert all(x["session_id"] is None and x["links"]["analysis"] is None for x in rows)
    paged, cursor = [], None
    while True:
        page = get(c, f"evidence/analysis?{q}&known_at={known}&limit=29" + (f"&cursor={cursor}" if cursor else ""))
        assert page["excluded_records"] == excluded and page["total_count"] == full["total_count"]
        paged += page["items"]
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert paged == accepted


def test_ev_finding_record_ids_are_selected_support(chain) -> None:  # noqa: F811
    built = _settled(chain, "interrupted")
    c = client(built)
    overview = get(c, "overview")
    items = overview["findings"]["items"]
    assert overview["findings"]["count"] == len(items) and items
    q = f"from={overview['window']['from']}&to={overview['window']['to']}&known_at={overview['window']['known_at']}"
    analysis = {x["evidence_id"]: x for x in analysis_all(c, q, 200)}
    for item in items:
        detail = get(c, f"findings/{item['finding_id']}?{q}")
        for key in ("start_evidence_id", "fault_evidence_id", "abort_evidence_id"):
            assert item[key] == detail["claim"].get(key), key
        for key, kind in (("start_evidence_id", "EV_SESSION_START"), ("fault_evidence_id", "EV_CONNECTOR_FAULT"),
                          ("abort_evidence_id", "EV_SESSION_ABORT")):
            assert item[key] is not None, key
            assert (analysis[item[key]]["record_kind"], analysis[item[key]]["use"]) == (kind, "SUPPORT")


@pytest.mark.parametrize("case", CASES)
def test_six_replays_read_through_the_five_routes(chain, case) -> None:  # noqa: F811
    built = _settled(chain, case)
    golden_tariff(built)
    if case == "late-record":
        assert all(o.succeeded for o in money(built))
        built.advance_late()
        assert {b["currentness"]["state"] for b in five_reads(built).values()} == {"PENDING_RECOMPUTE"}
        run_worker(built)
    assert all(o.succeeded for o in money(built))
    reads = five_reads(built)
    assert {b["currentness"]["state"] for b in reads.values()} == {"CURRENT"}
    state, reason, quantity, amount, _links = VECTORS[case]
    current = reads["financials"]["consequence"]
    assert (current["state"], current["reason"], current["quantity_kwh"], current["amount"]) == (
        state, reason, quantity, amount)
    assert current["revision_id"] == str(money_head(ev_money_rows(built))["id"])
    if case == "late-record":
        # The late terminal past the selected end is a real accepted Analysis row of the START-anchored session.
        ends = [x for x in reads["analysis"]["items"] if x["record_kind"] == "EV_SESSION_END"]
        assert ends and all(x["use"] == "SUPPORT" for x in ends), ends
        # A late terminal past the selected end: an exact [08:00, 08:30) selection still reads its 08:31 END as
        # the START-anchored session's accepted row, with W2-06's selected use.
        select_exact(built, LATE_LO, LATE_HI)
        narrow = five_reads(built, LATE_LO, LATE_HI)
        assert narrow["analysis"]["source_provenance"]["basis_sha256"] is not None
        late = [x for x in narrow["analysis"]["items"]
                if x["record_kind"] == "EV_SESSION_END" and _at(x["source_time"]) >= LATE_HI]
        assert late and all(x["use"] is not None for x in late), late
