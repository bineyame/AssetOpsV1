"""UP-1 (rev 7 section 7.5, D-17N.5): the reading-upload routes.

- `POST /api/sites/{site_code}/reading-uploads?dry_run=true|false&file_name=<name>`: the body is the CSV file
  itself (`Content-Type: text/csv`, at most 2 MB). `dry_run=true` answers the preview (200, state CHECKED) and
  writes nothing; `dry_run=false` sends it and answers the upload (201). A refused file is 422 with its code and
  words; on confirm the refusal is recorded and nothing is admitted.
- `GET /api/sites/{site_code}/reading-uploads/{upload_id}`: the upload's state (Sent, Accepted n of m, Still
  processing, Analysed; Refused; Held alongside).
- `GET /api/sites/{site_code}/reading-uploads/template`: the CSV template (the profile's header row, built by the
  host), `text/csv`, downloaded as `<SITE>-readings-template.csv`. The page shows `reading_upload.template_note`.

SPEC DEVIATION (transport, D-UP.5): section 7.5 said multipart; the body is the raw file (`text/csv`) with
`?file_name=` (display-only, at most 200 characters), so no multipart dependency is added.

Refusal order: Site read access (401/403), Site scope (404 `SITE_NOT_FOUND`), the switch (403 `READING_UPLOAD_OFF`
when no service is wired, i.e. `ASSETOPS_READING_UPLOAD_SITES` unset), the Site list (403
`READING_UPLOAD_NOT_THIS_SITE`), the request (422 `READING_UPLOAD_BAD_REQUEST`), the media type (415
`READING_UPLOAD_UNSUPPORTED_TYPE`), size (413 `FILE_TOO_LARGE`), then the service. Every refusal carries `code`, `message` (rendered for the request's locale) and `words` (the key).
A parse stopped by a limit answers 503 with the check's or the send's unavailable words (ENV-1).
"""

from __future__ import annotations

import logging
from typing import Any, Callable
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from assetops_backend.finding_api import Access, Scope, development_access
from assetops_backend.i18n import Message, message, render
from assetops_backend.reading_upload.service import (LOAD_CAUSES, MAX_BYTES, GatewayUnavailable, ParseLimitBreach,
                                                     ReadingUploadService, UploadRefused, refusal_words)

#: D-UP.5: `file_name` is display-only (never a path) and at most 200 characters.
MAX_FILE_NAME = 200
#: ENV-1 (D-ENV1.5, D-ENV1.11; the D-3A6.29 pattern): every 503 of the service logs once, as codes and numbers.
_LOG = logging.getLogger("assetops.reading_upload")


def _refusal(status: int, code: str, words: Message, **extra: Any) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "message": render(words), "words": words,
                                                     **extra})


def _rendered(body: dict) -> dict:
    """Each `words` message in the body gains its rendered `text` (the page shows server words only)."""
    if isinstance(body.get("words"), dict) and "key" in body["words"]:
        body["text"] = render(body["words"])
    if isinstance(body.get("uploaded_by"), dict):
        body["uploaded_by_text"] = render(body["uploaded_by"])
    preview = body.get("preview")
    if isinstance(preview, dict):
        for column in preview.get("columns") or ():
            for name in ("meter", "role_name"):
                if isinstance(column.get(name), dict):
                    column[f"{name}_text"] = render(column[name])
    return body


async def _body_within(request: Request, limit: int) -> bytes | None:
    """The request body, or None as soon as it passes `limit` bytes (never read whole into memory past it)."""
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


def build_reading_upload_router(service: ReadingUploadService | None, scope: Scope, allowed_sites: frozenset[str],
                                access: Access = development_access,
                                unavailable: tuple[type[BaseException], ...] = ()) -> APIRouter:
    router = APIRouter()
    allowed = frozenset(code.upper() for code in allowed_sites)

    def open_site(request: Request, site_code: str) -> tuple[UUID, UUID] | JSONResponse:
        refusal = access(request, site_code)
        if refusal == 401:
            return _refusal(401, "UNAUTHENTICATED", message("reading_upload.not_this_site"))
        if refusal == 403:
            return _refusal(403, "SITE_SCOPE_FORBIDDEN", message("reading_upload.not_this_site"))
        try:
            found = scope(site_code)
        except unavailable:
            return _refusal(503, "READING_UPLOAD_UNAVAILABLE", message("reading_upload.gateway_unavailable"))
        if found is None:
            return _refusal(404, "SITE_NOT_FOUND", message("analytics.site_not_found", site_id=site_code))
        code, tenant_id, site_id = found
        if service is None:
            return _refusal(403, "READING_UPLOAD_OFF", message("reading_upload.off"))
        if code.upper() not in allowed:
            return _refusal(403, "READING_UPLOAD_NOT_THIS_SITE", message("reading_upload.not_this_site"))
        return tenant_id, site_id

    async def run(work: Callable[[], tuple[int, dict]], *, site: str | None = None,
                  size: int | None = None) -> JSONResponse:
        # The upload runs field processes and database reads: off the event loop (as `evidence_api` does).
        try:
            status, body = await run_in_threadpool(work)
        except UploadRefused as refused:
            return _refusal(refused.status, refused.code, refused.words, **refused.extra)
        except ParseLimitBreach as breach:  # ENV-1: before the two below; no file name, content or reading logged
            extra = {"cause": breach.cause, "step": breach.step, "bytes": size, "site": site}
            if breach.cause in LOAD_CAUSES:
                _LOG.warning("reading upload parse stopped by load", extra=extra)
            else:
                _LOG.error("reading upload parse stopped by its CPU, memory or crash limit; a file within the upload "
                           "cap should not reach it: re-measure FieldLimits for this host (ENV-1 section 0)",
                           extra=extra)
            if breach.step == "send":
                return _refusal(503, "READING_UPLOAD_GATEWAY_UNAVAILABLE",
                                message("reading_upload.gateway_unavailable"))
            return _refusal(503, "READING_UPLOAD_CHECK_UNAVAILABLE", message("reading_upload.check_unavailable"))
        except GatewayUnavailable:
            _LOG.warning("reading upload send unavailable",
                         extra={"cause": "gateway", "step": "send", "bytes": size, "site": site})
            return _refusal(503, "READING_UPLOAD_GATEWAY_UNAVAILABLE", message("reading_upload.gateway_unavailable"))
        except RuntimeError:  # a field process that printed no JSON: said in words, never a bare 500
            _LOG.error("reading upload check failed without an answer",
                       extra={"cause": "error", "step": "check", "bytes": size, "site": site})
            return _refusal(503, "READING_UPLOAD_CHECK_UNAVAILABLE", message("reading_upload.check_unavailable"))
        if status == 422 and "refusal" in body:
            return JSONResponse(status_code=422, content={"code": body["refusal"]["code"],
                                                          "message": render(body["words"]), **_rendered(body)})
        return JSONResponse(status_code=status, content=_rendered(body))

    @router.post("/api/sites/{site_code}/reading-uploads")
    async def post_upload(request: Request, site_code: str) -> JSONResponse:
        opened = open_site(request, site_code)
        if isinstance(opened, JSONResponse):
            return opened
        tenant_id, site_id = opened
        dry = request.query_params.get("dry_run")
        if dry not in ("true", "false"):
            return _refusal(422, "READING_UPLOAD_BAD_REQUEST",
                            message("reading_upload.bad_request", detail="dry_run must be true or false"))
        file_name = (request.query_params.get("file_name") or "").strip()
        if not 1 <= len(file_name) <= MAX_FILE_NAME or "/" in file_name or "\\" in file_name:
            return _refusal(422, "READING_UPLOAD_BAD_REQUEST",
                            message("reading_upload.bad_request", detail="file_name names one file"))
        media_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
        if media_type != "text/csv":
            return _refusal(415, "READING_UPLOAD_UNSUPPORTED_TYPE", message("reading_upload.unsupported_type"))
        data = await _body_within(request, MAX_BYTES)
        if data is None:
            return _refusal(413, "FILE_TOO_LARGE", refusal_words("FILE_TOO_LARGE", limit_mb=MAX_BYTES // 2**20))
        assert service is not None  # open_site refused otherwise
        return await run(lambda: service.upload(tenant_id, site_id, file_name, data, dry == "true"),
                         site=site_code.upper(), size=len(data))

    @router.get("/api/sites/{site_code}/reading-uploads")
    async def get_uploads_entry(request: Request, site_code: str) -> JSONResponse:
        """Whether the upload page is on for this Site (the Health panel shows only on 200), with the template
        words. Off, or another Site, is the same 403 the POST gives."""
        opened = open_site(request, site_code)
        if isinstance(opened, JSONResponse):
            return opened
        return JSONResponse(status_code=200, content={"enabled": True,
                                                      "template_note": render(message("reading_upload.template_note")),
                                                      "health_text": render(message("reading_upload.health_panel")),
                                                      "template_step": render(message("reading_upload.template_step"))},
                            headers={"Cache-Control": "no-store"})

    # Declared before `/{upload_id}`, so "template" is never read as an upload reference.
    @router.get("/api/sites/{site_code}/reading-uploads/template")
    async def get_template(request: Request, site_code: str) -> Response:
        opened = open_site(request, site_code)
        if isinstance(opened, JSONResponse):
            return opened
        assert service is not None
        body = service.template_csv()
        if body is None:
            return _refusal(503, "READING_UPLOAD_TEMPLATE_UNAVAILABLE", message("reading_upload.template_unavailable"))
        name = f"{site_code.upper()}-readings-template.csv"
        return Response(content=body, media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{name}"',
                                 "Cache-Control": "no-store"})

    @router.get("/api/sites/{site_code}/reading-uploads/{upload_id}")
    async def get_upload(request: Request, site_code: str, upload_id: str) -> JSONResponse:
        opened = open_site(request, site_code)
        if isinstance(opened, JSONResponse):
            return opened
        tenant_id, site_id = opened
        try:
            parsed = UUID(upload_id)
        except ValueError:
            return _refusal(404, "UPLOAD_NOT_FOUND", message("reading_upload.not_found"))
        assert service is not None
        return await run(lambda: service.status(tenant_id, site_id, parsed))

    return router

