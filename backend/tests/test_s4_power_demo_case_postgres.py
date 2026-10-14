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

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
BACKEND = Path(__file__).resolve().parents[1]
POWER_SPEC = json.loads((BACKEND / "conversions" / "s4-power-demo-cases-v1.json").read_text(encoding="utf-8"))

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import text
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import SourceEnvelopeV3, _z, canonical_envelope_v3_text, v3_message_id
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_finding_store_postgres import SPEC, CaseRunner, block_rows

    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
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
        reads = ConsequenceReadService(cstore, prices)
        want = POWER_SPEC["expected_consequence"]
        run_fixture(prices, capsys, "v1", "v2", "v3")
        assert all(o.succeeded for o in worker.run_pending(runner.tenant, runner.site))

        def read() -> dict:
            return reads.read(runner.tenant, runner.site, rev["finding_id"], rev["id"], finding_revision_is_latest=True)

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
