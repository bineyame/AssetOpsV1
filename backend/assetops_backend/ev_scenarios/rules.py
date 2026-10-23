"""W5-03b E5: the authored EV scenario command rules (`.agent/W5-03-build-spec.md` E5 card, "E5 exact persisted
schema and wire contract" and "E5 consolidated correction").

`ev-scenario-authored/1` allows one `kind`, `GROSS_TARIFF_CONTEXT`, whose only assumption object is
`{tariff_per_kwh, currency}`. It is an authored what-if beside the selected W2-07 complete metered sessions: no
computed money amount, collected revenue, lost sales, comparison delta or observed outcome exists here, and one body
currency asks for no conversion. The decimal and ISO 4217 grammar is W5-01b C4's (imported, not copied). Pure
functions; no SQL and no clock.
"""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import Any, Mapping
from uuid import UUID

from assetops_backend.cold_scenarios.rules import CURRENCY, DECIMAL, ISO_4217
from assetops_backend.mini_decisions.model import MESSAGES as DECISION_MESSAGES
from assetops_backend.mini_decisions.model import DecisionRefused
from assetops_backend.work import model as work
from assetops_backend.work.model import WorkRefused

SCHEMA_COMMAND = "ev-scenario-command-1"
SCHEMA_WRITE = "ev-scenario-write-1"
SCHEMA_LIST = "ev-scenarios-1"
KIND = "GROSS_TARIFF_CONTEXT"
FORMULA_VERSION = "AUTHORED_ONLY/1"
ROUTE = "ev/financials/scenarios"
PAGE_DEFAULT, PAGE_MAX = 50, 100
ASSUMPTION_KEYS = ("tariff_per_kwh", "currency")
BASIS_KEYS = ("from", "to", "cutoff", "assessment_revision_id", "session_revision_ids", "accepted_evidence_ids",
              "foundation_revision_id", "consequence_revision_id", "tariff_revision_id", "source_provenance")
ROOT_KEYS = ("schema_version", "idempotency_key", "actor", "name", "kind", "assumptions")
CORRECTION_KEYS = ROOT_KEYS + ("supersedes_revision_id", "correction_reason")

#: The new E5 refusal literals; `DECISION_*` reuse `mini_decisions.model.MESSAGES`.
MESSAGES = {
    "EV_SCENARIO_INVALID": "The EV scenario request or selected basis is invalid.",
    "EV_SCENARIO_CURSOR_INVALID": "The EV scenario cursor is invalid.",
    "EV_SCENARIO_CURSOR_BASIS_CHANGED": "The selected EV scenario basis changed. Start at the first page.",
    "EV_SCENARIO_IDEMPOTENCY_CONFLICT": "This idempotency key belongs to a different EV scenario request.",
    "EV_SCENARIO_REVISION_CONFLICT": "The EV scenario has a newer revision. Reload it before correcting.",
}
STATUS = {
    "EV_SCENARIO_INVALID": 422, "EV_SCENARIO_CURSOR_INVALID": 422, "EV_SCENARIO_CURSOR_BASIS_CHANGED": 409,
    "EV_SCENARIO_IDEMPOTENCY_CONFLICT": 409, "EV_SCENARIO_REVISION_CONFLICT": 409,
}


def refused(code: str, message: str | None = None, status: int | None = None) -> DecisionRefused:
    """An E5 refusal in the shared `DecisionRefused` carrier (E5 literal, else the mini-decision literal)."""
    if code in MESSAGES:
        return DecisionRefused(code, message or MESSAGES[code], status or STATUS[code])
    return DecisionRefused(code, message or DECISION_MESSAGES.get(code), status)


def invalid() -> DecisionRefused:
    return refused("EV_SCENARIO_INVALID")


def _shape(fn, *args: Any) -> Any:
    """A W4-01 validator (imported, not copied) with its refusal mapped to `EV_SCENARIO_INVALID`."""
    try:
        return fn(*args)
    except WorkRefused:
        raise invalid() from None


def scenario_code(public_no: int) -> str:
    """`ESCN-` plus at least six zero-padded decimal digits."""
    return f"ESCN-{int(public_no):06d}"


def positive_decimal(value: Any) -> str:
    if not isinstance(value, str) or DECIMAL.match(value) is None or not Decimal(value) > 0:
        raise invalid()
    return value


def currency(value: Any) -> str:
    if not isinstance(value, str) or CURRENCY.match(value) is None or value not in ISO_4217:
        raise invalid()
    return value


def assumptions(value: Any) -> dict[str, str]:
    a = _shape(work.closed, value, ASSUMPTION_KEYS)
    return {"tariff_per_kwh": positive_decimal(a["tariff_per_kwh"]), "currency": currency(a["currency"])}


def actor_of(body: Any) -> dict[str, Any]:
    """The closed actor object, read before the rest of the body so the actor policy answers first."""
    if not isinstance(body, dict) or "actor" not in body:
        raise invalid()
    actor = _shape(work.actor_shape, body["actor"])
    return {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]}


def parse_command(body: Any, *, correction: bool) -> dict[str, Any]:
    """The closed `ev-scenario-command-1` body, canonical (trimmed text, verbatim decimal strings)."""
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
    """`{command, site_id, window:{from,to,cutoff}}`: the root `create_payload_sha256` and revision 1's
    `payload_sha256` (the C4 P-C4-22 rule)."""
    return _sha({"command": _command(cmd), "site_id": str(site_id).lower(),
                 "window": {"from": lo, "to": hi, "cutoff": cutoff}})


def correction_sha256(cmd: Mapping[str, Any], root_id: str, lo: str, hi: str, cutoff: str | None) -> str:
    """The corrected body, the root ID and the resolved same root window and cutoff (the C4 P-C4-22 rule)."""
    return _sha({"command": _command(cmd), "root_id": str(root_id).lower(),
                 "window": {"from": lo, "to": hi, "cutoff": cutoff}})


def basis_sha256(authored_basis: Mapping[str, Any]) -> str:
    return _sha(dict(authored_basis))


def check_basis(authored_basis: Any) -> dict[str, Any]:
    """A persisted authored basis has exactly the closed keys; anything else is a malformed store row."""
    if not isinstance(authored_basis, dict) or set(authored_basis) != set(BASIS_KEYS):
        raise ValueError("A stored EV scenario basis is malformed.")
    for key in ("from", "to", "cutoff"):
        if not isinstance(authored_basis[key], str):
            raise ValueError("A stored EV scenario basis is malformed.")
    return authored_basis
