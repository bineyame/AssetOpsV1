"""TEL-02 read-only Modbus TCP client against an in-test stdlib server (no pymodbus)."""

from __future__ import annotations

import socket
import socketserver
import struct
import sys
import threading
import time
from pathlib import Path
from typing import Callable

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import gx2_rows, profile_document, row_document  # noqa: E402

from assetops_field.aggregate import PollOutcome  # noqa: E402
from assetops_field.modbus_tcp import (  # noqa: E402
    ModbusTcpClient,
    ReadResult,
    WriteForbidden,
    classify,
    requests_for,
)
from assetops_field.profile import parse_profile  # noqa: E402

PROFILE = parse_profile(profile_document())
PV, SOC = PROFILE.rows

Reply = Callable[[bytes], "bytes | None"]


class ScriptedServer:
    """Records every byte received; answers each request frame from `reply(frame)` (None = stay silent)."""

    def __init__(self, reply: Reply) -> None:
        self.received = bytearray()
        self.frames: list[bytes] = []
        self.reply = reply
        owner = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                buffer = b""
                while True:
                    try:
                        chunk = self.request.recv(4096)
                    except OSError:
                        return
                    if not chunk:
                        return
                    owner.received += chunk
                    buffer += chunk
                    while len(buffer) >= 7:
                        length = struct.unpack(">H", buffer[4:6])[0]
                        if len(buffer) < 6 + length:
                            break
                        frame, buffer = buffer[:6 + length], buffer[6 + length:]
                        owner.frames.append(frame)
                        answer = owner.reply(frame)
                        if answer is not None:
                            self.request.sendall(answer)

        socketserver.ThreadingTCPServer.allow_reuse_address = False
        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def serve():
    servers: list[ScriptedServer] = []
    clients: list[ModbusTcpClient] = []

    def start(reply: Reply, timeout_s: float = 1.0) -> tuple[ScriptedServer, ModbusTcpClient]:
        server = ScriptedServer(reply)
        client = ModbusTcpClient("127.0.0.1", server.port, timeout_s=timeout_s)
        servers.append(server)
        clients.append(client)
        return server, client

    yield start
    for client in clients:
        client.close()
    for server in servers:
        server.close()


def words_reply(words: list[int], *, tid_shift: int = 0, unit_shift: int = 0) -> Reply:
    def reply(frame: bytes) -> bytes:
        tid, _, _, unit = struct.unpack(">HHHB", frame[:7])
        function = frame[7]
        pdu = bytes([function, 2 * len(words)]) + struct.pack(f">{len(words)}H", *words)
        return struct.pack(">HHHB", (tid + tid_shift) % 65536, 0, len(pdu) + 1, (unit + unit_shift) % 256) + pdu
    return reply


def exception_reply(code: int) -> Reply:
    def reply(frame: bytes) -> bytes:
        tid, _, _, unit = struct.unpack(">HHHB", frame[:7])
        return struct.pack(">HHHBBB", tid, 0, 3, unit, frame[7] | 0x80, code)
    return reply


@pytest.mark.parametrize("function", [5, 6, 15, 16, 23])
def test_write_function_codes_raise_before_any_byte(serve, function):
    server, client = serve(words_reply([0]))
    with pytest.raises(WriteForbidden):
        client.read(1, function, 0, 1)
    time.sleep(0.05)
    assert bytes(server.received) == b"" and client._socket is None


@pytest.mark.parametrize(
    "unit, function, address, count, expected",
    [
        (1, 4, 0, 2, "00 01 00 00 00 06 01 04 00 00 00 02"),  # Figure 2a
        (1, 3, 0, 2, "00 01 00 00 00 06 01 03 00 00 00 02"),
        (1, 2, 0, 2, "00 01 00 00 00 06 01 02 00 00 00 02"),
        (1, 1, 0, 2, "00 01 00 00 00 06 01 01 00 00 00 02"),
        (100, 3, 808, 3, "00 01 00 00 00 06 64 03 03 28 00 03"),  # profile -1 PV, Q-T38
    ],
)
def test_request_frames_with_transaction_id_1(serve, unit, function, address, count, expected):
    server, client = serve(lambda frame: None, timeout_s=0.2)
    result = client.read(unit, function, address, count)
    assert result.request == bytes.fromhex(expected)
    assert bytes(server.received) == bytes.fromhex(expected)


def test_figure_2b_response_gives_words(serve):
    figure_2b = bytes.fromhex("00 01 00 00 00 07 01 04 04 00 7B FF 9C")
    _, client = serve(lambda frame: figure_2b)
    result = client.read(1, 4, 0, 2)
    assert (result.kind, result.words, result.response) == ("WORDS", (0x007B, 0xFF9C), figure_2b)


def test_figure_2c_exception_gives_exception_02(serve):
    figure_2c = bytes.fromhex("00 01 00 00 00 03 01 84 02")
    _, client = serve(lambda frame: figure_2c)
    result = client.read(1, 4, 0, 2)
    assert (result.kind, result.exception_code) == ("EXCEPTION", 2)


def test_transaction_ids_increment_on_one_persistent_connection(serve):
    server, client = serve(words_reply([1, 2, 3]))
    for _ in range(3):
        assert client.read(100, 3, 808, 3).kind == "WORDS"
    assert [struct.unpack(">H", f[:2])[0] for f in server.frames] == [1, 2, 3]
    client._tid = 65535
    client.read(100, 3, 808, 3)
    client.read(100, 3, 808, 3)
    assert [struct.unpack(">H", f[:2])[0] for f in server.frames[-2:]] == [65535, 0]


@pytest.mark.parametrize("kind, reply", [("TID_MISMATCH", words_reply([1, 2, 3], tid_shift=1)),
                                         ("UNIT_MISMATCH", words_reply([1, 2, 3], unit_shift=1))])
def test_tid_and_unit_mismatch_are_no_answer_and_reconnect(serve, kind, reply):
    _, client = serve(reply)
    result = client.read(100, 3, 808, 3)
    assert (result.kind, result.no_answer) == ("NO_ANSWER", kind)
    assert result.response is not None and client._socket is None
    assert classify([result], PV) == (PollOutcome.NO_ANSWER, None)


def test_a_silent_server_times_out_and_the_client_sends_nothing_more(serve):
    server, client = serve(lambda frame: None, timeout_s=0.3)
    started = time.monotonic()
    result = client.read(100, 3, 808, 3)
    elapsed = time.monotonic() - started
    assert (result.kind, result.no_answer, result.response) == ("NO_ANSWER", "TIMEOUT", None)
    assert 0.25 <= elapsed < 1.0
    time.sleep(0.3)
    assert len(server.frames) == 1 and len(server.received) == 12


def test_a_closed_port_is_no_answer():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    result = ModbusTcpClient("127.0.0.1", port, timeout_s=5.0).read(1, 3, 0, 1)
    assert result.kind == "NO_ANSWER" and result.no_answer in ("REFUSED", "TIMEOUT")


def test_reconnects_on_the_next_read_after_no_answer(serve):
    answers = iter([None, "words"])

    def reply(frame: bytes):
        return words_reply([7])(frame) if next(answers) else None

    _, client = serve(reply, timeout_s=0.2)
    assert client.read(100, 3, 843, 1).no_answer == "TIMEOUT"
    assert client.read(100, 3, 843, 1).words == (7,)


@pytest.mark.parametrize(
    "code, outcome",
    [(0x01, PollOutcome.CONFIG_FAULT), (0x02, PollOutcome.NO_VALUE), (0x03, PollOutcome.CONFIG_FAULT),
     (0x04, PollOutcome.FAILED), (0x06, PollOutcome.FAILED), (0x0A, PollOutcome.NO_ANSWER),
     (0x0B, PollOutcome.NO_ANSWER)],
)
def test_exception_codes_map_through_classify(serve, code, outcome):
    _, client = serve(exception_reply(code))
    result = client.read(100, 3, 808, 3)
    assert (result.kind, result.exception_code) == ("EXCEPTION", code)
    assert classify([result], PV) == (outcome, None)


def test_classify_values_sentinels_and_word_count_faults():
    ok = ReadResult("WORDS", words=(1000, 1, 2))
    outcome, decoded = classify([ok], PV)
    assert outcome is PollOutcome.VALUE and str(decoded.value) == "1003/1000"
    outcome, decoded = classify([ReadResult("WORDS", words=(1000, 0, 0xFFFF))], PV)
    assert outcome is PollOutcome.NO_VALUE and decoded.kind == "SENTINEL"
    assert classify([ReadResult("WORDS", words=(1, 2))], PV) == (PollOutcome.CONFIG_FAULT, None)
    status = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE")).rows[1]
    assert classify([ReadResult("WORDS", words=(9,))], status) == (PollOutcome.CONFIG_FAULT, None)
    assert classify([ReadResult("WORDS", words=(2,))], status)[1].state == "RUNNING"


def test_requests_for_contiguous_and_split_rows():
    assert requests_for(PV) == [(100, 3, 808, 3)]
    assert requests_for(SOC) == [(100, 3, 843, 1)]
    block = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE")).rows[2]
    assert requests_for(block) == [(101, 3, 1002, 2)]
    gap = row_document(registers=[
        {"unit_id": 100, "function": 3, "address": 808, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 810, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 4, "address": 811, "type": "uint16", "word_order": "BIG"}])
    split = parse_profile(profile_document(rows=[gap])).rows[0]
    assert requests_for(split) == [(100, 3, 808, 1), (100, 3, 810, 1), (100, 4, 811, 1)]


def test_classify_precedence_across_several_requests():
    gap = row_document(registers=[
        {"unit_id": 100, "function": 3, "address": 808, "type": "uint16", "word_order": "BIG"},
        {"unit_id": 100, "function": 3, "address": 810, "type": "uint16", "word_order": "BIG"}])
    row = parse_profile(profile_document(rows=[gap])).rows[0]
    words, sentinel = ReadResult("WORDS", words=(5,)), ReadResult("WORDS", words=(0xFFFF,))
    exc = lambda code: ReadResult("EXCEPTION", exception_code=code)  # noqa: E731
    silent = ReadResult("NO_ANSWER", no_answer="TIMEOUT")
    assert classify([words, words], row)[0] is PollOutcome.VALUE
    assert classify([words, sentinel], row)[0] is PollOutcome.NO_VALUE
    assert classify([exc(2), sentinel], row)[0] is PollOutcome.NO_VALUE
    assert classify([exc(4), exc(2)], row)[0] is PollOutcome.FAILED
    assert classify([exc(4), silent], row)[0] is PollOutcome.NO_ANSWER
    assert classify([exc(3), silent], row)[0] is PollOutcome.CONFIG_FAULT
    assert classify([words, ReadResult("WORDS", words=(1, 2))], row)[0] is PollOutcome.CONFIG_FAULT
