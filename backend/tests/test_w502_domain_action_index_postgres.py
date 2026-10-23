"""W5-02a K1b: the cold domain Action detail and the Site Action union index on real Postgres.

`.agent/W5-02-build-spec.md` "Command/read wire", "Site Action index", K1b lines and the Architect pre-flight ruling
B1-B3. The cold Finding comes from the ordinary W2-02 `backup-failed` replay (`cold` fixture of
`test_w502_domain_intent_postgres.py`); domain roots, intents and case links are written through the K1a service
and W4 cases through the W4 service. The one W1 battery Action is a direct-SQL row (a cold Site cannot accept one
through the W1 service) read through the W1 window port, never a second W1 SQL. Requires
ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import chain  # noqa: F401
    from test_w401_work_service_postgres import PRINCIPAL, record
    from test_w502_domain_intent_postgres import (SHA, W1_INSERT, _w1_sql, action_body, cold, create,  # noqa: F401
                                                  head_event, intent, intent_body, iso, link, link_body, now_utc,
                                                  w4_request)

    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.work import domain_action as d
    from assetops_backend.work import domain_action_index as x
    from assetops_backend.work.composition import build_domain_action_read
    from assetops_backend.work.model import MESSAGES, WorkRefused

ENVELOPE_KEYS = {"schema_version", "site_code", "window", "known_at", "status", "coverage", "total_count",
                 "all_due_dates_unset", "rows", "next_cursor", "selection_token"}
ROW_KEYS = {"action_id", "action_code", "domain", "title", "owner_label", "due_at", "raised_at", "recorded_at",
            "origin", "state", "criterion_summary", "links"}
DETAIL_KEYS = {"schema_version", "site_code", "action", "known_at", "status", "intent", "results", "links",
               "source_provenance", "selection_token"}
ACTION_KEYS = {"id", "action_code", "domain", "title", "owner_label", "due_at", "raised_at", "recorded_at", "state"}
WORK_KEYS = {"case_id", "case_code", "case_title", "request_state", "record_id", "label", "href"}
W1_EVENT = ("INSERT INTO action_event (id, tenant_id, site_id, action_id, kind, occurred_at, recorded_at, actor_kind, "
            "actor_id, source_channel, authorization_basis, triggering_service, triggering_command, "
            "triggering_fixture, idempotency_key, payload, payload_sha256) SELECT :e, tenant_id, site_id, id, "
            "'ACCEPTED', created_at, created_at, 'SYSTEM', 'service:w502-test', 'SYSTEM_DEMONSTRATION_API', "
            "'w502 test basis', 'w502-test', 'ACCEPT', 'w502-fixture', 'w502-w1-accept', CAST('{}' AS jsonb), :sha "
            "FROM action WHERE id = :id")


@pytest.fixture()
def reads(cold):
    store = build_domain_action_read(URL)
    yield x.DomainActionReadService(store)
    store.dispose()


def w1_action(cold, no: int) -> str:
    params = _w1_sql(cold, no)
    with cold.engine.begin() as c:
        c.execute(text(W1_INSERT), params)
        c.execute(text(W1_EVENT), {"e": str(uuid4()), "id": params["id"], "sha": SHA})
    return params["id"]


def refused(code: str, call, *args, **kwargs) -> None:
    with pytest.raises((WorkRefused, d.DomainIntentRefused)) as caught:
        call(*args, **kwargs)
    assert caught.value.code == code
    assert caught.value.message == (d.MESSAGES.get(code) or MESSAGES[code])


def index(reads, cold, lo, hi, *, limit=None, known=(), cursor=None):
    return reads.index(cold.t, cold.s, cold.code, x.parse_index_request(iso(lo), iso(hi), limit, list(known), cursor))


def detail(reads, cold, aid, known=()):
    return reads.detail(cold.t, cold.s, cold.code, aid, list(known))


def test_detail_selects_old_intent_at_old_cutoff(cold, reads) -> None:
    _, action = create(cold, action_body(cold))
    aid = action["id"]
    with cold.engine.connect() as c:
        raised = c.execute(text("SELECT raised_at FROM domain_action WHERE id = :i"), {"i": aid}).scalar_one()
    bare = detail(reads, cold, aid)
    assert set(bare) == DETAIL_KEYS and set(bare["action"]) == ACTION_KEYS, bare
    assert bare["schema_version"] == "domain-action-intent-read-1" and bare["site_code"] == cold.code
    assert bare["action"]["domain"] == "COLDCHAIN" and bare["action"]["state"] == "OPEN"
    assert (bare["intent"], bare["results"]) == (None, None)  # a successful missing declaration
    assert bare["links"]["work"] == dict.fromkeys(WORK_KEYS)
    assert bare["links"]["finding"] == {
        "label": f"Finding {cold.finding_id[:8]}",
        "href": f"/sites/{cold.code}/findings/{cold.finding_id}?revision_id={cold.revision_id}"}
    assert bare["selection_token"] == d.selection_token(cold.t, cold.s, {"id": aid, "raised_at": raised},
                                                        cold.revision_id, None, None, None, [])
    present = bare["status"]
    assert present in ("CURRENT", "STALE_SOURCE", "PENDING_RECOMPUTE"), bare["status"]

    wr = w4_request(cold, "w502-k1b-request-01")
    case_id, rev_id = wr["id"], wr["revision"]["id"]
    s, rec = cold.work.post_record(cold.t, cold.s, case_id, record("w502-k1b-record-01"), PRINCIPAL)
    assert s == 201, rec
    ev = head_event(cold, case_id)
    assert link(cold, aid, link_body(case_id, rev_id, ev, key="w502-k1b-link-01"))[0] == 201
    _, v1 = intent(cold, aid, intent_body(cold, "w502-k1b-intent-01", work_case_id=case_id, work_record_id=rec["id"]))
    cutoff = now_utc(cold.engine)
    first = detail(reads, cold, aid)
    assert first["intent"]["id"] == v1["intent_id"] and first["selection_token"] == v1["selection_token"]
    assert first["intent"]["criteria"] == [{"key": k, "label": lb, "required_evidence": r} for k, lb, r in d.CRITERIA]
    assert first["intent"]["basis"]["accepted_evidence_ids"] == cold.cited
    assert first["results"] == [{"key": k, "result": r, "evidence_ids": []} for (k, _, _), r in
                                zip(d.CRITERIA, ("NOT_TESTED", "NOT_TESTED", "NOT_ESTABLISHED", "PENDING"))]
    work = first["links"]["work"]
    assert work["case_code"].startswith("WR-"), work
    assert work == {
        "case_id": case_id, "case_code": work["case_code"], "case_title": "Inspect starter circuit",
        "request_state": "OPEN", "record_id": rec["id"], "label": f"Maintenance request {work['case_code']}",
        "href": None}
    prov = first["source_provenance"]
    assert prov["basis_sha256"] == basis_sha256(
        cold.t, cold.s, [aid, cold.revision_id, v1["intent_id"], rev_id, ev, rec["id"]], cold.cited), prov

    _, v2 = intent(cold, aid, intent_body(cold, "w502-k1b-intent-02", supersedes=v1["intent_id"]))
    now = detail(reads, cold, aid)
    assert now["intent"]["id"] == v2["intent_id"] and now["selection_token"] == v2["selection_token"]
    assert now["links"]["work"]["case_id"] == case_id  # the explicit link still selects the request
    old = detail(reads, cold, aid, [iso(cutoff)])
    assert old["intent"]["id"] == v1["intent_id"] and old["selection_token"] == v1["selection_token"]
    assert old["known_at"] == iso(cutoff)
    assert old["status"] == ("HISTORICAL" if present == "CURRENT" else present), (present, old["status"])
    assert old["selection_token"] != now["selection_token"]

    refused("ACTION_NOT_FOUND", detail, reads, cold, aid, [iso(raised - timedelta(hours=1))])  # not yet recorded
    refused("ACTION_NOT_FOUND", detail, reads, cold, str(uuid4()))
    refused("ACTION_NOT_FOUND", detail, reads, cold, "not-a-uuid")
    refused("INVALID_KNOWN_AT", detail, reads, cold, aid, [iso(now_utc(cold.engine) + timedelta(hours=1))])
    refused("INVALID_KNOWN_AT", detail, reads, cold, aid, [iso(cutoff), iso(cutoff)])
    refused("INVALID_KNOWN_AT", detail, reads, cold, aid, ["2026-01-01T00:00:00"])


def test_union_index_mixed_site_paging_and_fence(cold, reads) -> None:
    db_now = now_utc(cold.engine)
    lo, hi = db_now - timedelta(days=1), db_now + timedelta(hours=1)
    empty = index(reads, cold, lo, hi)
    assert set(empty) == ENVELOPE_KEYS and empty["total_count"] == 0 and empty["rows"] == []
    assert (empty["all_due_dates_unset"], empty["next_cursor"]) == (False, None)
    assert empty["coverage"] == {"state": "COMPLETE", "reason": None} and empty["status"] == "CURRENT"

    w1 = w1_action(cold, 900101)
    ids = []
    for n in range(5):
        over = {"raised_at": iso(db_now - timedelta(minutes=10 * (n + 1)))}
        if n == 4:
            over["due_at"] = iso(db_now + timedelta(days=3))
        _, made = create(cold, action_body(cold, f"w502-k1b-action-{n:02d}", **over))
        ids.append(made["id"])
    _, declared = intent(cold, ids[0], intent_body(cold, "w502-k1b-intent-10"))
    full = index(reads, cold, lo, hi)
    assert set(full) == ENVELOPE_KEYS and full["schema_version"] == "site-domain-action-index-1"
    assert full["window"] == {"from": iso(lo), "to": iso(hi), "bounds": "[from, to)"}
    assert full["total_count"] == 6 and len(full["rows"]) == 5 and full["next_cursor"] is not None
    assert full["all_due_dates_unset"] is False and full["selection_token"].startswith("sha256:")
    assert len(full["selection_token"]) == len("sha256:") + 64
    assert all(set(r) == ROW_KEYS for r in full["rows"])
    order = [r["action_id"] for r in full["rows"]]
    assert order == [w1, *ids[:4]], order  # membership time descending (W1 created now, domain raised earlier)
    w1_row, top = full["rows"][0], full["rows"][1]
    assert (w1_row["domain"], w1_row["title"], w1_row["owner_label"], w1_row["due_at"],
            w1_row["criterion_summary"]) == ("MINIGRID", None, None, None, None)
    assert isinstance(w1_row["state"], dict) and w1_row["links"]["action"].startswith(f"/sites/{cold.code}/actions/")
    assert w1_row["links"]["history"] is not None and w1_row["origin"]["href"] is not None
    assert (top["domain"], top["state"], top["title"], top["owner_label"]) == (
        "COLDCHAIN", "OPEN", "Witness automatic-start test", "Maintenance lead")
    assert top["criterion_summary"] == "Start requested → generator runs → power → cooling"
    assert full["rows"][2]["criterion_summary"] is None
    assert top["links"] == {"action": f"/sites/{cold.code}/actions/{ids[0]}/verification", "history": None}
    assert top["origin"] == {"finding_id": cold.finding_id, "finding_revision_id": cold.revision_id,
                             "label": f"Finding {cold.finding_id[:8]}",
                             "href": f"/sites/{cold.code}/findings/{cold.finding_id}?revision_id={cold.revision_id}"}
    present = full["status"]
    assert present in ("CURRENT", "STALE_SOURCE", "PENDING_RECOMPUTE")

    page2 = index(reads, cold, lo, hi, cursor=full["next_cursor"])
    assert [r["action_id"] for r in page2["rows"]] == [ids[4]] and page2["next_cursor"] is None
    assert page2["rows"][0]["due_at"] is not None and page2["selection_token"] == full["selection_token"]
    narrow = index(reads, cold, db_now - timedelta(minutes=15), hi)
    assert narrow["total_count"] == 2 and narrow["all_due_dates_unset"] is True
    assert index(reads, cold, lo, hi, limit="100")["total_count"] == 6

    # A historical cutoff before the intent: the fence differs and the old row has no criterion summary.
    with cold.engine.connect() as c:
        intent_at = c.execute(text("SELECT recorded_at FROM domain_action_intent WHERE id = :i"),
                              {"i": declared["intent_id"]}).scalar_one()
    before = index(reads, cold, lo, hi, known=[iso(intent_at - timedelta(microseconds=1))], limit="10")
    assert before["total_count"] == 6 and before["selection_token"] != full["selection_token"]
    assert next(r for r in before["rows"] if r["action_id"] == ids[0])["criterion_summary"] is None
    assert before["status"] == ("HISTORICAL" if present == "CURRENT" else present)

    # The cursor binds page one's cutoff: later writes do not move page two (fixed K, same full-set fence) ...
    intent(cold, ids[1], intent_body(cold, "w502-k1b-intent-11"))
    create(cold, action_body(cold, "w502-k1b-action-09", raised_at=iso(db_now - timedelta(minutes=55))))
    again = index(reads, cold, lo, hi, cursor=full["next_cursor"])
    assert [r["action_id"] for r in again["rows"]] == [ids[4]] and again["selection_token"] == full["selection_token"]
    assert index(reads, cold, lo, hi)["total_count"] == 7
    # ... and a valid cursor whose fence, scope or cutoff no longer matches is 409 WORK_BASIS_CHANGED.
    payload = x.decode_cursor(full["next_cursor"])
    stale = x.encode_cursor({**payload, "selection_token": "sha256:" + "0" * 64})
    refused("WORK_BASIS_CHANGED", index, reads, cold, lo, hi, cursor=stale)
    refused("WORK_BASIS_CHANGED", index, reads, cold, lo + timedelta(seconds=1), hi, cursor=full["next_cursor"])
    refused("WORK_BASIS_CHANGED", index, reads, cold, lo, hi, cursor=full["next_cursor"],
            known=[iso(intent_at - timedelta(microseconds=1))])
    # No domain row was copied into the W1 table.
    with cold.engine.connect() as c:
        assert c.execute(text("SELECT count(*) FROM action WHERE site_id = :s"), {"s": cold.s}).scalar_one() == 1
