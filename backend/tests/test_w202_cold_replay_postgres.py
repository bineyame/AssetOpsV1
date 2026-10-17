"""W2-02 commit (4): six registered cold replays through the real chain, pinned as public manifests.

`.agent/W2-02-build-spec.md` "Commit (4) exact contract". Each case runs in a fresh private `*_test` database:
install COLD-LAB-001 -> freeze a registered cold Draft -> Host Lab start with the frozen re-read port -> a real
`assetops_gateway serve` process admits the v2 reports and seals Stage -> preauthorized SYSTEM_LAB_RELEASE
publication and gateway release -> the gateway's own uploader posts Batch V2 over TLS to an in-process S2 ingestion
route -> the S2 ledger -> the cold replay route and the Site Evidence reads.

Determinism is held by explicit test fixtures only: a per-case UUID counter replaces `uuid4` in the loaded
backend/host modules (imported fixture IDs, run ID, publication and accepted-evidence IDs), the gateway epoch is
the case name, and every setup clock is fixed. Production allocation is unchanged.

Manifests are generated once with `ASSETOPS_W202_WRITE_MANIFESTS=1`, reviewed, then pinned; an ordinary run only
compares bytes and never writes. Needs `ASSETOPS_TEST_DATABASE_URL` naming a `*_test` database; skipped (never
passed) without it.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import types
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
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

    from assetops_backend.cold_replay import ColdReplayService
    from assetops_contracts.lab_projection import LabControlRefused
    from assetops_backend.cold_replay_api import build_cold_replay_router, development_owner, no_owner_principal
    from assetops_backend.evidence import ledger_service
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.composition import build_cold_replay_reader
    from assetops_backend.evidence.gateway_access import StoreGatewayPrincipals
    from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.legacy_comparison import (
        compare,
        environment_identity,
        legacy_inventory,
        store_root_identity,
    )
    from assetops_backend.evidence.models import SiteEvidence
    from assetops_backend.evidence.provision_gateway import main as provision
    from assetops_backend.evidence.service import IngestionService
    from assetops_backend.evidence_api import build_evidence_router
    from assetops_backend.gateway_api import install_gateway_tls_boundary
    from assetops_backend.main import create_app
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.profiles import COLD_PUBLICATION_PROFILE, COLD_THERMAL_MODEL
    from assetops_backend.runs.registered_basis import RegisteredLabBasis
    from assetops_backend.runs.registered_release import publisher_for
    from assetops_backend.runs.service import RunSetupService
    from assetops_backend.scenarios.composition import build_scenario_repository
    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore
    from assetops_backend.sites.cold_lab import install_cold_lab
    from assetops_backend.sites.cutover import ImportedSiteRegistry
    from assetops_backend.sites.foundation_service import FoundationService
    from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text, seal_batch_v2
    from assetops_contracts.source_envelope import canonical_json
    from assetops_contracts.source_envelope_v3 import v3_message_id
    from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS
    from cold_lab import StoreColdInputs
    from cold_publication import cold_reports, verify_cold_inputs
    from fake_central import CERT, FakeCentral
    from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config, write_upload_credential
    from gateway_publication import RegisteredGatewayPublisher
    from lab_execution import HostLabExecution, YamlExecutionArtifacts
    from publication_schedule import JsonPublicationSchedules
    from run_fixtures import FakeScenarios, FakeSites, site
    from source_stages import JsonSourceStages
    from test_s1_bindings_postgres import Clock
    from test_w202_cold_run_identity import cold_definition, cold_request

CASES = ("normal", "excursion", "backup-failed", "missing-probe", "late-reading", "contradictory")
MANIFESTS = ROOT / "contract-fixtures" / "w2" / "cold"
COLD = "COLD-LAB-001"
INSTALL_AT = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
SETUP_AT = datetime(2026, 10, 6, 18, 0, tzinfo=timezone.utc)
WINDOW = {"start": "2026-10-06T19:00:00Z", "end": "2026-10-06T20:05:00Z", "end_exclusive": True}
RELEASE = "2026-10-06T20:10:00Z"
MANIFEST_KEYS = ("schema", "scenario_id", "scenario_sha256", "model_profile", "publication_profile",
                 "observation_profile", "observation_sha256", "seed", "site_code", "foundation_revision_id",
                 "binding_revision_id", "window", "envelope_sha256", "batch_sha256", "receipt_dispositions",
                 "accepted_evidence_ids", "public_digest", "assertions")
ASSERTION_KEYS = ("chamber_point_count", "event_kinds", "unavailable_count", "late_source_time",
                  "late_published_at", "start_result_at", "transfer_result_at", "high_1915", "high_1920")
#: Private forcing/state/oracle keys that must never appear in Stage, Batch, accepted rows or replay JSON.
PRIVATE_KEYS = ("heat_kwh", "cool_kwh", "minute_records", "forcings", "forcing", "before", "after",
                "private_state", "content_digest", "door_heat", "heat_leak", "thermal_capacity", "run_id",
                "trajectory", "oracle", "cold-private")


def sha(text_value: str) -> str:
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def canonical_file(document: dict) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


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

    def open(self) -> "Chain":
        url = make_url(URL)
        assert url.database and url.database.endswith("_test"), "Refusing a database not named *_test"
        pg_harness.fresh_database()
        self.engine = create_engine(URL)
        self.store = PostgresFoundationStore(URL)
        result = install_cold_lab(self.store, tenant_slug="demo", clock=Clock(INSTALL_AT))
        self.tenant_id, self.site_id = result.tenant.id, result.site.id
        self.runs = YamlRunStore(self.tmp / "runs")
        setup = RunSetupService(
            self.runs, FakeSites((site(site_id=COLD),)), FakeScenarios((cold_definition(self.case),)),
            model_profiles=(COLD_THERMAL_MODEL,), publication_profiles=(COLD_PUBLICATION_PROFILE,),
            now=lambda: "2026-10-06T18:00:00Z",
            registered_bases=RegisteredLabBasis(ImportedSiteRegistry(FoundationService(self.store, "demo",
                                                                                       Clock(SETUP_AT)))))
        self.run = setup.create_draft_run(cold_request(self.case))
        assert self.run.execution_status == "READY", self.run.blocking_reasons
        self._gateway()
        self.host = HostLabExecution(
            artifacts=YamlExecutionArtifacts(self.tmp / "executions"),
            stages=JsonSourceStages(self.tmp / "stages"),
            gateway=RegisteredGatewayPublisher(self.process.link),
            schedules=JsonPublicationSchedules(self.tmp / "schedules"),
            source_publisher=publisher_for(URL),
            cold_inputs=StoreColdInputs(self.store, build_scenario_repository()),
        )
        return self

    def _gateway(self) -> None:
        with self.engine.connect() as c:
            gateway = c.execute(text("SELECT id, gateway_external_id FROM gateway WHERE site_id = :s"),
                                {"s": self.site_id}).one()
            sources = list(c.execute(text("SELECT source_external_id FROM source WHERE gateway_id = :g "
                                          "ORDER BY source_external_id"), {"g": gateway.id}).scalars())
        out = self.tmp / "issued"
        out.mkdir(parents=True)
        flags = [x for s in sources for x in ("--enable-source", s)]
        assert provision(["--tenant", "demo", "--site", COLD, "--gateway", gateway.gateway_external_id, "issue",
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
            batch_ingestion=BatchIngestionService(PostgresEvidenceLedger(URL), lambda: datetime.now(timezone.utc)),
            gateway_principals=StoreGatewayPrincipals(PostgresGatewayAccess(URL))))
        central = TestClient(central_app, base_url="https://testserver")

        def forward(path, headers, body):
            wanted = {k: v for k, v in headers.items() if k.lower() in ("authorization", "content-type")}
            answer = central.post(path, content=body, headers=wanted)
            return answer.status_code, answer.content

        self.central = FakeCentral(forward)
        config = write_config(state, provisioning_from_snapshot(self.run.registered_basis.snapshot_canonical,
                                                                epoch=f"cold-{self.case}"))
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

    def replay_client(self, *, access=None, owner=None) -> TestClient:
        app = FastAPI()
        scope = (lambda code: (COLD, self.tenant_id, self.site_id) if code.upper() == COLD else None)
        app.include_router(build_cold_replay_router(
            ColdReplayService(build_cold_replay_reader(URL), self.runs), scope,
            access=access or (lambda request, code: None), owner=owner or development_owner))
        return TestClient(app)

    def replay(self) -> dict:
        response = self.replay_client().get(f"/api/sites/{COLD}/cold/replay", params={"run_id": self.run.run_id})
        assert response.status_code == 200, response.text
        return response.json()

    def evidence_client(self) -> TestClient:
        environment = environment_identity(URL)
        root = store_root_identity("c:\\ws-cold\\var\\evidence", "c:\\ws-cold\\var\\commits")
        report = compare(
            site_code=COLD, tenant_id=self.tenant_id, site_id=self.site_id, legacy=SiteEvidence(site_id=COLD),
            ledger_digests={}, bound_channels=(), legacy_dispatch_claims=[], recompute_jobs=[],
            compared_at="2026-10-06T18:30:00.000000Z", committed_artifacts=(), environment=environment,
            store_root=root)
        reads = ImportedEvidenceReads(
            PostgresEvidenceLedger(URL),
            lambda code: (COLD, self.tenant_id, self.site_id) if code.upper() == COLD else None,
            lambda code: report, lambda code: legacy_inventory(SiteEvidence(site_id=code), ()),
            environment, lambda: root)
        app = FastAPI()
        app.include_router(build_evidence_router(
            IngestionService(None, _NoSites()), _NoSites(), imported_reads=reads))  # type: ignore[arg-type]
        return TestClient(app)

    def chamber_records(self) -> list[dict]:
        response = self.evidence_client().get(
            f"/api/sites/{COLD}/evidence/records",
            params={"device": "chamber-probe", "signal": "temperature", "from": WINDOW["start"],
                    "to": WINDOW["end"], "limit": 500})
        assert response.status_code == 200, response.text
        return response.json()["records"]

    def batches(self) -> list[dict]:
        """Linked batches of this run's publications in replay order, with their dispositions."""
        with self.engine.connect() as c:
            rows = c.execute(text(
                "SELECT b.id, b.external_batch_id, b.payload_sha256, b.batch_text, b.received_at "
                "FROM evidence_publication p JOIN batch_publication_link l ON l.publication_id = p.id "
                "JOIN ingestion_batch b ON b.id = l.batch_id WHERE p.run_id = :run "
                "ORDER BY p.recorded_at, p.id"), {"run": self.run.run_id}).all()
            out = []
            for r in rows:
                dispositions = c.execute(text(
                    "SELECT ordinal, decision, CAST(accepted_evidence_id AS text) AS accepted "
                    "FROM ingestion_disposition WHERE batch_id = :b ORDER BY ordinal"), {"b": r.id}).all()
                out.append({"batch_id": r.external_batch_id, "payload_sha256": r.payload_sha256,
                            "text": r.batch_text, "received_at": r.received_at,
                            "dispositions": [(d.ordinal, d.decision, d.accepted) for d in dispositions]})
            return out


@pytest.fixture()
def chain(tmp_path, monkeypatch):
    opened: list[Chain] = []

    def make(case: str) -> Chain:
        hold_uuids(monkeypatch, CASES.index(case) + 1)
        built = Chain(case, tmp_path / case)
        opened.append(built)
        return built.open()

    yield make
    for built in opened:
        built.close()


# --- manifest -------------------------------------------------------------------------------------------


def _envelopes(chain: Chain) -> list[tuple[str, int, str, str, str | None]]:
    """(batch_id, ordinal, envelope text, decision, accepted ID) in replay order."""
    found = []
    for batch in chain.batches():
        parsed = parse_canonical_batch_v2_text(batch["text"])
        for ordinal, decision, accepted in batch["dispositions"]:
            found.append((batch["batch_id"], ordinal, parsed.envelopes[ordinal], decision, accepted))
    return found


def _assertions(chain: Chain) -> dict:
    accepted = [json.loads(t) for (_, _, t, d, _) in _envelopes(chain) if d == "ACCEPTED"]

    def at(e):
        return e["timing"]["source_time"]

    chamber = [e for e in accepted if (e["source"]["device_id"], e["source"]["signal_id"]) ==
               ("chamber-probe", "temperature") and e["payload"].get("value") is not None
               and WINDOW["start"] <= at(e) < WINDOW["end"]]
    events = sorted((e for e in accepted if e["payload"]["family"] == "EVENT"), key=at)  # stable: receipt order
    late = [e for e in accepted if e["timing"]["published_at"] >= RELEASE]
    starts = [e for e in events if e["payload"]["record_kind"] == "START_RESULT"]
    transfers = [e for e in events if e["payload"]["record_kind"] == "TRANSFER_RESULT"]
    by_time = {at(e): e["payload"]["value"] for e in chamber}
    excursion = chain.case == "excursion"
    return {
        "chamber_point_count": len(chamber),
        "event_kinds": [e["payload"]["record_kind"] for e in events],
        "unavailable_count": sum(1 for e in accepted if e["payload"].get("quality") == "UNAVAILABLE"),
        "late_source_time": at(late[0]) if late else None,
        "late_published_at": late[0]["timing"]["published_at"] if late else None,
        "start_result_at": at(starts[0]) if starts else None,
        "transfer_result_at": at(transfers[0]) if transfers else None,
        "high_1915": by_time.get("2026-10-06T19:15:00Z") if excursion else None,
        "high_1920": by_time.get("2026-10-06T19:20:00Z") if excursion else None,
    }


def manifest(chain: Chain, replay: dict) -> dict:
    run = chain.run
    identity = run.deterministic_identity
    profiles = identity.profiles
    envelopes = _envelopes(chain)
    return {
        "schema": "cold-replay-manifest/1",
        "scenario_id": identity.scenario.scenario_id,
        "scenario_sha256": identity.scenario.scenario_sha256,
        "model_profile": {"profile_id": profiles.model_profile_id, "profile_version": profiles.model_profile_version},
        "publication_profile": {"profile_id": profiles.publication_profile_id,
                                "profile_version": profiles.publication_profile_version},
        "observation_profile": {"profile_id": profiles.observation_profile_id,
                                "profile_version": profiles.observation_profile_version},
        "observation_sha256": profiles.observation_sha256,
        "seed": identity.seed,
        "site_code": identity.site.site_id,
        "foundation_revision_id": run.registered_basis.foundation_revision_id,
        "binding_revision_id": run.registered_basis.binding_set_revision_id,
        "window": WINDOW,
        "envelope_sha256": [sha(t) for (_, _, t, _, _) in envelopes],
        "batch_sha256": [b["payload_sha256"] for b in chain.batches()],
        "receipt_dispositions": [{"batch_id": b, "ordinal": o, "decision": d, "accepted_evidence_id": a}
                                 for (b, o, _, d, a) in envelopes],
        "accepted_evidence_ids": [a for (_, _, _, d, a) in envelopes if d == "ACCEPTED"],
        "public_digest": replay["public_digest"],
        "assertions": _assertions(chain),
    }


def pinned(case: str, built: dict) -> dict:
    path = MANIFESTS / f"{case}.json"
    if os.environ.get("ASSETOPS_W202_WRITE_MANIFESTS") == "1":
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        path.write_text(canonical_file(built), encoding="utf-8", newline="\n")
    text_value = path.read_text(encoding="utf-8")
    document = json.loads(text_value)
    assert text_value == canonical_file(document), f"{path} is not canonical JSON"
    assert tuple(document) == tuple(sorted(MANIFEST_KEYS)) and set(document) == set(MANIFEST_KEYS)
    assert set(document["assertions"]) == set(ASSERTION_KEYS)
    return document


# --- the six proofs -------------------------------------------------------------------------------------


@pytest.mark.parametrize("case", CASES)
def test_six_registered_replays(chain, case) -> None:
    built = chain(case)
    built.start_release_upload()
    if case == "late-reading":
        assert _assertions(built)["chamber_point_count"] == 12
        built.advance_late()
    replay = built.replay()
    produced = manifest(built, replay)
    document = pinned(case, produced)
    # The second clean replay is byte-identical to the pinned first one.
    assert canonical_file(produced) == canonical_file(document)
    assert document["schema"] == "cold-replay-manifest/1" and document["site_code"] == COLD
    assert document["seed"] == 20417 and document["window"] == WINDOW
    assert document["scenario_sha256"] == cold_definition(case).scenario_sha256
    # Replay route agrees with the manifest's public transport.
    assert replay["accepted_record_ids"] == document["accepted_evidence_ids"]
    assert [r["batch_id"] for r in replay["receipts"]] == replay["batch_ids"]
    assert sum(r["accepted"] for r in replay["receipts"]) == len(document["accepted_evidence_ids"])
    # Direct Site Evidence read: the chamber points the S2 records route serves.
    a = document["assertions"]
    expected = {"missing-probe": 7}.get(case, 13)
    assert a["chamber_point_count"] == expected
    served = [r for r in built.chamber_records() if r["original"]["value"] is not None]
    assert len(served) == expected
    if case == "normal":
        assert (a["start_result_at"], a["transfer_result_at"]) == ("2026-10-06T19:07:00Z", "2026-10-06T19:08:00Z")
    if case == "backup-failed":
        assert a["start_result_at"] == "2026-10-06T19:05:00Z"
    if case == "excursion":
        assert float(a["high_1915"]) > 4.06 and float(a["high_1920"]) > 4.15
    if case == "late-reading":
        assert (a["late_source_time"], a["late_published_at"]) == ("2026-10-06T19:20:00Z", RELEASE)


def test_second_release_duplicate(chain) -> None:
    built = chain("normal")
    built.start_release_upload()
    first = built.replay()
    before = built.batches()
    # Gateway layer: the same reports again are ALREADY_ADMITTED by report key (no new sequence).
    store = built.store
    basis = built.run.registered_basis
    revision = next(r for r in store.revisions(built.tenant_id, built.site_id)
                    if str(r.id) == basis.foundation_revision_id)
    reports = [r.report_text for r in cold_reports(verify_cold_inputs(built.run, revision, cold_definition("normal")))]
    answer = built.process.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256,
                                               "lab_run_ref": built.run.run_id, "reports": reports[:20]})
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
    after = built.batches()
    assert [b["dispositions"] for b in after] == [b["dispositions"] for b in before]
    again = built.replay()
    assert again["accepted_record_ids"] == first["accepted_record_ids"]
    assert again["public_digest"] == first["public_digest"] and again["batch_ids"] == first["batch_ids"]


def test_late_source_time_and_receive_time(chain) -> None:
    built = chain("late-reading")
    built.start_release_upload()
    assert len([r for r in built.chamber_records() if r["original"]["value"] is not None]) == 12
    built.advance_late()
    assert len([r for r in built.chamber_records() if r["original"]["value"] is not None]) == 13
    late = [(json.loads(t), batch) for batch in built.batches()
            for t in parse_canonical_batch_v2_text(batch["text"]).envelopes
            if json.loads(t)["timing"]["published_at"] == RELEASE]
    assert len(late) == 1
    envelope, batch = late[0]
    assert envelope["timing"]["source_time"] == "2026-10-06T19:20:00Z"
    received = batch["received_at"]
    assert received > datetime(2026, 10, 6, 20, 10, tzinfo=timezone.utc)
    replay = built.replay()
    assert len(replay["publication_ids"]) == len(replay["batch_ids"]) >= 2


def test_event_conflict_counts(chain, monkeypatch) -> None:
    built = chain("normal")
    built.start_release_upload()
    basis = built.run.registered_basis
    # EVENT_ID_CONFLICT through the gateway: an accepted event's ID with a changed outcome, a new report key.
    accepted = [json.loads(t) for (_, _, t, d, _) in _envelopes(built) if d == "ACCEPTED"]
    start_result = next(e for e in accepted if e["payload"].get("record_kind") == "START_RESULT")
    p = start_result["payload"]
    report = {
        "schema": {"id": "assetops.simulated-device-report", "version": 2},
        "report_key": "cold:" + "f" * 64, "device_id": start_result["source"]["device_id"],
        "signal_id": start_result["source"]["signal_id"], "source_time": start_result["timing"]["source_time"],
        "family": "EVENT", "measurement": None, "interval_start": None, "interval_end": None, "value": None,
        "unit": None, "quality": "GOOD", "unavailable_reason": None, "record_kind": "START_RESULT",
        "event_id": p["event_id"], "correlation_id": p["correlation_id"], "component_id": p["component_id"],
        "actor": p["actor"], "outcome": "FAILED" if p["outcome"] == "SUCCEEDED" else "SUCCEEDED",
        "session_id": None, "connector_id": None,
    }
    answer = built.process.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256,
                                               "lab_run_ref": "conflict-probe", "reports": [canonical_json(report)]})
    assert answer["admissions"][0]["outcome"] == "ADMITTED"
    built.process.link.call("seal")
    built.process.link.call("release_run", {"lab_run_ref": "conflict-probe"})
    while RegisteredGatewayPublisher(built.process.link).deliver(50)["batches"]["attempted"]:
        pass
    # SESSION_ID_CONFLICT: COLD-LAB-001 binds no session channel and the gateway refuses an unbound channel,
    # so the session vector is posted to the ordinary S2 ingestion route with the reserved EV session channel
    # bound test-only exactly as W2-00's acceptance does (`test_w200_source_events_postgres.py:v4`).
    original = ledger_service.basis_from_snapshot

    def patched(stored, **kw):
        found = original(stored, **kw)
        template = found.bindings[("chamber-probe", "temperature")]
        entry = V4_CHANNEL_MAPPINGS[("charger-controller", "session-event")]
        extra = replace_binding(template, device_id="charger-controller", signal_id="session-event",
                                role="test-session", asset_code="charger-1", source_unit="none", canonical_unit="none",
                                conversion={"kind": "IDENTITY", "parameters": {}}, **entry.metadata())
        return replace_basis(found, bindings={**found.bindings, ("charger-controller", "session-event"): extra})

    monkeypatch.setattr(ledger_service, "basis_from_snapshot", patched)
    snapshot = json.loads(basis.snapshot_canonical)
    gateway_id = snapshot["gateway"]["gateway_id"]
    site_uuid = snapshot["site"]["site_id"]
    probe = next(b for b in snapshot["bindings"] if (b["device_id"], b["signal_id"]) == ("chamber-probe", "temperature"))

    def session_start(seq: int, event_id: str, minute: str) -> str:
        source_time = f"2026-10-06T19:{minute}:00Z"
        return canonical_json({
            "schema": {"id": "assetops.source-envelope", "version": 4},
            "message": {"message_id": v3_message_id(site_id=site_uuid, gateway_id=gateway_id, source_id=probe["source_id"],
                                                    sequence_epoch="session-probe", sequence=seq),
                        "sequence_epoch": "session-probe", "sequence": seq},
            "source": {"site_id": site_uuid, "gateway_id": gateway_id, "source_id": probe["source_id"],
                       "device_id": "charger-controller", "signal_id": "session-event"},
            "mapping": {"binding_set_id": snapshot["mapping"]["binding_set_id"],
                        "version": snapshot["mapping"]["version"]},
            "timing": {"source_time": source_time, "published_at": source_time, "interval_start": None,
                       "interval_end": None},
            "payload": {"family": "EVENT", "record_kind": "EV_SESSION_START", "event_id": event_id,
                        "correlation_id": "sess-1", "component_id": "charger-1", "actor": "CONTROLLER",
                        "outcome": "STARTED", "unit": None, "value": None, "quality": "GOOD",
                        "session_id": "sess-1", "connector_id": "charger-1"},
        })

    for texts in ([session_start(1, "start-1", "30")], [session_start(2, "start-2", "31")]):
        _, body = seal_batch_v2(
            site_id=site_uuid, gateway_id=gateway_id, source_id=probe["source_id"], source_mode="SIMULATED",
            foundation_version=snapshot["foundation"]["version"],
            foundation_valid_from=snapshot["foundation"]["valid_from"],
            binding_set_id=snapshot["mapping"]["binding_set_id"], binding_version=snapshot["mapping"]["version"],
            snapshot_sha256=basis.snapshot_sha256, envelope_texts=texts)
        status, payload = built.central.responder("/api/ingestion/batches",
                                            {"Authorization": f"Bearer {built.credential}",
                                             "Content-Type": "application/json"}, body.encode("utf-8"))
        assert status == 200, payload
    # The actual Site Evidence and rejection-list routes count both kinds as conflicts.
    client = built.evidence_client()
    rejections = client.get(f"/api/sites/{COLD}/evidence/rejections").json()
    kinds = sorted(r["kind"] for r in rejections["rejections"])
    assert "EVENT_ID_CONFLICT" in kinds and "SESSION_ID_CONFLICT" in kinds
    assert kinds == ["EVENT_ID_CONFLICT", "SESSION_ID_CONFLICT"]
    counts = client.get(f"/api/sites/{COLD}/evidence").json()["counts"]
    assert (counts["conflicts"], counts["rejected"]) == (2, 0)  # both count as conflicts, neither as rejected


def replace_binding(template, **changes):
    from dataclasses import replace

    return replace(template, **changes)


def replace_basis(found, **changes):
    from dataclasses import replace

    return replace(found, **changes)


def test_owner_and_tenant_gate(chain) -> None:
    built = chain("normal")
    q = {"run_id": built.run.run_id}
    route = f"/api/sites/{COLD}/cold/replay"
    assert built.replay_client(access=lambda r, s: 401).get(route, params=q).status_code == 401
    assert built.replay_client(access=lambda r, s: 403).get(route, params=q).json()["error"]["code"] == \
        "SITE_SCOPE_FORBIDDEN"
    assert built.replay_client(owner=no_owner_principal).get(route, params=q).status_code == 403
    assert built.replay_client().get("/api/sites/OTHER-1/cold/replay", params=q).json()["error"]["code"] == \
        "SITE_NOT_FOUND"
    assert built.replay_client().get(route, params={"run_id": "run-none"}).json()["error"]["code"] == \
        "RUN_NOT_FOUND"
    # A persisted cold run with no publication yet is an empty, valid replay.
    empty = built.replay()
    assert empty["publication_id"] is None and empty["public_digest"] == sha("[]")
    # Production composition: the Lab-gated route exists and no ownerless read succeeds.
    from assetops_backend.config import FeatureFlags

    app = create_app(FeatureFlags(simulator_lab_enabled=True), run_repository=built.runs,
                     foundation_store=built.store)
    response = TestClient(app).get(route, params=q)
    assert response.status_code == 403 and response.json()["error"]["code"] == "SITE_SCOPE_FORBIDDEN"
    gated = create_app(FeatureFlags(simulator_lab_enabled=False), run_repository=built.runs,
                       foundation_store=built.store)
    assert TestClient(gated).get(route, params=q).status_code == 404


def test_public_digest_no_private_truth(chain) -> None:
    built = chain("excursion")
    built.start_release_upload()
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
                    for (b, o, t, d, a) in _envelopes(built)]
    assert replay["public_digest"] == sha(canonical_json(digest_input))


def _report(key: str, device: str, signal: str, source_time: str, **payload) -> str:
    report = {
        "schema": {"id": "assetops.simulated-device-report", "version": 2}, "report_key": "cold:" + sha(key),
        "device_id": device, "signal_id": signal, "source_time": source_time, "family": "MEASUREMENT",
        "measurement": None, "interval_start": None, "interval_end": None, "value": None, "unit": None,
        "quality": "GOOD", "unavailable_reason": None, "record_kind": None, "event_id": None,
        "correlation_id": None, "component_id": None, "actor": None, "outcome": None, "session_id": None,
        "connector_id": None,
    }
    report.update(payload)
    return canonical_json(report)


def test_v4_gateway_to_ledger_probe(chain) -> None:
    """Rule 8 / W2-02: one V4 measurement and one V4 event from gateway allocation to the S2 accepted read."""
    built = chain("normal")
    basis = built.run.registered_basis
    RegisteredGatewayPublisher(built.process.link)._activate(basis)
    reports = [
        _report("probe-measurement", "chamber-probe", "temperature", "2026-10-06T19:00:00Z",
                measurement="STATE_AT_INSTANT", value="3", unit="degC"),
        _report("probe-event", "door-sensor", "event", "2026-10-06T19:01:00Z", family="EVENT",
                record_kind="DOOR_OPEN", event_id="cold-" + sha("probe-door"), correlation_id="cold-" + sha("door"),
                component_id="door-1", actor="SENSOR", outcome="OPEN"),
    ]
    answer = built.process.link.call("admit", {"snapshot_sha256": basis.snapshot_sha256, "lab_run_ref": "v4-probe",
                                               "reports": reports})
    admissions = answer["admissions"]
    assert [a["outcome"] for a in admissions] == ["ADMITTED", "ADMITTED"], admissions
    snapshot = json.loads(basis.snapshot_canonical)
    gateway_id = snapshot["gateway"]["gateway_id"]
    # The gateway allocates per (gateway, source, epoch): each report is the first of its source here.
    assert [a["sequence"] for a in admissions] == [1, 1]
    built.process.link.call("seal")
    built.process.link.call("release_run", {"lab_run_ref": "v4-probe"})
    while RegisteredGatewayPublisher(built.process.link).deliver(50)["batches"]["attempted"]:
        pass
    with built.engine.connect() as c:
        rows = c.execute(text("SELECT batch_text, id FROM ingestion_batch WHERE site_id = :s"),
                         {"s": built.site_id}).all()
        # Canonical Batch V2 bytes re-checked by the parser; one batch per source.
        texts = {}
        decided = {}
        for row in rows:
            for t in parse_canonical_batch_v2_text(row.batch_text).envelopes:
                texts[json.loads(t)["message"]["message_id"]] = t
            for d in c.execute(text("SELECT decision, message_id FROM ingestion_disposition WHERE batch_id = :b"),
                               {"b": row.id}).all():
                decided[d.message_id] = d.decision
    by_id = {json.loads(t)["message"]["message_id"]: json.loads(t) for t in texts.values()}
    envelopes = [by_id[a["message_id"]] for a in admissions]
    assert [e["schema"]["version"] for e in envelopes] == [4, 4]
    assert len({e["source"]["source_id"] for e in envelopes}) == 2
    for e, a in zip(envelopes, admissions):
        assert e["message"]["sequence"] == a["sequence"] == 1 and e["message"]["sequence_epoch"] == "cold-normal"
        expected = v3_message_id(site_id=e["source"]["site_id"], gateway_id=gateway_id,
                                 source_id=e["source"]["source_id"], sequence_epoch="cold-normal", sequence=1)
        assert e["message"]["message_id"] == expected == a["message_id"]
    assert decided == {e["message"]["message_id"]: "ACCEPTED" for e in envelopes}
    records = built.evidence_client().get(f"/api/sites/{COLD}/evidence/records", params={"limit": 50}).json()
    assert {r["message_id"] for r in records["records"]} == {e["message"]["message_id"] for e in envelopes}
