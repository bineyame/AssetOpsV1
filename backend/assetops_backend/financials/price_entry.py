"""PR-3 (D-PRICE.1): a price typed on the Site price page, validated and derived on the server. Pure: no I/O.

Design: `.agent/architect-sequence-client-scope-2026-11-11.md` revision 5, §5.3. The browser sends a closed body
(`ENTRY_FIELDS`); it never sends an actor, a change kind or an instant. `validate_entry` is refusal step 6 (shape, every
failing field named) and step 7 (a known future key); `derive` is step 9 (Site-local midnight, the bounds, currency,
change kind and the reason rule). The route (`financial_api.py`) runs the steps in order and publishes through the
assumption store with `SITE_ADMIN_PRICE_PUBLISHER` on `SITE_ADMIN_CHANNEL`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.financials.assumptions import (
    BASES, ISO_4217, SITE_ADMIN_PROVENANCE, Current, plan_assignments)
from assetops_backend.outcomes.price_action import PRICE_NOUN, STORED_KEYS

REQUIRED_FIELDS = ("key", "value", "currency", "basis", "source", "applies_from", "idempotency_key")
OPTIONAL_FIELDS = ("reason", "dry_run")
ENTRY_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS

VALUE = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,4})?")
DAY = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
KEY = re.compile(r"price-entry-[0-9a-f]{32}")
CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")
SOURCE_MAX, REASON_MAX = 120, 200
DAYS_BACK, DAYS_AHEAD = 400, 366

SET_BY = "Entered by site admin"
#: The per-unit word of a stored key's unit (`assumptions.UNITS`).
UNIT_WORD = {"currency/L": "litre", "currency/kWh": "kWh"}

MESSAGES = {
    "PRICE_ENTRY_OFF": "Saving prices is switched off on this server.",
    "PRICE_ENTRY_INVALID": "Some fields are missing or not valid.",
    "PRICE_KEY_NOT_ENTERABLE": "No figure uses this price yet, so it cannot be saved here.",
    "APPLIES_FROM_OUT_OF_RANGE": "The date must be within 400 days before and 366 days after today at this site.",
    "CURRENCY_DIFFERS": "This site's {noun} is kept in {currency}.",
    "REASON_REQUIRED": "This date changes figures already shown. Say why.",
}

SUMMARY = {
    "INITIAL": "First {noun} for {site}: {value} {currency} per {unit} from {date}. Figures from that date get a price.",
    "SUCCESSION": "New {noun} from {date}. Earlier figures keep the current price.",
    "CORRECTION": "Correction from {date}. Figures from {date} are recalculated with this price; the earlier version "
                  "is kept in the history.",
}
SAVED = ("Saved. {Noun} {value} {currency} per {unit} from {date}. Figures that use it read \"Updating…\" for a few "
         "minutes, then show the new price.")


class EntryRefused(Exception):
    """A typed 422 refusal of the entry route; `fields` names the failing fields of a shape refusal."""

    def __init__(self, code: str, message: str | None = None, fields: list[str] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.message = message or MESSAGES[code]
        self.fields = fields

    def detail(self) -> dict[str, Any]:
        body: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.fields is not None:
            body["fields"] = self.fields
        return body


@dataclass(frozen=True)
class Entry:
    key: str
    value: Decimal
    value_text: str
    currency: str
    basis: str
    source: str
    applies_from: date
    reason: str | None
    dry_run: bool
    idempotency_key: str


def _text(raw: Any, limit: int) -> str | None:
    if not isinstance(raw, str) or CONTROL.search(raw):
        return None
    trimmed = raw.strip()
    return trimmed if 1 <= len(trimmed) <= limit else None


def validate_entry(body: Any) -> Entry:
    """Steps 6 and 7. A body that is not an object names no field; otherwise every failing field is named, an unknown
    field included. A known key (PR-1 `PRICE_NOUN`) outside `STORED_KEYS` is `PRICE_KEY_NOT_ENTERABLE`."""
    if not isinstance(body, dict):
        raise EntryRefused("PRICE_ENTRY_INVALID", fields=[])
    bad = [name for name in body if name not in ENTRY_FIELDS]
    bad += [name for name in REQUIRED_FIELDS if name not in body]
    key = body.get("key")
    if "key" in body and not (isinstance(key, str) and key in PRICE_NOUN):
        bad.append("key")
    raw = body.get("value")
    if "value" in body and not (isinstance(raw, str) and VALUE.fullmatch(raw) and Decimal(raw) > 0):
        bad.append("value")
    currency = body.get("currency")
    if "currency" in body and not (isinstance(currency, str) and currency in ISO_4217):
        bad.append("currency")
    basis = body.get("basis")
    if "basis" in body and not (isinstance(basis, str) and basis in BASES):
        bad.append("basis")
    source = _text(body.get("source"), SOURCE_MAX)
    if "source" in body and source is None:
        bad.append("source")
    day = body.get("applies_from")
    applies: date | None = None
    if isinstance(day, str) and DAY.fullmatch(day):
        try:
            applies = date.fromisoformat(day)
        except ValueError:
            applies = None
    if "applies_from" in body and applies is None:
        bad.append("applies_from")
    reason = body.get("reason")
    if reason is not None:
        reason = _text(reason, REASON_MAX)
        if reason is None:
            bad.append("reason")
    dry_run = body.get("dry_run", False)
    if not isinstance(dry_run, bool):
        bad.append("dry_run")
    idem = body.get("idempotency_key")
    if "idempotency_key" in body and not (isinstance(idem, str) and KEY.fullmatch(idem)):
        bad.append("idempotency_key")
    if bad:
        raise EntryRefused("PRICE_ENTRY_INVALID", fields=list(dict.fromkeys(bad)))
    if key not in STORED_KEYS:
        raise EntryRefused("PRICE_KEY_NOT_ENTERABLE")
    return Entry(key, Decimal(raw), raw, currency, basis, source, applies, reason, dry_run, idem)


def site_today(now: datetime, zone: ZoneInfo) -> date:
    return now.astimezone(zone).date()


def local_midnight_utc(day: date, zone: ZoneInfo) -> datetime:
    """`valid_from`: Site-local midnight of `day` (fold 0), as UTC."""
    return datetime.combine(day, time(0), tzinfo=zone).astimezone(timezone.utc)


@dataclass(frozen=True)
class Derived:
    valid_from: datetime
    change_kind: str
    reason_required: bool
    expected_prior_revision_id: UUID | None
    current: tuple[Current, ...]


def series_state(snapshot: dict[str, Any]) -> tuple[list[Current], dict[str, Any] | None]:
    """The current assignments and the head revision of a current `store.snapshot` read. The head is the highest
    revision cited by a current assignment: every publication's own assignment stays current until a later one is
    published, so the head always cites itself (`publication_revision_id`)."""
    current = [Current(a["id"], a["revision_id"], a["valid_from"], a["valid_to"]) for a in snapshot["timeline"]]
    cited = list(snapshot["cited"].values()) + list(snapshot["revisions"])
    head = max(cited, key=lambda r: r["revision_no"]) if cited else None
    return current, head


def derive(entry: Entry, zone: ZoneInfo, now: datetime, snapshot: dict[str, Any], *, require_reason: bool) -> Derived:
    """Step 9: bounds, currency, change kind, then the reason rule (skipped for a dry run, which reports it)."""
    today = site_today(now, zone)
    if not today - timedelta(days=DAYS_BACK) <= entry.applies_from <= today + timedelta(days=DAYS_AHEAD):
        raise EntryRefused("APPLIES_FROM_OUT_OF_RANGE")
    current, head = series_state(snapshot)
    if head is not None and head["currency"] != entry.currency:
        raise EntryRefused("CURRENCY_DIFFERS", MESSAGES["CURRENCY_DIFFERS"].format(
            noun=PRICE_NOUN[entry.key], currency=head["currency"]))
    valid_from = local_midnight_utc(entry.applies_from, zone)
    overlaps = [c for c in current if c.valid_to is None or valid_from < c.valid_to]
    if not overlaps:
        kind = "INITIAL"
    elif valid_from >= now:
        kind = "SUCCESSION"
    else:
        kind = "CORRECTION"
    reason_required = kind == "CORRECTION"
    if reason_required and require_reason and entry.reason is None:
        raise EntryRefused("REASON_REQUIRED")
    return Derived(valid_from, kind, reason_required, None if head is None else head["id"], tuple(current))


def plan(derived: Derived, now: datetime) -> None:
    """The store's pure plan over the read series; its `PublicationRefused` (409) passes through unchanged."""
    plan_assignments(derived.change_kind, derived.valid_from, None, now, list(derived.current))


def correction_and_provenance(entry: Entry, change_kind: str) -> tuple[str | None, dict[str, Any]]:
    """A CORRECTION stores the reason as `correction_reason`; any other kind keeps a sent reason as `entry_note`."""
    provenance = dict(SITE_ADMIN_PROVENANCE)
    if change_kind == "CORRECTION":
        return entry.reason, provenance
    if entry.reason is not None:
        provenance["entry_note"] = entry.reason
    return None, provenance


def day_words(day: date) -> str:
    """`d MMM yyyy`, e.g. "10 Nov 2026"."""
    return f"{day.day} {day.strftime('%b')} {day.year}"


def _words(entry: Entry, unit: str, site: str) -> dict[str, str]:
    noun = PRICE_NOUN[entry.key]
    return {"noun": noun, "Noun": noun[:1].upper() + noun[1:], "site": site, "value": entry.value_text,
            "currency": entry.currency, "unit": UNIT_WORD[unit], "date": day_words(entry.applies_from)}


def dry_run_summary(entry: Entry, change_kind: str, unit: str, site: str) -> str:
    return SUMMARY[change_kind].format(**_words(entry, unit, site))


def saved_summary(entry: Entry, unit: str, site: str) -> str:
    return SAVED.format(**_words(entry, unit, site))
