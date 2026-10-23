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

import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

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
    run(built)
    return built


def finding_revision(built, mechanism: str | None = None) -> tuple[str, str]:
    """(finding_id, revision_id) of the newest selected cold Finding revision (of `mechanism`, when given)."""
    with built.engine.connect() as c:
        row = c.execute(text(
            "SELECT CAST(f.id AS text), CAST(r.id AS text) FROM finding_revision r JOIN finding f ON f.id = r.finding_id "
            "WHERE r.site_id = :s AND r.domain = 'cold_chain' AND (CAST(:m AS text) IS NULL OR f.mechanism = :m) "
            "ORDER BY r.created_at DESC, r.id LIMIT 1"), {"s": built.site_id, "m": mechanism}).first()
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
