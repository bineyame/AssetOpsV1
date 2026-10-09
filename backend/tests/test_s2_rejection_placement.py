"""S2-02 Q19 (Architect batch answers 3): rejection read placement, no database.

A rejected or conflicting reading is placed in a source-time window by its OWN
envelope's source time. A conflict keeps its original accepted reading's time as
lineage only. A rejection without a readable source time is in no window; it is
counted (`rejected_without_source_time`) and listed in the unwindowed rejections.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from assetops_backend.evidence.ledger_reads import ImportedEvidenceReads, ImportedScope

ORIGINAL = datetime(2026, 10, 9, 8, 1, tzinfo=timezone.utc)
CONFLICT_TIME = "2026-10-09T08:45:00Z"


def _row(kind: str, envelope_text: str | None, *, original=None, conflicts_with=None) -> dict:
    return {
        "rejection_id": uuid4(), "batch_id": uuid4(), "external_batch_id": f"b-{kind}", "ordinal": 0,
        "message_id": f"m-{kind}", "decision": "CONFLICT" if conflicts_with else "REJECTED", "kind": kind,
        "field": None, "detail": "x", "received_at": None, "decided_at": None, "envelope_sha256": None,
        "envelope_text": envelope_text, "conflicts_with_evidence_id": conflicts_with,
        "original_source_time": original,
    }


ROWS = [
    _row("MESSAGE_CONFLICT", json.dumps({"timing": {"source_time": CONFLICT_TIME}}),
         original=ORIGINAL, conflicts_with=uuid4()),
    _row("CONFIGURATION_UNBOUND", "not an envelope"),
]


class _Ledger:
    def site_window(self, tenant_id, site_id, start, end):
        return {"sources": [], "coverage": [], "batches": [], "projection": [], "rejections": ROWS,
                "extent": {"first_source_time": None, "last_source_time": None, "last_received_at": None,
                           "accepted_total": 0}}

    def rejections(self, tenant_id, site_id, batch):
        return {"rejections": ROWS, "duplicates": []}


READS = ImportedEvidenceReads(_Ledger(), lambda code: None, lambda code: None, lambda code: {}, "env")
SCOPE = ImportedScope("KOBO-001", UUID(int=1), UUID(int=2), None)


def at(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def test_a_conflict_is_placed_by_its_own_source_time_not_its_originals() -> None:
    around_conflict = READS.site_evidence(SCOPE, at("2026-10-09T08:40:00Z"), at("2026-10-09T08:50:00Z"))
    assert around_conflict["counts"]["conflicts"] == 1 and "CONFLICTING" in around_conflict["states"]
    around_original = READS.site_evidence(SCOPE, at("2026-10-09T08:00:00Z"), at("2026-10-09T08:10:00Z"))
    assert around_original["counts"]["conflicts"] == 0 and around_original["state"] == "NO_DATA"
    [conflict] = READS.rejections(SCOPE, None)["conflicts"]
    assert conflict["source_time"] == CONFLICT_TIME
    assert conflict["conflicts_with_source_time"] == "2026-10-09T08:01:00Z"  # lineage only


def test_an_unreadable_time_rejection_is_in_no_window_but_counted_and_listed_unwindowed() -> None:
    windowed = READS.site_evidence(SCOPE, at("2000-01-01T00:00:00Z"), at("2100-01-01T00:00:00Z"))
    assert windowed["counts"]["rejected"] == 0
    assert windowed["counts"]["rejected_without_source_time"] == 1
    listed = READS.rejections(SCOPE, None)
    assert listed["rejected_without_source_time"] == 1
    untimed = [r for r in listed["rejections"] if r["source_time"] is None]
    assert [r["kind"] for r in untimed] == ["CONFIGURATION_UNBOUND"]
