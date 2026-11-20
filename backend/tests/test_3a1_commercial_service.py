"""3A1 (spec `specs/3A1-commercial-record-store/spec.md` §3, §4, §6; rulings D-3A1.1 to D-3A1.12, R1-R17, P1-P7): the
commercial record service over an in-memory store.

`MemoryCommercialStore` implements the store port of spec §4.1 with a `threading.Lock` per tenant. The lock only makes
the fake safe; the concurrency claim rests on the Postgres proof alone (R15). It also keeps the four tables' uniqueness
keys, so a service that plans a duplicate row fails here as it would in Postgres. The Postgres test reuses it for the
"in both stores" checks (R7, R3, P7).
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import threading
from collections import defaultdict
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable, Mapping
from uuid import UUID, uuid4

import pytest

from assetops_backend.commercial.model import (OUTCOMES, ExistingRecord, IntakeResult, IntakeSummary, Plan,
                                               RecordOutcome, RevisionRow)
from assetops_backend.commercial.service import CommercialRecords
from assetops_contracts.canonical import loads_canonical, parse_record, to_canonical_json

TREE = Path(__file__).resolve().parents[2]
FIXTURE = TREE / "backend" / "tests" / "fixtures" / "canonical_v1_examples.json"
T0 = datetime(2026, 11, 20, 8, 0, tzinfo=timezone.utc)
BY = "service:commercial-intake"
TENANTS = ("lakeside-power", "harvest-cold", "metro-bus")
#: P5: the 9 Site codes of 2a's fixture and DS1b's fixture view, by tenant.
SITES = {
    "lakeside-power": ("KOBO-001", "KISIWA-001", "MTO-001"),
    "harvest-cold": ("COLD-THIKA", "COLD-MWEA", "COLD-KIRI"),
    "metro-bus": ("EV-EMB", "EV-KAS", "EV-RUI"),
}


class Clock:
    def __init__(self, now: datetime = T0) -> None:
        self.now = now

    def __call__(self) -> datetime:
        return self.now


# --- the in-memory store -----------------------------------------------------------------------------------------

def _sort_key(row: RevisionRow):
    """Spec §4.1: (site_id NULLS FIRST, kind, recognition_period, source_system, source_record_id); an ascending
    Postgres sort puts a NULL recognition_period last."""
    return (row.site_id is not None, str(row.site_id or ""), row.kind, row.recognition_period is None,
            row.recognition_period or "", row.source_system, row.source_record_id)


class MemoryCommercialStore:
    def __init__(self) -> None:
        self.slugs: dict[UUID, str] = {}
        self.sites: dict[tuple[UUID, str], UUID] = {}
        self.intakes: list = []
        self.records: list = []
        self.revisions: list[RevisionRow] = []
        self.rejections: list = []
        self._locks: defaultdict[UUID, threading.Lock] = defaultdict(threading.Lock)
        self._guard = threading.Lock()

    def add_tenant(self, slug: str) -> UUID:
        tid = uuid4()
        self.slugs[tid] = slug
        return tid

    def add_site(self, tenant_id: UUID, code: str) -> UUID:
        sid = uuid4()
        self.sites[(tenant_id, code.lower())] = sid
        return sid

    def counts(self) -> tuple[int, int, int, int]:
        return len(self.intakes), len(self.records), len(self.revisions), len(self.rejections)

    # port

    def tenant_slug(self, tenant_id: UUID) -> str | None:
        return self.slugs.get(tenant_id)

    def site_ids(self, tenant_id: UUID, codes: set[str]) -> dict[str, UUID]:
        return {c: self.sites[(tenant_id, c.lower())] for c in codes if (tenant_id, c.lower()) in self.sites}

    def existing(self, tenant_id: UUID, source_system: str, ids: set[str]) -> dict[str, ExistingRecord]:
        out: dict[str, ExistingRecord] = {}
        for record in self.records:
            if record.tenant_id != tenant_id or record.source_system != source_system or record.source_record_id not in ids:
                continue
            revs = sorted((r for r in self.revisions if r.record_id == record.id), key=lambda r: r.revision_no)
            out[record.source_record_id] = ExistingRecord(
                record_id=record.id, kind=record.kind, site_id=record.site_id,
                versions={r.source_version: r.record_sha256 for r in revs},
                latest_revision_id=revs[-1].id, latest_revision_no=revs[-1].revision_no,
                provenances={r.source_version: r.provenance for r in revs})
        return out

    def write_intake(self, tenant_id: UUID, source_system: str | None, ids: set[str],
                     decide: Callable[[Mapping[str, ExistingRecord]], Plan], *, dry_run: bool) -> Plan:
        with self._locks[tenant_id]:
            existing = self.existing(tenant_id, source_system, ids) if ids else {}
            plan = decide(existing)
            if not dry_run:
                with self._guard:
                    self._check_keys(plan)
                    self.intakes.append(plan.intake)
                    self.records.extend(plan.records)
                    self.revisions.extend(plan.revisions)
                    self.rejections.extend(plan.rejections)
            return plan

    def _check_keys(self, plan: Plan) -> None:
        """The uniqueness keys of spec §2, so a duplicate planned row fails as it would in Postgres."""
        keys = {(r.tenant_id, r.source_system, r.source_record_id) for r in self.records}
        for record in plan.records:
            key = (record.tenant_id, record.source_system, record.source_record_id)
            assert key not in keys, "UNIQUE (tenant_id, source_system, source_record_id)"
            keys.add(key)
        versions = {(r.record_id, r.source_version) for r in self.revisions}
        numbers = {(r.record_id, r.revision_no) for r in self.revisions}
        for rev in plan.revisions:
            assert (rev.record_id, rev.source_version) not in versions, "UNIQUE (record_id, source_version)"
            assert (rev.record_id, rev.revision_no) not in numbers, "UNIQUE (record_id, revision_no)"
            versions.add((rev.record_id, rev.source_version))
            numbers.add((rev.record_id, rev.revision_no))

    def latest_revisions(self, tenant_id: UUID, *, site_id: UUID | None = None, kind: str | None = None,
                         recognition_period: str | None = None) -> tuple[RevisionRow, ...]:
        latest: dict[UUID, RevisionRow] = {}
        for rev in self.revisions:  # R7: latest per record over all revisions first, then the filters
            if rev.tenant_id == tenant_id and (rev.record_id not in latest
                                               or rev.revision_no > latest[rev.record_id].revision_no):
                latest[rev.record_id] = rev
        rows = [r for r in latest.values()
                if (site_id is None or r.site_id == site_id) and (kind is None or r.kind == kind)
                and (recognition_period is None or r.recognition_period == recognition_period)]
        return tuple(sorted(rows, key=_sort_key))

    def record_history(self, tenant_id: UUID, record_id: UUID) -> tuple[RevisionRow, ...]:
        return tuple(sorted((r for r in self.revisions if r.tenant_id == tenant_id and r.record_id == record_id),
                            key=lambda r: r.revision_no))

    def intake(self, tenant_id: UUID, intake_id: UUID) -> IntakeSummary | None:
        found = [i for i in self.intakes if i.tenant_id == tenant_id and i.id == intake_id]
        if not found:
            return None
        rejections = sorted((r for r in self.rejections if r.intake_id == intake_id), key=lambda r: r.record_index)
        revision_ids = sorted((r.id for r in self.revisions if r.intake_id == intake_id), key=str)
        return IntakeSummary(intake=found[0], rejections=tuple(rejections), revision_ids=tuple(revision_ids))


# --- the world and its batches -----------------------------------------------------------------------------------

def make_world(store) -> dict:
    """P5: the 3 demo tenants and all 9 Site codes; `seed` adds them to whichever store is given."""
    tenants: dict[str, UUID] = {}
    sites: dict[str, UUID] = {}
    for slug in TENANTS:
        tenants[slug] = store.add_tenant(slug)
        for code in SITES[slug]:
            sites[code] = store.add_site(tenants[slug], code)
    return dict(tenants=tenants, sites=sites)


@pytest.fixture()
def world():
    store = MemoryCommercialStore()
    w = make_world(store)
    clock = Clock()
    return dict(w, store=store, clock=clock, svc=CommercialRecords(store, clock=clock))


def fixture_batches() -> list[dict]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["batches"]


def encode(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def batch(records: list[dict], *, tenant: str = "lakeside-power", source_type: str = "expense_ledger",
          source_system: str = "lakeside-accounts", provenance: str = "source-emulated") -> bytes:
    return encode({"format_version": 1, "tenant_code": tenant, "source_type": source_type,
                   "source_system": source_system, "provenance": provenance,
                   "produced_at": "2026-11-05T09:00:00+03:00", "records": records})


def expense(rid: str = "Q-KIS-0091", version: str = "1", *, amount: str = "1800.00", site: str | None = "KISIWA-001",
            period: str = "2026-11", ref: str = "KIS-GEN-1") -> dict:
    record = {"format_version": 1, "kind": "EXPENSE", "source_record_id": rid, "source_version": version,
              "site_code": site, "subject": {"kind": "ASSET", "ref": ref},
              "clocks": {"occurred_at": "2026-11-04T15:30:00+03:00", "recognition_period": period},
              "amount": {"value": amount, "currency": "USD"}, "status": "QUOTE",
              "body": {"counterparty_ref": "SUP-GENSERV", "category": "REPAIR", "document_ref": "Q-KIS-0091.pdf"}}
    if site is None:
        del record["site_code"]
    return record


def adjustment(rid: str, version: str = "1", *, site: str = "KISIWA-001") -> dict:
    return {"format_version": 1, "kind": "ADJUSTMENT", "source_record_id": rid, "source_version": version,
            "site_code": site, "subject": {"kind": "CUSTOMER", "ref": "CUST-117"},
            "clocks": {"effective_from": "2026-10-21", "recognition_period": "2026-10"},
            "amount": {"value": "-108.00", "currency": "USD"},
            "body": {"reason_code": "SPOILAGE_CREDIT", "authorised_by_ref": "P-KEVIN", "document_ref": "CN-0412.pdf"}}


def kinds(result: IntakeResult) -> list[str]:
    return [o.outcome for o in result.outcomes]


def refusals(result: IntakeResult) -> list[tuple[str | None, str | None]]:
    return [(o.code, o.path) for o in result.outcomes if o.outcome == "REFUSED"]


def ingest(w, data: bytes, tenant: str = "lakeside-power", **kw) -> IntakeResult:
    return w["svc"].ingest(w["tenants"][tenant], data, entered_by=BY, **kw)


# --- §3 rule 5: the outcomes ---------------------------------------------------------------------------------------

def test_new_then_revised_then_unchanged(world) -> None:
    store = world["store"]
    first = ingest(world, batch([expense()]))
    assert first.state == "STORED" and kinds(first) == ["NEW"] and first.outcomes[0].revision_no == 1
    assert first.intake_id is not None and first.dry_run is False
    world["clock"].now = T0.replace(hour=9)
    second = ingest(world, batch([expense(version="2", amount="1750.00")]))
    assert kinds(second) == ["REVISED"] and second.outcomes[0].revision_no == 2
    assert second.outcomes[0].record_id == first.outcomes[0].record_id
    history = store.record_history(world["tenants"]["lakeside-power"], first.outcomes[0].record_id)
    assert [r.revision_no for r in history] == [1, 2]
    assert history[0].supersedes_revision_id is None and history[1].supersedes_revision_id == history[0].id
    assert history[1].amount == Decimal("1750.00") and history[1].recorded_at == T0.replace(hour=9)
    (latest,) = store.latest_revisions(world["tenants"]["lakeside-power"])
    assert latest.id == history[1].id
    before = store.counts()
    third = ingest(world, batch([expense(version="2", amount="1750.00")]))
    assert kinds(third) == ["UNCHANGED"] and third.outcomes[0].record_id == first.outcomes[0].record_id
    assert store.counts() == (before[0] + 1, before[1], before[2], before[3])


def test_a_known_version_with_other_content_is_a_conflict(world) -> None:
    ingest(world, batch([expense()]))
    before = world["store"].counts()
    result = ingest(world, batch([expense(amount="1900.00")]))
    assert refusals(result) == [("INTAKE_VERSION_CONFLICT", "record.source_version")]
    assert result.outcomes[0].source_record_id == "Q-KIS-0091"
    after = world["store"].counts()
    assert after == (before[0] + 1, before[1], before[2], before[3] + 1)
    rejection = world["store"].rejections[-1]
    assert (rejection.code, rejection.path, rejection.source_record_id, rejection.record_index) == (
        "INTAKE_VERSION_CONFLICT", "record.source_version", "Q-KIS-0091", 0)


def test_the_same_version_under_another_provenance_is_refused(world) -> None:  # R12, D-3A1.9
    ingest(world, batch([expense()]))
    result = ingest(world, batch([expense()], provenance="demo-simulated"))
    assert refusals(result) == [("INTAKE_PROVENANCE_CHANGED", "record.source_version")]
    assert {r.provenance for r in world["store"].revisions} == {"source-emulated"}


def test_the_same_file_twice_adds_one_intake_row_and_nothing_else(world) -> None:  # R8
    data = encode(fixture_batches()[4])
    first = ingest(world, data)
    assert kinds(first) == ["NEW", "NEW"]
    before = world["store"].counts()
    second = ingest(world, data)
    assert kinds(second) == ["UNCHANGED", "UNCHANGED"] and second.state == "STORED"
    assert world["store"].counts() == (before[0] + 1, before[1], before[2], before[3])
    row = world["store"].intakes[-1]
    assert (row.record_count, row.new_count, row.revised_count, row.unchanged_count, row.refused_count) == (2, 0, 0, 2, 0)
    summary = world["store"].intake(world["tenants"]["lakeside-power"], second.intake_id)
    assert summary.intake == row and summary.rejections == () and summary.revision_ids == ()


# --- §3 rules 3 and 4: refusals per record -------------------------------------------------------------------------

def test_a_refused_record_never_stops_the_others(world) -> None:
    bad = expense("Q-BAD")
    bad["amount"]["value"] = "1.0e3"
    result = ingest(world, batch([expense("Q-1"), bad, expense("Q-2", site="MTO-001"), expense("Q-3", site="COLD-THIKA")]))
    assert kinds(result) == ["NEW", "REFUSED", "NEW", "REFUSED"]
    assert refusals(result) == [("CANONICAL_NUMBER", "record.amount.value"), ("INTAKE_SITE_UNKNOWN", "record.site_code")]
    assert result.outcomes[1].source_record_id is None and result.outcomes[3].source_record_id == "Q-3"
    rows = world["store"].rejections
    assert [(r.record_index, r.source_record_id, r.code) for r in rows] == [
        (1, None, "CANONICAL_NUMBER"), (3, "Q-3", "INTAKE_SITE_UNKNOWN")]  # P3
    intake = world["store"].intakes[-1]
    assert (intake.record_count, intake.new_count, intake.refused_count) == (4, 2, 2)
    summary = world["store"].intake(world["tenants"]["lakeside-power"], result.intake_id)
    assert [r.record_index for r in summary.rejections] == [1, 3] and len(summary.revision_ids) == 2


def test_a_service_ticket_is_not_commercial(world) -> None:
    data = encode(fixture_batches()[11])
    result = ingest(world, data, tenant="metro-bus")
    assert refusals(result) == [("INTAKE_NOT_COMMERCIAL", "record.kind")]
    assert world["store"].rejections[0].source_record_id == result.outcomes[0].source_record_id is not None
    assert world["store"].records == []


def test_a_changed_kind_or_site_is_refused(world) -> None:
    ingest(world, batch([expense("X-1"), adjustment("X-2")]))
    result = ingest(world, batch([adjustment("X-1", "2"), expense("X-2", "2"), expense("X-1", "3", site="KOBO-001")]))
    assert refusals(result) == [("INTAKE_KIND_CHANGED", "record.kind"), ("INTAKE_KIND_CHANGED", "record.kind"),
                                ("INTAKE_SITE_CHANGED", "record.site_code")]
    assert len(world["store"].revisions) == 2


def test_two_versions_of_one_record_in_one_batch(world) -> None:  # R9, D-3A1.11
    result = ingest(world, batch([expense("X", "1"), expense("X", "2", amount="10.00"), adjustment("Y", "1"),
                                  expense("Y", "2")]))
    assert kinds(result) == ["NEW", "REVISED", "NEW", "REFUSED"]
    assert refusals(result) == [("INTAKE_KIND_CHANGED", "record.kind")]
    assert [o.revision_no for o in result.outcomes[:2]] == [1, 2]
    history = world["store"].record_history(world["tenants"]["lakeside-power"], result.outcomes[0].record_id)
    assert history[1].supersedes_revision_id == history[0].id and len(world["store"].records) == 2


def test_a_null_site_budget_line(world) -> None:
    data = encode(fixture_batches()[5])
    result = ingest(world, data)
    assert kinds(result) == ["NEW", "NEW", "NEW"]
    assert [r.site_id is None for r in world["store"].latest_revisions(world["tenants"]["lakeside-power"])] == [
        True, False, False]  # NULL Sites first (P7)


# --- §3 rules 1 and 2: intake refusals -----------------------------------------------------------------------------

ENVELOPE = {"format_version": 1, "tenant_code": "lakeside-power", "source_type": "expense_ledger",
            "source_system": "lakeside-accounts", "provenance": "source-emulated",
            "produced_at": "2026-11-05T09:00:00+03:00", "records": []}


@pytest.mark.parametrize("data, code, path, filled", [
    (b"not json {", "CANONICAL_TYPE", "json", ()),
    (encode(dict(ENVELOPE, source_type="no_such_type")), "CANONICAL_SOURCE_TYPE", "batch.source_type", ()),
    (encode(dict(ENVELOPE, provenance="observed")), "CANONICAL_PROVENANCE", "batch.provenance",
     ("source_type", "source_system")),
    (encode(dict(ENVELOPE, records={})), "CANONICAL_TYPE", "batch.records",
     ("source_type", "source_system", "provenance", "produced_at")),
], ids=["not-json", "bad-source-type", "bad-provenance", "bad-records"])
def test_an_envelope_refusal_keeps_only_what_parsed(world, data, code, path, filled) -> None:  # R1
    result = ingest(world, data)
    assert (result.state, result.refusal_code, result.refusal_path, result.outcomes) == ("REFUSED", code, path, ())
    (row,) = world["store"].intakes
    assert world["store"].counts() == (1, 0, 0, 0)
    assert row.batch_sha256 == hashlib.sha256(data).hexdigest()
    assert (row.state, row.refusal_code, row.refusal_path) == ("REFUSED", code, path)
    assert (row.record_count, row.new_count, row.revised_count, row.unchanged_count, row.refused_count) == (0,) * 5
    for column in ("source_type", "source_system", "provenance", "produced_at"):
        assert (getattr(row, column) is not None) == (column in filled), column
    if "produced_at" in filled:
        assert row.produced_at == datetime.fromisoformat("2026-11-05T09:00:00+03:00")
    assert (row.entered_by, row.entered_at) == (BY, T0)


def test_an_envelope_value_after_the_refused_one_is_null_even_when_valid(world) -> None:  # R1
    data = encode(dict(ENVELOPE, source_system=" padded "))
    result = ingest(world, data)
    assert (result.refusal_code, result.refusal_path) == ("CANONICAL_REF", "batch.source_system")
    row = world["store"].intakes[0]
    assert (row.source_type, row.source_system, row.provenance, row.produced_at) == ("expense_ledger", None, None, None)


def test_another_tenants_batch_is_refused(world) -> None:  # P4 isolation
    data = encode(fixture_batches()[4])
    result = ingest(world, data, tenant="harvest-cold")
    assert (result.state, result.refusal_code, result.refusal_path) == (
        "REFUSED", "INTAKE_TENANT_MISMATCH", "batch.tenant_code")
    (row,) = world["store"].intakes
    assert row.tenant_id == world["tenants"]["harvest-cold"] and row.record_count == 0
    assert (row.source_type, row.source_system, row.provenance) == ("expense_ledger", "lakeside-accounts",
                                                                     "source-emulated")
    assert world["store"].counts() == (1, 0, 0, 0)


def test_an_unknown_tenant_is_a_programming_error(world) -> None:  # R15
    with pytest.raises(LookupError) as raised:
        world["svc"].ingest(uuid4(), batch([expense()]), entered_by=BY)
    assert world["store"].counts() == (0, 0, 0, 0)
    assert "Q-KIS" not in str(raised.value)


# --- §3 rule 7: the dry run ----------------------------------------------------------------------------------------

def test_a_dry_run_gives_the_real_outcomes_and_writes_nothing(world) -> None:
    ingest(world, batch([expense("X")]))
    data = batch([expense("X"), expense("X", "2"), expense("Z", site="COLD-THIKA"), expense("N")])
    before = world["store"].counts()
    dry = ingest(world, data, dry_run=True)
    assert dry.intake_id is None and dry.dry_run is True and world["store"].counts() == before
    real = ingest(world, data)
    assert real.intake_id is not None and real.dry_run is False
    strip = lambda r: [replace(o, record_id=None) for o in r.outcomes]  # noqa: E731 - new IDs differ by run
    assert strip(dry) == strip(real) and kinds(real) == ["UNCHANGED", "REVISED", "REFUSED", "NEW"]
    assert dry.outcomes[0].record_id == real.outcomes[0].record_id  # an existing record keeps its ID
    refused = ingest(world, b"[]", dry_run=True)
    assert refused.state == "REFUSED" and refused.intake_id is None and world["store"].counts()[0] == before[0] + 1


# --- R3, P7: exactness, and R13: no leak ---------------------------------------------------------------------------

def assert_exact(rows) -> int:
    """Every amount and quantity is the record's own decimal text, and `canonical` is 2a's bytes (R3, P7)."""
    checked = 0
    for row in rows:
        stored = json.loads(row.canonical)
        assert row.canonical == to_canonical_json(parse_record(loads_canonical(row.canonical.encode()))).decode()
        assert hashlib.sha256(row.canonical.encode()).hexdigest() == row.record_sha256
        if row.amount is not None:
            assert isinstance(row.amount, Decimal) and format(row.amount, "f") == stored["amount"]["value"]
            assert row.currency == stored["amount"]["currency"]
            checked += 1
        else:
            assert "amount" not in stored
        if row.quantity is not None:
            assert isinstance(row.quantity, Decimal) and format(row.quantity, "f") == stored["quantity"]["value"]
            assert row.unit == stored["quantity"]["unit"]
            checked += 1
        else:
            assert "quantity" not in stored
        assert row.recognition_period == stored["clocks"].get("recognition_period")
    return checked


def test_no_float_in_the_commercial_package() -> None:  # R3
    package = TREE / "backend" / "assetops_backend" / "commercial"
    files = sorted(package.rglob("*.py"))
    assert len(files) >= 5
    assert [str(f) for f in files if re.search(r"\bfloat\(", f.read_text(encoding="utf-8"))] == []


def test_no_log_call_in_the_commercial_package() -> None:  # R13, D-3A1.10
    package = TREE / "backend" / "assetops_backend" / "commercial"
    pattern = re.compile(r"\b(?:import logging|getLogger|logger\.|print\()")
    assert [str(f) for f in package.rglob("*.py") if pattern.search(f.read_text(encoding="utf-8"))] == []


def test_no_ref_or_value_in_a_refusal(world) -> None:  # R13, probe P6
    marker = "PII-MARKER-7731"
    ingest(world, batch([expense(marker, ref=marker)]))
    bad_ref = expense("Q-9", ref=marker + "\u0007")
    results = [
        ingest(world, batch([expense(marker, amount="99.00", ref=marker)])),                   # conflict
        ingest(world, batch([expense(marker, ref=marker)], provenance="demo-simulated")),      # provenance
        ingest(world, batch([adjustment(marker, "2")])),                                       # kind changed
        ingest(world, batch([expense(marker, "3", site="KOBO-001", ref=marker)])),             # site changed
        ingest(world, batch([expense("Q-8", site="EV-EMB", ref=marker)])),                     # site unknown
        ingest(world, batch([bad_ref])),                                                       # 2a format refusal
        ingest(world, batch([expense(ref=marker)]), tenant="metro-bus"),                       # tenant mismatch
    ]
    seen = 0
    for result in results:
        for text in [result.refusal_code, result.refusal_path] + [x for o in result.outcomes for x in (o.code, o.path)]:
            assert marker not in (text or "")
            seen += text is not None
    assert seen >= 14
    assert [r.code for r in world["store"].rejections] == [
        "INTAKE_VERSION_CONFLICT", "INTAKE_PROVENANCE_CHANGED", "INTAKE_KIND_CHANGED", "INTAKE_SITE_CHANGED",
        "INTAKE_SITE_UNKNOWN", "CANONICAL_REF"]
    assert all(marker not in r.path for r in world["store"].rejections)


# --- R7: latest before any filter ----------------------------------------------------------------------------------

def month_move(w) -> UUID:
    tid = w["tenants"]["lakeside-power"]
    ingest(w, batch([expense("MOVE", period="2026-10")]))
    ingest(w, batch([expense("MOVE", "2", period="2026-11")]))
    return tid


def test_a_correction_that_moves_the_month_counts_once(world) -> None:
    tid = month_move(world)
    store = world["store"]
    assert store.latest_revisions(tid, recognition_period="2026-10") == ()
    (row,) = store.latest_revisions(tid, recognition_period="2026-11")
    assert (row.revision_no, row.source_record_id, row.source_system) == (2, "MOVE", "lakeside-accounts")
    assert store.latest_revisions(tid, kind="EXPENSE", site_id=world["sites"]["KISIWA-001"]) == (row,)
    assert store.latest_revisions(tid, kind="ADJUSTMENT") == ()


# --- the fixtures (spec §6; R5, P5) --------------------------------------------------------------------------------

def ingest_fixture(w) -> list[IntakeResult]:
    return [ingest(w, encode(b), tenant=b["tenant_code"]) for b in fixture_batches()]


def test_the_2a_fixture_ingests(world) -> None:
    results = ingest_fixture(world)
    assert len(results) == 17 and all(r.state == "STORED" for r in results)
    outcomes = [o for r in results for o in r.outcomes]
    assert sum(o.outcome == "NEW" for o in outcomes) == 22
    assert [(o.code, o.path) for o in outcomes if o.outcome == "REFUSED"] == [("INTAKE_NOT_COMMERCIAL", "record.kind")]
    rows = [r for t in world["tenants"].values() for r in world["store"].latest_revisions(t)]
    assert len(rows) == 22 and {r.provenance for r in rows} == {"source-emulated"}
    assert assert_exact(rows) > 15
    assert {o.outcome for o in outcomes} <= set(OUTCOMES)


def ds1b_batches(tmp_path: Path) -> list[Path]:
    out = tmp_path / "ds1b"
    subprocess.run([sys.executable, str(TREE / "tools" / "world_history.py"), "records", "--manifest",
                    str(TREE / "simulator" / "tests" / "world" / "fixtures" / "view_v1.json"), "--out", str(out)],
                   check=True, capture_output=True)
    files = sorted(p for p in out.glob("*.json") if p.name != "unwritten.json")
    assert len(files) == 7
    return files


def ingest_ds1b(w, files: list[Path]) -> list[str]:
    outcomes: list[str] = []
    for path in files:
        data = path.read_bytes()
        tenant = json.loads(data)["tenant_code"]
        outcomes += kinds(ingest(w, data, tenant=tenant))
    return outcomes


def test_the_ds1b_batches_ingest_twice(world, tmp_path) -> None:
    files = ds1b_batches(tmp_path)
    assert ingest_ds1b(world, files) == ["NEW"] * 142
    assert ingest_ds1b(world, files) == ["UNCHANGED"] * 142
    assert world["store"].rejections == []
    rows = [r for t in world["tenants"].values() for r in world["store"].latest_revisions(t)]
    assert len(rows) == 142 and {r.provenance for r in rows} == {"source-emulated"}
    assert assert_exact(rows) == 58  # 57 EXPENSE and 1 ADJUSTMENT amounts; BUDGET_LINE values live in `canonical`


def test_the_model_shapes() -> None:
    assert OUTCOMES == ("NEW", "REVISED", "UNCHANGED", "REFUSED")
    outcome = RecordOutcome(0, "NEW", "X", uuid4(), 1, None, None)
    with pytest.raises(Exception):
        outcome.index = 1  # frozen
    assert IntakeResult(None, "REFUSED", "C", "json", (), True).intake_id is None
    assert {"source_system", "source_record_id", "canonical", "provenance", "supersedes_revision_id"} <= set(
        RevisionRow.__dataclass_fields__)
    assert copy.copy(outcome) == outcome
