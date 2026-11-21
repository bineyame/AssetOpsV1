"""3B7a units 1 and 2: the frozen monthly structure snapshot, in memory (spec §2.2 to §3.4, §5, §6 tests 2 to 11;
D-3B7A.1 to D-3B7A.12). No database. The Postgres file reuses the `check_*` functions with its own store.

Expected values are 4b's and 5a's literals (spec §5) and fresh reads at the same `known_at` (reviewer guide W2).
"""
from __future__ import annotations

import ast
import json
import shutil
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from uuid import UUID

import pytest
import test_5a_targets as t5a
from test_3a4_commercial_months import READ_AT, new_world
from test_4b_money_leaves import PRICE_ID, fallback, ingest, ingest_fixture

from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.months import PORTFOLIO_ZONE
from assetops_backend.structure.check import StructureError
from assetops_backend.structure.evaluate import Coverage, LeafValue
from assetops_backend.structure.money import CommercialLeafSource
from assetops_backend.structure.read import StructureRead, evaluate_inputs, site_count
from assetops_backend.structure.registry import REGISTRIES
from assetops_backend.structure.sources import ProductLeafSource
from assetops_backend.structure.targets.lines import BudgetLineReader
from assetops_backend.structure.targets.read import TargetCheck, TargetRead
from assetops_backend.structure_snapshot import codec
from assetops_backend.structure_snapshot.build import SnapshotBuilder
from assetops_backend.structure_snapshot.kinds import StoreHeldKinds
from assetops_backend.structure_snapshot.model import REASONS, SNAPSHOT_FORMAT, Freshness, Served, SnapshotRow
from assetops_backend.structure_snapshot.read import SnapshotRead
from assetops_backend.structure_snapshot.adapters.code_digest import import_closure, rules_digest
from assetops_backend.structure_snapshot.store import MemoryStructureSnapshotStore, SnapshotExists
from assetops_backend.structure_snapshot.untracked import untracked

D = Decimal
OCT = "2026-10"
MG = "MINI_GRID"
NAIROBI = "Africa/Nairobi"
AS_OF = READ_AT  # 2026-11-20T08:00:00+00:00
BY = "service:test-3b7a"
RULES_A, RULES_B = "a" * 64, "b" * 64
CODES = ("KOBO-001", "KISIWA-001", "MTO-001")
THIKA_ID = UUID("3b7a0000-0000-4000-8000-000000000009")
LATE_AT = "2026-11-21T09:00:00+00:00"
READ_LATE = datetime(2026, 11, 21, 9, 30, tzinfo=timezone.utc)
REBUILD_AT = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)
PKG = Path(__file__).resolve().parents[1] / "assetops_backend"


# --- the world (spec §5) -------------------------------------------------------------------------------------------

def lakeside(w: dict | None = None, names: dict[str, str] | None = None) -> dict:
    """3A4's world; every step of 4b's money fixture; steps 1 and 2 of 5a's targets fixture."""
    w = ingest_fixture(new_world() if w is None else w)
    return t5a.load(w, 2, names=names)


def refs(w) -> list[SiteRef]:
    out = [SiteRef(w["tid"], w["sites"][c], c, "MINIGRID", NAIROBI) for c in CODES]
    return out + [SiteRef(w["tid"], THIKA_ID, "THIKA-001", "COLDCHAIN", NAIROBI)]


def by_code(w) -> dict[str, SiteRef]:
    return {s.site_code: s for s in refs(w)}


def priced(value: str) -> ProductLeafSource:
    def window(tenant, site, key, start, end, known_at):
        if key == "diesel_price_per_litre":
            return SimpleNamespace(state="PRICED", value=D(value), currency="USD", revision_id=PRICE_ID, reason=None)
        return SimpleNamespace(state="NO_PRICE", value=None, currency=None, revision_id=None, reason="NO_PRICE")
    return ProductLeafSource(SimpleNamespace(latest=lambda *a, **k: ()), window, lambda: READ_AT)


def fresh(w, fb=None) -> SimpleNamespace:
    src = CommercialLeafSource(w["months"], w["store"], fb or fallback())
    actual = StructureRead(src, stated=src)
    lines = BudgetLineReader(w["months"], w["store"])
    return SimpleNamespace(actual=actual, lines=lines, targets=TargetRead(lines, actual))


class Clock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def counter(start: int = 1):
    n = [start - 1]

    def ids() -> UUID:
        n[0] += 1
        return UUID(int=n[0])
    return ids


def setup(w, store=None, rules: str = RULES_A, fb=None, start: int = 1) -> SimpleNamespace:
    store = store if store is not None else MemoryStructureSnapshotStore()
    r = fresh(w, fb)
    kinds = StoreHeldKinds(w["store"])
    clock = Clock(AS_OF)
    builder = SnapshotBuilder(r.actual, r.targets, r.lines, store, kinds, rules, clock, ids=counter(start))
    return SimpleNamespace(w=w, store=store, r=r, kinds=kinds, clock=clock, builder=builder)


def reader(s, rules: str = RULES_A, at: datetime = AS_OF, months=None) -> SnapshotRead:
    return SnapshotRead(s.store, months if months is not None else s.w["months"], s.kinds, rules, Clock(at))


def late_batch() -> dict:
    return {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "expense_ledger",
            "source_system": "lakeside-accounts", "provenance": "source-emulated", "produced_at": LATE_AT,
            "records": [{"format_version": 1, "kind": "EXPENSE", "source_record_id": "KISIWA-EX-OM-1031",
                         "source_version": "1", "site_code": "KISIWA-001",
                         "clocks": {"occurred_at": "2026-10-31T10:00:00+03:00", "recognition_period": "2026-10"},
                         "amount": {"value": "700.00", "currency": "USD"}, "status": "PAID",
                         "body": {"counterparty_ref": "SUP-OM", "category": "OM",
                                  "document_ref": "KISIWA-EX-OM-1031"}}]}


def charge_batch() -> dict:
    return {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "billing_export",
            "source_system": "mto-billing", "provenance": "source-emulated", "produced_at": LATE_AT,
            "records": [{"format_version": 1, "kind": "CHARGE", "source_record_id": "MTO-CH-1101",
                         "source_version": "1", "site_code": "MTO-001",
                         "clocks": {"effective_from": "2026-11-01", "effective_to": "2026-12-01",
                                    "recognition_period": "2026-11"},
                         "amount": {"value": "100.00", "currency": "USD"}, "quantity": {"value": "250", "unit": "kWh"},
                         "body": {"account_ref": "C-3001", "line_type": "USAGE", "tariff_code": "T-MTO",
                                  "tariff_class": "STANDARD"}}]}


def ingest_late(w) -> None:
    ingest(w, LATE_AT, late_batch(), BY)


def ingest_charge(w) -> None:
    ingest(w, LATE_AT, charge_batch(), BY)


def row_count(store) -> int:
    return len(store.rows) if isinstance(store, MemoryStructureSnapshotStore) else store.count_rows()


# --- unit 1: test 2, the codec ---------------------------------------------------------------------------------------

def _site_row(w, s, inputs, actual, targets, payload, *, rid=1) -> SnapshotRow:
    return SnapshotRow(UUID(int=rid), w["tid"], s.site_id, OCT, MG, REGISTRIES[MG].version, SNAPSHOT_FORMAT, AS_OF,
                       BY, True, RULES_A, (), (targets.lines.stamp,), payload, codec.digest(payload), None)


def _numbers(obj, out: list) -> list:
    if isinstance(obj, dict):
        for v in obj.values():
            _numbers(v, out)
    elif isinstance(obj, list):
        for v in obj:
            _numbers(v, out)
    elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
        out.append(obj)
    return out


def _no_float(text: str):
    raise AssertionError(f"a JSON float in the payload: {text}")


@pytest.mark.parametrize("code", CODES)
def test_2_codec_round_trip(code) -> None:
    w = lakeside()
    r = fresh(w)
    s = by_code(w)[code]
    inputs = r.actual.site_inputs(s, OCT, AS_OF)
    actual = evaluate_inputs(inputs)
    targets = r.targets.site(s, OCT, AS_OF)
    payload = codec.encode_site(w["tid"], s, OCT, AS_OF, inputs, actual, targets)
    snap = codec.decode_site(_site_row(w, s, inputs, actual, targets, payload), s)
    assert snap.inputs == inputs and snap.actual == actual and snap.targets == targets
    assert list(snap.inputs.leaves) == list(inputs.leaves) and list(snap.actual.values) == list(actual.values)
    assert isinstance(snap.inputs.leaves, MappingProxyType) and isinstance(snap.targets.lines.blocked, MappingProxyType)
    assert codec.encode_site(w["tid"], s, OCT, AS_OF, snap.inputs, snap.actual, snap.targets) == payload
    numbers = _numbers(json.loads(payload, parse_float=_no_float), [])
    assert numbers and all(type(n) is int for n in numbers)


def test_2_exact_decimals_and_coverage_survive() -> None:
    w = lakeside()
    r = fresh(w)
    s = by_code(w)["KOBO-001"]
    inputs = r.actual.site_inputs(s, OCT, AS_OF)
    cov = Coverage(28, 31, {"A": 20, "B": 8})
    planted = {"om": "1.3", "staff": "1.30", "diesel_price": "1E+2"}
    leaves = dict(inputs.leaves)
    for f, v in planted.items():
        leaves[f] = LeafValue(D(v), "RECORDED", ("commercial:x",), cov, None, "USD", ("source-emulated",))
    inputs = replace(inputs, leaves=MappingProxyType(leaves))
    actual, targets = r.actual.site(s, OCT, AS_OF), r.targets.site(s, OCT, AS_OF)
    payload = codec.encode_site(w["tid"], s, OCT, AS_OF, inputs, actual, targets)
    snap = codec.decode_site(_site_row(w, s, inputs, actual, targets, payload), s)
    for f, v in planted.items():
        assert str(snap.inputs.leaves[f].value) == v
        assert snap.inputs.leaves[f].coverage == cov
    assert '"1E+2"' in payload and '"1.30"' in payload
    _numbers(json.loads(payload, parse_float=_no_float), [])


def test_2_a_changed_payload_is_never_decoded() -> None:
    w = lakeside()
    r = fresh(w)
    s = by_code(w)["KOBO-001"]
    inputs = r.actual.site_inputs(s, OCT, AS_OF)
    actual, targets = evaluate_inputs(inputs), r.targets.site(s, OCT, AS_OF)
    payload = codec.encode_site(w["tid"], s, OCT, AS_OF, inputs, actual, targets)
    row = _site_row(w, s, inputs, actual, targets, payload)
    assert '"883.00"' in payload
    with pytest.raises(RuntimeError, match="snapshot payload does not match its digest"):
        codec.decode_site(replace(row, payload=payload.replace('"883.00"', '"883.01"', 1)), s)


def test_2_portfolio_round_trip() -> None:
    w = lakeside()
    r = fresh(w)
    pl = r.lines.portfolio(w["tid"], OCT, structure_key=MG, known_at=AS_OF)
    asked = [s.site_code for s in refs(w)]
    excluded = {"THIKA-001": ("STRUCTURE_NOT_DECLARED",)}
    payload = codec.encode_portfolio(w["tid"], OCT, MG, REGISTRIES[MG].version, AS_OF, asked, excluded, pl)
    row = SnapshotRow(UUID(int=9), w["tid"], None, OCT, MG, REGISTRIES[MG].version, SNAPSHOT_FORMAT, AS_OF, BY, True,
                      RULES_A, (), (pl.stamp,), payload, codec.digest(payload), ())
    snap = codec.decode_portfolio(row, {})
    assert snap.portfolio_lines == pl and snap.asked == tuple(asked) and snap.sites_excluded == excluded
    assert codec.encode_portfolio(w["tid"], OCT, MG, REGISTRIES[MG].version, AS_OF, snap.asked, snap.sites_excluded,
                                  snap.portfolio_lines) == payload


# --- unit 2: tests 3 to 10, 11(a) -------------------------------------------------------------------------------------

def check_3_build_and_serve(w, store=None) -> SimpleNamespace:
    s = setup(w, store)
    sites = refs(w)
    result = s.builder.build(w["tid"], sites, OCT, built_by=BY)
    assert result.as_of == AS_OF and result.excluded == ("THIKA-001",) and list(result.sites) == list(CODES)
    assert result.rules_digest == RULES_A
    read = reader(s)
    served = {c: read.site(w["tid"], by_code(w)[c], OCT) for c in CODES}
    for c, sv in served.items():
        assert sv.state == "SERVED" and sv.as_of == AS_OF, (c, sv.freshness)
        assert sv.freshness.current and sv.freshness.reasons == () and sv.freshness.stale_stamps == ()
        ref = by_code(w)[c]
        assert sv.snapshot.inputs == s.r.actual.site_inputs(ref, OCT, AS_OF)
        assert sv.snapshot.actual == s.r.actual.site(ref, OCT, AS_OF)
        assert sv.snapshot.targets == s.r.targets.site(ref, OCT, AS_OF)
        assert sv.snapshot.stamps == (w["months"].site_month(w["tid"], ref.site_id, OCT, known_at=AS_OF).stamp,)
        assert sv.snapshot.closed_at_build is True and sv.snapshot.built_by == BY
    kobo, kisiwa, mto = (served[c].snapshot for c in CODES)
    a = kobo.actual.values
    assert (a["contribution"].value, a["contribution"].evidence) == (D("883.00"), "RECORDED")
    assert (a["revenue"].value, a["revenue"].stated) == (D("3458.00"), True)
    assert (a["diesel_price"].value, a["diesel_price"].evidence) == (D("1.25"), "DERIVED")
    t = kobo.targets.structure.values["contribution"]
    assert (t.value, t.evidence) == (D("1445.00"), "DECLARED")
    assert kobo.targets.checks == (TargetCheck("contribution", D("1445.00"), D("1445.00"), "USD", True),)
    k = kisiwa.actual.values["contribution"]
    assert (k.value, k.missing_leaves) == (None, ("om",))
    assert kisiwa.targets.structure.values["contribution"].value == D("-65.00")
    assert kisiwa.targets.checks == (TargetCheck("contribution", D("-60.00"), D("-65.00"), "USD", False),)
    assert mto.actual.values["contribution"].value is None
    assert mto.targets.structure.values["contribution"].value == D("915.00")
    assert served["MTO-001"].freshness.untracked == ("diesel_price",)
    assert served["KOBO-001"].freshness.untracked == () and served["KISIWA-001"].freshness.untracked == ()

    pf = read.portfolio(w["tid"], OCT)
    assert pf.state == "SERVED" and pf.as_of == AS_OF and pf.freshness.current and pf.freshness.reasons == ()
    assert pf.freshness.untracked == ("MTO-001:diesel_price",)
    p = pf.snapshot
    assert p.snapshot_id == result.portfolio_snapshot_id and p.asked == tuple(c.site_code for c in sites)
    assert p.sites_excluded == {"THIKA-001": ("STRUCTURE_NOT_DECLARED",)} and list(p.sites) == list(CODES)
    assert p.stamps == (w["months"].portfolio_month(w["tid"], OCT, known_at=AS_OF).stamp,)
    assert p.closed_at_build is True
    act, tgt = p.actual(), p.targets()
    assert act == s.r.actual.portfolio(w["tid"], sites, OCT, AS_OF)
    assert tgt == s.r.targets.portfolio(w["tid"], sites, OCT, AS_OF)
    assert act.composition.values["contribution"].value.value == D("883.00")
    ca = site_count(act, "contribution")
    assert (ca.k, ca.n) == (1, 4) and {c for c, _ in ca.out} == set(CODES) - {"KOBO-001"} | {"THIKA-001"}
    assert act.composition.values["contribution"].included == ("KOBO-001",)
    assert tgt.structure.composition.values["contribution"].value.value == D("2295.00")
    ct = site_count(tgt.structure, "contribution")
    assert (ct.k, ct.n) == (3, 4) and [c for c, _ in ct.out] == ["THIKA-001"]
    assert tgt.structure.composition.values["staff"].value.value == D("1450.00")
    assert [(ln.factor_id, ln.value) for ln in p.portfolio_lines.lines] == [("staff", D("1200.00"))]
    return SimpleNamespace(s=s, result=result, served=served, portfolio=pf)


def test_3_build_and_serve() -> None:
    check_3_build_and_serve(lakeside())


def check_4a_late_invoice(w, store=None) -> SimpleNamespace:
    got = check_3_build_and_serve(w, store)
    s = got.s
    kisiwa_stamp = got.served["KISIWA-001"].snapshot.stamps[0]
    ingest_late(w)
    read = reader(s, at=READ_LATE)
    sv = read.site(w["tid"], by_code(w)["KISIWA-001"], OCT)
    assert sv.state == "SERVED" and not sv.freshness.current and sv.freshness.reasons == ("RECORDS",)
    assert sv.freshness.stale_stamps == (kisiwa_stamp,) and sv.as_of == AS_OF
    assert sv.snapshot == got.served["KISIWA-001"].snapshot
    assert sv.snapshot.inputs.leaves["om"].value is None
    for c in ("KOBO-001", "MTO-001"):
        assert read.site(w["tid"], by_code(w)[c], OCT).freshness.current, c
    pf = read.portfolio(w["tid"], OCT)
    assert pf.freshness.reasons == ("RECORDS",) and pf.freshness.stale_stamps == (kisiwa_stamp,)
    assert pf.state == "SERVED" and pf.snapshot == got.portfolio.snapshot
    return SimpleNamespace(got=got, s=s)


def test_4a_late_invoice_makes_the_read_out_of_date() -> None:
    check_4a_late_invoice(lakeside())


def check_4b_rebuild(w, store=None) -> None:
    got = check_4a_late_invoice(w, store)
    s = got.s
    first_ids = [*got.got.result.sites.values(), got.got.result.portfolio_snapshot_id]
    first_rows = s.store.get(w["tid"], first_ids)
    s.clock.now = REBUILD_AT
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    read = reader(s, at=REBUILD_AT)
    sv = read.site(w["tid"], by_code(w)["KISIWA-001"], OCT)
    assert sv.state == "SERVED" and sv.freshness.current and sv.as_of == REBUILD_AT
    om, contribution = sv.snapshot.actual.values["om"], sv.snapshot.actual.values["contribution"]
    assert (om.value, om.evidence) == (D("700.00"), "RECORDED")
    assert (contribution.value, contribution.evidence) == (D("-250.00"), "RECORDED")
    for c in CODES:
        assert read.site(w["tid"], by_code(w)[c], OCT).freshness.current, c
    assert read.portfolio(w["tid"], OCT).freshness.current
    assert row_count(s.store) == 8
    assert s.store.get(w["tid"], first_ids) == first_rows


def test_4b_rebuild_makes_it_current_and_keeps_the_first_rows() -> None:
    check_4b_rebuild(lakeside())


def test_4c_one_build_one_instant() -> None:
    w = lakeside()
    ingest_late(w)  # recorded at 2026-11-21T09:00Z, after the build's instant
    s = setup(w)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    sv = reader(s, at=READ_LATE).site(w["tid"], by_code(w)["KISIWA-001"], OCT)
    assert sv.snapshot.inputs.leaves["om"].value is None and sv.snapshot.actual.values["om"].value is None
    assert sv.freshness.reasons == ("RECORDS",) and len(sv.freshness.stale_stamps) == 1


def test_4e_held_kinds_are_read_at_the_build_instant() -> None:
    """F2: a first record of a new kind ingested after `as_of` is not in the frozen held kinds."""
    w = lakeside()
    ingest_charge(w)  # recorded at LATE_AT, after the build's instant AS_OF
    s = setup(w)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    mto = by_code(w)["MTO-001"]
    assert "CHARGE" in s.kinds.of(w["tid"], mto.site_id)  # held by now ...
    (row,) = [r for r in s.store.rows if r.site_id == mto.site_id]
    assert "CHARGE" not in row.held_kinds  # ... but not at as_of
    sv = reader(s, at=READ_LATE).site(w["tid"], mto, OCT)
    assert sv.freshness.reasons == ("RECORDS",) and sv.freshness.changed_kinds == ("MTO-001:CHARGE",)


def check_4d_new_kind(w, store=None) -> None:
    s = setup(w, store)
    mto = by_code(w)["MTO-001"]
    assert "CHARGE" not in s.kinds.of(w["tid"], mto.site_id, known_at=AS_OF)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    before = reader(s).site(w["tid"], mto, OCT).snapshot
    ingest_charge(w)
    read = reader(s, at=READ_LATE)
    sv = read.site(w["tid"], mto, OCT)
    assert sv.freshness.reasons == ("RECORDS",) and sv.freshness.stale_stamps == ()
    assert sv.freshness.changed_kinds == ("MTO-001:CHARGE",) and sv.snapshot == before
    for c in ("KOBO-001", "KISIWA-001"):
        assert read.site(w["tid"], by_code(w)[c], OCT).freshness.current, c
    pf = read.portfolio(w["tid"], OCT)
    assert pf.freshness.reasons == ("RECORDS",) and pf.freshness.changed_kinds == ("MTO-001:CHARGE",)


def test_4d_a_first_record_of_a_new_kind() -> None:
    check_4d_new_kind(lakeside())


def test_5a_month_closed_after_the_build() -> None:
    w = lakeside()
    s = setup(w)
    s.clock.now = datetime(2026, 12, 15, tzinfo=timezone.utc)
    s.builder.build(w["tid"], refs(w), "2026-12", built_by=BY)
    kobo = by_code(w)["KOBO-001"]
    open_read = reader(s, at=datetime(2026, 12, 20, tzinfo=timezone.utc))
    assert open_read.site(w["tid"], kobo, "2026-12").freshness.current
    assert open_read.portfolio(w["tid"], "2026-12").freshness.current
    closed = reader(s, at=datetime(2027, 1, 2, tzinfo=timezone.utc))
    for sv in (closed.site(w["tid"], kobo, "2026-12"), closed.portfolio(w["tid"], "2026-12")):
        assert sv.state == "SERVED" and sv.freshness.reasons == ("MONTH_CLOSED",) and sv.freshness.stale_stamps == ()


def test_5b_built_before_nairobi_month_end() -> None:
    w = lakeside()
    s = setup(w)
    s.clock.now = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    sv = reader(s).site(w["tid"], by_code(w)["KOBO-001"], OCT)
    assert sv.snapshot.closed_at_build is False
    assert sv.freshness.reasons == ("RECORDS", "MONTH_CLOSED")


def _planted(row: SnapshotRow, rid: int, seconds: int, **change) -> SnapshotRow:
    obj = json.loads(row.payload)
    obj.update({k: v for k, v in change.items()})
    payload = codec.canonical(obj)
    return replace(row, id=UUID(int=rid), as_of=row.as_of + timedelta(seconds=seconds), payload=payload,
                   payload_sha256=codec.digest(payload), **change)


def test_6_rebuild_needed_and_no_snapshot() -> None:
    w = lakeside()
    s = setup(w)
    kobo = by_code(w)["KOBO-001"]
    read = reader(s)
    assert read.site(w["tid"], kobo, OCT) == Served("NO_SNAPSHOT", None, None, None)
    assert read.portfolio(w["tid"], OCT) == Served("NO_SNAPSHOT", None, None, None)
    result = s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    row = s.store.get(w["tid"], [result.sites["KOBO-001"]])[0]
    old = _planted(row, 900, 1, structure_version=row.structure_version - 1)
    s.store.put([old])
    assert read.site(w["tid"], kobo, OCT) == Served(
        "REBUILD_NEEDED", None, old.as_of, Freshness(False, ("STRUCTURE_VERSION",), (), (), ()))
    new_format = _planted(row, 901, 2, format=2)
    s.store.put([new_format])
    assert read.site(w["tid"], kobo, OCT) == Served(
        "REBUILD_NEEDED", None, new_format.as_of, Freshness(False, ("FORMAT",), (), (), ()))


class OnlyStale:
    """Exposes `stale` only: any other attribute of the months raises AttributeError (test 7)."""

    def __init__(self, months) -> None:
        self._months = months

    def stale(self, *a, **k):
        return self._months.stale(*a, **k)


def test_7_no_recompute_on_read() -> None:
    w = lakeside()
    s = setup(w)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    plain, only = reader(s), reader(s, months=OnlyStale(w["months"]))
    with pytest.raises(AttributeError):
        OnlyStale(w["months"]).site_month
    for c in CODES:
        assert only.site(w["tid"], by_code(w)[c], OCT) == plain.site(w["tid"], by_code(w)[c], OCT)
    assert only.portfolio(w["tid"], OCT) == plain.portfolio(w["tid"], OCT)
    ingest_late(w)
    late_plain = reader(s, at=READ_LATE)
    late_only = reader(s, at=READ_LATE, months=OnlyStale(w["months"]))
    assert late_only.portfolio(w["tid"], OCT) == late_plain.portfolio(w["tid"], OCT)
    assert late_only.site(w["tid"], by_code(w)["KISIWA-001"], OCT).freshness.reasons == ("RECORDS",)


def test_8_refusals() -> None:
    w = lakeside()
    s = setup(w)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    before = row_count(s.store)
    with pytest.raises(SnapshotExists):
        s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    assert row_count(s.store) == before
    kobo, kisiwa = by_code(w)["KOBO-001"], by_code(w)["KISIWA-001"]
    s.clock.now = AS_OF + timedelta(hours=1)
    s.builder.build(w["tid"], [kobo], OCT, built_by=BY)
    before = row_count(s.store)
    with pytest.raises(SnapshotExists):
        s.builder.build(w["tid"], [kisiwa], OCT, built_by=BY)
    assert row_count(s.store) == before
    assert s.store.latest_site(w["tid"], kisiwa.site_id, OCT).as_of == AS_OF  # no Kisiwa row at the second instant
    s.clock.now = AS_OF + timedelta(hours=2)
    with pytest.raises(ValueError, match="BAD_BUILT_BY"):
        s.builder.build(w["tid"], [kobo], OCT, built_by="test:x")
    other = replace(kobo, tenant_id=UUID(int=77))
    for sites in ([kobo, other], [kobo, kobo]):
        with pytest.raises(StructureError) as e:
            s.builder.build(w["tid"], sites, OCT, built_by=BY)
        assert e.value.code == "STRUCTURE_COMPOSE"
    with pytest.raises(ValueError):
        s.builder.build(w["tid"], [kobo], "2026-13", built_by=BY)
    assert row_count(s.store) == before


def check_9_verify(w, store=None) -> None:
    s = setup(w, store)
    result = s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    v = s.builder.verify(w["tid"], result.portfolio_snapshot_id)
    assert (v.snapshot_id, v.matches, v.differences, v.rules_changed) == (result.portfolio_snapshot_id, True, (), False)
    ingest_late(w)
    assert s.builder.verify(w["tid"], result.portfolio_snapshot_id).matches
    dear = setup(w, s.store, fb=priced("1.40"), start=500)
    v = dear.builder.verify(w["tid"], result.portfolio_snapshot_id)
    assert not v.matches and v.differences == tuple(sorted(v.differences))
    assert "MTO-001:inputs.leaves.diesel_price" in v.differences and "MTO-001:actual.diesel_price" in v.differences
    assert not [d for d in v.differences if d.startswith(("KOBO-001", "KISIWA-001"))], v.differences
    assert setup(w, s.store, rules=RULES_B).builder.verify(w["tid"], result.portfolio_snapshot_id).rules_changed


def test_9_verify_rebuilds_at_the_as_of() -> None:
    check_9_verify(lakeside())


def _imports(path: Path) -> list[tuple[str, str]]:
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom):
            out.extend((node.module or "", a.name) for a in node.names)
        elif isinstance(node, ast.Import):
            out.extend((a.name, "") for a in node.names)
    return out


def test_10_grep() -> None:
    pkg = PKG / "structure_snapshot"
    files = sorted(pkg.rglob("*.py"))
    assert len(files) >= 8
    for f in files:
        assert "float(" not in f.read_text(encoding="utf-8"), f
    imports = _imports(pkg / "read.py")
    assert sorted(n for m, n in imports if m == "assetops_backend.structure.read") == [
        "NOT_DECLARED", "SITE_TYPE_TO_STRUCTURE", "SiteInputs"]
    assert [n for m, n in imports if m == "assetops_backend.structure.check"] == ["StructureError"]
    assert {n for m, n in imports if m == "assetops_backend.structure.targets.read"} <= {
        "SiteTargets", "PortfolioTargets", "TargetCheck"}
    assert not [x for x in imports if x[0] == "assetops_backend.structure.evaluate" or x[1] in (
        "evaluate", "evaluate_inputs", "StructureRead", "TargetRead", "compose")], imports


def test_11a_a_different_code_digest_is_rules() -> None:
    w = lakeside()
    s = setup(w)
    result = s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    current = reader(s, rules=RULES_A).site(w["tid"], by_code(w)["KOBO-001"], OCT)
    assert current.freshness.current
    sv = reader(s, rules=RULES_B).site(w["tid"], by_code(w)["KOBO-001"], OCT)
    assert sv.state == "SERVED" and not sv.freshness.current and sv.freshness.reasons == ("RULES",)
    assert sv.snapshot == current.snapshot
    assert reader(s, rules=RULES_B).portfolio(w["tid"], OCT).freshness.reasons == ("RULES",)
    assert setup(w, s.store, rules=RULES_B).builder.verify(w["tid"], result.portfolio_snapshot_id).rules_changed


def test_reasons_order() -> None:
    assert REASONS == ("RECORDS", "MONTH_CLOSED", "RULES", "STRUCTURE_VERSION", "FORMAT")
    assert PORTFOLIO_ZONE == "UTC"


# --- unit 1: test 11(b), 11(c), the code digest -----------------------------------------------------------------------

def test_11b_the_import_closure() -> None:
    closure = import_closure(PKG)
    assert list(closure) == sorted(closure)
    for name in ("structure.targets.rules", "structure.sources", "structure.money", "structure.registry",
                 "structure.rows_mini_grid", "structure.evaluate", "commercial.months", "commercial.composition",
                 "structure_snapshot.composition", "structure"):
        assert f"assetops_backend.{name}" in closure, name
    assert "assetops_backend" in closure
    # F1 (review r1): every first-party package the build imports is covered (D-3B7A.11 for all of them)
    assert "assetops_contracts" in closure and "assetops_contracts.canonical" in closure
    assert "assetops_contracts.canonical.factors" in closure
    assert not [n for n in closure if not n.startswith(("assetops_backend", "assetops_contracts"))]


def test_11c_the_digest_is_over_the_bytes(tmp_path) -> None:
    copy = tmp_path / "assetops_backend"
    shutil.copytree(PKG, copy, ignore=shutil.ignore_patterns("__pycache__"))
    original = rules_digest(PKG)
    assert len(original) == 64 and rules_digest(copy) == original and rules_digest() == original
    rules = copy / "structure" / "targets" / "rules.py"
    text = rules.read_text(encoding="utf-8")
    start = text.index("TARGET_RULE: Mapping")
    entry = text.index('"om", "staff"', start)  # one AT_ACTUAL entry of TARGET_RULE, reordered
    rules.write_text(text[:entry] + '"staff", "om"' + text[entry + len('"om", "staff"'):], encoding="utf-8")
    assert rules_digest(copy) != original


def test_11d_a_contracts_change_is_rules(tmp_path) -> None:
    """F1: a build under the contracts as they were, read after one byte of contracts/.../factors.py changes."""
    contracts = tmp_path / "assetops_contracts"
    import assetops_contracts
    shutil.copytree(Path(assetops_contracts.__file__).parent, contracts, ignore=shutil.ignore_patterns("__pycache__"))
    built = rules_digest(PKG, contracts)
    assert built == rules_digest()  # the copy is the running contracts
    w = lakeside()
    s = setup(w, rules=built)
    s.builder.build(w["tid"], refs(w), OCT, built_by=BY)
    assert reader(s, rules=built).site(w["tid"], by_code(w)["KOBO-001"], OCT).freshness.current
    factors = contracts / "canonical" / "factors.py"
    factors.write_text(factors.read_text(encoding="utf-8") + "\n# planted\n", encoding="utf-8")
    running = rules_digest(PKG, contracts)
    assert running != built
    read = reader(s, rules=running)
    sv = read.site(w["tid"], by_code(w)["KOBO-001"], OCT)
    assert sv.state == "SERVED" and not sv.freshness.current and sv.freshness.reasons == ("RULES",)
    assert read.portfolio(w["tid"], OCT).freshness.reasons == ("RULES",)


# --- unit 3: the command, with an injected in-memory service (spec §4.4) ------------------------------------------------

def _service(w) -> SimpleNamespace:
    s = setup(w)
    s.store.sites["lakeside-power"] = (w["tid"], tuple(refs(w)))
    return SimpleNamespace(builder=s.builder, store=s.store, s=s)


def test_command_build_verify_and_refusals(capsys, monkeypatch) -> None:
    from assetops_backend.build_structure_snapshot import main

    w = lakeside()
    svc = _service(w)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert main(["build", "--tenant", "lakeside-power", "--month", OCT, "--by", BY]) == 2
    assert capsys.readouterr().err.startswith("NO_DATABASE ")
    for argv, code in ((["build", "--tenant", "lakeside-power", "--month", "2026-13", "--by", BY], "BAD_MONTH"),
                       (["build", "--tenant", "lakeside-power", "--month", OCT, "--by", "test:x"], "BAD_BUILT_BY"),
                       (["build", "--tenant", "nope", "--month", OCT, "--by", BY], "UNKNOWN_TENANT")):
        assert main(argv, service=svc) == 2
        assert capsys.readouterr().err.startswith(code + " ")
    assert row_count(svc.store) == 0
    assert main(["build", "--tenant", "lakeside-power", "--month", OCT, "--by", BY], service=svc) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1
    line = json.loads(out[0])
    assert list(line) == ["as_of", "portfolio_snapshot_id", "sites", "excluded", "rules_digest"]
    assert list(line["sites"]) == sorted(CODES) and line["excluded"] == ["THIKA-001"]  # tenant_sites: by code
    assert main(["build", "--tenant", "lakeside-power", "--month", OCT, "--by", BY], service=svc) == 3
    assert capsys.readouterr().err.startswith("SNAPSHOT_EXISTS ")
    pid = line["portfolio_snapshot_id"]
    assert main(["verify", "--tenant", "lakeside-power", "--snapshot", pid], service=svc) == 0
    v = json.loads(capsys.readouterr().out)
    assert v == {"snapshot_id": pid, "matches": True, "differences": [], "rules_changed": False}
    dear = setup(w, svc.store, fb=priced("1.40"), start=500)
    assert main(["verify", "--tenant", "lakeside-power", "--snapshot", pid],
                service=SimpleNamespace(builder=dear.builder, store=svc.store)) == 4
    assert "MTO-001:actual.diesel_price" in json.loads(capsys.readouterr().out)["differences"]
    assert main(["verify", "--tenant", "lakeside-power", "--snapshot", str(UUID(int=4242))], service=svc) == 2
    assert capsys.readouterr().err.startswith("UNKNOWN_SNAPSHOT ")


def test_command_a_rebuild_fault_is_not_unknown_snapshot(capsys) -> None:
    """F3: an error raised while verify rebuilds is not reported as an unknown snapshot."""
    from assetops_backend.build_structure_snapshot import main

    w = lakeside()
    svc = _service(w)
    assert main(["build", "--tenant", "lakeside-power", "--month", OCT, "--by", BY], service=svc) == 0
    pid = json.loads(capsys.readouterr().out)["portfolio_snapshot_id"]

    def boom(*a, **k):
        raise ValueError("planted rebuild fault")

    svc.s.builder._site_payload = boom
    with pytest.raises(ValueError, match="planted rebuild fault"):
        main(["verify", "--tenant", "lakeside-power", "--snapshot", pid], service=svc)
    assert "UNKNOWN_SNAPSHOT" not in capsys.readouterr().err


def test_composition_releases_all_three_engines_when_the_digest_fails(monkeypatch) -> None:
    """F4: rules_digest() raising after the three services are built disposes all three."""
    import assetops_backend.commercial.composition as cc
    import assetops_backend.structure.composition as sc
    import assetops_backend.structure_snapshot.adapters.code_digest as cd
    import assetops_backend.structure_snapshot.adapters.postgres_structure_snapshot_store as ps
    from assetops_backend.structure_snapshot.composition import build_structure_snapshot

    disposed: list[str] = []

    def fake(name):
        return SimpleNamespace(read=object(), months=object(), store=object(), dispose=lambda: disposed.append(name))

    class FakeStore:
        def dispose(self) -> None:
            disposed.append("snapshot")

    monkeypatch.setattr(sc, "build_structure_read", lambda url: fake("actual"))
    monkeypatch.setattr(cc, "build_commercial_reads", lambda url: fake("commercial"))
    monkeypatch.setattr(ps, "PostgresStructureSnapshotStore", lambda url: FakeStore())

    def broken(*a, **k):
        raise OSError("planted digest failure")

    monkeypatch.setattr(cd, "rules_digest", broken)
    with pytest.raises(OSError, match="planted digest failure"):
        build_structure_snapshot("postgresql://unused")
    assert sorted(disposed) == ["actual", "commercial", "snapshot"]
