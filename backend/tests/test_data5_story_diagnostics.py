"""DATA-5 (D-17N.4): the story harnesses route gateway diagnostics to the product ingestion. No database: the
ingestion is a fake with the `DiagnosticIngestionService.submit` contract; the Postgres proof is the VPS scratch
prepare named in `archive/agent-history/DATA-17N-packet.md`."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from assetops_backend.evidence.gateway_access import DiagnosticReceipt, DiagnosticRefused
from story_diagnostics import diagnostic_gateway, diagnostics_router, forward_diagnostic

GW = str(uuid4())
AT = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)


class _Service:
    def __init__(self, refuse: DiagnosticRefused | None = None) -> None:
        self.calls: list[tuple] = []
        self.refuse = refuse

    def submit(self, principal, path_gateway_id, raw):
        self.calls.append((principal, path_gateway_id, raw))
        if self.refuse is not None:
            raise self.refuse
        return DiagnosticReceipt(status=201, diagnostic_id=uuid4(), received_at=AT, payload_sha256="ab" * 32)


def test_only_the_diagnostics_route_is_matched() -> None:
    assert diagnostic_gateway(f"/api/gateways/{GW}/diagnostics") == GW
    assert diagnostic_gateway(f"/api/gateways/{GW}/diagnostics?x=1") == GW
    assert diagnostic_gateway("/api/ingestion/batches") is None
    assert diagnostic_gateway(f"/api/gateways/{GW}/other") is None


def test_a_diagnostic_is_submitted_as_the_principal_and_answered_like_the_route() -> None:
    service, principal = _Service(), object()
    status, body = forward_diagnostic(service, principal, f"/api/gateways/{GW}/diagnostics", b"{diag}")
    assert service.calls == [(principal, GW, b"{diag}")]
    answer = json.loads(body)
    assert status == 201
    assert answer["received_at"] == "2026-11-03T12:00:00.000000Z"  # the service's receipt, as the route formats it
    assert set(answer) == {"diagnostic_id", "received_at", "received_at_clock", "payload_sha256"}


def test_a_refusal_is_returned_not_swallowed() -> None:
    service = _Service(DiagnosticRefused(403, "GATEWAY_SCOPE_MISMATCH", "SCOPE", "site_id", "another Site"))
    status, body = forward_diagnostic(service, object(), f"/api/gateways/{GW}/diagnostics", b"{}")
    assert status == 403 and json.loads(body)["detail"]["code"] == "GATEWAY_SCOPE_MISMATCH"


def test_a_batch_path_is_not_forwarded() -> None:
    with pytest.raises(ValueError):
        forward_diagnostic(_Service(), object(), "/api/ingestion/batches", b"{}")


def test_the_router_mounts_the_product_diagnostics_route() -> None:
    router = diagnostics_router("postgresql://unused", lambda: AT)  # engines are lazy: no connection is made
    assert ("/api/gateways/{gateway_id}/diagnostics", "POST") in {
        (r.path, m) for r in router.routes for m in getattr(r, "methods", ())}


def test_the_demo_prepare_turns_forwarding_on_for_cold_ev_and_kisiwa_only() -> None:
    """The ordinary tests keep their centrals (flags off); the demo children turn them on (source pins)."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    import test_w202_cold_replay_postgres as w202
    import test_w205b_ev_replay_postgres as w205b

    assert w202.DIAGNOSTIC_CLOCK is None and w205b.FORWARD_DIAGNOSTICS is False
    cold = (root / "tools" / "demo_combined_cold.py").read_text(encoding="utf-8")
    ev = (root / "tools" / "demo_combined_ev.py").read_text(encoding="utf-8")
    kisiwa = (root / "tools" / "demo_combined_kisiwa.py").read_text(encoding="utf-8")
    kobo = (root / "tools" / "demo_combined_kobo.py").read_text(encoding="utf-8")
    assert "w202.DIAGNOSTIC_CLOCK = gateway_clock" in cold
    assert "registered.FORWARD_DIAGNOSTICS = True" in ev and '"FORWARD_DIAGNOSTICS")' in ev
    assert "diagnostics=True" in kisiwa
    assert "diagnostics=True" not in kobo  # Kobo Health is unchanged (packet question Q1)


def test_a_forwarded_diagnostic_is_received_on_the_gateway_clock_not_the_story_instant() -> None:
    """D-DATA.2: the receipt's `received_at` is the clock that sealed the diagnostic (the gateway's own clock)."""
    import story_diagnostics
    from assetops_backend.evidence.gateway_access import DiagnosticIngestionService

    sealed = datetime(2026, 11, 15, 21, 4, 5, tzinfo=timezone.utc)  # the prepare's real time, not the story `AT`
    service = story_diagnostics.diagnostics_service("postgresql://unused", lambda: sealed)  # lazy engine: no connection
    assert isinstance(service, DiagnosticIngestionService) and service._clock() == sealed != AT
    # the default is the gateway's own clock, and the three harness paths name it (no story or decision clock)
    assert story_diagnostics.diagnostics_service.__defaults__ == (story_diagnostics.gateway_clock,)
    assert story_diagnostics.diagnostics_router.__defaults__ == (story_diagnostics.gateway_clock,)
    before = datetime.now(timezone.utc)
    assert before <= story_diagnostics.gateway_clock() <= datetime.now(timezone.utc)
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    replay = (root / "host" / "tests" / "test_s6_verification_replay.py").read_text(encoding="utf-8")
    ev = (root / "backend" / "tests" / "test_w205b_ev_replay_postgres.py").read_text(encoding="utf-8")
    assert "diagnostics_service(URL, gateway_clock)" in replay and "diagnostics_service(URL, received)" not in replay
    assert "diagnostics_router(URL, gateway_clock)" in ev and "diagnostics_router(URL, self.decision_clock)" not in ev


def test_the_gateway_clock_is_the_gateway_process_default_clock() -> None:
    """`gateway_clock` restates the gateway's default (`GatewayService(clock=_utc_now)`); pin them together."""
    import inspect
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    service = (root / "gateway" / "assetops_gateway" / "service.py").read_text(encoding="utf-8")
    main = (root / "gateway" / "assetops_gateway" / "__main__.py").read_text(encoding="utf-8")
    assert "clock: Callable[[], datetime] = _utc_now" in service
    assert "def _utc_now() -> datetime:\n    return datetime.now(timezone.utc)" in service
    assert "GatewayService(config.database)" in main  # the process runs without a clock override
    import story_diagnostics

    assert "datetime.now(timezone.utc)" in inspect.getsource(story_diagnostics.gateway_clock)
