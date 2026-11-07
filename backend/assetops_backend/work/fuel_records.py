"""DIESEL-K2 (`.agent/build-sheet-DIESEL-1.md` §9c.2): the as-known fuel records read, for K3.

A fuel record is a `FUEL_DELIVERY` or `TANK_DIP` operational record that names one fuel tank. The read selects every
operational-record root of the Site recorded at or before `known_at`, at its latest version recorded at or before
`known_at` by `(recorded_at, id)` (the `_OPERATIONAL` root/head shape), and keeps a record whose **head** is a fuel
kind, names the tank and occurred in `[lo, hi)`. Membership uses the head's occurrence, so a corrected time moves a
delivery to its true night. Ordered by `(occurred_at, root_id)`. The read never writes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Protocol
from uuid import UUID

FUEL_KINDS = ("FUEL_DELIVERY", "TANK_DIP")
WINDOW_REFUSED = "fuel_records needs UTC instants with lo < hi"


@dataclass(frozen=True)
class FuelRecord:
    root_id: str              # canonical record id (the REC lineage root)
    head_id: str              # the version selected at known_at
    code: str                 # the root's public code, REC-nnnnnn
    kind: str                 # the head's kind, one of FUEL_KINDS
    occurred_at: datetime     # the head's occurrence (a correction may move it)
    recorded_at: datetime     # the head's recorded_at
    root_recorded_at: datetime  # when the record was first recorded (K3's DELIVERY_RECORDED_LATE reads it)
    quantity_l: Decimal       # the head's quantity, exact
    ticket_sha256: str | None  # the head's source_document_sha256
    actor_id: str
    body: str


class FuelRecordsPort(Protocol):
    def fuel_records(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                     lo: datetime, hi: datetime, known_at: datetime) -> tuple[FuelRecord, ...]: ...


def check_window(lo: datetime, hi: datetime, known_at: datetime) -> None:
    """All three instants UTC-aware and `lo < hi`; `known_at` is not capped (K3 passes a past window end)."""
    for value in (lo, hi, known_at):
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError(WINDOW_REFUSED)
    if not lo < hi:
        raise ValueError(WINDOW_REFUSED)
