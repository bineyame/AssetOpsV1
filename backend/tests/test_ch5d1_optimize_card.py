"""CH-5d1 L0 (build sheet CH-5d, ruling CH5d1-R §2.1-2.2, §3): the Portfolio Optimize card from each Site's chain cost
claim (`rows[OPTIMIZE_COST].nodes.earnings`), never summed across Sites. Pure."""
from __future__ import annotations

from decimal import Decimal

import pytest

from assetops_backend.chain import vocabulary as v
from assetops_backend.site_outcomes.read import _optimize_card, _unknown_row, portfolio_cards

FULL = {"complete": 7, "partial": 0, "low": 0, "no_data": 0, "pending": 0, "expected": 7}
BASIS_MONEY = "Modelled from the stored record and the declared price · not a saving"


def _claim(amount: str | None, label: str = "possible_extra_fuel_cost", days=None, cur: str = "USD") -> dict:
    """A cost claim as `money_claim` builds it (a stored consequence: no days, so the text is the amount alone)."""
    return v.money_claim(label, None if amount is None else {"amount": Decimal(amount), "currency": cur}, days).to_json()


def _site(code: str, name: str, claim: dict | None, nodes: bool = True) -> dict:
    row = {"category": "OPTIMIZE_COST", "state": "NEEDS_ATTENTION", "state_label": "Needs attention",
           "nodes": {"kpi": None, "potential": None, "earnings": claim} if nodes else None}
    return {"site_code": code, "site_name": name, "rows": [row], "earnings": None}


def _failed(code: str, name: str) -> dict:
    return {"site_code": code, "site_name": name, "earnings": None,
            "rows": [_unknown_row(c) for c in ("GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE")]}


def test_no_priced_site_reads_not_known() -> None:
    card = _optimize_card([_site("K", "Kobo", _claim(None)), _site("D", "Depot", None)])
    assert card == {"value": {"text": "Not known yet", "small": None}, "missing": False,
                    "detail": "No cost worked out yet at any site", "basis_text": "A cost needs a priced record",
                    "days_line": None, "tone": "neutral", "claim": None}
    assert _optimize_card([]) == card


def test_one_priced_site_shows_its_claim_text_byte_equal() -> None:
    claim = _claim("3.31")
    card = _optimize_card([_site("K", "Kobo", claim)])
    assert claim["text"] == "3.31 USD"
    assert card == {"value": {"text": claim["text"], "small": "possible extra fuel cost"}, "missing": False,
                    "detail": "At Kobo · not added across sites", "basis_text": BASIS_MONEY, "days_line": None,
                    "tone": "amber", "claim": claim}
    assert card["value"]["text"].encode() == claim["text"].encode()   # ONE-SOURCE: byte-equal


def test_one_priced_plus_one_not_known_and_a_failed_site_count_one() -> None:
    claim = _claim("3.31")
    sites = [_site("K", "Kobo", claim), _site("D", "Depot", _claim(None)), _failed("C", "Cold room")]
    card = _optimize_card(sites)
    assert card["value"] == {"text": "3.31 USD", "small": "possible extra fuel cost"}
    assert card["detail"] == "At Kobo · not added across sites" and card["claim"] == claim and card["tone"] == "amber"
    # a failed board alone is never priced
    assert _optimize_card([_failed("C", "Cold room")])["value"]["text"] == "Not known yet"


def test_two_priced_sites_list_each_and_never_sum() -> None:
    a, b = _claim("3.31"), _claim("1.20")
    card = _optimize_card([_site("K", "Kobo", a), _site("D", "Depot", b)])
    assert card == {"value": {"text": "Costs at 2 sites", "small": None}, "missing": False,
                    "detail": "Kobo: 3.31 USD possible extra fuel cost · Depot: 1.20 USD possible extra fuel cost",
                    "basis_text": BASIS_MONEY, "days_line": None, "tone": "amber", "claim": None}
    total = Decimal("3.31") + Decimal("1.20")
    flat = repr(card)
    for form in (str(total), v.money2(total), v.money_text(total, None, "USD")):
        assert form not in flat, form


def test_days_line_comes_from_the_claims_days() -> None:
    card = _optimize_card([_site("K", "Kobo", _claim("3.31", days=FULL))])
    assert card["days_line"] == "Kobo: " + v.days_line(FULL)
    assert card["value"]["text"] == _claim("3.31", days=FULL)["text"]
    assert _optimize_card([_site("K", "Kobo", _claim("3.31"))])["days_line"] is None


def test_unknown_cost_label_fails_loud() -> None:
    with pytest.raises(KeyError):
        _optimize_card([_site("K", "Kobo", _claim("3.31", label="something_new"))])


def test_portfolio_cards_order_is_grow_optimize_protect_assure() -> None:
    cards = portfolio_cards([_site("K", "Kobo", _claim("3.31"))], None, v.estate_income([]), [], None, 1)
    assert list(cards) == ["GROW_REVENUE", "OPTIMIZE_COST", "PROTECT_ASSET", "ASSURE_PERFORMANCE"]
    assert cards["OPTIMIZE_COST"] == _optimize_card([_site("K", "Kobo", _claim("3.31"))])
