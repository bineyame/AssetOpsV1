"""3A6 fix round r5 (spec §2.12 "Tests"; D-3A6.23, D-3A6.25): the parse envelope, E0 to E9. No database.

Each upload goes through `CommercialUploads.check` with the kobo profile admitted in memory, unless a test says
otherwise. Large files are built here by hand from the hand-written fixtures (W2), never by the code under test.
"""
from __future__ import annotations

import ast
import io
import json
import logging
import threading
import time
import zipfile
from dataclasses import replace
from pathlib import Path
from uuid import UUID

import pytest

from assetops_backend.commercial.envelope import DEFAULT_LIMITS, EnvelopeLimits, ParseEnvelope, reader_spec
from assetops_backend.commercial.readers import READERS, XLSX_MEDIA_TYPE, LayoutReader, ReadContext
from assetops_backend.commercial.uploads import UploadRefused
from assetops_contracts.canonical import CanonicalRefused
from assetops_contracts.native import compile_profile, split_file
from source_contracts import CONTRACT_CASES
from test_3a2_commercial_upload_service import T_SUBMIT, b_bill, counts, encode
from test_3a6_source_profiles import (BUDGET_EXPECTED, BUDGET_PROFILE, BUDGET_SAMPLE, KOBO_EXPECTED, KOBO_PROFILE,
                                      KOBO_SAMPLE, V1, make_world, people)

__all__ = ["people"]  # the module-scoped People fixture, shared with 3A6's file

BACKEND = Path(__file__).resolve().parents[1] / "assetops_backend"
LAKESIDE = "profile.lakeside-budget.v1"
SENTINEL = "SENTINEL-E9-QX7"
CAUSES = {"wall", "memory", "cpu", "result", "crash"}
CTX = ReadContext("acme", T_SUBMIT, False)


# --- files (built by hand from the fixtures) -------------------------------------------------------------------------

def _kobo_head() -> bytes:
    return b"".join(KOBO_SAMPLE.splitlines(keepends=True)[:3])


def kobo_10k(*, padded: bool) -> bytes:
    """10,000 kobo rows (unique refs, legitimate values). Padded: the Supplier ref at 120 characters and the unread
    Phone column filled, to about 8 MiB in all; both carry `SENTINEL`."""
    rows = []
    for n in range(10_000):
        supplier, phone = "fuel-co", "0712000001"
        if padded:
            supplier = (f"{SENTINEL}-{n:05d}-" + "s" * 120)[:120]
            phone = SENTINEL + "9" * 630
        rows.append(f"PL-{n:05d};{11 + n % 18:02d}/10/2026 09:00;KOBO-001;Diesel;{supplier};{phone};400;500,00;"
                    f"Invoiced\r\n".encode("cp1252"))
    data = _kobo_head() + b"".join(rows)
    assert len(data) <= 8 * 2**20
    return data


@pytest.fixture(scope="module")
def big() -> bytes:
    data = kobo_10k(padded=True)
    assert len(data) > 7.5 * 2**20
    return data


@pytest.fixture(scope="module")
def plain_10k() -> bytes:
    data = kobo_10k(padded=False)
    assert 700_000 < len(data) < 900_000
    return data


def lakeside_with_rows(xml: bytes) -> bytes:
    z = zipfile.ZipFile(io.BytesIO(BUDGET_SAMPLE))
    members = {n: z.read(n) for n in z.namelist()}
    sheet = members["xl/worksheets/sheet1.xml"]
    at = sheet.index(b"</sheetData>")
    members["xl/worksheets/sheet1.xml"] = sheet[:at] + xml + sheet[at:]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as w:
        for name, value in members.items():
            w.writestr(name, value)
    return out.getvalue()


# --- the world -------------------------------------------------------------------------------------------------------

def world(people, limits: EnvelopeLimits | None = None, *, lakeside: bool = False):
    envelope = ParseEnvelope(limits) if limits is not None else None
    w = make_world(people, envelope=envelope)
    w.profiles.admit(w.tid, w.ana, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED)
    if lakeside:
        w.profiles.admit(w.tid, w.ana, BUDGET_PROFILE, BUDGET_SAMPLE, BUDGET_EXPECTED)
    w.envelope = w.svc._envelope
    return w


def check(w, data: bytes, reader: str = V1, media: str = "text/csv") -> dict:
    return w.svc.check(w.tid, w.org, w.ana, data, reader_id=reader, media_type=media)


def too_large(w, data: bytes, caplog, reader: str = V1, media: str = "text/csv") -> UploadRefused:
    """The check refuses `NATIVE_TOO_LARGE` (422, its words), carries the cause, and logs nothing (D-3A6.29): returned."""
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(UploadRefused) as raised:
            check(w, data, reader, media)
    e = raised.value
    assert (e.status, e.code, e.params.get("code")) == (422, "UPLOAD_FILE_REFUSED", "NATIVE_TOO_LARGE"), (
        e.status, e.code, e.params)
    assert e.words["params"]["reason"] == (
        "this file is too large or too complex to read in one upload; split it and upload the parts.")
    assert not [r for r in caplog.records if r.name.startswith("assetops.commercial")]
    return e


def survives(w) -> None:
    """E6: the kobo fixture reads to its expected records through the same envelope."""
    reader = w.profiles.reader(w.tid, V1)
    got = w.envelope.read(reader, KOBO_SAMPLE, CTX).result
    assert got.obj["records"] == json.loads(KOBO_EXPECTED)
    assert counts(check(w, KOBO_SAMPLE))[0] == 4


# --- E0 --------------------------------------------------------------------------------------------------------------

def test_e0_default_limits_are_pinned() -> None:
    assert DEFAULT_LIMITS == EnvelopeLimits(512 * 2**20, 6, 12.0, 32 * 2**20, 2)
    for field in ("memory_bytes", "cpu_seconds", "wall_seconds", "result_bytes", "concurrent"):
        for bad in (0, -1):
            with pytest.raises(ValueError):
                replace(DEFAULT_LIMITS, **{field: bad})


def test_e0_production_builds_the_default_envelope_only(people) -> None:
    """No setting turns the envelope off or changes it: services built without one share `DEFAULT_LIMITS`'s."""
    w = make_world(people)
    assert w.svc._envelope is w.profiles._envelope and w.svc._envelope.limits == DEFAULT_LIMITS
    calls = [n for n in ast.walk(ast.parse((BACKEND / "commercial" / "envelope.py").read_text(encoding="utf-8")))
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "ParseEnvelope"]
    assert len(calls) == 1 and ast.unparse(calls[0]) == "ParseEnvelope(DEFAULT_LIMITS)"
    scanned = {p.relative_to(BACKEND).as_posix(): p.read_text(encoding="utf-8") for p in BACKEND.rglob("*.py")}
    assert {rel for rel, src in scanned.items() if "ParseEnvelope(" in src} == {"commercial/envelope.py"}
    source = scanned["commercial/envelope.py"]
    assert "environ" not in source and "getenv" not in source  # no setting reaches the limits
    assert "EnvelopeLimits(" not in "".join(src for rel, src in scanned.items() if rel != "commercial/envelope.py")


# --- E1 to E6 --------------------------------------------------------------------------------------------------------

def test_e1_memory(people, big, caplog) -> None:
    w = world(people, replace(DEFAULT_LIMITS, memory_bytes=80 * 2**20))
    record = too_large(w, big, caplog)
    assert record.cause in ("memory", "crash")
    survives(w)
    assert counts(check(world(people), big))[0] == 10_000  # the same file under DEFAULT_LIMITS reads


def test_e2_cpu(people, caplog) -> None:
    data = lakeside_with_rows(b"<row/>" * 499_000)
    reader = LayoutReader(compile_profile(json.loads(BUDGET_PROFILE), 1))
    started = time.process_time()
    reader.read(data, context=CTX)  # the precondition, in process: at least 1.3 s of CPU (never skipped)
    assert time.process_time() - started >= 1.3
    w = world(people, replace(DEFAULT_LIMITS, cpu_seconds=1, wall_seconds=30.0), lakeside=True)
    record = too_large(w, data, caplog, LAKESIDE, XLSX_MEDIA_TYPE)
    assert record.cause == "cpu"
    survives(w)


def test_e3_wall(people, big, caplog) -> None:
    w = world(people, replace(DEFAULT_LIMITS, wall_seconds=0.2))
    started = time.monotonic()
    record = too_large(w, big, caplog)
    assert time.monotonic() - started < 2.0
    assert record.cause == "wall"
    survives(w)


def test_e4_result(people, plain_10k, caplog) -> None:
    w = world(people, replace(DEFAULT_LIMITS, result_bytes=1 * 2**20))
    record = too_large(w, plain_10k, caplog)
    assert record.cause == "result"
    survives(w)


def test_e5_concurrency(people, big) -> None:
    w = world(people, replace(DEFAULT_LIMITS, concurrent=1))
    results: list = []

    def one() -> None:
        results.append(counts(check(w, big))[0])

    threads = [threading.Thread(target=one) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(120)
    assert results == [10_000, 10_000] and w.envelope.peak_active == 1


def test_e6_a_killed_child_is_refused_and_the_next_reads(people, big, caplog, monkeypatch) -> None:
    """E6 for the fifth breach: a child that dies without answering (killed by hand) refuses, and the next reads."""
    import assetops_backend.commercial.envelope as env
    import os
    import signal

    real = env._process

    def killed(target, args):
        process = real(target, args)

        def kill_once_started() -> None:  # by hand, as `kill -9` would: the child is mid-parse (about 1.5 s)
            while process._popen is None:
                time.sleep(0.001)
            os.kill(process.pid, signal.SIGKILL)
        threading.Thread(target=kill_once_started, daemon=True).start()
        return process

    w = world(people)
    monkeypatch.setattr(env, "_process", killed)
    record = too_large(w, big, caplog)
    assert record.cause == "crash"
    monkeypatch.setattr(env, "_process", real)
    survives(w)


def test_e6_admission_refuses_a_breach_with_the_same_words(people, caplog) -> None:
    """Admission's one envelope read (step 4, `split=True`): a breach is `ADMIT_SAMPLE_FILE` `NATIVE_TOO_LARGE`, in
    the same words; the next admission reads."""
    from assetops_backend.commercial.profiles import ProfileRefused
    from assetops_backend.i18n import render
    w = make_world(people, envelope=ParseEnvelope(replace(DEFAULT_LIMITS, wall_seconds=0.001)))
    with caplog.at_level(logging.WARNING), pytest.raises(ProfileRefused) as raised:
        w.profiles.check(w.tid, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED)
    assert (raised.value.code, raised.value.params) == ("ADMIT_SAMPLE_FILE", {"code": "NATIVE_TOO_LARGE"})
    assert render(raised.value.words) == ("The sample cannot be read: this file is too large or too complex to read "
                                          "in one upload; split it and upload the parts.")
    assert not [r for r in caplog.records if r.name.startswith("assetops.commercial")]
    w = make_world(people)
    assert w.profiles.check(w.tid, KOBO_PROFILE, KOBO_SAMPLE, KOBO_EXPECTED).sample_rows == 4


# --- E7 --------------------------------------------------------------------------------------------------------------

PARSE_CALLS = frozenset({"read_layout", "split_file", "xlsx_rows", "xlsx_sparse_rows", "loads_canonical"})
PARSE_HOMES = frozenset({"commercial/envelope.py", "commercial/readers.py"})
#: Known deviation (packet): `loads_canonical` also parses text the server wrote itself, never upload bytes: the
#: stored canonical rows (`months.py`, `structure/targets/lines.py`) and `CommercialRecords.ingest`, which reads
#: the batch the intake re-serialised from the envelope's bounded result (`uploads.py` `data2`).
SERVER_TEXT = {("commercial/months.py", "loads_canonical"), ("structure/targets/lines.py", "loads_canonical"),
               ("commercial/service.py", "loads_canonical")}


def parse_sites(rel: str, source: str) -> list[tuple[str, str]]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else None)
        if name in PARSE_CALLS:
            found.append((rel, name))
        elif name == "read" and any(k.arg == "context" for k in node.keywords):
            found.append((rel, ".read(context=)"))
    return found


def test_e7_upload_bytes_are_parsed_only_in_the_envelope() -> None:
    sites = []
    for path in sorted(BACKEND.rglob("*.py")):
        rel = path.relative_to(BACKEND).as_posix()
        sites += parse_sites(rel, path.read_text(encoding="utf-8"))
    outside = {s for s in sites if s[0] not in PARSE_HOMES} - SERVER_TEXT
    assert outside == set(), sorted(outside)
    assert {s for s in sites if s[0] == "commercial/envelope.py"} >= {
        ("commercial/envelope.py", ".read(context=)"), ("commercial/envelope.py", "split_file")}
    assert SERVER_TEXT <= set(sites)  # the allowance is exact: each named site still exists


@pytest.mark.parametrize("planted", [
    "def f(reader, data, ctx):\n    return reader.read(data, context=ctx)\n",
    "from assetops_contracts.native import split_file\nsplit_file(layout, data)\n",
    "from assetops_contracts.canonical import loads_canonical as lc\nimport x\nx.loads_canonical(b)\n",
])
def test_e7_the_scan_sees_a_planted_parse(planted: str) -> None:
    assert parse_sites("commercial/uploads.py", planted)


# --- E8 --------------------------------------------------------------------------------------------------------------

def _same(envelope: ParseEnvelope, reader, data: bytes, *, split: bool = False) -> None:
    inside = envelope.read(reader, data, CTX, split=split)
    there = reader.read(data, context=CTX)
    assert (inside.result.obj, inside.result.rows, dict(inside.result.refused), inside.result.personal_paths) == (
        there.obj, there.rows, dict(there.refused), there.personal_paths)
    if split:
        assert inside.split == split_file(reader.layout, data)


def test_e8_envelope_reads_equal_in_process_reads() -> None:
    envelope = ParseEnvelope()
    for case in CONTRACT_CASES:
        _same(envelope, READERS[case.reader_id], case.golden.read_bytes())
    for profile, sample in ((KOBO_PROFILE, KOBO_SAMPLE), (BUDGET_PROFILE, BUDGET_SAMPLE)):
        text = profile.decode("utf-8")
        reader = LayoutReader(compile_profile(json.loads(text), 1), profile=(text, 1))
        _same(envelope, reader, sample)
        _same(envelope, reader, sample, split=True)
    _same(envelope, READERS["canonical-json-v1"], encode(b_bill()))


def test_e8_refusals_cross_back_as_the_same_code_and_path() -> None:
    envelope = ParseEnvelope()
    for reader, data in ((READERS["canonical-json-v1"], b"{"), (READERS["billing-illustrative-1"], b"\xff\xfe")):
        with pytest.raises(CanonicalRefused) as there:
            reader.read(data, context=CTX)
        with pytest.raises(CanonicalRefused) as inside:
            envelope.read(reader, data, CTX)
        assert (inside.value.code, inside.value.path) == (there.value.code, there.value.path)


def test_e8_a_json_batch_of_a_million_records_is_refused_in_the_child() -> None:
    """Spec §2.12 step 3, pre-flight: 2a's `parse_batch` refuses the count before it walks the records, so the
    verdict is its own; the child answers it, so the parent never unpickles a million records."""
    obj = json.loads(encode(b_bill()))
    obj["records"] = [{}] * 1_000_000
    data = json.dumps(obj).encode()
    started = time.monotonic()
    with pytest.raises(CanonicalRefused) as inside:
        ParseEnvelope().read(READERS["canonical-json-v1"], data, CTX)
    assert (inside.value.code, inside.value.path) == ("CANONICAL_RANGE", "batch.records")
    assert time.monotonic() - started < 5.0
    obj["format_version"] = 99  # an envelope field still refuses first, as in process
    with pytest.raises(CanonicalRefused) as inside:
        ParseEnvelope().read(READERS["canonical-json-v1"], json.dumps(obj).encode(), CTX)
    assert inside.value.code == "CANONICAL_VERSION"


def test_e8_reader_spec() -> None:
    assert reader_spec(READERS["canonical-json-v1"]) == ("builtin", "canonical-json-v1")
    text = KOBO_PROFILE.decode("utf-8")
    assert reader_spec(LayoutReader(compile_profile(json.loads(text), 2), profile=(text, 2))) == ("profile", text, 2)
    with pytest.raises(TypeError):
        reader_spec(LayoutReader(compile_profile(json.loads(text), 1)))  # no profile source

    class Stub:
        id = "stub"
    with pytest.raises(TypeError):
        reader_spec(Stub())


def test_e8_a_rebuilt_reader_whose_id_differs_does_not_run() -> None:
    text = KOBO_PROFILE.decode("utf-8")
    liar = LayoutReader(compile_profile(json.loads(text), 1), profile=(text, 2))  # its text rebuilds v2
    with pytest.raises(RuntimeError, match="parse failed in the envelope: LookupError"):
        ParseEnvelope().read(liar, KOBO_SAMPLE, CTX)


# --- E9 --------------------------------------------------------------------------------------------------------------

def test_e9_the_api_logs_codes_and_numbers_and_the_envelope_logs_nothing(people, big, caplog) -> None:
    """D-3A6.29: a breach reaches the log only from the upload API; the marker in the file reaches no record."""
    from test_3a2_commercial_upload_api import SITE, as_, client
    from test_3c1a_person_work import People
    people = People()  # the API's own signed-in analyst, as 3A2's API tests have it
    people.sign("ana")
    w = world(people, replace(DEFAULT_LIMITS, memory_bytes=80 * 2**20))
    c = client(people, world=w)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        r = c.post(f"{SITE}?dry_run=true&reader={V1}", content=big,
                   headers=as_(people, "ana", **{"x-file-name": f"{SENTINEL}.csv", "content-type": "text/csv"}))
    assert (r.status_code, r.json()["code"]) == (422, "UPLOAD_FILE_REFUSED")
    assert not [r for r in caplog.records if r.name.startswith("assetops.commercial.")]
    records = [r for r in caplog.records if r.name == "assetops.commercial_upload"]
    assert len(records) == 1
    record = records[0]
    standard = set(vars(logging.LogRecord("n", logging.INFO, "p", 1, "m", (), None))) | {"message", "asctime"}
    extra = {k: v for k, v in vars(record).items() if k not in standard}
    assert set(extra) == {"cause", "reader", "bytes", "tenant"}
    assert extra["cause"] in CAUSES and isinstance(extra["bytes"], int) and type(extra["bytes"]) is int
    assert (extra["reader"], extra["bytes"], extra["tenant"]) == (V1, len(big), "acme")
    assert record.getMessage() == "upload parse refused by the envelope" and record.args == ()
    for text in [record.getMessage(), repr(record.args), *map(repr, extra.values()), caplog.text]:
        assert SENTINEL not in text
    assert record.exc_info is None


def test_e9_an_envelope_breach_is_a_canonical_refusal_with_a_closed_cause() -> None:
    from assetops_backend.commercial.envelope import EnvelopeBreach
    breach = EnvelopeBreach("wall")
    assert isinstance(breach, CanonicalRefused) and (breach.code, breach.path, breach.cause) == (
        "NATIVE_TOO_LARGE", "json", "wall")
