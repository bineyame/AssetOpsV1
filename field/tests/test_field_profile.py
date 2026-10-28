"""TEL-01 profile rules (build spec 0.6): every PROFILE_CODES code has a test."""

from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from field_fixtures import GX1_SOC_ROW, gx2_rows, profile_document, row_document  # noqa: E402

from assetops_field.profile import PROFILE_CODES, ProfileRefused, load_profile, parse_profile  # noqa: E402

def refused(document, code: str, field: str | None = None) -> ProfileRefused:
    with pytest.raises(ProfileRefused) as caught:
        parse_profile(document)
    assert caught.value.code == code, caught.value
    if field is not None:
        assert caught.value.field == field, caught.value
    return caught.value


def with_rows(*rows, **overrides):
    return profile_document(rows=list(rows), **overrides)


def test_the_gx1_shaped_profile_loads_with_exact_fields():
    profile = parse_profile(profile_document())
    pv, soc = profile.rows
    assert profile.profile_id == "gx-system-illustrative-1" and profile.status == "UNPINNED"
    assert [r.address for r in pv.registers] == [808, 809, 810]
    assert pv.word_count == 3 and pv.exponent == -3
    assert pv.output_resolution == Fraction(1, 1000) and pv.register_quantum == 1
    assert pv.sentinels == frozenset({65535})
    assert soc.span_seconds is None and soc.poll_period_seconds is None and soc.cadence_seconds == 900
    assert pv.registers[0].words == 1 and pv.registers[0].bits == 16 and not pv.registers[0].signed


def test_profile_2_rows_load_including_the_enum_row():
    profile = parse_profile(with_rows(*gx2_rows(), status="ILLUSTRATIVE", profile_id="gx-system-illustrative-2"))
    status_row = profile.rows[1]
    assert status_row.decode == "ENUM" and dict(status_row.enum_map) == {0: "STOPPED", 1: "STARTING",
                                                                         2: "RUNNING", 3: "FAILED"}
    assert status_row.output_resolution is None
    assert profile.rows[2].registers[0].words == 2 and profile.rows[2].registers[0].signed


def test_profile_sha_is_unchanged_under_key_reordering(tmp_path):
    document = profile_document()
    reordered = json.loads(json.dumps(document, sort_keys=True))
    reordered = dict(reversed(list(reordered.items())))
    reordered["rows"] = [dict(reversed(list(row.items()))) for row in reordered["rows"]]
    assert list(reordered) != list(document)
    assert parse_profile(reordered).sha256 == parse_profile(document).sha256
    path = tmp_path / "p.json"
    path.write_text(json.dumps(reordered, indent=2), encoding="utf-8")
    assert load_profile(path).sha256 == parse_profile(document).sha256
    changed = profile_document(profile_version=2)
    assert parse_profile(changed).sha256 != parse_profile(document).sha256


def test_load_profile_refuses_non_json_as_schema_invalid(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(ProfileRefused) as caught:
        load_profile(path)
    assert caught.value.code == "SCHEMA_INVALID"


@pytest.mark.parametrize(
    "document, field",
    [
        (profile_document(extra=1), "extra"),
        (profile_document(coverage=...), "coverage"),
        (profile_document(schema={"id": "assetops.field-profile", "version": 2}), "schema"),
        (profile_document(profile_id="GX"), "profile_id"),
        (profile_document(profile_version=0), "profile_version"),
        (profile_document(state_skew_max_seconds=11), "state_skew_max_seconds"),
        (profile_document(rows=[]), "rows"),
        (profile_document(interface="MODBUS_RTU"), "interface"),
        (with_rows(row_document(colour="red")), "rows[0].colour"),
        (with_rows(row_document(span_seconds=...)), "rows[0].span_seconds"),
        (with_rows(row_document(csv={"column": "pv_kw"})), "rows[0].csv"),
        (with_rows(row_document(quantity={"kind": "AC_POWER", "point": "x", "sign": "y"})),
         "rows[0].quantity.phase_aggregation"),
        (with_rows(row_document(quantity={"kind": "", "point": "x", "sign": "y", "phase_aggregation": "EXACT_SUM_L1"})),
         "rows[0].quantity.kind"),
        (with_rows(row_document(registers=[{"unit_id": 100, "function": 6, "address": 808, "type": "uint16",
                                            "word_order": "BIG"}])), "rows[0].registers[0].function"),
        (with_rows(row_document(registers=[{"unit_id": 256, "function": 3, "address": 808, "type": "uint16",
                                            "word_order": "BIG"}])), "rows[0].registers[0].unit_id"),
        (with_rows(row_document(registers=[{"unit_id": 1, "function": 3, "address": 65535, "type": "uint32",
                                            "word_order": "BIG"}],
                                quantity={"kind": "A", "point": "p", "sign": "s",
                                          "phase_aggregation": "SINGLE_REGISTER"})),
         "rows[0].registers[0].address"),
        (with_rows(row_document(registers=[{"unit_id": 1, "function": 3, "address": 1, "type": "float32",
                                            "word_order": "BIG"}])), "rows[0].registers[0].type"),
        (with_rows(row_document(quantity={"kind": "A", "point": "p", "sign": "s",
                                          "phase_aggregation": "SINGLE_REGISTER"})),
         "rows[0].quantity.phase_aggregation"),
        (with_rows(row_document(enum_map={"0": "OFF"})), "rows[0].enum_map"),
        (with_rows(row_document(scale_exponent=13)), "rows[0].scale_exponent"),
        (with_rows(row_document(output_resolution="1/1000")), "rows[0].output_resolution"),
        (with_rows(row_document(row_id="PV")), "rows[0].row_id"),
        (with_rows(row_document(), row_document(signal_id="other")), "rows[1].row_id"),
        (with_rows(dict(copy.deepcopy(GX1_SOC_ROW), span_seconds=900)), "rows[0].span_seconds"),
    ],
)
def test_schema_invalid_names_the_json_path(document, field):
    refused(document, "SCHEMA_INVALID", field)


def test_enum_rows_are_one_uint16_state_register_without_number_keys():
    enum_row = gx2_rows()[1]
    refused(with_rows(dict(enum_row, source_unit="kW"), status="ILLUSTRATIVE"), "SCHEMA_INVALID",
            "rows[0].source_unit")
    two = copy.deepcopy(enum_row)
    two["registers"][0]["type"] = "int16"
    refused(with_rows(two, status="ILLUSTRATIVE"), "SCHEMA_INVALID", "rows[0].registers")
    refused(with_rows(dict(enum_row, output_resolution="1"), status="ILLUSTRATIVE"), "SCHEMA_INVALID",
            "rows[0].output_resolution")
    refused(with_rows(dict(enum_row, enum_map={"0": "stopped"}), status="ILLUSTRATIVE"), "SCHEMA_INVALID")


def test_unsupported_value():
    refused(profile_document(source_timestamps="LOCAL"), "UNSUPPORTED_VALUE", "source_timestamps")
    refused(profile_document(coverage="MOST_POLLS"), "UNSUPPORTED_VALUE", "coverage")


def test_status_inconsistent():
    refused(profile_document(status="PINNED"), "STATUS_INCONSISTENT", "status")
    refused(profile_document(status="ILLUSTRATIVE"), "STATUS_INCONSISTENT", "status")


def test_poll_period_not_divisor():
    refused(with_rows(row_document(poll_period_seconds=400)), "POLL_PERIOD_NOT_DIVISOR")
    refused(with_rows(row_document(poll_period_seconds=225)), "POLL_PERIOD_NOT_DIVISOR")  # odd
    refused(with_rows(row_document(span_seconds=2, cadence_seconds=2, poll_period_seconds=1)),
            "POLL_PERIOD_NOT_DIVISOR")


def test_cadence_not_aligned():
    refused(with_rows(row_document(cadence_seconds=1000)), "CADENCE_NOT_ALIGNED", "rows[0].cadence_seconds")
    refused(with_rows(row_document(cadence_seconds=1200)), "CADENCE_NOT_ALIGNED", "rows[0].cadence_seconds")
    refused(with_rows(row_document(span_seconds=7, cadence_seconds=7)), "CADENCE_NOT_ALIGNED",
            "rows[0].cadence_seconds")
    refused(with_rows(row_document(span_seconds=7, cadence_seconds=86400)), "CADENCE_NOT_ALIGNED",
            "rows[0].span_seconds")
    assert parse_profile(with_rows(row_document(cadence_seconds=3600))).rows[0].cadence_seconds == 3600


def test_duplicate_signal():
    refused(with_rows(row_document(), row_document(row_id="pv-two")), "DUPLICATE_SIGNAL", "rows[1]")


def test_report_key_too_long():
    refused(with_rows(row_document(device_id="d" * 150)), "REPORT_KEY_TOO_LONG", "rows[0]")


def test_resolution_finer_than_quantum():
    refused(with_rows(row_document(output_resolution="0.0001")), "RESOLUTION_FINER_THAN_QUANTUM",
            "rows[0].output_resolution")
    assert parse_profile(with_rows(row_document(output_resolution="0.01"))).rows[0].output_resolution == Fraction(1, 100)


def test_sentinel_out_of_range():
    refused(with_rows(row_document(sentinels=[65536])), "SENTINEL_OUT_OF_RANGE", "rows[0].sentinels[0]")
    refused(with_rows(row_document(sentinels=[-1])), "SENTINEL_OUT_OF_RANGE", "rows[0].sentinels[0]")
    signed = row_document(registers=[{"unit_id": 1, "function": 4, "address": 1, "type": "int16",
                                      "word_order": "BIG"}],
                          quantity={"kind": "A", "point": "p", "sign": "s", "phase_aggregation": "SINGLE_REGISTER"},
                          sentinels=[32768])
    assert parse_profile(with_rows(signed)).rows[0].sentinels == frozenset({32768})


def test_every_profile_code_has_a_refusal_test():
    source = Path(__file__).read_text(encoding="utf-8")
    missing = [code for code in PROFILE_CODES if f'"{code}"' not in source.split("def test_every_profile_code")[0]]
    assert missing == []
