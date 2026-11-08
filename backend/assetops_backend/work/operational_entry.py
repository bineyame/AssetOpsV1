"""OWN-G3a: the operational entry mapping (build sheet OWN-GAPS-2026-11-08 §3.2, Rev 1, R2-G3a).

`POST /api/sites/{site_code}/work/operational-entries` takes a closed screen entry and the server composes the
`operational-record-1` command that `WorkService.post_operational_record` already validates, hashes and stores. The
browser never sends an actor: records are written by the server-configured entry service `service:operator-entry`
(§3.1), labelled "Entered by site admin" on screen. Pure: no I/O.

`validate_entry` is §3.2's shape steps 1-5 (the route runs it before reading the Site's tank and time zone);
`compose_entry` validates again and maps. The body literals are K7's (`tools/demo_combined_kisiwa.py:201-203`).
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID
from zoneinfo import ZoneInfo

from assetops_backend.work import model as m
from assetops_backend.work.model import WorkRefused, WorkStoreUnavailable

ENTRY_PRINCIPAL = "service:operator-entry"
ENTRY_ATTESTATION = "service=operator-entry;job=site-admin-entry;rule=oprec-entry/1"
ENTRY_ACTOR = {"kind": "SERVICE", "id": ENTRY_PRINCIPAL, "attestation": ENTRY_ATTESTATION}

ENTRY_KEYS = ("entry", "value", "taken_at_local", "ticket_reference", "idempotency_key")
ENTRIES = ("TANK_DIP", "FUEL_DELIVERY", "STOCK_IN_CHAMBER", "METER_READING")
FUEL_ENTRIES = ("TANK_DIP", "FUEL_DELIVERY")

VALUE = re.compile(r"[0-9]{1,6}(?:\.[0-9]{1,3})?")
TAKEN_AT = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}")
TICKET = re.compile(r"[A-Za-z0-9][A-Za-z0-9 /._-]{0,39}")
KEY = re.compile(r"oprec-entry-[0-9a-f]{32}")

#: K7's record literals, verbatim (`tools/demo_combined_kisiwa.py:201-203`), plus the two reading bodies (§3.2 table).
DIP_BODY = "Tank dip at the {hhmm} round: {value} L."
DELIVERY_BODY = "Fuel delivery of {value} L received, ticket {reference}."
TICKET_TEXT = "Fuel delivery ticket {reference}, {value} L"
STOCK_BODY = "Stock in chamber: {value} kg."
METER_BODY = "Meter reading: {value} kWh."


def _invalid() -> WorkRefused:
    return WorkRefused("OPREC_ENTRY_INVALID")


def validate_entry(body: Any) -> dict[str, Any]:
    """§3.2 validation steps 1-5 in order (R2-G3a 4): all five keys, no other; the first failing step refuses.
    Returns `{entry, value, taken_at, hhmm, ticket, key}` with `value` as `m.decimal_text` (R2-G3a 3)."""
    if not isinstance(body, dict) or set(body) != set(ENTRY_KEYS):
        raise _invalid()
    entry = body["entry"]
    if not isinstance(entry, str) or entry not in ENTRIES:  # step 1
        raise _invalid()
    raw = body["value"]  # step 2
    if not isinstance(raw, str) or VALUE.fullmatch(raw) is None:
        raise _invalid()
    number = Decimal(raw)
    if entry == "FUEL_DELIVERY" and not number > 0:
        raise _invalid()
    taken = body["taken_at_local"]  # step 3
    if not isinstance(taken, str) or TAKEN_AT.fullmatch(taken) is None:
        raise _invalid()
    try:
        local = datetime.strptime(taken, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise _invalid() from None
    ticket = body["ticket_reference"]  # step 4
    if entry == "FUEL_DELIVERY":
        if ticket is None:
            raise WorkRefused("OPREC_ENTRY_TICKET_REQUIRED")
        if not isinstance(ticket, str) or TICKET.fullmatch(ticket) is None:
            raise _invalid()
    elif ticket is not None:
        raise _invalid()
    key = body["idempotency_key"]  # step 5
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise _invalid()
    return {"entry": entry, "value": m.decimal_text(number), "local": local, "hhmm": taken[11:16],
            "ticket": ticket, "key": key}


def occurred_utc(local: datetime, zone: str) -> str:
    """The typed Site-local minute in the Site's time zone (zoneinfo, fold 0) as a UTC wire instant."""
    instant = local.replace(tzinfo=ZoneInfo(zone), fold=0).astimezone(timezone.utc)
    return instant.strftime("%Y-%m-%dT%H:%M:%SZ")


def entry_site_context(night_context: Callable[[UUID, UUID], tuple[Any, Any, Any]]
                       ) -> Callable[[UUID, UUID], tuple[str, str | None]]:
    """R2-G3a 2: the route's `site_context` over the fuel-balance store's `night_context` (instant dropped). A store
    failure (the driver's errors, the no-URL `RuntimeError`) is `WorkStoreUnavailable` (503); a programming error is
    not. The driver is not named here: storage technology stays in the adapters (`night_read.py` `_guard` pattern)."""
    def site_context(tenant_id: UUID, site_id: UUID) -> tuple[str, str | None]:
        try:
            zone, tank_id, _ = night_context(tenant_id, site_id)
        except (ValueError, TypeError, KeyError, AttributeError):
            raise
        except Exception as error:
            raise WorkStoreUnavailable(f"The Site context read failed: {error.__class__.__name__}") from error
        return zone, tank_id
    return site_context


def compose_entry(body: Any, zone: str, tank_id: str | None) -> dict[str, Any]:
    """The `operational-record-1` command for one validated entry (§3.2 server mapping). A fuel entry with no single
    active tank is 422 `OPREC_ENTRY_NO_TANK`."""
    e = validate_entry(body)
    entry, value = e["entry"], e["value"]
    if entry in FUEL_ENTRIES and tank_id is None:
        raise WorkRefused("OPREC_ENTRY_NO_TANK")
    digest = None
    if entry == "TANK_DIP":
        kind, unit, text = "TANK_DIP", "L", DIP_BODY.format(hhmm=e["hhmm"], value=value)
    elif entry == "FUEL_DELIVERY":
        kind, unit = "FUEL_DELIVERY", "L"
        text = DELIVERY_BODY.format(value=value, reference=e["ticket"])
        digest = hashlib.sha256(TICKET_TEXT.format(reference=e["ticket"], value=value).encode("ascii")).hexdigest()
    elif entry == "STOCK_IN_CHAMBER":
        kind, unit, text = "MANUAL_READING", "kg", STOCK_BODY.format(value=value)
    else:
        kind, unit, text = "MANUAL_READING", "kWh", METER_BODY.format(value=value)
    command = {"kind": kind, "body": text, "occurred_at": occurred_utc(e["local"], zone), "period_end": None,
               "unit": unit, "quantity": value, "source_document_sha256": digest, "case_id": None,
               "actor": dict(ENTRY_ACTOR), "idempotency_key": e["key"]}
    if entry in FUEL_ENTRIES:
        command["asset_id"] = tank_id
    return command
