"""D-SR.59 H-1 (no DB): every window the mini depth client sends is one `hour_windows` takes.

The checked-in contract `frontend/src/sites/__tests__/fixtures/mini-windows-contract.json` lists, for a +3 and a -5
zone, the window `renewableWindowFromParams` / `serviceWindowFromParams` give under every bar preset, 2- and 5-day
ranges, a story hour and a day-form address. The frontend vitest (`ui/__tests__/sharedRange.test.tsx`) asserts the
client equals it; this test asserts the server refuses none of it. `hour_windows` stays strict: do not loosen it or
regenerate the fixture to make one side pass.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from assetops_backend.mini_depth.read import MiniReadRefused, hour_windows

FIXTURE = Path(__file__).resolve().parents[2] / "frontend/src/sites/__tests__/fixtures/mini-windows-contract.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


def _at(token: str) -> datetime:
    return datetime.fromisoformat(token.replace("Z", "+00:00"))


def test_contract_covers_both_zones_and_every_input() -> None:
    labels = {"preset yesterday", "preset 7d", "preset 30d", "custom 2 days", "custom 5 days", "story hour", "day form"}
    for zone in ("Africa/Addis_Ababa", "America/Bogota"):
        assert labels <= {c["label"] for c in CASES if c["zone"] == zone}


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['zone']}-{c['label']}")
def test_renewable_window_is_accepted(case: dict) -> None:
    w = case["renewable"]
    try:
        days = hour_windows("renewable", _at(w["from"]), _at(w["to"]), case["zone"])
    except MiniReadRefused as error:  # pragma: no cover - the failure message is the point
        pytest.fail(f"renewable {w} refused: {error}")
    assert days


@pytest.mark.parametrize("domain", ["service", "backup", "fuel"])
@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['zone']}-{c['label']}")
def test_hour_window_is_accepted(case: dict, domain: str) -> None:
    w = case["service"]
    try:
        windows = hour_windows(domain, _at(w["from"]), _at(w["to"]), case["zone"])
    except MiniReadRefused as error:  # pragma: no cover
        pytest.fail(f"{domain} {w} refused: {error}")
    assert [win.start for _, win in windows] == [_at(w["from"])]


def test_server_still_refuses_a_utc_day_in_a_shifted_zone() -> None:
    """The pair is not vacuous: the old client's raw UTC-day address is refused for both domains."""
    with pytest.raises(MiniReadRefused):
        hour_windows("renewable", _at("2026-11-11T00:00:00Z"), _at("2026-11-12T00:00:00Z"), "America/Bogota")
    with pytest.raises(MiniReadRefused):
        hour_windows("service", _at("2026-11-11T00:00:00Z"), _at("2026-11-12T00:00:00Z"), "Africa/Addis_Ababa")
