"""W5-02a K1a: the cold domain Action model - refusals, the closed command bodies and the canonical digests.

`.agent/W5-02-build-spec.md` "Command/read wire", "Backend wire, validation and lineage (K1a-K1c)" and the
Architect pre-flight ruling A2/A3. Pure: no I/O. Shape and static-bound violations are 422
`DOMAIN_INTENT_INVALID`; selection/link failures are decided by the service against the store.

The four declared criteria are fixed (keys, labels, required evidence, order). An intent declares success
conditions only; it is never a verification outcome and never implies `VERIFIED`.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping
from uuid import UUID

from assetops_backend.work import model as m

SCHEMA_ACTION = "domain-action-1"
SCHEMA_INTENT = "domain-action-intent-1"
SCHEMA_CASE_LINK = "domain-action-case-link-1"
DOMAIN = "COLDCHAIN"
FINDING_DOMAIN = "cold_chain"

CMD_ACTION = "domain_action"
CMD_INTENT = "domain_action_intent"
CMD_CASE_LINK = "domain_action_case_link"

TEXT_MAX = 160
DUE_LIMIT = timedelta(days=365)

#: The one supported cold contract, in display order: (key, label, required_evidence).
CRITERIA: tuple[tuple[str, str, str], ...] = (
    ("AUTOMATIC_START", "Automatic start", "Accepted command followed by successful running status"),
    ("POWER_DELIVERY", "Power delivery", "Generator supply reaches the cooling system"),
    ("COOLING_RECOVERY", "Cooling recovery", "Temperature recovery within declared test conditions"),
    ("RECURRENCE", "Recurrence", "Covered observation window without a qualifying repeat"),
)

MESSAGES = {
    "DOMAIN_INTENT_INVALID": "The cold Action declaration is incomplete or invalid.",
    "DOMAIN_INTENT_LINK_INVALID": "The declared Finding or work record is not selected at this site and cutoff.",
    "DOMAIN_INTENT_CONFLICT": "This Action declaration has a newer version; reload it.",
    "DOMAIN_INTENT_BASIS_CHANGED": "The selected cold work basis changed; reload the Action.",
    "ACTION_NOT_FOUND": "Action was not found at this site.",
}
STATUS = {"DOMAIN_INTENT_INVALID": 422, "DOMAIN_INTENT_LINK_INVALID": 422, "DOMAIN_INTENT_CONFLICT": 409,
          "DOMAIN_INTENT_BASIS_CHANGED": 409, "ACTION_NOT_FOUND": 404}

#: W5-04a V1a (pre-flight 9, readiness 12): the EV contract, in display order.
EV_DOMAIN = "EV_CHARGING"
EV_FINDING_DOMAIN = "ev_charging"
EV_CRITERIA: tuple[tuple[str, str, str], ...] = (
    ("WITNESSED_SESSION", "Complete a witnessed charging session", "Session start, end, outcome and meter delta"),
    ("NO_FAULT_RECURRENCE", "No fault recurrence during observation", "Connector diagnostic events with full coverage"),
    ("NO_SERVICE_REDUCTION", "No reduction in service availability", "Comparable status coverage / operational window"),
)
EV_MESSAGES = {
    "DOMAIN_INTENT_INVALID": "The EV Action declaration is incomplete or invalid.",
    "DOMAIN_INTENT_LINK_INVALID": "The declared Finding or session is not selected at this site and cutoff.",
    "DOMAIN_INTENT_CONFLICT": "This Action declaration has a newer version; reload it.",
    "DOMAIN_INTENT_BASIS_CHANGED": "The selected EV work basis changed; reload the Action.",
    "ACTION_NOT_FOUND": "Action was not found at this site.",
}
#: Pre-flight 10: neutral literals used only before a domain or an Action is resolved.
NEUTRAL_DOMAIN_INVALID = "The Action domain is missing or unsupported."
NEUTRAL_LINK_INVALID = "The Action could not be resolved at this site and cutoff."


@dataclass(frozen=True)
class DomainSpec:
    """One closed domain contract (pre-flight 9). `domain` is the upper-case Site/Action literal, `finding_domain`
    the lower-case analytics literal; nothing outside `DOMAINS` falls through to cold."""

    domain: str
    finding_domain: str
    criteria: tuple[tuple[str, str, str], ...]
    summary: str
    initial_results: tuple[str, ...]
    messages: Mapping[str, str]
    basis_keys: tuple[str, ...]

    def refuse(self, code: str) -> "DomainIntentRefused":
        return DomainIntentRefused(STATUS[code], code, self.messages[code])


_BASIS = ("finding_revision_id", "work_case_id", "work_record_id", "accepted_evidence_ids")
DOMAINS: Mapping[str, DomainSpec] = {
    DOMAIN: DomainSpec(DOMAIN, FINDING_DOMAIN, CRITERIA, "Start requested → generator runs → power → cooling",
                       ("NOT_TESTED", "NOT_TESTED", "NOT_ESTABLISHED", "PENDING"), MESSAGES, _BASIS),
    EV_DOMAIN: DomainSpec(EV_DOMAIN, EV_FINDING_DOMAIN, EV_CRITERIA, "A complete witnessed session and no repeat fault",
                          ("PENDING", "PENDING", "PENDING"), EV_MESSAGES, _BASIS + ("session_ids",)),
}
#: Finding (analytics) domain -> Action domain, for `_domain_links` and pins (readiness ruling 12).
BY_FINDING_DOMAIN: Mapping[str, str] = {spec.finding_domain: name for name, spec in DOMAINS.items()}


def spec_of(domain: Any) -> DomainSpec | None:
    """The closed contract of a stored or declared domain; None for anything unreviewed."""
    return DOMAINS.get(domain) if isinstance(domain, str) else None


#: The cross-table Action code collision trigger's constraint name (migration 0033, ruling A4).
CODE_CONFLICT_CONSTRAINT = "action_cross_domain_code_conflict"


class DomainIntentRefused(Exception):
    """A refused domain Action command (ruling A2); nothing it would have written is committed."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(code)
        self.status, self.code, self.message = status, code, message

    @classmethod
    def of(cls, code: str) -> "DomainIntentRefused":
        return cls(STATUS[code], code, MESSAGES[code])

    def detail(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


def invalid() -> DomainIntentRefused:
    return DomainIntentRefused.of("DOMAIN_INTENT_INVALID")


def refuse(code: str) -> DomainIntentRefused:
    return DomainIntentRefused.of(code)


# ---- values (W4 parsers, re-typed to this contract's 422) -------------------------------------------------------

def _w4(parse, *args: Any) -> Any:
    try:
        return parse(*args)
    except m.WorkRefused:
        raise invalid() from None


def closed(body: Any, required: tuple[str, ...]) -> dict[str, Any]:
    return _w4(m.closed, body, required)


def uuid_text(value: Any) -> str:
    return _w4(m.uuid_text, value)


def optional_uuid(value: Any) -> str | None:
    return None if value is None else uuid_text(value)


def instant(value: Any) -> datetime:
    return _w4(m.utc_instant, value)


def bounded_text(value: Any) -> str:
    """Trimmed, nonempty, at most 160 Unicode code points (stored and hashed trimmed)."""
    return _w4(m.text_value, value, 1, TEXT_MAX)


def key(value: Any) -> str:
    return _w4(m.idempotency_key, value)


def actor_shape(value: Any) -> dict[str, Any]:
    """W4 `actor_shape` (public, ruling A2); its closed-shape refusal is this contract's 422."""
    return _w4(m.actor_shape, value)


def evidence_ids(value: Any) -> list[str]:
    """Distinct UUIDs, canonically sorted; a duplicate is an invalid declaration, never silently merged."""
    if not isinstance(value, list):
        raise invalid()
    ids = [uuid_text(v) for v in value]
    if len(set(ids)) != len(ids):
        raise invalid()
    return sorted(ids)


def within_command_window(value: datetime, db_now: datetime) -> bool:
    """`raised_at`/`declared_at`: no later than DB time plus five minutes, no earlier than 30 days before it."""
    return db_now - m.BACKDATE_LIMIT <= value <= db_now + m.FUTURE_SLACK


# ---- closed bodies ---------------------------------------------------------------------------------------------

def action_body(body: Any) -> dict[str, Any]:
    """The normalized closed Action creation body (actor excluded; validated by the caller)."""
    b = closed(body, ("domain", "origin_finding_id", "origin_finding_revision_id", "title", "owner_label", "due_at",
                      "raised_at", "actor", "idempotency_key"))
    if b["domain"] != DOMAIN:
        raise invalid()
    raised = instant(b["raised_at"])
    due = None if b["due_at"] is None else instant(b["due_at"])
    if due is not None and not raised <= due <= raised + DUE_LIMIT:
        raise invalid()
    return {"domain": DOMAIN, "origin_finding_id": uuid_text(b["origin_finding_id"]),
            "origin_finding_revision_id": uuid_text(b["origin_finding_revision_id"]),
            "title": bounded_text(b["title"]),
            "owner_label": None if b["owner_label"] is None else bounded_text(b["owner_label"]),
            "due_at": due, "raised_at": raised, "idempotency_key": key(b["idempotency_key"])}


def criteria(value: Any) -> list[dict[str, str]]:
    """Exactly the four fixed criteria, in order, each a closed `{key,label,required_evidence}`."""
    if not isinstance(value, list) or len(value) != len(CRITERIA):
        raise invalid()
    out = []
    for given, (k, label, required) in zip(value, CRITERIA):
        row = closed(given, ("key", "label", "required_evidence"))
        if (row["key"], row["label"], row["required_evidence"]) != (k, label, required):
            raise invalid()
        out.append({"key": k, "label": label, "required_evidence": required})
    return out


def basis(value: Any) -> dict[str, Any]:
    b = closed(value, ("finding_revision_id", "work_case_id", "work_record_id", "accepted_evidence_ids"))
    out = {"finding_revision_id": uuid_text(b["finding_revision_id"]), "work_case_id": optional_uuid(b["work_case_id"]),
           "work_record_id": optional_uuid(b["work_record_id"]),
           "accepted_evidence_ids": evidence_ids(b["accepted_evidence_ids"])}
    if out["work_record_id"] is not None and out["work_case_id"] is None:
        raise invalid()  # a performed record is cited only through its explicitly linked request
    return out


def intent_body(body: Any) -> dict[str, Any]:
    b = closed(body, ("supersedes_id", "declared_at", "criteria", "basis", "actor", "idempotency_key"))
    return {"supersedes_id": optional_uuid(b["supersedes_id"]), "declared_at": instant(b["declared_at"]),
            "criteria": criteria(b["criteria"]), "basis": basis(b["basis"]),
            "idempotency_key": key(b["idempotency_key"])}


def case_link_body(body: Any) -> dict[str, Any]:
    b = closed(body, ("case_id", "case_revision_id", "case_event_id", "actor", "idempotency_key"))
    return {"case_id": uuid_text(b["case_id"]), "case_revision_id": uuid_text(b["case_revision_id"]),
            "case_event_id": uuid_text(b["case_event_id"]), "idempotency_key": key(b["idempotency_key"])}


def path_action_id(value: str) -> str | None:
    """A malformed path Action ID names no Action (404 after the body checks), never a 500."""
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        return None


# ---- canonical digests -----------------------------------------------------------------------------------------

def _canonical(value: Any) -> Any:
    if isinstance(value, datetime):
        return m.iso(value)
    if isinstance(value, dict):
        return {k: _canonical(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def command_sha256(tenant_id: UUID, site_id: UUID, action_id: str | None, command: str,
                   normalized: Mapping[str, Any], actor: m.Actor) -> str:
    """Ruling A2: W4 `command_sha256` over route identity `{tenant_id,site_id,action_id|null,command}` and the
    normalized closed body (trimmed text, UTC `Z` instants, sorted evidence IDs, the validated actor)."""
    path = {"tenant_id": str(tenant_id), "site_id": str(site_id), "action_id": action_id, "command": command}
    return m.command_sha256(path, _canonical({**normalized, "actor": actor.canonical()}))


def selection_token(tenant_id: UUID | str, site_id: UUID | str, action: Mapping[str, Any],
                    finding_revision_id: str, intent_id: str | None, case: Mapping[str, Any] | None,
                    work_record_id: str | None, cited_evidence_ids: list[str]) -> str:
    """Ruling A2: `sha256:` + SHA-256 of the canonical tenant/Site, root (ID and attested `raised_at`), Finding
    revision, intent ID, selected case/revision/event, record and sorted cited evidence IDs at the cutoff.
    K1b recomputes this exact digest on read through this function."""
    payload = {
        "tenant_id": str(tenant_id), "site_id": str(site_id),
        "action": {"id": str(action["id"]), "raised_at": m.iso(action["raised_at"])},
        "finding_revision_id": str(finding_revision_id), "intent_id": None if intent_id is None else str(intent_id),
        "case": None if case is None else {"case_id": str(case["case_id"]),
                                           "case_revision_id": str(case["case_revision_id"]),
                                           "case_event_id": str(case["case_event_id"])},
        "work_record_id": None if work_record_id is None else str(work_record_id),
        "accepted_evidence_ids": sorted(str(e) for e in cited_evidence_ids),
    }
    return "sha256:" + hashlib.sha256(m.canonical_json(payload).encode("utf-8")).hexdigest()
