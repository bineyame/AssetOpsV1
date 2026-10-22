"""W4-03 unit 5: the opportunity list/detail reads and the authored opportunity-scenario association.

`.agent/W4-03-build-spec.md`: "API, exact wire, ordering and errors"; closure 1 Q1-Q3 (association command and
response), Q7-Q11 (status, currentness, provenance), Q12-Q16 (one REPEATABLE READ snapshot, head at cutoff, list
envelope, token, cursor, link bounds); closure 4 S5 (physical comparison by revision, not seq), S7, S9 (the W4-02
basis is read only through `MiniDepthRead.read_selected_renewable_basis`), S10, S14, S20; u4b (read-side ownership)
and "Unit-5..12 rulings (u5)" unit 5 rulings 1-7, which control.

Reads never rewrite the frozen `mini_opportunity_revision.result`: status is the stored claim; currentness and the
read-time limitations are computed at the cutoff and appended. All SQL lives in `store.py`.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
from datetime import date, datetime
from typing import Any, Callable, Mapping, Sequence
from uuid import UUID, uuid4

from assetops_backend.mini_decisions import projection
from assetops_backend.mini_decisions.model import DecisionPrincipal, DecisionRefused, invalid
from assetops_backend.mini_decisions.scenario_rules import decimal_text
from assetops_backend.mini_decisions.scenarios import SELECTION_VERSION, _instant, _shape, admit, authorize, \
    encode_cursor, parse_list
from assetops_backend.mini_decisions.store import (
    MiniDecisionStoreUnavailable,
    MiniDecisionWriteRefused,
    PostgresMiniDecisionStore,
)
from assetops_backend.mini_depth.inputs import MiniInputsRefused, zone
from assetops_backend.mini_depth.read import MiniDepthRead, MiniReadRefused, MiniReadUnavailable, aggregate_job, iso
from assetops_backend.work import model as work

SCHEMA_LIST = "mini-opportunities-1"
SCHEMA_DETAIL = "mini-opportunity-detail-1"
SCHEMA_COMMAND = "mini-opportunity-scenario-command-1"
SCHEMA_WRITE = "mini-opportunity-scenario-write-1"
ROUTE = "opportunities"
LINK_ROUTE = "opportunities/scenario-links"
#: u5 ruling 1: weakest first.
STATUS_ORDER = ("UNKNOWN", "LIMITED", "SUPPORTED")
#: u5 ruling 2: the list envelope's row-state aggregate.
LIST_STATE_ORDER = ("PENDING_RECOMPUTE", "STALE_SOURCE", "UNKNOWN", "HISTORICAL", "CURRENT")
LIVE = ("FAILED", "LEASED", "PENDING")
#: u5 ruling 3: read-time codes, appended in this order after the frozen ones.
READ_CODES = ("SELECTION_CHANGED", "RECOMPUTE_PENDING", "SOURCE_STALE", "SCENARIO_BASIS_MISMATCH")
GATE_STATES = ("CURRENT", "HISTORICAL")


def opportunity_code(public_no: int) -> str:
    """`OPP-` plus `public_no` zero-padded to at least six digits (u5 ruling 5)."""
    return f"OPP-{int(public_no):06d}"


def decode_cursor(value: str) -> dict[str, Any]:
    """The opportunity cursor: `after` is `[first_day, id]` as strings (u5 ruling 6)."""
    try:
        payload = json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)).decode("utf-8"))
        ok = (isinstance(payload, dict) and payload.get("v") == 1
              and all(isinstance(payload.get(k), str)
                      for k in ("tenant_id", "site_id", "route", "from", "to", "known_at", "selection_token"))
              and isinstance(payload.get("after"), list) and len(payload["after"]) == 2
              and all(isinstance(x, str) for x in payload["after"]))
        if ok:
            for key in ("from", "to", "known_at"):
                _instant(payload[key], "INVALID_CURSOR")
            ok = date.fromisoformat(payload["after"][0]).isoformat() == payload["after"][0]
            UUID(payload["after"][1])
    except (binascii.Error, ValueError, UnicodeDecodeError, TypeError, DecisionRefused):
        ok = False
    if not ok:
        raise DecisionRefused("INVALID_CURSOR")
    return payload


def parse_opportunity_list(start: str | None, end: str | None, limit: str | None, known: Sequence[str],
                           cursor: str | None) -> dict[str, Any]:
    """u5 ruling 6: both bounds are required (422 `INVALID_WINDOW`), then the scenario order: limit, `known_at`,
    cursor. The exact Site-local midnight check needs the Site zone and runs in the read."""
    if start in (None, "") or end in (None, ""):
        raise DecisionRefused("INVALID_WINDOW")
    parsed = parse_list(start, end, limit, known, None)
    parsed["cursor"] = None if cursor in (None, "") else decode_cursor(cursor)
    return parsed


def _local_day(at: datetime, tz_name: str | None) -> date:
    """The Site-local day that `at` starts; a bound that is not exactly a Site-local midnight is `INVALID_WINDOW`."""
    try:
        day = at.astimezone(zone(tz_name)).date()
        if projection.local_midnight(day, tz_name) != at:
            raise DecisionRefused("INVALID_WINDOW")
    except MiniInputsRefused:
        raise DecisionRefused("INVALID_WINDOW") from None
    return day


def _pins_visible(pins: Sequence[Mapping[str, Any]], known: datetime) -> bool:
    """Closure 1 Q12-Q16: every pinned W4-02 selection also satisfies the cutoff."""
    return all(p["selection_at"] is None or _instant(p["selection_at"], "DECISION_STORE_UNAVAILABLE") <= known
               for p in pins)


def _weakest(statuses: Sequence[str]) -> str:
    return next((x for x in STATUS_ORDER if x in set(statuses)), "UNKNOWN")


class OpportunityService:
    """`mini-opportunities-1` list, `mini-opportunity-detail-1` detail and the scenario association command."""

    def __init__(self, store: PostgresMiniDecisionStore, reader: MiniDepthRead, *,
                 test_read_clock_override: Callable[[], datetime] | None = None) -> None:
        self._store = store
        self._reader = reader
        self.test_read_clock_override = test_read_clock_override

    # --- command ------------------------------------------------------------------------------------------------

    def link_scenario(self, tenant_id: UUID, site_id: UUID, principal: DecisionPrincipal | None, opportunity_id: str,
                      body: Any) -> tuple[int, dict[str, Any]]:
        """Closure 1 Q1-Q3: admission (403) before the body; a non-UUID path root is 404; the closed shape (422, the
        body ID must equal the path ID); the actor; the canonical hash; then, under the root lock, a foreign path
        root 404, the idempotency lookup (exact retry 200 / changed body 409) and a foreign body scenario 422. The
        association is authored intent: it is stored even when the scenario head is incompatible."""
        principal = admit(principal, tenant_id, site_id)
        try:
            root_id = str(UUID(opportunity_id)).lower()
        except ValueError:
            raise DecisionRefused("DECISION_NOT_FOUND") from None
        b = _shape(work.closed, body, ("schema_version", "idempotency_key", "actor", "opportunity_id", "scenario_id"))
        if b["schema_version"] != SCHEMA_COMMAND:
            raise invalid()
        actor = _shape(work.actor_shape, b["actor"])
        cmd = {"schema_version": SCHEMA_COMMAND,
               "idempotency_key": _shape(work.idempotency_key, b["idempotency_key"]),
               "actor": {"kind": actor["kind"], "id": actor["id"], "attestation": actor["attestation"]},
               "opportunity_id": _shape(work.uuid_text, b["opportunity_id"]).lower(),
               "scenario_id": _shape(work.uuid_text, b["scenario_id"]).lower()}
        if cmd["opportunity_id"] != root_id:
            raise invalid()
        who = authorize(cmd["actor"], principal)
        sha = work.command_sha256({"site_id": str(site_id), "route": LINK_ROUTE, "root_id": root_id}, cmd)

        def write(c: Any) -> tuple[int, dict[str, Any]]:
            if self._store.lock_opportunity(c, tenant_id, site_id, root_id) is None:
                raise DecisionRefused("DECISION_NOT_FOUND")
            prior = self._store.opportunity_link_by_key(c, tenant_id, site_id, cmd["idempotency_key"])
            if prior is not None:
                if prior["payload_sha256"] != sha:
                    raise DecisionRefused("DECISION_DUPLICATE_KEY")
                return 200, self._write_body(prior)
            if not self._store.scenario_exists(c, tenant_id, site_id, cmd["scenario_id"]):
                raise DecisionRefused("DECISION_LINK_SCOPE_INVALID")
            self._store.insert_opportunity_scenario_link(c, {
                "id": uuid4(), "tenant_id": tenant_id, "site_id": site_id, "opportunity_id": root_id,
                "scenario_id": cmd["scenario_id"], **who, "idempotency_key": cmd["idempotency_key"],
                "payload_sha256": sha})
            return 201, self._write_body(self._store.opportunity_link_by_key(c, tenant_id, site_id,
                                                                             cmd["idempotency_key"]))

        try:
            return self._write(write)
        except MiniDecisionWriteRefused:
            return self._write(write, final=True)  # a concurrent identical-key association committed first: the lookup answers

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
        return {"schema_version": SCHEMA_WRITE, "id": str(link["id"]), "opportunity_id": str(link["opportunity_id"]),
                "scenario_id": str(link["scenario_id"]), "recorded_at": iso(link["created_at"])}

    # --- reads --------------------------------------------------------------------------------------------------

    def _snapshot(self, read: Callable[[Any, datetime], dict[str, Any]]) -> dict[str, Any]:
        try:
            with self._store.snapshot() as c:
                read_time = self._store.db_now(c)
                if self.test_read_clock_override is not None:
                    read_time = self.test_read_clock_override()
                return read(c, read_time)
        except (MiniDecisionStoreUnavailable, MiniReadUnavailable, MiniReadRefused,
                projection.ProjectionIntegrityError) as error:
            raise DecisionRefused("DECISION_STORE_UNAVAILABLE") from error

    def list(self, tenant_id: UUID, site_id: UUID, request: Mapping[str, Any], access_basis: str) -> dict[str, Any]:
        return self._snapshot(lambda c, now: self._list(c, tenant_id, site_id, request, access_basis, now))

    def detail(self, tenant_id: UUID, site_id: UUID, opportunity_id: str, known: Sequence[str]) -> dict[str, Any]:
        try:
            root_id = str(UUID(opportunity_id)).lower()
        except ValueError:
            raise DecisionRefused("DECISION_NOT_FOUND") from None
        if len(known) > 1:
            raise DecisionRefused("INVALID_KNOWN_AT")
        explicit = _instant(known[0], "INVALID_KNOWN_AT") if known else None
        return self._snapshot(lambda c, now: self._detail(c, tenant_id, site_id, root_id, explicit, now))

    def _list(self, c: Any, t: UUID, s: UUID, request: Mapping[str, Any], access_basis: str,
              read_time: datetime) -> dict[str, Any]:
        explicit = request["known_at"]
        if explicit is not None and explicit > read_time:
            raise DecisionRefused("INVALID_KNOWN_AT")
        cursor = request["cursor"]
        lo, hi = request["from"], request["to"]
        if cursor is not None:
            if (cursor["tenant_id"], cursor["site_id"], cursor["route"]) != (str(t), str(s), ROUTE):
                raise DecisionRefused("INVALID_CURSOR")
            if (iso(lo), iso(hi)) != (cursor["from"], cursor["to"]) or (
                    explicit is not None and iso(explicit) != cursor["known_at"]):
                raise DecisionRefused("DECISION_BASIS_CHANGED")
            known = _instant(cursor["known_at"], "INVALID_CURSOR")
            if known > read_time:
                raise DecisionRefused("DECISION_BASIS_CHANGED")
        else:
            known = read_time if explicit is None else explicit
        historical = explicit is not None and known < read_time
        tz_row = self._store.site_timezone(c, t, s)
        tz_name = tz_row[0] if tz_row else None
        lo_day, hi_day = _local_day(lo, tz_name), _local_day(hi, tz_name)

        roots = self._store.opportunity_roots(c, t, s, known=known, lo_day=lo_day, hi_day=hi_day)
        studies = self._studies(c, t, s, roots, known, historical, tz_name)
        token_rows = sorted((x["token"] for x in studies), key=lambda r: r["root_id"])
        pending_jobs = sorted({j for x in studies for j in x["pending_job_ids"]})
        token = "sha256:" + hashlib.sha256(work.canonical_json({
            "version": SELECTION_VERSION, "tenant_id": str(t), "site_id": str(s), "route": ROUTE, "from": iso(lo),
            "to": iso(hi), "known_at": iso(known), "access_basis": access_basis, "rows": token_rows,
            "pending_job_ids": pending_jobs}).encode("utf-8")).hexdigest()
        if cursor is not None and cursor["selection_token"] != token:
            raise DecisionRefused("DECISION_BASIS_CHANGED")

        ordered = sorted(studies, key=lambda x: x["id"])  # (first_day DESC, id ASC) by two stable sorts
        ordered.sort(key=lambda x: x["first_day"], reverse=True)
        if cursor is not None:
            after_day, after_id = cursor["after"]
            ordered = [x for x in ordered if x["first_day"] < after_day
                       or (x["first_day"] == after_day and x["id"] > after_id)]
        page = ordered[:request["limit"]]
        next_cursor = None
        if len(ordered) > len(page):
            last = page[-1]
            next_cursor = encode_cursor({"v": 1, "tenant_id": str(t), "site_id": str(s), "route": ROUTE,
                                         "from": iso(lo), "to": iso(hi), "known_at": iso(known),
                                         "selection_token": token, "after": [last["first_day"], last["id"]]})
        pending_ids = sorted({i for x in studies for i in (x["pending_evidence_ids"] or [])})
        blocks = self._reader.provenance_blocks(
            c, tenant_id=t, site_id=s, selected_revision_ids=[i for x in studies for i in x["selected_ids"]],
            selected_evidence_ids=[i for x in studies for i in x["selected_evidence"]],
            pending_evidence_ids=pending_ids or None)
        states = [x["row"]["currentness"]["state"] for x in studies]
        currentness = {"state": next((x for x in LIST_STATE_ORDER if x in set(states)), "UNKNOWN"),
                       "job_state": aggregate_job(x["row"]["currentness"]["job_state"] for x in studies)
                       if studies else "NONE"}
        return {"schema_version": SCHEMA_LIST,
                "window": {"from": iso(lo), "to": iso(hi), "known_at": iso(known)},
                "status": _weakest([x["row"]["status"] for x in studies]), "currentness": currentness, **blocks,
                "total_count": len(studies), "rows": [x["row"] for x in page], "next_cursor": next_cursor,
                "selection_token": token}

    def _detail(self, c: Any, t: UUID, s: UUID, root_id: str, explicit: datetime | None,
                read_time: datetime) -> dict[str, Any]:
        if explicit is not None and explicit > read_time:
            raise DecisionRefused("INVALID_KNOWN_AT")
        known = read_time if explicit is None else explicit
        historical = explicit is not None and known < read_time
        roots = self._store.opportunity_roots(c, t, s, known=known, opportunity_id=root_id)
        if not roots:
            raise DecisionRefused("DECISION_NOT_FOUND")
        tz_row = self._store.site_timezone(c, t, s)
        tz_name = tz_row[0] if tz_row else None
        [study] = self._studies(c, t, s, roots, known, historical, tz_name)
        window = study["window"]
        kinds = {k for _, k in self._store.opportunity_work_kinds(c, t, s, [root_id], known)}
        site_work = (f"/sites/{s}/work/incidents" if "INCIDENT" in kinds
                     else f"/sites/{s}/work/maintenance" if "MAINTENANCE_REQUEST" in kinds else None)
        return {"schema_version": SCHEMA_DETAIL, **study["row"], "history": study["history"],
                "scenario_links": study["scenario_links"],
                "links": {"renewable": f"/sites/{s}/performance/renewable?from={iso(window.start)}"
                                       f"&to={iso(window.end)}&known_at={iso(known)}",
                          "site_work": site_work, "scenario": None}}

    # --- one study at the cutoff --------------------------------------------------------------------------------

    def _studies(self, c: Any, t: UUID, s: UUID, roots: Sequence[Mapping[str, Any]], known: datetime,
                 historical: bool, tz_name: str | None) -> list[dict[str, Any]]:
        ids = [r["id"] for r in roots]
        selections = self._store.opportunity_selections(c, t, s, ids, known)
        links = self._store.opportunity_scenario_links(c, t, s, ids, known)
        return [self._study(c, t, s, root, [x for x in selections if x["opportunity_id"] == root["id"]],
                            [link for link in links if link["opportunity_id"] == root["id"]], known, historical,
                            tz_name) for root in roots]

    def _study(self, c: Any, t: UUID, s: UUID, root: Mapping[str, Any], selections: Sequence[Mapping[str, Any]],
               links: Sequence[Mapping[str, Any]], known: datetime, historical: bool,
               tz_name: str | None) -> dict[str, Any]:
        first, last = root["first_day"], root["last_day"]
        window = projection.study_window(first, last, tz_name)
        jobs = self._store.live_opportunity_jobs_at(c, t, s, window.start, window.end, known)
        job_statuses = [str(j[1]) for j in jobs]
        visible = [x for x in selections if _pins_visible(x["selected_hours"], known)]
        head = visible[0] if visible else None
        pins: list[Mapping[str, Any]] = list(head["selected_hours"]) if head else []
        codes: list[str] = []
        pending_jobs = [str(j[0]) for j in jobs]
        pending_evidence: list[str] | None = None
        if head is None:
            state = "PENDING_RECOMPUTE" if jobs else "UNKNOWN"
            job_state = aggregate_job(job_statuses) if jobs else "NONE"
        else:
            basis = self._reader.read_selected_renewable_basis(
                c, tenant_id=t, site_id=s, days=[date.fromisoformat(p["local_day"]) for p in pins], known=known,
                historical=historical)
            days = basis["days"]
            changed = any(p["mini_revision_id"] != b["mini_revision_id"]
                          or sorted(p["evidence_ids"]) != sorted(i.lower() for i in b["evidence_ids"])
                          for p, b in zip(pins, days))
            pending = bool(jobs) or any(b["state"] == "PENDING_RECOMPUTE"
                                        or (b["mini_revision_id"] is None and b["job_state"] in LIVE) for b in days)
            if pending:
                state = "PENDING_RECOMPUTE"
            elif changed or any(b["state"] == "STALE_SOURCE" for b in days):
                state = "STALE_SOURCE"
            elif any(p["mini_revision_id"] is None for p in pins):
                state = "UNKNOWN"
            else:
                state = "HISTORICAL" if historical else "CURRENT"
            job_state = aggregate_job([b["job_state"] for b in days] + job_statuses)
            pending_jobs += basis["pending_job_ids"]
            pending_evidence = basis["pending_evidence_ids"] or None
            if changed:
                codes.append("SELECTION_CHANGED")
        if state == "PENDING_RECOMPUTE":
            codes.append("RECOMPUTE_PENDING")
        if state == "STALE_SOURCE":
            codes.append("SOURCE_STALE")

        pin_ids = [p["mini_revision_id"] for p in pins if p["mini_revision_id"] is not None]
        pin_evidence = sorted({i for p in pins for i in p["evidence_ids"]})
        blocks = self._reader.provenance_blocks(c, tenant_id=t, site_id=s, selected_revision_ids=pin_ids,
                                                selected_evidence_ids=pin_evidence,
                                                pending_evidence_ids=pending_evidence)

        # u5 ruling 4: the greatest visible association is selected; only a compatible one supplies the scenario.
        compatible = [self._compatible(c, t, s, link["scenario_id"], pins, known) for link in links]
        scenario_id = proposed = gross = None
        if links and compatible[0]:
            scenario_id = str(links[0]["scenario_id"])
            sc = self._store.scenario_head_at(c, t, s, links[0]["scenario_id"], known)
            proposed = next((decimal_text(work.decimal_value(a["value"])) for a in sc["assumptions"]
                             if a["key"] == "proposed_kw"), None)
            calc = sc["calculation"]
            selected = blocks["selected_source_provenance"] or {}
            # Closure 1 Q7-Q11: the read gate withholds money on a pending/stale/unknown basis or a MIXED/UNKNOWN
            # selected class, as the scenario row gate does; the stored arithmetic is never changed.
            if (calc.get("state") == "GROSS_SCENARIO" and calc.get("gross_sales") and state in GATE_STATES
                    and selected.get("classification") not in (None, "MIXED", "UNKNOWN")):
                gross = {"amount": decimal_text(work.decimal_value(calc["gross_sales"]["amount"])),
                         "currency": calc["gross_sales"]["currency"], "basis": "SCENARIO"}
        elif links:
            codes.append("SCENARIO_BASIS_MISMATCH")

        result = head["result"] if head else None
        stored = list(result["limitations"]) if result else []
        seen = {x["code"] for x in stored}
        limitations = stored + [{"code": code, "evidence_ids": []} for code in READ_CODES
                                if code in codes and code not in seen]
        obj = {"id": str(root["id"]), "code": opportunity_code(root["public_no"]),
               "revision_id": str(head["revision_id"]) if head else None,
               "revision_no": head["revision_no"] if head else None,
               "first_day": first.isoformat(), "last_day": last.isoformat(), "model_version": root["model_version"],
               "study_days": projection.STUDY_DAYS,
               "eligible_days": result["eligible_days"] if result else None,
               "assessed_days": result["assessed_days"] if result else None,
               "headroom_kw": result["headroom_kw"] if result else None,
               "proposed_load_kw": proposed, "gross_sales_scenario": gross, "demand_state": "UNVERIFIED",
               "collection_state": "UNVERIFIED", "scenario_id": scenario_id,
               "day_rows": [{**r, "selection_seq": p["selection_seq"], "mini_revision_id": p["mini_revision_id"]}
                            for r, p in zip(result["day_rows"], pins)] if result else []}
        windows = [{"local_day": p["local_day"], "selection_seq": p["selection_seq"],
                    "mini_revision_id": p["mini_revision_id"]} for p in pins]
        row = {"opportunity": obj, "status": result["status"] if result else "UNKNOWN",
               "currentness": {"state": state, "job_state": job_state,
                               "selection_seq": head["seq"] if head else None,
                               "selected_at": iso(head["selected_at"]) if head else None, "windows": windows},
               **blocks, "limitations": limitations}
        return {
            "id": str(root["id"]), "first_day": first.isoformat(), "window": window, "row": row,
            "selected_ids": pin_ids, "selected_evidence": pin_evidence, "pending_evidence_ids": pending_evidence,
            "pending_job_ids": sorted(set(pending_jobs)),
            "token": {"root_id": str(root["id"]), "selected_revision_id": str(head["revision_id"]) if head else None,
                      "selected_selection_seq": head["seq"] if head else None,
                      "linked_ids": sorted({str(link["scenario_id"]) for link in links}),
                      "pins": [[p["local_day"], p["selection_seq"], p["mini_revision_id"]] for p in pins]},
            "history": [{"revision_id": str(x["revision_id"]), "revision_no": x["revision_no"],
                         "input_sha256": x["input_sha256"], "created_at": iso(x["created_at"]),
                         "selection_seq": x["seq"], "selected_at": iso(x["selected_at"]),
                         "job_id": None if x["job_id"] is None else str(x["job_id"]),
                         "status": x["result"]["status"], "current": i == 0} for i, x in enumerate(visible)],
            "scenario_links": [{"id": str(link["id"]), "scenario_id": str(link["scenario_id"]),
                                "created_at": iso(link["created_at"]), "selected": i == 0, "compatible": ok}
                               for i, (link, ok) in enumerate(zip(links, compatible))]}

    def _compatible(self, c: Any, t: UUID, s: UUID, scenario_id: Any, pins: Sequence[Mapping[str, Any]],
                    known: datetime) -> bool:
        """Closure 1 Q1-Q3 with closure 4 S5: the scenario head at the cutoff is PRODUCTIVE_LOAD and pins exactly
        the selected opportunity's five `(local_day, mini_revision_id)` (a harmless new seq stays compatible)."""
        if len(pins) != projection.STUDY_DAYS or any(p["mini_revision_id"] is None for p in pins):
            return False
        sc = self._store.scenario_head_at(c, t, s, scenario_id, known)
        if sc is None or sc["kind"] != "PRODUCTIVE_LOAD":
            return False
        theirs = sorted((p["local_day"], str(p["mini_revision_id"]).lower()) for p in sc["pinned_selection_hours"])
        return theirs == sorted((p["local_day"], p["mini_revision_id"]) for p in pins)


def unsupported_detail() -> dict[str, Any]:
    """S10 for an authorized non-MINIGRID Site's opportunity detail: 200 UNKNOWN, no store consulted."""
    return {"schema_version": SCHEMA_DETAIL, "opportunity": None, "status": "UNKNOWN",
            "currentness": {"state": "UNKNOWN", "job_state": "NONE", "selection_seq": None, "selected_at": None,
                            "windows": []},
            "source_provenance": {"classification": "UNKNOWN", "state": "UNKNOWN", "source_ids": [],
                                  "evidence_ids": [], "basis_sha256": None,
                                  "reasons": [{"code": "EMPTY_CITATION_SET", "accepted_evidence_ids": []}]},
            "selected_source_provenance": None, "pending_source_provenance": None,
            "limitations": [{"code": "SITE_ROLE_UNSUPPORTED", "evidence_ids": []}], "history": [],
            "scenario_links": [], "links": {"renewable": None, "site_work": None, "scenario": None}}


__all__ = ["LINK_ROUTE", "OpportunityService", "ROUTE", "SCHEMA_COMMAND", "SCHEMA_DETAIL", "SCHEMA_LIST",
           "SCHEMA_WRITE", "decode_cursor", "opportunity_code", "parse_opportunity_list", "unsupported_detail"]
