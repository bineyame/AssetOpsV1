"""W2-03 commit 3: the cold worker over the six registered W2-02 replays, through authenticated Batch V2 intake.

`.agent/W2-03-build-spec.md` "Commits 3-5 exact contract", commit 3. Each case runs the W2-02 chain (real gateway
process, Batch V2 over TLS into the S2 ledger) in a fresh private `*_test` database; the only setup added here is
the SYSTEM attester's labelled simulated clock attestation for the lab's sources, recorded before any upload
(the cold rules need an attested source clock). Accepted rows are never inserted by hand; negative records enter
through the same gateway admit path. Needs `ASSETOPS_TEST_DATABASE_URL`; skipped (never passed) without it.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_w202_cold_replay_postgres import (  # noqa: F401 - `chain` is the W2-02 replay fixture
        CASES,
        RegisteredGatewayPublisher,
        canonical_json,
        chain,
        cold_definition,
        cold_reports,
        verify_cold_inputs,
    )

    from assetops_backend.analytics import cold
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore
    from assetops_backend.analytics.assessment_inputs import Window
    from assetops_backend.analytics.assessment_worker import ColdAssessmentWorker
    from assetops_backend.analytics.composition import build_postgres_assessment_store
    from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange

FROM = datetime(2026, 10, 6, 19, 0, tzinfo=timezone.utc)
TO = datetime(2026, 10, 6, 20, 5, tzinfo=timezone.utc)
EXC_KEY = "cold-excursion:2026-10-06T19:00:00.000000Z:2026-10-06T20:05:00.000000Z"
START_KEY = "cold-start-response:2026-10-06T19:00:00.000000Z:2026-10-06T20:05:00.000000Z"


def attest(built) -> None:
    """The SYSTEM attester's simulated clock attestation for every lab source, recorded before any upload."""
    store = PostgresAssessmentStore(URL)
    with built.engine.connect() as c:
        sources = c.execute(text("SELECT s.id FROM source s JOIN gateway g ON g.id = s.gateway_id "
                                 "WHERE g.site_id = :s ORDER BY s.id"), {"s": built.site_id}).scalars().all()
    for n, source in enumerate(sources):
        change = AttestationChange(
            event_kind="RECORDED", source_id=UUID(str(source)), sequence_epoch=f"cold-{built.case}",
            idempotency_key=f"w203-{built.case}-{n}", channel="SYSTEM_CLI", authority="lab-simulated-clock",
            label="SIMULATED demonstration clock (W2-03)", max_utc_error=timedelta(seconds=5),
            valid_from=datetime(2026, 10, 6, 0, 0, tzinfo=timezone.utc),
            valid_to=datetime(2026, 10, 8, 0, 0, tzinfo=timezone.utc))
        store.record_clock_attestation(built.tenant_id, built.site_id, change, SYSTEM_ATTESTER,
                                       datetime.now(timezone.utc), domain="cold_chain")
    store._engine.dispose()


def worker(**kw) -> ColdAssessmentWorker:
    return ColdAssessmentWorker(build_postgres_assessment_store(URL), PostgresFindingStore(URL), **kw)


def run(built, **kw) -> list:
    outcomes = worker(**kw).run_pending(tenant_id=built.tenant_id, site_id=built.site_id)
    assert outcomes and all(o.status == "DONE" for o in outcomes), outcomes
    return outcomes


def opened(case: str, chain_factory):  # noqa: F811
    built = chain_factory(case)
    attest(built)
    built.start_release_upload()
    return built


def rows(built, sql: str, **params) -> list:
    with built.engine.connect() as c:
        return [r._mapping for r in c.execute(text(sql), {"s": built.site_id, **params}).all()]


def latest(built, key: str) -> dict:
    [r] = rows(built, "SELECT revision_no, result, basis_sha256 FROM assessment_revision WHERE site_id = :s "
                      "AND assessment_key = :k ORDER BY revision_no DESC LIMIT 1", k=key)
    return {"revision_no": r["revision_no"], "basis": r["basis_sha256"], **r["result"]}


def findings(built, mechanism: str) -> list:
    return rows(built, "SELECT f.id, f.split_from_finding_id, f.subject_asset_id, f.generator_asset_id, "
                       "r.revision_no, r.transition, r.lifecycle, r.claim_level, r.claim, r.candidate_minutes "
                       "FROM finding f JOIN finding_revision r ON r.finding_id = f.id WHERE f.site_id = :s "
                       "AND f.domain = 'cold_chain' AND f.mechanism = :m ORDER BY f.created_at, r.revision_no",
                m=mechanism)


def step(chain_doc: dict, name: str) -> dict:
    return next(s for s in chain_doc["steps"] if s["step"] == name)


def report_like(built, *, device: str, minute: str, **changes) -> str:
    """A v2 device report shaped exactly like this run's own report at that device/minute, with changes."""
    revision = next(r for r in built.store.revisions(built.tenant_id, built.site_id)
                    if str(r.id) == built.run.registered_basis.foundation_revision_id)
    for r in cold_reports(verify_cold_inputs(built.run, revision, cold_definition(built.case))):
        doc = json.loads(r.report_text)
        if doc["device_id"] == device and doc["source_time"] == f"2026-10-06T19:{minute}:00Z":
            doc.update(changes)
            return canonical_json(doc)
    raise AssertionError((device, minute))


def admit(built, reports: list[str], ref: str) -> None:
    basis = built.run.registered_basis
    answer = built.process.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256, "lab_run_ref": ref,
                                               "reports": reports})
    assert {a["outcome"] for a in answer["admissions"]} == {"ADMITTED"}, answer
    built.process.link.call("seal")
    built.process.link.call("release_run", {"lab_run_ref": ref})
    while RegisteredGatewayPublisher(built.process.link).deliver(50)["batches"]["attempted"]:
        pass


@pytest.mark.parametrize("case", CASES)
def test_all_six_w202_manifests_through_intake(chain, case) -> None:  # noqa: F811
    built = opened(case, chain)
    run(built)
    if case == "late-reading":
        exc = latest(built, EXC_KEY)
        assert (exc["known_points"], exc["expected_points"]) == (12, 13)
        assert [x["anchor_time"] for x in exc["excursions"]] == ["2026-10-06T19:15:00.000000Z"]
        return  # the 20:10 recompute is test_late_recompute_keeps_history
    exc, start = latest(built, EXC_KEY), latest(built, START_KEY)
    exposure, failure = findings(built, "COLD_EXCURSION"), findings(built, "COLD_START_FAILURE")
    assert all(f["generator_asset_id"] is None and f["candidate_minutes"] is None for f in exposure + failure)
    assert rows(built, "SELECT count(*) AS n FROM financial_consequence_work w JOIN finding_revision r "
                       "ON r.id = w.finding_revision_id WHERE r.site_id = :s AND r.domain = 'cold_chain'")[0]["n"] == 0
    if case == "normal":
        assert (exc["known_points"], exc["state"], exc["claim_level"]) == (13, "NO_EXCURSION_OBSERVED", "BOUNDED")
        assert exc["excursions"] == [] and exposure == []
        [c] = start["chains"]
        assert c["result"] == "OBSERVED_SUCCESS"
        assert step(c, "START_RESULT")["at"] == "2026-10-06T19:07:00.000000Z"
        assert step(c, "TRANSFER") == {**step(c, "TRANSFER"), "state": "OBSERVED", "at": "2026-10-06T19:08:00.000000Z"}
        assert failure == []
    if case in ("excursion", "backup-failed"):
        assert (exc["known_points"], exc["state"], exc["claim_level"]) == (13, "OBSERVED_EXCURSION", "BOUNDED")
        [x] = exc["excursions"]
        assert (x["direction"], x["anchor_time"], x["open"]) == ("HIGH", "2026-10-06T19:15:00.000000Z", True)
        assert (x["start_earliest"], x["start_latest"]) == ("2026-10-06T19:10:00.000000Z",
                                                            "2026-10-06T19:15:00.000000Z")
        assert (x["end_earliest"], x["end_latest"], x["duration_low"], x["duration_high"]) == (None, None, "45", None)
        [f] = exposure
        assert (f["transition"], f["lifecycle"], f["claim_level"]) == ("OPENED", "SUPPORTED", "BOUNDED")
        episode = rows(built, "SELECT e.kind, r.duration_low, r.duration_high, r.peak_observed, r.coverage "
                              "FROM cold_episode e JOIN cold_episode_revision r ON r.episode_id = e.id "
                              "WHERE r.id = :r", r=f["claim"]["episode_revision_id"])[0]
        assert (episode["kind"], str(episode["duration_low"]), episode["duration_high"]) == ("EXCURSION", "45", None)
        assert str(episode["coverage"]) == "1.0000"
        if case == "excursion":
            assert x["peak_observed"] == "4.8"
            assert len({f["id"] for f in failure}) <= 1  # its start chain is not specified by the case
    if case == "backup-failed":
        [c] = start["chains"]
        assert (c["result"], c["claim_level"]) == ("OBSERVED_FAILURE", "OBSERVED")
        assert "TRANSFER" in c["missing_steps"] and step(c, "TRANSFER")["state"] == "MISSING"
        assert {(link["use"], link["reason"]) for link in exc["links"]
                if link["reason"] == "DOOR_EVENT"} == {("CONTEXT", "DOOR_EVENT")}
        [f] = failure
        assert (f["transition"], f["claim_level"], f["claim"]["result"]) == ("OPENED", "OBSERVED", "OBSERVED_FAILURE")
        missing = rows(built, "SELECT missing_steps FROM cold_episode_revision WHERE id = :r",
                       r=f["claim"]["episode_revision_id"])[0]["missing_steps"]
        assert "TRANSFER" in missing
    if case == "missing-probe":
        assert (exc["known_points"], exc["expected_points"], exc["state"]) == (7, 13, "UNKNOWN")
        assert exposure == []
        assert any(g["start"] == "2026-10-06T19:15:00.000000Z" and g["end"] == "2026-10-06T19:45:00.000000Z"
                   for g in exc["gaps"]), exc["gaps"]
        assert start["chains"][0]["result"] == "OBSERVED_FAILURE"
    if case == "contradictory":
        assert start["state"] == "CONTRADICTORY" and start["chains"][0]["result"] == "CONTRADICTORY"
        assert failure == []
        assert {link["reason"] for link in start["links"] if link["use"] == "EXCLUDED"} >= {"CONTRADICTORY"}


def test_late_recompute_keeps_history(chain) -> None:  # noqa: F811
    built = opened("late-reading", chain)
    run(built)
    windows = rows(built, "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE site_id = :s")
    assert [(w["window_start"], w["window_end"]) for w in windows] == [(FROM, TO)]  # one bracketed work window
    first = latest(built, EXC_KEY)
    episode_before = rows(built, "SELECT id FROM cold_episode WHERE site_id = :s AND kind = 'EXCURSION'")
    built.advance_late()
    pending = rows(built, "SELECT status FROM recompute_job WHERE site_id = :s AND domain = 'cold_chain' "
                          "AND status = 'PENDING'")
    assert pending, "the late accepted reading enqueues cold work"
    run(built)
    second = latest(built, EXC_KEY)
    assert (first["known_points"], second["known_points"]) == (12, 13)
    assert second["revision_no"] == first["revision_no"] + 1 and second["basis"] != first["basis"]
    assert rows(built, "SELECT count(*) AS n FROM assessment_revision WHERE site_id = :s AND assessment_key = :k",
                k=EXC_KEY)[0]["n"] == 2  # the old revision is retained
    assert rows(built, "SELECT id FROM cold_episode WHERE site_id = :s AND kind = 'EXCURSION'") == episode_before
    assert [x["anchor_time"] for x in second["excursions"]] == ["2026-10-06T19:15:00.000000Z"]
    [episode] = episode_before
    revisions = rows(built, "SELECT revision_no FROM cold_episode_revision WHERE episode_id = :e "
                            "ORDER BY revision_no", e=episode["id"])
    assert [r["revision_no"] for r in revisions] == [1, 2]
    transitions = [f["transition"] for f in findings(built, "COLD_EXCURSION")]
    assert transitions == ["OPENED", "SUPPORT_CHANGED"]


def test_same_basis_idempotent(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    counts = "SELECT (SELECT count(*) FROM analytic_run WHERE site_id = :s) AS runs, " \
             "(SELECT count(*) FROM assessment_revision WHERE site_id = :s) AS revisions, " \
             "(SELECT count(*) FROM cold_episode_revision WHERE site_id = :s) AS episodes, " \
             "(SELECT count(*) FROM finding_revision WHERE site_id = :s) AS findings"
    before = dict(rows(built, counts)[0])
    known = rows(built, "SELECT max(decided_at) AS k FROM ingestion_disposition WHERE site_id = :s")[0]["k"]
    w = worker()
    first = w.assess_explicit(built.tenant_id, built.site_id, Window(FROM, TO), known)
    again = w.assess_explicit(built.tenant_id, built.site_id, Window(FROM, TO), known)
    assert [r["revision_id"] for r in first.runs] == [r["revision_id"] for r in again.runs]
    assert all(not r["created"] for r in first.runs + again.runs)  # the selected job run had this exact basis
    assert dict(rows(built, counts)[0]) == before
    assert worker().run_once(built.tenant_id, built.site_id) is None  # no cold job left


def test_split_from_invalidation(chain) -> None:  # noqa: F811
    built = opened("excursion", chain)
    run(built)
    [old] = rows(built, "SELECT id FROM cold_episode WHERE site_id = :s AND kind = 'EXCURSION'")
    [old_finding] = {f["id"] for f in findings(built, "COLD_EXCURSION")}
    # A later-accepted GOOD in-band reading at 19:17 breaks the 19:15 confirmation: 19:15 is no longer the first
    # qualifying crossing, and the excursion re-anchors on the 19:20/19:25 pair (a new episode split from the old).
    report = report_like(built, device="chamber-probe", minute="15", report_key="cold:" + "e" * 64,
                         source_time="2026-10-06T19:17:00Z", value="3.5")
    admit(built, [report], "split-probe")
    run(built)
    episodes = rows(built, "SELECT id, split_from_episode_id, anchor_time FROM cold_episode WHERE site_id = :s "
                           "AND kind = 'EXCURSION' ORDER BY created_at")
    assert len(episodes) == 2 and episodes[1]["split_from_episode_id"] == old["id"]
    assert episodes[1]["anchor_time"] == datetime(2026, 10, 6, 19, 20, tzinfo=timezone.utc)
    tail = rows(built, "SELECT claim_level, lower_start FROM cold_episode_revision WHERE episode_id = :e "
                       "ORDER BY revision_no DESC LIMIT 1", e=old["id"])[0]
    assert (tail["claim_level"], tail["lower_start"]) == ("UNKNOWN", None)
    assert not rows(built, "SELECT 1 FROM cold_episode_evidence x JOIN cold_episode_revision r "
                           "ON r.id = x.episode_revision_id WHERE r.episode_id = :e AND r.revision_no = 2", e=old["id"])
    revisions = findings(built, "COLD_EXCURSION")
    old_tail = [f for f in revisions if f["id"] == old_finding][-1]
    assert (old_tail["transition"], old_tail["lifecycle"]) == ("NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED")
    # The ad hoc reading enters through the gateway outside the registered run publication, so the S4-05 gate of
    # the window becomes MIXED: the re-anchored excursion is POSSIBLE and opens no Finding (a closed gate never
    # becomes a positive Finding), so no new Finding carries `split_from_finding_id` here.
    exc = latest(built, EXC_KEY)
    assert exc["source_gate"]["classification"] == "MIXED" and exc["source_gate"]["permitted"] is False
    [x] = exc["excursions"]
    assert (x["anchor_time"], x["claim_level"], x["exposure_finding"]) == ("2026-10-06T19:20:00.000000Z",
                                                                          "POSSIBLE", False)
    assert [f for f in revisions if f["id"] != old_finding] == []


def test_worker_retry_atomic(chain, monkeypatch) -> None:  # noqa: F811
    built = opened("backup-failed", chain)
    projected = ("SELECT (SELECT count(*) FROM analytic_run WHERE site_id = :s) + "
                 "(SELECT count(*) FROM cold_episode WHERE site_id = :s) + "
                 "(SELECT count(*) FROM cold_episode_revision WHERE site_id = :s) + "
                 "(SELECT count(*) FROM finding WHERE site_id = :s) AS n")
    original = PostgresFindingStore.cold_apply

    def failing(self, *args, **kwargs):
        original(self, *args, **kwargs)  # Finding rows are written in the shared transaction, then it fails
        raise RuntimeError("injected failure after the Finding write")

    monkeypatch.setattr(PostgresFindingStore, "cold_apply", failing)
    [outcome] = worker(backoff=timedelta(0)).run_pending(limit=1, tenant_id=built.tenant_id, site_id=built.site_id)
    assert outcome.status == "RETRY" and "injected failure" in outcome.error
    assert rows(built, projected)[0]["n"] == 0  # nothing of the projection survived
    [job] = rows(built, "SELECT status, attempts, last_error FROM recompute_job WHERE id = :j", j=outcome.job_id)
    assert (job["status"], job["attempts"]) == ("PENDING", 1) and "injected failure" in job["last_error"]
    monkeypatch.setattr(PostgresFindingStore, "cold_apply", original)
    run(built)
    assert rows(built, projected)[0]["n"] > 0
    assert len({f["id"] for f in findings(built, "COLD_START_FAILURE")}) == 1
    assert {r["status"] for r in rows(built, "SELECT status FROM recompute_job WHERE site_id = :s "
                                             "AND domain = 'cold_chain'")} == {"DONE"}


def test_equal_event_id_conflict_not_support(chain) -> None:  # noqa: F811
    built = opened("normal", chain)
    run(built)
    jobs_before = rows(built, "SELECT count(*) AS n FROM recompute_job WHERE site_id = :s AND domain = 'cold_chain'")
    accepted_before = rows(built, "SELECT count(*) AS n FROM accepted_evidence WHERE site_id = :s")
    # EVENT_ID_CONFLICT: the accepted START_RESULT's event ID with the opposite outcome under a new report key.
    conflict = report_like(built, device="generator-controller", minute="07", report_key="cold:" + "f" * 64,
                           outcome="FAILED")
    admit(built, [conflict], "conflict-probe")
    assert rows(built, "SELECT count(*) AS n FROM accepted_evidence WHERE site_id = :s") == accepted_before
    assert rows(built, "SELECT count(*) AS n FROM ingestion_disposition WHERE site_id = :s "
                       "AND decision = 'CONFLICT'")[0]["n"] == 1
    # The conflicting ordinal enqueues nothing and changes no claim.
    assert rows(built, "SELECT count(*) AS n FROM recompute_job WHERE site_id = :s AND domain = 'cold_chain'") == \
        jobs_before
    assert worker().run_once(built.tenant_id, built.site_id) is None
    [c] = latest(built, START_KEY)["chains"]
    assert c["result"] == "OBSERVED_SUCCESS" and findings(built, "COLD_START_FAILURE") == []
    accepted = {str(r["id"]) for r in rows(built, "SELECT id FROM accepted_evidence WHERE site_id = :s")}
    linked = {str(r["evidence_id"]) for r in rows(built, "SELECT evidence_id FROM cold_episode_evidence "
                                                         "WHERE site_id = :s")}
    assert linked and linked <= accepted
    # A SUSPECT chamber reading through the same intake stays linked as CONTEXT, never SUPPORT.
    suspect = report_like(built, device="chamber-probe", minute="10", report_key="cold:" + "d" * 64,
                          source_time="2026-10-06T19:12:00Z", value="9.9", quality="SUSPECT")
    admit(built, [suspect], "suspect-probe")
    run(built)
    exc = latest(built, EXC_KEY)
    [sus] = [r["id"] for r in rows(built, "SELECT id FROM accepted_evidence WHERE site_id = :s AND quality = 'SUSPECT' "
                                          "AND role = :r", r=cold.PROBE_ROLE)]
    assert {(link["use"], link["reason"]) for link in exc["links"] if link["evidence_id"] == str(sus)} == \
        {("CONTEXT", "SUSPECT")}
    assert exc["state"] == "NO_EXCURSION_OBSERVED"


def test_split_links_finding_when_gate_permits(chain, monkeypatch) -> None:  # noqa: F811
    """L3 `finding.split_from_finding_id`: the same intake-driven split, with the S4-05 classification held at
    the run's registered class by a test-only double (the ad hoc reading cannot join the registered publication),
    opens the re-anchored Finding split from the withdrawn one."""
    import assetops_backend.analytics.adapters.postgres_assessment_store as module

    real = module.classify
    monkeypatch.setattr(module, "classify", lambda ids, links: {**real(ids, links), "state": "REGISTERED_SIMULATION"})
    built = opened("excursion", chain)
    run(built)
    [old_finding] = {f["id"] for f in findings(built, "COLD_EXCURSION")}
    report = report_like(built, device="chamber-probe", minute="15", report_key="cold:" + "e" * 64,
                         source_time="2026-10-06T19:17:00Z", value="3.5")
    admit(built, [report], "split-probe")
    run(built)
    episodes = rows(built, "SELECT id, split_from_episode_id FROM cold_episode WHERE site_id = :s "
                           "AND kind = 'EXCURSION' ORDER BY created_at")
    revisions = findings(built, "COLD_EXCURSION")
    assert [f["transition"] for f in revisions if f["id"] == old_finding] == ["OPENED", "NO_LONGER_SUPPORTED"]
    [new] = [f for f in revisions if f["id"] != old_finding]
    assert (new["split_from_finding_id"], new["transition"], new["claim_level"]) == (old_finding, "OPENED", "BOUNDED")
    assert new["claim"]["episode_id"] == str(episodes[1]["id"]) and episodes[1]["split_from_episode_id"] == episodes[0]["id"]
