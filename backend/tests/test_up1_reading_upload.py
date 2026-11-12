"""UP-1 (rev 7 section 7.5, D-17N.5) no-DB tests: the reading-upload service and routes over fakes.

The checker and sender stand in for the field process (`host/reading_upload_process.py` runs the real one; the
host tests pin it). Covered: the 8 CSV codes, ALREADY_RECORDED, too large, the switch off, a Site not switched on,
an unknown Site, a dry run writes nothing, confirm records one row attributed to the entry service, Held, a gateway
outage records nothing, and the derived read states.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.i18n import LocaleMiddleware
from assetops_backend.i18n.messages import CATALOGUE
from assetops_backend.reading_upload.service import (CSV_CODES, MAX_BYTES, REFUSAL_CODES, STATES, FileRefusal,
                                                     GatewayUnavailable, Preview, Progress, ReadingUploadService,
                                                     Sent, UploadRow)
from assetops_backend.reading_upload_api import build_reading_upload_router

TENANT, KOBO, COLD = UUID(int=1), UUID(int=2), UUID(int=3)
SITES = {"KOBO-001": ("KOBO-001", TENANT, KOBO), "COLD-LAB-001": ("COLD-LAB-001", TENANT, COLD)}
ENTRY = "service:operator-entry"
P = "a" * 64
D17 = datetime(2026, 11, 17, tzinfo=timezone.utc)
URL = "/api/sites/KOBO-001/reading-uploads"


def _preview(first: datetime = D17 + timedelta(minutes=15)) -> Preview:
    return Preview(profile_sha256=P, file_sha256="b" * 64, period_start=first - timedelta(minutes=15),
                   period_end=first + timedelta(hours=10), rows=40, cells=160, readings=156, blanks=4,
                   columns=({"row_id": "pv-ac-power", "column": "pv_ac_power", "unit": "kW", "readings": 39,
                             "blanks": 1},),
                   first_interval_end_by_role={"pv_power": first, "feeder_demand": first})


class FakeChecker:
    def __init__(self, answer: Preview | FileRefusal | None = None) -> None:
        self.answer = answer or _preview()
        self.calls = 0

    def check(self, data: bytes):
        self.calls += 1
        return self.answer


class FakeSender:
    def __init__(self, answer: Sent | FileRefusal | Exception | None = None) -> None:
        self.answer = answer or Sent("field:x", 160, 0, tuple(f"m{i}" for i in range(160)))
        self.calls = 0

    def send(self, data: bytes):
        self.calls += 1
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class FakeStore:
    def __init__(self, latest: dict[str, datetime] | None = None) -> None:
        self.latest = latest or {"pv_power": D17 - timedelta(minutes=15), "feeder_demand": D17}
        self.rows: dict[UUID, UploadRow] = {}
        self.progress_of = Progress(0, False)

    def latest_accepted_by_role(self, tenant_id, site_id, roles):
        return {r: self.latest[r] for r in roles if r in self.latest}

    def insert(self, row):
        stored = replace(row, entered_at=datetime(2026, 11, 17, 10, 5, tzinfo=timezone.utc))
        self.rows[row.id] = stored
        return stored

    def get(self, tenant_id, site_id, upload_id):
        row = self.rows.get(upload_id)
        return row if row is not None and (row.tenant_id, row.site_id) == (tenant_id, site_id) else None

    def progress(self, row):
        return self.progress_of


def _client(checker=None, sender=None, store=None, sites=frozenset({"KOBO-001"}), on=True):
    checker, store = checker or FakeChecker(), store or FakeStore()
    sender = FakeSender() if sender is None else sender
    service = ReadingUploadService(checker, sender, store, entered_by=ENTRY) if on else None
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)
    app.include_router(build_reading_upload_router(service, SITES.get, sites))
    return TestClient(app), checker, sender, store


def _post(client, dry: str = "true", body: bytes = b"timestamp_utc\n", name: str = "kobo.csv", url: str = URL):
    return client.post(url, params={"dry_run": dry, "file_name": name}, content=body,
                       headers={"Content-Type": "text/csv"})


def test_every_refusal_and_state_has_words():
    en = CATALOGUE["en"]
    for code in REFUSAL_CODES:
        assert f"reading_upload.refused.{code.lower()}" in en, code
    for state in STATES[1:]:
        assert f"reading_upload.state.{state.lower()}" in en, state
    assert en["reading_upload.uploaded_by_site_admin"] == "Uploaded by site admin"


@pytest.mark.parametrize("code", CSV_CODES)
def test_each_csv_code_refuses_the_whole_file_in_plain_words(code):
    client, _, sender, store = _client(FakeChecker(FileRefusal(code, "rows[6].timestamp_utc", "detail", P)))
    answer = _post(client)
    assert answer.status_code == 422
    body = answer.json()
    assert body["code"] == code and body["state"] == "REFUSED"
    assert body["words"]["key"] == f"reading_upload.refused.{code.lower()}"
    assert body["message"].startswith("The file was not saved") and code not in body["message"]
    assert sender.calls == 0 and store.rows == {}  # a dry run writes nothing


def test_a_refused_confirm_is_recorded_and_admits_nothing():
    client, _, sender, store = _client(FakeChecker(FileRefusal("SPAN_MISMATCH", "rows[6].timestamp_utc", "d", P)))
    answer = _post(client, dry="false")
    assert answer.status_code == 422 and "Row 7" in answer.json()["message"]
    (row,) = store.rows.values()
    assert (row.state, row.refusal_code, row.admitted_count, row.message_ids, row.entered_by) == (
        "REFUSED", "SPAN_MISMATCH", 0, (), ENTRY)
    assert sender.calls == 0
    again = client.get(f"{URL}/{row.id}").json()
    assert again["state"] == "REFUSED" and again["refusal"]["code"] == "SPAN_MISMATCH"


@pytest.mark.parametrize("first", [D17 - timedelta(minutes=15), D17 - timedelta(hours=1)])
def test_already_recorded_when_an_interval_ends_at_or_before_the_latest_reading(first):
    client, _, sender, store = _client(FakeChecker(_preview(first)),
                                       store=FakeStore({"pv_power": D17 - timedelta(minutes=15)}))
    answer = _post(client, dry="false")
    body = answer.json()
    assert answer.status_code == 422 and body["code"] == "ALREADY_RECORDED"
    assert "solar" in body["message"] and "2026-11-16T23:45:00Z" in body["message"]
    assert sender.calls == 0 and [r.state for r in store.rows.values()] == ["REFUSED"]


def test_the_feeder_role_is_checked_on_its_own_latest():
    client, *_ = _client(FakeChecker(_preview(D17)))  # pv latest 23:45 passes; feeder latest 00:00 does not
    body = _post(client).json()
    assert body["code"] == "ALREADY_RECORDED" and body["refusal"]["field"] == "feeder_demand"


def test_too_large_is_413_before_the_check():
    client, checker, sender, store = _client()
    answer = _post(client, body=b"x" * (MAX_BYTES + 1))
    assert answer.status_code == 413 and answer.json()["code"] == "FILE_TOO_LARGE"
    assert checker.calls == 0 and sender.calls == 0 and store.rows == {}


def test_switch_off_by_default_is_403():
    client, *_ = _client(on=False)
    answer = _post(client)
    assert answer.status_code == 403 and answer.json()["code"] == "READING_UPLOAD_OFF"
    assert client.get(f"{URL}/{uuid4()}").json()["code"] == "READING_UPLOAD_OFF"


def test_a_site_not_switched_on_is_refused():
    client, checker, *_ = _client()
    answer = _post(client, url="/api/sites/COLD-LAB-001/reading-uploads")
    assert answer.status_code == 403 and answer.json()["code"] == "READING_UPLOAD_NOT_THIS_SITE"
    assert checker.calls == 0


def test_an_unknown_site_is_404():
    client, *_ = _client()
    answer = _post(client, url="/api/sites/NOPE-1/reading-uploads")
    assert answer.status_code == 404 and answer.json()["code"] == "SITE_NOT_FOUND"


@pytest.mark.parametrize("params", [{"file_name": "a.csv"}, {"dry_run": "yes", "file_name": "a.csv"},
                                    {"dry_run": "true"}, {"dry_run": "true", "file_name": "../a.csv"}])
def test_a_bad_request_is_422(params):
    client, checker, *_ = _client()
    answer = client.post(URL, params=params, content=b"x")
    assert answer.status_code == 422 and answer.json()["code"] == "READING_UPLOAD_BAD_REQUEST"
    assert checker.calls == 0


def test_a_dry_run_answers_the_preview_and_writes_nothing():
    client, checker, sender, store = _client()
    answer = _post(client)
    body = answer.json()
    assert answer.status_code == 200 and body["state"] == "CHECKED" and body["dry_run"] is True
    assert body["preview"]["rows"] == 40 and body["preview"]["period_start"] == "2026-11-17T00:00:00Z"
    assert "Nothing is saved" in body["text"]
    assert checker.calls == 1 and sender.calls == 0 and store.rows == {}


def test_confirm_sends_once_and_records_the_upload_as_site_admin():
    client, _, sender, store = _client()
    answer = _post(client, dry="false")
    body = answer.json()
    assert answer.status_code == 201 and body["state"] == "SENT" and body["held"] is False
    assert body["uploaded_by_text"] == "Uploaded by site admin"
    (row,) = store.rows.values()
    assert (row.state, row.entered_by, row.admitted_count, len(row.message_ids)) == ("SENT", ENTRY, 160, 160)
    assert sender.calls == 1 and body["upload_id"] == str(row.id)


def test_held_readings_are_recorded_and_said():
    sent = Sent("field:x", 120, 40, tuple(f"m{i}" for i in range(120)), {"pv-ac-power": 40})
    client, _, _, store = _client(sender=FakeSender(sent))
    body = _post(client, dry="false").json()
    assert body["held"] is True and body["held_by_column"] == {"pv-ac-power": 40}
    assert "40 readings are held" in body["text"]
    assert [r.state for r in store.rows.values()] == ["HELD"]


def test_a_gateway_outage_is_503_and_records_nothing():
    client, _, _, store = _client(sender=FakeSender(GatewayUnavailable("down")))
    answer = _post(client, dry="false")
    assert answer.status_code == 503 and answer.json()["code"] == "READING_UPLOAD_GATEWAY_UNAVAILABLE"
    assert store.rows == {}


def test_no_gateway_configured_still_allows_the_dry_run():
    store = FakeStore()
    service = ReadingUploadService(FakeChecker(), None, store, entered_by=ENTRY)
    app = FastAPI()
    app.include_router(build_reading_upload_router(service, SITES.get, frozenset({"KOBO-001"})))
    client = TestClient(app)
    assert _post(client).status_code == 200
    assert _post(client, dry="false").status_code == 503 and store.rows == {}


@pytest.mark.parametrize("progress,state", [(Progress(0, False), "SENT"), (Progress(80, False), "ACCEPTED"),
                                            (Progress(160, False), "PROCESSING"), (Progress(160, True), "ANALYSED")])
def test_the_read_derives_the_state_from_the_ledger(progress, state):
    client, _, _, store = _client()
    upload_id = _post(client, dry="false").json()["upload_id"]
    store.progress_of = progress
    body = client.get(f"{URL}/{upload_id}").json()
    assert body["state"] == state and body["counts"]["accepted"] == progress.accepted
    assert body["counts"]["accepted_of"] == 160
    if state == "ACCEPTED":
        assert body["text"] == "Accepted 80 of 160 readings."


def test_an_unknown_or_other_site_upload_is_404():
    client, _, _, store = _client(sites=frozenset({"KOBO-001", "COLD-LAB-001"}))
    upload_id = _post(client, dry="false").json()["upload_id"]
    assert client.get(f"{URL}/{uuid4()}").status_code == 404
    assert client.get(f"{URL}/not-a-uuid").status_code == 404
    assert client.get(f"/api/sites/COLD-LAB-001/reading-uploads/{upload_id}").status_code == 404


TEMPLATE = b"timestamp_utc,pv_ac_power [kW]\r\n"


def _template_client(template=lambda: TEMPLATE, sites=frozenset({"KOBO-001"}), on=True):
    service = ReadingUploadService(FakeChecker(), FakeSender(), FakeStore(), entered_by=ENTRY,
                                   template=template) if on else None
    app = FastAPI()
    app.add_middleware(LocaleMiddleware)
    app.include_router(build_reading_upload_router(service, SITES.get, sites))
    return TestClient(app)


def test_the_template_downloads_as_csv_named_for_the_site():
    answer = _template_client().get(f"{URL}/template")
    assert answer.status_code == 200 and answer.content == TEMPLATE
    assert answer.headers["content-type"].startswith("text/csv")
    assert answer.headers["content-disposition"] == 'attachment; filename="KOBO-001-readings-template.csv"'


def test_the_template_follows_the_switch_and_the_site_list():
    assert _template_client(on=False).get(f"{URL}/template").json()["code"] == "READING_UPLOAD_OFF"
    other = _template_client().get("/api/sites/COLD-LAB-001/reading-uploads/template")
    assert other.status_code == 403 and other.json()["code"] == "READING_UPLOAD_NOT_THIS_SITE"
    missing = _template_client(template=None).get(f"{URL}/template")
    assert missing.status_code == 503 and missing.json()["code"] == "READING_UPLOAD_TEMPLATE_UNAVAILABLE"


@pytest.mark.parametrize("content_type", [None, "multipart/form-data; boundary=x", "application/octet-stream"])
def test_a_body_that_is_not_text_csv_is_415(content_type):
    client, checker, sender, store = _client()
    headers = {} if content_type is None else {"Content-Type": content_type}
    answer = client.post(URL, params={"dry_run": "true", "file_name": "a.csv"}, content=b"x", headers=headers)
    assert answer.status_code == 415 and answer.json()["code"] == "READING_UPLOAD_UNSUPPORTED_TYPE"
    assert answer.json()["words"]["key"] == "reading_upload.unsupported_type"
    assert checker.calls == 0 and sender.calls == 0 and store.rows == {}
    ok = client.post(URL, params={"dry_run": "true", "file_name": "a.csv"}, content=b"x",
                     headers={"Content-Type": "text/csv; charset=utf-8"})
    assert ok.status_code != 415


def test_a_file_name_is_at_most_200_characters():
    client, *_ = _client()
    assert _post(client, name="a" * 196 + ".csv").status_code == 200
    answer = _post(client, name="a" * 197 + ".csv")
    assert answer.status_code == 422 and answer.json()["code"] == "READING_UPLOAD_BAD_REQUEST"


def test_the_bom_refusal_and_the_template_note_name_the_excel_fix():
    fix = "save as 'CSV (Comma delimited)', not 'CSV UTF-8'"
    assert fix in CATALOGUE["en"]["reading_upload.refused.encoding"]
    assert fix in CATALOGUE["en"]["reading_upload.template_note"]
