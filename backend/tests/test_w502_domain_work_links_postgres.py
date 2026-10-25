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
    # Post-W6 W6 Q10 (R366): the global row labels the Action by its stored public code; the Site row keeps W4's
    # `Action {id8}` label (Site Work stays W4/W5's). The href and every other field stay at parity.
    with cold.engine.connect() as c:
        code = c.execute(text("SELECT action_code FROM domain_action WHERE id = :a"), {"a": b.aid}).scalar_one()
    assert code.startswith("ACT-")
    relabel = {domain["label"]: code}
    assert rows[case_id]["action_links"] == [{"label": code, "href": domain["href"]}]
    assert {r["site_domain"] for r in rows.values()} == {"COLDCHAIN"}
    assert {r["links"]["site"]["href"] for r in rows.values()} == {f"/sites/{cold.code}"}
    for got, site in ((rows, w4), (old_rows, w4_old)):
        for cid, row in got.items():
            assert row["action_links"] == [{"label": relabel.get(x["label"], x["label"]), "href": x["href"]}
                                           for x in site[cid]["action_links"]]
            assert row["source_provenance"]["basis_sha256"] == site[cid]["source_provenance"]["basis_sha256"]
    sel = selected_ids(cold, case_id, b.after, b.aid, cold.revision_id)
    assert rows[case_id]["source_provenance"]["basis_sha256"] == basis_sha256(cold.t, cold.s, sel, cold.cited)
    assert old_rows[case_id]["action_links"] == []
    assert old_rows[case_id]["source_provenance"]["basis_sha256"] != rows[case_id]["source_provenance"]["basis_sha256"]
    assert now["selection_token"] != old["selection_token"]
    if root == "maintenance":
        assert rows[b.free]["action_links"] == old_rows[b.free]["action_links"] == []
        assert rows[b.free]["source_provenance"] == old_rows[b.free]["source_provenance"]


# ---- K1c rulings 2/3: link states on the test-only shifted producer (`test_w502_cold_scenario_producer.py`) -------

if URL:
    from test_w502_cold_scenario_producer import finding_revision, produce, shifted_chain, w501_read  # noqa: F401


def produced_cold(built, mechanism: str) -> SimpleNamespace:
    """The `cold` namespace over a shifted producer chain, pinned to its selected Finding revision of `mechanism`."""
    from assetops_backend.work.composition import build_domain_intent_service, build_work_service

    finding_id, revision_id = finding_revision(built, mechanism)
    with built.engine.connect() as c:
        cited = sorted(str(v) for v in c.execute(text(
            "SELECT evidence_id FROM finding_revision_evidence WHERE finding_revision_id = :r"),
            {"r": revision_id}).scalars())
    assert cited, "the selected cold Finding revision cites no accepted evidence"
    return SimpleNamespace(t=built.tenant_id, s=built.site_id, engine=built.engine, finding_id=finding_id,
                           revision_id=revision_id, cited=cited, svc=build_domain_intent_service(URL),
                           work=build_work_service(URL), code="COLD-LAB-001")


def domain_selection(cold, case_id: str) -> tuple[dict, dict]:
    """(raw `link_selections` row, `linked_coverage` link) of the case's one domain link at the read time."""
    from assetops_backend.work.composition import build_work_read
    from assetops_backend.work.link_coverage import linked_coverage

    reads = build_work_read(URL)
    try:
        def work(rx):
            rev = str(rx.revisions(case_id, rx.read_at)[-1]["id"])
            raw = [r for r in rx.link_selections(rev, None, None, rx.read_at) if r["kind"] == DOMAIN]
            cov = [x for x in linked_coverage(rx, cold.t, cold.s, rev, None, None, rx.read_at)["links"]
                   if x["kind"] == DOMAIN]
            return raw, cov
        raw, cov = reads.snapshot(cold.t, cold.s, cold.code, work)
    finally:
        reads.dispose()
    assert len(raw) == len(cov) == 1, (raw, cov)
    return raw[0], cov[0]


def test_pending_recompute_link_state(shifted_chain) -> None:  # noqa: F811
    """Ruling 3 PENDING: a later accepted reading (the HELD probe report, released at the shifted late-publication
    instant) enqueues a `cold_chain` recompute job that stays unrun; the pinned link and the W5-01 read at the
    returned cutoff both say PENDING_RECOMPUTE over the unchanged selected assessment."""
    built = produce(shifted_chain, "pending")
    cold = produced_cold(built, "COLD_EXCURSION")
    try:
        b = bind(cold, "pending")
        raw, cov = domain_selection(cold, b.request)
        assert raw["pin"] is not None and raw["lineage"] and cov["state"] == "CURRENT"
        first = raw["pin"]
        built.advance_late()  # the later accepted reading; its recompute job is never run
        with built.engine.connect() as c:
            jobs = c.execute(text("SELECT status, created_at FROM recompute_job WHERE site_id = :s "
                                  "AND domain = 'cold_chain' AND status = 'PENDING'"), {"s": built.site_id}).all()
            late = c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE site_id = :s "
                                  "AND decision = 'ACCEPTED'"), {"s": built.site_id}).scalar_one()
        assert jobs and late > first["evidence_cutoff"]
        raw, cov = domain_selection(cold, b.request)
        pin = raw["pin"]
        assert pin is not None and raw["lineage"] and raw["selected_id"] == cold.revision_id
        assert (pin["state"], cov["state"]) == ("PENDING_RECOMPUTE", "PENDING_RECOMPUTE")
        assert pin["evidence_cutoff"] == late
        assert pin["assessment_revision_id"] == first["assessment_revision_id"]  # the selection is not recomputed
        body = w501_read(built, iso(pin["evidence_cutoff"]))
        assert body["selection"]["state"] == "PENDING_RECOMPUTE"
        assert pin["assessment_revision_id"] in body["selection"]["assessment_revision_ids"]
    finally:
        cold.svc._store.dispose()
        cold.work._store.dispose()


if URL:
    from test_w502_cold_scenario_producer import seed_empty_support, selected_excursion, support_times


def test_stale_source_link_state(shifted_chain) -> None:  # noqa: F811
    """Run-5 STALE ruling 2: the wider-window producer's selected excursion Finding, its pinned Action and Case link;
    at the returned cutoff the exact pin, the linked coverage and the W5-01 read all say STALE_SOURCE over the same
    assessment revision and window, after the support-time check (latest SUPPORT probe <= end < window_end - 10m)."""
    built = produce(shifted_chain, "stale")
    sh = built.shifted
    cold = produced_cold(built, "COLD_EXCURSION")
    try:
        b = bind(cold, "stale")
        exc = selected_excursion(built)
        times = support_times(built, exc["ar"])
        assert times and times[-1] <= sh.end < sh.window_end - timedelta(minutes=10)
        raw, cov = domain_selection(cold, b.request)
        pin = raw["pin"]
        assert pin is not None and raw["lineage"] and raw["selected_id"] == cold.revision_id
        assert (pin["window_start"], pin["window_end"]) == (sh.start, sh.window_end)
        assert pin["assessment_revision_id"] == exc["ar"]
        assert (pin["state"], cov["state"]) == ("STALE_SOURCE", "STALE_SOURCE")
        body = w501_read(built, iso(pin["evidence_cutoff"]))
        assert body["selection"]["state"] == "STALE_SOURCE"
        assert exc["ar"] in body["selection"]["assessment_revision_ids"]
    finally:
        cold.svc._store.dispose()
        cold.work._store.dispose()


def test_unknown_link_state(shifted_chain) -> None:  # noqa: F811
    """Run-5 UNKNOWN ruling 3: the no-probe replay plus the test-only seeded empty-support selection; a domain Action
    pinned to the selected START_RESPONSE Finding revision and linked to a real W4 Case. At one returned cutoff the
    exact pin (nonempty lineage), the linked coverage and the W5-01 read say UNKNOWN because the selected excursion
    support set has no usable probe (not no selection, a missing Finding, a future window or an FK failure)."""
    from assetops_backend.analytics import cold as cold_analytics

    built = produce(shifted_chain, "no-probe")
    seed = seed_empty_support(built)
    assert support_times(built, seed.new["ar"]) == []
    cold = produced_cold(built, "COLD_START_FAILURE")
    try:
        b = bind(cold, "unknown")
        raw, cov = domain_selection(cold, b.request)
        pin = raw["pin"]
        assert pin is not None and raw["lineage"] and raw["selected_id"] == cold.revision_id
        assert pin["selection_seqs"][cold_analytics.EXCURSION_ANALYTIC] == seed.new["seq"]
        assert pin["window_end"] <= now_utc(cold.engine)
        assert (pin["state"], cov["state"]) == ("UNKNOWN", "UNKNOWN")
        body = w501_read(built, iso(pin["evidence_cutoff"]))
        assert body["selection"]["state"] == "UNKNOWN"
        # The reason is the empty selected support set (the depth read carries no note): a selection exists, the
        # window has ended before the read cutoff, and the seeded excursion's SUPPORT probes are zero.
        assert body["selection"]["assessment_revision_ids"] and body["window"]["to"] < body["window"]["known_at"]
        assert {seed.new["ar"], pin["assessment_revision_id"]} <= set(body["selection"]["assessment_revision_ids"])
    finally:
        cold.svc._store.dispose()
        cold.work._store.dispose()
