"""W2-05b commit 5: six registered EV replays through the real chain, pinned as public manifests.

`.agent/W2-05b-build-spec.md` "Commit 5: exact replay, manifest and final checks", the final commit 4-5 dry-read
item 4 and "Run 6 rulings (q6), manifest table". Each case runs in a fresh private `*_test` database: install
EV-LAB-001 -> freeze a registered EV Draft (`RegisteredLabBasis`) -> Host Lab start with the frozen re-read port
(`StoreEvInputs`) -> a real `assetops_gateway serve` process admits the v2 reports and seals Stage -> the
ordinary SYSTEM_LAB_RELEASE publication and gateway release -> the gateway's own uploader posts Batch V2 over TLS to
an in-process S2 ingestion route -> the S2 ledger -> the EV replay route.

Determinism is held by explicit test fixtures only (the W2-02 cold precedent): a per-case UUID counter replaces
`uuid4` in the loaded backend/host modules, the gateway epoch is the case name and every setup clock is fixed.
Production allocation is unchanged and product code holds no fixture ID.

The `assertions` object of each manifest is the literal q6 table (Q26: pinned expectations). The test separately
inspects the accepted GOOD public rows reached through the run's persisted publication/batch/disposition links and
cross-checks every pinned value with a small test-local calculation; that calculation is not a product classifier.

Manifests are generated once with `ASSETOPS_W205B_WRITE_MANIFESTS=1`, reviewed, then pinned; an ordinary run is
the second clean database and only compares bytes. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test`
database; skipped (never passed) without it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import types
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)"
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "host"))
sys.path.insert(0, str(ROOT / "host" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))

if URL:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url

    from assetops_backend.analytics.adapters import postgres_assessment_store
    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange
    from assetops_backend.cold_replay_api import development_owner, no_owner_principal
    from assetops_backend.ev_replay import EvReplayService
    from assetops_backend.ev_replay_api import build_ev_replay_router
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.composition import build_ev_replay_reader
    from assetops_backend.evidence.gateway_access import StoreGatewayPrincipals
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.provision_gateway import main as provision
    from assetops_backend.evidence.service import IngestionService
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.gateway_api import install_gateway_tls_boundary
    from assetops_backend.main import create_app
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.profiles import EV_CHARGER_MODEL, EV_PUBLICATION_PROFILE
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.runs.registered_release import publisher_for
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.scenarios.adapters.yaml_shipped_scenario_store import ReadOnlyYamlScenarioStore
    from scenario_cache import CachedScenarioRepository, cached_scenario_repository
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.ev_lab import install_ev_lab
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text, seal_batch_v2
    from assetops_contracts.lab_projection import LabControlRefused
    from assetops_contracts.source_envelope import canonical_json
    from assetops_contracts.source_envelope_v3 import v3_message_id
    from ev_lab import StoreEvInputs
    from ev_publication import ev_execution, ev_reports, verify_ev_inputs
    from fake_central import CERT, FakeCentral
    from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config, write_upload_credential
    from gateway_publication import RegisteredGatewayPublisher
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from publication_schedule import JsonPublicationSchedules
    from run_fixtures import FakeScenarios, FakeSites
    from source_stages import JsonSourceStages
    from test_s1_bindings_postgres import Clock

CASES = ("complete", "interrupted", "fault", "missing-meter", "late-record", "contradictory")
MANIFESTS = ROOT / "contract-fixtures" / "w2" / "ev"
EV = "EV-LAB-001"
INSTALL_AT = datetime(2026, 10, 6, 6, 0, tzinfo=timezone.utc)
SETUP_AT = datetime(2026, 10, 6, 7, 0, tzinfo=timezone.utc)
WINDOW = {"start": "2026-10-06T08:00:00Z", "end": "2026-10-06T09:00:00Z", "end_exclusive": True}
RELEASE = "2026-10-06T09:05:00Z"
#: W2-06 q3 P1: the SYSTEM simulated clock attestation validity for every EV-LAB-001 source.
ATTEST_FROM = datetime(2026, 10, 6, 0, 0, tzinfo=timezone.utc)
ATTEST_TO = datetime(2026, 10, 8, 0, 0, tzinfo=timezone.utc)
#: W2-06 q4 Q4-1: the fixed test decision/ingestion clock per phase and the simulated attestation's record instant.
FIRST_DECISION = datetime(2026, 10, 6, 9, 0, 0, tzinfo=timezone.utc)
LATE_DECISION = datetime(2026, 10, 6, 9, 5, 0, tzinfo=timezone.utc)
ATTESTED_AT = datetime(2026, 10, 6, 8, 59, 0, tzinfo=timezone.utc)
MANIFEST_KEYS = ("schema", "site_code", "scenario_id", "scenario_sha256", "model_profile", "publication_profile",
                 "observation_profile", "observation_sha256", "seed", "foundation_revision_id",
                 "binding_revision_id", "window", "envelope_sha256", "batch_sha256", "receipt_dispositions",
                 "accepted_evidence_ids", "public_digest", "assertions")
ASSERTION_KEYS = ("start_at", "end_at", "abort_at", "fault_at", "clear_at", "supported_kwh", "energy_complete",
                  "unknown_meter_seconds", "outcome", "first_cutoff_outcome")
DISPOSITION_KEYS = ("batch_external_id", "ordinal", "decision", "error_code", "accepted_evidence_id")


def _t(minute: int) -> str:
    return f"2026-10-06T08:{minute:02d}:00Z"


#: q6 "Run 6 rulings (q6), manifest table": the complete ten-key `assertions` object per case, literal.
EXPECTED = {
    "complete": {"start_at": _t(1), "end_at": _t(31), "abort_at": None, "fault_at": None, "clear_at": None,
                 "supported_kwh": "30.000", "energy_complete": True, "unknown_meter_seconds": 0,
                 "outcome": "COMPLETED", "first_cutoff_outcome": None},
    "interrupted": {"start_at": _t(1), "end_at": None, "abort_at": _t(16), "fault_at": _t(16), "clear_at": None,
                    "supported_kwh": "15.000", "energy_complete": True, "unknown_meter_seconds": 0,
                    "outcome": "OBSERVED_ABORT", "first_cutoff_outcome": None},
    "fault": {"start_at": _t(11), "end_at": _t(21), "abort_at": None, "fault_at": _t(0), "clear_at": _t(5),
              "supported_kwh": "10.000", "energy_complete": True, "unknown_meter_seconds": 0,
              "outcome": "COMPLETED", "first_cutoff_outcome": None},
    "missing-meter": {"start_at": _t(1), "end_at": _t(31), "abort_at": None, "fault_at": None, "clear_at": None,
                      "supported_kwh": "25.000", "energy_complete": False, "unknown_meter_seconds": 300,
                      "outcome": "COMPLETED", "first_cutoff_outcome": None},
    "late-record": {"start_at": _t(1), "end_at": _t(31), "abort_at": None, "fault_at": None, "clear_at": None,
                    "supported_kwh": "30.000", "energy_complete": True, "unknown_meter_seconds": 0,
                    "outcome": "COMPLETED", "first_cutoff_outcome": "INCOMPLETE"},
    "contradictory": {"start_at": _t(1), "end_at": None, "abort_at": None, "fault_at": None, "clear_at": None,
                      "supported_kwh": None, "energy_complete": None, "unknown_meter_seconds": None,
                      "outcome": "CONTRADICTORY", "first_cutoff_outcome": None},
}
#: Q26/Q28: the selected started session's connector per case (fault selects c2/session-2).
SELECTED = {case: ("c2" if case == "fault" else "c1") for case in CASES}
#: Q26: raw accepted GOOD session-energy sums (contradictory's raw sum is diagnostic only) and the commit-2
#: private world terminal totals, asserted side by side and never equated.
RAW_ACCEPTED_KWH = dict(zip(CASES, ("30.000", "15.000", "10.000", "25.000", "30.000", "30.000")))
WORLD_KWH = dict(zip(CASES, ("30", "15", "10", "30", "30", "30")))
#: Private pack/forcing/oracle keys that must never appear in Stage, Batch, accepted rows or replay JSON.
PRIVATE_KEYS = ("connectors", "requested_kw", "allocated_kw", "energy_kwh", "site_available_kw", "site_import_kw",
                "forcing_ordinal", "forcing", "forcings", "observations", "release_at", "content_digest",
                "boundary", "minute_records", "private_state", "oracle", "vehicle_id", "customer_id",
                "hidden_demand", "delay_event_id", "run_id")
SCENARIOS = CachedScenarioRepository(ReadOnlyYamlScenarioStore(ROOT / "config" / "scenarios")) if URL else None


def sha(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def canonical_file(document: dict) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def definition(case: str):
    return next(s for s in SCENARIOS.list_scenarios() if s.scenario_id == f"ev-{case}")


def ev_request(case: str) -> dict:
    return {
        "site_id": EV, "foundation_version": 1, "scenario_id": f"ev-{case}", "scenario_version": 1,
        "interval": {"start_time": WINDOW["start"], "end_time": WINDOW["end"]}, "timestep_minutes": 1,
        "seed": 20517, "model_profile": {"profile_id": "ev-charger", "profile_version": 1},
        "publication_profile": {"profile_id": "ev-publication", "profile_version": 1}, "run_inputs": [],
    }


# --- determinism: a per-case UUID counter, test fixture only ---------------------------------------------


def hold_uuids(monkeypatch, tag: int) -> None:
    """Replace `uuid4` in every loaded backend/host module (and the run-ID allocator) with a counter."""
    original = uuid.uuid4
    counter = {"n": 0}

    def next_uuid() -> UUID:
        counter["n"] += 1
        return UUID(f"{tag:08x}-0000-4000-8000-{counter['n']:012x}")

    for module in list(sys.modules.values()):
        path = str(getattr(module, "__file__", "") or "")
        if getattr(module, "uuid4", None) is original and path.startswith(str(ROOT)) and ".venv" not in path:
            monkeypatch.setattr(module, "uuid4", next_uuid)
    import assetops_backend.runs.identity as run_identity

    monkeypatch.setattr(run_identity, "uuid", types.SimpleNamespace(uuid4=next_uuid))


# --- the chain ------------------------------------------------------------------------------------------


class _NoSites:
    def get_site(self, site_id):  # pragma: no cover - an imported Site never reaches the legacy path
        raise AssertionError(site_id)


@dataclass
class Chain:
    """One case executed through the registered path in a fresh database; the gateway stays up until close."""

    case: str
    tmp: Path
    engine: object = None
    store: object = None
    tenant_id: UUID | None = None
    site_id: UUID | None = None
    run: object = None
    runs: object = None
    host: object = None
    process: object = None
    central: object = None
    credential: str | None = None
    released: list = field(default_factory=list)
    late: bool = False

    def decision_clock(self) -> datetime:
        """W2-06 q4 Q4-1: 09:00 through the first release, 09:05 once `advance_late()` begins. It is both the S2
        decision clock and the batch ingestion clock, so `received_at <= decided_at` in every chunk of a phase."""
        return LATE_DECISION if self.late else FIRST_DECISION

    def open(self) -> "Chain":
        url = make_url(URL)
        assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
        pg_harness.fresh_database()
        self.engine = create_engine(URL)
        self.store = PostgresFoundationStore(URL)
        result = install_ev_lab(self.store, tenant_slug="demo", clock=Clock(INSTALL_AT))
        self.tenant_id, self.site_id = result.tenant.id, result.site.id
        self.runs = YamlRunStore(self.tmp / "runs")
        setup = RunSetupService(
            self.runs, FakeSites(()), FakeScenarios((definition(self.case),)),
            model_profiles=(EV_CHARGER_MODEL,), publication_profiles=(EV_PUBLICATION_PROFILE,),
            now=lambda: "2026-10-06T07:00:00Z",
            registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(self.store, "demo",
                                                                                       Clock(SETUP_AT)))))
        self.run = setup.create_draft_run(ev_request(self.case))
        assert self.run.execution_status == "READY", self.run.blocking_reasons
        self._gateway()
        self.host = HostLabExecution(
            artifacts=YamlExecutionArtifacts(self.tmp / "executions"),
            stages=JsonSourceStages(self.tmp / "stages"),
            gateway=RegisteredGatewayPublisher(self.process.link),
            schedules=JsonPublicationSchedules(self.tmp / "schedules"),
            source_publisher=publisher_for(URL),
            ev_inputs=StoreEvInputs(self.store, cached_scenario_repository()),
        )
        self.attest()
        return self

    def attest(self) -> None:
        """W2-06 q3 P1 (the `test_w203_cold_replay_postgres.py:attest` precedent): the SYSTEM attester's simulated
        clock attestation for every registered source of the built Site, for the gateway epoch `ev-<case>`,
        recorded before any upload. The real allocator is bound to the store module only during the call, so the
        counter-pinned manifest IDs do not shift."""
        with self.engine.connect() as c:
            sources = c.execute(text("SELECT s.id FROM source s JOIN gateway g ON g.id = s.gateway_id "
                                     "WHERE g.site_id = :s ORDER BY s.id"), {"s": self.site_id}).scalars().all()
        assert sources
        store = PostgresAssessmentStore(URL)
        patched = postgres_assessment_store.uuid4
        postgres_assessment_store.uuid4 = uuid.uuid4
        try:
            for n, source in enumerate(sources):
                change = AttestationChange(
                    event_kind="RECORDED", source_id=UUID(str(source)), sequence_epoch=f"ev-{self.case}",
                    idempotency_key=f"w206-{self.case}-{n}", channel="SYSTEM_CLI", authority="lab-simulated-clock",
                    label="SIMULATED demonstration clock (W2-06)", max_utc_error=timedelta(seconds=5),
                    valid_from=ATTEST_FROM, valid_to=ATTEST_TO)
                store.record_clock_attestation(self.tenant_id, self.site_id, change, SYSTEM_ATTESTER,
                                               ATTESTED_AT, domain="ev_charging")
        finally:
            postgres_assessment_store.uuid4 = patched
            store._engine.dispose()
        with self.engine.connect() as c:
            rows = c.execute(text(
                "SELECT source_id, sequence_epoch, event_kind, proof_class, valid_from, valid_to "
                "FROM source_clock_attestation WHERE tenant_id = :t AND site_id = :s ORDER BY source_id"),
                {"t": self.tenant_id, "s": self.site_id}).all()
        # One RECORDED simulated proof per registered source, for exactly this case's gateway epoch.
        assert [r.source_id for r in rows] == list(sources)
        assert {(r.sequence_epoch, r.event_kind, r.proof_class, r.valid_from, r.valid_to) for r in rows} == {
            (f"ev-{self.case}", "RECORDED", "SIMULATED", ATTEST_FROM, ATTEST_TO)}

    def _gateway(self) -> None:
        with self.engine.connect() as c:
            gateway = c.execute(text("SELECT id, gateway_external_id FROM gateway WHERE site_id = :s"),
                                {"s": self.site_id}).one()
            sources = list(c.execute(text("SELECT source_external_id FROM source WHERE gateway_id = :g "
                                          "ORDER BY source_external_id"), {"g": gateway.id}).scalars())
        out = self.tmp / "issued"
        out.mkdir(parents=True)
        flags = [x for s in sources for x in ("--enable-source", s)]
        assert provision(["--tenant", "demo", "--site", EV, "--gateway", gateway.gateway_external_id, "issue",
                          "--credential-out", str(out / "cred"), *flags],
                         store=PostgresGatewayAccess(URL), now=Clock(INSTALL_AT)()) == 0
        [issued] = list(out.glob("cred.*"))
        self.credential = issued.read_text(encoding="ascii").strip()
        state = self.tmp / "gateway"
        write_upload_credential(state, self.credential)  # the host's gateway helper; backend never imports it
        central_app = FastAPI()
        install_gateway_tls_boundary(central_app)
        central_app.include_router(build_evidence_router(
            IngestionService(None, _NoSites()), _NoSites(),  # type: ignore[arg-type]
            batch_ingestion=BatchIngestionService(
                PostgresEvidenceLedger(URL, test_decision_clock_override=self.decision_clock), self.decision_clock),
            gateway_principals=StoreGatewayPrincipals(PostgresGatewayAccess(URL))))
        central = TestClient(central_app, base_url="https://testserver")

        def forward(path, headers, body):
            wanted = {k: v for k, v in headers.items() if k.lower() in ("authorization", "content-type")}
            answer = central.post(path, content=body, headers=wanted)
            return answer.status_code, answer.content

        self.central = FakeCentral(forward)
        config = write_config(state, provisioning_from_snapshot(self.run.registered_basis.snapshot_canonical,
                                                                epoch=f"ev-{self.case}"))
        document = json.loads(config.read_text(encoding="utf-8"))
        document["upload"] = {"server_url": self.central.url, "upload_credential_file": "upload.credential",
                              "ca_file": str(CERT), "interval_seconds": 3600}
        config.write_text(json.dumps(document), encoding="utf-8")
        self.process = GatewayProcess(config)
        assert self.process.ready, self.process.first_line

    def start_release_upload(self) -> None:
        projection = self.host.start(self.run)
        assert projection.status == "COMPLETED", projection
        self.release_and_upload()

    def release_and_upload(self) -> None:
        try:
            self.released.append(self.host.release_registered(self.run))
        except LabControlRefused as refused:
            raise AssertionError(f"{refused.kind}: {refused.detail}") from refused
        publisher = RegisteredGatewayPublisher(self.process.link)
        while publisher.deliver(50)["batches"]["attempted"]:
            pass

    def advance_late(self) -> None:
        self.late = True
        self.host.advance_publication(self.run, RELEASE)
        self.release_and_upload()

    def close(self) -> None:
        for closing in (lambda: self.process.kill(), lambda: self.central.close(), lambda: self.engine.dispose()):
            try:
                closing()
            except Exception:  # noqa: BLE001 - teardown keeps going
                pass
        pg_harness.dispose(self.store)

    # --- reads ---------------------------------------------------------------------------------------

    def scope(self, code: str):
        return (EV, self.tenant_id, self.site_id) if code.upper() == EV else None

    def replay_client(self, *, access=None, owner=None, reader=None) -> TestClient:
        app = FastAPI()
        app.include_router(build_ev_replay_router(
            EvReplayService(reader or build_ev_replay_reader(URL), self.runs), self.scope,
            access=access or (lambda request, code: None), owner=owner or development_owner))
        return TestClient(app)

    def replay(self) -> dict:
        response = self.replay_client().get(f"/api/sites/{EV}/ev/replay", params={"run_id": self.run.run_id})
        assert response.status_code == 200, response.text
        return response.json()

    def batches(self) -> list[dict]:
        """Linked batches of this run's publications in replay order, with their stored dispositions."""
        with self.engine.connect() as c:
            rows = c.execute(text(
                "SELECT b.id, b.external_batch_id, b.payload_sha256, b.batch_text, b.received_at "
                "FROM evidence_publication p JOIN batch_publication_link l ON l.publication_id = p.id "
                "JOIN ingestion_batch b ON b.id = l.batch_id WHERE p.run_id = :run "
                "ORDER BY p.recorded_at, p.id"), {"run": self.run.run_id}).all()
            out = []
            for r in rows:
                dispositions = c.execute(text(
                    "SELECT d.ordinal, d.decision, CAST(d.accepted_evidence_id AS text) AS accepted, r.kind "
                    "FROM ingestion_disposition d LEFT JOIN evidence_rejection r ON r.id = d.rejection_id "
                    "WHERE d.batch_id = :b ORDER BY d.ordinal"), {"b": r.id}).all()
                out.append({"batch_id": r.external_batch_id, "payload_sha256": r.payload_sha256,
                            "text": r.batch_text, "received_at": r.received_at,
                            "dispositions": [(d.ordinal, d.decision, d.accepted, d.kind) for d in dispositions]})
            return out


@pytest.fixture()
def chain(tmp_path, monkeypatch):
    opened: list[Chain] = []

    def make(case: str) -> Chain:
        hold_uuids(monkeypatch, 0x0500 + CASES.index(case) + 1)
        built = Chain(case, tmp_path / case)
        opened.append(built)
        return built.open()

    yield make
    for built in opened:
        built.close()


# --- the persisted public rows and the test-local cross-check --------------------------------------------


def _envelopes(chain: Chain) -> list[tuple[str, int, str, str, str | None, str | None]]:
    """(batch_id, ordinal, envelope text, decision, accepted ID, error code) in replay order."""
    found = []
    for batch in chain.batches():
        parsed = parse_canonical_batch_v2_text(batch["text"])
        for ordinal, decision, accepted, kind in batch["dispositions"]:
            found.append((batch["batch_id"], ordinal, parsed.envelopes[ordinal], decision, accepted, kind))
    return found


def _accepted(chain: Chain) -> list[dict]:
    return [json.loads(t) for (_, _, t, d, _, _) in _envelopes(chain) if d == "ACCEPTED"]


def _at(e: dict) -> str:
    return e["timing"]["source_time"]


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _channel(e: dict) -> tuple[str, str]:
    return e["source"]["device_id"], e["source"]["signal_id"]


def _events(accepted: list[dict], connector: str, signal: str, kind: str) -> list[dict]:
    device = f"{connector}-charger-controller" if signal == "session-event" else f"{connector}-connector-controller"
    return [e for e in accepted if _channel(e) == (device, signal) and e["payload"]["family"] == "EVENT"
            and e["payload"]["record_kind"] == kind and e["payload"]["quality"] == "GOOD"]


def _session_deltas(accepted: list[dict], connector: str, session_id: str, connector_id: str) -> list[dict]:
    """Accepted GOOD connector INTERVAL_DELTA rows of exactly this session and connector."""
    return [e for e in accepted if _channel(e) == (f"{connector}-connector-meter", "energy")
            and e["payload"]["family"] == "MEASUREMENT" and e["payload"]["measurement"] == "INTERVAL_DELTA"
            and e["payload"]["quality"] == "GOOD" and e["payload"]["unit"] == "kWh"
            and e["payload"]["session_id"] == session_id and e["payload"]["connector_id"] == connector_id]


def cross_check(accepted: list[dict], connector: str) -> tuple[dict, Decimal | None]:
    """Q26 test-local cross-check over accepted GOOD public rows: never a product classifier.

    Returns the ten-key view (without `first_cutoff_outcome`) and the raw accepted session-energy sum."""
    starts = _events(accepted, connector, "session-event", "EV_SESSION_START")
    faults = [e for c in ("c1", "c2") for e in _events(accepted, c, "fault-event", "EV_CONNECTOR_FAULT")]
    clears = [e for c in ("c1", "c2") for e in _events(accepted, c, "fault-event", "EV_CONNECTOR_CLEAR")]
    assert len(faults) <= 1 and len(clears) <= 1, (faults, clears)
    view = {"start_at": None, "end_at": None, "abort_at": None, "fault_at": _at(faults[0]) if faults else None,
            "clear_at": _at(clears[0]) if clears else None, "supported_kwh": None, "energy_complete": None,
            "unknown_meter_seconds": None, "outcome": None}
    if not starts:
        return view, None
    [start] = starts
    session_id, connector_id = start["payload"]["session_id"], start["payload"]["connector_id"]
    assert session_id and connector_id and start["payload"]["correlation_id"] == session_id

    def scoped(kind: str) -> list[dict]:
        return [e for e in _events(accepted, connector, "session-event", kind)
                if (e["payload"]["session_id"], e["payload"]["connector_id"]) == (session_id, connector_id)]

    ends, aborts = scoped("EV_SESSION_END"), scoped("EV_SESSION_ABORT")
    deltas = _session_deltas(accepted, connector, session_id, connector_id)
    raw = sum((Decimal(e["payload"]["value"]) for e in deltas), Decimal("0"))
    view["start_at"] = _at(start)
    if len({e["payload"]["event_id"] for e in ends}) >= 2:
        view["outcome"] = "CONTRADICTORY"
        return view, raw
    if len(ends) == 1 and not aborts:
        view["outcome"], view["end_at"], terminal = "COMPLETED", _at(ends[0]), _at(ends[0])
    elif len(aborts) == 1 and not ends:
        view["outcome"], view["abort_at"], terminal = "OBSERVED_ABORT", _at(aborts[0]), _at(aborts[0])
    else:
        assert not ends and not aborts
        view["outcome"] = "INCOMPLETE"
        return view, raw
    lo, hi = _instant(view["start_at"]), _instant(terminal)
    eligible = sorted(((_instant(e["timing"]["interval_start"]), _instant(e["timing"]["interval_end"]), e)
                       for e in deltas), key=lambda x: (x[0], x[1]))
    eligible = [x for x in eligible if lo <= x[0] < x[1] <= hi]
    for (_, end_a, _), (start_b, _, _) in zip(eligible, eligible[1:]):
        assert end_a <= start_b, "overlapping accepted deltas"
    covered = sum((b - a).total_seconds() for a, b, _ in eligible)
    unknown = int((hi - lo).total_seconds() - covered)
    total = sum((Decimal(e["payload"]["value"]) for _, _, e in eligible), Decimal("0"))
    view["supported_kwh"] = f"{total.quantize(Decimal('0.001'))}" if eligible else None
    view["unknown_meter_seconds"] = unknown
    view["energy_complete"] = unknown == 0
    return view, raw


def world_total(built: Chain) -> Fraction:
    """The commit-2 private world terminal total (both connectors), recomputed beside the public sums only."""
    basis = built.run.registered_basis
    revision = next(r for r in built.store.revisions(built.tenant_id, built.site_id)
                    if str(r.id) == basis.foundation_revision_id)
    inputs = StoreEvInputs(built.store, cached_scenario_repository())
    binding = inputs.binding_revision(built.tenant_id, built.site_id, UUID(basis.binding_set_revision_id))
    verified = verify_ev_inputs(built.run, revision, binding, definition(built.case))
    final = ev_execution(verified.definition, verified.parameters).documents[-1]
    return sum((Fraction(c["energy_kwh"]) for c in final["connectors"]), Fraction(0))


# --- manifest -------------------------------------------------------------------------------------------


def _compact(profile_id: str, version: int) -> str:
    return f"{profile_id}/{version}"


def manifest(chain: Chain, replay: dict) -> dict:
    run = chain.run
    identity = run.deterministic_identity
    profiles = identity.profiles
    envelopes = _envelopes(chain)
    return {
        "schema": "ev-replay-manifest/1",
        "site_code": identity.site.site_id,
        "scenario_id": identity.scenario.scenario_id,
        "scenario_sha256": identity.scenario.scenario_sha256,
        "model_profile": _compact(profiles.model_profile_id, profiles.model_profile_version),
        "publication_profile": _compact(profiles.publication_profile_id, profiles.publication_profile_version),
        "observation_profile": _compact(profiles.observation_profile_id, profiles.observation_profile_version),
        "observation_sha256": profiles.observation_sha256,
        "seed": identity.seed,
        "foundation_revision_id": run.registered_basis.foundation_revision_id,
        "binding_revision_id": run.registered_basis.binding_set_revision_id,
        "window": WINDOW,
        "envelope_sha256": [sha(t) for (_, _, t, _, _, _) in envelopes],
        "batch_sha256": [b["payload_sha256"] for b in chain.batches()],
        "receipt_dispositions": [{"batch_external_id": b, "ordinal": o, "decision": d, "error_code": k,
                                  "accepted_evidence_id": a} for (b, o, _, d, a, k) in envelopes],
        "accepted_evidence_ids": [a for (_, _, _, d, a, _) in envelopes if d == "ACCEPTED"],
        "public_digest": replay["public_digest"],
        "assertions": EXPECTED[chain.case],
    }


def pinned(case: str, built: dict) -> dict:
    path = MANIFESTS / f"{case}.json"
    if os.environ.get("ASSETOPS_W205B_WRITE_MANIFESTS") == "1":
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_file(built), encoding="utf-8", newline="\n")
    text_value = path.read_text(encoding="utf-8")
    document = json.loads(text_value)
    assert text_value == canonical_file(document), f"{path} is not canonical JSON"
    assert tuple(document) == tuple(sorted(MANIFEST_KEYS)) and set(document) == set(MANIFEST_KEYS)
    return document


def _check_types(document: dict) -> None:
    for key in ("schema", "site_code", "scenario_id", "scenario_sha256", "model_profile", "publication_profile",
                "observation_profile", "observation_sha256", "foundation_revision_id", "binding_revision_id"):
        assert isinstance(document[key], str) and document[key], key
    assert type(document["seed"]) is int
    for key in ("envelope_sha256", "batch_sha256", "accepted_evidence_ids"):
        assert all(isinstance(v, str) for v in document[key]), key
    for row in document["receipt_dispositions"]:
        assert tuple(sorted(row)) == tuple(sorted(DISPOSITION_KEYS))
        assert isinstance(row["batch_external_id"], str) and type(row["ordinal"]) is int
        assert isinstance(row["decision"], str)
        assert row["error_code"] is None or isinstance(row["error_code"], str)
        assert row["accepted_evidence_id"] is None or isinstance(row["accepted_evidence_id"], str)
    digest = document["public_digest"]
    assert len(digest) == 64 and digest == digest.lower() and int(digest, 16) >= 0
    a = document["assertions"]
    assert set(a) == set(ASSERTION_KEYS)
    for key in ("start_at", "end_at", "abort_at", "fault_at", "clear_at", "outcome", "first_cutoff_outcome",
                "supported_kwh"):
        assert a[key] is None or isinstance(a[key], str), key
    assert a["energy_complete"] is None or type(a["energy_complete"]) is bool
    assert a["unknown_meter_seconds"] is None or type(a["unknown_meter_seconds"]) is int


# --- W2-06 R12: the exact vector artifact produced from this persisted chain -------------------------------
#
# `.agent/W2-06-build-spec.md` "R12: exact vector artifact (Q1-Q9)". Rows come from the persisted publication ->
# batch -> disposition chain; each accepted envelope is paired to exactly one DeviceReport V2 of
# `host.ev_publication.ev_reports` by complete report-field projection equality and to the gateway's own
# report-admission key. `expected` is the R12 table with ID selectors expanded mechanically on `records`.

VECTORS = ROOT / "backend" / "tests" / "fixtures" / "w2" / "ev-w206-vectors.json"
VECTOR_SCHEMA = "ev-w206-vectors/1"
RECORD_KEYS = ("report_key", "report_sha256", "batch_external_id", "ordinal", "accepted_evidence_id",
               "envelope_sha256", "source_time", "interval_start", "interval_end", "connector_id", "session_id",
               "family", "record_kind", "measurement", "quality", "value", "unit", "event_id", "outcome", "asset_id",
               "binding_revision_id", "source_id", "sequence_epoch", "clock_attested", "source_class",
               "binding_set_revision_id", "role", "device_id", "signal_id")  # q4 Q4-2: the four added row keys
MEMBER_KEYS = ("binding_revision_id", "binding_set_revision_id", "role", "asset_id", "source_id", "device_id",
               "signal_id", "valid_from", "valid_to")
CASE_KEYS = ("binding_members", "expected", "first_cutoff", "manifest", "records", "selected_connector", "window")
EXPECTED_KEYS = ("state", "start_at", "end_at", "start_bounds", "end_bounds", "supported_kwh", "energy_complete",
                 "unknown_meter_seconds", "reason_codes", "fault_evidence_id", "finding_support_evidence_ids",
                 "raw_accepted_kwh", "intervals")
PROJECTION = ("device_id", "signal_id", "source_time", "interval_start", "interval_end", "family", "measurement",
              "value", "unit", "quality", "unavailable_reason", "session_id", "connector_id", "record_kind",
              "event_id", "correlation_id", "component_id", "actor", "outcome")
METER_ERROR = "0.002"  # R6/Q7: 2 x the fixture's per-boundary ev-meter-error-bound 0.001
_COMPLETE = (("01", "05", "4.000"), ("05", "10", "5.000"), ("10", "15", "5.000"), ("15", "20", "5.000"),
             ("20", "25", "5.000"), ("25", "30", "5.000"), ("30", "31", "1.000"))


def _hm(hhmm: str) -> str:
    return f"2026-10-06T{hhmm}:00Z"


def _point(hhmm: str | None) -> dict | None:
    return None if hhmm is None else {"earliest": _hm(hhmm), "latest": _hm(hhmm)}


def _table(state, start, end, start_b, end_b, supported, complete, unknown, reasons, fault, support, raw, meters,
           use="SUPPORT", reason=None) -> dict:
    """One literal R12 table row; selectors stay symbolic (`(kind, HH:MM)`) until expanded on `records`."""
    return {"state": state, "start_at": start, "end_at": end, "start_bounds": start_b, "end_bounds": end_b,
            "supported_kwh": supported, "energy_complete": complete, "unknown_meter_seconds": unknown,
            "reason_codes": reasons, "fault_evidence_id": fault, "finding_support_evidence_ids": support,
            "raw_accepted_kwh": raw,
            "intervals": [(f"08:{a}", f"08:{b}", kwh, use, reason) for a, b, kwh in meters]}


_START = ("EV_SESSION_START", "08:01")
R12_TABLE = {
    "complete": _table("COMPLETED", "08:01", "08:31", _point("08:01"), _point("08:31"), "30.000", True, 0, [],
                       None, [], "30.000", _COMPLETE),
    "interrupted": _table("OBSERVED_ABORT", "08:01", "08:16", _point("08:01"), _point("08:16"), "15.000", True, 0,
                          [], ("EV_CONNECTOR_FAULT", "08:16"),
                          [_START, ("EV_CONNECTOR_FAULT", "08:16"), ("EV_SESSION_ABORT", "08:16")], "15.000",
                          (("01", "05", "4.000"), ("05", "10", "5.000"), ("10", "15", "5.000"),
                           ("15", "16", "1.000"))),
    "fault": _table("COMPLETED", "08:11", "08:21", _point("08:11"), _point("08:21"), "10.000", True, 0, [], None,
                    [], "10.000", (("11", "15", "4.000"), ("15", "20", "5.000"), ("20", "21", "1.000"))),
    "missing-meter": _table("COMPLETED", "08:01", "08:31", _point("08:01"), _point("08:31"), "25.000", False, 300,
                            ["METER_GAP"], None, [], "25.000", tuple(m for m in _COMPLETE if m[0] != "10")),
    "late-record": _table("COMPLETED", "08:01", "08:31", _point("08:01"), _point("08:31"), "30.000", True, 0, [],
                          None, [], "30.000", _COMPLETE),
    "contradictory": _table("CONTRADICTORY", "08:01", None, _point("08:01"),
                            {"earliest": _hm("08:30"), "latest": _hm("08:31")}, None, None, None,
                            ["CONFLICTING_TERMINAL"], None, [], "30.000", _COMPLETE,
                            use="EXCLUDED", reason="CONFLICTING_TERMINAL"),
}
#: The late-record first cutoff (09:00): END absent, INCOMPLETE, `"30.000"` partial over the observed span.
LATE_FIRST = _table("INCOMPLETE", "08:01", None, _point("08:01"), None, "30.000", False, 0, ["MISSING_TERMINAL"],
                    None, [], "30.000", _COMPLETE)


def watermark(built: Chain) -> datetime:
    """The committed disposition watermark of the Site (`cold_watermark`'s query): the selected knowledge cutoff."""
    with built.engine.connect() as c:
        return c.execute(text("SELECT max(decided_at) FROM ingestion_disposition WHERE tenant_id = :t "
                              "AND site_id = :s"), {"t": built.tenant_id, "s": built.site_id}).scalar_one()


def _vector_text(document: dict) -> str:
    return json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _gateway_admission(built: Chain, message_id: str) -> tuple[str, str]:
    """The gateway's own (report_key, report_sha256) for one admitted message (its `report_admission` row)."""
    import sqlite3

    database = built.tmp / "gateway" / "gateway.sqlite3"
    with sqlite3.connect(f"file:{database.as_posix()}?mode=ro", uri=True) as db:
        rows = db.execute("SELECT report_key, report_sha256 FROM report_admission WHERE message_id = ?",
                          (message_id,)).fetchall()
    assert len(rows) == 1, (message_id, rows)
    return rows[0]


def _run_reports(built: Chain) -> list:
    basis = built.run.registered_basis
    revision = next(r for r in built.store.revisions(built.tenant_id, built.site_id)
                    if str(r.id) == basis.foundation_revision_id)
    inputs = StoreEvInputs(built.store, cached_scenario_repository())
    binding = inputs.binding_revision(built.tenant_id, built.site_id, UUID(basis.binding_set_revision_id))
    verified = verify_ev_inputs(built.run, revision, binding, definition(built.case))
    return list(ev_reports(verified.definition, verified.channels,
                           ev_execution(verified.definition, verified.parameters)))


def vector_records(built: Chain, document: dict) -> list[dict]:
    """Q1: every accepted public report in persisted publication order, paired one-to-one and fully asserted."""
    from assetops_backend.analytics.adapters.postgres_assessment_store import _attestations
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import link_rows_on
    from assetops_backend.evidence.source_provenance import classify, link_of
    from assetops_contracts.gateway_report import parse_device_report_v2_text
    from assetops_contracts.source_envelope_v4 import parse_canonical_envelope_v4_text

    reports = _run_reports(built)
    parsed = [(r, parse_device_report_v2_text(r.report_text)) for r in reports]
    envelopes = _envelopes(built)
    # Q1: the manifest's complete disposition triples, accepted-ID order and envelope SHA sequence.
    assert [(b, o, a) for (b, o, _, _, a, _) in envelopes] == \
        [(d["batch_external_id"], d["ordinal"], d["accepted_evidence_id"]) for d in document["receipt_dispositions"]]
    assert [a for (_, _, _, d, a, _) in envelopes if d == "ACCEPTED"] == document["accepted_evidence_ids"]
    assert [sha(t) for (_, _, t, _, _, _) in envelopes] == document["envelope_sha256"]
    used: set[str] = set()
    out = []
    with built.engine.connect() as c:
        # q3 P1: proof recorded by the selected knowledge cutoff (the committed disposition watermark).
        attestations = _attestations(c, built.tenant_id, built.site_id, watermark(built))
        for batch_id, ordinal, envelope_text, decision, accepted_id, _ in envelopes:
            if decision != "ACCEPTED":
                continue
            envelope = parse_canonical_envelope_v4_text(envelope_text)
            projection = tuple(getattr(envelope, k) for k in PROJECTION)
            matches = [(r, p) for r, p in parsed if tuple(getattr(p, k) for k in PROJECTION) == projection]
            assert len(matches) == 1, (accepted_id, len(matches))
            report, device_report = matches[0]
            assert report.report_key == device_report.report_key and report.report_key not in used
            used.add(report.report_key)
            report_sha = sha(report.report_text)
            assert _gateway_admission(built, envelope.message_id) == (report.report_key, report_sha)
            row = c.execute(text(
                "SELECT e.id, e.ordinal, b.external_batch_id, e.envelope_sha256, e.envelope_text, e.message_id, "
                "e.source_time, e.interval_start, e.interval_end, e.connector_id, e.session_id, e.family, "
                "e.record_kind, e.measurement, e.quality, e.normalized_value_text, e.normalized_unit, e.event_id, "
                "e.outcome, e.asset_id, e.binding_revision_id, e.source_id, e.sequence_epoch, e.device_id, "
                "e.signal_id, e.binding_set_revision_id, e.role FROM accepted_evidence e JOIN ingestion_batch b ON b.id = e.batch_id "
                "WHERE e.tenant_id = :t AND e.site_id = :s AND e.id = :id"),
                {"t": built.tenant_id, "s": built.site_id, "id": accepted_id}).one()
            # Accepted ledger fields agree with the paired envelope (never reconstructed from the report).
            assert (str(row.id), row.ordinal, row.external_batch_id) == (accepted_id, ordinal, batch_id)
            assert row.envelope_text == envelope_text and row.envelope_sha256 == sha(envelope_text)
            assert (row.message_id, row.sequence_epoch) == (envelope.message_id, envelope.sequence_epoch)
            assert (row.device_id, row.signal_id) == (envelope.device_id, envelope.signal_id)
            for column, value in (("source_time", envelope.source_time), ("interval_start", envelope.interval_start),
                                  ("interval_end", envelope.interval_end)):
                stored = getattr(row, column)
                assert (stored is None) == (value is None) and (stored is None or stored == _instant(value)), column
            assert (row.family, row.record_kind, row.measurement, row.quality, row.event_id, row.outcome,
                    row.connector_id, row.session_id) == \
                (envelope.family, envelope.record_kind, envelope.measurement, envelope.quality, envelope.event_id,
                 envelope.outcome, envelope.connector_id, envelope.session_id)
            # q3 P1: the attestation covers source, epoch and the full measurement interval (or the instant).
            lo = row.interval_start if row.interval_start is not None else row.source_time
            hi = row.interval_end if row.interval_end is not None else row.source_time
            attested = any(str(a.source_id) == str(row.source_id) and a.sequence_epoch == row.sequence_epoch
                           and a.covers(lo, hi) for a in attestations)
            links = {r.requested_id: link_of(r) for r in link_rows_on(c, built.tenant_id, built.site_id,
                                                                        [accepted_id])}
            out.append({
                "report_key": report.report_key, "report_sha256": report_sha, "batch_external_id": batch_id,
                "ordinal": ordinal, "accepted_evidence_id": accepted_id, "envelope_sha256": row.envelope_sha256,
                "source_time": envelope.source_time, "interval_start": envelope.interval_start,
                "interval_end": envelope.interval_end, "connector_id": row.connector_id,
                "session_id": row.session_id, "family": row.family, "record_kind": row.record_kind,
                "measurement": row.measurement, "quality": row.quality, "value": row.normalized_value_text,
                "unit": row.normalized_unit, "event_id": row.event_id, "outcome": row.outcome,
                "asset_id": str(row.asset_id), "binding_revision_id": str(row.binding_revision_id),
                "source_id": str(row.source_id), "sequence_epoch": row.sequence_epoch, "clock_attested": attested,
                "source_class": classify([accepted_id], links)["state"],
                # q4 Q4-2: from the accepted ledger row, never from report text or a reconstructed binding.
                "binding_set_revision_id": str(row.binding_set_revision_id), "role": row.role,
                "device_id": row.device_id, "signal_id": row.signal_id,
            })
    return out


def _connector_asset(built: Chain, code: str) -> str:
    with built.engine.connect() as c:
        return str(c.execute(text("SELECT id FROM asset WHERE tenant_id = :t AND site_id = :s AND asset_code = :c"),
                             {"t": built.tenant_id, "s": built.site_id, "c": code}).scalar_one())


def expand(table: dict, records: list[dict], connector_asset: str) -> dict:
    """R12: the table row with ID selectors expanded on the unique matching row of the selected connector/session;
    zero or multiple matches fail."""
    [start] = [r for r in records if r["asset_id"] == connector_asset and r["record_kind"] == "EV_SESSION_START"
               and r["source_time"] == _hm(table["start_at"])]
    session = start["session_id"]

    def event(selector) -> str:
        kind, hhmm = selector
        found = [r for r in records if r["asset_id"] == connector_asset and r["record_kind"] == kind
                 and r["source_time"] == _hm(hhmm) and r["session_id"] in (session, None)]
        assert len(found) == 1, (selector, len(found))
        return found[0]["accepted_evidence_id"]

    def meter(lo: str, hi: str, kwh: str, use: str, reason) -> dict:
        found = [r for r in records if r["asset_id"] == connector_asset and r["family"] == "MEASUREMENT"
                 and r["measurement"] == "INTERVAL_DELTA" and r["session_id"] == session
                 and r["interval_start"] == _hm(lo) and r["interval_end"] == _hm(hi)]
        assert len(found) == 1, ((lo, hi), len(found))
        assert Decimal(found[0]["value"]) == Decimal(kwh) and found[0]["unit"] == "kWh", found[0]
        return {"evidence_id": found[0]["accepted_evidence_id"], "connector_asset_id": found[0]["asset_id"],
                "start_at": _hm(lo), "end_at": _hm(hi), "kwh": kwh, "error_bound_kwh": METER_ERROR, "use": use,
                "reason": reason}

    expanded = {**table, "start_at": _hm(table["start_at"]),
                "end_at": None if table["end_at"] is None else _hm(table["end_at"]),
                "fault_evidence_id": None if table["fault_evidence_id"] is None else event(table["fault_evidence_id"]),
                "finding_support_evidence_ids": sorted(event(s) for s in table["finding_support_evidence_ids"]),
                "intervals": [meter(*m) for m in table["intervals"]]}
    assert tuple(sorted(expanded)) == tuple(sorted(EXPECTED_KEYS))
    return expanded


def binding_members(built: Chain, set_id: str) -> list[dict]:
    """q4 Q4-2: every immutable `signal_binding_revision` member of the case's effective selected set, ordered by
    lowercase member ID; each member's set ID equals the manifest's selected set ID."""
    from assetops_backend.financials.fuel_cost import iso

    with built.engine.connect() as c:
        rows = c.execute(text(
            "SELECT id, binding_set_revision_id, role, asset_id, source_id, device_id, signal_id, valid_from, "
            "valid_to FROM signal_binding_revision WHERE tenant_id = :t AND site_id = :s "
            "AND binding_set_revision_id = :b"), {"t": built.tenant_id, "s": built.site_id, "b": set_id}).all()
    assert rows
    members = sorted(({"binding_revision_id": str(r.id).lower(),
                       "binding_set_revision_id": str(r.binding_set_revision_id).lower(), "role": r.role,
                       "asset_id": None if r.asset_id is None else str(r.asset_id).lower(),
                       "source_id": str(r.source_id).lower(), "device_id": r.device_id, "signal_id": r.signal_id,
                       "valid_from": iso(r.valid_from), "valid_to": None if r.valid_to is None else iso(r.valid_to)}
                      for r in rows), key=lambda m: m["binding_revision_id"])
    assert all(m["binding_set_revision_id"] == set_id.lower() for m in members)
    assert all(tuple(sorted(m)) == tuple(sorted(MEMBER_KEYS)) for m in members)
    return members


def vector_case(built: Chain, document: dict, first_ids: list[str] | None,
                first_known_at: datetime | None) -> dict:
    from assetops_backend.financials.fuel_cost import iso

    records = vector_records(built, document)
    assert [r["accepted_evidence_id"] for r in records] == document["accepted_evidence_ids"]
    assert all(tuple(sorted(r)) == tuple(sorted(RECORD_KEYS)) for r in records)
    members = binding_members(built, document["binding_revision_id"])
    member_ids = {m["binding_revision_id"] for m in members}
    assert all(r["binding_set_revision_id"] == document["binding_revision_id"] for r in records)
    assert all(r["binding_revision_id"] in member_ids for r in records)
    connector = SELECTED[built.case]
    asset = _connector_asset(built, connector)
    first = None
    if built.case == "late-record":
        assert first_ids is not None
        visible = [r for r in records if r["accepted_evidence_id"] in set(first_ids)]
        assert [r["accepted_evidence_id"] for r in visible] == first_ids
        assert not [r for r in visible if r["record_kind"] == "EV_SESSION_END"]
        # q3 P6 / q4 Q4-1: the queried first committed watermark and the sorted accepted IDs (held END absent).
        first = {**expand(LATE_FIRST, visible, asset), "known_at": iso(first_known_at),
                 "accepted_evidence_ids": sorted(first_ids)}
    case = {"manifest": f"contract-fixtures/w2/ev/{built.case}.json", "window": document["window"],
            "selected_connector": connector, "records": records, "binding_members": members,
            "expected": expand(R12_TABLE[built.case], records, asset), "first_cutoff": first}
    assert tuple(sorted(case)) == CASE_KEYS
    return case


def vector_document(cases: dict) -> dict:
    assert tuple(cases) == CASES
    return {"schema": VECTOR_SCHEMA, "cases": cases}


# --- the six proofs -------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_six_registered_replays(chain, case) -> None:
    built = chain(case)
    built.start_release_upload()
    first_cutoff = None
    if case == "late-record":
        first_cutoff = (built.replay(), _accepted(built))
        built.advance_late()
    replay = built.replay()
    produced = manifest(built, replay)
    document = pinned(case, produced)
    # The second clean database reproduces the pinned first one byte for byte.
    assert canonical_file(produced) == canonical_file(document)
    # W2-06 q3 P1: the clock attestation recorded before upload leaves every manifest byte unchanged.
    assert (MANIFESTS / f"{case}.json").read_bytes() == canonical_file(produced).encode("utf-8")
    _check_types(document)
    assert document["schema"] == "ev-replay-manifest/1" and document["site_code"] == EV
    assert document["seed"] == 20517 and document["window"] == WINDOW
    assert (document["model_profile"], document["publication_profile"], document["observation_profile"]) == \
        ("ev-charger/1", "ev-publication/1", "ev-observation/1")
    assert document["scenario_sha256"] == definition(case).scenario_sha256
    assert document["assertions"] == EXPECTED[case]
    # Replay route agrees with the manifest's public transport; counts come from persisted dispositions.
    assert replay["accepted_record_ids"] == document["accepted_evidence_ids"]
    assert [r["batch_id"] for r in replay["receipts"]] == replay["batch_ids"]
    assert sum(r["accepted"] for r in replay["receipts"]) == len(document["accepted_evidence_ids"])
    assert replay["scenario_digest"] == document["scenario_sha256"]
    assert {d["decision"] for d in document["receipt_dispositions"]} == {"ACCEPTED"}
    # Q26 cross-check from the accepted GOOD public rows only.
    accepted = _accepted(built)
    view, raw = cross_check(accepted, SELECTED[case])
    expected = {k: v for k, v in EXPECTED[case].items() if k != "first_cutoff_outcome"}
    assert view == expected, (view, expected)
    assert raw is not None and f"{raw.quantize(Decimal('0.001'))}" == RAW_ACCEPTED_KWH[case]
    assert world_total(built) == Fraction(WORLD_KWH[case])  # the private total: beside, never equated
    if case == "missing-meter":
        assert raw != Decimal(WORLD_KWH[case]) and EXPECTED[case]["supported_kwh"] != "30.000"
    if case == "fault":
        # Q27/Q28: c1 faults and clears but never starts; no c1 session, abort or session energy.
        c1 = [e for e in accepted if e["source"]["device_id"].startswith("c1-")]
        assert not _events(c1, "c1", "session-event", "EV_SESSION_START")
        assert not _events(c1, "c1", "session-event", "EV_SESSION_ABORT")
        assert not [e for e in c1 if _channel(e) == ("c1-connector-meter", "energy")
                    and e["payload"]["session_id"] is not None]
        assert cross_check(accepted, "c1")[0]["outcome"] is None
    if case == "contradictory":
        # Q29: both GOOD ENDs accepted with distinct event IDs, plus the 08:01 START; raw deltas not lost.
        ends = _events(accepted, "c1", "session-event", "EV_SESSION_END")
        assert sorted(_at(e) for e in ends) == [_t(30), _t(31)]
        assert len({e["payload"]["event_id"] for e in ends}) == 2
        assert len({(e["payload"]["session_id"], e["payload"]["connector_id"]) for e in ends}) == 1
    if case == "late-record":
        first_replay, first_rows = first_cutoff
        # Q30: at 09:00 the START and 30.000 kWh of known deltas are accepted, but no END: INCOMPLETE.
        first_view, first_raw = cross_check(first_rows, "c1")
        assert first_view["outcome"] == "INCOMPLETE" == EXPECTED[case]["first_cutoff_outcome"]
        assert first_view["end_at"] is None and f"{first_raw.quantize(Decimal('0.001'))}" == "30.000"
        assert set(first_replay["batch_ids"]) < set(replay["batch_ids"])
        assert set(first_replay["accepted_record_ids"]) < set(replay["accepted_record_ids"])
        assert first_replay["public_digest"] != replay["public_digest"]


def test_w206_ev_vector_artifact(chain, monkeypatch) -> None:
    """W2-06 q4 Q4-3: all six chains in case order, each manifest and persisted publication -> batch ->
    disposition chain checked, the whole vector file assembled in memory, then written once
    (`ASSETOPS_W206_WRITE_VECTORS=1`) or byte-compared once. Per-case assertions name the failing case."""
    from assetops_backend.financials.fuel_cost import iso

    cases: dict[str, dict] = {}
    for case in CASES:
        built = chain(case)
        try:
            built.start_release_upload()
            first = None
            if case == "late-record":
                first_replay = built.replay()
                first_known_at = watermark(built)
                assert iso(first_known_at) == "2026-10-06T09:00:00.000000Z", case
                first = (first_replay["accepted_record_ids"], first_known_at)
                built.advance_late()
                assert iso(watermark(built)) == "2026-10-06T09:05:00.000000Z", case
            else:
                assert iso(watermark(built)) == "2026-10-06T09:00:00.000000Z", case
            produced = manifest(built, built.replay())
            document = pinned(case, produced)
            assert (MANIFESTS / f"{case}.json").read_bytes() == canonical_file(produced).encode("utf-8"), case
            cases[case] = vector_case(built, document, *(first or (None, None)))
        finally:
            built.close()
            monkeypatch.undo()  # the next case's `hold_uuids` counter replaces the real allocator afresh
    rendered = _vector_text(vector_document(cases)).encode("utf-8")
    if os.environ.get("ASSETOPS_W206_WRITE_VECTORS") == "1":
        VECTORS.parent.mkdir(parents=True, exist_ok=True)
        VECTORS.write_bytes(rendered)
    pinned_bytes = VECTORS.read_bytes()
    assert not pinned_bytes.startswith(b"\xef\xbb\xbf") and b"\r" not in pinned_bytes
    assert pinned_bytes.endswith(b"\n") and not pinned_bytes.endswith(b"\n\n")
    pinned_document = json.loads(pinned_bytes.decode("utf-8"))
    for case in CASES:
        assert _vector_text(pinned_document["cases"][case]) == _vector_text(cases[case]), case
    assert pinned_bytes == rendered


def test_late_record_cutoff_and_release(chain) -> None:
    """Q30: the held END is PENDING and absent at 09:00; at 09:05 it is released once, unchanged, and accepted."""
    built = chain("late-record")
    built.start_release_upload()
    schedule = built.host.publication_schedule(built.run)
    [held] = schedule.delayed
    assert (held.state, held.source_time, held.scheduled_release_at) == ("PENDING", _t(31), RELEASE)
    first = built.replay()
    texts_before = [t for (_, _, t, _, _, _) in _envelopes(built)]
    assert not [t for t in texts_before if json.loads(t)["payload"].get("record_kind") == "EV_SESSION_END"]
    ends_before = _events(_accepted(built), "c1", "session-event", "EV_SESSION_END")
    assert ends_before == []
    built.advance_late()
    [after] = built.host.publication_schedule(built.run).delayed
    assert after.state == "RELEASED" and (after.report_key, after.report_text) == (held.report_key, held.report_text)
    late = [(json.loads(t), batch) for batch in built.batches()
            for t in parse_canonical_batch_v2_text(batch["text"]).envelopes
            if json.loads(t)["payload"].get("record_kind") == "EV_SESSION_END"]
    assert len(late) == 1
    envelope, batch = late[0]
    report = json.loads(held.report_text)
    assert envelope["timing"]["source_time"] == _t(31) == report["source_time"]
    assert envelope["payload"]["event_id"] == report["event_id"]
    assert envelope["timing"]["published_at"] >= RELEASE
    assert batch["received_at"] == LATE_DECISION  # r5 R5-1: exactly the fixed 09:05 ingestion clock of the late phase
    assert batch["batch_id"] not in first["batch_ids"]
    final = built.replay()
    assert len(final["publication_ids"]) == len(final["batch_ids"]) > len(first["batch_ids"])
    # A second advance to the same instant releases nothing new.
    built.advance_late()
    assert built.released[-1]["released_now"] == 0
    assert built.replay() == final


def test_second_release_duplicate(chain) -> None:
    built = chain("complete")
    built.start_release_upload()
    first = built.replay()
    before = built.batches()
    # Gateway layer: the same reports again are ALREADY_ADMITTED by report key (no new sequence).
    basis = built.run.registered_basis
    revision = next(r for r in built.store.revisions(built.tenant_id, built.site_id)
                    if str(r.id) == basis.foundation_revision_id)
    inputs = StoreEvInputs(built.store, cached_scenario_repository())
    binding = inputs.binding_revision(built.tenant_id, built.site_id, UUID(basis.binding_set_revision_id))
    verified = verify_ev_inputs(built.run, revision, binding, definition("complete"))
    reports = [r.report_text for r in ev_reports(verified.definition, verified.channels,
                                                  ev_execution(verified.definition, verified.parameters))][:20]
    answer = built.process.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256,
                                               "lab_run_ref": built.run.run_id, "reports": reports})
    assert {a["outcome"] for a in answer["admissions"]} == {"ALREADY_ADMITTED"}
    # Commit layer: a second release releases nothing new and a further upload pass sends nothing.
    built.release_and_upload()
    assert built.released[-1]["released_now"] == 0
    # Central layer: the same external batch posted again is idempotent - no second disposition set.
    central = built.central
    replayed = [r for r in central.requests if r.path.endswith("/batches")][0]
    count_before = len(central.requests)
    status, _ = central.responder(replayed.path, replayed.headers, replayed.body)
    assert status == 200 and len(central.requests) == count_before
    assert [b["dispositions"] for b in built.batches()] == [b["dispositions"] for b in before]
    again = built.replay()
    assert again == first


def _post(built: Chain, texts: list[str]) -> None:
    basis = built.run.registered_basis
    snapshot = json.loads(basis.snapshot_canonical)
    first = json.loads(texts[0])
    _, body = seal_batch_v2(
        site_id=first["source"]["site_id"], gateway_id=first["source"]["gateway_id"],
        source_id=first["source"]["source_id"], source_mode="SIMULATED",
        foundation_version=snapshot["foundation"]["version"],
        foundation_valid_from=snapshot["foundation"]["valid_from"],
        binding_set_id=snapshot["mapping"]["binding_set_id"], binding_version=snapshot["mapping"]["version"],
        snapshot_sha256=basis.snapshot_sha256, envelope_texts=texts)
    status, payload = built.central.responder(
        "/api/ingestion/batches", {"Authorization": f"Bearer {built.credential}",
                                   "Content-Type": "application/json"}, body.encode("utf-8"))
    assert status == 200, payload


def _reissued(envelope: dict, seq: int, timing: dict | None = None, **payload) -> str:
    """An accepted envelope with a fresh message identity (`conflict-probe` epoch) and changed payload."""
    copy = json.loads(json.dumps(envelope))
    s = copy["source"]
    copy["message"] = {"message_id": v3_message_id(site_id=s["site_id"], gateway_id=s["gateway_id"],
                                                   source_id=s["source_id"], sequence_epoch="conflict-probe",
                                                   sequence=seq),
                       "sequence_epoch": "conflict-probe", "sequence": seq}
    copy["payload"].update(payload)
    copy["timing"].update(timing or {})
    return canonical_json(copy)


def test_s2_delta_connector_and_event_session_conflicts(chain) -> None:
    """The S2 ledger keeps the originals: a delta on the wrong connector, a reused event ID, a second START."""
    built = chain("complete")
    built.start_release_upload()
    accepted = _accepted(built)
    before = built.replay()
    delta = _session_deltas(accepted, "c1", *[(e["payload"]["session_id"], e["payload"]["connector_id"]) for e in
                                              _events(accepted, "c1", "session-event", "EV_SESSION_START")][0])[0]
    snapshot = json.loads(built.run.registered_basis.snapshot_canonical)
    c2_asset_id = next(b["asset_id"] for b in snapshot["bindings"]
                       if (b["device_id"], b["signal_id"]) == ("c2-connector-meter", "energy"))
    with built.engine.connect() as c:
        c2_asset = c.execute(text("SELECT asset_code FROM asset WHERE id = :a"), {"a": c2_asset_id}).scalar_one()
    assert c2_asset != delta["payload"]["connector_id"]
    _post(built, [_reissued(delta, 1, connector_id=c2_asset)])
    [start] = _events(accepted, "c1", "session-event", "EV_SESSION_START")
    # The accepted START's event ID with a different event identity (another source time).
    _post(built, [_reissued(start, 2, timing={"source_time": _t(2), "published_at": "2026-10-06T08:02:03Z"})])
    _post(built, [_reissued(start, 3, event_id="ev-" + "0" * 64)])
    with built.engine.connect() as c:
        kinds = sorted(c.execute(text("SELECT kind FROM evidence_rejection WHERE site_id = :s"),
                                 {"s": built.site_id}).scalars())
        decisions = sorted(c.execute(text(
            "SELECT d.decision FROM ingestion_disposition d JOIN ingestion_batch b ON b.id = d.batch_id "
            "WHERE b.site_id = :s AND d.decision <> 'ACCEPTED'"), {"s": built.site_id}).scalars())
    assert kinds == ["EVENT_ID_CONFLICT", "EV_CONNECTOR_MISMATCH", "SESSION_ID_CONFLICT"], kinds
    assert decisions == ["CONFLICT", "CONFLICT", "REJECTED"], decisions
    # The run's replay is unchanged: probe batches belong to no run publication.
    assert built.replay() == before


def test_owner_scope_and_error_responses(chain) -> None:
    built = chain("complete")
    q = {"run_id": built.run.run_id}
    route = f"/api/sites/{EV}/ev/replay"

    def code(response):
        return response.status_code, response.json()["error"]["code"]

    assert code(built.replay_client(access=lambda r, s: 401).get(route, params=q)) == (401, "UNAUTHENTICATED")
    assert code(built.replay_client(access=lambda r, s: 403).get(route, params=q)) == (403, "SITE_SCOPE_FORBIDDEN")
    assert code(built.replay_client(owner=no_owner_principal).get(route, params=q)) == \
        (403, "SITE_SCOPE_FORBIDDEN")
    for bad in ({}, {"run_id": ""}, {"run_id": "not a run id"}):
        assert code(built.replay_client().get(route, params=bad)) == (422, "EV_REPLAY_PARAMETER_INVALID")
    assert code(built.replay_client().get(route, params=[("run_id", built.run.run_id)] * 2)) == \
        (422, "EV_REPLAY_PARAMETER_INVALID")
    assert code(built.replay_client().get("/api/sites/OTHER-1/ev/replay", params=q)) == (404, "SITE_NOT_FOUND")
    assert code(built.replay_client().get(route, params={"run_id": "run-" + "0" * 32})) == (404, "RUN_NOT_FOUND")
    # A persisted EV run with no publication yet is an empty, valid replay.
    empty = built.replay()
    assert empty["publication_id"] is None and empty["public_digest"] == sha("[]")
    assert empty["batch_ids"] == empty["receipts"] == empty["accepted_record_ids"] == []
    # Production composition: the Lab-gated route exists and no ownerless read succeeds (N1 default).
    from assetops_backend.config import FeatureFlags

    app = create_app(FeatureFlags(simulator_lab_enabled=True), run_repository=built.runs,
                     foundation_store=built.store)
    assert code(TestClient(app).get(route, params=q)) == (403, "SITE_SCOPE_FORBIDDEN")


def test_corrupt_link_and_missing_run_answer_503(chain) -> None:
    built = chain("complete")
    built.start_release_upload()
    real = build_ev_replay_reader(URL)

    class Tampered:
        def __init__(self, change):
            self.change = change

        def ev_replay_rows(self, tenant_id, site_id, run_id):
            rows = real.ev_replay_rows(tenant_id, site_id, run_id)
            rows["publications"] = [dict(p) for p in rows["publications"]]
            self.change(rows["publications"][0])
            return rows

        def ev_replay_run_referenced(self, tenant_id, site_id, run_id):
            return real.ev_replay_run_referenced(tenant_id, site_id, run_id)

    route = f"/api/sites/{EV}/ev/replay"
    q = {"run_id": built.run.run_id}
    for change in (lambda p: p.update(b_id=None), lambda p: p.update(b_status="RECEIVING"),
                   lambda p: p.update(b_text=p["b_text"].replace("ev-", "xx-", 1)),
                   lambda p: p.update(b_sha="0" * 64)):
        response = built.replay_client(reader=Tampered(change)).get(route, params=q)
        assert (response.status_code, response.json()["error"]["code"]) == (503, "EV_REPLAY_UNAVAILABLE")
    # A publication naming a run that is not persisted is unavailable, never an empty success.
    for path in (built.tmp / "runs").rglob("*"):
        if path.is_file() and built.run.run_id in path.read_text(encoding="utf-8", errors="ignore"):
            path.unlink()
    response = built.replay_client().get(route, params=q)
    assert (response.status_code, response.json()["error"]["code"]) == (503, "EV_REPLAY_UNAVAILABLE")


def test_public_digest_and_private_byte_scan(chain) -> None:
    built = chain("late-record")
    built.start_release_upload()
    built.advance_late()
    replay = built.replay()
    stage = built.host.registered_stage(built.run)
    stage_text = json.dumps([[getattr(b, "payload_text", "") for b in stage.batches]])
    with built.engine.connect() as c:
        accepted_rows = json.dumps([dict(r._mapping) for r in c.execute(text(
            "SELECT * FROM accepted_evidence WHERE site_id = :s"), {"s": built.site_id}).all()], default=str)
    batches = built.batches()
    surfaces = {"stage": stage_text, "batch": json.dumps([b["text"] for b in batches]),
                "accepted": accepted_rows, "replay": json.dumps(replay)}
    for name, surface in surfaces.items():
        for key in PRIVATE_KEYS:
            assert f'"{key}"' not in surface and f'\\"{key}\\"' not in surface, (name, key)
    assert built.run.run_id not in surfaces["replay"] + surfaces["batch"] + surfaces["stage"]
    # Recompute the digest from persisted batch text and dispositions.
    digest_input = [[b, o, sha(t), d, a if d in ("ACCEPTED", "DUPLICATE") else None]
                    for (b, o, t, d, a, _) in _envelopes(built)]
    assert replay["public_digest"] == sha(canonical_json(digest_input))
