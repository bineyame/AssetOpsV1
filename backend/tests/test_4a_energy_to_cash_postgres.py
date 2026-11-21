"""4a (spec `specs/4a-energy-to-cash/spec.md` §6.2): energy to cash over Postgres.

PG1 and PG1b run on the Kobo producer world (D-4A.22): three `minigrid-roles-4` feeders, hourly `INTERVAL_MEAN` kW
readings through central ingestion, the loss band published on each LOAD between day 3 and day 4. PG2 and PG3 run on
3A4's `pgworld` with 4b's, 5a's and this slice's commercial fixtures (§5.5). Expected values are §5's hand literals,
the same ones the no-database file asserts (W2). Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database;
skipped (never passed) without it. Run through `tools/heavy-slot.sh --db`.

Mid-build Q1 (default applied): D-4A.22's IMPORT_AT/INSTALL_AT (2026-08-31/09-01) precede the Kobo Foundation's
first period (2026-09-29T11:57:49Z), so `configure_at` refuses; the world uses 2026-09-29T12:00Z / 2026-09-30T06:00Z,
which keeps the roles-4 set (install + 27 min) in force over all of October.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "host" / "tests"))

if URL:
    from sqlalchemy import text
    import demo_combined_kobo as producer
    import pg_harness
    import test_s1_bindings_postgres as pgb
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_3a4_commercial_months_postgres import pgworld  # noqa: F401
    from test_s2_evidence_ledger_postgres import Kit, enable

    import test_4a_energy_to_cash as nodb
    import test_4b_money_leaves as t4b
    import test_5a_targets as t5a
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.mini_depth.read import MiniDepthRead
    from assetops_backend.structure.attribution.composition import build_bridge_read
    from assetops_backend.structure.composition import build_structure_read
    from assetops_backend.structure.energy.inputs import StoreEnergyInputs
    from assetops_backend.structure.targets.composition import build_target_read
    from assetops_contracts.source_envelope_v3 import SourceEnvelopeV3, canonical_envelope_v3_text, v3_message_id

D = Decimal
UTC = timezone.utc
IMPORT_AT = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
INSTALL_AT = datetime(2026, 9, 30, 6, 0, tzinfo=UTC)
LOCAL = timedelta(hours=3)                       # Africa/Addis_Ababa, no daylight saving
LO, HI = datetime(2026, 9, 30, 21, 0, tzinfo=UTC), datetime(2026, 10, 31, 21, 0, tzinfo=UTC)
PINNED = datetime(2026, 11, 2, 0, 0, tzinfo=UTC)
NOW = datetime(2026, 11, 20, tzinfo=UTC)
OCT = "2026-10"
FEEDERS = {"clinic-meter": "load-clinic", "residential-meter": "load-res", "mill-meter": "load-mill"}
BAND = {"property_key": "technical-loss-band", "value": 5, "unit": "%", "source": "SITE", "source_version": 1}
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "energy_to_cash_mto.json"


def _z(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def kw(device: str, day: int, hour: int) -> str:
    """D-4A.15's profile: clinic 2, res 4, mill 2 with 4 at 18:00-19:00 local; day 31 mill 1.5."""
    if device == "clinic-meter":
        return "2"
    if device == "residential-meter":
        return "4"
    if day == 31:
        return "1.5"
    return "4" if hour == 18 else "2"


def interval_envelope(kit, device: str, seq: int, end: datetime, value: str) -> str:
    """`test_s4_consequence_store_postgres.py`'s `INTERVAL_MEAN` shape, one hour ending at `source_time`."""
    b = kit.binding(device)
    e = SourceEnvelopeV3(
        message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                 source_id=b["source_id"], sequence_epoch="epoch-4a", sequence=seq),
        sequence_epoch="epoch-4a", sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
        source_id=b["source_id"], device_id=device, signal_id=b["signal_id"],
        binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
        source_time=_z(end), published_at=_z(end), interval_start=_z(end - timedelta(hours=1)), interval_end=_z(end),
        family="MEASUREMENT", measurement="INTERVAL_MEAN", value=value, unit=b["source_unit"], quality="GOOD",
        unavailable_reason=None)
    return canonical_envelope_v3_text(e)


class Producer:
    """D-4A.22's world: the Kobo producer Site with its roles-4 feeders, readings delivered one Site-local day at a
    time (one batch per feeder, received at 00:30Z the next day)."""

    def __init__(self, store, engine) -> None:  # noqa: F811
        self.engine = engine
        self.result = r = pgb.imported(store, when=IMPORT_AT)
        pgb.convert(store, pgb.BindingService(store, pgb.Clock(INSTALL_AT)), r.tenant, r.site, pgb.FIXTURE)
        producer.configure_at(store, r, INSTALL_AT)
        enable(engine, r.site.id)
        with engine.connect() as c:
            (rev,) = c.execute(text(
                "SELECT id FROM signal_binding_set_revision WHERE site_id = :s AND role_set = 'minigrid-roles-4' "
                "AND superseded_at IS NULL"), {"s": r.site.id}).scalars().all()
        self.kit = Kit(engine, rev)
        assert sorted(b["device_id"] for b in self.kit.doc["bindings"] if b["role"] == "feeder_demand") == sorted(
            FEEDERS)
        self.seq = dict.fromkeys(FEEDERS, 0)
        self.ref = SiteRef(r.tenant.id, r.site.id, "KOBO-001", "MINIGRID", "Africa/Addis_Ababa")
        self.store = store

    def deliver(self, day: int) -> None:
        received = datetime(2026, 10, 1, 0, 30, tzinfo=UTC) + timedelta(days=day)
        clock = pgb.Clock(received)
        ledger = PostgresEvidenceLedger(URL, test_decision_clock_override=clock)
        try:
            service = BatchIngestionService(ledger, clock)
            local_midnight = LO + timedelta(days=day - 1)
            for device in FEEDERS:
                texts = []
                for hour in range(24):
                    self.seq[device] += 1
                    texts.append(interval_envelope(self.kit, device, self.seq[device],
                                                   local_midnight + timedelta(hours=hour + 1), kw(device, day, hour)))
                body = self.kit.seal(texts, device_id=device, mode="SIMULATED")
                out = service.submit(self.kit.principal, body.encode())
                assert {d.decision for d in out.receipt.dispositions} == {"ACCEPTED"}, (device, day, out.receipt.dispositions[:1])
        finally:
            pg_harness.dispose(ledger)

    def publish_band(self) -> None:
        import test_s6_verification_publication as pub
        foundation = pub.registered.FoundationService(
            self.store, "demo", pub.registered.Clock(datetime(2026, 10, 4, 1, 0, tzinfo=UTC)))
        for code in FEEDERS.values():
            foundation.publish_component_properties(
                self.result.tenant, self.result.site, asset_code=code, effective_from=INSTALL_AT + timedelta(minutes=28),
                note="Declared expected technical loss on this feeder (4a test)", properties=[dict(BAND)])

    def energy(self, known_at: datetime | None):
        mini = MiniDepthRead(self.engine, link_rows=None)
        commercial = PostgresCommercialStore(URL)
        try:
            return StoreEnergyInputs(mini, commercial).read(self.ref, OCT, known_at, NOW)
        finally:
            pg_harness.dispose(commercial)


def _absent(lv, cause: str, note: str | None) -> None:
    assert (lv.value, lv.evidence, lv.missing.cause, lv.missing.note) == (None, "NOT_AVAILABLE", cause, note), lv


def test_pg_1_and_1b_feeders_then_the_chain(store, engine):  # noqa: F811
    w = Producer(store, engine)
    for day in (1, 2, 3):
        w.deliver(day)

    # PG1 (a), (b): the read method alone
    mini = MiniDepthRead(engine, link_rows=None)
    t, s = w.ref.tenant_id, w.ref.site_id
    rows = mini.feeder_month(tenant_id=t, site_id=s, lo=LO, hi=HI, known_at=None)
    assert len(rows.binding_sets) == 1 and len(rows.feeder_bindings) == 3
    assert len(rows.readings) == 216 and {r["source_mode"] for r in rows.readings} == {"SIMULATED"}
    early = mini.feeder_month(tenant_id=t, site_id=s, lo=LO, hi=HI, known_at=datetime(2026, 10, 3, 12, tzinfo=UTC))
    assert len(early.readings) == 144

    # PG1 (c), (d): the inputs and the rules
    v = nodb.run(w.energy(PINNED))
    _absent(v["delivered_kwh"], "NOT_RECEIVED", "FEEDER_READINGS_GAP")
    assert v["delivered_kwh"].coverage == nodb.cov(3)
    _absent(v["technical_loss_kwh"], "NOT_CONNECTED", "LOSS_BAND_NOT_DECLARED")

    # PG1 (e): the same absence through the evaluated structure (D-4A.17)
    service = build_structure_read(URL)
    try:
        values = service.read.site(w.ref, OCT, PINNED).values
    finally:
        service.dispose()
    # Mid-build Q2: technical's band step names the band; unexplained takes delivered's absence first (§2.4 step 1),
    # which after days 1-3 is the readings gap. Both are "Not available yet", never 0.
    for f, note in (("technical_loss_kwh", "LOSS_BAND_NOT_DECLARED"), ("unexplained_loss_kwh", "FEEDER_READINGS_GAP")):
        assert (values[f].value, values[f].evidence, values[f].missing.note) == (None, "NOT_AVAILABLE", note), (
            f, values[f])

    w.publish_band()
    for day in range(4, 32):
        w.deliver(day)

    # PG1b (a): delivered and technical from the stored readings and the stored band
    inputs = w.energy(PINNED)
    v = nodb.run(inputs)
    nodb.valued(v["delivered_kwh"], "6000", "MEASURED", nodb.FEED, (nodb.SIM,), coverage=nodb.cov(31))
    nodb.valued(v["technical_loss_kwh"], "300", "MODELLED", nodb.BAND, (nodb.SIM,))
    assert (v["metered_kwh"].value, v["metered_kwh"].missing.cause) == (None, "NOT_CONNECTED")

    # PG1b (b): the same feeders with §5.1's commercial records
    mto = nodb.mto()
    v = nodb.run(dataclasses.replace(inputs, held=mto.held, charges=mto.charges, adjustments=mto.adjustments,
                                     reads=mto.reads, assignments=mto.assignments))
    assert (v["metered_kwh"].value, v["unexplained_loss_kwh"].value) == (D(5580), D(120))
    assert v["unexplained_loss_kwh"].evidence == "MODELLED"

    # PG1b (c): a cutoff before the band was recorded does not see it
    v = nodb.run(w.energy(datetime(2026, 10, 4, 0, 45, tzinfo=UTC)))
    _absent(v["technical_loss_kwh"], "NOT_CONNECTED", "LOSS_BAND_NOT_DECLARED")


def steps(skip: str | None = None) -> list[dict]:
    return [s for s in json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"] if s["step"] != skip]


def commercial_world(w: dict, skip: str | None = None) -> dict:
    """§5.5: 4b's fixture steps, 5a's `targets_lakeside.json`, then this slice's file."""
    t4b.ingest_fixture(w)
    t5a.load(w, 2)
    for step in steps(skip):
        t4b.ingest(w, step["at"], step["batch"], step["entered_by"])
    return w


def test_pg_2_commercial_end_to_end(pgworld):  # noqa: F811
    w = commercial_world(pgworld)
    mto = t4b.site(w, "MTO-001")
    service = build_structure_read(URL)
    try:
        v = service.read.site(mto, OCT).values
        cut = service.read.site(mto, OCT, datetime(2026, 11, 7, 9, 5, tzinfo=UTC)).values
    finally:
        service.dispose()
    assert (v["metered_kwh"].value, v["metered_kwh"].stated, v["metered_kwh"].evidence) == (D(5580), True, "RECORDED")
    assert (v["billed_kwh"].value, v["billed_kwh"].stated, v["billed_kwh"].evidence) == (D(5400), True, "RECORDED")
    assert (v["unmapped_kwh"].value, v["adjustments_kwh"].value) == (D(140), D(40))
    assert v["tariff"].value == D("0.4") and v["tariff"].currency == "USD"
    _absent(v["delivered_kwh"], "NOT_CONNECTED", "FEEDER_NOT_BOUND")
    assert (format(v["revenue"].value, "f"), v["revenue"].stated) == ("2160.00", True)
    assert (cut["metered_kwh"].value, cut["metered_kwh"].missing.cause) == (None, "NOT_CONNECTED")


def _kobo_structure(w: dict) -> None:
    service = build_structure_read(URL)
    try:
        v = service.read.site(t4b.site(w, "KOBO-001"), OCT).values
    finally:
        service.dispose()
    for f in ("delivered_kwh", "technical_loss_kwh", "unexplained_loss_kwh"):
        _absent(v[f], "NOT_CONNECTED", "FEEDER_NOT_BOUND")
    m = v["metered_kwh"]
    assert (m.value, m.stated, m.evidence, m.computed) == (D(8690), True, "RECORDED", None)
    assert (v["adjustments_kwh"].value, v["unmapped_kwh"].value) == (D(45), D(0))


def test_pg_3a_the_bridge_with_the_billed_budget_line(pgworld):  # noqa: F811
    w = commercial_world(pgworld)
    kobo = t5a.refs(w)["KOBO-001"]
    bridges, targets = build_bridge_read(URL), build_target_read(URL)
    try:
        sb = bridges.read.site(kobo, OCT)
        tg = targets.read.site(kobo, OCT)
    finally:
        bridges.dispose()
        targets.dispose()
    revenue = next(r for r in sb.roots["contribution"].rows if r.factor_id == "revenue")
    assert (revenue.split, revenue.effect, format(revenue.effect, "f")) == ("SPLIT", D("38.00"), "38.00")
    by = {r.factor_id: r for r in revenue.rows}
    billed, tariff = by["billed_kwh"], by["tariff"]
    assert (billed.kind, billed.scale, billed.gap, format(billed.effect, "f")) == ("VOLUME", D("0.40"), D(95), "38.00")
    assert (tariff.kind, tariff.scale, tariff.gap, format(tariff.effect, "f")) == ("PRICE", D(8645), D(0), "0.00")
    assert sum(r.effect for r in revenue.rows) == D("38.00")
    (residual,) = [r for r in revenue.rows if r.kind == "RESIDUAL"]
    assert format(residual.effect, "f") == "0.00"
    # D-4A.21: one budget version, so every Kobo target is still used
    assert tg.lines.problem is None and not dict(tg.lines.blocked)
    assert all(u.reason != "BUDGET_VERSIONS" for u in tg.lines.unused)
    tv = tg.structure.values
    assert {f: tv[f].value for f in ("revenue", "fuel_cost", "om", "staff", "billed_kwh")} == {
        "revenue": D("3420.00"), "fuel_cost": D("875.00"), "om": D("600.00"), "staff": D("500.00"),
        "billed_kwh": D(8550)}
    _kobo_structure(w)


def test_pg_3b_without_the_billed_budget_line_revenue_is_not_split(pgworld):  # noqa: F811
    w = commercial_world(pgworld, skip="4")
    service = build_bridge_read(URL)
    try:
        sb = service.read.site(t5a.refs(w)["KOBO-001"], OCT)
    finally:
        service.dispose()
    revenue = next(r for r in sb.roots["contribution"].rows if r.factor_id == "revenue")
    assert revenue.split == "NOT_SPLIT"
