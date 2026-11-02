"""WALK1-5 (build sheet WALK1 §6 WALK1-5, Addendum 4 fallback copy): the Kobo Grow spare-solar line reads the 5
Site-local days ending on the board day through the existing mini-depth renewable read contract.

The depth port is fed by the read's own pure `compose_renewable` over fixture stored hours (mixed ELIGIBLE, EXCLUDED,
LIMITED and missing days), so the composer is tested against the wire the real read returns once WALK1-4's
readings exist. No database."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from assetops_backend.mini_depth import read as depth_read
from assetops_backend.mini_depth.inputs import local_noon
from assetops_backend.site_outcomes import mini
from test_out_b2_mini import DAY, DEPTH, ZONE, Fake, contributor, run

GROW = mini.GROW
DAYS = [DAY - timedelta(days=4 - i) for i in range(5)]  # 16..20 Oct, the board day last


def hour(decision: str | None, cap=("40", "44"), used="15", head=("20", "26")) -> dict[str, Any] | None:
    """One selected stored noon hour as the read's `compose_renewable` takes it; `None` is a day with no result."""
    if decision is None:
        return None
    return {"hour": {"decision": decision, "capability_kw": {"low": cap[0], "high": cap[1]}, "used_kw": used,
                     "headroom_kw": {"low": head[0], "high": head[1]}}}


def cards(*decisions: Any) -> dict[str, Any]:
    """The renewable `cards` the read returns over the 5 requested days."""
    stored = [(d, local_noon(d, ZONE), r) for d, r in zip(DAYS, decisions)]
    return depth_read.compose_renewable(stored)["cards"]


def grow(renewable: dict[str, Any]) -> tuple[Any, dict[str, Any]]:
    comp, rows = run(Fake(cards={**DEPTH, "renewable": renewable}))
    return comp, rows[GROW]


def test_window_is_five_local_days_ending_on_the_board_day_and_the_read_accepts_it() -> None:
    fake = Fake()
    run(fake)
    lo, hi = next(args[1:] for name, args in fake.calls if name == "depth" and args[0] == "renewable")
    assert mini.RENEWABLE_DAYS == depth_read.MAX_DAYS == 5
    days = depth_read.hour_windows("renewable", lo, hi, ZONE)
    assert [d for d, _ in days] == DAYS
    assert [w for _, w in days] == [local_noon(d, ZONE) for d in DAYS]


def test_story_day_s_shape_no_spare_solar_on_two_checked_days() -> None:
    """Sheet: S board "Spare solar on 0 of 2 well-observed days · 3 of the last 5 days not checked"."""
    c = cards(None, hour("LIMITED"), hour("EXCLUDED", head=("-4", "0")), None, hour("EXCLUDED", head=("-2", "0")))
    assert (c["eligible_days"], c["assessed_days"]) == (0, 2)
    comp, row = grow(c)
    assert contributor(row, "productive_use")["text"] == (
        "Spare solar on 0 of 2 well-observed days · 3 of the last 5 days not checked")
    assert not any(i["kind"] == "OPPORTUNITY" for i in row["issues"])
    assert row["headline"] is None or "solar" not in row["headline"]


def test_mixed_days_give_headroom_headline_issue_and_suffix() -> None:
    c = cards(hour("ELIGIBLE", head=("20", "26")), hour("EXCLUDED", head=("-3", "0")), None,
              hour("ELIGIBLE", head=("22", "29")), hour("LIMITED"))
    assert (c["eligible_days"], c["assessed_days"]) == (2, 3)
    comp, row = grow(c)
    assert contributor(row, "productive_use")["text"] == (
        "Spare solar on 2 of 3 well-observed days · 2 of the last 5 days not checked")
    assert row["headline"] == "20–29 kW of daytime solar unused"  # span over the eligible days, form unchanged
    assert comp.short_values[GROW] == "20–29 kW unused"
    assert any(i["kind"] == "OPPORTUNITY" and i["text"] == "Productive-use headroom" for i in row["issues"])


def test_all_five_days_checked_has_no_suffix() -> None:
    c = cards(hour("ELIGIBLE"), hour("EXCLUDED", head=("-1", "0")), hour("ELIGIBLE"), hour("EXCLUDED", head=("-1", "0")),
              hour("ELIGIBLE"))
    _, row = grow(c)
    assert contributor(row, "productive_use")["text"] == "Spare solar on 3 of 5 well-observed days"


def test_one_checked_day_reads_singular() -> None:
    _, row = grow(cards(None, None, None, None, hour("ELIGIBLE")))
    assert contributor(row, "productive_use")["text"] == (
        "Spare solar on 1 of 1 well-observed day · 4 of the last 5 days not checked")


def test_no_checked_day_in_the_window_states_it() -> None:
    """Addendum 4: replaces "solar headroom not read for this day" when the 5-day window has no assessed day."""
    for c in (cards(None, None, None, None, None), cards(hour("LIMITED"), None, hour("CONFLICT"), None, None)):
        assert (c["eligible_days"], c["assessed_days"]) == (None, None)
        comp, row = grow(c)
        assert contributor(row, "productive_use")["text"] == (
            "Not available yet · spare solar not checked on the last 5 days")
        assert GROW not in comp.short_values
        assert not any(i["kind"] == "OPPORTUNITY" for i in row["issues"])


def test_refused_renewable_read_stays_not_available() -> None:
    _, rows = run(Fake(refuse=("depth:renewable",)))
    assert contributor(rows[GROW], "productive_use")["text"].startswith("Not available yet")
    assert "last 5 days" not in contributor(rows[GROW], "productive_use")["text"]


def test_new_strings_are_in_the_vocabulary_copy() -> None:
    assert "Not available yet · spare solar not checked on the last 5 days" in mini.COPY
    assert "Spare solar on 0 of 2 well-observed days · 3 of the last 5 days not checked" in mini.COPY
