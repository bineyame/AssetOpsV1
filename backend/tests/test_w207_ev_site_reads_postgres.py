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
    from assetops_backend.ev_site_reads import (
        KIND_TEXT,
        NEXT_EVIDENCE,
        SOURCE_SUFFIX,
        STATE_TEXT,
        UNKNOWN_SOURCE_SUFFIX,
        UNRECOGNISED_STATE,
        EvSiteReads,
    )
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.assumptions import SYSTEM_PUBLISHER, Publication
    from assetops_backend.financials.composition import build_ev_site_read_service
    from assetops_backend.sites.binding_roles import EV_CONNECTOR_STATES, EV_ROLES_1

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
    assert Decimal(power["observed_peak_kw"]) == max(Decimal(str(x["value_display"])) for x in imports)
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
    # Review r1 L3: the served rows are the first three of the deduplicated ranked candidates.
    served = [x["code"] for x in e["next_evidence"]]
    ranked = ["TERMINAL_GAP", "METER_GAP", "STATUS_GAP", "INDEPENDENT_POWER_GAP", "SITE_IMPORT_GAP", "TARIFF_GAP",
              "BILLING_GAP"]
    assert len(set(served)) == len(served) and served == sorted(served, key=ranked.index)
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


# --- q5 commit-3 wire corrections --------------------------------------------------------------------------------

REVISION_KEYS = {"revision_id", "revision_no", "state", "reason", "quantity_kwh", "tariff_revision_id", "tariff_value",
                 "currency", "amount", "overlap_group", "recorded_at", "tariff_recorded_at", "source_gate",
                 "session_revision_ids", "evidence_ids", "limitation"}
SUMMARY_KEYS = {"state", "reason", "quantity_kwh", "amount", "currency", "overlap_group", "as_of", "limitation"}
ITEM_KEYS = {"evidence_id", "source_label", "role", "record_kind", "value_display", "unit", "source_time", "sent_at",
             "received_at", "quality", "use", "reason", "session_id", "note", "record_target_state", "links",
             "interval_start", "interval_end"}
COVERAGE_UNKNOWN = "Coverage duration cannot be calculated from the selected records."
NULL_COVERAGE = {"known_seconds": None, "expected_seconds": None, "ratio": None, "unit": None}
FIXTURE_WINDOW = {"from": "2026-10-06T08:00:00.000000Z", "to": "2026-10-06T16:00:00.000000Z"}


def _conn(cid: str, enabled: bool = True) -> dict:
    """q6 R1: a Foundation EV_CONNECTOR component, enabled or not."""
    return {"component_id": cid, "component_type": "EV_CONNECTOR",
            "properties": [{"property_key": "ev-connector-enabled", "value": "ENABLED" if enabled else "DISABLED"}]}


def _schedule(cid: str, weekday: str, start: str, end: str) -> dict:
    return {"connector_asset_id": cid, "time_zone": "Etc/UTC",
            "weekly": [{"weekday": weekday, "local_start": start, "local_end": end, "utc_offset_minutes": 0}]}


def test_objective_resolves_selected_foundation_schedule(chain) -> None:  # noqa: F811
    from datetime import datetime, timezone

    from assetops_backend.ev_site_reads import objective_windows

    built = _settled(chain)
    c = client(built)
    o = get(c, "overview")
    assets = {x["slot"]: x["asset_id"] for x in get(c, "evidence")["sources"]}
    objective = o["objective"]
    assert objective["configured_service_window"] == FIXTURE_WINDOW  # both connectors, deduplicated
    assert objective["configured_service_windows"] == [
        {**FIXTURE_WINDOW, "connector_asset_ids": sorted([assets["CONNECTOR_1"], assets["CONNECTOR_2"]])}]
    assert objective["service_schedule_declared"] is True
    # A declared weekly schedule with no occurrence in the selection is not missing configuration.
    wed = get(c, "overview?from=2026-10-07T08:00:00Z&to=2026-10-07T16:00:00Z")["objective"]
    assert (wed["configured_service_window"], wed["configured_service_windows"], wed["service_schedule_declared"]) == (
        None, [], True)

    utc = timezone.utc
    lo, hi = datetime(2026, 10, 6, 8, tzinfo=utc), datetime(2026, 10, 6, 16, tzinfo=utc)
    ids = {"c1": "a1", "c2": "a2"}
    # No Foundation, no schedule key, empty weekly lists: not declared.
    assert objective_windows(None, ids, lo, hi) == (None, [], False)
    assert objective_windows({"content": {"components": [_conn("c1")]}}, ids, lo, hi) == (None, [], False)
    assert objective_windows({"content": {"components": [_conn("c1"), _conn("c2")], "connector_enable_schedules": [
        {"connector_asset_id": "c1", "time_zone": "Etc/UTC", "weekly": []}]}}, ids, lo, hi) == (None, [], False)
    # Two different connector schedules: two occurrences in start/end/ID order and no common window.
    two = {"content": {"components": [_conn("c1"), _conn("c2")], "connector_enable_schedules": [_schedule("c1", "TUESDAY", "08:00", "16:00"),
                                                      _schedule("c2", "TUESDAY", "10:00", "14:00")]}}
    common, windows, declared = objective_windows(two, ids, lo, hi)
    assert (common, declared) == (None, True)
    assert windows == [{"from": "2026-10-06T08:00:00.000000Z", "to": "2026-10-06T16:00:00.000000Z",
                        "connector_asset_ids": ["a1"]},
                       {"from": "2026-10-06T10:00:00.000000Z", "to": "2026-10-06T14:00:00.000000Z",
                        "connector_asset_ids": ["a2"]}]
    # A connector enabled on another weekday keeps the single occurrence from being common to all.
    other = {"content": {"components": [_conn("c1"), _conn("c2")], "connector_enable_schedules": [_schedule("c1", "TUESDAY", "08:00", "16:00"),
                                                        _schedule("c2", "MONDAY", "08:00", "16:00")]}}
    assert objective_windows(other, ids, lo, hi)[0] is None
    # A window crossing two occurrences: configured hours are unclipped and both occurrences are listed.
    same = {"content": {"components": [_conn("c1"), _conn("c2")], "connector_enable_schedules": [_schedule("c1", "TUESDAY", "08:00", "16:00"),
                                                       _schedule("c2", "TUESDAY", "08:00", "16:00")]}}
    common, windows, _ = objective_windows(same, ids, datetime(2026, 10, 6, 12, tzinfo=utc),
                                           datetime(2026, 10, 13, 12, tzinfo=utc))
    assert common is None and [(w["from"], w["to"]) for w in windows] == [
        ("2026-10-06T08:00:00.000000Z", "2026-10-06T16:00:00.000000Z"),
        ("2026-10-13T08:00:00.000000Z", "2026-10-13T16:00:00.000000Z")]
    assert all(w["connector_asset_ids"] == ["a1", "a2"] for w in windows)
    # q6 R1: an enabled connector without a schedule keeps c1's occurrence from being common; a disabled one does not.
    one = [_schedule("c1", "TUESDAY", "08:00", "16:00"), {"connector_asset_id": "c2", "time_zone": "Etc/UTC",
                                                           "weekly": []}]
    unscheduled = {"content": {"components": [_conn("c1"), _conn("c2")], "connector_enable_schedules": one}}
    common, windows, declared = objective_windows(unscheduled, ids, lo, hi)
    assert (common, declared) == (None, True) and [w["connector_asset_ids"] for w in windows] == [["a1"]]
    disabled = {"content": {"components": [_conn("c1"), _conn("c2", False)], "connector_enable_schedules": one}}
    assert objective_windows(disabled, ids, lo, hi) == (
        FIXTURE_WINDOW, [{**FIXTURE_WINDOW, "connector_asset_ids": ["a1"]}], True)
    # A schedule declared only for a disabled connector is not a declared service schedule.
    off = {"content": {"components": [_conn("c1", False)],
                       "connector_enable_schedules": [_schedule("c1", "TUESDAY", "08:00", "16:00")]}}
    assert objective_windows(off, ids, lo, hi) == (None, [], False)
    # Declared with no occurrence in the selection: true and an empty list (the UI's "no overlap" case).
    assert objective_windows(same, ids, datetime(2026, 10, 7, 8, tzinfo=utc), datetime(2026, 10, 7, 16, tzinfo=utc)) == (
        None, [], True)


def test_source_contact_uses_bound_source_diagnostics_at_cutoff(chain) -> None:  # noqa: F811
    import json

    built = _settled(chain)
    c = client(built)
    window = get(c, "overview")["window"]
    hi = min(_at(window["to"]), _at(window["known_at"]))  # the contact cutoff min(to, known_at)
    slots = {x["slot"]: x["asset_id"] for x in get(c, "evidence")["sources"]}
    with built.engine.begin() as cx:
        bindings = cx.execute(text(
            "SELECT DISTINCT b.asset_id, b.source_id, b.gateway_id, b.role, g.diagnostic_cadence_seconds "
            "FROM signal_binding_revision b JOIN gateway g ON g.id = b.gateway_id WHERE b.site_id = :s "
            "AND b.asset_id IS NOT NULL"), {"s": built.site_id}).all()
        cx.execute(text("DELETE FROM gateway_diagnostic WHERE site_id = :s"), {"s": built.site_id})

    def bound(slot: str, role: str | None = None) -> set:
        return {(str(b[1]), b[2], b[4]) for b in bindings
                if str(b[0]) == slots[slot] and (role is None or b[3] == role)}

    c1, meter = bound("CONNECTOR_1"), bound("SITE_METER", "ev_site_import")
    # Connector 1 aggregates its own bound sources (one per role) on one registered gateway.
    assert len({x[1] for x in c1}) == 1 and len(meter) == 1, (c1, meter)
    sources = sorted({x[0] for x in c1})
    [gateway] = list({x[1] for x in c1})
    [cadence] = list({x[2] for x in c1})
    [(meter_source, meter_gateway, _cadence)] = list(meter)
    seq = iter(range(1, 100))

    def diagnostic(gw, received, contacts) -> UUID:
        i = uuid4()
        body = json.dumps({k: None if v is None else _iso(v) for k, v in contacts.items()})
        with built.engine.begin() as cx:
            cx.execute(text(
                "INSERT INTO gateway_diagnostic (id, tenant_id, site_id, gateway_id, sequence_epoch, "
                "diagnostic_sequence, observed_at, received_at, last_device_contact_by_source, queue_count, "
                "disk_pressure, mapping_error_count, payload_sha256, diagnostic_text) VALUES (:i, :t, :s, :g, "
                "'w207-q5', :n, :r, :r, CAST(:c AS jsonb), 0, 'OK', 0, :h, '{}')"),
                {"i": i, "t": built.tenant_id, "s": built.site_id, "g": gw, "n": next(seq), "r": received,
                 "c": body, "h": "a" * 64})
        return i

    def contact(slot: str) -> dict:
        return {x["slot"]: x for x in get(c, "evidence")["sources"]}[slot]["contact"]

    keys = {"state", "checked_at", "last_seen_at", "age_seconds", "diagnostic_id", "diagnostic_received_at",
            "cadence_seconds", "by_source"}
    per = {"source_id", "state", "last_seen_at", "age_seconds", "diagnostic_id", "diagnostic_received_at",
           "cadence_seconds"}
    aggregate = ("last_seen_at", "age_seconds", "diagnostic_id", "diagnostic_received_at", "cadence_seconds")

    def multi(got: dict) -> list[dict]:
        """q6 R2: the three-source slot's exact keys, sorted per-source objects and null aggregate details."""
        assert set(got) == keys and got["checked_at"] == _iso(hi)
        assert [x["source_id"] for x in got["by_source"]] == sources and len(sources) == 3
        assert all(set(x) == per for x in got["by_source"])
        assert all(got[k] is None for k in aggregate)
        return got["by_source"]

    # The contact cutoff is min(to, known_at): 09:00 in the stocked replay, not the 09:05 window end.
    assert _iso(hi) == "2026-10-06T09:00:00.000000Z"
    # No eligible diagnostic: UNKNOWN, never "Not connected".
    got = contact("CONNECTOR_1")
    assert got["state"] == "UNKNOWN" and all(x["state"] == "UNKNOWN" for x in multi(got))
    # Another source's contact only: each bound source is NEVER, from that diagnostic (identical states agree).
    other = diagnostic(gateway, hi - timedelta(seconds=50), {str(uuid4()): hi - timedelta(seconds=55)})
    got = contact("CONNECTOR_1")
    assert got["state"] == "NEVER"
    assert all((x["state"], x["diagnostic_id"], x["last_seen_at"]) == ("NEVER", str(other), None) for x in multi(got))
    # Old: contact older than twice the declared cadence.
    old_at = hi - timedelta(seconds=2 * cadence + 1)
    old = diagnostic(gateway, hi - timedelta(seconds=40), {x: old_at for x in sources})
    got = contact("CONNECTOR_1")
    assert got["state"] == "OLD"
    assert all((x["state"], x["last_seen_at"], x["age_seconds"], x["diagnostic_id"], x["cadence_seconds"]) == (
        "OLD", _iso(old_at), 2 * cadence + 1, str(old), cadence) for x in multi(got))
    # Recent: within twice the cadence, from its own key only.
    recent = diagnostic(gateway, hi - timedelta(seconds=30), {x: hi - timedelta(seconds=cadence) for x in sources})
    got = contact("CONNECTOR_1")
    assert got["state"] == "RECENT"
    assert all((x["state"], x["age_seconds"], x["diagnostic_id"], x["diagnostic_received_at"]) == (
        "RECENT", cadence, str(recent), _iso(hi - timedelta(seconds=30))) for x in multi(got))
    # A diagnostic received after the cutoff is not read.
    diagnostic(gateway, hi + timedelta(seconds=5), {x: hi + timedelta(seconds=1) for x in sources})
    assert {x["diagnostic_id"] for x in multi(contact("CONNECTOR_1"))} == {str(recent)}
    # One-source slot: the meter's own key is absent from its gateway's diagnostic: NEVER, not another source's
    # contact; its top-level details are that one source's details.
    assert meter_source not in sources and meter_gateway == gateway
    got = contact("SITE_METER")
    assert set(got) == keys and got["state"] == "NEVER"
    [only] = got["by_source"]
    assert only["source_id"] == meter_source and set(only) == per
    assert {k: got[k] for k in aggregate} == {k: only[k] for k in aggregate} and got["diagnostic_id"] is not None
    # Differing per-source states: MIXED, with null aggregate details and each source's own detail kept.
    diagnostic(gateway, hi - timedelta(seconds=10), {sources[0]: hi - timedelta(seconds=1)})
    got = contact("CONNECTOR_1")
    detail = multi(got)
    assert got["state"] == "MIXED" and len({x["state"] for x in detail}) == 2
    assert detail[0]["age_seconds"] == 1
    billing = contact("BILLING")
    assert set(billing) == keys and (billing["state"], billing["last_seen_at"], billing["by_source"]) == (
        "UNKNOWN", None, [])


def test_claim_coverage_uses_exact_unions_or_null(chain) -> None:  # noqa: F811
    from datetime import datetime, timezone

    from assetops_backend.ev_site_reads import EvSiteReads

    built = _settled(chain)
    c = client(built)
    rules = get(c, "evidence")["capabilities"]
    assert [x["claim"] for x in rules] == CLAIMS
    by = {x["claim"]: x for x in rules}
    lo, hi = ev_window(built)
    assert by["SITE_POWER_CONTEXT"]["coverage"]["expected_seconds"] == int((hi - lo).total_seconds())
    for claim in ("SERVICE_STATE", "FAULT_ASSOCIATION"):
        assert by[claim]["coverage"] == NULL_COVERAGE and by[claim]["limitation"].endswith(COVERAGE_UNKNOWN)
    assert get(c, "overview")["site_power"]["coverage"] == by["SITE_POWER_CONTEXT"]["coverage"]

    t0 = datetime(2026, 10, 6, 8, tzinfo=timezone.utc)

    def at(m):
        return t0 + timedelta(minutes=m)

    def row(role, a, b, use=None, session=None):
        return {"role": role, "interval_start": None if a is None else at(a),
                "interval_end": None if b is None else at(b), "use": use, "session_id": session,
                "evidence_id": str(uuid4()), "value": "1"}

    def session(sid, a, b, state="COMPLETED"):
        return {"session_id": sid, "revision_id": f"r-{sid}", "state": state, "start_at": _iso(at(a)),
                "end_at": None if b is None else _iso(at(b)), "unknown_meter_seconds": 0, "supported_kwh": "1.000"}

    def caps(accepted, sessions, current=None):
        ctx = {"snap": {"lo": at(0), "hi": at(60), "known": at(120), "selected": {"created_at": at(90)},
                        "state": "CURRENT"},
               "accepted": accepted, "sessions": sessions, "tariffs": [],
               "money": {"current": current, "guard": None, "history": []}}
        return {x["claim"]: x for x in EvSiteReads(None, None)._capabilities(ctx)}

    # Duplicate and overlapping Site import intervals count once: [0,20) U [10,30) U [10,30) = 30 of 60 min.
    imports = [row("ev_site_import", 0, 20), row("ev_site_import", 10, 30), row("ev_site_import", 10, 30)]
    two = [session("s1", 0, 30), session("s2", 0, 30)]  # two simultaneous connector sessions
    meters = [row("ev_connector_energy", 0, 30, "SUPPORT", "s1"), row("ev_connector_energy", 0, 30, "SUPPORT", "s1"),
              row("ev_connector_energy", 0, 15, "SUPPORT", "s2")]
    events = [row("ev_session_event", None, None, "SUPPORT", "s1"),
              row("ev_session_event", None, None, "SUPPORT", "s2")]
    got = caps(imports + meters + events, two)
    assert list(got) == CLAIMS
    assert got["SITE_POWER_CONTEXT"]["coverage"] == {"known_seconds": 1800, "expected_seconds": 3600,
                                                     "ratio": "0.5", "unit": "WINDOW_SECONDS"}
    assert got["SITE_POWER_CONTEXT"]["state"] == "LIMITED"  # Full needs complete coverage
    # Session-seconds: each simultaneous session contributes; the duplicate interval within s1 does not.
    assert got["SESSION_OUTCOME"]["coverage"] == {"known_seconds": 3600, "expected_seconds": 3600, "ratio": "1",
                                                  "unit": "SESSION_SECONDS"}
    assert got["SESSION_OUTCOME"]["state"] == "SUPPORTED"
    assert got["DELIVERED_ENERGY"]["coverage"] == {"known_seconds": 2700, "expected_seconds": 3600,
                                                   "ratio": "0.75", "unit": "SESSION_SECONDS"}
    assert got["DELIVERED_ENERGY"]["state"] == "LIMITED"
    # Missing requested/allocated power: null; absent connector-state intervals: null.
    assert got["POWER_CONSTRAINT"]["coverage"] == NULL_COVERAGE
    assert got["POWER_CONSTRAINT"]["state"] == "LIMITED"
    assert got["SERVICE_STATE"]["coverage"] == NULL_COVERAGE and got["SERVICE_STATE"]["state"] == "UNAVAILABLE"
    assert got["GROSS_TARIFF_SCENARIO"]["coverage"] == NULL_COVERAGE  # no priced consequence
    assert got["GROSS_TARIFF_SCENARIO"]["limitation"] == f"Gross scenario only. {COVERAGE_UNKNOWN}"
    # All three power signals: the intersection of the three unions on one time axis = [15,25), 10 min.
    power = imports + [row("ev_requested_power", 5, 25), row("ev_allocated_limit", 15, 60)]
    assert caps(power, [])["POWER_CONSTRAINT"]["coverage"] == {
        "known_seconds": 600, "expected_seconds": 3600, "ratio": format((Decimal(600) / Decimal(3600)).normalize(), "f"),
        "unit": "WINDOW_SECONDS"}
    # An incomplete terminal: no proved span, so session coverage is null and never Full.
    got = caps(meters + events, [session("s1", 0, 30), session("s2", 0, None, "INCOMPLETE")])
    for claim in ("SESSION_OUTCOME", "DELIVERED_ENERGY"):
        assert got[claim]["coverage"] == NULL_COVERAGE and got[claim]["state"] != "SUPPORTED"
        assert got[claim]["limitation"] == COVERAGE_UNKNOWN
    # A priced consequence: the complete eligible priced interval union per session.
    priced = caps(meters + events, two, current={"amount": "1.00", "session_revision_ids": ["r-s1"],
                                                 "evidence_ids": [meters[0]["evidence_id"]]})
    assert priced["GROSS_TARIFF_SCENARIO"]["coverage"] == {"known_seconds": 1800, "expected_seconds": 1800,
                                                           "ratio": "1", "unit": "SESSION_SECONDS"}
    # q6 R3: exact key set on every row; null coverage is all-null with a null unit; the limitation sentence is
    # appended once, with one separating space, to the claim's own limitation (capability and claim-rule rows).
    for x in got.values():
        assert set(x["coverage"]) == {"known_seconds", "expected_seconds", "ratio", "unit"}
        if x["coverage"]["unit"] is None:
            assert x["coverage"] == NULL_COVERAGE and x["limitation"].count(COVERAGE_UNKNOWN) == 1
    assert got["FAULT_ASSOCIATION"]["limitation"] == f"Cause is not established. {COVERAGE_UNKNOWN}"
    assert got["SERVICE_STATE"]["limitation"] == f"Availability is not assessed. {COVERAGE_UNKNOWN}"
    for rule in rules:
        if rule["coverage"]["unit"] is None:
            assert rule["limitation"].count(COVERAGE_UNKNOWN) == 1 and "  " not in rule["limitation"]
    # Gross-scenario completeness: a priced session whose eligible priced intervals cover only part of its span
    # is not complete (ratio != "1"), so the claim cannot be Full.
    partial = caps(meters + events, two, current={"amount": "1.00", "session_revision_ids": ["r-s2"],
                                                  "evidence_ids": [meters[2]["evidence_id"]]})
    assert partial["GROSS_TARIFF_SCENARIO"]["coverage"] == {"known_seconds": 900, "expected_seconds": 1800,
                                                            "ratio": "0.5", "unit": "SESSION_SECONDS"}
    assert partial["GROSS_TARIFF_SCENARIO"]["state"] != "SUPPORTED"


def test_complete_replay_site_import_and_full_analysis_count(chain) -> None:  # noqa: F811
    built = _settled(chain)
    c = client(built)
    o = get(c, "overview")
    lo, hi = ev_window(built)
    power = o["site_power"]
    assert (power["observed_peak_kw"], power["claim_limit"]) == ("60", "CONTEXT_ONLY")
    assert power["coverage"]["known_seconds"] > 0
    assert power["coverage"]["expected_seconds"] == int((hi - lo).total_seconds())
    assert power["limitation"] != "No accepted Site import intervals cover this window."
    q = f"from={o['window']['from']}&to={o['window']['to']}&known_at={o['window']['known_at']}"
    first = get(c, f"evidence/analysis?{q}")
    assert first["total_count"] == 223 and len(first["items"]) == 50 and first["next_cursor"]
    every = analysis_all(c, q, 50)
    assert len({x["evidence_id"] for x in every}) == 223
    assert every[:50] == first["items"] and analysis_all(c, q, 200) == every


def test_analysis_intervals_and_publication_note(chain) -> None:  # noqa: F811
    built = _settled(chain)
    tariff = golden_tariff(built)
    assert all(o.succeeded for o in money(built))
    c = client(built)
    reads = all_five(c)
    window = reads["overview"]["window"]
    known = window["known_at"]
    items = analysis_all(c, f"from={window['from']}&to={window['to']}&known_at={known}", 200)
    assert all(set(x) == ITEM_KEYS for x in items)
    imports = [x for x in items if x["role"] == "site_import"]
    events = [x for x in items if x["role"] == "session_event"]
    assert imports and all(_at(x["interval_start"]) < _at(x["interval_end"]) for x in imports)
    assert events and all(x["interval_start"] is None and x["interval_end"] is None for x in events)
    # Review r1 M3: plain first-cell words and values from the accepted records; no role code, enum or " state".
    suffix = {"session_event": "session", "connector_meter_delta": "energy", "site_import": "site import",
              "connector_status": "connector status", "fault_event": "connector fault",
              "requested_power": "requested power", "allocated_limit": "allocated power limit"}
    for x in items:
        assert x["source_label"].endswith(f" · {suffix.get(x['role'], 'EV reading')}"), x["source_label"]
        if x["record_kind"] in KIND_TEXT:
            assert x["value_display"] == KIND_TEXT[x["record_kind"]] and x["unit"] is None
        if x["role"] == "connector_status":
            assert x["value_display"] in STATE_TEXT.values() and x["unit"] is None
        if x["role"] in ("connector_meter_delta", "site_import"):
            assert x["unit"] in ("kWh", "kW") and Decimal(str(x["value_display"])) >= 0
    assert any(x["source_label"].endswith(" · session") for x in items)
    assert any(x["source_label"].endswith(" · energy") for x in items)
    a = reads["assumptions"]
    recorded = _at(a["tariff"]["recorded_at"])
    assert a["publication_note"] == (
        f"Tariff published {recorded.strftime('%Y-%m-%d %H:%M')} UTC; applied as a scenario to the selected "
        f"delivery window. Evidence through {_at(known).strftime('%Y-%m-%d %H:%M')} UTC.")
    f = reads["financials"]["consequence"]
    assert a["consequence_tariff"] == {"revision_id": str(tariff), "value": f["tariff_value"],
                                       "currency": f["currency"], "recorded_at": f["tariff_recorded_at"]}
    assert set(f) == REVISION_KEYS and set(reads["overview"]["consequence_summary"]) == SUMMARY_KEYS
    assert {"configured_service_window", "configured_service_windows"} <= set(reads["overview"]["objective"])
    # Without a selected current tariff-bearing consequence: explicit nulls.
    empty = all_five(c, "from=2026-10-07T08:00:00Z&to=2026-10-07T16:00:00Z")
    assert (empty["assumptions"]["consequence_tariff"], empty["assumptions"]["publication_note"]) == (None, None)
    assert set(empty["overview"]["consequence_summary"]) == SUMMARY_KEYS


def test_next_evidence_candidates_rank_and_first_three() -> None:
    """Review r1 L3: the ruled candidate rank, deduplicated, before the first-three slice."""
    cand = EvSiteReads._next_candidates
    everything = {"session_terminal", "connector_meter_delta", "connector_status", "site_import", "ev_gross_tariff_per_kwh"}
    many = cand(everything, {"requested_power", "allocated_limit"}, True)
    assert many == ["TERMINAL_GAP", "METER_GAP", "STATUS_GAP", "INDEPENDENT_POWER_GAP", "SITE_IMPORT_GAP",
                    "TARIFF_GAP", "BILLING_GAP"]
    assert many[:3] == ["TERMINAL_GAP", "METER_GAP", "STATUS_GAP"] and len(many[:3]) == 3
    # Independent power outranks Site import, tariff and billing; terminal, meter and status outrank it.
    only = cand({"site_import", "ev_gross_tariff_per_kwh"}, {"requested_power"}, False)
    assert only == ["INDEPENDENT_POWER_GAP", "SITE_IMPORT_GAP", "TARIFF_GAP", "BILLING_GAP"]
    assert cand({"connector_status"}, {"allocated_limit"}, False)[:2] == ["STATUS_GAP", "INDEPENDENT_POWER_GAP"]
    # An unknown-meter session alone yields the meter gap; both power roles observed yields no rank-4 item.
    assert cand(set(), set(), True) == ["METER_GAP", "BILLING_GAP"]
    assert "INDEPENDENT_POWER_GAP" not in cand({"site_import"}, set(), False)
    assert cand(set(), set(), False) == ["BILLING_GAP"]
    assert NEXT_EVIDENCE["INDEPENDENT_POWER_GAP"] == (
        "Record requested and allocated power",
        "Independent requested and allocated readings are needed before a power constraint can be assessed.",
        "analysis")


def test_analysis_plain_mapping_tables_are_complete() -> None:
    """Review r1 M3: every accepted role, state and event kind has a plain word; none falls back to a code."""
    roles = {r.role: r for r in EV_ROLES_1}
    assert SOURCE_SUFFIX == {
        "ev_session_event": "session", "ev_connector_fault": "connector fault", "ev_connector_state": "connector status",
        "ev_connector_energy": "energy", "ev_connector_power": "connector power", "ev_site_import": "site import",
        "ev_requested_power": "requested power", "ev_allocated_limit": "allocated power limit"}
    assert set(SOURCE_SUFFIX) == set(roles) and UNKNOWN_SOURCE_SUFFIX == "EV reading"
    assert STATE_TEXT == {"AVAILABLE": "Available", "UNPLUGGED": "Unplugged", "PLUGGED": "Plugged in",
                          "AUTHORIZING": "Authorizing", "CHARGING": "Charging", "FAULTED": "Faulted",
                          "DISABLED": "Disabled"}
    assert set(STATE_TEXT) == set(EV_CONNECTOR_STATES) and UNRECOGNISED_STATE == "State not recognised"
    assert KIND_TEXT == {"EV_SESSION_START": "Session started", "EV_SESSION_END": "Session ended",
                         "EV_SESSION_ABORT": "Session aborted", "EV_CONNECTOR_FAULT": "Connector fault",
                         "EV_CONNECTOR_CLEAR": "Connector fault cleared"}
    kinds = {k for name in ("ev_session_event", "ev_connector_fault") for k in roles[name].event_kinds}
    assert set(KIND_TEXT) == kinds


def test_analysis_row_words_for_every_role_state_and_event() -> None:
    """Review r1 M3: the row builder's plain first cell and value for all eight roles, seven states, five events."""
    row = EvSiteReads._row_words
    assert row("Connector c1", "ev_connector_state", "STATE", "STATE", "AUTHORIZING", "state") == (
        "Connector c1 · connector status", "Authorizing", None)
    assert row("Connector c2", "ev_session_event", "EVENT", "EV_SESSION_START", None, None) == (
        "Connector c2 · session", "Session started", None)
    assert row("Connector c2", "ev_connector_energy", "INTERVAL_DELTA", "EV_CONNECTOR_ENERGY", "1.250", "kWh") == (
        "Connector c2 · energy", "1.250", "kWh")
    for state, word in STATE_TEXT.items():
        assert row("C", "ev_connector_state", "STATE", "STATE", state, "state")[1:] == (word, None)
    for kind, word in KIND_TEXT.items():
        role = "ev_session_event" if kind.startswith("EV_SESSION") else "ev_connector_fault"
        assert row("C", role, "EVENT", kind, None, None)[1:] == (word, None)
    for role, suffix in SOURCE_SUFFIX.items():
        assert row("C", role, "NUMBER", "X", "5", "kW")[0] == f"C · {suffix}"
    assert row("C", "ev_connector_state", "STATE", "STATE", None, "state")[1:] == (None, None)
    assert row("C", "ev_connector_state", "STATE", "STATE", "ODD_CODE", "state")[1:] == (UNRECOGNISED_STATE, None)
    assert row("C", "ev_unknown_role", "NUMBER", "X", "5", "kW") == ("C · EV reading", "5", "kW")
    assert row("C", None, "NUMBER", "X", "5", "kW")[0] == "C · EV reading"
