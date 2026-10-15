"""Site financial assumption publication: the pure contract (S4-02a phase 1).

`D-2026-10-13-s4-bounded-financial-basis`; packet `tasks/S4-02a-site-assumptions.md` items 1-2.

A publication is one explicitly authored Site price with a stored `change_kind`. This module validates it
(typed 422 refusals), derives the canonical request digest an exact retry is compared against, and plans
how the publication changes the Site/key series' current assignments (typed 409 refusals). It does no I/O:
the PostgreSQL store runs the plan under the series lock with one server instant.

Overlap rules (packet item 2, review C1):
- INITIAL: the first price, or one covering time with no current price. May be backdated. Refused if its
  authored range overlaps any current assignment.
- SUCCESSION: `valid_from` >= the server `recorded_at`. It may only shorten the single open-ended current
  assignment that strictly contains `valid_from`; any other overlap, or none at all, is refused.
- CORRECTION: backdated or bounded, with a reason. Supersedes every current assignment it overlaps and
  re-assigns the uncovered left/right remainders to their same old revisions. Refused if it overlaps nothing
  (that is an INITIAL) or is a future open-ended change (that is a SUCCESSION).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import UUID

ASSUMPTION_KEYS = ("diesel_price_per_litre",)
UNIT = "currency/L"
BASES = ("AUTHORED_ESTIMATE", "CONTRACT_RATE", "RECORDED_PURCHASE")
CHANGE_KINDS = ("INITIAL", "SUCCESSION", "CORRECTION")
SYSTEM_CHANNELS = ("SYSTEM_CLI", "SYSTEM_FIXTURE")


@dataclass(frozen=True)
class SystemPrincipal:
    """The stable server-side service principal. Never taken from a request or a command-line flag."""

    actor_id: str
    authorization_basis: str
    actor_kind: str = "SYSTEM"


SYSTEM_PUBLISHER = SystemPrincipal(
    actor_id="service:assetops-assumption-publisher",
    authorization_basis=("SERVER_ADMINISTRATIVE_TRIGGER: published by the server-side assumption publisher "
                         "run by an operator with database access; no human sign-in exists yet "
                         "(D-2026-10-13-s4-bounded-financial-basis)"))


class PublicationRefused(Exception):
    """A typed refusal: `status` is the HTTP-equivalent code (409 conflict, 422 invalid)."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.status = status
        self.code = code
        self.message = message


@dataclass(frozen=True)
class Publication:
    assumption_key: str
    currency: str
    value: Decimal
    basis: str
    source_reference: str
    valid_from: datetime
    valid_to: datetime | None
    change_kind: str
    correction_reason: str | None
    # Explicit: None means "this is the first revision of the series", never "whatever is latest".
    expected_prior_revision_id: UUID | None
    idempotency_key: str
    channel: str
    provenance: dict[str, Any] = field(default_factory=dict)


def parse_value(raw: str) -> Decimal:
    """An authored decimal string; floats and non-finite or negative values are refused."""
    if not isinstance(raw, str):
        raise PublicationRefused(422, "VALUE_NOT_AUTHORED_DECIMAL", "The price must be an authored decimal string.")
    try:
        value = Decimal(raw.strip())
    except InvalidOperation as error:
        raise PublicationRefused(422, "VALUE_NOT_DECIMAL", f"{raw!r} is not a decimal number.") from error
    return value


def validate(p: Publication) -> None:
    def refuse(code: str, message: str) -> None:
        raise PublicationRefused(422, code, message)

    if p.assumption_key not in ASSUMPTION_KEYS:
        refuse("UNKNOWN_ASSUMPTION_KEY", f"Only {', '.join(ASSUMPTION_KEYS)} is supported.")
    if not (isinstance(p.currency, str) and len(p.currency) == 3 and p.currency.isascii()
            and p.currency.isalpha() and p.currency.isupper()):
        refuse("CURRENCY_NOT_ISO", "Currency must be an ISO 4217 three-letter upper-case code.")
    if not isinstance(p.value, Decimal) or not p.value.is_finite():
        refuse("VALUE_NOT_FINITE", "The price must be a finite authored decimal.")
    if p.value < 0:
        refuse("VALUE_NEGATIVE", "A price per litre cannot be negative.")
    if p.basis not in BASES:
        refuse("BASIS_NOT_OPERATIONAL", f"Basis must be one of {', '.join(BASES)}; a scenario is not published here.")
    if not (p.source_reference or "").strip():
        refuse("SOURCE_REQUIRED", "A source reference is required.")
    for name, at in (("valid_from", p.valid_from), ("valid_to", p.valid_to)):
        if at is not None and (not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None):
            refuse("VALIDITY_NOT_ZONED", f"{name} must be a timezone-aware instant.")
    if p.valid_to is not None and not p.valid_from < p.valid_to:
        refuse("VALIDITY_EMPTY", "valid_from must be before valid_to (half-open, non-empty).")
    if p.change_kind not in CHANGE_KINDS:
        refuse("UNKNOWN_CHANGE_KIND", f"change_kind must be one of {', '.join(CHANGE_KINDS)}.")
    reason = (p.correction_reason or "").strip()
    if p.change_kind == "CORRECTION" and not reason:
        refuse("CORRECTION_REASON_REQUIRED", "A correction must state its reason.")
    if p.change_kind != "CORRECTION" and p.correction_reason is not None:
        refuse("REASON_ONLY_FOR_CORRECTION", "Only a CORRECTION carries a correction reason.")
    if p.channel not in SYSTEM_CHANNELS:
        refuse("CHANNEL_NOT_SYSTEM", "Only the server-side SYSTEM publisher can publish in this slice.")
    if not (p.idempotency_key or "").strip():
        refuse("IDEMPOTENCY_KEY_REQUIRED", "An idempotency key is required.")


# Stored provenance that describes the carrier of a publication, not the publication itself. It stays in the
# stored row but is excluded from the retry digest, so appending a fixture step, re-encoding line endings or
# bumping the fixture file version never turns an already-published step into an idempotency conflict.
PROVENANCE_NOT_DIGESTED = frozenset({"fixture_sha256", "fixture_version"})


def canonical_step_sha256(step: dict[str, Any]) -> str:
    """Digest of one fixture step's canonical JSON: independent of file bytes, line endings and other steps."""
    canonical = json.dumps(step, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def request_sha256(p: Publication, principal: SystemPrincipal, tenant_id: UUID, site_id: UUID) -> str:
    """Digest of everything a retry must repeat exactly; the server instant and new IDs are excluded.

    It covers the canonical publication step and the principal's stable identity. The principal's
    `authorization_basis` prose and the carrier file's bytes/version are stored but not digested."""
    body = {
        "tenant_id": str(tenant_id), "site_id": str(site_id), "assumption_key": p.assumption_key,
        "currency": p.currency, "unit": UNIT, "value": str(p.value), "basis": p.basis,
        "source_reference": p.source_reference,
        "valid_from": p.valid_from.isoformat(), "valid_to": None if p.valid_to is None else p.valid_to.isoformat(),
        "change_kind": p.change_kind, "correction_reason": p.correction_reason,
        "expected_prior_revision_id": None if p.expected_prior_revision_id is None else str(p.expected_prior_revision_id),
        "idempotency_key": p.idempotency_key, "channel": p.channel,
        "provenance": {k: v for k, v in p.provenance.items() if k not in PROVENANCE_NOT_DIGESTED},
        "actor_kind": principal.actor_kind, "actor_id": principal.actor_id,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Current:
    """A current assignment (recorded_to IS NULL) of the series."""

    id: UUID
    revision_id: UUID
    valid_from: datetime
    valid_to: datetime | None


@dataclass(frozen=True)
class NewAssignment:
    """`revision_id` None means the revision being published."""

    revision_id: UUID | None
    valid_from: datetime
    valid_to: datetime | None


@dataclass(frozen=True)
class Plan:
    close: tuple[UUID, ...]
    insert: tuple[NewAssignment, ...]


def _overlaps(a_from: datetime, a_to: datetime | None, b_from: datetime, b_to: datetime | None) -> bool:
    """Half-open `[from, to)` overlap; None is unbounded above."""
    return (b_to is None or a_from < b_to) and (a_to is None or b_from < a_to)


def plan_assignments(change_kind: str, valid_from: datetime, valid_to: datetime | None, recorded_at: datetime,
                     current: list[Current]) -> Plan:
    def conflict(code: str, message: str) -> PublicationRefused:
        return PublicationRefused(409, code, message)

    hit = [c for c in current if _overlaps(c.valid_from, c.valid_to, valid_from, valid_to)]
    own = NewAssignment(None, valid_from, valid_to)
    if change_kind == "INITIAL":
        if hit:
            raise conflict("INITIAL_OVERLAPS_CURRENT",
                           "An INITIAL price may only cover time with no current price; it overlaps "
                           f"{len(hit)} current assignment(s). Publish a SUCCESSION or CORRECTION instead.")
        return Plan((), (own,))
    if change_kind == "SUCCESSION":
        if valid_from < recorded_at:
            raise conflict("SUCCESSION_NOT_FUTURE",
                           "A SUCCESSION takes effect at or after the server recording time; a backdated change "
                           "is a CORRECTION.")
        if not hit:
            raise conflict("SUCCESSION_NOTHING_TO_SUCCEED",
                           "No current price overlaps this range; time with no current price is an INITIAL.")
        only = hit[0]
        if len(hit) != 1 or only.valid_to is not None or not only.valid_from <= valid_from:
            raise conflict("SUCCESSION_OVERLAP_NOT_PERMITTED",
                           "A SUCCESSION may only shorten or replace the single open-ended current assignment "
                           "containing its valid_from; this range overlaps other current validity.")
        if only.valid_from == valid_from:
            # Equal-start succession (Architect S4-02 Q1): the scheduled price is replaced from its own
            # start, so there is no left remainder; a zero-length [t, t) row is never written.
            return Plan((only.id,), (own,))
        return Plan((only.id,), (NewAssignment(only.revision_id, only.valid_from, valid_from), own))
    if change_kind == "CORRECTION":
        if valid_to is None and valid_from >= recorded_at:
            raise conflict("CORRECTION_NOT_BACKDATED_OR_BOUNDED",
                           "A future open-ended change is a SUCCESSION; a CORRECTION is backdated or bounded.")
        if not hit:
            raise conflict("CORRECTION_NOTHING_TO_CORRECT",
                           "No current price overlaps this range; time with no current price is an INITIAL.")
        inserts: list[NewAssignment] = []
        for c in sorted(hit, key=lambda c: c.valid_from):
            if c.valid_from < valid_from:
                inserts.append(NewAssignment(c.revision_id, c.valid_from, valid_from))
            if valid_to is not None and (c.valid_to is None or valid_to < c.valid_to):
                inserts.append(NewAssignment(c.revision_id, valid_to, c.valid_to))
        return Plan(tuple(c.id for c in hit), (*inserts, own))
    raise PublicationRefused(422, "UNKNOWN_CHANGE_KIND", f"Unknown change_kind {change_kind!r}.")
