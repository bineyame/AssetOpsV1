"""W4-03 unit 3: authored Alternatives on exact W1 mini dispatch Finding revisions over Postgres.

`.agent/W4-03-build-spec.md`: original Alternative domain paragraph and panel ledger; closure 1 Q1-Q3, Q12-Q16;
closure 4 B1 (KOBO-001 carries the W1 dispatch Finding), S17 (R1 -> R2 without and with carry-forward, both cutoffs),
S20 (provenance basis), N1 (dispatch only), N2 (strict overlap, empty episode, boundary touch, point inside).

The W1 Finding and its two revisions come from the S4 `CaseRunner` running case F02 (OPENED, then SUPPORT_CHANGED).
Its revisions carry fixture times, so the service runs with its constructor-only test clocks (W4-01's pattern); the
W1 Finding read before and after every alternative write is the regression proof that nothing W1 changed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from test_s4_finding_store_postgres import SPEC, URL  # noqa: F401

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s4_finding_store_postgres import runner  # noqa: F401

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.analytics.finding_read import FindingReadService
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.mini_decisions.alternatives import AlternativeService, rules_out
    from assetops_backend.mini_decisions.model import GRANT_PREFIX, DecisionPrincipal, DecisionRefused
    from assetops_backend.mini_decisions.scenarios import decode_cursor, encode_cursor, parse_list
    from assetops_backend.mini_decisions.store import PostgresMiniDecisionStore
    from assetops_backend.mini_decisions_api import build_mini_decisions_router
    from assetops_backend.mini_depth.read import MiniDepthRead
    from assetops_backend.sites.ports import SiteStoreUnavailable

PRINCIPAL_ID = "service:w403-fixture"
ATTESTATION = "service=w403-fixture;job=positive-decisions;rule=w403/1"
READ_AT = datetime(2027, 1, 1, tzinfo=timezone.utc)
WRITE_KEYS = {"schema_version", "id", "finding_id", "finding_revision_id", "alternative_key", "version_no",
              "supersedes_revision_id", "recorded_at"}
ROW_KEYS = {"id", "revision_id", "finding_revision_id", "explanation", "evidence_summary",
            "cited_accepted_evidence_ids", "missing_evidence_reason", "disposition", "reason", "review_state"}
LIST_KEYS = {"schema_version", "window", "status", "currentness", "source_provenance", "selected_source_provenance",
             "pending_source_provenance", "total_count", "rows", "next_cursor", "selection_token"}
F02 = next(c for c in SPEC["cases"] if c["case_id"] == "F02")
TABLES = ("mini_alternative_revision", "mini_alternative_evidence", "finding", "finding_revision")


def actor(**overrides):
    return {"kind": "SERVICE", "id": PRINCIPAL_ID, "attestation": ATTESTATION, **overrides}


def command(key, finding_revision_id, alternative_key="POLICY", **extra):
    body = {"schema_version": "mini-alternative-command-1", "idempotency_key": key, "actor": actor(),
            "finding_revision_id": str(finding_revision_id), "alternative_key": alternative_key,
            "supersedes_revision_id": None, "explanation": "A configured reserve policy may explain the run.",
            "evidence_summary": "The selected record documents the configured policy.",
            "cited_accepted_evidence_ids": [], "missing_evidence_reason": "No record states the counterfactual.",
            "disposition": "PLAUSIBLE",
            "reason": "This record does not establish the counterfactual service outcome."}
    body.update(extra)
    return body


def iso(at: datetime) -> str:
    return at.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


class Clock:
    def __init__(self, at: datetime) -> None:
        self.at = at

    def tick(self, seconds: int = 1) -> datetime:
        self.at += timedelta(seconds=seconds)
        return self.at


def counts(engine) -> tuple:
    with engine.connect() as c:
        return tuple(c.execute(text(f"SELECT count(*) FROM {t}")).scalar_one() for t in TABLES)


def finding_revisions(engine, site):
    with engine.connect() as c:
        return [dict(r) for r in c.execute(text(
            "SELECT f.id AS finding_id, r.id, r.revision_no, r.episode_start, r.episode_end, r.created_at "
            "FROM finding f JOIN finding_revision r ON r.finding_id = f.id WHERE f.site_id = :s "
            "AND f.anchor_start = :a ORDER BY r.revision_no"), {"s": site, "a": "2026-10-08T23:20:00Z"}).mappings()]


def evidence(engine, site, rev, *, inside: bool):
    """One accepted row of the Site overlapping (or wholly before) the revision's half-open episode."""
    where = ("COALESCE(interval_start, source_time) < :end AND "
             "COALESCE(interval_end, source_time + interval '1 microsecond') > :start" if inside else
             "COALESCE(interval_end, source_time + interval '1 microsecond') <= :start")
    with engine.connect() as c:
        return str(c.execute(text(f"SELECT id FROM accepted_evidence WHERE site_id = :s AND {where} "
                                  "AND received_at <= :cut ORDER BY id LIMIT 1"),
                             {"s": site, "start": rev["episode_start"], "end": rev["episode_end"],
                              "cut": rev["created_at"]}).scalar_one())


def foreign_evidence(engine, evidence_id) -> str:
    """A test-only replica copy of an accepted row under another Site (u3 2: a foreign citation)."""
    copy = uuid4()
    with engine.begin() as c:
        c.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in ("CREATE TEMP TABLE e_copy ON COMMIT DROP AS SELECT * FROM accepted_evidence WHERE id = :e",
                    "UPDATE e_copy SET id = :n, site_id = gen_random_uuid()",
                    "INSERT INTO accepted_evidence SELECT * FROM e_copy"):
            c.execute(text(sql), {"e": evidence_id, "n": copy})
    return str(copy)


def w1_read(runner, finding_id, revision_id):
    reads = FindingReadService(PostgresFindingStore(URL), DispatchReadService(PostgresAssessmentStore(URL)), None)
    return reads.finding(runner.tenant, runner.site, finding_id, revision_id)


def steps(runner, part):
    for step in part:
        runner.step(step)


def service_for(engine, clock: Clock) -> "AlternativeService":
    return AlternativeService(PostgresMiniDecisionStore(engine), MiniDepthRead(engine, link_rows_on),
                              test_db_clock_override=lambda: clock.at, test_read_clock_override=lambda: READ_AT)


def test_alternative_r1_r2_carry_forward_reads_and_w1_regression(runner, engine) -> None:  # noqa: F811
    t, s = runner.tenant, runner.site
    who = DecisionPrincipal("SERVICE", PRINCIPAL_ID, t, s, GRANT_PREFIX + PRINCIPAL_ID)
    steps(runner, F02["steps"][:3])
    (r1,) = finding_revisions(engine, s)
    fid = str(r1["finding_id"])
    inside, outside = evidence(engine, s, r1, inside=True), evidence(engine, s, r1, inside=False)
    w1_before = w1_read(runner, r1["finding_id"], r1["id"])
    clock = Clock(r1["created_at"] + timedelta(seconds=10))
    svc = service_for(engine, clock)

    def post(body):
        try:
            return svc.create(t, s, who, fid, body)
        except DecisionRefused as refused:
            return refused.status, refused.code

    # Version 1 on R1: create, exact retry, changed body.
    status, policy = post(command("w403-alt-p001", r1["id"], cited_accepted_evidence_ids=[inside.upper(), inside]))
    assert status == 201 and set(policy) == WRITE_KEYS and policy["schema_version"] == "mini-alternative-write-1"
    assert (policy["finding_id"], policy["finding_revision_id"], policy["alternative_key"], policy["version_no"],
            policy["supersedes_revision_id"], policy["recorded_at"]) == (fid, str(r1["id"]), "POLICY", 1, None,
                                                                          iso(clock.at))
    assert post(command("w403-alt-p001", r1["id"], cited_accepted_evidence_ids=[inside])) == (200, policy)
    before = counts(engine)
    assert post(command("w403-alt-p001", r1["id"], cited_accepted_evidence_ids=[inside], reason="Other.")) == (
        409, "DECISION_DUPLICATE_KEY")
    clock.tick()
    status, uncertainty = post(command("w403-alt-u001", r1["id"], "UNCERTAINTY", disposition="CANNOT_EXCLUDE",
                                       missing_evidence_reason="No PCS fault log is recorded for this window."))
    assert status == 201
    clock.tick()
    # RULED_OUT needs cited overlapping counterevidence; absence or an outside-only record cannot rule out.
    assert post(command("w403-alt-c001", r1["id"], "CAPABILITY", disposition="RULED_OUT",
                        cited_accepted_evidence_ids=[outside])) == (422, "DECISION_COUNTEREVIDENCE_INVALID")
    assert post(command("w403-alt-c002", r1["id"], "CAPABILITY", disposition="RULED_OUT")) == (
        422, "DECISION_COUNTEREVIDENCE_INVALID")
    status, capability = post(command("w403-alt-c003", r1["id"], "CAPABILITY", disposition="RULED_OUT",
                                      cited_accepted_evidence_ids=[inside, outside]))
    assert status == 201
    # Refusal vectors write nothing.
    foreign = foreign_evidence(engine, inside)
    snapshot = counts(engine)
    for body, expected in (
            (command("w403-alt-x001", r1["id"]), (409, "DECISION_CORRECTION_CONFLICT")),  # a second version 1
            (command("w403-alt-x002", r1["id"], supersedes_revision_id=policy["id"],
                     cited_accepted_evidence_ids=[str(uuid4())]),
             (422, "DECISION_LINK_SCOPE_INVALID")),
            (command("w403-alt-x003", uuid4(), "UNCERTAINTY"), (422, "DECISION_LINK_SCOPE_INVALID")),
            (command("w403-alt-x004", r1["id"], supersedes_revision_id=str(uuid4())),
             (422, "DECISION_LINK_SCOPE_INVALID")),
            (command("w403-alt-x005", r1["id"], missing_evidence_reason=None), (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x006", r1["id"], rank=1), (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x007", r1["id"], alternative_key="OTHER"), (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x008", r1["id"], disposition="LIKELY"), (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x009", r1["id"], explanation=" "), (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x010", r1["id"], reason="x" * 2001), (422, "DECISION_INPUT_INVALID")),  # uF 4
            (command("w403-alt-x011", r1["id"], actor=actor(kind="USER")), (403, "DECISION_USER_AUTH_REQUIRED")),
            (command("w403-alt-x012", r1["id"], actor=actor(attestation="service=other;job=j;rule=r")),
             (422, "DECISION_ATTESTATION_INVALID")),
            (command("w403-alt-x013", r1["id"], actor=actor(authorization_basis=None)),
             (422, "DECISION_INPUT_INVALID")),
            # u3 2: citation admission and the missing-evidence reason bounds.
            (command("w403-alt-x015", r1["id"], "CAPABILITY", missing_evidence_reason="   "),
             (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x016", r1["id"], "CAPABILITY", missing_evidence_reason="x" * 501),
             (422, "DECISION_INPUT_INVALID")),
            (command("w403-alt-x017", r1["id"], "CAPABILITY", supersedes_revision_id=capability["id"],
                     cited_accepted_evidence_ids=[inside, foreign]),
             (422, "DECISION_LINK_SCOPE_INVALID")),
            # u3 1: a wrong-key predecessor (another key's head) and a wrong-path one (the Finding revision ID).
            (command("w403-alt-x018", r1["id"], supersedes_revision_id=uncertainty["id"]),
             (422, "DECISION_LINK_SCOPE_INVALID")),
            (command("w403-alt-x019", r1["id"], supersedes_revision_id=str(r1["id"])),
             (422, "DECISION_LINK_SCOPE_INVALID"))):
        assert post(body) == expected, body["idempotency_key"]
    assert counts(engine) == snapshot and snapshot[0] == before[0] + 2
    with pytest.raises(DecisionRefused) as missing:
        svc.create(t, s, who, str(uuid4()), command("w403-alt-x014", r1["id"]))
    assert missing.value.code == "DECISION_NOT_FOUND"
    k_r1 = clock.tick()
    assert w1_read(runner, r1["finding_id"], r1["id"]) == w1_before  # W1 regression: alternatives change nothing

    # R2 (SUPPORT_CHANGED). The W1 read of R1 is unchanged by every alternative write.
    steps(runner, F02["steps"][3:])
    r1_again, r2 = finding_revisions(engine, s)
    assert r1_again == r1 and r2["revision_no"] == 2 and r2["created_at"] > k_r1
    w1_r1, w1_r2 = (w1_read(runner, r1["finding_id"], r["id"]) for r in (r1, r2))
    clock.at = r2["created_at"] + timedelta(seconds=10)
    stale = command("w403-alt-s001", r1["id"], supersedes_revision_id=policy["id"], reason="Re-evaluated.")
    assert post(stale) == (409, "DECISION_BASIS_CHANGED")  # R1 is no longer the selected Finding revision
    # u3 1: an exact authorized retry still returns its original body after a later Finding revision exists.
    assert post(command("w403-alt-p001", r1["id"], cited_accepted_evidence_ids=[inside])) == (200, policy)
    assert post(command("w403-alt-s002", r2["id"])) == (409, "DECISION_CORRECTION_CONFLICT")  # a second version 1

    def read(**q):
        revision = q.pop("revision_id", None)
        known = [q["known_at"]] if "known_at" in q else []
        return svc.list(t, s, fid, revision, parse_list(None, None, q.get("limit"), known, q.get("cursor")), "basis")

    # R2 selected, no carry-forward: every key is NEEDS_REVIEW history on R1, never a current disposition.
    needs = read()
    assert set(needs) == LIST_KEYS and needs["schema_version"] == "mini-alternatives-1"
    assert needs["window"] == {"from": None, "to": None, "known_at": iso(READ_AT)} and needs["status"] == "UNKNOWN"
    assert needs["currentness"] == {"state": "CURRENT", "job_state": "NONE"} and needs["total_count"] == 3
    assert all(set(r) == ROW_KEYS for r in needs["rows"])
    assert [(r["revision_id"], r["review_state"], r["finding_revision_id"]) for r in needs["rows"]] == [
        (policy["id"], "NEEDS_REVIEW", str(r1["id"])), (uncertainty["id"], "NEEDS_REVIEW", str(r1["id"])),
        (capability["id"], "NEEDS_REVIEW", str(r1["id"]))]
    # S20, no current citation: only the exact selected Finding revision in the basis; no evidence IDs.
    selected = needs["selected_source_provenance"]
    assert selected["evidence_ids"] == [] and selected["basis_sha256"] == basis_sha256(t, s, [r2["id"]], [])
    assert needs["pending_source_provenance"] is None and needs["source_provenance"] == selected
    # R1 pinned: its own rows, HISTORICAL relative to R2, with their stored dispositions and citations.
    pinned = read(revision_id=str(r1["id"]))
    assert [(r["review_state"], r["disposition"]) for r in pinned["rows"]] == [
        ("HISTORICAL", "PLAUSIBLE"), ("HISTORICAL", "CANNOT_EXCLUDE"), ("HISTORICAL", "RULED_OUT")]
    assert pinned["rows"][1]["cited_accepted_evidence_ids"] == [] and pinned["rows"][1]["missing_evidence_reason"]
    assert pinned["rows"][2]["cited_accepted_evidence_ids"] == sorted([inside, outside])
    assert pinned["currentness"]["state"] == "HISTORICAL"
    r1_ids = [r1["id"], policy["id"], uncertainty["id"], capability["id"]]
    assert pinned["selected_source_provenance"]["evidence_ids"] == sorted({inside, outside})
    assert pinned["selected_source_provenance"]["basis_sha256"] == basis_sha256(t, s, r1_ids, [inside, outside])
    # The cutoff before R2: R1 is selected and its rows are CURRENT; the explicit past cutoff is HISTORICAL.
    early = read(known_at=iso(k_r1))
    assert [r["review_state"] for r in early["rows"]] == ["CURRENT"] * 3
    assert early["currentness"]["state"] == "HISTORICAL" and early["window"]["known_at"] == iso(k_r1)

    # Carry-forward onto R2 (S17): same key, exact predecessor, next version, re-evaluation reason.
    clock.tick()
    carry = command("w403-alt-p002", r2["id"], supersedes_revision_id=policy["id"], cited_accepted_evidence_ids=[inside],
                    reason="Re-evaluated against Finding revision 2; the policy still may explain the run.")
    status, carried = post(carry)
    assert status == 201 and (carried["version_no"], carried["supersedes_revision_id"],
                              carried["finding_revision_id"]) == (2, policy["id"], str(r2["id"]))
    assert post(carry) == (200, carried)
    assert post({**carry, "idempotency_key": "w403-alt-p003"}) == (409, "DECISION_CORRECTION_CONFLICT")
    after = read()
    # u3 3: a fresh service (a new request) reads the same stable row IDs: version 1's ID, displayed head revision.
    fresh = service_for(engine, clock).list(t, s, fid, None, parse_list(None, None, None, [], None), "basis")
    assert fresh["rows"] == after["rows"]
    assert [(r["id"], r["revision_id"], r["review_state"]) for r in after["rows"]] == [
        (policy["id"], carried["id"], "CURRENT"), (uncertainty["id"], uncertainty["id"], "NEEDS_REVIEW"),
        (capability["id"], capability["id"], "NEEDS_REVIEW")]
    assert after["selected_source_provenance"]["evidence_ids"] == [inside]
    assert after["selected_source_provenance"]["basis_sha256"] == basis_sha256(t, s, [r2["id"], carried["id"]],
                                                                               [inside])
    assert after["selection_token"] != needs["selection_token"]
    between = read(known_at=iso(r2["created_at"] + timedelta(seconds=5)))
    assert [r["review_state"] for r in between["rows"]] == ["NEEDS_REVIEW"] * 3
    # The historical R1 heads are not replaced by the carry-forward.
    assert [r["revision_id"] for r in read(revision_id=str(r1["id"]))["rows"]] == [
        policy["id"], uncertainty["id"], capability["id"]]
    assert (w1_read(runner, r1["finding_id"], r1["id"]), w1_read(runner, r1["finding_id"], r2["id"])) == (
        w1_r1, w1_r2)

    # Pages (rank, created_at, id), a fixed token, and refusals.
    first = read(limit="1")
    second = read(limit="1", cursor=first["next_cursor"])
    third = read(limit="1", cursor=second["next_cursor"])
    assert [p["rows"][0]["id"] for p in (first, second, third)] == [policy["id"], uncertainty["id"], capability["id"]]
    assert third["next_cursor"] is None and first["total_count"] == second["total_count"] == 3
    assert decode_cursor(first["next_cursor"])["from"] is None
    tampered = decode_cursor(first["next_cursor"])
    tampered["selection_token"] = "sha256:" + "0" * 64
    for q, expected in (({"cursor": encode_cursor(tampered)}, "DECISION_BASIS_CHANGED"),
                        ({"cursor": "not-base64!"}, "INVALID_CURSOR"), ({"limit": "0"}, "INVALID_LIMIT"),
                        ({"known_at": iso(READ_AT + timedelta(microseconds=1))}, "INVALID_KNOWN_AT"),
                        ({"revision_id": "not-a-uuid"}, "DECISION_INPUT_INVALID"),
                        ({"revision_id": str(uuid4())}, "DECISION_NOT_FOUND"),
                        ({"known_at": iso(r1["created_at"] - timedelta(seconds=1))}, "DECISION_NOT_FOUND"),
                        # u3 7: R2 requested at a cutoff before R2 exists.
                        ({"revision_id": str(r2["id"]), "known_at": iso(k_r1)}, "DECISION_NOT_FOUND")):
        with pytest.raises(DecisionRefused) as refused:
            read(**q)
        assert refused.value.code == expected, q


def test_non_dispatch_and_wrong_domain_findings_are_refused(runner, engine) -> None:  # noqa: F811
    """N1: a cold-domain Finding and a mini-grid non-dispatch Finding (test-only replica copies of the F02 rows)."""
    t, s = runner.tenant, runner.site
    who = DecisionPrincipal("SERVICE", PRINCIPAL_ID, t, s, GRANT_PREFIX + PRINCIPAL_ID)
    steps(runner, F02["steps"][:3])
    (r1,) = finding_revisions(engine, s)
    svc = service_for(engine, Clock(r1["created_at"] + timedelta(seconds=10)))
    copies = []
    for domain, analytic in (("cold_chain", "dispatch"), ("mini_grid", "start_response")):
        nf, nr = uuid4(), uuid4()
        with engine.begin() as c:
            c.execute(text("SET LOCAL session_replication_role = replica"))
            for sql in ("CREATE TEMP TABLE f_copy ON COMMIT DROP AS SELECT * FROM finding WHERE id = :f",
                        "UPDATE f_copy SET id = :nf, domain = :d, finding_key = finding_key || :suffix",
                        "UPDATE f_copy SET subject_asset_id = gen_random_uuid(), generator_asset_id = NULL "
                        "WHERE domain = 'cold_chain'",
                        "INSERT INTO finding SELECT * FROM f_copy",
                        "CREATE TEMP TABLE r_copy ON COMMIT DROP AS SELECT * FROM finding_revision WHERE id = :r",
                        "UPDATE r_copy SET id = :nr, finding_id = :nf, analytic_id = :a, domain = :d",
                        "UPDATE r_copy SET candidate_minutes = NULL, necessary_minutes = NULL, "
                        "indeterminate_minutes = NULL WHERE domain = 'cold_chain'",
                        "INSERT INTO finding_revision SELECT * FROM r_copy"):
                c.execute(text(sql), {"f": r1["finding_id"], "r": r1["id"], "nf": nf, "nr": nr, "d": domain,
                                      "a": analytic, "suffix": "-" + domain + analytic})
        copies.append((nf, nr))
    snapshot = counts(engine)
    for nf, nr in copies:
        with pytest.raises(DecisionRefused) as listed:
            svc.list(t, s, str(nf), None, parse_list(None, None, None, [], None), "basis")
        assert listed.value.code == "DECISION_NOT_FOUND"
        with pytest.raises(DecisionRefused) as posted:
            svc.create(t, s, who, str(nf), command("w403-n1-" + str(nr)[:8], nr,
                                                  missing_evidence_reason="No record."))
        assert posted.value.code == "DECISION_LINK_SCOPE_INVALID"
    # A real dispatch revision submitted against the wrong-domain path Finding is outside that Finding's scope.
    with pytest.raises(DecisionRefused) as crossed:
        svc.create(t, s, who, str(copies[0][0]), command("w403-n1-cross", r1["id"],
                                                        missing_evidence_reason="No record."))
    assert crossed.value.code == "DECISION_LINK_SCOPE_INVALID"
    # u3 1/7: a wrong-path revision (the start_response copy) on the dispatch path Finding: 422 POST, 404 GET.
    fid, other = str(r1["finding_id"]), copies[1][1]
    with pytest.raises(DecisionRefused) as wrong_path:
        svc.create(t, s, who, fid, command("w403-n1-path", other, missing_evidence_reason="No record."))
    assert wrong_path.value.code == "DECISION_LINK_SCOPE_INVALID"
    with pytest.raises(DecisionRefused) as wrong_read:
        svc.list(t, s, fid, str(other), parse_list(None, None, None, [], None), "basis")
    assert wrong_read.value.code == "DECISION_NOT_FOUND"
    assert counts(engine) == snapshot


def test_one_command_instant_governs_basis_citation_and_recorded_at(runner, engine) -> None:  # noqa: F811
    """u3 8: the command clock, not wall time, selects the latest Finding revision, admits citations by
    `received_at` and is stored as `recorded_at` (exact six-digit UTC)."""
    t, s = runner.tenant, runner.site
    who = DecisionPrincipal("SERVICE", PRINCIPAL_ID, t, s, GRANT_PREFIX + PRINCIPAL_ID)
    steps(runner, F02["steps"])
    r1, r2 = finding_revisions(engine, s)
    with engine.connect() as c:
        late, received = c.execute(text(
            "SELECT id::text, received_at FROM accepted_evidence WHERE site_id = :s AND received_at > :a "
            "AND received_at <= :b ORDER BY received_at, id LIMIT 1"),
            {"s": s, "a": r1["created_at"], "b": r2["created_at"]}).one()
    clock = Clock(received - timedelta(microseconds=1))
    svc = service_for(engine, clock)
    fid = str(r1["finding_id"])

    def post(body):
        try:
            return svc.create(t, s, who, fid, body)
        except DecisionRefused as refused:
            return refused.status, refused.code

    cites = {"cited_accepted_evidence_ids": [late], "missing_evidence_reason": None}
    assert post(command("w403-clk-001", r1["id"], **cites)) == (422, "DECISION_LINK_SCOPE_INVALID")  # not yet received
    clock.at = received
    if received < r2["created_at"]:
        assert post(command("w403-clk-002", r2["id"], **cites)) == (409, "DECISION_BASIS_CHANGED")  # R2 not yet visible
        clock.at = r2["created_at"] - timedelta(microseconds=1)
        assert post(command("w403-clk-003", r2["id"], **cites)) == (409, "DECISION_BASIS_CHANGED")
    clock.at = r2["created_at"]
    assert post(command("w403-clk-004", r1["id"], **cites)) == (409, "DECISION_BASIS_CHANGED")  # R2 now latest
    status, body = post(command("w403-clk-005", r2["id"], **cites))
    assert status == 201 and body["finding_revision_id"] == str(r2["id"])
    assert body["recorded_at"] == iso(r2["created_at"]) and len(body["recorded_at"].split(".")[1]) == 7
    with engine.connect() as c:
        stored = c.execute(text("SELECT created_at FROM mini_alternative_revision WHERE id = :i"),
                           {"i": body["id"]}).scalar_one()
    assert stored == r2["created_at"]


def test_final_review_m3_alternative_reason_bounds_2000(runner, engine) -> None:  # noqa: F811
    """uF 4 (final review M3): Alternative `reason` is 1-2000 authored text (closure 1); `missing_evidence_reason`
    keeps u3's separate 1-500 bound."""
    t, s = runner.tenant, runner.site
    who = DecisionPrincipal("SERVICE", PRINCIPAL_ID, t, s, GRANT_PREFIX + PRINCIPAL_ID)
    steps(runner, F02["steps"][:3])
    (r1,) = finding_revisions(engine, s)
    fid = str(r1["finding_id"])
    clock = Clock(r1["created_at"] + timedelta(seconds=10))
    svc = service_for(engine, clock)

    def post(body):
        try:
            return svc.create(t, s, who, fid, body)
        except DecisionRefused as refused:
            return refused.status, refused.code

    before = counts(engine)
    assert post(command("w403-m3-over", r1["id"], reason="x" * 2001)) == (422, "DECISION_INPUT_INVALID")
    assert post(command("w403-m3-miss", r1["id"], missing_evidence_reason="m" * 501)) == (
        422, "DECISION_INPUT_INVALID")
    assert counts(engine) == before
    for key, length in (("POLICY", 500), ("UNCERTAINTY", 501), ("CAPABILITY", 2000)):
        clock.tick()
        status, body = post(command(f"w403-m3-{key.lower()}", r1["id"], key, reason="x" * length))
        assert status == 201, (key, length, body)
        with engine.connect() as c:
            stored = c.execute(text("SELECT reason FROM mini_alternative_revision WHERE id = :i"),
                               {"i": body["id"]}).scalar_one()
        assert stored == "x" * length


def test_ruled_out_interval_rule() -> None:
    """N2: strict half-open overlap; a boundary touch never qualifies; a point inside does; an empty episode never."""
    start = datetime(2026, 10, 8, 23, 20, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)
    us = timedelta(microseconds=1)
    assert not rules_out([(start - timedelta(minutes=5), start)], start, end)  # ends exactly at the start
    assert not rules_out([(end, end + us)], start, end)  # a point at the exclusive end
    assert rules_out([(start, start + us)], start, end)  # a point at the inclusive start
    assert rules_out([(start + timedelta(minutes=30), start + timedelta(minutes=30) + us)], start, end)
    assert not rules_out([(start, start + us)], start, start)  # an empty episode
    assert not rules_out([], start, end)


class _Registry:
    def __init__(self, site_type="MINIGRID"):
        self._site = SimpleNamespace(id=uuid4(), site_code="KOBO-001", site_type=site_type)

    def tenant(self):
        return SimpleNamespace(id=uuid4())

    def imported(self, code):
        return self._site if code == "KOBO-001" else None


def test_alternative_routes_refusal_order(monkeypatch) -> None:
    path = f"/api/sites/KOBO-001/findings/{uuid4()}/alternatives"
    body = command("w403-route-01", uuid4(), missing_evidence_reason="No record.")

    def api(registry=None, alternatives=None, **kw):
        app = FastAPI()
        app.include_router(build_mini_decisions_router(None, registry or _Registry(), alternatives=alternatives, **kw))
        return TestClient(app)

    missing = api().get(f"/api/sites/NOPE-1/findings/{uuid4()}/alternatives")
    assert missing.status_code == 404 and missing.json()["detail"] == {
        "code": "SITE_NOT_FOUND", "message": "No imported Site 'NOPE-1' in this tenant.", "rows": None,
        "total_count": None}
    assert api(access=lambda r, c: 403).get(path).json()["detail"]["code"] == "SITE_SCOPE_FORBIDDEN"
    assert api(access=lambda r, c: 401).post(path, json=body).json()["detail"]["code"] == "UNAUTHENTICATED"
    assert api().post(path, json=body).json()["detail"] == {
        "code": "DECISION_WRITE_FORBIDDEN", "message": "This actor cannot change decisions at this Site."}
    unavailable = api(command_access=lambda r, c: None)
    assert unavailable.get(path).status_code == 503 and unavailable.post(path, json=body).status_code == 503
    stub = AlternativeService(None, None)  # type: ignore[arg-type]  never reached: admission refuses first
    who = api(alternatives=stub, command_access=lambda r, c: None, principal=lambda r, c: None)
    refused = who.post(path, content=b"not json")
    assert refused.status_code == 403 and refused.json()["detail"]["code"] == "DECISION_WRITE_FORBIDDEN"
    cold = api(_Registry("COLD_ROOM"), stub, command_access=lambda r, c: None)
    # L1 (final review): the closure-1 literal messages.
    assert cold.post(path, json=body).json()["detail"] == {
        "code": "DECISION_LINK_SCOPE_INVALID", "message": "A cited or linked ID is outside this Site or basis."}
    # uF 8 (final review M2): a current read without `revision_id` takes the Performance gate after scope and the
    # store check: closed is 409 with W1's reason, a gate failure 503; the service is never reached. A pinned
    # `revision_id` keeps W1's audit exception and reaches the service.
    class _Reached(Exception):
        pass

    class _Spy:
        def list(self, *args):
            raise _Reached()

    def gated(gate, **kw):
        return api(alternatives=_Spy(), gate=gate, **kw)

    shut = gated(lambda code, t, s: (False, "Performance cutover is closed for this Site."))
    closed_read = shut.get(path)
    assert closed_read.status_code == 409 and closed_read.json()["detail"] == {
        "code": "PERFORMANCE_CUTOVER_CLOSED", "message": "Performance cutover is closed for this Site.", "rows": None,
        "total_count": None}
    assert shut.get(path, params={"limit": "0"}).json()["detail"]["code"] == "PERFORMANCE_CUTOVER_CLOSED"
    assert gated(lambda code, t, s: (False, "x"), access=lambda r, c: 403).get(path).status_code == 403
    assert api(gate=lambda code, t, s: (False, "x")).get(path).status_code == 503  # store check precedes the gate

    def broken(code, t, s):
        raise SiteStoreUnavailable("gate down")

    failed = gated(broken).get(path)
    assert failed.status_code == 503 and failed.json()["detail"]["code"] == "DECISION_STORE_UNAVAILABLE"
    with pytest.raises(_Reached):
        shut.get(path, params={"revision_id": str(uuid4())})
    with pytest.raises(_Reached):
        gated(lambda code, t, s: (True, "")).get(path)
    paged = gated(lambda code, t, s: (True, "")).get(path, params={"limit": "0"})
    assert paged.status_code == 422 and paged.json()["detail"] == {
        "code": "INVALID_LIMIT", "message": "Choose 1 to 100 rows.", "rows": None, "total_count": None}
    # The production composition mounts the route (W1 Finding routes do not shadow it).
    from assetops_backend import main

    monkeypatch.setenv("DATABASE_URL", URL)
    served = TestClient(main.create_app()).get(f"/api/sites/NOPE-1/findings/{uuid4()}/alternatives")
    assert served.status_code == 404 and served.json()["detail"]["code"] == "SITE_NOT_FOUND"
    assert set(served.json()["detail"]) == {"code", "message", "rows", "total_count"}
