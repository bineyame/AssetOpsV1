"""A fake central ingestion server over real TLS, for the gateway upload tests.

Serves `https://127.0.0.1:<port>` with the checked-in, test-only self-signed
certificate in `fixtures/` (CN/SAN localhost and 127.0.0.1, valid to 2126; its
private key protects nothing but these tests). `responder(path, headers, body)`
answers `(status, body bytes)`, or `DROP` to close the connection with no
response (a server that committed but crashed before answering), or sleeps to
force a client timeout. Every request is recorded with its exact bytes.
"""

from __future__ import annotations

import ssl
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from assetops_contracts.ingestion_batch_v2 import parse_canonical_batch_v2_text
from assetops_contracts.ingestion_receipt_v2 import (
    IngestionReceiptV2,
    ReceiptCounts,
    ReceiptDisposition,
    ReceiptRejection,
    canonical_receipt_v2_text,
)
from assetops_contracts.source_envelope_v3 import parse_canonical_envelope_v3_text

FIXTURES = Path(__file__).parent / "fixtures"
CERT = FIXTURES / "test_tls_cert.pem"
KEY = FIXTURES / "test_tls_key.pem"
DROP = "DROP"
SERVER_INSTANT = "2026-10-09T10:00:00.000000Z"


@dataclass
class Recorded:
    path: str
    headers: dict[str, str]
    body: bytes


@dataclass
class FakeCentral:
    responder: Callable[[str, dict[str, str], bytes], object]
    requests: list[Recorded] = field(default_factory=list)

    def __post_init__(self) -> None:
        central = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_: object) -> None:  # quiet
                pass

            def do_POST(self) -> None:  # noqa: N802
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                headers = {k: v for k, v in self.headers.items()}
                central.requests.append(Recorded(self.path, headers, body))
                answer = central.responder(self.path, headers, body)
                if answer == DROP:
                    self.close_connection = True
                    self.connection.shutdown(2)
                    return
                status, payload = answer
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(CERT, KEY)
        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.httpd.socket = context.wrap_socket(self.httpd.socket, server_side=True)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def url(self) -> str:
        return f"https://127.0.0.1:{self.httpd.server_address[1]}"

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


def receipt_for(
    payload_text: str,
    *,
    decisions: dict[int, str] | None = None,
    decided: int | None = None,
    **overrides: object,
) -> IngestionReceiptV2:
    """The receipt an honest server would build for these exact batch bytes."""
    batch = parse_canonical_batch_v2_text(payload_text)
    message_ids = [parse_canonical_envelope_v3_text(t).message_id for t in batch.envelopes]
    total = len(message_ids)
    count = total if decided is None else decided
    decisions = decisions or {}
    dispositions = []
    for ordinal in range(count):
        decision = decisions.get(ordinal, "ACCEPTED")
        tail = f"{ordinal:012x}"
        evidence = f"00000000-0000-4000-8000-{tail}" if decision in ("ACCEPTED", "DUPLICATE") else None
        rejection = (
            None
            if evidence is not None
            else ReceiptRejection(
                rejection_id=f"00000000-0000-4000-9000-{tail}",
                kind="OUTSIDE_VALIDITY",
                field="source_time",
                detail="test",
                conflicts_with_evidence_id=f"00000000-0000-4000-a000-{tail}" if decision == "CONFLICT" else None,
            )
        )
        dispositions.append(ReceiptDisposition(ordinal, message_ids[ordinal], decision, evidence, rejection))
    tallies = {d: sum(1 for x in dispositions if x.decision == d) for d in ("ACCEPTED", "DUPLICATE", "REJECTED", "CONFLICT")}
    fields = dict(
        batch_id=batch.batch_id,
        payload_sha256=batch.payload_sha256,
        site_id=batch.site_id,
        gateway_id=batch.gateway_id,
        source_id=batch.source_id,
        status="COMPLETED" if count == total else "IN_PROGRESS",
        received_at=SERVER_INSTANT,
        completed_at=SERVER_INSTANT if count == total else None,
        counts=ReceiptCounts(
            total=total,
            processed=count,
            accepted=tallies["ACCEPTED"],
            duplicate=tallies["DUPLICATE"],
            rejected=tallies["REJECTED"],
            conflict=tallies["CONFLICT"],
        ),
        dispositions=tuple(dispositions),
    )
    fields.update(overrides)
    return IngestionReceiptV2(**fields)


def receipt_text(payload_text: str, **kwargs: object) -> bytes:
    return canonical_receipt_v2_text(receipt_for(payload_text, **kwargs)).encode("utf-8")
