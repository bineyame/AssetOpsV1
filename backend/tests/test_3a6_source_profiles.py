"""3A6 (spec `specs/3A6-source-profiles/spec.md` §2.5, §2.6, §6 "Service, no database"; D-3A6.2 to D-3A6.16):
admitting a source profile, and uploads read through it by 3A2's intake.

`ProfileMemoryStore` subclasses (never edits) 3A2's `UploadMemoryStore` and mirrors migration 0067 (the three unique
keys refuse with the key's name) and `write_intake`'s acceptance re-check under the tenant's lock (D-3A6.15). The
people are 3C1a's (`acme`; Ana ANALYST, Fiona FINANCE). The fixtures and every expected value here are written by
hand (W2); the pseudonym below is 3A2's formula written out with `hmac`, never `pseudonymise()`.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
from dataclasses import fields, replace
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

import pytest

from assetops_backend.commercial.model import ProfileRow, StoreRefused, UploadSourceSwitched
from assetops_backend.commercial.profiles import ProfileRefused, SourceProfiles
from assetops_backend.commercial.readers import XLSX_MEDIA_TYPE
from assetops_backend.commercial.service import CommercialRecords
from assetops_backend.commercial.uploads import Actor, CommercialUploads, UploadRefused, UploadScope
from assetops_backend.i18n import render
from assetops_contracts.native import compile_profile, read_rows, run_probes, split_file
from assetops_contracts.native.layouts_v1 import NativeRead
from test_3a1_commercial_service import Clock
from test_3a2_commercial_upload_service import KEY, T_SUBMIT, Keys, UploadMemoryStore, counts, refusal_rows, refused
from test_3c1a_person_work import KISIWA, KOBO, People

F6 = Path(__file__).resolve().parent / "fixtures" / "3a6"
F3 = Path(__file__).resolve().parent / "fixtures" / "3a3"
sys.path.insert(0, str(F6))
import make_budget_xlsx as mk  # noqa: E402

FIN, ANALYST = "FINANCE_AND_COMMERCIAL_LEAD", "ANALYST"
KOBO_PROFILE = (F6 / "kobo-ledger-expenses.profile.json").read_bytes()
KOBO_SAMPLE = (F6 / "kobo-ledger-expenses.csv").read_bytes()
KOBO_EXPECTED = (F6 / "kobo-ledger-expenses.expected.json").read_bytes()
BUDGET_PROFILE = (F6 / "lakeside-budget.profile.json").read_bytes()
BUDGET_SAMPLE = (F6 / "lakeside-budget.xlsx").read_bytes()
BUDGET_EXPECTED = (F6 / "lakeside-budget.expected.json").read_bytes()
TEMPLATE = (F3 / "expenses-illustrative-1.csv").read_bytes()
V1, V2 = "profile.kobo-ledger-expenses.v1", "profile.kobo-ledger-expenses.v2"
UNIQUE = (("profile_id", "version"), ("reader",), ("profile_id", "profile_sha256"))
UNIQUE_NAMES = ("commercial_source_profile_version_key", "commercial_source_profile_reader_key",
                "commercial_source_profile_sha256_key")


# --- the in-memory store ---------------------------------------------------------------------------------------------

class ProfileMemoryStore(UploadMemoryStore):
    """3A2's store plus spec §5's profile table and the acceptance re-check under the lock (D-3A6.15)."""

    def __init__(self, names: dict[UUID, str]) -> None:
        super().__init__(names)
        self.profiles: list[ProfileRow] = []
        self.held_once = None  # U3's race: what the next `held_uploads` call returns, once

    def source_profiles_all(self, tenant_id, profile_id):
        return tuple(sorted((r for r in self.profiles if r.tenant_id == tenant_id and r.profile_id == profile_id),
                            key=lambda r: r.version))

    def source_profile_latest(self, tenant_id, profile_id):
        rows = self.source_profiles_all(tenant_id, profile_id)
        return rows[-1] if rows else None

    def source_profiles_latest(self, tenant_id):
        ids = sorted({r.profile_id for r in self.profiles if r.tenant_id == tenant_id})
        return tuple(self.source_profile_latest(tenant_id, p) for p in ids)

    def add_source_profile(self, row: ProfileRow) -> None:
        with self._guard:
            for key, name in zip(UNIQUE, UNIQUE_NAMES):
                if any(r.tenant_id == row.tenant_id and all(getattr(r, k) == getattr(row, k) for k in key)
                       for r in self.profiles):
                    raise StoreRefused(name)
            self.profiles.append(row)

    def held_uploads(self, tenant_id):
        if self.held_once is not None:
            once, self.held_once = self.held_once, None
            return once
        return super().held_uploads(tenant_id)

    def _switched(self, tenant_id: UUID, upload_id: UUID) -> str | None:
        a = next(u for u in self.uploads if u.tenant_id == tenant_id and u.id == upload_id)
        accepted = {d.upload_id for d in self.decisions if d.tenant_id == tenant_id and d.decision == "ACCEPTED"}
        systems = [b.source_system for b in self.uploads
                   if b.tenant_id == tenant_id and b.id != a.id and b.id in accepted and b.source_type == a.source_type
                   and b.source_system != a.source_system and set(a.month_site_code) & set(b.month_site_code)]
        return min(systems) if systems else None

    def write_intake(self, tenant_id, source_system, ids, decide, *, dry_run, decision=None):
        if decision is not None and not dry_run and decision.decision == "ACCEPTED":
            inner = decide

            def decide(existing):  # under the lock, after the "no decision yet" check, before deciding
                system = self._switched(tenant_id, decision.upload_id)
                if system is not None:
                    raise UploadSourceSwitched(system)
                return inner(existing)
        return super().write_intake(tenant_id, source_system, ids, decide, dry_run=dry_run, decision=decision)


@pytest.fixture(scope="module")
def people() -> People:
    return People()


def make_world(people: People, *, real_data: bool = False) -> SimpleNamespace:
    names = {pid: name.title() for name, pid in people.ids.items()}
    store = ProfileMemoryStore(names)
    store.slugs[people.acme] = "acme"
    store.sites[(people.acme, KOBO.lower())] = people.kobo
    store.sites[(people.acme, KISIWA.lower())] = people.kisiwa
    clock = Clock(T_SUBMIT)
    profiles = SourceProfiles(store, clock=clock, real_data=real_data)
    svc = CommercialUploads(CommercialRecords(store, clock=clock), store, Keys({people.acme: KEY}), clock=clock,
                            real_data=real_data, profiles=profiles)
    return SimpleNamespace(store=store, profiles=profiles, svc=svc, tid=people.acme, org=UploadScope(None, None),
                           ana=Actor(people.ids["ana"], ANALYST), fiona=Actor(people.ids["fiona"], FIN))


@pytest.fixture()
def w(people) -> SimpleNamespace:
    return make_world(people)


# --- helpers ---------------------------------------------------------------------------------------------------------

def kobo_rows(edit=None, *, drop: tuple[int, ...] = ()) -> bytes:
    """The kobo sample with `edit(physical row, cells)` applied to each data row (rows 4 to 7) and `drop`ped rows."""
    lines = KOBO_SAMPLE.decode("cp1252").split("\r\n")
    out = []
    for n, line in enumerate(lines, start=1):
        if n in drop:
            continue
        if n >= 4 and line and edit is not None:
            cells = line.split(";")
            edit(n, cells)
            line = ";".join(cells)
        out.append(line)
    return "\r\n".join(out).encode("cp1252")


def cell(header: str) -> int:
    return ["Ref", "Txn Date", "Site", "Account", "Supplier", "Phone", "Litres", "Net (USD)", "State"].index(header)


def profile_with(**changes) -> bytes:
    obj = json.loads(KOBO_PROFILE)
    obj.update(changes)
    return json.dumps(obj, indent=2).encode("utf-8")


def admit(w, profile=KOBO_PROFILE, sample=KOBO_SAMPLE, expected=KOBO_EXPECTED, actor=None) -> ProfileRow:
    return w.profiles.admit(w.tid, actor or w.ana, profile, sample, expected)


def refusal(call) -> ProfileRefused:
    with pytest.raises(ProfileRefused) as raised:
        call()
    return raised.value


def upload(w, data=KOBO_SAMPLE, reader=V1, media="text/csv", name="kobo-ledger.csv") -> dict:
    return w.svc.submit(w.tid, w.org, w.ana, data, file_name=name, reader_id=reader, media_type=media)


def accept(w, answer: dict) -> dict:
    return w.svc.decide(w.tid, w.org, w.fiona, answer["upload_id"], "ACCEPT")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- A1 to A10: admission --------------------------------------------------------------------------------------------

def test_a1_admit_then_already_admitted(w) -> None:
    row = admit(w)
    assert (row.profile_id, row.version, row.reader, row.status, row.source_type, row.source_system, row.file_format,
            row.sample_rows, row.admitted_role) == ("kobo-ledger-expenses", 1, V1, "ILLUSTRATIVE", "expense_ledger",
                                                    "lakeside-purchases-ledger", "csv", 4, ANALYST)
    assert (row.profile_sha256, row.sample_sha256, row.expected_sha256) == (
        sha(KOBO_PROFILE), sha(KOBO_SAMPLE), sha(KOBO_EXPECTED))
    assert row.profile_json == KOBO_PROFILE.decode("utf-8") and row.admitted_at == T_SUBMIT
    report = w.profiles.check(w.tid, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED)
    assert report.already == row
    assert admit(w) == row and len(w.store.profiles) == 1


def test_a2_new_version_supersedes_and_lineage_holds(w) -> None:
    admit(w)
    v2 = profile_with(personal=[["body.counterparty_ref", "P"]])
    row = admit(w, v2)
    assert (row.version, row.reader) == (2, V2)
    e = refused(lambda: upload(w, reader=V1))
    assert (e.status, e.code, e.params) == (422, "UPLOAD_READER_SUPERSEDED", {"latest": V2})
    assert render(e.words) == f"That file layout has a newer version: use {V2}."
    assert refusal(lambda: admit(w, profile_with(source_system="another-ledger"))).code == "PROFILE_LINEAGE"
    taken = refusal(lambda: admit(w, profile_with(profile_id="kobo-other")))
    assert (taken.code, taken.params) == ("PROFILE_SOURCE_SYSTEM_TAKEN", {"system": "lakeside-purchases-ledger"})


def test_a3_status_follows_the_database(people) -> None:
    real = make_world(people, real_data=True)
    assert refusal(lambda: admit(real)).code == "PROFILE_STATUS"
    emulated = make_world(people)
    assert refusal(lambda: admit(emulated, profile_with(status="PINNED"))).code == "PROFILE_STATUS"


def test_a4_sample_refusals(w) -> None:
    e = refusal(lambda: admit(w, sample=kobo_rows(drop=(6, 7))))
    assert (e.code, e.params) == ("ADMIT_SAMPLE_SIZE", {"rows": "2"})

    def litres(n, cells):
        if n == 4:
            cells[cell("Litres")] = "4OO"
    e = refusal(lambda: admit(w, sample=kobo_rows(litres)))
    assert (e.code, e.params) == ("ADMIT_SAMPLE_ROW", {"row": "4", "code": "NATIVE_FORMAT",
                                                       "path": "record.quantity.value"})
    assert render(e.words) == ("Row 4 of the sample is refused: Litres: this value is not written the way this "
                               "layout reads it (for example, a date in another order).")
    renamed = KOBO_SAMPLE.replace(b"Net (USD)", b"Net USD")
    e = refusal(lambda: admit(w, sample=renamed))
    assert (e.code, e.params) == ("ADMIT_SAMPLE_FILE", {"code": "NATIVE_HEADER"})
    e = refusal(lambda: admit(w, profile=b"\xef\xbb\xbf" + KOBO_PROFILE))
    assert (e.code, e.params) == ("PROFILE_INVALID", {"where": "json"})
    assert w.store.profiles == []


def test_a5_expected_refusals(w) -> None:
    wanted = json.loads(KOBO_EXPECTED)
    wanted[1]["amount"]["value"] = 475.0
    e = refusal(lambda: admit(w, expected=json.dumps(wanted).encode()))
    assert (e.code, e.params) == ("ADMIT_EXPECTED", {"row": "5", "where": "amount.value"})
    e = refusal(lambda: admit(w, expected=json.dumps(json.loads(KOBO_EXPECTED)[:3]).encode()))
    assert (e.code, e.params) == ("ADMIT_EXPECTED_COUNT", {"expected": "3", "records": "4"})
    assert refusal(lambda: admit(w, expected=b"\xef\xbb\xbf" + KOBO_EXPECTED)).code == "ADMIT_EXPECTED_FILE"


def _kobo_split():
    layout = compile_profile(json.loads(KOBO_PROFILE), 1)
    header, rows = split_file(layout, KOBO_SAMPLE)
    return layout, header, rows


CTX = {"tenant_code": "acme", "produced_at": "2026-11-06T09:00:00+00:00", "provenance": "source-emulated"}


def _drops_short(layout, header, rows, **kw):
    return read_rows(layout, header, [r for r in rows if len(r[1]) == len(layout.columns)], **kw)


def _admits_zwsp(layout, header, rows, **kw):
    return read_rows(layout, header, [(n, [c.replace("​", "") for c in cells]) for n, cells in rows], **kw)


def _without(code):
    def read(layout, header, rows, **kw):
        result = read_rows(layout, header, rows, **kw)
        return NativeRead(result.obj, result.rows, {k: v for k, v in result.refused.items() if v[0] != code})
    return read


def _zero_amount(layout, header, rows, **kw):
    i = cell("Net (USD)")
    return read_rows(layout, header, [(n, [("0" if j == i and c == "" else c) for j, c in enumerate(cells)])
                                      for n, cells in rows], **kw)


def _ignores_order(layout, header, rows, **kw):
    return read_rows(layout, [c.header for c in layout.columns], rows, **kw)


@pytest.mark.parametrize("read,probe", [(_drops_short, "P2"), (_admits_zwsp, "P3"), (_without("NATIVE_VALUE"), "P4"),
                                        (_without("NATIVE_FORMAT"), "P5"), (_zero_amount, "P6"),
                                        (_ignores_order, "P1")], ids=list("abcdef"))
def test_a6_probes_refuse_a_lax_engine(read, probe) -> None:
    layout, header, rows = _kobo_split()
    failed = run_probes(layout, header, rows, read=read, **CTX)
    assert failed is not None and failed[0] == probe, failed
    assert run_probes(layout, header, rows, **CTX) is None


def test_a7_personal_paths(w) -> None:
    assert admit(w, profile_with(personal=[["body.counterparty_ref", "P"]])).version == 1
    e = refusal(lambda: w.profiles.check(w.tid, profile_with(profile_id="kobo-b", source_system="b-ledger",
                                                             personal=[["amount.value", "P"]]),
                                         KOBO_SAMPLE, KOBO_EXPECTED))
    assert (e.code, e.params) == ("PROFILE_INVALID", {"where": "personal.0"})


def test_a8_nothing_of_the_sample_is_stored(w) -> None:
    row = admit(w)
    strings = [getattr(row, f.name) for f in fields(row) if isinstance(getattr(row, f.name), str)]
    assert strings and not any(v in s for s in strings for v in ("fuel-co", "STAFF-07", "0712000001"))


def test_a9_coverage(w) -> None:
    obj = json.loads(KOBO_PROFILE)
    # Mid-build Q1: the spec's literal `"Quote": "INVOICED"` is not one to one, which `check_layout` (3A3) refuses
    # at compile (`PROFILE_INVALID`); a one-to-one map with an uncovered key exercises step 4b the same way.
    obj["columns"][cell("State")]["paths"][0]["map"] = {"Invoiced": "INVOICED", "Paid": "PAID", "Quote": "DRAFT"}
    e = refusal(lambda: admit(w, json.dumps(obj).encode()))
    assert (e.code, e.params) == ("ADMIT_MAP_UNCOVERED", {"header": "State", "value": "Quote"})

    def no_litres(n, cells):
        cells[cell("Litres")] = ""
    e = refusal(lambda: admit(w, sample=kobo_rows(no_litres)))
    assert (e.code, e.params) == ("ADMIT_COLUMN_EMPTY", {"header": "Litres"})


def test_a10_ambiguity(w) -> None:
    dates = {4: "11/10/2026 09:00", 5: "12/10/2026 09:00", 6: "10/10/2026 17:00", 7: "09/10/2026 17:30"}
    amounts = {4: "500", 5: "475", 6: "1.200", 7: "450"}

    def set_dates(n, cells):
        cells[cell("Txn Date")] = dates[n]

    def set_amounts(n, cells):
        cells[cell("Net (USD)")] = amounts[n]
    assert refusal(lambda: admit(w, sample=kobo_rows(set_dates))).code == "ADMIT_DATE_AMBIGUOUS"
    assert refusal(lambda: admit(w, sample=kobo_rows(set_amounts))).code == "ADMIT_NUMBER_AMBIGUOUS"
    assert w.profiles.check(w.tid, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED).sample_rows == 4


# --- U1 to U6: uploads through the intake ------------------------------------------------------------------------------

def _pseudonym(cls: str, value: str) -> str:  # 3A2's formula, written out
    return f"{cls}-" + hmac.new(KEY, f"{cls}\x1f{value}".encode("utf-8"), hashlib.sha256).hexdigest()[:32]


def test_u1_upload_through_the_intake(w) -> None:
    admit(w)
    answer = upload(w)
    assert answer["state"] == "WAITING" and counts(answer) == (4, 4, 0, 0, 0)
    done = accept(w, answer)
    assert done["state"] == "ACCEPTED" and done["result"]["counts"]["new"] == 4
    strings = w.store.stored_strings()
    assert any(_pseudonym("P", "STAFF-07") in s for s in strings)
    assert not any("STAFF-07" in s for s in strings)
    texts = strings + [json.dumps(answer, default=str), json.dumps(done, default=str)]
    assert not any(phone in t for t in texts for phone in ("0712000001", "0712000777"))


def test_u2_budget_workbook(w) -> None:
    assert admit(w, BUDGET_PROFILE, BUDGET_SAMPLE, BUDGET_EXPECTED).file_format == "xlsx"
    reader = "profile.lakeside-budget.v1"
    answer = upload(w, BUDGET_SAMPLE, reader, XLSX_MEDIA_TYPE, "budget.xlsx")
    assert counts(answer) == (3, 3, 0, 0, 0)
    accept(w, answer)
    assert refused(lambda: upload(w, BUDGET_SAMPLE, reader, XLSX_MEDIA_TYPE, "budget.xlsx")).code == \
        "UPLOAD_NOTHING_NEW"
    rows = [(r, [(ref, t, "3421" if ref == "D2" else v) for ref, t, v in cells]) for r, cells in mk.GOLDEN_ROWS]
    changed = mk.build_workbook(rows)
    checked = w.svc.check(w.tid, w.org, w.ana, changed, reader_id=reader, media_type=XLSX_MEDIA_TYPE)
    assert counts(checked) == (3, 0, 1, 2, 0)


def _template(site: str = KOBO) -> bytes:
    return TEMPLATE.replace(b"KOBO-001", site.encode())


def test_u3_one_source_system_per_site(w, people) -> None:
    admit(w)
    accept(w, upload(w))
    for call in (lambda: w.svc.check(w.tid, w.org, w.ana, _template(), reader_id="expenses-illustrative-1",
                                     media_type="text/csv"),
                 lambda: upload(w, _template(), "expenses-illustrative-1", name="template.csv")):
        e = refused(call)
        assert (e.status, e.code, e.params) == (409, "UPLOAD_SOURCE_SWITCHED", {
            "source_type": "expense_ledger", "system": "lakeside-purchases-ledger"})
        assert render(e.words) == ("These Sites already send this kind of export from another system. Use that "
                                   "system's export, or ask for the switch to be set up.")
    assert upload(w, _template(KISIWA), "expenses-illustrative-1", name="template.csv")["state"] == "WAITING"
    # a newer version of the same profile still uploads (the rule keys on the source system, not the reader);
    # v2 is v1 reformatted, so it reads the same records
    assert admit(w, profile_with()).reader == V2
    def paid(n, cells):
        if n == 4:
            cells[cell("State")] = "Paid"
    assert counts(upload(w, kobo_rows(paid), V2)) == (4, 0, 1, 3, 0)

    declined = make_world(people)
    admit(declined)
    template = upload(declined, _template(), "expenses-illustrative-1", name="template.csv")
    declined.svc.decide(declined.tid, declined.org, declined.fiona, template["upload_id"], "DECLINE", "wrong file")
    assert upload(declined, KOBO_SAMPLE)["state"] == "WAITING"


def test_u3_race_is_refused_at_acceptance_under_the_lock(people) -> None:
    w = make_world(people)
    admit(w)
    template = upload(w, _template(), "expenses-illustrative-1", name="template.csv")
    w.store.held_once = ()  # the concurrent submit that passed its check first
    profile_upload = upload(w)
    assert accept(w, profile_upload)["state"] == "ACCEPTED"
    e = refused(lambda: accept(w, template))
    assert (e.status, e.code, e.params) == (409, "UPLOAD_SOURCE_SWITCHED", {
        "source_type": "expense_ledger", "system": "lakeside-purchases-ledger"})
    assert w.svc.get(w.tid, w.org, template["upload_id"])["state"] == "WAITING"


def test_u4_unknown_tampered_and_media_type(w) -> None:
    e = refused(lambda: upload(w, reader="profile.nope.v1"))
    assert (e.status, e.code) == (422, "UPLOAD_READER_UNKNOWN")
    row = admit(w)
    assert refused(lambda: upload(w, media=XLSX_MEDIA_TYPE)).status == 415
    w.store.profiles[0] = replace(row, profile_json=row.profile_json.replace("Net (USD)", "Net (EUR)"))
    e = refused(lambda: upload(w))
    assert (e.status, e.code) == (500, "COMMERCIAL_STORE_FAULT")


def test_u5_field_labels_and_stored_reader(w) -> None:
    admit(w)
    reader = w.profiles.reader(w.tid, V1)
    assert reader.field_label("record.amount.value") == "Net (USD)" and reader.field_label("row.6") == "row 6"

    def bad_amount(n, cells):
        if n == 5:
            cells[cell("Net (USD)")] = "4.75,00,0"
    answer = upload(w, kobo_rows(bad_amount))
    assert refusal_rows(answer) == [(5, "NATIVE_FORMAT", "Net (USD)")]
    admit(w, profile_with(personal=[["body.counterparty_ref", "P"]]))
    assert refusal_rows(w.svc.get(w.tid, w.org, answer["upload_id"])) == [(5, "NATIVE_FORMAT", "Net (USD)")]


def test_u6_corrections_flow(w) -> None:
    admit(w)
    accept(w, upload(w))

    def paid(n, cells):
        if n == 4:
            cells[cell("State")] = "Paid"
    checked = w.svc.check(w.tid, w.org, w.ana, kobo_rows(paid), reader_id=V1, media_type="text/csv")
    assert counts(checked) == (4, 0, 1, 3, 0)
