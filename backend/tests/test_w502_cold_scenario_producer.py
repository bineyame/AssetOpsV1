"""W5-02a K1c item 29: the test-only cold generated-scenario producer through the ordinary W2 chain.

`.agent/W5-02-build-spec.md` "W5-02a build rulings (K1c)" 2 and 3. In a fresh private `*_test` database the existing
`install_cold_lab` imports COLD-LAB-001; `tools/w502_cold_work_cases.py` shifts `cold-backup-failed` (unique
`cold-...` ID) onto `[D+16h, D+17h)` for the DB time `R`; the definition is registered only in this test's
`FakeScenarios`, shared by `RunSetupService` and `host.cold_lab.StoreColdInputs`; the run is frozen and replayed
through the W2-02 Host Lab -> real gateway -> Batch V2 ingestion chain, then the W2-03 worker. This file owns the
ordinary replay proof and the mode fixture inputs; the three link-state assertions live in
`test_w502_domain_work_links_postgres.py`. Requires ASSETOPS_TEST_DATABASE_URL naming a `*_test` database.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from test_s4_finding_store_postgres import URL

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import w502_cold_work_cases as producer  # noqa: E402

if URL:
    from sqlalchemy import text

    import test_w202_cold_replay_postgres as w202
    from test_w202_cold_replay_postgres import Chain, COLD
    from test_w203_cold_replay_postgres import run
    from test_w501_cold_depth_postgres import client, get

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange
    from assetops_backend.runs.profiles import COLD_PUBLICATION_PROFILE, COLD_THERMAL_MODEL
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.runs.registered_release import publisher_for
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.simulator_lab_api import COLD_SCENARIO_LABELS
    from assetops_backend.sites.cold_lab import V4_EFFECTIVE_FROM, install_cold_lab
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from cold_lab import StoreColdInputs
    from gateway_publication import RegisteredGatewayPublisher
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from publication_schedule import JsonPublicationSchedules
    from run_fixtures import FakeScenarios, FakeSites, site
    from source_stages import JsonSourceStages
    from test_s1_bindings_postgres import Clock
    from test_w202_cold_run_identity import cold_definition
    import pg_harness

    @dataclass
    class ShiftedChain(Chain):
        """The W2-02 chain on a shifted test-only definition; clocks follow their causal inputs, all before `R`."""

        shifted: object = None
        scenarios: object = None
        install_result: object = None

        def open(self) -> "ShiftedChain":
            pg_harness.fresh_database()
            from sqlalchemy import create_engine

            self.engine = create_engine(URL)
            with self.engine.connect() as c:
                r = c.execute(text("SELECT clock_timestamp()")).scalar_one()
            self.shifted = producer.shifted_case(r, self.case, secrets.token_hex(4))
            sh = self.shifted
            install_at, setup_at = sh.start - timedelta(hours=4), sh.start - timedelta(hours=1)
            # The W2 helper's fixed instants, moved by the same delta (read by `_gateway`/`chamber_records`).
            w202.INSTALL_AT, w202.WINDOW, w202.RELEASE = install_at, sh.evidence_window(), producer.text_of(sh.release)
            self.store = PostgresFoundationStore(URL)
            self.install_result = install_cold_lab(self.store, tenant_slug="demo", clock=Clock(install_at))
            self.tenant_id, self.site_id = self.install_result.tenant.id, self.install_result.site.id
            self.runs = YamlRunStore(self.tmp / "runs")
            self.scenarios = FakeScenarios((sh.definition(),))
            setup = RunSetupService(
                self.runs, FakeSites((site(site_id=COLD),)), self.scenarios,
                model_profiles=(COLD_THERMAL_MODEL,), publication_profiles=(COLD_PUBLICATION_PROFILE,),
                now=lambda: producer.text_of(setup_at),
                registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(
                    self.store, "demo", Clock(setup_at)))))
            self.run = setup.create_draft_run(sh.request())
            assert self.run.execution_status == "READY", self.run.blocking_reasons
            producer.validate_foundation(self.run, self.install_result.site, self.frozen_revision(), sh)
            self._gateway()
            self.host = HostLabExecution(
                artifacts=YamlExecutionArtifacts(self.tmp / "executions"),
                stages=JsonSourceStages(self.tmp / "stages"),
                gateway=RegisteredGatewayPublisher(self.process.link),
                schedules=JsonPublicationSchedules(self.tmp / "schedules"),
                source_publisher=publisher_for(URL),
                cold_inputs=StoreColdInputs(self.store, self.scenarios),
            )
            return self

        def frozen_revision(self):
            basis = self.run.registered_basis
            return next((x for x in self.store.revisions(self.tenant_id, self.site_id)
                         if str(x.id) == basis.foundation_revision_id), None)

        def advance_late(self) -> None:
            self.host.advance_publication(self.run, producer.text_of(self.shifted.release))
            self.release_and_upload()

        def attest(self) -> None:
            """The W2-03 SYSTEM simulated clock attestation for every lab source, valid over the shifted days."""
            store = PostgresAssessmentStore(URL)
            with self.engine.connect() as c:
                sources = c.execute(text("SELECT s.id FROM source s JOIN gateway g ON g.id = s.gateway_id "
                                         "WHERE g.site_id = :s ORDER BY s.id"), {"s": self.site_id}).scalars().all()
            for n, source in enumerate(sources):
                store.record_clock_attestation(self.tenant_id, self.site_id, AttestationChange(
                    event_kind="RECORDED", source_id=UUID(str(source)), sequence_epoch=f"cold-{self.case}",
                    idempotency_key=f"w502-{self.case}-{n}", channel="SYSTEM_CLI", authority="lab-simulated-clock",
                    label="SIMULATED demonstration clock (W2-03)", max_utc_error=timedelta(seconds=5),
                    valid_from=self.shifted.attest_from, valid_to=self.shifted.attest_to),
                    SYSTEM_ATTESTER, datetime.now(timezone.utc), domain="cold_chain")
            store._engine.dispose()


def w501_read(built, known_at: str | None = None) -> dict:
    """The W5-01 cold depth read over the shifted selected window (optionally at an explicit cutoff)."""
    sh = built.shifted
    query = f"from={producer.text_of(sh.start)}&to={producer.text_of(sh.window_end)}"
    if known_at:
        query += f"&known_at={known_at}"
    return get(client(built), query)


def produce(chain_factory, mode: str):
    """Open the shifted mode chain, attest, replay through Host Lab -> gateway -> Batch V2, run the worker."""
    built = chain_factory(mode)
    built.attest()
    built.start_release_upload()
    if built.shifted.window_end != built.shifted.start + timedelta(minutes=65):
        enqueue_window(built)  # the W5-01 wider-window route (run-5 ruling 2): the exact stale window
    run(built)
    return built


def enqueue_window(built) -> None:
    """Enqueue the case's exact `cold_chain` recompute window, as W5-01 `test_stale_probe_window` does."""
    sh = built.shifted
    with built.engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
            "available_at, created_at) VALUES (:j, :t, :s, 'cold_chain', :lo, :hi, 'PENDING', now(), now())"),
            {"j": uuid4(), "t": built.tenant_id, "s": built.site_id, "lo": sh.start, "hi": sh.window_end})


def finding_revision(built, mechanism: str | None = None) -> tuple[str, str]:
    """(finding_id, revision_id) of the newest cold Finding revision (of `mechanism`, when given) whose analytic run
    is over the case's exact evidence/assessment window."""
    with built.engine.connect() as c:
        row = c.execute(text(
            "SELECT CAST(f.id AS text), CAST(r.id AS text) FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
            "JOIN analytic_run ar ON ar.id = r.analytic_run_id WHERE r.site_id = :s AND r.domain = 'cold_chain' "
            "AND (CAST(:m AS text) IS NULL OR f.mechanism = :m) AND ar.window_start = :lo AND ar.window_end = :hi "
            "ORDER BY r.created_at DESC, r.id LIMIT 1"),
            {"s": built.site_id, "m": mechanism, "lo": built.shifted.start, "hi": built.shifted.window_end}).first()
    assert row is not None, f"the shifted replay wrote no cold Finding ({mechanism})"
    return row[0], row[1]


@pytest.fixture()
def shifted_chain(tmp_path):
    opened: list = []
    saved = (w202.INSTALL_AT, w202.WINDOW, w202.RELEASE)

    def make(mode: str):
        built = ShiftedChain(mode, tmp_path / f"{mode}-{len(opened)}")
        opened.append(built)
        return built.open()

    yield make
    for built in opened:
        built.close()
    w202.INSTALL_AT, w202.WINDOW, w202.RELEASE = saved


def test_shifted_definition_is_pure_and_unregistered() -> None:
    now = datetime(2026, 10, 23, 9, 30, tzinfo=timezone.utc)
    case = producer.shifted_case(now, "ordinary", "t1")
    assert (case.start, case.end) == (datetime(2026, 10, 22, 16, tzinfo=timezone.utc),
                                      datetime(2026, 10, 22, 17, tzinfo=timezone.utc))
    base = cold_definition("backup-failed")
    shifted = case.definition()
    assert shifted.scenario_id == "cold-w502-ordinary-t1" and shifted.site_code == "COLD-LAB-001"
    assert shifted.scenario_sha256 != base.scenario_sha256  # a new digest; never the shipped SHA
    # Every absolute instant moved by one delta; relative offsets preserved.
    assert [f.at for f in shifted.forcings] == [producer.text_of(producer.instant(f.at) + case.delta)
                                                for f in base.forcings]
    assert case.release - case.start == timedelta(minutes=70) and case.window_end - case.start == timedelta(minutes=65)
    stale = producer.shifted_case(now, "stale", "t1").definition()
    assert min(o.at for o in stale.observations) == "2026-10-22T16:45:00Z"
    assert all(o.action == "DROP" for o in stale.observations)
    pending = producer.shifted_case(now, "pending", "t1").definition()
    assert [(o.action, o.release_at) for o in pending.observations] == [("HOLD", "2026-10-22T17:10:00Z")]
    assert len(producer.shifted_case(now, "no-probe", "t1").definition().observations) == 60
    assert not any(s.startswith("cold-w502") for s in COLD_SCENARIO_LABELS)  # the public catalog is unchanged


def test_ordinary_shifted_replay(shifted_chain) -> None:
    built = produce(shifted_chain, "ordinary")
    sh, basis, identity = built.shifted, built.run.registered_basis, built.run.deterministic_identity
    # Frozen run identity: the shifted definition's digest, interval and the registered COLD-LAB-001 revisions.
    assert identity.scenario.scenario_id == sh.scenario_id
    assert identity.scenario.scenario_sha256 == sh.definition().scenario_sha256 != cold_definition(
        "backup-failed").scenario_sha256
    assert (identity.interval.start_time, identity.interval.end_time) == (producer.text_of(sh.start),
                                                                          producer.text_of(sh.end))
    revisions = built.store.revisions(built.tenant_id, built.site_id)
    imported = next(r for r in revisions if r.origin == "IMPORT")
    assert basis.foundation_revision_id == str(imported.id)
    with built.engine.connect() as c:
        v4 = c.execute(text("SELECT CAST(id AS text) FROM signal_binding_set_revision WHERE site_id = :s AND valid_from = :v "
                            "AND superseded_at IS NULL"), {"s": built.site_id, "v": V4_EFFECTIVE_FROM}).scalar_one()
    assert basis.binding_set_revision_id == v4
    # Effective coverage: both valid-from instants precede the shifted window and remain effective through it.
    assert producer.instant(basis.foundation_valid_from[:19] + "Z") <= sh.start
    assert producer.instant(basis.binding_valid_from[:19] + "Z") <= sh.start
    assert basis.foundation_valid_to is None and basis.binding_valid_to is None
    # The contract check that ran before replay rejects a mismatched Site/Foundation/binding contract.
    frozen = built.frozen_revision()
    for bad in (SimpleNamespace(site_code=COLD, site_type="COLDCHAIN", timezone="UTC"),
                SimpleNamespace(site_code=COLD, site_type="MINIGRID", timezone=producer.TIMEZONE)):
        with pytest.raises(AssertionError, match="not the cold test contract"):
            producer.validate_foundation(built.run, bad, frozen, sh)
    with pytest.raises(AssertionError, match="Foundation revision is not stored"):
        producer.validate_foundation(built.run, built.install_result.site, None, sh)
    # Ordinary accepted envelopes, every one inside the shifted interval and bound to the frozen revisions.
    batches = built.batches()
    decisions = [d for b in batches for (_, d, _) in b["dispositions"]]
    assert decisions and set(decisions) == {"ACCEPTED"}
    with built.engine.connect() as c:
        span = c.execute(text("SELECT min(source_time), max(source_time), count(DISTINCT foundation_revision_id), "
                              "count(*) FROM accepted_evidence WHERE site_id = :s"), {"s": built.site_id}).one()
    assert sh.start <= span[0] and span[1] <= sh.end and span[2] == 1 and span[3] == len(decisions)
    # The selected Finding and exact K0, corroborated against the W5-01 selection.
    _, revision_id = finding_revision(built)
    body = w501_read(built)
    assert body["selection"]["state"] == "CURRENT", body["selection"]
    with built.engine.connect() as c:
        k0 = producer.corroborate_k0(c, built.tenant_id, built.site_id, revision_id, sh, v4, body["selection"])
    assert producer.instant(body["window"]["known_at"][:19] + "Z") == k0.known_at.replace(microsecond=0)
    assert k0.window == (sh.start, sh.window_end)


# ---- run-5 STALE/UNKNOWN rulings: the wider-window producer and the seeded empty-support selection -------------


def selected_excursion(built) -> dict:
    """The newest selected COLD_EXCURSION selection over the case's exact window: seq, run and assessment revision."""
    from assetops_backend.analytics import cold as cold_analytics

    sh = built.shifted
    with built.engine.connect() as c:
        row = c.execute(text(
            "SELECT sel.seq, CAST(sel.run_id AS text) AS run_id, CAST(x.assessment_revision_id AS text) AS ar "
            "FROM analytic_run_selection sel JOIN analytic_run_assessment x ON x.run_id = sel.run_id "
            "WHERE sel.site_id = :s AND sel.analytic_id = :a AND sel.window_start = :lo AND sel.window_end = :hi "
            "ORDER BY sel.seq DESC LIMIT 1"),
            {"s": built.site_id, "a": cold_analytics.EXCURSION_ANALYTIC, "lo": sh.start, "hi": sh.window_end}).first()
    assert row is not None, "no selected excursion assessment over the case window"
    return dict(row._mapping)


def support_times(built, assessment_revision_id: str) -> list[datetime]:
    """Source times of the stored selected excursion result's SUPPORT probe links, ascending."""
    with built.engine.connect() as c:
        result = c.execute(text("SELECT result FROM assessment_revision WHERE id = :r"),
                           {"r": assessment_revision_id}).scalar_one()
        ids = [x["evidence_id"] for x in (result.get("links") or []) if x["use"] == "SUPPORT"]
        return sorted(c.execute(text("SELECT source_time FROM accepted_evidence WHERE site_id = :s "
                                     "AND id = ANY(CAST(:ids AS uuid[]))"), {"s": built.site_id, "ids": ids}).scalars())


def _columns(conn, table: str) -> list[str]:
    return list(conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = :t "
                                  "AND table_schema = current_schema() ORDER BY ordinal_position"), {"t": table}).scalars())


def _copy(conn, table: str, where: str, params: dict, overrides: dict) -> int:
    """`INSERT ... SELECT` one table's rows matching `where`, with column SQL overrides (None = column default)."""
    cols = [c for c in _columns(conn, table) if not (c in overrides and overrides[c] is None)]
    exprs = [overrides.get(c) or c for c in cols]
    return conn.execute(text(f"INSERT INTO {table} ({', '.join(cols)}) SELECT {', '.join(exprs)} FROM {table} "
                             f"WHERE {where}"), params).rowcount


def _children(conn, parent: str) -> list[tuple[str, str]]:
    """(child table, its column referencing `parent.id`) for every foreign key onto `parent`'s `id`."""
    return [tuple(r) for r in conn.execute(text(
        "SELECT cl.relname, ca.attname FROM pg_constraint c JOIN pg_class cl ON cl.oid = c.conrelid "
        "JOIN LATERAL unnest(c.conkey, c.confkey) AS k(ck, fk) ON true "
        "JOIN pg_attribute ca ON ca.attrelid = c.conrelid AND ca.attnum = k.ck "
        "JOIN pg_attribute pa ON pa.attrelid = c.confrelid AND pa.attnum = k.fk "
        "WHERE c.contype = 'f' AND c.confrelid = CAST(:p AS regclass) AND pa.attname = 'id' "
        "ORDER BY cl.relname, ca.attname"), {"p": parent}).all()]


#: Tables the seed writes explicitly (or must not copy): the selection, the run/assessment link, the run and
#: revision themselves, the job queue and the Findings (the START_RESPONSE Finding revision stays the replay's,
#: pinned to its unchanged assessment).
_EXPLICIT = {"analytic_run_selection", "analytic_run_assessment", "assessment_revision", "finding_revision",
             "analytic_run", "recompute_job"}


def canonical(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def seed_empty_support(built) -> SimpleNamespace:
    """Run-5 ruling 3: after the ordinary no-probe replay, a test-only, internally consistent selected `cold_chain`
    excursion run/assessment/selection over the same `[D+16:00, D+17:05)` window whose result's SUPPORT probe set is
    empty. Rows are copies of the replay's selected excursion (tenant/Site scope, frozen Foundation/binding lineage,
    knowledge cutoff = its actual accepted watermark K0); timestamps are the committing DB's `clock_timestamp()`.
    No accepted report is deleted or relabelled; the START_RESPONSE assessment and Finding revision are untouched."""
    old = selected_excursion(built)
    run_id, ar_id = str(uuid4()), str(uuid4())
    with built.engine.begin() as c:
        row = c.execute(text("SELECT result, evidence_ids, assessment_key FROM assessment_revision WHERE id = :r"),
                        {"r": old["ar"]}).one()
        result, evidence_ids, key = row[0], row[1], row[2]
        support = {x["evidence_id"] for x in (result.get("links") or []) if x["use"] == "SUPPORT"}
        assert support, "the replayed excursion has no SUPPORT probe to empty (closing-boundary report expected)"
        seeded = dict(result, links=[x for x in result.get("links") or [] if x["use"] != "SUPPORT"])
        evidence = [e for e in evidence_ids if e not in support]
        body = canonical(seeded)
        p = {"old_run": old["run_id"], "old_ar": old["ar"], "run": run_id, "ar": ar_id, "s": built.site_id}
        _copy(c, "analytic_run", "id = :old_run", p, {
            "id": ":run", "started_at": "clock_timestamp()", "completed_at": "clock_timestamp()"})
        _copy(c, "assessment_revision", "id = :old_ar",
              {**p, "key": key, "res": body, "ev": canonical(evidence),
               "basis": hashlib.sha256(body.encode("utf-8")).hexdigest()},
              {"id": ":ar", "analytic_run_id": ":run", "result": "CAST(:res AS jsonb)",
               "evidence_ids": "CAST(:ev AS jsonb)", "basis_sha256": ":basis", "created_at": "clock_timestamp()",
               "revision_no": "(SELECT max(revision_no) + 1 FROM assessment_revision WHERE site_id = :s "
                              "AND assessment_key = :key)"})
        for parent, old_key, new_key in (("assessment_revision", "old_ar", "ar"), ("analytic_run", "old_run", "run")):
            for child, col in _children(c, parent):
                if child in _EXPLICIT:
                    continue
                cols = _columns(c, child)
                where = f"{col} = :{old_key}"
                if "evidence_id" in cols:
                    where += " AND CAST(evidence_id AS text) <> ALL(CAST(:support AS text[]))"
                over = {col: f":{new_key}", **({"id": "gen_random_uuid()"} if "id" in cols else {})}
                _copy(c, child, where, {**p, "support": sorted(support)}, over)
        _copy(c, "analytic_run_assessment", "run_id = :old_run AND assessment_revision_id = :old_ar", p,
              {"run_id": ":run", "assessment_revision_id": ":ar"})
        default_seq = c.execute(text(
            "SELECT column_default IS NOT NULL OR is_identity = 'YES' FROM information_schema.columns "
            "WHERE table_name = 'analytic_run_selection' AND column_name = 'seq' "
            "AND table_schema = current_schema()")).scalar_one()
        selection_cols = _columns(c, "analytic_run_selection")
        _copy(c, "analytic_run_selection", "run_id = :old_run AND seq = :seq", {**p, "seq": old["seq"]}, {
            "run_id": ":run", "selected_at": "clock_timestamp()",
            "seq": None if default_seq else "(SELECT max(seq) + 1 FROM analytic_run_selection)",
            **({"assessment_revision_id": ":ar"} if "assessment_revision_id" in selection_cols else {})})
    new = selected_excursion(built)
    assert (new["run_id"], new["ar"]) == (run_id, ar_id) and new["seq"] > old["seq"]
    return SimpleNamespace(old=old, new=new, support_removed=sorted(support))


def test_stale_wider_window_producer(shifted_chain) -> None:
    """Ruling 2: the ordinary replay assessed over `[D+16:00, D+17:30)`; the selected excursion's latest SUPPORT
    probe is at or before `D+17:00`, strictly older than `window_end - 10 minutes`, and W5-01 says STALE_SOURCE."""
    built = produce(shifted_chain, "stale")
    sh = built.shifted
    assert sh.window_end - sh.start == timedelta(minutes=90)
    exc = selected_excursion(built)
    times = support_times(built, exc["ar"])
    assert times and times[-1] <= sh.end < sh.window_end - timedelta(minutes=10)
    _, revision_id = finding_revision(built, "COLD_EXCURSION")
    body = w501_read(built)
    assert body["selection"]["state"] == "STALE_SOURCE", body["selection"]
    assert exc["ar"] in body["selection"]["assessment_revision_ids"]
    with built.engine.connect() as c:
        v4 = built.run.registered_basis.binding_set_revision_id
        k0 = producer.corroborate_k0(c, built.tenant_id, built.site_id, revision_id, sh, v4, body["selection"])
    assert k0.window == (sh.start, sh.window_end)


def test_unknown_seeded_empty_support(shifted_chain) -> None:
    """Ruling 3: the no-probe replay still selects one closing-boundary SUPPORT probe (CURRENT); the test-only seeded
    selection empties the excursion's support set and the unchanged W5-01 read says UNKNOWN for no usable probe."""
    from assetops_backend.analytics.cold_reads import FUTURE_NOTE, NO_PROBE_NOTE, NO_SELECTION_NOTE

    built = produce(shifted_chain, "no-probe")
    assert w501_read(built)["selection"]["state"] == "CURRENT"  # the replay alone cannot yield UNKNOWN
    seed = seed_empty_support(built)
    assert support_times(built, seed.new["ar"]) == []
    _, revision_id = finding_revision(built, "COLD_START_FAILURE")
    body = w501_read(built)
    text_body = canonical(body)
    assert body["selection"]["state"] == "UNKNOWN", body["selection"]
    assert NO_PROBE_NOTE in text_body and NO_SELECTION_NOTE not in text_body and FUTURE_NOTE not in text_body
    assert seed.new["ar"] in body["selection"]["assessment_revision_ids"]
    assert seed.old["ar"] not in body["selection"]["assessment_revision_ids"]
    with built.engine.connect() as c:
        v4 = built.run.registered_basis.binding_set_revision_id
        k0 = producer.corroborate_k0(c, built.tenant_id, built.site_id, revision_id, built.shifted, v4,
                                     body["selection"])
        cutoff = c.execute(text("SELECT knowledge_cutoff FROM analytic_run WHERE id = :r"),
                           {"r": seed.new["run_id"]}).scalar_one()
    assert cutoff == k0.known_at
