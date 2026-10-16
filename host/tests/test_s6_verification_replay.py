"""S6-02a: the `D-verification-window` replay - the complete verification path over real accepted public evidence.

`D-2026-10-16-s6-verification`, `D-2026-10-16-s602-questions`, `D-2026-10-16-s602a-cutoff`. The manifest
`backend/conversions/d-verification-window-v1.json` is replayed end to end against real PostgreSQL (skipped without
`ASSETOPS_TEST_DATABASE_URL`):

1. KOBO-001 imported and converted, the S3 dispatch demo configuration and the S6 verification demo configuration
   (`minigrid-roles-3`) applied.
2. A fixed-policy registered Lab run (`mini-grid` v4, `registered-kobo-publication` v4) on the old Foundation, through
   a real gateway process; its staged batches are registered as `REGISTERED_SIMULATION` publications and delivered
   into the ordinary S2 batch ingestion. S3 assesses and S4 matches.
3. S6-01: the Finding's reserve-trial recommendation is accepted and applied (a new Foundation revision).
4. S6-02a: a SYSTEM demonstration VERIFY freezes the plan before any later-window report exists.
5. A second, separate registered Lab run on the new Foundation, ingested the same way; S3 + S4 again.
6. The later selection is bound and evaluation requested; the evaluator job settles the outcome.

Every number the expected block pins comes from this replay; nothing in a window is authored or test-scoped.
With the shipped `mini-grid` model the settled verdict is INCONCLUSIVE, not VERIFIED: the generator policy reads
only the start/stop SOC thresholds, never the reserve, so the lower reserve leaves the later run five SOC points
lower (initial SOC outside the 2-point band) with the generator running longer (target miss). The manifest's
`expected.why_not_verified` states this, and the test pins the generator ON spans that show it.

S6-02b (`D-2026-10-16-s602a-replay`) adds manifest v2, replayed by the same test: the reserve-aware `mini-grid` v5
(generator start at min(start threshold, reserve + 5)) on the `kobo-mini-grid-reserve-trial` scenario, windows
predeclared before the first replay. It settles VERIFIED on the frozen bands (`expected.why_verified`); v1 stays
pinned beside it, so the earlier model version remains reproducible.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend" / "tests"))
sys.path.insert(0, str(ROOT / "gateway" / "tests"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
#: v1: mini-grid v4 on the prolonged scenario (settles INCONCLUSIVE, kept reproducible). v2 (S6-02b,
#: `D-2026-10-16-s602a-replay`): the reserve-aware mini-grid v5 on the reserve-trial scenario (settles VERIFIED).
MANIFESTS = {
    name: json.loads((ROOT / "backend" / "conversions" / f"d-verification-window-{name}.json").read_text("utf-8"))
    for name in ("v1", "v2")
}
FIVE = timedelta(minutes=5)


def _at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


@pytest.mark.parametrize("version", sorted(MANIFESTS))
def test_manifest_is_labelled_and_lists_only_proven_cases(version: str) -> None:
    MANIFEST = MANIFESTS[version]
    assert MANIFEST["schema"]["version"] == int(version[1:])
    assert MANIFEST["schema"]["id"] == "assetops.verification-window-replay"
    assert MANIFEST["label"] == "Simulated policy trial; no savings claim; RESOLVED can later be withdrawn"
    cases = {c["case_id"]: c for c in MANIFEST["cases"]}
    assert cases["complete-pass"]["status"] == (
        "replayed" if MANIFEST["expected"]["outcome"]["outcome"] == "VERIFIED" else "replayed-not-verified")
    assert cases["complete-pass"]["test"].endswith(
        "test_s6_verification_replay.py")
    for case_id in ("target-miss", "guardrail-fail", "missing-critical-role", "late-evidence-reassessment",
                    "different-finding-hold", "overlap"):
        status = cases[case_id]["status"]
        assert status == "not-replayed" or status.startswith("proven-in "), (case_id, status)
        if status.startswith("proven-in "):
            assert (ROOT / status.removeprefix("proven-in ").split("::")[0]).is_file(), status
    baseline, later = MANIFEST["windows"]["baseline_start"], MANIFEST["windows"]["later_start"]
    assert (_at(later) - _at(baseline)) % timedelta(days=1) == timedelta(0)
    for name, start in (("baseline", baseline), ("later", later)):
        run = MANIFEST["runs"][name]
        assert _at(run["start"]) <= _at(start) and _at(start) + timedelta(minutes=60) <= _at(run["end"])
    assert _at(baseline) + timedelta(minutes=60) <= _at(MANIFEST["action"]["effective_from"]) <= _at(later)


# --- the replay (PostgreSQL) ---------------------------------------------------------------------


class LabRunner:
    """The S6 test harness's runner surface (`test_s6_action_store_postgres.Harness`) over Lab-published evidence:
    S3 assessment and S4 matching only - no authored readings."""

    def __init__(self, store, engine, result, now: datetime) -> None:
        from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore

        self.store, self.engine, self.result = store, engine, result
        self.tenant, self.site = result.tenant.id, result.site.id
        self.now = now
        self.findings = PostgresFindingStore(URL)

    def tick(self) -> datetime:
        self.now += timedelta(minutes=1)
        return self.now

    def step(self, step: dict):
        import test_s4_finding_store_postgres as s4
        from assetops_backend.analytics import dispatch_v3
        from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
        from assetops_backend.analytics.adapters.postgres_finding_store import FindingFenceMoved
        from assetops_backend.analytics.assessment_worker import DispatchAssessmentWorker
        from assetops_backend.analytics.finding_service import FindingMatcher

        if step["do"] == "assess":
            for outcome in DispatchAssessmentWorker(PostgresAssessmentStore(URL), model=dispatch_v3,
                                                    clock=s4.Clock(self.tick())).run_pending():
                assert outcome.status == "DONE", outcome.error
            return None
        if step["do"] == "match":
            return FindingMatcher(PostgresAssessmentStore(URL), self.findings, model=dispatch_v3,
                                  now=lambda: self.tick(), fence_moved=FindingFenceMoved).match(self.tenant, self.site)
        raise AssertionError(f"a Lab replay has no authored step {step['do']!r}")

    def reload(self) -> dict:
        from assetops_backend.analytics.adapters.postgres_finding_store import PostgresFindingStore

        return PostgresFindingStore(URL).rows(self.tenant, self.site)


def _scenario(MANIFEST: dict):
    import test_s6_verification_publication as pub
    import yaml

    sid = MANIFEST["scenario"]["scenario_id"]
    scenario = pub.registered.parse_scenario_document(
        yaml.safe_load((ROOT / "config" / "scenarios" / f"{sid}.yaml").read_text(encoding="utf-8")),
        source=sid, origin="SHIPPED")
    assert scenario.version.scenario_version == MANIFEST["scenario"]["scenario_version"]
    return scenario


def _model(MANIFEST: dict):
    from assetops_backend.runs.profiles import MODEL_PROFILES, find_model_profile

    want = MANIFEST["model_profile"]
    model = find_model_profile(MODEL_PROFILES, want["profile_id"], want["profile_version"])
    assert model is not None, want
    return model


def _draft(store, run_spec: dict, MANIFEST: dict):
    import test_s6_verification_publication as pub

    registered = pub.registered
    scenario = _scenario(MANIFEST)
    known = registered.Clock(_at(run_spec["foundation_known_at"]))
    registry = registered.ImportedSiteRegistry(registered.FoundationService(store, "demo", known))
    service = registered.RunSetupService(
        registered.FakeRuns(), registered.FakeSites(()), registered.FakeScenarios((scenario,)),
        model_profiles=(_model(MANIFEST),),
        publication_profiles=(pub.REGISTERED_KOBO_PUBLICATION_PROFILE_V3, pub.V4),
        now=lambda: run_spec["foundation_known_at"],
        registered_bases=registered.RegisteredLabBasis(registry),
    )
    foundation = registered.FoundationService(store, "demo", known)
    tenant = foundation.tenant()
    view = foundation.read(foundation.site(tenant, MANIFEST["site_code"]), tenant, _at(run_spec["start"]), None)
    body = registered.request(
        foundation_version=view.revision.version, scenario_id=scenario.scenario_id,
        scenario_version=scenario.version.scenario_version,
        interval={"start_time": run_spec["start"], "end_time": run_spec["end"]},
        timestep_minutes=MANIFEST["timestep_minutes"], seed=run_spec["seed"],
        model_profile=MANIFEST["model_profile"], publication_profile=MANIFEST["publication_profile"],
    )
    run = service.create_draft_run(body)
    assert run.execution_status == "READY" and run.blocking_reasons == (), (run.execution_status, run.blocking_reasons)
    return run, view


def _gateway(tmp_path: Path, run, epoch: str, upload: dict):
    """A freshly provisioned gateway process for one run: its own state directory and sequence epoch (a second
    provisioning of the Site's gateway never reuses an epoch, so message IDs never collide across runs)."""
    from gateway_process import GatewayProcess, provisioning_from_snapshot, write_config

    config = write_config(tmp_path / "gateway",
                          provisioning_from_snapshot(run.registered_basis.snapshot_canonical, epoch=epoch))
    document = json.loads(config.read_text(encoding="utf-8"))
    config.write_text(json.dumps({**document, "upload": upload}), encoding="utf-8")
    process = GatewayProcess(config)
    assert process.ready, process.first_line
    return process


def _publish_and_accept(tmp_path: Path, run, epoch: str, received_at: datetime) -> dict:
    """One registered run through a real gateway: run to end, register its STAGED batches as REGISTERED_SIMULATION
    publications, release, and deliver every sealed batch into the ordinary S2 batch ingestion."""
    import test_s6_verification_publication as pub
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.publication import register_run
    from assetops_backend.runs.source_publication import run_attestation
    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text
    from assetops_gateway.credential_protection import restrict_to_current_user
    from fake_central import CERT, FakeCentral
    from gateway_publication import RegisteredGatewayPublisher

    doc = json.loads(run.registered_basis.snapshot_canonical)
    principal = GatewayPrincipal(tenant_id=UUID(doc["tenant_id"]), site_id=UUID(doc["site"]["site_id"]),
                                 gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])
    received = pub.registered.Clock(received_at)
    ingestion = BatchIngestionService(PostgresEvidenceLedger(URL, test_decision_clock_override=received), received)
    statuses: list[str] = []

    def respond(path, headers, body):
        if path.split("?")[0] != "/api/ingestion/batches":  # gateway diagnostics: not evidence
            return 201, b"{}"
        answer = ingestion.submit(principal, body)
        statuses.append(answer.receipt.status)
        return answer.status, canonical_receipt_v2_text(answer.receipt).encode("utf-8")

    token = f"aog1.{secrets.token_hex(16)}.{secrets.token_urlsafe(32)}"
    (tmp_path / "gateway").mkdir(parents=True)
    (tmp_path / "gateway" / "upload.credential").write_text(token, encoding="ascii")
    restrict_to_current_user(tmp_path / "gateway" / "upload.credential")
    central = FakeCentral(respond)
    process = _gateway(tmp_path, run, epoch, {"server_url": central.url, "upload_credential_file": "upload.credential",
                                           "ca_file": str(CERT), "interval_seconds": 3600})
    try:
        port = pub._host(tmp_path / "h", process.link)
        port.start(run)
        assert port.run_to_end(run).status == "COMPLETED"
        stage = port.registered_stage(run)
        assert stage.status == "STAGED", stage.status
        registrations = register_run(PostgresEvidenceLedger(URL), run_attestation(run, stage))
        port.release_registered(run)
        publisher = RegisteredGatewayPublisher(process.link)
        while publisher.deliver(50)["batches"]["attempted"]:
            pass
    finally:
        process.kill()
        central.close()
    assert statuses and set(statuses) == {"COMPLETED"}, statuses
    from sqlalchemy import create_engine, text

    engine = create_engine(URL)
    try:
        with engine.connect() as c:
            counts = c.execute(text(
                "SELECT count(*), sum(accepted_count), sum(duplicate_count), sum(rejected_count), sum(conflict_count) "
                "FROM ingestion_batch WHERE received_at = :r"), {"r": received_at}).one()
    finally:
        engine.dispose()
    # Every envelope the run staged is accepted: no duplicate, rejection or message conflict.
    assert tuple(counts) == (len(stage.batches), len(stage.envelopes), 0, 0, 0), tuple(counts)
    return {"batches": len(stage.batches), "envelopes": len(stage.envelopes), "publications": len(registrations)}


def _slots_all_present(engine, site_id, start: datetime) -> None:
    """Every five-minute slot of the window has each verification channel's GOOD reading (no dropout)."""
    from sqlalchemy import text

    end = start + timedelta(minutes=60)
    with engine.connect() as c:
        got = [dict(r._mapping) for r in c.execute(text(
            "SELECT role, asset_id, measurement, source_time, interval_start, interval_end, quality "
            "FROM accepted_evidence WHERE site_id = :s AND source_time >= :a AND source_time <= :b"),
            {"s": site_id, "a": start, "b": end + FIVE})]
    ends = [start + FIVE * (i + 1) for i in range(12)]
    instants = [start + FIVE * i for i in range(13)]
    power_roles = ("generator_power", "pv_available_power", "pcs_discharge_capability",
                   "critical_load_requested_power", "critical_load_delivered_power")
    for role in power_roles:
        rows = [r for r in got if r["role"] == role and r["quality"] == "GOOD" and r["source_time"] in ends]
        assert sorted(r["source_time"] for r in rows) == ends, (role, start)
        assert all(r["measurement"] == "INTERVAL_MEAN" and r["interval_end"] - r["interval_start"] == FIVE
                   for r in rows), role
    feeders = {r["asset_id"] for r in got if r["role"] == "feeder_demand"}
    assert len(feeders) == 3, feeders
    for asset in feeders:
        rows = [r for r in got if r["role"] == "feeder_demand" and r["asset_id"] == asset and r["quality"] == "GOOD"
                and r["source_time"] in ends]
        assert sorted(r["source_time"] for r in rows) == ends, (asset, start)
    for role in ("battery_soc", "generator_state"):
        rows = {r["source_time"] for r in got if r["role"] == role and r["quality"] == "GOOD"}
        assert set(instants[:12]) <= rows, (role, start)
    assert end in {r["source_time"] for r in got if r["role"] == "battery_soc" and r["quality"] == "GOOD"}


@pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")
@pytest.mark.parametrize("version", sorted(MANIFESTS))
def test_d_verification_window_replays_the_complete_path(tmp_path, version: str) -> None:
    import pg_harness
    import test_s1_bindings_postgres as pgb
    import test_s6_verification_publication as pub
    from sqlalchemy import create_engine, text
    from test_s6_verification_plan_postgres import verifying

    from assetops_backend.sites.adapters.postgres_foundation_store import PostgresFoundationStore

    MANIFEST = MANIFESTS[version]
    expected = MANIFEST["expected"]
    act, win = MANIFEST["action"], MANIFEST["windows"]
    b0, l0 = _at(win["baseline_start"]), _at(win["later_start"])
    pg_harness.fresh_database()
    engine = create_engine(URL)
    store = PostgresFoundationStore(URL)
    runner = h = None
    try:
        result, _ = pgb.converted(store)
        pub.configure(store, result)
        with engine.begin() as c:  # stand in for credential provisioning (as the S2 ledger tests do)
            c.execute(text("UPDATE gateway SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})
            c.execute(text("UPDATE source SET disabled_at = NULL WHERE site_id = :s"), {"s": result.site.id})

        # 1. Baseline run on the old Foundation -> S2 -> S3 -> S4.
        spec = MANIFEST["runs"]["baseline"]
        base_run, base_view = _draft(store, spec, MANIFEST)
        assert base_view.binding_set.role_set == MANIFEST["role_set"]
        published = {"baseline": _publish_and_accept(tmp_path / "baseline", base_run, spec["sequence_epoch"],
                                                     _at(spec["received_at"]))}
        runner = LabRunner(store, engine, result, _at(spec["received_at"]) + timedelta(minutes=5))
        runner.step({"do": "assess"})
        runner.step({"do": "match"})
        _slots_all_present(engine, result.site.id, b0)

        # 2. S6-01: recommendation -> accept -> apply (reserve old -> new, effective_from).
        h = verifying(runner)
        h.clock.at = _at(act["accept_at"])
        findings = h.findings()
        finding = findings[act["finding_anchor_day"]]
        proposal = h.recommendation(finding).json()["proposal"]
        assert (proposal["old_value"], proposal["proposed_value"]) == (act["reserve_old"], act["reserve_new"])
        made = h.accept(finding, proposal, idempotency_key="replay-accept-0001")
        assert made.status_code == 201, made.text
        action_id = made.json()["action"]["action_id"]
        h.clock.at = _at(act["apply_at"])
        current = h.client.get(f"/api/sites/KOBO-001/actions/{action_id}").json()["application_basis"][
            "current_foundation_revision_id"]
        applied = h.client.post(f"/api/sites/KOBO-001/actions/{action_id}/apply", json={
            "expected_foundation_revision_id": current, "value": act["reserve_new"],
            "effective_from": act["effective_from"], "idempotency_key": "replay-apply-0001"})
        assert applied.status_code == 201, applied.text
        runner.now = max(runner.now, h.clock.at)
        runner.step({"do": "assess"})
        runner.step({"do": "match"})

        # 3. S6-02a: freeze the plan (VERIFY) before any later-window report exists.
        h.clock.at = max(_at(MANIFEST["plan"]["freeze_at"]), runner.now + timedelta(minutes=1))
        base = f"/api/sites/KOBO-001/actions/{action_id}/verification"
        frozen = h.client.post(f"{base}/plans", json={"baseline_start": win["baseline_start"],
                                                      "later_start": win["later_start"],
                                                      "idempotency_key": "replay-freeze-0001"})
        assert frozen.status_code == 201, frozen.text
        plan = frozen.json()["plan"]
        assert "no causal or savings claim" in frozen.json()["label"] and "policy trial" in frozen.json()["label"]

        # 4. Later run, separate, on the new Foundation -> S2 -> S3 -> S4.
        spec = MANIFEST["runs"]["later"]
        later_run, later_view = _draft(store, spec, MANIFEST)
        assert str(later_view.revision.id) == plan["new_foundation_revision_id"]
        assert later_run.run_id != base_run.run_id
        published["later"] = _publish_and_accept(tmp_path / "later", later_run, spec["sequence_epoch"],
                                                 _at(spec["received_at"]))
        runner.now = max(runner.now, _at(spec["received_at"]) + timedelta(minutes=5))
        runner.step({"do": "assess"})
        runner.step({"do": "match"})
        _slots_all_present(engine, result.site.id, l0)

        # 5. Bind the later selection, request evaluation; the evaluator settles the outcome.
        h.clock.at = max(_at(MANIFEST["evaluate_at"]), runner.now + timedelta(minutes=1))
        bound = h.client.post(f"{base}/plans/{plan['plan_id']}/later-selection",
                              json={"idempotency_key": "replay-bind-0001"})
        assert bound.status_code == 201, bound.text
        made = h.client.post(f"{base}/evaluations", json={"idempotency_key": "replay-eval-0001"})
        assert made.status_code == 201, made.text
        outcome = made.json()["outcome"]
        read = h.client.get(f"{base}/outcome").json()
        evidence = h.client.get(f"{base}/evidence").json()
        kinds = [e["kind"] for e in h.client.get(f"/api/sites/KOBO-001/actions/{action_id}/events").json()["events"]]
        _dump(tmp_path, plan=plan, outcome=outcome, read=read, evidence=evidence, kinds=kinds, published=published)

        assert "pending" not in expected, "fill the expected block from ASSETOPS_REPLAY_DUMP"
        # --- the expected block --------------------------------------------------------------------------
        assert published["baseline"] == expected["published"]["baseline"]
        assert published["later"] == expected["published"]["later"]
        assert plan["baseline_candidate_seconds"] == expected["plan"]["baseline_candidate_seconds"]
        assert plan["old_foundation_revision_id"] != plan["new_foundation_revision_id"]
        assert outcome["outcome"] == expected["outcome"]["outcome"], outcome["reasons"]
        assert outcome["reasons"] == expected["outcome"]["reasons"]
        windows = evidence["windows"]
        for name in ("baseline", "later"):
            w = windows[name]
            assert len(w["evidence_ids"]) == expected["window_evidence_ids"], name
            assert len(outcome["basis"]["source_resolutions"][name]["publication_ids"]) ==                 expected["window_publication_ids"], name
            assert w["complete"] is expected["windows"][name]["complete"] is True, (name, w.get("problems"))
            assert [s["complete"] for s in w["slots"]] == [True] * 12, name
            for key in ("feeder_demand_kwh", "pv_available_kwh", "unserved_critical_kwh", "below_reserve_seconds",
                        "initial_soc", "terminal_soc"):
                assert w[key] == expected["windows"][name][key], (name, key, w[key])
        sources = outcome["basis"]["source_resolutions"]
        digests = []
        for name in ("baseline", "later"):
            assert sources[name]["state"] == expected["source"]["per_window_class"] == "REGISTERED_SIMULATION"
            assert len(sources[name]["runs"]) == 1
            digests.append(sources[name]["runs"][0]["run_identity_sha256"])
        assert digests[0] != digests[1]
        metrics = {(m["metric_key"], m["window_name"]): m for m in read["metrics"]}
        for name, state in expected["metrics"].items():
            key, window = name.split("@")
            assert metrics[(key, window)]["state"] == state, (key, window, metrics[(key, window)])
        for window, seconds in (expected.get("candidate_seconds") or {}).items():
            assert metrics[("candidate_avoidable_seconds", window.upper())]["value_text"] == str(seconds), window
        assert evidence["comparability"]["state"] == ("PASS" if expected["metrics"][
            "initial_soc_band@COMPARISON"] == "PASS" else "FAIL")
        assert ("RESOLVED" in kinds) is expected["outcome"]["resolved_appended"], kinds
        assert ("RESOLVED" in kinds) is (outcome["outcome"] == "VERIFIED")
        assert read["current_state"]["state"] == expected["outcome"]["current_state"]
        # Why the shipped model settles where it does: the generator's ON span per run (S3's own segments).
        assert _generator_running(engine) == expected["generator_running"]
        # The API labels: a simulated policy trial, never a savings claim; RESOLVED can be withdrawn.
        for label in (frozen.json()["label"], evidence["label"], read.get("label") or evidence["label"]):
            assert "policy trial" in label and "no causal or savings claim" in label, label
            assert "Simulated" in label and "RESOLVED can be withdrawn" in label, label
        statement = read["current_state"]["statement"]
        assert "simulated" in statement and "no causal or savings claim" in statement, statement
        assert metrics[("source_provenance", "COMPARISON")]["value_text"] == expected["source"]["per_window_class"]
    finally:
        if h is not None:
            h.close()
        if runner is not None:
            pg_harness.dispose(runner.findings)
        pg_harness.dispose(store)
        engine.dispose()


def _dump(tmp_path: Path, **parts) -> None:
    """The replay's observations, beside the test's tmp dir, for reading a mismatch against the manifest."""
    out = os.environ.get("ASSETOPS_REPLAY_DUMP")
    if out:
        Path(out).write_text(json.dumps(parts, indent=1, sort_keys=True, default=str), encoding="utf-8")


def _generator_running(engine) -> dict[str, list[str]]:
    """UTC day -> [first, last] instant of the S3 dispatch segments (the generator ON span each run produced)."""
    from sqlalchemy import text

    spans: dict[str, list[datetime]] = {}
    with engine.connect() as c:
        for (result,) in c.execute(text("SELECT result FROM assessment_revision")):
            for seg in (result or {}).get("segments") or []:
                lo, hi = _at(seg["start"]), _at(seg["end"])
                day = spans.setdefault(lo.date().isoformat(), [lo, hi])
                day[0], day[1] = min(day[0], lo), max(day[1], hi)
    return {d: [v.isoformat() for v in span] for d, span in sorted(spans.items())}
