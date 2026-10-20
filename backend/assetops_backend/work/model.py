"""W4-01 commit 2: pure work-case rules (`.agent/W4-01-build-spec.md`).

Refusal codes and messages ("API wire and refusals", S14-S17, Q6/Q28, Run 1 ruling 1), the state table and its
pure reducer over `(recorded_at, id)` ("Identity, time and frozen domain rules"), closed command shapes (B4), the
canonical command hash (B6, Q6/Q28) and the SERVICE attestation grammar (Q28). No I/O, no SQL driver.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping
from uuid import UUID

SCHEMA_CASE = "work-case-1"
SCHEMA_EVENT = "work-event-1"
SCHEMA_PLAN = "maintenance-plan-1"
SCHEMA_RECORD = "maintenance-record-1"
SCHEMA_OPERATIONAL = "operational-record-1"
SCHEMA_DETAIL = "work-case-detail-1"
SCHEMA_INDEX = "site-work-index-1"

INCIDENT = "INCIDENT"
REQUEST = "MAINTENANCE_REQUEST"
CASE_KINDS = (INCIDENT, REQUEST)
CODE_PREFIX = {INCIDENT: "INC", REQUEST: "WR"}

# Run 1 ruling 1 / Q28: the development fixture SERVICE principal and its server-side grant literal.
SERVICE_GRANT_PREFIX = "SITE_WORK_WRITE:"
ATTESTATION = re.compile(r"^service=([^;]+);job=([^;]+);rule=([^;]+)$")

FUTURE_SLACK = timedelta(minutes=5)
BACKDATE_LIMIT = timedelta(days=30)

MESSAGES = {
    "WORK_WRITE_FORBIDDEN": "This actor cannot change work at this site.",
    "WORK_USER_AUTH_REQUIRED": "A signed-in user identity is required for user-attested work commands.",
    "WORK_CASE_NOT_FOUND": "No work case with this ID at this site.",
    "WORK_EVENT_DUPLICATE_KEY": "This key was used for different work content.",
    "WORK_TRANSITION_INVALID": "This transition is not allowed from the selected state.",
    "WORK_OUTCOME_NOT_SUPPORTED": "No frozen outcome plan and accepted later evidence support this outcome.",
    "WORK_CORRECTION_CONFLICT": "This record has a newer correction; reload its latest version.",
    "WORK_INPUT_INVALID": "A required work field or UTC time is invalid.",
    "WORK_ATTESTATION_INVALID": "Service attestation must name the authenticated service, job and rule version.",
    "WORK_LINK_SCOPE_INVALID": "A linked record is not in this Site and tenant.",
    "WORK_OCCURRED_AT_FUTURE": "The occurrence time is more than five minutes in the future.",
    "WORK_OCCURRED_AT_TOO_OLD": "The occurrence time is more than 30 days before it was recorded.",
    "WORK_STORE_UNAVAILABLE": "Work records could not be read or saved.",
    "INVALID_KNOWN_AT": "'known_at' must be one UTC instant no later than the read time.",
    # q7-5: list refusals (INVALID_WINDOW carries its per-field message from `work/site_index.py`).
    "INVALID_WINDOW": "The window may span at most 31 days.",
    "INVALID_LIMIT": "`limit` must be an integer from 1 to 100.",
    "INVALID_CURSOR": "The cursor is not a work-list cursor.",
    "WORK_BASIS_CHANGED": "The work list changed; request page one without a cursor.",
}
STATUS = {"WORK_WRITE_FORBIDDEN": 403, "WORK_USER_AUTH_REQUIRED": 403, "WORK_CASE_NOT_FOUND": 404,
          "WORK_EVENT_DUPLICATE_KEY": 409, "WORK_TRANSITION_INVALID": 409, "WORK_OUTCOME_NOT_SUPPORTED": 409,
          "WORK_CORRECTION_CONFLICT": 409, "WORK_INPUT_INVALID": 422, "WORK_ATTESTATION_INVALID": 422,
          "WORK_LINK_SCOPE_INVALID": 422, "WORK_OCCURRED_AT_FUTURE": 422, "WORK_OCCURRED_AT_TOO_OLD": 422,
          "WORK_STORE_UNAVAILABLE": 503, "INVALID_KNOWN_AT": 422, "INVALID_WINDOW": 422, "INVALID_LIMIT": 422,
          "INVALID_CURSOR": 422, "WORK_BASIS_CHANGED": 409}


class WorkRefused(Exception):
    """A refused work command; nothing it would have written is committed."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.status = STATUS[code]
        self.message = MESSAGES[code] if message is None else message

    def detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class WorkStoreUnavailable(Exception):
    """The work store could not be reached or failed (503 `WORK_STORE_UNAVAILABLE`)."""


def invalid() -> WorkRefused:
    return WorkRefused("WORK_INPUT_INVALID")


# ---- state table ---------------------------------------------------------------------------------------------

# (kind, state, command) -> next state. ASSIGN on IN_PROGRESS stays IN_PROGRESS (new assignee); COMMENT never
# changes state. Anything absent is 409 WORK_TRANSITION_INVALID.
TRANSITIONS: dict[tuple[str, str, str], str] = {
    (INCIDENT, "OPEN", "ASSIGN"): "IN_PROGRESS",
    (INCIDENT, "OPEN", "CLOSE"): "CLOSED",
    (INCIDENT, "IN_PROGRESS", "ASSIGN"): "IN_PROGRESS",
    (INCIDENT, "IN_PROGRESS", "CLOSE"): "CLOSED",
    # q2 reading 1: these explicit cells control; REOPEN from OPEN (nothing to reopen) is 409.
    (INCIDENT, "IN_PROGRESS", "REOPEN"): "OPEN",
    (INCIDENT, "CLOSED", "REOPEN"): "OPEN",
    (REQUEST, "OPEN", "ASSIGN"): "IN_PROGRESS",
    (REQUEST, "OPEN", "CANCEL"): "CANCELLED",
    (REQUEST, "IN_PROGRESS", "ASSIGN"): "IN_PROGRESS",
    (REQUEST, "IN_PROGRESS", "COMPLETE"): "COMPLETED",
    (REQUEST, "IN_PROGRESS", "CANCEL"): "CANCELLED",
    (REQUEST, "COMPLETED", "REOPEN"): "IN_PROGRESS",
    (REQUEST, "VERIFICATION_WINDOW", "REOPEN"): "IN_PROGRESS",
}
COMMENT_STATES = {INCIDENT: ("OPEN", "IN_PROGRESS", "CLOSED"),
                  REQUEST: ("OPEN", "IN_PROGRESS", "COMPLETED", "VERIFICATION_WINDOW")}
WRITABLE_EVENTS = ("ASSIGN", "COMPLETE", "COMMENT", "CLOSE", "REOPEN", "CANCEL")
RESERVED_EVENTS = ("CREATED", "OPEN_VERIFICATION")
OUTCOME_REQUESTS = ("VERIFIED", "INEFFECTIVE", "INCONCLUSIVE")


def next_state(kind: str, state: str, command: str) -> str:
    if command == "COMMENT":
        if state in COMMENT_STATES[kind]:
            return state
        raise WorkRefused("WORK_TRANSITION_INVALID")
    target = TRANSITIONS.get((kind, state, command))
    if target is None:
        raise WorkRefused("WORK_TRANSITION_INVALID")
    return target


def reduce_state(kind: str, events: Iterable[Mapping[str, Any]]) -> str:
    """The state after `events`, applied in `(recorded_at, id)` order; CREATED yields OPEN. Pure."""
    state: str | None = None
    for event in sorted(events, key=lambda e: (e["recorded_at"], str(e["id"]))):
        if event["kind"] == "CREATED":
            state = "OPEN"
        elif state is not None:
            state = next_state(kind, state, event["kind"])
    if state is None:
        raise ValueError("a work case has no CREATED event")
    return state


# ---- values ---------------------------------------------------------------------------------------------------

def uuid_text(value: Any) -> str:
    if not isinstance(value, str):
        raise invalid()
    try:
        return str(UUID(value))
    except ValueError:
        raise invalid() from None


def optional_uuid(value: Any) -> str | None:
    return None if value is None else uuid_text(value)


def uuid_set(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise invalid()
    return sorted({uuid_text(v) for v in value})


def text_value(value: Any, low: int, high: int) -> str:
    """A trimmed nonblank string of `low..high` characters (stored as trimmed)."""
    if not isinstance(value, str):
        raise invalid()
    trimmed = value.strip()
    if not low <= len(trimmed) <= high:
        raise invalid()
    return trimmed


def optional_text(value: Any, low: int, high: int) -> str | None:
    return None if value is None else text_value(value, low, high)


def utc_instant(value: Any) -> datetime:
    """An ISO-8601 instant with an explicit UTC offset (`Z` or `+00:00`); anything else is WORK_INPUT_INVALID."""
    if not isinstance(value, str) or not (value.endswith("Z") or value.endswith("+00:00")):
        raise invalid()
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        raise invalid() from None
    if parsed.utcoffset() != timedelta(0):
        raise invalid()
    return parsed.astimezone(timezone.utc)


def optional_instant(value: Any) -> datetime | None:
    return None if value is None else utc_instant(value)


def iso(value: datetime) -> str:
    """Six fractional digits and `Z` (B6 canonical time)."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def decimal_value(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise invalid()
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        raise invalid() from None
    if not number.is_finite() or number < 0:
        raise invalid()
    return number


def decimal_text(value: Decimal | None) -> str | None:
    """Plain base-10 without trailing zeros (B6)."""
    if value is None:
        return None
    text = format(value.normalize(), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def idempotency_key(value: Any) -> str:
    if not isinstance(value, str) or not 8 <= len(value) <= 128 or not value.isprintable():
        raise invalid()
    return value


def closed(body: Any, required: Iterable[str], optional: Iterable[str] = ()) -> dict[str, Any]:
    """A JSON object with exactly the required keys and any of the optional ones."""
    if not isinstance(body, dict):
        raise invalid()
    required, optional = set(required), set(optional)
    keys = set(body)
    if not required <= keys or keys - required - optional:
        raise invalid()
    return body


def check_occurrence(occurred_at: datetime, db_now: datetime) -> None:
    if occurred_at > db_now + FUTURE_SLACK:
        raise WorkRefused("WORK_OCCURRED_AT_FUTURE")
    if occurred_at < db_now - BACKDATE_LIMIT:
        raise WorkRefused("WORK_OCCURRED_AT_TOO_OLD")


# ---- actor and authority --------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Actor:
    kind: str
    id: str
    attestation: str
    authorization_basis: str

    def canonical(self) -> dict[str, str]:
        """Hashed actor: validated client fields only, never the server-derived basis (Run 1 ruling 1)."""
        return {"kind": self.kind, "id": self.id, "attestation": self.attestation}


def actor_shape(value: Any) -> dict[str, Any]:
    """The actor object has exactly `kind,id,attestation`; `authorization_basis` or any other key is refused."""
    actor = closed(value, ("kind", "id", "attestation"))
    if actor["kind"] not in ("USER", "SERVICE"):
        raise invalid()
    text_value(actor["id"], 1, 128)
    text_value(actor["attestation"], 1, 1000)
    return actor


def authorize(actor: Mapping[str, Any], principal: str | None) -> Actor:
    """Run 1 ruling 1 and Q28, after the shape check: a development USER actor is 403; a SERVICE command needs
    the server-injected principal and an attestation naming it."""
    if actor["kind"] == "USER":
        raise WorkRefused("WORK_USER_AUTH_REQUIRED")
    if principal is None:
        raise WorkRefused("WORK_WRITE_FORBIDDEN")
    match = ATTESTATION.match(actor["attestation"])
    if (match is None or any(g != g.strip() or not g.strip() for g in match.groups())
            or actor["id"] != principal or "service:" + match.group(1) != actor["id"]):
        raise WorkRefused("WORK_ATTESTATION_INVALID")
    return Actor("SERVICE", actor["id"], actor["attestation"], SERVICE_GRANT_PREFIX + principal)


# ---- canonical command hash -----------------------------------------------------------------------------------

def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def command_sha256(path: Mapping[str, Any], body: Mapping[str, Any]) -> str:
    """SHA-256 of `{path, body}` sorted-key compact UTF-8 JSON (B6, Q6/Q28). Bare hex, as the columns store it."""
    return hashlib.sha256(canonical_json({"path": dict(path), "body": dict(body)}).encode("utf-8")).hexdigest()


def finding_links(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise invalid()
    pairs = set()
    for item in value:
        link = closed(item, ("finding_id", "finding_revision_id"))
        pairs.add((uuid_text(link["finding_id"]), uuid_text(link["finding_revision_id"])))
    return [{"finding_id": f, "finding_revision_id": r} for f, r in sorted(pairs)]


def action_links(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise invalid()
    pairs = set()
    for item in value:
        link = closed(item, ("action_id", "action_event_id"))
        pairs.add((uuid_text(link["action_id"]), uuid_text(link["action_event_id"])))
    return [{"action_id": a, "action_event_id": e} for a, e in sorted(pairs)]


def event_payload(kind: str, payload: Any) -> dict[str, Any]:
    """B4 closed payloads for the writable event kinds."""
    if kind == "ASSIGN":
        return {"assignee": text_value(closed(payload, ("assignee",))["assignee"], 1, 128)}
    if kind == "COMMENT":
        return {"text": text_value(closed(payload, ("text",))["text"], 1, 2000)}
    if kind in ("CLOSE", "REOPEN", "CANCEL"):
        return {"reason": text_value(closed(payload, ("reason",))["reason"], 1, 500)}
    if kind == "COMPLETE":
        return {"maintenance_record_id": uuid_text(closed(payload, ("maintenance_record_id",))["maintenance_record_id"])}
    raise invalid()
