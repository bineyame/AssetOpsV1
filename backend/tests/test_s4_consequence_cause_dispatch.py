"""S4-02c review L3: the recompute worker dispatches each work cause explicitly.

An unknown cause records a typed FAILED attempt and stays pending; it never falls through to the assumption-range
recompute. (`EVIDENCE_ACCEPTED` is dispatched since S4-02c phase 2; see `test_s4_evidence_drain.py`.) No database
needed.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from assetops_backend.financials.recompute import ERROR_CAUSE_NOT_SUPPORTED, ConsequenceRecomputeWorker


class Store:
    def __init__(self) -> None:
        self.attempts: list[dict] = []

    def latest_revisions_overlapping(self, *args, **kw):
        raise AssertionError("an unsupported cause fell through to the assumption-range recompute")

    def load_input(self, *args, **kw):
        raise AssertionError("an unsupported cause derived a consequence")

    def append(self, *args, **kw):
        raise AssertionError("an unsupported cause appended a consequence")

    def record_attempt(self, tenant_id, site_id, work_id, **kw) -> int:
        self.attempts.append({"work_id": work_id, **kw})
        return len(self.attempts)


@pytest.mark.parametrize("cause", ["SOMETHING_NEW", "evidence_accepted"])
def test_an_unsupported_cause_records_a_typed_failure_and_never_falls_through(cause: str) -> None:
    store = Store()
    work = {"id": uuid4(), "cause": cause, "finding_id": uuid4(), "finding_revision_id": uuid4(),
            "accepted_evidence_id": uuid4(), "affected_from": datetime(2026, 10, 6, tzinfo=timezone.utc),
            "affected_to": None}
    out = ConsequenceRecomputeWorker(store, prices=None).process(uuid4(), uuid4(), work)
    assert (out.succeeded, out.error_code, out.consequence_revision_ids) == (False, ERROR_CAUSE_NOT_SUPPORTED, [])
    (attempt,) = store.attempts
    assert attempt["succeeded"] is False and attempt["error_code"] == ERROR_CAUSE_NOT_SUPPORTED
    assert cause in attempt["error_detail"]
