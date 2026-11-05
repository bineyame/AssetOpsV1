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


def test_productive_use_and_headroom_issue_link_to_the_same_five_local_days() -> None:
    """M2/L1: Nairobi is UTC+3, so the bounds are local midnights (21:00Z), not UTC midnights."""
    c = cards(hour("ELIGIBLE"), hour("EXCLUDED", head=("-3", "0")), None, hour("ELIGIBLE"), hour("LIMITED"))
    _, row = grow(c)
    # CH-5a2a: built by `href_for` (URLSearchParams encoding, `:` as `%3A`; the same instants)
    want = (f"/sites/KOBO-001/performance/renewable?from={(DAY - timedelta(days=5)).isoformat()}T21%3A00%3A00Z"
            f"&to={DAY.isoformat()}T21%3A00%3A00Z")
    assert contributor(row, "productive_use")["href"] == want
    assert next(i for i in row["issues"] if i["text"] == "Productive-use headroom")["href"] == want


def test_board_link_bounds_are_accepted_by_the_opportunity_list_and_utc_midnights_are_not() -> None:
    """M1: WK-6 sends the link's bounds to the opportunity list; UTC midnights (the old window) were INVALID_WINDOW."""
    import pytest
    from datetime import datetime, timezone
    from urllib.parse import parse_qs, urlparse

    from assetops_backend.mini_decisions.model import DecisionRefused
    from assetops_backend.mini_decisions.opportunities import _local_day

    _, row = grow(cards(hour("ELIGIBLE"), None, None, None, None))
    q = parse_qs(urlparse(contributor(row, "productive_use")["href"]).query)
    lo, hi = (datetime.fromisoformat(q[k][0].replace("Z", "+00:00")) for k in ("from", "to"))
    assert (_local_day(lo, ZONE), _local_day(hi, ZONE)) == (DAY - timedelta(days=4), DAY + timedelta(days=1))
    with pytest.raises(DecisionRefused):
        _local_day(datetime(DAY.year, DAY.month, DAY.day, tzinfo=timezone.utc), ZONE)


def test_headline_and_signal_read_the_study_not_the_per_hour_cards() -> None:
    """CH9-R4 F2: the Grow headline figure, the short value and the headroom signal come from the selected study
    (the Portfolio's `opportunity_threads` read, over the same five renewable days); the per-hour card spread is a
    different fact and never names the opportunity."""
    c = cards(hour("ELIGIBLE", head=("2", "20")), hour("ELIGIBLE", head=("4", "18")), None, None, None)
    fake = Fake(cards={**DEPTH, "renewable": c}, study={"headroom_kw": {"low": "2", "high": "8"}, "eligible_days": 2,
                                                        "assessed_days": 2})
    comp, rows = run(fake)
    assert rows[GROW]["headline"] == "2–8 kW of daytime solar unused" and comp.short_values[GROW] == "2–8 kW unused"
    assert any(i["kind"] == "OPPORTUNITY" for i in rows[GROW]["issues"])
    depth_window = next(a[1:] for n, a in fake.calls if n == "depth" and a[0] == "renewable")
    assert next(a for n, a in fake.calls if n == "opportunity") == depth_window
    # No study item: no headroom headline and no signal, whatever the per-hour cards say.
    comp, rows = run(Fake(cards={**DEPTH, "renewable": c}, study=None))
    assert GROW not in comp.short_values and (rows[GROW]["headline"] is None or "solar" not in rows[GROW]["headline"])
    assert not any(i["kind"] == "OPPORTUNITY" for i in rows[GROW]["issues"])
