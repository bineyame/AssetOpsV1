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

    from assetops_backend.analytics.adapters.postgres_assessment_store import selected_windows_on
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


def imported_before(engine, site_id, at: datetime) -> None:
    """TEST-SCOPED: the replay imports its Site at today's DB time; the estate scope admits a Site only when its
    committed import precedes the requested `to`. Re-date the fixture import so the replay's 2026-10-06 day is a
    valid estate window (the scope rule itself is proven unchanged in the scope test)."""
    with engine.begin() as c:
        c.execute(text("UPDATE site_import SET imported_at = :at WHERE site_id = :s"), {"at": at, "s": site_id})


def test_cold_ev_cutoff_precedes_reselection_and_revision(chain) -> None:  # noqa: F811
    """Run 7 q7 historical reselection proof at the estate level (cold): a later selection of the same stored
    window, with new assessment revisions, does not move an explicit earlier cutoff's rows, IDs or token."""
    built = opened("late-reading", chain)
    run(built)
    imported_before(built.engine, built.site_id, DAY - timedelta(days=1))
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
    imported_before(built.engine, built.site_id, DAY - timedelta(days=1))
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
    imported_before(built.engine, empty, DAY + timedelta(days=1))
    assert estate.ok("findings", **day)["scope"]["authorized_site_count"] == 1
    imported_before(built.engine, empty, DAY - timedelta(days=1))
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
    assert second["rows"] == whole["rows"][1:2] and second["selection_token"] == first["selection_token"]
    assert first["summary"] == whole["summary"]
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
    # A changed selected window (a later selection with new revisions) fences page two.
    built.advance_late()
    run(built)
    assert refused(**day, limit=1, cursor=cursor) == (409, "ESTATE_BASIS_CHANGED")
