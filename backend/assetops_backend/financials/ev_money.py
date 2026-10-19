"""W2-07 commit 2: the pure EV gross tariff scenario (`ev-gross-tariff/1`), no SQL driver.

`.agent/W2-07-build-spec.md` commit 1 "Use exact SHA row forms", "Commits 2-3" price state table and the
post-W2-06 reconciliation (exact selected `ev-session/1` window only), with the q1 R2 two-clock tariff contract,
the R5 precedence table and R6 composition table, and the q3 R8 ruling and C1-C5 confirmations:

- R8: an overlapping PENDING/LEASED/FAILED `ev_charging` job is a retryable refusal (`ERROR_PENDING`), never a
  stored WITHHELD/PENDING_RECOMPUTE revision; the worker checks it before `derive`. STALE_BASIS and
  HISTORICAL_CURRENT_CLAIM are read guards only and are never derived here.
- C1: the technical hash's `known_at` is the selected run's `knowledge_cutoff`.
- C2: technical rows are the deduplicated SUPPORT meter intervals of every selected session revision (excluded
  incomplete sessions too); only the priced eligible sessions/intervals are linked.
- C3: `TARIFF_MISSING` only when no current EV assignment covers any eligible interval; partial coverage, a gap or a
  revision/currency/unit change is `PRICE_GAP_OR_CHANGE`.
- C5: `source_gate` is the S4-05 class of the selected assessment's exact accepted IDs; a non-assessable class or a
  mismatch with the selected stored class is `WITHHELD/SOURCE_GATE`.

Amounts are exact `Decimal` products; nothing is rounded for storage or hashing.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from assetops_backend.financials.fuel_cost import iso, sha256_canonical

FORMULA_VERSION = "ev-gross-tariff/1"
TARIFF_KEY = "ev_gross_tariff_per_kwh"
TARIFF_UNIT = "currency/kWh"
ASSESSABLE_CLASSES = ("REGISTERED_SIMULATION", "AUTHORED_DEMONSTRATION")
ELIGIBLE_STATES = ("COMPLETED", "OBSERVED_ABORT")
ERROR_PENDING = "PENDING_RECOMPUTE"

ESTIMATED, UNPRICED, WITHHELD = "ESTIMATED", "UNPRICED", "WITHHELD"
ELIGIBLE = "ELIGIBLE_COMPLETE_INTERVALS"
SOURCE_GATE = "SOURCE_GATE"
CONTRADICTORY = "CONTRADICTORY_EVIDENCE"
INCOMPLETE = "INCOMPLETE_ENERGY"
TARIFF_MISSING = "TARIFF_MISSING"
PRICE_GAP = "PRICE_GAP_OR_CHANGE"


@dataclass(frozen=True)
class SessionHead:
    revision_id: str
    basis_sha256: str
    state: str
    supported_kwh: Decimal | None
    unknown_meter_seconds: int | None

    @property
    def energy_complete(self) -> bool | None:
        """The W2-06 read rule (`analytics/ev_reads.energy_complete`) on the stored revision."""
        if self.state == "CONTRADICTORY":
            return None
        if self.state == "INCOMPLETE":
            return False
        return self.supported_kwh is not None and self.unknown_meter_seconds == 0


@dataclass(frozen=True)
class MeterInterval:
    session_revision_id: str
    connector_asset_id: str
    evidence_id: str
    content_sha256: str
    start_at: datetime
    end_at: datetime
    kwh: Decimal
    use: str
    reason: str | None


@dataclass(frozen=True)
class TariffAssignment:
    revision_id: str
    value: Decimal
    currency: str
    unit: str
    valid_from: datetime
    valid_to: datetime | None
    recorded_at: datetime

    def covers(self, start_at: datetime, end_at: datetime) -> bool:
        return self.valid_from <= start_at and (self.valid_to is None or end_at <= self.valid_to)


@dataclass(frozen=True)
class EvMoneyBasis:
    tenant_id: str
    site_id: str
    window_start: datetime
    window_end: datetime
    known_at: datetime  # C1: the selected run's knowledge_cutoff
    assessment_revision_id: str
    source_class: str | None  # the selected stored class (`result.source_provenance.class`)
    source_gate: str  # C5: S4-05 class of the selected exact accepted IDs
    sessions: tuple[SessionHead, ...]
    intervals: tuple[MeterInterval, ...]  # every ev_meter_interval row of the selected session revisions
    tariffs: tuple[TariffAssignment, ...]  # current (`recorded_to IS NULL`) EV assignments at the Site


@dataclass(frozen=True)
class EvConsequence:
    assessment_revision_id: str
    window_start: datetime
    window_end: datetime
    state: str
    reason: str
    quantity_kwh: Decimal | None
    tariff_revision_id: str | None
    tariff_value: Decimal | None
    currency: str | None
    amount: Decimal | None
    source_gate: str
    overlap_group: str
    technical_input_sha256: str
    basis_sha256: str
    sessions: tuple[tuple[str, Decimal], ...]  # (session revision ID, included kWh), priced eligible only
    evidence_ids: tuple[str, ...]  # priced eligible meter evidence only


def technical_rows(basis: EvMoneyBasis) -> list[list]:
    """C2 rows `[session_revision_id, session_basis_sha256, meter_evidence_id, content_sha256, interval_start,
    interval_end, kwh]`, sorted by session revision ID then interval start/evidence ID, deduplicated by accepted
    evidence ID (the first in that order is kept)."""
    sessions = {s.revision_id: s for s in basis.sessions}
    support = sorted((i for i in basis.intervals if i.use == "SUPPORT"),
                     key=lambda i: (i.session_revision_id, i.start_at, i.evidence_id))
    seen: set[str] = set()
    rows = []
    for i in support:
        if i.evidence_id in seen:
            continue
        seen.add(i.evidence_id)
        rows.append([i.session_revision_id, sessions[i.session_revision_id].basis_sha256, i.evidence_id,
                     i.content_sha256, iso(i.start_at), iso(i.end_at), i.kwh])
    return rows


def technical_input_sha256(basis: EvMoneyBasis) -> str:
    return sha256_canonical([iso(basis.window_start), iso(basis.window_end), iso(basis.known_at),
                             technical_rows(basis)])


def consequence_basis_sha256(technical: str, tariff: TariffAssignment | None, source_class: str | None,
                             source_gate: str, assessment_revision_ids: Sequence[str]) -> str:
    return sha256_canonical([technical, None if tariff is None else tariff.revision_id,
                             None if tariff is None else tariff.value, None if tariff is None else tariff.currency,
                             source_class, source_gate, sorted(assessment_revision_ids), FORMULA_VERSION])


def overlap_group(tenant_id: str, site_id: str, window_start: datetime, window_end: datetime,
                  tariff_revision_id: str | None) -> str:
    return "ev:" + sha256_canonical([tenant_id, site_id, iso(window_start), iso(window_end),
                                     tariff_revision_id or "NO_TARIFF"])


def conflicts(basis: EvMoneyBasis) -> bool:
    """R5/R6 contradiction anywhere in the selected window: a CONTRADICTORY session, an accepted meter interval
    excluded for overlap, one accepted interval ID supporting two sessions, or overlapping supported intervals of
    distinct IDs on one connector."""
    if any(s.state == "CONTRADICTORY" for s in basis.sessions):
        return True
    if any(i.use == "EXCLUDED" and i.reason == "METER_OVERLAP" for i in basis.intervals):
        return True
    support = [i for i in basis.intervals if i.use == "SUPPORT"]
    owners: dict[str, set[str]] = {}
    for i in support:
        owners.setdefault(i.evidence_id, set()).add(i.session_revision_id)
    if any(len(v) > 1 for v in owners.values()):
        return True
    for n, a in enumerate(support):
        for b in support[n + 1:]:
            if (a.evidence_id != b.evidence_id and a.connector_asset_id == b.connector_asset_id
                    and a.start_at < b.end_at and b.start_at < a.end_at):
                return True
    return False


def select_tariff(intervals: Sequence[MeterInterval],
                  tariffs: Sequence[TariffAssignment]) -> tuple[TariffAssignment | None, str | None]:
    """R2/C3: one current assignment must cover every eligible half-open interval entirely, with one revision,
    currency and the EV unit. Returns `(tariff, None)` or `(None, TARIFF_MISSING | PRICE_GAP_OR_CHANGE)`."""
    covering = [[t for t in tariffs if t.covers(i.start_at, i.end_at)] for i in intervals]
    if all(not c for c in covering):
        return None, TARIFF_MISSING
    if any(len(c) != 1 for c in covering):
        return None, PRICE_GAP
    chosen = [c[0] for c in covering]
    if (len({t.revision_id for t in chosen}) != 1 or len({t.currency for t in chosen}) != 1
            or len({t.value for t in chosen}) != 1 or any(t.unit != TARIFF_UNIT for t in chosen)):
        return None, PRICE_GAP
    return chosen[0], None


def derive(basis: EvMoneyBasis) -> EvConsequence | None:
    """The one Site/window consequence of an exact settled selection, or None when no qualifying session exists
    (no fictional zero consequence). The R5 rows apply in priority order; the pending row is the worker's refusal."""
    if not basis.sessions:
        return None
    technical = technical_input_sha256(basis)

    def made(state: str, reason: str, quantity: Decimal | None = None, tariff: TariffAssignment | None = None,
             priced: Sequence[MeterInterval] = ()) -> EvConsequence:
        amount = None if state != ESTIMATED else quantity * tariff.value
        priced = priced if state == ESTIMATED else ()  # C2: only priced eligible sessions/intervals are linked
        per: dict[str, Decimal] = {}
        for i in priced:
            per[i.session_revision_id] = per.get(i.session_revision_id, Decimal(0)) + i.kwh
        return EvConsequence(
            assessment_revision_id=basis.assessment_revision_id, window_start=basis.window_start,
            window_end=basis.window_end, state=state, reason=reason, quantity_kwh=quantity,
            tariff_revision_id=None if tariff is None else tariff.revision_id,
            tariff_value=None if tariff is None else tariff.value,
            currency=None if state != ESTIMATED else tariff.currency, amount=amount, source_gate=basis.source_gate,
            overlap_group=overlap_group(basis.tenant_id, basis.site_id, basis.window_start, basis.window_end,
                                        None if tariff is None else tariff.revision_id),
            technical_input_sha256=technical,
            basis_sha256=consequence_basis_sha256(technical, tariff, basis.source_class, basis.source_gate,
                                                  [basis.assessment_revision_id]),
            sessions=tuple(sorted(per.items())), evidence_ids=tuple(sorted({i.evidence_id for i in priced})))

    if basis.source_gate not in ASSESSABLE_CLASSES or basis.source_gate != basis.source_class:
        return made(WITHHELD, SOURCE_GATE)
    if conflicts(basis):
        return made(WITHHELD, CONTRADICTORY)
    eligible = {s.revision_id for s in basis.sessions
                if s.state in ELIGIBLE_STATES and s.energy_complete is True}
    if not eligible:
        return made(UNPRICED, INCOMPLETE)
    priced = sorted((i for i in basis.intervals if i.use == "SUPPORT" and i.session_revision_id in eligible),
                    key=lambda i: (i.start_at, i.evidence_id))
    quantity = sum((i.kwh for i in priced), Decimal(0))
    tariff, gap = select_tariff(priced, basis.tariffs)
    if tariff is None:
        return made(UNPRICED, gap, quantity, None, priced)
    return made(ESTIMATED, ELIGIBLE, quantity, tariff, priced)
