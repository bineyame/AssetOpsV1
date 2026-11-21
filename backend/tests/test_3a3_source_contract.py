"""3A3 (spec `specs/3A3-emulators-contract-test/spec.md` §2.4, §5 "Service, no database"; D-3A3.3, D-3A3.5,
D-3A3.10): the source contract suite C1 to C10 over every case of `source_contracts.CONTRACT_CASES`, and S2 to S5.

3A2's in-memory world (`UploadMemoryStore`, `People`, key `bytes(range(32))`, `T_SUBMIT`). Expected records are the
hand-written fixtures, pseudonymised here with the formula written out (W2), never by the code under test.
"""
from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
from types import MappingProxyType

import pytest

import assetops_backend.commercial.uploads as uploads_module
from assetops_backend.commercial.readers import READERS, LayoutReader, ReadResult
from assetops_backend.commercial.uploads import UploadRefused, reason_words
from assetops_backend.i18n import message, render
from assetops_contracts.canonical import SOURCE_TYPES
from assetops_contracts.native import LAYOUTS
from source_contracts import CONTRACT_CASES, ContractCase
from test_3a2_commercial_upload_service import (CANONICAL_CODES, KEY, T_SUBMIT, encode, envelope, make_world,
                                                people, receipt, refused)

__all__ = ["people"]  # the module-scoped People fixture, shared with 3A2's file

CASES = {c.reader_id: c for c in CONTRACT_CASES}
NATIVE_WORDS = {
    "NATIVE_ENCODING": "the file is not text in the character encoding this layout reads.",  # 3A6 §2.11
    "NATIVE_HEADER": "the column headings are not the ones this layout reads, in this order.",
    "NATIVE_ROW": "this row cannot be read: its cells do not line up with the headings.",
    "NATIVE_VALUE": "this value is not one this layout knows.",
    "NATIVE_CHARACTER": "this row holds a character that is not text (such as a NUL byte or an invisible mark).",
}
#: Spec §3.4's table for the kinds these layouts carry, written out: (path, class, condition).
PERSONAL = {
    "CHARGE": (("subject.ref", "C", ("subject.kind", "CUSTOMER")), ("body.account_ref", "C", None)),
    "RECEIPT": (("subject.ref", "C", None), ("body.payer_ref", "C", None)),
    "EXPENSE": (("body.counterparty_ref", "P", ("body.category", "STAFF")),),
    "BUDGET_LINE": (),
}


def _hm(cls: str, raw: str) -> str:
    return f"{cls}-" + hmac.new(KEY, f"{cls}\x1f{raw}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def _at(obj: dict, path: str):
    for part in path.split("."):
        obj = obj.get(part) if isinstance(obj, dict) else None
    return obj


def _set(obj: dict, path: str, value: str) -> None:
    *head, last = path.split(".")
    for part in head:
        obj = obj[part]
    obj[last] = value


def pseudonymised(record: dict) -> dict:
    out = json.loads(json.dumps(record))
    for path, cls, condition in PERSONAL[record["kind"]]:
        if condition is not None and _at(record, condition[0]) != condition[1]:
            continue
        if _at(record, path) is not None:
            _set(out, path, _hm(cls, _at(record, path)))
    return out


def golden(case: ContractCase) -> bytes:
    return case.golden.read_bytes()


def expected(case: ContractCase) -> list[dict]:
    return json.loads(case.expected.read_text(encoding="utf-8"))


def grid(case: ContractCase) -> list[list[str]]:
    return list(csv.reader(io.StringIO(golden(case).decode("utf-8"), newline="")))


def write(rows: list[list[str]]) -> bytes:
    out = io.StringIO()
    csv.writer(out, lineterminator="\n").writerows(rows)
    return out.getvalue().encode("utf-8")


def changed(case: ContractCase, header: str, value: str, row: int = 2) -> bytes:
    rows = grid(case)
    rows[row - 1][rows[0].index(header)] = value
    return write(rows)


def check(w, case: ContractCase, data: bytes) -> dict:
    return w.svc.check(w.tid, w.org, w.ana, data, reader_id=case.reader_id, media_type="text/csv")


def submit(w, case: ContractCase, data: bytes) -> dict:
    return w.svc.submit(w.tid, w.org, w.ana, data, file_name=f"acme.{case.reader_id}.csv", reader_id=case.reader_id,
                        media_type="text/csv")


def accept(w, upload: dict) -> dict:
    return w.svc.decide(w.tid, w.org, w.fiona, upload["upload_id"], "ACCEPT")


def refusals(answer: dict) -> list[tuple[int, str, str]]:
    return [(r["row"], r["code"], r["field"]) for r in answer["refusals"]]


def counts(answer: dict) -> tuple[int, ...]:
    c = answer["counts"] if "counts" in answer else answer["preview"]
    return c["records"], c["new"], c["revised"], c["unchanged"], c["refused"]


def stored(w) -> dict[str, dict]:
    return {r.source_record_id: json.loads(r.canonical) for r in w.store.revisions}


ids = [c.reader_id for c in CONTRACT_CASES]
parametrise = pytest.mark.parametrize("case", CONTRACT_CASES, ids=ids)


@pytest.fixture()
def w(people):
    return make_world(people)


# --- C1 to C10 -------------------------------------------------------------------------------------------------------

@parametrise
def test_c1_check_submit_accept_on_the_organisation_path(w, case) -> None:
    checked = check(w, case, golden(case))
    rows = len(grid(case)) - 1  # the golden's data rows: the record count equals them
    assert counts(checked) == (rows, rows, 0, 0, 0) and rows == len(expected(case))
    want_months = sorted({(r.get("site_code"), "2026-10") for r in expected(case)},
                         key=lambda m: (m[0] is not None, m[0] or ""))
    assert [(m["site_code"], m["period"]) for m in checked["months"]] == want_months
    upload = submit(w, case, golden(case))
    assert upload["state"] == "WAITING" and upload["scope"] == "ORGANISATION" and upload["reader"] == case.reader_id
    done = accept(w, upload)
    assert done["state"] == "ACCEPTED" and done["result"]["counts"]["new"] == 3
    want = {r["source_record_id"]: pseudonymised(r) for r in expected(case)}
    assert stored(w) == want


@parametrise
def test_c2_kinds_belong_to_the_source_type(w, case) -> None:
    accept(w, submit(w, case, golden(case)))
    kinds = SOURCE_TYPES[LAYOUTS[case.reader_id].source_type].kinds
    assert {r["kind"] for r in stored(w).values()} <= kinds and stored(w)


@pytest.mark.parametrize("case,header", [(c, h) for c in CONTRACT_CASES for h in c.required_headers],
                         ids=[f"{c.reader_id}-{h}" for c in CONTRACT_CASES for h in c.required_headers])
def test_c3_required_cell_blank_refuses_row_2_only(w, case, header) -> None:
    answer = check(w, case, changed(case, header, ""))
    field = case.field_for.get(header, header)
    [(row, code, got)] = refusals(answer)
    assert (row, got) == (2, field) and code in CANONICAL_CODES
    assert answer["refusals"][0]["text"] == f"Row 2, {field}: {render(reason_words(code))}"
    assert counts(answer) == (3, 2, 0, 0, 1)


@pytest.mark.parametrize("case,header", [(c, h) for c in CONTRACT_CASES for h in grid(c)[0] if h not in c.required_headers],
                         ids=[f"{c.reader_id}-{h}" for c in CONTRACT_CASES for h in grid(c)[0]
                              if h not in c.required_headers])
def test_c3_optional_cell_blank_keeps_row_2(w, case, header) -> None:
    """The complement: every header not listed as required is optional, so the case fully states the required cells."""
    n = len(grid(case)) - 1
    answer = check(w, case, changed(case, header, ""))
    assert refusals(answer) == [] and counts(answer) == (n, n, 0, 0, 0)


@parametrise
def test_c3_every_listed_header_is_a_header_of_the_file(case) -> None:
    assert set(case.required_headers) <= set(grid(case)[0])


@parametrise
def test_c4_number_with_comma(w, case) -> None:
    answer = check(w, case, changed(case, case.amount_header, "12,5"))
    assert refusals(answer) == [(2, "CANONICAL_NUMBER", case.amount_header)]


@parametrise
def test_c5_clock(w, case) -> None:
    answer = check(w, case, changed(case, case.clock_header, case.bad_clock))
    assert refusals(answer) == [(2, "CANONICAL_CLOCK", case.clock_header)]


@parametrise
def test_c6_idempotency_key(w, case) -> None:
    accept(w, submit(w, case, golden(case)))
    assert refused(lambda: submit(w, case, golden(case))).code == "UPLOAD_NOTHING_NEW"
    rows = grid(case)
    assert refused(lambda: submit(w, case, write([rows[0], *reversed(rows[1:])]))).code == "UPLOAD_NOTHING_NEW"
    other = changed(case, case.amount_header, "999.00")
    answer = check(w, case, other)
    assert [(r, c) for r, c, _ in refusals(answer)] == [(2, "INTAKE_VERSION_CONFLICT")]
    assert counts(answer) == (3, 0, 0, 2, 1)
    assert refused(lambda: submit(w, case, other)).code == "UPLOAD_NOTHING_NEW"
    if case.revision_header is not None:
        rows = grid(case)
        rows[1][rows[0].index(case.amount_header)] = "999.00"
        rows[1][rows[0].index(case.revision_header)] = "2"
        assert counts(check(w, case, write(rows))) == (3, 0, 1, 2, 0)


@parametrise
def test_c7_late_record_names_its_month(w, case) -> None:
    assert w.clock() == T_SUBMIT
    checked = check(w, case, golden(case))
    assert {m["period"] for m in checked["months"]} == {"2026-10"}


@parametrise
def test_c8_native_refusals_on_the_service(w, case) -> None:
    rows = grid(case)
    reordered = write([[r[1], r[0], *r[2:]] for r in rows])
    error = refused(lambda: check(w, case, reordered))
    assert (error.status, error.code, error.params) == (422, "UPLOAD_FILE_REFUSED",
                                                        {"code": "NATIVE_HEADER", "field": "the file"})
    # A case with no mapped cell is allowed only where the layout maps nothing: admission is never vacuous.
    assert (case.mapped is None) == (not any(c.maps for c in LAYOUTS[case.reader_id].columns))
    n = len(rows) - 1
    short = [r[:] for r in rows]
    short[2] = short[2][:-1]
    answer = check(w, case, write(short))
    assert refusals(answer) == [(3, "NATIVE_ROW", "row 3")] and counts(answer) == (n, n - 1, 0, 0, 1)
    assert answer["refusals"][0]["text"] == f"Row 3, row 3: {NATIVE_WORDS['NATIVE_ROW']}"
    nul = [r[:] for r in rows]
    nul[2][-1] = "a\x00b"
    answer = check(w, case, write(nul))
    assert refusals(answer) == [(3, "NATIVE_CHARACTER", "row 3")] and counts(answer) == (n, n - 1, 0, 0, 1)
    assert answer["refusals"][0]["text"] == f"Row 3, row 3: {NATIVE_WORDS['NATIVE_CHARACTER']}"
    if case.mapped is not None:
        header, value = case.mapped
        answer = check(w, case, changed(case, header, value))
        assert refusals(answer) == [(2, "NATIVE_VALUE", header)]
        assert answer["refusals"][0]["text"] == f"Row 2, {header}: this value is not one this layout knows."


def test_c8_unclosed_quote_refuses_the_file_at_its_last_line(w) -> None:
    case = CASES["collections-illustrative-1"]
    lines = golden(case).decode("utf-8").split("\n")
    lines[2] = '"MM-0002' + lines[2][len("MM-0002"):]
    data = "\n".join(lines).encode("utf-8")
    assert data.count(b"\n") == 4
    error = refused(lambda: check(w, case, data))
    assert (error.status, error.code, error.params) == (422, "UPLOAD_FILE_REFUSED",
                                                        {"code": "NATIVE_ROW", "field": "row 4"})


@parametrise
def test_c9_no_raw_personal_value_stored_or_answered(w, case) -> None:
    answers = [check(w, case, golden(case))]
    upload = submit(w, case, golden(case))
    answers += [upload, accept(w, upload)]
    blank = changed(case, case.required_headers[0], "", row=3)
    answers.append(check(w, case, blank))
    second = submit(w, case, changed(case, case.required_headers[0], "NEW-0001"))  # one new record ID
    answers += [second, accept(w, second), w.svc.list(w.tid, w.org)]
    text = json.dumps(answers, default=str) + "\n".join(w.store.stored_strings())
    assert w.store.uploads and w.store.revisions
    for raw in case.personal_raw:
        assert raw not in text, raw


@parametrise
def test_c10_provenance_follows_the_database(people, case) -> None:
    emulated = make_world(people)
    accept(emulated, submit(emulated, case, golden(case)))
    assert emulated.store.uploads[0].provenance == "source-emulated"
    assert {r.provenance for r in emulated.store.revisions} == {"source-emulated"}
    real = make_world(people, real_data=True)
    done = accept(real, submit(real, case, golden(case)))
    assert done["state"] == "ACCEPTED" and real.store.uploads[0].provenance == "observed-financial"
    assert {r.provenance for r in real.store.revisions} == {"observed-financial"}


def test_c10_canonical_reader_keeps_the_cap(people) -> None:
    real = make_world(people, real_data=True)
    batch = envelope([receipt()], source_type="mobile_money_statement", source_system="kobo-mm")
    error = refused(lambda: real.svc.check(real.tid, real.org, real.ana, encode(batch)))
    assert (error.status, error.code) == (422, "UPLOAD_PROVENANCE_NOT_ALLOWED")


# --- S2 to S5 --------------------------------------------------------------------------------------------------------

def test_s2_every_reader_has_a_contract_case() -> None:
    assert set(READERS) == {"canonical-json-v1"} | {c.reader_id for c in CONTRACT_CASES}
    assert len(CASES) == len(CONTRACT_CASES)


def test_s3_native_words_and_labels() -> None:
    for code, words in NATIVE_WORDS.items():
        assert render(reason_words(code)) == words
        assert render(message(f"commercial_upload.reason.{code.lower()}")) == words
    reader = READERS["billing-illustrative-1"]
    assert isinstance(reader, LayoutReader)
    assert [reader.field_label(p) for p in ("row.7", "record.amount.value", "record.kind", "json")] == [
        "row 7", "Amount", "the record", "the file"]
    assert reader.field_label("record.quantity") == "kWh"


def test_s4_one_customer_one_pseudonym_across_billing_and_collections(w) -> None:
    for reader_id in ("billing-illustrative-1", "collections-illustrative-1"):
        case = CASES[reader_id]
        accept(w, submit(w, case, golden(case)))
    by_id = stored(w)
    assert by_id["INV-K-0001"]["subject"]["ref"] == by_id["MM-0001"]["body"]["payer_ref"] == _hm("C", "C-0412")


def test_s5_reader_refusal_outside_the_records_is_a_store_fault(w, monkeypatch) -> None:
    class Stub:
        id = "stub"
        media_types = frozenset({"text/csv"})

        def read(self, data, *, context):
            inner = READERS["billing-illustrative-1"].read(data, context=context)
            return ReadResult(inner.obj, inner.rows, inner.personal_paths,
                              MappingProxyType({3: ("NATIVE_ROW", "row.9")}))

        def field_label(self, path):
            return path

    monkeypatch.setattr(uploads_module, "READERS", {**READERS, "stub": Stub()})
    case = CASES["billing-illustrative-1"]
    error = refused(lambda: w.svc.check(w.tid, w.org, w.ana, golden(case), reader_id="stub", media_type="text/csv"))
    assert (error.status, error.code) == (500, "COMMERCIAL_STORE_FAULT")


def test_reader_refused_row_is_dropped_whatever_2a_said(w) -> None:
    case = CASES["expenses-illustrative-1"]
    answer = check(w, case, changed(case, "Category", "Fuel"))
    assert refusals(answer) == [(2, "NATIVE_VALUE", "Category")]
    upload = submit(w, case, changed(case, "Category", "Fuel"))
    assert w.store.uploads[0].kept_index == (1, 2) and upload["preview"]["refused"] == 1


def test_unknown_tenant_is_refused_before_reading(w) -> None:
    del w.store.slugs[w.tid]
    error = refused(lambda: w.svc.check(w.tid, w.org, w.ana, b"\xff", reader_id="billing-illustrative-1",
                                        media_type="text/csv"))
    assert (error.status, error.code) == (422, "UPLOAD_TENANT_MISMATCH")
