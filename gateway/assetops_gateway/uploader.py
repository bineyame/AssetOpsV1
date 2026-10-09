"""Authenticated HTTPS delivery of sealed batches and diagnostics (S2-02 phase 2).

`D-2026-10-09-s2-pilot-gateway-upload-credential`: TLS plus an independently
provisioned opaque bearer credential per registered gateway, for Batch V2 and
GatewayDiagnosticsV1 alike.

- TLS only. A non-`https` server URL is refused when the configuration loads;
  there is no plaintext fallback. The server certificate is verified against the
  system store or the configured `ca_file`, hostname included.
- The secret lives in its own owner-only file (`aog1.<32 hex>.<43 urlsafe>`),
  read afresh for every pass so a rotated credential takes effect without a
  restart and without touching sealed bytes. It is never written to the SQLite
  ledger, a log line, an exception or an IPC answer: those carry only the
  redacted form `aog1.<selector>.<redacted>`.
- The request body is the exact sealed `payload_text` UTF-8 bytes, never
  re-serialized, so a retry sends byte-identical bytes.
- One batch is in flight at a time. A pass takes at most `batches_per_pass`
  due READY batches, oldest first; the Kobo run's ~245 batches drain over
  several passes. The service lock is held only for each short ledger
  transaction, never across the network call.

HTTP answers for `POST /api/ingestion/batches`:

- 200: COMPLETED Receipt V2. Verified (hash, batch ID, digest, scope, count,
  every ordinal's message ID) and persisted with the acknowledgements and the
  terminal states in ONE transaction. A mismatch is `RECEIPT_MISMATCH`: never
  acknowledged, READY again, the pass stops.
- 202: IN_PROGRESS Receipt V2, the decided prefix. Verified the same way;
  nothing terminal is stored and the same bytes are due again at once.
- 401/403: credential or scope. Not terminal for the batch: READY, the pass
  stops and the code is surfaced.
- 409/413/422: authenticated terminal whole-batch refusal: REFUSED, its
  envelopes DEAD_LETTER, code recorded.
- anything else, a timeout, a TLS or connection failure: READY with back-off,
  the pass stops. A crash after the server committed is recovered exactly this
  way: the same bytes are posted again and the server answers its durable
  receipt.

Stdlib plus `assetops_contracts` (through the service) only.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import re
import socket
import ssl
import stat
import sys
import threading
from contextlib import nullcontext
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.parse import quote, urlsplit

from assetops_gateway.service import GatewayRefused, ReceiptMismatch, verify_receipt

LOG = logging.getLogger("assetops_gateway.uploader")

UPLOAD_KEYS = frozenset(
    {"server_url", "upload_credential_file", "ca_file", "timeout_seconds", "batches_per_pass", "interval_seconds"}
)
REQUIRED_UPLOAD_KEYS = frozenset({"server_url", "upload_credential_file"})
BATCHES_ROUTE = "/api/ingestion/batches"
DIAGNOSTICS_ROUTE = "/api/gateways/{gateway_id}/diagnostics"
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_BATCHES_PER_PASS = 500
DIAGNOSTICS_PER_PASS = 20
TERMINAL_BATCH_STATUSES = (409, 413, 422)
CREDENTIAL_STATUSES = (401, 403)
_CREDENTIAL = re.compile(r"aog1\.([0-9a-f]{32})\.([A-Za-z0-9_-]{43})")
_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")


class UploadConfigInvalid(ValueError):
    """The `upload` configuration is unusable; the gateway refuses to start."""


class UploadCredentialInvalid(RuntimeError):
    """The upload credential file is missing, unreadable, mis-shaped or too open.

    Its message never contains the file's content."""

    code = "UPLOAD_CREDENTIAL_INVALID"


@dataclass(frozen=True)
class UploadConfig:
    server_url: str
    host: str
    port: int
    base_path: str
    upload_credential_file: Path
    ca_file: Path | None = None
    timeout_seconds: float = 10.0
    batches_per_pass: int = 50
    interval_seconds: float = 30.0


def parse_upload_config(raw: object, base: Path) -> UploadConfig:
    """Validate the `upload` block. Unknown keys and any non-https URL refuse."""
    if not isinstance(raw, dict) or not set(raw) <= UPLOAD_KEYS or not REQUIRED_UPLOAD_KEYS <= set(raw):
        raise UploadConfigInvalid(
            f"upload needs {sorted(REQUIRED_UPLOAD_KEYS)} and takes only {sorted(UPLOAD_KEYS)}"
        )
    url = raw["server_url"]
    if not isinstance(url, str):
        raise UploadConfigInvalid("upload.server_url must be a string")
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise UploadConfigInvalid("upload.server_url must be https: TLS is required, with no plaintext fallback")
    if not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise UploadConfigInvalid("upload.server_url must be https://host[:port][/path] only")
    try:
        port = parts.port or 443
    except ValueError as error:
        raise UploadConfigInvalid(f"upload.server_url port: {error}") from error

    def number(key: str, default: float, low: float, high: float, integer: bool = False) -> Any:
        value = raw.get(key, default)
        if type(value) not in ((int,) if integer else (int, float)) or not low <= value <= high:
            raise UploadConfigInvalid(f"upload.{key} must be {'an integer ' if integer else ''}in [{low}, {high}]")
        return value

    credential_file = raw["upload_credential_file"]
    ca_file = raw.get("ca_file")
    if not isinstance(credential_file, str) or (ca_file is not None and not isinstance(ca_file, str)):
        raise UploadConfigInvalid("upload file paths must be strings")
    return UploadConfig(
        server_url=url.rstrip("/"),
        host=parts.hostname,
        port=port,
        base_path=parts.path.rstrip("/"),
        upload_credential_file=(base / credential_file).resolve(),
        ca_file=None if ca_file is None else (base / ca_file).resolve(),
        timeout_seconds=float(number("timeout_seconds", 10.0, 0.1, 300.0)),
        batches_per_pass=number("batches_per_pass", 50, 1, MAX_BATCHES_PER_PASS, integer=True),
        interval_seconds=float(number("interval_seconds", 30.0, 0.05, 3600.0)),
    )


class UploadCredential:
    """The bearer secret. Its `str`/`repr` are the redacted form only."""

    __slots__ = ("_token", "selector")

    def __init__(self, token: str) -> None:
        match = _CREDENTIAL.fullmatch(token)
        if match is None:
            raise UploadCredentialInvalid("the upload credential is not aog1.<32 hex>.<43 urlsafe>")
        self._token = token
        self.selector = match.group(1)

    @property
    def redacted(self) -> str:
        return f"aog1.{self.selector}.<redacted>"

    def authorization(self) -> str:
        return f"Bearer {self._token}"

    def scrub(self, text: str) -> str:
        return text.replace(self._token, self.redacted)

    def __repr__(self) -> str:
        return f"UploadCredential({self.redacted})"

    __str__ = __repr__


def read_upload_credential(path: Path) -> UploadCredential:
    """Read the owner-only credential file. On POSIX a group/other-readable file
    refuses; on Windows the file's ACL is the operator's provisioning duty."""
    path = Path(path)
    try:
        if sys.platform != "win32" and stat.S_IMODE(os.stat(path).st_mode) & 0o077:
            raise UploadCredentialInvalid(f"{path} must be owner-only (0600)")
        text = path.read_text(encoding="ascii").strip()
    except UploadCredentialInvalid:
        raise
    except (OSError, UnicodeDecodeError) as error:
        raise UploadCredentialInvalid(f"the upload credential file is unreadable: {type(error).__name__}") from None
    return UploadCredential(text)


class _Transport(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _error_code(status: int, body: bytes) -> tuple[str, str]:
    """The server's typed code from `{"detail": {"code": ...}}`, else `HTTP_<status>`."""
    code, detail = f"HTTP_{status}", ""
    try:
        document = json.loads(body.decode("utf-8"))
        inner = document.get("detail") if isinstance(document, dict) else None
        if isinstance(inner, dict):
            if isinstance(inner.get("code"), str) and _CODE.fullmatch(inner["code"]):
                code = inner["code"]
            message = inner.get("message") or inner.get("detail") or ""
            detail = message if isinstance(message, str) else ""
    except (ValueError, UnicodeDecodeError, AttributeError):
        pass
    return code, detail[:500]


class Uploader:
    """Drives delivery passes over one `GatewayService`.

    `service_lock` is the lock every other writer of that service takes (the
    IPC server's), held only around each ledger call. `connect` is injectable
    for tests; by default it opens a verified TLS connection."""

    def __init__(
        self,
        service: Any,
        config: UploadConfig,
        *,
        service_lock: threading.Lock | None = None,
        connect: Callable[[], http.client.HTTPConnection] | None = None,
    ) -> None:
        self._service = service
        self._config = config
        self._service_lock = service_lock
        self._pass_lock = threading.Lock()
        self._connect = connect or self._tls_connection
        self.last_result: dict[str, Any] | None = None

    @property
    def config(self) -> UploadConfig:
        return self._config

    def _locked(self):
        return self._service_lock if self._service_lock is not None else nullcontext()

    def _call(self, method: str, *args: Any, **kwargs: Any) -> Any:
        with self._locked():
            return getattr(self._service, method)(*args, **kwargs)

    def _tls_connection(self) -> http.client.HTTPConnection:
        context = ssl.create_default_context(
            cafile=None if self._config.ca_file is None else str(self._config.ca_file)
        )
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return http.client.HTTPSConnection(
            self._config.host, self._config.port, timeout=self._config.timeout_seconds, context=context
        )

    def _post(self, credential: UploadCredential, path: str, body: bytes) -> tuple[int, bytes]:
        connection = self._connect()
        try:
            connection.request(
                "POST",
                self._config.base_path + path,
                body=body,
                headers={
                    "Authorization": credential.authorization(),
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                },
            )
            response = connection.getresponse()
            data = response.read(MAX_RESPONSE_BYTES + 1)
            if len(data) > MAX_RESPONSE_BYTES:
                raise _Transport("RESPONSE_TOO_LARGE")
            return response.status, data
        except _Transport:
            raise
        except ssl.SSLError:
            raise _Transport("TLS_ERROR") from None
        except (socket.timeout, TimeoutError):
            raise _Transport("TIMEOUT") from None
        except (OSError, http.client.HTTPException):
            raise _Transport("CONNECTION_FAILED") from None
        finally:
            connection.close()

    # --- passes ------------------------------------------------------------------

    def deliver(self, max_batches: int | None = None) -> dict[str, Any]:
        """One batch pass then one diagnostics pass, now."""
        result = {"batches": self.upload_pass(max_batches), "diagnostics": self.diagnostics_pass()}
        self.last_result = result
        return result

    def upload_pass(self, max_batches: int | None = None) -> dict[str, Any]:
        limit = self._config.batches_per_pass if max_batches is None else max_batches
        if not 1 <= limit <= MAX_BATCHES_PER_PASS:
            raise ValueError("max_batches out of range")
        summary: dict[str, Any] = {
            "attempted": 0, "acked": 0, "in_progress": 0, "refused": 0, "retrying": 0, "stopped": None,
            "credential": None,
        }
        with self._pass_lock:
            try:
                credential = read_upload_credential(self._config.upload_credential_file)
            except UploadCredentialInvalid as invalid:
                summary["stopped"] = invalid.code
                LOG.warning("upload pass stopped: %s", invalid)
                return summary
            summary["credential"] = credential.redacted
            for batch_id in self._call("due_batches", limit):
                summary["attempted"] += 1
                outcome = self._send_batch(credential, batch_id)
                summary[outcome[0]] += 1
                if outcome[1] is not None:
                    summary["stopped"] = outcome[1]
                    break
        return summary

    def _send_batch(self, credential: UploadCredential, batch_id: str) -> tuple[str, str | None]:
        """Returns (outcome key, stop code or None)."""
        try:
            payload = self._call("begin_attempt", batch_id)
        except GatewayRefused:
            return "retrying", None  # moved since the due list was read
        try:
            status, body = self._post(credential, BATCHES_ROUTE, payload.encode("utf-8"))
        except _Transport as failure:
            self._call("record_retry", batch_id, code=failure.code, retry_after_seconds=None)
            LOG.info("batch %s: %s; retrying the same bytes later", batch_id, failure.code)
            return "retrying", failure.code
        if status in (200, 202):
            try:
                text = body.decode("utf-8")
                if status == 200:
                    self._call("record_receipt", batch_id, text)
                    return "acked", None
                verify_receipt(text, self._call("batch_expectation", batch_id), complete=False)
            except (ReceiptMismatch, UnicodeDecodeError) as mismatch:
                self._call("record_retry", batch_id, code=ReceiptMismatch.code, retry_after_seconds=None)
                LOG.warning("batch %s: %s", batch_id, mismatch)
                return "retrying", ReceiptMismatch.code
            except Exception as error:  # noqa: BLE001 - never leave a batch IN_FLIGHT behind
                self._call("record_retry", batch_id, code="LOCAL_ERROR", retry_after_seconds=None)
                LOG.warning("batch %s: local error %s", batch_id, type(error).__name__)
                return "retrying", "LOCAL_ERROR"
            self._call("record_retry", batch_id, code=None, retry_after_seconds=0)
            return "in_progress", None
        code, detail = _error_code(status, body)
        detail = credential.scrub(detail)
        if status in TERMINAL_BATCH_STATUSES:
            self._call("record_batch_refusal", batch_id, http_status=status, code=code, detail=detail)
            LOG.warning("batch %s refused %s %s", batch_id, status, code)
            return "refused", None
        if status in CREDENTIAL_STATUSES:
            self._call("record_retry", batch_id, code=code, retry_after_seconds=0)
            LOG.warning("upload credential %s refused: %s %s", credential.redacted, status, code)
            return "retrying", code
        self._call("record_retry", batch_id, code=code, retry_after_seconds=None)
        return "retrying", code

    def diagnostics_pass(self, max_diagnostics: int = DIAGNOSTICS_PER_PASS) -> dict[str, Any]:
        summary: dict[str, Any] = {"attempted": 0, "acked": 0, "refused": 0, "retrying": 0, "stopped": None}
        with self._pass_lock:
            try:
                credential = read_upload_credential(self._config.upload_credential_file)
            except UploadCredentialInvalid as invalid:
                summary["stopped"] = invalid.code
                return summary
            for key in self._call("due_diagnostics", max_diagnostics):
                summary["attempted"] += 1
                outcome, stop = self._send_diagnostic(credential, key)
                summary[outcome] += 1
                if stop is not None:
                    summary["stopped"] = stop
                    break
        return summary

    def _send_diagnostic(self, credential: UploadCredential, key: tuple[str, str, int]) -> tuple[str, str | None]:
        try:
            payload, sha = self._call("begin_diagnostic", key)
        except GatewayRefused:
            return "retrying", None
        path = DIAGNOSTICS_ROUTE.format(gateway_id=quote(key[0], safe=""))
        try:
            status, body = self._post(credential, path, payload.encode("utf-8"))
        except _Transport as failure:
            self._call("diagnostic_failed", key, code=failure.code, retry_after_seconds=None)
            return "retrying", failure.code
        if status in (200, 201):
            try:
                answer = json.loads(body.decode("utf-8"))
                received_at = answer["received_at"]
                if answer["payload_sha256"] != sha or not isinstance(received_at, str) or not received_at:
                    raise ValueError("the answer names other bytes")
            except (ValueError, KeyError, TypeError, UnicodeDecodeError):
                self._call("diagnostic_failed", key, code=ReceiptMismatch.code, retry_after_seconds=None)
                return "retrying", ReceiptMismatch.code
            self._call("diagnostic_acked", key, server_received_at=received_at)
            return "acked", None
        code, _ = _error_code(status, body)
        if status in (409, 422):
            self._call("diagnostic_failed", key, code=code, retry_after_seconds=None, refused=True)
            return "refused", None
        if status in CREDENTIAL_STATUSES:
            self._call("diagnostic_failed", key, code=code, retry_after_seconds=0)
            return "retrying", code
        self._call("diagnostic_failed", key, code=code, retry_after_seconds=None)
        return "retrying", code

    # --- background --------------------------------------------------------------

    def start(self, stop: threading.Event) -> threading.Thread:
        """Deliver every `interval_seconds` until `stop` is set; failures wait for the next tick."""

        def run() -> None:
            while not stop.is_set():
                try:
                    self.deliver()
                except Exception as error:  # noqa: BLE001 - never stops the gateway
                    LOG.warning("delivery pass failed: %s", type(error).__name__)
                stop.wait(self._config.interval_seconds)

        thread = threading.Thread(target=run, daemon=True, name="gateway-uploads")
        thread.start()
        return thread
