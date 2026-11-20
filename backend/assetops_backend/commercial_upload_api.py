"""3A2 (spec §5; D-3A2.8, D-3A2.9, D-3A2.15, R7, R8): the commercial export upload routes.

`{base}` is `/api/sites/{site_code}/commercial-uploads` (every record must be this Site's) or
`/api/organisation/commercial-uploads` (any Site of the person's tenant, and portfolio-level records).

- `POST {base}?dry_run=true|false[&reader=<id>]`, header `X-File-Name` (percent-encoded UTF-8), body the file:
  200 `{"state": "CHECKED", ...}` or 201 the upload (WAITING).
- `GET {base}`: the 50 newest uploads in scope. `GET {base}/{upload_id}`: one upload.
- `POST {base}/{upload_id}/decision`, JSON `{"decision": "ACCEPT"|"DECLINE", "reason"}` (4 KiB): 201 the upload.

A signed-in person is always required, whatever `ASSETOPS_REQUIRE_PERSON` says. Refusal order, Site path: access
(401/403), scope (404 `SITE_NOT_FOUND`; a store error 503), the switch (403 `COMMERCIAL_UPLOAD_OFF`), the person
(`person_step`: 503, 401, the byte-equal Site 404 for another tenant, 403 with `roles`), the request (422
`UPLOAD_BAD_REQUEST`), then the service. The organisation path has no access or scope step; its tenant is the
person's. Every answer carries `Cache-Control: no-store`; every refusal is `{"code", "message", "words", "params"}`.
The file name travels in a header, never the query string, and is never logged (D-3A2.15).
"""
from __future__ import annotations

import json
import urllib.parse
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from assetops_backend.accounts.permissions import PersonRefused, person_step, roles_of
from assetops_backend.accounts.principal import person_from_request
from assetops_backend.commercial.model import StoreRefused
from assetops_backend.commercial.uploads import (MAX_UPLOAD_BYTES, Actor, CommercialUploads, UploadRefused,
                                                 UploadScope, has_control_character)
from assetops_backend.finding_api import Access, Scope, development_access
from assetops_backend.i18n import Message, message, render
from assetops_backend.reading_upload_api import _body_within

if TYPE_CHECKING:
    from assetops_backend.accounts.service import AccountService

MAX_FILE_NAME = 200
MAX_DECISION_BYTES = 4 * 1024
DECISION_KEYS = frozenset({"decision", "reason"})
NO_STORE = {"Cache-Control": "no-store"}
SITE_BASE = "/api/sites/{site_code}/commercial-uploads"
ORGANISATION_BASE = "/api/organisation/commercial-uploads"


def _refusal(status: int, code: str, words: Message, params: dict[str, Any] | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, headers=NO_STORE,
                        content={"code": code, "message": render(words), "words": words, "params": dict(params or {})})


def _answer(status: int, body: dict[str, Any]) -> JSONResponse:
    return JSONResponse(status_code=status, content=body, headers=NO_STORE)


def _site_not_found(site_code: str) -> JSONResponse:
    return _refusal(404, "SITE_NOT_FOUND", message("analytics.site_not_found", site_id=site_code))


def _unavailable() -> JSONResponse:
    return _refusal(503, "COMMERCIAL_UPLOAD_UNAVAILABLE", message("commercial_upload.unavailable"))


def _file_name(request: Request) -> str | None:
    """D-3A2.15: the `X-File-Name` header, percent-decoded as strict UTF-8, 1 to 200 characters after `strip()`, one
    file (no `/` or `\\`); None when any of that fails."""
    raw = request.headers.get("x-file-name")
    if raw is None:
        return None
    try:
        decoded = urllib.parse.unquote(raw, errors="strict")
    except UnicodeDecodeError:
        return None
    if has_control_character(decoded):  # F3: never stored, never a store fault
        return None
    name = decoded.strip()
    if not 1 <= len(name) <= MAX_FILE_NAME or "/" in name or "\\" in name:
        return None
    return name


def build_commercial_upload_router(uploads: CommercialUploads | None, scope: Scope, *,
                                   accounts: "AccountService | None",
                                   unavailable: tuple[type[BaseException], ...],
                                   access: Access = development_access) -> APIRouter:
    router = APIRouter()

    def person_refusal(refused: PersonRefused, site_code: str | None) -> JSONResponse:
        if refused.reason == "UNAVAILABLE":
            return _unavailable()
        if refused.reason == "PERSON_REQUIRED":
            return _refusal(401, "PERSON_REQUIRED", message("person.person_required"))
        if refused.reason == "TENANT" and site_code is not None:
            return _site_not_found(site_code)
        return _refusal(403, "PERSON_ROLE_REQUIRED", message("person.person_role_required"), refused.params)

    def open_site(request: Request, site_code: str, command: str) -> tuple[UUID, UploadScope, Actor] | JSONResponse:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", message("person.person_required"))
        if refusal == 403:
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", message("commercial_upload.site_forbidden", site_code=site_code),
                             {"site_code": site_code})
        try:
            found = scope(site_code)
        except unavailable:
            return _unavailable()
        if found is None:
            return _site_not_found(site_code)
        code, tenant_id, site_id = found
        if uploads is None:
            return _refusal(403, "COMMERCIAL_UPLOAD_OFF", message("commercial_upload.off"))
        try:
            grant = person_step(request, accounts, required=True, unavailable=unavailable, tenant_id=tenant_id,
                                site_id=site_id, command=command, enabled=True)
        except PersonRefused as refused:
            return person_refusal(refused, site_code)
        assert grant is not None  # required=True: no unsigned path
        return tenant_id, UploadScope(site_id, code), Actor(grant.person_id, grant.role)

    def open_organisation(request: Request, command: str) -> tuple[UUID, UploadScope, Actor] | JSONResponse:
        if uploads is None:
            return _refusal(403, "COMMERCIAL_UPLOAD_OFF", message("commercial_upload.off"))
        roles = roles_of(command)
        person = None
        if accounts is not None:
            try:
                person = person_from_request(request, accounts)
            except unavailable:
                return _unavailable()
        if person is None:
            return _refusal(401, "PERSON_REQUIRED", message("person.person_required"))
        for role in roles:
            if person.has_role(role, None):
                return person.tenant_id, UploadScope(None, None), Actor(person.person_id, role)
        return _refusal(403, "PERSON_ROLE_REQUIRED", message("person.person_role_required"),
                        {"roles": list(roles)})

    async def run(work: Callable[[], dict[str, Any]], status: int) -> JSONResponse:
        try:
            body = await run_in_threadpool(work)
        except UploadRefused as refused:
            return _refusal(refused.status, refused.code, refused.words, refused.params)
        except StoreRefused:  # D-3A2.2: a bug, not a user error; no constraint name or driver text leaves
            return _refusal(500, "COMMERCIAL_STORE_FAULT", message("commercial_upload.store_fault"))
        except unavailable:
            return _unavailable()
        return _answer(status, body)

    async def post_file(request: Request, opened: tuple[UUID, UploadScope, Actor] | JSONResponse) -> JSONResponse:
        if isinstance(opened, JSONResponse):
            return opened
        tenant_id, upload_scope, actor = opened
        dry = request.query_params.get("dry_run")
        if dry not in ("true", "false"):
            return _refusal(422, "UPLOAD_BAD_REQUEST", message("commercial_upload.bad_request", field="dry_run"),
                            {"field": "dry_run"})
        file_name = None if "file_name" in request.query_params else _file_name(request)
        if file_name is None:
            return _refusal(422, "UPLOAD_BAD_REQUEST", message("commercial_upload.bad_request", field="file_name"),
                            {"field": "file_name"})
        assert uploads is not None
        reader_id = request.query_params.get("reader")
        media_type = request.headers.get("content-type")
        try:
            uploads.reader(reader_id, media_type)
        except UploadRefused as refused:
            return _refusal(refused.status, refused.code, refused.words, refused.params)
        data = await _body_within(request, MAX_UPLOAD_BYTES)
        if data is None:
            refused = UploadRefused(413, "FILE_TOO_LARGE", {"limit_mb": MAX_UPLOAD_BYTES // 2**20})
            return _refusal(refused.status, refused.code, refused.words, refused.params)
        if dry == "true":
            return await run(lambda: uploads.check(tenant_id, upload_scope, actor, data, reader_id=reader_id,
                                                   media_type=media_type), 200)
        return await run(lambda: uploads.submit(tenant_id, upload_scope, actor, data, file_name=file_name,
                                                reader_id=reader_id, media_type=media_type), 201)

    async def post_decision(request: Request, opened: tuple[UUID, UploadScope, Actor] | JSONResponse,
                            upload_id: str) -> JSONResponse:
        if isinstance(opened, JSONResponse):
            return opened
        tenant_id, upload_scope, actor = opened

        def invalid(field: str) -> JSONResponse:
            return _refusal(422, "UPLOAD_DECISION_INVALID", message("commercial_upload.decision_invalid", field=field),
                            {"field": field})

        media_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            return _refusal(415, "JSON_REQUIRED", message("commercial_upload.json_required"))
        raw = await _body_within(request, MAX_DECISION_BYTES)
        if raw is None:
            return invalid("body")
        try:
            body = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            return invalid("body")
        if not isinstance(body, dict):
            return invalid("body")
        unknown = sorted(k for k in body if k not in DECISION_KEYS)
        if unknown:
            return invalid(unknown[0])
        decision = body.get("decision")
        if decision not in ("ACCEPT", "DECLINE"):
            return invalid("decision")
        assert uploads is not None
        return await run(lambda: uploads.decide(tenant_id, upload_scope, actor, upload_id, decision,
                                                body.get("reason")), 201)

    # --- the Site path ----------------------------------------------------------------------------------------

    @router.post(SITE_BASE)
    async def post_site(request: Request, site_code: str) -> JSONResponse:
        return await post_file(request, open_site(request, site_code, "commercial.upload"))

    @router.get(SITE_BASE)
    async def list_site(request: Request, site_code: str) -> JSONResponse:
        opened = open_site(request, site_code, "commercial.upload_read")
        if isinstance(opened, JSONResponse):
            return opened
        assert uploads is not None
        return await run(lambda: uploads.list(opened[0], opened[1]), 200)

    @router.get(SITE_BASE + "/{upload_id}")
    async def get_site(request: Request, site_code: str, upload_id: str) -> JSONResponse:
        opened = open_site(request, site_code, "commercial.upload_read")
        if isinstance(opened, JSONResponse):
            return opened
        assert uploads is not None
        return await run(lambda: uploads.get(opened[0], opened[1], upload_id), 200)

    @router.post(SITE_BASE + "/{upload_id}/decision")
    async def decide_site(request: Request, site_code: str, upload_id: str) -> JSONResponse:
        return await post_decision(request, open_site(request, site_code, "commercial.upload_decision"), upload_id)

    # --- the organisation path --------------------------------------------------------------------------------

    @router.post(ORGANISATION_BASE)
    async def post_organisation(request: Request) -> JSONResponse:
        return await post_file(request, open_organisation(request, "commercial.upload"))

    @router.get(ORGANISATION_BASE)
    async def list_organisation(request: Request) -> JSONResponse:
        opened = open_organisation(request, "commercial.upload_read")
        if isinstance(opened, JSONResponse):
            return opened
        assert uploads is not None
        return await run(lambda: uploads.list(opened[0], opened[1]), 200)

    @router.get(ORGANISATION_BASE + "/{upload_id}")
    async def get_organisation(request: Request, upload_id: str) -> JSONResponse:
        opened = open_organisation(request, "commercial.upload_read")
        if isinstance(opened, JSONResponse):
            return opened
        assert uploads is not None
        return await run(lambda: uploads.get(opened[0], opened[1], upload_id), 200)

    @router.post(ORGANISATION_BASE + "/{upload_id}/decision")
    async def decide_organisation(request: Request, upload_id: str) -> JSONResponse:
        return await post_decision(request, open_organisation(request, "commercial.upload_decision"), upload_id)

    return router
