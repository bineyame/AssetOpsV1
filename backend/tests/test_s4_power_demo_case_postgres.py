"""S4-02b phase 2a: the authored power-mean demonstration case (`s4-power-demo-cases-v1`).

Owner ruling `.agent/owner-S4-02b-money-demo-2026-10-14.md`. The spec is delivered through the same in-process
Batch V2 path as the S4 Finding cases (the walkthrough producer `tools/s402b_power_cases.py` posts the same
envelopes over TLS with the registered gateway credential), assessed, matched, and recomputed by the durable
worker: a positive bounded amount at price v1 and a second consequence revision after the v4 correction.
Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
BACKEND = Path(__file__).resolve().parents[1]
POWER_SPEC = json.loads((BACKEND / "conversions" / "s4-power-demo-cases-v1.json").read_text(encoding="utf-8"))

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    """Each case builds several short-lived stores (CaseRunner, workers); collect their engines promptly so a
    full-suite run does not exhaust the server's connection slots."""
    yield
    import gc

    gc.collect()

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import SourceEnvelopeV3, _z, canonical_envelope_v3_text, v3_message_id
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_finding_store_postgres import SPEC, CaseRunner, block_rows

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from money_gate_stub import ELIGIBLE
    from assetops_backend.financials.consequence_read import ConsequenceReadService
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def power_envelopes(runner, step: dict, rules: dict) -> list[tuple[str, str]]:
    """The spec's back-to-back INTERVAL_MEAN generator-power envelopes, in source-time order."""
    kit, epoch = runner.kit, step["epoch"]
    device, signal = rules["device"], rules["signal"]
    b = kit.binding(device, signal)
    out = []
    for block in step["means"]:
        end = instant(block["first_end"])
        while end <= instant(block["last_end"]):
            key = (b["source_id"], epoch)
            runner.seq[key] = runner.seq.get(key, 0) + 1
            seq = runner.seq[key]
            e = SourceEnvelopeV3(
                message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                         source_id=b["source_id"], sequence_epoch=epoch, sequence=seq),
                sequence_epoch=epoch, sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                source_id=b["source_id"], device_id=device, signal_id=signal,
                binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
                source_time=_z(end), published_at=_z(end),
                interval_start=_z(end - timedelta(minutes=rules["mean_minutes"])), interval_end=_z(end),
                family="MEASUREMENT", measurement=rules["measurement"], value=block["kw"], unit=b["source_unit"],
                quality=rules["quality"], unavailable_reason=None)
            out.append((device, canonical_envelope_v3_text(e)))
            end += timedelta(minutes=rules["mean_minutes"])
    return out


def deliver(runner, step: dict) -> None:
    context = block_rows(step["context"], SPEC["reading_rules"])
    now, _ = runner.seal([(row, False) for row in sorted(context, key=lambda x: x[2])], step["epoch"] + "-context")
    runner.submit(power_envelopes(runner, step, POWER_SPEC["power_rules"]) + now,
                  runner.tick(step["decided"]))


def test_the_spec_is_a_new_labelled_version_and_leaves_the_s4_cases_spec_alone() -> None:
    assert POWER_SPEC["label"] == "s4-power-demo-cases-v1" and POWER_SPEC["base_spec"] == SPEC["label"]
    assert "AUTHORED" in POWER_SPEC["status"] and "DEMONSTRATION" in POWER_SPEC["status"]
    days = {c["day"] for c in SPEC["cases"]} | {"2026-10-02"}  # 10-02 is the F01-gateway day
    assert not days & {c["day"] for c in POWER_SPEC["cases"]}


def test_the_power_case_yields_a_positive_amount_then_a_second_revision_after_v4(store, engine, capsys) -> None:  # noqa: F811
    runner = CaseRunner(store, engine)
    (case,) = POWER_SPEC["cases"]
    for step in case["steps"]:
        if step["do"] == "deliver_power":
            deliver(runner, step)
        elif step["do"] == "assess":
            runner.step(step)
        elif step["do"] == "match":
            runner.step(step)
    with engine.connect() as c:
        (rev,) = [dict(r._mapping) for r in c.execute(text(
            "SELECT r.id, r.finding_id, r.episode_start, r.episode_end, r.lifecycle, r.transition FROM finding_revision r "
            "WHERE r.site_id = :s AND r.episode_start >= :d AND r.episode_start < :d + interval '1 day'"),
            {"s": runner.site, "d": instant(case["day"] + "T00:00:00Z")})]
    (expect,) = case["steps"][-1]["expect"]
    assert (rev["lifecycle"], rev["transition"]) == (expect["lifecycle"], expect["transition"])
    assert [rev["episode_start"], rev["episode_end"]] == [instant(x) for x in expect["episode"]]

    prices, cstore = PostgresAssumptionStore(URL), PostgresConsequenceStore(URL)
    try:
        worker = ConsequenceRecomputeWorker(cstore, prices, CONSEQUENCE_UNAVAILABLE)
        reads = ConsequenceReadService(cstore, prices, eligibility=ELIGIBLE)
        want = POWER_SPEC["expected_consequence"]
        run_fixture(prices, capsys, "v1", "v2", "v3")
        assert all(o.succeeded for o in worker.run_pending(runner.tenant, runner.site))

        def read() -> dict:
            return reads.read(runner.tenant, runner.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True,
                              source_open=True)

        first = read()
        c = first["consequence"]
        assert (first["currentness"]["state"], c["state"], c["revision_no"]) == ("CURRENT", "PRICED", 1)
        assert len(c["lineage"]["power_intervals"]) == want["counted_intervals"]
        assert Decimal(c["quantity"]["high"]) == Decimal(want["quantity_high_l"])
        v1 = want["amount_high"]["v1-v3"]
        assert Decimal(c["amount"]["high"]) == Decimal(v1["amount"]) and c["display"]["amount_high"] == v1["display"]
        run_fixture(prices, capsys, "v4")
        assert read()["currentness"]["state"] == "STALE"
        worker.run_pending(runner.tenant, runner.site)
        second = read()["consequence"]
        v4 = want["amount_high"]["v4"]
        assert (second["revision_no"], second["prior_consequence_revision_id"]) == (2, c["id"])
        assert Decimal(second["amount"]["high"]) == Decimal(v4["amount"])
        assert second["display"]["amount_high"] == v4["display"]
        assert second["digests"]["technical_input_sha256"] == c["digests"]["technical_input_sha256"]
    finally:
        prices.dispose()
        cstore.dispose()


# ---- S4-05b phase 1: register before upload, then exact source provenance on the reads ----

if URL:
    from test_s2_evidence_ledger_postgres import Kit, converted_enabled
    from test_s2_registered_basis import request as run_request
    from test_s2_registered_basis_postgres import service as run_setup
    from test_s405_publication_postgres import P02, accepted_ids, submit
    from test_s405_resolver_postgres import is_power, publishing_submit, stage

    from assetops_backend.evidence.composition import build_source_provenance
    from assetops_backend.runs.adapters.yaml_run_store import YamlRunStore
    from assetops_backend.runs.registered_release import publisher_for
    from assetops_backend.runs.source_publication import run_identity_sha256

P01_FIXTURE = (POWER_SPEC["schema"]["id"], str(POWER_SPEC["schema"]["version"]))


def p01(store, engine, capsys, monkeypatch, policy):  # noqa: F811
    """Run the authored P01 case with `policy(device, texts)` deciding each exact batch's pre-upload publication,
    recompute its consequence at prices v1-v3 and read it with the production provenance resolver."""
    if policy is not None:
        monkeypatch.setattr(CaseRunner, "submit", publishing_submit(policy))
    runner = CaseRunner(store, engine)
    (case,) = POWER_SPEC["cases"]
    for step in case["steps"]:
        if step["do"] == "deliver_power":
            deliver(runner, step)
        else:
            runner.step(step)
    with engine.connect() as c:
        (rev,) = [dict(r._mapping) for r in c.execute(text(
            "SELECT id, finding_id FROM finding_revision WHERE site_id = :s AND episode_start >= :d "
            "AND episode_start < :d + interval '1 day'"), {"s": runner.site, "d": instant(case["day"] + "T00:00:00Z")})]
    prices, cstore = PostgresAssumptionStore(URL), PostgresConsequenceStore(URL)
    worker = ConsequenceRecomputeWorker(cstore, prices, CONSEQUENCE_UNAVAILABLE)
    run_fixture(prices, capsys, "v1", "v2", "v3")
    assert all(o.succeeded for o in worker.run_pending(runner.tenant, runner.site))
    reads = ConsequenceReadService(cstore, prices, eligibility=ELIGIBLE, provenance=build_source_provenance(URL))
    body = reads.read(runner.tenant, runner.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True,
                      source_open=True)
    return runner, body, (prices, cstore)


def published(engine, ids) -> set[str]:
    """The accepted IDs whose batch carries a pre-admission publication link."""
    with engine.connect() as c:
        return {str(x) for (x,) in c.execute(text(
            "SELECT e.id FROM accepted_evidence e JOIN batch_publication_link l ON l.batch_id = e.batch_id "
            "WHERE e.id = ANY(CAST(:ids AS uuid[]))"), {"ids": list(ids)})}


def test_s405b_fresh_p01_publication_binds_every_cited_and_power_id(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    runner, body, stores = p01(store, engine, capsys, monkeypatch, lambda device, texts: P01_FIXTURE)
    try:
        assert body["currentness"]["state"] == "CURRENT" and body["consequence"]["state"] == "PRICED"
        finding, union = body["source_provenance"]["finding_revision"], body["source_provenance"]["consequence_revision"]
        assert finding["finding_revision_id"] == str(body["consequence"]["finding_revision_id"])
        assert union["consequence_revision_id"] == body["consequence"]["id"]
        cited, power = finding["cited_accepted_evidence_ids"], union["power_accepted_evidence_ids"]
        assert cited and power and set(power) == set(body["consequence"]["lineage"]["evidence_ids"])
        assert published(engine, cited) == set(cited) and published(engine, power) == set(power)
        for block in (finding, union):
            assert block["state"] == "AUTHORED_DEMONSTRATION" and block["reasons"] == []
            assert block["fixtures"] == [{"fixture_id": P01_FIXTURE[0], "fixture_version": P01_FIXTURE[1]}]
            assert {e["publication_id"] for e in block["evidence"]} == set(block["publication_ids"])
            assert all(e["status"] == "BOUND" and e["batch_id"] for e in block["evidence"])
        assert len(union["publication_ids"]) >= 2  # the power batch and the authored context batches
        assert body["consequence"]["source_provenance"] == union
    finally:
        for s in stores:
            s.dispose()


def test_source_state_compatibility_all_w1_consumers(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    """W3-01 Run 3 q3 (W1 rows of the dry-read map): every W1 reader keeps its resolver fields and gains the public
    keys through the composition injection, with independent Finding/consequence digests over their own selected
    sets; an unwired or missing revision keeps the fail-closed `unresolved` shape with no fabricated public keys."""
    from assetops_backend.analytics.composition import build_finding_read_service
    from assetops_backend.evidence.composition import build_public_provenance
    from assetops_backend.evidence.provenance_read import consequence_provenance, finding_provenance
    from assetops_backend.evidence.public_provenance import basis_sha256
    from assetops_backend.financials import consequence_history as ch
    from assetops_backend.financials.composition import build_consequence_history_service

    runner, legacy, stores = p01(store, engine, capsys, monkeypatch, lambda device, texts: P01_FIXTURE)
    prices, cstore = stores
    public = build_public_provenance(URL)
    findings = build_finding_read_service(URL)
    history_service = build_consequence_history_service(URL)
    try:
        t, s = runner.tenant, runner.site
        fr_id, c_id = legacy["consequence"]["finding_revision_id"], legacy["consequence"]["id"]
        with engine.connect() as c:
            finding_id = c.execute(text("SELECT finding_id FROM finding_revision WHERE id = :r"), {"r": fr_id}).scalar_one()
        reads = ConsequenceReadService(cstore, prices, eligibility=ELIGIBLE, provenance=public)
        body = reads.read(t, s, finding_id, fr_id, finding_revision_is_latest=True, source_open=True)
        finding, union = body["source_provenance"]["finding_revision"], body["source_provenance"]["consequence_revision"]
        old_finding = legacy["source_provenance"]["finding_revision"]
        old_union = legacy["source_provenance"]["consequence_revision"]
        public_keys = {"classification", "state", "source_ids", "evidence_ids", "basis_sha256", "reasons", "detail"}
        for new, old in ((finding, old_finding), (union, old_union)):
            assert set(old) <= set(new) and public_keys <= set(new)
            assert {k: new[k] for k in old if k != "reasons"} == {k: old[k] for k in old if k != "reasons"}
            assert new["classification"] == new["state"] == "AUTHORED_DEMONSTRATION"
            assert new["evidence_ids"] == sorted(old["accepted_evidence_ids"]) and new["reasons"] == []
            assert new["detail"]["accepted_evidence_ids"] == old["accepted_evidence_ids"]
        assert finding["basis_sha256"] == basis_sha256(t, s, [fr_id], finding["evidence_ids"])
        assert union["basis_sha256"] == basis_sha256(t, s, [c_id, fr_id], union["evidence_ids"])
        assert finding["basis_sha256"] != union["basis_sha256"]
        assert union["finding_revision_state"] == "AUTHORED_DEMONSTRATION"
        assert body["consequence"]["source_provenance"] == union
        # The W1 Finding reader (`FindingReadService.source_provenance`) returns the same Finding block.
        assert findings.source_provenance(t, s, fr_id) == finding
        # Consequence history rows carry the consequence block of each revision through the same composition.
        req = ch.parse_request(None, None, "25")
        rows = history_service.read(t, s, "KOBO-001", req, source_open=True, source_reason=None,
                                    access_basis="dev")["rows"]
        mine = [r for r in rows if str(r["consequence_revision_id"]) == str(c_id)]
        assert mine and mine[0]["source_provenance"]["basis_sha256"] == union["basis_sha256"]
        # Fallbacks: unwired and missing revisions keep the old fail-closed keys; no public key is invented.
        for fallback in (finding_provenance(None, t, s, fr_id), consequence_provenance(None, t, s, fr_id, c_id),
                         finding_provenance(public, t, s, uuid4())):
            assert fallback["state"] == "UNKNOWN" and fallback["reasons"][0]["code"].startswith("PROVENANCE_")
            assert not ({"classification", "source_ids", "evidence_ids", "basis_sha256", "detail"} & set(fallback))
    finally:
        if hasattr(history_service, "dispose"):
            history_service.dispose()
        for st in stores:
            st.dispose()


def test_s405b_an_ordinary_contextual_id_makes_the_finding_and_union_mixed(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    plain_device: list[str] = []

    def policy(device, texts):
        """Publish every batch except one ordinary context device's (an unbound contextual reading)."""
        if not is_power(texts) and (not plain_device or plain_device[0] == device):
            plain_device[:] = [device]
            return None
        return P01_FIXTURE

    runner, body, stores = p01(store, engine, capsys, monkeypatch, policy)
    try:
        finding, union = body["source_provenance"]["finding_revision"], body["source_provenance"]["consequence_revision"]
        cited = finding["cited_accepted_evidence_ids"]
        plain = sorted(set(cited) - published(engine, cited))
        assert plain, "the P01 Finding cites ordinary context readings"
        assert finding["state"] == "MIXED" and [r["code"] for r in finding["reasons"]] == ["BOUND_AND_UNBOUND"]
        assert finding["reasons"][0]["accepted_evidence_ids"] == plain == finding["problematic_accepted_evidence_ids"]
        assert union["state"] == "MIXED" and union["finding_revision_state"] == "MIXED"
        assert published(engine, union["power_accepted_evidence_ids"]) == set(union["power_accepted_evidence_ids"])
        assert union["problematic_accepted_evidence_ids"] == plain  # the bound power IDs are not the problem
    finally:
        for s in stores:
            s.dispose()


def test_s405b_same_day_unpublished_p01_from_an_old_producer_is_unknown(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    runner, body, stores = p01(store, engine, capsys, monkeypatch, None)  # the pre-S4-05b producer: no publication
    try:
        finding, union = body["source_provenance"]["finding_revision"], body["source_provenance"]["consequence_revision"]
        assert published(engine, union["accepted_evidence_ids"]) == set()
        for block in (finding, union):
            assert block["state"] == "UNKNOWN" and block["reasons"][0]["code"] == "NO_POSITIVE_BINDING"
            assert block["publication_ids"] == [] and block["source_classes"] == []
    finally:
        for s in stores:
            s.dispose()


def test_s405b_fresh_p02_publication_is_authored_beside_its_eligible_current_amount(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    from test_lr01_money_eligibility_postgres import Walk, amount

    monkeypatch.setattr(CaseRunner, "submit", publishing_submit(lambda device, texts: P02))
    w = Walk(store, engine, capsys, on_time=True)
    w.reads._provenance = build_source_provenance(URL)
    try:
        w.attest()
        w.deliver_first()
        run_fixture(w.prices, capsys, "v1")
        w.settle()
        late = w.deliver_late()
        w.settle()
        body = w.read(w.latest())
        assert body["money_eligibility"]["state"] == "ELIGIBLE" and amount(body) == Decimal("15.8125")
        union = body["source_provenance"]["consequence_revision"]
        assert union["state"] == "AUTHORED_DEMONSTRATION" and union["fixtures"] == [
            {"fixture_id": P02[0], "fixture_version": P02[1]}]
        assert set(late) <= set(union["power_accepted_evidence_ids"])
        assert published(engine, union["accepted_evidence_ids"]) == set(union["accepted_evidence_ids"])
        assert len(union["publication_ids"]) >= 3  # first power, context and the late batch
    finally:
        w.close()


def test_s405b_the_lab_release_publisher_registers_an_ordinary_run_before_upload(store, engine, tmp_path) -> None:  # noqa: F811
    _, outcome = converted_enabled(store, engine)
    kit = Kit(engine, outcome.published.changed.id)
    run = run_setup(store, YamlRunStore(tmp_path / "runs")).create_draft_run(run_request())
    bodies = [kit.seal(kit.pv(2)), kit.seal(kit.pv(2, first=3))]
    pubs = publisher_for(URL).publish(run, stage(run, bodies))  # the composed Lab release step, before upload
    ids = [str(i) for body in bodies for i in accepted_ids(submit(kit, body).receipt)]
    resolver = build_source_provenance(URL)
    r = resolver.resolve(kit.principal.tenant_id, kit.principal.site_id, ids)
    assert r["state"] == "REGISTERED_SIMULATION" and r["publication_ids"] == sorted(pubs)
    assert r["runs"] == [{"run_id": run.run_id, "run_identity_sha256": run_identity_sha256(run)}]
    assert publisher_for(URL).publish(run, stage(run, [])) == ()  # nothing left STAGED: nothing to publish
    plain = [str(i) for i in accepted_ids(submit(kit, kit.seal(kit.pv(1, first=9))).receipt)]
    same_day = resolver.resolve(kit.principal.tenant_id, kit.principal.site_id, ids + plain)
    assert same_day["state"] == "MIXED" and same_day["reasons"][0]["accepted_evidence_ids"] == plain
