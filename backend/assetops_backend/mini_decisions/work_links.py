"""W4-03 unit 8: explicit decision-to-work associations and the Site Work decision-context overlay.

`.agent/W4-03-build-spec.md`: "Work connection"; closure 1 (case-link command/response and the overlay read);
closure 4 B1/B2/N4; "Unit-5..12 rulings (u5)" unit 8 and the u6 unit-8 dry-read paragraph, which control.

- `POST /api/sites/{code}/work/decision-links` (`mini-decision-link-command-1` -> `mini-decision-link-write-1`).
- `GET /api/sites/{code}/work/decision-contexts?case_ids=&known_at=` (`mini-work-contexts-1`).

W4-01 tables, list envelopes, counts and cursors are never written or changed; the association table is separate.
All SQL lives in `store.py`.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.mini_decisions.model import DecisionPrincipal, DecisionRefused, case_not_found, invalid
from assetops_backend.mini_decisions.opportunities import _pins_visible, opportunity_code
from assetops_backend.mini_decisions.scenarios import _instant, _shape, admit, authorize, scenario_code
from assetops_backend.mini_decisions.store import (
    MiniDecisionStoreUnavailable,
    MiniDecisionWriteRefused,
    PostgresMiniDecisionStore,
)
from assetops_backend.mini_depth.read import iso
from assetops_backend.work import model as work

SCHEMA_COMMAND = "mini-decision-link-command-1"
SCHEMA_WRITE = "mini-decision-link-write-1"
SCHEMA_CONTEXTS = "mini-work-contexts-1"
ROUTE = "work/decision-links"
UNAVAILABLE = "Decision context unavailable"
MAX_CASES = 100
_LOWER_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def parse_case_ids(values: Sequence[str]) -> list[str]:
    """1-100 distinct comma-separated lowercase UUIDs, one `case_ids` parameter; else 422 `DECISION_INPUT_INVALID`."""
    if len(values) != 1:
        raise invalid()
    ids = values[0].split(",")
    if not 1 <= len(ids) <= MAX_CASES or len(set(ids)) != len(ids) or not all(_LOWER_UUID.match(i) for i in ids):
        raise invalid()
    return ids


class WorkLinkService:
    def __init__(self, store: PostgresMiniDecisionStore, *,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._store = store
        self.test_read_clock_override = test_read_clock_override

    # --- the association command ------------------------------------------------------------------------------

    def link(self, tenant_id: UUID, site_id: UUID, principal: DecisionPrincipal | None,
             body: Any) -> tuple[int, dict[str, Any]]:
        """Admission (403) before the body; the closed shape with exactly one decision ID (422); the actor; the
        canonical hash; then, under the case share-lock, an unknown/foreign case 404 `WORK_CASE_NOT_FOUND`, the
        idempotency lookup (exact retry 200 / changed body 409), a foreign decision 422
        `DECISION_LINK_SCOPE_INVALID`, and an already-linked pair under another key 409 `DECISION_DUPLICATE_KEY`."""
        principal = admit(principal, tenant_id, site_id)
        b = _shape(work.closed, body, ("schema_version", "idempotency_key", "actor", "case_id", "scenario_id",
                                       "opportunity_id"))
        if b["schema_version"] != SCHEMA_COMMAND:
            raise invalid()
        actor = _shape(work.actor_shape, b["actor"])

        def optional_id(value: Any) -> str | None:
            return None if value is None else _shape(work.uuid_text, value).lower()

        cmd = {"schema_version": SCHEMA_COMMAND,
               "idempotency_key": _shape(work.idempotency_key, b["idempotency_key"]),
               "actor": {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]},
               "case_id": _shape(work.uuid_text, b["case_id"]).lower(),
               "scenario_id": optional_id(b["scenario_id"]), "opportunity_id": optional_id(b["opportunity_id"])}
        if (cmd["scenario_id"] is None) == (cmd["opportunity_id"] is None):
            raise invalid()
        who = authorize(cmd["actor"], principal)
        sha = work.command_sha256({"site_id": str(site_id), "route": ROUTE}, cmd)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            if self._store.lock_work_case(c, tenant_id, site_id, cmd["case_id"]) is None:
                raise case_not_found()
            prior = self._store.work_link_by_key(c, tenant_id, site_id, cmd["idempotency_key"])
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise DecisionRefused("DECISION_DUPLICATE_KEY")
                return 200, self._write_body(prior)
            exists = (self._store.opportunity_exists(c, tenant_id, site_id, cmd["opportunity_id"])
                      if cmd["opportunity_id"] is not None
                      else self._store.scenario_exists(c, tenant_id, site_id, cmd["scenario_id"]))
            if not exists:
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            if self._store.work_link_pair(c, tenant_id, site_id, cmd["case_id"], cmd["scenario_id"],
                                          cmd["opportunity_id"]) is not None:
                raise DecisionRefused("DECISION_DUPLICATE_KEY")
            self._store.insert_work_link(c, {
                "id": uuid4(), "tenant_id": tenant_id, "site_id": site_id, "case_id": cmd["case_id"],
                "scenario_id": cmd["scenario_id"], "opportunity_id": cmd["opportunity_id"], **who,
                "idempotency_key": cmd["idempotency_key"], "payload_sha256": sha})
            return 201, self._write_body(self._store.work_link_by_key(c, tenant_id, site_id, cmd["idempotency_key"]))

        try:
            return self._write(write)
        except MiniDecisionWriteRefused:
            return self._write(write, final=True)  # a concurrent write committed first: the lookups answer

    def _write(self, work_: Callable[[Any], tuple[int, dict[str, Any]]],
               final: bool = False) -> tuple[int, dict[str, Any]]:
        """One write transaction. `final` (the single retry, or a write with none): a further race or store
        refusal is 503 `DECISION_STORE_UNAVAILABLE`, never an uncaught 500 (final review L3, uF 5)."""
        try:
            with self._store.transaction() as c:
                return work_(c)
        except MiniDecisionWriteRefused as error:
            if final:
                raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error
            raise
        except MiniDecisionStoreUnavailable as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    @staticmethod
    def _write_body(link: Mapping[str, Any] | None) -> dict[str, Any]:
        assert link is not None
        opportunity = link["opportunity_id"] is not None
        return {"schema_version": SCHEMA_WRITE, "id": str(link["id"]), "case_id": str(link["case_id"]),
                "kind": "OPPORTUNITY" if opportunity else "SCENARIO",
                "decision_id": str(link["opportunity_id"] if opportunity else link["scenario_id"]),
                "recorded_at": iso(link["created_at"])}

    # --- the overlay read -------------------------------------------------------------------------------------

    def contexts(self, tenant_id: UUID, site_id: UUID, site_code: str, case_values: Sequence[str],
                 known: Sequence[str]) -> dict[str, Any]:
        case_ids = parse_case_ids(case_values)
        if len(known) > 1:
            raise DecisionRefused("INVALID_KNOWN_AT")
        explicit = _instant(known[0], "INVALID_KNOWN_AT") if known else None
        try:
            with self._store.snapshot() as c:
                read_time = self._store.db_now(c)
                if self.test_read_clock_override is not None:
                    read_time = self.test_read_clock_override()
                return self._contexts(c, tenant_id, site_id, site_code, case_ids, explicit, read_time)
        except MiniDecisionStoreUnavailable as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    def _contexts(self, c: Any, t: UUID, s: UUID, site_code: str, case_ids: list[str], explicit: datetime | None,
                  read_time: datetime) -> dict[str, Any]:
        if explicit is not None and explicit > read_time:
            raise DecisionRefused("INVALID_KNOWN_AT")
        known = read_time if explicit is None else explicit
        if self._store.visible_cases(c, t, s, case_ids, known) != set(case_ids):
            raise case_not_found()
        links = self._store.work_contexts(c, t, s, case_ids, known)
        opportunity_ids = sorted({str(x["opportunity_id"]) for x in links if x["opportunity_id"] is not None})
        selected = {str(x["opportunity_id"]) for x in self._store.opportunity_selections(c, t, s, opportunity_ids,
                                                                                         known)
                    if _pins_visible(x["selected_hours"], known)}
        out: dict[str, list[dict[str, Any]]] = {cid: [] for cid in case_ids}
        for kind in ("OPPORTUNITY", "SCENARIO"):
            for x in links:
                if (x["opportunity_id"] is not None) != (kind == "OPPORTUNITY"):
                    continue
                if kind == "OPPORTUNITY":
                    oid = str(x["opportunity_id"])
                    ok = oid in selected
                    entry = {"kind": kind, "id": oid,
                             "label": opportunity_code(x["opportunity_no"]) if ok else UNAVAILABLE,
                             "url": f"/sites/{site_code}/opportunities/{oid}" if ok else None}
                else:
                    ok = x["scenario_name"] is not None
                    entry = {"kind": kind, "id": str(x["scenario_id"]),
                             "label": f"{scenario_code(x['scenario_no'])} · {x['scenario_name']}" if ok
                             else UNAVAILABLE, "url": None}
                out[x["case_id"]].append(entry)
        return {"schema_version": SCHEMA_CONTEXTS, "known_at": iso(known), "contexts": out}


__all__ = ["SCHEMA_CONTEXTS", "SCHEMA_WRITE", "WorkLinkService", "parse_case_ids"]
