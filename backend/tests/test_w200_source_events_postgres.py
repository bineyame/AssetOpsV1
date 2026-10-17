"""W2-00: V4 source events through Batch V2/S2 over real PostgreSQL.

Covers packet acceptance 1 (ordinal refusals, tenant refusal, no dispatch job for v4), 2 (replay, event and
session identity, collision precedence, race loser, unlisted unique violation, contradictory terminal events,
receipt counts and reads) and 3 (migration 0020 upgrade/downgrade, constraints and indexes).

No cold or EV binding can be published before W2-01/W2-02, so `basis_from_snapshot` is patched (test-only, per
ruling 6) to add v4 `BindingBasis` rows for the closed channel table that reuse the registered pv-inverter
binding revision and asset. Requires ASSETOPS_TEST_DATABASE_URL (see backend/README-db.md).
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError, IntegrityError
    from test_s1_bindings_postgres import (  # noqa: F401
        FIXTURE, KOBO_SOURCE, NOW, BindingService, Clock, ImportSource, _alembic, convert, engine,
        import_site, read_import_source, store,
    )
    from test_s2_evidence_ledger_postgres import RECEIVED, Kit, _z, enable, ingestion, kit, submit  # noqa: F401

    from assetops_backend.evidence import ledger_service
    from assetops_backend.evidence.adapters import postgres_evidence_ledger as adapter_module
    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.ledger_service import BatchIngestionService, BatchRefused
    from assetops_contracts.ingestion_receipt_v2 import (
        canonical_receipt_v2_text,
        parse_canonical_receipt_v2_text,
    )
    from assetops_contracts.source_envelope import canonical_json
    from assetops_contracts.source_envelope_v3 import v3_message_id
    from assetops_contracts.source_envelope_v4 import V4_CHANNEL_MAPPINGS

TEMPLATE = ("pv-inverter-controller", "ac-power")
ASSET_CODE = "pv-inverter"  # the template binding's frozen asset code: the "connector" public identifier


# --- v4 fixtures -----------------------------------------------------------------


@pytest.fixture()
def v4(kit, monkeypatch):
    """Patch S2's basis so the closed v4 channels are bound (test-only), and return an envelope builder."""
    original = ledger_service.basis_from_snapshot
    overrides: dict = {}

    def patched(stored, **kw):
        basis = original(stored, **kw)
        template = basis.bindings[TEMPLATE]
        extra = {}
        for (device, signal), entry in V4_CHANNEL_MAPPINGS.items():
            unit = entry.allowed_units[0] if entry.allowed_units else "none"
            extra[(device, signal)] = replace(
                template, device_id=device, signal_id=signal, role=entry.role or f"test-{device}-{signal}",  # W2-01: the table names the role
                source_unit=unit, canonical_unit=unit, conversion={"kind": "IDENTITY", "parameters": {}},
                **entry.metadata(),
            )
        extra.update({key: replace(extra.get(key, basis.bindings.get(key)), **change)
                      for key, change in overrides.items()})
        return replace(basis, bindings={**basis.bindings, **extra})

    monkeypatch.setattr(ledger_service, "basis_from_snapshot", patched)
    return Builder(kit, overrides)


class Builder:
    def __init__(self, kit, overrides) -> None:
        self.kit = kit
        self.overrides = overrides
        b = kit.binding(*TEMPLATE)
        self.site, self.gateway, self.source = kit.doc["site"]["site_id"], b["gateway_id"], b["source_id"]

    def at(self, minutes: int) -> str:
        return _z(self.kit.start + timedelta(minutes=minutes))

    def doc(self, seq, device, signal, payload, *, minutes=5, published=None, interval=None, schema=4) -> dict:
        source = self.at(minutes)
        return {
            "schema": {"id": "assetops.source-envelope", "version": schema},
            "message": {"message_id": v3_message_id(site_id=self.site, gateway_id=self.gateway,
                                                    source_id=self.source, sequence_epoch="epoch-1", sequence=seq),
                        "sequence_epoch": "epoch-1", "sequence": seq},
            "source": {"site_id": self.site, "gateway_id": self.gateway, "source_id": self.source,
                       "device_id": device, "signal_id": signal},
            "mapping": {"binding_set_id": self.kit.doc["mapping"]["binding_set_id"],
                        "version": self.kit.doc["mapping"]["version"]},
            "timing": {"source_time": source, "published_at": published or source,
                       "interval_start": None if interval is None else self.at(interval),
                       "interval_end": None if interval is None else source},
            "payload": payload,
        }

    def event(self, seq, kind, event_id, outcome, *, device="generator-controller", signal="start-event",
              corr="attempt-1", component="generator-1", unit=None, value=None, session=None, connector=None,
              **kw) -> str:
        payload = {"family": "EVENT", "record_kind": kind, "event_id": event_id, "correlation_id": corr,
                   "component_id": component, "actor": "CONTROLLER", "outcome": outcome, "unit": unit,
                   "value": value, "quality": "GOOD", "session_id": session, "connector_id": connector}
        return canonical_json(self.doc(seq, device, signal, payload, **kw))

    def start(self, seq, event_id, session="sess-1", connector=ASSET_CODE, **kw) -> str:
        return self.event(seq, "EV_SESSION_START", event_id, "STARTED", device="charger-controller",
                          signal="session-event", corr=session, component="charger-1", session=session,
                          connector=connector, **kw)

    def point(self, seq, value="3.8", unit="degC", **kw) -> str:
        payload = {"family": "MEASUREMENT", "measurement": "STATE_AT_INSTANT", "value": value, "unit": unit,
                   "quality": "GOOD", "unavailable_reason": None, "session_id": None, "connector_id": None}
        return canonical_json(self.doc(seq, "chamber-probe", "temperature", payload, **kw))

    def delta(self, seq, value="1.25", unit="kWh", interval=0, **kw) -> str:
        payload = {"family": "MEASUREMENT", "measurement": "INTERVAL_DELTA", "value": value, "unit": unit,
                   "quality": "GOOD", "unavailable_reason": None, "session_id": "sess-1", "connector_id": ASSET_CODE}
        return canonical_json(self.doc(seq, "charger-controller", "session-event", payload, interval=interval, **kw))

    def submit(self, texts):
        return submit(self.kit, self.kit.seal(texts))


def rows(engine, sql, **params):
    with engine.connect() as connection:
        return connection.execute(text(sql), params).mappings().all()


def decisions(receipt):
    return [(d.decision, None if d.rejection is None else d.rejection.kind,
             None if d.rejection is None else d.rejection.field) for d in receipt.dispositions]


# --- acceptance 1: admission, typed columns, ordinal refusals ------------------------------


class TestAdmission:
    def test_v4_events_and_measurements_are_accepted_with_typed_columns_and_no_dispatch_job(self, v4, engine) -> None:
        answer = v4.submit([
            v4.point(1),
            v4.event(2, "START_RESULT", "evt-2", "FAILED"),
            v4.event(3, "MANUAL_LOG", "evt-3", "OBSERVED", device="operator-log", signal="temperature-event",
                     corr="round-1", component="room-1", unit="degC", value="4.1"),
            v4.event(4, "POWER_LOSS", "evt-4", "LOST", device="grid-meter", signal="event", corr="outage-1",
                     component=None),
            v4.start(5, "evt-5"),
        ])
        assert decisions(answer.receipt) == [("ACCEPTED", None, None)] * 5
        got = {r["device_id"]: r for r in rows(engine, "SELECT * FROM accepted_evidence")}
        point, failed, log, power, start = (got[d] for d in ("chamber-probe", "generator-controller", "operator-log",
                                                              "grid-meter", "charger-controller"))
        assert (point["family"], point["measurement"], point["conversion_kind"], point["record_kind"],
                point["session_id"]) == ("MEASUREMENT", "STATE_AT_INSTANT", "IDENTITY", None, None)
        assert (failed["family"], failed["measurement"], failed["conversion_kind"], failed["original_unit"],
                failed["normalized_value_text"], failed["record_kind"], failed["event_id"], failed["correlation_id"],
                failed["actor"], failed["outcome"]) == (
            "EVENT", None, None, None, None, "START_RESULT", "evt-2", "attempt-1", "CONTROLLER", "FAILED")
        assert (log["original_value_text"], log["original_unit"], log["normalized_value_text"],
                log["normalized_unit"]) == ("4.1", "degC", "4.1", "degC")
        assert power["record_kind"] == "POWER_LOSS"
        assert (start["session_id"], start["connector_id"], str(start["asset_id"])) == (
            "sess-1", ASSET_CODE, v4.kit.binding(*TEMPLATE)["asset_id"])
        assert rows(engine, "SELECT * FROM recompute_job") == []
        v3 = v4.submit(v4.kit.pv(1, first=50))
        assert decisions(v3.receipt) == [("ACCEPTED", None, None)]
        assert [j["domain"] for j in rows(engine, "SELECT domain FROM recompute_job")] == ["dispatch"]

    def test_a_valid_header_batch_completes_with_one_persisted_ordinal_refusal_each(self, v4, engine) -> None:
        def v3_event(seq):
            doc = __import__("json").loads(v4.event(seq, "START_REQUEST", f"evt-{seq}", "REQUESTED"))
            doc["schema"]["version"] = 3
            return canonical_json(doc)

        noncanonical = __import__("json").dumps(__import__("json").loads(v4.point(13)), indent=1)
        texts = [
            v4.event(1, "START_REQUEST", "evt-1", "REQUESTED"),                       # accepted
            v3_event(2),                                                               # v4 kind under v3
            v4.event(3, "START_REQUEST", None, "REQUESTED"),                           # null event id
            v4.delta(4, unit="Wh"),                                                    # delta unit
            v4.delta(5, interval=5),                                                   # zero-length interval
            v4.delta(6, value="-1"),                                                   # negative delta
            v4.start(7, "evt-7", connector="connector-9"),                             # bound connector mismatch
            v4.event(8, "COMPRESSOR_TRIP", "evt-8", "OBSERVED"),                       # unknown kind
            v4.event(9, "START_RESULT", "evt-9", "OPEN"),                              # invalid outcome
            v4.point(10, unit="degF"),                                                 # unit not registered
            v4.event(11, "DOOR_OPEN", "evt-11", "OPEN"),                               # kind not this channel's
            v4.event(12, "START_REQUEST", "evt-12", "REQUESTED", device=TEMPLATE[0], signal=TEMPLATE[1]),
            noncanonical,                                                              # not canonical text
            v4.event(14, "START_REQUEST", "evt-14", "REQUESTED", minutes=-60 * 24 * 30),  # before Foundation
        ]
        answer = v4.submit(texts)
        assert answer.receipt.status == "COMPLETED"
        assert decisions(answer.receipt) == [
            ("ACCEPTED", None, None),
            ("REJECTED", "SCHEMA_UNSUPPORTED", "payload.family"),
            ("REJECTED", "CORRELATION_INVALID", "payload.event_id"),
            ("REJECTED", "EV_DELTA_UNIT_INVALID", "payload.unit"),
            ("REJECTED", "EV_DELTA_INTERVAL_INVALID", "timing.interval_start"),
            ("REJECTED", "EV_DELTA_VALUE_INVALID", "payload.value"),
            ("REJECTED", "EV_CONNECTOR_MISMATCH", "payload.connector_id"),
            ("REJECTED", "RECORD_KIND_UNSUPPORTED", "payload.record_kind"),
            ("REJECTED", "INVALID_PAYLOAD", "payload.outcome"),
            ("REJECTED", "UNIT_INCOMPATIBLE", "payload.unit"),
            ("REJECTED", "MAPPING_INCOMPATIBLE", "mapping"),
            ("REJECTED", "MAPPING_INCOMPATIBLE", "mapping"),
            ("REJECTED", "NOT_CANONICAL", "envelope"),
            ("REJECTED", "OUTSIDE_FOUNDATION_PERIOD", "timing.source_time"),
        ]
        stored = rows(engine, "SELECT ordinal, message_id, kind, conflicts_with_evidence_id FROM evidence_rejection "
                              "ORDER BY ordinal")
        assert [r["ordinal"] for r in stored] == list(range(1, 14))
        assert all(r["conflicts_with_evidence_id"] is None for r in stored)  # the four EV codes included
        by_ordinal = {r["ordinal"]: r for r in stored}
        for ordinal in (1, 2, 12):  # the valid header's message ID is kept on a parser refusal
            assert by_ordinal[ordinal]["message_id"] == answer.receipt.dispositions[ordinal].message_id != ""
        assert len(rows(engine, "SELECT 1 FROM ingestion_disposition")) == len(texts)

    def test_missing_or_divergent_v4_binding_metadata_is_mapping_incompatible(self, v4) -> None:
        v4.overrides[("door-sensor", "event")] = {"requires_session": True}               # divergent
        v4.overrides[("transfer-controller", "event")] = {"allowed_record_kinds": None}   # absent (a v3 row)
        answer = v4.submit([
            v4.event(1, "DOOR_OPEN", "evt-1", "OPEN", device="door-sensor", signal="event", corr="cycle-1",
                     component="door-1"),
            v4.event(2, "TRANSFER_RESULT", "evt-2", "SUCCEEDED", device="transfer-controller", signal="event"),
        ])
        assert decisions(answer.receipt) == [("REJECTED", "MAPPING_INCOMPATIBLE", "mapping")] * 2

    def test_a_binding_registered_only_in_another_tenant_is_whole_batch_configuration_unregistered(
            self, v4, store, engine) -> None:
        source = read_import_source(str(KOBO_SOURCE))
        other = import_site(store, tenant_slug="w200-other", configured_tenant_slug="w200-other",
                            source=ImportSource(path="var/sites/kobo-001.yaml", sha256=source.sha256,
                                                record=source.record),
                            legacy_documents=(), clock=Clock(NOW - timedelta(hours=2)))
        outcome = convert(store, BindingService(store, Clock(NOW - timedelta(hours=1))), other.tenant, other.site,
                          FIXTURE)
        enable(engine, other.site.id)
        theirs = Kit(engine, outcome.published.changed.id)
        assert theirs.principal.tenant_id != v4.kit.principal.tenant_id
        # The other tenant's own registered scope, naming our tenant's binding set.
        b = theirs.binding(*TEMPLATE)
        foreign = replace_builder(v4, site=theirs.doc["site"]["site_id"], gateway=b["gateway_id"],
                                  source=b["source_id"])
        body = foreign_seal(theirs, v4.kit, [foreign.event(1, "START_REQUEST", "evt-1", "REQUESTED")])
        before = rows(engine, "SELECT (SELECT count(*) FROM accepted_evidence) a, "
                              "(SELECT count(*) FROM ingestion_disposition) d")[0]
        with pytest.raises(BatchRefused) as refused:
            ingestion().submit(theirs.principal, body.encode("utf-8"))
        assert (refused.value.kind, refused.value.field) == ("CONFIGURATION_UNREGISTERED", "mapping")
        after = rows(engine, "SELECT (SELECT count(*) FROM accepted_evidence) a, "
                             "(SELECT count(*) FROM ingestion_disposition) d")[0]
        assert after == before


def foreign_seal(theirs, ours, texts) -> str:
    from assetops_contracts.ingestion_batch_v2 import seal_batch_v2

    b = theirs.binding(*TEMPLATE)
    _, body = seal_batch_v2(
        site_id=theirs.doc["site"]["site_id"], gateway_id=b["gateway_id"], source_id=b["source_id"],
        source_mode=theirs.doc["gateway"]["mode"], foundation_version=ours.doc["foundation"]["version"],
        foundation_valid_from=ours.doc["foundation"]["valid_from"],
        binding_set_id=ours.doc["mapping"]["binding_set_id"], binding_version=ours.doc["mapping"]["version"],
        snapshot_sha256=ours.sha, envelope_texts=texts)
    return body


# Builder is a plain class; dataclasses.replace needs a dataclass, so give it a tiny copy helper.
def _builder_replace(builder, **fields):
    clone = Builder.__new__(Builder)
    clone.__dict__.update(builder.__dict__, **fields)
    return clone


replace_builder = _builder_replace


# --- acceptance 2: replay, identity, precedence -----------------------------------------------


class TestReplayAndCollisions:
    def test_duplicates_conflicts_and_precedence_with_receipts_after_reload(self, v4, engine) -> None:
        first = v4.submit([
            v4.event(1, "START_RESULT", "evt-1", "FAILED"),
            v4.start(2, "start-1"),
            v4.event(3, "START_RESULT", "evt-3", "SUCCEEDED"),  # contradictory terminal event: still accepted
        ])
        assert decisions(first.receipt) == [("ACCEPTED", None, None)] * 3
        ids = {d.ordinal: d.evidence_id for d in first.receipt.dispositions}
        replay = v4.submit([
            v4.event(1, "START_RESULT", "evt-1", "FAILED"),                                  # same bytes
            v4.event(10, "START_RESULT", "evt-1", "FAILED", published=v4.at(9)),              # new message, same event
            v4.event(11, "START_RESULT", "evt-1", "SUCCEEDED"),                               # changed event identity
            v4.start(12, "start-2"),                                                          # distinct START
            v4.event(13, "START_RESULT", "evt-1", "FAILED", minutes=6),                       # source time differs
        ])
        assert decisions(replay.receipt) == [
            ("DUPLICATE", None, None), ("DUPLICATE", None, None),
            ("CONFLICT", "EVENT_ID_CONFLICT", "payload.event_id"),
            ("CONFLICT", "SESSION_ID_CONFLICT", "payload.session_id"),
            ("CONFLICT", "EVENT_ID_CONFLICT", "payload.event_id"),
        ]
        d = replay.receipt.dispositions
        assert d[0].evidence_id == d[1].evidence_id == ids[0]
        assert d[2].rejection.conflicts_with_evidence_id == ids[0]
        assert d[3].rejection.conflicts_with_evidence_id == ids[1]
        # message+event double collision: the message key wins; event+session with a free message: event wins.
        doubles = v4.submit([
            v4.event(1, "START_RESULT", "evt-1", "SUCCEEDED"),       # message 1 changed bytes, event evt-1 changed
            v4.start(20, "start-1", minutes=7),                     # event start-1 changed and session collides
        ])
        assert decisions(doubles.receipt) == [("CONFLICT", "MESSAGE_CONFLICT", "message.message_id"),
                                              ("CONFLICT", "EVENT_ID_CONFLICT", "payload.event_id")]
        assert doubles.receipt.dispositions[0].rejection.conflicts_with_evidence_id == ids[0]
        assert doubles.receipt.dispositions[1].rejection.conflicts_with_evidence_id == ids[1]
        # Receipts after reload: counts, conflict kinds and references round-trip byte for byte.
        for answer, counts in ((replay, (5, 0, 2, 0, 3)), (doubles, (2, 0, 0, 0, 2))):
            reloaded = ingestion().receipt(v4.kit.principal, answer.receipt.batch_id)
            assert canonical_receipt_v2_text(reloaded) == canonical_receipt_v2_text(answer.receipt)
            assert parse_canonical_receipt_v2_text(canonical_receipt_v2_text(reloaded)) == reloaded
            c = reloaded.counts
            assert (c.total, c.accepted, c.duplicate, c.rejected, c.conflict) == counts

    def test_site_evidence_and_rejection_reads_count_every_conflict_kind_as_a_conflict(self, v4, engine) -> None:
        from assetops_backend.evidence.ledger_reads import CONFLICT_KINDS

        v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED"), v4.start(2, "start-1")])
        v4.submit([v4.event(3, "START_RESULT", "evt-1", "SUCCEEDED"), v4.start(4, "start-2"),
                   v4.event(5, "START_REQUEST", None, "REQUESTED")])
        kinds = {r["kind"] for r in rows(engine, "SELECT kind FROM evidence_rejection")}
        assert kinds == {"EVENT_ID_CONFLICT", "SESSION_ID_CONFLICT", "CORRELATION_INVALID"}
        assert {"EVENT_ID_CONFLICT", "SESSION_ID_CONFLICT"} <= CONFLICT_KINDS
        assert "CORRELATION_INVALID" not in CONFLICT_KINDS

    def test_a_concurrent_race_loser_gets_the_typed_conflict(self, v4, engine) -> None:
        holding, release = threading.Event(), threading.Event()
        winner = PostgresEvidenceLedger(URL, test_decision_clock_override=Clock(RECEIVED))
        persist = winner._persist

        def slow_persist(c, batch, decision, decided_at):
            out = persist(c, batch, decision, decided_at)
            holding.set()
            assert release.wait(30)
            return out

        winner._persist = slow_persist
        results: dict = {}
        body_a = v4.kit.seal([v4.event(1, "START_RESULT", "evt-1", "FAILED")])
        body_b = v4.kit.seal([v4.event(2, "START_RESULT", "evt-1", "SUCCEEDED")])
        a = threading.Thread(target=lambda: results.setdefault("a", BatchIngestionService(
            winner, Clock(RECEIVED)).submit(v4.kit.principal, body_a.encode())))
        a.start()
        assert holding.wait(30)
        b = threading.Thread(target=lambda: results.setdefault("b", ingestion().submit(
            v4.kit.principal, body_b.encode())))
        b.start()
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:  # B's INSERT is blocked on the winner's uncommitted event key
            waiting = rows(engine, "SELECT count(*) n FROM pg_stat_activity WHERE wait_event_type = 'Lock' "
                                   "AND query LIKE 'INSERT INTO accepted_evidence%'")[0]["n"]
            if waiting:
                break
            time.sleep(0.05)
        assert waiting, "the loser never blocked on the unique index"
        release.set()
        a.join(30)
        b.join(30)
        assert decisions(results["a"].receipt) == [("ACCEPTED", None, None)]
        assert decisions(results["b"].receipt) == [("CONFLICT", "EVENT_ID_CONFLICT", "payload.event_id")]
        assert results["b"].receipt.dispositions[0].rejection.conflicts_with_evidence_id == \
            results["a"].receipt.dispositions[0].evidence_id

    def test_an_unlisted_unique_violation_propagates_and_writes_nothing(self, v4, engine, monkeypatch) -> None:
        first = v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED")])
        existing = UUID(first.receipt.dispositions[0].evidence_id)
        before = rows(engine, "SELECT count(*) n FROM ingestion_disposition")[0]["n"]
        monkeypatch.setattr(adapter_module, "uuid4", lambda: existing)  # primary-key collision, not listed
        with pytest.raises(IntegrityError, match="accepted_evidence_pkey"):
            v4.submit([v4.event(2, "START_RESULT", "evt-2", "FAILED")])
        monkeypatch.undo()
        assert rows(engine, "SELECT count(*) n FROM ingestion_disposition")[0]["n"] == before


# --- reads ---------------------------------------------------------------------------------


class FixedPrincipals:
    def __init__(self, principal) -> None:
        self.principal = principal

    def resolve(self, authorization):
        return self.principal


class TestReads:
    def test_postgres_records_filter_by_family_and_kind_and_old_rows_serialize_nulls(self, v4, engine) -> None:
        from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads, record_payload

        v4.submit(v4.kit.pv(1, first=40))
        v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED"), v4.start(2, "start-1"), v4.point(3)])
        ledger = PostgresEvidenceLedger(URL)
        t, s = v4.kit.principal.tenant_id, v4.kit.principal.site_id

        def page(**filters):
            return ledger.records_page(t, s, start=None, end=None, device=None, signal=None, source=None,
                                       after=None, limit=100, **filters)

        assert page()["total"] == 4
        assert {r["record_kind"] for r in page(family="EVENT")["rows"]} == {"START_RESULT", "EV_SESSION_START"}
        assert [r["event_id"] for r in page(kind="EV_SESSION_START")["rows"]] == ["start-1"]
        assert page(family="MEASUREMENT", kind="START_RESULT")["total"] == 0
        old = next(r for r in page(family="MEASUREMENT")["rows"] if r["device_id"] == TEMPLATE[0])
        served = record_payload(old)
        for key in ("record_kind", "event_id", "correlation_id", "session_id", "connector_id", "outcome"):
            assert served[key] is None
        assert served["family"] == "MEASUREMENT"
        event = record_payload(page(kind="START_RESULT")["rows"][0])
        assert (event["family"], event["record_kind"], event["event_id"], event["correlation_id"],
                event["outcome"]) == ("EVENT", "START_RESULT", "evt-1", "attempt-1", "FAILED")
        assert ImportedEvidenceReads  # the route builder below exercises the HTTP validation

    def test_records_route_validates_the_new_filters(self, v4) -> None:
        from test_s2_site_evidence_postgres import client, empty_set_report

        v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED"), v4.point(2)])
        http = client(v4.kit, empty_set_report(v4.kit))
        events = http.get("/api/sites/KOBO-001/evidence/records?family=EVENT").json()
        assert [r["record_kind"] for r in events["records"]] == ["START_RESULT"]
        assert http.get("/api/sites/KOBO-001/evidence/records?kind=START_RESULT&family=MEASUREMENT").json()[
            "total"] == 0
        for query, code in (("family=POLICY", "INVALID_FAMILY"), ("kind=COMPRESSOR_TRIP", "INVALID_KIND")):
            bad = http.get(f"/api/sites/KOBO-001/evidence/records?{query}")
            assert (bad.status_code, bad.json()["detail"]["code"]) == (422, code)


def test_the_legacy_file_backed_records_route_rejects_the_new_filters(tmp_path) -> None:
    from test_t027_ingestion import SITE_ID, FakeSites, a_site, client_for

    http = client_for(tmp_path, FakeSites((a_site(),)))
    assert http.get(f"/api/sites/{SITE_ID}/evidence/records").status_code == 200
    for query in ("family=EVENT", "kind=START_RESULT"):
        bad = http.get(f"/api/sites/{SITE_ID}/evidence/records?{query}")
        assert (bad.status_code, bad.json()["detail"]["code"]) == (422, "FILTER_UNSUPPORTED")


# --- acceptance 3: migration 0020 ----------------------------------------------------------

V3_COLUMNS = (
    "id, tenant_id, site_id, batch_id, ordinal, gateway_id, source_id, message_id, sequence_epoch, sequence, "
    "device_id, signal_id, asset_id, role, family, measurement, source_time, published_at, received_at, "
    "interval_start, interval_end, quality, unavailable_reason, original_value_text, original_unit, "
    "normalized_value_text, normalized_unit, conversion_kind, envelope_sha256, envelope_text, "
    "foundation_revision_id, binding_set_revision_id, binding_revision_id, configuration_outdated, source_mode"
)


def raw_copy(engine, source_id, **changes):
    """Insert a modified copy of an accepted row directly (test-only; proves the 0020 constraints)."""
    with engine.connect() as connection:
        row = dict(connection.execute(text("SELECT * FROM accepted_evidence WHERE id = :i"),
                                      {"i": source_id}).mappings().one())
    row.update(id=uuid4(), message_id=uuid4().hex + uuid4().hex, **changes)
    columns = ", ".join(row)
    values = ", ".join(f":{k}" for k in row)
    with engine.begin() as connection:
        connection.execute(text(f"INSERT INTO accepted_evidence ({columns}) VALUES ({values})"), row)
    return row["id"]


def _delete_as_replica(engine, statements) -> None:
    """Test-only cleanup of rows this test created: the replica role skips the append-only trigger."""
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL session_replication_role = replica"))
        for sql in statements:
            connection.execute(text(sql))


def remove_test_events(engine) -> None:
    _delete_as_replica(engine, (
        "DELETE FROM ingestion_disposition d USING accepted_evidence e WHERE d.accepted_evidence_id = e.id "
        "AND (e.family = 'EVENT' OR e.measurement = 'INTERVAL_DELTA')",
        "DELETE FROM accepted_evidence WHERE family = 'EVENT' OR measurement = 'INTERVAL_DELTA'",
    ))


def remove_test_blockers(engine) -> None:
    _delete_as_replica(engine, (
        "DELETE FROM ingestion_disposition d USING evidence_rejection r WHERE d.rejection_id = r.id "
        "AND r.kind IN ('EVENT_ID_CONFLICT','SESSION_ID_CONFLICT')",
        "DELETE FROM evidence_rejection WHERE kind IN ('EVENT_ID_CONFLICT','SESSION_ID_CONFLICT')",
        "DELETE FROM recompute_job WHERE domain = 'cold_chain'",
    ))
    remove_test_events(engine)


def head(engine) -> str:
    with engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


def nullable(engine, column):
    with engine.connect() as connection:
        return connection.execute(text(
            "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'accepted_evidence' "
            "AND column_name = :c"), {"c": column}).scalar()


class TestMigration0020:
    def test_upgrade_keeps_v3_rows_and_reads_and_downgrade_refuses_while_v4_facts_exist(self, v4, engine) -> None:
        from alembic import command

        from assetops_backend.evidence.ledger_reads import record_payload

        config = _alembic()
        v4.submit(v4.kit.pv(3, first=60))
        ledger = PostgresEvidenceLedger(URL)
        t, s = v4.kit.principal.tenant_id, v4.kit.principal.site_id

        def v3_reads():
            page = ledger.records_page(t, s, start=None, end=None, device=None, signal=None, source=None,
                                       after=None, limit=100)
            return [record_payload(r) for r in page["rows"]]

        def v3_rows():
            return [dict(r) for r in rows(engine, f"SELECT {V3_COLUMNS} FROM accepted_evidence ORDER BY id")]

        refused = "Downgrade of 0020_w2_source_event refused"
        before_rows, before_reads = v3_rows(), v3_reads()
        try:
            command.downgrade(config, "0019_verification_core")
            assert head(engine) == "0019_verification_core" and nullable(engine, "record_kind") is None
            assert v3_rows() == before_rows
            command.upgrade(config, "head")
            assert v3_rows() == before_rows and v3_reads() == before_reads
            assert all(r["record_kind"] is None and r["session_id"] is None
                       for r in rows(engine, "SELECT record_kind, session_id FROM accepted_evidence"))

            # 1. an accepted event
            first = v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED"), v4.start(2, "start-1")])
            assert first.receipt.counts.accepted == 2
            evidence_count = len(rows(engine, "SELECT 1 FROM accepted_evidence"))
            with pytest.raises(DBAPIError, match=refused):
                command.downgrade(config, "0019_verification_core")
            assert head(engine) == "0021_w2_cold_config"
            assert len(rows(engine, "SELECT 1 FROM accepted_evidence")) == evidence_count  # nothing deleted
            remove_test_blockers(engine)

            # 2. an accepted interval delta
            source_time = before_rows[0]["source_time"]
            raw_copy(engine, before_rows[0]["id"], measurement="INTERVAL_DELTA", original_unit="kWh",
                     normalized_unit="kWh", original_value_text="1.5", normalized_value_text="1.5",
                     interval_start=source_time - timedelta(minutes=5), interval_end=source_time,
                     session_id="sess-1", connector_id=ASSET_CODE)
            with pytest.raises(DBAPIError, match=refused):
                command.downgrade(config, "0019_verification_core")
            remove_test_blockers(engine)

            # 3. an event-ID conflict alone (its accepted event removed first)
            v4.submit([v4.event(3, "START_RESULT", "evt-3", "FAILED")])
            v4.submit([v4.event(4, "START_RESULT", "evt-3", "SUCCEEDED")])
            assert rows(engine, "SELECT kind FROM evidence_rejection WHERE kind = 'EVENT_ID_CONFLICT'")
            _delete_as_replica(engine, (
                "DELETE FROM ingestion_disposition d USING accepted_evidence e WHERE d.accepted_evidence_id = e.id "
                "AND e.family = 'EVENT' AND NOT EXISTS (SELECT 1 FROM evidence_rejection r "
                "WHERE r.conflicts_with_evidence_id = e.id)",
            ))
            with pytest.raises(DBAPIError, match=refused):
                command.downgrade(config, "0019_verification_core")
            remove_test_blockers(engine)

            # 4. a cold_chain recompute job
            with engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO recompute_job (id, tenant_id, site_id, domain, window_start, window_end, status, "
                    "available_at, created_at) VALUES (:i, :t, :s, 'cold_chain', now(), "
                    "now() + interval '1 minute', 'PENDING', now(), now())"), {"i": uuid4(), "t": t, "s": s})
            with pytest.raises(DBAPIError, match=refused):
                command.downgrade(config, "0019_verification_core")
            remove_test_blockers(engine)

            command.downgrade(config, "0019_verification_core")
            assert [nullable(engine, c) for c in ("measurement", "conversion_kind", "original_unit",
                                                  "normalized_unit")] == ["NO"] * 4
            with engine.connect() as connection:
                check = connection.execute(text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conname = 'evidence_rejection_conflict_kind'")).scalar_one()
            assert "MESSAGE_CONFLICT" in check and "EVENT_ID_CONFLICT" not in check
            assert v3_rows() == before_rows
        finally:
            command.upgrade(config, "head")
        assert head(engine) == "0021_w2_cold_config" and v3_reads() == before_reads

    def test_constraints_indexes_site_fks_and_append_only_hold(self, v4, engine) -> None:
        answer = v4.submit([v4.event(1, "START_RESULT", "evt-1", "FAILED"), v4.start(2, "start-1"), v4.point(3)])
        event_id, start_id, point_id = (UUID(d.evidence_id) for d in answer.receipt.dispositions)
        for source_id, changes, constraint in (
            (event_id, {"event_id": None}, "accepted_evidence_event_shape"),
            (event_id, {"outcome": "OPEN"}, "accepted_evidence_event_kind_outcome"),
            (event_id, {"measurement": "STATE_AT_INSTANT"}, "accepted_evidence_event_shape"),
            (event_id, {"family": "POLICY"}, "accepted_evidence_family"),
            (event_id, {"event_id": "x" * 129}, "accepted_evidence_event_id_length"),
            (event_id, {"actor": "ROBOT"}, "accepted_evidence_event_actor"),
            (event_id, {}, "accepted_event_identity_unique"),                       # same event key
            (event_id, {"asset_id": uuid4(), "event_id": "evt-fk"}, "accepted_evidence_asset_fk"),         # composite same-Site FK
            (event_id, {"site_id": uuid4()}, r"accepted_evidence_(?:site|batch|source|asset|foundation|binding)\w*_fk"),
            (start_id, {"event_id": "start-2"}, "accepted_ev_start_unique"),         # distinct START, same session
            (point_id, {"session_id": "sess-1"}, "accepted_evidence_measurement_ids"),
            (point_id, {"measurement": "INTERVAL_DELTA"}, "accepted_evidence_ev_delta_shape"),
            (point_id, {"record_kind": "DOOR_OPEN"}, "accepted_evidence_measurement_shape"),
        ):
            with pytest.raises(IntegrityError, match=constraint):
                raw_copy(engine, source_id, **changes)
        raw_copy(engine, start_id, event_id="start-3", session_id="sess-2", correlation_id="sess-2")
        raw_copy(engine, event_id, event_id="evt-9")  # a distinct event key is admitted
        with pytest.raises(DBAPIError, match="append-only"):
            with engine.begin() as connection:
                connection.execute(text("UPDATE accepted_evidence SET outcome = 'SUCCEEDED' WHERE id = :i"),
                                   {"i": event_id})
        with pytest.raises(IntegrityError, match="evidence_rejection_conflict_kind"):
            with engine.begin() as connection:
                connection.execute(text(
                    "INSERT INTO evidence_rejection (id, tenant_id, site_id, batch_id, ordinal, message_id, kind, "
                    "field, detail, envelope_sha256, conflicts_with_evidence_id, received_at) SELECT :i, tenant_id, "
                    "site_id, batch_id, 99, message_id, 'EVENT_ID_CONFLICT', 'payload.event_id', 'x', "
                    "envelope_sha256, NULL, received_at FROM accepted_evidence WHERE id = :e"),
                    {"i": uuid4(), "e": event_id})
