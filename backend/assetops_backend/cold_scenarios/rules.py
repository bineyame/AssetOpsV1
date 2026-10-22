"""W5-01b C4: the authored cold scenario command rules (`.agent/W5-01-build-spec.md` C4 card and pre-flight rulings
P-C4-7..23).

`cold-scenario-authored/1` allows one `kind`, `STOCK_VALUE_CONTEXT`, whose only assumption object is
`{stock_quantity, stock_unit, unit_value, currency}`. It is an authored what-if beside the selected observed W2 cold
window: no calculated amount, spoilage rule, comparison delta or outcome exists here, and one body currency asks
for no conversion. Pure functions; no SQL and no clock.
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from assetops_backend.mini_decisions.model import MESSAGES as DECISION_MESSAGES
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.work import model as work
from assetops_backend.work.model import WorkRefused

SCHEMA_COMMAND = "cold-scenario-command-1"
SCHEMA_WRITE = "cold-scenario-write-1"
SCHEMA_LIST = "cold-scenarios-1"
KIND = "STOCK_VALUE_CONTEXT"
FORMULA_VERSION = "AUTHORED_ONLY/1"
ROUTE = "cold/financials/scenarios"
PAGE_DEFAULT, PAGE_MAX = 50, 100
ASSUMPTION_KEYS = ("stock_quantity", "stock_unit", "unit_value", "currency")
BASIS_KEYS = ("from", "to", "cutoff", "assessment_revision_ids", "accepted_evidence_ids", "foundation_revision_id",
              "source_provenance")
ROOT_KEYS = ("schema_version", "idempotency_key", "actor", "name", "kind", "assumptions")
CORRECTION_KEYS = ROOT_KEYS + ("supersedes_revision_id", "correction_reason")

#: P-C4-15..20: an exact positive decimal string, verbatim; no sign, exponent, `.5`, `5.` or leading zero.
DECIMAL = re.compile(r"^(?:0|[1-9][0-9]{0,17})(?:\.[0-9]{1,8})?$")
CURRENCY = re.compile(r"^[A-Z]{3}$")
#: ISO 4217 list one (current currency, fund and special codes); membership, never coercion.
ISO_4217 = frozenset("""
AED AFN ALL AMD AOA ARS AUD AWG AZN BAM BBD BDT BGN BHD BIF BMD BND BOB BOV BRL BSD BTN BWP BYN BZD CAD CDF CHE
CHF CHW CLF CLP CNY COP COU CRC CUP CVE CZK DJF DKK DOP DZD EGP ERN ETB EUR FJD FKP GBP GEL GHS GIP GMD GNF GTQ
GYD HKD HNL HTG HUF IDR ILS INR IQD IRR ISK JMD JOD JPY KES KGS KHR KMF KPW KRW KWD KYD KZT LAK LBP LKR LRD LSL
LYD MAD MDL MGA MKD MMK MNT MOP MRU MUR MVR MWK MXN MXV MYR MZN NAD NGN NIO NOK NPR NZD OMR PAB PEN PGK PHP PKR
PLN PYG QAR RON RSD RUB RWF SAR SBD SCR SDG SEK SGD SHP SLE SOS SRD SSP STN SVC SYP SZL THB TJS TMT TND TOP TRY
TTD TWD TZS UAH UGX USD USN UYI UYU UYW UZS VED VES VND VUV WST XAF XAG XAU XBA XBB XBC XBD XCD XCG XDR XOF XPD
XPF XPT XSU XTS XUA XXX YER ZAR ZMW ZWG
""".split())

#: P-C4-7..14: the new C4 refusal literals; `DECISION_*` reuse `mini_decisions.model.MESSAGES`.
MESSAGES = {
    "COLD_SCENARIO_INVALID": "The cold scenario request or selected basis is invalid.",
    "COLD_SCENARIO_CURSOR_INVALID": "The cold scenario cursor is invalid.",
    "COLD_SCENARIO_CURSOR_BASIS_CHANGED": "The selected cold scenario basis changed. Start at the first page.",
    "COLD_SCENARIO_IDEMPOTENCY_CONFLICT": "This idempotency key belongs to a different cold scenario request.",
    "COLD_SCENARIO_REVISION_CONFLICT": "The cold scenario has a newer revision. Reload it before correcting.",
    "COLD_LIMIT_INVALID": "Limit must be an integer from 1 to 100.",
}
STATUS = {
    "COLD_SCENARIO_INVALID": 422, "COLD_SCENARIO_CURSOR_INVALID": 422, "COLD_SCENARIO_CURSOR_BASIS_CHANGED": 409,
    "COLD_SCENARIO_IDEMPOTENCY_CONFLICT": 409, "COLD_SCENARIO_REVISION_CONFLICT": 409, "COLD_LIMIT_INVALID": 422,
}


def refused(code: str, message: str | None = None, status: int | None = None) -> DecisionRefused:
    """A C4 refusal in the shared `DecisionRefused` carrier (C4 literal, else the mini-decision literal)."""
    if code in MESSAGES:
        return DecisionRefused(code, message or MESSAGES[code], status or STATUS[code])
    return DecisionRefused(code, message or DECISION_MESSAGES.get(code), status)


def invalid() -> DecisionRefused:
    return refused("COLD_SCENARIO_INVALID")


def _shape(fn, *args: Any) -> Any:
    """A W4-01 validator (imported, not copied) with its refusal mapped to `COLD_SCENARIO_INVALID`."""
    try:
        return fn(*args)
    except WorkRefused:
        raise invalid() from None


def scenario_code(public_no: int) -> str:
    """`CSCN-` plus at least six zero-padded decimal digits."""
    return f"CSCN-{int(public_no):06d}"


def positive_decimal(value: Any) -> str:
    if not isinstance(value, str) or DECIMAL.match(value) is None or not Decimal(value) > 0:
        raise invalid()
    return value


def stock_unit(value: Any) -> str:
    """Trimmed, 1..64 printable non-control characters."""
    if not isinstance(value, str):
        raise invalid()
    trimmed = value.strip()
    if not 1 <= len(trimmed) <= 64 or not trimmed.isprintable():
        raise invalid()
    return trimmed


def currency(value: Any) -> str:
    if not isinstance(value, str) or CURRENCY.match(value) is None or value not in ISO_4217:
        raise invalid()
    return value


def assumptions(value: Any) -> dict[str, str]:
    a = _shape(work.closed, value, ASSUMPTION_KEYS)
    return {"stock_quantity": positive_decimal(a["stock_quantity"]), "stock_unit": stock_unit(a["stock_unit"]),
            "unit_value": positive_decimal(a["unit_value"]), "currency": currency(a["currency"])}


def actor_of(body: Any) -> dict[str, Any]:
    """The closed actor object, read before the rest of the body so the actor policy answers first."""
    if not isinstance(body, dict) or "actor" not in body:
        raise invalid()
    actor = _shape(work.actor_shape, body["actor"])
    return {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]}


def parse_command(body: Any, *, correction: bool) -> dict[str, Any]:
    """The closed `cold-scenario-command-1` body, canonical (trimmed text, verbatim decimal strings)."""
    b = _shape(work.closed, body, CORRECTION_KEYS if correction else ROOT_KEYS)
    if b["schema_version"] != SCHEMA_COMMAND or b["kind"] != KIND:
        raise invalid()
    cmd: dict[str, Any] = {
        "schema_version": SCHEMA_COMMAND, "idempotency_key": _shape(work.idempotency_key, b["idempotency_key"]),
        "actor": actor_of(b), "name": _shape(work.text_value, b["name"], 1, 160), "kind": KIND,
        "assumptions": assumptions(b["assumptions"])}
    if correction:
        cmd["supersedes_revision_id"] = _shape(work.uuid_text, b["supersedes_revision_id"]).lower()
        cmd["correction_reason"] = _shape(work.text_value, b["correction_reason"], 1, 2000)
    return cmd


def _sha(value: Any) -> str:
    return hashlib.sha256(work.canonical_json(value).encode("utf-8")).hexdigest()


def _command(cmd: Mapping[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in cmd.items() if k != "idempotency_key"}


def create_sha256(cmd: Mapping[str, Any], site_id: UUID, lo: str, hi: str, cutoff: str | None) -> str:
    """P-C4-22: `{command, site_id, window:{from,to,cutoff}}`; the root `create_payload_sha256` and revision 1's
    `payload_sha256`."""
    return _sha({"command": _command(cmd), "site_id": str(site_id).lower(),
                 "window": {"from": lo, "to": hi, "cutoff": cutoff}})


def correction_sha256(cmd: Mapping[str, Any], root_id: str, lo: str, hi: str, cutoff: str | None) -> str:
    """P-C4-22: the corrected body, the root ID and the resolved same root window and cutoff."""
    return _sha({"command": _command(cmd), "root_id": str(root_id).lower(),
                 "window": {"from": lo, "to": hi, "cutoff": cutoff}})


def basis_sha256(authored_basis: Mapping[str, Any]) -> str:
    return _sha(dict(authored_basis))


def check_basis(authored_basis: Any) -> dict[str, Any]:
    """A persisted authored basis has exactly the closed keys; anything else is a malformed store row."""
    if not isinstance(authored_basis, dict) or set(authored_basis) != set(BASIS_KEYS):
        raise ValueError("A stored cold scenario basis is malformed.")
    for key in ("from", "to", "cutoff"):
        if not isinstance(authored_basis[key], str):
            raise ValueError("A stored cold scenario basis is malformed.")
    return authored_basis
