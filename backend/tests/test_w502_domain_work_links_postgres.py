"""W5-02a K1c: explicit cold domain Action case links beneath the W4 Site reads, on real Postgres.

`.agent/W5-02-build-spec.md` K1c card, "Backend wire" K1c paragraph and the Architect pre-flight ruling C1/C2.
The cold Finding comes from the ordinary W2-02 `backup-failed` replay (`cold` fixture); the domain root and its case
links are written through the K1a service and the W4 cases through the W4 service. A domain link reaches the W4
Site index, the case detail and link coverage with `action_event_id: null`, the `Action {id[:8]}` label and the
domain Verification href; it never appears before its recorded time, carries forward to a later revision of the
same case, and leaves an unlinked case byte-equivalent. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` DB.
"""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401
    from test_w401_work_service_postgres import ACTOR, PRINCIPAL, incident
    from test_w502_domain_intent_postgres import (action_body, cold, create, head_event, iso, link,  # noqa: F401
                                                  link_body, now_utc, w4_request)

    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.work.composition import build_work_detail_service, build_work_index_service
    from assetops_backend.work.site_index import parse_list_request

DOMAIN = "DOMAIN_ACTION"


def bind(cold, suffix: str = "a") -> SimpleNamespace:
    """One domain Action, an Incident and a request each explicitly linked at their selected head, and one
    unlinked request; `before` is a DB instant before any link was recorded."""
    _, action = create(cold, action_body(cold, key=f"w502-k1c-action-{suffix}"))
    aid = action["id"]
    status, inc = cold.work.create_case(cold.t, cold.s, incident(f"w502-k1c-incident-{suffix}"), PRINCIPAL)
    assert status == 201, inc
    wr = w4_request(cold, f"w502-k1c-request-{suffix}")
    free = w4_request(cold, f"w502-k1c-free-{suffix}")
    before = now_utc(cold.engine)
    for case, key in ((inc, "inc"), (wr, "wr")):
        status, _ = link(cold, aid, link_body(case["id"], case["revision"]["id"], head_event(cold, case["id"]),
                                              key=f"w502-k1c-link-{key}-{suffix}"))
        assert status == 201
    after = now_utc(cold.engine)
    # A midnight-aligned window, as the W6 global parser requires, holding every case of this fixture.
    lo = (before - timedelta(hours=3)).replace(hour=0, minute=0, second=0, microsecond=0)
    window = (iso(lo), iso(after.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)))
    return SimpleNamespace(aid=aid, incident=inc["id"], request=wr["id"], free=free["id"], before=before,
                           after=after, window=window)


def expected_link(cold, aid: str) -> dict:
    return {"kind": DOMAIN, "action_id": aid, "action_event_id": None, "finding_revision_id": cold.revision_id,
            "label": f"Action {aid[:8]}", "href": f"/sites/{cold.code}/actions/{aid}/verification"}


def site_index(cold, kind: str, window: tuple[str, str], known=()) -> dict:
    svc = build_work_index_service(URL)
    try:
        return svc.read(cold.t, cold.s, cold.code, kind, parse_list_request(window[0], window[1], None, list(known),
                                                                          None), access_basis="test")
    finally:
        svc._reads.dispose()


def case_detail(cold, case_id: str, known=()) -> dict:
    svc = build_work_detail_service(URL)
    try:
        return svc.detail(cold.t, cold.s, cold.code, case_id, list(known))
    finally:
        svc._reads.dispose()


def rows_by_id(body: dict) -> dict[str, dict]:
    return {r["case_id"]: r for r in body["rows"]}


def selected_ids(cold, case_id: str, known_at, *extra: str) -> list[str]:
    with cold.engine.connect() as c:
        rev = c.execute(text("SELECT CAST(id AS text) FROM work_case_revision WHERE case_id = :c AND recorded_at <= :k "
                             "ORDER BY recorded_at DESC, id DESC LIMIT 1"), {"c": case_id, "k": known_at}).scalar_one()
        events = [str(v) for v in c.execute(text("SELECT id FROM work_event WHERE case_id = :c AND recorded_at <= :k"),
                                            {"c": case_id, "k": known_at}).scalars()]
    return [rev, *events, *extra]


def test_domain_link_in_site_index_detail_and_coverage(cold) -> None:
    b = bind(cold)
    link_dto = expected_link(cold, b.aid)
    for kind, case_id in (("incidents", b.incident), ("maintenance", b.request)):
        now = site_index(cold, kind, b.window)
        old = site_index(cold, kind, b.window, [iso(b.before)])
        row, old_row = rows_by_id(now)[case_id], rows_by_id(old)[case_id]
        assert row["action_links"] == [link_dto]
        # Never before its recorded time: the earlier cutoff has no domain link and the W4 W1-only basis.
        assert old_row["action_links"] == []
        assert now["selection_token"] != old["selection_token"]
        known = now["known_at"]
        sel = selected_ids(cold, case_id, known, b.aid, cold.revision_id)
        assert row["source_provenance"]["basis_sha256"] == basis_sha256(cold.t, cold.s, sel, cold.cited)
        assert set(cold.cited) <= set(row["source_provenance"]["evidence_ids"])
        assert set(cold.cited).isdisjoint(old_row["source_provenance"]["evidence_ids"])
    # The unlinked request is byte-equivalent apart from the read instant.
    now, old = site_index(cold, "maintenance", b.window), site_index(cold, "maintenance", b.window, [iso(b.before)])
    assert rows_by_id(now)[b.free] == rows_by_id(old)[b.free]
    assert rows_by_id(now)[b.free]["action_links"] == []

    detail = case_detail(cold, b.request)
    raw = {k: link_dto[k] for k in ("kind", "action_id", "action_event_id", "finding_revision_id")}
    assert detail["action_links"] == [raw]
    links = [x for x in detail_coverage_links(cold, b.request) if x["kind"] == DOMAIN]
    assert [(x["id"], x["selected_id"]) for x in links] == [(b.aid, cold.revision_id)]
    assert links[0]["selection_token"].startswith("sha256:")
    assert case_detail(cold, b.request, [iso(b.before)])["action_links"] == []
    assert case_detail(cold, b.free)["action_links"] == []


def detail_coverage_links(cold, case_id: str) -> list[dict]:
    from assetops_backend.work.composition import build_work_read
    from assetops_backend.work.link_coverage import linked_coverage

    reads = build_work_read(URL)
    try:
        def work(rx):
            rev = rx.revisions(case_id, rx.read_at)[-1]
            return linked_coverage(rx, cold.t, cold.s, str(rev["id"]), None, None, rx.read_at)["links"]
        return reads.snapshot(cold.t, cold.s, cold.code, work)
    finally:
        reads.dispose()


def test_link_carries_forward_to_a_later_revision(cold) -> None:
    b = bind(cold)
    linked_revision = head_revision_at(cold, b.request, b.after)
    status, revised = cold.work.post_revision(cold.t, cold.s, b.request, {
        "supersedes_revision_id": linked_revision, "title": "Starter/control inspection",
        "narrative": "Revised after the link.", "reason": "Scope clarified",
        "occurred_at": iso(now_utc(cold.engine) - timedelta(minutes=5)), "actor": dict(ACTOR),
        "idempotency_key": "w502-k1c-revise-a"}, PRINCIPAL)
    assert status == 201, revised
    row = rows_by_id(site_index(cold, "maintenance", b.window))[b.request]
    assert row["revision_id"] == revised["revision_id"] != linked_revision
    assert row["action_links"] == [expected_link(cold, b.aid)]
    # The W4 battery FK table never receives the domain link (command replay copies it forward).
    with cold.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM work_case_action_link WHERE action_id = :a"),
                         {"a": b.aid}).scalar_one() == 0


def head_revision_at(cold, case_id: str, known_at) -> str:
    with cold.engine.connect() as c:
        return c.execute(text("SELECT CAST(id AS text) FROM work_case_revision WHERE case_id = :c "
                              "AND recorded_at <= :k ORDER BY recorded_at DESC, id DESC LIMIT 1"),
                         {"c": case_id, "k": known_at}).scalar_one()


def assert_global_domain_parity(cold, b: SimpleNamespace, api_class, root: str, case_id: str) -> None:
    """Ruling C2 for one W6 global root (`incidents` or `maintenance`): at the returned cutoff the global row's
    Action links equal W4's Site row links (label/href of the domain link, null event never faked), its selected
    IDs/citations equal W4's and include the domain root and Finding revision; an earlier cutoff and an unlinked
    request have no domain link and keep their W4 basis."""
    window = {"from": b.window[0], "to": b.window[1]}
    api = api_class(str(cold.t), None)
    call = (lambda **q: api.ok(**q)) if root == "incidents" else (lambda **q: api.ok(root, **q))
    try:
        now = call(**window, known_at=iso(b.after))
        old = call(**window, known_at=iso(b.before))
    finally:
        api.close()
    w4_kind = "incidents" if root == "incidents" else "maintenance"
    w4 = rows_by_id(site_index(cold, w4_kind, b.window, [iso(b.after)]))
    w4_old = rows_by_id(site_index(cold, w4_kind, b.window, [iso(b.before)]))
    rows, old_rows = rows_by_id(now), rows_by_id(old)
    domain = expected_link(cold, b.aid)
    assert rows[case_id]["action_links"] == [{"label": domain["label"], "href": domain["href"]}]
    for got, site in ((rows, w4), (old_rows, w4_old)):
        for cid, row in got.items():
            assert row["action_links"] == [{"label": x["label"], "href": x["href"]} for x in site[cid]["action_links"]]
            assert row["source_provenance"]["basis_sha256"] == site[cid]["source_provenance"]["basis_sha256"]
    sel = selected_ids(cold, case_id, b.after, b.aid, cold.revision_id)
    assert rows[case_id]["source_provenance"]["basis_sha256"] == basis_sha256(cold.t, cold.s, sel, cold.cited)
    assert old_rows[case_id]["action_links"] == []
    assert old_rows[case_id]["source_provenance"]["basis_sha256"] != rows[case_id]["source_provenance"]["basis_sha256"]
    assert now["selection_token"] != old["selection_token"]
    if root == "maintenance":
        assert rows[b.free]["action_links"] == old_rows[b.free]["action_links"] == []
        assert rows[b.free]["source_provenance"] == old_rows[b.free]["source_provenance"]
