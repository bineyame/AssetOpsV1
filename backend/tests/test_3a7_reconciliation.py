"""3A7 (spec `specs/3A7-month-reconciled/spec.md` §2, §6, §7; rulings D-3A7.1 to D-3A7.13): one closed month
reconciled against the operator's management accounts, over the in-memory commercial store. No database.

Commit 1 of D-SC1.28: the standing as codes and `Decimal`s. Every expected figure, state and reason is a spec §6
literal written by hand (W2), never computed by the code under test; the sentences of §2.7 and §6 (and R6's
`money_word`) are asserted in commit 2, when the words land as SC-1 statements.

`ReconMemoryStore` adds spec §4's two tables and `site_rows` to 3A4's `MonthsMemoryStore` (3A4's file is not edited).
One settable clock is shared by the months and the reconciliation services (handshake R3).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from assetops_backend.accounts.permissions import FINANCE
from assetops_backend.chain.ports import SiteRef
from assetops_backend.commercial.model import SiteRow, StatementRow, ToleranceRow
from assetops_backend.commercial.months import CommercialMonths
from assetops_backend.structure.reconciliation import (DEFAULT_TOLERANCE, HEADINGS, CommercialReconciliation,
                                                        ReconRefused, _compare)
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import Actor
from assetops_backend.structure.sources import ReadContext
from test_3a1_commercial_service import BY, Clock, encode, make_world
from test_3a4_commercial_months import MonthsMemoryStore, READ_AT, steps as kobo_steps

TREE = Path(__file__).resolve().parents[2]
FIXTURE = TREE / "backend" / "tests" / "fixtures" / "3a7" / "reconciliation_two_sites.json"
D = Decimal
USD = "USD"
FIONA = Actor(UUID("3a700000-0000-4000-8000-00000000f10a"), FINANCE)
ANA = Actor(UUID("3a700000-0000-4000-8000-0000000000a1"), "ANALYST")
S1_AT, S2_AT, S3_AT, S4_AT = (datetime(2026, 11, d, 10, 0, tzinfo=timezone.utc) for d in (5, 12, 13, 14))
T3_SET_AT = datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc)
OWNER_REF = "owner/owner-tol-2026-11-20.md"


class ReconMemoryStore(MonthsMemoryStore):
    """3A4's store plus spec §4: the statements, the tolerances and `site_rows` (a Site's type defaults to
    MINIGRID). Each read is counted, for R8."""

    def __init__(self) -> None:
        super().__init__()
        self.site_types: dict[UUID, tuple[str, str]] = {}
        self.statement_rows: list[StatementRow] = []
        self.tolerance_rows: list[ToleranceRow] = []
        self.reads: dict[str, int] = {"accounts_statements": 0, "tolerances": 0, "site_rows": 0}

    def add_site(self, tenant_id: UUID, code: str, site_type: str = "MINIGRID") -> UUID:
        sid = super().add_site(tenant_id, code)
        self.site_types[sid] = (code, site_type)
        return sid

    def add_accounts_statement(self, row: StatementRow) -> None:
        self.statement_rows.append(row)

    def accounts_statements(self, tenant_id: UUID) -> tuple[StatementRow, ...]:
        self.reads["accounts_statements"] += 1
        return tuple(sorted((r for r in self.statement_rows if r.tenant_id == tenant_id),
                            key=lambda r: (r.recorded_at, str(r.id))))

    def add_tolerance(self, row: ToleranceRow) -> None:
        self.tolerance_rows.append(row)

    def tolerances(self, tenant_id: UUID) -> tuple[ToleranceRow, ...]:
        self.reads["tolerances"] += 1
        return tuple(sorted((r for r in self.tolerance_rows if r.tenant_id == tenant_id),
                            key=lambda r: (r.set_at, str(r.id))))

    def site_rows(self, tenant_id: UUID) -> tuple[SiteRow, ...]:
        self.reads["site_rows"] += 1
        rows = [SiteRow(sid, *self.site_types[sid]) for (tid, _key), sid in self.sites.items() if tid == tenant_id]
        return tuple(sorted(rows, key=lambda r: r.site_code))


class CountingMonths(CommercialMonths):
    """3A4's months service; every `site_month` call is logged as (site_id, period, known_at)."""

    def __init__(self, store, *, clock) -> None:
        super().__init__(store, clock=clock)
        self.calls: list[tuple[UUID, str, datetime | None]] = []

    def site_month(self, tenant_id, site_id, period, *, known_at=None):
        self.calls.append((site_id, period, known_at))
        return super().site_month(tenant_id, site_id, period, known_at=known_at)


def owner_reader(root: Path | None):
    """The owner-file port over a temporary owner root (the composition's reader comes in commit 2)."""
    if root is None:
        return None

    def read(ref: str) -> bytes | None:
        path = root / ref
        return path.read_bytes() if path.is_file() else None
    return read


def _services(store, sites: dict, tid: UUID, owner_root: Path | None) -> dict:
    clock = Clock()
    months = CountingMonths(store, clock=clock)
    return dict(store=store, clock=clock, svc=CommercialRecords(store, clock=clock), months=months, tid=tid,
                sites=sites, recon=CommercialReconciliation(months, store, owner_file=owner_reader(owner_root)))


def two_sites_world(owner_root: Path | None = None) -> dict:
    """§6.2: lakeside-power with KOBO-001 and MTO-001 (MINIGRID) and FRZ-001 (COLDCHAIN), and a second tenant."""
    store = ReconMemoryStore()
    tid = store.add_tenant("lakeside-power")
    sites = {code: store.add_site(tid, code, kind) for code, kind in
             (("KOBO-001", "MINIGRID"), ("MTO-001", "MINIGRID"), ("FRZ-001", "COLDCHAIN"))}
    other = store.add_tenant("harvest-cold")
    sites["COLD-THIKA"] = store.add_site(other, "COLD-THIKA", "COLDCHAIN")
    return _services(store, sites, tid, owner_root)


def kobo_world() -> dict:
    """§6.1: 3A4's world (every Site MINIGRID) for 3A4's `commercial_months_kobo.json`."""
    store = ReconMemoryStore()
    w = make_world(store)
    return _services(store, w["sites"], w["tenants"]["lakeside-power"], None)


def two_steps() -> dict[str, dict]:
    return {s["step"]: s for s in json.loads(FIXTURE.read_text(encoding="utf-8"))["steps"]}


def load(w, *names: str) -> None:
    for name in names:
        step = two_steps()[name]
        ingest(w, step["at"], step["batch"])


def ingest(w, at: str, batch: dict) -> None:
    w["clock"].now = datetime.fromisoformat(at)
    result = w["svc"].ingest(w["tid"], encode(batch), entered_by=BY)
    assert result.state == "STORED" and all(o.outcome in ("NEW", "REVISED") for o in result.outcomes), result
    w["clock"].now = READ_AT


def record(w, at: datetime, *, site: str | None, revenue: str, fuel: str, currency: str = USD,
           period: str = "2026-10", actor: Actor = FIONA, source_ref: str = "Management accounts, October 2026"):
    w["clock"].now = at
    try:
        return w["recon"].record(w["tid"], actor, site_code=site, period=period, currency=currency, revenue=revenue,
                                 fuel_cost=fuel, source_ref=source_ref, by_script=True)
    finally:
        w["clock"].now = READ_AT


def owner_file(root: Path, text: str) -> Path:
    path = root / OWNER_REF
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def figures(h) -> tuple:
    """A heading as (state, reason, accounts, recorded, difference, allowed), the Decimals as plain text."""
    def f(v):
        return None if v is None else format(v, "f")
    return (h.state, h.reason, f(h.accounts), f(h.recorded), f(h.difference), f(h.allowed))


def heads(check) -> dict[str, tuple]:
    assert tuple(h.heading for h in check.headings) == HEADINGS
    return {h.heading: figures(h) for h in check.headings}


def standing(w, code: str, period: str = "2026-10", **kw):
    return w["recon"].standing(w["tid"], w["sites"][code], period, **kw)


def only(w):
    (one,) = w["recon"].statements(w["tid"])
    return one


# ---------------------------------------------------------------- R1: §6.1, 3A4's Kobo month


def test_r1_kobo_before_and_after_the_corrections() -> None:
    w = kobo_world()
    for s in kobo_steps()[:4]:  # A to D
        ingest(w, s["at"], s["batch"])
    k = record(w, S1_AT, site="KOBO-001", revenue="500.00", fuel="780.00")
    assert k.state == "NOT_MATCHED" and k.opens is False and k.tolerance == D("0.01")
    assert heads(k) == {"revenue": ("NOT_MATCHED", None, "500.00", "505.50", "5.50", "5.0000"),
                        "fuel_cost": ("NOT_MATCHED", None, "780.00", "762.50", "-17.50", "7.8000")}
    assert w["store"].statement_rows[0].result_at_record == "NOT_MATCHED"
    for s in kobo_steps()[4:6]:  # E and F
        ingest(w, s["at"], s["batch"])
    after = only(w)
    assert after.state == "MATCHED" and after.opens is True
    assert heads(after) == {"revenue": ("MATCHED", None, "500.00", "495.50", "-4.50", "5.0000"),
                            "fuel_cost": ("MATCHED", None, "780.00", "775.00", "-5.00", "7.8000")}
    assert w["store"].statement_rows[0].result_at_record == "NOT_MATCHED"  # what was seen, never rewritten


def test_r1_the_same_statement_in_eur() -> None:
    w = kobo_world()
    for s in kobo_steps():
        ingest(w, s["at"], s["batch"])
    k = record(w, S1_AT, site="KOBO-001", revenue="500.00", fuel="780.00", currency="EUR")
    assert k.state == "NOT_COMPARABLE" and k.opens is False
    for h in k.headings:
        assert (h.state, h.reason, h.record_currencies, h.recorded) == ("NOT_COMPARABLE", "CURRENCY_MISMATCH",
                                                                        ("USD",), None)


# ---------------------------------------------------------------- R2: §6.2, T1, T2, T4, T5, T6 on one world


def test_r2_t1_t2_t4_t5_t6_in_order() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    # T1
    s1 = record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    assert w["store"].statement_rows[0].result_at_record == "MATCHED"
    assert w["store"].statement_rows[0].tolerance_at_record == "0.01"
    t1 = only(w)
    assert (t1.statement_id, t1.site_id, t1.site_code, t1.state, t1.opens) == (s1.statement_id, None, None,
                                                                               "MATCHED", True)
    assert heads(t1) == {"revenue": ("MATCHED", None, "755.00", "750.00", "-5.00", "7.5500"),
                         "fuel_cost": ("MATCHED", None, "505.00", "500.00", "-5.00", "5.0500")}
    for code in ("KOBO-001", "MTO-001"):
        st = standing(w, code)
        assert (st.reconciled, st.reason, st.tolerance) == (True, "RECONCILED", D("0.01"))
        assert st.this_month.statement_id == s1.statement_id and st.cited.statement_id == s1.statement_id
    # T2: the late fuel invoice
    load(w, "C")
    t2 = only(w)
    assert t2.state == "NOT_MATCHED" and t2.opens is False
    assert heads(t2)["fuel_cost"] == ("NOT_MATCHED", None, "505.00", "512.50", "7.50", "5.0500")
    for code in ("KOBO-001", "MTO-001"):
        st = standing(w, code)
        assert (st.reconciled, st.reason, st.cited) == (False, "THIS_MONTH_NOT_MATCHED", None)
        assert st.this_month.statement_id == s1.statement_id
    assert w["store"].statement_rows[0].result_at_record == "MATCHED"
    # T4: S2 supersedes S1
    s2 = record(w, S2_AT, site=None, revenue="755.00", fuel="510.00")
    t4 = only(w)
    assert t4.statement_id == s2.statement_id and t4.state == "MATCHED" and t4.opens is True
    assert heads(t4)["fuel_cost"] == ("MATCHED", None, "510.00", "512.50", "2.50", "5.1000")
    st = standing(w, "KOBO-001")
    assert (st.reconciled, st.reason, st.cited.statement_id) == (True, "RECONCILED", s2.statement_id)
    # T5: MTO-001, fuel stated as 0.00 with no fuel record
    s3 = record(w, S3_AT, site="MTO-001", revenue="250.00", fuel="0.00")
    assert (s3.state, s3.opens, s3.site_code, s3.site_id) == ("MATCHED", False, "MTO-001", w["sites"]["MTO-001"])
    assert heads(s3) == {"revenue": ("MATCHED", None, "250.00", "250.00", "0.00", "2.5000"),
                         "fuel_cost": ("MATCHED", "NONE_RECORDED_ZERO_STATED", "0.00", None, None, "0.0000")}
    # T6: S4 is current for MTO-001; fuel stated, none recorded
    s4 = record(w, S4_AT, site="MTO-001", revenue="250.00", fuel="40.00")
    assert (s4.state, s4.opens) == ("NOT_COMPARABLE", False)
    assert heads(s4)["fuel_cost"] == ("NOT_COMPARABLE", "NOT_RECEIVED", "40.00", None, None, "0.4000")
    assert [c.statement_id for c in w["recon"].statements(w["tid"])] == [s2.statement_id, s4.statement_id]
    st = standing(w, "MTO-001")
    assert (st.reconciled, st.reason, st.this_month.statement_id) == (False, "THIS_MONTH_NOT_COMPARABLE",
                                                                      s4.statement_id)
    st = standing(w, "KOBO-001")  # S2 still opens the gate for KOBO-001
    assert (st.reconciled, st.reason, st.cited.statement_id) == (True, "RECONCILED", s2.statement_id)


def t2_world(owner_root: Path | None = None) -> dict:
    w = two_sites_world(owner_root)
    load(w, "A", "B")
    s1 = record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    load(w, "C")
    return dict(w, s1=s1)


def test_r2_t3_a_wider_tolerance_set_by_the_owner(tmp_path) -> None:
    w = t2_world(tmp_path)
    path = owner_file(tmp_path, "Tolerance for lakeside-power: 2% of revenue and of fuel cost.\n")
    w["clock"].now = T3_SET_AT
    w["recon"].set_tolerance(w["tid"], "0.02", OWNER_REF)
    w["clock"].now = READ_AT
    (row,) = w["store"].tolerance_rows
    assert (row.tolerance, row.owner_ref, row.set_at) == ("0.02", OWNER_REF, T3_SET_AT)
    assert row.owner_ref_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert heads(only(w))["fuel_cost"] == ("MATCHED", None, "505.00", "512.50", "7.50", "10.1000")
    st = standing(w, "KOBO-001")
    assert (st.reconciled, st.reason, st.tolerance) == (True, "RECONCILED", D("0.02"))
    assert w["recon"].tolerance(w["tid"]) == D("0.02")
    assert w["store"].statement_rows[0].tolerance_at_record == "0.01"


def test_r2_t7_no_statement() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    st = standing(w, "KOBO-001")
    assert (st.reconciled, st.reason, st.this_month, st.cited, st.tolerance) == (False, "NO_STATEMENT", None,
                                                                                 None, DEFAULT_TOLERANCE)


def test_r2_t8_none_matched_for_an_uncovered_month() -> None:
    w = t2_world()
    st = standing(w, "KOBO-001", "2026-09")
    assert (st.reconciled, st.reason, st.this_month, st.cited) == (False, "NONE_MATCHED", None, None)


def test_r2_t9_an_open_month_is_refused_and_nothing_written() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    with pytest.raises(ReconRefused) as got:
        record(w, READ_AT, site=None, revenue="755.00", fuel="505.00", period="2026-11")
    assert (got.value.code, got.value.params) == ("RECON_MONTH_OPEN", {"period": "2026-11"})
    assert w["store"].statement_rows == []


def test_r2_t10_a_zero_stated_heading_never_opens_the_gate() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    s3 = record(w, S3_AT, site="MTO-001", revenue="250.00", fuel="0.00")
    assert (s3.state, s3.opens) == ("MATCHED", False)
    for code in ("KOBO-001", "MTO-001"):
        st = standing(w, code)
        assert (st.reconciled, st.reason, st.cited) == (False, "NONE_MATCHED", None)
    assert standing(w, "MTO-001").this_month.statement_id == s3.statement_id


# ---------------------------------------------------------------- R3: the boundary (pure)


@pytest.mark.parametrize("accounts, recorded, state", [
    ("505.00", "510.05", "MATCHED"), ("505.00", "510.06", "NOT_MATCHED"),
    ("505.00", "499.95", "MATCHED"), ("505.00", "499.94", "NOT_MATCHED"),
    ("0.00", "3.00", "NOT_MATCHED"),
    ("501.50", "506.52", "NOT_MATCHED"),  # allowed exactly 5.015, never quantised before comparing (V9)
    ("500.00", "500.004", "MATCHED"),
])
def test_r3_the_boundary(accounts, recorded, state) -> None:
    assert _compare(D(accounts), D(recorded), D("0.01")) == state


# ---------------------------------------------------------------- R4: refusals, one each, nothing written


@pytest.mark.parametrize("kw, code, params", [
    (dict(actor=ANA), "RECON_ROLE", {}),
    (dict(period="2026-13"), "RECON_PERIOD", {}),
    (dict(period="２026-10"), "RECON_PERIOD", {}),
    (dict(site="NOPE-001"), "RECON_SITE_UNKNOWN", {"site": "NOPE-001"}),
    (dict(site="COLD-THIKA"), "RECON_SITE_UNKNOWN", {"site": "COLD-THIKA"}),  # another tenant's Site
    (dict(currency="usd"), "RECON_CURRENCY", {}),
    (dict(revenue="755"), "RECON_AMOUNT", {"heading": "revenue"}),
    (dict(revenue="1,200.00"), "RECON_AMOUNT", {"heading": "revenue"}),
    (dict(fuel="05.00"), "RECON_AMOUNT", {"heading": "fuel_cost"}),
    (dict(source_ref=""), "RECON_SOURCE_REF", {}),
    (dict(source_ref="x" * 201), "RECON_SOURCE_REF", {}),
    (dict(source_ref=" padded"), "RECON_SOURCE_REF", {}),
    (dict(source_ref="line\nbreak"), "RECON_SOURCE_REF", {}),
    (dict(period="2026-11"), "RECON_MONTH_OPEN", {"period": "2026-11"}),
    (dict(site="FRZ-001"), "RECON_SITE_TYPE", {"site": "FRZ-001"}),
])
def test_r4_refusals(kw, code, params) -> None:
    w = two_sites_world()
    load(w, "A", "B")
    before = w["store"].counts()
    args = dict(site=None, revenue="755.00", fuel="505.00")
    args.update(kw)
    with pytest.raises(ReconRefused) as got:
        record(w, READ_AT, **args)
    assert (got.value.code, got.value.params) == (code, params)
    assert w["store"].statement_rows == [] and w["store"].counts() == before


def test_r4_an_organisation_with_no_mini_grid_site_is_unknown() -> None:
    store = ReconMemoryStore()
    tid = store.add_tenant("harvest-cold")
    w = _services(store, {"COLD-THIKA": store.add_site(tid, "COLD-THIKA", "COLDCHAIN")}, tid, None)
    with pytest.raises(ReconRefused) as got:
        record(w, READ_AT, site=None, revenue="0.00", fuel="0.00")
    assert got.value.code == "RECON_SITE_UNKNOWN" and store.statement_rows == []


# ---------------------------------------------------------------- R5: latest wins, ties by id text


LOW = UUID("3a700000-0000-4000-8000-000000000001")
HIGH = UUID("3a700000-0000-4000-8000-000000000002")


def row(w, sid: UUID, *, fuel: str, site_id: UUID | None = None, at: datetime = S1_AT) -> StatementRow:
    return StatementRow(id=sid, tenant_id=w["tid"], site_id=site_id, period="2026-10", currency=USD,
                        revenue="755.00", fuel_cost=fuel, source_ref="Management accounts", recorded_at=at,
                        recorded_by=FIONA.person_id, recorded_role=FINANCE, recorded_by_script=True,
                        result_at_record="NOT_COMPARABLE", tolerance_at_record="0.01")


def test_r5_equal_recorded_at_resolves_by_id_text() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    w["store"].statement_rows.extend([row(w, HIGH, fuel="505.00"), row(w, LOW, fuel="600.00")])  # HIGH first
    w["store"].accounts_statements = lambda tid: tuple(w["store"].statement_rows)  # insertion order, not sorted
    (current,) = w["recon"].statements(w["tid"])
    assert (current.statement_id, current.state) == (HIGH, "MATCHED")
    assert standing(w, "KOBO-001").reason == "RECONCILED"
    w["store"].statement_rows.reverse()
    (current,) = w["recon"].statements(w["tid"])
    assert current.statement_id == HIGH


def test_r5_a_later_recorded_at_wins_over_a_higher_id() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    later = datetime(2026, 11, 6, tzinfo=timezone.utc)
    w["store"].statement_rows.extend([row(w, HIGH, fuel="505.00"), row(w, LOW, fuel="600.00", at=later)])
    (current,) = w["recon"].statements(w["tid"])
    assert (current.statement_id, current.state) == (LOW, "NOT_MATCHED")


# ---------------------------------------------------------------- R7: the same definition as the screen (4b)


def test_r7_the_recorded_figures_are_the_screens() -> None:
    from assetops_backend.structure.money import CommercialLeafSource
    from test_4b_money_leaves import fallback

    w = two_sites_world()
    load(w, "A", "B", "C")
    leaves = CommercialLeafSource(w["months"], w["store"], fallback())

    def stated(code: str, factor: str):
        site = SiteRef(w["tid"], w["sites"][code], code, "MINIGRID", "Africa/Nairobi")
        return leaves.stated(ReadContext(site, "2026-10", None), factor).value

    def mine(code: str) -> dict:
        check = w["recon"].check(w["tid"], row(w, uuid4(), fuel="1.00", site_id=w["sites"][code]))
        return {h.heading: h for h in check.headings}

    kobo, mto = mine("KOBO-001"), mine("MTO-001")
    assert (stated("KOBO-001", "revenue"), stated("KOBO-001", "fuel_cost")) == (D("500.00"), D("512.50"))
    assert (kobo["revenue"].recorded, kobo["fuel_cost"].recorded) == (D("500.00"), D("512.50"))
    assert stated("MTO-001", "revenue") == mto["revenue"].recorded == D("250.00")
    assert stated("MTO-001", "fuel_cost") is None and mto["fuel_cost"].reason == "NOT_RECEIVED"
    assert kobo["revenue"].sources == ("commercial:kobo-vending",)
    assert kobo["fuel_cost"].sources == ("commercial:lakeside-accounts",)
    assert kobo["fuel_cost"].origins == ("source-emulated",)


# ---------------------------------------------------------------- R8: reads per standing


def counted(w, code: str, period: str = "2026-10") -> tuple[dict, list]:
    store, months = w["store"], w["months"]
    store.reads = {k: 0 for k in store.reads}
    months.calls.clear()
    standing(w, code, period)
    return dict(store.reads), [(c[0], c[1]) for c in months.calls]


def test_r8_reads_per_standing() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    load(w, "C")
    record(w, S2_AT, site=None, revenue="755.00", fuel="510.00")  # T4's state
    kobo, mto = w["sites"]["KOBO-001"], w["sites"]["MTO-001"]
    reads, calls = counted(w, "KOBO-001")
    assert reads == {"accounts_statements": 1, "tolerances": 1, "site_rows": 1}
    assert sorted(calls, key=str) == sorted([(kobo, "2026-10"), (mto, "2026-10")], key=str)
    record(w, S3_AT, site="MTO-001", revenue="250.00", fuel="0.00")
    record(w, S4_AT, site="MTO-001", revenue="250.00", fuel="40.00")  # T6's state
    reads, calls = counted(w, "MTO-001")
    assert reads == {"accounts_statements": 1, "tolerances": 1, "site_rows": 1} and len(calls) == 2
    # two consecutive standings read the months afresh
    w["months"].calls.clear()
    standing(w, "KOBO-001")
    standing(w, "KOBO-001")
    assert len(w["months"].calls) == 4


def test_r8_the_gate_walk_stops_at_the_first_opener_and_t8_reads_two() -> None:
    w = t2_world()
    reads, calls = counted(w, "KOBO-001", "2026-09")
    assert reads == {"accounts_statements": 1, "tolerances": 1, "site_rows": 1} and len(calls) == 2
    # The October organisation statement opens and comes first in cited order (period descending): the walk stops
    # there, so KOBO-001's September statement is never checked (its month never read).
    w2 = two_sites_world()
    load(w2, "A", "B")
    record(w2, S1_AT, site=None, revenue="755.00", fuel="505.00")
    record(w2, S2_AT, site="KOBO-001", revenue="0.00", fuel="0.00", period="2026-09")
    _reads, calls = counted(w2, "KOBO-001", "2026-08")
    assert [c[1] for c in calls] == ["2026-10", "2026-10"]


# ---------------------------------------------------------------- R9: the instant (D-3A7.9)


def test_r9_the_standing_at_an_instant(tmp_path) -> None:
    w = t2_world(tmp_path)
    at = datetime(2026, 11, 6, tzinfo=timezone.utc)
    st = standing(w, "KOBO-001", known_at=at)
    assert (st.reconciled, st.reason, st.known_at) == (True, "RECONCILED", at)
    assert heads(st.cited)["fuel_cost"] == ("MATCHED", None, "505.00", "500.00", "-5.00", "5.0500")
    assert all(c[2] == at for c in w["months"].calls[-2:])
    st = standing(w, "KOBO-001")
    assert (st.reconciled, st.reason, st.known_at) == (False, "THIS_MONTH_NOT_MATCHED", None)
    assert all(c[2] is None for c in w["months"].calls[-2:])  # live stays live
    st = standing(w, "KOBO-001", known_at=datetime(2026, 11, 4, tzinfo=timezone.utc))
    assert (st.reconciled, st.reason) == (False, "NO_STATEMENT")
    owner_file(tmp_path, "lakeside-power 2%\n")
    w["clock"].now = T3_SET_AT
    w["recon"].set_tolerance(w["tid"], "0.02", OWNER_REF)
    w["clock"].now = READ_AT
    before = datetime(2026, 11, 14, tzinfo=timezone.utc)
    st = standing(w, "KOBO-001", known_at=before)
    assert (st.reconciled, st.reason, st.tolerance) == (False, "THIS_MONTH_NOT_MATCHED", D("0.01"))
    assert w["recon"].tolerance(w["tid"], known_at=before) == D("0.01")
    assert standing(w, "KOBO-001").reason == "RECONCILED"


def test_r9_a_month_open_at_the_instant_is_not_comparable() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    w["store"].statement_rows.append(row(w, LOW, fuel="505.00", at=datetime(2026, 10, 31, 12, tzinfo=timezone.utc)))
    check = w["recon"].check(w["tid"], w["store"].statement_rows[0],
                             known_at=datetime(2026, 10, 31, 20, tzinfo=timezone.utc))  # 23:00 in Nairobi
    assert check.state == "NOT_COMPARABLE" and {h.reason for h in check.headings} == {"MONTH_OPEN"}


# ---------------------------------------------------------------- R10: scope (D-3A7.11)


def test_r10_the_organisation_is_its_mini_grid_sites() -> None:
    w = two_sites_world()
    load(w, "A", "B")
    record(w, S1_AT, site=None, revenue="755.00", fuel="505.00")
    t1 = only(w)
    standing(w, "KOBO-001")
    standing(w, "MTO-001")
    assert heads(t1)["revenue"][3] == "750.00"
    assert w["sites"]["FRZ-001"] not in {c[0] for c in w["months"].calls}
    assert {c[0] for c in w["months"].calls} == {w["sites"]["KOBO-001"], w["sites"]["MTO-001"]}


# ---------------------------------------------------------------- the tolerance (§2.4), service side


@pytest.mark.parametrize("tolerance, text, code", [
    ("0.06", "lakeside-power 6%", "TOLERANCE_INVALID"),
    ("0.0000", "lakeside-power 0.0000", "TOLERANCE_INVALID"),
    ("0.00001", "lakeside-power 0.00001", "TOLERANCE_INVALID"),
    ("abc", "lakeside-power abc", "TOLERANCE_INVALID"),
    ("0.02", "2% for every operator", "OWNER_REF_INVALID"),  # no slug
    ("0.02", "lakeside-power 3%", "OWNER_REF_INVALID"),  # another figure
    ("0.02", "lakeside-power 12%", "OWNER_REF_INVALID"),  # 12% does not cite 2%
    ("0.02", "lakeside-power 0.025", "OWNER_REF_INVALID"),  # 0.025 does not cite 0.02
    ("0.02", "lakeside-power 0.2%", "OWNER_REF_INVALID"),  # 0.2% does not cite 2% (preceded by '.')
    ("0.02", "north-lakeside-power 0.02", "OWNER_REF_INVALID"),  # review L2: a longer slug does not cite ours
    ("0.02", "north-lakeside-power 0.02", "OWNER_REF_INVALID"),  # review L2: a longer slug does not cite ours
    ("0.02", "lakeside-power: 0.02", None),
    ("0.005", "lakeside-power 0.5%", None),
])
def test_set_tolerance_cites_an_owner_file(tmp_path, tolerance, text, code) -> None:
    w = two_sites_world(tmp_path)
    owner_file(tmp_path, text)
    if code is None:
        w["recon"].set_tolerance(w["tid"], tolerance, OWNER_REF)
        assert w["recon"].tolerance(w["tid"]) == D(tolerance)
        return
    with pytest.raises(ReconRefused) as got:
        w["recon"].set_tolerance(w["tid"], tolerance, OWNER_REF)
    assert got.value.code == code and w["store"].tolerance_rows == []


@pytest.mark.parametrize("ref", ["owner/nope.md", "owner/owner-absent.md", "../owner/owner-tol-2026-11-20.md",
                                 "owner/owner-Tol.md"])
def test_set_tolerance_refuses_a_missing_or_malformed_ref(tmp_path, ref) -> None:
    w = two_sites_world(tmp_path)
    owner_file(tmp_path, "lakeside-power 2%")
    with pytest.raises(ReconRefused) as got:
        w["recon"].set_tolerance(w["tid"], "0.02", ref)
    assert got.value.code == "OWNER_REF_INVALID" and w["store"].tolerance_rows == []


def test_no_owner_reader_no_tolerance() -> None:
    w = two_sites_world(None)
    with pytest.raises(ReconRefused) as got:
        w["recon"].set_tolerance(w["tid"], "0.02", OWNER_REF)
    assert got.value.code == "OWNER_REF_INVALID" and w["recon"].tolerance(w["tid"]) == D("0.01")


def test_no_float_in_the_reconciliation_module() -> None:
    source = (TREE / "backend" / "assetops_backend" / "structure" / "reconciliation.py").read_text("utf-8")
    assert "float" not in source
