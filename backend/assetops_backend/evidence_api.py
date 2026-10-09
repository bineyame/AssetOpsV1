"""Ingestion, Site > Evidence and Site Overview routes (T027). Ungated: mounted in both gate states.

The Simulator Lab gate covers simulator surfaces and execution, never accepted
evidence, so these routes are served with the gate closed (AC13, AC19).

`POST /api/ingestion/batches` is a thin wrapper over
`IngestionService.ingest`, the one ingestion entry point; the Lab Commit route
calls the same method in process. No other path writes evidence.

Payloads (snake_case JSON). Instants are `YYYY-MM-DDTHH:MM:SSZ` text; values are
exact decimal text or a discrete member, never floats.

POST /api/ingestion/batches
  body: an `assetops.ingestion-batch` v1 document
    {schema: {id, version}, batch_id, site_id, source_id, gateway_id,
     source_mode: "SIMULATED"|"LIVE",
     configuration: {site_id, foundation_version, foundation_valid_from},
     mapping: <mapping set document>, envelopes: [<canonical envelope text>...]}
  422 {detail: {code: "BATCH_REJECTED", kind, field, message}} - refused whole
      (unknown/private field anywhere, missing field, bad mapping, ...); nothing
      is written.
  200 BATCH  (status COMPLETED, or IN_PROGRESS if interrupted)
  409 BATCH  (status REFUSED: SITE_UNKNOWN, SITE_MISMATCH, SOURCE_MODE_MISMATCH,
      MAPPING_CONFLICT, CONFIGURATION_UNRESOLVED, BATCH_ID_CONFLICT)

  BATCH = {batch_id, site_id, source_id, gateway_id, source_mode, status,
           total, processed, accepted, duplicates, rejected, conflicts,
           refusal: null | {kind, detail}, started_at, completed_at|null,
           window_start|null, window_end|null}

GET /api/ingestion/batches/{batch_id} -> 200 BATCH | 404

GET /api/sites/{site_id}/evidence?from=&to=  -> 200 | 404 SITE_NOT_FOUND
  {site_id,
   window: {start|null, end|null, basis: "LATEST_RELEASE"|"REQUESTED"},
   sources: [{source_id, gateway_id, source_mode, accepted_total,
              accepted_in_window, duplicates, rejected, conflicts,
              last_source_time, last_published_at, last_received_at,
              batches: [{batch_id, status, processed, total}]}],
   source_health_statement,
   coverage: [{device_id, signal_id, family|null,
               status: "REPORTED"|"NOT_REPORTED", unit|null, records, good,
               unavailable, overlapping, first_source_time|null,
               last_source_time|null, longest_silence_seconds|null,
               needed_by: [metric name...]}],
   coverage_statement, overlap_statement,
   basis: {mappings: [{mapping_set_id, mapping_version}],
           configurations: [{foundation_version, foundation_valid_from,
                             registered_at, signal_count}],
           current_foundation: {foundation_version, foundation_valid_from}},
   rejection_count, conflict_count}
  Default window: the latest completed batch's accepted window, else all.

GET /api/sites/{site_id}/evidence/records?device=&signal=&source=&from=&to=&limit=
  -> {site_id, total, limit, records: [{message_id, source_id, gateway_id,
      device_id, signal_id, family, value, unit, quality, source_time,
      published_at, received_at, overlapping}]}  newest source_time first.

GET /api/sites/{site_id}/evidence/records/{message_id} -> 200 | 404
  {message_id, site_id, source_id, gateway_id, source_mode, device_id,
   signal_id, family, measurement,
   mapping: {mapping_set_id, mapping_version},
   configuration: {foundation_version, foundation_valid_from, registered_at},
   quality, unavailable_reason,
   original: {value, unit}, normalized: {value, unit},
   normalization: "IDENTITY", normalization_statement,
   interval: null | {start, end}, record_detail: {name: text},
   source_time, published_at, received_at, batch_id, content_digest,
   envelope_text, overlapping_with: [message_id], conflicts: [{batch_id,
   original_digest, conflicting_digest, received_at}]}

GET /api/sites/{site_id}/evidence/rejections?batch=
  -> {site_id, total, rejections: [{batch_id, index|null, message_id|null,
      kind, field, detail, reason (plain, read-time), received_at,
      content_digest}],
      conflicts: [{message_id, batch_id, original_digest, conflicting_digest,
      received_at}]}

GET /api/sites/{site_id}/overview?from=&to=   (T027 phase 2)
  -> {site_id, site_type, window: {start, end, basis, hours}, accepted_in_window,
      source_gateway_pairs_in_window,
      objective: {assessment: ASSESSMENT, service_delivered: METRIC|null},
      cards: [{domain_id, label, assessment: ASSESSMENT, metrics: [METRIC],
               coverage: [{device_id, signal_id, status: "REPORTED"|
                 "NOT_REPORTED"|"NO_GOOD_RECORD"|"NO_INTERVAL_SPAN"|
                 "OVERLAPPING_ONLY"|"OVERLAPPING_OR_NO_SPAN", records, good,
                 usable, unavailable,
                 last_source_time|null}],
               gaps: [{device_id, signal_id, status, reason}]}],
      interval_statement, timeline: [{series_id, label, unit,
        kind: "INTERVAL_MEAN"|"STATE_AT_INSTANT", basis,
        points: [{start, end, value, message_id|null} | {at, value, message_id}]}],
      timeline_statement, findings: [], findings_statement}
  ASSESSMENT = {status: "NO_ASSESSMENT", label: "No assessment yet", reason}
  METRIC = {metric_id, label, unit, value|null, at|null, basis, window_note|null,
            evidence: [{device_id, signal_id, message_id}],
            unavailable_because|null}
  Accepted evidence only; the same default window as Site > Evidence.

Errors use {detail: {code, message}}; 503 EVIDENCE_STORE_UNAVAILABLE when the
store cannot be read.
"""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, Response

from assetops_backend.evidence.overview import CardAssessments, OverviewReadModel
from assetops_backend.evidence.ports import EvidenceStoreUnavailable
from assetops_backend.evidence.read_model import EvidenceReadModel, batch_payload
from assetops_backend.evidence.ledger import (
    ClosedGatewayPrincipals,
    GatewayPrincipal,
    GatewayPrincipalResolver,
    LedgerUnavailable,
    PrincipalRefused,
)
from assetops_backend.evidence.ledger_service import BatchIngestionService, BatchRefused
from assetops_backend.evidence.service import IngestionService
from assetops_backend.sites.models import SiteRecord
from assetops_backend.sites.ports import (
    SiteAwaitingMigration,
    SiteNotFound,
    SiteRepository,
    SiteStoreUnavailable,
)
from assetops_contracts.ingestion_batch import (
    IngestionBatchRejected,
    parse_ingestion_batch_document,
)
from assetops_contracts.ingestion_batch_v2 import MAX_BATCH_BYTES
from assetops_contracts.ingestion_receipt_v2 import canonical_receipt_v2_text

INGESTION_BATCHES_ROUTE = "/api/ingestion/batches"
INGESTION_BATCH_ROUTE = "/api/ingestion/batches/{batch_id}"
SITE_EVIDENCE_ROUTE = "/api/sites/{site_id}/evidence"
SITE_EVIDENCE_RECORDS_ROUTE = "/api/sites/{site_id}/evidence/records"
SITE_EVIDENCE_RECORD_ROUTE = "/api/sites/{site_id}/evidence/records/{message_id}"
SITE_EVIDENCE_REJECTIONS_ROUTE = "/api/sites/{site_id}/evidence/rejections"
SITE_OVERVIEW_ROUTE = "/api/sites/{site_id}/overview"

_INSTANT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def _instant_param(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    if not _INSTANT.fullmatch(value):
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_WINDOW", "message": f"{name} is a UTC instant (YYYY-MM-DDTHH:MM:SSZ)"},
        )
    return value


def build_evidence_router(
    ingestion: IngestionService,
    sites: SiteRepository,
    card_assessments: CardAssessments | None = None,
    batch_ingestion: BatchIngestionService | None = None,
    gateway_principals: GatewayPrincipalResolver | None = None,
) -> APIRouter:
    """`batch_ingestion` serves Batch/Receipt V2 (S2-02) for a request carrying
    `Authorization`; the principal comes only from `gateway_principals`, which
    defaults to closed (every V2 upload 401) until the TLS/bearer verifier exists.
    A request without `Authorization` keeps the legacy V1 path for YAML Sites."""
    router = APIRouter()
    principals = ClosedGatewayPrincipals() if gateway_principals is None else gateway_principals
    read_model = EvidenceReadModel(ingestion.store)
    overview_model = OverviewReadModel(ingestion.store, card_assessments)

    def site_or_404(site_id: str) -> SiteRecord:
        try:
            return sites.get_site(site_id)
        except SiteAwaitingMigration as error:
            raise HTTPException(
                status_code=409,
                detail={"code": SiteAwaitingMigration.code, "message": str(error)},
            ) from error
        except SiteStoreUnavailable as error:
            raise HTTPException(
                status_code=503,
                detail={"code": "SITE_STORE_UNAVAILABLE", "message": str(error)},
            ) from error
        except SiteNotFound as error:
            raise HTTPException(
                status_code=404,
                detail={"code": "SITE_NOT_FOUND", "message": f"No Site {site_id} is configured."},
            ) from error

    def unavailable(error: EvidenceStoreUnavailable) -> HTTPException:
        return HTTPException(
            status_code=503,
            detail={"code": "EVIDENCE_STORE_UNAVAILABLE", "message": str(error)},
        )

    def authenticate(request: Request) -> GatewayPrincipal | JSONResponse:
        try:
            return principals.resolve(request.headers.get("authorization"))
        except PrincipalRefused as refusal:
            headers = {"WWW-Authenticate": "Bearer"} if refusal.status == 401 else None
            return JSONResponse(
                status_code=refusal.status,
                content={"detail": {"code": refusal.code, "message": refusal.message}},
                headers=headers,
            )

    def ledger_unavailable(message: str) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": {"code": "EVIDENCE_LEDGER_UNAVAILABLE", "message": message}}
        )

    def receipt_response(status: int, receipt) -> Response:
        # The exact canonical Receipt V2 text, so the gateway can verify receipt_sha256.
        return Response(status_code=status, content=canonical_receipt_v2_text(receipt),
                        media_type="application/json")

    async def post_batch_v2(request: Request) -> Response:
        principal = authenticate(request)
        if isinstance(principal, JSONResponse):
            return principal
        if batch_ingestion is None:
            return ledger_unavailable("No central evidence ledger is configured.")
        declared = request.headers.get("content-length")
        if declared is not None and declared.isdigit() and int(declared) > MAX_BATCH_BYTES:
            return JSONResponse(status_code=413, content={"detail": {
                "code": "BATCH_REFUSED", "kind": "TOO_LARGE", "field": "batch",
                "message": f"more than {MAX_BATCH_BYTES} bytes"}})
        raw = await request.body()
        try:
            submitted = await run_in_threadpool(batch_ingestion.submit, principal, raw)
        except BatchRefused as refused:
            return JSONResponse(status_code=refused.status, content={"detail": {
                "code": refused.code, "kind": refused.kind, "field": refused.field,
                "message": refused.detail, "refusal_id": refused.refusal_id}})
        except LedgerUnavailable as error:
            return ledger_unavailable(str(error))
        return receipt_response(submitted.status, submitted.receipt)

    @router.post(INGESTION_BATCHES_ROUTE)
    async def post_batch(request: Request) -> Response:
        if "authorization" in request.headers:
            return await post_batch_v2(request)
        raw = await request.body()
        try:
            document = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise HTTPException(
                status_code=422,
                detail={"code": "BATCH_REJECTED", "kind": "NOT_A_BATCH", "field": "",
                        "message": "the body is not JSON"},
            ) from error
        if isinstance(document, dict) and document.get("schema") == {
            "id": "assetops.ingestion-batch", "version": 2
        }:
            # Batch V2 is accepted only from an authenticated registered gateway.
            return JSONResponse(status_code=401, headers={"WWW-Authenticate": "Bearer"}, content={"detail": {
                "code": "GATEWAY_CREDENTIAL_REQUIRED",
                "message": "Batch V2 requires a registered gateway credential."}})
        try:
            batch = parse_ingestion_batch_document(document)
        except IngestionBatchRejected as refusal:
            raise HTTPException(
                status_code=422,
                detail={"code": "BATCH_REJECTED", "kind": refusal.kind,
                        "field": refusal.field, "message": refusal.detail},
            ) from refusal
        try:
            progress = await run_in_threadpool(ingestion.ingest, batch)
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error
        status = 409 if progress.status == "REFUSED" else 200
        return JSONResponse(status_code=status, content=batch_payload(progress))

    @router.get(INGESTION_BATCH_ROUTE)
    def get_batch(batch_id: str, request: Request):
        if "authorization" in request.headers:
            principal = authenticate(request)
            if isinstance(principal, JSONResponse):
                return principal
            if batch_ingestion is None:
                return ledger_unavailable("No central evidence ledger is configured.")
            try:
                receipt = batch_ingestion.receipt(principal, batch_id)
            except LedgerUnavailable as error:
                return ledger_unavailable(str(error))
            if receipt is None:
                return JSONResponse(status_code=404, content={"detail": {
                    "code": "BATCH_NOT_FOUND", "message": f"No batch {batch_id} was received from this gateway."}})
            return receipt_response(200 if receipt.status == "COMPLETED" else 202, receipt)
        try:
            payload = read_model.batch(batch_id)
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error
        if payload is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "BATCH_NOT_FOUND", "message": f"No batch {batch_id} was ingested."},
            )
        return payload

    @router.get(SITE_EVIDENCE_ROUTE)
    def get_site_evidence(site_id: str, request: Request) -> dict:
        site = site_or_404(site_id)
        start = _instant_param(request.query_params.get("from"), "from")
        end = _instant_param(request.query_params.get("to"), "to")
        try:
            return read_model.site_evidence(site, start, end)
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error

    @router.get(SITE_OVERVIEW_ROUTE)
    def get_site_overview(site_id: str, request: Request) -> dict:
        site = site_or_404(site_id)
        start = _instant_param(request.query_params.get("from"), "from")
        end = _instant_param(request.query_params.get("to"), "to")
        try:
            return overview_model.site_overview(site, start, end)
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error

    @router.get(SITE_EVIDENCE_RECORDS_ROUTE)
    def get_records(site_id: str, request: Request) -> dict:
        site = site_or_404(site_id)
        params = request.query_params
        limit_text = params.get("limit", "100")
        if not limit_text.isdigit() or not 1 <= int(limit_text) <= 1000:
            raise HTTPException(
                status_code=422,
                detail={"code": "INVALID_LIMIT", "message": "limit is a whole number from 1 to 1000"},
            )
        try:
            return read_model.records(
                site.site_id,
                device_id=params.get("device"),
                signal_id=params.get("signal"),
                source_id=params.get("source"),
                window_start=_instant_param(params.get("from"), "from"),
                window_end=_instant_param(params.get("to"), "to"),
                limit=int(limit_text),
            )
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error

    @router.get(SITE_EVIDENCE_RECORD_ROUTE)
    def get_record(site_id: str, message_id: str) -> dict:
        site = site_or_404(site_id)
        try:
            payload = read_model.record(site.site_id, message_id)
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error
        if payload is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "RECORD_NOT_FOUND",
                        "message": f"No accepted record {message_id} at {site.site_id}."},
            )
        return payload

    @router.get(SITE_EVIDENCE_REJECTIONS_ROUTE)
    def get_rejections(site_id: str, request: Request) -> dict:
        site = site_or_404(site_id)
        try:
            return read_model.rejections(site.site_id, request.query_params.get("batch"))
        except EvidenceStoreUnavailable as error:
            raise unavailable(error) from error

    return router
