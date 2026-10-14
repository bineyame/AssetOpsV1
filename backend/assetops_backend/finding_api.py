"""Site-scoped exact Finding read (S4-01 phase 2) at the `A-claim-work-routes` API routes.

`D-2026-10-09-pre-s3-claim-routes-and-actor`: the Site code resolves inside the configured tenant; an
unauthenticated caller is 401 and an authenticated caller without the known Site scope is 403 (the `access`
seam decides both); a foreign or unknown Site, Finding or revision is 404; an unavailable store is a typed
503, never an empty claim. No human sign-in exists yet: the default composition admits the development
tenant's operator context exactly as the S3 Performance read does, and says so in every body.

Q19 (`D-2026-10-12-s4-finding-phase-2-read-boundaries`): the S3 Performance cutover gate (comparison,
lineage breaks, other-model heads) guards both routes. While it is closed a default/current read is a typed
409 `PERFORMANCE_CUTOVER_CLOSED`, never a positive Finding or `NO_FINDING`; a pinned `revision_id` is served
as non-current audit material (`SOURCE_CLOSED`), and S3 drill-down links are withheld with the reason.
An unconfigured gate is closed.

S4-03 phase 1 (`I-finding-evidence-read`, `I-finding-history-read`) adds two child reads of the same root,
`.../findings/{finding_id}/evidence?revision_id=&offset=&limit=` and
`.../history?revision_id=&after_revision_no=&limit=`,
with the same scope, gate and refusal semantics; a broken lineage join is a named 200 state, a store failure 503.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder

from assetops_backend.analytics.assessment_ports import AssessmentStoreUnavailable
from assetops_backend.analytics.finding_read import FindingReadService
from assetops_backend.analytics.ports import AssessmentStoreUnavailable as FileAssessmentStoreUnavailable
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.financials.demonstration import demonstration_case

Scope = Callable[[str], "tuple[str, UUID, UUID] | None"]
# (request, site_code) -> None to admit, else 401 or 403.
Access = Callable[[Request, str], "int | None"]
ACCESS_BASIS = ("DEVELOPMENT_TENANT_OPERATOR_CONTEXT: no authenticated human principal exists yet; the read is "
                "admitted for the configured development tenant, as the S3 Performance read is")


Gate = Callable[[str, UUID, UUID], "tuple[bool, str]"]
CLOSED_LINKS = "S3 Performance drill-down routes answer 409 PERFORMANCE_CUTOVER_CLOSED while the gate is closed"


def development_access(request: Request, site_code: str) -> int | None:
    return None


def no_gate(site_code: str, tenant_id: UUID, site_id: UUID) -> tuple[bool, str]:
    return False, "No Performance cutover gate is configured for the Finding read."


def build_finding_router(reads: FindingReadService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                         access: Access = development_access, access_basis: str = ACCESS_BASIS,
                         gate: Gate = no_gate, consequences: Any = None,
                         consequence_unavailable: tuple[type, ...] = ()) -> APIRouter:
    router = APIRouter()
    down = (AssessmentStoreUnavailable, FileAssessmentStoreUnavailable, EvidenceStoreUnavailable, *unavailable)
    consequence_down = (*down, *consequence_unavailable)

    def open_scope(request: Request, site_code: str) -> tuple[str, UUID, UUID]:
        refusal = access(request, site_code)
        if refusal == 401:
            raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Bearer"},
                                detail={"code": "UNAUTHENTICATED", "message": "Sign in to read Findings."})
        if refusal == 403:
            raise HTTPException(status_code=403, detail={"code": "SITE_SCOPE_FORBIDDEN",
                                                         "message": f"No access to Site {site_code!r}."})
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if reads is None:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": "No product database is configured."})
        return found

    def source_gate(code: str, tenant_id: UUID, site_id: UUID) -> dict[str, Any]:
        try:
            permitted, reason = gate(code, tenant_id, site_id)
        except down as error:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        return {"permitted": permitted, "reason": reason}

    def closed(source: dict[str, Any]) -> HTTPException:
        return HTTPException(status_code=409, detail={
            "code": "PERFORMANCE_CUTOVER_CLOSED", "read": "CLOSED", "message": source["reason"],
            "note": "The Finding's authority is the selected S3 assessment, which is closed for this Site; no "
                    "current Finding or no-Finding verdict is shown. An exact revision_id reads audit material."})

    def served(work: Callable[[], Any], missing: str) -> Any:
        try:
            body = work()
        except down as error:
            raise HTTPException(status_code=503, detail={"code": "FINDING_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error
        if body is None:
            raise HTTPException(status_code=404, detail=missing)
        return jsonable_encoder(body)

    @router.get("/api/sites/{site_code}/finding-windows/{day}")
    def window_state(request: Request, site_code: str, day: date) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"]:
            raise closed(source)
        return {"site_code": code, "access_basis": access_basis, "source_gate": source,
                **served(lambda: reads.window_state(tenant_id, site_id, day), "No such window.")}

    @router.get("/api/sites/{site_code}/findings/{finding_id}")
    def finding(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                after_revision_no: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.finding(tenant_id, site_id, finding_id, revision_id,
                                            after_revision_no=after_revision_no, limit=limit,
                                            source_open=source["permitted"]),
                      "No such Finding or revision for this Site.")
        performance = {"status": "OPEN" if source["permitted"] else "CLOSED", "reason": source["reason"]}
        if not source["permitted"]:
            performance["note"] = CLOSED_LINKS
        selected = body["selection"]["revision_id"]
        base = f"/sites/{code}/findings/{finding_id}"
        audit = None if source["permitted"] else {
            "non_current": True, "reason": source["reason"],
            "statement": "Audit material only: the selected S3 source is closed, so this recorded revision is not "
                         "a current claim and its currentness is not read."}
        return {"site_code": code, "access_basis": access_basis, "source_gate": source, "audit_only": audit,
                **body, "links": {
            "canonical": base, "selected_revision": f"{base}?revision_id={selected}",
            "api_selected_revision": f"/api{base}?revision_id={selected}",
            "canonical_finding": f"/sites/{code}/findings/{body['relations']['canonical_finding_id']}",
            "performance": performance,
            "assessment_revisions": {} if not source["permitted"] else {
                str(a["assessment_revision_id"]):
                f"/api/sites/{code}/performance/dispatch/revisions/{a['assessment_revision_id']}"
                for a in body["revision"]["assessments"]},
            "windows": {} if not source["permitted"] else {
                w["day"]: f"/api/sites/{code}/performance/dispatch/windows/{w['day']}"
                for w in body["revision"]["currentness"]["windows"]}}}

    # ---- S4-03 phase 1: Evidence and History child reads of the same Finding root ----
    # Same scope, gate and refusal semantics as the root read: an omitted revision is the latest at read time
    # and is 409 while the Performance cutover is closed; a pinned revision is audit material then.

    def child_links(code: str, finding_id: UUID, selected: Any, permitted: bool) -> dict[str, Any]:
        base = f"/sites/{code}/findings/{finding_id}"
        pin = f"?revision_id={selected}"
        return {"canonical": base, "selected_revision": f"{base}{pin}",
                "evidence": f"{base}/evidence{pin}", "history": f"{base}/history{pin}",
                "api_finding": f"/api{base}{pin}", "api_evidence": f"/api{base}/evidence{pin}",
                "api_history": f"/api{base}/history{pin}",
                "performance": {"status": "OPEN" if permitted else "CLOSED",
                                **({} if permitted else {"note": CLOSED_LINKS})}}

    def audit_only(source: dict[str, Any]) -> dict[str, Any] | None:
        return None if source["permitted"] else {
            "non_current": True, "reason": source["reason"],
            "statement": "Audit material only: the selected S3 source is closed, so this recorded revision is not "
                         "a current claim and no live S3 drill-down is offered."}

    @router.get("/api/sites/{site_code}/findings/{finding_id}/evidence")
    def finding_evidence(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                         offset: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.evidence(tenant_id, site_id, finding_id, revision_id, offset=offset,
                                             limit=limit, source_open=source["permitted"]),
                      "No such Finding or revision for this Site.")
        links = child_links(code, finding_id, body["selection"]["revision_id"], source["permitted"])
        # Exact accepted evidence ID, never the message ID (a message ID can be 409 RECORD_AMBIGUOUS).
        links["records"] = {r["evidence_id"]: f"/api/sites/{code}/evidence/records/{r['evidence_id']}"
                            for r in body["records"] if r["resolved"]}
        links["assessment_revisions"] = {} if not source["permitted"] else {
            a["assessment_revision_id"]:
            f"/api/sites/{code}/performance/dispatch/revisions/{a['assessment_revision_id']}"
            for a in body["assessments"]}
        if body["page"]["next_offset"] is not None:
            links["api_next_page"] = (f"{links['api_evidence']}&offset={body['page']['next_offset']}"
                                      f"&limit={body['page']['limit']}")
        return {"site_code": code, "access_basis": access_basis, "source_gate": source,
                "audit_only": audit_only(source), **body, "links": links}

    @router.get("/api/sites/{site_code}/findings/{finding_id}/history")
    def finding_history(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                        after_revision_no: int = Query(0, ge=0), limit: int = Query(200, ge=1, le=500)
                        ) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.history(tenant_id, site_id, finding_id, revision_id,
                                            after_revision_no=after_revision_no, limit=limit),
                      "No such Finding or revision for this Site.")
        links = child_links(code, finding_id, body["selection"]["revision_id"], source["permitted"])
        base = f"/sites/{code}/findings/{finding_id}"
        links["revisions"] = {r["id"]: {"finding": f"{base}?revision_id={r['id']}",
                                        "evidence": f"{base}/evidence?revision_id={r['id']}",
                                        "api_evidence": f"/api{base}/evidence?revision_id={r['id']}"}
                              for r in body["revisions"]}
        if body["page"]["next_after_revision_no"] is not None:
            links["api_next_page"] = (f"{links['api_history']}&after_revision_no="
                                      f"{body['page']['next_after_revision_no']}&limit={body['page']['limit']}")
        return {"site_code": code, "access_basis": access_basis, "source_gate": source,
                "audit_only": audit_only(source), **body, "links": links}

    # ---- S4-02b phase 2a: the stored `fuel-cost-1` consequence of the same exact Finding revision ----

    def consequence_unavailable() -> HTTPException:
        return HTTPException(status_code=503, detail={"code": "CONSEQUENCE_STORE_UNAVAILABLE",
                                                      "message": "No consequence store is configured."})

    def consequence_call(work: Callable[[], Any]) -> Any:
        if consequences is None:
            raise consequence_unavailable()
        try:
            return work()
        except consequence_down as error:
            raise HTTPException(status_code=503, detail={"code": "CONSEQUENCE_STORE_UNAVAILABLE",
                                                         "message": str(error)}) from error

    def consequence_links(code: str, finding_id: UUID, selected: Any, permitted: bool,
                          result: dict[str, Any]) -> dict[str, Any]:
        links = child_links(code, finding_id, selected, permitted)
        base = f"/api/sites/{code}/findings/{finding_id}/financial-consequences?revision_id={selected}"
        links["financials"] = f"/sites/{code}/financials?finding_id={finding_id}&revision_id={selected}"
        links["api_consequences"] = base
        rows = [r for r in [result["consequence"], *result["history"]["revisions"]] if r is not None]
        links["consequence_revisions"] = {r["id"]: f"{base}&consequence_revision_id={r['id']}" for r in rows}
        links["evidence_records"] = {e: f"/api/sites/{code}/evidence/records/{e}"
                                     for r in rows for e in r["lineage"]["evidence_ids"]}
        links["price_revisions"] = {r["price"]["revision_id"]:
                                    f"/api/sites/{code}/financial-assumptions/{r['price']['revision_id']}"
                                    for r in rows if r["price"]["revision_id"]}
        nxt = result["history"]["page"]["next_after_revision_no"]
        if nxt is not None:
            links["api_next_page"] = f"{base}&after_revision_no={nxt}&limit={result['history']['page']['limit']}"
        return links

    @router.get("/api/sites/{site_code}/findings/{finding_id}/financial-consequences")
    def finding_consequences(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None,
                             consequence_revision_id: UUID | None = None, after_revision_no: int = Query(0, ge=0),
                             limit: int = Query(50, ge=1, le=200)) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if consequence_revision_id is not None and revision_id is None:
            revision_id = consequence_call(lambda: consequences.locate(tenant_id, site_id, finding_id,
                                                                       consequence_revision_id))
            if revision_id is None:
                raise HTTPException(status_code=404, detail="No such consequence revision for this Finding.")
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.finding(tenant_id, site_id, finding_id, revision_id, limit=1,
                                            source_open=source["permitted"]),
                      "No such Finding or revision for this Site.")
        selection = body["selection"]
        result = consequence_call(lambda: consequences.read(
            tenant_id, site_id, finding_id, UUID(str(selection["revision_id"])),
            finding_revision_is_latest=bool(selection.get("is_latest")), source_open=bool(source["permitted"]),
            consequence_revision_id=consequence_revision_id, after_revision_no=after_revision_no, limit=limit))
        if result is None:
            raise HTTPException(status_code=404, detail="No such consequence revision for this FindingRevision.")
        return jsonable_encoder({
            "site_code": code, "access_basis": access_basis, "source_gate": source, "audit_only": audit_only(source),
            "finding": body["finding"], "selection": selection,
            "revision": {"id": selection["revision_id"], "revision_no": selection["revision_no"],
                         "lifecycle": body["revision"]["lifecycle"]},
            "window": body["revision"]["episode"], **result,
            "demonstration": demonstration_case(code, body["revision"]["episode"]["start"],
                                                body["revision"]["episode"]["end"]),
            "links": consequence_links(code, finding_id, selection["revision_id"], source["permitted"], result)})

    # ---- S4-02a phase 2 bridge, S4-02b phase 2a consequence ----
    # It holds the Finding ID and exact FindingRevision ID and summarises the stored consequence of that
    # revision (`bridge_consequence`): a positive amount only when the head is CURRENT and PRICED, otherwise a
    # typed state with no amount. No consequence revision is manufactured and no mock number is inferred.

    @router.get("/api/sites/{site_code}/findings/{finding_id}/financials")
    def finding_financials(request: Request, site_code: str, finding_id: UUID, revision_id: UUID | None = None
                           ) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code)
        source = source_gate(code, tenant_id, site_id)
        if not source["permitted"] and revision_id is None:
            raise closed(source)
        body = served(lambda: reads.finding(tenant_id, site_id, finding_id, revision_id, limit=1,
                                            source_open=source["permitted"]),
                      "No such Finding or revision for this Site.")
        selected = body["selection"]["revision_id"]
        episode = body["revision"]["episode"]
        links = child_links(code, finding_id, selected, source["permitted"])
        links["financials"] = f"/sites/{code}/financials?finding_id={finding_id}&revision_id={selected}"
        links["assumptions"] = f"/sites/{code}/financials/assumptions"
        return jsonable_encoder({
            "site_code": code, "access_basis": access_basis, "source_gate": source, "audit_only": audit_only(source),
            "finding": body["finding"], "selection": body["selection"],
            "revision": {"id": selected, "revision_no": body["selection"]["revision_no"],
                         "title": body["revision"]["title"], "lifecycle": body["revision"]["lifecycle"],
                         "claim_level": body["revision"]["claim_level"]},
            "window": episode,
            "demonstration": demonstration_case(code, episode["start"], episode["end"]),
            "consequence": bridge(tenant_id, site_id, finding_id, body["selection"], bool(source["permitted"])),
            "links": links})

    def bridge(tenant_id: UUID, site_id: UUID, finding_id: UUID, selection: dict[str, Any],
               source_open: bool) -> dict[str, Any]:
        if consequences is None:
            return bridge_consequence(None)
        try:
            result = consequences.read(tenant_id, site_id, finding_id, UUID(str(selection["revision_id"])),
                                       finding_revision_is_latest=bool(selection.get("is_latest")),
                                       source_open=source_open, limit=1)
        except consequence_down:
            return bridge_consequence(None)
        return bridge_consequence(result)

    return router


QUANTITY_SOURCE = "fuel-cost-1"

REASONS = {
    "UNAVAILABLE": "The fuel-cost record could not be read just now, so no cost is shown.",
    "PENDING": "The fuel cost for this finding has not been calculated yet, so no cost is shown.",
    # Review L4: STALE is worded from the read's pending work; nothing is claimed to be queued unless it is.
    "STALE": "The price or inputs changed since the fuel cost was calculated, and it has not been recalculated "
             "yet, so no current cost is shown.",
    "STALE_QUEUED": "The price or inputs changed since the fuel cost was calculated; a recalculation is waiting "
                    "to run, so no current cost is shown.",
    "AUDIT_ONLY": "The finding's source is not open for current use, so its fuel cost is shown for the record "
                  "only and no current cost is shown.",
    "HISTORICAL": "This is an earlier version of the finding; its fuel cost is kept for the record only.",
    "QUANTITY_UNAVAILABLE": "The fuel quantity could not be bounded from the accepted generator data, so no "
                            "diesel price is applied and no cost is shown.",
    "UNPRICED": "No single Site diesel price covers this finding's whole window, so no cost is shown.",
    "MINOR_UNIT_UNKNOWN": "No rounding rule is known for this price currency, so no cost is shown.",
    "PRICED": "Modelled potential fuel-cost exposure under the reviewed fuel-cost-1 assumptions. This is not "
              "measured fuel saved or a physical maximum.",
}


def bridge_consequence(result: dict[str, Any] | None) -> dict[str, Any]:
    """The bridge's typed summary of one FindingRevision's stored consequence. Never zero, never a mock number:
    an amount appears only for a CURRENT PRICED head, rounded outward for display."""
    empty = {"quantity_source": QUANTITY_SOURCE, "quantity": None, "amount": None, "currency": None,
             "price_revision_id": None, "consequence_revision_id": None, "quantity_reason": None,
             "price_reason": None, "recalculation_queued": False, "currentness_reasons": []}
    if result is None:
        return {**empty, "state": "UNAVAILABLE", "currentness": None, "reason": REASONS["UNAVAILABLE"]}
    currentness = result["currentness"]
    row = result["consequence"]
    if row is None or currentness["state"] != "CURRENT":
        state = currentness["state"]
        queued = bool(currentness["pending_work"])
        key = "STALE_QUEUED" if state == "STALE" and queued else state
        return {**empty, "state": state, "currentness": state, "recalculation_queued": queued,
                "consequence_revision_id": None if row is None else row["id"],
                "currentness_reasons": list(currentness["reasons"]), "reason": REASONS[key]}
    priced = row["state"] == "PRICED" and row["display"] and row["display"]["state"] == "ROUNDED_OUTWARD"
    return {**empty, "state": row["state"], "currentness": "CURRENT", "consequence_revision_id": row["id"],
            "quantity": None if row["quantity"]["high"] is None else {
                "low": row["quantity"]["low"], "high": row["quantity"]["high"], "unit": row["quantity"]["unit"]},
            "quantity_reason": row["quantity"]["reason"], "price_reason": row["price"]["reason"],
            "price_revision_id": row["price"]["revision_id"],
            "amount": {"low": row["display"]["amount_low"], "high": row["display"]["amount_high"]} if priced else None,
            "currency": row["amount"]["currency"] if priced else None,
            "reason": REASONS[row["state"]] if row["state"] != "PRICED" or priced else REASONS["MINOR_UNIT_UNKNOWN"]}
