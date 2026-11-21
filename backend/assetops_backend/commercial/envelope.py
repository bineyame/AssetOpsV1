"""3A6 fix round r5 (spec §2.12; D-3A6.23, D-3A6.25): every upload parse runs in a fresh child process under hard
OS limits.

The step that turns upload bytes into rows or a batch object (`SourceReader.read` for every reader, `canonical-json-v1`
included, and admission's `split_file`) runs only here, in a short-lived child forked from a forkserver that has
preloaded the pure contracts package. The child sets `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_FSIZE` and `RLIMIT_CORE`
before it reads a byte; the parent waits a bounded wall time and takes a bounded result back. Any breach refuses the
file with `NATIVE_TOO_LARGE`, and the log names the cause with no file content. There is no in-process mode and no
setting that turns the envelope off: production builds it from `DEFAULT_LIMITS` only (tests may lower the limits).
Linux only (`resource`, forkserver); elsewhere the constructor raises.
"""
from __future__ import annotations

import io
import json
import logging
import multiprocessing
import os
import pickle
import signal
import sys
import threading
import time
from dataclasses import astuple, dataclass, fields
from multiprocessing import forkserver, popen_forkserver, reduction, spawn, util
from multiprocessing.context import ForkServerProcess
from multiprocessing.context import set_spawning_popen as _spawning
from types import MappingProxyType

from assetops_backend.commercial.readers import READERS, LayoutReader, ReadContext, ReadResult, SourceReader
from assetops_contracts.canonical import CanonicalRefused
from assetops_contracts.canonical.records_v1 import MAX_RECORDS

_LOG = logging.getLogger("assetops.commercial.envelope")


@dataclass(frozen=True)
class EnvelopeLimits:
    memory_bytes: int = 512 * 2**20  # RLIMIT_AS, soft = hard
    cpu_seconds: int = 6  # RLIMIT_CPU soft; hard = soft + 1
    wall_seconds: float = 12.0  # the parent's wait, then SIGKILL
    result_bytes: int = 32 * 2**20  # the pickled answer, checked in the child and by recv_bytes(maxlength)
    concurrent: int = 2  # children at once per ParseEnvelope (one per server process)

    def __post_init__(self) -> None:
        for name, value in zip((f.name for f in fields(self)), astuple(self)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not value > 0:
                raise ValueError(f"envelope limit {name} must be > 0")


DEFAULT_LIMITS = EnvelopeLimits()


@dataclass(frozen=True)
class BoundedRead:
    result: ReadResult  # `refused` back as MappingProxyType
    split: tuple[list[str], list[tuple[int, list[str]]]] | None  # admission only


def reader_spec(reader: SourceReader) -> tuple:
    """What the child rebuilds the reader from: a registered reader by its ID, or a profile reader by its text."""
    if READERS.get(reader.id) is reader:
        return ("builtin", reader.id)
    if isinstance(reader, LayoutReader) and reader.profile is not None:
        text, version = reader.profile
        return ("profile", text, version)
    raise TypeError(f"the envelope cannot rebuild reader {type(reader).__name__}")


def _rebuild(spec: tuple) -> SourceReader:
    if spec[0] == "builtin":
        return READERS[spec[1]]
    from assetops_contracts.native import compile_profile
    text, version = spec[1], spec[2]
    return LayoutReader(compile_profile(json.loads(text), version))


def _too_many_records(obj: object) -> CanonicalRefused | None:
    """Fix round r5 (spec §2.12 step 3): `parse_batch` refuses a count past `MAX_RECORDS` before it walks the
    records (records_v1.py), but the parent would still unpickle the whole list. A list longer than
    `MAX_RECORDS + 1` is answered here with what `parse_batch` says of its first `MAX_RECORDS + 1` records, so the
    verdict is the in-process one (an envelope field's refusal first, else `CANONICAL_RANGE batch.records`)."""
    if not isinstance(obj, dict) or not isinstance(obj.get("records"), list) or len(obj["records"]) <= MAX_RECORDS + 1:
        return None
    from assetops_contracts.canonical import parse_batch
    try:
        parse_batch({**obj, "records": obj["records"][:MAX_RECORDS + 1]})
    except CanonicalRefused as refused:
        return refused
    return CanonicalRefused("CANONICAL_RANGE", "batch.records")  # unreachable: the count alone refuses


def _child(conn, spec: tuple, data: bytes, context: ReadContext, split: bool, limits: EnvelopeLimits) -> None:
    """The parse, in a fresh child. No database handle, no key, no store: only the bytes and the reader's spec."""
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (limits.memory_bytes, limits.memory_bytes))
    resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds + 1))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    answer: tuple
    try:
        reader = _rebuild(spec)
        if spec[0] == "profile" and reader.id != spec[3]:
            raise LookupError("the rebuilt reader's id differs")
        read = reader.read(data, context=context)
        many = _too_many_records(read.obj)
        if many is not None:
            raise many
        cut = None
        if split:
            from assetops_contracts.native import split_file
            cut = split_file(reader.layout, data)
        answer = ("ok", read.obj, read.rows, dict(read.refused), sorted(read.personal_paths), cut)
        del read
    except CanonicalRefused as refused:
        answer = ("refused", refused.code, refused.path)
    except MemoryError:
        answer = ("breach", "memory")
    except Exception as error:  # noqa: BLE001 - the name only crosses back; the parent raises a 500
        answer = ("error", type(error).__name__)
    try:
        blob = pickle.dumps(answer, protocol=5)
    except MemoryError:
        blob = pickle.dumps(("breach", "memory"), protocol=5)
    del answer
    if len(blob) > limits.result_bytes:
        blob = pickle.dumps(("breach", "result"), protocol=5)
    try:
        conn.send_bytes(blob)
    except (OSError, MemoryError):
        pass  # the parent stopped waiting (or memory ran out); it reads EOF and refuses
    finally:
        conn.close()


class ParseEnvelope:
    """One per server process (`default_envelope()`); tests may build one with lower limits."""

    def __init__(self, limits: EnvelopeLimits = DEFAULT_LIMITS) -> None:
        if not sys.platform.startswith("linux"):
            raise RuntimeError("the parse envelope needs Linux (resource limits and a forkserver)")
        if not isinstance(limits, EnvelopeLimits):
            raise TypeError("limits must be EnvelopeLimits")
        self.limits = limits
        self._slots = threading.BoundedSemaphore(limits.concurrent)
        self._count = threading.Lock()
        self._active = 0
        self.peak_active = 0

    def read(self, reader: SourceReader, data: bytes, context: ReadContext, *, split: bool = False) -> BoundedRead:
        spec = reader_spec(reader)
        data = bytes(data)
        with self._slots:  # an upload waits for a slot; it is never refused for waiting
            with self._count:
                self._active += 1
                self.peak_active = max(self.peak_active, self._active)
            try:
                answer, cause = self._run(spec, reader.id, data, context, split)
            finally:
                with self._count:
                    self._active -= 1
        if cause is None and answer[0] == "breach":
            cause = answer[1]
        if cause is not None:
            _LOG.warning("upload parse refused by the envelope",
                         extra={"cause": cause, "reader": reader.id, "bytes": len(data),
                                "tenant": context.tenant_code})
            raise CanonicalRefused("NATIVE_TOO_LARGE", "json")
        if answer[0] == "refused":
            raise CanonicalRefused(answer[1], answer[2])
        if answer[0] == "ok":
            _, obj, rows, refused, personal, cut = answer
            return BoundedRead(ReadResult(obj, rows, frozenset(personal), MappingProxyType(refused)), cut)
        raise RuntimeError(f"parse failed in the envelope: {answer[1] if len(answer) > 1 else answer[0]}")

    def _run(self, spec: tuple, reader_id: str, data: bytes, context: ReadContext,
             split: bool) -> tuple[tuple, str | None]:
        limits = self.limits
        ctx = _context()
        receive, send = ctx.Pipe(duplex=False)
        process = _process(_child, (send, _with_id(spec, reader_id), data, context, split, limits))
        started = time.monotonic()
        answer: tuple = ("error", "none")
        cause: str | None = None
        try:
            process.start()
            send.close()
            if not receive.poll(limits.wall_seconds):
                process.kill()
                cause = "wall"
            else:
                try:
                    answer = pickle.loads(receive.recv_bytes(maxlength=limits.result_bytes + 4096))
                except OSError:
                    cause = "result"
                except EOFError:
                    process.join(1)
                    code = process.exitcode
                    if code == -signal.SIGXCPU or (code == -signal.SIGKILL
                                                   and time.monotonic() - started >= limits.cpu_seconds):
                        cause = "cpu"
                    else:
                        cause = "crash"
        finally:
            send.close()
            process.join(1)
            if process.is_alive():
                process.kill()
                process.join()
            process.close()
            receive.close()
        return answer, cause


def _with_id(spec: tuple, reader_id: str) -> tuple:
    """A profile spec carries the parent's reader ID, so the child refuses to run a reader that rebuilt otherwise."""
    return spec if spec[0] == "builtin" else (*spec, reader_id)


class _Launcher(popen_forkserver.Popen):
    """The stdlib's forkserver launch, less the parent's `__main__`: a spawned child re-runs the parent's main
    script (`init_main_from_path`) before its target, which in a server or a test runner imports the whole program
    into every parse child. The child needs only `sys.path`, the working directory and its target."""

    def _launch(self, process_obj) -> None:
        prep_data = spawn.get_preparation_data(process_obj._name)
        prep_data.pop("init_main_from_path", None)
        prep_data.pop("init_main_from_name", None)
        buf = io.BytesIO()
        _spawning(self)
        try:
            reduction.dump(prep_data, buf)
            reduction.dump(process_obj, buf)
        finally:
            _spawning(None)
        self.sentinel, w = forkserver.connect_to_new_process(self._fds)
        _parent_w = os.dup(w)
        self.finalizer = util.Finalize(self, util.close_fds, (_parent_w, self.sentinel))
        with io.FileIO(w, "wb", closefd=True) as f:  # the launch pipe to the child
            f.write(buf.getbuffer())
        self.pid = forkserver.read_signed(self.sentinel)


_CONTEXT = None
_CONTEXT_LOCK = threading.Lock()
_DEFAULT: ParseEnvelope | None = None


def _context():
    global _CONTEXT
    with _CONTEXT_LOCK:
        if _CONTEXT is None:
            ctx = multiprocessing.get_context("forkserver")
            ctx.set_forkserver_preload(["assetops_contracts.native"])  # the pure contracts package only
            _CONTEXT = ctx
        return _CONTEXT


def _process(target, args):
    """A forkserver child launched by `_Launcher`."""
    return _Child(target=target, args=args, daemon=True)


def default_envelope() -> ParseEnvelope:
    """The one shared envelope of this process, from `DEFAULT_LIMITS` (its only production construction)."""
    global _DEFAULT
    with _CONTEXT_LOCK:
        if _DEFAULT is None:
            _DEFAULT = ParseEnvelope(DEFAULT_LIMITS)
        return _DEFAULT


def _launcher_for(process_obj) -> _Launcher:
    _context()  # the preload is set before the forkserver first starts
    return _Launcher(process_obj)


class _Child(ForkServerProcess):
    """A forkserver process launched by `_Launcher` (multiprocessing calls the class's launch hook)."""


_Child._Popen = staticmethod(_launcher_for)  # the stdlib's hook name; set here so no call site spells it
