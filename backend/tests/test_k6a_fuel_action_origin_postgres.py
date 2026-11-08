"""DIESEL-K6a L2 (build sheet DIESEL-1 §9m.3, rulings DIESEL-1-R3m and R3m2): the fuel Finding as a domain-Action
origin on Postgres at migration 0057, on its own `assetops_k6_test`.

A fuel Finding is raised the K4a way (synthetic windows through the fuel-balance store on a virtual clock, then
`raise_night`) on the imported Kobo MINIGRID Site, with the clock before the real DB time so `command_now` sees it:

1. 0057 up/down/up with the CHECKs as pg prints them; the downgrade refused with a `FUEL_BALANCE` Action and with a
   fuel plan row; the origin and family CHECKs below the service; a single alembic head.
2. Create (201 / identical retry 200 / other body 409) and the three LINK_INVALID refusals.
3. The case: request, record, ASSIGN, COMPLETE, then the case link.
4. The Cold/EV index omits the fuel Action while a Cold row is still listed.
5. The request's domain-link row: lineage true, pin None; R3m2: no served href names `/actions/{id}`.
6. `run_threads` joins the Action to the fuel Finding's thread.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from test_k4a_fuel_finding_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

MIGRATION, PREVIOUS = "0057_fuel_verification", "0056_unexplained_fuel_finding"
REFUSED = "0057 downgrade requires no fuel-balance Actions or fuel verification plans"
UTC = timezone.utc
CODE = "KOBO-001"
NIGHT, OTHER_NIGHT, LATE_NIGHT = date(2026, 10, 20), date(2026, 10, 22), date(2026, 10, 24)
FUEL_LINK = "The declared unexplained-fuel Finding is not its current supported version at this site and time."
FUEL_CONFLICT = "This Action declaration has a newer version; reload it."
CHECK_NAMES = ("domain_action_domain_chk", "verification_plan_plan_version_check", "verification_plan_rule_id_check",
               "verification_plan_family")

if URL:
    import pg_harness
    from pg_harness import alembic_head
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_k4a_fuel_finding_postgres import Fuel
    from test_s1_bindings_postgres import _alembic, engine, imported, store  # noqa: F401
    from test_w203_cold_migration_postgres import head
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, at, event, record, request

    from assetops_backend.chain.backfill import run_threads
    from assetops_backend.chain.composition import build_thread_sources, build_thread_store
    from assetops_backend.work import domain_action as d
    from assetops_backend.work.adapters.postgres_domain_action_index import PostgresDomainActionRead
    from assetops_backend.work.composition import build_domain_intent_service, build_work_read, build_work_service
    from assetops_backend.work.detail import WorkDetailService
    from assetops_backend.work.site_index import WorkIndexService, parse_list_request


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _now(engine) -> datetime:  # noqa: F811
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one().astimezone(UTC)


class Kit:
    """The Kobo Site with the fuel Finding service (K4a's `Fuel`), the domain Action commands and the work service."""

    def __init__(self, store, engine) -> None:  # noqa: F811
        result = imported(store)
        self.engine, self.t, self.s = engine, result.tenant.id, result.site.id
        self.fuel = Fuel(engine, self.t, self.s)
        self.svc, self.work = build_domain_intent_service(URL), build_work_service(URL)
        assert self.fuel.clock.now < _now(engine), "the fuel clock must be before the real DB time"

    def finding(self, night: date, low: str = "45", high: str = "60", state: str = "UNEXPLAINED"):
        self.fuel.put(night, state, low, high)
        return self.fuel.raise_(night)

    def body(self, raised, key: str = "k6a-fuel-action-0001", **over) -> dict:
        return {"domain": "FUEL_BALANCE", "origin_finding_id": str(raised.finding_id),
                "origin_finding_revision_id": str(raised.revision_id),
                "title": "Seal the tank cap and sign the dip log", "owner_label": "Site lead", "due_at": None,
                "raised_at": _iso(_now(self.engine) - timedelta(minutes=10)), "actor": dict(ACTOR),
                "idempotency_key": key, **over}

    def create(self, body: dict):
        return self.svc.create_action(self.t, self.s, CODE, body, PRINCIPAL)

    def refused(self, body: dict) -> str:
        with pytest.raises(d.DomainIntentRefused) as e:
            self.create(body)
        return e.value.message

    def rows(self, sql: str, **p) -> list:
        with self.engine.connect() as c:
            return c.execute(text(sql), {"t": self.t, "s": self.s, **p}).all()

    def complete_case(self, action_id: str, tag: str) -> tuple[str, str]:
        """A W4 maintenance request, its performed record, ASSIGN, COMPLETE, then the case link (item 3)."""
        status, wr = self.work.create_case(self.t, self.s, request(f"{tag}-request"), PRINCIPAL)
        assert status == 201, wr
        case_id, rev_id = wr["id"], wr["revision"]["id"]
        s, rec = self.work.post_record(self.t, self.s, case_id, record(f"{tag}-record", occurred_at=at(minutes=20)),
                                       PRINCIPAL)
        assert s == 201, rec
        s, got = self.work.post_event(self.t, self.s, case_id, event("ASSIGN", {"assignee": "Site lead"},
                                                                     f"{tag}-assign", occurred_at=at(minutes=15)),
                                      PRINCIPAL)
        assert s == 201, got
        s, got = self.work.post_event(self.t, self.s, case_id, event(
            "COMPLETE", {"maintenance_record_id": rec["id"]}, f"{tag}-complete", occurred_at=at(minutes=10)),
            PRINCIPAL)
        assert s == 201 and got["state"] == "COMPLETED", got
        (head_event,) = self.rows("SELECT id FROM work_event WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                                  "LIMIT 1", c=case_id)[0]
        s, linked = self.svc.post_case_link(self.t, self.s, CODE, action_id, {
            "case_id": case_id, "case_revision_id": rev_id, "case_event_id": str(head_event), "actor": dict(ACTOR),
            "idempotency_key": f"{tag}-link"}, PRINCIPAL)
        assert s == 201, linked
        return case_id, str(head_event)

    def close(self) -> None:
        self.fuel.close()
        pg_harness.dispose(self.svc._store, self.work._store)


@pytest.fixture()
def kit(store, engine):  # noqa: F811
    owned = Kit(store, engine)
    yield owned
    owned.close()


# --- 1. 0057 ------------------------------------------------------------------------------------------------------

def checks(engine) -> dict:  # noqa: F811
    with engine.connect() as c:
        return dict(c.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                                   "WHERE conname = ANY(:n)"), {"n": list(CHECK_NAMES)}).all())


def test_single_alembic_head(engine) -> None:  # noqa: F811
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(_alembic())
    assert script.get_heads() == [alembic_head()] and head(engine) == alembic_head()
    assert script.get_revision(MIGRATION).down_revision == PREVIOUS


def test_0057_up_down_up_on_empty_tables(store, engine) -> None:  # noqa: F811
    from alembic import command

    pg_harness.dispose(store)
    up = checks(engine)
    assert set(up) == set(CHECK_NAMES)
    assert up["domain_action_domain_chk"] == ("CHECK ((domain = ANY (ARRAY['COLDCHAIN'::text, 'EV_CHARGING'::text, "
                                              "'MINI'::text, 'FUEL_BALANCE'::text])))")
    assert up["verification_plan_rule_id_check"] == (
        "CHECK ((rule_id = ANY (ARRAY['reserve-trial-1'::text, 'midday-productive-shift-1'::text, "
        "'fuel-residual-within-band-1'::text])))")
    assert up["verification_plan_plan_version_check"] == (
        "CHECK ((plan_version = ANY (ARRAY['reserve-trial-verification-1'::text, "
        "'midday-productive-shift-verification-1'::text, 'fuel-residual-verification-1'::text])))")
    family = up["verification_plan_family"]
    assert "'fuel-residual-within-band-1'::text" in family and "'fuel-seal-dip-sensor-power@1'::text" in family
    assert "(later_end - later_start) = '14 days'::interval" in family and "(baseline_start < baseline_end)" in family
    config = _alembic()
    engine.dispose()
    try:
        command.downgrade(config, PREVIOUS)
        assert head(engine) == PREVIOUS
        down = checks(engine)
        assert "FUEL_BALANCE" not in down["domain_action_domain_chk"] and "'MINI'::text" in down["domain_action_domain_chk"]
        for name in CHECK_NAMES[1:]:
            assert "fuel" not in down[name] and "midday-productive-shift" in down[name], name
        assert family.startswith(down["verification_plan_family"][:-2])  # 0052's arms verbatim, fuel arm appended
        command.upgrade(config, "head")
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert checks(engine) == up


def _downgrade_refused(engine) -> None:  # noqa: F811
    from alembic import command

    config = _alembic()
    engine.dispose()
    try:
        with pytest.raises(RuntimeError, match=REFUSED):
            command.downgrade(config, PREVIOUS)
    finally:
        if head(engine) != alembic_head():
            command.upgrade(config, "head")
    assert head(engine) == alembic_head()


def test_downgrade_refused_with_a_fuel_action(kit, engine) -> None:  # noqa: F811
    status, _ = kit.create(kit.body(kit.finding(NIGHT)))
    assert status == 201
    kit.close()
    _downgrade_refused(engine)


_INSERT = ("INSERT INTO domain_action (id, tenant_id, site_id, action_no, action_code, domain, origin_finding_id, "
           "origin_finding_revision_id, origin_opportunity_id, origin_opportunity_revision_id, title, raised_at, "
           "actor_kind, actor_id, attestation, idempotency_key, payload_sha256) VALUES (:id, :t, :s, :no, :code, "
           ":dom, :f, :fr, :o, :orv, 'check', now(), 'SERVICE', 'k6a', 'K6a L2', :key, :sha)")


def _refused_check(engine, sql: str, p: dict, constraint: str) -> None:  # noqa: F811
    with engine.connect() as c:
        with pytest.raises((IntegrityError, DBAPIError)) as e:
            c.execute(text(sql), p)
    assert constraint in str(e.value), e.value


def test_origin_checks_refuse_mini_with_a_finding_and_fuel_with_an_opportunity(kit, engine) -> None:  # noqa: F811
    raised = kit.finding(NIGHT)
    base = {"id": uuid4(), "t": kit.t, "s": kit.s, "o": None, "orv": None, "sha": "0" * 64}
    _refused_check(engine, _INSERT, {**base, "no": 920001, "code": "ACT-920001", "dom": "MINI", "f": raised.finding_id,
                                     "fr": raised.revision_id, "key": "k6a-raw-920001"}, "domain_action_mini_origin")
    _refused_check(engine, _INSERT, {**base, "no": 920002, "code": "ACT-920002", "dom": "FUEL_BALANCE", "f": None,
                                     "fr": None, "o": uuid4(), "orv": uuid4(), "key": "k6a-raw-920002"},
                   "domain_action_mini_origin")


_PLAN = ("INSERT INTO verification_plan (id, tenant_id, site_id, action_id, plan_version, origin_finding_revision_id, "
         "rule_id, effective_from, baseline_start, baseline_end, later_start, later_end, baseline_selection, "
         "baseline_evidence_ids, basis, target, guardrails, bands, coverage, later_selection_rule, plan_sha256, "
         "actor_kind, actor_id, source_channel, authorization_basis, triggering_service, triggering_fixture, "
         "idempotency_key, payload, payload_sha256, recorded_at, domain_action_id, applied_work_event_id, "
         "battery_asset_id) VALUES (:id, :t, :s, NULL, 'fuel-residual-verification-1', :fr, :rule, :e, :bs, :be, "
         ":ls, :le, '{}', '[]', '{}', '{}', '{}', '{}', '{}', '{}', repeat('a', 64), 'SYSTEM', 'service:k6a-l2', "
         "'SYSTEM_DEMONSTRATION_API', 'K6a L2', 'k6a-l2', :fixture, :key, '{}', repeat('b', 64), now(), :da, :we, "
         ":battery)")


def _plan(kit, action_id: str, work_event: str, revision_id, **over) -> dict:
    e = datetime(2026, 11, 1, tzinfo=UTC)
    return {"id": uuid4(), "t": kit.t, "s": kit.s, "fr": revision_id, "rule": "fuel-residual-within-band-1", "e": e,
            "bs": e - timedelta(days=12), "be": e - timedelta(days=5), "ls": e, "le": e + timedelta(days=14),
            "fixture": "fuel-seal-dip-sensor-power@1", "key": f"k6a-plan-{uuid4().hex[:8]}", "da": action_id,
            "we": work_event, "battery": None, **over}


def test_fuel_plan_family_check_and_downgrade_refused_with_a_plan(kit, engine) -> None:  # noqa: F811
    raised = kit.finding(NIGHT)
    status, action = kit.create(kit.body(raised))
    assert status == 201, action
    _, work_event = kit.complete_case(action["id"], "k6a-plan")
    battery = kit.rows("SELECT id FROM asset WHERE site_id = :s AND retired_at IS NULL LIMIT 1")[0][0]
    for over in ({"battery": battery},                                     # a reserve column set
                 {"fixture": "productive-load-midday@1"},                  # a different fixture
                 {"le": datetime(2026, 11, 14, tzinfo=UTC)}):              # later range not 14 days
        _refused_check(engine, _PLAN, _plan(kit, action["id"], work_event, raised.revision_id, **over),
                       "verification_plan_family")
    with engine.begin() as c:  # the legal fuel row
        c.execute(text(_PLAN), _plan(kit, action["id"], work_event, raised.revision_id))
    # A fuel plan always cites a domain Action, so its own refusal is proven with the Action present too.
    assert kit.rows("SELECT count(*) FROM verification_plan WHERE rule_id = 'fuel-residual-within-band-1'")[0][0] == 1
    kit.close()
    _downgrade_refused(engine)


# --- 2. create ----------------------------------------------------------------------------------------------------

def test_create_retry_conflict_and_link_refusals(kit) -> None:
    raised = kit.finding(NIGHT)
    body = kit.body(raised)
    status, action = kit.create(body)
    assert status == 201 and action["action_code"].startswith("ACT-")
    (row,) = kit.rows("SELECT domain, origin_finding_id, origin_finding_revision_id, origin_opportunity_id "
                      "FROM domain_action WHERE id = :a", a=action["id"])
    assert (row[0], str(row[1]), str(row[2]), row[3]) == ("FUEL_BALANCE", str(raised.finding_id),
                                                          str(raised.revision_id), None)
    again = kit.create(body)
    assert again[0] == 200 and again[1]["id"] == action["id"]
    assert kit.refused({**body, "title": "Another title"}) == FUEL_CONFLICT

    # an older SUPPORTED revision while a newer one exists (SUPPORT_CHANGED)
    revised = kit.finding(NIGHT, "50", "70")
    assert revised.finding_id == raised.finding_id and revised.revision_id != raised.revision_id
    assert kit.refused(kit.body(raised, key="k6a-older-0001")) == FUEL_LINK
    assert kit.create(kit.body(revised, key="k6a-newer-0001"))[0] == 201

    # the Finding's later NO_LONGER_SUPPORTED revision
    other = kit.finding(OTHER_NIGHT)
    withdrawn = kit.finding(OTHER_NIGHT, "-5", "10", state="WITHIN_MARGIN")
    assert withdrawn.status == "WITHDRAWN" and withdrawn.finding_id == other.finding_id
    assert kit.refused(kit.body(withdrawn, key="k6a-withdrawn-0001")) == FUEL_LINK

    # a revision created after command_now
    kit.fuel.clock.now = _now(kit.engine) + timedelta(days=1)
    late = kit.finding(LATE_NIGHT)
    assert late.status == "OPENED"
    assert kit.refused(kit.body(late, key="k6a-late-0001")) == FUEL_LINK


# --- 3-6. the case, the index, the request lineage and the thread --------------------------------------------------

def test_case_index_request_lineage_and_thread(kit, engine) -> None:  # noqa: F811
    raised = kit.finding(NIGHT)
    status, action = kit.create(kit.body(raised))
    assert status == 201, action
    aid = action["id"]
    case_id, _ = kit.complete_case(aid, "k6a-case")                      # item 3

    # item 4: a Cold row (raw, Finding pair) is listed; the fuel Action is not
    cold = uuid4()
    with engine.begin() as c:
        c.execute(text(_INSERT), {"id": cold, "t": kit.t, "s": kit.s, "no": 920010, "code": "ACT-920010",
                                  "dom": "COLDCHAIN", "f": raised.finding_id, "fr": raised.revision_id, "o": None,
                                  "orv": None, "key": "k6a-cold-920010", "sha": "0" * 64})
    reader = PostgresDomainActionRead(URL)
    lo, hi = _now(engine) - timedelta(days=2), _now(engine) + timedelta(days=1)
    try:
        got, listed, cold_one = reader.snapshot(kit.t, kit.s, CODE, lambda tx: (
            tx.action(aid, tx.read_at), [a["id"] for a in tx.actions_in_window(lo, hi, tx.read_at)],
            tx.action(str(cold), tx.read_at)))
    finally:
        pg_harness.dispose(reader)
    assert got is None and aid not in listed
    assert str(cold) in listed and cold_one is not None

    # item 5: the request's domain-link row reads like the mill's (lineage true, pin None)
    work_read = build_work_read(URL)
    try:
        (rev,) = kit.rows("SELECT id FROM work_case_revision WHERE case_id = :c ORDER BY recorded_at DESC, id DESC "
                          "LIMIT 1", c=case_id)[0]
        rows = work_read.snapshot(kit.t, kit.s, CODE, lambda tx: tx.link_selections(str(rev), None, None, tx.read_at))
        (link,) = [r for r in rows if r["id"] == aid]
        assert link["lineage"] is True and link["pin"] is None and link["domain"] == "fuel_balance"

        # R3m2: neither the request detail nor the maintenance index serves an `/actions/{id}` href for it
        detail = WorkDetailService(work_read).detail(kit.t, kit.s, CODE, case_id, [])
        now = _now(engine)
        index = WorkIndexService(work_read).read(
            kit.t, kit.s, CODE, "maintenance",
            parse_list_request(_iso(now - timedelta(days=1)), _iso(now + timedelta(minutes=5)), None, [], None),
            access_basis="k6a-l2")
    finally:
        pg_harness.dispose(work_read)
    for served in (detail, index):
        wire = json.dumps(served, default=str)
        assert aid in wire, "the fuel Action is not in the served body (the check would be vacuous)"
        assert f"/actions/{aid}" not in wire

    # item 6: the chain joins the Action to the fuel Finding's thread
    readers, writer = build_thread_sources(URL), build_thread_store(URL)
    try:
        run_threads(readers, writer, kit.t, kit.s)
    finally:
        pg_harness.dispose(readers, writer)
    (thread,) = kit.rows("SELECT o.thread_id FROM finding_thread_occurrence o WHERE o.finding_id = :f",
                         f=raised.finding_id)
    links = kit.rows("SELECT thread_id, origin_finding_id FROM chain_action_thread WHERE action_id = :a", a=aid)
    assert [(str(t), str(f)) for t, f in links] == [(str(thread[0]), str(raised.finding_id))]
