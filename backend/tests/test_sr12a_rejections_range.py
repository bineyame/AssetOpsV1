"""SR-12a (rev 10b.4, D-SR.34/39): Site Evidence rejections over the date range, no database.

`GET /api/sites/{site}/evidence/rejections` takes optional `from`/`to` (both or neither, else 422 `INVALID_WINDOW`).
The imported-reads path passes the window to the ledger read; with none, the ledger read is called as before. The
file-backed read keeps the rejections and conflicts received in `[from, to)`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads, ImportedScope
from assetops_backend.evidence.read_model import EvidenceReadModel
from assetops_backend.evidence_api import build_evidence_router

SCOPE = ImportedScope("KOBO-001", UUID(int=1), UUID(int=2), None)
FROM, TO = "2026-10-05T00:00:00Z", "2026-10-12T00:00:00Z"


def at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


class _Reads:
    """The imported-reads seam the router calls (scope, then rejections)."""

    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def scope(self, site_id):
        return SCOPE if site_id == "KOBO-001" else None

    def rejections(self, scope, batch, window=None):
        self.calls.append((scope.site_code, batch, window))
        return {"store": "POSTGRES", "site_id": scope.site_code, "total": 0, "rejections": [], "conflicts": [],
                "duplicates": []}


class _NoSites:
    def get_site(self, site_id):  # pragma: no cover - the imported Site never reaches the legacy path
        raise AssertionError(site_id)


def _client(reads: _Reads) -> TestClient:
    from assetops_backend.evidence.service import IngestionService

    app = FastAPI()
    app.include_router(build_evidence_router(
        IngestionService(None, _NoSites()), _NoSites(), imported_reads=reads))  # type: ignore[arg-type]
    return TestClient(app)


def test_the_range_reaches_the_ledger_read_as_instants() -> None:
    reads = _Reads()
    answer = _client(reads).get(f"/api/sites/KOBO-001/evidence/rejections?from={FROM}&to={TO}")
    assert answer.status_code == 200
    assert reads.calls == [("KOBO-001", None, (at(FROM), at(TO)))]


def test_without_a_range_the_read_is_unchanged() -> None:
    reads = _Reads()
    assert _client(reads).get("/api/sites/KOBO-001/evidence/rejections?batch=b-1").status_code == 200
    assert reads.calls == [("KOBO-001", "b-1", None)]


@pytest.mark.parametrize("query", [
    f"from={FROM}",                      # one bound
    f"to={TO}",                          # the other bound
    f"from={TO}&to={FROM}",              # reversed
    f"from={FROM}&to={FROM}",            # empty
    "from=2026-10-05&to=2026-10-12",     # days, not instants
])
def test_a_partial_or_bad_range_is_refused(query: str) -> None:
    reads = _Reads()
    answer = _client(reads).get(f"/api/sites/KOBO-001/evidence/rejections?{query}")
    assert answer.status_code == 422
    assert answer.json()["detail"]["code"] == "INVALID_WINDOW"
    assert reads.calls == []


class _Ledger:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def rejections(self, tenant_id, site_id, batch, window=None):
        self.calls.append((batch, window))
        return {"rejections": [], "duplicates": []}


def test_imported_reads_pass_the_window_only_when_given() -> None:
    ledger = _Ledger()
    reads = ImportedEvidenceReads(ledger, lambda c: None, lambda c: None, lambda c: {}, "env", lambda: "root")
    reads.rejections(SCOPE, None)
    reads.rejections(SCOPE, None, (at(FROM), at(TO)))
    assert ledger.calls == [(None, None), (None, (at(FROM), at(TO)))]


def _rejection(batch: str, received_at: str):
    return SimpleNamespace(batch_id=batch, index=0, message_id=f"m-{batch}", kind="CONFIGURATION_UNBOUND",
                           field=None, detail="x", received_at=received_at, content_digest="d")


def _conflict(batch: str, received_at: str):
    return SimpleNamespace(message_id=f"m-{batch}", batch_id=batch, original_digest="a", conflicting_digest="b",
                           received_at=received_at)


class _Store:
    def load_site(self, site_id):
        return SimpleNamespace(
            rejections=[_rejection("before", "2026-10-04T23:59:59Z"), _rejection("inside", "2026-10-05T00:00:00Z"),
                        _rejection("end", "2026-10-12T00:00:00Z")],
            conflicts=[_conflict("inside", "2026-10-11T23:00:00Z"), _conflict("after", "2026-10-13T00:00:00Z")],
        )


def test_the_file_backed_read_keeps_what_was_received_in_the_range() -> None:
    model = EvidenceReadModel(_Store())  # type: ignore[arg-type]
    ranged = model.rejections("SITE-1", None, (at(FROM), at(TO)))
    assert [r["batch_id"] for r in ranged["rejections"]] == ["inside"] and ranged["total"] == 1
    assert [c["batch_id"] for c in ranged["conflicts"]] == ["inside"]
    whole = model.rejections("SITE-1")
    assert whole["total"] == 3 and len(whole["conflicts"]) == 2
