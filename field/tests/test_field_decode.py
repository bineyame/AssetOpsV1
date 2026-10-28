"""TEL-01 decoder vectors and the encode/decode round trip (build spec TEL-01 gates)."""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import gx2_rows, profile_document, row_document  # noqa: E402

from assetops_field.decode import (  # noqa: E402
    DecodeFault,
    EncodeRefused,
    decode_words,
    encode_sentinel,
    encode_value,
)
from assetops_field.profile import parse_profile  # noqa: E402

FIELD_PACKAGE = Path(__file__).resolve().parents[1] / "assetops_field"
SINGLE = {"kind": "A", "point": "p", "sign": "s", "phase_aggregation": "SINGLE_REGISTER"}


def one_register_row(kind: str, order: str = "BIG", *, scale: int = 0, unit: int = 0, sentinels=(),
                     resolution: str | None = None):
    exponent = scale + unit
    document = row_document(
        registers=[{"unit_id": 1, "function": 4, "address": 0, "type": kind, "word_order": order}],
        quantity=SINGLE, scale_exponent=scale, unit_exponent=unit, sentinels=list(sentinels),
        output_resolution=resolution or (str(10**exponent) if exponent >= 0 else "0." + "0" * (-exponent - 1) + "1"),
    )
    return parse_profile(profile_document(rows=[document])).rows[0]


def test_int16_ff9c_times_0_1_is_minus_ten():
    row = one_register_row("int16", scale=-1)
    assert decode_words(row, [[0xFF9C]]).value == Fraction(-10)


def test_declared_sentinel_7fff_is_sentinel():
    row = one_register_row("int16", scale=-1, sentinels=[0x7FFF])
    assert decode_words(row, [[0x7FFF]]).kind == "SENTINEL"


def test_int16_sentinel_is_compared_unsigned_before_twos_complement():
    row = one_register_row("int16", sentinels=[32768], resolution="1")
    assert decode_words(row, [[0x8000]]).kind == "SENTINEL"
    assert decode_words(row, [[0x8001]]).value == Fraction(-32767)


def test_uint32_word_orders():
    big = one_register_row("uint32", "BIG", unit=-3)
    little = one_register_row("uint32", "LITTLE", unit=-3)
    assert decode_words(big, [[0x0001, 0x86A0]]).value == Fraction(100)
    assert decode_words(little, [[0x86A0, 0x0001]]).value == Fraction(100)


def test_three_phase_rows_sentinel_on_any_register_and_exact_sum():
    pv = parse_profile(profile_document()).rows[0]
    assert decode_words(pv, [[0x03E8], [0x0000], [0xFFFF]]).kind == "SENTINEL"
    decoded = decode_words(pv, [[0x03E8], [0x0001], [0x0002]])
    assert decoded.kind == "VALUE" and decoded.value == Fraction(1003, 1000)


def test_wrong_word_count_and_unmapped_enum_are_decode_faults():
    pv = parse_profile(profile_document()).rows[0]
    with pytest.raises(DecodeFault):
        decode_words(pv, [[1], [2]])
    with pytest.raises(DecodeFault):
        decode_words(pv, [[1], [2], [3, 4]])
    profile2 = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE"))
    status = profile2.rows[1]
    assert decode_words(status, [[2]]).state == "RUNNING"
    with pytest.raises(DecodeFault):
        decode_words(status, [[9]])


def test_encode_then_decode_round_trips_every_row_of_profile_1_and_2():
    profile1 = parse_profile(profile_document())
    profile2 = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE"))
    samples = {
        "kW:-3": [Fraction(0), Fraction(12345, 1000), Fraction(65534, 1000)],
        "%:0": [Fraction(0), Fraction(87), Fraction(100)],
        "kW:-6": [Fraction(-1234567, 1_000_000), Fraction(0), Fraction(2147483646, 1_000_000)],
        "%:-6": [Fraction(55123456, 1_000_000)],
    }
    checked = 0
    for row in profile1.rows + profile2.rows:
        if row.decode == "ENUM":
            for state in row.enum_map.values():
                assert decode_words(row, encode_value(row, state)).state == state
                checked += 1
            continue
        for value in samples[f"{row.source_unit}:{row.exponent}"]:
            words = encode_value(row, value)
            assert len(words) == len(row.registers)
            assert all(w == [0] * len(w) for w in words[1:])  # whole value on the first register
            assert decode_words(row, words).value == value
            checked += 1
        assert decode_words(row, encode_sentinel(row)).kind == "SENTINEL"
    assert checked >= 2 * 3 + 4 + 7


def test_encode_refuses_out_of_range_and_non_multiples():
    pv = parse_profile(profile_document()).rows[0]
    with pytest.raises(EncodeRefused) as caught:
        encode_value(pv, Fraction(65536, 1000))
    assert caught.value.code == "OUT_OF_RANGE"
    with pytest.raises(EncodeRefused) as caught:
        encode_value(pv, "65.535")  # raw 65535 is the declared sentinel
    assert caught.value.code == "OUT_OF_RANGE"
    with pytest.raises(EncodeRefused) as caught:
        encode_value(pv, "0.0005")
    assert caught.value.code == "NOT_A_MULTIPLE"
    status = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE")).rows[1]
    with pytest.raises(EncodeRefused) as caught:
        encode_value(status, "IDLE")
    assert caught.value.code == "UNKNOWN_STATE"


def test_encode_sentinel_writes_the_sentinel_on_every_register():
    pv = parse_profile(profile_document()).rows[0]
    assert encode_sentinel(pv) == [[0xFFFF], [0xFFFF], [0xFFFF]]
    block = parse_profile(profile_document(rows=gx2_rows(), status="ILLUSTRATIVE")).rows[2]
    assert encode_sentinel(block) == [[0x7FFF, 0xFFFF]]


def test_no_float_anywhere_in_the_field_package():
    offenders = [
        f"{path.name}:{number}"
        for path in sorted(FIELD_PACKAGE.glob("*.py"))
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if "float(" in line
    ]
    assert offenders == []
