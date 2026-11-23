"""DD5a unit 1 (D-DD.138): the closed world EV table is generated from the depots' `/2` Foundations, and the lab
tables stay byte-identical. Pure; no database."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from pathlib import Path

from assetops_contracts import source_envelope_v4 as v4

ON1 = Path(__file__).resolve().parent / "fixtures" / "on1"
#: Digests of the lab tables on main at 9c38b69ac (D-DD.138: "the lab EV table is unchanged").
LAB_EV_SHA = "d3ddf9e338db6bddb4b443e2c221d99426c45ee94cf878d1c7073ed226c3ee33"
LAB_COLD_SHA = "7ec91e8fd6d17180643c8aa77fd21d977110bd4546bd93bb44695e3e29d057d5"


def _digest(table) -> str:
    rows = sorted([[list(k), dataclasses.asdict(e)] for k, e in table.items()])
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()


def _depots():
    doc = json.loads((ON1 / "metro-bus.onboarding.json").read_bytes())
    return {s["code"]: s for s in doc["sites"]}


def test_lab_tables_are_byte_identical() -> None:
    assert _digest(v4.V4_EV_CHANNEL_MAPPINGS) == LAB_EV_SHA
    assert _digest(v4.V4_COLD_CHANNEL_MAPPINGS) == LAB_COLD_SHA


def test_world_ev_table_is_generated_from_each_depot_foundation_exactly() -> None:
    union: dict = {}
    for code, site in _depots().items():
        declared = {(d["device_id"], s["signal_id"]) for d in site["devices"] for s in d["signals"]}
        table = v4.world_ev_channel_mappings(d["device_id"] for d in site["devices"])
        assert set(table) == declared, code  # every declared channel, nothing else: closed per Site
        prefixes = {re.match(r"(ch-[a-z0-9]+-c\d+)-", k[0]).group(1) for k in table if k[0].startswith("ch-")}
        assert prefixes == set(v4.WORLD_EV_CONNECTOR_PREFIXES[code]), code
        assert all(table[k] == v4._ev_connector(k[0].rsplit("-", 2)[0])[k] for k in table if k[0].startswith("ch-"))
        union.update(table)
    assert union == dict(v4.V4_WORLD_EV_CHANNEL_MAPPINGS)
    assert all(v4.V4_CHANNEL_MAPPINGS[k] == e for k, e in v4.V4_WORLD_EV_CHANNEL_MAPPINGS.items())


def test_world_ev_generation_refuses_a_device_outside_the_closed_shape() -> None:
    for bad in ("charger-controller", "ch-k1-connector-meter", "ch-K1-c1-connector-meter", "site-meter-2"):
        try:
            v4.world_ev_channel_mappings(["site-meter", bad])
        except ValueError:
            continue
        raise AssertionError(bad)
