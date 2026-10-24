"""W5-02a K1a / W5-04a V1: the three domain Action commands (root, declared intent, explicit W4 case link).

`.agent/W5-02-build-spec.md` "Command/read wire" and "Backend wire, validation and lineage (K1a-K1c)", Architect
pre-flight ruling A2/A3, and W5-04 readiness rulings 27, 28 and 30. Every command dispatches by the closed
`domain_action.DOMAINS` contract of the declared (creation) or stored (intent, case link) domain; nothing outside it
falls through to cold.

Order (readiness 28): absent server SERVICE principal 403 (W4 gate); the closed shape, static bounds and actor shape
422 `DOMAIN_INTENT_INVALID` - for creation with the declared domain's literal (a missing/unsupported domain is the
neutral domain literal), for an intent or case link with the neutral literal, since the Action's domain is not yet
known; W4 actor authorization (USER 403, attestation 422); then one store transaction: the scoped Action (404
`ACTION_NOT_FOUND`), the stored domain's exact criteria and basis keys (422 with that domain's literal), the
advisory-locked idempotency check (identical retry 200 with the original response; another body 409), DB-time bounds
422, selection/link checks 422 `DOMAIN_INTENT_LINK_INVALID` or 409 `DOMAIN_INTENT_BASIS_CHANGED`, chain conflicts
409, then INSERT and 201. Every refusal writes nothing.

No telemetry creates an Action or a case link; an intent declares success conditions and is never an outcome.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping, Protocol
from uuid import UUID, uuid4

from assetops_backend.work import domain_action as d
from assetops_backend.work import model as m

class DomainIntentStore(Protocol):
    def transaction(self, tenant_id: UUID, site_id: UUID, site_code: str, work: Callable[[Any], Any]) -> Any: ...


def _actor(body: Mapping[str, Any], principal: str | None, refusal: d.DomainIntentRefused) -> m.Actor:
    return m.authorize(d.actor_shape(body["actor"], refusal), principal)


def _gate(principal: str | None) -> None:
    if principal is None:
        raise m.WorkRefused("WORK_WRITE_FORBIDDEN")


def _actor_row(actor: m.Actor) -> dict[str, str]:
    return {"actor_kind": actor.kind, "actor_id": actor.id, "attestation": actor.attestation}


def _spec(action: Mapping[str, Any]) -> d.DomainSpec:
    """The stored Action's closed contract. The 0035 domain CHECK admits only closed domains, so anything else is
    a store fault (503), never a cold fallback."""
    spec = d.spec_of(action["domain"])
    if spec is None:
        raise m.WorkStoreUnavailable("The stored domain Action has an unsupported domain.")
    return spec


def selected_ev_finding(tx: Any, pin: Mapping[str, Any], revision_id: str) -> dict[str, Any] | None:
    """The selected EV basis at the transaction's cutoff when it selects exactly this SUPPORTED Finding revision."""
    ev = tx.selected_ev_basis(pin, revision_id)
    return ev if d.ev_selects_finding(ev, revision_id) else None


class DomainIntentService:
    def __init__(self, store: DomainIntentStore, *, new_id: Callable[[], UUID] = uuid4) -> None:
        self._store = store
        self._new_id = new_id

    def _id(self) -> str:
        return str(self._new_id())

    # ---- Action root ---------------------------------------------------------------------------------------

    @staticmethod
    def _action_response(row: Mapping[str, Any]) -> dict[str, Any]:
        return {"schema_version": d.SCHEMA_ACTION, "id": str(row["id"]), "action_code": row["action_code"],
                "recorded_at": m.iso(row["recorded_at"])}

    def create_action(self, tenant_id: UUID, site_id: UUID, site_code: str, body: Any,
                      principal: str | None) -> tuple[int, dict[str, Any]]:
        _gate(principal)
        normalized = d.action_body(body)
        spec = d.DOMAINS[normalized["domain"]]
        actor = _actor(body, principal, spec.refuse("DOMAIN_INTENT_INVALID"))
        sha = d.command_sha256(tenant_id, site_id, None, d.CMD_ACTION, normalized, actor)

        def work(tx: Any) -> tuple[int, dict[str, Any]]:
            tx.lock(d.CMD_ACTION, normalized["idempotency_key"])
            prior = tx.action_by_key(normalized["idempotency_key"])
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise spec.refuse("DOMAIN_INTENT_CONFLICT")
                return 200, self._action_response(prior)
            now = tx.db_now()
            if not d.within_command_window(normalized["raised_at"], now):
                raise spec.refuse("DOMAIN_INTENT_INVALID")
            # Pre-flight 11: Site type, tenant/Site scope, Finding domain and the exact selected revision agree.
            if tx.site_type() != spec.domain:
                raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
            revision = tx.finding_revision(normalized["origin_finding_id"], normalized["origin_finding_revision_id"])
            if revision is None or revision["domain"] != spec.finding_domain:
                raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
            pin = tx.selected_pin(revision)
            if pin is None or (spec.domain == d.EV_DOMAIN and selected_ev_finding(tx, pin, revision["id"]) is None):
                raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
            number = tx.next_action_no()
            row = {"id": self._id(), "action_no": number, "action_code": f"ACT-{number:06d}",
                   "domain": spec.domain, "origin_finding_id": normalized["origin_finding_id"],
                   "origin_finding_revision_id": normalized["origin_finding_revision_id"],
                   "title": normalized["title"], "owner_label": normalized["owner_label"],
                   "due_at": normalized["due_at"], "raised_at": normalized["raised_at"],
                   "idempotency_key": normalized["idempotency_key"], "payload_sha256": sha, **_actor_row(actor)}
            tx.insert_action(row)
            return 201, self._action_response({**row, "recorded_at": now})

        return self._store.transaction(tenant_id, site_id, site_code, work)

    # ---- declared intent -----------------------------------------------------------------------------------

    @staticmethod
    def _intent_token(tx: Any, tenant_id: UUID, site_id: UUID, action: Mapping[str, Any], intent_id: str,
                      basis: Mapping[str, Any], upto: Any) -> str:
        case = None
        if basis["work_case_id"] is not None:
            case = tx.selected_case_link(str(action["id"]), basis["work_case_id"], upto)
        return d.selection_token(tenant_id, site_id, action, basis["finding_revision_id"], intent_id, case,
                                 basis["work_record_id"], basis["accepted_evidence_ids"])

    def post_intent(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: str, body: Any,
                    principal: str | None) -> tuple[int, dict[str, Any]]:
        _gate(principal)
        shape = d.intent_shape(body)
        actor = _actor(body, principal, d.neutral(d.NEUTRAL_INTENT_INVALID))
        aid = d.path_action_id(action_id)

        def respond(tx: Any, action: Mapping[str, Any], intent_id: str, basis: Mapping[str, Any],
                    recorded_at: Any) -> dict[str, Any]:
            return {"schema_version": d.SCHEMA_INTENT, "intent_id": intent_id, "action_id": str(action["id"]),
                    "recorded_at": m.iso(recorded_at),
                    "selection_token": self._intent_token(tx, tenant_id, site_id, action, intent_id, basis,
                                                          recorded_at)}

        def work(tx: Any) -> tuple[int, dict[str, Any]]:
            action = None if aid is None else tx.action(aid)
            if action is None:
                raise d.refuse("ACTION_NOT_FOUND")
            spec = _spec(action)
            normalized = d.intent_for(spec, shape)
            sha = d.command_sha256(tenant_id, site_id, aid, d.CMD_INTENT, normalized, actor)
            tx.lock(d.CMD_INTENT, f"{aid}:{normalized['idempotency_key']}")
            prior = tx.intent_by_key(aid, normalized["idempotency_key"])
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise spec.refuse("DOMAIN_INTENT_CONFLICT")
                return 200, respond(tx, action, prior["id"], prior["basis"], prior["recorded_at"])
            now = tx.db_now()
            if not (normalized["declared_at"] >= action["raised_at"]
                    and d.within_command_window(normalized["declared_at"], now)):
                raise spec.refuse("DOMAIN_INTENT_INVALID")
            basis = normalized["basis"]
            self._check_basis(tx, spec, action, basis)
            ids, superseded = tx.intent_ids(aid)
            heads = [i for i in ids if i not in superseded]
            if normalized["supersedes_id"] is None:
                if ids:
                    raise spec.refuse("DOMAIN_INTENT_CONFLICT")  # the root already exists
            elif heads != [normalized["supersedes_id"]]:
                raise spec.refuse("DOMAIN_INTENT_CONFLICT")  # supersession must target the current head
            intent_id = self._id()
            tx.insert_intent({"id": intent_id, "action_id": aid, "supersedes_id": normalized["supersedes_id"],
                              "declared_at": normalized["declared_at"], "criteria": normalized["criteria"],
                              "basis": basis, "idempotency_key": normalized["idempotency_key"],
                              "payload_sha256": sha, **_actor_row(actor)})
            return 201, respond(tx, action, intent_id, basis, now)

        return self._store.transaction(tenant_id, site_id, site_code, work)

    @staticmethod
    def _check_basis(tx: Any, spec: d.DomainSpec, action: Mapping[str, Any], basis: Mapping[str, Any]) -> None:
        """Ruling A3 / readiness 27 at `command_now`: the root's pinned Finding revision, still selected; an
        explicitly linked case; a performed record on that request; cold evidence inside the selected Finding's cited
        accepted basis, EV sessions and evidence inside the three selected sets (readiness 30). Any failure is the
        domain's 422 link refusal, never a silent intersection."""
        def link() -> d.DomainIntentRefused:
            return spec.refuse("DOMAIN_INTENT_LINK_INVALID")

        if basis["finding_revision_id"] != action["origin_finding_revision_id"]:
            raise link()
        revision = tx.finding_revision(action["origin_finding_id"], action["origin_finding_revision_id"])
        if revision is None or revision["domain"] != spec.finding_domain:
            raise link()
        pin = tx.selected_pin(revision)
        if pin is None:
            raise link()
        ev = None
        if spec.domain == d.EV_DOMAIN:
            ev = selected_ev_finding(tx, pin, revision["id"])
            if ev is None:
                raise link()
        if basis["work_case_id"] is not None:
            if tx.selected_case_link(str(action["id"]), basis["work_case_id"], tx.db_now()) is None:
                raise link()
            if basis["work_record_id"] is not None:
                case = tx.case(basis["work_case_id"])
                if (case is None or case["kind"] != m.REQUEST
                        or not tx.record_in_case(basis["work_case_id"], basis["work_record_id"])):
                    raise link()
        if ev is None:
            if not set(basis["accepted_evidence_ids"]) <= tx.cited_evidence(action["origin_finding_revision_id"]):
                raise link()
        elif not d.ev_members_selected(ev, basis):
            raise link()

    # ---- explicit W4 case link -----------------------------------------------------------------------------

    def post_case_link(self, tenant_id: UUID, site_id: UUID, site_code: str, action_id: str, body: Any,
                       principal: str | None) -> tuple[int, dict[str, Any]]:
        _gate(principal)
        normalized = d.case_link_body(body)
        actor = _actor(body, principal, d.neutral(d.NEUTRAL_CASE_LINK_INVALID))
        aid = d.path_action_id(action_id)
        sha = d.command_sha256(tenant_id, site_id, aid, d.CMD_CASE_LINK, normalized, actor)

        def respond(row: Mapping[str, Any]) -> dict[str, Any]:
            return {"schema_version": d.SCHEMA_CASE_LINK, "case_link_id": str(row["id"]),
                    "action_id": str(row["action_id"]), "case_id": str(row["case_id"]),
                    "recorded_at": m.iso(row["recorded_at"])}

        def work(tx: Any) -> tuple[int, dict[str, Any]]:
            action = None if aid is None else tx.action(aid)
            if action is None:
                raise d.refuse("ACTION_NOT_FOUND")
            spec = _spec(action)
            tx.lock(d.CMD_CASE_LINK, f"{aid}:{normalized['idempotency_key']}")
            prior = tx.case_link_by_key(aid, normalized["idempotency_key"])
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise spec.refuse("DOMAIN_INTENT_BASIS_CHANGED")
                return 200, respond(prior)
            case_id, rev_id, event_id = (normalized["case_id"], normalized["case_revision_id"],
                                         normalized["case_event_id"])
            if tx.case(case_id) is None:
                raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
            revisions, events, head_revision, last_event = tx.case_heads(case_id)
            if rev_id not in revisions or event_id not in events:
                raise spec.refuse("DOMAIN_INTENT_LINK_INVALID")
            if (rev_id, event_id) != (head_revision, last_event):
                raise spec.refuse("DOMAIN_INTENT_BASIS_CHANGED")  # a newer revision or event is now selected
            if tx.case_link_exists(aid, case_id, rev_id, event_id):
                raise spec.refuse("DOMAIN_INTENT_CONFLICT")  # this exact selection is already linked under another key
            row = {"id": self._id(), "action_id": aid, "case_id": case_id, "case_revision_id": rev_id,
                   "case_event_id": event_id, "idempotency_key": normalized["idempotency_key"],
                   "payload_sha256": sha, **_actor_row(actor)}
            tx.insert_case_link(row)
            return 201, respond({**row, "recorded_at": tx.db_now()})

        return self._store.transaction(tenant_id, site_id, site_code, work)
