"""D-OPEN.1: `open_now` is an extra. When counting it fails, each Work list omits it, logs `open_now_unavailable` and
still serves the list. No database: the readers are fakes and the row selection is replaced."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from assetops_backend.work import global_index as gi
from assetops_backend.work import site_index as si

READ_AT = datetime(2026, 10, 30, 12, 0, tzinfo=timezone.utc)
FROM, TO = datetime(2026, 10, 1, tzinfo=timezone.utc), datetime(2026, 10, 8, tzinfo=timezone.utc)


class Reads:
    def __init__(self, rx) -> None:
        self.rx = rx

    def snapshot(self, *args):
        return args[-1](self.rx)


class FailingCount:
    read_at = READ_AT

    def site_name(self) -> str:
        return "Test Site"

    def eligible_cases(self, *args):
        raise RuntimeError("count failed")

    def site(self, *args):
        return self


def test_site_list_omits_open_now_logs_and_still_serves(monkeypatch, caplog) -> None:
    chosen = {"rows": [], "selection_token": "t", "linked_selection_fences": [], "source_provenance": []}
    monkeypatch.setattr(si, "select", lambda *a, **k: chosen)
    request = si.ListRequest(start=FROM, end=TO, limit=10, known_at=None, cursor=None)
    with caplog.at_level(logging.WARNING, logger="assetops_backend.work.open_now"):
        body = si.WorkIndexService(Reads(FailingCount())).read(uuid4(), uuid4(), "KOBO-001", "incidents", request,
                                                               access_basis="b")
    assert "open_now" not in body and body["rows"] == [] and body["total_count"] == 0
    assert "open_now_unavailable" in caplog.text


def test_global_list_omits_open_now_logs_and_still_serves(monkeypatch, caplog) -> None:
    monkeypatch.setenv(gi.CURSOR_KEY_ENV, "a1" * 32)
    monkeypatch.setitem(gi.SELECT, "incidents", lambda *a, **k: [])
    monkeypatch.setattr(gi, "access_basis", lambda *a, **k: "b")
    rx = FailingCount()
    rx.imported_sites = lambda tenant_id, to: [{"site_id": uuid4(), "site_code": "KOBO-001"}]
    request = gi.GlobalWorkRequest(kind="incidents", from_=FROM, to=TO, known_at=None)
    with caplog.at_level(logging.WARNING, logger="assetops_backend.work.open_now"):
        body = gi.GlobalWorkIndexService(Reads(rx)).read(uuid4(), "incidents", request, lambda code: True)
    assert "open_now" not in body and body["rows"] == [] and body["coverage"]["state"] == "COMPLETE"
    assert "open_now_unavailable" in caplog.text
