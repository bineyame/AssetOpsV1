"""3B4 (`specs/3B4-observer/` spec §6 F3, §7 tests 10 to 15): the structure observer over real Postgres.

One tenant, the MINIGRID Site `KOBO-001` (Africa/Nairobi) and `OTHER-001`; a fake `SnapshotRead` serving F1's Kobo
sides as `SiteMonthSnapshot`s and a fake `StructureSnapshotStore` whose `get` answers a known `payload_sha256` per
snapshot id (the portfolio row's differs); the real Finding and assessment stores; one FINANCE person, one
SITE_MANAGER bound to `KOBO-001` and one bound to `OTHER-001`. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test`
database.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType, SimpleNamespace
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MIGRATION, PREVIOUS = "0068_structure_finding", "0067_source_profile"
REFUSED = "0068 downgrade requires no structure Findings or tolerance declarations"
UTC = timezone.utc
OCT, NOV = "2026-10", "2026-11"
SLUG = "lakeside"
PW = "correct horse battery"
FIN, SM = "FINANCE_AND_COMMERCIAL_LEAD", "SITE_MANAGER"
SUBJECT_ARM = ("((domain = 'structure'::text) AND (subject_asset_id IS NULL) AND (generator_asset_id IS NULL))")
MINUTES_ARM = ("((domain = 'structure'::text) AND (candidate_minutes IS NULL) AND (necessary_minutes IS NULL) "
               "AND (indeterminate_minutes IS NULL))")
#: Spec §4.3 (D-3B4.18): the claim's 25 keys, a literal.
CLAIM_KEYS = {"format", "structure_key", "structure_version", "factor_id", "home", "objective", "kind", "month",
              "direction", "state", "unit", "currency", "actual", "target", "gap", "band", "tolerance",
              "actual_evidence", "target_evidence", "sources", "origins", "also_pinned", "snapshot_id",
              "snapshot_as_of", "tolerance_known_at"}
#: Spec §6 F1, Kobo October: the four raised leaves and their gaps (pack figures at M rev 16.20, D-DD.150-152:
#: necessary_l 489 against the plan's 700 is FAVOURABLE and is not written).
KOBO_RAISED = {"adjustments_kwh": "45", "outstanding": "278", "candidate_l": "25", "unexplained_l": "120"}

if URL:
    import pg_harness
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import _alembic, engine, store  # noqa: F401
    from test_w203_cold_migration_postgres import head

    from assetops_backend import declare_tolerance, observe_structure
    from assetops_backend.accounts.adapters.postgres_account_store import PostgresAccountStore
    from assetops_backend.accounts.service import AccountService
    from assetops_backend.analytics.composition import build_finding_store, build_postgres_assessment_store
    from assetops_backend.chain.adapters.postgres_chain_read import _UNSETTLED
    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.chain.ports import SiteRef
    from assetops_backend.scheduling.stages import chain_threads
    from assetops_backend.structure.evaluate import LeafValue, SiteStructure, evaluate
    from assetops_backend.structure.observe import rules
    from assetops_backend.structure.observe.service import ObserveRefused, StructureObserver
    from assetops_backend.structure.read import OTHER_STRUCTURE
    from assetops_backend.structure.targets.read import SiteTargets
    from assetops_backend.structure_snapshot.model import (Freshness, PortfolioMonthSnapshot, Served,
                                                           SiteMonthSnapshot, SnapshotRow)
    from test_3b4_observer import MG, _missing, _pack


class SetClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


def _side(name: str, side: str, month: str, *, drop=(), values=None) -> "SiteStructure":
    """F1's pack side for `month`; `values` overrides a leaf's figure, `drop` makes it not available."""
    nodes = _pack(name)["actual" if side == "actual" else "plan"]["nodes"]
    evidence, source = ("RECORDED", "pack:actual") if side == "actual" else ("DECLARED", "pack:plan")
    leaves = {}
    for row in MG.rows:
        if not row.is_leaf:
            continue
        cur = "USD" if rules.money_dimension(row.unit) else None
        if row.factor_id in drop:
            leaves[row.factor_id] = LeafValue(None, "NOT_AVAILABLE", (), None, _missing(), None)
        else:
            figure = (values or {}).get(row.factor_id, nodes[row.factor_id])
            leaves[row.factor_id] = LeafValue(Decimal(str(figure)), evidence, (source,), None, None, cur,
                                              ("source-emulated",))
    return SiteStructure(f"{name.upper()}-001", month, "MINI_GRID", MG.version, evaluate(MG, leaves))


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _row(rid: UUID, tenant_id: UUID, site_id: UUID | None, month: str, as_of: datetime, digest: str,
         sites: tuple[UUID, ...] | None = None) -> "SnapshotRow":
    return SnapshotRow(rid, tenant_id, site_id, month, "MINI_GRID", MG.version, 1, as_of, "service:test", True,
                       "0" * 64, (), (), "{}", digest, sites)


@dataclass
class Put:
    """One fake build: what `portfolio` serves for a month and the rows `get` answers."""
    served: "Served"
    site_snapshot_id: UUID | None
    site_digest: str | None
    portfolio_digest: str | None


class World:
    """F3 over the harness database: the Sites and people written, the fakes in memory."""

    def __init__(self, engine) -> None:  # noqa: F811
        self.engine = engine
        self.t, self.s, self.other = uuid4(), uuid4(), uuid4()
        at = datetime(2026, 9, 1, tzinfo=UTC)
        with engine.begin() as c:
            c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, :s, :s, :at)"),
                      {"id": self.t, "s": SLUG, "at": at})
            for sid, code in ((self.s, "KOBO-001"), (self.other, "OTHER-001")):
                c.execute(text(
                    "INSERT INTO site (id, tenant_id, site_code, site_code_key, name, site_type, timezone, "
                    "lifecycle, origin, proposed_source_mode, created_at) VALUES (:id, :t, :c, lower(:c), :c, "
                    "'MINIGRID', 'Africa/Nairobi', 'ACTIVE', 'IMPORTED', 'SIMULATED', :at)"),
                    {"id": sid, "t": self.t, "c": code, "at": at})
        self.ref = SiteRef(self.t, self.s, "KOBO-001", "MINIGRID", "Africa/Nairobi")
        self.refs = (self.ref, SiteRef(self.t, self.other, "OTHER-001", "MINIGRID", "Africa/Nairobi"),
                     SiteRef(self.t, uuid4(), "COLD-001", "COLDCHAIN", "Africa/Nairobi"))
        self.accounts = AccountService(PostgresAccountStore(URL), clock=lambda: at)
        self.accounts.onboard_create(SLUG, "amina@lakeside.example", "Amina", PW, executive=True)
        boss = self.accounts.sign_in("amina@lakeside.example", PW).principal
        for name, role, site in (("fiona", FIN, None), ("sam", SM, "KOBO-001"), ("olga", SM, "OTHER-001")):
            pid = self.accounts.onboard_create(SLUG, f"{name}@lakeside.example", name.title(), PW, executive=False)
            self.accounts.grant(boss, pid, role, site)
        self.puts: dict[str, Put] = {}
        self.rows: dict[UUID, SnapshotRow] = {}
        self.findings = build_finding_store(URL)
        self.assessments = build_postgres_assessment_store(URL)
        self.clock = SetClock(datetime.now(UTC))
        self.observer = StructureObserver(self, self, self.findings, self.assessments, self.clock)
        self.wiring = SimpleNamespace(observer=self.observer, store=self, findings=self.findings,
                                      dispose=lambda: None)

    # --- the fake SnapshotRead and StructureSnapshotStore ---------------------------------------------------------

    def portfolio(self, tenant_id: UUID, month: str) -> "Served":
        put = self.puts.get(month)
        return Served("NO_SNAPSHOT", None, None, None) if put is None else put.served

    def get(self, tenant_id: UUID, ids) -> tuple:
        return tuple(self.rows[i] for i in ids if i in self.rows and self.rows[i].tenant_id == tenant_id)

    def tenant_sites(self, slug: str):
        return (self.t, self.refs) if slug == SLUG else None

    # --- builds -----------------------------------------------------------------------------------------------------

    def put(self, month: str = OCT, *, drop=(), values=None, closed=True, site_closed=True, current=True,
            state="SERVED") -> Put:
        """A new build of `month`: new ids, a new `as_of`, new row digests; same figures unless told."""
        as_of = datetime.now(UTC)
        sid, pid = uuid4(), uuid4()
        if state == "REBUILD_NEEDED":
            put = Put(Served("REBUILD_NEEDED", None, as_of, Freshness(False, ("FORMAT",), (), (), ())), None, None,
                      None)
            self.puts[month] = put
            return put
        targets = SiteTargets(_side("Kobo", "plan", month), None, (), "USD")
        site = SiteMonthSnapshot(sid, self.t, self.ref, month, as_of, "service:test", site_closed, (), None,
                                 _side("Kobo", "actual", month, drop=drop, values=values), targets)
        snap = PortfolioMonthSnapshot(pid, self.t, month, as_of, "service:test", closed, (),
                                      ("KOBO-001", "COLD-001"), MappingProxyType({"COLD-001": OTHER_STRUCTURE}),
                                      MappingProxyType({"KOBO-001": site}), None)
        sd, pd = _digest(f"site:{sid}"), _digest(f"portfolio:{pid}")
        self.rows[sid] = _row(sid, self.t, self.s, month, as_of, sd)
        self.rows[pid] = _row(pid, self.t, None, month, as_of, pd, (sid,))
        freshness = Freshness(current, () if current else ("RECORDS",), (), (), ())
        put = Put(Served("SERVED", snap, as_of, freshness), sid, sd, pd)
        self.puts[month] = put
        return put

    def run(self, month: str = OCT):
        self.clock.now = datetime.now(UTC)
        return self.observer.run(self.t, month)

    # --- reads --------------------------------------------------------------------------------------------------------

    def q(self, sql: str, **p) -> list:
        with self.engine.connect() as c:
            return c.execute(text(sql), {"t": self.t, "s": self.s, **p}).all()

    def count(self, table: str, where: str = "true") -> int:
        return self.q(f"SELECT count(*) FROM {table} WHERE tenant_id = :t AND {where}")[0][0]

    def declare(self, *argv: str, capsys=None) -> tuple[int, str, str]:
        code = declare_tolerance.main(list(argv), observer=self.wiring, accounts=self.accounts)
        out, err = capsys.readouterr() if capsys is not None else ("", "")
        return code, out, err

    def close(self) -> None:
        pg_harness.dispose(self.findings, self.assessments, self.accounts._store)


@pytest.fixture()
def world(store, engine):  # noqa: F811 - `store` empties the tenant closure
    owned = World(engine)
    yield owned
    owned.close()


def _written(result) -> list[tuple[str, str]]:
    return [(w.factor_id, w.transition) for w in result.sites["KOBO-001"].written]


# --- test 10: the migration ------------------------------------------------------------------------------------------

def checks(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        return dict(c.execute(text(
            "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE conname IN ('finding_domain_subject', 'finding_revision_domain_minutes')")).all())


def _widened(before: str, arm: str) -> str:
    """pg's text of 0056's flat OR list `CHECK ((a OR ... OR d))` with one more arm."""
    assert before.startswith("CHECK ((") and before.endswith("))")
    return f"{before[:-2]} OR {arm}))"


def _tolerance_table(engine) -> bool:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT to_regclass('structure_tolerance') IS NOT NULL")).scalar_one()


def test_10_single_head_on_0067() -> None:
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [alembic_head()]
    assert script.get_revision(MIGRATION).down_revision == PREVIOUS


def test_10_checks_are_0056s_plus_the_arms_down_and_up(store, engine) -> None:  # noqa: F811
    from alembic import command

    pg_harness.dispose(store)
    up = checks(engine)
    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS and not _tolerance_table(engine)
        down = checks(engine)
        assert "structure" not in " ".join(down.values()) and "fuel_balance" in down["finding_domain_subject"]
        assert up["finding_domain_subject"] == _widened(down["finding_domain_subject"], SUBJECT_ARM)
        assert up["finding_revision_domain_minutes"] == _widened(down["finding_revision_domain_minutes"],
                                                                 MINUTES_ARM)
        command.upgrade(config, "head")
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert checks(engine) == up and _tolerance_table(engine)


def test_10_subject_refused_and_downgrade_refused_with_a_row(world, engine) -> None:  # noqa: F811
    from alembic import command

    world.put()
    world.run()
    fid = world.q("SELECT id FROM finding WHERE domain = 'structure' LIMIT 1")[0][0]
    with pytest.raises(IntegrityError, match="finding_domain_subject"):
        with engine.begin() as c:
            c.execute(text(
                "INSERT INTO finding (id, tenant_id, site_id, finding_key, domain, mechanism, analytic_id, "
                "generator_asset_id, subject_asset_id, anchor_start, anchor_assessment_revision_id, matcher_version, "
                "opened_at, created_at) SELECT :id, tenant_id, site_id, 'x', 'structure', mechanism, analytic_id, "
                "NULL, :a, anchor_start, anchor_assessment_revision_id, matcher_version, opened_at, created_at "
                "FROM finding WHERE id = :f"), {"id": uuid4(), "a": uuid4(), "f": fid})
    world.close()
    config = _alembic()
    engine.dispose()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert head(engine) == alembic_head()


# --- test 11: the lifecycle --------------------------------------------------------------------------------------------

def _revision(world, rid):
    return world.q("SELECT * FROM finding_revision WHERE id = :r", r=rid)[0]


def test_11_lifecycle(world, capsys) -> None:
    oct1 = world.put()
    first = world.run()
    assert sorted(_written(first)) == sorted((f, "OPENED") for f in KOBO_RAISED)
    assert first.excluded == {"COLD-001": ("STRUCTURE_OTHER_KEY",)}   # 3B6: cold has its own structure
    digests = {}   # revision id -> the Site row digest of the build it came from
    for w in first.sites["KOBO-001"].written:
        digests[w.revision_id] = oct1.site_digest
        r = _revision(world, w.revision_id)
        assert (r.domain, r.lifecycle, r.transition, r.title, r.claim_level) == (
            "structure", "SUPPORTED", "OPENED", rules.MECHANISM, "COMPLETE")
        assert set(r.claim) == CLAIM_KEYS                                   # P15: a literal key set
        assert Decimal(r.claim["gap"]) == Decimal(KOBO_RAISED[w.factor_id])
        assert (r.claim["state"], r.claim["month"], r.claim["snapshot_id"]) == ("RAISED", OCT,
                                                                                str(oct1.site_snapshot_id))
        f = world.q("SELECT * FROM finding WHERE id = :f", f=w.finding_id)[0]
        assert f.finding_key == rules.finding_key("MINI_GRID", w.factor_id, OCT, "UP")
        assert (f.domain, f.generator_asset_id, f.subject_asset_id, f.recurs_after_finding_id) == (
            "structure", None, None, None)
    unexplained = _revision(world, next(w.revision_id for w in first.sites["KOBO-001"].written
                                        if w.factor_id == "unexplained_l"))
    assert Decimal(unexplained.claim["band"]) == Decimal("12.68") and unexplained.claim["tolerance"]["source"] == \
        "STRUCTURE"
    outstanding = _revision(world, next(w.revision_id for w in first.sites["KOBO-001"].written
                                        if w.factor_id == "outstanding"))
    assert outstanding.claim["currency"] == "USD" and outstanding.claim["unit"] == "MONEY"
    assert _written(world.run()) == []                                      # a re-run writes nothing
    rebuilt = world.put()                                                   # new as_of, id and row digest
    assert rebuilt.site_digest != oct1.site_digest
    assert _written(world.run()) == []                                      # P10: still nothing
    changed = world.put(values={"candidate_l": 340})
    result = world.run()
    # candidate_l moves diesel_l (necessary + candidate + unexplained + extra), so unexplained_l's 2 % band moves too
    assert _written(result) == [("candidate_l", "SUPPORT_CHANGED"), ("unexplained_l", "SUPPORT_CHANGED")]
    for w in result.sites["KOBO-001"].written:
        digests[w.revision_id] = changed.site_digest
    put = world.put(values={"candidate_l": 340})
    code, out, err = world.declare("set", "--tenant", SLUG, "--site", "KOBO-001", "--factor", "adjustments_kwh",
                                   "--of", "delivered_kwh", "--pct", "5", "--from", OCT, "--as", "sam@lakeside.example",
                                   capsys=capsys)
    assert code == 0, err
    result = world.run()
    assert result.sites["KOBO-001"].states["adjustments_kwh"] == "INSIDE_TOLERANCE"
    assert _written(result) == [("adjustments_kwh", "NO_LONGER_SUPPORTED")]   # P11: never UNCONFIRMED here
    digests[result.sites["KOBO-001"].written[0].revision_id] = put.site_digest
    code, _, err = world.declare("clear", "--tenant", SLUG, "--site", "KOBO-001", "--factor", "adjustments_kwh",
                                 "--from", OCT, "--as", "sam@lakeside.example", capsys=capsys)
    assert code == 0, err
    result = world.run()
    assert _written(result) == [("adjustments_kwh", "REOPENED")]
    digests[result.sites["KOBO-001"].written[0].revision_id] = put.site_digest
    put = world.put(values={"candidate_l": 340}, drop=("outstanding",))
    result = world.run()
    assert result.sites["KOBO-001"].states["outstanding"] == "ACTUAL_NOT_AVAILABLE"
    assert _written(result) == [("outstanding", "UNCONFIRMED")]
    digests[result.sites["KOBO-001"].written[0].revision_id] = put.site_digest
    nov = world.put(NOV)
    result = world.run(NOV)
    assert sorted(_written(result)) == sorted((f, "OPENED") for f in KOBO_RAISED)
    by_leaf = {w.factor_id: w for w in result.sites["KOBO-001"].written}
    for w in result.sites["KOBO-001"].written:
        digests[w.revision_id] = nov.site_digest
    october = {f: world.q("SELECT id FROM finding WHERE finding_key = :k",
                          k=rules.finding_key("MINI_GRID", f, OCT, "UP"))[0][0] for f in KOBO_RAISED}
    recurs = dict(world.q("SELECT finding_key, recurs_after_finding_id FROM finding WHERE id = ANY(:ids)",
                          ids=[w.finding_id for w in by_leaf.values()]))
    assert recurs[rules.finding_key("MINI_GRID", "candidate_l", NOV, "UP")] == october["candidate_l"]
    assert recurs[rules.finding_key("MINI_GRID", "outstanding", NOV, "UP")] is None   # October's is UNCONFIRMED
    stored = dict(world.q("SELECT id, input_evidence_sha256 FROM finding_revision WHERE domain = 'structure'"))
    assert stored == digests                                                # P23: the Site row's, every revision
    assert not set(stored.values()) & {p.portfolio_digest for p in world.puts.values()}
    for r in world.q("SELECT claim FROM finding_revision WHERE domain = 'structure'"):
        assert set(r.claim) == CLAIM_KEYS


# --- test 12: runs and assessment revisions --------------------------------------------------------------------------

def test_12_one_run_per_site_month_basis_one_assessment_per_revision(world) -> None:
    analytic = rules.OBSERVER_ANALYTIC

    def counts():
        return (world.count("analytic_run", f"analytic_id = '{analytic}'"),
                world.count("assessment_revision", f"analytic_id = '{analytic}'"),
                world.count("analytic_run_assessment"))

    world.put()
    # candidate_l also moves unexplained_l's band (2 % of diesel_l), so each change writes two revisions
    for values, expected in ((None, 4), (None, 0), ({"candidate_l": 340}, 2), ({"candidate_l": 340}, 0),
                             ({"candidate_l": 350}, 2)):
        before = counts()
        world.put(values=values)
        written = world.run().sites["KOBO-001"].written
        after = counts()
        assert len(written) == expected
        assert after == (before[0] + (1 if expected else 0), before[1] + expected, before[2] + expected)
        if written:
            runs = {world.q("SELECT analytic_run_id FROM finding_revision WHERE id = :r", r=w.revision_id)[0][0]
                    for w in written}
            assert len(runs) == 1
            ar = world.q("SELECT assessment_key, result FROM assessment_revision WHERE id IN (SELECT "
                         "assessment_revision_id FROM finding_revision WHERE id = ANY(:ids))",
                         ids=[w.revision_id for w in written])
            assert sorted(k for k, _ in ar) == sorted(f"{w.factor_id}:{OCT}" for w in written)
            assert all(set(result) == CLAIM_KEYS for _, result in ar)


# --- test 13: today's readers leave the domain out ----------------------------------------------------------------

def test_13_readers(world, engine) -> None:  # noqa: F811
    fence_before = world.findings.fence(world.t, world.s, "dispatch-shortfall-1")
    world.put()
    written = world.run().sites["KOBO-001"].written
    assert len(written) == 4
    a, b = written[0], written[1]
    with engine.begin() as c:   # a merge and an evidence link on structure revisions, so the last two lists are tested
        c.execute(text("INSERT INTO finding_merge (superseded_finding_id, canonical_finding_id, tenant_id, site_id, "
                       "finding_revision_id, created_at) VALUES (:a, :b, :t, :s, :r, now())"),
                  {"a": a.finding_id, "b": b.finding_id, "t": world.t, "s": world.s, "r": b.revision_id})
        c.execute(text("SET LOCAL session_replication_role = replica"))   # no accepted_evidence row exists
        c.execute(text("INSERT INTO finding_revision_evidence (finding_revision_id, evidence_id, tenant_id, site_id) "
                       "VALUES (:r, :e, :t, :s)"), {"r": a.revision_id, "e": uuid4(), "t": world.t, "s": world.s})
    structure_revisions = {r[0] for r in world.q("SELECT id FROM finding_revision WHERE domain = 'structure'")}
    for table in ("finding_revision_assessment", "finding_revision_evidence", "finding_merge"):
        assert world.count(table, "finding_revision_id = ANY(:ids)".replace(":ids", "ARRAY[" + ",".join(
            f"'{i}'::uuid" for i in structure_revisions) + "]")) > 0, table
    # the fence (P17)
    assert world.findings.fence(world.t, world.s, "dispatch-shortfall-1").finding_revisions == \
        fence_before.finding_revisions
    # finding_detail (P13)
    for w in written:
        assert world.findings.finding_detail(world.t, world.s, w.finding_id) is None
    # rows(), all five lists (P18, P19)
    rows = world.findings.rows(world.t, world.s)
    assert rows["findings"] == [] and rows["revisions"] == []
    for name in ("assessments", "evidence", "merges"):
        assert not {r["finding_revision_id"] for r in rows[name]} & structure_revisions, name
    # the threads stage consumes the events and places nothing (P12)
    with engine.connect() as c:
        assert c.execute(_UNSETTLED, {"t": world.t, "s": world.s, "k": None}).scalar() is True
    out = chain_threads(URL, {"tenant_id": str(world.t), "site_id": str(world.s)})
    assert out["code"] == "OK", out
    with engine.connect() as c:
        assert c.execute(_UNSETTLED, {"t": world.t, "s": world.s, "k": None}).scalar() is False
    reader, threads = build_thread_sources(URL), build_thread_store(URL)
    try:
        run_threads(reader, threads, world.t, world.s)   # the backfill does not abort either
    finally:
        reader.dispose()
        threads.dispose()
    assert world.count("finding_thread") == 0 and world.count("finding_thread_occurrence") == 0


# --- test 14: refusals ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("code, put", [
    ("NO_SNAPSHOT", None),
    ("REBUILD_NEEDED", {"state": "REBUILD_NEEDED"}),
    ("SNAPSHOT_NOT_CURRENT", {"current": False}),
    ("MONTH_OPEN", {"site_closed": False}),
    ("MONTH_OPEN", {"closed": False}),
])
def test_14_refusals_write_nothing(world, capsys, code, put) -> None:
    if put is not None:
        world.put(**put)
    with pytest.raises(ObserveRefused) as refused:
        world.run()
    assert refused.value.code == code
    assert observe_structure.main(["run", "--tenant", SLUG, "--month", OCT], observer=world.wiring) == 3
    out, err = capsys.readouterr()
    assert (out, err) == ("", f"{code}\n")
    assert world.count("finding") == 0 and world.count("analytic_run") == 0 and \
        world.count("assessment_revision") == 0


def test_14_command_line(world, capsys, monkeypatch) -> None:
    for argv, exit_code, err in ((["run", "--tenant", "nobody", "--month", OCT], 2, "UNKNOWN_TENANT\n"),
                                 (["run", "--tenant", SLUG, "--month", "2026-13"], 2, "BAD_MONTH\n")):
        assert observe_structure.main(argv, observer=world.wiring) == exit_code
        assert capsys.readouterr() == ("", err)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert observe_structure.main(["run", "--tenant", SLUG, "--month", OCT]) == 2
    assert capsys.readouterr() == ("", "NO_DATABASE\n")
    world.put()
    assert observe_structure.main(["run", "--tenant", SLUG, "--month", OCT], observer=world.wiring) == 0
    out, err = capsys.readouterr()
    line = json.loads(out)
    assert err == "" and set(line) == {"month", "snapshot_id", "as_of", "sites", "excluded"}
    assert sorted(w["transition"] for w in line["sites"]["KOBO-001"]["written"]) == ["OPENED"] * 4
    assert line["excluded"] == {"COLD-001": ["STRUCTURE_OTHER_KEY"]}


# --- test 15: the tolerance command ----------------------------------------------------------------------------------

def _set(factor: str, of: str, pct: str, person: str, *, site="KOBO-001", tenant=SLUG, month=OCT) -> list[str]:
    return ["set", "--tenant", tenant, "--site", site, "--factor", factor, "--of", of, f"--pct={pct}",
            "--from", month, "--as", f"{person}@lakeside.example"]


def test_15_tolerance_command(world, capsys, monkeypatch) -> None:
    code, out, err = world.declare(*_set("outstanding", "outstanding", "10", "fiona"), capsys=capsys)
    assert code == 0, err
    line = json.loads(out)
    assert (line["state"], line["factor_id"], line["of_factor"], line["pct"], line["valid_from"],
            line["recorded_role"], line["recorded_by_script"]) == ("SET", "outstanding", "outstanding", "10", OCT,
                                                                   FIN, True)
    assert world.declare(*_set("necessary_l", "diesel_l", "5", "fiona"), capsys=capsys)[1:] == \
        ("", "PERSON_ROLE_REQUIRED\n")
    code, out, err = world.declare(*_set("necessary_l", "diesel_l", "5", "sam"), capsys=capsys)
    assert code == 0 and json.loads(out)["recorded_role"] == SM, err
    assert world.declare(*_set("necessary_l", "diesel_l", "5", "olga"), capsys=capsys)[1:] == \
        ("", "PERSON_ROLE_REQUIRED\n")                                          # P14: another Site's manager
    assert world.declare(*_set("outstanding", "outstanding", "10", "sam"), capsys=capsys)[1:] == \
        ("", "PERSON_ROLE_REQUIRED\n")                                          # money needs the finance lead
    held = world.count("structure_tolerance")
    assert held == 2
    # L3: a FINANCE person of another tenant, and a disabled FINANCE person of this one, are not found
    other = AccountService(PostgresAccountStore(URL), clock=lambda: datetime(2026, 9, 1, tzinfo=UTC))
    with world.engine.begin() as c:
        c.execute(text("INSERT INTO tenant (id, slug, name, created_at) VALUES (:id, 'elsewhere', 'elsewhere', now())"),
                  {"id": uuid4()})
    other.onboard_create("elsewhere", "zed@elsewhere.example", "Zed", PW, executive=True)
    zed = other.sign_in("zed@elsewhere.example", PW).principal
    other.grant(zed, other.onboard_person("zed@elsewhere.example").person_id, FIN, None)
    boss = world.accounts.sign_in("amina@lakeside.example", PW).principal
    pid = world.accounts.onboard_create(SLUG, "dora@lakeside.example", "Dora", PW, executive=False)
    world.accounts.grant(boss, pid, FIN, None)
    with world.engine.begin() as c:
        c.execute(text("INSERT INTO account_status (id, tenant_id, person_id, status, reason, set_at, set_by) "
                       "VALUES (:i, :t, :p, 'DISABLED', NULL, now(), 'service:test')"),
                  {"i": uuid4(), "t": world.t, "p": pid})
    for who in ("zed@elsewhere.example", "dora@lakeside.example"):
        argv = _set("outstanding", "outstanding", "10", "x")
        argv[-1] = who
        assert world.declare(*argv, capsys=capsys) == (2, "", "PERSON_NOT_FOUND\n"), who
    assert world.count("structure_tolerance") == held
    pg_harness.dispose(other._store)
    refusals = [
        (_set("necessary_l", "diesel_l", "5", "sam", tenant="nobody"), "UNKNOWN_TENANT"),
        (_set("necessary_l", "diesel_l", "5", "sam", site="NOPE-001"), "SITE_UNKNOWN"),
        (_set("necessary_l", "diesel_l", "5", "sam", site="COLD-001"), "FACTOR_NOT_OBSERVED"),  # 3B6: COLD_CHAIN, unobserved
        (_set("billed_kwh", "billed_kwh", "5", "sam"), "FACTOR_NOT_OBSERVED"),
        (_set("technical_loss_kwh", "delivered_kwh", "5", "sam"), "FACTOR_NOT_OBSERVED"),
        (_set("necessary_l", "outstanding", "5", "sam"), "OF_FACTOR_UNIT"),
        (_set("necessary_l", "nope_l", "5", "sam"), "OF_FACTOR_UNIT"),
        (_set("necessary_l", "diesel_l", "100.5", "sam"), "PCT_INVALID"),
        (_set("necessary_l", "diesel_l", "abc", "sam"), "PCT_INVALID"),
        (_set("necessary_l", "diesel_l", "-1", "sam"), "PCT_INVALID"),
        (_set("necessary_l", "diesel_l", "5", "sam", month="2026-13"), "BAD_MONTH"),
        (_set("necessary_l", "diesel_l", "5", "nobody"), "PERSON_NOT_FOUND"),
        (["clear", "--tenant", SLUG, "--site", "KOBO-001", "--factor", "necessary_l", "--from", OCT, "--as",
          "fiona@lakeside.example"], "PERSON_ROLE_REQUIRED"),
    ]
    for argv, expected in refusals:
        assert world.declare(*argv, capsys=capsys) == (2, "", f"{expected}\n"), argv
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert declare_tolerance.main(_set("necessary_l", "diesel_l", "5", "sam")) == 2
    assert capsys.readouterr() == ("", "NO_DATABASE\n")
    assert world.count("structure_tolerance") == held                         # refusals wrote nothing
    code, out, err = world.declare(*_set("candidate_l", "diesel_l", "0", "sam"), capsys=capsys)
    assert code == 0 and json.loads(out)["pct"] == "0", err                    # P20: 0 is accepted
    code, out, err = world.declare("show", "--tenant", SLUG, "--site", "KOBO-001", "--month", OCT, capsys=capsys)
    assert code == 0, err
    shown = {r["factor_id"]: r for r in json.loads(out)}
    assert list(shown) == list(rules.OBSERVED["MINI_GRID"])
    latest = world.q("SELECT id FROM structure_tolerance WHERE factor_id = 'candidate_l' AND pct = '0'")[0][0]
    assert shown["candidate_l"] == {"factor_id": "candidate_l", "source": "SITE", "of_factor": "diesel_l",
                                    "pct": "0", "declaration_id": str(latest)}
    assert (shown["outstanding"]["source"], shown["outstanding"]["pct"]) == ("SITE", "10")
    assert shown["unexplained_l"] == {"factor_id": "unexplained_l", "source": "STRUCTURE", "of_factor": "diesel_l",
                                      "pct": "2.0", "declaration_id": None}
    assert {k: v for k, v in shown["necessary_l"].items() if k != "declaration_id"} == {   # sam's earlier 5 %
        "factor_id": "necessary_l", "source": "SITE", "of_factor": "diesel_l", "pct": "5"}
    code, out, _ = world.declare("show", "--tenant", SLUG, "--site", "KOBO-001", "--month", "2026-09",
                                 capsys=capsys)
    assert {r["factor_id"]: r["source"] for r in json.loads(out)}["candidate_l"] == "NONE"   # read by month
    rows = world.q("SELECT recorded_by, recorded_role, recorded_by_script, recorded_at FROM structure_tolerance "
                   "ORDER BY recorded_at")
    assert all(r.recorded_by_script and r.recorded_at is not None for r in rows)
    with pytest.raises(DBAPIError, match="append-only"):
        with world.engine.begin() as c:
            c.execute(text("UPDATE structure_tolerance SET pct = '9' WHERE id = :i"), {"i": latest})
    # pct 0 in force at run time: Kobo candidate_l is RAISED with band 0 (D-3B4.19; necessary_l is FAVOURABLE at M rev 16.20)
    world.put()
    result = world.run()
    assert result.sites["KOBO-001"].states["candidate_l"] == "RAISED"
    rid = next(w.revision_id for w in result.sites["KOBO-001"].written if w.factor_id == "candidate_l")
    claim = _revision(world, rid).claim
    assert Decimal(claim["band"]) == 0 and claim["tolerance"]["source"] == "SITE"
    assert (claim["tolerance"]["pct"], claim["tolerance"]["declaration_id"]) == ("0", str(latest))
