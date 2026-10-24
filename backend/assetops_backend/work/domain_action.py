"""W5-02a K1a / W5-04a V1: the domain Action model - refusals, the closed command bodies and the canonical digests.

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
#: Pre-flight 10 / readiness 28: neutral literals used only while the domain is unknown - a creation POST whose
#: `domain` is missing or unsupported, and an intent or case-link body that fails the domain-independent checks
#: before its Action is resolved. An unresolved Action is 404, never a neutral link refusal.
NEUTRAL_DOMAIN_INVALID = "The Action domain is missing or unsupported."
NEUTRAL_INTENT_INVALID = "The Action declaration is incomplete or invalid."
NEUTRAL_CASE_LINK_INVALID = "The Action case link is incomplete or invalid."


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


#: The only EV Finding lifecycle that can originate or support an EV Action (pre-flight 15).
EV_SUPPORTED = "SUPPORTED"


def _lower(values: Any) -> set[str]:
    return {str(v).lower() for v in values or ()}


def ev_selects_finding(ev: Mapping[str, Any] | None, revision_id: str) -> bool:
    """The selected EV basis (`composition.selected_ev_basis`) selects exactly this SUPPORTED Finding revision."""
    finding = None if ev is None else ev.get("finding")
    return (finding is not None and str(finding["revision_id"]).lower() == str(revision_id).lower()
            and finding["lifecycle"] == EV_SUPPORTED)


def ev_members_selected(ev: Mapping[str, Any], basis: Mapping[str, Any]) -> bool:
    """Readiness 7, 9, 13 and 30, without intersection: every declared session root is selected at the pin and the
    Finding's own session is among them; every declared evidence ID is in the window's accepted set (A), the selected
    assessment head's cited set (B) and the exact Finding revision's citations. UUID case is normalized."""
    finding = ev["finding"]
    declared = _lower(basis["session_ids"])
    own = finding.get("session_id")
    if own is None or str(own).lower() not in declared or not declared <= _lower(ev["sessions"]):
        return False
    evidence = _lower(basis["accepted_evidence_ids"])
    return (evidence <= _lower(ev["accepted_evidence_ids"]) and evidence <= _lower(ev["selected_evidence_ids"])
            and evidence <= _lower(finding["evidence_ids"]))


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


def neutral(message: str) -> DomainIntentRefused:
    """A 422 `DOMAIN_INTENT_INVALID` carrying one of the neutral literals (readiness 28)."""
    return DomainIntentRefused(STATUS["DOMAIN_INTENT_INVALID"], "DOMAIN_INTENT_INVALID", message)


class _Malformed(DomainIntentRefused):
    """A value-parser refusal; each closed-body function re-types it to the literal its stage selects (neutral
    before the domain is known, else that domain's). Standalone callers still see the cold 422 it defaults to."""

    def __init__(self) -> None:
        super().__init__(STATUS["DOMAIN_INTENT_INVALID"], "DOMAIN_INTENT_INVALID", MESSAGES["DOMAIN_INTENT_INVALID"])


def _as(refusal: DomainIntentRefused, parse, *args: Any) -> Any:
    try:
        return parse(*args)
    except _Malformed:
        raise refusal from None


def refuse(code: str) -> DomainIntentRefused:
    return DomainIntentRefused.of(code)


# ---- values (W4 parsers, re-typed to this contract's 422) -------------------------------------------------------

def _w4(parse, *args: Any) -> Any:
    try:
        return parse(*args)
    except m.WorkRefused:
        raise _Malformed() from None


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


def actor_shape(value: Any, refusal: DomainIntentRefused | None = None) -> dict[str, Any]:
    """W4 `actor_shape` (public, ruling A2); its closed-shape refusal is the caller's stage literal (cold 422 by
    default)."""
    if refusal is None:
        return _w4(m.actor_shape, value)
    return _as(refusal, _w4, m.actor_shape, value)


def evidence_ids(value: Any) -> list[str]:
    """Distinct UUIDs, canonically sorted; a duplicate is an invalid declaration, never silently merged."""
    if not isinstance(value, list):
        raise _Malformed()
    ids = [uuid_text(v) for v in value]
    if len(set(ids)) != len(ids):
        raise _Malformed()
    return sorted(ids)


def within_command_window(value: datetime, db_now: datetime) -> bool:
    """`raised_at`/`declared_at`: no later than DB time plus five minutes, no earlier than 30 days before it."""
    return db_now - m.BACKDATE_LIMIT <= value <= db_now + m.FUTURE_SLACK


# ---- closed bodies ---------------------------------------------------------------------------------------------

def action_body(body: Any) -> dict[str, Any]:
    """The normalized closed Action creation body (actor excluded; validated by the caller). A missing or
    unsupported `domain` is the neutral 422 (pre-flight 10); every other failure carries that domain's literal."""
    spec = spec_of(body.get("domain")) if isinstance(body, dict) else None
    if spec is None:
        raise neutral(NEUTRAL_DOMAIN_INVALID)
    return _as(spec.refuse("DOMAIN_INTENT_INVALID"), _action_body, body, spec)


def _action_body(body: Any, spec: DomainSpec) -> dict[str, Any]:
    b = closed(body, ("domain", "origin_finding_id", "origin_finding_revision_id", "title", "owner_label", "due_at",
                      "raised_at", "actor", "idempotency_key"))
    raised = instant(b["raised_at"])
    due = None if b["due_at"] is None else instant(b["due_at"])
    if due is not None and not raised <= due <= raised + DUE_LIMIT:
        raise _Malformed()
    return {"domain": spec.domain, "origin_finding_id": uuid_text(b["origin_finding_id"]),
            "origin_finding_revision_id": uuid_text(b["origin_finding_revision_id"]),
            "title": bounded_text(b["title"]),
            "owner_label": None if b["owner_label"] is None else bounded_text(b["owner_label"]),
            "due_at": due, "raised_at": raised, "idempotency_key": key(b["idempotency_key"])}


_CRITERION = ("key", "label", "required_evidence")
#: The basis keys every closed domain shares, and every key some closed domain allows (readiness 28).
_COMMON_BASIS = tuple(k for k in _BASIS if all(k in spec.basis_keys for spec in DOMAINS.values()))
_ANY_BASIS = tuple(dict.fromkeys(k for spec in DOMAINS.values() for k in spec.basis_keys))


def _criteria_shape(value: Any) -> list[dict[str, str]]:
    """Domain-independent: a list of closed `{key,label,required_evidence}` text objects (count, order and triples
    are the resolved domain's)."""
    if not isinstance(value, list):
        raise _Malformed()
    out = []
    for given in value:
        row = closed(given, _CRITERION)
        if not all(isinstance(row[k], str) for k in _CRITERION):
            raise _Malformed()
        out.append({k: row[k] for k in _CRITERION})
    return out


def _basis_shape(value: Any) -> dict[str, Any]:
    """Domain-independent: an object holding every shared key and only keys some closed domain allows; the shared
    values are parsed (domain-specific keys such as EV `session_ids` stay raw until the Action is resolved)."""
    if not isinstance(value, dict) or not set(_COMMON_BASIS) <= set(value) <= set(_ANY_BASIS):
        raise _Malformed()
    out = {"finding_revision_id": uuid_text(value["finding_revision_id"]),
           "work_case_id": optional_uuid(value["work_case_id"]),
           "work_record_id": optional_uuid(value["work_record_id"]),
           "accepted_evidence_ids": evidence_ids(value["accepted_evidence_ids"])}
    if out["work_record_id"] is not None and out["work_case_id"] is None:
        raise _Malformed()  # a performed record is cited only through its explicitly linked request
    return {**out, **{k: value[k] for k in value if k not in _COMMON_BASIS}}


def criteria(value: Any, spec: DomainSpec | None = None) -> list[dict[str, str]]:
    """Exactly the resolved domain's fixed criteria (cold by default), in order, each a closed
    `{key,label,required_evidence}`."""
    spec = DOMAINS[DOMAIN] if spec is None else spec
    rows = _criteria_shape(value)
    if len(rows) != len(spec.criteria):
        raise _Malformed()
    for row, triple in zip(rows, spec.criteria):
        if (row["key"], row["label"], row["required_evidence"]) != triple:
            raise _Malformed()
    return [{"key": k, "label": label, "required_evidence": required} for k, label, required in spec.criteria]


def session_ids(value: Any) -> list[str]:
    """EV `basis.session_ids`: nonempty distinct public `ev_session.id` UUIDs, canonically sorted (readiness 9)."""
    ids = evidence_ids(value)
    if not ids:
        raise _Malformed()
    return ids


def basis(value: Any, spec: DomainSpec | None = None) -> dict[str, Any]:
    """The resolved domain's exact basis keys (cold by default) with every value parsed."""
    spec = DOMAINS[DOMAIN] if spec is None else spec
    b = _basis_shape(value)
    if sorted(b) != sorted(spec.basis_keys):
        raise _Malformed()
    out = {k: b[k] for k in _COMMON_BASIS}
    if "session_ids" in spec.basis_keys:
        out["session_ids"] = session_ids(b["session_ids"])
    return out


def _intent_shape(body: Any) -> dict[str, Any]:
    b = closed(body, ("supersedes_id", "declared_at", "criteria", "basis", "actor", "idempotency_key"))
    return {"supersedes_id": optional_uuid(b["supersedes_id"]), "declared_at": instant(b["declared_at"]),
            "criteria": _criteria_shape(b["criteria"]), "basis": _basis_shape(b["basis"]),
            "idempotency_key": key(b["idempotency_key"])}


def intent_shape(body: Any) -> dict[str, Any]:
    """Readiness 28, before the Action is resolved: the closed top-level shape, static bounds and the
    domain-independent criteria/basis shape; any failure is the neutral intent 422."""
    return _as(neutral(NEUTRAL_INTENT_INVALID), _intent_shape, body)


def intent_for(spec: DomainSpec, shape: Mapping[str, Any]) -> dict[str, Any]:
    """Readiness 28, after the Action is resolved: the stored domain's exact criteria and basis keys, with that
    domain's 422 literal. The normalized result is what is hashed and stored (cold output unchanged)."""
    def parse() -> dict[str, Any]:
        return {"supersedes_id": shape["supersedes_id"], "declared_at": shape["declared_at"],
                "criteria": criteria(shape["criteria"], spec), "basis": basis(shape["basis"], spec),
                "idempotency_key": shape["idempotency_key"]}
    return _as(spec.refuse("DOMAIN_INTENT_INVALID"), parse)


def intent_body(body: Any, domain: str = DOMAIN) -> dict[str, Any]:
    """The shared shape, then the resolved `domain`'s exact contract (cold by default)."""
    return intent_for(DOMAINS[domain], intent_shape(body))


def _case_link_body(body: Any) -> dict[str, Any]:
    b = closed(body, ("case_id", "case_revision_id", "case_event_id", "actor", "idempotency_key"))
    return {"case_id": uuid_text(b["case_id"]), "case_revision_id": uuid_text(b["case_revision_id"]),
            "case_event_id": uuid_text(b["case_event_id"]), "idempotency_key": key(b["idempotency_key"])}


def case_link_body(body: Any) -> dict[str, Any]:
    """Domain-independent (readiness 28): any failure is the neutral case-link 422."""
    return _as(neutral(NEUTRAL_CASE_LINK_INVALID), _case_link_body, body)


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
