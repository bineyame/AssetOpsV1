"""W2-06 commit 3: the `ev-session/1` writer, recompute and Finding through ordinary accepted replay.

Each case runs the W2-05b registered chain (`test_w205b_ev_replay_postgres.py:Chain`, its pinned `hold_uuids`
counter and simulated clock attestation), then the EV worker leases the jobs the accepted-evidence trigger
enqueued and persists run, assessment, session, interval and Finding rows in one transaction. Persisted values
must equal the pinned public vectors (`backend/tests/fixtures/w2/ev-w206-vectors.json`, q2 R12 / q4).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from test_w205b_ev_replay_postgres import (  # noqa: F401 - `chain` is the shared fixture
    ATTEST_FROM,
    ATTEST_TO,
    ATTESTED_AT,
    CASES,
    SELECTED,
    URL,
    VECTORS,
    Chain,
    _connector_asset,
    chain,
    watermark,
)

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text

    from assetops_backend.analytics import ev
    from assetops_backend.analytics.adapters import postgres_assessment_store
    from assetops_backend.analytics.adapters.postgres_assessment_store import EvReadService, PostgresAssessmentStore
    from assetops_backend.analytics.adapters.postgres_finding_store import (
        EV_LIMITATIONS,
        EV_WITHDRAWN,
        PostgresFindingStore,
    )
    from assetops_backend.analytics.assessment_inputs import Window
    from assetops_backend.analytics.assessment_worker import EvAssessmentWorker
    from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange
    from assetops_backend.analytics.composition import build_ev_assessment_worker

EV_TABLES = ("ev_session", "ev_session_revision", "ev_session_evidence", "ev_meter_interval")
COUNTED = ("analytic_run", "assessment_revision", "analytic_run_selection", "finding", "finding_revision",
           "finding_revision_evidence") + EV_TABLES


def _vectors() -> dict:
    return json.loads(VECTORS.read_text(encoding="utf-8"))["cases"]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _normalize(value):
    if isinstance(value, str) and value.endswith("Z") and "T" in value:
        return ev.plain(_instant(value))
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def _dispose(worker) -> None:
    for store in (worker.store, worker.findings):
        if getattr(store, "_engine", None) is not None:
            store._engine.dispose()


def run_worker(built: Chain, worker=None) -> list:
    """Lease and run every pending EV job of the Site; every outcome must be DONE."""
    own = worker is None
    worker = worker or build_ev_assessment_worker(URL)
    try:
        outcomes = worker.run_pending(tenant_id=built.tenant_id, site_id=built.site_id)
    finally:
        if own:
            _dispose(worker)
    assert outcomes and all(o.status == "DONE" for o in outcomes), [(o.status, o.error) for o in outcomes]
    return outcomes


def counts(built: Chain) -> dict[str, int]:
    with built.engine.connect() as c:
        out = {t: c.execute(text(f"SELECT count(*) FROM {t} WHERE site_id = :s"), {"s": built.site_id}).scalar_one()
               for t in COUNTED}
        out["analytic_run_evidence"] = c.execute(text(
            "SELECT count(*) FROM analytic_run_evidence WHERE site_id = :s"), {"s": built.site_id}).scalar_one()
    return out


def revisions(built: Chain, connector_asset: str) -> list:
    with built.engine.connect() as c:
        return c.execute(text(
            "SELECT r.* FROM ev_session_revision r JOIN ev_session e ON e.id = r.session_id "
            "WHERE e.tenant_id = :t AND e.site_id = :s AND e.connector_asset_id = :co ORDER BY r.revision_no"),
            {"t": built.tenant_id, "s": built.site_id, "co": connector_asset}).all()


def persisted(built: Chain, rev) -> dict:
    """The vector `expected` keys a session revision stores (energy_complete is a read value; raw accepted kWh and
    Finding support live elsewhere)."""
    with built.engine.connect() as c:
        intervals = c.execute(text(
            "SELECT evidence_id, connector_asset_id, start_at, end_at, kwh, error_bound_kwh, use, reason "
            "FROM ev_meter_interval WHERE revision_id = :r ORDER BY start_at, evidence_id"), {"r": rev.id}).all()
    end = None if rev.end_earliest is None and rev.end_latest is None else \
        {"earliest": ev.plain(rev.end_earliest), "latest": ev.plain(rev.end_latest)}
    return {
        "state": rev.state, "start_at": ev.plain(rev.start_at), "end_at": ev.plain(rev.end_at),
        "start_bounds": {"earliest": ev.plain(rev.start_earliest), "latest": ev.plain(rev.start_latest)},
        "end_bounds": end, "supported_kwh": None if rev.supported_kwh is None else format(rev.supported_kwh, "f"),
        "unknown_meter_seconds": rev.unknown_meter_seconds, "reason_codes": list(rev.reason_codes),
        "fault_evidence_id": ev.plain(rev.fault_evidence_id),
        "intervals": [{"evidence_id": str(i.evidence_id), "connector_asset_id": str(i.connector_asset_id),
                       "start_at": ev.plain(i.start_at), "end_at": ev.plain(i.end_at), "kwh": format(i.kwh, "f"),
                       "error_bound_kwh": format(i.error_bound_kwh, "f"), "use": i.use, "reason": i.reason}
                      for i in intervals],
    }


def split_expected(expected: dict) -> tuple[dict, dict]:
    wanted = _normalize(dict(expected))
    other = {k: wanted.pop(k) for k in ("energy_complete", "finding_support_evidence_ids", "raw_accepted_kwh")}
    wanted["intervals"] = sorted(wanted["intervals"], key=lambda i: (i["start_at"], i["evidence_id"]))
    return wanted, other


def projected_session(outcomes: list, connector_asset: str):
    found = [s for o in outcomes for p in o.runs if p.run["created"] for s in p.assessment.sessions
             if str(s.connector_asset_id) == connector_asset]
    return found[-1]


def findings(built: Chain) -> list:
    with built.engine.connect() as c:
        return c.execute(text(
            "SELECT f.id, f.finding_key, f.domain, f.mechanism, f.analytic_id, f.generator_asset_id, "
            "f.subject_asset_id, f.anchor_start, f.matcher_version, r.id AS revision_id, r.revision_no, "
            "r.transition, r.lifecycle, r.claim_level, r.title, r.episode_start, r.episode_end, "
            "r.candidate_minutes, r.necessary_minutes, r.indeterminate_minutes, r.claim, r.limitations, "
            "r.basis_sha256, r.input_evidence_sha256, r.support_sha256, r.cited_evidence_sha256, "
            "r.assessment_revision_id, r.analytic_run_id, r.window_assessment_revision_id, "
            "(SELECT coalesce(json_agg(x.evidence_id ORDER BY x.evidence_id), '[]'::json) "
            " FROM finding_revision_evidence x WHERE x.finding_revision_id = r.id) AS support "
            "FROM finding f JOIN finding_revision r ON r.finding_id = f.id WHERE f.site_id = :s "
            "ORDER BY f.id, r.revision_no"), {"s": built.site_id}).all()


def run_input(built: Chain, run_id) -> dict:
    with built.engine.connect() as c:
        return c.execute(text("SELECT * FROM analytic_run WHERE id = :r"), {"r": run_id}).mappings().one()


# --- the six cases ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_six_cases_persist_the_vectors(chain, case) -> None:
    vector = _vectors()[case]
    built = chain(case)
    built.start_release_upload()
    asset = _connector_asset(built, SELECTED[case])
    if case == "missing-meter":
        _failed_job_rolls_back(built)
    outcomes = run_worker(built)
    rev = revisions(built, asset)
    if case == "late-record":
        first, other = split_expected({k: v for k, v in vector["first_cutoff"].items()
                                       if k not in ("known_at", "accepted_evidence_ids")})
        assert len(rev) == 1 and persisted(built, rev[0]) == first
        assert projected_session(outcomes, asset).energy_complete is other["energy_complete"] is False
        first_run = outcomes[-1].runs[-1].run
        assert ev.plain(run_input(built, first_run["run_id"])["knowledge_cutoff"]) == \
            ev.plain(_instant(vector["first_cutoff"]["known_at"]))
        with built.engine.connect() as c:
            linked = sorted(str(x) for x in c.execute(text(
                "SELECT evidence_id FROM analytic_run_evidence WHERE run_id = :r"),
                {"r": first_run["run_id"]}).scalars())
        assert linked == vector["first_cutoff"]["accepted_evidence_ids"]
        built.advance_late()
        outcomes = run_worker(built)
        rev = revisions(built, asset)
        assert [r.state for r in rev] == ["INCOMPLETE", "COMPLETED"] and [r.revision_no for r in rev] == [1, 2]
        _late_history_selectable(built, first_run, outcomes[-1].runs[-1].run)
    wanted, other = split_expected(vector["expected"])
    assert persisted(built, rev[-1]) == wanted, case
    session = projected_session(outcomes, asset)
    assert session.energy_complete is other["energy_complete"], case
    assert session.basis_sha256 == rev[-1].basis_sha256
    rows = findings(built)
    if case == "interrupted":
        _interrupted_finding(built, rows, rev[-1], session, other["finding_support_evidence_ids"])
    else:
        assert rows == [], case
    if case == "fault":
        c1 = _connector_asset(built, "c1")
        assert revisions(built, c1) == []  # c1 FAULT/CLEAR are window context; no c1 session
    if case == "complete":
        _idempotent_replay(built, outcomes)
        _orphan_only_selection(built)


def _late_history_selectable(built: Chain, first_run: dict, final_run: dict) -> None:
    """09:00 INCOMPLETE then 09:05 COMPLETED: one assessment key, revisions 1 and 2, both runs selected in turn,
    the first still reachable at its own knowledge cutoff. (The install-time configuration enqueue seeds its own
    empty bracket window, which is a separate selection.)"""
    with built.engine.connect() as c:
        heads = c.execute(text(
            "SELECT s.run_id, r.knowledge_cutoff, v.revision_no, v.assessment_key FROM analytic_run_selection s "
            "JOIN analytic_run r ON r.id = s.run_id JOIN analytic_run_assessment x ON x.run_id = r.id "
            "JOIN assessment_revision v ON v.id = x.assessment_revision_id WHERE s.site_id = :s "
            "AND s.analytic_id = 'ev-session/1' AND s.window_start = :ws ORDER BY s.selected_at"),
            {"s": built.site_id, "ws": run_input(built, first_run["run_id"])["window_start"]}).all()
    assert [h.run_id for h in heads] == [first_run["run_id"], final_run["run_id"]]
    assert [ev.plain(h.knowledge_cutoff) for h in heads] == ["2026-10-06T09:00:00.000000Z",
                                                             "2026-10-06T09:05:00.000000Z"]
    assert [h.revision_no for h in heads] == [1, 2] and len({h.assessment_key for h in heads}) == 1
    assert final_run["previous_revision_id"] == first_run["revision_id"]


def _interrupted_finding(built: Chain, rows: list, rev, session, support_ids: list[str]) -> None:
    [row] = rows
    assert (row.domain, row.mechanism, row.analytic_id, row.generator_asset_id, row.matcher_version) == \
        ("ev_charging", "EV_INTERRUPTION", "ev-session/1", None, "1")
    assert str(row.subject_asset_id) == str(session.connector_asset_id) and row.anchor_start == session.start_at
    assert row.finding_key == session.finding_key_sha256
    assert (row.revision_no, row.transition, row.lifecycle, row.claim_level, row.title) == \
        (1, "OPENED", "SUPPORTED", "OBSERVED", "Observed EV charging interruption")
    assert (row.episode_start, row.episode_end) == (session.start_at, session.end_at)
    assert (row.candidate_minutes, row.necessary_minutes, row.indeterminate_minutes) == (None, None, None)
    assert row.window_assessment_revision_id is None and row.assessment_revision_id == rev.assessment_revision_id
    # Exactly three sorted support IDs: START, the contemporaneous FAULT and ABORT.
    assert row.support == sorted(support_ids) and len(row.support) == 3
    assert row.support_sha256 == row.cited_evidence_sha256 == session.finding_support_sha256
    assert row.basis_sha256 == row.input_evidence_sha256 == run_input(built, row.analytic_run_id)["input_sha256"]
    assert row.limitations == list(EV_LIMITATIONS)
    assert row.claim == ev.plain({
        "session_id": rev.session_id, "external_session_id": session.external_session_id,
        "connector_asset_id": session.connector_asset_id, "start_at": session.start_at, "abort_at": session.end_at,
        "fault_evidence_id": session.fault_evidence_id, "supported_kwh": session.supported_kwh,
        "energy_complete": True})
    _withdrawal(built, row)


def _withdrawal(built: Chain, opened) -> None:
    """Revoking the FAULT source's clock proof (recorded by the selected cutoff) withdraws support: the new basis
    appends NO_LONGER_SUPPORTED with no support links; the Finding and its first revision stay."""
    with built.engine.connect() as c:
        fault_source = c.execute(text("SELECT source_id FROM accepted_evidence WHERE id = :e"),
                                 {"e": opened.claim["fault_evidence_id"]}).scalar_one()
        attestation_id, version = c.execute(text(
            "SELECT attestation_id, version FROM source_clock_attestation WHERE site_id = :s AND source_id = :src "
            "ORDER BY version DESC LIMIT 1"), {"s": built.site_id, "src": fault_source}).one()
    store = PostgresAssessmentStore(URL)
    try:
        store.record_clock_attestation(built.tenant_id, built.site_id, AttestationChange(
            event_kind="REVOKED", source_id=fault_source, sequence_epoch=f"ev-{built.case}",
            idempotency_key="w206-withdraw", channel="SYSTEM_CLI", attestation_id=attestation_id,
            expected_version=version, reason="W2-06 withdrawal proof"), SYSTEM_ATTESTER, watermark(built),
            domain="ev_charging")
    finally:
        store._engine.dispose()
    run_worker(built)
    first, withdrawn = findings(built)
    assert first.revision_id == opened.revision_id and first.transition == "OPENED"
    assert (withdrawn.revision_no, withdrawn.transition, withdrawn.lifecycle, withdrawn.claim_level) == \
        (2, "NO_LONGER_SUPPORTED", "NO_LONGER_SUPPORTED", "UNKNOWN")
    assert withdrawn.support == [] and withdrawn.support_sha256 == ev.EMPTY_SUPPORT_SHA256
    assert withdrawn.cited_evidence_sha256 == ev.EMPTY_SUPPORT_SHA256
    assert (withdrawn.episode_start, withdrawn.episode_end) == (opened.episode_start, opened.episode_end)
    assert withdrawn.claim == {**opened.claim, "fault_evidence_id": None, "supported_kwh": None,
                               "energy_complete": None}
    assert withdrawn.limitations == list(EV_LIMITATIONS) + [EV_WITHDRAWN]
    assert withdrawn.basis_sha256 != opened.basis_sha256


def _idempotent_replay(built: Chain, outcomes: list) -> None:
    """The same window at the same committed cutoff: the existing IDs, nothing appended (no selected head)."""
    before = counts(built)
    run = outcomes[-1].runs[-1].run
    store = PostgresAssessmentStore(URL)
    try:
        with built.engine.connect() as c:
            ws, we = c.execute(text("SELECT window_start, window_end FROM analytic_run WHERE id = :r"),
                               {"r": run["run_id"]}).one()
        store.enqueue(built.tenant_id, built.site_id, "ev_charging", Window(ws, we),
                      datetime(2026, 10, 6, 9, 30, tzinfo=timezone.utc))
    finally:
        store._engine.dispose()
    [again] = run_worker(built)
    [projection] = again.runs
    assert projection.run["created"] is False
    assert (projection.run["run_id"], projection.run["revision_id"]) == (run["run_id"], run["revision_id"])
    assert projection.sessions == () and projection.finding_revision_ids == ()
    assert counts(built) == before


def _orphan_only_selection(built: Chain) -> None:
    """An explicit window holding the END but not its START: NO_SESSIONS_OBSERVED with orphan > 0, no session
    revision or Finding, and the DEFAULT selection untouched."""
    before = counts(built)
    worker = build_ev_assessment_worker(URL)
    try:
        projection = worker.assess_explicit(built.tenant_id, built.site_id,
                                            Window(datetime(2026, 10, 6, 8, 30, tzinfo=timezone.utc),
                                                   datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc)))
    finally:
        _dispose(worker)
    assert projection.run["created"] is True and projection.sessions == ()
    with built.engine.connect() as c:
        result, claim, selection = c.execute(text(
            "SELECT v.result, v.claim_level, r.selection FROM assessment_revision v JOIN analytic_run r "
            "ON r.id = v.analytic_run_id WHERE v.id = :v"), {"v": projection.run["revision_id"]}).one()
    assert (result["status"]["state"], claim, selection) == ("NO_SESSIONS_OBSERVED", "UNKNOWN", "EXPLICIT")
    assert result["denominator"]["started"] == 0 and result["denominator"]["orphan"] >= 1
    assert result["session_revision_ids"] == []
    after = counts(built)
    for table in EV_TABLES + ("finding", "finding_revision", "analytic_run_selection"):
        assert after[table] == before[table], table
    assert after["assessment_revision"] == before["assessment_revision"] + 1


def _failed_job_rolls_back(built: Chain) -> None:
    """A failure after session rows were written rolls the whole projection back; fail_job records FAILED."""

    class Boom:
        def ev_apply(self, *args, **kwargs):
            raise RuntimeError("Finding store unavailable (test)")

    worker = EvAssessmentWorker(build_ev_assessment_worker(URL).store, Boom(), max_attempts=1)
    try:
        outcome = worker.run_once(built.tenant_id, built.site_id)
    finally:
        _dispose(worker)
    assert outcome is not None and outcome.status == "FAILED"
    assert "Finding store unavailable" in outcome.error
    assert counts(built) == dict.fromkeys(COUNTED + ("analytic_run_evidence",), 0)
    with built.engine.connect() as c:
        job = c.execute(text("SELECT status, last_error, window_start, window_end FROM recompute_job "
                             "WHERE id = :j"), {"j": outcome.job_id}).one()
    assert job.status == "FAILED" and "Finding store unavailable" in job.last_error
    retry = PostgresAssessmentStore(URL)
    try:
        retry.enqueue(built.tenant_id, built.site_id, "ev_charging", Window(job.window_start, job.window_end),
                      datetime(2026, 10, 6, 9, 30, tzinfo=timezone.utc))
    finally:
        retry._engine.dispose()


# --- r8 H1: exact selected windows re-head at their exact bounds ------------------------------------------

LATE_LO = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)
#: The late-record START is 08:01 and its late END 08:31 (accepted at 09:05): an exact selected window ending at
#: 08:30 puts that terminal past the selected end, through the ordinary registered replay (no manifest change).
LATE_HI = datetime(2026, 10, 6, 8, 30, tzinfo=timezone.utc)


def select_exact(built: Chain, lo: datetime, hi: datetime) -> None:
    """A DEFAULT selection of exactly `[lo,hi)` at the committed cutoff, written by the production EV writer over
    the accepted replay (the shape any earlier job's window would have left)."""
    worker = build_ev_assessment_worker(URL)
    try:
        with worker.store.transaction() as c:
            cutoff = worker.store.ev_watermark(c, built.tenant_id, built.site_id)
            worker._project(c, built.tenant_id, built.site_id, Window(lo, hi), cutoff, job_id=None,
                            selection="DEFAULT")
    finally:
        _dispose(worker)


def exact_heads(built: Chain, lo: datetime, hi: datetime) -> list:
    with built.engine.connect() as c:
        return c.execute(text(
            "SELECT s.run_id, s.job_id, v.id AS revision_id, v.revision_no, v.basis_sha256 "
            "FROM analytic_run_selection s JOIN analytic_run_assessment x ON x.run_id = s.run_id "
            "JOIN assessment_revision v ON v.id = x.assessment_revision_id WHERE s.site_id = :s "
            "AND s.analytic_id = 'ev-session/1' AND s.window_start = :lo AND s.window_end = :hi ORDER BY s.seq"),
            {"s": built.site_id, "lo": lo, "hi": hi}).all()


def selected_windows(built: Chain) -> set:
    with built.engine.connect() as c:
        return {(r[0], r[1]) for r in c.execute(text(
            "SELECT DISTINCT window_start, window_end FROM analytic_run_selection WHERE site_id = :s "
            "AND analytic_id = 'ev-session/1'"), {"s": built.site_id}).all()}


def exact_read(built: Chain, lo: datetime, hi: datetime) -> dict:
    reads = EvReadService(URL)
    try:
        return reads.sessions(built.tenant_id, built.site_id, "EV-LAB-001", lo, hi, None, None, 50)
    finally:
        reads.dispose()


def run_spying(built: Chain, lo: datetime, hi: datetime) -> tuple[list, dict]:
    """Run every pending EV job; while each is LEASED (inside `ev_windows`), read the exact window's state."""
    worker = build_ev_assessment_worker(URL)
    seen: dict = {"windows": [], "status": [], "state": []}
    original = worker.store.ev_windows

    def spy(c, lease):
        windows = original(c, lease)
        seen["windows"].append([(w.start, w.end) for w in windows])
        with built.engine.connect() as r:
            seen["status"].append(r.execute(text("SELECT status FROM recompute_job WHERE id = :j"),
                                            {"j": lease.job_id}).scalar_one())
        seen["state"].append(exact_read(built, lo, hi)["currentness"]["state"])
        return windows

    worker.store.ev_windows = spy
    try:
        return run_worker(built, worker), seen
    finally:
        _dispose(worker)


def test_late_terminal_past_selected_end_reheads_exact_window(chain) -> None:  # noqa: F811
    built = chain("late-record")
    built.start_release_upload()
    run_worker(built)
    select_exact(built, LATE_LO, LATE_HI)
    [before] = exact_heads(built, LATE_LO, LATE_HI)
    first = exact_read(built, LATE_LO, LATE_HI)
    assert first["currentness"]["state"] == "CURRENT"
    assert [i["state"] for i in first["items"]] == ["INCOMPLETE"] and first["items"][0]["end_at"] is None
    preexisting = selected_windows(built)
    built.advance_late()
    _outcomes, seen = run_spying(built, LATE_LO, LATE_HI)
    # The old head is pending while the job is leased; the exact window is re-assessed at its exact bounds.
    assert seen["status"] and set(seen["status"]) == {"LEASED"}
    assert set(seen["state"]) == {"PENDING_RECOMPUTE"}
    assert any((LATE_LO, LATE_HI) in windows for windows in seen["windows"])
    # Nothing new stands in for the exact key: every covering window the job assessed was already selected.
    for windows in seen["windows"]:
        assert all((a, b) in preexisting for a, b in windows if a <= LATE_LO and LATE_HI <= b
                   and (a, b) != (LATE_LO, LATE_HI))
    heads = exact_heads(built, LATE_LO, LATE_HI)
    assert heads[0].run_id == before.run_id and len(heads) == 2
    after = heads[-1]
    assert after.job_id is not None and after.revision_no == before.revision_no + 1
    assert after.basis_sha256 != before.basis_sha256
    # No covering-only selection was written by the job in place of the exact key.
    with built.engine.connect() as c:
        written = c.execute(text(
            "SELECT window_start, window_end FROM analytic_run_selection WHERE site_id = :s AND job_id = :j"),
            {"s": built.site_id, "j": after.job_id}).all()
    assert (LATE_LO, LATE_HI) in [(w[0], w[1]) for w in written]
    assert all((w[0], w[1]) in preexisting for w in written
               if w[0] <= LATE_LO and LATE_HI <= w[1] and (w[0], w[1]) != (LATE_LO, LATE_HI))
    read = exact_read(built, LATE_LO, LATE_HI)
    assert read["currentness"]["state"] == "CURRENT"
    assert read["source_provenance"]["basis_sha256"] == after.basis_sha256
    [item] = read["items"]
    # The late same-session terminal outside the selected end is correlation input for the START inside it.
    assert item["state"] == "COMPLETED" and ev.plain(_instant(item["end_at"])) == "2026-10-06T08:31:00.000000Z"
    assert read["denominator"]["started"] == 1 and read["denominator"]["orphan"] == 0


# --- clock proof ------------------------------------------------------------------------------------------


def test_clock_unattested_missing_wrong_epoch_and_expired(chain, monkeypatch) -> None:
    """q3 P1: only an effective attestation for the row's source, epoch and whole interval supports it. The
    session events keep their real proof; the meter's proof names another epoch, the connector controller has
    none and the Site meter's expired before the window: each such linked record is EXCLUDED CLOCK_UNATTESTED."""
    expired_to = datetime(2026, 10, 6, 8, 0, tzinfo=timezone.utc)

    def attest(self) -> None:
        with self.engine.connect() as c:
            sources = dict(c.execute(text(
                "SELECT DISTINCT source_id, device_id FROM signal_binding_revision WHERE site_id = :s"),
                {"s": self.site_id}).all())
        store = PostgresAssessmentStore(URL)
        patched = postgres_assessment_store.uuid4
        postgres_assessment_store.uuid4 = __import__("uuid").uuid4
        try:
            for n, (source, device) in enumerate(sorted(sources.items(), key=lambda kv: kv[1])):
                if device == "c1-connector-controller":
                    continue  # missing proof
                epoch = "ev-other" if device == "c1-connector-meter" else f"ev-{self.case}"
                valid_to = expired_to if device == "site-meter" else ATTEST_TO
                store.record_clock_attestation(self.tenant_id, self.site_id, AttestationChange(
                    event_kind="RECORDED", source_id=UUID(str(source)), sequence_epoch=epoch,
                    idempotency_key=f"w206-clock-{n}", channel="SYSTEM_CLI", authority="lab-simulated-clock",
                    label="SIMULATED demonstration clock (W2-06)", max_utc_error=timedelta(seconds=5),
                    valid_from=ATTEST_FROM, valid_to=valid_to), SYSTEM_ATTESTER, ATTESTED_AT, domain="ev_charging")
        finally:
            postgres_assessment_store.uuid4 = patched
            store._engine.dispose()

    monkeypatch.setattr(Chain, "attest", attest)
    built = chain("complete")
    built.start_release_upload()
    run_worker(built)
    [rev] = revisions(built, _connector_asset(built, "c1"))
    assert rev.state == "COMPLETED" and rev.supported_kwh is None and rev.unknown_meter_seconds == 1800
    assert "CLOCK_UNATTESTED" in rev.reason_codes and "METER_GAP" in rev.reason_codes
    with built.engine.connect() as c:
        links = c.execute(text(
            "SELECT e.device_id, e.record_kind, x.use, x.reason FROM ev_session_evidence x JOIN accepted_evidence e "
            "ON e.id = x.evidence_id WHERE x.revision_id = :r"), {"r": rev.id}).all()
        meters = c.execute(text("SELECT use, reason FROM ev_meter_interval WHERE revision_id = :r"),
                           {"r": rev.id}).all()
    by_device: dict[str, set] = {}
    for device, _, use, reason in links:
        by_device.setdefault(device, set()).add((use, reason))
    assert {(r.record_kind, r.use) for r in links if r.device_id == "c1-charger-controller"} == {
        ("EV_SESSION_START", "SUPPORT"), ("EV_SESSION_END", "SUPPORT")}
    for device in ("c1-connector-meter", "c1-connector-controller", "site-meter"):  # wrong epoch, missing, expired
        assert by_device.get(device) == {("EXCLUDED", "CLOCK_UNATTESTED")}, (device, by_device.get(device))
    assert len(meters) == 7 and set(meters) == {("EXCLUDED", "CLOCK_UNATTESTED")}
    assert findings(built) == []
