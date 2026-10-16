"""S6-01a Site-scoped Action routes: `reserve-trial-1` recommendation, acceptance, demo observation, exact reads.

Under `/api/sites/{site_code}` (`D-2026-10-15-s601-action-store-and-ui`):

- `GET  /findings/{finding_id}/recommendation?revision_id=` - the proposal or typed unavailable reason served from
  persisted inputs; once accepted, the immutable accepted snapshot with its Action link beside a labelled live
  recomputation status. Exposes `system_demo_capability` for ACCEPT.
- `POST /findings/{finding_id}/recommendation/accept` - SYSTEM demonstration acceptance (201 new, 200 replay).
- `POST /actions/{action_id}/apply` - SYSTEM demonstration application: the Action lock, then the S1 publish under
  the Site lock, then the change artifact and APPLIED in one commit (201 new, 200 replay). An authorized same-Site
  domain or publish failure is typed (stale 409, invalid/no-change/backdate 422) and appends FAILED after rollback.
- `POST /actions/{action_id}/observations` - the state-neutral `DEMO_REVIEW_NOTE` OBSERVED event.
- `GET  /actions/{action_id}?event_id=|recorded_at=` and `GET /actions/{action_id}/events?...` - exact reads.
- `GET  /foundation/changes/{change_id}` - the applied change artifact with every Foundation/binding revision ID.

Refusal order for a command: access 401/403, unknown Site 404, store 503, unknown or wrong-Site Finding (accept)
or Action (apply/observe) 404, scoped capability for that fixture record 403, malformed body 422, unknown revision
or expected Foundation revision 404, then domain 409/422. A refused command writes nothing.
The development composition admits the caller exactly as the Finding read does; the authority to run a command is
the server's scoped SYSTEM demonstration grant, which a client cannot supply.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request

from assetops_backend.actions.lifecycle import OBSERVATION_CODE, SelectorConflict, selector
from assetops_backend.actions.ports import ActionRefused, ActionStoreUnavailable
from assetops_backend.actions.service import ActionService
from assetops_backend.actions.verification import VerificationService
from assetops_backend.finding_api import ACCESS_BASIS, Access, Gate, Scope, development_access, no_gate

ACCEPT_FIELDS = ("revision_id", "recommendation_key", "foundation_revision_id", "proposed_value", "idempotency_key")
OBSERVE_FIELDS = ("observation_code", "occurred_at", "idempotency_key")
APPLY_FIELDS = ("expected_foundation_revision_id", "value", "effective_from", "idempotency_key")
FREEZE_FIELDS = ("baseline_start", "later_start", "idempotency_key")
BIND_FIELDS = ("idempotency_key",)
EVALUATE_FIELDS = ("idempotency_key",)
AUTHORITY_WORDS = ("actor", "author", "principal", "capability", "authority", "approved", "user")


def _refuse(status: int, code: str, message: str, **extra: Any) -> HTTPException:
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return HTTPException(status_code=status, headers=headers, detail={"code": code, "message": message, **extra})


def _instant(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.strip().replace(" ", "+"))
    except ValueError:
        raise _refuse(422, "ACTION_SELECTOR_INVALID" if name == "recorded_at" else "COMMAND_INVALID",
                      f"{name} must be an ISO-8601 instant with a time zone offset.", fields=[name]) from None
    if parsed.tzinfo is None:
        raise _refuse(422, "ACTION_SELECTOR_INVALID" if name == "recorded_at" else "COMMAND_INVALID",
                      f"{name} must carry a time zone offset.", fields=[name])
    return parsed


def build_action_router(service: ActionService | None, scope: Scope, unavailable: tuple[type, ...] = (),
                        access: Access = development_access, command_access: Access = development_access,
                        gate: Gate = no_gate, access_basis: str = ACCESS_BASIS) -> APIRouter:
    router = APIRouter()
    down = (ActionStoreUnavailable, *unavailable)

    def open_scope(request: Request, site_code: str, check: Access) -> tuple[str, UUID, UUID]:
        refusal = check(request, site_code)
        if refusal == 401:
            raise _refuse(401, "UNAUTHENTICATED", "Sign in to use Actions.")
        if refusal == 403:
            raise _refuse(403, "SITE_SCOPE_FORBIDDEN", f"No access to Site {site_code!r}.")
        found = scope(site_code)
        if found is None:
            raise HTTPException(status_code=404, detail=f"No imported Site {site_code!r} in this tenant.")
        if service is None:
            raise _refuse(503, "ACTION_STORE_UNAVAILABLE", "No product database is configured.")
        return found

    def run(work: Callable[[], Any]) -> Any:
        try:
            return work()
        except ActionRefused as refused:
            raise _refuse(refused.status, refused.code, refused.message, **refused.extra) from refused
        except down as error:
            raise _refuse(503, "ACTION_STORE_UNAVAILABLE", str(error)) from error

    def source_open(code: str, tenant_id: UUID, site_id: UUID) -> bool:
        try:
            return bool(gate(code, tenant_id, site_id)[0])
        except down as error:
            raise _refuse(503, "ACTION_STORE_UNAVAILABLE", str(error)) from error

    async def body_of(request: Request, fields: tuple[str, ...],
                      optional: tuple[str, ...] = ()) -> dict[str, Any]:
        try:
            body = await request.json()
        except ValueError:
            raise _refuse(422, "BODY_NOT_JSON", "The command body must be a JSON object.") from None
        if not isinstance(body, dict):
            raise _refuse(422, "BODY_NOT_JSON", "The command body must be a JSON object.")
        claimed = sorted(k for k in body if any(w in k.lower() for w in AUTHORITY_WORDS))
        if claimed:
            raise _refuse(422, "CLIENT_AUTHORITY_FORBIDDEN", "A client cannot name an actor or grant authority; "
                          "the server records the SYSTEM demonstration actor.", fields=claimed)
        extra = sorted(set(body) - set(fields) - set(optional))
        missing = [f for f in fields if body.get(f) in (None, "")]
        if extra or missing:
            raise _refuse(422, "COMMAND_INVALID", "The command has unknown or missing fields.",
                          unknown=extra, missing=missing)
        key = body["idempotency_key"]
        if not isinstance(key, str) or not 8 <= len(key) <= 128:
            raise _refuse(422, "COMMAND_INVALID", "idempotency_key must be 8-128 characters.",
                          fields=["idempotency_key"])
        return body

    def uuid_field(body: dict[str, Any], name: str) -> UUID:
        try:
            return UUID(str(body[name]))
        except ValueError:
            raise _refuse(422, "COMMAND_INVALID", f"{name} must be a UUID.", fields=[name]) from None

    def chosen(event_id: str | None, recorded_at: str | None):
        try:
            event = None if event_id is None else UUID(event_id)
        except ValueError:
            raise _refuse(422, "ACTION_SELECTOR_INVALID", "event_id must be a UUID.", fields=["event_id"]) from None
        instant = None if recorded_at is None else _instant(recorded_at, "recorded_at")
        try:
            return selector(event, instant)
        except SelectorConflict as conflict:
            raise _refuse(422, "ACTION_SELECTOR_CONFLICT", str(conflict),
                          selectors={"event_id": event_id, "recorded_at": recorded_at}) from None

    @router.get("/api/sites/{site_code}/findings/{finding_id}/recommendation")
    def recommendation(request: Request, site_code: str, finding_id: UUID,
                       revision_id: UUID | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        opened = source_open(code, tenant_id, site_id)
        body = run(lambda: service.recommendation(tenant_id, site_id, code, finding_id, revision_id, opened))
        if body is None:
            raise HTTPException(status_code=404, detail="No such Finding or revision for this Site.")
        # S6-02a: each accepted Action's current verification state; the typed prior-trial block is
        # `prior_action_block` (PRIOR_ACTION_UNRESOLVED, PRIOR_TRIAL_GUARDRAIL_FAILED or PRIOR_TRIAL_REASSESSMENT_OVERLAP).
        body["verification"] = {a["action_id"]: run(lambda a=a: verification.summary(
            tenant_id, site_id, code, UUID(a["action_id"]))) for a in body.get("accepted") or []}
        return {"access_basis": access_basis, "source_open": opened, **body}

    @router.post("/api/sites/{site_code}/findings/{finding_id}/recommendation/accept")
    async def accept(request: Request, site_code: str, finding_id: UUID) -> Any:
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_accept(tenant_id, site_id, code, finding_id))
        raw = await body_of(request, ACCEPT_FIELDS)
        try:
            proposed = Decimal(str(raw["proposed_value"]))
            if not proposed.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            raise _refuse(422, "COMMAND_INVALID", "proposed_value must be a number.",
                          fields=["proposed_value"]) from None
        command = {"revision_id": uuid_field(raw, "revision_id"),
                   "foundation_revision_id": uuid_field(raw, "foundation_revision_id"),
                   "recommendation_key": str(raw["recommendation_key"]), "proposed_value": proposed,
                   "idempotency_key": raw["idempotency_key"]}
        opened = source_open(code, tenant_id, site_id)
        status, body = run(lambda: service.accept(tenant_id, site_id, code, finding_id, command, opened))
        return _respond(status, body)

    @router.post("/api/sites/{site_code}/actions/{action_id}/apply")
    async def apply(request: Request, site_code: str, action_id: UUID) -> Any:
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_action(tenant_id, site_id, code, "APPLY", action_id))
        raw = await body_of(request, APPLY_FIELDS)
        try:
            value = Decimal(str(raw["value"]))
            if not value.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            raise _refuse(422, "COMMAND_INVALID", "value must be a number.", fields=["value"]) from None
        command = {"expected_foundation_revision_id": uuid_field(raw, "expected_foundation_revision_id"),
                   "value": value, "effective_from": _instant(str(raw["effective_from"]), "effective_from"),
                   "idempotency_key": raw["idempotency_key"]}
        status, body = run(lambda: service.apply(tenant_id, site_id, code, action_id, command))
        return _respond(status, body)

    @router.get("/api/sites/{site_code}/foundation/changes/{change_id}")
    def change(request: Request, site_code: str, change_id: UUID) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        body = run(lambda: service.change(tenant_id, site_id, code, change_id))
        if body is None:
            raise HTTPException(status_code=404, detail="No such change for this Site.")
        action_id = UUID(body["change"]["action_id"])
        body["verification"] = run(lambda: verification.summary(tenant_id, site_id, code, action_id))
        return {"access_basis": access_basis, **body}

    @router.post("/api/sites/{site_code}/actions/{action_id}/observations")
    async def observe(request: Request, site_code: str, action_id: UUID) -> Any:
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_action(tenant_id, site_id, code, "OBSERVE", action_id))
        raw = await body_of(request, OBSERVE_FIELDS)
        if raw["observation_code"] != OBSERVATION_CODE:
            raise _refuse(422, "OBSERVATION_CODE_INVALID", f"Only {OBSERVATION_CODE} is accepted.",
                          fields=["observation_code"])
        command = {"occurred_at": _instant(str(raw["occurred_at"]), "occurred_at"),
                   "idempotency_key": raw["idempotency_key"]}
        status, body = run(lambda: service.observe(tenant_id, site_id, code, action_id, command))
        return _respond(status, body)

    @router.get("/api/sites/{site_code}/actions/{action_id}")
    def action(request: Request, site_code: str, action_id: UUID, event_id: str | None = None,
               recorded_at: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        pick = chosen(event_id, recorded_at)
        body = run(lambda: service.action(tenant_id, site_id, code, action_id, pick))
        if body is None:
            raise HTTPException(status_code=404, detail="No such Action for this Site.")
        # S6-02a: the current verification state beside (never instead of) the pinned S6-01 history.
        body["verification"] = run(lambda: verification.summary(tenant_id, site_id, code, action_id))
        return {"access_basis": access_basis, **body}

    @router.get("/api/sites/{site_code}/actions/{action_id}/events")
    def events(request: Request, site_code: str, action_id: UUID, event_id: str | None = None,
               recorded_at: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        pick = chosen(event_id, recorded_at)
        body = run(lambda: service.events(tenant_id, site_id, code, action_id, pick))
        if body is None:
            raise HTTPException(status_code=404, detail="No such Action for this Site.")
        return {"access_basis": access_basis, **body}

    # ---- S6-02a verification (D-2026-10-16-s6-verification) ---------------------------------------------------

    verification = VerificationService(service) if service is not None else None

    def plan_selector(plan_id: str | None, recorded_at: str | None) -> tuple[UUID | None, datetime | None]:
        try:
            chosen = None if plan_id is None else UUID(plan_id)
        except ValueError:
            raise _refuse(422, "VERIFICATION_SELECTOR_INVALID", "plan_id must be a UUID.", fields=["plan_id"]) from None
        return chosen, None if recorded_at is None else _instant(recorded_at, "recorded_at")

    @router.post("/api/sites/{site_code}/actions/{action_id}/verification/plans")
    async def freeze_plan(request: Request, site_code: str, action_id: UUID) -> Any:
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_action(tenant_id, site_id, code, "VERIFY", action_id))
        raw = await body_of(request, FREEZE_FIELDS, optional=("supersedes_plan_id",))
        command = {"baseline_start": _instant(str(raw["baseline_start"]), "baseline_start"),
                   "later_start": _instant(str(raw["later_start"]), "later_start"),
                   "supersedes_plan_id": None if raw.get("supersedes_plan_id") in (None, "")
                   else uuid_field(raw, "supersedes_plan_id"),
                   "idempotency_key": raw["idempotency_key"]}
        status, body = run(lambda: verification.freeze(tenant_id, site_id, code, action_id, command))
        return _respond(status, body)

    @router.post("/api/sites/{site_code}/actions/{action_id}/verification/plans/{plan_id}/later-selection")
    async def bind_later_selection(request: Request, site_code: str, action_id: UUID, plan_id: UUID) -> Any:
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_action(tenant_id, site_id, code, "VERIFY", action_id))
        raw = await body_of(request, BIND_FIELDS)
        status, body = run(lambda: verification.bind_later_selection(tenant_id, site_id, code, action_id, plan_id,
                                                                     raw))
        return _respond(status, body)

    @router.get("/api/sites/{site_code}/actions/{action_id}/verification/plan")
    def verification_plan(request: Request, site_code: str, action_id: UUID, plan_id: str | None = None,
                          recorded_at: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        chosen, cutoff = plan_selector(plan_id, recorded_at)
        return {"access_basis": access_basis,
                **run(lambda: verification.plan(tenant_id, site_id, code, action_id, chosen, cutoff))}

    @router.post("/api/sites/{site_code}/actions/{action_id}/verification/evaluations")
    async def request_evaluation(request: Request, site_code: str, action_id: UUID) -> Any:
        """SYSTEM demonstration evaluation request: the evaluator job computes and appends; the caller never
        supplies a verdict, metric or event (`CLIENT_AUTHORITY_FORBIDDEN` refuses such fields)."""
        code, tenant_id, site_id = open_scope(request, site_code, command_access)
        run(lambda: service.authorize_action(tenant_id, site_id, code, "VERIFY", action_id))
        raw = await body_of(request, EVALUATE_FIELDS, optional=("plan_id",))
        command = {"idempotency_key": raw["idempotency_key"],
                   "plan_id": None if raw.get("plan_id") in (None, "") else uuid_field(raw, "plan_id")}
        status, body = run(lambda: verification.evaluate(tenant_id, site_id, code, action_id, command))
        return _respond(status, body)

    @router.get("/api/sites/{site_code}/actions/{action_id}/verification/outcome")
    def verification_outcome(request: Request, site_code: str, action_id: UUID, outcome_id: str | None = None,
                             recorded_at: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        try:
            chosen = None if outcome_id is None else UUID(outcome_id)
        except ValueError:
            raise _refuse(422, "VERIFICATION_SELECTOR_INVALID", "outcome_id must be a UUID.",
                          fields=["outcome_id"]) from None
        cutoff = None if recorded_at is None else _instant(recorded_at, "recorded_at")
        return {"access_basis": access_basis,
                **run(lambda: verification.outcome(tenant_id, site_id, code, action_id, chosen, cutoff))}

    @router.get("/api/sites/{site_code}/actions/{action_id}/verification/history")
    def verification_history(request: Request, site_code: str, action_id: UUID) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        return {"access_basis": access_basis, **run(lambda: verification.history(tenant_id, site_id, code, action_id))}

    @router.get("/api/sites/{site_code}/actions/{action_id}/verification/evidence")
    def verification_evidence(request: Request, site_code: str, action_id: UUID, plan_id: str | None = None,
                              recorded_at: str | None = None) -> dict[str, Any]:
        code, tenant_id, site_id = open_scope(request, site_code, access)
        chosen, cutoff = plan_selector(plan_id, recorded_at)
        return {"access_basis": access_basis,
                **run(lambda: verification.evidence(tenant_id, site_id, code, action_id, chosen, cutoff))}

    return router


def _respond(status: int, body: dict[str, Any]) -> Any:
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=status, content=body)
