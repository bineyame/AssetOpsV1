"""1a (spec `specs/1a-optimize-card-scope/spec.md`, D-1A.1): the Portfolio Optimize card's figure is one lead
Finding's stored cost, chosen on the window's last day. Commit 1 pins today's behaviour (P1 to P4) before any change.
Pure: no database."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID

from assetops_backend.chain import vocabulary as v
from assetops_backend.chain.read import FindingHead, board_day, lead_finding, window_day
from assetops_backend.site_outcomes.read import (WINDOW_BASIS_DAY, BoardServices, SiteOutcomeBoardService, SiteRef,
                                                 _optimize_card)

UTC = timezone.utc
NAIROBI = "Africa/Nairobi"
LO, HI = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 31, tzinfo=UTC)
# The `KOBO` SiteRef literal of `test_out_w2_summary_window.py` (fixed ids here: the pins read no id).
T = UUID("00000000-0000-4000-8000-0000000001a0")
KOBO = SiteRef(T, UUID("00000000-0000-4000-8000-0000000001a1"), "KOBO-001", "Kobo", "MINIGRID", NAIROBI)


def _claim(amount: str | None, label: str = "possible_extra_fuel_cost", days=None, cur: str = "USD") -> dict:
    """As `test_ch5d1_optimize_card.py`: a cost claim as `money_claim` builds it (a stored consequence: no days)."""
    return v.money_claim(label, None if amount is None else {"amount": Decimal(amount), "currency": cur}, days).to_json()


def _site(code: str, name: str, claim: dict | None, nodes: bool = True) -> dict:
    """As `test_ch5d1_optimize_card.py`: one summary Site with only its `OPTIMIZE_COST` row."""
    row = {"category": "OPTIMIZE_COST", "state": "NEEDS_ATTENTION", "state_label": "Needs attention",
           "nodes": {"kpi": None, "potential": None, "earnings": claim} if nodes else None}
    return {"site_code": code, "site_name": name, "rows": [row], "earnings": None}


def _head(fid: str, start: datetime, end: datetime | None) -> FindingHead:
    return FindingHead(finding_id=fid, revision_id=f"{fid}-r1", revision_no=1, lifecycle="OPEN", transition=None,
                       episode_start=start, episode_end=end, mechanism="GENERATOR_AVOIDABLE", subject_ref="gen-1",
                       thread_id=None, occurrence_no=None)


# --- commit 1: the pins ----------------------------------------------------------------------------------------


def test_p1_the_board_day_of_a_multi_day_window_is_its_last_day() -> None:
    """Pins `chain/read.py` `window_day` rule 3: `to` is a UTC midnight, so the day is the UTC date of `to - 1 µs`."""
    assert window_day(LO, HI, NAIROBI) == date(2026, 10, 30)
    assert window_day(LO, HI, None) == date(2026, 10, 30)


def test_p2_a_mini_grid_site_is_judged_on_that_day_in_the_summary() -> None:
    """Pins `site_outcomes/read.py` `summary_window`: mini reads `window_day` on the DAY basis, no lo/hi."""
    service = SiteOutcomeBoardService(BoardServices(estate=None))
    assert service.summary_window(KOBO, LO, HI, None) == (WINDOW_BASIS_DAY, date(2026, 10, 30), None, None)
    assert WINDOW_BASIS_DAY == "DAY"


def test_p3_the_money_comes_from_the_one_lead_finding_touching_the_board_day() -> None:
    """Pins `chain/read.py` `lead_finding`: of the heads whose episode touches `[start, end)`, the greatest episode
    start; a head that ended before the day is never chosen."""
    a = _head("a", datetime(2026, 10, 2, tzinfo=UTC), datetime(2026, 10, 10, tzinfo=UTC))
    b = _head("b", datetime(2026, 10, 30, 6, tzinfo=UTC), None)
    start, end = board_day(date(2026, 10, 30), NAIROBI)
    assert lead_finding((a, b), start, end, source_open=True) == (b.finding_id, b.revision_id, True)
    assert lead_finding((a,), start, end, source_open=True) is None


def test_p4_the_card_carries_no_day_or_scope_today() -> None:
    """Pins `site_outcomes/read.py` `_optimize_card`: the seven keys, and no days line for a stored consequence."""
    card = _optimize_card([_site("K", "Kobo", _claim("3.31"))])
    assert set(card) == {"value", "missing", "detail", "basis_text", "days_line", "tone", "claim"}
    assert card["days_line"] is None
