"""2a: canonical record v1, its units and source types (spec §9, T5-T10).

Every planted failure is a minimal edit of a fixture record and asserts the full
`str(refused)`, code and path (spec §6.7, §6.8). No database.
"""

from __future__ import annotations

import copy
import json
import os
import random
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from assetops_contracts.canonical import (
    BAND_UNITS,
    DAY,
    FORMAT_VERSION,
    HOUR,
    KINDS,
    KW,
    KWH,
    L,
    LEAF_FACTORS,
    MONEY,
    ONE,
    QUANTITY_UNITS,
    SOURCE_TYPES,
    BatchResult,
    CanonicalRecordV1,
    CanonicalRefused,
    Unit,
    batch_digest,
    loads_canonical,
    parse_batch,
    parse_record,
    parse_unit,
    record_digest,
    to_canonical_json,
)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "canonical_v1_examples.json"
REPO = Path(__file__).resolve().parents[2]


def _fixture() -> dict:
    return loads_canonical(FIXTURE.read_bytes())


def _batches() -> list[dict]:
    return _fixture()["batches"]


def _record(source_record_id: str) -> dict:
    for batch in _batches():
        for record in batch["records"]:
            if record["source_record_id"] == source_record_id:
                return copy.deepcopy(record)
    raise KeyError(source_record_id)


def _batch(source_type: str) -> dict:
    for batch in _batches():
        if batch["source_type"] == source_type:
            return copy.deepcopy(batch)
    raise KeyError(source_type)


def _refusal(obj) -> str:
    with pytest.raises(CanonicalRefused) as caught:
        parse_record(obj)
    return str(caught.value)


# --- T5: the fixture parses, round-trips to the same bytes, digests are stable ---


def test_t5_every_fixture_record_parses_and_round_trips_to_the_same_bytes():
    batches = _batches()
    assert len(batches) == 17
    assert [b["source_type"] for b in batches] != []
    assert {b["source_type"] for b in batches} == set(SOURCE_TYPES)
    kinds_seen = set()
    count = 0
    for batch in batches:
        result = parse_batch(batch)
        assert isinstance(result, BatchResult)
        for outcome in result.outcomes:
            assert isinstance(outcome, CanonicalRecordV1), (batch["source_type"], str(outcome))
            kinds_seen.add(outcome.kind)
            first = to_canonical_json(outcome)
            again = parse_record(loads_canonical(first))
            assert again == outcome
            assert to_canonical_json(again) == first
            count += 1
        batch_bytes = to_canonical_json(result)
        reparsed = parse_batch(loads_canonical(batch_bytes))
        assert reparsed.outcomes == result.outcomes
        assert to_canonical_json(reparsed) == batch_bytes
        assert batch_digest(reparsed) == batch_digest(result)
    assert kinds_seen == set(KINDS)
    assert len(KINDS) == 14
    assert count == 23


def test_t5_canonical_bytes_keep_decimal_text_and_normalise_z():
    record = _record("MM-7F31")
    record["clocks"]["occurred_at"] = "2026-10-30T16:12:00Z"
    record["amount"]["value"] = "1.50"
    text = to_canonical_json(parse_record(record)).decode("utf-8")
    assert '"value":"1.50"' in text
    assert '"occurred_at":"2026-10-30T16:12:00+00:00"' in text
    assert text.startswith('{"amount":')


DECIMAL_EDGES = ["1.50", "0.0000001", "0.000000000001", "1000000000000", "-108.00"]


@pytest.mark.parametrize("value", DECIMAL_EDGES)
def test_t5_decimal_edges_round_trip_to_identical_bytes(value):
    record = _record("CN-0412")
    record["amount"]["value"] = value
    parsed = parse_record(record)
    assert parsed.amount == (Decimal(value), "USD")
    first = to_canonical_json(parsed)
    assert f'"value":"{value}"'.encode() in first
    assert to_canonical_json(parse_record(loads_canonical(first))) == first


@pytest.mark.parametrize("value", ["0.0000000000001", "10000000000000"])
def test_t5_decimal_exponent_out_of_bound_is_refused(value):
    record = _record("CN-0412")
    record["amount"]["value"] = value
    assert _refusal(record) == "CANONICAL_NUMBER record.amount.value"


def test_t5_record_digest_is_stable_across_processes():
    script = (
        "import sys, json\n"
        "from pathlib import Path\n"
        "from assetops_contracts.canonical import loads_canonical, parse_record, record_digest\n"
        "f = loads_canonical(Path(sys.argv[1]).read_bytes())\n"
        "print(record_digest(parse_record(f['batches'][0]['records'][0])))\n"
    )
    digests = []
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        out = subprocess.run(
            [sys.executable, "-c", script, str(FIXTURE)],
            env=env, capture_output=True, text=True, check=True,
        )
        digests.append(out.stdout.strip())
    local = record_digest(parse_record(_batches()[0]["records"][0]))
    assert digests[0] == digests[1] == local
    assert len(local) == 64 and local == local.lower()


# --- T6: one planted failure per code and per row of §6.8 ---------------------


def _set(path: list, value):
    def edit(obj):
        target = obj
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = value
        return obj
    return edit


def _drop(path: list):
    def edit(obj):
        target = obj
        for step in path[:-1]:
            target = target[step]
        del target[path[-1]]
        return obj
    return edit


def _chain(*edits):
    def edit(obj):
        for e in edits:
            obj = e(obj)
        return obj
    return edit


RECORD_CASES = [
    # §6.7 codes and §6.6 order
    ("MM-7F31", _set(["format_version"], 2), "CANONICAL_VERSION record.format_version"),
    ("MM-7F31", _set(["format_version"], True), "CANONICAL_VERSION record.format_version"),
    ("MM-7F31", _set(["format_version"], 1.0), "CANONICAL_VERSION record.format_version"),
    ("MM-7F31", _drop(["format_version"]), "CANONICAL_VERSION record.format_version"),
    ("MM-7F31", _set(["kind"], "INVOICE"), "CANONICAL_KIND record.kind"),
    ("MM-7F31", _drop(["kind"]), "CANONICAL_FIELD record.kind"),
    ("MM-7F31", _set(["note"], "x"), "CANONICAL_FORBIDDEN record.note"),
    ("MM-7F31", _chain(_set(["zeta"], 1), _set(["alpha"], 1)), "CANONICAL_FORBIDDEN record.alpha"),
    ("MM-7F31", _chain(_set(["note"], "x"), _drop(["source_record_id"])), "CANONICAL_FORBIDDEN record.note"),
    ("MM-7F31", _drop(["source_record_id"]), "CANONICAL_FIELD record.source_record_id"),
    ("MM-7F31", _drop(["clocks"]), "CANONICAL_FIELD record.clocks"),
    ("MM-7F31", _drop(["body"]), "CANONICAL_FIELD record.body"),
    ("MM-7F31", _drop(["site_code"]), "CANONICAL_FIELD record.site_code"),
    ("MM-7F31", _set(["body", "note"], "x"), "CANONICAL_FORBIDDEN record.body.note"),
    ("MM-7F31", _drop(["body", "payer_ref"]), "CANONICAL_FIELD record.body.payer_ref"),
    ("MM-7F31", _set(["body"], []), "CANONICAL_TYPE record.body"),
    ("MM-7F31", _set(["clocks"], "2026-10"), "CANONICAL_TYPE record.clocks"),
    ("MM-7F31", _set(["site_code"], None), "CANONICAL_TYPE record.site_code"),
    ("MM-7F31", _set(["source_record_id"], 7), "CANONICAL_TYPE record.source_record_id"),
    # decimals
    ("MM-7F31", _set(["amount", "value"], 8.4), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], "08.40"), "CANONICAL_NUMBER record.amount.value"),
    ("CN-0412", _set(["amount", "value"], "-0.00"), "CANONICAL_NUMBER record.amount.value"),
    ("CN-0412", _set(["amount", "value"], "-0"), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], "1e3"), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], "1.5e0"), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], "1." + "0" * 31), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], "١٢"), "CANONICAL_NUMBER record.amount.value"),
    ("MM-7F31", _set(["amount", "value"], None), "CANONICAL_TYPE record.amount.value"),
    ("B-1031:IN", _set(["quantity", "value"], "120.5"), "CANONICAL_NUMBER record.quantity.value"),
    # signs
    ("MM-7F31", _set(["amount", "value"], "0"), "CANONICAL_SIGN record.amount.value"),
    ("INV-MTO-2026-10-C0412-1", _set(["amount", "value"], "-8.40"), "CANONICAL_SIGN record.amount.value"),
    ("FP-KOBO-2026-10-14", _set(["amount", "value"], "-1"), "CANONICAL_SIGN record.amount.value"),
    ("BUS-E07:2026-10-15", _set(["body", "required_kwh"], "0"), "CANONICAL_SIGN record.body.required_kwh"),
    ("B-1031:IN", _set(["quantity", "value"], "0"), "CANONICAL_SIGN record.quantity.value"),
    ("DEP-BUS-K03-2026-10-19", _set(["body", "soc_pct"], "-1"), "CANONICAL_SIGN record.body.soc_pct"),
    # currency, units, enums
    ("MM-7F31", _set(["amount", "currency"], "usd"), "CANONICAL_CURRENCY record.amount.currency"),
    ("C-114:rev-2", _set(["body", "currency"], "US"), "CANONICAL_CURRENCY record.body.currency"),
    ("INV-MTO-2026-10-C0412-1", _set(["quantity", "unit"], "MWh"), "CANONICAL_UNIT record.quantity.unit"),
    ("INV-MTO-2026-10-C0412-1", _set(["quantity", "unit"], "kW"), "CANONICAL_UNIT record.quantity.unit"),
    ("CN-0412", _set(["quantity"], {"value": "1", "unit": "L"}), "CANONICAL_UNIT record.quantity.unit"),
    ("C-114:rev-2", _set(["body", "bands", 0, "unit"], "per_MWh"), "CANONICAL_UNIT record.body.bands[0].unit"),
    ("MM-7F31", _set(["body", "method"], "CHEQUE"), "CANONICAL_ENUM record.body.method"),
    ("MM-7F31", _set(["status"], "PAID"), "CANONICAL_ENUM record.status"),
    ("MM-7F31", _set(["subject", "kind"], "METER"), "CANONICAL_ENUM record.subject.kind"),
    ("MM-7F31", _set(["subject", "kind"], "PERSON"), "CANONICAL_ENUM record.subject.kind"),
    ("MM-7F31", _set(["subject", "extra"], "x"), "CANONICAL_FORBIDDEN record.subject.extra"),
    ("MM-7F31", _drop(["status"]), "CANONICAL_FIELD record.status"),
    # forbidden by the kind's row
    ("MM-SETTLE-2026-11-02", _set(["subject"], {"kind": "SITE", "ref": "MTO-001"}), "CANONICAL_FORBIDDEN record.subject"),
    ("INV-MTO-2026-10-C0412-1", _set(["status"], "PAID"), "CANONICAL_FORBIDDEN record.status"),
    ("BUS-E07:2026-10-15", _set(["amount"], {"value": "1", "currency": "USD"}), "CANONICAL_FORBIDDEN record.amount"),
    (
        "INV-MTO-2026-10-C0412-1",
        _set(["body", "line_type"], "FIXED"),
        "CANONICAL_FORBIDDEN record.quantity",
    ),
    ("MM-7F31", _set(["clocks", "settled_at"], "2026-11-02T10:00:00+03:00"), "CANONICAL_FORBIDDEN record.clocks.settled_at"),
    ("BUS-E07:2026-10-15", _set(["clocks", "effective_to"], "2026-10-16"), "CANONICAL_FORBIDDEN record.clocks.effective_to"),
    ("MM-7F31", _drop(["clocks", "recognition_period"]), "CANONICAL_FIELD record.clocks.recognition_period"),
    ("FP-KOBO-2026-10-14", _drop(["quantity"]), "CANONICAL_FIELD record.quantity"),
    (
        "MT-2201:2026-10",
        _chain(_set(["body", "read_type"], "REGISTER"), _drop(["quantity"]), _set(["body", "register_start"], "100")),
        "CANONICAL_FIELD record.body.register_end",
    ),
    (
        "MT-2201:2026-10",
        _chain(_set(["body", "read_type"], "REGISTER"), _drop(["quantity"]),
               _set(["body", "register_start"], "100"), _set(["body", "register_end"], "99")),
        "CANONICAL_RANGE record.body.register_end",
    ),
    ("MT-2201:2026-10", _set(["body", "register_start"], "100"), "CANONICAL_FORBIDDEN record.body.register_start"),
    ("B-1031:IN", _drop(["body", "rate"]), "CANONICAL_FORBIDDEN record.body.currency"),
    ("B-1031:IN", _drop(["body", "currency"]), "CANONICAL_FIELD record.body.currency"),
    ("CN-0412", _drop(["amount"]), "CANONICAL_FIELD record.amount"),
    # clocks
    ("MM-7F31", _set(["clocks", "occurred_at"], "2026-10-30T19:12:00"), "CANONICAL_CLOCK record.clocks.occurred_at"),
    ("MM-7F31", _set(["clocks", "occurred_at"], "2026-02-30T19:12:00+03:00"), "CANONICAL_CLOCK record.clocks.occurred_at"),
    ("MM-7F31", _set(["clocks", "recognition_period"], "2026-13"), "CANONICAL_CLOCK record.clocks.recognition_period"),
    ("MM-7F31", _set(["clocks", "recognition_period"], "٢٠٢٦-١٠"), "CANONICAL_CLOCK record.clocks.recognition_period"),
    ("MT-2201:C-0412:2026-10-03", _set(["clocks", "effective_from"], "2026-10-3"), "CANONICAL_CLOCK record.clocks.effective_from"),
    (
        "INV-MTO-2026-10-C0412-1",
        _set(["clocks", "effective_to"], "2026-10-01"),
        "CANONICAL_RANGE record.clocks.effective_to",
    ),
    ("C-114:rev-2", _set(["body", "bands", 0, "from"], "24:00"), "CANONICAL_CLOCK record.body.bands[0].from"),
    ("C-114:rev-2", _set(["body", "bands", 0, "to"], "00:00"), "CANONICAL_RANGE record.body.bands[0].to"),
    ("C-114:rev-2", _set(["body", "bands", 1, "from"], "04:00"), "CANONICAL_RANGE record.body.bands[1].from"),
    ("C-114:rev-2", _set(["body", "bands", 2, "band"], "PEAK"), "CANONICAL_DUPLICATE record.body.bands[2].band"),
    ("C-114:rev-2", _set(["body", "bands"], []), "CANONICAL_RANGE record.body.bands"),
    (
        "C-114:rev-2",
        _set(["body", "bands"], [
            {"band": f"B{i}", "from": f"{i:02d}:00", "to": f"{i:02d}:30", "rate": "0.1", "unit": "per_kWh"}
            for i in range(24)
        ] + [{"band": "B24", "from": "23:30", "to": "24:00", "rate": "0.1", "unit": "per_kWh"}]),
        "CANONICAL_RANGE record.body.bands",
    ),
    ("C-114:rev-2", _set(["body", "bands", 0, "note"], "x"), "CANONICAL_FORBIDDEN record.body.bands[0].note"),
    ("C-114:rev-2", _set(["body", "bands", 0, "band"], "B" * 41), "CANONICAL_REF record.body.bands[0].band"),
    ("TCK-CH-K2-0193", _set(["body", "acknowledged_at"], "2026-10-18T07:00:00+03:00"), "CANONICAL_RANGE record.body.acknowledged_at"),
    ("TCK-CH-K2-0193", _drop(["body", "restored_at"]), "CANONICAL_FIELD record.body.restored_at"),
    (
        "BUS-E07:2026-10-15",
        _set(["body", "departure_at"], "2026-10-14T21:40:00+03:00"),
        "CANONICAL_RANGE record.body.departure_at",
    ),
    ("DEP-BUS-K03-2026-10-19", _set(["body", "block_met"], "false"), "CANONICAL_TYPE record.body.block_met"),
    ("DEP-BUS-K03-2026-10-19", _set(["body", "soc_pct"], "100.5"), "CANONICAL_RANGE record.body.soc_pct"),
    ("DOC-SUNFIELD-WARRANTY", _set(["body", "pages"], 0), "CANONICAL_RANGE record.body.pages"),
    ("DOC-SUNFIELD-WARRANTY", _set(["body", "pages"], 10001), "CANONICAL_RANGE record.body.pages"),
    ("DOC-SUNFIELD-WARRANTY", _set(["body", "pages"], "14"), "CANONICAL_TYPE record.body.pages"),
    ("DOC-SUNFIELD-WARRANTY", _set(["body", "pages"], True), "CANONICAL_TYPE record.body.pages"),
    ("DOC-SUNFIELD-WARRANTY", _set(["body", "document_sha256"], "4F" * 32), "CANONICAL_REF record.body.document_sha256"),
    ("MM-SETTLE-2026-11-02", _set(["body", "receipts"], []), "CANONICAL_RANGE record.body.receipts"),
    # refs
    ("MM-7F31", _set(["body", "payer_ref"], "C-0412 "), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["body", "payer_ref"], ""), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["body", "payer_ref"], "C-\u00850412"), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["body", "payer_ref"], "C-\x070412"), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["body", "payer_ref"], "C-\ud8000412"), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["body", "method"], "CASH\udc00"), "CANONICAL_REF record.body.method"),
    ("MM-7F31", _set(["body", "payer_ref"], "x" * 201), "CANONICAL_REF record.body.payer_ref"),
    ("MM-7F31", _set(["source_version"], "v" * 65), "CANONICAL_REF record.source_version"),
    ("MM-7F31", _set(["site_code"], "mto-001"), "CANONICAL_REF record.site_code"),
    ("CN-0412", _set(["body", "reason_code"], "R" * 41), "CANONICAL_REF record.body.reason_code"),
    ("MM-SETTLE-2026-11-02", _set(["body", "receipts"], ["MM-7F31", "MM-7F31"]), "CANONICAL_DUPLICATE record.body.receipts[1]"),
    # factor IDs and the currency rule
    ("BUD-2026-10:KOBO-001:diesel_l", _set(["body", "factor_id"], "Diesel"), "CANONICAL_FACTOR record.body.factor_id"),
    ("BUD-2026-10:KOBO-001:diesel_l", _set(["body", "factor_id"], "diesel\n"), "CANONICAL_FACTOR record.body.factor_id"),
    ("BUD-2026-10:portfolio:staff", _drop(["body", "currency"]), "CANONICAL_FACTOR record.body.currency"),
    (
        "BUD-2026-10:KOBO-001:diesel_l",
        _chain(_set(["body", "factor_id"], "candidate_l"), _set(["body", "currency"], "USD")),
        "CANONICAL_FACTOR record.body.currency",
    ),
    ("BUD-2026-10:portfolio:staff", _set(["site_code"], "kobo"), "CANONICAL_REF record.site_code"),
]


@pytest.mark.parametrize(
    "source_record_id, edit, expected",
    RECORD_CASES,
    ids=[f"{i:03d}-{c[2]}" for i, c in enumerate(RECORD_CASES)],
)
def test_t6_planted_record_failure(source_record_id, edit, expected):
    assert _refusal(edit(_record(source_record_id))) == expected


ACCEPTED_CASES = [
    ("a per_L band", "C-114:rev-2", _set(["body", "bands", 0, "unit"], "per_L")),
    (
        "return and departure compared as moments, not text",
        "BUS-E07:2026-10-15",
        _chain(_set(["body", "return_at"], "2026-10-15T00:30:00+03:00"),
               _set(["body", "departure_at"], "2026-10-14T22:00:00+00:00")),
    ),
    ("a node ID budget line without currency", "BUD-2026-10:KOBO-001:diesel_l", lambda r: r),
    ("a node ID budget line with currency", "BUD-2026-10:KOBO-001:diesel_l", _set(["body", "currency"], "USD")),
    ("a portfolio contract", "DOC-SUNFIELD-WARRANTY", _drop(["site_code"])),
    ("a charge FIXED without quantity", "INV-MTO-2026-10-C0412-1",
     _chain(_set(["body", "line_type"], "FIXED"), _drop(["quantity"]))),
    ("a storage movement without rate and currency", "B-1031:IN",
     _chain(_drop(["body", "rate"]), _drop(["body", "currency"]))),
    ("an adjustment with any sign", "ADJ-MTO-2026-10-CLINIC", _set(["quantity", "value"], "-40")),
]


@pytest.mark.parametrize("label, source_record_id, edit", ACCEPTED_CASES, ids=[c[0] for c in ACCEPTED_CASES])
def test_t6_planted_edge_accepted(label, source_record_id, edit):
    record = parse_record(edit(_record(source_record_id)))
    assert to_canonical_json(parse_record(loads_canonical(to_canonical_json(record)))) == to_canonical_json(record)


def test_t6_band_overlap_sorted_by_from_in_canonical_output():
    record = _record("C-114:rev-2")
    record["body"]["bands"].reverse()
    text = to_canonical_json(parse_record(record)).decode()
    assert text.index('"NIGHT"') < text.index('"PEAK"') < text.index('"OFFPEAK"')


def _batch_refusal(batch) -> str:
    with pytest.raises(CanonicalRefused) as caught:
        parse_batch(batch)
    return str(caught.value)


BATCH_CASES = [
    (_set(["provenance"], "recorded"), "CANONICAL_PROVENANCE batch.provenance"),
    (_set(["source_type"], "invoices"), "CANONICAL_SOURCE_TYPE batch.source_type"),
    (_set(["produced_at"], "2026-11-02 06:00"), "CANONICAL_CLOCK batch.produced_at"),
    (_set(["format_version"], 2), "CANONICAL_VERSION batch.format_version"),
    (_drop(["format_version"]), "CANONICAL_VERSION batch.format_version"),
    (_set(["note"], "x"), "CANONICAL_FORBIDDEN batch.note"),
    (_drop(["source_system"]), "CANONICAL_FIELD batch.source_system"),
    (_set(["tenant_code"], "Lakeside"), "CANONICAL_REF batch.tenant_code"),
    (_set(["records"], {}), "CANONICAL_TYPE batch.records"),
]


@pytest.mark.parametrize("edit, expected", BATCH_CASES, ids=[c[1] for c in BATCH_CASES])
def test_t6_planted_batch_failure(edit, expected):
    assert _batch_refusal(edit(_batch("billing_export"))) == expected


def test_t6_batch_not_an_object():
    assert _batch_refusal([]) == "CANONICAL_TYPE batch"


def test_t6_over_ten_thousand_records():
    batch = _batch("billing_export")
    batch["records"] = [batch["records"][0]] * 10001
    assert _batch_refusal(batch) == "CANONICAL_RANGE batch.records"


def test_t6_record_kind_outside_its_source_type():
    batch = _batch("service_tickets")
    batch["records"].append(_record("DEP-BUS-K03-2026-10-19"))
    result = parse_batch(batch)
    assert isinstance(result.outcomes[0], CanonicalRecordV1)
    assert str(result.outcomes[1]) == "CANONICAL_SOURCE_TYPE record.kind"


def test_t6_duplicate_id_and_version_second_refused():
    batch = _batch("billing_export")
    batch["records"].append(copy.deepcopy(batch["records"][0]))
    result = parse_batch(batch)
    assert isinstance(result.outcomes[0], CanonicalRecordV1)
    assert isinstance(result.outcomes[1], CanonicalRecordV1)
    assert str(result.outcomes[2]) == "CANONICAL_DUPLICATE record.source_record_id"


def test_t6_duplicate_with_first_refused_leaves_the_second_valid():
    batch = _batch("billing_export")
    broken = copy.deepcopy(batch["records"][0])
    broken["amount"]["value"] = 8.4
    batch["records"].insert(0, broken)
    result = parse_batch(batch)
    assert str(result.outcomes[0]) == "CANONICAL_NUMBER record.amount.value"
    assert isinstance(result.outcomes[1], CanonicalRecordV1)


def test_t6_non_object_record_element_and_per_row_independence():
    batch = _batch("billing_export")
    first, second = batch["records"]
    batch["records"] = [first, "not a record", second]
    result = parse_batch(batch)
    assert isinstance(result.outcomes[0], CanonicalRecordV1)
    assert str(result.outcomes[1]) == "CANONICAL_TYPE record"
    assert isinstance(result.outcomes[2], CanonicalRecordV1)
    written = json.loads(to_canonical_json(result))
    assert [r["source_record_id"] for r in written["records"]] == [
        first["source_record_id"], second["source_record_id"]]
    assert set(written) == {"format_version", "tenant_code", "source_type", "source_system",
                            "provenance", "produced_at", "records"}


def test_t6_parse_record_on_a_non_object():
    assert _refusal(["x"]) == "CANONICAL_TYPE record"


def test_t6_refusal_attributes():
    with pytest.raises(CanonicalRefused) as caught:
        parse_record(_set(["kind"], "INVOICE")(_record("MM-7F31")))
    assert caught.value.code == "CANONICAL_KIND"
    assert caught.value.path == "record.kind"


@pytest.mark.parametrize(
    "data, expected",
    [
        (b'{"a":1,"a":2}', "CANONICAL_DUPLICATE json.a"),
        (b'{"value": NaN}', "CANONICAL_NUMBER json"),
        (b'[Infinity]', "CANONICAL_NUMBER json"),
        (b'[-Infinity]', "CANONICAL_NUMBER json"),
        (b'{"a":"\xff"}', "CANONICAL_TYPE json"),
        (b'{"a":', "CANONICAL_TYPE json"),
    ],
)
def test_t6_loads_canonical(data, expected):
    with pytest.raises(CanonicalRefused) as caught:
        loads_canonical(data)
    assert str(caught.value) == expected


# --- T7: robustness --------------------------------------------------------


def _paths(obj, prefix=()):
    yield prefix
    if isinstance(obj, dict):
        for key, value in obj.items():
            yield from _paths(value, prefix + (key,))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _paths(value, prefix + (index,))


def _get(obj, path):
    for step in path:
        obj = obj[step]
    return obj


def _mutate(rng: random.Random, record: dict) -> dict:
    record = copy.deepcopy(record)
    paths = [p for p in _paths(record) if p]
    path = rng.choice(paths)
    parent = _get(record, path[:-1])
    key = path[-1]
    op = rng.choice(["drop", "type", "control", "surrogate", "sign", "key"])
    if op == "key":
        # A key mutation at any object level (spec T7): a surrogate, a control character or 1,000 characters.
        target = parent[key] if isinstance(parent.get(key) if isinstance(parent, dict) else None, dict) else parent
        if isinstance(target, dict):
            target[rng.choice(["\ud800x", "a\x00b", "\x1f", "k" * 1000, "\udfff" * 3])] = 1
    elif op == "drop":
        if isinstance(parent, dict):
            del parent[key]
        else:
            parent.pop(key)
    elif op == "type":
        parent[key] = rng.choice([None, 1, 1.5, True, False, [], {}, "x", -3, "1e3", [1], {"a": None}])
    elif op in ("control", "surrogate"):
        value = parent[key]
        char = rng.choice(["\x00", "\x1f", "\x7f", "\x85", "\n"]) if op == "control" else rng.choice(["\ud800", "\udfff"])
        if isinstance(value, str):
            at = rng.randrange(len(value) + 1)
            parent[key] = value[:at] + char + value[at:]
        else:
            parent[key] = char
    else:
        value = parent[key]
        if isinstance(value, str):
            parent[key] = value[1:] if value.startswith("-") else "-" + value
        elif isinstance(value, int) and not isinstance(value, bool):
            parent[key] = -value
    return record


def test_t7_mutations_raise_only_canonical_refused():
    rng = random.Random(2026)
    records = [r for b in _batches() for r in b["records"]]
    parsed_count = 0
    for _ in range(500):
        mutated = _mutate(rng, rng.choice(records))
        try:
            record = parse_record(mutated)
        except CanonicalRefused as refused:
            assert refused.path.startswith("record"), str(refused)
            str(refused).encode("ascii")  # D-2A.11: every refusal text is ASCII
            assert len(refused.path) < 400
            continue
        parsed_count += 1
        written = to_canonical_json(record)
        assert to_canonical_json(parse_record(loads_canonical(written))) == written
    assert 0 < parsed_count < 500


# --- T11: review round 1 (spec rev 3: D-2A.11, D-2A.12) ---------------------


def _refusal_text(fn, *args) -> str:
    with pytest.raises(CanonicalRefused) as caught:
        fn(*args)
    text = str(caught.value)
    text.encode("ascii")
    return text


def test_t11_surrogate_key_in_body_is_a_ref_refusal_at_the_container():
    record = _record("INV-MTO-2026-10-C0412-1")
    record["body"]["\ud800"] = "x"
    assert _refusal_text(parse_record, record) == "CANONICAL_REF record.body"


def test_t11_loads_canonical_duplicate_surrogate_key():
    data = b'{"\\ud800": 1, "\\ud800": 2}'
    assert _refusal_text(loads_canonical, data) == "CANONICAL_REF json"


def test_t11_long_unknown_key_is_escaped_and_capped():
    record = _record("INV-MTO-2026-10-C0412-1")
    record["body"]["k" * 1000] = "x"
    assert _refusal_text(parse_record, record) == "CANONICAL_FORBIDDEN record.body." + "k" * 64 + "..."
    record = _record("INV-MTO-2026-10-C0412-1")
    record["body"]["\u00e9" * 1000] = "x"
    assert _refusal_text(parse_record, record) == "CANONICAL_FORBIDDEN record.body." + "\\u00e9" * 10 + "..."[:0] + "\\u00e9"[:4] + "..."
    assert _refusal_text(loads_canonical, ('{"' + "z" * 1000 + '": 1, "' + "z" * 1000 + '": 2}').encode()) == \
        "CANONICAL_DUPLICATE json." + "z" * 64 + "..."


CONTROL_CASES = [
    ("INV-MTO-2026-10-C0412-1", "line_type"),
    ("FP-KOBO-2026-10-14", "category"),
    ("MT-2201:2026-10", "read_type"),
]


@pytest.mark.parametrize("record_id, control", CONTROL_CASES, ids=[c[1] for c in CONTROL_CASES])
def test_t11_missing_or_invalid_control_is_the_root_cause(record_id, control):
    record = _record(record_id)
    assert "quantity" in record
    del record["body"][control]
    assert _refusal(record) == f"CANONICAL_FIELD record.body.{control}"
    record = _record(record_id)
    record["body"][control] = "BOGUS"
    assert _refusal(record) == f"CANONICAL_ENUM record.body.{control}"


def test_t11_version_before_envelope_keys():
    batch = _batch("mobile_money_statement")
    batch["format_version"] = 2
    batch["extra"] = 1
    assert _batch_refusal(batch) == "CANONICAL_VERSION batch.format_version"


def test_t11_null_subject_on_a_forbidden_row():
    record = _record("MM-SETTLE-2026-11-02")
    record["subject"] = None
    assert _refusal(record) == "CANONICAL_FORBIDDEN record.subject"


JUNK_CASES = [
    ("INV-MTO-2026-10-C0412-1", ["site_code"], "CANONICAL_REF record.site_code"),
    ("INV-MTO-2026-10-C0412-1", ["amount", "currency"], "CANONICAL_CURRENCY record.amount.currency"),
    ("DOC-SUNFIELD-WARRANTY", ["body", "document_sha256"], "CANONICAL_REF record.body.document_sha256"),
    ("INV-MTO-2026-10-C0412-1", ["clocks", "recognition_period"], "CANONICAL_CLOCK record.clocks.recognition_period"),
    ("INV-MTO-2026-10-C0412-1", ["clocks", "effective_from"], "CANONICAL_CLOCK record.clocks.effective_from"),
    ("C-114:rev-2", ["body", "bands", 0, "from"], "CANONICAL_CLOCK record.body.bands[0].from"),
    ("FP-KOBO-2026-10-14", ["clocks", "occurred_at"], "CANONICAL_CLOCK record.clocks.occurred_at"),
]


@pytest.mark.parametrize("record_id, path, expected", JUNK_CASES, ids=[c[2] for c in JUNK_CASES])
def test_t11_trailing_junk_fails_every_pattern(record_id, path, expected):
    record = _record(record_id)
    target = _get(record, path[:-1])
    target[path[-1]] = target[path[-1]] + "\n"
    assert _refusal(record) == expected


def test_t11_trailing_junk_tenant_code():
    batch = _batch("mobile_money_statement")
    batch["tenant_code"] += "\n"
    assert _batch_refusal(batch) == "CANONICAL_REF batch.tenant_code"


def test_t11_nfd_ref_round_trips_and_differs_from_nfc():
    import unicodedata
    nfd = unicodedata.normalize("NFD", "Caf\u00e9")
    nfc = unicodedata.normalize("NFC", nfd)
    assert nfd != nfc
    a = _record("INV-MTO-2026-10-C0412-1")
    a["body"]["tariff_code"] = nfd
    b = _record("INV-MTO-2026-10-C0412-1")
    b["body"]["tariff_code"] = nfc
    written = to_canonical_json(parse_record(a))
    assert nfd.encode() in written and nfc.encode() not in written
    assert to_canonical_json(parse_record(loads_canonical(written))) == written
    assert written != to_canonical_json(parse_record(b))
    assert record_digest(parse_record(a)) != record_digest(parse_record(b))


def test_t11_overlap_points_at_the_input_index_of_the_later_band():
    record = _record("C-114:rev-2")
    mk = lambda name, a, b: {"band": name, "from": a, "to": b, "rate": "0.10", "unit": "per_kWh"}
    record["body"]["bands"] = [mk("C", "20:00", "23:00"), mk("A", "01:00", "11:00"), mk("B", "10:00", "12:00")]
    assert _refusal(record) == "CANONICAL_RANGE record.body.bands[2].from"


# --- T8: units ---------------------------------------------------------------


def test_t8_units():
    for factor in LEAF_FACTORS.values():
        assert parse_unit(str(factor.unit)) == factor.unit
    assert str(ONE / DAY) == "1/DAY"
    assert str(ONE) == "1"
    assert KW * HOUR == KWH
    assert MONEY / MONEY == ONE
    assert str(KW) == "KWH/HOUR"
    assert str(MONEY * HOUR / KWH) == "HOUR*MONEY/KWH"
    assert MONEY.is_money and not (MONEY / L).is_money and not ONE.is_money
    assert isinstance(KW, Unit)
    assert dict(QUANTITY_UNITS) == {"kWh": KWH, "kW": KW, "L": L, "crate": ONE, "crate_day": DAY}
    assert dict(BAND_UNITS) == {"per_kWh": MONEY / KWH, "per_crate_day": MONEY / DAY, "per_L": MONEY / L}
    assert hash(KWH * L / L) == hash(KWH)


@pytest.mark.parametrize(
    "text", ["MONEY*HOUR/KWH", "KWH*L/KWH", "KWH/KWH", "kWh", "", "KWH /HOUR", "KWH^2", "1/1", "MONEY/DAY/L"]
)
def test_t8_parse_unit_refuses_non_canonical_text(text):
    with pytest.raises(ValueError) as caught:
        parse_unit(text)
    assert str(caught.value) == f"CANONICAL_UNIT {text}"


# --- T9: neutrality -----------------------------------------------------------


def test_t9_import_adds_only_stdlib_and_the_package():
    script = (
        "import sys, json\n"
        "before = set(sys.modules)\n"
        "import assetops_contracts.canonical\n"
        "added = sorted(set(sys.modules) - before)\n"
        "outside = [m for m in added if m.split('.')[0] not in sys.stdlib_module_names"
        " and m.split('.')[0] != 'assetops_contracts']\n"
        "print(json.dumps({'added': added, 'outside': outside}))\n"
    )
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    report = json.loads(out.stdout)
    assert "assetops_contracts.canonical" in report["added"]
    assert report["outside"] == []


# --- T10: source types -------------------------------------------------------


def test_t10_source_types():
    assert list(SOURCE_TYPES) == [
        "billing_export", "mobile_money_statement", "meter_register", "meter_data_export",
        "expense_ledger", "budget_workbook", "contract_documents", "storage_ledger",
        "customer_invoicing", "storage_rate_card", "tariff_sheet", "electricity_bill",
        "utility_invoice", "fleet_roster", "depot_dispatch_log", "service_tickets",
        "penalty_statement",
    ]
    emitted = set()
    for source_id, source in SOURCE_TYPES.items():
        assert source.id == source_id
        assert source.kinds <= KINDS, source_id
        assert source.words
        emitted |= source.kinds
    assert emitted == KINDS
    assert FORMAT_VERSION == 1
