"""S5-01 phase 1: the selected-window Site Overview read, route order and money precedence (no database).

Packet `tasks/S5-01-site-overview.md` phase 1. Fakes stand in for the S4-02d upstream seam, the evidence ledger, the
Finding store and the consequence read, so every gate and the Finding choice can be driven independently; the
real-store composition is proved in `test_s5_overview_postgres.py`.
"""

from __future__ import annotations

import types
from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend import demonstration_label
from assetops_backend.evidence.ledger_reads import AwaitingComparison
from assetops_backend.evidence_api import build_evidence_router
from assetops_backend.site_overview import money_state as ms
from assetops_backend.site_overview.read import SiteOverviewRead, choose, intersects
from assetops_backend.site_overview.route import SiteOverviewRoute, selected_day
from assetops_backend.sites.ports import SiteNotFound

UTC = timezone.utc
DAY = date(2026, 10, 24)
D0 = datetime(2026, 10, 24, tzinfo=UTC)
T, S = uuid4(), uuid4()
CURRENT = {"status": "CURRENT", "stage": None, "reasons": [], "errors": []}


def finding(start: datetime, end: datetime, fid: str | None = None, head: str | None = "c-head") -> dict:
    return {"finding_id": fid or str(uuid4()), "finding_revision_id": str(uuid4()), "lifecycle": "SUPPORTED",
            "episode_start": start, "episode_end": end, "head_consequence_revision_id": head,
            "upstream_status": {"status": "CURRENT", "reasons": []}, "current_amount_permitted": True}


def priced(fid: str, rid: str, *, head="c-head", currency="USD", state="CURRENT", gate="ELIGIBLE",
           quantity="AVAILABLE", price="PRICED", row_state="PRICED", shown=True) -> dict:
    display = ({"state": "ROUNDED_OUTWARD", "currency": currency, "amount_low": "0.00", "amount_high": "15.82"}
               if currency == "USD" else {"state": "MINOR_UNIT_UNKNOWN", "currency": currency,
                                          "amount_low": None, "amount_high": None})
    return {"consequence_selection": {"head_consequence_revision_id": head, "finding_revision_id": rid},
            "currentness": {"state": state, "reasons": [], "pending_work": [], "current_amount_shown": shown},
            "money_eligibility": {"version": "money-eligibility-1", "state": gate, "pending_reasons": []},
            "consequence": {"id": head, "state": row_state, "presented_as_current": shown,
                            "model": {"model_id": "fuel-cost-1"}, "quantity": {"state": quantity},
                            "price": {"state": price, "revision_id": "p-1"},
                            "amount": {"low": "0", "high": "15.8125", "currency": currency},
                            "display": display if row_state == "PRICED" else None,
                            "lineage": {"assumptions": [{"assumption_revision_id": "p-1"}],
                                        "evidence_ids": ["e-1"], "assessments": [{"assessment_revision_id": "a-1"}]}}}


class World:
    def __init__(self, findings=(), eligibility=CURRENT, fingerprints=None, merged=(), bodies=None, day_run="run-1",
                 detail_run="run-1") -> None:
        self.findings_list = list(findings)
        self.eligibility = eligibility
        self.fingerprints = list(fingerprints or [{"count": 3, "sha256": "x"}, {"count": 3, "sha256": "x"}])
        self.merged, self.bodies = set(merged), bodies or {}
        self.day_run, self.detail_run = day_run, detail_run
        self.revisions = {f["finding_id"]: [{"id": f["finding_revision_id"], "episode_start": f["episode_start"],
                                             "episode_end": f["episode_end"]}] for f in self.findings_list}
        self.upstream = types.SimpleNamespace(window=self.window, dispose=lambda: None,
                                              schedule=types.SimpleNamespace(db_now=lambda: D0 + timedelta(hours=9)),
                                              dispatch_read=types.SimpleNamespace(window=self.detail))

    def window(self, t, s, start, end, env):
        return {"db_now": D0, "eligibility": self.eligibility, "findings": self.findings_list, "s3_jobs": [],
                "consequence_work": [], "schedule": {"state": "RUNNING"},
                "match": [{"day": DAY.isoformat(), "match_pass_id": "m-1", "matched_through_selection_seq": 4}],
                "days": [{"day": DAY.isoformat(), "s3_status": "CURRENT" if self.day_run else "UNASSESSED",
                          "s3_status_reasons": [], "limitations": [], "run_id": self.day_run,
                          "window_assessment_revision_id": "wa-1" if self.day_run else None, "claim_level": "C",
                          "watermark": {"selection_seq": 4, "input_sha256": "i", "configuration_sha256": "c"}}]}

    def detail(self, t, s, day):
        if not self.detail_run:
            return {"selection": None, "window_assessment": None, "intervals": [], "coverage": None}
        return {"model_version": "dispatch-3.2", "selection": {"run_id": self.detail_run},
                "window_assessment": {"id": "wa-1", "result": {}}, "coverage": {"roles": []}, "intervals": []}

    def accepted_fingerprint(self, t, s, lo, hi):
        return self.fingerprints.pop(0)

    def site_window(self, t, s, start, end):
        return {"coverage": []}

    def records_page(self, t, s, **kw):
        return {"total": 0, "rows": []}

    def finding_detail(self, t, s, fid):
        key = str(fid)
        if key not in self.revisions:
            return None
        return {"finding": {}, "revisions": self.revisions[key],
                "relations": {"merged_into": [{"canonical": "x"}] if key in self.merged else []}}

    def read(self, t, s, fid, rid, *, finding_revision_is_latest, source_open, limit):
        body = self.bodies.get(str(fid)) or priced(str(fid), str(rid))
        if not source_open:
            body = {**body, "currentness": {**body["currentness"], "state": "AUDIT_ONLY", "current_amount_shown": False}}
        return body

    def service(self, **kw) -> SiteOverviewRead:
        return SiteOverviewRead(self.upstream, self, self, self, **kw)


def run(world: World, *, source_open=True, pinned=None, **kw) -> dict:
    return world.service(**kw).read("KOBO-001", T, S, DAY, access_basis="DEV", source_open=source_open,
                                    source_reason="test", pinned=pinned)


# ---- Finding choice (D-2026-10-15-s501-finding-choice) ----

def test_half_open_intersection_excludes_an_episode_ending_exactly_at_midnight() -> None:
    assert not intersects(D0 - timedelta(hours=2), D0, D0, D0 + timedelta(days=1))
    assert intersects(D0 - timedelta(hours=2), D0 + timedelta(seconds=1), D0, D0 + timedelta(days=1))
    assert not intersects(D0 + timedelta(days=1), D0 + timedelta(days=1, hours=1), D0, D0 + timedelta(days=1))
    edge = finding(D0 - timedelta(hours=3), D0)
    body = run(World([edge]))
    assert body["known_finding"] is None and body["money"]["state"] == ms.ABSENT


def test_greatest_start_then_smallest_uuid_and_one_finding_never_a_sum() -> None:
    a = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=7), "bbbbbbbb-0000-0000-0000-000000000000")
    b = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8), "aaaaaaaa-0000-0000-0000-000000000000")
    c = finding(D0 + timedelta(hours=1), D0 + timedelta(hours=2))
    assert choose([a, b, c])["finding_id"] == b["finding_id"]
    body = run(World([a, b, c]))
    known = body["known_finding"]
    assert (known["id"], known["revision_id"], known["several_intersect"]) == (
        b["finding_id"], b["finding_revision_id"], True)
    assert "only" in known["note"] and body["finding_list"]["state"] == "UNAVAILABLE"
    assert body["money"]["amount_high"] == "15.82"  # this Finding's display bound, not a sum of three


def test_merge_superseded_finding_is_excluded_and_lifecycle_is_not_a_filter() -> None:
    merged = finding(D0 + timedelta(hours=9), D0 + timedelta(hours=10))
    kept = finding(D0 + timedelta(hours=2), D0 + timedelta(hours=3))
    kept["lifecycle"] = "CLOSED"
    body = run(World([merged, kept], merged={merged["finding_id"]}))
    assert body["known_finding"]["id"] == kept["finding_id"]
    assert body["known_finding"]["excluded"] == [{"finding_id": merged["finding_id"], "reason": "SUPERSEDED_BY_MERGE"}]


def test_priced_reads_exact_head_display_amounts_and_exact_links() -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    money = run(World([f]))["money"]
    assert money["state"] == ms.PRICED
    assert (money["amount_low"], money["amount_high"], money["currency"]) == ("0.00", "15.82", "USD")
    assert money["consequence_revision_id"] == "c-head" and money["finding_revision_id"] == f["finding_revision_id"]
    assert money["links"]["consequence"].endswith(
        f"revision_id={f['finding_revision_id']}&consequence_revision_id=c-head")
    assert money["links"]["price_revision"] == "/api/sites/KOBO-001/financial-assumptions/p-1"
    assert money["eligibility"]["state"] == "ELIGIBLE"


@pytest.mark.parametrize("change, state", [
    (dict(head="c-newer"), ms.CONSEQUENCE_STALE),  # the exact read observed a different head than the seam
    (dict(state="STALE", shown=False), ms.CONSEQUENCE_STALE),
    (dict(state="PENDING", shown=False), ms.CONSEQUENCE_PENDING),
    (dict(gate="WITHHELD_GENERATOR_SERIES", shown=False), ms.WITHHELD_GENERATOR_SERIES),
    (dict(gate="PENDING_REASSESSMENT", shown=False), ms.PENDING_REASSESSMENT),
    (dict(quantity="QUANTITY_UNAVAILABLE", price="NOT_EVALUATED", row_state="QUANTITY_UNAVAILABLE", shown=False),
     ms.QUANTITY_UNAVAILABLE),
    (dict(price="UNPRICED", row_state="UNPRICED", shown=False), ms.UNPRICED),
    (dict(currency="XXX"), ms.MINOR_UNIT_UNKNOWN),
])
def test_no_amount_states_from_the_exact_read(change, state) -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    body = run(World([f], bodies={f["finding_id"]: priced(f["finding_id"], f["finding_revision_id"], **change)}))
    money = body["money"]
    assert money["state"] == state
    assert money["amount_low"] is None and money["amount_high"] is None
    assert body["known_finding"]["id"] == f["finding_id"]  # the selected Finding and links stay


def test_seam_that_does_not_permit_the_amount_fails_closed() -> None:
    """LR-01 fix round: the seam's own `current_amount_permitted` is a further conjunct, never a bypass."""
    f = {**finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8)), "current_amount_permitted": False,
         "upstream_status": {"status": "BLOCKED", "reasons": [{"stage": "CONSEQUENCE", "code": "CONSEQUENCE_STALE"}]}}
    money = run(World([f]))["money"]
    assert money["state"] == ms.CONSEQUENCE_STALE
    assert money["amount_low"] is None and money["amount_high"] is None
    assert money["seam_current_amount_permitted"] is False


def test_unverified_demonstration_source_gives_no_amount(monkeypatch) -> None:
    def unreadable():
        raise demonstration_label.SpecUnreadable("missing")
    monkeypatch.setattr(demonstration_label, "_declared", unreadable)
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    money = run(World([f]))["money"]
    assert money["state"] == ms.MIXED_OR_UNKNOWN_SOURCE and money["amount_high"] is None
    assert money["demonstration"]["case_id"] == "unverified"


def test_stopped_schedule_keeps_the_raw_gate_eligible_and_blocks_the_amount_upstream() -> None:
    """Architect LR-01 deviations item 2: the raw gate stays ELIGIBLE; S5's upstream status blocks the amount."""
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    stopped = {"status": "STALE_PROJECTION", "stage": "SCHEDULE", "reasons": ["SCHEDULE_STOPPED"], "errors": []}
    body = run(World([f], eligibility=stopped))
    money = body["money"]
    assert money["eligibility"]["state"] == "ELIGIBLE"
    assert money["state"] == ms.UPSTREAM_STALE and money["amount_high"] is None
    assert money["upstream"]["reasons"] == ["SCHEDULE_STOPPED"]
    assert body["freshness"]["state"] == "STALE_PROJECTION" and "SCHEDULE_STOPPED" in body["freshness"]["reasons"]


@pytest.mark.parametrize("status, state", [("FAILED", ms.UPSTREAM_FAILED), ("PENDING", ms.UPSTREAM_PENDING),
                                           ("UNASSESSED", ms.UPSTREAM_UNASSESSED)])
def test_upstream_states_give_no_amount(status, state) -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    elig = {"status": status, "stage": "S3", "reasons": [f"S3_{status}"], "errors": []}
    assert run(World([f], eligibility=elig))["money"]["state"] == state


def test_timeline_interval_uses_its_stored_span_not_the_day_window() -> None:
    world = World()
    detail = world.detail(T, S, DAY)
    detail["intervals"] = [{"id": "iv-1", "window_start": D0, "window_end": D0 + timedelta(days=1),
                            "claim_level": "CANDIDATE_AVOIDABLE", "assessment_key": "k",
                            "result": {"interval": {"first_on": "2026-10-24T06:05:00.000000Z",
                                                    "last_on": "2026-10-24T08:00:00.000000Z"}}}]
    world.upstream.dispatch_read.window = lambda t, s, day: detail
    (iv,) = run(world)["assessment"]["dispatch_intervals"]
    assert (iv["start"], iv["end"]) == ("2026-10-24T06:05:00Z", "2026-10-24T08:00:00Z")
    assert iv["window"] == {"start": "2026-10-24T00:00:00Z", "end": "2026-10-25T00:00:00Z"}


def test_unassessed_day_is_unknown_and_never_absent() -> None:
    elig = {"status": "UNASSESSED", "stage": "S3", "reasons": ["S3_UNASSESSED"], "errors": []}
    body = run(World([], eligibility=elig, day_run=None, detail_run=None))
    assert body["assessment"]["state"] == "UNKNOWN"
    assert body["money"]["state"] == ms.UPSTREAM_UNASSESSED and body["freshness"]["state"] == "UNASSESSED"
    assert body["known_finding"] is None


def test_moved_accepted_source_or_selection_is_never_current() -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    moved = run(World([f], fingerprints=[{"count": 3, "sha256": "x"}, {"count": 4, "sha256": "y"}]))
    assert moved["money"]["state"] == ms.UPSTREAM_PENDING and moved["money"]["amount_high"] is None
    assert moved["freshness"]["state"] == "STALE_PROJECTION"
    assert "ACCEPTED_SOURCE_MOVED_DURING_READ" in moved["freshness"]["reasons"]
    reselected = run(World([f], detail_run="run-2"))
    assert reselected["money"]["state"] == ms.UPSTREAM_PENDING
    assert "SELECTION_MOVED_DURING_READ" in reselected["freshness"]["reasons"]


def test_pinned_finding_is_retained_while_the_basis_moves_and_replaced_once_settled() -> None:
    old = finding(D0 + timedelta(hours=1), D0 + timedelta(hours=2))
    new = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    pending = {"status": "PENDING", "stage": "S4", "reasons": ["MATCH_PENDING"], "errors": []}
    world = World([old, new], eligibility=pending)
    held = run(world, pinned=(UUID(old["finding_id"]), UUID(old["finding_revision_id"])))
    assert held["known_finding"]["id"] == old["finding_id"]
    assert held["known_finding"]["selected_by"] == "PINNED_RETAINED_WHILE_BASIS_INCOMPLETE"
    assert held["money"]["state"] == ms.UPSTREAM_PENDING and held["money"]["amount_high"] is None
    settled = run(World([old, new]), pinned=(UUID(old["finding_id"]), UUID(old["finding_revision_id"])))
    assert settled["known_finding"]["id"] == new["finding_id"]
    assert settled["known_finding"]["previous_pin"] == {
        "finding_id": old["finding_id"], "finding_revision_id": old["finding_revision_id"],
        "reason": "SETTLED_CHOICE_IS_ANOTHER_FINDING"}
    with pytest.raises(LookupError):
        run(world, pinned=(uuid4(), None))


def test_source_closed_keeps_only_pinned_audit_material() -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    closed = run(World([f]), source_open=False)
    assert closed["known_finding"] is None and closed["money"]["state"] == ms.SOURCE_CLOSED
    assert closed["assessment"]["state"] == "CLOSED" and closed["assessment"]["run_id"] is None
    assert closed["freshness"]["state"] != "CURRENT" and closed["freshness"]["source_open"] is False
    # Review M2: while closed, an ID-only pin is not resolved to the latest revision.
    bare = run(World([f]), source_open=False, pinned=(UUID(f["finding_id"]), None))
    assert bare["known_finding"] is None and bare["money"]["state"] == ms.SOURCE_CLOSED
    assert bare["previous_pin"]["reason"] == "EXACT_REVISION_REQUIRED_WHILE_SOURCE_CLOSED"
    other = finding(D0 + timedelta(hours=7), D0 + timedelta(hours=9))
    third = finding(D0 + timedelta(hours=8), D0 + timedelta(hours=10))
    pinned = run(World([f, other, third], merged={third["finding_id"]}), source_open=False,
                 pinned=(UUID(f["finding_id"]), UUID(f["finding_revision_id"])))
    assert pinned["known_finding"]["audit_only"] is True and pinned["known_finding"]["id"] == f["finding_id"]
    assert pinned["known_finding"]["revision_id"] == f["finding_revision_id"]
    # nothing from the unpinned current discovery while the pin is retained
    assert pinned["known_finding"]["several_intersect"] is False and pinned["known_finding"]["excluded"] == []
    assert pinned["money"]["state"] == ms.SOURCE_CLOSED and pinned["money"]["amount_high"] is None


def test_a_pin_from_another_day_is_dropped_and_reported() -> None:
    """Review M1: another day's Finding never stands in for the selected day, even while the basis is incomplete."""
    elsewhere = finding(D0 - timedelta(days=5), D0 - timedelta(days=5) + timedelta(hours=2))
    today = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    pin = (UUID(elsewhere["finding_id"]), UUID(elsewhere["finding_revision_id"]))
    pending = {"status": "PENDING", "stage": "S4", "reasons": ["MATCH_PENDING"], "errors": []}
    for world, source_open in ((World([elsewhere, today], eligibility=pending), True),
                               (World([elsewhere, today]), False)):
        body = run(world, source_open=source_open, pinned=pin)
        assert body["known_finding"] is None or body["known_finding"]["id"] != elsewhere["finding_id"]
        assert body["previous_pin"] == {"finding_id": elsewhere["finding_id"],
                                        "finding_revision_id": elsewhere["finding_revision_id"],
                                        "reason": "NOT_IN_SELECTED_DAY"}
        assert body["money"]["amount_high"] is None
    settled = run(World([elsewhere, today]), pinned=pin)
    assert settled["known_finding"]["id"] == today["finding_id"]
    assert settled["known_finding"]["previous_pin"]["reason"] == "NOT_IN_SELECTED_DAY"


def test_pin_dropped_when_settled_discovery_finds_no_finding() -> None:
    """Review L3: a pin that settled discovery no longer selects is reported, never dropped silently."""
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    body = run(World([f], merged={f["finding_id"]}), pinned=(UUID(f["finding_id"]), UUID(f["finding_revision_id"])))
    assert body["known_finding"] is None and body["money"]["state"] == ms.ABSENT
    assert body["previous_pin"]["reason"] == "SETTLED_DISCOVERY_FOUND_NO_FINDING"


def test_unreadable_seam_finding_is_not_called_merged() -> None:
    """Review L7."""
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    world = World([f])
    world.revisions.pop(f["finding_id"])
    body = run(world)
    assert body["known_finding"] is None


# ---- precedence (mutation-checked) ----

def _inputs(**kw):
    base = dict(source_open=True, upstream_status="CURRENT", discovery_complete=True, finding_selected=True,
                eligibility="ELIGIBLE", revision_is_latest=True, consequence_state="CURRENT", head_matches_seam=True,
                consequence_row_state="PRICED", quantity_state="AVAILABLE", price_state="PRICED",
                display_state="ROUNDED_OUTWARD", presented_as_current=True)
    base.update(kw)
    return ms.MoneyInputs(**base)


def test_precedence_order() -> None:
    assert ms.money_state(_inputs()) == ms.PRICED
    worst = dict(source_open=False, upstream_status="FAILED", upstream_reasons=("S3_FAILED",),
                 eligibility="PENDING_REASSESSMENT", revision_is_latest=False, consequence_state="STALE",
                 quantity_state="QUANTITY_UNAVAILABLE", price_state="UNPRICED", display_state=None,
                 provenance_resolved=False)
    order = [("source_open", ms.SOURCE_CLOSED), ("upstream_status", ms.UPSTREAM_FAILED),
             ("eligibility", ms.PENDING_REASSESSMENT), ("revision_is_latest", ms.SUPERSEDED),
             ("consequence_state", ms.CONSEQUENCE_STALE), ("quantity_state", ms.QUANTITY_UNAVAILABLE),
             ("price_state", ms.UNPRICED), ("display_state", ms.MINOR_UNIT_UNKNOWN),
             ("provenance_resolved", ms.MIXED_OR_UNKNOWN_SOURCE)]
    good = _inputs()
    for i, (name, expected) in enumerate(order):
        kw = {k: v for k, v in worst.items()}
        for done, _ in order[:i]:
            kw[done] = getattr(good, done)
        kw.pop("upstream_reasons", None) if i > 1 else None
        assert ms.money_state(_inputs(**kw)) == expected, name
    assert ms.money_state(_inputs(eligibility="WITHHELD_GENERATOR_SERIES", revision_is_latest=False)) == \
        ms.WITHHELD_GENERATOR_SERIES
    assert ms.money_state(_inputs(eligibility=None)) == ms.PENDING_REASSESSMENT
    assert ms.money_state(_inputs(finding_selected=False)) == ms.ABSENT
    assert ms.money_state(_inputs(finding_selected=False, discovery_complete=False)) == ms.UPSTREAM_PENDING
    assert ms.money_state(_inputs(presented_as_current=False)) == ms.CONSEQUENCE_STALE
    assert ms.money_state(_inputs(head_matches_seam=False)) == ms.CONSEQUENCE_STALE
    # consequence-only upstream blockers fall through to the Finding but never price
    assert ms.money_state(_inputs(upstream_status="STALE_PROJECTION", upstream_reasons=("WORK_OUTSTANDING",))) == \
        ms.CONSEQUENCE_STALE
    assert ms.money_state(_inputs(upstream_status="STALE_PROJECTION",
                                  upstream_reasons=("WORK_OUTSTANDING", "SCHEDULE_STOPPED"))) == ms.UPSTREAM_STALE
    assert ms.money_state(_inputs(basis_moved=True)) == ms.UPSTREAM_PENDING


# ---- route: access, scope, S2 comparison, Performance gate, UTC day ----

class Imported:
    def __init__(self, passed: bool) -> None:
        self.passed = passed

    def scope(self, code):
        if not self.passed:
            raise AwaitingComparison("no passing comparison")
        return types.SimpleNamespace(site_code=code)


class LegacySites:
    def get_site(self, code):
        raise SiteNotFound(code)


def client(world: World, *, access=None, passed=True, gate=True) -> tuple[TestClient, list]:
    calls: list = []

    def gate_fn(code, t, s):
        calls.append(code)
        return gate, "test gate open" if gate else "test gate closed"

    overview = SiteOverviewRoute(world.service(), {"KOBO-001": ("KOBO-001", T, S)}.get, gate_fn,
                                 access or (lambda request, code: None), "DEV-BASIS")
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), LegacySites(),
                                             imported_reads=Imported(passed), site_overview=overview))
    return TestClient(app), calls


def test_route_access_refusals_come_before_discovery() -> None:
    world = World()
    for code in (401, 403):
        c, calls = client(world, access=lambda request, site, code=code: code)
        assert c.get("/api/sites/KOBO-001/overview").status_code == code
        assert c.get("/api/sites/UNKNOWN/overview").status_code == code  # no discovery before refusal
        assert calls == []


def test_route_s2_comparison_gates_the_whole_imported_overview_even_with_performance_open() -> None:
    c, calls = client(World(), passed=False)
    response = c.get("/api/sites/KOBO-001/overview?date=2026-10-24")
    assert response.status_code == 409 and response.json()["detail"]["code"] == "AWAITING_EVIDENCE_MIGRATION"
    assert calls == []


def test_route_performance_closed_with_comparison_passed_and_both_open() -> None:
    f = finding(D0 + timedelta(hours=6), D0 + timedelta(hours=8))
    closed, _ = client(World([f]), gate=False)
    body = closed.get("/api/sites/KOBO-001/overview?date=2026-10-24").json()
    assert body["freshness"]["source_open"] is False and body["money"]["state"] == "SOURCE_CLOSED"
    assert body["access_basis"] == "DEV-BASIS" and body["schema_version"] == "site-window-summary-1"
    opened, _ = client(World([f]))
    body = opened.get("/api/sites/KOBO-001/overview?date=2026-10-24").json()
    assert body["money"]["state"] == "PRICED" and body["window"]["utc_date"] == "2026-10-24"


def test_route_day_selection_default_and_validation() -> None:
    c, _ = client(World())
    assert c.get("/api/sites/KOBO-001/overview").json()["window"]["utc_date"] == "2026-10-24"  # DB-clock day
    same = c.get("/api/sites/KOBO-001/overview?from=2026-10-24T00:00:00Z&to=2026-10-25T00:00:00Z")
    assert same.status_code == 200 and same.json()["window"]["start"] == "2026-10-24T00:00:00Z"
    for query, code in [("date=2026-10-2", "INVALID_WINDOW"), ("date=2026-02-30", "INVALID_WINDOW"),
                        ("from=2026-10-24T00:00:00Z", "PARTIAL_WINDOW"),
                        ("from=2026-10-24T01:00:00Z&to=2026-10-25T01:00:00Z", "NOT_ONE_UTC_DAY"),
                        ("from=2026-10-24T00:00:00Z&to=2026-10-26T00:00:00Z", "NOT_ONE_UTC_DAY"),
                        ("from=2026-10-24T00:00:00%2B01:00&to=2026-10-25T00:00:00Z", "INVALID_WINDOW"),
                        ("date=2026-10-23&from=2026-10-24T00:00:00Z&to=2026-10-25T00:00:00Z", "CONFLICTING_WINDOW"),
                        ("finding_revision_id=" + str(uuid4()), "INVALID_FINDING_PIN")]:
        response = c.get(f"/api/sites/KOBO-001/overview?{query}")
        assert (response.status_code, response.json()["detail"]["code"]) == (422, code), query
    assert c.get(f"/api/sites/KOBO-001/overview?date=2026-10-24&finding_id={uuid4()}").status_code == 404


def test_route_store_outage_is_a_typed_503_and_internal_errors_are_not_pin_misses() -> None:
    """Review L1 (the legacy handler's 503 kept) and L2 (only a real pin miss is 404)."""
    from assetops_backend.sites.ports import SiteStoreUnavailable

    def down(code):
        raise SiteStoreUnavailable("site store down")

    overview = SiteOverviewRoute(World().service(), down, lambda c, t, s: (True, "open"), lambda r, c: None, "DEV")
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), LegacySites(),
                                             imported_reads=Imported(True), site_overview=overview))
    response = TestClient(app).get("/api/sites/KOBO-001/overview")
    assert (response.status_code, response.json()["detail"]["code"]) == (503, "SITE_STORE_UNAVAILABLE")
    broken = World()
    window = broken.window
    broken.upstream.window = lambda *a: {k: v for k, v in window(*a).items() if k != "schedule"}
    c, _ = client(broken)
    with pytest.raises(KeyError):
        c.get("/api/sites/KOBO-001/overview?date=2026-10-24")


def test_route_no_comparison_reader_foreign_site_and_legacy_date(monkeypatch) -> None:
    """Review L6: no S2 comparison reader is 409; a Site outside this tenant's ledger scope is never read as
    imported; a legacy Site's `date=` reaches the legacy model as the midnight pair."""
    import assetops_backend.evidence_api as api

    seen: list = []

    class Legacy:
        def __init__(self, *a, **k):
            pass

        def site_overview(self, site, start, end):
            seen.append((start, end))
            return {"legacy": True}

    class OneLegacySite:
        def get_site(self, code):
            if code != "LEGACY-1":
                raise SiteNotFound(code)
            return types.SimpleNamespace(site_id=code)

    monkeypatch.setattr(api, "OverviewReadModel", Legacy)
    world = World()
    overview = SiteOverviewRoute(world.service(), {"KOBO-001": ("KOBO-001", T, S)}.get,
                                 lambda c, t, s: (True, "open"), lambda r, c: None, "DEV")
    app = FastAPI()
    app.include_router(build_evidence_router(types.SimpleNamespace(store=None), OneLegacySite(),
                                             imported_reads=None, site_overview=overview))
    c = TestClient(app)
    response = c.get("/api/sites/KOBO-001/overview?date=2026-10-24")
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "AWAITING_EVIDENCE_MIGRATION")
    assert c.get("/api/sites/OTHER-TENANT-SITE/overview?date=2026-10-24").status_code == 404
    assert c.get("/api/sites/LEGACY-1/overview?date=2026-10-24").json() == {"legacy": True}
    assert seen == [("2026-10-24T00:00:00Z", "2026-10-25T00:00:00Z")]


def test_selected_day_and_legacy_translation() -> None:
    assert selected_day({}) is None
    assert selected_day({"date": "2026-10-24"}) == DAY
    assert SiteOverviewRoute.legacy_window({"date": "2026-10-24"}) == ("2026-10-24T00:00:00Z", "2026-10-25T00:00:00Z")
    assert SiteOverviewRoute.legacy_window({}) is None
