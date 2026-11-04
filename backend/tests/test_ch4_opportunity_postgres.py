"""CH-4 L2 (build sheet CH-4 §8.2): opportunity threads on Postgres.

On a fresh, head-pinned database (the `engine` fixture: `pg_harness.fresh_database()`, then the sole
`pg_harness.alembic_head()`), two studies are seeded directly through the mini-decisions store on the W4-02
MINIGRID Site `MG-W402-001`: study A (1-5 Oct) with 0 eligible days, and study B (6-10 Oct) with two revisions and
two selections (r1 LIMITED with 2 eligible days, r2 SUPPORTED with 3). Then:

- backfill step b places one thread with one occurrence (study B) and counts study A as `skipped_ineligible`; a rerun
  writes nothing;
- `OPPORTUNITY_LOOKUP` through both read adapters (the estate snapshot and the board's `PostgresThreadSources`) gives
  identical items, and a `known_at` before the second selection gives the first revision;
- `GET /api/estate/findings?lens=opportunities` and `GET /api/estate/portfolio` carry the item.

The set-up (`seed_opportunities`) is a setup_cache FUNCTION_OP: engine-only effects, plain arguments, a pickled
plain return value.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import pytest

from link_parity import checked
from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401 - fresh head database per module
    from test_w301_estate_index_postgres import imported_before
    from test_w302_evidence_scope_snapshot_postgres import evidence_read
    from test_w402_reads_postgres import CODE, _setup

    import pg_harness
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.estate.composition import build_estate_read
    from assetops_backend.estate.portfolio import EstatePortfolioService
    from assetops_backend.estate.scope import PORTFOLIO_CURSOR_KEY_ENV
    from assetops_backend.estate_api import build_estate_router
    from assetops_backend.estate_portfolio_api import build_estate_portfolio_router
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore

ZONE = "Africa/Nairobi"
FROM = datetime(2026, 10, 6, tzinfo=timezone.utc)
TO = datetime(2026, 10, 11, tzinfo=timezone.utc)
WINDOW = {"from": "2026-10-06T00:00:00Z", "to": "2026-10-11T00:00:00Z"}
A_DAYS = [date(2026, 10, d) for d in range(1, 6)]
B_DAYS = [date(2026, 10, d) for d in range(6, 11)]


def _day(d: date, decision: str, kwh: tuple[str, str] | None = None, constraints: tuple[str, ...] = ()) -> dict:
    return {"local_day": d.isoformat(), "decision": decision,
            "opportunity_kwh": None if kwh is None else {"low": kwh[0], "high": kwh[1]},
            "constraints": list(constraints), "evidence_ids": []}


def _result(status: str, rows: list[dict], headroom: dict | None, limitations: list[str]) -> dict:
    """A u4 frozen five-day result (`mini_decisions/projection.frozen_result` shape)."""
    return {"status": status, "assessed_days": sum(r["decision"] in ("ELIGIBLE", "EXCLUDED") for r in rows),
            "eligible_days": sum(r["decision"] == "ELIGIBLE" for r in rows), "headroom_kw": headroom,
            "day_rows": rows, "limitations": [{"code": c, "evidence_ids": []} for c in limitations]}


#: Study A: every day excluded (no positive headroom) -> SUPPORTED with 0 eligible days, not a Source (R1).
RESULT_A = _result("SUPPORTED", [_day(d, "EXCLUDED", constraints=("HEADROOM_NON_POSITIVE",)) for d in A_DAYS],
                   None, ["HEADROOM_NON_POSITIVE"])
#: Study B r1: 7 and 8 Oct eligible, 9 Oct LIMITED (PV use unknown) -> LIMITED, 2 of 4.
RESULT_B1 = _result("LIMITED", [
    _day(B_DAYS[0], "EXCLUDED", constraints=("HEADROOM_NON_POSITIVE",)), _day(B_DAYS[1], "ELIGIBLE", ("18", "20")),
    _day(B_DAYS[2], "ELIGIBLE", ("16", "19")), _day(B_DAYS[3], "LIMITED", constraints=("PV_USE_MISSING",)),
    _day(B_DAYS[4], "EXCLUDED", constraints=("CHARGE_OBLIGATION_ACTIVE",))],
    None, ["PV_USE_MISSING", "HEADROOM_NON_POSITIVE", "CHARGE_OBLIGATION_ACTIVE"])
#: Study B r2: 9 Oct now read -> SUPPORTED, 3 of 5; headroom on every eligible day = (min low, min high).
RESULT_B2 = _result("SUPPORTED", [
    _day(B_DAYS[0], "EXCLUDED", constraints=("HEADROOM_NON_POSITIVE",)), _day(B_DAYS[1], "ELIGIBLE", ("18", "20")),
    _day(B_DAYS[2], "ELIGIBLE", ("16", "19")), _day(B_DAYS[3], "ELIGIBLE", ("17", "21")),
    _day(B_DAYS[4], "EXCLUDED", constraints=("CHARGE_OBLIGATION_ACTIVE",))],
    {"low": "16", "high": "19"}, ["HEADROOM_NON_POSITIVE", "CHARGE_OBLIGATION_ACTIVE"])


def _hours(days: list[date]) -> list[dict]:
    return [{"local_day": d.isoformat(), "selection_seq": None, "selection_at": None, "mini_revision_id": None,
             "evidence_ids": []} for d in days]


def _now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def seed_opportunities(store, engine) -> dict:  # noqa: F811
    """The W4-02 MINIGRID Site, its import re-dated before the window, and studies A and B through the store
    (named backfill writes, no job). Returns plain IDs and `k1`, an instant between B's two selections."""
    _, t, s = _setup(store, engine)
    imported_before(engine, t, s, FROM - timedelta(days=1))
    mini = PostgresMiniDecisionStore(engine)
    out = {"t": t, "s": s}

    def study(first: date, last: date) -> tuple:
        oid = uuid4()
        with mini.transaction() as c:
            no = mini.insert_opportunity(c, {"id": oid, "tenant_id": t, "site_id": s, "first_day": first,
                                             "last_day": last, "model_version": "mini-opportunity/1"})
        return oid, no

    def revision(oid, no: int, days: list[date], result: dict):
        rid = uuid4()
        with mini.transaction() as c:
            mini.insert_opportunity_revision(c, {
                "id": rid, "tenant_id": t, "site_id": s, "opportunity_id": oid, "revision_no": no,
                "selected_hours": _hours(days), "result": result,
                "input_sha256": "sha256:" + hashlib.sha256(f"{oid}:{no}".encode()).hexdigest(),
                "producer_id": "ch4-l2-seed", "model_version": "mini-opportunity/1"}, backfill=True)
            mini.insert_opportunity_selection(c, {"tenant_id": t, "site_id": s, "opportunity_id": oid,
                                                  "revision_id": rid}, backfill=True)
        return rid

    out["a"], out["a_no"] = study(A_DAYS[0], A_DAYS[-1])
    out["a_r1"] = revision(out["a"], 1, A_DAYS, RESULT_A)
    out["b"], out["b_no"] = study(B_DAYS[0], B_DAYS[-1])
    out["b_r1"] = revision(out["b"], 1, B_DAYS, RESULT_B1)
    out["k1"] = _now(engine)
    out["b_r2"] = revision(out["b"], 2, B_DAYS, RESULT_B2)
    return out


def _backfill(seed: dict) -> tuple[list[dict], list[dict]]:
    reader, writer = build_thread_sources(URL), build_thread_store(URL)
    try:
        return (run_threads(reader, writer, seed["t"], seed["s"], steps=("b",)),
                run_threads(reader, writer, seed["t"], seed["s"], steps=("b",)))
    finally:
        pg_harness.dispose(reader, writer)


def _thread_rows(engine, s) -> tuple[list, list, list]:
    with engine.connect() as c:
        threads = c.execute(text("SELECT id, mechanism FROM finding_thread WHERE site_id = :s"), {"s": s}).all()
        occ = c.execute(text("SELECT thread_id, occurrence_no, opportunity_id, episode_start, episode_end "
                             "FROM finding_thread_occurrence WHERE site_id = :s"), {"s": s}).all()
        events = c.execute(text("SELECT thread_id, seq, state FROM finding_thread_event WHERE site_id = :s"),
                           {"s": s}).all()
    return threads, occ, events


def _both(engine, seed: dict, k: datetime | None) -> tuple[list[dict], list[dict]]:
    """The items through the estate snapshot and through the board's thread sources (one SQL text)."""
    estate = build_estate_read(engine.url.render_as_string(hide_password=False))
    estate._engine = engine
    via_estate = estate.read(lambda snap: snap.opportunity_threads(seed["t"], [seed["s"]], FROM, TO, k))
    board = build_thread_sources(URL)
    try:
        via_board = board.opportunity_threads(seed["t"], [seed["s"]], FROM, TO, k)
    finally:
        pg_harness.dispose(board)
    return via_estate, via_board


def _site(engine, s) -> tuple[str, str]:
    with engine.connect() as c:
        return tuple(c.execute(text("SELECT site_code, name FROM site WHERE id = :s"), {"s": s}).one())


def test_backfill_places_one_thread_and_both_adapters_agree(store, engine) -> None:  # noqa: F811
    seed = seed_opportunities(store, engine)
    with engine.connect() as c:
        assert c.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == pg_harness.alembic_head()

    first, again = _backfill(seed)
    (b,) = first
    assert (b["step"], b["skipped_ineligible"], b["written"]) == ("b", 1, 1), b
    assert b["counts"] == {"ALREADY_PLACED": 1, "NEW_THREAD": 1}, b  # r2 joins r1's occurrence
    (b2,) = again
    assert (b2["skipped_ineligible"], b2["written"], b2["counts"]) == (1, 0, {"ALREADY_PLACED": 2}), b2
    threads, occ, events = _thread_rows(engine, seed["s"])
    assert len(threads) == 1 and threads[0].mechanism == "PRODUCTIVE_USE_HEADROOM"
    (o,) = occ
    assert (o.thread_id, o.occurrence_no, o.opportunity_id) == (threads[0].id, 1, seed["b"])
    # R2: the episode is r1's eligible days (7-8 Oct, Site-local), not the study window or build time.
    assert (o.episode_start.astimezone(timezone(timedelta(hours=3))).isoformat(),
            o.episode_end.astimezone(timezone(timedelta(hours=3))).isoformat()) == (
        "2026-10-07T00:00:00+03:00", "2026-10-09T00:00:00+03:00")
    assert [(e.seq, e.state) for e in events] == [(1, "OPEN")]

    code, name = _site(engine, seed["s"])
    tid, oid = str(threads[0].id), str(seed["b"])
    now = _now(engine)
    via_estate, via_board = _both(engine, seed, now)
    assert via_estate == via_board and len(via_estate) == 1
    (item,) = via_estate
    assert {k: item[k] for k in ("thread_id", "site_id", "site_code", "site_name", "mechanism", "domain")} == {
        "thread_id": tid, "site_id": str(seed["s"]), "site_code": code, "site_name": name,
        "mechanism": "PRODUCTIVE_USE_HEADROOM", "domain": "MINIGRID"}
    assert (item["title"], item["short_label"]) == (f"Daytime solar unused at {name}", f"{name} daytime solar")
    assert (item["state"], item["state_label"], item["state_effective_day"], item["state_day"]) == (
        "OPEN", "Open", "2026-10-07", "2026-10-11")
    assert item["occurrences"] == 1
    assert item["study"] == {"opportunity_id": oid, "code": f"OPP-{seed['b_no']:06d}", "first_day": "2026-10-06",
                             "last_day": "2026-10-10", "status": "SUPPORTED", "eligible_days": 3,
                             "assessed_days": 5, "headroom_kw": {"low": "16", "high": "19"}, "window_hours": 1}
    assert (item["evidence"], item["evidence_label"], item["filter_state"]) == ("SUPPORTED", "Supported", "supported")
    assert item["seen_line"] == "Seen on 3 of 5 well-observed days · 6 Oct–10 Oct"
    assert item["value_line"] == "16–19 kW at midday on every eligible day" and item["limit_line"] is None
    assert "OPPORTUNITY" in item["lens_flags"]
    # CH-5a2a D1: one builder, one encoding (`:` is `%3A`); every link equals href_for of its link_refs sibling
    assert checked(item)["links"] == {"opportunity": f"/sites/{code}/opportunities/{oid}",
                                      "evidence": f"/sites/{code}/performance/renewable?from=2026-10-05T21%3A00%3A00Z"
                                                  "&to=2026-10-10T21%3A00%3A00Z",
                                      "site": f"/sites/{code}"}
    assert item["ref"] == {"kind": "OPPORTUNITY", "site": code, "id": oid}
    assert item["thread_ref"] == {"kind": "THREAD", "site": code, "id": tid}
    # As known now (None) on the board path equals an explicit present cutoff.
    assert build_and_read_board_now(seed) == via_board

    # known_at before the second selection: the first revision is the head (LIMITED, 2 of 4).
    early_estate, early_board = _both(engine, seed, seed["k1"])
    assert early_estate == early_board and len(early_estate) == 1
    early = early_estate[0]
    assert {k: early["study"][k] for k in ("status", "eligible_days", "assessed_days", "headroom_kw")} == {
        "status": "LIMITED", "eligible_days": 2, "assessed_days": 4, "headroom_kw": None}
    assert (early["evidence_label"], early["filter_state"]) == ("Limited evidence", "unconfirmed")
    assert early["seen_line"] == "Seen on 2 of 4 well-observed days · 6 Oct–10 Oct"
    assert early["value_line"] is None
    assert early["limit_line"] == "Limited evidence: 1 of the 5 study days lack a reading needed to size it"
    # Before anything was recorded, nothing is visible.
    with engine.connect() as c:
        before = c.execute(text("SELECT min(created_at) FROM mini_opportunity_revision WHERE site_id = :s"),
                           {"s": seed["s"]}).scalar_one() - timedelta(microseconds=1)
    assert _both(engine, seed, before) == ([], [])


def build_and_read_board_now(seed: dict) -> list[dict]:
    board = build_thread_sources(URL)
    try:
        return board.opportunity_threads(seed["t"], [seed["s"]], FROM, TO, None)
    finally:
        pg_harness.dispose(board)


def test_findings_and_portfolio_bodies_carry_the_item(store, engine, monkeypatch) -> None:  # noqa: F811
    seed = seed_opportunities(store, engine)
    _backfill(seed)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c4" * 32)  # test-only Portfolio deployment key (after the op)
    (item,) = build_and_read_board_now(seed)

    service = EstatePortfolioService(evidence_read(engine))
    app = FastAPI()
    for build in (build_estate_router, build_estate_portfolio_router):
        app.include_router(build(service, lambda: seed["t"], access=lambda request, code: None))
    client = TestClient(app)

    def ok(root: str, **params) -> dict:
        response = client.get(f"/api/estate/{root}?" + urlencode(params))
        assert response.status_code == 200, response.text
        return response.json()

    findings = ok("findings", **WINDOW, lens="opportunities")
    assert findings["opportunities"] == [item]
    count = findings["summary"]["opportunity_count"]
    assert count == 1, count  # D2: the item count whenever the opportunity read succeeds
    assert ok("findings", **WINDOW, lens="opportunities", state="supported")["opportunities"] == [item]
    assert ok("findings", **WINDOW, lens="opportunities", state="unconfirmed")["opportunities"] == []
    assert ok("findings", **WINDOW, lens="cost")["opportunities"] == []
    early = ok("findings", **WINDOW, lens="opportunities", known_at=seed["k1"].astimezone(timezone.utc)
               .isoformat().replace("+00:00", "Z"))["opportunities"]
    assert [i["study"]["status"] for i in early] == ["LIMITED"]

    portfolio = ok("portfolio", **WINDOW, limit=100)
    assert checked(portfolio["opportunity"]) == {"state": "FOUND", "items": [checked(item)], "finding_id": None,
                                        "scenario_amount": None, "headroom": {"low": "16", "high": "19"},
                                        "destination": "/findings/opportunities"}
    assert portfolio["summary"]["opportunity_count"] == 1
    assert portfolio["summary"]["opportunity_labels"] == [item["short_label"]]
    card = next(c for c in portfolio["value_cards"] if c["key"] == "PRODUCTIVE_USE")
    assert (card["state"], card["destination"], card["detail"], card["tone"]) == (
        "FOUND", "/findings/opportunities", item["short_label"], "green")


def test_failing_opportunity_query_leaves_portfolio_rendering_with_unknown(store, engine, monkeypatch) -> None:  # noqa: F811
    """CH-4 fix round 2 (L2): a SQL error in the opportunity read is rolled back to its SAVEPOINT, so the Portfolio's
    later reads still run and the opportunity state is UNKNOWN (not an unavailable page)."""
    seed = seed_opportunities(store, engine)
    _backfill(seed)
    monkeypatch.setenv(PORTFOLIO_CURSOR_KEY_ENV, "c4" * 32)
    monkeypatch.setattr("assetops_backend.estate.adapters.postgres_estate_read.OPPORTUNITY_LOOKUP",
                        "SELECT * FROM table_that_does_not_exist")
    service = EstatePortfolioService(evidence_read(engine))
    app = FastAPI()
    app.include_router(build_estate_portfolio_router(service, lambda: seed["t"], access=lambda request, code: None))
    response = TestClient(app).get("/api/estate/portfolio?" + urlencode({**WINDOW, "limit": 100}))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["opportunity"]["state"] == "UNKNOWN" and body["summary"]["opportunity_count"] is None
