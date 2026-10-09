"""Receipt V2 contract (S2-02): strict shape, digest and canonical spelling."""

from __future__ import annotations

import json

import pytest

from assetops_contracts.ingestion_receipt_v2 import (
    IngestionReceiptV2,
    ReceiptCounts,
    ReceiptDisposition,
    ReceiptRejected,
    ReceiptRejection,
    canonical_receipt_v2_text,
    parse_canonical_receipt_v2_text,
)

MSG = "a" * 64
EVIDENCE = "11111111-1111-4111-8111-111111111111"
REJECTION = "22222222-2222-4222-8222-222222222222"


def receipt(**changes) -> IngestionReceiptV2:
    fields = dict(
        batch_id="batch-1", payload_sha256="b" * 64, site_id="s", gateway_id="g", source_id="src",
        status="COMPLETED", received_at="2026-10-09T08:30:00.000000Z", completed_at="2026-10-09T08:30:01.000000Z",
        counts=ReceiptCounts(total=2, processed=2, accepted=1, duplicate=0, rejected=1, conflict=0),
        dispositions=(
            ReceiptDisposition(0, MSG, "ACCEPTED", EVIDENCE, None),
            ReceiptDisposition(1, "c" * 64, "REJECTED", None,
                               ReceiptRejection(REJECTION, "UNIT_INCOMPATIBLE", "payload.unit", "x", None)),
        ),
    )
    fields.update(changes)
    return IngestionReceiptV2(**fields)


def test_round_trip_is_exact() -> None:
    body = canonical_receipt_v2_text(receipt())
    assert parse_canonical_receipt_v2_text(body) == receipt()
    assert canonical_receipt_v2_text(parse_canonical_receipt_v2_text(body)) == body


def test_a_changed_decision_misses_the_digest() -> None:
    doc = json.loads(canonical_receipt_v2_text(receipt()))
    doc["dispositions"][0]["evidence_id"] = REJECTION
    tampered = json.dumps(doc, sort_keys=True, separators=(",", ":"))
    with pytest.raises(ReceiptRejected, match="DIGEST_MISMATCH"):
        parse_canonical_receipt_v2_text(tampered)


def test_counts_status_and_references_must_agree() -> None:
    with pytest.raises(ReceiptRejected, match="INVALID_COUNTS"):
        receipt(counts=ReceiptCounts(total=2, processed=2, accepted=2, duplicate=0, rejected=0, conflict=0))
    with pytest.raises(ReceiptRejected, match="COMPLETED exactly"):
        receipt(status="IN_PROGRESS")
    with pytest.raises(ReceiptRejected, match="wrong reference"):
        receipt(dispositions=(ReceiptDisposition(0, MSG, "ACCEPTED", None, None),) + receipt().dispositions[1:])


def test_a_partial_receipt_lists_only_decided_ordinals() -> None:
    partial = receipt(
        status="IN_PROGRESS", completed_at=None,
        counts=ReceiptCounts(total=5, processed=1, accepted=1, duplicate=0, rejected=0, conflict=0),
        dispositions=receipt().dispositions[:1],
    )
    assert parse_canonical_receipt_v2_text(canonical_receipt_v2_text(partial)) == partial
