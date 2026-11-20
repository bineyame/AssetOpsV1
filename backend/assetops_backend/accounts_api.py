"""3C0a (spec §5; R9, R12-R14, P5, P6, P9, MB2): sign-in, sign-out, the signed-in person and Organisation's people
and role grants.

- `POST /api/auth/sign-in`, `POST /api/auth/sign-out`, `GET /api/auth/me`, `GET /api/organisation/people`,
  `GET /api/organisation/role-grants`, `POST /api/organisation/role-grants`,
  `POST /api/organisation/role-grants/{grant_id}/removal`.
- Order of refusals: 503 `ACCOUNTS_UNAVAILABLE` (no service, or the store is down: `unavailable`), 415 `JSON_REQUIRED` (every POST),
  422 `ACCOUNTS_BAD_REQUEST` (a body over 4 KiB, not JSON or not an object: `field = "body"`; else the first unknown
  key in sorted order, then the first missing or wrongly typed key in the route's order), 401 `NOT_SIGNED_IN`
  (routes needing a session; sign-out never answers 401), then the service's order. Unknown keys are refused, so a
  body naming an actor is refused: the browser never names one.
- Every response carries `Cache-Control: no-store`. Every refusal is `{"code", "message", "words"}`.
- The session cookie is `assetops_session`, HttpOnly, SameSite=Strict, Path=/api, 12 hours, and Secure unless
  `ASSETOPS_SESSION_COOKIE_SECURE=off`. Cross-site requests are refused by SameSite=Strict, the required JSON content
  type and the absence of any CORS middleware (R12c); a later slice adding CORS with credentials must say so.
"""
from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from assetops_backend.accounts.model import COOKIE, ROLES, SESSION_HOURS, AccountRefused, GrantRow, PersonPrincipal
from assetops_backend.accounts.principal import person_from_request
from assetops_backend.accounts.service import AccountService
from assetops_backend.i18n import message, render

MAX_BODY = 4 * 1024
NO_STORE = {"Cache-Control": "no-store"}


class _Answer(Exception):
    def __init__(self, response: Response) -> None:
        self.response = response


def _refusal(status: int, code: str, **params: Any) -> JSONResponse:
    words = message(f"accounts.{code.lower()}", **params)
    return JSONResponse(status_code=status, content={"code": code, "message": render(words), "words": words},
                        headers=NO_STORE)


async def _body_within(request: Request, limit: int) -> bytes | None:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > limit:
        return None
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            return None
        chunks.append(chunk)
    return b"".join(chunks)


async def _json(request: Request, listed: tuple[str, ...], optional: frozenset[str] = frozenset()) -> dict:
    """415 unless JSON; 422 naming the field (P6) unless an object with exactly the listed string keys."""
    media = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    if media != "application/json":
        raise _Answer(_refusal(415, "JSON_REQUIRED"))
    data = await _body_within(request, MAX_BODY)
    try:
        parsed = None if data is None else json.loads(data)
    except (ValueError, UnicodeDecodeError):
        parsed = None
    if not isinstance(parsed, dict):
        raise _Answer(_refusal(422, "ACCOUNTS_BAD_REQUEST", field="body"))
    unknown = sorted(key for key in parsed if key not in listed)
    if unknown:
        raise _Answer(_refusal(422, "ACCOUNTS_BAD_REQUEST", field=unknown[0]))
    for key in listed:
        if key in optional and parsed.get(key) is None:
            continue
        if not isinstance(parsed.get(key), str):
            raise _Answer(_refusal(422, "ACCOUNTS_BAD_REQUEST", field=key))
    return parsed


def _iso(value) -> str:
    return value.isoformat()


def _record(row: GrantRow) -> dict:
    by = ({"service": row.by_service} if row.by_service is not None
          else {"person_id": str(row.by_person_id), "display_name": row.by_display_name})
    return {"row_id": str(row.row_id), "grant_id": str(row.grant_id), "person_id": str(row.person_id),
            "display_name": row.display_name, "role": row.role, "site_code": row.site_code, "action": row.action,
            "by": by, "at": _iso(row.at)}


def _person(view) -> dict:
    roles = sorted(view.grants, key=lambda g: (ROLES.index(g.role), g.site_code or ""))
    return {"person_id": str(view.person_id), "display_name": view.display_name, "email": view.email,
            "status": view.status,
            "roles": [{"grant_id": str(g.grant_id), "role": g.role, "site_code": g.site_code} for g in roles]}


def build_accounts_router(accounts: AccountService | None, *, cookie_secure: bool,
                          unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    """`unavailable`: the store errors answered 503 `ACCOUNTS_UNAVAILABLE` (R14; `create_app` passes the
    composition's `ACCOUNTS_UNAVAILABLE`, as reading-upload's tuple)."""
    router = APIRouter()

    async def _call(work: Callable[..., Any], *args: Any) -> Any:
        try:
            return await run_in_threadpool(work, *args)
        except AccountRefused as refused:
            raise _Answer(_refusal(refused.status, refused.code, **refused.params)) from None
        except unavailable:
            raise _Answer(_refusal(503, "ACCOUNTS_UNAVAILABLE")) from None

    async def guarded(handler: Callable[[], Awaitable[Response]]) -> Response:
        if accounts is None:
            return _refusal(503, "ACCOUNTS_UNAVAILABLE")
        try:
            return await handler()
        except _Answer as answer:
            return answer.response

    async def signed_in(request: Request) -> PersonPrincipal:
        principal = await _call(person_from_request, request, accounts)
        if principal is None:
            raise _Answer(_refusal(401, "NOT_SIGNED_IN"))
        return principal

    def me_body(principal: PersonPrincipal, expires_at) -> dict:
        tenant = accounts.tenant(principal)
        me = next((v for v in accounts.people(principal) if v.person_id == principal.person_id), None)
        if tenant is None or me is None:  # MB2: never invented
            raise _Answer(_refusal(503, "ACCOUNTS_UNAVAILABLE"))
        return {"person": _person(me), "tenant": {"slug": tenant[0], "name": tenant[1]},
                "session_expires_at": _iso(expires_at)}

    def set_cookie(response: Response, value: str, max_age: int) -> None:
        response.set_cookie(COOKIE, value, max_age=max_age, path="/api", secure=cookie_secure, httponly=True,
                            samesite="strict")

    async def sign_in(request: Request) -> Response:
        body = await _json(request, ("email", "password"))
        signed = await _call(accounts.sign_in, body["email"], body["password"])
        content = await _call(me_body, signed.principal, signed.expires_at)
        response = JSONResponse(status_code=200, content=content, headers=NO_STORE)
        set_cookie(response, signed.token, SESSION_HOURS * 3600)
        return response

    async def sign_out(request: Request) -> Response:
        await _json(request, ())
        await _call(accounts.sign_out, request.cookies.get(COOKIE))
        response = Response(status_code=204, headers=NO_STORE)
        set_cookie(response, "", 0)  # the same attributes as sign-in (P9)
        return response

    async def me(request: Request) -> Response:
        principal = await signed_in(request)
        content = await _call(me_body, principal, principal.session_expires_at)
        return JSONResponse(status_code=200, content=content, headers=NO_STORE)

    async def people(request: Request) -> Response:
        principal = await signed_in(request)
        views = await _call(accounts.people, principal)
        return JSONResponse(status_code=200, content={"people": [_person(v) for v in views]}, headers=NO_STORE)

    async def role_grants(request: Request) -> Response:
        principal = await signed_in(request)
        rows = await _call(accounts.grant_record, principal)
        return JSONResponse(status_code=200, content={"rows": [_record(r) for r in rows]}, headers=NO_STORE)

    async def grant(request: Request) -> Response:
        body = await _json(request, ("person_id", "role", "site_code"), optional=frozenset({"site_code"}))
        principal = await signed_in(request)
        row = await _call(accounts.grant, principal, body["person_id"], body["role"], body.get("site_code"))
        return JSONResponse(status_code=201, content=_record(row), headers=NO_STORE)

    async def removal(request: Request, grant_id: str) -> Response:
        await _json(request, ())
        principal = await signed_in(request)
        row = await _call(accounts.remove, principal, grant_id)
        return JSONResponse(status_code=201, content=_record(row), headers=NO_STORE)

    @router.post("/api/auth/sign-in")
    async def post_sign_in(request: Request) -> Response:
        return await guarded(lambda: sign_in(request))

    @router.post("/api/auth/sign-out")
    async def post_sign_out(request: Request) -> Response:
        return await guarded(lambda: sign_out(request))

    @router.get("/api/auth/me")
    async def get_me(request: Request) -> Response:
        return await guarded(lambda: me(request))

    @router.get("/api/organisation/people")
    async def get_people(request: Request) -> Response:
        return await guarded(lambda: people(request))

    @router.get("/api/organisation/role-grants")
    async def get_role_grants(request: Request) -> Response:
        return await guarded(lambda: role_grants(request))

    @router.post("/api/organisation/role-grants")
    async def post_role_grant(request: Request) -> Response:
        return await guarded(lambda: grant(request))

    @router.post("/api/organisation/role-grants/{grant_id}/removal")
    async def post_removal(request: Request, grant_id: str) -> Response:
        return await guarded(lambda: removal(request, grant_id))

    return router
