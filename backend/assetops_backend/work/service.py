"""W4-01 commit 2: the work command service (`.agent/W4-01-build-spec.md` "Commit sequence" item 2).

The service owns validation, authorization, state reduction and exact-link checks; the store port runs each
command in one SERIALIZABLE transaction (`WorkStore.transaction`) and hands back a transaction object whose reads
and INSERTs all use that one connection and DB time. Order per command (Run 1 rulings, "Creation and retry
order"): write principal, closed shape (the actor object is exactly `kind,id,attestation`), actor authority,
canonical path/body hash, then in the transaction the scoped idempotency lookup (an identical retry returns the
stored result with 200 even after a clock advance or a newer head; a different hash is 409), and only for a first
submission the occurrence bounds, accepted-evidence `received_at <=` DB time, pinned links, current predecessor
and the atomic INSERTs. Case provenance is the shared W3 `PublicProvenance` DTO over Q11's selected IDs and cited
union; this module never builds a second DTO.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping, Protocol
from uuid import UUID, uuid4

from assetops_backend.evidence.public_provenance import LinkRowsReads, PublicProvenance, canonical_reasons
from assetops_backend.work import model as m
from assetops_backend.work.model import WorkRefused

Result = tuple[int, dict[str, Any]]

CASE_CREATE_KEYS = ("kind", "occurred_at", "asset_id", "finding_links", "action_links", "title", "narrative",
                    "cited_accepted_evidence_ids", "actor", "idempotency_key")
REVISION_KEYS = ("supersedes_revision_id", "title", "narrative", "reason", "occurred_at", "actor", "idempotency_key")
REVISION_OPTIONAL = ("cited_accepted_evidence_ids", "finding_links", "action_links")
EVENT_KEYS = ("kind", "occurred_at", "payload", "actor", "idempotency_key")
RECORD_KEYS = ("activity", "outcome_note", "occurred_at", "actor", "idempotency_key")
PLAN_KEYS = ("asset_id", "title", "trigger_kind", "next_due_at", "next_due_hours", "occurred_at", "actor",
             "idempotency_key")
PLAN_CORRECTION = ("supersedes_plan_id", "canonical_plan_id", "correction_reason")
OPERATIONAL_KEYS = ("kind", "body", "occurred_at", "period_end", "unit", "quantity", "source_document_sha256",
                    "case_id", "actor", "idempotency_key")
OPERATIONAL_CORRECTION = ("supersedes_record_id", "canonical_record_id", "correction_reason")
OPERATIONAL_KINDS = ("OPERATOR_LOG", "MANUAL_READING", "SHIFT_NOTE", "SITE_VISIT")


def case_provenance(tx: Any, tenant_id: UUID, site_id: UUID, links: Mapping[str, Any], revision_id: str,
                    event_ids: list[str], record_id: str | None) -> dict[str, Any]:
    """Q11 on the caller's transaction (command or read): the selected IDs are the selected revision, the given
    events, the selected latest record, pinned Finding revisions and pinned Action events; the cited set is the
    revision's evidence plus each pinned Finding revision's and each pinned Action's basis and origin revision's."""
    selected, cited = case_basis(tx, links, revision_id, event_ids, record_id)
    return provenance_dto(tx, tenant_id, site_id, cited, selected)


def case_basis(tx: Any, links: Mapping[str, Any], revision_id: str, event_ids: list[str],
               record_id: str | None) -> tuple[list[str], list[str]]:
    """Q11's sorted selected-ID set and full available cited accepted-ID union for one selected case (W4 commit 4
    splits it from the DTO so the list can classify the union over every eligible case)."""
    finding_revs = [f["finding_revision_id"] for f in links["finding_links"]]
    action_events = [a["action_event_id"] for a in links["action_links"]]
    selected = {revision_id, *event_ids, *finding_revs, *action_events, *([record_id] if record_id else [])}
    cited = set(links["evidence_ids"]) | set(tx.lineage_evidence(
        finding_revs, [a["action_id"] for a in links["action_links"]]))
    return sorted(str(x) for x in selected), sorted(str(x) for x in cited)


def provenance_dto(tx: Any, tenant_id: UUID, site_id: UUID, cited: list[str],
                   selected: list[str]) -> dict[str, Any]:
    reads = LinkRowsReads(lambda t, s, ids: tx.link_rows(ids))
    return PublicProvenance(reads).cited_set(tenant_id, site_id, sorted(cited), selected, detail=False)


LINK_SELECTION_MISSING_REASON = {"code": "LINK_SELECTION_MISSING", "accepted_evidence_ids": []}


def missing_lineage(dto: Mapping[str, Any]) -> dict[str, Any]:
    """q7-4: a pinned Finding revision, Action event, Action root or origin revision absent/foreign at the cutoff.
    The DTO's IDs and computed basis stay; classification and state become UNKNOWN and the reasons gain
    `LINK_SELECTION_MISSING` (canonically sorted, identical reasons deduplicated). Never a complete subset claim."""
    seen, reasons = set(), []
    for reason in canonical_reasons([*dto["reasons"], LINK_SELECTION_MISSING_REASON]):
        key = m.canonical_json(reason)
        if key not in seen:
            seen.add(key)
            reasons.append(reason)
    return {**dto, "classification": "UNKNOWN", "state": "UNKNOWN", "reasons": reasons}


class WorkStore(Protocol):
    def transaction(self, tenant_id: UUID, site_id: UUID, work: Callable[[Any], Any]) -> Any: ...


class WorkService:
    def __init__(self, store: WorkStore, *, new_id: Callable[[], UUID] = uuid4) -> None:
        self._store = store
        self._new_id = new_id

    # ---- shared steps ----------------------------------------------------------------------------------------

    def _id(self) -> str:
        return str(self._new_id())

    @staticmethod
    def _actor(body: Mapping[str, Any], principal: str | None) -> m.Actor:
        return m.authorize(m.actor_shape(body["actor"]), principal)

    @staticmethod
    def _gate(principal: str | None) -> None:
        if principal is None:
            raise WorkRefused("WORK_WRITE_FORBIDDEN")

    @staticmethod
    def _retry(stored_sha: str, sha: str) -> None:
        if stored_sha != sha:
            raise WorkRefused("WORK_EVENT_DUPLICATE_KEY")

    @staticmethod
    def _check_links(tx: Any, finding: list[dict[str, str]], action: list[dict[str, str]], evidence: list[str],
                     asset_id: str | None, db_now: datetime) -> None:
        if asset_id is not None and not tx.asset_in_scope(asset_id):
            raise WorkRefused("WORK_LINK_SCOPE_INVALID")
        pairs = [(f["finding_id"], f["finding_revision_id"]) for f in finding]
        if pairs and tx.finding_pairs_in_scope(pairs) != set(pairs):
            raise WorkRefused("WORK_LINK_SCOPE_INVALID")
        # Run 1 dry-read: the two scoped FKs do not prove the event belongs to the Action; the pair is checked here.
        pairs = [(a["action_id"], a["action_event_id"]) for a in action]
        if pairs and tx.action_pairs_in_scope(pairs) != set(pairs):
            raise WorkRefused("WORK_LINK_SCOPE_INVALID")
        if evidence:
            # q2 ruling 4: scoped rows with `received_at <= :command_now`; `db_now` is that same command instant.
            if tx.accepted_evidence_by_command_now(evidence) != {str(v) for v in evidence}:
                raise WorkRefused("WORK_LINK_SCOPE_INVALID")

    def provenance(self, tx: Any, tenant_id: UUID, site_id: UUID, case_id: str, *,
                   upto_revision: Mapping[str, Any], upto_event: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Q11: selected IDs are the selected revision, every event through the selection, the latest same-case
        record, pinned Finding revisions and pinned Action events; the cited set is the revision's evidence plus
        each pinned Finding revision's evidence plus each pinned Action's basis evidence and origin revision's."""
        rev_id = str(upto_revision["id"])
        links = tx.revision_links(rev_id)
        cutoff = upto_event or upto_revision
        events = [str(e["id"]) for e in tx.events(case_id) if (e["recorded_at"], str(e["id"])) <=
                  (cutoff["recorded_at"], str(cutoff["id"]))]
        record = tx.latest_record(case_id, cutoff["recorded_at"])
        return case_provenance(tx, tenant_id, site_id, links, rev_id, events,
                               None if record is None else str(record["id"]))

    # ---- case create -----------------------------------------------------------------------------------------

    def create_case(self, tenant_id: UUID, site_id: UUID, body: Any, principal: str | None) -> Result:
        self._gate(principal)
        if not isinstance(body, dict):
            raise m.invalid()
        kind = body.get("kind")
        if kind not in m.CASE_KINDS:
            raise m.invalid()
        m.closed(body, CASE_CREATE_KEYS, ("incident_id",) if kind == m.REQUEST else ())
        actor = self._actor(body, principal)
        occurred_at = m.utc_instant(body["occurred_at"])
        canon = {"kind": kind, "occurred_at": m.iso(occurred_at), "asset_id": m.optional_uuid(body["asset_id"]),
                 "finding_links": m.finding_links(body["finding_links"]),
                 "action_links": m.action_links(body["action_links"]),
                 "title": m.text_value(body["title"], 1, 200), "narrative": m.text_value(body["narrative"], 1, 4000),
                 "cited_accepted_evidence_ids": m.uuid_set(body["cited_accepted_evidence_ids"]),
                 "actor": actor.canonical(), "idempotency_key": m.idempotency_key(body["idempotency_key"])}
        if "incident_id" in body:
            canon["incident_id"] = m.optional_uuid(body["incident_id"])
        sha = m.command_sha256({"site_id": str(site_id)}, canon)

        def work(tx: Any) -> Result:
            prior = tx.case_by_create_key(canon["idempotency_key"])
            if prior is not None:
                self._retry(prior["create_payload_sha256"], sha)
                return 200, self._case_body(tx, tenant_id, site_id, prior)
            db_now = tx.db_now()
            m.check_occurrence(occurred_at, db_now)
            self._check_links(tx, canon["finding_links"], canon["action_links"],
                              canon["cited_accepted_evidence_ids"], canon["asset_id"], db_now)
            incident_id = canon.get("incident_id")
            if incident_id is not None and not tx.incident_in_scope(incident_id):
                raise WorkRefused("WORK_LINK_SCOPE_INVALID")
            case_id, rev_id, event_id = self._id(), self._id(), self._id()
            no = tx.next_public_no()
            row = {"id": case_id, "kind": kind, "public_no": no, "public_code": f"{m.CODE_PREFIX[kind]}-{no:06d}",
                   "asset_id": canon["asset_id"], "occurred_at": occurred_at, "create_key": canon["idempotency_key"],
                   "create_payload_sha256": sha, **self._actor_cols(actor)}
            tx.insert_case(row)
            if kind == m.INCIDENT:
                tx.insert_incident(case_id, canon["idempotency_key"])
            else:
                tx.insert_request(case_id, canon["idempotency_key"], incident_id)
            self._insert_revision(tx, {"id": rev_id, "case_id": case_id, "revision_no": 1,
                                       "supersedes_revision_id": None, "title": canon["title"],
                                       "narrative": canon["narrative"], "reason": None, "occurred_at": occurred_at,
                                       "idempotency_key": canon["idempotency_key"], "payload_sha256": sha,
                                       **self._actor_cols(actor)},
                                  canon["finding_links"], canon["action_links"], canon["cited_accepted_evidence_ids"])
            tx.insert_event({"id": event_id, "case_id": case_id, "kind": "CREATED", "payload": {},
                             "occurred_at": occurred_at, "idempotency_key": canon["idempotency_key"],
                             "payload_sha256": sha, **self._actor_cols(actor)})
            return 201, self._case_body(tx, tenant_id, site_id, tx.case(case_id))

        return self._store.transaction(tenant_id, site_id, work)

    @staticmethod
    def _actor_cols(actor: m.Actor) -> dict[str, str]:
        return {"actor_kind": actor.kind, "actor_id": actor.id, "attestation": actor.attestation,
                "authorization_basis": actor.authorization_basis}

    @staticmethod
    def _insert_revision(tx: Any, row: dict[str, Any], finding: list[dict[str, str]], action: list[dict[str, str]],
                         evidence: list[str]) -> None:
        tx.insert_revision(row)
        for link in finding:
            tx.insert_finding_link(row["id"], link["finding_id"], link["finding_revision_id"])
        for link in action:
            tx.insert_action_link(row["id"], link["action_id"], link["action_event_id"])
        for evidence_id in evidence:
            tx.insert_case_evidence(row["id"], evidence_id)

    def _case_body(self, tx: Any, tenant_id: UUID, site_id: UUID, case: Mapping[str, Any]) -> dict[str, Any]:
        """The `work-case-1` create result, rebuilt from the stored revision 1 and CREATED event."""
        case_id = str(case["id"])
        revision = tx.revisions(case_id)[0]
        created = next(e for e in tx.events(case_id) if e["kind"] == "CREATED")
        return {"schema_version": m.SCHEMA_CASE, "id": case_id, "code": case["public_code"], "kind": case["kind"],
                "site_id": str(site_id), "revision": {"id": str(revision["id"]), "number": revision["revision_no"]},
                "event": {"id": str(created["id"]), "kind": "CREATED", "recorded_at": m.iso(created["recorded_at"])},
                "state": "OPEN",
                "source_provenance": self.provenance(tx, tenant_id, site_id, case_id, upto_revision=revision,
                                                     upto_event=created)}

    def _locked_case(self, tx: Any, case_id: Any) -> dict[str, Any]:
        try:
            case_id = m.uuid_text(case_id)
        except WorkRefused:
            raise WorkRefused("WORK_CASE_NOT_FOUND") from None
        case = tx.lock_case(case_id)
        if case is None:
            raise WorkRefused("WORK_CASE_NOT_FOUND")
        return case

    # ---- events ----------------------------------------------------------------------------------------------

    def post_event(self, tenant_id: UUID, site_id: UUID, case_id: Any, body: Any, principal: str | None) -> Result:
        self._gate(principal)
        m.closed(body, EVENT_KEYS)
        kind = body["kind"]
        if kind in m.OUTCOME_REQUESTS:
            raise WorkRefused("WORK_OUTCOME_NOT_SUPPORTED")
        if kind in m.RESERVED_EVENTS:
            raise WorkRefused("WORK_TRANSITION_INVALID")
        if kind not in m.WRITABLE_EVENTS:
            raise m.invalid()
        payload = m.event_payload(kind, body["payload"])
        actor = self._actor(body, principal)
        occurred_at = m.utc_instant(body["occurred_at"])

        def work(tx: Any) -> Result:
            case = self._locked_case(tx, case_id)
            cid = str(case["id"])
            canon = {"kind": kind, "occurred_at": m.iso(occurred_at), "payload": payload,
                     "actor": actor.canonical(), "idempotency_key": m.idempotency_key(body["idempotency_key"])}
            sha = m.command_sha256({"site_id": str(site_id), "case_id": cid}, canon)
            events = tx.events(cid)
            prior = next((e for e in events if e["idempotency_key"] == canon["idempotency_key"]), None)
            if prior is not None:
                self._retry(prior["payload_sha256"], sha)
                return 200, self._event_body(tx, case, prior, events)
            db_now = tx.db_now()
            m.check_occurrence(occurred_at, db_now)
            m.next_state(case["kind"], m.reduce_state(case["kind"], events), kind)
            if kind == "COMPLETE" and not tx.record_in_case(cid, payload["maintenance_record_id"]):
                raise WorkRefused("WORK_LINK_SCOPE_INVALID")
            event_id = self._id()
            tx.insert_event({"id": event_id, "case_id": cid, "kind": kind, "payload": payload,
                             "occurred_at": occurred_at, "idempotency_key": canon["idempotency_key"],
                             "payload_sha256": sha, **self._actor_cols(actor)})
            events = tx.events(cid)
            return 201, self._event_body(tx, case, next(e for e in events if str(e["id"]) == event_id), events)

        return self._store.transaction(tenant_id, site_id, work)

    @staticmethod
    def _event_body(tx: Any, case: Mapping[str, Any], event: Mapping[str, Any], events: list[dict[str, Any]]
                    ) -> dict[str, Any]:
        """`work-event-1`: the state reduced through this event and the head revision recorded by then."""
        upto = (event["recorded_at"], str(event["id"]))
        through = [e for e in events if (e["recorded_at"], str(e["id"])) <= upto]
        revisions = [r for r in tx.revisions(str(case["id"])) if (r["recorded_at"], str(r["id"])) <= upto]
        return {"schema_version": m.SCHEMA_EVENT, "case_id": str(case["id"]),
                "event": {"id": str(event["id"]), "kind": event["kind"], "payload": event["payload"],
                          "occurred_at": m.iso(event["occurred_at"]), "recorded_at": m.iso(event["recorded_at"])},
                "state": m.reduce_state(case["kind"], through), "revision_id": str(revisions[-1]["id"])}

    # ---- revisions (corrections) -----------------------------------------------------------------------------

    def post_revision(self, tenant_id: UUID, site_id: UUID, case_id: Any, body: Any, principal: str | None
                      ) -> Result:
        self._gate(principal)
        m.closed(body, REVISION_KEYS, REVISION_OPTIONAL)
        actor = self._actor(body, principal)
        occurred_at = m.utc_instant(body["occurred_at"])
        canon: dict[str, Any] = {
            "supersedes_revision_id": m.uuid_text(body["supersedes_revision_id"]),
            "title": m.text_value(body["title"], 1, 200), "narrative": m.text_value(body["narrative"], 1, 4000),
            "reason": m.text_value(body["reason"], 1, 500), "occurred_at": m.iso(occurred_at),
            "actor": actor.canonical(), "idempotency_key": m.idempotency_key(body["idempotency_key"])}
        if "cited_accepted_evidence_ids" in body:
            canon["cited_accepted_evidence_ids"] = m.uuid_set(body["cited_accepted_evidence_ids"])
        if "finding_links" in body:
            canon["finding_links"] = m.finding_links(body["finding_links"])
        if "action_links" in body:
            canon["action_links"] = m.action_links(body["action_links"])

        def work(tx: Any) -> Result:
            case = self._locked_case(tx, case_id)
            cid = str(case["id"])
            sha = m.command_sha256({"site_id": str(site_id), "case_id": cid}, canon)
            revisions = tx.revisions(cid)
            prior = next((r for r in revisions if r["idempotency_key"] == canon["idempotency_key"]), None)
            if prior is not None:
                self._retry(prior["payload_sha256"], sha)
                return 200, self._revision_body(prior)
            db_now = tx.db_now()
            m.check_occurrence(occurred_at, db_now)
            head = max(revisions, key=lambda r: r["revision_no"])
            if str(head["id"]) != canon["supersedes_revision_id"]:
                raise WorkRefused("WORK_CORRECTION_CONFLICT")
            current = tx.revision_links(str(head["id"]))
            finding = canon.get("finding_links", current["finding_links"])
            action = canon.get("action_links", current["action_links"])
            evidence = canon.get("cited_accepted_evidence_ids", current["evidence_ids"])
            self._check_links(tx, finding, action, evidence, None, db_now)
            row = {"id": self._id(), "case_id": cid, "revision_no": head["revision_no"] + 1,
                   "supersedes_revision_id": str(head["id"]), "title": canon["title"],
                   "narrative": canon["narrative"], "reason": canon["reason"], "occurred_at": occurred_at,
                   "idempotency_key": canon["idempotency_key"], "payload_sha256": sha, **self._actor_cols(actor)}
            self._insert_revision(tx, row, finding, action, evidence)
            return 201, self._revision_body(row)

        return self._store.transaction(tenant_id, site_id, work)

    @staticmethod
    def _revision_body(row: Mapping[str, Any]) -> dict[str, Any]:
        sup = row["supersedes_revision_id"]
        return {"case_id": str(row["case_id"]), "revision_id": str(row["id"]), "revision_no": row["revision_no"],
                "supersedes_revision_id": None if sup is None else str(sup)}

    # ---- performed activity ----------------------------------------------------------------------------------

    def post_record(self, tenant_id: UUID, site_id: UUID, case_id: Any, body: Any, principal: str | None) -> Result:
        self._gate(principal)
        m.closed(body, RECORD_KEYS)
        actor = self._actor(body, principal)
        occurred_at = m.utc_instant(body["occurred_at"])
        canon = {"activity": m.text_value(body["activity"], 1, 4000),
                 "outcome_note": m.optional_text(body["outcome_note"], 1, 2000), "occurred_at": m.iso(occurred_at),
                 "actor": actor.canonical(), "idempotency_key": m.idempotency_key(body["idempotency_key"])}

        def work(tx: Any) -> Result:
            case = self._locked_case(tx, case_id)
            cid = str(case["id"])
            if case["kind"] != m.REQUEST:
                raise m.invalid()
            sha = m.command_sha256({"site_id": str(site_id), "case_id": cid}, canon)
            prior = tx.record_by_key(cid, canon["idempotency_key"])
            if prior is not None:
                self._retry(prior["payload_sha256"], sha)
                return 200, self._record_body(prior)
            m.check_occurrence(occurred_at, tx.db_now())
            rid = self._id()
            tx.insert_record({"id": rid, "case_id": cid, "activity": canon["activity"],
                              "outcome_note": canon["outcome_note"], "occurred_at": occurred_at,
                              "idempotency_key": canon["idempotency_key"], "payload_sha256": sha,
                              **self._actor_cols(actor)})
            return 201, self._record_body(tx.record_by_key(cid, canon["idempotency_key"]))

        return self._store.transaction(tenant_id, site_id, work)

    @staticmethod
    def _record_body(row: Mapping[str, Any]) -> dict[str, Any]:
        return {"schema_version": m.SCHEMA_RECORD, "id": str(row["id"]), "case_id": str(row["case_id"]),
                "recorded_at": m.iso(row["recorded_at"]), "outcome": "UNVERIFIED"}

    # ---- lineage roots: draft plans and authored operational records -----------------------------------------

    @staticmethod
    def _correction(body: Mapping[str, Any], keys: tuple[str, str, str]) -> dict[str, Any] | None:
        present = [k for k in keys if k in body]
        if not present:
            return None
        if len(present) != 3:
            raise m.invalid()
        return {keys[0]: m.uuid_text(body[keys[0]]), keys[1]: m.uuid_text(body[keys[1]]),
                keys[2]: m.text_value(body[keys[2]], 1, 500)}

    @staticmethod
    def _successor(tx: Any, table: str, correction: Mapping[str, Any] | None, keys: tuple[str, str, str]
                   ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        """(root, head) for a correction under the root row lock; a non-head or wrong-root predecessor is 409."""
        if correction is None:
            return None, None
        root = tx.lock_root(table, correction[keys[1]])
        if root is None:
            raise WorkRefused("WORK_CORRECTION_CONFLICT")
        head = tx.lineage_head(table, str(root["id"]))
        if str(head["id"]) != correction[keys[0]]:
            raise WorkRefused("WORK_CORRECTION_CONFLICT")
        return root, head

    def post_plan(self, tenant_id: UUID, site_id: UUID, body: Any, principal: str | None) -> Result:
        self._gate(principal)
        m.closed(body, PLAN_KEYS, PLAN_CORRECTION)
        actor = self._actor(body, principal)
        correction = self._correction(body, PLAN_CORRECTION)
        occurred_at = m.utc_instant(body["occurred_at"])
        trigger = body["trigger_kind"]
        if trigger not in ("CALENDAR", "RUN_HOURS"):
            raise m.invalid()
        due_at = m.optional_instant(body["next_due_at"])
        due_hours = m.decimal_value(body["next_due_hours"])
        if (trigger == "CALENDAR" and due_hours is not None) or (trigger == "RUN_HOURS" and due_at is not None):
            raise m.invalid()
        canon = {"asset_id": m.optional_uuid(body["asset_id"]), "title": m.text_value(body["title"], 1, 200),
                 "trigger_kind": trigger, "next_due_at": None if due_at is None else m.iso(due_at),
                 "next_due_hours": m.decimal_text(due_hours), "occurred_at": m.iso(occurred_at),
                 "actor": actor.canonical(), "idempotency_key": m.idempotency_key(body["idempotency_key"]),
                 **(correction or {})}
        path = {"site_id": str(site_id), **({"canonical_plan_id": correction["canonical_plan_id"]} if correction
                                            else {})}
        sha = m.command_sha256(path, canon)

        def work(tx: Any) -> Result:
            prior = tx.lineage_by_key("maintenance_plan", canon["idempotency_key"])
            if prior is not None:
                self._retry(prior["payload_sha256"], sha)
                return 200, self._lineage_body(tx, "maintenance_plan", prior)
            db_now = tx.db_now()
            m.check_occurrence(occurred_at, db_now)
            if canon["asset_id"] is not None and not tx.asset_in_scope(canon["asset_id"]):
                raise WorkRefused("WORK_LINK_SCOPE_INVALID")
            root, head = self._successor(tx, "maintenance_plan", correction, PLAN_CORRECTION)
            pid, no = self._id(), tx.next_public_no()
            tx.insert_plan({"id": pid, "public_no": no, "public_code": f"PM-{no:06d}",
                            "canonical_plan_id": pid if root is None else str(root["id"]),
                            "asset_id": canon["asset_id"], "title": canon["title"], "trigger_kind": trigger,
                            "next_due_at": due_at, "next_due_hours": canon["next_due_hours"], "state": "DRAFT",
                            "supersedes_plan_id": None if head is None else str(head["id"]),
                            "correction_reason": None if correction is None else correction["correction_reason"],
                            "occurred_at": occurred_at, "idempotency_key": canon["idempotency_key"],
                            "payload_sha256": sha, **self._actor_cols(actor)})
            return 201, self._lineage_body(tx, "maintenance_plan", tx.lineage_by_key("maintenance_plan",
                                                                                     canon["idempotency_key"]))

        return self._store.transaction(tenant_id, site_id, work)

    def post_operational_record(self, tenant_id: UUID, site_id: UUID, body: Any, principal: str | None) -> Result:
        self._gate(principal)
        m.closed(body, OPERATIONAL_KEYS, OPERATIONAL_CORRECTION)
        actor = self._actor(body, principal)
        correction = self._correction(body, OPERATIONAL_CORRECTION)
        kind = body["kind"]
        if kind not in OPERATIONAL_KINDS:
            raise m.invalid()
        occurred_at = m.utc_instant(body["occurred_at"])
        period_end = m.optional_instant(body["period_end"])
        quantity = m.decimal_value(body["quantity"])
        unit = m.optional_text(body["unit"], 1, 32)
        digest = body["source_document_sha256"]
        if digest is not None and (not isinstance(digest, str) or not m.re.fullmatch(r"[0-9a-f]{64}", digest)):
            raise m.invalid()
        if ((quantity is None) != (unit is None) or (kind == "MANUAL_READING" and quantity is None)
                or (period_end is not None and period_end < occurred_at)):
            raise m.invalid()
        canon = {"kind": kind, "body": m.text_value(body["body"], 1, 4000), "occurred_at": m.iso(occurred_at),
                 "period_end": None if period_end is None else m.iso(period_end), "unit": unit,
                 "quantity": m.decimal_text(quantity), "source_document_sha256": digest,
                 "case_id": m.optional_uuid(body["case_id"]), "actor": actor.canonical(),
                 "idempotency_key": m.idempotency_key(body["idempotency_key"]), **(correction or {})}
        path = {"site_id": str(site_id), **({"canonical_record_id": correction["canonical_record_id"]} if correction
                                            else {})}
        sha = m.command_sha256(path, canon)

        def work(tx: Any) -> Result:
            prior = tx.lineage_by_key("operational_record", canon["idempotency_key"])
            if prior is not None:
                self._retry(prior["payload_sha256"], sha)
                return 200, self._lineage_body(tx, "operational_record", prior)
            m.check_occurrence(occurred_at, tx.db_now())
            if canon["case_id"] is not None and tx.case(canon["case_id"]) is None:
                raise WorkRefused("WORK_LINK_SCOPE_INVALID")
            root, head = self._successor(tx, "operational_record", correction, OPERATIONAL_CORRECTION)
            rid, no = self._id(), tx.next_public_no()
            tx.insert_operational_record({
                "id": rid, "public_no": no, "public_code": f"REC-{no:06d}",
                "canonical_record_id": rid if root is None else str(root["id"]), "kind": kind,
                "body": canon["body"], "period_end": period_end, "unit": unit, "quantity": canon["quantity"],
                "source_document_sha256": digest,
                "correction_reason": None if correction is None else correction["correction_reason"],
                "state": "SUBMITTED", "supersedes_record_id": None if head is None else str(head["id"]),
                "case_id": canon["case_id"], "occurred_at": occurred_at, "idempotency_key": canon["idempotency_key"],
                "payload_sha256": sha, **self._actor_cols(actor)})
            return 201, self._lineage_body(tx, "operational_record", tx.lineage_by_key("operational_record",
                                                                                       canon["idempotency_key"]))

        return self._store.transaction(tenant_id, site_id, work)

    @staticmethod
    def _lineage_body(tx: Any, table: str, row: Mapping[str, Any]) -> dict[str, Any]:
        """New version `id`/`recorded_at`, the canonical root ID and the root's visible public code."""
        if table == "maintenance_plan":
            root_id, schema, canonical_key = str(row["canonical_plan_id"]), m.SCHEMA_PLAN, "canonical_plan_id"
        else:
            root_id, schema, canonical_key = str(row["canonical_record_id"]), m.SCHEMA_OPERATIONAL, "canonical_record_id"
        root = row if str(row["id"]) == root_id else tx.lineage_row(table, root_id)
        return {"schema_version": schema, "id": str(row["id"]), canonical_key: root_id,
                "public_code": root["public_code"], "state": row["state"], "recorded_at": m.iso(row["recorded_at"])}
