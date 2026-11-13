"""DATA-5 (D-17N.4): the story harnesses forward gateway diagnostics to the product's diagnostics ingestion.

Before DATA-5 the story centrals answered a gateway's diagnostic post with `201 {}` and stored nothing, so Cold, EV and
Kisiwa Health read "Not in the gateway's latest report · Unknown" (`.agent/architect-answer-non-kobo-sites-2026-11-10.md`
E14, K16). The ingestion is the one behind `POST /api/gateways/{gateway_id}/diagnostics`
(`assetops_backend.gateway_api`, `DiagnosticIngestionService`); this module only routes the harness's posts to it.

- `forward_diagnostic`: for the replay harness, whose principal is built from the snapshot (no issued credential).
- `diagnostics_router`: for the Cold and EV harnesses, whose centrals are real FastAPI apps with issued credentials.

Each is opt-in (the demo prepare turns it on); the ordinary Postgres tests keep their centrals unchanged.

D-DATA.2: a forwarded diagnostic is received on the clock that sealed it, the harness gateway's own clock
(`gateway_clock`), never a story or decision clock. Otherwise every row has `observed_at` after `received_at` and
Health reads "Unknown age" (a harness artefact shown as a data fact), or a future `received_at` makes the read 409.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Callable

#: The gateway's diagnostic route (`assetops_backend.gateway_api.GATEWAY_DIAGNOSTICS_ROUTE`), path only.
_DIAGNOSTIC_PATH = re.compile(r"^/api/gateways/([^/?]+)/diagnostics$")


def diagnostic_gateway(path: str) -> str | None:
    """The gateway id a diagnostics post names, or None when `path` is not the diagnostics route."""
    match = _DIAGNOSTIC_PATH.match(path.split("?")[0])
    return None if match is None else match.group(1)


def forward_diagnostic(service, principal, path: str, body: bytes) -> tuple[int, bytes]:
    """Submit one diagnostic post to `service` (a `DiagnosticIngestionService`) as `principal`; the answer has the
    route's status and JSON (`gateway_api.post_diagnostic`), so the gateway records its receipt as from central."""
    from assetops_backend.evidence.gateway_access import DiagnosticRefused

    gateway_id = diagnostic_gateway(path)
    if gateway_id is None:
        raise ValueError(f"{path!r} is not the diagnostics route")
    try:
        receipt = service.submit(principal, gateway_id, body)
    except DiagnosticRefused as refused:
        return refused.status, json.dumps({"detail": {
            "code": refused.code, "kind": refused.kind, "field": refused.field, "message": refused.detail,
            "refusal_id": None if refused.refusal_id is None else str(refused.refusal_id)}}).encode("utf-8")
    return receipt.status, json.dumps({
        "diagnostic_id": str(receipt.diagnostic_id),
        "received_at": receipt.received_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "received_at_clock": "SERVER_REAL_UTC",
        "payload_sha256": receipt.payload_sha256,
    }).encode("utf-8")


def gateway_clock() -> datetime:
    """The harness gateway's own clock: the gateway process seals each diagnostic (`observed_at`, device contacts)
    on the real UTC wall clock (`assetops_gateway.service._utc_now`, the `GatewayService` default; the harness
    starts the process without a clock override). Backend tests do not import the gateway package, so it is
    restated here; `test_data5_story_diagnostics` pins the two together."""
    return datetime.now(timezone.utc)


def diagnostics_service(url: str, clock: Callable[[], datetime] = gateway_clock):
    """The product's diagnostics ingestion on the Postgres gateway-access store at `url`, receiving on `clock`
    (D-DATA.2: the gateway's own clock, which is the default)."""
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.gateway_access import DiagnosticIngestionService

    return DiagnosticIngestionService(PostgresGatewayAccess(url), clock)


def diagnostics_router(url: str, clock: Callable[[], datetime] = gateway_clock):
    """The product's gateway router (`build_gateway_router`) with diagnostics ingestion and credential principals
    on `url`; no Site health read is mounted (the harness central serves gateway posts only)."""
    from assetops_backend.evidence.adapters.postgres_gateway_access import PostgresGatewayAccess
    from assetops_backend.evidence.gateway_access import StoreGatewayPrincipals
    from assetops_backend.gateway_api import build_gateway_router

    return build_gateway_router(StoreGatewayPrincipals(PostgresGatewayAccess(url)), diagnostics_service(url, clock),
                                None, lambda _site: None, clock)
