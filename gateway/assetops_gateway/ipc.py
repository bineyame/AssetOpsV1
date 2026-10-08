"""The authenticated local host-to-gateway channel (S2-01b phase 2).

`D-2026-10-08-s2-local-gateway-snapshot-transfer`: the Lab host hands the
gateway process the exact registered snapshot bytes, their claimed references
and public device reports over bounded local IPC. A loopback address or a pipe
name alone is not an authenticated peer, so every connection first passes a
mutual HMAC-SHA256 challenge over a protected local credential: 32 random bytes
the gateway creates once, owner-only, beside its ledger. A peer without that
credential cannot complete the handshake and no request of its is read. Neither
side sends anything before both have proved the key.

Wire: the transport is `multiprocessing.connection` (a Windows named pipe or a
Unix socket), used ONLY through `send_bytes`/`recv_bytes`, never its pickling
`send`/`recv`. Each message is one canonical-JSON object bounded by
`MAX_MESSAGE_BYTES`; an over-long message ends the connection. Requests name an
op from `OPS` and nothing else is dispatched. The credential is a local
publisher credential only - it is not, and implies nothing about, the S2-02
upload credential.

This module is stdlib plus `assetops_contracts`; the client half is what the Lab
host imports, so the host never touches the ledger or the service directly.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import threading
from dataclasses import dataclass
from multiprocessing.connection import Client, Connection, Listener, answer_challenge, deliver_challenge
from pathlib import Path
from typing import Any

PROTOCOL_ID = "assetops.gateway-local-ipc"
PROTOCOL_VERSION = 1
#: One request or response. A full-day Kobo run's stage read is about 1 MiB.
MAX_MESSAGE_BYTES = 16 * 1024 * 1024
CREDENTIAL_BYTES = 32
OPS = ("identity", "activate", "admit", "seal", "run_stage")
#: Keys a request may carry, per op. Anything else is refused unread.
REQUEST_BODY_KEYS: dict[str, frozenset[str]] = {
    "identity": frozenset(),
    "activate": frozenset({"snapshot_text", "claimed"}),
    "admit": frozenset({"snapshot_sha256", "lab_run_ref", "reports"}),
    "seal": frozenset(),
    "run_stage": frozenset({"lab_run_ref"}),
}
CLAIMED_KEYS = frozenset(
    {
        "snapshot_sha256",
        "foundation_revision_id",
        "foundation_version",
        "binding_set_id",
        "binding_set_revision_id",
        "binding_set_version",
    }
)


class GatewayUnavailable(RuntimeError):
    """No authenticated gateway answered: not running, wrong credential, or
    the channel broke mid-request. The caller fails closed."""


class GatewayRequestRefused(RuntimeError):
    """The gateway answered and refused the request, with its typed reason."""

    def __init__(self, kind: str, field: str | None, detail: str) -> None:
        self.kind, self.field, self.detail = kind, field, detail
        super().__init__(f"{kind}" + (f" at {field}" if field else "") + f": {detail}")


def default_address(state_dir: Path, gateway_id: str) -> str:
    if sys.platform == "win32":
        return rf"\\.\pipe\assetops-gateway-{gateway_id}"
    return str(Path(state_dir) / "gateway.sock")


def ensure_credential(path: Path) -> bytes:
    """Create the credential once (owner-only, exclusive create), then read it."""
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, "w", encoding="ascii") as handle:
                handle.write(secrets.token_hex(CREDENTIAL_BYTES))
    return read_credential(path)


def read_credential(path: Path) -> bytes:
    try:
        text = Path(path).read_text(encoding="ascii").strip()
        key = bytes.fromhex(text)
    except (OSError, ValueError) as error:
        raise GatewayUnavailable(f"the local gateway credential is unreadable: {error}") from error
    if len(key) != CREDENTIAL_BYTES:
        raise GatewayUnavailable("the local gateway credential has the wrong length")
    return key


def _canonical(document: Any) -> bytes:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _family(address: str) -> str:
    return "AF_PIPE" if address.startswith("\\\\.\\pipe\\") else "AF_UNIX"


# --- client (imported by the Lab host) -------------------------------------------


@dataclass(frozen=True)
class GatewayLink:
    """How the Lab host reaches its colocated gateway. One connection per call."""

    address: str
    credential_file: Path

    def call(self, op: str, body: dict[str, Any] | None = None) -> Any:
        if op not in OPS:
            raise ValueError(f"unknown gateway op {op!r}")
        key = read_credential(self.credential_file)
        request = _canonical({"protocol": PROTOCOL_ID, "version": PROTOCOL_VERSION, "op": op, "body": body or {}})
        if len(request) > MAX_MESSAGE_BYTES:
            raise ValueError("request exceeds the channel bound")
        try:
            # Client() answers the gateway's challenge, then challenges the
            # gateway in turn: the host also learns it reached the real gateway.
            connection = Client(self.address, family=_family(self.address), authkey=key)
        except Exception as error:  # noqa: BLE001 - every failure here is "unavailable"
            raise GatewayUnavailable(f"no authenticated gateway at {self.address}: {error}") from error
        try:
            connection.send_bytes(request)
            raw = connection.recv_bytes(MAX_MESSAGE_BYTES)
        except (OSError, EOFError) as error:
            raise GatewayUnavailable(f"the gateway channel broke: {error}") from error
        finally:
            connection.close()
        response = json.loads(raw.decode("utf-8"))
        if response.get("ok") is True:
            return response["body"]
        raise GatewayRequestRefused(response.get("kind", "REFUSED"), response.get("field"), response.get("detail", ""))


# --- server (run by `python -m assetops_gateway serve`) ---------------------------


class GatewayServer:
    """Serves one `GatewayService` over the authenticated channel.

    A thread per connection does the handshake and reads with bounds; the
    service itself is driven under one lock, so the ledger keeps its single
    writer regardless of how many hosts connect.
    """

    def __init__(self, service: Any, reader_path: Path, address: str, credential: bytes) -> None:
        self._service = service
        self._reader_path = Path(reader_path)
        self._address = address
        self._credential = credential
        self._lock = threading.Lock()
        self._listener = Listener(address, family=_family(address))  # no authkey: we challenge per thread

    @property
    def address(self) -> str:
        return self._address

    def serve_forever(self) -> None:
        while True:
            try:
                connection = self._listener.accept()
            except OSError:
                continue
            threading.Thread(target=self._serve, args=(connection,), daemon=True).start()

    def close(self) -> None:
        self._listener.close()

    def _serve(self, connection: Connection) -> None:
        try:
            deliver_challenge(connection, self._credential)
            answer_challenge(connection, self._credential)
        except Exception:  # noqa: BLE001 - an unauthenticated peer gets nothing
            connection.close()
            return
        try:
            raw = connection.recv_bytes(MAX_MESSAGE_BYTES)
            response = self.handle(raw)
            connection.send_bytes(_canonical(response))
        except (OSError, EOFError):
            pass
        finally:
            connection.close()

    def handle(self, raw: bytes) -> dict[str, Any]:
        from assetops_gateway.service import GatewayRefused
        from assetops_gateway.snapshot import SnapshotRefused

        try:
            request = json.loads(raw.decode("utf-8"))
            op, body = _request(request)
            with self._lock:
                return {"ok": True, "body": self._dispatch(op, body)}
        except _BadRequest as bad:
            return {"ok": False, "kind": "BAD_REQUEST", "field": bad.field, "detail": bad.detail}
        # SnapshotRefused is a ValueError: it must be matched first.
        except SnapshotRefused as refused:
            return {"ok": False, "kind": refused.kind, "field": refused.field, "detail": refused.detail}
        except (ValueError, UnicodeDecodeError) as error:
            return {"ok": False, "kind": "BAD_REQUEST", "field": None, "detail": str(error)}
        except GatewayRefused as refused:
            return {"ok": False, "kind": refused.kind, "field": None, "detail": refused.detail}
        except Exception as error:  # noqa: BLE001 - typed, so the host fails closed knowingly
            return {"ok": False, "kind": "GATEWAY_ERROR", "field": None, "detail": type(error).__name__}

    def _dispatch(self, op: str, body: dict[str, Any]) -> Any:
        from assetops_gateway.service import MAX_ADMISSION_CHUNK, GatewayReader
        from assetops_gateway.snapshot import ClaimedReferences

        service = self._service
        if op == "identity":
            return service.identity()
        if op == "activate":
            claimed = body["claimed"]
            if not isinstance(claimed, dict) or set(claimed) != CLAIMED_KEYS:
                raise _BadRequest("claimed", f"exactly {sorted(CLAIMED_KEYS)} are wanted")
            verified = service.activate(body["snapshot_text"], ClaimedReferences(**claimed))
            return {"snapshot_sha256": verified.snapshot_sha256}
        if op == "admit":
            reports = body["reports"]
            if not isinstance(reports, list) or not all(isinstance(r, str) for r in reports):
                raise _BadRequest("reports", "a list of report texts is wanted")
            if len(reports) > MAX_ADMISSION_CHUNK:
                raise _BadRequest("reports", f"at most {MAX_ADMISSION_CHUNK} reports per request")
            admissions = service.admit_texts(
                reports, snapshot_sha256=_str(body, "snapshot_sha256"), lab_run_ref=_str(body, "lab_run_ref")
            )
            return {"admissions": [a.__dict__ for a in admissions]}
        if op == "seal":
            return {"batch_ids": service.seal()}
        if op == "run_stage":
            with GatewayReader(self._reader_path) as reader:
                stage = reader.run_stage(_str(body, "lab_run_ref"))
            return stage_document(stage)
        raise _BadRequest("op", f"unknown op {op!r}")


class _BadRequest(Exception):
    def __init__(self, field: str, detail: str) -> None:
        self.field, self.detail = field, detail


def _str(body: dict[str, Any], key: str) -> str:
    value = body.get(key)
    if not isinstance(value, str) or not value:
        raise _BadRequest(key, "a non-empty string is wanted")
    return value


def _request(request: object) -> tuple[str, dict[str, Any]]:
    if not isinstance(request, dict) or set(request) != {"protocol", "version", "op", "body"}:
        raise _BadRequest("request", "exactly protocol, version, op and body are wanted")
    if request["protocol"] != PROTOCOL_ID or request["version"] != PROTOCOL_VERSION:
        raise _BadRequest("protocol", "unsupported channel protocol")
    op, body = request["op"], request["body"]
    if op not in REQUEST_BODY_KEYS:
        raise _BadRequest("op", f"unknown op {op!r}")
    if not isinstance(body, dict) or set(body) != REQUEST_BODY_KEYS[op]:
        raise _BadRequest("body", f"op {op} takes exactly {sorted(REQUEST_BODY_KEYS[op])}")
    return op, body


def stage_document(stage: Any) -> dict[str, Any]:
    """`RunStage` as plain JSON for the channel."""
    return {
        "lab_run_ref": stage.lab_run_ref,
        "sequence_epoch": stage.sequence_epoch,
        "envelopes": [dict(e.__dict__) for e in stage.envelopes],
        "batches": [{**b.__dict__, "message_ids": list(b.message_ids)} for b in stage.batches],
        "holds": [dict(h.__dict__) for h in stage.holds],
        "queue_depth_by_state": dict(stage.queue_depth_by_state),
    }

