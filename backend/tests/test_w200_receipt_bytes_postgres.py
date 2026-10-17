"""W2-00 ruling 6: a MESSAGE_CONFLICT Receipt V2 is byte-stable across the conflict-count change.

The fixture `fixtures/w200/message-conflict-receipt.txt` was frozen from the pre-W2-00 revision (`dc643215`)
by running this module with ASSETOPS_W200_FREEZE=1. Random identifiers (Site, gateway, source, evidence and
rejection UUIDs, and the batch, payload and message digests derived from them) are replaced by placeholders in order of first appearance; every other byte must match.
This module deliberately imports nothing W2-00 added, so it runs unchanged on the old revision.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

URL = os.environ.get("ASSETOPS_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="ASSETOPS_TEST_DATABASE_URL is not set (see backend/README-db.md)")

if URL:
    from test_s1_bindings_postgres import engine, store  # noqa: F401
    from test_s2_evidence_ledger_postgres import kit, submit  # noqa: F401

    from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "w200" / "message-conflict-receipt.txt"
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9a-f]{64}")


def normalized(receipt_text: str) -> str:
    seen: dict[str, str] = {}
    return _UUID.sub(lambda m: seen.setdefault(m.group(0), f"<id-{len(seen) + 1}>"), receipt_text)


def test_message_conflict_receipt_bytes_are_unchanged(kit) -> None:  # noqa: F811
    submit(kit, kit.seal(kit.pv(1, value="1.5")))
    conflicting = submit(kit, kit.seal(kit.pv(2, value="2.5")))  # seq 1 changed bytes, seq 2 new
    receipt = conflicting.receipt
    assert [d.decision for d in receipt.dispositions] == ["CONFLICT", "ACCEPTED"]
    assert receipt.dispositions[0].rejection.kind == "MESSAGE_CONFLICT"
    text = normalized(canonical_receipt_v2_text(receipt))
    if os.environ.get("ASSETOPS_W200_FREEZE") == "1":
        FIXTURE.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE.write_text(text, encoding="utf-8", newline="")
    assert text == FIXTURE.read_text(encoding="utf-8")
