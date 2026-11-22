"""DD2.2 (spec `specs/DD-demo-data/spec.md` §7 DD2.2; D-DD.24): the profile `bool` type.

A `bool` path must carry a `map` whose values are exactly {"true", "false"} (the one exception to "a map sits only on a
coded path"); it writes a JSON boolean. Every literal below is written by hand from the spec.
"""

from __future__ import annotations

import copy
from types import MappingProxyType

import pytest

from assetops_contracts.native import (
    Column,
    Layout,
    ProfileInvalid,
    check_layout,
    compile_profile,
    read_layout,
)
from assetops_contracts.native.profiles_v1 import run_probes
from assetops_contracts.native.layouts_v1 import TYPES, split_file

CTX = {"tenant_code": "metro-bus", "produced_at": "2026-11-06T06:00:00+03:00", "provenance": "source-emulated"}

PROFILE = {
    "schema": "assetops.source-profile",
    "schema_version": 1,
    "profile_id": "bool-departures",
    "status": "ILLUSTRATIVE",
    "source_type": "fleet_roster",
    "source_system": "depot-log",
    "file": {"format": "csv", "encoding": "utf-8", "delimiter": ",", "header_row": 1},
    "values": {"decimal_mark": ".", "thousands_mark": "", "negative": "minus", "date_format": "YYYY-MM-DD",
               "time_format": "HH:MM:SS", "month_format": "YYYY-MM", "timezone": "Africa/Nairobi"},
    "version": {"from": "constant", "value": "1"},
    "columns": [
        {"header": "Row", "paths": [{"path": "source_record_id", "type": "text"}]},
        {"header": "Bus", "paths": [{"path": "subject.ref", "type": "text"}, {"path": "body.vehicle_ref", "type": "text"}]},
        {"header": "Block met", "paths": [{"path": "body.block_met", "type": "bool", "map": {"Y": "true", "N": "false"}}]},
    ],
    "constants": {"kind": "DEPARTURE", "subject.kind": "VEHICLE"},
    "personal": [],
}
DATA = b"Row,Bus,Block met\nd-1,BUS-01,Y\nd-2,BUS-02,N\n"


def bool_column(mapping: dict) -> dict:
    obj = copy.deepcopy(PROFILE)
    obj["columns"][2]["paths"][0]["map"] = mapping
    return obj


def test_bool_is_a_type() -> None:
    assert "bool" in TYPES


def test_accept_writes_json_booleans() -> None:
    read = read_layout(compile_profile(PROFILE, 1), DATA, **CTX)
    assert read.refused == {}
    met = [r["body"]["block_met"] for r in read.obj["records"]]
    assert met == [True, False]
    assert all(type(v) is bool for v in met)


def test_refuse_an_unmapped_cell() -> None:
    read = read_layout(compile_profile(PROFILE, 1), b"Row,Bus,Block met\nd-1,BUS-01,yes\n", **CTX)
    assert dict(read.refused) == {0: ("NATIVE_VALUE", "record.body.block_met")}


@pytest.mark.parametrize("mapping", [
    {"Y": "true"},
    {"N": "false"},
    {"Y": "true", "N": "no"},
    {"Y": "true", "N": "false", "?": "maybe"},
    {"Y": "TRUE", "N": "FALSE"},
])
def test_refuse_a_map_without_both_values(mapping: dict) -> None:
    with pytest.raises(ProfileInvalid) as refused:
        compile_profile(bool_column(mapping), 1)
    assert refused.value.where == "columns.2.paths.0.map"


def test_refuse_a_bool_path_without_a_map() -> None:
    obj = copy.deepcopy(PROFILE)
    del obj["columns"][2]["paths"][0]["map"]
    with pytest.raises(ProfileInvalid) as refused:
        compile_profile(obj, 1)
    assert refused.value.where == "columns.2.paths.0.map"


def test_refuse_a_map_on_a_non_bool_non_coded_path() -> None:
    obj = copy.deepcopy(PROFILE)
    obj["columns"][2]["paths"][0]["type"] = "text"
    with pytest.raises(ProfileInvalid) as refused:
        compile_profile(obj, 1)
    assert refused.value.where == "columns.2.paths.0.map"


def test_layout_check_holds_the_same_rule() -> None:
    good = Column("Met", ("body.block_met",), MappingProxyType({"body.block_met": {"Y": "true", "N": "false"}}),
                  MappingProxyType({"body.block_met": "bool"}))
    text_map = Column("Met", ("body.block_met",), MappingProxyType({"body.block_met": {"Y": "true", "N": "false"}}))
    bare = Column("Met", ("body.block_met",), types=MappingProxyType({"body.block_met": "bool"}))
    half = Column("Met", ("body.block_met",), MappingProxyType({"body.block_met": {"Y": "true"}}),
                  MappingProxyType({"body.block_met": "bool"}))

    def layout(column: Column) -> Layout:
        return Layout("t", "fleet_roster", "x", (Column("Row", ("source_record_id",)), column), MappingProxyType({}))

    check_layout(layout(good))
    for bad in (text_map, bare, half):
        with pytest.raises(ValueError):
            check_layout(layout(bad))


def test_the_contract_probes_pass_on_a_bool_profile() -> None:
    layout = compile_profile(PROFILE, 1)
    header, rows = split_file(layout, DATA)
    assert run_probes(layout, header, rows, **CTX) is None
