"""DD5a unit 4 (spec §4.7 as amended by D-DD.140; D-DD.9): the bulk path stores what central ingestion stores for one
cold Site-day and one EV Site-day, so `postgres_evidence_ledger.py:688` admits COLDCHAIN and EV_CHARGING.

One seed (`dd5apseed`: `harvest-cold` and `metro-bus` onboarded with their world bindings, as `onboard_operator apply
--bindings` does), two clones (`dd5apreal`, `dd5apbulk`). The batches are sealed by `evidence/world_seal` from hand
readings in the writers' shapes (cold: a meter mean, a probe instant, a door open and close; EV: a session start, the
in-session connector energy, the depot import, the session end), then submitted to `BatchIngestionService` on one
clone and bulk-loaded on the other. Stored rows are compared without receipt times and generated ids, as
`test_ds3_parity_postgres.py` does, and the enqueue rule (`_enqueue_admitted`) is spied on both paths. Plant (c) of
the card (revert `:688`) fails this file with `BULK_SITE_TYPE_UNPROVEN`. Requires ASSETOPS_TEST_DATABASE_URL."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from uuid import UUID

import pytest

import pg_harness

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from sqlalchemy import create_engine, text
    from test_dd1_onboarding_postgres import ON1, PG_TARGET_ENV, WORLD

    from test_ds3_parity_postgres import BATCH_SQL, DISPOSITION_SQL, EVIDENCE_SQL, _engine

    from assetops_backend.evidence.adapters.postgres_evidence_ledger import PostgresEvidenceLedger
    from assetops_backend.evidence.bulk_load import BulkEvidenceLoad
    from assetops_backend.evidence.ledger import GatewayPrincipal
    from assetops_backend.evidence.ledger_service import BatchIngestionService
    from assetops_backend.evidence.world_seal import context_from_snapshot, seal_readings

DAY = date(2026, 10, 12)
DIGEST = "f" * 64
SESSION = "ev-" + hashlib.sha256(b"dd5a parity session").hexdigest()
JOB_SQL = ("SELECT tenant_id, site_id, domain, window_start, window_end FROM recompute_job "
           "ORDER BY site_id, domain, window_start")


def _t(hhmm: str) -> str:
    return f"{DAY.isoformat()}T{hhmm}:00+03:00"


def _row(device, signal, start, end, value, unit, **extra) -> dict:
    return {"source_id": device, "signal_id": signal, "start": _t(start), "end": _t(end), "value": value, "unit": unit,
            **extra}


def _event(device, signal, at, kind, outcome, ordinal, **ids) -> dict:
    return _row(device, signal, at, at, None, "event", event={
        "record_kind": kind, "outcome": outcome, "actor": ids.pop("actor", "SENSOR"), "component_id": ids.pop("component"),
        "ordinal": ordinal, **ids})


COLD_DAY = [
    _row("compressor-meter", "power", "09:25", "09:30", "3.200", "kW"),
    _event("door-sensor", "event", "09:31", "DOOR_OPEN", "OPEN", 1, component="door-sensor", correlation=["door", 1]),
    _row("compressor-meter", "power", "09:30", "09:35", "3.100", "kW"),
    _event("door-sensor", "event", "09:36", "DOOR_CLOSE", "CLOSED", 2, component="door-sensor",
           correlation=["door", 1]),
]
_IN_SESSION = {"session_id": SESSION, "connector_id": "ch-k1-c1"}
EV_DAY = [
    _event("ch-k1-c1-charger-controller", "session-event", "22:05", "EV_SESSION_START", "STARTED", 1,
           actor="CONTROLLER", component="ch-k1-c1", correlation=None, **_IN_SESSION),
    _row("ch-k1-c1-connector-meter", "energy", "22:05", "22:10", "4.000", "kWh", session=dict(_IN_SESSION)),
    _row("site-meter", "import", "22:05", "22:10", "48.000", "kW"),
    _row("ch-k1-c1-connector-meter", "energy", "22:10", "22:15", "4.500", "kWh", session=dict(_IN_SESSION)),
    _event("ch-k1-c1-charger-controller", "session-event", "22:15", "EV_SESSION_END", "COMPLETED", 2,
           actor="CONTROLLER", component="ch-k1-c1", correlation=None, **_IN_SESSION),
]
SITES = (("harvest-cold", "COLD-THIKA", COLD_DAY), ("metro-bus", "EV-KAS", EV_DAY))


def _snapshot(engine, code):
    with engine.connect() as c:
        row = c.execute(text(
            "SELECT r.snapshot_canonical, s.id FROM signal_binding_set_revision r JOIN site s ON s.id = r.site_id "
            "WHERE s.site_code = :c AND r.superseded_at IS NULL"), {"c": code}).one()
    body = bytes(row[0])
    return json.loads(body), hashlib.sha256(body).hexdigest(), row[1]


@pytest.fixture(scope="module")
def seeded():
    """The seed's URL and, per Site, `(principal, sealed batch bytes)`."""
    seed = pg_harness.clone_database("dd5apseed")
    try:
        out = {}
        # The command runs in its own process: its engines close when it exits, so the seed can be cloned.
        with tempfile.TemporaryDirectory() as keys:
            os.chmod(keys, 0o700)
            env = {k: v for k, v in os.environ.items() if k not in (*PG_TARGET_ENV, "ASSETOPS_REAL_OPERATOR_DATA")}
            env.update(DATABASE_URL=seed, ASSETOPS_PSEUDONYM_KEY_DIR=keys)
            for slug, _, _ in SITES:
                env["ASSETOPS_TENANT_SLUG"] = slug
                path = str(ON1 / f"{slug}.onboarding.json")
                command = [sys.executable, "-m", "assetops_backend.onboard_operator"]
                digest = subprocess.run([*command, "digest", "--file", path], env=env, capture_output=True,
                                        text=True, check=True).stdout.strip()
                applied = subprocess.run([*command, "apply", "--file", path, "--confirmed-digest", digest,
                                          "--bindings", str(WORLD)], env=env, capture_output=True, text=True)
                assert applied.returncode == 0, applied.stderr
        engine = create_engine(seed)
        try:
            for slug, code, rows in SITES:
                doc, sha, site_id = _snapshot(engine, code)
                context = context_from_snapshot(code, str(site_id), doc, sha, DIGEST)
                batches = [b.text.encode("utf-8") for b in seal_readings(context, [(DAY, rows)])]
                principal = GatewayPrincipal(tenant_id=UUID(doc["tenant_id"]), site_id=site_id,
                                             gateway_id=UUID(doc["gateway"]["gateway_id"]), mode=doc["gateway"]["mode"])
                out[code] = (principal, batches)
        finally:
            pg_harness.dispose(engine)
        yield seed, out
    finally:
        pg_harness.drop_database(seed)


class _Spy:
    """The enqueue rule's input per call: Site type and the admitted `(message_id, is_v4, role)`."""

    def __init__(self, monkeypatch) -> None:
        self.calls: list[tuple[str, tuple]] = []
        original = PostgresEvidenceLedger._enqueue_admitted
        spy = self

        def wrapped(ledger, c, row, site_type, admitted, decided_at):
            spy.calls.append((site_type, tuple((d.envelope.message_id, d.is_v4, d.binding.role) for d, _ in admitted)))
            return original(ledger, c, row, site_type, admitted, decided_at)

        monkeypatch.setattr(PostgresEvidenceLedger, "_enqueue_admitted", wrapped)

    def admitted(self) -> dict[str, set]:
        out: dict[str, set] = {}
        for site_type, rows in self.calls:
            out.setdefault(site_type, set()).update(rows)
        return out


@pytest.mark.parametrize("code", ["COLD-THIKA", "EV-KAS"])
def test_the_bulk_path_stores_what_central_ingestion_stores(seeded, code, monkeypatch) -> None:
    seed, sites = seeded
    principal, batches = sites[code]
    envelopes = sum(len(json.loads(b)["envelopes"]) for b in batches)
    assert envelopes == len(dict(SITES_BY_CODE)[code])
    urls = []
    try:
        real = pg_harness.clone_database("dd5apreal", seed)
        urls.append(real)
        bulk = pg_harness.clone_database("dd5apbulk", seed)
        urls.append(bulk)

        spy_real = _Spy(monkeypatch)
        ledger = PostgresEvidenceLedger(real)
        try:
            service = BatchIngestionService(ledger)
            for body in batches:
                answer = service.submit(principal, body)
                assert answer.status == 200 and answer.receipt.status == "COMPLETED", answer
                assert answer.receipt.counts.accepted == answer.receipt.counts.total, answer.receipt.dispositions
        finally:
            pg_harness.dispose(ledger)
        enqueued_real = spy_real.admitted()
        monkeypatch.undo()

        spy_bulk = _Spy(monkeypatch)
        ledger = PostgresEvidenceLedger(bulk)
        try:
            loaded = BulkEvidenceLoad(ledger).load(batches)
        finally:
            pg_harness.dispose(ledger)
        assert (loaded.batches, loaded.already_loaded, loaded.envelopes) == (len(batches), 0, envelopes)
        enqueued_bulk = spy_bulk.admitted()
        monkeypatch.undo()

        # The enqueue rule saw the same admitted ordinals under the same Site type on both paths.
        assert enqueued_real and enqueued_bulk == enqueued_real
        with _engine(real) as r, _engine(bulk) as b:
            real_evidence = r.execute(text(EVIDENCE_SQL)).all()
            assert len(real_evidence) == envelopes
            assert b.execute(text(EVIDENCE_SQL)).all() == real_evidence
            assert b.execute(text(BATCH_SQL)).all() == r.execute(text(BATCH_SQL)).all()
            assert b.execute(text(DISPOSITION_SQL)).all() == r.execute(text(DISPOSITION_SQL)).all()
            assert b.execute(text(JOB_SQL)).all() == r.execute(text(JOB_SQL)).all()
            if code == "EV-KAS":
                ids = {(row.record_kind, row.session_id, row.correlation_id) for row in real_evidence
                       if row.session_id is not None}
                assert ids == {("EV_SESSION_START", SESSION, SESSION), ("EV_SESSION_END", SESSION, SESSION),
                               (None, SESSION, None)}
    finally:
        for url in urls:
            pg_harness.drop_database(url)


SITES_BY_CODE = tuple((code, rows) for _, code, rows in SITES)
