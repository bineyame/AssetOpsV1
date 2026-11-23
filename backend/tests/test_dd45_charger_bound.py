"""DD4.5 (D-DD.125): the EV capacity stage bounds buses by charger as well as by energy.

`buses_full_by_charger = chargers_in_service * floor(charger_kw * window_h / kwh_per_bus_night)`; a bus is short when
the energy is short or when no charger can fill it in the window. Kasarani's November is restated from the departure
log (`simulator/tests/world/fixtures/measured/metro-bus.measured.json`): short rows less spare rows met. The bound does
not bind at Embakasi, Ruiru, or Kasarani before 1 Nov (four chargers, eight buses)."""
from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

import pytest
import yaml

from assetops_backend.structure.evaluate import evaluate
from assetops_backend.structure.registry import REGISTRIES
from option_fixtures import leaves_for, recorded, stated

ROOT = Path(__file__).resolve().parents[2]
EV = REGISTRIES["EV_DEPOT_CAPTIVE"]
MANIFEST = yaml.safe_load((ROOT / "Docs/demo-sprint/product-direction-layer4/demo-site-scenario-manifest.yaml")
                          .read_text(encoding="utf-8"))
DEPARTURES = ROOT / "simulator/tests/world/fixtures/measured/metro-bus.measured.json"


def _physical(site: str) -> dict:
    tenant = next(t for t in MANIFEST["tenants"] if any(s["site"] == site for s in t["sites"]))
    return next(s for s in tenant["sites"] if s["site"] == site)


def _night(site: str, chargers: int, *, kwh: D, nights: int, short_nights: int, spare: int) -> dict:
    p = _physical(site)["physical"]
    given = {"chargers_in_service": stated(chargers), "charger_kw": stated(p["charger_kw"]),
             "import_limit_kw": stated(p["import_limit_kw"]), "window_h": stated(p["window_h"]),
             "buses": recorded(p["buses"]), "kwh_per_bus_night": recorded(p["kwh_per_bus_night"]),
             "peak_kwh": recorded(0), "kwh_2200_2400": recorded(kwh), "kwh_0000_0500": recorded(0),
             "short_nights": stated(short_nights), "spare_bus_nights": recorded(spare),
             "penalty_rate": stated("120.00", currency="USD")}
    out = dict(leaves_for(EV, given))
    from assetops_backend.structure.evaluate import LeafValue

    out["nights_in_period"] = LeafValue(D(nights), "DERIVED", ("calendar",), None, None, None, ())
    return {k: v.value for k, v in evaluate(EV, out).items()}


def test_b1_the_node_and_the_short_bus_expression() -> None:
    nodes = {r.factor_id: r.expression for r in EV.rows if not r.is_leaf}
    assert nodes["buses_full_by_charger"] == "chargers_in_service * floor(charger_kw * window_h / kwh_per_bus_night)"
    assert nodes["buses_short_per_night"] == ("max(ceil(max(required_kwh_night - supplied_kwh_night, 0) / "
                                              "kwh_per_bus_night), max(buses - buses_full_by_charger, 0))")
    order = [r.factor_id for r in EV.rows]
    assert order.index("required_kwh_night") < order.index("buses_full_by_charger") < order.index(
        "buses_short_per_night")
    row = EV.row("buses_full_by_charger")
    assert (row.home.category, row.home.objective, row.composes) == ("PROTECT_ASSET", "P1", "NONE")


def _log_missed(site: str, first: str) -> tuple[int, int, int]:
    rows = [r for r in json.loads(DEPARTURES.read_text(encoding="utf-8"))["departures"]
            if r["site_code"] == site and r["service_day"] >= first]
    short = [r for r in rows if D(r["kwh_at_departure"]) < D(r["required_kwh"])]
    spare_met = [r for r in rows if "-S" in r["vehicle_ref"] and D(r["kwh_at_departure"]) >= D(r["required_kwh"])]
    return len(short), len(spare_met), len(short) - len(spare_met)


def test_b2_kasarani_november_follows_the_departure_log() -> None:
    obs = _physical("Kasarani")["observations"]["november_to_date"]
    got = _night("Kasarani", 4 - obs["failed_chargers"], kwh=D(obs["kwh"]), nights=obs["nights"],
                 short_nights=obs["nights"], spare=obs["spare_bus_nights"])
    short, spare_met, missed = _log_missed("EV-KAS", obs["short_nights_from"])
    assert (short, spare_met, missed) == (10, 3, 7)  # B03, B04 on 1 Nov; B07, B08 on 2-5 Nov; S01 met 2-4 Nov
    assert obs["spare_bus_nights"] == spare_met
    assert got["buses_full_by_charger"] == 6  # 3 x floor(50 x 7 / 150)
    assert got["buses_short_per_night"] == 2  # the energy alone says 1
    assert got["departures_missed"] == missed
    assert got["penalties"] == D("840.00")


@pytest.mark.parametrize("site", ["Embakasi", "Ruiru", "Kasarani"])
def test_b3_the_bound_does_not_bind_with_every_charger_in_service(site) -> None:
    p = _physical(site)["physical"]
    got = _night(site, p["chargers"], kwh=D(p["buses"] * p["kwh_per_bus_night"]) * 30, nights=30, short_nights=0,
                 spare=0)
    assert got["buses_full_by_charger"] >= p["buses"]
    assert got["buses_short_per_night"] == 0
