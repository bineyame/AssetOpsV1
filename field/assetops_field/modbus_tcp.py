"""Read-only Modbus TCP client (build spec TEL-02, 0.7, Q-T13, Q-T21, Q-T22).

One persistent connection; `read` is exactly one transaction and never retries
(the poller owns the single retry). Any function code outside 01-04 raises
`WriteForbidden` before a socket is opened or a byte is written. After any
`NO_ANSWER` the connection is dropped and reopened on the next read.

`classify` is the one place the 0.7 fault table is applied.
"""

from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass
from typing import Sequence

from assetops_field.aggregate import PollOutcome
from assetops_field.decode import Decoded, DecodeFault, decode_words
from assetops_field.profile import ProfileRow

READ_FUNCTIONS = frozenset({1, 2, 3, 4})
MAX_REGISTERS = 125  # FC 03/04 per request
MAX_BITS = 2000  # FC 01/02 per request
_MBAP = struct.Struct(">HHHB")  # transaction, protocol, length, unit


class WriteForbidden(ValueError):
    """A function code other than a read was asked for; nothing was sent."""


@dataclass(frozen=True)
class ReadResult:
    kind: str  # "WORDS" | "EXCEPTION" | "NO_ANSWER"
    words: tuple[int, ...] = ()
    exception_code: int | None = None
    no_answer: str | None = None  # "TIMEOUT" | "REFUSED" | "RESET" | "UNIT_MISMATCH" | "TID_MISMATCH"
    request: bytes = b""
    response: bytes | None = None


class _NoAnswer(Exception):
    def __init__(self, kind: str, received: bytes = b"") -> None:
        self.kind, self.received = kind, received


class ModbusTcpClient:
    def __init__(self, host: str, port: int, *, timeout_s: float = 1.0) -> None:
        self.host, self.port, self.timeout_s = host, port, timeout_s
        self._socket: socket.socket | None = None
        self._tid = 1

    def close(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            finally:
                self._socket = None

    def _next_tid(self) -> int:
        tid = self._tid
        self._tid = (self._tid + 1) % 65536
        return tid

    def read(self, unit_id: int, function: int, address: int, count: int) -> ReadResult:
        if function not in READ_FUNCTIONS:
            raise WriteForbidden(f"function code {function} is not a read; this client never writes")
        limit = MAX_REGISTERS if function in (3, 4) else MAX_BITS
        if not 0 <= unit_id <= 255 or not 0 <= address <= 65535 or not 1 <= count <= limit:
            raise ValueError(f"unit {unit_id}, address {address}, count {count} is not a valid read")
        tid = self._next_tid()
        request = _MBAP.pack(tid, 0, 6, unit_id) + struct.pack(">BHH", function, address, count)
        deadline = time.monotonic() + self.timeout_s
        received = b""
        try:
            connection = self._connect(deadline)
            try:
                connection.sendall(request)
            except OSError as error:
                raise _NoAnswer("RESET") from error
            header = self._receive(connection, _MBAP.size, deadline, b"")
            received = header
            r_tid, _protocol, length, r_unit = _MBAP.unpack(header)
            if length < 2:
                raise _NoAnswer("RESET", received)
            body = self._receive(connection, length - 1, deadline, received)
            received = header + body
            if r_tid != tid:
                raise _NoAnswer("TID_MISMATCH", received)
            if r_unit != unit_id:
                raise _NoAnswer("UNIT_MISMATCH", received)
        except _NoAnswer as no_answer:
            self.close()
            return ReadResult("NO_ANSWER", no_answer=no_answer.kind, request=request,
                              response=no_answer.received or None)
        return _parse_pdu(function, count, body, request, received, self)

    def _connect(self, deadline: float) -> socket.socket:
        if self._socket is not None:
            return self._socket
        try:
            connection = socket.create_connection((self.host, self.port), timeout=max(deadline - time.monotonic(), 0.001))
        except TimeoutError as error:
            raise _NoAnswer("TIMEOUT") from error
        except OSError as error:
            raise _NoAnswer("REFUSED") from error
        connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self._socket = connection
        return connection

    @staticmethod
    def _receive(connection: socket.socket, size: int, deadline: float, before: bytes) -> bytes:
        data = b""
        while len(data) < size:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _NoAnswer("TIMEOUT", before + data)
            connection.settimeout(remaining)
            try:
                chunk = connection.recv(size - len(data))
            except TimeoutError as error:
                raise _NoAnswer("TIMEOUT", before + data) from error
            except OSError as error:
                raise _NoAnswer("RESET", before + data) from error
            if not chunk:
                raise _NoAnswer("RESET", before + data)
            data += chunk
        return data


def _parse_pdu(function: int, count: int, pdu: bytes, request: bytes, response: bytes,
               client: ModbusTcpClient) -> ReadResult:
    code = pdu[0]
    if code == function | 0x80 and len(pdu) == 2:
        return ReadResult("EXCEPTION", exception_code=pdu[1], request=request, response=response)
    if code != function or len(pdu) < 2 or len(pdu) != 2 + pdu[1]:
        # A malformed answer leaves the stream unframed: treated as no answer (T1 question).
        client.close()
        return ReadResult("NO_ANSWER", no_answer="RESET", request=request, response=response)
    data = pdu[2:]
    if function in (3, 4):
        if len(data) % 2:
            client.close()
            return ReadResult("NO_ANSWER", no_answer="RESET", request=request, response=response)
        words = struct.unpack(f">{len(data) // 2}H", data)
    else:
        bits = [(data[i // 8] >> (i % 8)) & 1 for i in range(min(count, len(data) * 8))]
        words = tuple(bits)
    return ReadResult("WORDS", words=tuple(words), request=request, response=response)


def requests_for(row: ProfileRow) -> list[tuple[int, int, int, int]]:
    """`(unit_id, function, address, count)`: one request when the registers are contiguous, else one each."""
    registers = row.registers
    if not registers:
        raise ValueError(f"row {row.row_id} reads no registers")
    first = registers[0]
    contiguous = all(
        nxt.unit_id == first.unit_id and nxt.function == first.function and nxt.address == cur.address + cur.words
        for cur, nxt in zip(registers, registers[1:])
    )
    if contiguous and row.word_count <= MAX_REGISTERS:
        return [(first.unit_id, first.function, first.address, row.word_count)]
    return [(r.unit_id, r.function, r.address, r.words) for r in registers]


# The 0.7 table, one place.
_EXCEPTION_OUTCOME = {
    0x01: PollOutcome.CONFIG_FAULT,
    0x02: PollOutcome.NO_VALUE,
    0x03: PollOutcome.CONFIG_FAULT,
    0x04: PollOutcome.FAILED,
    0x06: PollOutcome.FAILED,
    0x0A: PollOutcome.NO_ANSWER,
    0x0B: PollOutcome.NO_ANSWER,
}
_PRECEDENCE = (PollOutcome.CONFIG_FAULT, PollOutcome.NO_ANSWER, PollOutcome.FAILED, PollOutcome.NO_VALUE)


def exception_outcome(code: int) -> PollOutcome:
    # Codes the 0.7 table does not name are FAILED: no sample, no retry (T1 question).
    return _EXCEPTION_OUTCOME.get(code, PollOutcome.FAILED)


def classify(results: Sequence[ReadResult], row: ProfileRow) -> tuple[PollOutcome, Decoded | None]:
    if len(results) != len(requests_for(row)):
        raise ValueError(f"row {row.row_id} needs {len(requests_for(row))} read results, got {len(results)}")
    outcomes = set()
    for result in results:
        if result.kind == "NO_ANSWER":
            outcomes.add(PollOutcome.NO_ANSWER)
        elif result.kind == "EXCEPTION":
            outcomes.add(exception_outcome(result.exception_code))
        elif result.kind != "WORDS":
            raise ValueError(f"unknown read result kind {result.kind!r}")
    for outcome in _PRECEDENCE:
        if outcome in outcomes:
            return outcome, None
    if any(len(result.words) != count for result, (_, _, _, count) in zip(results, requests_for(row))):
        return PollOutcome.CONFIG_FAULT, None  # a decode type mismatch: wrong word count
    words = [word for result in results for word in result.words]
    per_register, offset = [], 0
    for register in row.registers:
        per_register.append(words[offset:offset + register.words])
        offset += register.words
    try:
        decoded = decode_words(row, per_register)
    except DecodeFault:
        return PollOutcome.CONFIG_FAULT, None
    if decoded.kind == "SENTINEL":
        return PollOutcome.NO_VALUE, decoded
    return PollOutcome.VALUE, decoded
