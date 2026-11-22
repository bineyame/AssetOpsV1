"""IA-P P4a (spec section 4.2; D-IAP.29, handshake R7): E0, the waiting counts beside `placement_counts`.

Pure, on composed `portfolio_row` shapes written as literals after `test_cc_placement_postgres.py`'s world (two cold
ACT_NOW Findings with no Action, Kobo's COMPARE_VALUE Finding), plus a matched Action and a MONITOR member. A member
waits when it has no matched Action and its placement group is not MONITOR (NEEDS_INVESTIGATION still waits).
"""
from __future__ import annotations

from assetops_backend.estate.portfolio import waiting_by_site, waiting_count


def member(site: str, group: str, action_id: str | None = None) -> dict:
    return {"site_code": site, "action_id": action_id, "placement": {"group": group}}


WORLD = [member("THIKA-001", "ACT_NOW"), member("THIKA-001", "ACT_NOW"), member("KOBO-001", "COMPARE_VALUE")]


def test_e0_the_world() -> None:
    assert waiting_count(WORLD, True) == 3
    assert waiting_by_site(WORLD, True) == {"THIKA-001": 2, "KOBO-001": 1}
    assert sum(waiting_by_site(WORLD, True).values()) == waiting_count(WORLD, True)


def test_e0_a_matched_action_is_not_waiting() -> None:
    rows = [*WORLD, member("MTO-001", "ACT_NOW", action_id="a-1")]
    assert waiting_count(rows, True) == 3
    assert waiting_by_site(rows, True) == {"THIKA-001": 2, "KOBO-001": 1, "MTO-001": 0}


def test_e0_a_monitor_member_is_not_waiting_but_investigation_is() -> None:
    rows = [*WORLD, member("KISIWA-001", "MONITOR"), member("KISIWA-001", "NEEDS_INVESTIGATION")]
    assert waiting_count(rows, True) == 4
    assert waiting_by_site(rows, True)["KISIWA-001"] == 1
    assert sum(waiting_by_site(rows, True).values()) == waiting_count(rows, True)


def test_e0_unknown_findings_are_null() -> None:
    assert waiting_count(WORLD, False) is None and waiting_by_site(WORLD, False) is None
