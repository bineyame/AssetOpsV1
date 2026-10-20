"""W3-01 commit 2: the estate Finding/Action/scope read over one read-only REPEATABLE READ snapshot.

Real persisted chains only: the W2-02/W2-03 cold `late-reading` replay (authenticated intake and the real cold
worker), the W2-05/W2-06 EV replay, and the S4/S6 mini-grid Finding and Action chain. Every body is read through
the local estate router (`estate_api.build_estate_router`); Lane A mounts it in `main.py`. Needs
ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from urllib.parse import urlencode

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401 - the W2-02 replay fixture
    from test_w203_cold_replay_postgres import opened, run

    from test_s1_bindings_postgres import engine, store  # noqa: F401 - the S4/S6 mini-grid fixtures
    from test_s4_consequence_store_postgres import POWER_DAY, STATE_DAY, PowerSite
    from test_s4_finding_store_postgres import CaseRunner, run_case
    from test_s6_action_store_postgres import CASES as S4_CASES

    import pg_harness
    from assetops_backend.analytics.adapters.postgres_assessment_store import (
        PostgresAssessmentStore, selected_windows_on)
    from assetops_backend.estate.adapters import postgres_estate_read
    from assetops_backend.estate.composition import build_estate_read
    from assetops_backend.estate.index import EstateIndexService
    from assetops_backend.estate.scope import decode_cursor, encode_cursor
    from assetops_backend.estate_api import build_estate_router

DAY = datetime(2026, 10, 6, tzinfo=timezone.utc)
COLD_ANALYTICS = ("cold-excursion", "cold-start-response")
ESTATE_KEYS = {"classification", "state", "source_ids", "evidence_ids", "basis_sha256", "reasons"}


def iso(at: datetime) -> str:
    return at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


class Estate:
    """The estate router over one engine, with the tenant and access seams of a test."""

    def __init__(self, engine, tenant_id, admit=lambda code: True) -> None:
        self.read = build_estate_read(engine.url.render_as_string(hide_password=False))
        self.read._engine = engine
        self.service = EstateIndexService(self.read)
        self.admit = admit
        app = FastAPI()
        app.include_router(build_estate_router(self.service, lambda: tenant_id,
                                               access=lambda request, code: None if self.admit(code) else 403))
        self.client = TestClient(app)

    def get(self, root: str, **params):
        return self.client.get(f"/api/estate/{root}?" + urlencode(params))

    def ok(self, root: str, **params) -> dict:
        response = self.get(root, **params)
        assert response.status_code == 200, response.text
        return response.json()

    def windows(self, tenant_id, site_id, domain, from_, to, known_at) -> list[dict]:
        """The selected windows the estate snapshot pins, read through the same adapter and transaction."""
        def work(snap):
            snap.historical = known_at < snap.read_at
            cutoff = snap.evidence_cutoff(tenant_id, site_id, known_at)
            return snap.selected_windows(tenant_id, site_id, domain, from_, to, cutoff, known_at)
        return self.read.read(work)


def db_now(engine) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT clock_timestamp()")).scalar_one()


def watermark(engine, site_id) -> datetime:
    with engine.connect() as c:
        return c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s"),
                         {"s": site_id}).scalar_one()


def imported_before(engine, tenant_id, site_id, at: datetime) -> None:
    """TEST-SCOPED: the replay imports its Site at today's DB time; the estate scope admits a Site only when its
    committed import precedes the requested `to`. Re-date the fixture import so the replay's 2026-10-06 day is a
    valid estate window (the scope rule itself is proven unchanged in the scope test). Run 8 fixture ruling (a):
    the update is constrained to this tenant and Site in the test's private DB; production import is untouched."""
    with engine.begin() as c:
        done = c.execute(text("UPDATE site_import SET imported_at = :at WHERE tenant_id = :t AND site_id = :s"),
                         {"at": at, "t": tenant_id, "s": site_id})
        assert done.rowcount == 1


def test_cold_ev_cutoff_precedes_reselection_and_revision(chain) -> None:  # noqa: F811
    """Run 7 q7 historical reselection proof at the estate level (cold): a later selection of the same stored
    window, with new assessment revisions, does not move an explicit earlier cutoff's rows, IDs or token."""
    built = opened("late-reading", chain)
    run(built)
    imported_before(built.engine, built.tenant_id, built.site_id, DAY - timedelta(days=1))
    estate = Estate(built.engine, built.tenant_id)
    t, s = built.tenant_id, built.site_id
    wm1, k1 = watermark(built.engine, s), db_now(built.engine)
    window = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    first = estate.ok("findings", **window, known_at=iso(k1))
    pinned = estate.windows(t, s, "cold_chain", DAY, DAY + timedelta(days=1), k1)
    built.advance_late()
    run(built)  # a later selection of the same stored window, with new assessment revisions
    again = estate.ok("findings", **window, known_at=iso(k1))
    repinned = estate.windows(t, s, "cold_chain", DAY, DAY + timedelta(days=1), k1)
    later = estate.ok("findings", **window)
    current = estate.windows(t, s, "cold_chain", DAY, DAY + timedelta(days=1), db_now(built.engine))
    assert first["status"] == again["status"] == "HISTORICAL"
    assert [x["state"] for x in again["coverage"]["sites"]] == ["HISTORICAL"]
    assert [x["state"] for x in later["coverage"]["sites"]] == ["CURRENT"] and later["status"] == "CURRENT"
    assert again["selection_token"] == first["selection_token"] and again["rows"] == first["rows"]
    assert again["coverage"] == first["coverage"]
    assert [(w["seq"], w["selection_id"]) for w in repinned] == [(w["seq"], w["selection_id"]) for w in pinned]
    assert pinned and all(w["selected_at"] > wm1 for w in pinned)
    assert [w["seq"] for w in current] != [w["seq"] for w in pinned]
    assert set(current[0]["assessment_revision_ids"]).isdisjoint(pinned[0]["assessment_revision_ids"])
    assert later["selection_token"] != first["selection_token"]
    # Selecting with the evidence watermark as the selected_at bound would select nothing (q7-1).
    with built.engine.connect() as c:
        assert selected_windows_on(c, t, s, COLD_ANALYTICS, DAY, DAY + timedelta(days=1), wm1) == []
    for body in (first, again, later):
        for row in body["rows"]:
            assert set(row["source_provenance"]) == ESTATE_KEYS


def cold_estate(chain):  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    imported_before(built.engine, built.tenant_id, built.site_id, DAY - timedelta(days=1))
    return built, Estate(built.engine, built.tenant_id)


def stored_cold_heads(engine, site_id) -> dict[str, str]:
    """Each cold Finding's latest stored revision (independent of the estate code)."""
    with engine.connect() as c:
        return {str(r[0]): str(r[1]) for r in c.execute(text(
            "SELECT DISTINCT ON (f.id) f.id, r.id FROM finding f JOIN finding_revision r ON r.finding_id = f.id "
            "WHERE f.site_id = :s AND f.domain = 'cold_chain' ORDER BY f.id, r.revision_no DESC"), {"s": site_id})}


def add_empty_site(engine, site_id, code: str) -> str:
    """TEST-SCOPED: a second imported Site of the same tenant with no selection (`W301-EMPTY-001`), copied from the
    replay Site's stored row with a new identity, and its own committed import."""
    new = str(uuid4())
    with engine.begin() as c:
        cols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'site' ORDER BY ordinal_position"))]
        pick = {"id": "CAST(:new AS uuid)", "site_code": ":code", "site_code_key": "lower(:code)",
                "name": "'Empty test Site'"}
        c.execute(text(f"INSERT INTO site ({', '.join(cols)}) SELECT {', '.join(pick.get(x, x) for x in cols)} "
                       "FROM site WHERE id = :s"), {"new": new, "code": code, "s": site_id})
        cols = [r[0] for r in c.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'site_import' "
            "ORDER BY ordinal_position"))]
        pick = {"id": "CAST(:imp AS uuid)", "site_id": "CAST(:new AS uuid)"}
        c.execute(text(f"INSERT INTO site_import ({', '.join(cols)}) SELECT {', '.join(pick.get(x, x) for x in cols)} "
                       "FROM site_import WHERE site_id = :s LIMIT 1"), {"imp": str(uuid4()), "new": new, "s": site_id})
    return new


def test_cold_ev_day_intersection_selects_exact_windows(chain) -> None:  # noqa: F811
    """Run 6 Blocker 1 (cold): the whole UTC day selects the exact hour-scale stored window, CURRENT, with the
    selected rows, IDs, six-key provenance and full-set counts."""
    built, estate = cold_estate(chain)
    day = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    body = estate.ok("findings", **day)
    (pinned,) = estate.windows(built.tenant_id, built.site_id, "cold_chain", DAY, DAY + timedelta(days=1),
                               db_now(built.engine))
    (site,) = body["coverage"]["sites"]
    assert body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
    assert site == {"site_id": str(built.site_id), "state": "CURRENT", "selection_id": pinned["selection_id"],
                    "committed_watermark": site["committed_watermark"], "match_state": "NOT_APPLICABLE",
                    "job_state": "SETTLED", "source_freshness": "RECENT"}
    assert body["scope"]["authorized_site_count"] == body["scope"]["covered_site_count"] == 1
    heads = stored_cold_heads(built.engine, built.site_id)
    assert body["rows"] and {r["finding_id"]: r["finding_revision_id"] for r in body["rows"]} == heads
    assert body["total_count"] == len(body["rows"]) == len(heads)
    assert body["summary"]["basis_count"] == len(heads)
    assert body["summary"]["supported_findings"] == sum(r["lifecycle"] == "SUPPORTED" for r in body["rows"])
    assert body["summary"]["high_priority"] is None and body["summary"]["low_confidence"] is None
    for row in body["rows"]:
        assert set(row["source_provenance"]) == ESTATE_KEYS and row["source_provenance"]["basis_sha256"]
        assert row["consequence"]["state"] == "UNPRICED" and row["consequence"]["amount"] is None
        assert row["consequence"]["amount_low"] is None and row["consequence"]["amount_high"] is None
        assert row["lens_flags"] == [] and row["priority"] is None and row["confidence"] is None
        assert row["finding_label"] == f"Finding {row['finding_id'][:8]}" and row["status"] == "CURRENT"
    order = [(-datetime.fromisoformat(r["episode_start"].replace("Z", "+00:00")).timestamp(), r["finding_id"])
             for r in body["rows"]]
    assert order == sorted(order)
    for lens in ("cost", "risks", "opportunities"):  # cold is unpriced; no stored risk/opportunity kind
        empty = estate.ok("findings", **day, lens=lens)
        assert empty["rows"] == [] and empty["total_count"] == 0 and empty["summary"]["basis_count"] == 0
    scope = estate.ok("scope", **day)
    assert scope["sites"] == [{"site_id": str(built.site_id), "site_code": scope["sites"][0]["site_code"],
                               "site_name": scope["sites"][0]["site_name"], "coverage_state": "CURRENT"}]
    assert scope["access_basis"] == body["scope"]["access_basis"]


def test_cold_ev_window_outside_day_is_unknown(chain) -> None:  # noqa: F811
    """No selected window intersecting the requested days is UNKNOWN with null totals, never a zero."""
    built, estate = cold_estate(chain)
    body = estate.ok("findings", **{"from": iso(DAY + timedelta(days=2)), "to": iso(DAY + timedelta(days=3))})
    (site,) = body["coverage"]["sites"]
    assert body["status"] == "UNKNOWN" and body["coverage"]["state"] == "UNKNOWN" and site["state"] == "UNKNOWN"
    assert site["selection_id"] is None and body["scope"]["covered_site_count"] == 0
    assert body["rows"] == [] and body["total_count"] is None
    assert all(v is None for v in body["summary"].values())


def test_scope_excludes_foreign_and_keeps_missing_site(chain) -> None:  # noqa: F811
    built, estate = cold_estate(chain)
    empty = add_empty_site(built.engine, built.site_id, "W301-EMPTY-001")
    day = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    body = estate.ok("findings", **day)
    states = {x["site_id"]: x["state"] for x in body["coverage"]["sites"]}
    assert states == {str(built.site_id): "CURRENT", empty: "UNKNOWN"}
    assert body["scope"]["authorized_site_count"] == 2 and body["scope"]["covered_site_count"] == 1
    assert body["coverage"]["state"] == "PARTIAL" and body["status"] == "UNKNOWN"
    assert body["total_count"] is None and all(v is None for v in body["summary"].values())
    assert body["rows"] and {r["site_id"] for r in body["rows"]} == {str(built.site_id)}  # settled rows stay
    # The committed-import rule: a Site imported at or after `to` is outside the scope.
    imported_before(built.engine, built.tenant_id, empty, DAY + timedelta(days=1))
    assert estate.ok("findings", **day)["scope"]["authorized_site_count"] == 1
    imported_before(built.engine, built.tenant_id, empty, DAY - timedelta(days=1))
    # A denied candidate never enters a row, count, coverage entry or digest.
    estate.admit = lambda code: code == "W301-EMPTY-001"
    denied = estate.get("findings", **day)
    assert denied.status_code == 200 and str(built.site_id) not in denied.text
    assert denied.json()["scope"]["authorized_site_count"] == 1 and denied.json()["rows"] == []
    assert denied.json()["scope"]["access_basis"] != body["scope"]["access_basis"]
    # A foreign tenant sees a complete empty estate: zero only after a complete read.
    foreign = Estate(built.engine, uuid4())
    for root in ("findings", "actions"):
        other = foreign.ok(root, **day)
        assert other["scope"]["authorized_site_count"] == 0
        assert other["coverage"] == {"state": "COMPLETE", "sites": []}
        assert other["rows"] == [] and other["total_count"] == 0 and str(built.site_id) not in str(other)
    assert foreign.ok("scope", **day)["sites"] == []
    # Cold Sites are NOT_APPLICABLE for Actions and do not make the Action cards partial.
    estate.admit = lambda code: True
    actions = estate.ok("actions", **day)
    assert {x["state"] for x in actions["coverage"]["sites"]} == {"NOT_APPLICABLE"}
    assert actions["coverage"]["state"] == "COMPLETE" and actions["summary"]["open_actions"] == 0
    assert actions["summary"]["due_overdue"] is None and actions["total_count"] == 0


def test_cursor_scope_window_lens_and_fence(chain) -> None:  # noqa: F811
    built, estate = cold_estate(chain)
    day = {"from": iso(DAY), "to": iso(DAY + timedelta(days=1))}
    whole = estate.ok("findings", **day)
    first = estate.ok("findings", **day, limit=1)
    assert len(whole["rows"]) >= 2 and first["next_cursor"] and first["rows"] == whole["rows"][:1]
    second = estate.ok("findings", **day, limit=1, cursor=first["next_cursor"])
    assert second["selection_token"] == first["selection_token"] and first["summary"] == whole["summary"]
    # Page two reads at the cursor cutoff, so its rows are labelled HISTORICAL; nothing else in them moves.
    assert [{**r, "status": None} for r in second["rows"]] == [{**r, "status": None} for r in whole["rows"][1:2]]
    assert {r["status"] for r in second["rows"]} == {"HISTORICAL"}
    # Run 8 ruling 2: the cursor's six-digit cutoff is page two's only cutoff, even when page one omitted it. Page
    # two is HISTORICAL at that instant and repeats the rows, summary, coverage and token of an explicit read there.
    cursor_k = decode_cursor("findings", first["next_cursor"])["known_at"]
    at_cursor = estate.ok("findings", **day, known_at=cursor_k)
    assert second["status"] == "HISTORICAL" and second["summary"]["as_of"] == second["window"]["known_at"]
    assert second["window"] == at_cursor["window"] and second["coverage"] == at_cursor["coverage"]
    assert second["summary"] == at_cursor["summary"] and second["rows"] == at_cursor["rows"][1:2]
    assert at_cursor["selection_token"] == second["selection_token"]
    assert {k: v for k, v in second["summary"].items() if k != "as_of"} == first["summary"]
    # A supplied cutoff must be the cursor's instant at full precision, or its wire-second copy (normalized to the
    # cursor instant); any other instant, even one inside the same second, is 409.
    wire_k = second["window"]["known_at"]
    for supplied in (cursor_k, wire_k):
        again = estate.ok("findings", **day, limit=1, cursor=first["next_cursor"], known_at=supplied)
        assert again["rows"] == second["rows"] and again["selection_token"] == second["selection_token"]
    other = datetime.fromisoformat(cursor_k.replace("Z", "+00:00"))
    other = other.replace(microsecond=(other.microsecond + 1) % 1_000_000 or 1)
    response = estate.get("findings", **day, limit=1, cursor=first["next_cursor"], known_at=iso(other))
    assert (response.status_code, response.json()["detail"]["code"]) == (409, "ESTATE_BASIS_CHANGED")
    # Page size never changes the full-set token or counts at one cutoff (a default cutoff is each read's time).
    pin = iso(db_now(built.engine))
    paged, full = (estate.ok("findings", **day, known_at=pin, limit=n) for n in (1, 100))
    assert paged["selection_token"] == full["selection_token"] and paged["summary"] == full["summary"]
    assert paged["rows"] == full["rows"][:1] and paged["status"] == "HISTORICAL"
    cursor = first["next_cursor"]

    def refused(**params) -> tuple[int, str]:
        response = estate.get("findings", **params)
        return response.status_code, response.json()["detail"]["code"]

    assert refused(**day, lens="cost", cursor=cursor) == (409, "ESTATE_BASIS_CHANGED")
    assert refused(**day, state="supported", cursor=cursor) == (409, "ESTATE_BASIS_CHANGED")
    assert refused(**{"from": iso(DAY - timedelta(days=1)), "to": day["to"]}, cursor=cursor) == (
        409, "ESTATE_BASIS_CHANGED")
    assert refused(**day, cursor=cursor + "x") == (422, "INVALID_CURSOR")
    actions_cursor = encode_cursor({**{k: v for k, v in decode_cursor("findings", cursor).items()
                                       if k not in ("lens", "state_filter")}, "kind": "actions"})
    assert refused(**day, cursor=actions_cursor) == (422, "INVALID_CURSOR")
    # A structurally valid cursor whose digest is not this `/2` selection (an old `/1` digest) is 409.
    old = encode_cursor({**decode_cursor("findings", cursor), "selection_token": "sha256:" + "0" * 64})
    assert refused(**day, cursor=old) == (409, "ESTATE_BASIS_CHANGED")
    # A grant change moves the access basis: 409 even though the remaining page would be empty.
    add_empty_site(built.engine, built.site_id, "W301-EMPTY-001")
    assert refused(**day, cursor=cursor) == (409, "ESTATE_BASIS_CHANGED")
    estate.admit = lambda code: code != "W301-EMPTY-001"
    assert estate.ok("findings", **day, limit=1, cursor=cursor)["rows"] == second["rows"]
    # A later selection with new revisions is not the selection at the cursor cutoff: page two still reads the
    # pinned page-one basis (Run 7), while a fresh live read moves to the new selection and token.
    built.advance_late()
    run(built)
    pinned = estate.ok("findings", **day, limit=1, cursor=cursor)
    assert pinned["rows"] == second["rows"] and pinned["selection_token"] == second["selection_token"]
    assert estate.ok("findings", **day)["selection_token"] != first["selection_token"]


# --- mini-grid: the S4 Finding/money chain and the S6 Action/verification chain --------------------------------

def pin_read_at(monkeypatch, present) -> None:
    """TEST-SCOPED: the S4/S6 fixtures run on a fixture clock ahead of the database clock (`SETUP_AT` 2026-10-29,
    `T_ACCEPT` 2026-11-01). Pin the estate snapshot's read time, and the dispatch helper's live-or-historical test,
    to the fixture's present `present()`, as the q5 helper tests pin `_transaction_time`. Every query, cutoff,
    selection and rule stays real; only "now" is the fixture's."""
    real = postgres_estate_read.EstateSnapshot

    class Pinned(real):
        def __init__(self, owner, c, read_at) -> None:
            super().__init__(owner, c, present())

    monkeypatch.setattr(postgres_estate_read, "EstateSnapshot", Pinned)
    monkeypatch.setattr(PostgresAssessmentStore, "_transaction_time", staticmethod(lambda c: present()))


def day_of(day: str) -> dict:
    start = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
    return {"from": iso(start), "to": iso(start + timedelta(days=1))}


def revisions(engine, finding_id) -> list[tuple]:
    with engine.connect() as c:
        return [tuple(r) for r in c.execute(text(
            "SELECT CAST(id AS text), revision_no, created_at FROM finding_revision WHERE finding_id = :f "
            "ORDER BY revision_no"), {"f": finding_id})]


@pytest.fixture()
def mini(store, engine, monkeypatch):  # noqa: F811
    runner = CaseRunner(store, engine)
    pin_read_at(monkeypatch, lambda: runner.now + timedelta(minutes=1))
    imported_before(engine, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    yield runner, Estate(engine, runner.tenant)
    pg_harness.dispose(runner.findings)


def rows_of(body: dict) -> list[tuple]:
    return [(r["finding_id"], r["finding_revision_id"], r["lifecycle"], r["episode_start"]) for r in body["rows"]]


def test_late_support_change_recurrence_at_exact_cutoff(mini) -> None:
    """S4 F03 (recurrence) and F05 (a later support change: SUPPORTED -> UNCONFIRMED -> NO_LONGER_SUPPORTED) read
    through the estate. Distinct recurrence rows keep their own Findings; each explicit cutoff keeps its exact selected
    revision, rows and token after later revisions land; one microsecond before the match pass that recorded the
    late revision the Site is UNKNOWN (the new selection is not yet matched), never the superseded row; late accepted
    evidence makes the live read pending while the earlier cutoff is unchanged."""
    runner, estate = mini
    run_case(runner, S4_CASES["F03"])
    recur = estate.ok("findings", **day_of("2026-10-11"))
    assert recur["status"] == "CURRENT" and recur["coverage"]["state"] == "COMPLETE"
    (a, b) = rows_of(recur)
    assert a[0] != b[0] and (a[2], b[2]) == ("SUPPORTED", "SUPPORTED")
    assert (a[3], b[3]) == ("2026-10-11T09:30:00Z", "2026-10-11T08:00:00Z")  # episode_start desc
    assert recur["total_count"] == 2 and recur["summary"]["supported_findings"] == 2

    steps = S4_CASES["F05"]["steps"]
    for step in steps[:3]:  # deliver, assess, match: SUPPORTED
        runner.step(step)
    day = day_of("2026-10-21")
    ((finding_id, rev1, lifecycle, _),) = rows_of(estate.ok("findings", **day))
    assert lifecycle == "SUPPORTED"
    for step in steps[3:6]:  # minimum runtime 120, assess, match: UNCONFIRMED
        runner.step(step)
    (r1, _, c1), (rev2, _, c2) = revisions(runner.engine, finding_id)
    assert r1 == rev1
    at_c2 = estate.ok("findings", **day, known_at=iso(c2))
    for step in steps[6:]:  # runtime 0, reserve 45, assess, match: NO_LONGER_SUPPORTED; then an empty retry
        runner.step(step)
    (_, _, _), (_, _, _), (rev3, _, c3) = revisions(runner.engine, finding_id)
    again = estate.ok("findings", **day, known_at=iso(c2))
    before = estate.ok("findings", **day, known_at=iso(c3 - timedelta(microseconds=1)))
    exact = estate.ok("findings", **day, known_at=iso(c3))
    live = estate.ok("findings", **day)
    # The late revision does not rewrite the explicit earlier cutoff: same rows, coverage and token.
    assert at_c2["status"] == "HISTORICAL" and rows_of(at_c2) == [(finding_id, rev2, "UNCONFIRMED",
                                                                    "2026-10-21T08:00:00Z")]
    assert again["rows"] == at_c2["rows"] and again["selection_token"] == at_c2["selection_token"]
    assert again["coverage"] == at_c2["coverage"] and again["summary"] == at_c2["summary"]
    assert at_c2["summary"]["supported_findings"] == 0 and at_c2["total_count"] == 1
    # One microsecond before the late match: the new selection is unmatched, the Site is UNKNOWN with no rows and
    # null totals, never the superseded UNCONFIRMED row.
    (site,) = before["coverage"]["sites"]
    assert (site["state"], site["match_state"]) == ("UNKNOWN", "PENDING")
    assert before["rows"] == [] and before["total_count"] is None
    assert all(v is None for v in before["summary"].values())
    # At the exact cutoff and live: the NO_LONGER_SUPPORTED revision, in All, outside Supported.
    assert rows_of(exact) == rows_of(live) == [(finding_id, rev3, "NO_LONGER_SUPPORTED", "2026-10-21T08:00:00Z")]
    assert exact["status"] == "HISTORICAL" and live["status"] == "CURRENT"
    assert live["summary"]["supported_findings"] == 0 and live["summary"]["basis_count"] == 1
    assert estate.ok("findings", **day, state="supported")["rows"] == []
    gone = estate.ok("findings", **day, state="no_longer_supported")
    assert rows_of(gone) == rows_of(live) and gone["summary"] == live["summary"]
    assert len({rev1, rev2, rev3}) == 3 and c1 < c2 < c3
    # Late accepted evidence on the day: the live read is pending; the exact earlier cutoff is unchanged.
    runner.step({"do": "deliver", "decided": "2026-10-30T16:00:00Z", "blocks": [
        {"from": "2026-10-21T10:00:00Z", "to": "2026-10-21T10:00:00Z", "soc": "50", "only": ["soc"]}]})
    pending = estate.ok("findings", **day)
    (site,) = pending["coverage"]["sites"]
    assert pending["status"] == site["state"] == "PENDING_RECOMPUTE" and site["job_state"] == "PENDING"
    assert pending["total_count"] is None and all(v is None for v in pending["summary"].values())
    held = estate.ok("findings", **day, known_at=iso(c3))
    assert held["rows"] == exact["rows"] and held["selection_token"] == exact["selection_token"]
    assert held["coverage"] == exact["coverage"] and held["status"] == "HISTORICAL"


def power_estate(store, engine, capsys, monkeypatch, policy=None):  # noqa: F811
    """The S4-03 `PowerSite` (a priced power-day Finding, a state-only Finding on 2026-10-08) and its consequence
    worker. `policy` is the S4-05 `publishing_submit` source policy; None keeps the ordinary unbound power path."""
    from test_w301_w1_money_snapshot_helpers_postgres import Rig

    if policy is not None:
        from test_s405_resolver_postgres import publishing_submit
        monkeypatch.setattr(CaseRunner, "submit", publishing_submit(policy))
    site = PowerSite(store, engine, capsys)
    pin_read_at(monkeypatch, lambda: site.runner.now + timedelta(minutes=1))
    imported_before(engine, site.tenant, site.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    return site, Rig(site, engine), Estate(engine, site.tenant)


def consequence_row(engine, revision_id) -> tuple:
    with engine.connect() as c:
        return tuple(c.execute(text(
            "SELECT CAST(finding_revision_id AS text), state, CAST(amount_low AS text), CAST(amount_high AS text), "
            "currency FROM financial_consequence_revision WHERE id = :r"), {"r": revision_id}).one())


LENSES = ("all", "cost", "risks", "opportunities")


def test_cost_risk_opportunity_eligibility_without_mock_seed(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    """One canonical Finding set underlies all four lenses. Without a stored risk or opportunity producer those
    lenses are truthfully empty over complete coverage (zero only after a complete read); an unpriced Finding and a
    stored PRICED amount whose source gate withholds money (unbound power) stay in All and never enter Cost."""
    site, rig, estate = power_estate(store, engine, capsys, monkeypatch)
    try:
        days = {"from": iso(POWER_DAY), "to": iso(STATE_DAY + timedelta(days=1))}
        rig.run()  # no price yet: the power-day consequence is UNPRICED
        power = site.on(POWER_DAY)
        day = {"from": iso(POWER_DAY), "to": iso(POWER_DAY + timedelta(days=1))}
        unpriced = estate.ok("findings", **day)
        ((row,),) = (unpriced["rows"],)
        assert row["finding_revision_id"] == str(power["id"]) and row["consequence"]["state"] == "UNPRICED"
        assert row["consequence"]["amount"] is None and row["lens_flags"] == []
        assert estate.ok("findings", **day, lens="cost")["rows"] == []
        site.publish("v1")
        rig.run()  # a stored PRICED revision, but the power evidence is unbound: the source gate withholds money
        bodies = {lens: estate.ok("findings", **day, lens=lens) for lens in LENSES}
        ((row,),) = (bodies["all"]["rows"],)
        stored = consequence_row(engine, row["consequence"]["source_revision_id"])
        assert stored[:2] == (str(power["id"]), "PRICED") and stored[4] == "USD"
        assert row["consequence"] == {"state": "UNKNOWN", "amount": None,
                                      "amount_low": None, "amount_high": None, "currency": None,
                                      "source_revision_id": row["consequence"]["source_revision_id"]}
        assert row["source_provenance"]["state"] != "AUTHORED_DEMONSTRATION" and row["lens_flags"] == []
        for lens in ("cost", "risks", "opportunities"):
            body = bodies[lens]
            assert body["lens"] == lens and body["status"] == "CURRENT" and body["coverage"]["state"] == "COMPLETE"
            assert body["rows"] == [] and body["total_count"] == 0 and body["summary"]["supported_findings"] == 0
            assert body["coverage"] == bodies["all"]["coverage"]
        # The three-day read: the 2026-10-07 day has no assessment, so the Site is UNKNOWN and no lens is a zero.
        for lens in LENSES:
            gap = estate.ok("findings", **days, lens=lens)
            assert gap["coverage"]["sites"][0]["state"] == "UNKNOWN" and gap["total_count"] is None
        # No mock seed: real labels only, no F-code, no risk/opportunity flag on any row.
        state_day = estate.ok("findings", **{"from": iso(STATE_DAY), "to": iso(STATE_DAY + timedelta(days=1))})
        for body in (*bodies.values(), state_day):
            assert "F-109" not in str(body) and "MG-DEMO" not in str(body)
            for r in body["rows"]:
                assert r["finding_label"] == f"Finding {r['finding_id'][:8]}"
                assert not {"RISK", "OPPORTUNITY"} & set(r["lens_flags"])
                assert (r["priority"], r["confidence"], r["confidence_reasons"]) == (None, None, [])
        assert state_day["rows"][0]["consequence"]["state"] == "UNPRICED"
        assert (state_day["summary"]["high_priority"], state_day["summary"]["low_confidence"]) == (None, None)
    finally:
        site.prices.dispose()
        site.store.dispose()


def test_cost_lens_only_exact_eligible_current_rows(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    """W7: Cost lists only the exact selected Finding revision's CURRENT, ELIGIBLE, source-permitted PRICED
    consequence, as its stored interval (no sum); the state-only Finding stays in All as Unpriced; an explicit
    earlier cutoff and a stale price selection are UNKNOWN and leave Cost until the consequence is recomputed."""
    from test_s405_publication_postgres import P01

    site, rig, estate = power_estate(store, engine, capsys, monkeypatch, lambda device, texts: P01)
    try:
        site.publish("v1", "v2", "v3")
        rig.run()
        power, state = site.on(POWER_DAY), site.on(STATE_DAY)
        day = {"from": iso(POWER_DAY), "to": iso(POWER_DAY + timedelta(days=1))}
        whole, cost = estate.ok("findings", **day), estate.ok("findings", **day, lens="cost")
        ((row,),) = (cost["rows"],)
        assert whole["rows"] == cost["rows"] and cost["status"] == "CURRENT"
        consequence = row["consequence"]
        stored = consequence_row(engine, consequence["source_revision_id"])
        assert row["finding_revision_id"] == str(power["id"]) == stored[0] and stored[1] == "PRICED"
        assert row["lens_flags"] == ["COST"] and consequence["state"] == "PRICED"
        assert (consequence["amount_low"], consequence["amount_high"], consequence["currency"]) == stored[2:]
        assert consequence["amount"] == consequence["amount_low"]  # the interval's low bound, never a sum
        assert row["source_provenance"]["state"] == "AUTHORED_DEMONSTRATION"
        assert cost["total_count"] == 1 and cost["summary"]["basis_count"] == 1
        # The state-only Finding: in All as Unpriced, absent from Cost (a complete zero).
        other = {"from": iso(STATE_DAY), "to": iso(STATE_DAY + timedelta(days=1))}
        ((unpriced,),) = (estate.ok("findings", **other)["rows"],)
        assert unpriced["finding_revision_id"] == str(state["id"]) and unpriced["consequence"]["state"] == "UNPRICED"
        none = estate.ok("findings", **other, lens="cost")
        assert none["rows"] == [] and none["total_count"] == 0 and none["coverage"]["state"] == "COMPLETE"
        # An explicit earlier cutoff never makes a current-money claim: UNKNOWN with the same revision, out of Cost.
        then = iso(site.runner.now)
        old_all, old_cost = estate.ok("findings", **day, known_at=then), estate.ok("findings", **day, known_at=then,
                                                                                  lens="cost")
        assert old_all["status"] == "HISTORICAL" and old_cost["rows"] == [] and old_cost["total_count"] == 0
        assert old_all["rows"][0]["consequence"] == {"state": "UNKNOWN", "amount": None,
                                                     "amount_low": None, "amount_high": None, "currency": None,
                                                     "source_revision_id": consequence["source_revision_id"]}
        # A backdated price correction: the stored amount is STALE until recomputed, so it leaves Cost.
        site.publish("v4")
        stale = estate.ok("findings", **day)
        assert stale["rows"][0]["consequence"]["state"] == "UNKNOWN" and stale["rows"][0]["lens_flags"] == []
        assert stale["rows"][0]["consequence"]["source_revision_id"] == consequence["source_revision_id"]
        assert estate.ok("findings", **day, lens="cost")["rows"] == []
        rig.run()
        again = estate.ok("findings", **day, lens="cost")
        ((fresh,),) = (again["rows"],)
        assert fresh["consequence"]["state"] == "PRICED"
        assert fresh["consequence"]["source_revision_id"] != consequence["source_revision_id"]
        assert consequence_row(engine, fresh["consequence"]["source_revision_id"])[0] == str(power["id"])
    finally:
        site.prices.dispose()
        site.store.dispose()


def at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_action_event_and_verification_counts_full_basis(store, engine, monkeypatch) -> None:  # noqa: F811
    """The S6 chain (F01 accepted, applied, plan frozen, later selection bound, evaluated VERIFIED with labelled
    TEST-SCOPED complete windows; then F02 accepted) read through the estate Action root. Each cutoff selects the
    latest event recorded by it and reduces through the W1 reducer; the cards count the full basis, never a page;
    the verification window and 30-day lookback switch at their exact persisted instants; ActionEvent OBSERVED is
    never a verification."""
    from test_s6_verification_evaluator_postgres import (
        CLOSED, bound_plan, complete_windows, evaluate, proposal_of, store_accept, verifying)

    runner = CaseRunner(store, engine)
    run_case(runner, S4_CASES["F01"])
    run_case(runner, S4_CASES["F02"])
    h = verifying(runner)
    pin: dict = {"at": None}
    pin_read_at(monkeypatch, lambda: pin["at"] or max(h.clock.at, runner.now) + timedelta(minutes=1))
    imported_before(engine, runner.tenant, runner.site, datetime(2026, 10, 1, tzinfo=timezone.utc))
    estate = Estate(engine, runner.tenant)
    window = {"from": "2026-11-01T00:00:00Z", "to": "2026-11-03T00:00:00Z"}
    f01_day = {"from": "2026-10-06T00:00:00Z", "to": "2026-10-07T00:00:00Z"}

    def actions(**params) -> tuple[dict, list[tuple]]:
        body = estate.ok("actions", **window, **params)
        return body, [(r["action_id"], r["application_state"], r["resolution_state"], r["verification_outcome"])
                      for r in body["rows"]]

    def card(body: dict) -> tuple:
        s = body["summary"]
        return s["open_actions"], s["verification_window"], s["verified_in_30_days"], s["basis_count"]

    try:
        p2 = proposal_of(h, "2026-10-08")
        complete_windows(monkeypatch, h)
        action_id, plan, _ = bound_plan(runner, h)
        with engine.connect() as c:
            events = [tuple(r) for r in c.execute(text(
                "SELECT kind, recorded_at, CAST(id AS text) FROM action_event WHERE action_id = :a "
                "ORDER BY recorded_at, id"), {"a": action_id})]
        accepted_at = next(e[1] for e in events if e[0] == "ACCEPTED")
        applied_at = next(e[1] for e in events if e[0] == "APPLIED")
        start, end = at(plan["later_start"]), at(plan["later_end"])
        # Event cutoffs: the selected event and the reduced state switch at the APPLIED event's recorded instant.
        none, none_rows = actions(known_at=iso(accepted_at - timedelta(microseconds=1)))
        assert none_rows == [] and none["total_count"] == 0 and card(none) == (0, 0, 0, 0)
        pending, rows = actions(known_at=iso(applied_at - timedelta(microseconds=1)))
        assert rows == [(action_id, "PENDING", None, None)] and card(pending) == (1, 0, 0, 1)
        applied, rows = actions(known_at=iso(applied_at))
        assert rows == [(action_id, "APPLIED", None, None)] and applied["status"] == "HISTORICAL"
        assert applied["rows"][0]["selected_event_id"] != pending["rows"][0]["selected_event_id"]
        assert applied["selection_token"] != pending["selection_token"]
        # The frozen plan's later window counts from later_start, inclusive, to later_end, exclusive.
        assert card(actions(known_at=iso(start - timedelta(microseconds=1)))[0]) == (1, 0, 0, 1)
        assert card(actions(known_at=iso(start))[0]) == (1, 1, 0, 1)
        assert card(actions(known_at=iso(end - timedelta(microseconds=1)))[0]) == (1, 1, 0, 1)
        assert card(actions(known_at=iso(end))[0]) == (1, 0, 0, 1)
        # Run 9 ruling 2 (honest zero): Awaiting verification joins the exact origin (Finding, revision) with an
        # open frozen later window and no resolved outcome. Applying F01 settles a new selected revision before
        # the window opens, so at later_start the card is 0 while the Action root's Verification window card is 1.
        in_window = estate.ok("findings", **f01_day, known_at=iso(start))
        assert in_window["summary"]["awaiting_verification"] == 0
        assert card(actions(known_at=iso(start))[0])[1] == 1
        with engine.connect() as c:
            origin = c.execute(text(
                "SELECT CAST(origin_finding_id AS text), CAST(origin_finding_revision_id AS text) FROM action "
                "WHERE id = :a"), {"a": action_id}).one()
        (selected,) = [r for r in in_window["rows"] if r["finding_id"] == origin[0]]
        assert selected["finding_revision_id"] != origin[1]
        # The earlier origin revision, selected before any plan exists, also counts 0.
        at_accept = estate.ok("findings", **f01_day, known_at=iso(accepted_at))
        assert [r["finding_revision_id"] for r in at_accept["rows"] if r["finding_id"] == origin[0]] == [origin[1]]
        assert at_accept["summary"]["awaiting_verification"] == 0
        # Controls: later_end is exclusive (the window is closed at it).
        assert estate.ok("findings", **f01_day, known_at=iso(end))["summary"]["awaiting_verification"] == 0
        # VERIFIED: RESOLVED closes the Action; the 30-day lookback counts the outcome's recorded instant.
        h.clock.at = CLOSED + timedelta(hours=1)
        outcome = evaluate(h, action_id, "eval-0001").json()["outcome"]
        assert outcome["outcome"] == "VERIFIED"
        verified, rows = actions()
        assert rows == [(action_id, "APPLIED", "RESOLVED", "VERIFIED")] and card(verified) == (0, 0, 1, 1)
        decided = at(outcome["recorded_at"])
        assert card(actions(known_at=iso(decided - timedelta(microseconds=1)))[0]) == (1, 0, 0, 1)
        assert verified["selection_token"] != applied["selection_token"]
        # Control: a resolved outcome never awaits verification.
        assert estate.ok("findings", **f01_day)["summary"]["awaiting_verification"] == 0
        # A second Action (F02, accepted, not applied) is open; the cards count both over the full basis.
        made = store_accept(h, runner, p2, "accept-f02", datetime(2026, 11, 2, 12, 30, tzinfo=timezone.utc))
        assert made is not None
        h.clock.at = datetime(2026, 11, 2, 13, 0, tzinfo=timezone.utc)
        both, rows = actions()
        assert [r[1:] for r in rows] == [("PENDING", None, None), ("APPLIED", "RESOLVED", "VERIFIED")]
        assert card(both) == (1, 0, 1, 2) and both["total_count"] == 2 and both["status"] == "CURRENT"
        page, _ = actions(limit=1)
        assert page["summary"] == both["summary"] and len(page["rows"]) == 1 and page["next_cursor"]
        assert page["selection_token"] == both["selection_token"]
        assert both["summary"]["due_overdue"] is None  # W1 has no authored due date
        # The 30-day lookback at its exact far edge (the read time pinned 30 days after the decision).
        pin["at"] = decided + timedelta(days=30, minutes=1)
        assert card(actions(known_at=iso(decided + timedelta(days=30)))[0])[2] == 1
        assert card(actions(known_at=iso(decided + timedelta(days=30, microseconds=1)))[0])[2] == 0
    finally:
        h.close()
        pg_harness.dispose(runner.findings)
