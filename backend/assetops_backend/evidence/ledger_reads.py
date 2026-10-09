"""Site Evidence read model over the central Postgres ledger (S2-02 phase 3a).

Pure: it builds payloads from the plain rows `PostgresEvidenceLedger` returns
and holds no SQL. `ImportedEvidenceReads` answers the four Site Evidence routes
for an imported Site only after that Site's legacy comparison record permits
the cutover (`legacy_comparison.permits_cutover`); otherwise the caller keeps
answering 409 `AWAITING_EVIDENCE_MIGRATION`.

Clocks. `source_time` and `published_at` on a `SIMULATED` report are
run-virtual instants (`RUN_VIRTUAL`); on a `LIVE` report they are the source's
own reported clock (`SOURCE_REPORTED`). `received_at` is the server's real UTC
first receipt of the batch (`SERVER_RECEIVED_AT`), never a later ordinal
decision time (`decided_at`). A difference between a virtual and a real instant
is not network lag, so no payload subtracts them.

Window. Source-time, half-open `[start, end)`; either bound may be absent
(`basis: "ALL"` when both are). Records page in `(source_time, evidence_id)`
order with an opaque `next_cursor`.

GET /api/sites/{id}/evidence            -> SITE_EVIDENCE (store "POSTGRES")
  {store, site_id, site_uuid, tenant_id, window, extent, state, states[],
   clock_statement, sources[], batches[], coverage[], counts, projection,
   migration, limits[]}
  state: NO_DATA | REJECTED_ONLY | ACCEPTED; states add PARTIAL_BATCH,
  CONFLICTING, STALE_PROJECTION, OUTDATED_CONFIGURATION.
GET /api/sites/{id}/evidence/records    -> {store, site_id, window, total, limit,
  next_cursor|null, records[RECORD]}
GET /api/sites/{id}/evidence/records/{evidence_id|message_id}
  -> RECORD + {envelope, accepted_as, receipt, sequence, duplicates[], conflicts[]}
GET /api/sites/{id}/evidence/rejections?batch= -> {store, site_id, total,
  rejected_without_source_time, rejections[], conflicts[], duplicates[]}
  A rejection's `source_time` is its own envelope's (null when unreadable);
  a conflict also carries `conflicts_with_source_time` (the original, lineage only).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Protocol
from uuid import UUID

from assetops_backend.evidence.legacy_comparison import permits_cutover
from assetops_backend.evidence.ports import EvidenceStoreUnavailable

CLOCK_STATEMENT = (
    "Source and publication times on simulated reports are run-virtual instants; "
    "received time is the server's real UTC first receipt of the batch. The two "
    "clocks are not subtracted: their difference is not network lag."
)
PROJECTION_STATEMENT = (
    "Accepted evidence queues dispatch recompute jobs; the Analysis projection is "
    "computed by the S3 worker, which is not part of this slice."
)


class LedgerReads(Protocol):
    def site_window(self, tenant_id: UUID, site_id: UUID, start, end) -> dict: ...
    def records_page(self, tenant_id: UUID, site_id: UUID, **filters) -> dict: ...
    def record_detail(self, tenant_id: UUID, site_id: UUID, key: str) -> list[dict]: ...
    def rejections(self, tenant_id: UUID, site_id: UUID, batch: str | None) -> dict: ...


class AwaitingComparison(Exception):
    """An imported Site whose legacy comparison does not (yet) permit the cutover."""


class InvalidCursor(ValueError):
    pass


class AmbiguousRecord(ValueError):
    pass


@dataclass(frozen=True)
class ImportedScope:
    site_code: str
    tenant_id: UUID
    site_id: UUID
    comparison: dict


def _z(value: datetime | None, *, micro: bool = False) -> str | None:
    if value is None:
        return None
    value = value.astimezone(timezone.utc)
    if micro or value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(text: str | None) -> datetime | None:
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def clocks(source_mode: str) -> dict:
    reported = "RUN_VIRTUAL" if source_mode == "SIMULATED" else "SOURCE_REPORTED"
    return {"source_time": reported, "published_at": reported, "received_at": "SERVER_RECEIVED_AT"}


def _window(start: datetime | None, end: datetime | None) -> dict:
    return {"start": _z(start), "end": _z(end), "half_open": True, "clock": "SOURCE_TIME",
            "basis": "ALL" if start is None and end is None else "REQUESTED"}


def _in(instant: datetime | None, start: datetime | None, end: datetime | None) -> bool:
    if instant is None:
        return False
    return (start is None or instant >= start) and (end is None or instant < end)


def _envelope_source_time(text: str | None) -> datetime | None:
    try:
        return _parse(json.loads(text)["timing"]["source_time"]) if text else None
    except (ValueError, KeyError, TypeError):
        return None


def _rejection(row: dict) -> dict:
    # Q19 (Architect, batch answers 3): a rejection is placed by the refused or
    # conflicting envelope's OWN source time. A conflict's original accepted row
    # is lineage (`conflicts_with_source_time`), never the conflict event's time.
    # No readable source time: no window holds it; it is counted and listed unwindowed.
    placed = _envelope_source_time(row["envelope_text"])
    return {
        "rejection_id": str(row["rejection_id"]), "batch_id": row["external_batch_id"], "ordinal": row["ordinal"],
        "message_id": row["message_id"], "decision": row["decision"], "kind": row["kind"],
        "field": row["field"], "detail": row["detail"], "source_time": _z(placed),
        "received_at": _z(row["received_at"], micro=True), "decided_at": _z(row["decided_at"], micro=True),
        "envelope_sha256": row["envelope_sha256"], "envelope_text": row["envelope_text"],
        "conflicts_with_evidence_id": None if row["conflicts_with_evidence_id"] is None
        else str(row["conflicts_with_evidence_id"]),
        "conflicts_with_source_time": _z(row["original_source_time"]),
    }


def record_payload(row: dict) -> dict:
    return {
        "evidence_id": str(row["id"]), "message_id": row["message_id"],
        "source": {"source_id": str(row["source_id"]), "external_id": row["source_external_id"]},
        "gateway": {"gateway_id": str(row["gateway_id"]), "external_id": row["gateway_external_id"]},
        "device_id": row["device_id"], "signal_id": row["signal_id"], "role": row["role"],
        "family": row["family"], "measurement": row["measurement"], "quality": row["quality"],
        "unavailable_reason": row["unavailable_reason"],
        "original": {"value": row["original_value_text"], "unit": row["original_unit"]},
        "normalized": {"value": row["normalized_value_text"], "unit": row["normalized_unit"]},
        "source_time": _z(row["source_time"]), "published_at": _z(row["published_at"]),
        "received_at": _z(row.get("batch_received_at") or row["received_at"], micro=True),
        "interval": None if row["interval_start"] is None
        else {"start": _z(row["interval_start"]), "end": _z(row["interval_end"])},
        "configuration_outdated": row["configuration_outdated"], "source_mode": row["source_mode"],
        "clocks": clocks(row["source_mode"]),
        "receipt": {"batch_id": row["external_batch_id"], "ordinal": row["ordinal"]},
    }


def encode_cursor(row: dict) -> str:
    return f"{_z(row['source_time'], micro=True)}~{row['id']}"


def decode_cursor(text: str) -> tuple[datetime, UUID]:
    instant, _, ident = text.partition("~")
    parsed = _parse(instant)
    try:
        identity = UUID(ident)
    except ValueError:
        identity = None
    if parsed is None or identity is None:
        raise InvalidCursor("the cursor is not one this route issued")
    return parsed, identity


class ImportedEvidenceReads:
    """The Postgres Site Evidence reads for imported Sites, behind the comparison gate."""

    def __init__(
        self,
        ledger: LedgerReads,
        imported: Callable[[str], tuple[str, UUID, UUID] | None],
        latest_comparison: Callable[[str], dict | None],
        current_inventory: Callable[[str], dict],
        environment: str | None,
        current_store_root: Callable[[], str | None],
    ) -> None:
        """`current_inventory(site_code)` recomputes `legacy_inventory` from the
        current legacy input (raises `EvidenceStoreUnavailable` when unreadable);
        `environment` is `environment_identity` of the active database (Q14);
        `current_store_root()` is `store_root_identity` of the local stores this
        process reads (Q26; None closes the gate)."""
        self._ledger = ledger
        self._imported = imported
        self._latest_comparison = latest_comparison
        self._current_inventory = current_inventory
        self._environment = environment
        self._current_store_root = current_store_root

    def scope(self, site_code: str) -> ImportedScope | None:
        """None for a Site that is not imported (the legacy path answers it).
        Raises `AwaitingComparison` for an imported Site the gate keeps closed."""
        found = self._imported(site_code)
        if found is None:
            return None
        code, tenant_id, site_id = found
        report = self._latest_comparison(code)
        try:
            inventory = self._current_inventory(code)
        except EvidenceStoreUnavailable:
            inventory = None  # unreadable legacy input: fail closed
        allowed, reason = permits_cutover(report, code, site_id, tenant_id=tenant_id,
                                          environment=self._environment, inventory=inventory,
                                          store_root=self._current_store_root())
        if not allowed:
            raise AwaitingComparison(
                f"Site {code} is imported; its Evidence moves to the central ledger only after a "
                f"passing legacy comparison record. {reason}"
            )
        return ImportedScope(code, tenant_id, site_id, report)

    def site_evidence(self, scope: ImportedScope, start: datetime | None, end: datetime | None) -> dict:
        rows = self._ledger.site_window(scope.tenant_id, scope.site_id, start, end)
        rejections = [_rejection(r) for r in rows["rejections"]]
        everything = start is None and end is None
        placed = [r for r in rejections if everything or _in(_parse(r["source_time"]), start, end)]
        conflicts = [r for r in placed if r["kind"] == "MESSAGE_CONFLICT"]
        rejected = [r for r in placed if r["kind"] != "MESSAGE_CONFLICT"]
        rejected_batches = {r["batch_id"] for r in placed}
        batches = [
            {"batch_id": b["external_batch_id"], "batch_uuid": str(b["id"]), "source_id": str(b["source_id"]),
             "status": b["status"], "partial": b["status"] == "IN_PROGRESS", "payload_sha256": b["payload_sha256"],
             "counts": {"total": b["total_count"], "processed": b["processed_count"], "accepted": b["accepted_count"],
                        "duplicate": b["duplicate_count"], "rejected": b["rejected_count"],
                        "conflict": b["conflict_count"]},
             "accepted_in_window": b["accepted_in_window"],
             "received_at": _z(b["received_at"], micro=True), "completed_at": _z(b["completed_at"], micro=True)}
            for b in rows["batches"]
            if everything or b["accepted_in_window"] or b["status"] == "IN_PROGRESS"
            or b["external_batch_id"] in rejected_batches
        ]
        by_source_rejected: dict[str, int] = {}
        source_of_batch = {b["external_batch_id"]: str(b["source_id"]) for b in rows["batches"]}
        for r in rejected:
            key = source_of_batch.get(r["batch_id"], "")
            by_source_rejected[key] = by_source_rejected.get(key, 0) + 1
        sources = [
            {"source_id": str(s["source_id"]), "external_id": s["source_external_id"],
             "gateway_id": str(s["gateway_id"]), "gateway_external_id": s["gateway_external_id"],
             "source_mode": s["source_mode"], "clocks": clocks(s["source_mode"]),
             "accepted_in_window": s["accepted"], "duplicates_in_window": s["duplicates"],
             "conflicts_in_window": s["conflicts"], "rejected_in_window": by_source_rejected.get(str(s["source_id"]), 0),
             "last_source_time": _z(s["last_source_time"]), "last_published_at": _z(s["last_published_at"]),
             "last_received_at": _z(s["last_received_at"], micro=True)}
            for s in rows["sources"]
        ]
        coverage = [
            {"device_id": c["device_id"], "signal_id": c["signal_id"], "role": c["role"], "unit": c["normalized_unit"],
             "records": c["records"], "good": c["good"], "configuration_outdated": c["outdated"],
             "first_source_time": _z(c["first_source_time"]), "last_source_time": _z(c["last_source_time"])}
            for c in rows["coverage"]
        ]
        jobs = {p["status"]: p for p in rows["projection"]}
        pending = sum(p["jobs"] for p in rows["projection"])
        projection = {
            "status": "STALE" if pending else "NO_PENDING_DISPATCH",
            "pending_jobs": jobs.get("PENDING", {}).get("jobs", 0),
            "leased_jobs": jobs.get("LEASED", {}).get("jobs", 0),
            "failed_jobs": jobs.get("FAILED", {}).get("jobs", 0),
            "oldest_job_created_at": _z(min((p["oldest_created_at"] for p in rows["projection"]), default=None),
                                        micro=True),
            "statement": PROJECTION_STATEMENT,
        }
        accepted = sum(s["accepted_in_window"] for s in sources)
        partial = any(b["partial"] for b in batches)
        state = "ACCEPTED" if accepted else ("REJECTED_ONLY" if placed else "NO_DATA")
        states = [state]
        if partial:
            states.append("PARTIAL_BATCH")
        if conflicts:
            states.append("CONFLICTING")
        if pending:
            states.append("STALE_PROJECTION")
        if any(c["configuration_outdated"] for c in coverage):
            states.append("OUTDATED_CONFIGURATION")
        extent = rows["extent"]
        return {
            "store": "POSTGRES", "site_id": scope.site_code, "site_uuid": str(scope.site_id),
            "tenant_id": str(scope.tenant_id), "window": _window(start, end),
            "extent": {"first_source_time": _z(extent["first_source_time"]),
                       "last_source_time": _z(extent["last_source_time"]),
                       "last_received_at": _z(extent["last_received_at"], micro=True),
                       "accepted_total": extent["accepted_total"]},
            "state": state, "states": states, "clock_statement": CLOCK_STATEMENT,
            "sources": sources, "batches": batches, "coverage": coverage,
            "counts": {"accepted": accepted, "duplicates": sum(s["duplicates_in_window"] for s in sources),
                       "rejected": len(rejected), "conflicts": len(conflicts),
                       "rejected_without_source_time": sum(1 for r in rejections if r["source_time"] is None)},
            "projection": projection, "migration": migration_summary(scope.comparison),
            "limits": [PROJECTION_STATEMENT,
                       "This view shows accepted evidence and its receipts only; it states no dispatch, "
                       "capability or service-health conclusion."],
        }

    def records(self, scope: ImportedScope, *, start, end, device, signal, source, cursor, limit) -> dict:
        after = None if cursor is None else decode_cursor(cursor)
        page = self._ledger.records_page(scope.tenant_id, scope.site_id, start=start, end=end, device=device,
                                         signal=signal, source=source, after=after, limit=limit)
        rows = page["rows"]
        more = len(rows) > limit
        rows = rows[:limit]
        return {"store": "POSTGRES", "site_id": scope.site_code, "window": _window(start, end),
                "total": page["total"], "limit": limit,
                "next_cursor": encode_cursor(rows[-1]) if more and rows else None,
                "records": [record_payload(r) for r in rows]}

    def record(self, scope: ImportedScope, key: str) -> dict | None:
        found = self._ledger.record_detail(scope.tenant_id, scope.site_id, key)
        if not found:
            return None
        if len(found) > 1:
            raise AmbiguousRecord(
                f"Message {key} was accepted from more than one source; open it by evidence ID: "
                + ", ".join(str(r["id"]) for r in found)
            )
        row = found[0]
        payload = record_payload(row)
        payload.update({
            "store": "POSTGRES", "site_id": scope.site_code,
            "sequence": {"epoch": row["sequence_epoch"], "sequence": row["sequence"]},
            "envelope": {"sha256": row["envelope_sha256"], "text": row["envelope_text"]},
            "accepted_as": {
                "foundation_revision_id": str(row["foundation_revision_id"]),
                "binding_set_revision_id": str(row["binding_set_revision_id"]),
                "binding_revision_id": str(row["binding_revision_id"]),
                "asset_id": None if row["asset_id"] is None else str(row["asset_id"]),
                "conversion_kind": row["conversion_kind"],
                "configuration_outdated": row["configuration_outdated"],
            },
            "receipt": {
                "batch_id": row["external_batch_id"], "batch_uuid": str(row["batch_id"]),
                "ordinal": row["ordinal"], "decision": row["decision"],
                "payload_sha256": row["payload_sha256"], "batch_status": row["batch_status"],
                "processed": row["processed_count"], "total": row["total_count"],
                "received_at": _z(row["batch_received_at"], micro=True),
                "decided_at": _z(row["decided_at"], micro=True),
                "completed_at": _z(row["batch_completed_at"], micro=True),
            },
            "duplicates": [
                {"batch_id": d["external_batch_id"], "ordinal": d["ordinal"],
                 "received_at": _z(d["received_at"], micro=True), "decided_at": _z(d["decided_at"], micro=True)}
                for d in row["duplicates"]
            ],
            "conflicts": [
                {"rejection_id": str(c["rejection_id"]), "batch_id": c["external_batch_id"], "ordinal": c["ordinal"],
                 "kind": c["kind"], "detail": c["detail"], "envelope_sha256": c["envelope_sha256"],
                 "envelope_text": c["envelope_text"], "received_at": _z(c["received_at"], micro=True),
                 "decided_at": _z(c["decided_at"], micro=True)}
                for c in row["conflicts"]
            ],
        })
        return payload

    def rejections(self, scope: ImportedScope, batch: str | None) -> dict:
        rows = self._ledger.rejections(scope.tenant_id, scope.site_id, batch)
        rejections = [_rejection(r) for r in rows["rejections"]]
        return {
            "store": "POSTGRES", "site_id": scope.site_code, "total": len(rejections),
            "rejections": rejections,
            "rejected_without_source_time": sum(1 for r in rejections if r["source_time"] is None),
            "conflicts": [r for r in rejections if r["kind"] == "MESSAGE_CONFLICT"],
            "duplicates": [
                {"batch_id": d["external_batch_id"], "ordinal": d["ordinal"], "message_id": d["message_id"],
                 "first_accepted_evidence_id": str(d["accepted_evidence_id"]),
                 "received_at": _z(d["received_at"], micro=True), "decided_at": _z(d["decided_at"], micro=True)}
                for d in rows["duplicates"]
            ],
        }


def migration_summary(report: dict[str, Any] | None) -> dict | None:
    if report is None:
        return None
    return {key: report.get(key) for key in ("report_id", "outcome", "empty_set", "statement", "compared_at")}
