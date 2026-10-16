"""Site source-health read (S7-01a, `I-source-health-read`, `D-2026-10-16-a-s7-health`).

A versioned read DTO over the central gateway store, separate from the S2
`gateway-health` contract (which stays unchanged). Two clocks are kept apart:

* **Contact** is the server receipt clock only: `CURRENT | STALE | UNKNOWN` against the
  gateway's declared cadence (`gateway_access.freshness`). A STALE contact does not date an
  outage; it says only that no receipt arrived inside two declared cadences.
* **Reported facts** are what the gateway said at its own `observed_at`: queue, disk pressure,
  clock offset and per-source device contact. Their age and clock trust are judged separately
  (`CURRENT | OLD | UNKNOWN`), so a fresh receipt of an old diagnostic is current contact with old
  facts. Queue and disk are the last *reported* state, never current hardware state.

Gateway contact never proves source-device contact: a source contact is shown only when the
selected diagnostic supplies that source's timestamp. Nothing here is a physical asset or device
health claim and nothing joins diagnostics to accepted measurement evidence.

Registration and the latest diagnostic per gateway are selected by the store in ONE repeatable-read
transaction; `check_consistent` refuses any selection whose rows disagree (409), and a store that
cannot be read is a 503, so neither can yield a current claim. There is no derived projection:
the read selects the central store directly, so `STALE_PROJECTION` is not applicable.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from assetops_backend.evidence.gateway_access import FRESHNESS_CADENCES, _z, freshness
from assetops_contracts.gateway_diagnostics import DiagnosticRejected, parse_canonical_gateway_diagnostics_v1_text

SCHEMA = {"id": "assetops.site-source-health", "version": 1}
RULE_ID = "assetops.source-health.two-clock.v1"
#: `D-2026-10-16-s701-clock`: two separate rules whose v1 values happen to match. Both are inclusive and
#: disclosed in the read; changing either needs a rule/DTO version review.
#: A measured clock offset with ``abs(offset_ms)`` above this makes the gateway's reported times UNTRUSTED.
CLOCK_OFFSET_LIMIT_MS = 5_000
#: An ``observed_at`` later than its server ``received_at`` by more than this is OBSERVED_AFTER_RECEIPT.
OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS = 5_000
SNAPSHOT_ISOLATIONS = ("repeatable read", "serializable")


@dataclass(frozen=True)
class RegisteredGateway:
    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    gateway_external_id: str
    mode: str
    registered_at: datetime
    disabled: bool
    cadence_seconds: int


@dataclass(frozen=True)
class RegisteredSource:
    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    source_id: UUID
    source_external_id: str
    disabled: bool


@dataclass(frozen=True)
class SelectedDiagnostic:
    tenant_id: UUID
    site_id: UUID
    gateway_id: UUID
    diagnostic_id: UUID
    sequence_epoch: str
    diagnostic_sequence: int
    observed_at: datetime
    received_at: datetime
    payload_sha256: str
    diagnostic_text: str


@dataclass(frozen=True)
class SourceHealthSnapshot:
    """Everything one read selected, from one database snapshot."""

    tenant_id: UUID
    site_id: UUID
    isolation: str
    gateways: tuple[RegisteredGateway, ...]
    sources: tuple[RegisteredSource, ...]
    diagnostics: tuple[SelectedDiagnostic, ...]  # at most one (the latest) per gateway


class SourceHealthStore(Protocol):
    def source_health_snapshot(self, tenant_id: UUID, site_id: UUID) -> SourceHealthSnapshot: ...


class SelectionInconsistent(Exception):
    """The registration and diagnostic selection disagree; no current claim is made."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _parse_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def check_consistent(snapshot: SourceHealthSnapshot, read_at: datetime) -> dict[UUID, dict]:
    """Refuse a selection that is not one consistent Site snapshot; return parsed facts per gateway."""
    if snapshot.isolation.lower() not in SNAPSHOT_ISOLATIONS:
        raise SelectionInconsistent(f"selection ran at isolation {snapshot.isolation!r}, not one snapshot")
    scope = (snapshot.tenant_id, snapshot.site_id)
    gateways = {g.gateway_id: g for g in snapshot.gateways}
    if len(gateways) != len(snapshot.gateways):
        raise SelectionInconsistent("a gateway was selected twice")
    for g in snapshot.gateways:
        if (g.tenant_id, g.site_id) != scope:
            raise SelectionInconsistent(f"gateway {g.gateway_id} is not registered to this tenant Site")
    sources_by_gateway: dict[UUID, set[UUID]] = {}
    for s in snapshot.sources:
        if (s.tenant_id, s.site_id) != scope or s.gateway_id not in gateways:
            raise SelectionInconsistent(f"source {s.source_id} is not registered to a selected gateway of this Site")
        sources_by_gateway.setdefault(s.gateway_id, set()).add(s.source_id)
    parsed: dict[UUID, dict] = {}
    for d in snapshot.diagnostics:
        if (d.tenant_id, d.site_id) != scope or d.gateway_id not in gateways:
            raise SelectionInconsistent(f"diagnostic {d.diagnostic_id} is not from a selected gateway of this Site")
        if d.gateway_id in parsed:
            raise SelectionInconsistent(f"gateway {d.gateway_id} has more than one selected latest diagnostic")
        if d.received_at > read_at:
            raise SelectionInconsistent(f"diagnostic {d.diagnostic_id} was received after the read time")
        try:
            body = parse_canonical_gateway_diagnostics_v1_text(d.diagnostic_text)
        except DiagnosticRejected as error:
            raise SelectionInconsistent(f"diagnostic {d.diagnostic_id} stored text does not parse: {error}") from None
        if (body.site_id, body.gateway_id, body.sequence_epoch, body.diagnostic_sequence, body.payload_sha256) != (
                str(d.site_id), str(d.gateway_id), d.sequence_epoch, d.diagnostic_sequence, d.payload_sha256) \
                or _parse_instant(body.observed_at) != d.observed_at:
            raise SelectionInconsistent(f"diagnostic {d.diagnostic_id} row and stored text disagree")
        for source_text, _ in body.last_device_contact_by_source:
            try:
                reported_source = UUID(source_text)
            except ValueError:
                reported_source = None
            if reported_source not in sources_by_gateway.get(d.gateway_id, set()):
                raise SelectionInconsistent(
                    f"diagnostic {d.diagnostic_id} reports source {source_text}, not registered to its gateway")
        parsed[d.gateway_id] = {
            "contacts": dict(body.last_device_contact_by_source), "queue_count": body.queue_count,
            "oldest_queue_age_seconds": body.oldest_queue_age_seconds, "disk_pressure": body.disk_pressure,
            "clock_offset_ms": body.clock_offset_ms, "mapping_error_count": body.mapping_error_count,
        }
    return parsed


def _seconds(delta: timedelta) -> int:
    return int(delta.total_seconds())


def clock_trust(offset_ms: int | None) -> tuple[str, str]:
    if offset_ms is None:
        return "UNKNOWN", "OFFSET_NOT_MEASURED"
    if abs(offset_ms) > CLOCK_OFFSET_LIMIT_MS:
        return "UNTRUSTED", "OFFSET_BEYOND_TOLERANCE"
    return "WITHIN_TOLERANCE", "OFFSET_MEASURED_WITHIN_TOLERANCE"


def fact_age(observed_at: datetime | None, received_at: datetime | None, trust: str, cadence_seconds: int,
             read_at: datetime) -> tuple[str, str]:
    """`CURRENT | OLD | UNKNOWN` for the reported facts, by the gateway's own clock."""
    if observed_at is None or received_at is None:
        return "UNKNOWN", "NEVER_RECEIVED"
    if trust == "UNTRUSTED":
        return "UNKNOWN", "GATEWAY_CLOCK_UNTRUSTED"
    if observed_at - received_at > timedelta(milliseconds=OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS):
        return "UNKNOWN", "OBSERVED_AFTER_RECEIPT"
    if read_at - observed_at <= timedelta(seconds=FRESHNESS_CADENCES * cadence_seconds):
        return "CURRENT", "OBSERVED_WITHIN_CADENCE_THRESHOLD"
    return "OLD", "OBSERVED_BEFORE_CADENCE_THRESHOLD"


def reported_age(at: datetime | None, trust: str, read_at: datetime) -> int | None:
    """Age of a gateway-reported time, or None when it cannot be stated: no time, an UNTRUSTED clock, or a
    time later than ``read_at`` (never a negative age; `D-2026-10-16-s701-clock` L5)."""
    if at is None or trust == "UNTRUSTED" or at > read_at:
        return None
    return _seconds(read_at - at)


def _watermark(diagnostics) -> dict:
    ids = sorted(str(d.diagnostic_id) for d in diagnostics)
    latest = max((d.received_at for d in diagnostics), default=None)
    return {"selected_diagnostic_count": len(ids), "latest_received_at": _z(latest),
            "selected_diagnostic_ids_sha256": hashlib.sha256("\n".join(ids).encode("ascii")).hexdigest()}


def source_health_document(snapshot: SourceHealthSnapshot, site_code: str, read_at: datetime,
                           access_basis: str) -> dict:
    """The S7-01a versioned Site source-health DTO. Raises `SelectionInconsistent`."""
    parsed = check_consistent(snapshot, read_at)
    latest = {d.gateway_id: d for d in snapshot.diagnostics}
    rows = []
    for g in sorted(snapshot.gateways, key=lambda g: g.gateway_external_id):
        d = latest.get(g.gateway_id)
        facts = parsed.get(g.gateway_id)
        received = None if d is None else d.received_at
        contact = freshness(received, g.cadence_seconds, read_at)
        trust, trust_reason = clock_trust(None if facts is None else facts["clock_offset_ms"])
        age_status, age_reason = fact_age(None if d is None else d.observed_at, received, trust,
                                          g.cadence_seconds, read_at)
        provenance = "REPORTED_SIMULATED_GATEWAY" if g.mode == "SIMULATED" else "REPORTED_GATEWAY"
        sources = []
        for s in sorted((s for s in snapshot.sources if s.gateway_id == g.gateway_id),
                        key=lambda s: s.source_external_id):
            reported = None if facts is None else facts["contacts"].get(str(s.source_id))
            in_report = facts is not None and str(s.source_id) in facts["contacts"]
            sources.append({
                "source_id": str(s.source_id), "source_external_id": s.source_external_id,
                "registration": "DISABLED" if s.disabled else "ENABLED",
                "reported_contact": reported,
                "reported_contact_status": (
                    "REPORTED" if reported is not None else
                    "REPORTED_NEVER_HEARD" if in_report else "NOT_IN_SELECTED_DIAGNOSTIC"),
                "reported_contact_age_seconds": reported_age(
                    None if reported is None else _parse_instant(reported), trust, read_at),
                "contact_basis": "GATEWAY_REPORTED_DEVICE_CONTACT",
            })
        rows.append({
            "gateway_id": str(g.gateway_id),
            "gateway_external_id": g.gateway_external_id,
            "mode": g.mode,
            "registration": "DISABLED" if g.disabled else "ENABLED",
            "registered_at": _z(g.registered_at),
            "declared_cadence_seconds": g.cadence_seconds,
            "contact": {
                "status": contact,
                "basis": "SERVER_RECEIVED_AT",
                "last_received_at": _z(received),
                "threshold_seconds": FRESHNESS_CADENCES * g.cadence_seconds,
                "since_last_receipt_seconds": None if received is None else _seconds(read_at - received),
                "reason": ("NEVER_RECEIVED" if received is None else
                           "RECEIVED_WITHIN_THRESHOLD" if contact == "CURRENT" else
                           "NO_RECEIPT_WITHIN_THRESHOLD_OUTAGE_START_NOT_DATED"),
            },
            "diagnostic": None if d is None else {
                "diagnostic_id": str(d.diagnostic_id), "sequence_epoch": d.sequence_epoch,
                "diagnostic_sequence": d.diagnostic_sequence, "received_at": _z(d.received_at),
                "observed_at": _z(d.observed_at), "observed_at_clock": "GATEWAY_REPORTED_UTC",
                "payload_sha256": d.payload_sha256,
            },
            "reported_facts": {
                "status": age_status,
                "reason": age_reason,
                "observed_at": None if d is None else _z(d.observed_at),
                "fact_age_seconds": reported_age(None if d is None else d.observed_at, trust, read_at),
                "receipt_lag_seconds": None if d is None else _seconds(d.received_at - d.observed_at),
                "clock": {"offset_ms": None if facts is None else facts["clock_offset_ms"],
                          "trust": trust if facts is not None else "UNKNOWN",
                          "reason": trust_reason if facts is not None else "NEVER_RECEIVED",
                          "tolerance_ms": CLOCK_OFFSET_LIMIT_MS,
                          "observed_after_receipt_allowance_ms": OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS},
                "queue": None if facts is None else {
                    "count": facts["queue_count"], "oldest_age_seconds": facts["oldest_queue_age_seconds"],
                    "as": "LAST_REPORTED"},
                "disk_pressure": None if facts is None else {
                    "value": facts["disk_pressure"], "as": "LAST_REPORTED", "provenance": provenance},
                "mapping_error_count": None if facts is None else facts["mapping_error_count"],
            },
            "sources": sources,
            "source_watermark": None if d is None else {
                "diagnostic_id": str(d.diagnostic_id), "sequence_epoch": d.sequence_epoch,
                "diagnostic_sequence": d.diagnostic_sequence, "received_at": _z(d.received_at)},
        })
    enabled = [r for r in rows if r["registration"] == "ENABLED"]
    counts = {k: sum(1 for r in enabled if r["contact"]["status"] == k) for k in ("CURRENT", "STALE", "UNKNOWN")}
    status = ("NO_REGISTERED_SOURCE" if not enabled else
              "ALL_CURRENT" if counts["CURRENT"] == len(enabled) else "NOT_ALL_CURRENT")
    # `D-2026-10-16-s701-clock` L3: the status name stays for compatibility; the reason says which case it is.
    reason = (None if enabled else "NO_ENABLED_GATEWAY" if rows else "NO_REGISTERED_GATEWAY")
    return {
        "schema": SCHEMA,
        "rule_id": RULE_ID,
        "site_code": site_code,
        "site_id": str(snapshot.site_id),
        "read_at": _z(read_at),
        "read_at_clock": "SERVER_REAL_UTC",
        "access_basis": access_basis,
        "claim_scope": "GATEWAY_OPERATIONAL_REPORT",
        "not_claimed": ["DEVICE_CONNECTED", "ASSET_CONDITION", "OUTAGE_START", "CURRENT_HARDWARE_STATE"],
        "snapshot": {"isolation": snapshot.isolation.upper().replace(" ", "_"), "selection": "CONSISTENT"},
        "stale_projection": {"applicable": False,
                             "reason": "The read selects the central diagnostic store directly; there is no "
                                       "derived projection to lag."},
        "summary": {
            "status": status,
            "reason": reason,
            "enabled_gateway_count": len(enabled),
            "disabled_gateway_count": len(rows) - len(enabled),
            "contact_counts": counts,
            "source_watermark": _watermark(snapshot.diagnostics),
        },
        "gateways": rows,
    }


__all__ = [
    "CLOCK_OFFSET_LIMIT_MS", "OBSERVED_AFTER_RECEIPT_ALLOWANCE_MS", "RULE_ID", "SCHEMA", "RegisteredGateway", "RegisteredSource", "SelectedDiagnostic",
    "SelectionInconsistent", "SourceHealthSnapshot", "SourceHealthStore", "check_consistent", "clock_trust",
    "fact_age", "reported_age", "source_health_document",
]
