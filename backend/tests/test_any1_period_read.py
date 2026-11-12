"""ANY-1 AR-1 (architect answer 2026-11-10 §4): the stored read-period foundation on fakes (no database).

Register kinds, the row contract (D-I18N.1, D-MONEY.1-4), the generic builder's revision rules, the one-statement
reader with PENDING-at-k from the outbox/consumption ledgers, the drain routing, the backfill CLI and the 0059
migration text. The Postgres round-trip and migration up/down run in phase 2 on a `*_test` database.
"""
from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass, field, fields
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from assetops_backend.chain.drain import DirtyRow, drain
from assetops_backend.chain.events import Event, RegisterError, parse_register, resolve
from assetops_backend.chain.period_read import (
    PeriodContractError,
    PeriodFragment,
    PeriodReadBuilder,
    PeriodReader,
    money_amount,
    money_line,
    period_fp,
    served_kinds,
    validate_body,
)
from assetops_backend.chain.ports import PeriodRow, SiteRef

ROOT = Path(__file__).resolve().parents[2]
T = UUID("00000000-0000-0000-0000-0000000000a1")
KOBO = SiteRef(T, UUID("00000000-0000-0000-0000-0000000000b1"), "KOBO-001", "MINIGRID", "Africa/Nairobi")
COLD = SiteRef(T, UUID("00000000-0000-0000-0000-0000000000b2"), "COLD-LAB-001", "COLDCHAIN", "Africa/Nairobi")
KIND = "mini_depth.renewable"
MONEY = "money.lines"
D = date(2026, 10, 21)
UTC = timezone.utc


def _register(kinds=None):
    return parse_register({
        "register_version": 1,
        "events": {
            "reading.accepted@1": {"days": "span_local", "measures": "by_role"},
            "assessment.revised@1": {"days": "windows_local", "measures": "by_analytic"},
            "price.revised@1": {"days": "valid_local", "measures": "by_assumption_key"},
            "foundation.revised@1": {"days": "from_valid_local_to_today", "measures": "all_of_site"},
            "finding.revised@1": {"days": "none", "consumer": "threads"},
        },
        "inputs": {"productive_kwh": {"roles": ["feeder_demand"]}},
        "kinds": kinds if kinds is not None else {
            KIND: {"grain": "hour", "site_types": ["MINIGRID"],
                   "inputs": {"roles": ["pv_available_power"], "mini_depth": ["renewable"]}},
            MONEY: {"grain": "local_day", "site_types": ["MINIGRID", "EV_CHARGING"],
                    "inputs": {"assumption_keys": ["productive_use_price_per_kwh"]}},
        },
    })


def _event(type_="reading.accepted", subject=None, recorded=None, site=KOBO):
    return Event(uuid4(), type_, 1, datetime(2026, 10, 21, 6, tzinfo=UTC), recorded or datetime(2026, 10, 21, 7,
                                                                                                    tzinfo=UTC),
                 "accepted_evidence", T, site.site_id,
                 subject if subject is not None else {"roles": ["pv_available_power"],
                                                      "span": ["2026-10-21T06:00:00Z", "2026-10-21T07:00:00Z"]})


# --- register ------------------------------------------------------------------------------------------------------


def test_register_accepts_kinds_and_the_live_register_parses() -> None:
    reg = _register()
    assert reg.kinds_for("MINIGRID") == [KIND, MONEY]
    assert reg.kinds_for("COLDCHAIN") == []
    assert reg.kinds[KIND].grain == "hour"
    from assetops_backend.chain.adapters.file_chain_config import load_event_register

    live = load_event_register()
    assert sorted(live.kinds) == ["dispatch.day", "evidence.claim", "mini_depth.backup", "mini_depth.fuel",
                                  "mini_depth.renewable", "mini_depth.service"]  # AR-2/3/4 kinds
    assert live.kinds["dispatch.day"].grain == "s3_day"
    assert live.kinds["mini_depth.renewable"].grain == "local_day" and live.kinds["mini_depth.fuel"].grain == "hour"
    assert live.kinds["evidence.claim"].grain == "s3_day"
    assert "productive_kwh" in live.inputs


@pytest.mark.parametrize("kinds, message", [
    ({"Mini.Depth": {"grain": "hour", "site_types": ["MINIGRID"], "inputs": {"roles": ["x"]}}}, "<area>.<name>"),
    ({"mini_depth": {"grain": "hour", "site_types": ["MINIGRID"], "inputs": {"roles": ["x"]}}}, "<area>.<name>"),
    ({KIND: {"grain": "week", "site_types": ["MINIGRID"], "inputs": {"roles": ["x"]}}}, "grain"),
    ({KIND: {"grain": "hour", "site_types": ["BOAT"], "inputs": {"roles": ["x"]}}}, "site_types"),
    ({KIND: {"grain": "hour", "site_types": ["MINIGRID"], "inputs": {}}}, "inputs"),
    ({KIND: {"grain": "hour", "site_types": ["MINIGRID"], "inputs": {"colour": ["x"]}}}, "keys must be among"),
    ({KIND: {"grain": "hour", "site_types": ["MINIGRID"], "inputs": {"roles": ["x"]}, "extra": 1}}, "keys"),
])
def test_register_refuses_a_mis_declared_kind(kinds, message) -> None:
    with pytest.raises(RegisterError, match=message):
        _register(kinds)


def test_resolve_dirties_kinds_like_measures() -> None:
    reg = _register()
    marks = resolve(reg, _event(), site_type="MINIGRID", tz=KOBO.timezone, today=D)
    assert (D, KIND) in marks and (D, MONEY) not in marks
    assert resolve(reg, _event(), site_type="COLDCHAIN", tz=COLD.timezone, today=D) == []
    price = _event("price.revised", {"key": "productive_use_price_per_kwh",
                                     "valid": ["2026-10-20T00:00:00Z", "2026-10-21T00:00:00Z"]})
    assert {k for _, k in resolve(reg, price, site_type="MINIGRID", tz=KOBO.timezone, today=D)} == {MONEY}
    found = _event("foundation.revised", {"valid_from": "2026-10-20T00:00:00Z"})
    got = resolve(reg, found, site_type="MINIGRID", tz=KOBO.timezone, today=D)
    assert {k for _, k in got} >= {KIND, MONEY} and {d for d, _ in got} == {date(2026, 10, 20), D}


# --- the row contract ----------------------------------------------------------------------------------------------


def _line(**kw):
    base = dict(qty="12.345", unit="kWh", rate="0.25", rate_unit="USD/kWh", rate_ref="rev-1", currency="USD",
                basis="DECLARED_PRICE")
    base.update(kw)
    return money_line(**base)


def test_money_amount_rounds_the_unrounded_product_half_up() -> None:
    assert money_amount("0.125", "1") == "0.13"
    assert money_amount("12.345", "0.25") == "3.09"  # 3.08625
    assert money_amount("2.5", "0.01") == "0.03"     # 0.025 half-up, not banker's 0.02
    assert _line()["amount"] == "3.09" and _line()["receipt"]["segments"] is None


def test_contract_accepts_messages_and_receipted_money() -> None:
    validate_body(KIND, {"cards": [{"label": {"key": "mini.renewable.title", "params": {"kwh": 3}}}],
                         "value": 1.5, "label": None})
    validate_body(MONEY, {"lines": [_line(), _line(low="1.00", high="2.00")]})


@pytest.mark.parametrize("kind, body, message", [
    (KIND, {"label": "Renewable share"}, "D-I18N.1"),
    (KIND, {"cards": [{"title": {"key": "x"}}]}, "D-I18N.1"),
    (KIND, {"total": 3}, "D-MONEY.3"),
    (MONEY, {"lines": [{**_line(), "amount": "9.99"}]}, "reproduce"),
    (MONEY, {"lines": [{**_line(), "currency": "usd"}]}, "ISO 4217"),
    (MONEY, {"lines": [{**_line(), "converted": "1.00"}]}, "unknown money line keys"),
    (MONEY, {"lines": [{**_line(), "receipt": {**_line()["receipt"], "fx": {"rate": "1"}}}]}, "fx"),
    (MONEY, {"lines": [{k: v for k, v in _line().items() if k != "receipt"}]}, "receipt"),
    (MONEY, {"lines": [{**_line(), "low": "1.00", "high": "2.00"}]}, "not both"),
    (MONEY, {"per_site": []}, "lines"),
])
def test_contract_refuses(kind, body, message) -> None:
    with pytest.raises(PeriodContractError, match=message):
        validate_body(kind, body)


def test_fingerprint_folds_in_every_rate_ref() -> None:
    a = period_fp(MONEY, "v1", {"ids": [1]}, {"lines": [_line()]})
    b = period_fp(MONEY, "v1", {"ids": [1]}, {"lines": [_line(rate_ref="rev-2")]})
    c = period_fp(MONEY, "v2", {"ids": [1]}, {"lines": [_line()]})
    assert len({a, b, c}) == 3 and len(a) == 64


# --- fakes ---------------------------------------------------------------------------------------------------------


@dataclass
class FakeStore:
    clock: list = field(default_factory=lambda: [datetime(2026, 10, 21, 8, tzinfo=UTC)])
    rows: list = field(default_factory=list)
    prov: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    consumed: dict = field(default_factory=dict)
    dirty: list = field(default_factory=list)
    calls: list = field(default_factory=list)

    def tick(self, minutes=1):
        self.clock[0] += timedelta(minutes=minutes)

    def latest(self, key):
        mine = [r for r in self.rows if (r.tenant_id, r.site_id, r.kind, r.period_start) ==
                (key.tenant_id, key.site_id, key.kind, key.period_start)]
        if not mine:
            return None
        r = max(mine, key=lambda r: r.revision)
        return r.revision, r.input_fp, r.builder_version

    def append(self, row):
        self.rows.append(PeriodRow(**{**{f.name: getattr(row, f.name) for f in fields(row)},
                                      "computed_at": self.clock[0]}))

    def read_latest(self, tenant_id, site_ids, kinds, from_day, to_day, known_at):
        self.calls.append("read_latest")
        best = {}
        for r in self.rows:
            if (r.tenant_id != tenant_id or r.site_id not in site_ids or r.kind not in kinds
                    or not from_day <= r.local_day <= to_day or (known_at and r.computed_at > known_at)):
                continue
            k = (r.site_id, r.kind, r.period_start)
            if k not in best or best[k].revision < r.revision:
                best[k] = r
        return list(best.values())

    def provenance(self, tenant_id, ids, version):
        return {i: self.prov[(i, version)] for i in ids if (i, version) in self.prov}

    def append_provenance(self, block):
        key = (block.assessment_revision_id, block.builder_version)
        if key in self.prov:
            return False
        self.prov[key] = block.block
        return True

    def unconsumed_at(self, tenant_id, site_ids, types, known_at):
        self.calls.append("unconsumed_at")
        k = known_at or self.clock[0]
        return [e for e in self.events if e.site_id in site_ids and e.key in types and e.recorded_at <= k
                and not (e.event_id in self.consumed and self.consumed[e.event_id] <= k)]

    def dirty_marks(self, tenant_id, site_ids, kinds, lo, hi):
        self.calls.append("dirty_marks")
        return [d for d in self.dirty if d[0] in site_ids and d[2] in kinds and lo <= d[1] <= hi]


class HourKind:
    kind = KIND

    def __init__(self, version="v1"):
        self.builder_version = version
        self.inputs = {"ids": ["r1"]}
        self.state = "CURRENT"
        self.provenance = {}

    def fragments(self, ctx, site):
        lo = ctx.period_start_utc
        return [PeriodFragment(lo + timedelta(hours=h), lo + timedelta(hours=h + 1), self.state,
                               {"hour": h, "label": {"key": "mini.hour", "params": {"h": h}}}, self.inputs,
                               self.provenance) for h in (6, 7)]


# --- builder -------------------------------------------------------------------------------------------------------


def test_builder_appends_only_on_a_changed_fingerprint_or_builder_version() -> None:
    store, kind = FakeStore(), HourKind()
    b = PeriodReadBuilder(store, {KIND: kind})
    first = b.build(T, KOBO, D, KIND)
    assert [w.written for w in first] == [True, True] and {w.row.revision for w in first} == {1}
    # the Site-local day starts at 21:00 UTC the day before (EAT = UTC+3); hour 6 of it is 03:00 UTC
    assert first[0].row.period_start == datetime(2026, 10, 21, 3, tzinfo=UTC)
    assert [w.written for w in b.build(T, KOBO, D, KIND)] == [False, False]
    kind.inputs = {"ids": ["r1", "r2"]}  # a late reading
    assert {w.row.revision for w in b.build(T, KOBO, D, KIND) if w.written} == {2}
    b2 = PeriodReadBuilder(store, {KIND: HourKind("v2")})
    b2._builders[KIND].inputs = kind.inputs
    assert {w.row.revision for w in b2.build(T, KOBO, D, KIND) if w.written} == {3}
    assert len(store.rows) == 6  # append-only: every revision kept


def test_builder_refuses_a_contract_breach_and_stores_provenance_once() -> None:
    store, kind = FakeStore(), HourKind()
    rid = uuid4()
    kind.provenance = {rid: {"classes": {"MEASURED": 3}}}
    b = PeriodReadBuilder(store, {KIND: kind})
    b.build(T, KOBO, D, KIND)
    assert list(store.prov) == [(rid, "v1")]
    kind.state = "current"
    with pytest.raises(PeriodContractError, match="upper-case"):
        b.build(T, KOBO, D, KIND)
    with pytest.raises(PeriodContractError, match="mis-declared"):
        PeriodReadBuilder(store, {"mini_depth.fuel": kind})


# --- reader --------------------------------------------------------------------------------------------------------


def _built():
    store, kind = FakeStore(), HourKind()
    b = PeriodReadBuilder(store, {KIND: kind})
    b.build(T, KOBO, D, KIND)
    return store, kind, b


def test_reader_reads_latest_as_known_at_k_in_one_row_statement() -> None:
    store, kind, b = _built()
    k1 = store.clock[0]
    store.tick(10)
    kind.inputs = {"ids": ["r1", "r2"]}
    b.build(T, KOBO, D, KIND)
    reader = PeriodReader(store, _register(), b.versions(), now=lambda: store.clock[0])
    live = reader.read(T, [KOBO, COLD], [KIND], D, D)
    assert [r.row.revision for r in live.rows] == [2, 2] and not live.pending
    assert store.calls.count("read_latest") == 1 and live.statements == 3
    hist = reader.read(T, [KOBO], [KIND], D, D, known_at=k1)
    assert [r.row.revision for r in hist.rows] == [1, 1] and hist.statements == 2
    assert reader.read(T, [KOBO], [KIND], D, D, known_at=k1 - timedelta(minutes=1)).rows == []


def test_pending_at_k_from_the_outbox_and_consumption_ledgers() -> None:
    store, kind, b = _built()
    reader = PeriodReader(store, _register(), b.versions(), now=lambda: store.clock[0])
    late = _event(recorded=datetime(2026, 10, 21, 9, tzinfo=UTC))
    store.events.append(late)
    before = datetime(2026, 10, 21, 8, 30, tzinfo=UTC)
    after = datetime(2026, 10, 21, 9, 30, tzinfo=UTC)
    assert not reader.read(T, [KOBO], [KIND], D, D, known_at=before).pending  # not yet recorded at k
    got = reader.read(T, [KOBO], [KIND], D, D, known_at=after)
    assert got.pending == {(KOBO.site_id, D, KIND): ("event",)}
    assert all(r.pending == ("event",) for r in got.rows)
    store.consumed[late.event_id] = datetime(2026, 10, 21, 10, tzinfo=UTC)
    assert reader.read(T, [KOBO], [KIND], D, D, known_at=after).pending  # consumed only after k
    assert not reader.read(T, [KOBO], [KIND], D, D, known_at=datetime(2026, 10, 21, 10, 1,
                                                                        tzinfo=UTC)).pending
    other = _event(subject={"roles": ["feeder_demand"], "span": ["2026-10-21T06:00:00Z", "2026-10-21T07:00Z"]},
                   recorded=datetime(2026, 10, 21, 9, tzinfo=UTC))
    store.events = [other]
    assert not reader.read(T, [KOBO], [KIND], D, D, known_at=after).pending  # dirties a measure, not this kind


def test_pending_live_dirty_marks_and_old_builder_versions() -> None:
    store, kind, b = _built()
    store.dirty.append((KOBO.site_id, D, KIND))
    reader = PeriodReader(store, _register(), b.versions(), now=lambda: store.clock[0])
    assert reader.read(T, [KOBO], [KIND], D, D).pending == {(KOBO.site_id, D, KIND): ("dirty",)}
    assert not reader.read(T, [KOBO], [KIND], D, D, known_at=store.clock[0]).pending  # the queue has no history
    store.dirty.clear()
    newer = PeriodReader(store, _register(), {KIND: "v2"}, now=lambda: store.clock[0])
    got = newer.read(T, [KOBO], [KIND], D, D)
    assert got.pending == {(KOBO.site_id, D, KIND): ("builder_version",)}
    assert all(r.pending == ("builder_version",) for r in got.rows)


def test_absent_rows_are_reported_rendered_no_data_and_logged_live(caplog) -> None:
    from assetops_backend.chain.period_read import ABSENT_LOG_EVENT, NO_ROW_STATE, absent_count

    store, kind, b = _built()
    reader = PeriodReader(store, _register(), b.versions(), now=lambda: store.clock[0])
    before = absent_count()
    with caplog.at_level("WARNING", logger="assetops.chain.period_read"):
        live = reader.read(T, [KOBO, COLD], [KIND], D, D + timedelta(days=1))
    assert live.absent == tuple(sorted([(COLD.site_id, D, KIND), (COLD.site_id, D + timedelta(days=1), KIND),
                                        (KOBO.site_id, D + timedelta(days=1), KIND)],
                                       key=lambda a: (str(a[0]), a[1], a[2])))
    assert live.day_state(KOBO.site_id, D, KIND) is None
    assert live.day_state(COLD.site_id, D, KIND) == NO_ROW_STATE == "NO_DATA"
    assert absent_count() == before + 3 and [r.message for r in caplog.records] == [ABSENT_LOG_EVENT]
    caplog.clear()
    k = store.clock[0] - timedelta(minutes=1)  # nothing known yet at k: absent, not logged (historical)
    hist = reader.read(T, [KOBO], [KIND], D, D, known_at=k)
    assert hist.rows == [] and hist.absent == ((KOBO.site_id, D, KIND),) and not caplog.records
    assert absent_count() == before + 3
    store.dirty.append((COLD.site_id, D, KIND))  # a missing period on a pending day renders PENDING
    assert reader.read(T, [COLD], [KIND], D, D).day_state(COLD.site_id, D, KIND) == "PENDING"


def test_served_kinds_switch(monkeypatch) -> None:
    monkeypatch.delenv("ASSETOPS_PERIOD_READ_KINDS", raising=False)
    assert served_kinds() == frozenset()
    monkeypatch.setenv("ASSETOPS_PERIOD_READ_KINDS", f" {KIND},, {MONEY} ")
    assert served_kinds() == {KIND, MONEY}


# --- drain ---------------------------------------------------------------------------------------------------------


class Queue:
    def __init__(self, rows):
        self.rows, self.done_rows = rows, []

    def pop(self, t, s, limit):
        return self.rows[:limit]

    def queued(self, t, s):
        return 0

    def done(self, t, s, row):
        self.done_rows.append(row)
        return True


def test_drain_routes_kind_rows_to_the_period_builder() -> None:
    store, kind = FakeStore(), HourKind()
    pb = PeriodReadBuilder(store, {KIND: kind})
    snap = SimpleNamespace(build=lambda *a, **k: (_ for _ in ()).throw(AssertionError("snapshot builder called")))
    at = datetime(2026, 10, 21, tzinfo=UTC)
    q = Queue([DirtyRow(D, KIND, at), DirtyRow(D, "money.unknown", at)])
    report = drain(q, snap, T, KOBO, 10, period_builder=pb)
    assert report.written == 2 and report.processed == 2 and len(q.done_rows) == 2
    assert report.by_measure == {KIND: 2}
    q2 = Queue([DirtyRow(D, KIND, at)])
    assert drain(q2, snap, T, KOBO, 10).written == 0  # without a period builder the row is dropped, as before


# --- backfill CLI --------------------------------------------------------------------------------------------------


def _services(store, builder):
    inputs = SimpleNamespace(tenant_id=lambda slug: T, site=lambda t, code: KOBO if code == "KOBO-001" else None,
                             first_evidence_time=lambda t, s: datetime(2026, 10, 20, 5, tzinfo=UTC))
    disposed = []
    return SimpleNamespace(inputs=inputs, period_builder=builder, periods=store,
                           dispose=lambda: disposed.append(1)), disposed


def test_backfill_build_stale_only_and_show(capsys) -> None:
    from assetops_backend.chain.period_backfill import main

    store = FakeStore()
    services, disposed = _services(store, PeriodReadBuilder(store, {KIND: HourKind()}))
    assert main(["build", "--site", "KOBO-001", "--from", "2026-10-20", "--to", "2026-10-21"], services=services,
                register=_register()) == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["written"] == 4 and summary["kinds"] == [KIND] and disposed == [1]
    services, _ = _services(store, PeriodReadBuilder(store, {KIND: HourKind("v2")}))
    assert main(["show", "--site", "KOBO-001", "--from", "2026-10-21", "--to", "2026-10-21"], services=services,
                register=_register()) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert json.loads(out[0])["pending"] == ["builder_version"]
    assert main(["build", "--site", "KOBO-001", "--from", "2026-10-21", "--to", "2026-10-21", "--stale-only"],
                services=services, register=_register()) == 0
    summary = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert summary["written"] == 2 and summary["stale_only"] is True
    assert main(["build", "--site", "KOBO-001", "--kind", "dispatch.day"], services=services,
                register=_register()) == 2
    assert main(["build", "--site", "NOPE"], services=services, register=_register()) == 2
    assert main(["build", "--site", "KOBO-001", "--tenant", "other"], services=services) == 2


# --- the migration -------------------------------------------------------------------------------------------------


def _migration():
    path = ROOT / "backend" / "migrations" / "versions" / "0059_site_period_read.py"
    spec = importlib.util.spec_from_file_location("m0059", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_0059_is_the_next_append_only_revision() -> None:
    m = _migration()
    assert m.revision == "0059_site_period_read" and m.down_revision == "0058_fuel_watermark_inputs"
    heads = [p.name for p in (ROOT / "backend" / "migrations" / "versions").glob("0059_*.py")]
    assert heads == ["0059_site_period_read.py"]
    for table in m.TABLES:
        assert f"BEFORE UPDATE OR DELETE ON {table}" in m.UPGRADE
        assert f"DROP TABLE {table};" in m.DOWNGRADE
    for col in ("tenant_id", "site_id", "kind", "period_start", "period_end", "local_day", "revision",
                "builder_version", "input_fp", "state", "body", "computed_at"):
        assert f"\n    {col} " in m.UPGRADE, col
    assert {f.name for f in fields(PeriodRow)} == {"tenant_id", "site_id", "kind", "period_start", "period_end",
                                                   "local_day", "revision", "builder_version", "input_fp", "state",
                                                   "body", "computed_at"}
    assert "PRIMARY KEY (tenant_id, site_id, kind, period_start, revision)" in m.UPGRADE
    assert "RAISE EXCEPTION" in m.REFUSE_IF_USED
