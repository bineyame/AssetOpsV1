"""DIESEL-K3 (`.agent/build-sheet-DIESEL-1.md` §9d.5, ruling DIESEL-1-R3d): the stored `fuel-balance-1` night window
and the read port K4 (Finding) and K6 (verification) use; K4a adds the unexplained-fuel Finding read (§9j.5).

Reason and limitation codes are internal. Client wording belongs to K4/K5.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from fractions import Fraction
from typing import Any, Mapping, Protocol
from uuid import UUID

PARAMETER_VERSION = "fuel-balance-1/v1"
STATES = ("UNEXPLAINED", "BELOW_MATERIALITY", "WITHIN_MARGIN", "EXCESS", "NOT_ASSESSED")
#: NOT_ASSESSED reasons in precedence order (the first that applies is stored), §9d.2
REASONS = ("NO_SENSOR_ACCURACY", "SFC_MISSING", "NO_LOAD_RATE_MISSING", "MISSING_OPENING", "MISSING_CLOSING",
           "FUEL_LEVEL_CONFLICT", "GENERATOR_KWH_UNKNOWN", "IDLE_SECONDS_UNKNOWN")
#: information only, in this fixed order, each at most once
LIMITATIONS = ("REPORTING_GAP", "DIP_SENSOR_CONFLICT", "DELIVERY_RECORDED_LATE")

WINDOW_INVALID = "FUEL_BALANCE_WINDOW_INVALID"
WINDOW_OPEN = "FUEL_BALANCE_WINDOW_OPEN"
ASSETS_UNSUPPORTED = "FUEL_BALANCE_ASSETS_UNSUPPORTED"
CLOCK_BACKWARDS = "FUEL_BALANCE_CLOCK_BACKWARDS"
REFUSAL_CODES = (WINDOW_INVALID, WINDOW_OPEN, ASSETS_UNSUPPORTED, CLOCK_BACKWARDS)
WINDOWS_REFUSED = "fuel balance windows need lo < hi and a UTC known_at"


class FuelBalanceRefused(Exception):
    """One of `REFUSAL_CODES`; nothing is written."""

    def __init__(self, code: str, detail: str) -> None:
        assert code in REFUSAL_CODES, code
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class FuelBalanceWindow:
    id: UUID
    tenant_id: UUID
    site_id: UUID
    tank_asset_id: UUID
    generator_asset_id: UUID
    night_date: date                 # Site-local date of the 18:00 start
    window_start: datetime           # UTC
    window_end: datetime             # UTC
    revision: int
    parameter_version: str
    recorded_at: datetime            # also the inputs' known_at
    state: str                       # one of STATES
    reason: str | None               # set iff NOT_ASSESSED
    residual_low: Fraction | None
    residual_high: Fraction | None
    gap_minutes: int
    gap_spans: tuple[tuple[datetime, datetime], ...]
    limitations: tuple[str, ...]
    terms: Mapping[str, Any]         # §9d.2 result terms, exact text
    evidence_ids: tuple[str, ...]
    record_ids: tuple[tuple[str, str], ...]
    input_sha256: str


@dataclass(frozen=True)
class AssessResult:
    window: FuelBalanceWindow
    appended: bool


class FuelBalanceReadPort(Protocol):
    def windows(self, tenant_id: UUID, site_id: UUID, tank_asset_id: UUID,
                lo: date, hi: date, known_at: datetime) -> tuple[FuelBalanceWindow, ...]: ...

    def window(self, tenant_id: UUID, site_id: UUID, window_id: UUID) -> FuelBalanceWindow | None: ...


# --- DIESEL-K4a (§9j.5): the unexplained-fuel Finding read ------------------------------------------------------
FINDINGS_REFUSED = "fuel findings need lo < hi and UTC instants"


@dataclass(frozen=True)
class FuelFinding:
    finding_id: UUID
    revision_id: UUID
    revision_no: int
    lifecycle: str                      # SUPPORTED | NO_LONGER_SUPPORTED
    night_date: date
    window: FuelBalanceWindow           # the revision the Finding revision cites
    consequence: Mapping[str, Any] | None   # the row's columns (exact text), None when NO_LONGER_SUPPORTED
    created_at: datetime


class FuelFindingReadPort(Protocol):
    def fuel_findings(self, tenant_id: UUID, site_id: UUID, lo: datetime, hi: datetime,
                      known_at: datetime | None) -> tuple[FuelFinding, ...]: ...

    def fuel_finding(self, tenant_id: UUID, site_id: UUID, finding_id: UUID,
                     known_at: datetime | None) -> FuelFinding | None: ...
