"""DIESEL-K5 L2 (`.agent/build-sheet-DIESEL-1.md` §9l.2 B1-B5): the fuel-balance night and fuel Finding routes over
real Postgres.

Kobo is imported as K3's B tests do (`test_s1_bindings_postgres.imported`); synthetic windows go through
`PostgresFuelBalanceStore`'s own transaction on a virtual DB clock (K4a's `Fuel` helper); fuel records go through K2
(the Work service on a virtual clock). B4 uses the S4 power Site (`test_s4_consequence_store_postgres.PowerSite`),
which holds a stored dispatch Finding. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

UTC = timezone.utc
NIGHT = date(2026, 10, 10)
TICKET = "ab" * 32

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_k3_fuel_balance_postgres import dip, iso
    from test_k4a_fuel_finding_postgres import Fuel
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_s4_consequence_store_postgres import POWER_DAY, PowerSite, _release_connections  # noqa: F401
    from test_w401_work_service_postgres import PRINCIPAL, VirtualDbClock, oprec

    from assetops_backend.chain import refs
    from assetops_backend.evidence.composition import build_link_rows_reader
    from assetops_backend.fuel_balance import finding_text as ft
    from assetops_backend.fuel_balance import night_text as nt
    from assetops_backend.fuel_balance import rules
    from assetops_backend.fuel_balance.composition import build_fuel_balance_store
    from assetops_backend.fuel_balance.night_read import FuelNightRead
    from assetops_backend.fuel_balance_api import build_fuel_balance_router
    from assetops_backend.work.adapters.postgres_fuel_records import select_fuel_records
    from assetops_backend.work.adapters.postgres_work_store import PostgresWorkStore
    from assetops_backend.work.service import WorkService


class Api:
    """The K5 router over one Site (the only code the scope admits), with the fuel helper and the Work service."""

    def __init__(self, engine, tenant_id: UUID, site_id: UUID, work_start: datetime | None = None) -> None:  # noqa: F811
        with engine.connect() as c:
            self.code = c.execute(text("SELECT site_code FROM site WHERE id = :s"), {"s": site_id}).scalar_one()
        self.fuel = Fuel(engine, tenant_id, site_id)
        self.read = FuelNightRead(URL, store=build_fuel_balance_store(URL), fuel_records=select_fuel_records,
                                  link_rows=build_link_rows_reader())
        scope = {self.code.lower(): (self.code, tenant_id, site_id)}
        app = FastAPI()
        app.include_router(build_fuel_balance_router(self.read, lambda code: scope.get(code.lower())))
        self.client = TestClient(app)
        self.work = None
        if work_start is not None:
            self.work_clock = VirtualDbClock(work_start)
            self.work = PostgresWorkStore(URL, link_rows=build_link_rows_reader(), test_db_clock_override=self.work_clock)

    def get(self, path: str, **params):
        return self.client.get(f"/api/sites/{self.code}{path}", params=params)

    def post(self, body: dict) -> dict:
        status, response = WorkService(self.work).post_operational_record(self.fuel.t, self.fuel.s, body, PRINCIPAL)
        assert status == 201, response
        return response

    def put(self, night: date, state: str, low, high, **terms):
        """A synthetic window whose terms the night text reads (opening, closing, use, records)."""
        start, end = rules.night_window(night, self.fuel.tz)
        self.fuel.clock.now = max(self.fuel.clock.now + timedelta(minutes=1), end + timedelta(hours=1))
        record_ids = terms.pop("record_ids", [])
        gap = terms.pop("gap", False)
        spans = [[rules.iso(start + timedelta(hours=6, minutes=45)), rules.iso(start + timedelta(hours=8, minutes=30))]]
        base = {"accuracy_l": "10", "accuracy_revision_id": None, "sfc_revision_id": None, "no_load_revision_id": None,
                "opening_l": "869.215", "opening_at": rules.iso(start), "closing_l": "705.787",
                "closing_at": rules.iso(end), "deliveries_l": "0", "generator_kwh": "122.3333",
                "idle_seconds": 0, "use_low": "39.0855", "use_high": "47.771", "sfc_l_per_kwh": "0.355",
                "no_load_l_per_h": "4.9", **terms}

        def work(tx):
            latest = tx.latest(self.fuel.tank, night)
            return tx.append(latest, {
                "tank_asset_id": self.fuel.tank, "generator_asset_id": self.fuel.gen, "night_date": night,
                "window_start": start, "window_end": end, "state": state,
                "reason": "MISSING_OPENING" if state == "NOT_ASSESSED" else None, "residual_low": low,
                "residual_high": high, "gap_minutes": 105 if gap else 0, "gap_spans": spans if gap else [],
                "limitations": ["REPORTING_GAP"] if gap else [], "terms": base, "evidence_ids": [],
                "record_ids": record_ids, "input_sha256": uuid4().hex * 2})
        return self.fuel.store.transaction(self.fuel.t, self.fuel.s, work)

    def close(self) -> None:
        self.read.dispose()
        self.fuel.close()
        if self.work is not None:
            self.work.dispose()


@pytest.fixture()
def kobo(store, engine):  # noqa: F811
    result = imported(store)
    api = Api(engine, result.tenant.id, result.site.id, work_start=datetime(2026, 10, 11, 12, tzinfo=UTC))
    yield api
    api.close()


def text_values(node) -> list:
    """Every `value`/`text` leaf of a body (B3: none is a number)."""
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("value", "text") and not isinstance(v, (dict, list)):
                out.append(v)
            else:
                out += text_values(v)
    elif isinstance(node, list):
        for v in node:
            out += text_values(v)
    return out


# --- B1 Kobo with no window ----------------------------------------------------------------------------------


def test_b1_kobo_without_windows_is_hour_mode(kobo) -> None:
    from assetops_backend.mini_depth.read import MiniDepthRead

    mini = MiniDepthRead.from_url(URL, build_link_rows_reader())
    lo, hi = datetime(2026, 10, 10, 6, tzinfo=UTC), datetime(2026, 10, 10, 7, tzinfo=UTC)
    try:
        before = mini.read(tenant_id=kobo.fuel.t, site_id=kobo.fuel.s, site_code=kobo.code, domain="fuel", lo=lo,
                           hi=hi, known_at=datetime(2026, 11, 1, tzinfo=UTC))
        r = kobo.get("/fuel-balance/nights")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["mode"] == "NONE" and body["nights"] == [] and body["site_code"] == kobo.code
        assert set(body["provenance"]) == {"source_provenance", "selected_source_provenance",
                                           "pending_source_provenance"}
        after = mini.read(tenant_id=kobo.fuel.t, site_id=kobo.fuel.s, site_code=kobo.code, domain="fuel", lo=lo,
                          hi=hi, known_at=datetime(2026, 11, 1, tzinfo=UTC))
        assert after == before
        assert kobo.get(f"/fuel-balance/nights/{NIGHT}").status_code == 404
    finally:
        mini.dispose()


# --- B2 the list ---------------------------------------------------------------------------------------------


def test_b2_list_as_known_default_range_and_refusals(kobo) -> None:
    first = kobo.put(NIGHT, "WITHIN_MARGIN", "-24.343", "24.343")
    kobo.put(NIGHT - timedelta(days=20), "WITHIN_MARGIN", "-24.343", "24.343")       # outside the default 14
    second = kobo.put(NIGHT, "UNEXPLAINED", "95.657", "144.343")                      # recorded later
    between = first.recorded_at + timedelta(seconds=30)
    assert first.recorded_at < between < second.recorded_at

    body = kobo.get("/fuel-balance/nights").json()
    assert body["mode"] == "NIGHTS" and [n["night_date"] for n in body["nights"]] == [NIGHT.isoformat()]
    assert body["nights"][0] == {"night_date": "2026-10-10", "label": "Night of 10 Oct · 6 pm to noon",
                                 "state": "UNEXPLAINED", "status": nt.STATUS["UNEXPLAINED"], "tone": "amber",
                                 "revision": 2}
    old = kobo.get("/fuel-balance/nights", known_at=between.isoformat()).json()
    assert [(n["state"], n["revision"]) for n in old["nights"]] == [("WITHIN_MARGIN", 1)]
    wide = kobo.get("/fuel-balance/nights", **{"from": "2026-09-15", "to": "2026-10-11"}).json()
    assert [n["night_date"] for n in wide["nights"]] == ["2026-09-20", "2026-10-10"]

    for params in ({"from": "2026-10-10", "to": "2026-10-10"}, {"from": "2026-10-11", "to": "2026-10-10"},
                   {"from": "2026-09-01", "to": "2026-10-10"}, {"from": "2026-10-1x", "to": "2026-10-10"},
                   {"from": "2026-10-01"}):
        r = kobo.get("/fuel-balance/nights", **params)
        assert r.status_code == 422, params
        assert r.json()["detail"] == {"code": "FUEL_BALANCE_RANGE_INVALID",
                                      "message": "Choose up to 31 nights, with the first night before the last."}
    assert kobo.get("/fuel-balance/nights", **{"from": "2026-09-09", "to": "2026-10-10"}).status_code == 200  # 31
    r = kobo.get(f"/fuel-balance/nights/{NIGHT + timedelta(days=1)}")
    assert r.status_code == 404 and r.json()["detail"]["code"] == "FUEL_BALANCE_NIGHT_NOT_FOUND"
    assert r.json()["detail"]["message"] == "No fuel check is stored for this night."
    other = kobo.client.get("/api/sites/OTHER-001/fuel-balance/nights")
    assert other.status_code == 404


# --- B3 the night body ---------------------------------------------------------------------------------------


def test_b3_night_body_records_half_open_and_notes(kobo) -> None:
    start, end = rules.night_window(NIGHT, kobo.fuel.tz)
    tank = kobo.fuel.tank
    at_start = kobo.post(dip(tank, "k5-b3-start", start, "869"))
    kobo.post(dip(tank, "k5-b3-before", start - timedelta(minutes=1), "870"))
    kobo.post(dip(tank, "k5-b3-end", end, "700"))
    late_dip = kobo.post(dip(tank, "k5-b3-late", end - timedelta(minutes=5), "706"))
    delivery = kobo.post(oprec("k5-b3-del", kind="FUEL_DELIVERY", body="Fuel delivery of 300 L received.",
                               occurred_at=iso(start + timedelta(hours=2)), unit="L", quantity="300",
                               source_document_sha256=TICKET, asset_id=tank))
    kobo.put(NIGHT, "UNEXPLAINED", "95.657", "144.343", gap=True, deliveries_l="300",
             record_ids=[[delivery["id"], delivery["id"]]])

    body = kobo.get(f"/fuel-balance/nights/{NIGHT}").json()
    assert [r["code"] for r in body["records"]] == [at_start["public_code"], delivery["public_code"],
                                                    late_dip["public_code"]]
    assert [r["kind"] for r in body["records"]] == ["Tank dip", "Fuel delivery", "Tank dip"]
    assert [r["volume"] for r in body["records"]] == ["869 L", "300 L", "706 L"]
    assert [c["label"] for c in body["cards"]] == ["Opening evidence", "Recorded deliveries", "Modelled expected use",
                                                   "Residual"]
    cards = {c["key"]: c for c in body["cards"]}
    assert cards["RESIDUAL"]["value"] == "95.7–144.3 L" and cards["DELIVERIES"]["value"] == "300 L"
    assert cards["DELIVERIES"]["note"] == nt.DELIVERIES_NOTE_ONE and cards["OPENING"]["value"] == "869.2 L"
    assert len(body["bars"]) == 5 and len(body["bridge"]) == 5
    assert [b["term"] for b in body["bridge"]] == ["OPENING", "DELIVERIES", "USE", "CLOSING", "RESIDUAL"]
    assert body["notes"] == [ft.gap_line(((start + timedelta(hours=6, minutes=45),
                                           start + timedelta(hours=8, minutes=30)),), kobo.fuel.tz)]
    assert body["status"] == nt.STATUS["UNEXPLAINED"] and body["label"] == "Night of 10 Oct · 6 pm to noon"
    assert body["finding"] is None and body["finding_note"] == nt.FINDING_NOT_RAISED
    assert body["links"] == {"evidence": f"/sites/{kobo.code}/evidence",
                             "fuel_page": f"/sites/{kobo.code}/performance/fuel?night=2026-10-10"}
    assert all(isinstance(v, str) for v in text_values({k: body[k] for k in ("cards", "bars", "bridge")}))
    assert all(isinstance(b["value_l"], (float, type(None))) for b in body["bars"])
    assert {"source_provenance", "selected_source_provenance"} <= set(body["provenance"])

    kobo.put(NIGHT, "WITHIN_MARGIN", "-24.343", "24.343")
    within = kobo.get(f"/fuel-balance/nights/{NIGHT}").json()
    assert within["finding"] is None and within["finding_note"] == nt.FINDING_NONE_WITHIN and within["notes"] == []


# --- B4 / B5 the fuel Finding (phase B) ----------------------------------------------------------------------


def test_b4_fuel_finding_routes_and_dispatch_id_refused(store, engine, capsys) -> None:  # noqa: F811
    night = date(2026, 10, 5)
    site = PowerSite(store, engine, capsys)
    api = Api(engine, site.tenant, site.site)
    try:
        api.put(night, "UNEXPLAINED", "95.657", "144.343", gap=True)
        raised = api.fuel.raise_(night)
        assert raised.status == "OPENED", raised
        fid, rid = str(raised.finding_id), str(raised.revision_id)

        body = api.get(f"/fuel-balance/nights/{night}").json()
        assert body["finding"] == {"finding_id": fid, "title": ft.TITLE,
                                   "text": ft.CLAIM_LINE.format(lo="95.7", hi="144.3", date="5 Oct"),
                                   "href": f"/sites/{api.code}/fuel-findings/{fid}"}
        assert body["finding_note"] is None

        lo, hi = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 31, tzinfo=UTC)
        rows = api.get("/fuel-findings", **{"from": lo.isoformat(), "to": hi.isoformat()}).json()["rows"]
        assert rows == [{"finding_id": fid, "night_date": "2026-10-05", "lifecycle": "SUPPORTED",
                         "text": "Unexplained fuel overnight · 5 Oct · about 95.7–144.3 L",
                         "href": f"/sites/{api.code}/fuel-findings/{fid}"}]
        assert api.get("/fuel-findings", **{"from": hi.isoformat(), "to": lo.isoformat()}).status_code == 422

        page = api.get(f"/fuel-findings/{fid}").json()
        assert (page["finding_id"], page["revision_id"], page["revision_no"], page["lifecycle"]) == (
            fid, rid, 1, "SUPPORTED")
        assert page["lifecycle_text"] == nt.LIFECYCLE["SUPPORTED"] and page["label"] == "Night of 5 Oct · 6 pm to noon"
        assert page["lines"]["claim"] == ft.CLAIM_LINE.format(lo="95.7", hi="144.3", date="5 Oct")
        assert page["lines"]["gap"] is not None and page["lines"]["not_why"] == ft.NOT_WHY
        assert page["lines"]["margin"] == ft.margin_line("10")
        assert "finding" not in page["night"] and page["night"]["night_date"] == "2026-10-05"
        assert [r["revision_no"] for r in page["revisions"]] == [1]
        assert page["links"] == {"canonical": f"/sites/{api.code}/fuel-findings/{fid}",
                                 "fuel_night": f"/sites/{api.code}/performance/fuel?night=2026-10-05",
                                 "fuel_night_label": nt.FUEL_NIGHT_LINK}
        assert page["night"]["records_empty"] == nt.RECORDS_EMPTY

        # a later check withdraws it: two versions, the pinned first still readable
        api.put(night, "WITHIN_MARGIN", "-24.343", "24.343")
        assert api.fuel.raise_(night).status == "WITHDRAWN"
        latest = api.get(f"/fuel-findings/{fid}").json()
        assert latest["lifecycle"] == "NO_LONGER_SUPPORTED" and latest["lines"]["no_longer"] == ft.NO_LONGER
        assert [r["revision_no"] for r in latest["revisions"]] == [1, 2]
        pinned = api.get(f"/fuel-findings/{fid}", revision_id=rid).json()
        assert pinned["revision_no"] == 1 and pinned["lifecycle"] == "SUPPORTED"

        dispatch = site.on(POWER_DAY)
        for path in (f"/fuel-findings/{dispatch['finding_id']}", f"/fuel-findings/{uuid4()}",
                     f"/fuel-findings/{fid}?revision_id={dispatch['id']}"):
            r = api.client.get(f"/api/sites/{api.code}{path}")
            assert r.status_code == 404, path
            assert r.json()["detail"] == {"code": "FUEL_FINDING_NOT_FOUND",
                                          "message": "No such fuel finding for this Site."}
    finally:
        api.close()
        site.prices.dispose()
        site.store.dispose()


def test_b4_another_sites_fuel_finding_is_404(store, engine) -> None:  # noqa: F811
    kisiwa_like = imported(store)
    other = imported(store, code="KOBO-002")
    a = Api(engine, kisiwa_like.tenant.id, kisiwa_like.site.id)
    b = Api(engine, other.tenant.id, other.site.id)
    try:
        a.put(NIGHT, "UNEXPLAINED", "95.657", "144.343")
        raised = a.fuel.raise_(NIGHT)
        assert raised.status == "OPENED"
        assert a.get(f"/fuel-findings/{raised.finding_id}").status_code == 200
        r = b.get(f"/fuel-findings/{raised.finding_id}")
        assert r.status_code == 404 and r.json()["detail"]["code"] == "FUEL_FINDING_NOT_FOUND"
    finally:
        a.close()
        b.close()


def test_b5_fuel_finding_ref_resolves() -> None:
    fid, rid = str(uuid4()), str(uuid4())
    ref = refs.fuel_finding_ref("KISIWA-001", fid)
    assert ref == {"kind": "FUEL_FINDING", "site": "KISIWA-001", "id": fid} and "FUEL_FINDING" in refs.KINDS
    assert refs.href_for(ref) == f"/sites/KISIWA-001/fuel-findings/{fid}"
    assert refs.href_for(refs.fuel_finding_ref("KISIWA-001", fid, rid)) == (
        f"/sites/KISIWA-001/fuel-findings/{fid}?revision_id={rid}")
    assert refs.links_of({"finding": ref}) == {"finding": f"/sites/KISIWA-001/fuel-findings/{fid}"}
