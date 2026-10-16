"""LR-01 phase 2: the outcome table on the authored late-power fixture, end to end in Postgres.

Packet `tasks/LR-01-late-reading-series-and-money-limit.md` (outcome table), decision
`D-2026-10-15-lr01-source-time-cohort` and `.agent/architect-LR-01-answers.md` Q4. The fixture
`backend/conversions/s4-power-late-demo-cases-v1.json` is delivered through the in-process Batch V2 path,
assessed (dispatch-3.2), matched (finding-episode-3) and recomputed (fuel-cost-1) by the durable workers; the
consequence read is built with the production `MoneyEligibility` gate over the same stores.

Rows: admission-sequenced run 1 without attestation (pending -> withheld at 7.5625 with SERIES_LIMIT) ->
labelled simulated attestation (pending, old IDs kept) -> reassessed (eligible at 15.8125, new IDs, the 7.5625
revision and IDs historical) -> revoked (pending -> withheld again); and the on-time-sequenced attested upload
(eligible at 15.8125). Requires ASSETOPS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
BACKEND = Path(__file__).resolve().parents[1]
LATE = json.loads((BACKEND / "conversions" / "s4-power-late-demo-cases-v1.json").read_text(encoding="utf-8"))
(CASE,) = LATE["cases"]
EPOCH = CASE["steps"][0]["epoch"]
DAY0 = datetime(2026, 10, 24, tzinfo=timezone.utc)

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")


@pytest.fixture(autouse=True)
def _release_connections():
    yield
    import gc

    gc.collect()


if URL:
    from sqlalchemy import text
    from money_gate_stub import AUTHORED
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import SourceEnvelopeV3, _z, canonical_envelope_v3_text, v3_message_id
    from test_s4_assumptions_postgres import run_fixture
    from test_s4_finding_store_postgres import SPEC, CaseRunner, block_rows

    from assetops_backend.analytics.adapters.postgres_assessment_store import PostgresAssessmentStore
    from assetops_backend.analytics.clock_attestation import SYSTEM_ATTESTER, AttestationChange
    from assetops_backend.analytics.dispatch_read import DispatchReadService
    from assetops_backend.finding_api import bridge_consequence
    from assetops_backend.financials.adapters.postgres_assumption_store import PostgresAssumptionStore
    from assetops_backend.financials.adapters.postgres_consequence_store import PostgresConsequenceStore
    from assetops_backend.financials.composition import CONSEQUENCE_UNAVAILABLE
    from assetops_backend.financials.consequence_read import ConsequenceReadService
    from assetops_backend.financials.money_eligibility import MoneyEligibility
    from assetops_backend.financials.recompute import ConsequenceRecomputeWorker


def instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def ends(blocks: list[dict]) -> list[datetime]:
    out = []
    for block in blocks:
        end = instant(block["first_end"])
        while end <= instant(block["last_end"]):
            out.append((end, block["kw"]))
            end += timedelta(minutes=LATE["power_rules"]["mean_minutes"])
    return out


class Walk:
    """One private fixture Site walked through the late-power case, with a gated consequence read."""

    def __init__(self, store, engine, capsys, *, on_time: bool) -> None:
        self.r = CaseRunner(store, engine)
        self.engine, self.capsys = engine, capsys
        rules = LATE["power_rules"]
        self.binding = self.r.kit.binding(rules["device"], rules["signal"])
        first, late = ends(CASE["steps"][0]["means"]), ends(CASE["late"]["means"])
        # On-time-sequenced: numbered when taken (source order, a gap at the withheld mean). Admission-sequenced
        # (run 1, the project's own gateway): the late mean gets the next sequence on intake.
        order = sorted(first + late) if on_time else first + late
        self.seq = {when: i + 1 for i, (when, _) in enumerate(order)}
        self.first, self.late = first, late
        self.prices, self.cstore = PostgresAssumptionStore(URL), PostgresConsequenceStore(URL)
        self.assessments = PostgresAssessmentStore(URL)
        # S4-05b phase 2: these tests exercise the LR-01 gate; the stored source gate is held positive here and
        # proved on real publications in the production-composition test below.
        self.reads = ConsequenceReadService(self.cstore, self.prices, eligibility=MoneyEligibility(
            DispatchReadService(self.assessments), self.r.findings), provenance=AUTHORED)
        self.worker = ConsequenceRecomputeWorker(self.cstore, self.prices, CONSEQUENCE_UNAVAILABLE)

    def close(self) -> None:
        self.prices.dispose()
        self.cstore.dispose()

    def envelopes(self, means) -> list[tuple[str, str]]:
        kit, b, rules = self.r.kit, self.binding, LATE["power_rules"]
        out = []
        for end, kw in means:
            seq = self.seq[end]
            e = SourceEnvelopeV3(
                message_id=v3_message_id(site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                                         source_id=b["source_id"], sequence_epoch=EPOCH, sequence=seq),
                sequence_epoch=EPOCH, sequence=seq, site_id=kit.doc["site"]["site_id"], gateway_id=b["gateway_id"],
                source_id=b["source_id"], device_id=rules["device"], signal_id=rules["signal"],
                binding_set_id=kit.doc["mapping"]["binding_set_id"], binding_version=kit.doc["mapping"]["version"],
                source_time=_z(end), published_at=_z(end),
                interval_start=_z(end - timedelta(minutes=rules["mean_minutes"])), interval_end=_z(end),
                family="MEASUREMENT", measurement=rules["measurement"], value=kw, unit=b["source_unit"],
                quality=rules["quality"], unavailable_reason=None)
            out.append((rules["device"], canonical_envelope_v3_text(e)))
        return out

    def deliver_first(self) -> None:
        step = CASE["steps"][0]
        context = block_rows(step["context"], SPEC["reading_rules"])
        now, _ = self.r.seal([(row, False) for row in sorted(context, key=lambda x: x[2])], EPOCH + "-context")
        self.r.submit(self.envelopes(self.first) + now, self.r.tick(step["decided"]))

    def deliver_late(self) -> list[str]:
        self.r.submit(self.envelopes(self.late), self.r.tick(CASE["late"]["decided"]))
        with self.engine.connect() as c:
            return [str(x) for (x,) in c.execute(text(
                "SELECT id FROM accepted_evidence WHERE site_id = :s AND interval_end = :e"),
                {"s": self.r.site, "e": self.late[0][0]})]

    def settle(self) -> None:
        self.r.step({"do": "assess"})
        self.r.match()
        assert all(o.succeeded for o in self.worker.run_pending(self.r.tenant, self.r.site))

    def attest(self, kind="RECORDED", key="lr01", attestation=None, expected=None) -> dict:
        record = kind in ("RECORDED", "REPLACED")
        change = AttestationChange(
            event_kind=kind, source_id=UUID(str(self.binding["source_id"])), sequence_epoch=EPOCH,
            idempotency_key=key, channel="SYSTEM_CLI", authority="lab-simulated-clock" if record else None,
            label="SIMULATED demonstration clock (LR-01)" if record else None,
            max_utc_error=timedelta(seconds=30) if record else None, valid_from=DAY0 if record else None,
            valid_to=DAY0 + timedelta(days=1) if record else None, attestation_id=attestation,
            expected_version=expected, reason=None if record else "clock proof withdrawn")
        return self.assessments.record_clock_attestation(self.r.tenant, self.r.site, change, SYSTEM_ATTESTER,
                                                         self.r.tick())

    def latest(self) -> dict:
        with self.engine.connect() as c:
            rows = [dict(r._mapping) for r in c.execute(text(
                "SELECT id, finding_id, revision_no, episode_start, episode_end, lifecycle, claim, matcher_version "
                "FROM finding_revision WHERE site_id = :s AND episode_start >= :d "
                "AND episode_start < :d + interval '1 day' ORDER BY revision_no"), {"s": self.r.site, "d": DAY0})]
        assert len({r["finding_id"] for r in rows}) == 1, rows
        return rows[-1]

    def read(self, rev: dict, latest: bool = True) -> dict:
        return self.reads.read(self.r.tenant, self.r.site, rev["finding_id"], rev["id"],
                               finding_revision_is_latest=latest, source_open=True)


def amount(body: dict) -> Decimal:
    return Decimal(body["consequence"]["amount"]["high"])


def assert_no_current_money(body: dict, state: str) -> None:
    assert body["money_eligibility"]["state"] == state, body["money_eligibility"]
    assert body["currentness"]["current_amount_shown"] is False
    assert body["consequence"] is None or body["consequence"]["presented_as_current"] is False
    bridge = bridge_consequence(body)
    assert bridge["amount"] is None and bridge["quantity"] is None


def test_run_one_withheld_then_attested_pending_then_eligible_then_revoked(store, engine, capsys) -> None:  # noqa: F811
    w = Walk(store, engine, capsys, on_time=False)
    try:
        w.deliver_first()
        run_fixture(w.prices, capsys, "v1")
        w.settle()
        r1 = w.latest()
        assert w.read(r1)["money_eligibility"]["state"] == "ELIGIBLE"

        late_ids = w.deliver_late()
        assert len(late_ids) == 1
        assert_no_current_money(w.read(r1), "PENDING_REASSESSMENT")  # late acceptance: S3 work pending
        w.r.step({"do": "assess"})
        assert_no_current_money(w.read(r1), "PENDING_REASSESSMENT")  # S4 match not yet run

        # Row 1: admission-sequenced run 1, settled -> SERIES_LIMIT revision, recorded 7.5625, withheld.
        w.r.match()
        assert all(o.succeeded for o in w.worker.run_pending(w.r.tenant, w.r.site))
        r2 = w.latest()
        claim = r2["claim"]
        assert (r2["revision_no"], r2["lifecycle"], r2["matcher_version"]) == (2, "SUPPORTED", "finding-episode-3")
        assert (r2["episode_start"], r2["episode_end"]) == (DAY0 + timedelta(hours=6, minutes=5),
                                                           DAY0 + timedelta(hours=7))
        assert claim["end_reason"] == "SERIES_LIMIT"
        assert any(late_ids[0] in x["evidence_ids"] and x["kind"] == "SEQUENCE_ORDER_INVERTED"
                   and x["clock"] == "NO_ATTESTATION" and x["relation"] == "CUTS_TAIL" and x["analytic_run_id"]
                   for x in claim["series_limits"])
        withheld = w.read(r2)
        assert (withheld["currentness"]["state"], withheld["consequence"]["state"]) == ("CURRENT", "PRICED")
        assert amount(withheld) == Decimal("7.5625")
        assert_no_current_money(withheld, "WITHHELD_GENERATOR_SERIES")
        recorded_id = withheld["consequence"]["id"]
        bridge = bridge_consequence(withheld)
        assert (bridge["state"], bridge["recorded_consequence_revision_id"]) == ("WITHHELD_GENERATOR_SERIES",
                                                                               recorded_id)
        old_runs = {x["analytic_run_id"] for x in withheld["consequence"]["lineage"]["assessments"]}

        # Row 2: a valid labelled simulated attestation -> pending; the 7.5625 revision and its IDs retained.
        out = w.attest()
        # Review L2: the requeued span covers the 07:00-07:05 interval mean.
        assert any(s.start <= DAY0 + timedelta(hours=7) and DAY0 + timedelta(hours=7, minutes=5) <= s.end
                   for s in out["requeued"]), out["requeued"]
        pending = w.read(r2)
        assert_no_current_money(pending, "PENDING_REASSESSMENT")
        assert pending["consequence"]["id"] == recorded_id and amount(pending) == Decimal("7.5625")

        # Row 3: reassessed under the attestation -> full episode, new 15.8125 head, eligible.
        w.settle()
        r3 = w.latest()
        assert r3["revision_no"] == 3 and r3["id"] != r2["id"]
        assert (r3["episode_start"], r3["episode_end"]) == (DAY0 + timedelta(hours=6, minutes=5),
                                                           DAY0 + timedelta(hours=8))
        assert r3["claim"]["end_reason"] != "SERIES_LIMIT" and r3["claim"]["series_limits"] == []
        eligible = w.read(r3)
        assert eligible["money_eligibility"]["state"] == "ELIGIBLE"
        assert eligible["consequence"]["presented_as_current"] is True
        assert eligible["currentness"]["current_amount_shown"] is True
        assert amount(eligible) == Decimal("15.8125") and eligible["consequence"]["id"] != recorded_id
        assert bridge_consequence(eligible)["amount"]["high"] == "15.82"
        new_runs = {x["analytic_run_id"] for x in eligible["consequence"]["lineage"]["assessments"]}
        assert new_runs.isdisjoint(old_runs)
        history = w.read(r2, latest=False)  # the 7.5625 revision stays, recorded only
        assert history["currentness"]["state"] == "HISTORICAL" and history["consequence"]["id"] == recorded_id
        assert amount(history) == Decimal("7.5625") and history["consequence"]["presented_as_current"] is False
        assert {x["analytic_run_id"] for x in history["consequence"]["lineage"]["assessments"]} == old_runs

        # Row 5: revoking the proof -> pending, then settled withheld again; 15.8125 kept as history.
        w.attest(kind="REVOKED", key="lr01-revoke", attestation=out["event"].attestation_id, expected=1)
        assert_no_current_money(w.read(r3), "PENDING_REASSESSMENT")
        w.settle()
        r4 = w.latest()
        assert r4["revision_no"] == 4 and r4["claim"]["end_reason"] == "SERIES_LIMIT"
        assert_no_current_money(w.read(r4), "WITHHELD_GENERATOR_SERIES")
        assert amount(w.read(r3, latest=False)) == Decimal("15.8125")
    finally:
        w.close()


def test_on_time_sequenced_attested_upload_is_eligible_at_15_8125(store, engine, capsys) -> None:  # noqa: F811
    w = Walk(store, engine, capsys, on_time=True)
    try:
        w.attest()
        w.deliver_first()
        run_fixture(w.prices, capsys, "v1")
        w.settle()
        w.deliver_late()
        assert_no_current_money(w.read(w.latest()), "PENDING_REASSESSMENT")
        w.settle()
        rev = w.latest()
        assert (rev["episode_start"], rev["episode_end"]) == (DAY0 + timedelta(hours=6, minutes=5),
                                                             DAY0 + timedelta(hours=8))
        assert rev["claim"]["series_limits"] == [] and rev["claim"]["end_reason"] != "SERIES_LIMIT"
        body = w.read(rev)
        assert body["money_eligibility"]["state"] == "ELIGIBLE"
        assert body["currentness"]["current_amount_shown"] is True and amount(body) == Decimal("15.8125")
        days = [x for x in body["money_eligibility"]["windows"] if x["episode_day"]]
        assert days and all(x["window_assessment_revision_id"] and x["analytic_run_id"] for x in days)
    finally:
        w.close()


def test_production_composition_wires_the_persisted_gate_and_a_failed_gate_shows_no_amount(store, engine, capsys, monkeypatch) -> None:  # noqa: F811
    """Architect ruling 5: `build_consequence_read_service` carries the persisted S3/S4 gate; an unreadable gate
    (or none) never shows a current amount. S4-05b phase 2: the batches are published (authored P02) before upload,
    so the composed stored source gate passes; an unwired resolver withholds the amount though LR is ELIGIBLE."""
    from assetops_backend.financials.composition import build_consequence_read_service
    from test_s405_publication_postgres import P02
    from test_s405_resolver_postgres import publishing_submit

    monkeypatch.setattr(CaseRunner, "submit", publishing_submit(lambda device, texts: P02))

    w = Walk(store, engine, capsys, on_time=True)
    prod = build_consequence_read_service(URL)
    try:
        w.attest()
        w.deliver_first()
        run_fixture(w.prices, capsys, "v1")
        w.settle()
        w.deliver_late()
        w.settle()
        rev = w.latest()

        def read(service):
            return service.read(w.r.tenant, w.r.site, rev["finding_id"], rev["id"],
                                finding_revision_is_latest=True, source_open=True)

        assert isinstance(prod._eligibility, MoneyEligibility)
        wired = read(prod)  # the production composition reads the same persisted lineage
        assert wired["money_eligibility"]["state"] == "ELIGIBLE"
        assert wired["currentness"]["current_amount_shown"] is True and amount(wired) == Decimal("15.8125")
        assert wired["currentness"]["source_gate"]["state"] == "AUTHORED_DEMONSTRATION"
        assert wired["currentness"]["withheld_reasons"] == []

        resolver, prod._provenance = prod._provenance, None  # LR ELIGIBLE + CURRENT PRICED, source unresolved
        unsourced = read(prod)
        assert unsourced["money_eligibility"]["state"] == "ELIGIBLE" and unsourced["currentness"]["state"] == "CURRENT"
        assert unsourced["consequence"]["state"] == "PRICED" and unsourced["consequence"]["presented_as_current"] is False
        assert unsourced["currentness"]["withheld_reasons"] == ["MIXED_OR_UNKNOWN_SOURCE"]
        held = bridge_consequence(unsourced)
        assert held["state"] == "MIXED_OR_UNKNOWN_SOURCE" and held["amount"] is None and held["quantity"] is None
        assert held["recorded_consequence_revision_id"] == unsourced["consequence"]["id"]
        prod._provenance = resolver

        class Broken:
            def for_finding(self, *a, **k):
                raise RuntimeError("gate storage unavailable")

        prod._eligibility = Broken()  # a failed gate read
        failed = read(prod)
        assert failed["money_eligibility"]["state"] == "PENDING_REASSESSMENT"
        assert "ELIGIBILITY_READ_FAILED" in json.dumps(failed["money_eligibility"])
        assert failed["currentness"]["current_amount_shown"] is False
        assert bridge_consequence(failed)["amount"] is None
        prod._eligibility = None  # an unwired service
        assert read(prod)["currentness"]["current_amount_shown"] is False
    finally:
        w.close()
        prod._store.dispose()
        prod._prices.dispose()
