"""6h (`specs/6h-named-option-levers/spec.md` §3.3, §10.1 P1, §10.2 test 2): prepare for a `STATED_OPTIONS` lever.

No action at position 0 with `settings {}`, then the lever's options in catalogue order; `current` must be `{}`."""
from __future__ import annotations

import json
from decimal import Decimal
from itertools import count
from types import MappingProxyType
from uuid import UUID

import pytest

from assetops_backend import prepare_decision
from assetops_backend.decisions.records import DecisionRefused, DecisionService
from assetops_backend.structure.levers import LEVERS
from lakeside_people import SLUG, email
from test_6a_commands import Composed
from test_6a_decisions import CLOCK, World, _cheap_hash  # noqa: F401 - the autouse password stand-in
from test_6h_levers import NAMED

EV_SITE = "DEPOT-001"


def _world(levers=None) -> World:
    w = World()
    w.store.add_site(w.p.tenant, EV_SITE, "EV_CHARGING", UUID(int=0xE1))
    if levers is not None:
        numbers = count(1)
        w.service = DecisionService(w.store, w.p.accounts, clock=lambda: w.clock[0],
                                    new_id=lambda: UUID(int=next(numbers)), levers=levers)
    return w


INJECTED = MappingProxyType({**LEVERS, NAMED.lever_id: NAMED})


def test_2_a_named_lever_prepares_no_action_then_its_options() -> None:
    w = _world(INJECTED)
    got = w.prepare(site="FRIDGE-001", lever_id="t_named", current={})
    assert [(o.option_key, o.generator, dict(o.settings), o.position) for o in got.options] == [
        ("no-action", "NO_ACTION", {}, 0), ("repair", "STATED_OPTIONS", {}, 1), ("replace", "STATED_OPTIONS", {}, 2)]
    assert got.decision.current_settings == {} and got.decision.purpose_factor_id == "excess_kwh"
    again = w.prepare(site="FRIDGE-001", lever_id="t_named", current={})
    assert again.already_prepared is True and again.decision.id == got.decision.id
    assert [o.id for o in again.options] == [o.id for o in got.options]
    assert len(w.store.decisions) == 1 and len(w.store.options) == 3


def test_2_a_named_lever_refuses_a_current_setting() -> None:
    w = _world(INJECTED)
    with pytest.raises(DecisionRefused, match="^BAD_CURRENT$"):
        w.prepare(site="FRIDGE-001", lever_id="t_named", current={"stop_soc_pct": Decimal(90)})


def test_2_a_grid_lever_still_refuses_an_empty_current() -> None:
    with pytest.raises(DecisionRefused, match="^BAD_CURRENT$"):
        _world().prepare(current={})


def test_2_the_cli_current_is_optional_and_refused_empty_for_a_grid_lever(capsys) -> None:
    w = _world()
    services = Composed(w.service)
    code = prepare_decision.main(["--tenant", SLUG, "--as", email("wanjiru"), "--site", "KOBO-001", "--lever",
                                  "generator_stop_reserve", "--period", "2026-10"], services=services)
    out, err = capsys.readouterr()
    assert code == 2 and out == "" and "BAD_CURRENT" in err


# --- P1: the nine catalogue levers (§10.1) -----------------------------------------------------------------------------

from test_6h_levers import NINE  # noqa: E402

SITE_OF = {"MINI_GRID": "KOBO-001", "COLD_CHAIN": "FRIDGE-001", "EV_DEPOT_CAPTIVE": EV_SITE}
OTHER_SITE = {"MINI_GRID": "FRIDGE-001", "COLD_CHAIN": EV_SITE, "EV_DEPOT_CAPTIVE": "KOBO-001"}


@pytest.mark.parametrize("lever_id", list(NINE))
def test_2_p1_each_named_lever_prepares_on_a_site_of_its_type(lever_id) -> None:
    key, _purpose, _changes, options, _bounds, _words = NINE[lever_id]
    w = _world()
    got = w.prepare(site=SITE_OF[key], lever_id=lever_id, current={})
    assert [(o.option_key, o.position, o.generator, dict(o.settings)) for o in got.options] == [
        ("no-action", 0, "NO_ACTION", {}), *[(k, i, "STATED_OPTIONS", {}) for i, (k, _, _) in enumerate(options, 1)]]
    assert w.prepare(site=SITE_OF[key], lever_id=lever_id, current={}).already_prepared is True
    with pytest.raises(DecisionRefused, match="^LEVER_SITE_TYPE$"):
        w.prepare(site=OTHER_SITE[key], lever_id=lever_id, current={})
    with pytest.raises(DecisionRefused, match="^BAD_CURRENT$"):
        w.prepare(site=SITE_OF[key], lever_id=lever_id, current={"stop_soc_pct": Decimal(90)}, period="2026-09")
