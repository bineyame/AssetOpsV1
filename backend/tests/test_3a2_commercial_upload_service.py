"""3A2 (spec `specs/3A2-commercial-file-intake/spec.md` §3, §6 "Service, no database"; D-3A2.1 to D-3A2.16): check,
submit, accept and decline an operator's export over the in-memory stores.

`UploadMemoryStore` subclasses (never edits) 3A1's `MemoryCommercialStore` and adds spec §3.5's methods with the same
per-tenant lock and the same "no decision yet" check. The people are 3C1a's `People` (tenant `acme`, Sites
`KOBO-001` and `KISIWA-001`). The pseudonym goldens below were computed by hand with `hmac` (W2); no expected value
here calls `pseudonym()`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import fields, replace
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from assetops_backend.commercial.model import (IntakeSummary, UploadAlreadyDecided, UploadDecisionRow, UploadRecord,
                                               UploadRow)
from assetops_backend.commercial.composition import FileKeyStore
from assetops_backend.commercial.pseudonym import (ALLOWED_EXTRA, REF_BODY_FIELDS, PseudonymKeyMissing,
                                                   PseudonymKeyUnusable, pseudonymise)
from assetops_backend.commercial.readers import READERS, CanonicalJsonReader, ReadResult
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import Actor, CommercialUploads, UploadRefused, UploadScope
from assetops_backend.i18n import message, render
from assetops_contracts.canonical import KIND_SPECS, loads_canonical
from test_3a1_commercial_service import Clock, MemoryCommercialStore
from test_3c1a_person_work import KISIWA, KOBO, People

TREE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T_SUBMIT = datetime(2026, 11, 6, 9, 0, tzinfo=timezone.utc)
KEY = bytes(range(32))
FIN, ANALYST, EXEC = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST", "OPERATOR_EXECUTIVE"
#: Hand-computed: HMAC-SHA256(bytes(range(32)), "<cls>\x1f<value>"), first 32 hex digits.
C_0412 = "C-448c423147e7b551e039ebc4c61f2029"
M_MT2201 = "M-c04f202e85dd8387ebaf47111ad43111"
P_JOSEPH = "P-8612fd0721ba1f89ecbd14eff25bcf42"
#: 2a §6.7's 17 codes and the 8 INTAKE_* codes the service can emit, written out here (W2).
CANONICAL_CODES = ("CANONICAL_VERSION", "CANONICAL_KIND", "CANONICAL_FIELD", "CANONICAL_FORBIDDEN", "CANONICAL_TYPE",
                   "CANONICAL_NUMBER", "CANONICAL_SIGN", "CANONICAL_ENUM", "CANONICAL_UNIT", "CANONICAL_CURRENCY",
                   "CANONICAL_CLOCK", "CANONICAL_RANGE", "CANONICAL_REF", "CANONICAL_DUPLICATE", "CANONICAL_FACTOR",
                   "CANONICAL_SOURCE_TYPE", "CANONICAL_PROVENANCE")
INTAKE_CODES = ("INTAKE_NOT_COMMERCIAL", "INTAKE_SITE_UNKNOWN", "INTAKE_SITE_NOT_THIS_SITE", "INTAKE_KIND_CHANGED",
                "INTAKE_SITE_CHANGED", "INTAKE_VERSION_CONFLICT", "INTAKE_PROVENANCE_CHANGED",
                "INTAKE_TENANT_MISMATCH")


# --- the in-memory upload store ------------------------------------------------------------------------------------

class UploadMemoryStore(MemoryCommercialStore):
    """3A1's store plus spec §3.5's upload methods, under the same per-tenant lock. `on_lock` runs under the lock
    before the decision check (service test 12's hook)."""

    def __init__(self, names: dict[UUID, str]) -> None:
        super().__init__()
        self.uploads: list[UploadRow] = []
        self.decisions: list[UploadDecisionRow] = []
        self.names = names
        self.on_lock = None
        self.under_lock_check = True

    def _decided(self, tenant_id: UUID, upload_id: UUID) -> bool:
        return any(d.tenant_id == tenant_id and d.upload_id == upload_id for d in self.decisions)

    def write_intake(self, tenant_id, source_system, ids, decide, *, dry_run, decision=None):
        with self._locks[tenant_id]:
            if self.on_lock is not None:
                self.on_lock()
            if decision is not None and not dry_run and self.under_lock_check and self._decided(tenant_id,
                                                                                                decision.upload_id):
                raise UploadAlreadyDecided()
            existing = self.existing(tenant_id, source_system, ids) if ids else {}
            plan = decide(existing)
            if not dry_run:
                with self._guard:
                    self._check_keys(plan)
                    self.intakes.append(plan.intake)
                    self.records.extend(plan.records)
                    self.revisions.extend(plan.revisions)
                    self.rejections.extend(plan.rejections)
                    if decision is not None:
                        self.decisions.append(decision)
            return plan

    def add_upload(self, row: UploadRow) -> None:
        with self._guard:
            self.uploads.append(row)

    def write_decline(self, row: UploadDecisionRow) -> None:
        with self._locks[row.tenant_id]:
            if self._decided(row.tenant_id, row.upload_id):
                raise UploadAlreadyDecided()
            self.decisions.append(row)

    def _record(self, row: UploadRow) -> UploadRecord:
        found = [d for d in self.decisions if d.tenant_id == row.tenant_id and d.upload_id == row.id]
        decision = found[0] if found else None
        intake = None if decision is None or decision.intake_id is None else self.intake(row.tenant_id,
                                                                                        decision.intake_id)
        return UploadRecord(row, self.names[row.submitted_by], decision,
                            None if decision is None else self.names[decision.decided_by], intake)

    def upload(self, tenant_id: UUID, upload_id: UUID) -> UploadRecord | None:
        found = [u for u in self.uploads if u.tenant_id == tenant_id and u.id == upload_id]
        return self._record(found[0]) if found else None

    def uploads_in_scope(self, tenant_id: UUID, site_id: UUID | None, limit: int) -> tuple[UploadRecord, ...]:
        rows = [u for u in self.uploads if u.tenant_id == tenant_id and u.site_id == site_id]
        rows.sort(key=lambda u: (u.submitted_at, str(u.id)), reverse=True)
        return tuple(self._record(u) for u in rows[:limit])

    def stored_strings(self) -> list[str]:
        """Every string of every stored row (uploads, decisions, intakes, records, revisions, rejections)."""
        out: list[str] = []

        def walk(value) -> None:
            if isinstance(value, str):
                out.append(value)
            elif isinstance(value, (tuple, list)):
                for item in value:
                    walk(item)

        for rows in (self.uploads, self.decisions, self.intakes, self.records, self.revisions, self.rejections):
            for row in rows:
                for f in fields(row):
                    walk(getattr(row, f.name))
        return out


class Keys:
    def __init__(self, keys: dict[UUID, bytes]) -> None:
        self.keys = keys

    def key(self, tenant_id: UUID) -> bytes:
        if tenant_id not in self.keys:
            raise PseudonymKeyMissing()
        return self.keys[tenant_id]


# --- the world -----------------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def people() -> People:
    p = People()
    p.sign("amina")
    return p


def make_world(people: People, *, real_data: bool = False, keys=None) -> SimpleNamespace:
    names = {pid: name.title() for name, pid in people.ids.items()}
    store = UploadMemoryStore(names)
    store.slugs[people.acme] = "acme"
    store.slugs[people.beta] = "beta"
    store.sites[(people.acme, KOBO.lower())] = people.kobo
    store.sites[(people.acme, KISIWA.lower())] = people.kisiwa
    clock = Clock(T_SUBMIT)
    records = CommercialRecords(store, clock=clock)
    svc = CommercialUploads(records, store, keys or Keys({people.acme: KEY}), clock=clock, real_data=real_data)
    return SimpleNamespace(store=store, clock=clock, svc=svc, records=records, tid=people.acme,
                           kobo=UploadScope(people.kobo, KOBO), org=UploadScope(None, None),
                           ana=Actor(people.ids["ana"], ANALYST), fiona=Actor(people.ids["fiona"], FIN),
                           amina=Actor(people.ids["amina"], EXEC))


@pytest.fixture()
def w(people) -> SimpleNamespace:
    return make_world(people)


# --- batches (spec §6 "Data") --------------------------------------------------------------------------------------

def envelope(records: list[dict], *, source_type: str, source_system: str, provenance: str = "source-emulated",
             tenant: str = "acme") -> dict:
    return {"format_version": 1, "tenant_code": tenant, "source_type": source_type, "source_system": source_system,
            "provenance": provenance, "produced_at": "2026-11-05T09:00:00+03:00", "records": records}


def charge(rid: str = "KOBO-CH-0001", version: str = "1", *, site: str = KOBO, value: str = "120.00") -> dict:
    return {"format_version": 1, "kind": "CHARGE", "source_record_id": rid, "source_version": version,
            "site_code": site, "subject": {"kind": "CUSTOMER", "ref": "C-0412"},
            "clocks": {"effective_from": "2026-10-01", "effective_to": "2026-11-01", "recognition_period": "2026-10"},
            "amount": {"value": value, "currency": "USD"}, "quantity": {"value": "400", "unit": "kWh"},
            "body": {"account_ref": "C-0412", "line_type": "USAGE", "tariff_code": "T-RES"}}


def receipt(rid: str = "KOBO-RC-0001", *, payer: str = "C-0412") -> dict:
    return {"format_version": 1, "kind": "RECEIPT", "source_record_id": rid, "source_version": "1",
            "site_code": KOBO, "subject": {"kind": "CUSTOMER", "ref": "C-0412"},
            "clocks": {"occurred_at": "2026-10-30T19:00:00+03:00", "recognition_period": "2026-10"},
            "amount": {"value": "100.00", "currency": "USD"}, "status": "COLLECTED",
            "body": {"payer_ref": payer, "method": "MOBILE_MONEY"}}


def expense(rid: str = "KOBO-EX-OM-1029", version: str = "1", *, value: str = "95.00", category: str = "OM",
            counterparty: str = "SUP-OM") -> dict:
    record = {"format_version": 1, "kind": "EXPENSE", "source_record_id": rid, "source_version": version,
              "site_code": KOBO, "clocks": {"occurred_at": "2026-10-29T10:00:00+03:00", "recognition_period": "2026-10"},
              "amount": {"value": value, "currency": "USD"}, "status": "INVOICED",
              "body": {"counterparty_ref": counterparty, "category": category, "document_ref": "INV-OM-1029"}}
    if category == "FUEL":
        record["quantity"] = {"value": "76", "unit": "L"}
    return record


def budget_line(rid: str, factor: str, value: str, site: str | None) -> dict:
    record = {"format_version": 1, "kind": "BUDGET_LINE", "source_record_id": rid, "source_version": "1",
              "site_code": site, "clocks": {"recognition_period": "2026-10"},
              "body": {"factor_id": factor, "value": value, "currency": "USD", "version_ref": "budget-2026-v1"}}
    if site is None:
        del record["site_code"]
    return record


def encode(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


def b_bill(**kw) -> dict:
    return envelope([charge(), receipt()], source_type="billing_export", source_system="kobo-vending", **kw)


def b_late(version: str = "1", value: str = "95.00") -> dict:
    return envelope([expense(version=version, value=value)], source_type="expense_ledger",
                    source_system="lakeside-accounts")


def b_mixed() -> dict:
    bad = charge("KOBO-CH-0009", value="12,5")
    return envelope([charge(), receipt(), charge("KISIWA-CH-0001", site=KISIWA), bad], source_type="billing_export",
                    source_system="kobo-vending")


def b_budget() -> dict:
    return envelope([budget_line("BUD-2026-10:KOBO-001:diesel_price", "diesel_price", "1.25", KOBO),
                     budget_line("BUD-2026-10:staff", "staff", "1200.00", None)],
                    source_type="budget_workbook", source_system="lakeside-budget-2026")


def counts(answer: dict) -> tuple[int, int, int, int, int]:
    c = answer["counts"] if "counts" in answer else answer["preview"]
    return c["records"], c["new"], c["revised"], c["unchanged"], c["refused"]


def refusal_rows(answer: dict) -> list[tuple[int, str, str]]:
    return [(r["row"], r["code"], r["field"]) for r in answer["refusals"]]


def refused(call) -> UploadRefused:
    with pytest.raises(UploadRefused) as raised:
        call()
    return raised.value


def submit(w, obj, scope=None, actor=None, name="kobo-billing-2026-10.json") -> dict:
    return w.svc.submit(w.tid, scope or w.kobo, actor or w.ana, encode(obj), file_name=name)


def accept(w, upload: dict, scope=None, actor=None) -> dict:
    return w.svc.decide(w.tid, scope or w.kobo, actor or w.fiona, upload["upload_id"], "ACCEPT")


def store_rows(w) -> tuple[int, ...]:
    return (*w.store.counts(), len(w.store.uploads), len(w.store.decisions))


# --- 1, 2: check, submit, accept -----------------------------------------------------------------------------------

def test_1_check_writes_nothing(w) -> None:
    answer = w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill()))
    assert answer["state"] == "CHECKED" and counts(answer) == (2, 2, 0, 0, 0)
    assert answer["months"] == [{"site_code": KOBO, "period": "2026-10"}]
    assert answer["words"] == message("commercial_upload.state.checked") and answer["text"] == render(answer["words"])
    assert store_rows(w) == (0, 0, 0, 0, 0, 0)


@pytest.mark.parametrize("submitter, decider", [("ana", "fiona"), ("fiona", "fiona")])
def test_2_submit_then_accept(people, submitter, decider) -> None:
    w = make_world(people)
    preview = w.svc.check(w.tid, w.kobo, getattr(w, submitter), encode(b_bill()))
    upload = submit(w, b_bill(), actor=getattr(w, submitter))
    assert upload["state"] == "WAITING" and upload["result"] is None
    assert store_rows(w) == (0, 0, 0, 0, 1, 0)  # D-3A2.4: nothing in the commercial store before acceptance
    done = accept(w, upload, actor=getattr(w, decider))
    assert done["state"] == "ACCEPTED"
    assert store_rows(w) == (1, 2, 2, 0, 1, 1)
    decision, intake = w.store.decisions[0], w.store.intakes[0]
    assert decision.decision == "ACCEPTED" and decision.intake_id == intake.id
    assert decision.decided_by == people.ids[decider] and w.store.uploads[0].submitted_by == people.ids[submitter]
    assert intake.state == "STORED" and intake.entered_by == f"person:{people.ids[decider]}"
    assert {r.source_record_id for r in w.store.latest_revisions(w.tid)} == {"KOBO-CH-0001", "KOBO-RC-0001"}
    assert done["result"]["counts"] == preview["counts"] == done["preview"]
    assert done["submitted_by"]["display_name"] == submitter.title()
    assert done["decision"]["by"] == {"person_id": str(people.ids[decider]), "display_name": decider.title()}
    assert done["text"] == f"Accepted by {decider.title()}."


# --- 3, 4, 5: pseudonyms and refused records -----------------------------------------------------------------------

def test_3_pseudonyms_before_anything_is_kept(w) -> None:
    upload = submit(w, b_bill())
    accept(w, upload)
    by_id = {r.source_record_id: json.loads(r.canonical) for r in w.store.revisions}
    assert by_id["KOBO-CH-0001"]["subject"]["ref"] == C_0412
    assert by_id["KOBO-CH-0001"]["body"]["account_ref"] == C_0412
    assert by_id["KOBO-RC-0001"]["body"]["payer_ref"] == C_0412
    assert by_id["KOBO-RC-0001"]["subject"]["ref"] == C_0412


def test_3_no_stored_string_or_error_holds_a_raw_ref(people) -> None:
    w = make_world(people)
    errors: list[str] = []
    mixed = submit(w, b_mixed())
    assert w.store.uploads[0].kept_index == (0, 1, 2)
    accept(w, mixed)
    bad = envelope([receipt("KOBO-RC-0002", payer=" C-0412"), receipt("KOBO-RC-0003")],
                   source_type="billing_export", source_system="kobo-vending")
    accept(w, submit(w, bad))
    for call in (lambda: submit(w, b_mixed()), lambda: w.svc.check(w.tid, w.org, w.ana, encode(b_bill(tenant="beta")))):
        error = refused(call)
        errors += [str(error), repr(error), json.dumps(error.params), json.dumps(error.words)]
    strings = w.store.stored_strings()
    assert len(w.store.uploads) == 2 and len(w.store.rejections) == 1 and strings
    assert not [s for s in strings + errors if "C-0412" in s]
    decoded = json.loads(w.store.uploads[0].batch)
    assert [r["source_record_id"] for r in decoded["records"]] == ["KOBO-CH-0001", "KOBO-RC-0001", "KISIWA-CH-0001"]


def test_4_goldens_and_the_expense_categories() -> None:
    meter = {"kind": "CUSTOMER_METER_READ", "subject": {"kind": "METER", "ref": "MT-2201"},
             "body": {"meter_ref": "MT-2201"}}
    out = pseudonymise(meter, KEY)
    assert out["subject"]["ref"] == out["body"]["meter_ref"] == M_MT2201
    assert meter["subject"]["ref"] == "MT-2201"  # the input is not mutated
    for category, expected in (("STAFF", P_JOSEPH), ("COLLECTION", P_JOSEPH), ("FUEL", "P-JOSEPH"),
                               ("HANDLING", "P-JOSEPH")):
        record = expense(category=category, counterparty="P-JOSEPH")
        assert pseudonymise(record, KEY)["body"]["counterparty_ref"] == expected, category


def _hm(cls: str, raw: str) -> str:
    """The spec §3.4 formula, written out here so the test does not call the code under test."""
    import hashlib
    import hmac
    return f"{cls}-" + hmac.new(KEY, f"{cls}\x1f{raw}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _rec(kind: str, subject_kind: str | None = None, subject_ref: str | None = None, **body) -> dict:
    out: dict = {"kind": kind, "other": "KEEP-ME", "body": {"note": "KEEP-ME", **body}}
    if subject_kind is not None:
        out["subject"] = {"kind": subject_kind, "ref": subject_ref}
    return out


#: (row label, record, [(path, class)] that must change, [path] that must stay raw), one case per spec §3.4 row/condition.
_TABLE = [
    ("CHARGE customer", _rec("CHARGE", "CUSTOMER", "R-SUBJ", account_ref="R-ACC"),
     [("subject.ref", "C"), ("body.account_ref", "C")], []),
    ("CHARGE meter", _rec("CHARGE", "METER", "R-SUBJ", account_ref="R-ACC"),
     [("subject.ref", "M"), ("body.account_ref", "C")], []),
    ("CHARGE site stays raw", _rec("CHARGE", "SITE", "R-SUBJ", account_ref="R-ACC"),
     [("body.account_ref", "C")], ["subject.ref"]),
    ("RECEIPT", _rec("RECEIPT", "CUSTOMER", "R-SUBJ", payer_ref="R-PAY"),
     [("subject.ref", "C"), ("body.payer_ref", "C")], []),
    ("ADJUSTMENT customer", _rec("ADJUSTMENT", "CUSTOMER", "R-SUBJ", authorised_by_ref="R-AUTH"),
     [("subject.ref", "C"), ("body.authorised_by_ref", "P")], []),
    ("ADJUSTMENT meter", _rec("ADJUSTMENT", "METER", "R-SUBJ", authorised_by_ref="R-AUTH"),
     [("subject.ref", "M"), ("body.authorised_by_ref", "P")], []),
    ("ADJUSTMENT site stays raw", _rec("ADJUSTMENT", "SITE", "R-SUBJ", authorised_by_ref="R-AUTH"),
     [("body.authorised_by_ref", "P")], ["subject.ref"]),
    ("EXPENSE staff", _rec("EXPENSE", category="STAFF", counterparty_ref="R-CP"),
     [("body.counterparty_ref", "P")], []),
    ("EXPENSE collection", _rec("EXPENSE", category="COLLECTION", counterparty_ref="R-CP"),
     [("body.counterparty_ref", "P")], []),
    ("EXPENSE fuel stays raw", _rec("EXPENSE", category="FUEL", counterparty_ref="R-CP"),
     [], ["body.counterparty_ref"]),
    ("STORAGE_MOVEMENT", _rec("STORAGE_MOVEMENT", customer_ref="R-CUST"), [("body.customer_ref", "C")], []),
    ("CUSTOMER_METER_READ", _rec("CUSTOMER_METER_READ", "METER", "R-SUBJ", meter_ref="R-MT"),
     [("subject.ref", "M"), ("body.meter_ref", "M")], []),
    ("METER_ASSIGNMENT", _rec("METER_ASSIGNMENT", "METER", "R-SUBJ", meter_ref="R-MT", customer_ref="R-CUST"),
     [("subject.ref", "M"), ("body.meter_ref", "M"), ("body.customer_ref", "C")], []),
    ("FLEET_ROSTER", _rec("FLEET_ROSTER", tag_ref="R-TAG"), [("body.tag_ref", "P")], []),
    ("all others", _rec("BUDGET_LINE", "SITE", "R-SUBJ", customer_ref="R-CUST", meter_ref="R-MT"),
     [], ["subject.ref", "body.customer_ref", "body.meter_ref"]),
]


def _at(obj: dict, path: str):
    for part in path.split("."):
        obj = obj[part]
    return obj


@pytest.mark.parametrize("label,record,changed,raw", _TABLE, ids=[t[0] for t in _TABLE])
def test_3b_every_pseudonymisation_row(label, record, changed, raw) -> None:
    before = json.loads(json.dumps(record))
    out = pseudonymise(record, KEY)
    assert record == before  # not mutated
    for path, cls in changed:
        assert _at(out, path) == _hm(cls, _at(before, path)), (label, path)
        assert _at(out, path) != _at(before, path)
    for path in raw:
        assert _at(out, path) == _at(before, path), (label, path)
    assert out["other"] == "KEEP-ME" and out["body"]["note"] == "KEEP-ME"  # a field outside the table stays raw


def test_5_a_refused_record_keeps_its_own_code(w) -> None:
    bad = envelope([receipt(payer=" C-0412"), charge()], source_type="billing_export", source_system="kobo-vending")
    answer = w.svc.check(w.tid, w.kobo, w.ana, encode(bad))
    assert [(r["code"], r["row"], r["field"]) for r in answer["refusals"]] == [
        ("CANONICAL_REF", 1, "body.payer_ref")]
    assert counts(answer) == (2, 1, 0, 0, 1)
    submit(w, bad)
    row = w.store.uploads[0]
    assert row.refusal_path == ("record.body.payer_ref",) and row.kept_index == (1,)
    assert "KOBO-RC-0001" not in row.batch and "C-0412" not in row.batch


# --- 6, 7, 8, 9: repeats, late records, Site scope -----------------------------------------------------------------

def test_6_the_same_file_twice_is_nothing_new(w) -> None:
    accept(w, submit(w, b_bill()))
    error = refused(lambda: submit(w, b_bill()))
    assert (error.status, error.code) == (422, "UPLOAD_NOTHING_NEW")
    assert counts(w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill()))) == (2, 0, 0, 2, 0)


def test_7_a_late_record_lands_in_its_own_month(w) -> None:
    preview = w.svc.check(w.tid, w.kobo, w.ana, encode(b_late()))
    assert preview["months"] == [{"site_code": KOBO, "period": "2026-10"}]
    accept(w, submit(w, b_late()))
    first = w.store.latest_revisions(w.tid)[0]
    assert first.recognition_period == "2026-10" and first.amount == 95
    v2 = w.svc.check(w.tid, w.kobo, w.ana, encode(b_late("2", "98.00")))
    assert counts(v2) == (1, 0, 1, 0, 0)
    accept(w, submit(w, b_late("2", "98.00")))
    latest = w.store.latest_revisions(w.tid)
    assert len(latest) == 1 and latest[0].amount == 98 and latest[0].supersedes_revision_id == first.id


def test_8_a_refused_row_never_sinks_its_file(w) -> None:
    answer = w.svc.check(w.tid, w.kobo, w.ana, encode(b_mixed()))
    assert refusal_rows(answer) == [(3, "INTAKE_SITE_NOT_THIS_SITE", "site_code"),
                                    (4, "CANONICAL_NUMBER", "amount.value")]
    assert counts(answer) == (4, 2, 0, 0, 2) and answer["refusals_total"] == 2
    assert answer["refusals"][0]["text"] == ("Row 3, site_code: this row is for another Site; send it from that Site "
                                             "or from the organisation.")


def test_9_budget_lines_by_path(w) -> None:
    kobo = w.svc.check(w.tid, w.kobo, w.ana, encode(b_budget()))
    assert refusal_rows(kobo) == [(2, "INTAKE_SITE_NOT_THIS_SITE", "site_code")] and counts(kobo) == (2, 1, 0, 0, 1)
    org = w.svc.check(w.tid, w.org, w.ana, encode(b_budget()))
    assert counts(org) == (2, 2, 0, 0, 0)
    assert org["months"] == [{"site_code": None, "period": "2026-10"}, {"site_code": KOBO, "period": "2026-10"}]


# --- 10, 11, 12, 13, 14: provenance, decline, the lock, keys, tenant ---------------------------------------------

def test_10_provenance_cap(people) -> None:
    off, on = make_world(people), make_world(people, real_data=True)
    observed = encode(b_bill(provenance="observed-financial"))
    error = refused(lambda: off.svc.check(off.tid, off.kobo, off.ana, observed))
    assert (error.status, error.code, error.params) == (422, "UPLOAD_PROVENANCE_NOT_ALLOWED",
                                                        {"provenance": "observed-financial"})
    assert counts(off.svc.check(off.tid, off.kobo, off.ana, encode(b_bill(provenance="demo-simulated"))))[1] == 2
    for provenance in ("source-emulated", "demo-simulated", "bench-tested", "field-integrated"):
        error = refused(lambda: on.svc.check(on.tid, on.kobo, on.ana, encode(b_bill(provenance=provenance))))
        assert error.code == "UPLOAD_PROVENANCE_NOT_ALLOWED", provenance
    assert counts(on.svc.check(on.tid, on.kobo, on.ana, observed))[1] == 2


def test_11_decline(w) -> None:
    upload = submit(w, b_bill())
    for reason in (None, "", "   ", "x" * 501, 5, "x\u0000y", "a\nb", "a\x7fb", "\x1bx"):
        error = refused(lambda: w.svc.decide(w.tid, w.kobo, w.fiona, upload["upload_id"], "DECLINE", reason))
        assert (error.code, error.params) == ("UPLOAD_DECISION_INVALID", {"field": "reason"})
    error = refused(lambda: w.svc.decide(w.tid, w.kobo, w.fiona, upload["upload_id"], "ACCEPT", "why"))
    assert error.params == {"field": "reason"}
    done = w.svc.decide(w.tid, w.kobo, w.fiona, upload["upload_id"], "DECLINE", "  Wrong month.  ")
    assert done["state"] == "DECLINED" and done["decision"]["reason"] == "Wrong month."
    assert done["text"] == "Declined by Fiona: Wrong month."
    assert store_rows(w) == (0, 0, 0, 0, 1, 1)
    error = refused(lambda: accept(w, upload))
    assert (error.status, error.code) == (409, "UPLOAD_ALREADY_DECIDED")


def test_11b_another_scope_or_tenant_is_not_found(w, people) -> None:
    kisiwa = UploadScope(people.kisiwa, KISIWA)
    kobo_up = submit(w, b_bill())
    kisiwa_up = w.svc.submit(w.tid, kisiwa, w.ana, encode(envelope(
        [charge("KISIWA-CH-0001", site=KISIWA)], source_type="billing_export", source_system="kobo-vending")),
        file_name="k.json")
    org_up = w.svc.submit(w.tid, w.org, w.ana, encode(b_budget()), file_name="b.json")
    ids = [kobo_up["upload_id"], kisiwa_up["upload_id"], org_up["upload_id"]]
    scopes = [w.kobo, kisiwa, w.org]
    unknown = refused(lambda: w.svc.get(w.tid, w.kobo, str(uuid4())))
    for i, scope in enumerate(scopes):
        for j, upload_id in enumerate(ids):
            if i == j:
                assert w.svc.get(w.tid, scope, upload_id)["upload_id"] == upload_id
                continue
            for call in (lambda: w.svc.get(w.tid, scope, upload_id),
                         lambda: w.svc.decide(w.tid, scope, w.fiona, upload_id, "ACCEPT")):
                error = refused(call)
                assert (error.status, error.code, error.params, error.words) == (
                    unknown.status, "UPLOAD_NOT_FOUND", unknown.params, unknown.words), (i, j)
    for scope in scopes:  # another tenant's real ID
        for upload_id in ids:
            assert refused(lambda: w.svc.get(people.beta, scope, upload_id)).code == "UPLOAD_NOT_FOUND"
    assert store_rows(w)[-1] == 0  # no decision was written by any refused attempt


def test_12_a_decision_between_the_outside_check_and_the_lock(w) -> None:
    upload = submit(w, b_bill())
    upload_id = UUID(upload["upload_id"])

    def sneak() -> None:
        w.store.on_lock = None
        w.store.decisions.append(UploadDecisionRow(uuid4(), w.tid, upload_id, "DECLINED", "x", None,
                                                   w.amina.person_id, EXEC, T_SUBMIT))

    w.store.on_lock = sneak
    error = refused(lambda: accept(w, upload))
    assert (error.status, error.code) == (409, "UPLOAD_ALREADY_DECIDED")
    assert store_rows(w) == (0, 0, 0, 0, 1, 1)


def test_13_keys(people, tmp_path) -> None:
    missing = make_world(people, keys=Keys({}))
    error = refused(lambda: missing.svc.check(missing.tid, missing.kobo, missing.ana, encode(b_bill())))
    assert (error.status, error.code) == (409, "PSEUDONYM_KEY_MISSING")
    good, tid = tmp_path / "good", people.acme
    good.mkdir()
    (good / "real.key").write_bytes(KEY)
    os.chmod(good / "real.key", 0o600)
    cases = {}
    for name in ("short", "loose", "link"):
        directory = tmp_path / name
        directory.mkdir()
        path = directory / f"{tid}.key"
        if name == "short":
            path.write_bytes(KEY[:31])
            os.chmod(path, 0o600)
        elif name == "loose":
            path.write_bytes(KEY)
            os.chmod(path, 0o644)
        else:
            os.symlink(good / "real.key", path)
        cases[name] = FileKeyStore(directory)
    for name, keys in cases.items():
        world = make_world(people, keys=keys)
        error = refused(lambda: world.svc.check(world.tid, world.kobo, world.ana, encode(b_bill())))
        assert (error.status, error.code) == (503, "PSEUDONYM_KEY_UNUSABLE"), name
    os.symlink(good / "real.key", good / f"{tid}.key")
    with pytest.raises(PseudonymKeyUnusable):
        FileKeyStore(good).key(tid)
    os.unlink(good / f"{tid}.key")
    os.rename(good / "real.key", good / f"{tid}.key")
    assert FileKeyStore(good).key(tid) == KEY
    with pytest.raises(PseudonymKeyMissing):
        FileKeyStore(tmp_path / "short").key(uuid4())


def test_14_another_tenants_file(w) -> None:
    error = refused(lambda: w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill(tenant="beta"))))
    assert (error.status, error.code) == (422, "UPLOAD_TENANT_MISMATCH")


# --- 15, 16, 17: words, reader paths, the key command -------------------------------------------------------------

def test_15_every_code_is_worded() -> None:
    for code in CANONICAL_CODES + INTAKE_CODES:
        words = render(message(f"commercial_upload.reason.{code.lower()}"))
        assert words and words.endswith("."), code
    assert render(message("commercial_upload.row_refused", row=3, field="site_code",
                          reason=render(message("commercial_upload.reason.intake_site_not_this_site")))) == (
        "Row 3, site_code: this row is for another Site; send it from that Site or from the organisation.")


class ExtraReader(CanonicalJsonReader):
    id = "canonical-json-extra"

    def __init__(self, extra: frozenset[tuple[str, str]]) -> None:
        self.extra = extra

    def read(self, data: bytes, *, context=None) -> ReadResult:
        return ReadResult(loads_canonical(data), None, self.extra)


def test_16_reader_paths(w, monkeypatch) -> None:
    for extra in ({("body.amount", "C")}, {("source_record_id", "X")}):
        with pytest.raises(ValueError):
            pseudonymise(charge(), KEY, frozenset(extra))
    monkeypatch.setattr("assetops_backend.commercial.uploads.READERS",
                        {**READERS, "canonical-json-extra": ExtraReader(frozenset({("source_record_id", "C")}))})
    call = dict(reader_id="canonical-json-extra")
    accept(w, w.svc.submit(w.tid, w.kobo, w.ana, encode(b_bill()), file_name="x.json", **call))
    stored = {r.source_record_id for r in w.store.records}
    assert "KOBO-CH-0001" not in stored and all(s.startswith("C-") and len(s) == 34 for s in stored)
    assert counts(w.svc.check(w.tid, w.kobo, w.ana, encode(b_bill()), **call)) == (2, 0, 0, 2, 0)
    assert REF_BODY_FIELDS == {f.name for s in KIND_SPECS.values() for f in s._body if f.type == "ref"}
    assert ALLOWED_EXTRA == {"source_record_id", "subject.ref"} | {f"body.{n}" for n in REF_BODY_FIELDS}


def _key_command(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "assetops_backend.commercial.pseudonym_key", *args],
                          capture_output=True, text=True, env=dict(os.environ), cwd=TREE)


def test_17_the_key_command(tmp_path) -> None:
    tid = str(uuid4())
    made = _key_command("create", "--dir", str(tmp_path), "--tenant-id", tid)
    path = tmp_path / f"{tid}.key"
    assert made.returncode == 0 and made.stdout == "" and path.stat().st_size == 32
    assert path.stat().st_mode & 0o777 == 0o600
    before = path.read_bytes()
    again = _key_command("create", "--dir", str(tmp_path), "--tenant-id", tid)
    assert again.returncode == 2 and "A key already exists for this tenant; it is never replaced." in again.stderr
    assert path.read_bytes() == before and before not in again.stderr.encode()
    gone = tmp_path / "absent"
    missing = _key_command("create", "--dir", str(gone), "--tenant-id", tid)
    assert missing.returncode == 2 and "The key directory does not exist." in missing.stderr and not gone.exists()


# --- 18: 3A1 unchanged when the keywords are unused ----------------------------------------------------------------

def test_18_ingest_without_the_new_keywords_is_3a1s(w) -> None:
    data = encode(b_bill())
    plain = w.records.ingest(w.tid, data, entered_by="service:commercial-intake", dry_run=True)
    explicit = w.records.ingest(w.tid, data, entered_by="service:commercial-intake", dry_run=True, site_scope=None,
                                acceptance=None)
    assert plain.basis_sha256 is not None and len(plain.basis_sha256) == 64
    def same(result):  # record IDs are drawn per call; everything else must match
        return replace(result, basis_sha256=None, outcomes=tuple(replace(o, record_id=None) for o in result.outcomes))

    assert same(plain) == same(explicit) and plain.basis_sha256 == explicit.basis_sha256
    assert [o.outcome for o in plain.outcomes] == ["NEW", "NEW"]
    done = w.records.ingest(w.tid, data, entered_by="service:commercial-intake")
    assert done.state == "STORED" and store_rows(w) == (1, 2, 2, 0, 0, 0)
    assert w.store.intakes[0].entered_by == "service:commercial-intake"


# --- 19, 20: the basis (D-3A2.13) ----------------------------------------------------------------------------------

def _one_charge(version: str, value: str) -> dict:
    return envelope([charge(version=version, value=value)], source_type="billing_export",
                    source_system="kobo-vending")


def test_19a_a_new_record_accepted_elsewhere_first(w) -> None:
    u1 = submit(w, _one_charge("1", "120.00"))
    assert u1["preview"]["new"] == 1
    accept(w, submit(w, _one_charge("2", "121.00")))
    before = store_rows(w)
    error = refused(lambda: accept(w, u1))
    assert (error.status, error.code) == (409, "UPLOAD_STALE")
    assert store_rows(w) == before and w.svc.get(w.tid, w.kobo, u1["upload_id"])["state"] == "WAITING"
    assert w.svc.decide(w.tid, w.kobo, w.fiona, u1["upload_id"], "DECLINE", "Superseded.")["state"] == "DECLINED"


def test_19b_a_revision_whose_counts_did_not_change(w) -> None:
    accept(w, submit(w, _one_charge("0", "119.00")))
    u1 = submit(w, _one_charge("1", "120.00"))
    assert u1["preview"]["revised"] == 1
    accept(w, submit(w, _one_charge("2", "121.00")))
    assert w.svc.check(w.tid, w.kobo, w.ana, encode(_one_charge("1", "120.00")))["counts"] == u1["preview"]
    before = store_rows(w)
    error = refused(lambda: accept(w, u1))
    assert error.code == "UPLOAD_STALE" and store_rows(w) == before


def test_20_the_tenant_slug_changed_after_submit(w) -> None:
    upload = submit(w, b_bill())
    w.store.slugs[w.tid] = "acme-renamed"
    error = refused(lambda: accept(w, upload))
    assert (error.status, error.code) == (409, "UPLOAD_STALE")
    assert store_rows(w) == (0, 0, 0, 0, 1, 0)


# --- 21, 22: the scrub sweep and the cut path ----------------------------------------------------------------------

def test_21_every_adapter_method_is_scrubbed() -> None:
    from assetops_backend.commercial.adapters.postgres_commercial_store import PostgresCommercialStore

    public = [n for n, v in vars(PostgresCommercialStore).items() if not n.startswith("_") and callable(v)]
    assert {"write_intake", "upload", "uploads_in_scope", "add_upload", "write_decline"} <= set(public)
    assert [n for n in public if getattr(getattr(PostgresCommercialStore, n), "__scrubbed__", False) is not True] == []


@pytest.mark.parametrize("key", ["John_Mwangi", "John.Mwangi"])
def test_22_a_forbidden_key_is_cut_to_its_parent(w, key) -> None:
    bad = charge("KOBO-CH-0002")
    bad["body"][key] = "x"
    obj = envelope([bad, charge()], source_type="billing_export", source_system="kobo-vending")
    answer = w.svc.check(w.tid, w.kobo, w.ana, encode(obj))
    assert refusal_rows(answer) == [(1, "CANONICAL_FORBIDDEN", "body")]
    upload = submit(w, obj)
    assert w.store.uploads[0].refusal_path == ("record.body",)
    assert "John" not in json.dumps([answer, upload, w.svc.list(w.tid, w.kobo)])
    assert not [s for s in w.store.stored_strings() if "John" in s]


def test_a_file_level_refusal_names_the_file(w) -> None:
    error = refused(lambda: w.svc.check(w.tid, w.kobo, w.ana, b'{"a": 1, "a": 2}'))
    assert (error.status, error.code, error.params) == (422, "UPLOAD_FILE_REFUSED",
                                                        {"code": "CANONICAL_DUPLICATE", "field": "the file"})
    assert render(error.words) == "This file cannot be read: the file. this appears twice."
