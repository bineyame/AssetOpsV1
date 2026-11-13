"""DATA-4 (D-DATA.5): "Charger use" from the declared ratings, and the availability read carrying them. No database:
the rule is pure (`site_outcomes.ev.charger_use`) and the ratings come from the W2 EV fixture read through the pure
`analytics.ev_availability.availability`."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import yaml

from assetops_backend.analytics.ev_availability import availability
from assetops_backend.site_outcomes.board import Contributor
from assetops_backend.site_outcomes.ev import (
    CHARGER_USE_NO_HOURS, CHARGER_USE_NO_RATING, CHARGER_USE_OVER, GROW, NO_SESSION_ASSESSMENT, _charging_from_claim,
    charger_use)
from assetops_backend.site_outcomes.mini import NOT_LOADED

RC = {"level": "HIGH"}
H8 = 8 * 3600  # one Tuesday's 08:00-16:00 schedule


def _c(asset: str, seconds, *, charger: str | None = "ch-1", charger_kw: str | None = "60.0",
       kw: str | None = "60.0") -> dict:
    return {"asset_id": asset, "label": asset, "scheduled_seconds": seconds, "charger_asset_id": charger,
            "charger_rated_kw": charger_kw, "connector_rated_kw": kw}


def _body(*connectors) -> dict:
    return {"availability": {"connectors": list(connectors)}}


def _text(kwh, body, limit="80") -> str:
    return charger_use(kwh, body, limit, RC).text


def test_normal_share_uses_the_charger_rating_not_the_connector_sum() -> None:
    use = charger_use("120", _body(_c("c1", H8), _c("c2", H8)), "80", RC)
    # 60 kW x 8 h = 480 kWh (not 120 kW x 8 h): 25 %
    assert use == Contributor("charger_use", "Charger use", "25% of declared charging capacity · 120 kWh with a "
                              "complete meter record in 8 h of scheduled charging at 60 kW", RC)


def test_connector_sum_when_the_charger_rating_is_not_declared() -> None:
    text = _text("120", _body(_c("c1", H8, charger_kw=None), _c("c2", H8, charger_kw=None)), "200")
    assert text.startswith("13% of declared charging capacity") and text.endswith("at 120 kW")  # 120/960


def test_import_limit_caps_the_rating_sum() -> None:
    body = _body(_c("c1", H8, charger="a", charger_kw="60"), _c("c2", H8, charger="b", charger_kw="60"))
    assert _text("320", body, "80").startswith("50% of declared charging capacity")  # 80 kW x 8 h = 640
    assert _text("320", body, "80").endswith("in 8 h of scheduled charging at the 80 kW import limit")  # 80 x 8 = 640, the capacity behind 50%
    assert _text("320", body, "200").startswith("33% ")  # 2 x 60 x 8 = 960, no cap
    assert _text("320", body, "200").endswith("at 60 kW")
    assert _text("320", body, "200").count("in 16 h") == 1  # uncapped: 60 kW x 16 charger-hours = 960


def test_import_limit_with_one_charger_and_with_unequal_hours() -> None:
    one = _body(_c("c1", H8, charger="a", charger_kw="100"))
    text = _text("200", one, "80")  # 100 kW > 80 kW: capacity 80 x 8 = 640 -> 31%
    assert text.startswith("31% ") and text.endswith("in 8 h of scheduled charging at the 80 kW import limit")
    assert _text("200", one, None).endswith("in 8 h of scheduled charging at 100 kW")
    two = _body(_c("c1", H8, charger="a", charger_kw="60"), _c("c2", H8 // 2, charger="b", charger_kw="60"))
    # capacity 60x8 + 60x4 = 720, scaled by 80/120 = 480 = 80 kW x 6 h
    assert _text("240", two, "80").startswith("50% ") and _text("240", two, "80").endswith(
        "in 6 h of scheduled charging at the 80 kW import limit")


def test_connectors_without_a_charger_count_on_their_own_rating() -> None:
    body = _body(_c("c1", H8, charger=None, kw="30"), _c("c2", H8 // 2, charger=None, kw="60"))
    assert _text("120", body, None).startswith("25% ")  # 30 x 8 + 60 x 4 = 480
    assert _text("120", body, None).endswith("in 12 h of scheduled charging at the declared ratings")


def test_small_zero_and_over_shares() -> None:
    body = _body(_c("c1", H8), _c("c2", H8))
    assert _text("2", body).startswith("under 1% of declared charging capacity · 2 kWh")
    assert _text("0", body).startswith("0% of declared charging capacity · 0 kWh")
    assert _text("480", body).startswith("100% ")
    assert _text("480.5", body) == CHARGER_USE_OVER


def test_not_loaded_no_session_no_rating_no_hours() -> None:
    body = _body(_c("c1", H8), _c("c2", H8))
    assert charger_use("120", None, "80", RC) == Contributor("charger_use", "Charger use", NOT_LOADED)
    assert _text(None, body) == NO_SESSION_ASSESSMENT
    assert _text("120", _body(_c("c1", H8, charger_kw=None, kw=None))) == CHARGER_USE_NO_RATING
    assert _text("120", _body(_c("c1", H8, charger_kw=None), _c("c2", H8, charger_kw=None, kw=None))) == \
        CHARGER_USE_NO_RATING  # a missing connector rating leaves the charger's sum undeclared
    assert _text("120", _body(_c("c1", 0), _c("c2", 0))) == CHARGER_USE_NO_HOURS
    assert _text("120", _body(_c("c1", None), _c("c2", None))) == CHARGER_USE_NO_HOURS
    assert _text("120", _body()) == CHARGER_USE_NO_HOURS
    assert charger_use("120", _body(), "80", RC).confidence is None  # a "Not available yet" line claims nothing


def test_the_claim_path_kwh_replaces_the_overview_kwh() -> None:
    body = _body(_c("c1", H8), _c("c2", H8))
    overview_use = charger_use("100", body, "80", RC)
    facts = SimpleNamespace(
        headline={GROW: "h"}, headline_money={GROW: None}, subline={GROW: None},
        contributors={GROW: (Contributor("charging_delivered", "Charging delivered", "100 kWh"), overview_use)})
    parts = {"known": True, "kwh": "240", "price": None, "money": None, "text": None}
    out = _charging_from_claim(parts, facts, False, 2, 3, RC, body, "80")
    lines = {x.key: x.text for x in out["contributors"][GROW]}
    assert lines["charging_delivered"].startswith("240 kWh with a complete meter record")
    assert lines["charger_use"].startswith("50% of declared charging capacity · 240 kWh")  # the same kWh
    unknown = {**parts, "known": False, "text": "Not known yet"}
    lines = {x.key: x.text for x in _charging_from_claim(unknown, facts, False, 2, 3, RC, body, "80")["contributors"][GROW]}
    assert lines["charger_use"] == NO_SESSION_ASSESSMENT


def test_the_ev_fixture_availability_rows_carry_the_declared_ratings() -> None:
    doc = yaml.safe_load((Path(__file__).parent / "fixtures" / "w2" / "ev-lab-001.yaml").read_text(encoding="utf-8"))
    content = doc["foundation"]
    assets = {c["component_id"]: f"asset-{c['component_id']}" for c in content["components"]}
    lo = datetime(2026, 10, 6, tzinfo=timezone.utc)  # a Tuesday
    hi = datetime(2026, 10, 7, tzinfo=timezone.utc)
    body = availability({"id": "rev", "content": content}, assets, [], lo, hi)
    rows = {r["asset_id"]: r for r in body["connectors"]}
    assert set(rows) == {"asset-c1", "asset-c2"}
    for r in rows.values():
        assert (r["connector_rated_kw"], r["charger_asset_id"], r["charger_rated_kw"], r["scheduled_seconds"]) == (
            "60.0", "asset-charger-1", "60.0", H8)
    # the whole rule over the fixture: 60 kW (not 120) x 8 h, under the 80 kW import limit
    assert _text("120", {"availability": body}, "80").startswith("25% of declared charging capacity")
    assert availability(None, assets, [], lo, hi)["connectors"] == []
